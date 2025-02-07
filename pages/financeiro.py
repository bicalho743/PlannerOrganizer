import streamlit as st
import pandas as pd
import plotly.express as px

def show():
    st.title("💰 Gestão Financeira")

    tab1, tab2, tab3 = st.tabs([
        "Registrar Transação",
        "Extrato",
        "Dashboard Financeiro"
    ])

    with tab1:
        st.subheader("Nova Transação")

        with st.form("registro_transacao"):
            tipo = st.selectbox(
                "Tipo",
                ["receita", "despesa"]
            )

            # Campos específicos para receita
            if tipo == "receita":
                tipo_receita = st.selectbox(
                    "Tipo de Receita",
                    ["organização", "comissão", "venda"]
                )

                origem_tipo = st.selectbox(
                    "Origem",
                    ["cliente", "fornecedor"]
                )

                # Carregar lista de clientes ou fornecedores
                if origem_tipo == "cliente":
                    origens = st.session_state.db.get_clientes()
                    origem_lista = origens['nome'].tolist() if not origens.empty else []
                else:
                    # Assumindo que temos uma lista de fornecedores
                    origem_lista = ["Fornecedor 1", "Fornecedor 2"]  # TODO: Implementar lista de fornecedores

                origem = st.selectbox("Selecione a Origem", origem_lista)
                if origem_tipo == "cliente":
                    origem_id = origens[origens['nome'] == origem]['id'].iloc[0] if origem else None
                else:
                    origem_id = None  # TODO: Implementar ID de fornecedores

            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            categoria = st.selectbox(
                "Categoria",
                ["Serviço", "Produto", "Fornecedor", "Outros"]
            )

            submitted = st.form_submit_button("Registrar")

            if submitted:
                if descricao and valor > 0:
                    try:
                        st.session_state.db.add_transacao(
                            tipo=tipo,
                            descricao=descricao,
                            valor=valor,
                            categoria=categoria,
                            tipo_receita=tipo_receita if tipo == "receita" else None,
                            origem_id=origem_id if tipo == "receita" else None,
                            origem_tipo=origem_tipo if tipo == "receita" else None
                        )
                        st.success("Transação registrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao registrar transação: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos corretamente.")

    with tab2:
        st.subheader("Extrato Financeiro")

        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_filtro = st.multiselect(
                "Tipo",
                ["receita", "despesa"]
            )
        with col2:
            categoria_filtro = st.multiselect(
                "Categoria",
                ["Serviço", "Produto", "Fornecedor", "Outros"]
            )
        with col3:
            data_filtro = st.date_input("Data")

        # Carregar dados
        @st.cache_data(ttl=300)
        def load_data():
            return st.session_state.db.get_financeiro(), st.session_state.db.get_clientes()

        financeiro, clientes = load_data()

        # Mesclar com informações do cliente
        if not financeiro.empty and not clientes.empty:
            financeiro = financeiro.merge(
                clientes[['id', 'nome']],
                left_on='origem_id',
                right_on='id',
                how='left',
                suffixes=('', '_cliente')
            )

        # Aplicar filtros
        if tipo_filtro:
            financeiro = financeiro[financeiro['tipo'].isin(tipo_filtro)]
        if categoria_filtro:
            financeiro = financeiro[financeiro['categoria'].isin(categoria_filtro)]

        # Exibir extrato
        if not financeiro.empty:
            # Preparar dados para exibição
            exibir_colunas = ['data', 'tipo', 'descricao', 'valor', 'categoria']
            if 'tipo_receita' in financeiro.columns:
                exibir_colunas.append('tipo_receita')
            if 'nome' in financeiro.columns:
                exibir_colunas.append('nome')

            st.dataframe(financeiro[exibir_colunas], use_container_width=True)

            # Resumo
            receitas = financeiro[financeiro['tipo'] == 'receita']['valor'].sum()
            despesas = financeiro[financeiro['tipo'] == 'despesa']['valor'].sum()
            saldo = receitas - despesas

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Receitas", f"R$ {receitas:.2f}")
            col2.metric("Total Despesas", f"R$ {despesas:.2f}")
            col3.metric("Saldo", f"R$ {saldo:.2f}")
        else:
            st.info("Nenhuma transação encontrada.")

    with tab3:
        st.subheader("Dashboard Financeiro")

        financeiro = st.session_state.db.get_financeiro()

        if not financeiro.empty:
            # Gráfico de barras por categoria
            fig1 = px.bar(
                financeiro,
                x='categoria',
                y='valor',
                color='tipo',
                title='Transações por Categoria'
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Gráfico de linha temporal
            financeiro['data'] = pd.to_datetime(financeiro['data'])
            dados_temporais = financeiro.groupby(
                ['data', 'tipo']
            )['valor'].sum().reset_index()

            fig2 = px.line(
                dados_temporais,
                x='data',
                y='valor',
                color='tipo',
                title='Evolução Temporal'
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Novo gráfico para tipos de receita
            if 'tipo_receita' in financeiro.columns:
                receitas = financeiro[financeiro['tipo'] == 'receita']
                if not receitas.empty:
                    fig3 = px.pie(
                        receitas,
                        values='valor',
                        names='tipo_receita',
                        title='Distribuição por Tipo de Receita'
                    )
                    st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Não há dados suficientes para gerar o dashboard.")