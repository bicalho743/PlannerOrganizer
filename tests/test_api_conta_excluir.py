"""
API do app: exclusão da conta (exigência da App Store e promessa da política de privacidade).

Bate no PostgreSQL de DATABASE_URL; cada execução usa contas únicas e apaga tudo no fim.
"""
import os
import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _tabelas(engine):
    with engine.begin() as c:
        return [r[0] for r in c.execute(text(
            "SELECT table_name FROM information_schema.columns "
            "WHERE column_name = 'usuario_id' AND table_schema = 'public'"))]


def _contar(engine, uid):
    total = 0
    with engine.begin() as c:
        for t in _tabelas(engine):
            total += c.execute(text(f'SELECT COUNT(*) FROM "{t}" WHERE usuario_id = :u'), {"u": uid}).scalar()
    return total


def _limpar(engine, *uids):
    import api.router as router
    for uid in uids:
        try:
            router._apagar_dados_do_usuario(uid)
        except Exception:
            pass


@pytest.fixture
def api():
    from fastapi.testclient import TestClient
    from utils.database import engine
    import api.router as router
    sai, fica = f"del-{uuid.uuid4().hex[:8]}", f"fica-{uuid.uuid4().hex[:8]}"
    _limpar(engine, sai, fica)
    with engine.begin() as c:
        for uid, dias in ((sai, 30), (fica, 2)):  # a conta que sai está em modo consulta
            c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) "
                           "VALUES (:u, :e, 'Teste', 'gratuito', :d)"),
                      {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now() - timedelta(days=dias)})
    conta = {"uid": fica}
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: conta["uid"]
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: conta["uid"]
    try:
        yield TestClient(router.api), conta, sai, fica, engine
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        _limpar(engine, sai, fica)


def _popular(cli, conta, uid):
    """Cria dados em várias tabelas com a conta ativa e depois os passa para uid."""
    conta["uid"] = uid
    from utils.database import engine
    with engine.begin() as c:  # libera a gravação: a conta precisa estar no teste grátis
        c.execute(text("UPDATE perfis SET data_cadastro = :d WHERE usuario_id = :u"),
                  {"d": datetime.now() - timedelta(days=1), "u": uid})
    assert cli.post("/clientes", json={"nome": "Cliente que sai", "telefone": "31999990000"}).status_code == 200
    cid = cli.get("/clientes").json()[0]["id"]
    assert cli.post("/compromissos", json={"data": date.today().isoformat(), "titulo": "Visita",
                                           "cliente_id": cid, "valor": 200}).status_code == 200
    assert cli.post("/financeiro", json={"tipo": "receita", "descricao": "Diária", "valor": 300,
                                         "categoria": "serviço"}).status_code == 200


def test_exclui_tudo_da_conta_e_nada_das_outras(api):
    cli, conta, sai, fica, engine = api
    _popular(cli, conta, fica)
    _popular(cli, conta, sai)
    with engine.begin() as c:  # volta a conta que sai para o modo consulta: excluir continua liberado
        c.execute(text("UPDATE perfis SET data_cadastro = :d WHERE usuario_id = :u"),
                  {"d": datetime.now() - timedelta(days=30), "u": sai})
    antes_fica = _contar(engine, fica)
    assert _contar(engine, sai) >= 4 and antes_fica >= 4

    conta["uid"] = sai
    assert cli.post("/conta/excluir", json={"confirmacao": "sim"}).status_code == 422
    assert _contar(engine, sai) > 0
    r = cli.post("/conta/excluir", json={"confirmacao": "excluir"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True and r.json()["assinaturas_canceladas"] == 0
    assert _contar(engine, sai) == 0
    assert _contar(engine, fica) == antes_fica
