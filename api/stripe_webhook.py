import os
import stripe
import streamlit as st
from utils.pagamentos import GerenciadorPagamentos

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def handle_stripe_webhook():
    payload = st.request.get_data(as_text=True)
    sig_header = st.request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, st.secrets["STRIPE_WEBHOOK_SECRET"]
        )
    except ValueError as e:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        return "Invalid signature", 400

    # Handle the event
    gerenciador = GerenciadorPagamentos(st.session_state.db)
    try:
        gerenciador.webhook_handler(event)
        return "Success", 200
    except Exception as e:
        return str(e), 400
