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
    section[data-testid="stSidebar"] summary {
        display: none !important;
    }
    
    /* Esconde elementos técnicos específicos */
    section[data-testid="stSidebar"] div[data-testid]:not([data-testid="stSidebar"]):not([data-testid="baseButton-secondary"]) {
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
    
    /* Mostra apenas botões do menu */
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Força exibição em todos os tamanhos de tela */
    @media screen {
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        /* Container da sidebar - apenas botões */
        section[data-testid="stSidebar"] > div:first-child {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        /* Esconde navegação nativa do Streamlit */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none !important;
        }
    }
    
    /* Mobile específico */
    @media (max-width: 768px) {
        /* Layout flexível para mobile */
        .main {
            display: flex !important;
            flex-direction: row !important;
        }
        
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
        }
        
        /* Conteúdo principal ajustado */
        .main .block-container {
            flex: 1 !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
            max-width: none !important;
            width: auto !important;
        }
        
        /* Força apenas elementos do menu funcional */
        section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        /* Esconde todo o resto */
        section[data-testid="stSidebar"] > div > div:not(.nav-buttons) {
            display: none !important;
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