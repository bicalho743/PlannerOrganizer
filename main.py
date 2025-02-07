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

        st.metric("Total de Clientes", len(clientes) if not clientes.empty else 0)
        propostas_ativas = len(propostas[propostas['status'] == 'Aberta']) if not propostas.empty else 0
        st.metric("Propostas Ativas", propostas_ativas)

        # Resumo financeiro
        if not financeiro.empty:
            receitas = financeiro[financeiro['tipo'] == 'receita']['valor'].sum()
            despesas = financeiro[financeiro['tipo'] == 'despesa']['valor'].sum()
            saldo = receitas - despesas
        else:
            saldo = 0.0

        st.metric("Saldo Total", f"R$ {saldo:.2f}")

    with col2:
        st.subheader("📅 Atividades Recentes")

        # Últimas propostas
        st.write("Últimas Propostas:")
        if not propostas.empty:
            ultimas_propostas = propostas.sort_values('data_proposta', ascending=False).head(5)
            st.dataframe(ultimas_propostas[['descricao', 'valor', 'status', 'data_proposta']])
        else:
            st.info("Nenhuma proposta cadastrada.")

        # Últimas transações
        st.write("Últimas Transações:")
        if not financeiro.empty:
            ultimas_transacoes = financeiro.sort_values('data', ascending=False).head(5)
            st.dataframe(ultimas_transacoes[['descricao', 'valor', 'tipo', 'data']])
        else:
            st.info("Nenhuma transação registrada.")

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