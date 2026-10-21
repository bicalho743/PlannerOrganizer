"""
Isolamento entre contas: uma conta nunca lê, altera ou apaga dados de outra.

A conta B recebe os ids da conta A (como faria alguém mexendo na API do app de celular)
e tenta usá-los pelos métodos do banco e pelas rotas da API. Os dados de A têm de
continuar intactos. Usa o Postgres de dev (DATABASE_URL); tudo é criado com ids de teste
únicos e apagado no fim.
"""
import os
import uuid

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="precisa de DATABASE_URL")

TABELAS = ["post_organization_actions", "post_organizations", "acrescimos_proposta", "produtos_organizadores",
           "itens_venda", "vendas", "financeiro", "andamento_propostas", "propostas", "clientes", "produtos"]


@pytest.fixture
def contas():
    from utils.database import Database, engine
    a, b = f"iso-a-{uuid.uuid4().hex[:8]}", f"iso-b-{uuid.uuid4().hex[:8]}"
    db_a = Database(usuario_id=a)
    cliente = db_a.add_cliente(nome="Cliente da conta A", telefone="31999990000")
    proposta = db_a.add_proposta(cliente_id=cliente, descricao="Proposta da conta A", valor=1000.0, status="em_aberto")
    db_a.add_transacao(tipo="receita", descricao="Receita da conta A", valor=500.0, categoria="Serviços")
    produto = db_a.add_produto_organizador(proposta_id=proposta, nome="Caixa", descricao="", valor=10.0, quantidade=2, comodo="Closet")
    db_a.add_acrescimo_proposta(proposta_id=proposta, tipo="fornecedor", valor=50.0, descricao="Acréscimo da conta A")
    with engine.begin() as c:
        transacao = c.execute(text("SELECT id FROM financeiro WHERE usuario_id = :a"), {"a": a}).scalar()
        acrescimo = c.execute(text("SELECT id FROM acrescimos_proposta WHERE proposta_id = :p"), {"p": proposta}).scalar()
    ids = {"cliente": cliente, "proposta": proposta, "transacao": transacao, "produto": produto, "acrescimo": acrescimo}
    yield a, b, ids
    with engine.begin() as c:
        c.execute(text("DELETE FROM produtos_organizadores WHERE proposta_id = :p"), {"p": proposta})
        c.execute(text("DELETE FROM acrescimos_proposta WHERE proposta_id = :p"), {"p": proposta})
        for t in TABELAS:
            c.execute(text(f"DELETE FROM {t} WHERE usuario_id IN (:a, :b)"), {"a": a, "b": b})
        c.execute(text("DELETE FROM propostas WHERE id = :p"), {"p": proposta})
        c.execute(text("DELETE FROM clientes WHERE id = :c"), {"c": cliente})


def _dados_de_a_intactos(ids):
    from utils.database import engine
    with engine.begin() as c:
        q = lambda sql, **p: c.execute(text(sql), p).scalar()
        assert q("SELECT nome FROM clientes WHERE id = :i", i=ids["cliente"]) == "Cliente da conta A"
        assert q("SELECT descricao FROM propostas WHERE id = :i", i=ids["proposta"]) == "Proposta da conta A"
        assert q("SELECT valor FROM financeiro WHERE id = :i", i=ids["transacao"]) == 500.0
        assert q("SELECT quantidade FROM produtos_organizadores WHERE id = :i", i=ids["produto"]) == 2
        assert q("SELECT valor FROM acrescimos_proposta WHERE id = :i", i=ids["acrescimo"]) == 50.0


def test_conta_b_nao_ve_dados_de_a(contas):
    from utils.database import Database
    _, b, ids = contas
    db_b = Database(usuario_id=b)
    assert db_b.get_clientes().empty
    assert db_b.get_propostas().empty
    assert db_b.get_cliente_by_id(ids["cliente"]).empty
    assert db_b.get_produtos_organizadores(ids["proposta"]).empty
    assert db_b.get_acrescimos_proposta(ids["proposta"]).empty
    fin = db_b.get_financeiro()
    assert fin.empty or ids["transacao"] not in set(fin["id"])


def test_conta_b_nao_altera_nem_apaga_dados_de_a(contas):
    from utils.database import Database
    _, b, ids = contas
    db_b = Database(usuario_id=b)
    db_b.update_cliente(cliente_id=ids["cliente"], nome="Alterado por B")
    db_b.delete_cliente(ids["cliente"])
    db_b.update_proposta(ids["proposta"], descricao="Alterada por B")
    db_b.excluir_proposta(ids["proposta"])
    db_b.delete_transacao(ids["transacao"])
    db_b.update_produto_organizador(ids["produto"], quantidade=99)
    db_b.remove_produto_organizador(ids["produto"])
    db_b.update_acrescimo_proposta(ids["acrescimo"], valor=1.0)
    db_b.remove_acrescimo_proposta(ids["acrescimo"])
    db_b.add_produto_organizador(proposta_id=ids["proposta"], nome="Intruso", descricao="", valor=1, quantidade=1, comodo="")
    _dados_de_a_intactos(ids)


def test_api_do_app_respeita_a_conta(contas):
    from fastapi.testclient import TestClient
    import api.router as router
    _, b, ids = contas
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: b
    try:
        cli = TestClient(router.api)
        p, c = ids["proposta"], ids["cliente"]
        assert cli.get("/clientes").json() == []
        cli.put(f"/clientes/{c}", json={"nome": "Alterado pela API"})
        cli.delete(f"/clientes/{c}")
        cli.put(f"/propostas/{p}", json={"descricao": "Alterada pela API"})
        cli.delete(f"/financeiro/{ids['transacao']}")
        cli.put(f"/propostas/{p}/produtos/{ids['produto']}", json={"quantidade": 99})
        cli.delete(f"/propostas/{p}/produtos/{ids['produto']}")
        cli.put(f"/propostas/{p}/acrescimos/{ids['acrescimo']}", json={"valor": 1.0})
        cli.delete(f"/propostas/{p}/acrescimos/{ids['acrescimo']}")
        assert cli.get(f"/propostas/{p}/produtos").json() == []
        assert cli.get(f"/propostas/{p}/acrescimos").json() == []
    finally:
        router.api.dependency_overrides.clear()
    _dados_de_a_intactos(ids)
