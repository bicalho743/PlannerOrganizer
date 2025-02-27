import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        text-align: left;
        padding: 0.75rem 1rem;
        background-color: transparent;
        border: none;
        color: #FFFFFF;
        margin-bottom: 0.25rem;
        font-size: 1rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1);
        color: #FFFFFF;
    }
    div.stButton > button:active {
        background-color: rgba(255, 255, 255, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Barra lateral com Menu Principal no topo
with st.sidebar:
    st.title("Menu Principal")

    # Botões de navegação no topo
    dashboard_btn = st.button("📊 Dashboard", use_container_width=True)
    cadastros_btn = st.button("👥 Cadastros", use_container_width=True)
    propostas_btn = st.button("📝 Propostas", use_container_width=True)
    financeiro_btn = st.button("💰 Financeiro", use_container_width=True)
    relatorios_btn = st.button("📈 Relatórios", use_container_width=True)

    # Separador antes das informações do sistema
    st.markdown("---")

    # Informações do sistema no final
    with st.expander("ℹ️ Informações do Sistema", expanded=False):
        st.write("Versão 1.0")
        st.write("Desenvolvido com ❤️ usando Streamlit")

# Determinar a página selecionada
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

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