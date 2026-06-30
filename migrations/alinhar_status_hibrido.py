"""Migração one-shot: corrige propostas presas em estado híbrido de status.

Contexto
--------
A Task #28 endureceu apenas os CAMINHOS DE ESCRITA: toda gravação nova mantém
`propostas.status` e `propostas.status_execucao` alinhados e canônicos. Porém,
registros gravados ANTES dessa correção podem estar em estado híbrido no banco
(ex.: status='finalizada' com status_execucao='Não iniciada'/'Em execução'/
'Cancelada'/NULL, ou status_execucao='Finalizada' sem o status principal). Como
as telas de finalizadas/acompanhamento filtram pelos DOIS campos, essas
propostas podem sumir das telas.

O que faz
---------
1. AUDITORIA: lista propostas cujos dois campos estão desalinhados em relação ao
   vocabulário canônico, agrupadas por usuário (multi-tenant).
2. MIGRAÇÃO: normaliza os valores legados e alinha os dois campos usando as
   fontes únicas de verdade `utils.proposta_status.normalize` e
   `utils.status_execucao` (normalize + derive_exec_from_status).
3. VERIFICAÇÃO PÓS-MIGRAÇÃO: confirma que não sobrou nenhum desalinhamento e que
   nenhuma proposta finalizada/vendida sumiu (a contagem de finalizadas por
   qualquer um dos sinais é preservada e fica visível com os DOIS campos).

Propriedades
------------
- Idempotente: rodar várias vezes não causa efeito colateral (só atualiza linhas
  que ainda divergem do canônico).
- Seguro por usuário: a auditoria/relatório é agrupada por `usuario_id`; a
  correção preserva o `usuario_id` de cada linha (não cruza tenants).
- Não destrutivo quanto a finalizadas: se QUALQUER um dos campos indica
  finalizada, ambos passam a finalizada/Finalizada (regra "proposta finalizada =
  dois campos", evita sumiço).

Uso
---
    python migrations/alinhar_status_hibrido.py            # aplica a migração
    python migrations/alinhar_status_hibrido.py --dry-run  # só audita, não grava
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from utils.proposta_status import normalize as norm_status, STATUS_FINALIZADA
from utils.status_execucao import (
    normalize as norm_exec,
    derive_exec_from_status,
    EXEC_FINALIZADA,
)


def canonical_pair(raw_status, raw_exec):
    """Retorna o par canônico (status, status_execucao) alinhado.

    Regras:
    - REGRA FORTE: se QUALQUER um dos campos indica finalizada (o status
      principal OU o status_execucao), ambos viram (finalizada, Finalizada).
      Isso preserva o objetivo "proposta finalizada = dois campos" e impede que
      uma finalizada histórica suma das telas por um campo desalinhado.
    - Caso contrário -> o status principal manda e derivamos o status_execucao
      coerente (derive_exec_from_status); se o status for desconhecido, mantemos
      o status_execucao normalizado.
    """
    cs = norm_status(raw_status)
    ce = norm_exec(raw_exec)

    if cs == STATUS_FINALIZADA or ce == EXEC_FINALIZADA:
        return STATUS_FINALIZADA, EXEC_FINALIZADA

    new_exec = derive_exec_from_status(cs)
    if new_exec is None:
        new_exec = ce
    return cs, new_exec


def _is_finalizada_por_qualquer_sinal(raw_status, raw_exec):
    return (
        norm_status(raw_status) == STATUS_FINALIZADA
        or norm_exec(raw_exec) == EXEC_FINALIZADA
    )


def main(dry_run=False):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL não definido; abortando.")

    engine = create_engine(database_url)

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, usuario_id, status, status_execucao FROM propostas"
            )
        ).fetchall()

        finalizadas_antes = sum(
            1 for r in rows if _is_finalizada_por_qualquer_sinal(r.status, r.status_execucao)
        )

        desalinhadas = []
        for r in rows:
            new_status, new_exec = canonical_pair(r.status, r.status_execucao)
            if new_status != r.status or new_exec != r.status_execucao:
                desalinhadas.append(
                    {
                        "id": r.id,
                        "usuario_id": r.usuario_id,
                        "de": (r.status, r.status_execucao),
                        "para": (new_status, new_exec),
                    }
                )

        print("=" * 70)
        print(f"AUDITORIA: {len(rows)} propostas no total")
        print(f"  finalizadas (por qualquer sinal) antes: {finalizadas_antes}")
        print(f"  desalinhadas a corrigir: {len(desalinhadas)}")
        print("-" * 70)

        # Relatório agrupado por usuário (multi-tenant)
        por_usuario = {}
        for d in desalinhadas:
            por_usuario.setdefault(d["usuario_id"], []).append(d)
        for usuario_id, itens in sorted(por_usuario.items(), key=lambda kv: str(kv[0])):
            print(f"  usuario_id={usuario_id!r}: {len(itens)} proposta(s)")
            for d in itens:
                print(
                    f"    proposta #{d['id']}: {d['de']} -> {d['para']}"
                )
        print("=" * 70)

        if not desalinhadas:
            print("Nada a corrigir. Banco já está canônico/alinhado.")
            return

        if dry_run:
            print("--dry-run: nenhuma alteração gravada.")
            return

        for d in desalinhadas:
            conn.execute(
                text(
                    "UPDATE propostas SET status = :status, "
                    "status_execucao = :exec WHERE id = :id"
                ),
                {"status": d["para"][0], "exec": d["para"][1], "id": d["id"]},
            )
        print(f"MIGRAÇÃO: {len(desalinhadas)} proposta(s) atualizada(s).")

        # Verificação ATÔMICA: roda na MESMA transação, antes do commit. O
        # PostgreSQL enxerga as próprias gravações (read-your-writes); se a
        # verificação falhar, o raise propaga e o engine.begin() faz ROLLBACK,
        # deixando o banco intacto (migração tudo-ou-nada).
        rows = conn.execute(
            text(
                "SELECT id, usuario_id, status, status_execucao FROM propostas"
            )
        ).fetchall()

        restantes = [
            r
            for r in rows
            if canonical_pair(r.status, r.status_execucao)
            != (r.status, r.status_execucao)
        ]
        finalizadas_depois = sum(
            1
            for r in rows
            if _is_finalizada_por_qualquer_sinal(r.status, r.status_execucao)
        )
        finalizadas_visiveis = sum(
            1
            for r in rows
            if r.status == STATUS_FINALIZADA and r.status_execucao == EXEC_FINALIZADA
        )

        print("-" * 70)
        print("VERIFICAÇÃO PRÉ-COMMIT (mesma transação):")
        print(f"  desalinhamentos restantes: {len(restantes)} (esperado: 0)")
        print(f"  finalizadas (por qualquer sinal) depois: {finalizadas_depois}")
        print(f"  finalizadas visíveis (dois campos alinhados): {finalizadas_visiveis}")

        ok = (
            len(restantes) == 0
            and finalizadas_visiveis == finalizadas_depois
            and finalizadas_depois >= finalizadas_antes
        )
        print("  RESULTADO:", "OK (commit)" if ok else "FALHOU (rollback)")
        print("=" * 70)
        if not ok:
            raise SystemExit(
                "Verificação falhou; transação revertida (ROLLBACK). "
                "Nenhuma alteração foi gravada."
            )


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
