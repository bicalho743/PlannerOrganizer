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
        st.session_state.autenticado = False
        st.session_state.usuario = None
        try:
            st.session_state.db = Database()
        except Exception as e:
            st.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.stop()

    # Interface principal
    if not st.session_state.autenticado:
        # Importar e mostrar página de login
        try:
            from pages.login import show as show_login
            show_login()
        except ImportError as e:
            st.error(f"Erro ao carregar página de login: {str(e)}")
            st.stop()
    else:
        # Menu lateral
        st.sidebar.title("Menu Principal")

        # Informações do usuário
        with st.sidebar:
            if st.session_state.usuario and isinstance(st.session_state.usuario, dict):
                st.write(f"👤 Olá, {st.session_state.usuario.get('nome', 'Usuário')}")

            # Botão de logout
            if st.button("📤 Sair"):
                st.session_state.autenticado = False
                st.session_state.usuario = None
                st.rerun()

        # Menu de navegação
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
        try:
            if pagina == "Dashboard":
                from pages.dashboard import show as show_dashboard
                show_dashboard()
            elif pagina == "Cadastros":
                from pages.cadastros import show as show_cadastros
                show_cadastros()
            elif pagina == "Propostas":
                from pages.propostas import show as show_propostas
                show_propostas()
            elif pagina == "Financeiro":
                from pages.financeiro import show as show_financeiro
                show_financeiro()
            elif pagina == "Relatórios":
                from pages.relatorios import show as show_relatorios
                show_relatorios()
        except ImportError as e:
            st.error(f"Erro ao carregar página {pagina}: {str(e)}")
        except Exception as e:
            st.error(f"Erro ao exibir página {pagina}: {str(e)}")

        # Rodapé
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")

except Exception as e:
    st.error(f"Erro durante a execução da aplicação: {str(e)}")
    logger.error(f"Erro durante a execução da aplicação: {str(e)}")