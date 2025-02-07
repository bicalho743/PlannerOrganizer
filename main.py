import streamlit as st
from utils.database import Database
from datetime import datetime
import pandas as pd

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
    ["Dashboard", "Clientes", "Propostas", "Financeiro", "Contas a Pagar", "Backup", "Relatórios"]
)

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

        # Aniversariantes
        if not clientes.empty:
            st.write("---")
            st.subheader("🎂 Aniversariantes")

            # Converter a coluna de data_aniversario para datetime
            clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'])
            hoje = datetime.now()

            # Aniversariantes do dia
            aniversariantes_dia = clientes[
                (clientes['data_aniversario'].dt.day == hoje.day) & 
                (clientes['data_aniversario'].dt.month == hoje.month)
            ]

            if not aniversariantes_dia.empty:
                st.write("**🎈 Hoje:**")
                for _, aniv in aniversariantes_dia.iterrows():
                    st.write(f"- {aniv['nome']}")
            else:
                st.write("**🎈 Hoje:** Nenhum aniversariante")

            # Aniversariantes do mês
            aniversariantes_mes = clientes[
                (clientes['data_aniversario'].dt.month == hoje.month) &
                (clientes['data_aniversario'].dt.day > hoje.day)
            ].sort_values('data_aniversario')

            if not aniversariantes_mes.empty:
                st.write("**📅 Próximos aniversariantes do mês:**")
                for _, aniv in aniversariantes_mes.iterrows():
                    data_aniv = aniv['data_aniversario']
                    st.write(f"- Dia {data_aniv.day}: {aniv['nome']}")

    with col2:
        st.subheader("📅 Atividades Recentes")

        # Últimas propostas
        st.write("Últimas Propostas:")
        if not propostas.empty:
            # Converter data_proposta para datetime
            propostas['data_proposta'] = pd.to_datetime(propostas['data_proposta'])
            # Ordenar por data mais recente
            ultimas_propostas = propostas.sort_values('data_proposta', ascending=False).head(5)
            st.dataframe(ultimas_propostas[['descricao', 'valor', 'status', 'data_proposta']])
        else:
            st.info("Nenhuma proposta cadastrada.")

        # Últimas transações
        st.write("Últimas Transações:")
        if not financeiro.empty:
            # Converter data para datetime
            financeiro['data'] = pd.to_datetime(financeiro['data'])
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

elif pagina == "Contas a Pagar":
    import pages.contas_pagar
    pages.contas_pagar.show()

elif pagina == "Backup":
    import pages.backup
    pages.backup.show()

elif pagina == "Relatórios":
    import pages.relatorios
    pages.relatorios.show()

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")