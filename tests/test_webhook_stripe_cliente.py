"""
Webhook do Stripe: o primeiro pagamento liga a conta ao cliente do Stripe (client_reference_id) e guarda o
código do cliente; renovações e cancelamentos acham a conta por esse código, mesmo com e-mail diferente.
"""
import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


@pytest.fixture
def ambiente(monkeypatch):
    import stripe
    from fastapi.testclient import TestClient
    from utils.database import engine
    import api.router as router
    uid = f"stripe-{uuid.uuid4().hex[:8]}"
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) VALUES (:u, :e, 'T', 'gratuito', :d)"),
                  {"u": uid, "e": f"{uid}@login.local", "d": datetime.now() - timedelta(days=30)})
    eventos = []
    monkeypatch.setattr(router, "STRIPE_WEBHOOK_SECRET", "whsec_teste")
    monkeypatch.setattr(router, "STRIPE_SECRET_KEY", "")
    monkeypatch.setattr(stripe.Webhook, "construct_event",
                        lambda payload, sig, secret: stripe.Event.construct_from(eventos.pop(0), "sk_test"))

    def enviar(tipo, obj):
        eventos.append({"id": "evt_1", "object": "event", "type": tipo, "data": {"object": obj}})
        r = TestClient(router.api).post("/webhook/stripe", content=b"{}", headers={"stripe-signature": "x"})
        assert r.status_code == 200, r.text

    def perfil():
        with engine.begin() as c:
            return c.execute(text("SELECT plano, stripe_customer_id FROM perfis WHERE usuario_id = :u"), {"u": uid}).one()

    try:
        yield enviar, perfil, uid
    finally:
        router._apagar_dados_do_usuario(uid)


def test_pagou_com_outro_email_e_renovacoes_seguem_a_conta(ambiente):
    enviar, perfil, uid = ambiente
    # pagou com um e-mail diferente do login, mas pelo link com o UID da conta
    enviar("checkout.session.completed", {"object": "checkout.session", "client_reference_id": uid,
                                           "customer": "cus_ABC", "customer_email": "outro@pagamento.local"})
    assert tuple(perfil()) == ("pro", "cus_ABC")

    # cancelamento chega só com o código do cliente (o e-mail no Stripe é o outro)
    enviar("customer.subscription.updated", {"object": "subscription", "customer": "cus_ABC", "status": "canceled"})
    assert perfil()[0] == "cancelado"

    # renovação paga reativa
    enviar("invoice.paid", {"object": "invoice", "customer": "cus_ABC", "customer_email": "outro@pagamento.local"})
    assert perfil()[0] == "pro"

    enviar("customer.subscription.deleted", {"object": "subscription", "customer": "cus_ABC"})
    assert perfil()[0] == "cancelado"


def test_assinatura_antiga_achada_pelo_email_guarda_o_codigo(ambiente):
    enviar, perfil, uid = ambiente
    enviar("invoice.paid", {"object": "invoice", "customer": "cus_ANTIGO", "customer_email": f"{uid}@login.local"})
    assert tuple(perfil()) == ("pro", "cus_ANTIGO")
    # daqui em diante basta o código
    enviar("customer.subscription.deleted", {"object": "subscription", "customer": "cus_ANTIGO"})
    assert perfil()[0] == "cancelado"
