import os
import sys
import streamlit as st
from datetime import datetime
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Sistema Personal Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from utils.database import Database
    
    # Inicialização da base de dados
    if 'db' not in st.session_state:
        st.session_state.db = Database()

    # Dashboard - Página Principal
    st.title("📋 Sistema de Gestão - Personal Organizer")

    # Add test data button in sidebar if database is empty
    clientes = st.session_state.db.get_clientes()
    if clientes.empty:
        st.sidebar.warning("Banco de dados vazio")
        if st.sidebar.button("Adicionar Dados de Teste"):
            if st.session_state.db.add_test_data():
                st.sidebar.success("Dados de teste adicionados com sucesso!")
                st.rerun()
            else:
                st.sidebar.error("Erro ao adicionar dados de teste")

    # Seleção de página
    pagina = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Propostas", "Clientes", "Financeiro", "Relatórios"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                        else f"📝 {x}" if x == "Propostas"
                        else f"👥 {x}" if x == "Clientes"
                        else f"💰 {x}" if x == "Financeiro"
                        else f"📈 {x}"  # Relatórios
    )

    # Roteamento de páginas
    if pagina == "Dashboard":
        import pages.dashboard as dashboard
        dashboard.show()
    elif pagina == "Propostas":
        import pages.propostas as propostas
        propostas.show()
    elif pagina == "Clientes":
        import pages.clientes as clientes
        clientes.show()
    elif pagina == "Financeiro":
        import pages.financeiro as financeiro
        financeiro.show()
    elif pagina == "Relatórios":
        import pages.relatorios as relatorios
        relatorios.show()

except Exception as e:
    st.error(f"Erro ao inicializar aplicação: {str(e)}")
    st.exception(e)
