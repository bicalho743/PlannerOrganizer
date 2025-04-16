import os
import sys
import streamlit as st
import logging
import pandas as pd
from datetime import datetime

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

# Carregar CSS customizado do arquivo style.css
with open('.streamlit/style.css', 'r') as f:
    custom_css = f.read()

# Adicionar estilo CSS personalizado para tema profissional
st.markdown(f"""
    <style>
    {custom_css}
    
    /* Estilo específico para a barra lateral */
    section[data-testid="stSidebar"] {{
        background-color: #F9FAFB;
        border-right: 1px solid #E0E0E0;
    }}

    div.block-container {{
        padding-top: 0;
    }}

    /* Estilo para botões do menu */
    div.stButton > button {{
        width: 100%;
        background-color: #1E88E5 !important;
        color: white !important;
        font-weight: 500;
        text-align: left;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        transition: all 0.2s ease;
    }}

    div.stButton > button:hover {{
        background-color: #1976D2 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }}

    /* Container para os botões */
    div.nav-buttons {{
        padding: 1rem;
        margin: 0 -1rem;
    }}
    
    /* Esconde os links nativos do Streamlit na barra lateral */
    section[data-testid="stSidebar"] .element-container:has(svg[xmlns="http://www.w3.org/2000/svg"]) {{
        display: none;
    }}
    
    /* Esconde o seletor de páginas nativo do Streamlit */
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Estilos para os links de navegação personalizados */
    .navigation-links a {{
        display: block;
        padding: 8px 12px;
        margin: 4px 0;
        text-decoration: none;
        color: #1E366F;
        border-radius: 4px;
        transition: all 0.2s ease;
    }}
    
    .navigation-links a:hover {{
        background-color: #E3F2FD;
        color: #1976D2 !important;
    }}
    
    /* Esconde o botão de hamburger do Streamlit */
    button[kind="header"] {{
        display: none !important;
    }}
    
    /* Remove excesso de padding na barra lateral */
    .st-emotion-cache-16txtl3 {{
        padding-top: 1rem !important;
    }}
    
    /* Título no topo */
    h1 {{
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        color: #1E366F;
        font-weight: 600;
    }}
    
    /* Expanders na sidebar */
    .sidebar .st-expander {{
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    
    /* Cabeçalho do expander */
    .sidebar .st-expander > div:first-child {{
        background-color: #F5F7FA;
        padding: 0.75rem;
    }}
    </style>
""", unsafe_allow_html=True)

# Título principal do menu
# Adicionar frase motivacional acima do menu principal
st.sidebar.markdown("""
<div style="font-size: 0.9rem; color: #1E366F; margin-bottom: 1.5rem; text-align: center; font-style: italic; padding: 15px; background-color: #E3F2FD; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
    "Transforme sua organização em resultados: gerencie propostas, clientes e finanças com precisão profissional."
</div>
""", unsafe_allow_html=True)

# Título do menu
st.sidebar.markdown("""
<h1 style="font-size: 1.6rem; color: #1E366F; margin-bottom: 1.5rem; text-align: center; font-weight: 600;">
    Planner Organizer<br>
    <span style="font-size: 0.9rem; color: #5A6A85; font-weight: 400;">Sistema Profissional de Gestão Personal Organizer</span>
</h1>
""", unsafe_allow_html=True)

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
    "🛒 Vendas": "Vendas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios"
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
    elif st.session_state.current_page == "Vendas":
        from pages.vendas import show
        show()
    elif st.session_state.current_page == "Financeiro":
        from pages.financeiro import show
        show()
    elif st.session_state.current_page == "Relatórios":
        from pages.relatorios import show
        show()
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Divisor antes das informações do sistema
st.sidebar.markdown('<div style="margin: 1.5rem 0;"><hr style="border: none; height: 1px; background-color: #E0E0E0;"></div>', unsafe_allow_html=True)

