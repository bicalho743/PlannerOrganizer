"""
PDFs da proposta pela API do app: a Proposta Comercial sai como "Proposta de Serviço", o fechamento
como "Fechamento do Serviço", os dois com o número da proposta (não o id interno) e o status legível.
A web (propostas_helper) mostra o mesmo número no cabeçalho.
"""
import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _texto(conteudo):
    import io
    from PyPDF2 import PdfReader
    return " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(conteudo)).pages)


def test_titulo_numero_e_status(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from utils.database import engine, Database
    import api.router as router
    uid = f"pdf-{uuid.uuid4().hex[:8]}"
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) VALUES (:u, :e, 'Tamara', 'pro', :d)"),
                  {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now() - timedelta(days=1)})
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: uid
    try:
        cli = TestClient(router.api)
        assert cli.post("/clientes", json={"nome": "Daniela Garcia"}).status_code == 200
        cid = cli.get("/clientes").json()[0]["id"]
        r = cli.post("/propostas", json={"cliente_id": cid, "descricao": "Organizacao", "valor": 1000})
        assert r.status_code == 200, r.text
        prop = cli.get("/propostas").json()[0]
        pid = prop["id"]
        numero = 7000 + pid  # garante número diferente do id interno
        with engine.begin() as c:
            c.execute(text("UPDATE propostas SET numero = :n WHERE id = :i"), {"n": numero, "i": pid})
        Database(usuario_id=uid).invalidar_cache()

        comercial = _texto(cli.get(f"/pdf/proposta/{pid}/comercial").content)
        assert "Proposta de Serviço" in comercial and "Fechamento" not in comercial
        assert f"#{numero}" in comercial and "Em Aberto" in comercial and "Em_aberto" not in comercial

        fechamento = _texto(cli.get(f"/pdf/proposta/{pid}/cliente").content)
        assert "Fechamento do Serviço" in fechamento and f"#{numero}" in fechamento and "Em Aberto" in fechamento

        # web: mesmo número no cabeçalho
        from utils.propostas_helper import gerar_pdf_cliente_proposta
        monkeypatch.chdir(tmp_path)
        ok, msg, arquivo = gerar_pdf_cliente_proposta(Database(usuario_id=uid), pid, tipo_documento="proposta")
        assert ok, msg
        web = _texto(open(arquivo, "rb").read())
        assert "Proposta de Serviço" in web and f"#{numero}" in web
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        router._apagar_dados_do_usuario(uid)
