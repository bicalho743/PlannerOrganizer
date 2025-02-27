import os
import sys
import streamlit as st
import logging
from datetime import datetime

# Adicionar diretório src ao path para importar utils
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log de início da aplicação
logger.info("Iniciando aplicação Planner Organizer")

# Adicionar diretório src ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)
    logger.info(f"Adicionado diretório src ao path: {src_dir}")

# Configuração da página
try:
    logger.info("Configurando página Streamlit")
    st.set_page_config(
        page_title="Planner Organizer",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Importar e carregar estilos personalizados
    from src.utils.custom_styles import load_custom_styles
    load_custom_styles()
    
    logger.info("Página configurada com sucesso")
except Exception as e:
    logger.error(f"Erro na configuração da página: {str(e)}")
    st.error(f"Erro na configuração da página: {str(e)}")
    st.stop()

try:
    # Verificar variáveis de ambiente críticas
    logger.info("Verificando variáveis de ambiente")
    required_env_vars = ['DATABASE_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
        st.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
        st.stop()

    # Importar módulo de banco de dados
    logger.info("Importando módulo de banco de dados")
    from utils.database import Database

    # Inicialização da sessão
    if 'initialized' not in st.session_state:
        logger.info("Inicializando sessão e banco de dados")
        st.session_state.initialized = True
        try:
            st.session_state.db = Database()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.stop()

    # Menu na parte superior
    logger.info("Criando menu horizontal")
    st.title("Menu Principal")
    
    # Seleção de página com layout horizontal
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        dashboard_btn = st.button("📊 Dashboard", use_container_width=True)
    with col2:
        cadastros_btn = st.button("👥 Cadastros", use_container_width=True)
    with col3:
        propostas_btn = st.button("📝 Propostas", use_container_width=True)
    with col4:
        financeiro_btn = st.button("💰 Financeiro", use_container_width=True)
    with col5:
        relatorios_btn = st.button("📈 Relatórios", use_container_width=True)
    with col6:
        importacao_btn = st.button("📥 Importação", use_container_width=True)
    
    # Determinar a página selecionada com base nos botões
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"  # Página padrão
    
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
    elif importacao_btn:
        st.session_state.current_page = "Importação"
    
    pagina = st.session_state.current_page
    logger.info(f"Página selecionada: {pagina}")
    
    # Adicionar separador visual após o menu
    st.markdown("---")
    
    # Rodapé movido para a barra lateral
    with st.sidebar:
        st.markdown("### Desenvolvido com ❤️ usando Streamlit")

    # Roteamento de páginas
    try:
        logger.info(f"Tentando carregar página: {pagina}")
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
        logger.info(f"Página {pagina} carregada com sucesso")
    except ImportError as e:
        logger.error(f"Erro ao importar módulo da página {pagina}: {str(e)}")
        st.error(f"Erro ao carregar página {pagina}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao exibir página {pagina}: {str(e)}")
        st.error(f"Erro ao exibir página {pagina}: {str(e)}")

    logger.info("Aplicação carregada com sucesso")

except Exception as e:
    logger.error(f"Erro durante a execução da aplicação: {str(e)}")
    st.error(f"Erro durante a execução da aplicação: {str(e)}")