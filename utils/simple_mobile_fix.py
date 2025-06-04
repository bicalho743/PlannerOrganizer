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
        position: relative !important;
        min-width: 200px !important;
        width: auto !important;
        background-color: #1E1F36 !important;
        z-index: 100 !important;
    }
    
    /* Garante que container dos botões seja visível */
    section[data-testid="stSidebar"] .nav-buttons {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Mostra todos os botões do menu */
    section[data-testid="stSidebar"] button {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 100% !important;
        margin: 4px 0 !important;
    }
    
    /* Força exibição em todos os tamanhos de tela */
    @media screen {
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
    }
    
    /* Mobile específico */
    @media (max-width: 768px) {
        /* Força sidebar visível em mobile */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            width: 250px !important;
            min-width: 250px !important;
            max-width: 250px !important;
            flex-shrink: 0 !important;
            transform: none !important;
            left: 0 !important;
            top: 0 !important;
            height: auto !important;
            background-color: #1E1F36 !important;
            overflow-y: auto !important;
            z-index: 100 !important;
        }
        
        /* Layout flexível para mobile */
        .main {
            display: flex !important;
            flex-direction: row !important;
        }
        
        /* Conteúdo principal ajustado */
        .main .block-container {
            flex: 1 !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
            max-width: none !important;
            width: auto !important;
        }
        
        /* Força visibilidade de todos os botões */
        section[data-testid="stSidebar"] button {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 100% !important;
            margin: 4px 0 !important;
            padding: 12px 16px !important;
            text-align: left !important;
        }
        
        /* Garante que div dos botões seja visível */
        section[data-testid="stSidebar"] div {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
    }
    
    /* Tablet */
    @media (min-width: 769px) and (max-width: 1024px) {
        section[data-testid="stSidebar"] {
            display: block !important;
            width: 260px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)