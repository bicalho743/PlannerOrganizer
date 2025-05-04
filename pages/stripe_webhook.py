"""
Endpoint para receber webhooks do Stripe
Este endpoint permite ao Stripe notificar o sistema sobre eventos como pagamentos, atualizações de assinatura, etc.
"""
import os
import json
import hmac
import hashlib
import logging
from datetime import datetime

import streamlit as st
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.stripe_integration import processar_webhook

# Configuração da página sem elementos visuais
st.set_page_config(
    page_title="Stripe Webhook",
    page_icon="🔔",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Ocultar todos os elementos
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    #stDecoration {display:none;}
    .main {padding-top: 0; padding-bottom: 0;}
    header {display:none;}
    [data-testid="stSidebar"] {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Configurar logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def main():
    # Verificar método da requisição
    request_method = os.environ.get('REQUEST_METHOD', 'GET')
    
    if request_method == 'POST':
        # Obter dados da requisição
        try:
            payload = st.runtime.scriptrunner.get_script_run_ctx().form_data_proxy.get_body()
            sig_header = os.environ.get('HTTP_STRIPE_SIGNATURE', '')
            
            if not payload or not sig_header:
                st.json({"status": "error", "message": "Dados de webhook ausentes"})
                logger.error("Dados de webhook ausentes")
                return
            
            # Processar webhook
            resultado = processar_webhook(payload, sig_header)
            
            # Responder com resultado
            st.json(resultado)
            
            # Registrar processamento
            logger.info(f"Webhook processado: {resultado}")
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
            st.json({"status": "error", "message": str(e)})
    else:
        # Método não suportado
        st.json({"status": "error", "message": "Método não suportado"})
        logger.warning(f"Método não suportado: {request_method}")
        
    # Retornar status code 200 para todas as requisições
    # Isso é importante para o Stripe não reenviar eventos
    os.environ['SCRIPT_RETURN_CODE'] = '200'

if __name__ == "__main__":
    main()