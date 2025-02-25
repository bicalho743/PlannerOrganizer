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

# Inicialização da base de dados (apenas se não existir)
if 'db' not in st.session_state:
    try:
        logger.info("Inicializando conexão com banco de dados...")
        st.session_state.db = Database()
        logger.info("Conexão com banco de dados estabelecida com sucesso")
    except Exception as e:
        logger.error(f"Erro ao conectar com banco de dados: {str(e)}")
        st.error("Erro ao conectar com banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Verificar autenticação (apenas se não existir)
if 'autenticado' not in st.session_state:
    logger.info("Inicializando estado de autenticação")
    st.session_state.autenticado = False
    st.session_state.usuario = None

# Página de login
if not st.session_state.get('autenticado', False):
    logger.info("Usuário não autenticado, mostrando página de login")
    st.title("Login")
    st.write("Por favor, faça login para continuar.")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            if st.session_state.db:
                logger.info(f"Tentativa de login para o email: {email}")
                sucesso, usuario = st.session_state.db.autenticar_usuario(email, senha)
                if sucesso:
                    logger.info("Login realizado com sucesso")
                    st.session_state.autenticado = True
                    st.session_state.usuario = usuario
                    st.success("Login realizado com sucesso!")
                    st.experimental_rerun()
                else:
                    logger.warning("Falha na autenticação")
                    st.error("Email ou senha inválidos")
    st.stop()  # Impede a renderização do resto da página se não estiver autenticado

else:
    logger.info("Usuário autenticado, mostrando dashboard")
    # Menu lateral personalizado
    st.sidebar.title("Menu Principal")

    # Mostrar informações do usuário
    with st.sidebar:
        if st.session_state.usuario and isinstance(st.session_state.usuario, dict):
            st.write(f"👤 Olá, {st.session_state.usuario.get('nome', 'Usuário')}")
        else:
            st.write("👤 Olá, Usuário")

        # Botão de logout com key única
        logout_key = f"logout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if st.button("📤 Sair", key=logout_key):
            logger.info("Usuário realizou logout")
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.success("Logout realizado com sucesso!")
            st.experimental_rerun()

    # Seleção de página com key única
    menu_key = f"menu_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    pagina = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios", "Teste de Importação"],
        key=menu_key,
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                        else f"👥 {x}" if x == "Cadastros"
                        else f"📝 {x}" if x == "Propostas"
                        else f"💰 {x}" if x == "Financeiro"
                        else f"📈 {x}" if x == "Relatórios"
                        else f"🔄 {x}"  # Teste de Importação
    )

    logger.info(f"Página selecionada: {pagina}")

    # Roteamento de páginas com tratamento de erro
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
        logger.error(f"Erro ao importar módulo da página {pagina}: {str(e)}")
        st.error(f"Erro ao carregar a página {pagina}. Módulo não encontrado.")
    except Exception as e:
        logger.error(f"Erro ao carregar página {pagina}: {str(e)}")
        st.error(f"Erro ao carregar a página {pagina}.")
        logger.exception(e)

    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")