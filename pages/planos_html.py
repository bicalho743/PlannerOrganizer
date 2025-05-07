import streamlit as st
from utils.stripe_links import exibir_planos_streamlit

# Configuração da página
st.set_page_config(
    page_title="Planos HTML - Planner Organizer",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Exibir planos usando a função da utils/stripe_links.py
exibir_planos_streamlit()