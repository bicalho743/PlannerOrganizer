import streamlit as st
import os

# URL base para API
API_HOST = os.environ.get('API_HOST', 'http://localhost:8000')

# Configurações da página
st.set_page_config(
    page_title="Planner Organizer - Planos e Assinaturas",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Remover marcas do Streamlit
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Título da página
st.title("Planos e Assinaturas")

# Espaço para os botões de assinatura (simples)
st.markdown("### Escolha um plano para começar")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("ASSINAR MENSAL", type="primary", key="btn_mensal"):
        api_url = f"{API_HOST}/api/checkout/mensal"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

with col2:
    if st.button("ASSINAR ANUAL", type="primary", key="btn_anual"):
        api_url = f"{API_HOST}/api/checkout/anual"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

with col3:
    if st.button("PLANO VITALÍCIO", type="primary", key="btn_vitalicio"):
        api_url = f"{API_HOST}/api/checkout/vitalicio"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{api_url}\'">', unsafe_allow_html=True)
        st.success("✅ Redirecionando para checkout...")

# Opção para período gratuito
st.markdown("### Não está pronto para assinar?")
if st.button("INICIAR PERÍODO GRATUITO", type="secondary"):
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'/api/iniciar_teste\'">', unsafe_allow_html=True)
    st.info("✅ Iniciando período de teste gratuito...")