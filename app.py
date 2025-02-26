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

# Inicialização da sessão
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.autenticado = False
    st.session_state.usuario = None
    try:
        logger.info("Inicializando conexão com banco de dados...")
        st.session_state.db = Database()
        logger.info("Conexão com banco de dados estabelecida com sucesso")
    except Exception as e:
        logger.error(f"Erro ao conectar com banco de dados: {str(e)}")
        st.error("Erro ao conectar com banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Verificação de autenticação - impede acesso a qualquer página se não estiver autenticado
if not st.session_state.autenticado:
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
                    st.rerun()  # Alterado de experimental_rerun para rerun
                else:
                    logger.warning("Falha na autenticação")
                    st.error("Email ou senha inválidos")
    st.stop()

# Se chegou aqui, está autenticado - mostrar interface principal
logger.info("Usuário autenticado, mostrando dashboard")

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
        st.success("Logout realizado com sucesso!")
        st.rerun()  # Alterado de experimental_rerun para rerun

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
    logger.error(f"Erro ao importar módulo da página {pagina}: {str(e)}")
    st.error(f"Erro ao carregar a página {pagina}. Módulo não encontrado.")
except Exception as e:
    logger.error(f"Erro ao carregar página {pagina}: {str(e)}")
    st.error(f"Erro ao carregar a página {pagina}.")
    logger.exception(e)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")