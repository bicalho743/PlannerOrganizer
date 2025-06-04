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
        background-color: #2E3440 !important;
        border-right: 1px solid #4C566A !important;
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
            background-color: #2E3440 !important;
            border-right: 1px solid #4C566A !important;
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
        
        /* Aplicar estilos APENAS aos botões de navegação da sidebar */
        section[data-testid="stSidebar"] div[data-testid="column"] button[data-testid="baseButton-secondary"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 8px 10px !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            border-radius: 6px !important;
            height: auto !important;
            line-height: 1.3 !important;
            text-align: center !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
            background-color: #3B4252 !important;
            color: #ECEFF4 !important;
            border: 1px solid #4C566A !important;
            transition: all 0.2s ease !important;
        }
        
        section[data-testid="stSidebar"] div[data-testid="column"] button[data-testid="baseButton-secondary"]:hover {
            background-color: #434C5E !important;
            color: #88C0D0 !important;
            border-color: #5E81AC !important;
        }
        
        /* Garantir que botões da página principal mantenham estilo padrão */
        div[data-testid="stMainBlockContainer"] button[data-testid="baseButton-primary"],
        div[data-testid="stMainBlockContainer"] button[data-testid="baseButton-secondary"],
        .main button[data-testid="baseButton-primary"],
        .main button[data-testid="baseButton-secondary"] {
            background-color: revert !important;
            color: revert !important;
            border: revert !important;
            font-size: revert !important;
            font-weight: revert !important;
            padding: revert !important;
            margin: revert !important;
            border-radius: revert !important;
            height: revert !important;
            line-height: revert !important;
            text-align: revert !important;
            white-space: revert !important;
            text-overflow: revert !important;
            overflow: revert !important;
            transition: revert !important;
        }
        
        /* Forçar reset completo de botões fora da sidebar */
        section[data-testid="stMain"] button,
        div[data-testid="stTabs"] button {
            all: revert !important;
        }
        
        /* Textos e labels da sidebar */
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #D8DEE9 !important;
            font-size: 0.8rem !important;
        }
        
        /* Botão toggle para esconder/mostrar sidebar */
        .sidebar-toggle-btn {
            position: fixed !important;
            top: 50% !important;
            left: 160px !important;
            width: 40px !important;
            height: 40px !important;
            background-color: #5E81AC !important;
            border: none !important;
            border-radius: 50% !important;
            color: white !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 1000 !important;
            font-size: 1.2rem !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
            transition: all 0.3s ease !important;
        }
        
        .sidebar-toggle-btn:hover {
            background-color: #81A1C1 !important;
            transform: scale(1.1) !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)