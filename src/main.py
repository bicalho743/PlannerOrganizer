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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from utils.database import Database
    from utils.celebration import toggle_celebration, show_celebration
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {str(e)}")
    st.error("Erro ao carregar módulos necessários. Por favor, tente novamente.")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização da base de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Estilo CSS customizado
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        text-align: left;
        padding: 0.75rem 1rem;
        background-color: #F1A208 !important;
        color: #262730 !important;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    div.stButton > button:hover {
        background-color: #ffc107 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #262730;
    }
    /* Container escuro para os botões */
    div.nav-buttons {
        background-color: #262730;
        padding: 1rem;
        margin: 0 -1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Menu principal
st.sidebar.title("Menu Principal")

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definindo as páginas visíveis principais
MENU_PRINCIPAL = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios",
    "📥 Importação": "Importar"
}

# Criar botões para cada página
for label, page_key in MENU_PRINCIPAL.items():
    if st.sidebar.button(label, key=f"menu_{page_key.lower()}", use_container_width=True):
        st.session_state.current_page = page_key
        st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Informações do sistema no final
st.sidebar.markdown("---")

# Sobre o Sistema
with st.sidebar.expander("📌 Sobre o Sistema", expanded=False):
    st.markdown("""
    O **Sistema Planner Organizer** é uma ferramenta completa para o gerenciamento 
    eficiente do seu negócio de Personal Organizer. Com ele, você pode:

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
    """)

# Informações da versão
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.markdown("""
    ### Sistema Personal Organizer
    **Versão:** 1.0.2

    **Recursos Disponíveis:**
    - ✅ Gestão de Clientes
    - ✅ Controle de Propostas
    - ✅ Gestão Financeira
    - ✅ Relatórios e Análises
    - ✅ Importação de Dados

    **Novidades:**
    - 🎉 Telas de celebração
    - 📊 Dashboard aprimorado
    - 📱 Interface responsiva

    Desenvolvido com ❤️ usando Streamlit
    """)

# Verificar se há uma celebração pendente
if st.session_state.get('show_celebration', False):
    show_celebration(
        task_name=st.session_state.get('celebration_task'),
        custom_message=st.session_state.get('celebration_message')
    )
else:
    # A navegação agora é controlada pelos botões do menu principal
    # Não é mais necessário verificar os botões aqui, pois eles já
    # atualizam st.session_state.current_page e fazem rerun()

    # Roteamento de páginas
    try:
        if st.session_state.current_page == "Dashboard":
            from pages.dashboard import show
            show()
        elif st.session_state.current_page == "Cadastros":
            from pages.cadastros import show
            show()
        elif st.session_state.current_page == "Propostas":
            from pages.propostas import show
            show()
        elif st.session_state.current_page == "Financeiro":
            from pages.financeiro import show
            show()
        elif st.session_state.current_page == "Relatórios":
            from pages.relatorios import show
            show()
        elif st.session_state.current_page == "Importar":
            st.title("📥 Importação de Dados")
            st.write("### Selecione o tipo de dados para importar:")

            import_type = st.selectbox(
                "Tipo de Importação",
                ["Clientes", "Propostas", "Fornecedores", "Assistentes", "Parceiros"]
            )

            st.info(f"A importação de {import_type} permite carregar dados em massa através de arquivos CSV ou Excel.")

            uploaded_file = st.file_uploader(
                "Escolha um arquivo para importar",
                type=["csv", "xlsx"]
            )

            if uploaded_file:
                st.warning("Funcionalidade em desenvolvimento. Em breve você poderá importar seus dados aqui!")

    except ImportError as e:
        logger.error(f"Erro ao importar módulo da página {st.session_state.current_page}: {str(e)}")
        st.error(f"Erro ao carregar página {st.session_state.current_page}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao exibir página {st.session_state.current_page}: {str(e)}")
        st.error(f"Erro ao exibir página {st.session_state.current_page}: {str(e)}")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; color: #888888; font-size: 0.8em;'>Sistema Personal Organizer</div>", unsafe_allow_html=True)