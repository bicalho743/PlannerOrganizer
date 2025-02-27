import os
import streamlit as st
from utils.database import Database

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do banco de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Estilo CSS customizado para garantir o menu no topo
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background-color: #262730;
    }

    div.block-container {
        padding-top: 0;
    }

    div.stButton > button {
        width: 100%;
        background-color: #F1A208 !important;
        color: #262730 !important;
        font-weight: 500;
        text-align: left;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }

    div.stButton > button:hover {
        background-color: #ffc107 !important;
    }

    /* Container escuro para os botões */
    div.nav-buttons {
        background-color: #262730;
        padding: 1rem;
        margin: 0 -1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Menu principal (deve aparecer no topo)
st.sidebar.title("Menu Principal")

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definição do menu principal
menu_items = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "💰 Financeiro": "Financeiro", 
    "📈 Relatórios": "Relatórios"
}

# Criação dos botões do menu principal
for label, page in menu_items.items():
    if st.sidebar.button(label, key=f"main_menu_{page.lower()}", use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Informações do sistema no final
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.markdown("""
    ### Sistema Personal Organizer
    **Versão:** 1.0.2

    **Recursos Disponíveis:**
    - ✅ Gestão de Clientes
    - ✅ Controle de Propostas
    - ✅ Gestão Financeira
    - ✅ Relatórios e Análises
    - ✅ Importação de Dados

    **Novidades:**
    - 🎉 Telas de celebração
    - 📊 Dashboard aprimorado
    - 📱 Interface responsiva

    Desenvolvido com ❤️ usando Streamlit
    """)

    # Botão de importação de propostas
    if st.button("📥 Importar Propostas", use_container_width=True):
        st.session_state.current_page = "Importar"
        st.rerun()

# Controle de navegação
if dashboard_btn:
    st.session_state.current_page = "Dashboard"
elif cadastros_btn:
    st.session_state.current_page = "Cadastros"
elif propostas_btn:
    st.session_state.current_page = "Propostas"
elif financeiro_btn:
    st.session_state.current_page = "Financeiro"
elif relatorios_btn:
    st.session_state.current_page = "Relatórios"

# Conteúdo principal da página atual
if st.session_state.current_page == "Dashboard":
    from pages.dashboard import show
    show()
elif st.session_state.current_page == "Cadastros":
    from pages.cadastros import show
    show()
elif st.session_state.current_page == "Propostas":
    from pages.propostas import show
    show()
elif st.session_state.current_page == "Financeiro":
    from pages.financeiro import show
    show()
elif st.session_state.current_page == "Relatórios":
    from pages.relatorios import show
    show()
elif st.session_state.current_page == "Importar":
    st.write("Página de Importação de Propostas") # Placeholder - needs actual implementation