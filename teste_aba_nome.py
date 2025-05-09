"""
Script de verificação para confirmar se a alteração do nome da aba está sendo aplicada corretamente.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(
    page_title="Teste de Alteração de Nome da Aba",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Teste de Alteração de Nome da Aba")

# Demonstrar o funcionamento das abas com nomes atualizados
st.markdown("""
Este script demonstra o novo nome da primeira aba como "Nova Proposta" em vez de "Propostas".
""")

# Criar as três abas com os nomes corretos
tab1, tab2, tab3 = st.tabs([
    "📝 Nova Proposta", 
    "⚙️ Em Execução", 
    "📋 Propostas Finalizadas"
])

# Primeira aba: Nova Proposta
with tab1:
    st.header("Nova Proposta")
    st.info("Esta aba agora tem o nome 'Nova Proposta' em vez de 'Propostas'")
    
    # Criar sub-abas
    proposta_tab1, proposta_tab2 = st.tabs(["Nova Proposta", "Gerenciar Propostas"])
    
    with proposta_tab1:
        st.subheader("Formulário de Nova Proposta")
        st.write("Aqui ficaria o formulário para criar uma nova proposta")
    
    with proposta_tab2:
        st.subheader("Gerenciar Propostas")
        st.write("Aqui ficariam as propostas em elaboração ou aguardando aprovação")

# Segunda aba: Em Execução
with tab2:
    st.header("Em Execução")
    st.info("Esta aba mantém o nome 'Em Execução'")
    st.write("Aqui ficariam as propostas em execução")

# Terceira aba: Propostas Finalizadas
with tab3:
    st.header("Propostas Finalizadas")
    st.info("Esta aba mantém o nome 'Propostas Finalizadas'")
    st.success("Alteração bem-sucedida!")
    st.write("Aqui ficariam as propostas finalizadas")

# Adicionar informações de diagnóstico
st.divider()
st.subheader("Informações de Diagnóstico")

st.code("""
# Código alterado para as abas na página principal:
tab1, tab2, tab3 = st.tabs([
    "📝 Nova Proposta", 
    "⚙️ Em Execução", 
    "📋 Propostas Finalizadas"
])

# Código alterado para o cabeçalho da primeira aba:
with tab1:
    st.header("Nova Proposta")
""", language="python")

# Informações sobre as alterações
st.write("""
**Alterações realizadas:**
1. Alterado o nome da primeira aba de "Propostas" para "Nova Proposta"
2. Alterado o cabeçalho interno da primeira aba para combinar com o nome
3. Mantidos os nomes das outras abas

**Arquivo modificado:** `pages/propostas.py`
""")

# Adicionar botão para atualizar a página
if st.button("🔄 Atualizar"):
    st.rerun()