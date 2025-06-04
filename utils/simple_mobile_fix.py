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
        /* Layout principal em coluna */
        .main {
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* Sidebar como barra de navegação horizontal no topo */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            width: 100% !important;
            max-width: 100vw !important;
            height: 60px !important;
            max-height: 60px !important;
            background-color: #1E1F36 !important;
            z-index: 50 !important;
            overflow: hidden !important;
            order: 1 !important;
        }
        
        /* Conteúdo principal abaixo da sidebar */
        .main .block-container {
            order: 2 !important;
            padding-top: 10px !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Container da sidebar com altura controlada */
        section[data-testid="stSidebar"] > div {
            height: 60px !important;
            max-height: 60px !important;
            overflow: hidden !important;
            width: 100% !important;
        }
        
        /* Botões do menu em layout horizontal compacto */
        section[data-testid="stSidebar"] .nav-buttons {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 3px !important;
            padding: 5px !important;
            height: 50px !important;
            max-height: 50px !important;
            overflow: hidden !important;
            align-items: center !important;
            justify-content: flex-start !important;
        }
        
        section[data-testid="stSidebar"] button {
            display: inline-block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            min-width: 60px !important;
            max-width: 85px !important;
            margin: 0 !important;
            padding: 3px 6px !important;
            font-size: 0.65rem !important;
            border-radius: 3px !important;
            flex: 0 0 auto !important;
            height: 24px !important;
            line-height: 1.1 !important;
            text-align: center !important;
            overflow: hidden !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)