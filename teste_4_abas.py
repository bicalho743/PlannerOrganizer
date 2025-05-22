import streamlit as st

st.set_page_config(page_title="Teste 4 Abas", layout="wide")

st.title("Teste das 4 Abas")

# Criar 4 abas simples
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Nova Proposta", 
    "⚙️ Em Execução", 
    "📋 Propostas Finalizadas",
    "🔍 Todas as Propostas"
])

with tab1:
    st.header("Aba 1 - Nova Proposta")
    st.write("Esta é a primeira aba")

with tab2:
    st.header("Aba 2 - Em Execução")
    st.write("Esta é a segunda aba")

with tab3:
    st.header("Aba 3 - Propostas Finalizadas")
    st.write("Esta é a terceira aba")

with tab4:
    st.header("Aba 4 - Todas as Propostas")
    st.write("Esta é a quarta aba - FUNCIONOU!")
    st.success("Se você está vendo esta mensagem, a quarta aba está funcionando!")