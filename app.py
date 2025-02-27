import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menu principal no topo da barra lateral
st.sidebar.title("Menu Principal")

# Seleção de página com ícones no topo
pagina = st.sidebar.radio(
    "",
    ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios"],
    format_func=lambda x: {
        "Dashboard": "📊 Dashboard",
        "Cadastros": "👥 Cadastros",
        "Propostas": "📝 Propostas",
        "Financeiro": "💰 Financeiro",
        "Relatórios": "📈 Relatórios"
    }[x]
)

# Espaçador para empurrar o conteúdo para baixo
for _ in range(10):
    st.sidebar.write("")

# Informações do sistema no final da barra
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.write("Versão 1.0")
    st.write("Desenvolvido com ❤️ usando Streamlit")

# Conteúdo principal (temporário)
st.title(f"{pagina}")
st.write("Carregando módulo...")