"""
Teste de integração da invariante "proposta finalizada = dois campos".

Esta invariante exige que, para uma proposta aparecer nas telas/listas de
finalizadas, os DOIS campos estejam alinhados:
    - `propostas.status`           == "finalizada"  (utils.proposta_status)
    - `propostas.status_execucao`  == "Finalizada"  (utils.status_execucao)

`utils.filtro_propostas.get_propostas_finalizadas()` faz o AND desses dois
campos. Se qualquer caminho de escrita esquecer um deles, a proposta "some".
Estes testes blindam os principais caminhos de finalização:
    - Caso A: criação direta com status finalizado (`db.add_proposta`).
    - Caso B: venda de proposta (`db.criar_venda_de_proposta`).
    - Caso C: edição pelo dropdown de status (`db.update_proposta`).
    - Caso D: botão "FINALIZAR PROJETO" (`finalizar_proposta_v2`).

Como rodar:
    python -m pytest tests/ -v

IMPORTANTE: estes testes batem no PostgreSQL de dev (via DATABASE_URL). Cada
execução usa um `usuario_id` único de teste e limpa (DELETE) tudo o que criou
no teardown, para não poluir dados reais de outros tenants.
"""

import os
import uuid

import pytest
from sqlalchemy import text

from utils.database import Database, engine
from utils.filtro_propostas import get_propostas_finalizadas
from utils.finalizar_proposta_v2 import finalizar_proposta_v2
from utils.proposta_status import (
    STATUS_FINALIZADA,
    STATUS_EM_ABERTO,
    STATUS_EM_EXECUCAO,
)
from utils.status_execucao import EXEC_FINALIZADA


def _cleanup(usuario_id):
    """Remove todas as linhas criadas pelo teste para este usuario_id.

    Ordem respeita as dependências de chave estrangeira: filhos antes dos pais.
    O engine roda em AUTOCOMMIT, então cada DELETE é efetivado imediatamente.
    """
    propostas_subselect = "SELECT id FROM propostas WHERE usuario_id = :uid"
    vendas_subselect = (
        f"SELECT id FROM vendas WHERE proposta_id IN ({propostas_subselect})"
    )
    post_org_subselect = (
        f"SELECT id FROM post_organizations WHERE proposta_id IN ({propostas_subselect})"
    )
    statements = [
        f"DELETE FROM post_organization_actions WHERE post_organization_id IN ({post_org_subselect})",
        f"DELETE FROM post_organizations WHERE proposta_id IN ({propostas_subselect})",
        f"DELETE FROM itens_venda WHERE venda_id IN ({vendas_subselect})",
        f"DELETE FROM financeiro WHERE proposta_id IN ({propostas_subselect})",
        f"DELETE FROM vendas WHERE proposta_id IN ({propostas_subselect})",
        f"DELETE FROM acrescimos_proposta WHERE proposta_id IN ({propostas_subselect})",
        f"DELETE FROM produtos_organizadores WHERE proposta_id IN ({propostas_subselect})",
        "DELETE FROM propostas WHERE usuario_id = :uid",
        "DELETE FROM clientes WHERE usuario_id = :uid",
        "DELETE FROM perfis WHERE usuario_id = :uid",
    ]
    with engine.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt), {"uid": usuario_id})


@pytest.fixture
def db_teste():
    """Cria um Database isolado com usuario_id único + um cliente de teste.

    Faz cleanup completo de tudo que foi criado no teardown.
    """
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL não definido; teste de integração ignorado.")

    usuario_id = f"test-finalizadas-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=usuario_id)

    # Garantir estado limpo mesmo que uma execução anterior tenha falhado.
    _cleanup(usuario_id)

    cliente_id = db.add_cliente(nome="Cliente Teste Finalizadas")
    assert cliente_id is not None, "Falha ao criar cliente de teste"

    yield db, usuario_id, cliente_id

    _cleanup(usuario_id)


def _buscar_proposta(df, proposta_id):
    """Retorna a linha da proposta no DataFrame de finalizadas, ou None."""
    if df is None or df.empty:
        return None
    encontrada = df[df["id"] == proposta_id]
    if encontrada.empty:
        return None
    return encontrada.iloc[0]


def _finalizadas_frescas(db):
    """Lê as propostas finalizadas direto do banco (verdade persistida).

    Dois efeitos garantem leitura fresca:
    - `session.expire_all()` descarta os objetos do identity map da sessão, para
      que a releitura traga os valores realmente gravados — necessário quando a
      finalização ocorre por outra conexão (ex.: `finalizar_proposta_v2`).
    - `invalidar_cache()` simula o rerun do Streamlit (que limpa o cache por
      sessão de `get_propostas()`), garantindo que a asserção bata no estado
      persistido no banco, não em uma leitura em cache.
    """
    db.session.expire_all()
    db.invalidar_cache()
    return get_propostas_finalizadas(db)


def test_criacao_direta_finalizada_aparece(db_teste):
    """Caso A: proposta criada já finalizada aparece em finalizadas com os dois campos."""
    db, usuario_id, cliente_id = db_teste

    proposta_id = db.add_proposta(
        cliente_id=cliente_id,
        descricao="Proposta criada finalizada (Caso A)",
        valor=1000.0,
        status=STATUS_FINALIZADA,
        gerar_transacoes_automaticas=False,
    )
    assert proposta_id and proposta_id > 0, "Falha ao criar proposta finalizada"

    finalizadas = _finalizadas_frescas(db)
    linha = _buscar_proposta(finalizadas, proposta_id)

    assert linha is not None, (
        "Proposta criada finalizada NÃO apareceu em get_propostas_finalizadas() "
        "— invariante 'dois campos' violada na criação direta."
    )
    assert linha["status"] == STATUS_FINALIZADA
    assert linha["status_execucao"] == EXEC_FINALIZADA


