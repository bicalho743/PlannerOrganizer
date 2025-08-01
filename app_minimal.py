"""
Versão mínima para teste - Planner Organizer
"""
import streamlit as st

st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Planner Organizer - Sistema de Gestão")

# Teste básico
st.success("Aplicação carregada com sucesso!")

# Menu simples
page = st.sidebar.selectbox("Menu", ["Dashboard", "Teste"])

if page == "Dashboard":
    st.header("Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Vendas", "12")
    with col2:
        st.metric("Receita", "R$ 15.240")  
    with col3:
        st.metric("Clientes", "45")
    with col4:
        st.metric("Propostas", "8")
        
    st.info("Sistema funcionando em modo básico")
    
else:
    st.header("Teste")
    st.write("Página de teste carregada!")
    
    if st.button("Testar Conexão"):
        st.success("Conexão OK!")