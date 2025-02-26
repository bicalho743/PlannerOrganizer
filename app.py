import os
import sys
import logging
import traceback
from datetime import datetime

# Configurar logging primeiro para capturar todos os erros
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Iniciando aplicação...")

try:
    # Adicionar diretório src ao path
    root_dir = os.path.dirname(__file__)
    src_dir = os.path.join(root_dir, "src")
    if src_dir not in sys.path:
        sys.path.append(src_dir)
        logger.info(f"Adicionado diretório src ao path: {src_dir}")

    # Verificar variáveis de ambiente críticas
    required_env_vars = ['DATABASE_URL'] # Removed JWT_SECRET as per edited code
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}"
        logger.error(error_msg)
        st.error(error_msg)
        st.stop()

    try:
        logger.info("Importando módulo de banco de dados...")
        from utils.database import Database
    except ImportError as e:
        error_msg = f"Erro ao importar módulo de banco de dados: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Stack trace: {traceback.format_exc()}")
        st.error(error_msg)
        st.stop()

    logger.info("Importando streamlit...")
    import streamlit as st

    # Configuração da página
    logger.info("Configurando página Streamlit...")
    st.set_page_config(
        page_title="Planner Organizer",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inicialização da sessão
    if 'initialized' not in st.session_state:
        logger.info("Inicializando estado da sessão...")
        st.session_state.initialized = True
        st.session_state.autenticado = False
        st.session_state.usuario = None
        try:
            logger.info("Inicializando conexão com banco de dados...")
            st.session_state.db = Database()
            logger.info("Conexão com banco de dados estabelecida com sucesso")
        except Exception as e:
            error_msg = f"Erro ao conectar com banco de dados: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Stack trace: {traceback.format_exc()}")
            st.error(error_msg)
            st.stop()

    # Interface principal
    try:
        if not st.session_state.autenticado:
            logger.info("Iniciando página de login...")
            import pages.login as login
            login.show()
        else:
            # Menu lateral
            st.sidebar.title("Menu Principal")

            # Informações do usuário
            with st.sidebar:
                if st.session_state.usuario and isinstance(st.session_state.usuario, dict):
                    st.write(f"👤 Olá, {st.session_state.usuario.get('nome', 'Usuário')}")
                else:
                    st.write("👤 Olá, Usuário")

                # Botão de logout
                if st.button("📤 Sair", key="logout_button"):
                    logger.info("Usuário realizou logout")
                    st.session_state.autenticado = False
                    st.session_state.usuario = None
                    st.rerun()

            # Menu de navegação
            pagina = st.sidebar.radio(
                "Menu",
                ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios", "Teste de Importação"],
                format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                                else f"👥 {x}" if x == "Cadastros"
                                else f"📝 {x}" if x == "Propostas"
                                else f"💰 {x}" if x == "Financeiro"
                                else f"📈 {x}" if x == "Relatórios"
                                else f"🔄 {x}"  # Teste de Importação
            )

            logger.info(f"Página selecionada: {pagina}")

            # Roteamento de páginas
            try:
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
                elif pagina == "Teste de Importação":
                    import pages.teste_importacao as teste_importacao
                    teste_importacao.show()
            except ImportError as e:
                error_msg = f"Erro ao importar módulo da página {pagina}: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
            except Exception as e:
                error_msg = f"Erro ao carregar página {pagina}: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Stack trace: {traceback.format_exc()}")
                st.error(error_msg)

    except Exception as e:
        error_msg = f"Erro não tratado: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Stack trace: {traceback.format_exc()}")
        st.error(error_msg)

except Exception as e:
    error_msg = f"Erro crítico durante inicialização: {str(e)}"
    print(error_msg)  # Fallback se o logger não estiver configurado
    if 'logger' in locals():
        logger.critical(error_msg)
        logger.critical(f"Stack trace: {traceback.format_exc()}")
    if 'st' in locals():
        st.error(error_msg)