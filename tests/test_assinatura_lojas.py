"""
Assinatura pelas lojas (RevenueCat) convivendo com a do site (Stripe): a conta tem um plano só,
cada canal só tira o acesso que ele mesmo deu, e o app libera na hora depois de comprar.
"""
import os
import uuid
from datetime import datetime, timedelta

import pytest
import stripe
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="precisa de DATABASE_URL")


@pytest.fixture
def ambiente(monkeypatch):
    from fastapi.testclient import TestClient
    import api.router as router
    import utils.assinatura as assinatura
    from utils.database import engine

    uid = f"loja-{uuid.uuid4().hex[:8]}"
    email = f"{uid}@teste.local"
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, ativo, data_cadastro) "
                       "VALUES (:u, :e, 'Teste Loja', 'gratuito', TRUE, :d)"),
                  {"u": uid, "e": email, "d": datetime.now() - timedelta(days=30)})
    monkeypatch.setenv("REVENUECAT_WEBHOOK_AUTH", "segredo-rc")
    monkeypatch.setattr(router, "STRIPE_WEBHOOK_SECRET", "whsec_teste")
    monkeypatch.setattr(router, "STRIPE_SECRET_KEY", "")
    evento = {}
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: evento["e"])
    router.api.dependency_overrides[router.verify_firebase_token] = lambda: uid
    original = router._uid_da_requisicao
    router._uid_da_requisicao = lambda request: uid
    cli = TestClient(router.api)

    def plano():
        with engine.begin() as c:
            return tuple(c.execute(text("SELECT plano, assinatura_origem FROM perfis WHERE usuario_id = :u"),
                                   {"u": uid}).fetchone())

    def rc(tipo, store="PLAY_STORE", **extra):
        corpo = {"event": {"type": tipo, "app_user_id": uid, "store": store, "entitlement_ids": ["pro"],
                           "expiration_at_ms": int((datetime.now() + timedelta(days=30)).timestamp() * 1000), **extra}}
        r = cli.post("/webhook/revenuecat", json=corpo, headers={"Authorization": "Bearer segredo-rc"})
        assert r.status_code == 200, r.text
        return plano()

    def stripe_evento(tipo, objeto):
        evento["e"] = stripe.StripeObject.construct_from({"type": tipo, "data": {"object": objeto}}, "sk_teste")
        assert cli.post("/webhook/stripe", content=b"{}", headers={"stripe-signature": "t=1,v1=x"}).status_code == 200
        return plano()

    try:
        yield cli, uid, email, rc, stripe_evento, plano, assinatura, monkeypatch
    finally:
        router.api.dependency_overrides.clear()
        router._uid_da_requisicao = original
        router._apagar_dados_do_usuario(uid)


def test_webhook_exige_segredo(ambiente):
    cli = ambiente[0]
    assert cli.post("/webhook/revenuecat", json={"event": {"type": "TEST"}}).status_code == 401
    assert cli.post("/webhook/revenuecat", json={"event": {"type": "TEST"}},
                    headers={"Authorization": "segredo-rc"}).json() == {"status": "teste"}


def test_compra_no_android_libera_e_vencimento_bloqueia(ambiente):
    cli, uid, _, rc, _, plano, *_ = ambiente
    assert cli.post("/clientes", json={"nome": "Bia"}).status_code == 402  # teste grátis acabou
    assert rc("INITIAL_PURCHASE") == ("pro", "google")
    assert cli.post("/clientes", json={"nome": "Bia"}).status_code == 200
    perfil = cli.get("/perfil").json()
    assert perfil["assinatura_origem"] == "google" and perfil["modo_consulta"] is False
    assert rc("CANCELLATION") == ("pro", "google")  # cancelou: usa até o fim do período
    assert rc("BILLING_ISSUE") == ("pro", "google")  # cartão recusado: a loja tenta de novo
    assert rc("EXPIRATION") == ("cancelado", "google")
    assert rc("RENEWAL", store="APP_STORE") == ("pro", "apple")


def test_um_canal_nao_derruba_o_outro(ambiente):
    _, uid, email, rc, stripe_evento, *_ = ambiente
    # assinou no site e depois passou a pagar pelo iPhone
    assert stripe_evento("checkout.session.completed", {"client_reference_id": uid, "customer": "cus_x"}) == ("pro", "stripe")
    assert rc("INITIAL_PURCHASE", store="APP_STORE") == ("pro", "apple")
    # o fim da assinatura antiga do site não tira o acesso
    assert stripe_evento("customer.subscription.deleted", {"customer": "cus_x"}) == ("pro", "apple")
    # vencimento de outra loja também não
    assert rc("EXPIRATION", store="PLAY_STORE") == ("pro", "apple")
    # compra feita no site e repassada pelo RevenueCat é ignorada aqui (o Stripe cuida)
    assert rc("EXPIRATION", store="STRIPE") == ("pro", "apple")


def test_sincronizar_depois_da_compra(ambiente):
    cli, uid, _, _, _, plano, assinatura, monkeypatch = ambiente
    assert cli.post("/assinatura/sincronizar").json()["pro"] is None  # sem chave: não mexe
    monkeypatch.setenv("REVENUECAT_SECRET_KEY", "sk_teste")
    vence = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    resposta = {"subscriber": {"entitlements": {"pro": {"expires_date": vence, "product_identifier": "anual"}},
                               "subscriptions": {"anual": {"store": "play_store", "expires_date": vence}}}}

    class R:
        status_code = 200
        def json(self):
            return resposta
    monkeypatch.setattr(assinatura.requests, "get", lambda *a, **k: R())
    assert cli.post("/assinatura/sincronizar").json() == {"pro": True, "origem": "google"}
    assert plano() == ("pro", "google")
    resposta["subscriber"]["entitlements"] = {}  # reembolsada / vencida
    assert cli.post("/assinatura/sincronizar").json()["pro"] is False
    assert plano() == ("cancelado", "google")
