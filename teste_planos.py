import streamlit as st
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("Iniciando teste simplificado")

# Configuração da página
st.set_page_config(
    page_title="Teste Planos",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Conteúdo básico
st.title("Página de Teste")
st.markdown("### Esta é uma página de teste para identificar problemas")

# Mostrar uma mensagem simples
st.success("Se você consegue ver esta mensagem, a aplicação está funcionando corretamente.")

# Log final
logger.info("Teste finalizado")