"""
Aniversário da cliente: só dia e mês, guardado como "14/jun", lido do mesmo jeito em todo o sistema.
"""
import os
import uuid
from datetime import date, datetime, timedelta

import pytest

from utils.agenda import dia_mes_aniversario, normalizar_aniversario, aniversario_para_digitar


@pytest.mark.parametrize("entrada", ["1406", "14/06", "14-06", "14.06", "14 06", "14/jun", "14/Jun", "14/06/1990",
                                     "1990-06-14", date(1990, 6, 14)])
def test_formas_de_digitar(entrada):
    assert dia_mes_aniversario(entrada) == (14, 6)
    assert normalizar_aniversario(entrada) == "14/jun"
    assert aniversario_para_digitar(entrada) == "14/06"


def test_vazio_e_invalidos():
    assert normalizar_aniversario("") == "" and normalizar_aniversario(None) == ""
    for ruim in ("xx", "31/02", "31/04", "14/13", "3206", "0/05"):
        assert normalizar_aniversario(ruim) is None, ruim
    assert normalizar_aniversario("29/02") == "29/fev"


def test_inicio_entende_qualquer_formato():
    from pages.dashboard import _aniversario
    hoje = datetime(2026, 6, 10)
    for valor in ("14/jun", "14/06", "1406", "14/06/1990"):
        assert _aniversario({"data_aniversario": valor}, hoje) == datetime(2026, 6, 14), valor
    assert _aniversario({"data_aniversario": "29/fev"}, datetime(2027, 1, 5)).day == 28


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")
def test_api_guarda_dia_e_mes():
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from utils.database import engine
    import api.router as router
    uid = f"aniv-{uuid.uuid4().hex[:8]}"
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) VALUES (:u, :e, 'T', 'gratuito', :d)"),
                  {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now() - timedelta(days=1)})
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: uid
    try:
        cli = TestClient(router.api)
        assert cli.post("/clientes", json={"nome": "Ana", "data_aniversario": "1406"}).status_code == 200
        assert cli.post("/clientes", json={"nome": "Bia", "data_aniversario": "14/06/1990"}).status_code == 200
        r = cli.post("/clientes", json={"nome": "Cris", "data_aniversario": "31/02"})
        assert r.status_code == 422 and "dia e mês" in r.json()["detail"]
        lista = {c["nome"]: c["data_aniversario"] for c in cli.get("/clientes").json()}
        assert lista == {"Ana": "14/jun", "Bia": "14/jun"}
        cid = next(c["id"] for c in cli.get("/clientes").json() if c["nome"] == "Ana")
        assert cli.put(f"/clientes/{cid}", json={"nome": "Ana", "data_aniversario": "05/10"}).status_code == 200
        assert next(c for c in cli.get("/clientes").json() if c["id"] == cid)["data_aniversario"] == "05/out"
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        router._apagar_dados_do_usuario(uid)
