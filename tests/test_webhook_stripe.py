"""
Webhook do Stripe (api/router.py): o plano da conta acompanha a assinatura.

O evento é montado como o Stripe envia (StripeObject) e a verificação de assinatura
é substituída; o banco é o de dev (DATABASE_URL), com um perfil de teste criado e
apagado aqui.
"""
import os
import uuid

import pytest
import stripe
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="precisa de DATABASE_URL")


@pytest.fixture
def ambiente(monkeypatch):
    from fastapi.testclient import TestClient
    import api.router as router
    from utils.database import engine

    email = f"webhook-{uuid.uuid4().hex[:8]}@teste.local"
    uid = f"uid-{uuid.uuid4().hex[:8]}"
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, ativo, data_cadastro) "
                       "VALUES (:u, :e, 'Teste Webhook', 'gratuito', TRUE, CURRENT_DATE)"), {"u": uid, "e": email})
    monkeypatch.setattr(router, "STRIPE_WEBHOOK_SECRET", "whsec_teste")
    monkeypatch.setattr(router, "STRIPE_SECRET_KEY", "")
    evento = {}
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: evento["e"])
    cliente = TestClient(router.api)

    def enviar(tipo, objeto):
        evento["e"] = stripe.StripeObject.construct_from({"type": tipo, "data": {"object": objeto}}, "sk_teste")
        r = cliente.post("/webhook/stripe", content=b"{}", headers={"stripe-signature": "t=1,v1=x"})
        assert r.status_code == 200, r.text
        with engine.begin() as c:
            return c.execute(text("SELECT plano FROM perfis WHERE usuario_id = :u"), {"u": uid}).scalar()

    yield enviar, uid, email
    with engine.begin() as c:
        c.execute(text("DELETE FROM perfis WHERE usuario_id = :u"), {"u": uid})


def test_pagamento_ativa_pelo_uid(ambiente):
    enviar, uid, _ = ambiente
    assert enviar("checkout.session.completed", {"client_reference_id": uid, "customer_email": "outro@x.com"}) == "pro"


def test_assinatura_sem_pagamento_bloqueia_e_renovacao_reativa(ambiente):
    enviar, uid, email = ambiente
    enviar("checkout.session.completed", {"client_reference_id": uid})
    assert enviar("customer.subscription.updated", {"status": "past_due", "customer_email": email}) == "pro"
    assert enviar("customer.subscription.updated", {"status": "unpaid", "customer_email": email}) == "cancelado"
    assert enviar("invoice.paid", {"customer_email": email}) == "pro"
