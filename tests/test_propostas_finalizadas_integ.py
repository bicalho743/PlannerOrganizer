"""
Testes de integração que garantem a invariante:
"proposta finalizada = dois campos" (status == "finalizada"
E status_execucao == "Finalizada"), de modo que propostas finalizadas
NUNCA sumam do filtro de finalizadas.

Estes testes batem no banco de DESENVOLVIMENTO (DATABASE_URL). Para preservar
o isolamento multi-tenant, cada teste roda sob um usuario_id de teste único e
remove (cleanup) tudo o que criou no teardown.

Como rodar:
    python -m pytest tests/ -v
"""

import os
import uuid

import pytest
from sqlalchemy import text

from utils.database import Database
from utils.filtro_propostas import get_propostas_finalizadas
from utils.finalizar_proposta_v2 import finalizar_proposta_v2
from utils.proposta_status import (
    STATUS_FINALIZADA,
    STATUS_EM_ABERTO,
    STATUS_EM_EXECUCAO,
)
from utils.status_execucao import EXEC_FINALIZADA

# Guarda: estes testes escrevem no banco apontado por DATABASE_URL. Só rodam
# quando a variável está definida (ambiente de desenvolvimento), evitando
# execução acidental sem banco configurado.
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="Testes de integração exigem DATABASE_URL (banco de desenvolvimento)",
)


@pytest.fixture
def db_ctx():
    """Cria uma Database isolada (usuario_id de teste único) + um cliente de
    teste, e limpa tudo ao final."""
    usuario_id = f"test-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=usuario_id)
    # Garante o isolamento mesmo que o construtor tenha caído em fallback.
    db.usuario_id = usuario_id

    cliente_id = db.add_cliente(nome="Cliente Teste Pytest")
    created = {"propostas": [], "cliente_id": cliente_id}

    try:
        yield db, created
    finally:
        for pid in created["propostas"]:
            try:
                db.excluir_proposta_segura(pid, usuario_id)
            except Exception:
                pass
        try:
            db.delete_cliente(cliente_id)
        except Exception:
            pass
        try:
            db.session.close()
        except Exception:
            pass


def _finalizadas(db):
    """Lê o filtro de finalizadas com estado/cache invalidados.

    `expire_all()` descarta os objetos do identity map da sessão para que a
    releitura traga os valores realmente gravados no banco — necessário quando
    a finalização ocorre por outra conexão (ex.: finalizar_proposta_v2)."""
    db.session.expire_all()
    db.invalidar_cache()
    return get_propostas_finalizadas(db)


def test_proposta_criada_finalizada_aparece(db_ctx):
    """Caso A: proposta criada já finalizada (criação direta) aparece no filtro
    de finalizadas com os dois campos alinhados."""
    db, created = db_ctx

    pid = db.add_proposta(
        cliente_id=created["cliente_id"],
        descricao="Proposta finalizada por criação direta",
        valor=1000.0,
        status=STATUS_FINALIZADA,
    )
    created["propostas"].append(pid)

    fin = _finalizadas(db)
    linha = fin[fin["id"] == pid]

    assert not linha.empty, "Proposta finalizada por criação direta sumiu do filtro de finalizadas"
    assert linha.iloc[0]["status"] == STATUS_FINALIZADA
    assert linha.iloc[0]["status_execucao"] == EXEC_FINALIZADA


def test_venda_de_proposta_finaliza_e_aparece(db_ctx):
    """Caso B: vender uma proposta de serviço finaliza-a e ela passa a aparecer
    no filtro de finalizadas com os dois campos alinhados."""
    db, created = db_ctx

    pid = db.add_proposta(
        cliente_id=created["cliente_id"],
        descricao="Proposta para venda de serviço",
        valor=2500.0,
        status=STATUS_EM_ABERTO,
    )
    created["propostas"].append(pid)

    resultado = db.criar_venda_de_proposta(pid)
    assert resultado.get("status") == "sucesso", f"Venda não criada: {resultado}"

    fin = _finalizadas(db)
    linha = fin[fin["id"] == pid]

    assert not linha.empty, "Proposta finalizada via venda sumiu do filtro de finalizadas"
    assert linha.iloc[0]["status"] == STATUS_FINALIZADA
    assert linha.iloc[0]["status_execucao"] == EXEC_FINALIZADA


