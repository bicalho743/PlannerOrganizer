"""Funil de vendas: eventos gravados uma vez, etapas lidas do banco e o POST /eventos do app."""
import json
import os
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


@pytest.fixture
def ambiente():
    from utils.database import engine
    from utils import funil
    funil.criar_tabela(engine)
    pre = f"fun-{uuid.uuid4().hex[:6]}"
    yield pre, engine
    with engine.begin() as c:
        c.execute(text("DELETE FROM eventos_funil WHERE usuario_id LIKE :p"), {"p": pre + "%"})
        c.execute(text("DELETE FROM perfis WHERE usuario_id LIKE :p"), {"p": pre + "%"})


def _perfil(engine, uid, dias_atras=0, plano="gratuito", onboarding=None, origem=None):
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro, onboarding, origem_cadastro) "
                       "VALUES (:u, :e, 'T', :p, :d, :o, :og)"),
                  {"u": uid, "e": f"{uid}@teste.local", "p": plano, "d": date.today() - timedelta(days=dias_atras),
                   "o": json.dumps(onboarding) if onboarding else None, "og": json.dumps(origem) if origem else None})


def test_evento_vale_uma_vez_e_so_nomes_conhecidos(ambiente):
    from utils import funil
    pre, engine = ambiente
    assert funil.registrar(engine, pre + "a", "conta_criada", "app") is True
    assert funil.registrar(engine, pre + "a", "conta_criada", "site") is False  # vale o primeiro canal
    assert funil.registrar(engine, pre + "a", "qualquer", "app") is False


def test_etapas_e_resumo(ambiente):
    from utils import funil
    pre, engine = ambiente
    _perfil(engine, pre + "1", onboarding={"respondido": True}, origem={"utm_source": "facebook", "utm_medium": "paid"})
    _perfil(engine, pre + "2", plano="pro", origem={"ref": "TAMARA"})
    _perfil(engine, pre + "3", dias_atras=90)  # fora do período
    funil.registrar(engine, pre + "1", "conta_criada", "app")
    funil.registrar(engine, pre + "1", "primeiro_pdf", "app")
    funil.registrar(engine, pre + "2", "planos_vistos", "site")
    lista = [x for x in funil.contas(engine, *funil.periodo(30)) if x["usuario_id"].startswith(pre)]
    por_uid = {x["usuario_id"]: x for x in lista}
    assert set(por_uid) == {pre + "1", pre + "2"}
    assert por_uid[pre + "1"]["onboarding"] and por_uid[pre + "1"]["pdf"] and por_uid[pre + "1"]["canal"] == "app"
    assert por_uid[pre + "1"]["origem"] == "anúncio Meta" and por_uid[pre + "2"]["origem"] == "afiliada"
    assert por_uid[pre + "2"]["assinou"] and por_uid[pre + "2"]["planos"]
    r = {k: n for k, _, n, _, _ in funil.resumo(lista)}
    assert r["cadastro"] == 2 and r["onboarding"] == 1 and r["pdf"] == 1 and r["assinou"] == 1


def test_post_eventos_do_app(ambiente):
    from fastapi.testclient import TestClient
    import api.router as router
    pre, engine = ambiente
    uid = pre + "api"
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    try:
        cli = TestClient(router.api)
        assert cli.post("/eventos", json={"nome": "planos_vistos"}).status_code == 200
        assert cli.post("/eventos", json={"nome": "primeiro_pdf"}).status_code == 400
    finally:
        router.api.dependency_overrides.clear()
    with engine.connect() as c:
        assert c.execute(text("SELECT canal FROM eventos_funil WHERE usuario_id = :u AND nome = 'planos_vistos'"),
                         {"u": uid}).scalar() == "app"