def test_venda_de_proposta_finaliza_e_aparece(db_teste):
    """Caso B: vender uma proposta a finaliza e ela aparece com os dois campos."""
    db, usuario_id, cliente_id = db_teste

    proposta_id = db.add_proposta(
        cliente_id=cliente_id,
        descricao="Proposta para venda (Caso B)",
        valor=2500.0,
        status=STATUS_EM_ABERTO,
        gerar_transacoes_automaticas=False,
    )
    assert proposta_id and proposta_id > 0, "Falha ao criar proposta base"

    # Antes da venda, não deve constar como finalizada.
    antes = _finalizadas_frescas(db)
    assert _buscar_proposta(antes, proposta_id) is None, (
        "Proposta em aberto não deveria aparecer como finalizada antes da venda."
    )

    resultado = db.criar_venda_de_proposta(proposta_id)
    assert resultado and resultado.get("status") == "sucesso", (
        f"criar_venda_de_proposta falhou: {resultado}"
    )

    depois = _finalizadas_frescas(db)
    linha = _buscar_proposta(depois, proposta_id)

    assert linha is not None, (
        "Proposta vendida NÃO apareceu em get_propostas_finalizadas() "
        "— invariante 'dois campos' violada no fluxo de venda."
    )
    assert linha["status"] == STATUS_FINALIZADA
    assert linha["status_execucao"] == EXEC_FINALIZADA


def test_edicao_status_para_finalizada_aparece(db_teste):
    """Caso C (tela de edição — dropdown de status): mudar o status para
    "finalizada" via update_proposta deve manter a proposta visível no filtro
    de finalizadas, com os dois campos alinhados."""
    db, usuario_id, cliente_id = db_teste

    proposta_id = db.add_proposta(
        cliente_id=cliente_id,
        descricao="Proposta finalizada pela edição (dropdown)",
        valor=1800.0,
        status=STATUS_EM_ABERTO,
        gerar_transacoes_automaticas=False,
    )
    assert proposta_id and proposta_id > 0, "Falha ao criar proposta base"

    # Caminho real da tela de edição: o dropdown "Finalizada" mapeia para o
    # status canônico e a gravação chama update_proposta(status=...).
    res = db.update_proposta(proposta_id, status=STATUS_FINALIZADA)
    assert res.get("status") == "success", f"Edição não aplicada: {res}"

    fin = _finalizadas_frescas(db)
    linha = _buscar_proposta(fin, proposta_id)

    assert linha is not None, (
        "Proposta finalizada pela edição sumiu do filtro de finalizadas "
        "— invariante 'dois campos' violada no fluxo de edição."
    )
    assert linha["status"] == STATUS_FINALIZADA
    assert linha["status_execucao"] == EXEC_FINALIZADA


def test_botao_finalizar_projeto_aparece(db_teste):
    """Caso D (tela de edição — botão "FINALIZAR PROJETO"): finalizar_proposta_v2
    deve alinhar os dois campos e manter a proposta visível no filtro de
    finalizadas."""
    db, usuario_id, cliente_id = db_teste

    proposta_id = db.add_proposta(
        cliente_id=cliente_id,
        descricao="Proposta finalizada pelo botão FINALIZAR PROJETO",
        valor=3200.0,
        status=STATUS_EM_EXECUCAO,
        gerar_transacoes_automaticas=False,
    )
    assert proposta_id and proposta_id > 0, "Falha ao criar proposta base"

    res = finalizar_proposta_v2(int(proposta_id))
    assert res.get("status") is True, f"Finalização v2 falhou: {res}"

    fin = _finalizadas_frescas(db)
    linha = _buscar_proposta(fin, proposta_id)

    assert linha is not None, (
        "Proposta finalizada pelo botão sumiu do filtro de finalizadas "
        "— invariante 'dois campos' violada no fluxo do botão FINALIZAR PROJETO."
    )
    assert linha["status"] == STATUS_FINALIZADA
    assert linha["status_execucao"] == EXEC_FINALIZADA


def test_geracao_fornecedores_usa_status_canonico(db_teste):
    """Caso E (geração financeira — gate de comissão de fornecedores):
    `gerar_lancamentos_financeiros_proposta_concluida` deve abrir o
    processamento de fornecedores quando o status canônico é "finalizada",
    mesmo que `status_execucao` esteja desalinhado.

    Antes da correção, o gate comparava o rótulo legado ("Concluída") e só
    funcionava pelo fallback de `status_execucao`; com os campos híbridos
    (status="finalizada", status_execucao!="Finalizada") os fornecedores
    deixavam de ser computados."""
    db, usuario_id, cliente_id = db_teste

    pid = db.add_proposta(
        cliente_id=cliente_id,
        descricao="Proposta com fornecedor (gate de comissão)",
        valor=2000.0,
        status=STATUS_EM_ABERTO,
        gerar_transacoes_automaticas=False,
    )
    assert pid and pid > 0, "Falha ao criar proposta base"

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
            "uid": usuario_id,
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
