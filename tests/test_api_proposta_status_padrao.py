"""POST /propostas sem status cria a proposta em aberto (o padrão antigo, em_elaboracao, era recusado)."""
import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def test_proposta_sem_status_fica_em_aberto():
    from fastapi.testclient import TestClient
    from utils.database import engine
    import api.router as router
    uid = f"st-{uuid.uuid4().hex[:8]}"
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) VALUES (:u, :e, 'Ana', 'pro', :d)"),
                  {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now() - timedelta(days=1)})
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: uid
    try:
        cli = TestClient(router.api)
        assert cli.post("/clientes", json={"nome": "Bia Souza"}).status_code == 200
        cid = cli.get("/clientes").json()[0]["id"]
        r = cli.post("/propostas", json={"cliente_id": cid, "descricao": "Closet", "valor": 800})
        assert r.status_code == 200, r.text
        assert cli.get("/propostas").json()[0]["status"] == "em_aberto"
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        router._apagar_dados_do_usuario(uid)
