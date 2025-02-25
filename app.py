import os
import sys
import streamlit as st
import logging
from datetime import datetime
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Verificar variáveis de ambiente críticas
required_env_vars = ['DATABASE_URL', 'JWT_SECRET']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    st.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
    st.stop()

try:
    # Tentar importar Database com tratamento detalhado de erro
    from utils.database import Database
except ImportError as e:
    st.error(f"Erro ao importar módulo de banco de dados: {str(e)}")
    st.exception(e)
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização da base de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Verificar autenticação
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

if not st.session_state.autenticado:
    import pages.login as login
    login.show()
else:
    # Menu lateral personalizado
    st.sidebar.title("Menu Principal")

    # Mostrar informações do usuário
    with st.sidebar:
        st.write(f"👤 Olá, {st.session_state.usuario['nome']}")
        if st.button("📤 Sair"):
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.experimental_rerun()

    # Seleção de página
    pagina = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                        else f"👥 {x}" if x == "Cadastros"
                        else f"📝 {x}" if x == "Propostas"
                        else f"💰 {x}" if x == "Financeiro"
                        else f"📈 {x}"  # Relatórios
    )

    # Roteamento de páginas
    if pagina == "Dashboard":
        import pages.dashboard as dashboard
        dashboard.show()
    elif pagina == "Cadastros":
        import pages.cadastros as cadastros
        cadastros.show()
    elif pagina == "Propostas":
        import pages.propostas as propostas
        propostas.show()
    elif pagina == "Financeiro":
        import pages.financeiro as financeiro
        financeiro.show()
    elif pagina == "Relatórios":
        import pages.relatorios as relatorios
        relatorios.show()

    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")