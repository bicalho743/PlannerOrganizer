import streamlit as st
from datetime import datetime
import pandas as pd

def show():
    st.title("📊 Dashboard")

    # Add test data button in sidebar if database is empty
    clientes = st.session_state.db.get_clientes()
    if clientes.empty:
        st.sidebar.warning("Banco de dados vazio")
        if st.sidebar.button("Adicionar Dados de Teste", key="btn_add_test_data_dashboard"):
            if st.session_state.db.add_test_data():
                st.sidebar.success("Dados de teste adicionados com sucesso!")
                st.rerun()
            else:
                st.sidebar.error("Erro ao adicionar dados de teste")

    # Dashboard layout
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.subheader("📊 Resumo")

        # Estatísticas básicas
        total_clientes = len(clientes) if not clientes.empty else 0
        st.metric("Total de Clientes", total_clientes)

        # Propostas
        propostas = st.session_state.db.get_propostas()
        propostas_ativas = len(propostas[propostas['status'] == 'Aberta']) if not propostas.empty else 0
        st.metric("Propostas Ativas", propostas_ativas)

        # Financeiro
        financeiro = st.session_state.db.get_financeiro()
        if not financeiro.empty:
            valores_receber = financeiro[
                (financeiro['tipo'] == 'receita') & 
                (financeiro['status'] == 'pendente')
            ]['valor'].sum()
        else:
            valores_receber = 0.0
        st.metric("Valores a Receber", f"R$ {valores_receber:,.2f}")

    with col2:
        st.subheader("📋 Propostas em Aberto")
        if not propostas.empty:
            propostas_abertas = propostas[propostas['status'] == 'Aberta'].sort_values('data_inicio', ascending=False)
            if not propostas_abertas.empty:
                for _, proposta in propostas_abertas.head(5).iterrows():
                    with st.expander(f"Proposta #{proposta['id']} - {proposta['descricao'][:50]}..."):
                        st.write(f"**Cliente:** {proposta['cliente_nome']}")
                        st.write(f"**Valor:** R$ {proposta['valor']:,.2f}")
                        if proposta.get('prazo_entrega'):
                            st.write(f"**Prazo:** {proposta['prazo_entrega'].strftime('%d/%m/%Y')}")
            else:
                st.info("Nenhuma proposta em aberto.")
        else:
            st.info("Nenhuma proposta cadastrada.")

    with col3:
        st.subheader("🎂 Aniversariantes")
        hoje = datetime.now()

        if not clientes.empty and 'data_aniversario' in clientes.columns:
            # Aniversariantes do dia
            aniversariantes_hoje = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower() == hoje.strftime('%d/%b').lower())
            ]

            st.write("**Hoje:**")
            if not aniversariantes_hoje.empty:
                for _, aniversariante in aniversariantes_hoje.iterrows():
                    st.write(f"🎈 {aniversariante['nome']}")
                    if aniversariante['telefone']:
                        st.write(f"📱 {aniversariante['telefone']}")
            else:
                st.info("Nenhum aniversariante hoje!")

            # Próximos aniversariantes
            st.write("\n**Próximos 7 dias:**")
            proximos_dias = pd.date_range(hoje, periods=7, freq='D')
            datas_proximas = [d.strftime('%d/%b').lower() for d in proximos_dias]

            proximos = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower().isin(datas_proximas))
            ]

            if not proximos.empty:
                for _, proximo in proximos.iterrows():
                    st.write(f"🎂 {proximo['nome']} ({proximo['data_aniversario']})")
                    if proximo['telefone']:
                        st.write(f"📱 {proximo['telefone']}")
            else:
                st.info("Nenhum aniversariante nos próximos dias.")
        else:
            st.info("Nenhum cliente cadastrado com data de aniversário.")