import streamlit as st
from utils.database import Database

st.set_page_config(
    page_title="Sistema Personal Organizer",
    page_icon="📋",
    layout="wide"
)

# Inicialização da base de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Título principal
st.title("📋 Sistema de Gestão - Personal Organizer")

# Menu lateral
st.sidebar.title("Menu Principal")
pagina = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Clientes", "Propostas", "Financeiro", "Produtos", "Relatórios"]
)

# Dashboard principal
if pagina == "Dashboard":
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Resumo")
        
        # Estatísticas básicas
        clientes = st.session_state.db.get_clientes()
        propostas = st.session_state.db.get_propostas()
        financeiro = st.session_state.db.get_financeiro()
        
        st.metric("Total de Clientes", len(clientes))
        st.metric("Propostas Ativas", 
                 len(propostas[propostas['status'] == 'Aberta']))
        
        # Resumo financeiro
        receitas = financeiro[financeiro['tipo'] == 'receita']['valor'].sum()
        despesas = financeiro[financeiro['tipo'] == 'despesa']['valor'].sum()
        saldo = receitas - despesas
        
        st.metric("Saldo Total", f"R$ {saldo:.2f}")
    
    with col2:
        st.subheader("📅 Atividades Recentes")
        
        # Últimas propostas
        st.write("Últimas Propostas:")
        ultimas_propostas = propostas.sort_values('data_proposta', ascending=False).head(5)
        st.dataframe(ultimas_propostas[['descricao', 'valor', 'status', 'data_proposta']])
        
        # Últimas transações
        st.write("Últimas Transações:")
        ultimas_transacoes = financeiro.sort_values('data', ascending=False).head(5)
        st.dataframe(ultimas_transacoes[['descricao', 'valor', 'tipo', 'data']])

elif pagina == "Clientes":
    import pages.clientes
    pages.clientes.show()

elif pagina == "Propostas":
    import pages.propostas
    pages.propostas.show()

elif pagina == "Financeiro":
    import pages.financeiro
    pages.financeiro.show()

elif pagina == "Relatórios":
    import pages.relatorios
    pages.relatorios.show()

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")
