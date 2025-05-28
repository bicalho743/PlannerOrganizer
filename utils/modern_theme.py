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
    /* Sidebar azul moderna */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%) !important;
    }
    
    /* Texto branco na sidebar */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Botões da sidebar */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        width: 100% !important;
        text-align: left !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(59, 130, 246, 0.4) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Conteúdo principal */
    .main {
        background: #f8fafc !important;
    }
    
    /* Botões principais azuis */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Headers azuis */
    h1, h2, h3 {
        color: #1e40af !important;
        font-weight: 600 !important;
    }
    
    /* Cards com bordas suaves */
    .element-container {
        background: white !important;
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)