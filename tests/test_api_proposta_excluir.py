"""
DELETE /propostas/{id} (app): apaga a proposta e os lançamentos ligados a ela; não apaga proposta de outra conta.

Bate no PostgreSQL de DATABASE_URL; usa usuario_id únicos e apaga tudo no fim.
"""
import os
import uuid

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _limpar(engine, uid):
    with engine.connect() as c:
        for sql in ["DELETE FROM financeiro WHERE usuario_id = :u OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM propostas WHERE usuario_id = :u",
                    "DELETE FROM clientes WHERE usuario_id = :u"]:
            c.execute(text(sql), {"u": uid})
        c.commit()


def _conta(engine, sql, pid):
    with engine.connect() as c:
        return c.execute(text(sql), {"p": pid}).scalar()


def test_excluir_proposta(monkeypatch):
    from fastapi.testclient import TestClient
    from utils.database import Database, engine
    from utils.proposta_status import STATUS_EM_ABERTO, STATUS_APROVADA
    import api.router as router

    dona, outra = (f"test-del-{uuid.uuid4().hex[:12]}" for _ in range(2))
    db = Database(usuario_id=dona)
    for u in (dona, outra):
        _limpar(engine, u)
    cliente = db.add_cliente(nome="Cliente Excluir")
    pid = db.add_proposta(cliente_id=cliente, descricao="Organização", valor=1500.0,
                          status=STATUS_EM_ABERTO, gerar_transacoes_automaticas=False)
    db.update_proposta(pid, sinal=300.0)
    db.update_proposta_status(proposta_id=pid, novo_status=STATUS_APROVADA)
    db.sincronizar_sinal_proposta(pid)

    usuario = {"uid": outra}
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: usuario["uid"]
    monkeypatch.setattr(router, "get_db", lambda u: Database(usuario_id=u))
    try:
        cli = TestClient(router.api)
        # outra conta não consegue apagar
        assert cli.delete(f"/propostas/{pid}").status_code == 404
        assert _conta(engine, "SELECT count(*) FROM propostas WHERE id = :p", pid) == 1

        assert _conta(engine, "SELECT count(*) FROM financeiro WHERE proposta_id = :p", pid) > 0

        usuario["uid"] = dona
        r = cli.delete(f"/propostas/{pid}")
        assert r.status_code == 200, r.text
        assert _conta(engine, "SELECT count(*) FROM propostas WHERE id = :p", pid) == 0
        assert _conta(engine, "SELECT count(*) FROM financeiro WHERE proposta_id = :p", pid) == 0
        assert all(p["id"] != pid for p in cli.get("/propostas").json())
        assert cli.delete(f"/propostas/{pid}").status_code == 404
    finally:
        router.api.dependency_overrides.clear()
        for u in (dona, outra):
            _limpar(engine, u)
