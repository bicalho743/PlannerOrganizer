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

# Log de início da aplicação
logger.info("Iniciando aplicação Planner Organizer")

# Configuração da página
try:
    logger.info("Configurando página Streamlit")
    st.set_page_config(
        page_title="Planner Organizer",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Importar e carregar estilos personalizados
    from src.utils.custom_styles import load_custom_styles
    load_custom_styles()

    logger.info("Página configurada com sucesso")
except Exception as e:
    logger.error(f"Erro na configuração da página: {str(e)}")
    st.error(f"Erro na configuração da página: {str(e)}")
    st.stop()

try:
    # Verificar variáveis de ambiente críticas
    logger.info("Verificando variáveis de ambiente")
    required_env_vars = ['DATABASE_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
        st.error(f"Configuração incompleta. Faltam variáveis: {', '.join(missing_vars)}")
        st.stop()

    # Importar módulo de banco de dados
    logger.info("Importando módulo de banco de dados")
    from utils.database import Database

    # Inicialização da sessão
    if 'initialized' not in st.session_state:
        logger.info("Inicializando sessão e banco de dados")
        st.session_state.initialized = True
        try:
            st.session_state.db = Database()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.error(f"Erro ao conectar com banco de dados: {str(e)}")
            st.stop()

    # Inicializar variável de controle da apresentação
    if 'mostrar_apresentacao' not in st.session_state:
        st.session_state.mostrar_apresentacao = False

    # Menu na barra lateral
    logger.info("Criando menu na barra lateral")
    with st.sidebar:
        st.title("Menu Principal")

        # Seleção de página em ordem correta
        dashboard_btn = st.button("📊 Dashboard", use_container_width=True)
        cadastros_btn = st.button("👥 Cadastros", use_container_width=True)
        propostas_btn = st.button("📝 Propostas", use_container_width=True)
        financeiro_btn = st.button("💰 Financeiro", use_container_width=True)
        relatorios_btn = st.button("📈 Relatórios", use_container_width=True)

        # Separador antes das informações do sistema
        st.markdown("---")

        # Expander para informações do sistema
        with st.expander("ℹ️ Informações do Sistema"):
            if st.button("📌 Sobre o Sistema"):
                st.session_state.mostrar_apresentacao = True
            st.markdown("Versão 1.0")
            st.markdown("Desenvolvido com ❤️ usando Streamlit")

    # Determinar a página selecionada com base nos botões
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"  # Página padrão

    if dashboard_btn:
        st.session_state.current_page = "Dashboard"
    elif cadastros_btn:
        st.session_state.current_page = "Cadastros"
    elif propostas_btn:
        st.session_state.current_page = "Propostas"
    elif financeiro_btn:
        st.session_state.current_page = "Financeiro"
    elif relatorios_btn:
        st.session_state.current_page = "Relatórios"

    pagina = st.session_state.current_page
    logger.info(f"Página selecionada: {pagina}")

    # Se a apresentação estiver ativa, mostrar na área principal
    if st.session_state.mostrar_apresentacao:
        st.title("👋 Bem-vindo ao seu assistente de organização!")

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
            logger.info(f"Tentando carregar página: {pagina}")
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
            logger.info(f"Página {pagina} carregada com sucesso")
        except ImportError as e:
            logger.error(f"Erro ao importar módulo da página {pagina}: {str(e)}")
            st.error(f"Erro ao carregar página {pagina}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao exibir página {pagina}: {str(e)}")
            st.error(f"Erro ao exibir página {pagina}: {str(e)}")

    logger.info("Aplicação carregada com sucesso")

except Exception as e:
    logger.error(f"Erro durante a execução da aplicação: {str(e)}")
    st.error(f"Erro durante a execução da aplicação: {str(e)}")