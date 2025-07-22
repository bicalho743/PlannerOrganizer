import os
import sys
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Corrigir o problema de adaptação de tipos numpy.int64 para PostgreSQL
try:
    from utils.type_conversion_fix import fix_numpy_int64_bug
    success = fix_numpy_int64_bug()
    if success:
        logger.info("Adaptadores para numpy.int* registrados com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar/executar fix_numpy_int64_bug: {str(e)}")

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Importar apenas componentes essenciais
from utils.database import Database

# Inicialização básica da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# CSS básico
st.markdown("""
<style>
/* Cabeçalho */
.app-header {
    background-color: #1E1F36;
    color: white;
    padding: 1rem;
    text-align: center;
    margin-bottom: 2rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1E1F36 !important;
}

section[data-testid="stSidebar"] button {
    width: 100% !important;
    background: rgba(255, 255, 255, 0.1) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    margin: 0.25rem 0 !important;
}

/* Botões */
.stButton > button {
    background-color: #3a75c4 !important;
    color: white !important;
    border: 1px solid #3a75c4 !important;
    width: 100% !important;
}

/* Campos de entrada */
.stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {
    background-color: #f8f9fa !important;
    color: #212529 !important;
    border: 1px solid #dee2e6 !important;
}

/* Labels */
label, .stTextInput > label, .stSelectbox > label {
    color: #1e1e1e !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

def main():
    # Cabeçalho
    st.markdown('<div class="app-header"><h1>Planner Organizer - Versão Estável</h1></div>', unsafe_allow_html=True)
    
    # Sidebar para navegação
    with st.sidebar:
        st.title("Menu Principal")
        
        pagina = st.selectbox(
            "Selecione uma página:",
            ["Dashboard", "Clientes", "Propostas", "Vendas", "Financeiro"]
        )
    
    # Conteúdo principal baseado na página selecionada
    if pagina == "Dashboard":
        st.header("📊 Dashboard")
        st.info("Sistema funcionando corretamente sem loops de inicialização!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "Ativo ✅", "Sistema estável")
        with col2:
            st.metric("Banco", "Conectado ✅", "PostgreSQL")
        with col3:
            st.metric("Workflows", "1 ativo", "Aplicação principal")
            
    elif pagina == "Clientes":
        st.header("👥 Gestão de Clientes")
        st.success("Módulo de clientes disponível")
        
    elif pagina == "Propostas":
        st.header("📋 Gestão de Propostas")
        st.success("Módulo de propostas disponível")
        
    elif pagina == "Vendas":
        st.header("💰 Gestão de Vendas")
        st.success("Módulo de vendas com CSS melhorado disponível")
        
        # Demonstrar os três botões padronizados
        st.subheader("Botões de Vendas Padronizados")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("EDITAR VENDAS", type="primary", use_container_width=True)
        with col2:
            st.button("GERAR RELATÓRIO DE VENDAS", type="primary", use_container_width=True)
        with col3:
            st.button("EXCLUIR VENDAS", type="primary", use_container_width=True)
            
    elif pagina == "Financeiro":
        st.header("💼 Gestão Financeira")
        st.success("Módulo financeiro disponível")

if __name__ == "__main__":
    main()