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
    import utils
    from utils.database import Database
    from utils.celebration import toggle_celebration, show_celebration
    import utils.importador
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
    /* Estilo para botões principais */
    div.stButton > button {
        width: 100%;
        text-align: left;
        padding: 0.75rem 1rem;
        background-color: #F1A208 !important;
        color: #262730 !important;
        font-weight: 600;
        margin-bottom: 0.4rem;
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #ffc107 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    /* Estilo para a barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        color: white;
    }
    
    /* Container para os botões do menu */
    div.nav-buttons {
        background-color: #1E293B;
        padding: 1.2rem;
        margin: 0 -1rem;
        border-radius: 0 0 10px 10px;
    }
    
    /* Estilo para os expanders de informações */
    div.streamlit-expanderHeader {
        background-color: #3B82F6 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.8rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    div.streamlit-expanderHeader:hover {
        background-color: #2563EB !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    div.streamlit-expanderContent {
        background-color: #2A3F5F !important;
        color: white !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
        margin-top: -0.5rem !important;
        border: 1px solid #3B82F6 !important;
    }
    
    /* Ajustes para texto dentro dos expanders */
    div.streamlit-expanderContent p, div.streamlit-expanderContent li {
        color: #E2E8F0 !important;
    }
    
    div.streamlit-expanderContent h3 {
        color: #F1A208 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    div.streamlit-expanderContent strong {
        color: #F8FAFC !important;
    }
    
    /* Customização do título do sidebar */
    section[data-testid="stSidebar"] .stMarkdown h1 {
        color: #F1A208 !important;
        margin-bottom: 1rem !important;
        font-size: 1.5rem !important;
        text-align: center !important;
        padding-top: 1rem !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Personalização para separadores */
    hr {
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Menu principal - com cabeçalho melhorado
st.sidebar.markdown("""
<div style='text-align: center; padding: 15px; background-color: #1E293B; border-bottom: 3px solid #F1A208; margin-bottom: 20px;'>
    <img src="https://cdn-icons-png.flaticon.com/512/3208/3208615.png" width="60" style='margin-bottom: 10px;'>
    <h1 style='color: #F1A208; font-size: 1.5rem; margin: 5px 0;'>PLANNER ORGANIZER</h1>
    <p style='color: #E2E8F0; font-size: 0.8rem; margin: 0;'>Sistema de Gestão Profissional</p>
</div>
""", unsafe_allow_html=True)

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
    "🛒 Vendas": "Vendas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios"
}

# Criar botões para cada página
for label, page_key in MENU_PRINCIPAL.items():
    if st.sidebar.button(label, key=f"menu_{page_key.lower()}", use_container_width=True):
        st.session_state.current_page = page_key
        st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Informações do sistema no final
st.sidebar.markdown("---")

# Cabeçalho personalizado para as seções do sistema
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #F1A208; margin-bottom: 10px; font-size: 1.3rem;'>INFORMAÇÕES DO SISTEMA</h2>
    <p style='color: #E2E8F0; font-size: 0.9rem;'>Confira recursos e funcionalidades abaixo</p>
    <div style='background-color: #F1A208; height: 3px; width: 50%; margin: 10px auto;'></div>
</div>
""", unsafe_allow_html=True)

# Sobre o Sistema - com botão personalizado
st.sidebar.markdown("""
<div class='system-info-button' onclick="document.querySelector('#sobre-sistema-expander button').click();" 
     style='background-color: #3B82F6; padding: 12px; border-radius: 10px; margin-bottom: 15px; cursor: pointer; 
     box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;'>
    <div style='display: flex; align-items: center;'>
        <div style='font-size: 24px; margin-right: 10px;'>📌</div>
        <div>
            <div style='font-weight: bold; font-size: 1.1rem; color: white;'>Sobre o Sistema</div>
            <div style='color: rgba(255,255,255,0.8); font-size: 0.8rem;'>Funcionalidades e recursos</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# O expander real (que será controlado pelo botão acima)
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
    
    **🛒 Gestão de Vendas**
    - Cadastro de produtos
    - Controle de estoque
    - Registro de vendas
    - Histórico de transações

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

# Informações do Sistema - com botão personalizado
st.sidebar.markdown("""
<div class='system-info-button' onclick="document.querySelector('#info-sistema-expander button').click();" 
     style='background-color: #2563EB; padding: 12px; border-radius: 10px; margin-bottom: 15px; cursor: pointer; 
     box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;'>
    <div style='display: flex; align-items: center;'>
        <div style='font-size: 24px; margin-right: 10px;'>ℹ️</div>
        <div>
            <div style='font-weight: bold; font-size: 1.1rem; color: white;'>Informações do Sistema</div>
            <div style='color: rgba(255,255,255,0.8); font-size: 0.8rem;'>Versão e atualizações recentes</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# O expander real (que será controlado pelo botão acima)
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.markdown("""
    ### Sistema Personal Organizer
    **Versão:** 1.1.0

    **Recursos Disponíveis:**
    - ✅ Gestão de Clientes
    - ✅ Controle de Propostas
    - ✅ Gestão de Vendas e Produtos
    - ✅ Gestão Financeira
    - ✅ Relatórios e Análises
    - ✅ Importação de Dados

    **Novidades:**
    - 🛒 Sistema de vendas e controle de estoque
    - 🎉 Telas de celebração
    - 📊 Dashboard aprimorado
    - 📱 Interface responsiva

    <div style='text-align: center; margin-top: 20px; padding: 10px; background-color: #1E293B; border-radius: 5px;'>
    Desenvolvido com ❤️ usando Streamlit
    </div>
    """, unsafe_allow_html=True)

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
        elif st.session_state.current_page == "Vendas":
            from pages.vendas import show
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
                ["Clientes", "Propostas", "Fornecedores", "Assistentes", "Parceiros", "Produtos"]
            )

            st.info(f"A importação de {import_type} permite carregar dados em massa através de arquivos CSV ou Excel.")

            uploaded_file = st.file_uploader(
                "Escolha um arquivo para importar",
                type=["csv", "xlsx"]
            )

            # Download de template
            col1, col2 = st.columns(2)
            with col1:
                st.write("### Template para Importação")
                # Botão para baixar template CSV
                st.download_button(
                    label=f"Baixar Template CSV",
                    data=utils.importador.gerar_template_csv(import_type),
                    file_name=f"template_{import_type.lower()}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Botão para baixar template Excel
                st.write("&nbsp;")  # Para alinhar com o título da coluna 1
                st.download_button(
                    label=f"Baixar Template Excel",
                    data=utils.importador.gerar_template_excel(import_type),
                    file_name=f"template_{import_type.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            if uploaded_file:
                try:
                    # Importar dados baseado no tipo selecionado
                    if import_type == "Propostas":
                        success, message = utils.importador.importar_propostas(uploaded_file, st.session_state.db)
                    else:
                        # Usar a função genérica para outros tipos de cadastro
                        success, message = utils.importador.importar_cadastros(
                            arquivo=uploaded_file,
                            tipo_cadastro=import_type.rstrip('s'),  # Remover o 's' do plural
                            db=st.session_state.db
                        )
                    
                    if success:
                        st.success(message)
                        # Adicionar opção de celebração
                        if st.button("🎉 Celebrar Importação", key="celebrate_import"):
                            toggle_celebration(
                                task_name="Importação Concluída",
                                custom_message=f"Importação de {import_type} realizada com sucesso!"
                            )
                            st.rerun()
                    else:
                        st.error(message)
                
                except Exception as e:
                    st.error(f"Erro durante a importação: {str(e)}")

    except ImportError as e:
        logger.error(f"Erro ao importar módulo da página {st.session_state.current_page}: {str(e)}")
        st.error(f"Erro ao carregar página {st.session_state.current_page}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao exibir página {st.session_state.current_page}: {str(e)}")
        st.error(f"Erro ao exibir página {st.session_state.current_page}: {str(e)}")

# Rodapé melhorado
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 15px; margin-top: 10px;'>
    <div style='font-weight: bold; color: #F1A208; margin-bottom: 5px; font-size: 1rem;'>Sistema Planner Organizer</div>
    <div style='color: #E2E8F0; font-size: 0.7rem; margin-bottom: 10px;'>© 2025 - Todos os direitos reservados</div>
    <div style='display: flex; justify-content: center; margin-top: 5px;'>
        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: #F1A208; display: flex; 
                 justify-content: center; align-items: center; margin: 0 5px; font-size: 15px;'>📱</div>
        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: #F1A208; display: flex; 
                 justify-content: center; align-items: center; margin: 0 5px; font-size: 15px;'>💼</div>
        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: #F1A208; display: flex; 
                 justify-content: center; align-items: center; margin: 0 5px; font-size: 15px;'>📈</div>
    </div>
</div>
""", unsafe_allow_html=True)