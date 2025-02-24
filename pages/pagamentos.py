
import streamlit as st
import mercadopago
from datetime import datetime

def show():
    st.title("💳 Pagamentos")
    
    if 'MERCADOPAGO_ACCESS_TOKEN' not in st.secrets:
        st.error("Configure o token do Mercado Pago nas secrets do Replit")
        return
        
    sdk = mercadopago.SDK(st.secrets.MERCADOPAGO_ACCESS_TOKEN)
    
    with st.form("criar_pagamento"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
        
        if st.form_submit_button("Gerar Link de Pagamento"):
            preference_data = {
                "items": [
                    {
                        "title": descricao,
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": float(valor)
                    }
                ],
                "back_urls": {
                    "success": f"https://{st.secrets.REPL_SLUG}.repl.co/success",
                    "failure": f"https://{st.secrets.REPL_SLUG}.repl.co/failure"
                }
            }
            
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            
            st.success("Link de pagamento gerado!")
            st.markdown(f"[Clique aqui para pagar]({preference['init_point']})")
