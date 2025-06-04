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
        /* Layout principal em linha - sidebar lateral */
        .main {
            display: flex !important;
            flex-direction: row !important;
        }
        
        /* Sidebar lateral mais fina */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            width: 180px !important;
            min-width: 180px !important;
            max-width: 180px !important;
            height: 100vh !important;
            background-color: #1E1F36 !important;
            z-index: 50 !important;
            flex-shrink: 0 !important;
            order: 1 !important;
        }
        
        /* Conteúdo principal ao lado da sidebar */
        .main .block-container {
            order: 2 !important;
            flex: 1 !important;
            padding: 10px !important;
            width: calc(100vw - 180px) !important;
            max-width: calc(100vw - 180px) !important;
        }
        
        /* Container da sidebar */
        section[data-testid="stSidebar"] > div {
            width: 100% !important;
            height: 100% !important;
            overflow-y: auto !important;
            padding: 8px !important;
        }
        
        /* Botões do menu em layout vertical */
        section[data-testid="stSidebar"] .nav-buttons {
            display: flex !important;
            flex-direction: column !important;
            gap: 4px !important;
            padding: 8px 4px !important;
        }
        
        section[data-testid="stSidebar"] button {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 6px 8px !important;
            font-size: 0.7rem !important;
            border-radius: 4px !important;
            height: auto !important;
            line-height: 1.2 !important;
            text-align: center !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
        }
        
        /* Botão para esconder/mostrar sidebar */
        section[data-testid="stSidebar"] .sidebar-toggle {
            position: absolute !important;
            top: 10px !important;
            right: -15px !important;
            width: 30px !important;
            height: 30px !important;
            background-color: #1E1F36 !important;
            border: none !important;
            border-radius: 50% !important;
            color: white !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 100 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)