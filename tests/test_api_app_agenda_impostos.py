"""
API do app de celular: Agenda, Impostos e modo consulta (teste grátis encerrado).

Bate no PostgreSQL de DATABASE_URL; cada execução usa contas únicas e apaga tudo no fim.
"""
import os
import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")

TABELAS = ["compromissos", "financeiro", "clientes", "perfis"]


def _limpar(engine, *uids):
    with engine.begin() as c:
        for t in TABELAS:
            c.execute(text(f"DELETE FROM {t} WHERE usuario_id = ANY(:u)"), {"u": list(uids)})


def _perfil(engine, uid, plano, cadastro):
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) "
                       "VALUES (:u, :e, 'Teste', :p, :d)"),
                  {"u": uid, "e": f"{uid}@teste.local", "p": plano, "d": cadastro})


@pytest.fixture
def api():
    from fastapi.testclient import TestClient
    from utils.database import engine
    import api.router as router
    ativa, expirada = f"app-ok-{uuid.uuid4().hex[:8]}", f"app-exp-{uuid.uuid4().hex[:8]}"
    _limpar(engine, ativa, expirada)
    _perfil(engine, ativa, "gratuito", datetime.now() - timedelta(days=2))
    _perfil(engine, expirada, "gratuito", datetime.now() - timedelta(days=30))
    conta = {"uid": ativa}
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: conta["uid"]
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: conta["uid"]
    try:
        yield TestClient(router.api), conta, ativa, expirada
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        _limpar(engine, ativa, expirada)


def test_compromisso_com_valor_entra_na_agenda_e_no_financeiro(api):
    cli, conta, ativa, _ = api
    assert cli.post("/clientes", json={"nome": "Organizer Ana", "telefone": "31999990000",
                                       "data_aniversario": date.today().strftime("%d/%m")}).status_code == 200
    cid = cli.get("/clientes").json()[0]["id"]
    hoje = date.today()
    r = cli.post("/compromissos", json={"data": hoje.isoformat(), "titulo": "Diária", "hora": "09:00",
                                        "cliente_id": cid, "valor": 350})
    assert r.status_code == 200, r.text
    comp_id = r.json()["id"]

    ag = cli.get("/agenda", params={"inicio": hoje.isoformat(), "fim": hoje.isoformat()}).json()
    tipos = [i["tipo"] for i in ag["itens"]]
    assert "compromisso" in tipos and "aniversario" in tipos
    aniv = next(i for i in ag["itens"] if i["tipo"] == "aniversario")
    assert aniv["whatsapp"].startswith("https://wa.me/55")
    comp = next(i for i in ag["itens"] if i["tipo"] == "compromisso")
    assert comp["situacao"] == "a receber" and comp["valor"] == 350 and comp["compromisso_id"] == comp_id
    assert ag["entra"] == 350
    assert ag["compromissos"][0]["cliente_id"] == cid and ag["compromissos"][0]["cliente_nome"] == "Organizer Ana"
    assert "Organizer Ana" in comp["detalhe"]

    assert cli.post(f"/compromissos/{comp_id}/recebido").status_code == 200
    ag = cli.get("/agenda", params={"inicio": hoje.isoformat(), "fim": hoje.isoformat()}).json()
    assert next(i for i in ag["itens"] if i["tipo"] == "compromisso")["situacao"] == "recebido"
    assert cli.post(f"/compromissos/{comp_id}/recebido").status_code == 409

    r = cli.put(f"/compromissos/{comp_id}", json={"data": hoje.isoformat(), "titulo": "Diária longa", "valor": 350})
    assert r.status_code == 200
    assert cli.delete(f"/compromissos/{comp_id}").status_code == 200
    assert cli.delete(f"/compromissos/{comp_id}").status_code == 404


