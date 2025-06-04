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
    /* Esconde elementos de debug/desenvolvimento */
    section[data-testid="stSidebar"] [data-testid="stExpander"],
    section[data-testid="stSidebar"] .streamlit-expanderHeader,
    section[data-testid="stSidebar"] details,
    section[data-testid="stSidebar"] summary,
    section[data-testid="stSidebar"] .element-container:has(details),
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
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
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 100% !important;
        margin: 4px 0 !important;
    }
    
    /* Mobile específico */
    @media (max-width: 768px) {
        /* Layout em coluna para mobile - sidebar fica acima do conteúdo */
        .main {
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* Força sidebar visível em mobile */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: auto !important;
            flex-shrink: 0 !important;
            transform: none !important;
            left: 0 !important;
            top: 0 !important;
            height: auto !important;
            max-height: 250px !important;
            background-color: #1E1F36 !important;
            overflow-y: auto !important;
            z-index: 100 !important;
            order: 1 !important;
        }
        
        /* Conteúdo principal ajustado */
        .main .block-container {
            flex: 1 !important;
            padding: 10px !important;
            max-width: 100% !important;
            width: 100% !important;
            order: 2 !important;
        }
        
        /* Força visibilidade de todos os botões */
        section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
            display: inline-block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            margin: 2px 4px !important;
            padding: 8px 12px !important;
            font-size: 0.8rem !important;
            border-radius: 6px !important;
        }
        
        /* Layout horizontal dos botões em mobile */
        section[data-testid="stSidebar"] .nav-buttons {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 4px !important;
            padding: 8px !important;
        }
        
        /* Esconde elementos de debug específicos para mobile */
        section[data-testid="stSidebar"] > div > div:not(.nav-buttons):not([data-testid="baseButton-secondary"]) {
            display: none !important;
        }
    }
    
    /* Tablet */
    @media (min-width: 769px) and (max-width: 1024px) {
        section[data-testid="stSidebar"] {
            display: block !important;
            width: 260px !important;
        }
        
        .main {
            display: flex !important;
            flex-direction: row !important;
        }
    }
    
    /* Desktop */
    @media (min-width: 1025px) {
        .main {
            display: flex !important;
            flex-direction: row !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)