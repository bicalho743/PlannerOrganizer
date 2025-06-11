import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
try:
    st.set_page_config(
        page_title="Examinar Tabela Propostas",
        page_icon="🔍",
        layout="wide"
    )
except:
    pass

st.title("🔍 Examinar Tabela de Propostas")
st.write("Esta ferramenta permite examinar e analisar a estrutura da tabela de propostas.")

# Inicializar banco de dados
@st.cache_resource
def get_database():
    try:
        from utils.database import Database
        return Database()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco: {str(e)}")
        return None

db = get_database()
if db is None:
    st.error("Não foi possível conectar ao banco de dados.")
    st.stop()

# Examinar propostas
try:
    propostas = db.get_propostas()
    
    if not propostas.empty:
        st.success(f"Total de propostas encontradas: {len(propostas)}")
        
        # Mostrar informações da tabela
        st.subheader("Estrutura da Tabela")
        st.write(f"Colunas: {list(propostas.columns)}")
        st.write(f"Tipos de dados:")
        st.write(propostas.dtypes)
        
        # Mostrar amostra dos dados
        st.subheader("Amostra dos Dados")
        st.dataframe(propostas.head(10))
        
        # Estatísticas básicas
        st.subheader("Estatísticas")
        if 'status' in propostas.columns:
            st.write("Distribuição por Status:")
            st.write(propostas['status'].value_counts())
        
        if 'valor' in propostas.columns:
            st.write("Estatísticas de Valor:")
            st.write(propostas['valor'].describe())
    else:
        st.warning("Nenhuma proposta encontrada na tabela.")
        
except Exception as e:
    st.error(f"Erro ao examinar propostas: {str(e)}")

# Botão de atualização
if st.button("🔄 Atualizar Dados"):
    st.rerun()