import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path para importar módulos personalizados
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.planos import mostrar_planos

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Planos",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remover o menu hamburguer e rodapé
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilos adicionais para a landing page */
    body {
        background: linear-gradient(135deg, #f9fafc, #eef5ff);
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Poppins', sans-serif;
    }
    
    .header-container {
        text-align: center;
        background: linear-gradient(135deg, #1E366F, #2D8CFF);
        padding: 3rem 1rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2.5rem;
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .header-subtitle {
        font-size: 1.5rem;
        font-weight: 300;
        max-width: 600px;
        margin: 0 auto;
        opacity: 0.9;
    }
    
    .contact-container {
        text-align: center;
        margin-top: 3rem;
        padding: 2rem;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
    
    .contact-title {
        color: #1E366F;
        margin-bottom: 1rem;
    }
    
    .contact-email {
        color: #1976D2;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .contact-email:hover {
        color: #2D8CFF;
        text-decoration: underline;
    }
    
    .footer-text {
        margin-top: 1.5rem;
        font-size: 0.9rem;
        color: #888;
    }
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Cabeçalho principal com logo e slogan
st.markdown("""
<div class="header-container">
    <h1 class="header-title">Planner Organizer</h1>
    <p class="header-subtitle">Transforme sua organização em resultados mensuráveis</p>
</div>
""", unsafe_allow_html=True)

# Mostrar a seção completa de planos usando o módulo otimizado
mostrar_planos(
    com_titulo=True,
    com_prova_social=True,
    com_teste_gratis=True,
    com_destaque_plano_medio=True,
    stripe_ready=True
)

# Informações de contato
st.markdown("""
<div class="contact-container">
    <h3 class="contact-title">Ainda tem dúvidas?</h3>
    <p>Entre em contato com nosso suporte:</p>
    <a href="mailto:contato@plannerorganiza.com.br" class="contact-email">contato@plannerorganiza.com.br</a>
    <p class="footer-text">
        © 2025 Planner Organizer. Todos os direitos reservados.
    </p>
</div>
""", unsafe_allow_html=True)

# Botão para voltar ao Login
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
if st.button("Voltar ao login", key="btn_voltar", use_container_width=True):
    # Aqui redirecionaria para o login
    st.info("Redirecionando para a página de login...")