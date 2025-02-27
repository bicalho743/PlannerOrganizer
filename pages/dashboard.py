import streamlit as st
from datetime import datetime
import pandas as pd

def show():
    st.title("📊 Dashboard")

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

    # Dashboard content
    col1, col2, col3 = st.columns([2, 2, 1])

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
            valores_receber = financeiro[
                (financeiro['tipo'] == 'receita') & 
                (financeiro['tipo_receita'].isin(['organização', 'venda']))
            ]['valor'].sum()
        else:
            valores_receber = 0.0

        st.metric("Valores a Receber", f"R$ {valores_receber:.2f}")

    with col2:
        st.subheader("📋 Propostas em Aberto")
        if not propostas.empty:
            propostas_abertas = propostas[propostas['status'] == 'Aberta']
            if not propostas_abertas.empty:
                for _, p in propostas_abertas.iterrows():
                    with st.expander(f"Proposta #{p['numero']} - {p['descricao']}"):
                        st.write(f"**Valor:** R$ {p['valor']:.2f}")
                        if 'prazo_entrega' in p and p['prazo_entrega']:
                            st.write(f"**Prazo de Entrega:** {p['prazo_entrega']}")
            else:
                st.info("Nenhuma proposta em aberto.")
        else:
            st.info("Nenhuma proposta cadastrada.")

    with col3:
        st.subheader("🎂 Aniversariantes")
        hoje = datetime.now().date()

        if not clientes.empty and 'data_aniversario' in clientes.columns:
            try:
                # Converter data_aniversario para datetime explicitamente
                clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

                # Filtrar aniversariantes do dia
                aniversariantes_hoje = clientes[
                    (clientes['data_aniversario'].notna()) & 
                    (clientes['data_aniversario'].dt.month == hoje.month) & 
                    (clientes['data_aniversario'].dt.day == hoje.day)
                ]

                # Mostrar aniversariantes de hoje
                st.write("**Hoje:**")
                if not aniversariantes_hoje.empty:
                    for _, aniversariante in aniversariantes_hoje.iterrows():
                        with st.container():
                            st.write(f"🎈 **{aniversariante['nome']}**")
                            if aniversariante['telefone']:
                                st.write(f"📱 {aniversariante['telefone']}")
                else:
                    st.info("Nenhum aniversariante hoje!")

                # Mostrar próximos aniversariantes (próximos 7 dias)
                st.write("\n**Próximos 7 dias:**")
                proximos_aniversariantes = clientes[
                    (clientes['data_aniversario'].notna()) &
                    (((clientes['data_aniversario'].dt.month == hoje.month) & 
                      (clientes['data_aniversario'].dt.day > hoje.day) & 
                      (clientes['data_aniversario'].dt.day <= hoje.day + 7)) |
                     ((clientes['data_aniversario'].dt.month == (hoje.month % 12 + 1)) & 
                      (clientes['data_aniversario'].dt.day <= (hoje.day + 7) % 31)))
                ]

                if not proximos_aniversariantes.empty:
                    for _, aniversariante in proximos_aniversariantes.iterrows():
                        with st.container():
                            data_aniv = aniversariante['data_aniversario'].strftime('%d/%m')
                            st.write(f"🎂 **{aniversariante['nome']}** ({data_aniv})")
                            if aniversariante['telefone']:
                                st.write(f"📱 {aniversariante['telefone']}")
                else:
                    st.info("Nenhum aniversariante nos próximos dias.")
            except Exception as e:
                st.error(f"Erro ao processar datas de aniversário: {str(e)}")
        else:
            st.info("Nenhum cliente cadastrado com data de aniversário.")