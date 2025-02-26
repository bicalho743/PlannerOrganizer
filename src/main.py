import os
import sys
import streamlit as st
import logging
from datetime import datetime
import pandas as pd

# Configurar logging primeiro para capturar todos os erros
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verificar variáveis de ambiente críticas
required_env_vars = ['DATABASE_URL']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    st.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
    st.stop()

try:
    from utils.database import Database
except ImportError as e:
    st.error(f"Erro ao importar módulo de banco de dados: {str(e)}")
    st.exception(e)
    st.stop()

# Inicialização da base de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Menu lateral simplificado
st.sidebar.title("Menu Principal")

# Seleção de página
pagina = st.sidebar.radio(
    "",  # Label vazio para não mostrar título do radio
    ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios"],
    format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                    else f"👥 {x}" if x == "Cadastros"
                    else f"📝 {x}" if x == "Propostas"
                    else f"💰 {x}" if x == "Financeiro"
                    else f"📈 {x}" if x == "Relatórios"
                    else f"📥 {x}"  # Importação
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
elif pagina == "Importação":
    import pages.importacao as importacao
    importacao.show()

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")