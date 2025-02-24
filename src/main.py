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
        except Exception as e:
            logger.error(f"Erro ao conectar com o banco de dados: {str(e)}")
            st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
            st.exception(e)
            st.stop()

    # Verificar autenticação
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario = None

    if not st.session_state.autenticado:
        # CSS para esconder o menu lateral na tela de login
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                display: none;
            }
            div[data-testid="stToolbar"] {
                display: none;
            }
            #MainMenu {
                display: none;
            }
            footer {
                display: none;
            }
            /* Estilo para o título principal */
            h1 {
                color: #B8860B !important;
                font-family: sans-serif !important;
                font-weight: bold !important;
                text-align: center !important;
                margin-bottom: 2rem !important;
            }
            /* Centraliza o conteúdo */
            .block-container {
                padding-top: 2rem;
                max-width: 1000px;
            }
            </style>
        """, unsafe_allow_html=True)
        import pages.login as login
        login.show()
    else:
        # Menu lateral personalizado
        st.sidebar.title("Menu Principal")

        # Mostrar informações do usuário
        with st.sidebar:
            st.write(f"👤 Olá, {st.session_state.usuario['nome']}")

            # Mostrar mais detalhes do usuário
            with st.expander("Ver meus dados"):
                st.write("**Seus dados:**")
                st.write(f"ID: {st.session_state.usuario['id']}")
                st.write(f"Nome: {st.session_state.usuario['nome']}")
                st.write(f"Email: {st.session_state.usuario['email']}")
                st.write(f"Tipo de usuário: {st.session_state.usuario['tipo']}")

            if st.button("📤 Sair"):
                st.session_state.autenticado = False
                st.session_state.usuario = None
                st.experimental_rerun()

        # Seleção de página
        pagina = st.sidebar.radio(
            "",  # Label vazio para não mostrar título do radio
            ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios", "Importação"],
            format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                            else f"👥 {x}" if x == "Cadastros"
                            else f"📝 {x}" if x == "Propostas"
                            else f"💰 {x}" if x == "Financeiro"
                            else f"📈 {x}" if x == "Relatórios"
                            else f"📥 {x}"  # Importação
        )

        # Navegação
        if pagina == "Dashboard":
            st.title("📋 Planner Organizer")
            st.write("Bem-vindo ao sistema!")

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

except Exception as e:
    logger.error(f"Erro na aplicação: {str(e)}")
    st.error(f"Ocorreu um erro inesperado: {str(e)}")
    st.exception(e)