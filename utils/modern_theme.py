"""
Tema moderno azul simplificado para o sistema
"""
import streamlit as st

def apply_modern_blue_theme():
    """
    Aplica o tema moderno azul com CSS simplificado
    """
    
    css = """
    <style>
    /* TEMA AZUL ELEGANTE E SUAVE */
    
    /* Sidebar com azul suave */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    
    /* Texto branco apenas na sidebar */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Botões da sidebar mais suaves */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 6px !important;
        width: 100% !important;
        text-align: left !important;
        padding: 8px 12px !important;
        margin: 2px 0 !important;
        font-weight: 400 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Hover suave dos botões */
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(2px) !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Fundo principal muito claro */
    .main {
        background: #fafbfc !important;
    }
    
    /* Títulos azuis suaves */
    h1, h2, h3 {
        color: #2563eb !important;
        font-weight: 500 !important;
    }
    
    /* Cards com bordas suaves */
    .element-container {
        background: white !important;
        border-radius: 6px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)