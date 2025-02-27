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

# Log de início da aplicação
logger.info("Iniciando aplicação Planner Organizer")

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

# Menu lateral
with st.sidebar:
    st.title("Menu Principal")

    # Botão de apresentação
    if st.button("📌 Sobre o Sistema"):
        st.session_state.mostrar_apresentacao = True

    # Seleção de página
    pagina = st.radio(
        "",  # Label vazio para não mostrar título do radio
        ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                    else f"👥 {x}" if x == "Cadastros"
                    else f"📝 {x}" if x == "Propostas"
                    else f"💰 {x}" if x == "Financeiro"
                    else f"📈 {x}" if x == "Relatórios"
                    else f"📥 {x}"  # Importação
    )

# Se a apresentação estiver ativa, mostrar na área principal
if 'mostrar_apresentacao' in st.session_state and st.session_state.mostrar_apresentacao:
    st.title("👋 Bem-vindo ao seu assistente de organização!")

    # Texto explicativo das funcionalidades
    st.markdown("""
    O **Sistema Planner Organizer** é uma ferramenta completa para o gerenciamento eficiente 
    do seu negócio de Personal Organizer. Com ele, você pode:

    ### 📊 Funcionalidades Principais

    **👥 Gestão de Clientes**
    - Cadastro completo de clientes
    - Controle de aniversários
    - Histórico de atendimentos
    - Importação de dados em massa

    **📝 Gestão de Propostas**
    - Criação e acompanhamento de propostas
    - Cálculo automático de valores
    - Geração de PDFs profissionais
    - Controle de status e prazos

    **💰 Gestão Financeira**
    - Controle de receitas e despesas
    - Gestão de contas a receber
    - Relatórios financeiros detalhados
    - Dashboard com indicadores

    **📈 Relatórios e Análises**
    - Visão geral do negócio
    - Análise de desempenho
    - Gráficos e estatísticas
    - Exportação de dados

    ### 🔍 Recursos Adicionais
    - Interface intuitiva e amigável
    - Backup automático de dados
    - Controle de acesso seguro
    - Suporte a múltiplos usuários

    ### 📱 Benefícios
    - Aumente sua produtividade
    - Mantenha seus dados organizados
    - Tome decisões baseadas em dados
    - Profissionalize seu negócio
    """)

    if st.button("Fechar Apresentação"):
        st.session_state.mostrar_apresentacao = False
        st.rerun()
else:
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
    except ImportError as e:
        logger.error(f"Erro ao importar módulo da página {pagina}: {str(e)}")
        st.error(f"Erro ao carregar página {pagina}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao exibir página {pagina}: {str(e)}")
        st.error(f"Erro ao exibir página {pagina}: {str(e)}")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")