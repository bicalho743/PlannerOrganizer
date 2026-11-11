"""
Aviso da manhã no celular: o app registra o token, a tarefa diária monta o Para fazer de cada conta
e manda um resumo pelo Expo Push (aqui o envio é simulado). Sem nada para hoje, não manda nada.
"""
import os
import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


@pytest.fixture
def ambiente(monkeypatch):
    from fastapi.testclient import TestClient
    from utils.database import engine
    import api.router as router
    com, sem = f"push-a-{uuid.uuid4().hex[:6]}", f"push-b-{uuid.uuid4().hex[:6]}"
    with engine.begin() as c:
        for uid in (com, sem):
            c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) VALUES (:u, :e, 'Ana Lima', 'pro', :d)"),
                      {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now() - timedelta(days=1)})
    conta = {"uid": com}
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: conta["uid"]
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: conta["uid"]
    enviados = []

    class Resposta:
        ok, status_code, text = True, 200, ""

        def __init__(self, lote):
            self.lote = lote

        def json(self):
            return {"data": [{"status": "error", "details": {"error": "DeviceNotRegistered"}}
                             if "MORTO" in m["to"] else {"status": "ok"} for m in self.lote]}

    def post(url, json=None, **k):
        enviados.extend(json)
        return Resposta(json)
    monkeypatch.setattr(router.requests, "post", post)
    monkeypatch.setenv("TAREFAS_CHAVE", "chave-teste")
    try:
        yield TestClient(router.api), conta, com, sem, enviados, engine
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        for uid in (com, sem):
            router._apagar_dados_do_usuario(uid)


def test_resumo_da_manha(ambiente):
    cli, conta, com, sem, enviados, engine = ambiente
    hoje = date.today()
    # conta com aniversário de cliente hoje e dois celulares (um já desinstalado)
    assert cli.post("/clientes", json={"nome": "Fernanda Rocha", "data_aniversario": f"{hoje.day:02d}/{hoje.month:02d}"}).status_code == 200
    assert cli.post("/push/token", json={"token": "ExponentPushToken[BOM]", "plataforma": "ios"}).status_code == 200
    assert cli.post("/push/token", json={"token": "ExponentPushToken[MORTO]", "plataforma": "android"}).status_code == 200
    assert cli.post("/push/token", json={"token": "qualquer-coisa"}).status_code == 422
    # conta sem nada para hoje
    conta["uid"] = sem
    assert cli.post("/push/token", json={"token": "ExponentPushToken[SEM]", "plataforma": "android"}).status_code == 200

    assert cli.post("/tarefas/lembretes-diarios").status_code == 401
    r = cli.post("/tarefas/lembretes-diarios", headers={"X-Tarefa-Chave": "chave-teste"})
    assert r.status_code == 200, r.text
    meus = [m for m in enviados if m["to"] in ("ExponentPushToken[BOM]", "ExponentPushToken[MORTO]")]
    assert len(meus) == 2 and not any(m["to"] == "ExponentPushToken[SEM]" for m in enviados)
    assert meus[0]["title"] == "Bom dia, Ana! Hoje no Planner"
    assert meus[0]["body"] == "Aniversário de Fernanda."
    assert meus[0]["data"] == {"tipo": "resumo_dia", "tela": "/"}  # o toque abre o Início

    # chamada repetida no mesmo dia (tentativa do GitHub Actions): ninguém recebe de novo
    antes = len(enviados)
    r = cli.post("/tarefas/lembretes-diarios", headers={"X-Tarefa-Chave": "chave-teste"})
    assert r.status_code == 200 and len(enviados) == antes
    # no dia seguinte volta a mandar
    with engine.begin() as c:
        c.execute(text("UPDATE push_tokens SET ultimo_resumo = :d WHERE usuario_id = :a"),
                  {"a": com, "d": date(2000, 1, 1)})
    cli.post("/tarefas/lembretes-diarios", headers={"X-Tarefa-Chave": "chave-teste"})
    assert [m["to"] for m in enviados[antes:]] == ["ExponentPushToken[BOM]"]
    with engine.begin() as c:
        tokens = {t for (t,) in c.execute(text("SELECT token FROM push_tokens WHERE usuario_id IN (:a, :b)"), {"a": com, "b": sem})}
    assert tokens == {"ExponentPushToken[BOM]", "ExponentPushToken[SEM]"}  # o desinstalado saiu

    # ao sair da conta o celular deixa de receber
    assert cli.post("/push/remover", json={"token": "ExponentPushToken[SEM]"}).status_code == 200
    with engine.begin() as c:
        assert c.execute(text("SELECT COUNT(*) FROM push_tokens WHERE token = 'ExponentPushToken[SEM]'")).scalar() == 0


def test_texto_do_resumo():
    from api.router import _resumo_do_dia
    assert _resumo_do_dia({"para_fazer": []}) is None
    itens = [{"tipo": "pos", "atrasado": True, "quando": "venceu ontem"},
             {"tipo": "pos", "atrasado": False, "quando": "hoje"},
             {"tipo": "pos", "atrasado": False, "quando": "amanhã"},
             {"tipo": "receber", "atrasado": True, "quando": "venceu há 3 dias"},
             {"tipo": "aniversario", "titulo": "Bia Souza", "quando": "hoje"},
             {"tipo": "aniversario", "titulo": "Carla Dias", "quando": "em 3 dias"}]
    titulo, texto = _resumo_do_dia({"nome": "", "para_fazer": itens})
    assert titulo == "Bom dia! Hoje no Planner"
    assert texto == "Aniversário de Bia, 2 retornos de cliente e 1 valor a receber."