def test_edicao_status_para_finalizada_aparece(db_ctx):
    """Caso C (tela de edição — dropdown de status): mudar o status para
    "finalizada" via update_proposta deve manter a proposta visível no filtro
    de finalizadas, com os dois campos alinhados."""
    db, created = db_ctx

    pid = db.add_proposta(
        cliente_id=created["cliente_id"],
        descricao="Proposta finalizada pela edição (dropdown)",
        valor=1800.0,
        status=STATUS_EM_ABERTO,
    )
    created["propostas"].append(pid)

    # Caminho real da tela de edição: o dropdown "Finalizada" mapeia para o
    # status canônico e a gravação chama update_proposta(status=...).
    res = db.update_proposta(pid, status=STATUS_FINALIZADA)
    assert res.get("status") == "success", f"Edição não aplicada: {res}"

    fin = _finalizadas(db)
    linha = fin[fin["id"] == pid]

    assert not linha.empty, "Proposta finalizada pela edição sumiu do filtro de finalizadas"
    assert linha.iloc[0]["status"] == STATUS_FINALIZADA
    assert linha.iloc[0]["status_execucao"] == EXEC_FINALIZADA


def test_botao_finalizar_projeto_aparece(db_ctx):
    """Caso D (tela de edição — botão "FINALIZAR PROJETO"): finalizar_proposta_v2
    deve alinhar os dois campos e manter a proposta visível no filtro de
    finalizadas."""
    db, created = db_ctx

    pid = db.add_proposta(
        cliente_id=created["cliente_id"],
        descricao="Proposta finalizada pelo botão FINALIZAR PROJETO",
        valor=3200.0,
        status=STATUS_EM_EXECUCAO,
    )
    created["propostas"].append(pid)

    res = finalizar_proposta_v2(int(pid))
    assert res.get("status") is True, f"Finalização v2 falhou: {res}"

    fin = _finalizadas(db)
    linha = fin[fin["id"] == pid]

    assert not linha.empty, "Proposta finalizada pelo botão sumiu do filtro de finalizadas"
    assert linha.iloc[0]["status"] == STATUS_FINALIZADA
    assert linha.iloc[0]["status_execucao"] == EXEC_FINALIZADA


def test_geracao_fornecedores_usa_status_canonico(db_ctx):
    """Caso E (geração financeira — gate de comissão de fornecedores):
    `gerar_lancamentos_financeiros_proposta_concluida` deve abrir o
    processamento de fornecedores quando o status canônico é "finalizada",
    mesmo que `status_execucao` esteja desalinhado.

    Antes da correção, o gate comparava o rótulo legado ("Concluída") e só
    funcionava pelo fallback de `status_execucao`; com os campos híbridos
    (status="finalizada", status_execucao!="Finalizada") os fornecedores
    deixavam de ser computados."""
    db, created = db_ctx

    pid = db.add_proposta(
        cliente_id=created["cliente_id"],
        descricao="Proposta com fornecedor (gate de comissão)",
        valor=2000.0,
        status=STATUS_EM_ABERTO,
    )
    created["propostas"].append(pid)

    db.add_acrescimo_proposta(
        proposta_id=pid,
        tipo="FORNECEDOR",
        valor=500.0,
        fornecedor="Fornecedor Teste Pytest",
    )

    # Força um estado HÍBRIDO via SQL cru, contornando o alinhamento automático
    # do ORM: status canônico "finalizada" mas status_execucao desalinhado.
    db.session.execute(
        text(
            "UPDATE propostas SET status = :st, status_execucao = :ex "
            "WHERE id = :pid AND usuario_id = :uid"
        ),
        {
            "st": STATUS_FINALIZADA,
            "ex": "Em execução",
            "pid": int(pid),
            "uid": db.usuario_id,
        },
    )
    db.session.commit()
    db.session.expire_all()

    resultado = db.gerar_lancamentos_financeiros_proposta_concluida(
        proposta_id=int(pid), forcar_geracao=False
    )

    assert resultado.get("valor_fornecedores") == 500.0, (
        "Fornecedores não computados: o gate não reconheceu o status canônico "
        f"'finalizada' com status_execucao desalinhado. Resultado: {resultado}"
    )
