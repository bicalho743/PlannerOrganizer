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
        /* Força sidebar visível em mobile com altura limitada */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            width: 100% !important;
            max-height: 80px !important;
            height: auto !important;
            background-color: #1E1F36 !important;
            z-index: 50 !important;
            overflow: hidden !important;
        }
        
        /* Container da sidebar com altura controlada */
        section[data-testid="stSidebar"] > div {
            max-height: 80px !important;
            overflow: hidden !important;
        }
        
        /* Botões do menu em layout horizontal compacto */
        section[data-testid="stSidebar"] .nav-buttons {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 4px !important;
            padding: 6px 8px !important;
            max-height: 70px !important;
            overflow: hidden !important;
        }
        
        section[data-testid="stSidebar"] button {
            display: inline-block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            min-width: 70px !important;
            max-width: 90px !important;
            margin: 0 !important;
            padding: 4px 8px !important;
            font-size: 0.7rem !important;
            border-radius: 4px !important;
            flex: 0 0 auto !important;
            height: 28px !important;
            line-height: 1.2 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)