# Seção de Informações do Sistema na barra lateral
informacoes_html = """
<div style="margin-bottom: 1rem;">
    <!-- Cabeçalho das informações -->
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.8rem; background-color: #E3F2FD; border-radius: 6px;">
        <h3 style="margin:0; color: #1E366F; font-size: 1.1rem;">ℹ️ Informações do Sistema</h3>
    </div>
    
    <!-- Conteúdo das informações -->
    <div style="padding: 0.8rem; background-color: white; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <h3 style="color: #1E366F; font-size: 1.2rem; margin-bottom: 1rem; border-bottom: 1px solid #E0E0E0; padding-bottom: 0.5rem;">Planner Organizer</h3>
        <p style="margin-bottom: 0.5rem;"><strong>Versão:</strong> 1.0.4</p>
        
        <p style="margin-top: 1.2rem; margin-bottom: 0.5rem;"><strong style="color: #1E366F;">Módulos do Sistema:</strong></p>
        <ul style="margin-top: 0; padding-left: 1.5rem;">
            <li style="margin-bottom: 0.5rem;"><strong style="color: #1976D2;">Dashboard</strong> - Visão geral com métricas, alertas de retorno de clientes e indicadores financeiros</li>
            <li style="margin-bottom: 0.5rem;"><strong style="color: #1976D2;">Cadastros</strong> - Gerenciamento completo de clientes, fornecedores, parceiros e assistentes</li>
            <li style="margin-bottom: 0.5rem;"><strong style="color: #1976D2;">Propostas</strong> - Ciclo completo de propostas desde elaboração até aprovação e finalização</li>
            <li style="margin-bottom: 0.5rem;"><strong style="color: #1976D2;">Vendas</strong> - Controle de produtos vendidos, quantidades e valores por cliente</li>
            <li style="margin-bottom: 0.5rem;"><strong style="color: #1976D2;">Financeiro</strong> - Gestão de receitas, despesas, contas a pagar e receber</li>
            <li style="margin-bottom: 0.5rem;"><strong style="color: #1976D2;">Relatórios</strong> - Análises e visualizações detalhadas de desempenho</li>
        </ul>
        
        <p style="margin-top: 1.2rem; margin-bottom: 0.5rem;"><strong style="color: #1E366F;">Funcionalidades Principais:</strong></p>
        <ul style="margin-top: 0; padding-left: 1.5rem;">
            <li style="margin-bottom: 0.3rem;">✅ Fluxo de propostas: Em elaboração → Aguardando aprovação → Aprovada → Em execução → Finalizada</li>
            <li style="margin-bottom: 0.3rem;">✅ Integração automática entre módulos (Propostas/Financeiro/Vendas)</li>
            <li style="margin-bottom: 0.3rem;">✅ Sistema de alertas para propostas próximas do prazo</li>
            <li style="margin-bottom: 0.3rem;">✅ Geração automática de lançamentos financeiros</li>
            <li style="margin-bottom: 0.3rem;">✅ Cálculo automático de comissões para fornecedores</li>
            <li style="margin-bottom: 0.3rem;">✅ Importação em lote de clientes e propostas</li>
            <li style="margin-bottom: 0.3rem;">✅ Sistema de backup e restauração de dados</li>
        </ul>
        
        <p style="margin-top: 1.2rem; margin-bottom: 0.5rem;"><strong style="color: #1E366F;">Novidades da Versão:</strong></p>
        <ul style="margin-top: 0; padding-left: 1.5rem;">
            <li style="margin-bottom: 0.3rem;">🎉 Telas de celebração para conclusão de tarefas</li>
            <li style="margin-bottom: 0.3rem;">📊 Dashboard com métricas de desempenho em tempo real</li>
            <li style="margin-bottom: 0.3rem;">📱 Interface responsiva para diferentes dispositivos</li>
            <li style="margin-bottom: 0.3rem;">🎨 Tema profissional com visual corporativo</li>
            <li style="margin-bottom: 0.3rem;">🧹 Seleção múltipla para exclusões em lote</li>
        </ul>
        
        <div style="margin-top: 1.5rem; text-align: center; padding-top: 1rem; border-top: 1px solid #E0E0E0;">
            <p style="font-size: 0.9rem; color: #5A6A85;">
                Desenvolvido com ❤️ para Personal Organizers
            </p>
            <p style="font-size: 0.8rem; color: #5A6A85; margin-top: 0.3rem;">
                © 2025 Planner Organizer
            </p>
        </div>
    </div>
</div>
"""

# Exibir as informações do sistema
st.sidebar.markdown(informacoes_html, unsafe_allow_html=True)

# Links de navegação ocultos em um expander para desenvolvedores
with st.sidebar.expander("🔧 Acesso Desenvolvedor", expanded=False):
    st.markdown("""
    <div style="padding: 0.5rem; background-color: white; border-radius: 4px;">
        <h4 style="color: #1E366F; font-size: 1rem; margin-bottom: 0.8rem;">Navegação Rápida</h4>
        
        <div class="navigation-links">
            <a href="/" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Home (App)</a>
            <a href="/cadastros" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Cadastros</a>
            <a href="/dashboard" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Dashboard</a>
            <a href="/dashboard_fixed" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Dashboard (Fixed)</a>
            <a href="/financeiro" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Financeiro</a>
            <a href="/propostas" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Propostas</a>
            <a href="/relatorios" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Relatórios</a>
            <a href="/vendas" style="display: block; padding: 8px 12px; margin: 4px 0; border-radius: 4px; background-color: #F5F7FA; color: #1E366F; text-decoration: none; font-size: 0.85rem;">Vendas</a>
        </div>
        
        <p style="margin-top: 1rem; font-size: 0.8rem; color: #5A6A85; text-align: center;">
            Acesso exclusivo para desenvolvedores
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sem botão de importação conforme solicitado

# A navegação é controlada pelos botões do menu principal
# Os botões já atualizam st.session_state.current_page

# O conteúdo principal já é exibido acima através da importação dos módulos
# Não precisamos processar novamente os módulos
if False:
    module_name = st.session_state.current_page.lower()
    try:
        module = __import__(f"pages.{module_name}", fromlist=["show"])
        module.show()
    except ImportError as e:
        st.error(f"Erro ao carregar módulo {module_name}: {str(e)}")
# Não temos mais a opção de importação no menu