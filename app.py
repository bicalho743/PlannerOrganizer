import os
import sys
import streamlit as st
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório src ao path
root_dir = os.path.dirname(__file__)
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    # Verificar variáveis de ambiente críticas
    required_env_vars = ['DATABASE_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        st.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
        st.stop()

    # Importar módulo de banco de dados
    from utils.database import Database

    # Inicialização da sessão
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        try:
            st.session_state.db = Database()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.stop()

    # Menu lateral
    st.sidebar.title("Menu Principal")

    # Seleção de página
    pagina = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios", "Importação"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                        else f"👥 {x}" if x == "Cadastros"
                        else f"📝 {x}" if x == "Propostas"
                        else f"💰 {x}" if x == "Financeiro"
                        else f"📈 {x}" if x == "Relatórios"
                        else f"📥 {x}"  # Importação
    )

    # Roteamento de páginas
    try:
        if pagina == "Dashboard":
            from pages.dashboard import show
            show()
        elif pagina == "Cadastros":
            from pages.cadastros import show
            show()
        elif pagina == "Propostas":
            from pages.propostas import show
            show()
        elif pagina == "Financeiro":
            from pages.financeiro import show
            show()
        elif pagina == "Relatórios":
            from pages.relatorios import show
            show()
        elif pagina == "Importação":
            from pages.importacao import show
            show()
    except ImportError as e:
        logger.error(f"Erro ao importar módulo da página {pagina}: {str(e)}")
        st.error(f"Erro ao carregar página {pagina}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao exibir página {pagina}: {str(e)}")
        st.error(f"Erro ao exibir página {pagina}: {str(e)}")

    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")

except Exception as e:
    logger.error(f"Erro durante a execução da aplicação: {str(e)}")
    st.error(f"Erro durante a execução da aplicação: {str(e)}")