def test_validacoes_da_agenda(api):
    cli, *_ = api
    assert cli.get("/agenda", params={"inicio": "2026-01-01", "fim": "2026-06-01"}).status_code == 422
    assert cli.get("/agenda", params={"inicio": "ontem", "fim": "2026-06-01"}).status_code == 422
    assert cli.post("/compromissos", json={"data": "2026-10-10", "titulo": "  "}).status_code == 422
    assert cli.post("/compromissos", json={"data": "2026-10-10", "titulo": "X", "hora": "9h"}).status_code == 422
    assert cli.post("/compromissos", json={"data": "2026-10-10", "titulo": "X", "cliente_id": 999999999}).status_code == 404


def test_impostos_mei_simples_e_outro(api):
    cli, *_ = api
    r = cli.get("/impostos").json()
    assert r["regime"] == "MEI" and "não é contador" in r["aviso"]
    assert len(r["mei"]["meses"]) == 12 and r["mei"]["limite"] == 81000

    hoje = date.today()
    mes_passado = (hoje.replace(day=1) - timedelta(days=1))
    assert cli.post("/impostos/das", json={"ano": mes_passado.year, "mes": mes_passado.month, "valor": 86.05,
                                           "pago_em": hoje.isoformat()}).status_code == 200
    if mes_passado.year == hoje.year:
        meses = cli.get("/impostos").json()["mei"]["meses"]
        assert meses[mes_passado.month - 1]["situacao"] == "pago"

    assert cli.put("/impostos/regime", json={"regime": "Simples Nacional", "aliquota": 6.5}).status_code == 200
    r = cli.get("/impostos").json()
    assert r["regime"] == "Simples Nacional" and abs(r["simples"]["aliquota"] - 0.065) < 1e-9
    assert len(r["simples"]["meses"]) == 12

    assert cli.put("/impostos/regime", json={"regime": "Outro"}).status_code == 200
    r = cli.get("/impostos").json()
    assert r["regime"] == "Outro" and len(r["outro"]["meses"]) == hoje.month

    assert cli.put("/impostos/regime", json={"regime": "Lucro Real"}).status_code == 422
    assert cli.get("/impostos", params={"ano": hoje.year - 5}).status_code == 422


def test_modo_consulta_le_mas_nao_grava(api):
    cli, conta, ativa, expirada = api
    assert cli.get("/perfil").json()["modo_consulta"] is False
    conta["uid"] = expirada
    perfil = cli.get("/perfil").json()
    assert perfil["modo_consulta"] is True and perfil["dias_restantes_trial"] == 0
    assert cli.get("/clientes").status_code == 200
    assert cli.get("/agenda", params={"inicio": date.today().isoformat(), "fim": date.today().isoformat()}).status_code == 200
    r = cli.post("/clientes", json={"nome": "Não pode"})
    assert r.status_code == 402 and r.json()["codigo"] == "modo_consulta"
    assert cli.post("/compromissos", json={"data": "2026-10-10", "titulo": "X"}).status_code == 402
    assert cli.delete("/financeiro/1").status_code == 402
    assert cli.get("/pdf/proposta/1/cliente").status_code == 402
    # perfil e tipo de empresa continuam liberados, como na web
    assert cli.put("/impostos/regime", json={"regime": "Outro"}).status_code == 200
    assert cli.get("/clientes").json() == []


def test_inicio_como_na_web(api):
    cli, conta, ativa, _ = api
    assert cli.post("/clientes", json={"nome": "Bia Souza", "telefone": "31988887777",
                                       "data_aniversario": date.today().strftime("%d/") + ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][date.today().month - 1]}).status_code == 200
    assert cli.post("/financeiro", json={"tipo": "receita", "descricao": "Diária", "valor": 300, "categoria": "serviço"}).status_code == 200
    r = cli.get("/inicio")
    assert r.status_code == 200, r.text
    d = r.json()
    assert set(d["kpis"]) >= {"lucro", "a_receber", "a_pagar", "conversao", "mes"}
    assert d["kpis"]["a_receber"] >= 300
    niver = [i for i in d["para_fazer"] if i["tipo"] == "aniversario"]
    assert niver and niver[0]["titulo"] == "Bia Souza" and niver[0]["quando"] == "hoje"
    assert niver[0]["whatsapp"].startswith("https://wa.me/55")
    assert d["aniversariantes_mes"][0]["nome"] == "Bia Souza"
