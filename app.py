import os
import sys
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

from utils.database import Database

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do banco de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
        st.success("Conexão com o banco de dados estabelecida com sucesso!")
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. O endpoint pode estar desabilitado.")
        st.warning("Se você estiver usando Neon PostgreSQL ou outro banco de dados serverless, você precisa reativar o endpoint.")
        
        # Mostrar informação sobre o DATABASE_URL (sem mostrar credenciais)
        db_url = os.getenv('DATABASE_URL', 'Não definido')
        if db_url:
            # Esconder credenciais na mensagem
            safe_url = db_url.split('@')
            if len(safe_url) > 1:
                host_part = safe_url[1]
                st.info(f"Sua conexão de banco de dados aponta para: ...@{host_part}")
            else:
                st.info("DATABASE_URL está definido, mas não está no formato esperado.")
        else:
            st.info("A variável de ambiente DATABASE_URL não está definida.")
        
        st.error(f"Detalhes do erro: {str(e)}")
        st.stop()

# Estilo CSS customizado para garantir o menu no topo
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background-color: #262730;
    }

    div.block-container {
        padding-top: 0;
    }

    div.stButton > button {
        width: 100%;
        background-color: #F1A208 !important;
        color: #262730 !important;
        font-weight: 500;
        text-align: left;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }

    div.stButton > button:hover {
        background-color: #ffc107 !important;
    }

    /* Container escuro para os botões */
    div.nav-buttons {
        background-color: #262730;
        padding: 1rem;
        margin: 0 -1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Menu principal (deve aparecer no topo)
st.sidebar.title("Menu Principal")

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definição do menu principal
MENU_PRINCIPAL = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios",
    "📥 Importação": "Importar"
}

# Criação dos botões do menu principal
for label, page in MENU_PRINCIPAL.items():
    if st.sidebar.button(label, key=f"main_menu_{page.lower()}", use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

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
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Informações do sistema no final
st.sidebar.markdown("---")
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

    # Botão de importação de propostas
    if st.button("📥 Importar Propostas", key="btn_import_propostas_sidebar", use_container_width=True):
        st.session_state.current_page = "Importar"
        st.rerun()

# A navegação é controlada pelos botões do menu principal
# Os botões já atualizam st.session_state.current_page

# Conteúdo principal da página atual
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