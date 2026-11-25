"""
Relatório do negócio em PDF pela API (GET /pdf/relatorio), o mesmo do "Baixar PDF" da tela Relatórios do site.

Bate no PostgreSQL de DATABASE_URL; usa um usuario_id único e apaga tudo no fim.
"""
import io
import os
import uuid

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _texto(conteudo):
    from PyPDF2 import PdfReader
    return " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(conteudo)).pages)


def _limpar(engine, uid):
    with engine.connect() as c:
        for sql in ["DELETE FROM financeiro WHERE usuario_id = :u OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM propostas WHERE usuario_id = :u",
                    "DELETE FROM clientes WHERE usuario_id = :u"]:
            c.execute(text(sql), {"u": uid})
        c.commit()


def test_periodo_igual_ao_da_tela():
    from datetime import date
    from utils import relatorio_negocio as rn
    p = rn.periodo("Últimos 3 meses", "Período anterior", date(2026, 11, 25))
    assert p["ini"] == date(2026, 9, 1) and p["fim"] == date(2026, 11, 25)
    assert p["cini"] == date(2026, 6, 1) and p["rot"].startswith("set/2026 a nov/2026")
    assert rn.periodo("qualquer", "x", date(2026, 11, 25))["ini"] == date(2026, 6, 1)   # cai nos últimos 6 meses


def test_pdf_relatorio_pela_api(monkeypatch):
    from fastapi.testclient import TestClient
    from utils.database import Database, engine
    from utils.proposta_status import STATUS_EM_ABERTO
    import api.router as router

    uid = f"test-rel-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=uid)
    _limpar(engine, uid)
    cliente = db.add_cliente(nome="Marina Lopes")
    db.add_proposta(cliente_id=cliente, descricao="Organização", valor=2500.0, status=STATUS_EM_ABERTO,
                    gerar_transacoes_automaticas=False)
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    monkeypatch.setattr(router, "get_db", lambda u: Database(usuario_id=u))
    monkeypatch.setattr(router, "get_perfil_dados", lambda u: {"empresa": "Organiza Marina", "cor_principal": "#B5546A"})
    try:
        r = TestClient(router.api).get("/pdf/relatorio", params={"periodo": "Este ano"})
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"
        t = _texto(r.content)
        assert "Relatório do negócio" in t and "Organiza Marina" in t and "USO INTERNO" in t
        assert "Propostas aguardando" in t.upper() or "PROPOSTAS AGUARDANDO" in t
    finally:
        router.api.dependency_overrides.clear()
        _limpar(engine, uid)
