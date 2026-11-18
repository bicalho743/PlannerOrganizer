"""
Onboarding (app e web): respostas guardadas em perfis.onboarding, juntadas a cada gravação,
e só os campos conhecidos aceitos pela API. Bate no PostgreSQL de DATABASE_URL.
"""
import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


@pytest.fixture
def api():
    from fastapi.testclient import TestClient
    from utils.database import engine
    import api.router as router
    uid = f"onb-{uuid.uuid4().hex[:8]}"
    with engine.begin() as c:
        c.execute(text("ALTER TABLE perfis ADD COLUMN IF NOT EXISTS onboarding TEXT"))
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) "
                       "VALUES (:u, :e, 'Teste', 'gratuito', :d)"),
                  {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now()})
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    try:
        yield TestClient(router.api), uid
    finally:
        router.api.dependency_overrides.clear()
        with engine.begin() as c:
            c.execute(text("DELETE FROM perfis WHERE usuario_id = :u"), {"u": uid})


def test_vazio_grava_junta_e_filtra(api):
    cli, uid = api
    assert cli.get("/onboarding").json() == {}
    r = cli.put("/onboarding", json={"dores": ["cobrar", "retornos"], "formal": "mei", "passos": "ativo",
                                     "plano": "pro"})
    assert r.status_code == 200
    assert cli.put("/onboarding", json={"passos": "fechado"}).status_code == 200
    dados = cli.get("/onboarding").json()
    assert dados == {"dores": ["cobrar", "retornos"], "formal": "mei", "passos": "fechado"}


def test_sem_perfil_responde_404(api):
    cli, uid = api
    import api.router as router
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: f"sem-{uuid.uuid4().hex[:6]}"
    assert cli.put("/onboarding", json={"passos": "ativo"}).status_code == 404
