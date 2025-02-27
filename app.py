import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        font-size: 1rem;
        border: none;
        border-radius: 4px;
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

# Criação dos botões
dashboard_btn = st.sidebar.button("📊 Dashboard", use_container_width=True)
cadastros_btn = st.sidebar.button("👥 Cadastros", use_container_width=True)
propostas_btn = st.sidebar.button("📝 Propostas", use_container_width=True)
financeiro_btn = st.sidebar.button("💰 Financeiro", use_container_width=True)
relatorios_btn = st.sidebar.button("📈 Relatórios", use_container_width=True)

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Informações do sistema no final
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.write("Versão 1.0")
    st.write("Desenvolvido com ❤️ usando Streamlit")

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

# Conteúdo principal (temporário)
st.title(f"{st.session_state.current_page}")
st.write("Carregando módulo...")