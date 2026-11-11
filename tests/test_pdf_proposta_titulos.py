"""
PDFs da proposta: a Proposta Comercial do app sai como "Proposta de Serviço" (igual à web), o fechamento
como "Fechamento do Serviço", e todos mostram o número da proposta (não o id interno) e o status legível.

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


def test_titulo_numero_e_status(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from utils.database import Database, engine
    from utils.proposta_status import STATUS_EM_ABERTO
    import api.router as router

    uid = f"test-pdf-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=uid)
    _limpar(engine, uid)
    cliente = db.add_cliente(nome="Daniela Garcia")
    pid = db.add_proposta(cliente_id=cliente, descricao="Organização", valor=1000.0,
                          status=STATUS_EM_ABERTO, gerar_transacoes_automaticas=False)
    numero = 7000 + int(pid)  # número diferente do id interno, como no caso #344 x #345
    with engine.begin() as c:
        c.execute(text("UPDATE propostas SET numero = :n WHERE id = :i"), {"n": numero, "i": pid})

    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    monkeypatch.setattr(router, "get_db", lambda u: Database(usuario_id=u))
    monkeypatch.setattr(router, "get_perfil_dados", lambda u: {})
    try:
        cli = TestClient(router.api)

        r = cli.get(f"/pdf/proposta/{pid}/comercial")
        assert r.status_code == 200, r.text
        comercial = _texto(r.content)
        assert "Proposta de Serviço" in comercial and "Fechamento" not in comercial
        assert f"#{numero}" in comercial and "Em Aberto" in comercial and "Em_aberto" not in comercial

        r = cli.get(f"/pdf/proposta/{pid}/cliente")
        assert r.status_code == 200, r.text
        fechamento = _texto(r.content)
        assert "Fechamento do Serviço" in fechamento and f"#{numero}" in fechamento and "Em Aberto" in fechamento

        # web: mesmo título e mesmo número no cabeçalho
        from utils.propostas_helper import gerar_pdf_cliente_proposta
        monkeypatch.chdir(tmp_path)
        ok, msg, arquivo = gerar_pdf_cliente_proposta(Database(usuario_id=uid), pid, tipo_documento="proposta")
        assert ok, msg
        web = _texto(open(arquivo, "rb").read())
        assert "Proposta de Serviço" in web and f"#{numero}" in web and f"#{pid} " not in web
    finally:
        router.api.dependency_overrides.clear()
        _limpar(engine, uid)
