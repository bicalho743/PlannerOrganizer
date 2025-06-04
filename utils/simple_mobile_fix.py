"""
Correção simples e direta para sidebar mobile
"""
import streamlit as st

def apply_mobile_sidebar_fix():
    """
    Aplica CSS simples para forçar a sidebar a aparecer em mobile apenas quando logado
    """
    
    # Só aplicar se o usuário estiver logado (verificar diferentes variáveis de estado)
    is_authenticated = (
        hasattr(st.session_state, 'authenticated') and st.session_state.authenticated or
        hasattr(st.session_state, 'user_info') and st.session_state.user_info or
        hasattr(st.session_state, 'usuario') and st.session_state.usuario
    )
    
    if not is_authenticated:
        return
    
    st.markdown("""
    <style>
    /* Força sidebar sempre visível quando logado */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background-color: #1E1F36 !important;
    }
    
    /* Mobile específico */
    @media (max-width: 768px) {
        /* Força sidebar visível em mobile */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            width: 100% !important;
            background-color: #1E1F36 !important;
            z-index: 50 !important;
        }
        
        /* Botões do menu em layout horizontal compacto */
        section[data-testid="stSidebar"] .nav-buttons {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
            padding: 8px !important;
        }
        
        section[data-testid="stSidebar"] button {
            display: inline-block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            min-width: 80px !important;
            margin: 0 !important;
            padding: 6px 10px !important;
            font-size: 0.75rem !important;
            border-radius: 6px !important;
            flex: 0 0 auto !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)