"""
Endpoint para receber webhooks do Stripe
Este arquivo deve ser carregado pelo Streamlit, mas não exibe uma interface de usuário.
Ele apenas processa as solicitações POST enviadas pelo Stripe para o endpoint.
"""
import os
import json
import hmac
import hashlib
import logging
import streamlit as st
from sqlalchemy.orm import Session
from utils.database import Session as DbSession
from utils.stripe_integration import processar_webhook

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chave secreta para verificar assinaturas
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

def processar_requisicao_webhook():
    """
    Processa requisições POST enviadas pelo Stripe para o endpoint de webhook
    """
    # Verifcar se é uma requisição POST
    if st.query_params.get('_method') != 'POST':
        logger.warning("Método não suportado. Apenas POST é aceito para webhooks.")
        st.stop()
        return
    
    # Obter dados do corpo da requisição
    try:
        payload = st.query_params.get('payload')
        sig_header = st.query_params.get('signature')
        
        if not payload or not sig_header:
            logger.error("Parâmetros obrigatórios não recebidos")
            st.stop()
            return
        
        # Descodificar payload se necessário
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        # Obter sessão do banco de dados
        session = DbSession()
        
        # Processar o webhook usando o módulo de integração com Stripe
        sucesso = processar_webhook(payload, sig_header, session)
        
        # Fechar a sessão do banco de dados
        session.close()
        
        return sucesso
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return False

def main():
    # Esconder elementos da UI do Streamlit
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Processar a requisição de webhook
    sucesso = processar_requisicao_webhook()
    
    # Responder com um código de status apropriado
    if sucesso:
        st.write("OK")
    else:
        st.error("Erro ao processar webhook")
        st.stop()

if __name__ == "__main__":
    main()