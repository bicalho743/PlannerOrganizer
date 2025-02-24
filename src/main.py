import os
import sys
import streamlit as st
import logging
from datetime import datetime

# Configurar logging primeiro para capturar todos os erros
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Adicionar diretório raiz ao path
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logger.info(f"Diretório raiz: {root_dir}")
    if root_dir not in sys.path:
        sys.path.append(root_dir)
        logger.info(f"Adicionado ao sys.path: {root_dir}")

    # Listar conteúdo do diretório utils para debug
    utils_dir = os.path.join(root_dir, "utils")
    logger.info(f"Conteúdo do diretório utils: {os.listdir(utils_dir) if os.path.exists(utils_dir) else 'Diretório não encontrado'}")

    # Configuração da página
    st.set_page_config(
        page_title="Planner Organizer",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📋 Planner Organizer")

    # Verificar variáveis de ambiente críticas
    required_env_vars = ['DATABASE_URL', 'JWT_SECRET']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
        st.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
        st.stop()

    # Tentar importar Database com tratamento detalhado de erro
    try:
        logger.info("Tentando importar módulo database...")
        from utils.database import Database
        logger.info("Módulo database importado com sucesso")
    except ImportError as e:
        logger.error(f"Erro ao importar módulo database: {str(e)}")
        st.error(f"Erro ao importar módulo de banco de dados: {str(e)}")
        st.exception(e)
        st.stop()

    # Inicialização da base de dados
    if 'db' not in st.session_state:
        try:
            logger.info("Inicializando conexão com o banco de dados...")
            st.session_state.db = Database()
            logger.info("Conexão com o banco de dados estabelecida com sucesso")
            st.success("Sistema inicializado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao conectar com o banco de dados: {str(e)}")
            st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
            st.exception(e)
            st.stop()

except Exception as e:
    logger.error(f"Erro na aplicação: {str(e)}")
    st.error(f"Ocorreu um erro inesperado: {str(e)}")
    st.exception(e)