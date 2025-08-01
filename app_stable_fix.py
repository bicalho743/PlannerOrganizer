"""
Aplicação Streamlit estável - Sistema de Gestão
Versão simplificada para correção do problema de loop
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, date, timedelta
import traceback

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal 
st.title("📊 Planner Organizer - Sistema de Gestão")

# Verificar se há problemas de importação
try:
    from utils.database import Database
    
    # Verificar se está logado (sem Firebase por enquanto)
    if 'usuario_logado' not in st.session_state:
        st.session_state.usuario_logado = True  # Temporariamente sempre logado
    
    # Inicializar banco de dados se não existir
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Menu lateral
    with st.sidebar:
        st.header("Menu Principal")
        page = st.selectbox(
            "Selecione uma página:",
            ["Dashboard", "Vendas", "Clientes", "Propostas", "Financeiro"]
        )
    
    # Carregar a página selecionada
    if page == "Dashboard":
        st.header("Dashboard")
        
        # Métricas básicas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Vendas do Mês", "12", "↑ 20%")
        with col2:
            st.metric("Receita Total", "R$ 15.240,00", "↑ 15%")
        with col3:
            st.metric("Clientes Ativos", "45", "↑ 5%")
        with col4:
            st.metric("Propostas Abertas", "8", "→ 0%")
            
        st.success("Sistema funcionando corretamente!")
        
    elif page == "Vendas":
        st.header("🛒 Vendas")
        
        # Tentar carregar o módulo de vendas
        try:
            from pages import vendas
            vendas.show()
        except Exception as e:
            st.error(f"Erro ao carregar módulo de vendas: {str(e)}")
            st.info("Use o sistema básico por enquanto")
            
    elif page == "Clientes":
        st.header("👥 Clientes")
        
        try:
            from pages import clientes
            clientes.show()
        except Exception as e:
            st.error(f"Erro ao carregar módulo de clientes: {str(e)}")
            
    elif page == "Propostas":
        st.header("📋 Propostas")
        
        try:
            from pages import propostas_unificado
            propostas_unificado.show()
        except Exception as e:
            st.error(f"Erro ao carregar módulo de propostas: {str(e)}")
            
    elif page == "Financeiro":
        st.header("💰 Financeiro")
        
        try:
            from pages import financeiro
            financeiro.show()
        except Exception as e:
            st.error(f"Erro ao carregar módulo financeiro: {str(e)}")

except Exception as e:
    st.error("Erro na aplicação principal")
    st.error(f"Detalhes: {str(e)}")
    
    # Mostrar traceback apenas para debug
    if st.checkbox("Mostrar detalhes técnicos"):
        st.code(traceback.format_exc())
        
    st.info("A aplicação está em modo de recuperação. Alguns recursos podem estar indisponíveis.")