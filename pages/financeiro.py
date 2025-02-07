import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def show():
    st.title("💰 Gestão Financeira")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Registrar Transação",
        "Extrato",
        "Contas a Receber",
        "Dashboard Financeiro"
    ])

    with tab1:
        st.subheader("Nova Transação")

        with st.form("registro_transacao", clear_on_submit=True):
            tipo = st.selectbox(
                "Tipo",
                ["receita", "despesa", "receita_a_receber"]
            )

            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            if tipo in ["receita", "receita_a_receber"]:
                tipo_receita = st.selectbox(
                    "Tipo de Receita",
                    ["organização", "comissão", "venda"]
                )

                origem_tipo = st.selectbox(
                    "Origem",
                    ["cliente", "fornecedor"]
                )

                # Carregar origens
                if origem_tipo == "cliente":
                    origens = st.session_state.db.get_clientes()
                    if not origens.empty:
                        origem = st.selectbox("Selecione o Cliente", origens['nome'].tolist())
                        origem_id = origens[origens['nome'] == origem]['id'].iloc[0]
                    else:
                        st.warning("Nenhum cliente cadastrado")
                        origem_id = None
                else:  # fornecedor
                    fornecedores = st.session_state.db.get_fornecedores()
                    if not fornecedores.empty:
                        origem = st.selectbox("Selecione o Fornecedor", fornecedores['nome'].tolist())
                        origem_id = fornecedores[fornecedores['nome'] == origem]['id'].iloc[0]
                    else:
                        st.warning("Nenhum fornecedor cadastrado")
                        origem_id = None
            else:
                tipo_receita = None
                origem_tipo = None
                origem_id = None

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
                            tipo_receita=tipo_receita,
                            origem_id=origem_id,
                            origem_tipo=origem_tipo
                        )
                        st.success("Transação registrada com sucesso!")
                        st.rerun()
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
                ["receita", "despesa", "receita_a_receber"]
            )
        with col2:
            categoria_filtro = st.multiselect(
                "Categoria",
                ["Serviço", "Produto", "Fornecedor", "Outros"]
            )
        with col3:
            data_filtro = st.date_input("Data")

        # Carregar e filtrar dados
        financeiro = st.session_state.db.get_financeiro()

        if tipo_filtro:
            financeiro = financeiro[financeiro['tipo'].isin(tipo_filtro)]
        if categoria_filtro:
            financeiro = financeiro[financeiro['categoria'].isin(categoria_filtro)]

        # Exibir extrato
        if not financeiro.empty:
            st.dataframe(
                financeiro[[
                    'data', 'tipo', 'descricao', 'valor', 'categoria',
                    'tipo_receita', 'status'
                ]].sort_values('data', ascending=False),
                use_container_width=True
            )

            # Resumo financeiro
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
        st.subheader("Contas a Receber")

        contas_receber = st.session_state.db.get_contas_receber()

        if not contas_receber.empty:
            # Adicionar coluna de ações
            for idx, conta in contas_receber.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{conta['descricao']}**")
                    st.write(f"Valor: R$ {conta['valor']:.2f}")
                    st.write(f"Origem: {conta['origem_tipo']}")
                    st.write(f"Status: {conta['status']}")

                with col2:
                    if conta['status'] == 'Pendente':
                        if st.button("✅ Receber", key=f"receber_{conta['id']}"):
                            st.session_state.db.atualizar_status_transacao(
                                conta['id'],
                                'Recebido',
                                datetime.now().date()
                            )
                            st.rerun()

                with col3:
                    if conta['status'] == 'Pendente':
                        if st.button("❌ Cancelar", key=f"cancelar_{conta['id']}"):
                            st.session_state.db.atualizar_status_transacao(
                                conta['id'],
                                'Cancelado'
                            )
                            st.rerun()

                st.divider()

            # Resumo de contas a receber
            total_pendente = contas_receber[contas_receber['status'] == 'Pendente']['valor'].sum()
            total_recebido = contas_receber[contas_receber['status'] == 'Recebido']['valor'].sum()

            col1, col2 = st.columns(2)
            col1.metric("Total Pendente", f"R$ {total_pendente:.2f}")
            col2.metric("Total Recebido", f"R$ {total_recebido:.2f}")
        else:
            st.info("Nenhuma conta a receber cadastrada.")

    with tab4:
        st.subheader("Dashboard Financeiro")

        if not financeiro.empty:
            # Resumo de Contas a Receber
            contas_receber = st.session_state.db.get_contas_receber()
            if not contas_receber.empty:
                st.subheader("Resumo de Contas a Receber")

                # Agrupar por origem e status
                resumo_receber = contas_receber.groupby(['origem_tipo', 'status'])['valor'].sum().reset_index()

                # Gráfico de barras empilhadas
                fig_receber = px.bar(
                    resumo_receber,
                    x='origem_tipo',
                    y='valor',
                    color='status',
                    title='Contas a Receber por Origem',
                    labels={'valor': 'Valor (R$)', 'origem_tipo': 'Origem', 'status': 'Status'}
                )
                st.plotly_chart(fig_receber, use_container_width=True)

            # Gráfico de Receitas vs Despesas por Categoria
            fig1 = px.bar(
                financeiro,
                x='categoria',
                y='valor',
                color='tipo',
                title='Transações por Categoria',
                labels={'valor': 'Valor (R$)', 'categoria': 'Categoria'}
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Evolução Temporal
            financeiro['data'] = pd.to_datetime(financeiro['data'])
            dados_temporais = financeiro.groupby(
                [pd.Grouper(key='data', freq='ME'), 'tipo']
            )['valor'].sum().reset_index()

            fig2 = px.line(
                dados_temporais,
                x='data',
                y='valor',
                color='tipo',
                title='Evolução Temporal',
                labels={'valor': 'Valor (R$)', 'data': 'Data'}
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Distribuição por Tipo de Receita
            receitas = financeiro[financeiro['tipo'].isin(['receita', 'receita_a_receber'])]
            if not receitas.empty and 'tipo_receita' in receitas.columns:
                fig3 = px.pie(
                    receitas,
                    values='valor',
                    names='tipo_receita',
                    title='Distribuição por Tipo de Receita'
                )
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Não há dados suficientes para gerar o dashboard.")