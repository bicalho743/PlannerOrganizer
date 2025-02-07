import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def show():
    st.title("📊 Relatórios Avançados")

    # Seleção do tipo de relatório
    tipo_relatorio = st.selectbox(
        "Selecione o Relatório",
        ["Desempenho Financeiro", "Análise de Clientes", "Status de Propostas"]
    )

    if tipo_relatorio == "Desempenho Financeiro":
        st.subheader("💰 Análise Financeira Detalhada")

        # Período de análise
        col1, col2 = st.columns(2)
        with col1:
            periodo = st.selectbox(
                "Período de Análise",
                ["Último mês", "Último trimestre", "Último ano", "Todo o período"]
            )

        with col2:
            tipo_conta = st.multiselect(
                "Tipo de Conta",
                ["PF", "PJ"],
                default=["PF", "PJ"]
            )

        financeiro = st.session_state.db.get_financeiro()

        if not financeiro.empty:
            # Filtrar por período
            financeiro['data'] = pd.to_datetime(financeiro['data'])
            if periodo == "Último mês":
                financeiro = financeiro[financeiro['data'] >= datetime.now() - timedelta(days=30)]
            elif periodo == "Último trimestre":
                financeiro = financeiro[financeiro['data'] >= datetime.now() - timedelta(days=90)]
            elif periodo == "Último ano":
                financeiro = financeiro[financeiro['data'] >= datetime.now() - timedelta(days=365)]

            # Filtrar por tipo de conta
            if tipo_conta:
                financeiro = financeiro[financeiro['tipo_conta'].isin(tipo_conta)]

            # Análise por tipo de receita
            receitas = financeiro[financeiro['tipo'] == 'receita']
            if not receitas.empty:
                st.subheader("Análise de Receitas")

                # Gráfico de receitas por tipo
                fig = px.pie(
                    receitas,
                    values='valor',
                    names='tipo_receita',
                    title='Distribuição de Receitas por Tipo'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tendência de receitas por tipo
                receitas_mensais = receitas.groupby([
                    receitas['data'].dt.strftime('%Y-%m'),
                    'tipo_receita'
                ])['valor'].sum().reset_index()

                fig = px.line(
                    receitas_mensais,
                    x='data',
                    y='valor',
                    color='tipo_receita',
                    title='Evolução de Receitas por Tipo'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Projeção financeira
            st.subheader("Projeção Financeira")
            # Calcular tendência linear simples
            dias_serie = (financeiro['data'] - financeiro['data'].min()).dt.days
            valores_serie = financeiro[financeiro['tipo'] == 'receita']['valor']

            if len(dias_serie) > 1:
                z = np.polyfit(dias_serie, valores_serie, 1)
                p = np.poly1d(z)

                # Criar dados para projeção
                dias_futuros = pd.date_range(
                    start=financeiro['data'].max(),
                    end=financeiro['data'].max() + timedelta(days=30),
                    freq='D'
                )

                dias_projecao = (dias_futuros - financeiro['data'].min()).days
                valores_projecao = p(dias_projecao)

                fig = go.Figure()

                # Dados históricos
                fig.add_trace(go.Scatter(
                    x=financeiro['data'],
                    y=valores_serie,
                    name='Dados Históricos'
                ))

                # Projeção
                fig.add_trace(go.Scatter(
                    x=dias_futuros,
                    y=valores_projecao,
                    name='Projeção',
                    line=dict(dash='dash')
                ))

                fig.update_layout(title='Projeção de Receitas (30 dias)')
                st.plotly_chart(fig, use_container_width=True)

    elif tipo_relatorio == "Análise de Clientes":
        st.subheader("👥 Análise de Clientes")

        clientes = st.session_state.db.get_clientes()
        propostas = st.session_state.db.get_propostas()

        if not clientes.empty and not propostas.empty:
            # Análise de clientes ativos
            analise = propostas.merge(
                clientes,
                left_on='cliente_id',
                right_on='id',
                suffixes=('_proposta', '')
            )

            # Métricas de clientes
            col1, col2, col3 = st.columns(3)

            with col1:
                clientes_ativos = len(analise['cliente_id'].unique())
                st.metric("Clientes Ativos", clientes_ativos)

            with col2:
                ticket_medio = analise['valor'].mean()
                st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")

            with col3:
                propostas_por_cliente = len(propostas) / len(clientes)
                st.metric("Propostas/Cliente", f"{propostas_por_cliente:.1f}")

            # Análise de valor por cliente
            st.subheader("Valor Total por Cliente")
            valor_por_cliente = analise.groupby('nome')['valor'].sum().sort_values(ascending=False)

            fig = px.bar(
                x=valor_por_cliente.index,
                y=valor_por_cliente.values,
                title='Valor Total de Propostas por Cliente'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Análise de sazonalidade
            st.subheader("Sazonalidade de Novos Clientes")
            clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'])
            cadastros_mensais = clientes.groupby(
                clientes['data_cadastro'].dt.strftime('%Y-%m')
            ).size().reset_index(name='count')

            fig = px.line(
                cadastros_mensais,
                x='data_cadastro',
                y='count',
                title='Novos Clientes por Mês'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Análise de origem dos clientes
            st.subheader("Efetividade das Origens")
            origem_conversao = analise.groupby('origem_cliente').agg({
                'cliente_id': 'count',
                'valor': 'sum'
            }).reset_index()

            origem_conversao.columns = ['Origem', 'Quantidade', 'Valor Total']
            origem_conversao['Ticket Médio'] = origem_conversao['Valor Total'] / origem_conversao['Quantidade']

            st.dataframe(origem_conversao.round(2), use_container_width=True)

    elif tipo_relatorio == "Status de Propostas":
        st.subheader("📋 Análise de Propostas")

        propostas = st.session_state.db.get_propostas()

        if not propostas.empty:
            # Métricas principais
            total_propostas = len(propostas)
            propostas_abertas = len(propostas[propostas['status'] == 'Aberta'])
            propostas_fechadas = len(propostas[propostas['status'] == 'Fechada'])
            taxa_conversao = (propostas_fechadas / total_propostas * 100) if total_propostas > 0 else 0

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total de Propostas", total_propostas)
            col2.metric("Propostas em Aberto", propostas_abertas)
            col3.metric("Propostas Fechadas", propostas_fechadas)
            col4.metric("Taxa de Conversão", f"{taxa_conversao:.1f}%")

            # Análise temporal
            st.subheader("Evolução Temporal")
            propostas['data_proposta'] = pd.to_datetime(propostas['data_proposta'])
            propostas_mensais = propostas.groupby([
                propostas['data_proposta'].dt.strftime('%Y-%m'),
                'status'
            ]).size().reset_index(name='count')

            fig = px.line(
                propostas_mensais,
                x='data_proposta',
                y='count',
                color='status',
                title='Evolução de Propostas por Status'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Análise de valor
            st.subheader("Análise de Valor")
            valor_status = propostas.groupby('status')['valor'].agg([
                'count', 'sum', 'mean'
            ]).round(2)
            valor_status.columns = ['Quantidade', 'Valor Total', 'Valor Médio']
            st.dataframe(valor_status, use_container_width=True)

            # Distribuição de valores
            fig = px.box(
                propostas,
                x='status',
                y='valor',
                title='Distribuição de Valores por Status'
            )
            st.plotly_chart(fig, use_container_width=True)