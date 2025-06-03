"""
Correção simples e direta para sidebar mobile
"""
import streamlit as st

def apply_mobile_sidebar_fix():
    """
    Aplica CSS simples para forçar a sidebar a aparecer em mobile
    """
    
    st.markdown("""
    <style>
    /* Força sidebar sempre visível */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: relative !important;
        min-width: 200px !important;
        width: auto !important;
        background-color: #1E1F36 !important;
    }
    
    /* Remove qualquer CSS que esconda a sidebar */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: none !important;
            left: 0 !important;
            position: relative !important;
            width: 100% !important;
            max-width: 280px !important;
            min-width: 200px !important;
        }
        
        /* Garante que o conteúdo da sidebar seja visível */
        section[data-testid="stSidebar"] > div {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        /* Ajusta o layout principal para mobile */
        .main .block-container {
            padding-left: 10px !important;
            padding-right: 10px !important;
            max-width: 100% !important;
        }
    }
    
    /* Garante que todos os elementos da sidebar sejam visíveis */
    section[data-testid="stSidebar"] * {
        visibility: visible !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)