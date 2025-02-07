import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def show():
    st.title("📊 Relatórios")
    
    # Seleção do tipo de relatório
    tipo_relatorio = st.selectbox(
        "Selecione o Relatório",
        ["Desempenho Financeiro", "Análise de Clientes", "Status de Propostas"]
    )
    
    if tipo_relatorio == "Desempenho Financeiro":
        st.subheader("Desempenho Financeiro")
        
        # Período de análise
        periodo = st.selectbox(
            "Período",
            ["Últimos 30 dias", "Último trimestre", "Último ano"]
        )
        
        # Calcular data inicial baseado no período
        hoje = datetime.now()
        if periodo == "Últimos 30 dias":
            data_inicial = hoje - timedelta(days=30)
        elif periodo == "Último trimestre":
            data_inicial = hoje - timedelta(days=90)
        else:
            data_inicial = hoje - timedelta(days=365)
        
        # Carregar dados financeiros
        financeiro = st.session_state.db.get_financeiro()
        financeiro['data'] = pd.to_datetime(financeiro['data'])
        
        # Filtrar por período
        financeiro = financeiro[financeiro['data'] >= data_inicial]
        
        if not financeiro.empty:
            # Resumo financeiro
            receitas = financeiro[financeiro['tipo'] == 'receita']['valor'].sum()
            despesas = financeiro[financeiro['tipo'] == 'despesa']['valor'].sum()
            saldo = receitas - despesas
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Receitas", f"R$ {receitas:.2f}")
            col2.metric("Despesas", f"R$ {despesas:.2f}")
            col3.metric("Saldo", f"R$ {saldo:.2f}")
            
            # Gráficos
            fig1 = px.pie(
                financeiro,
                values='valor',
                names='categoria',
                title='Distribuição por Categoria'
            )
            st.plotly_chart(fig1)
            
            fig2 = px.line(
                financeiro.groupby('data')['valor'].sum().reset_index(),
                x='data',
                y='valor',
                title='Evolução Temporal'
            )
            st.plotly_chart(fig2)
        else:
            st.info("Não há dados para o período selecionado.")
    
    elif tipo_relatorio == "Análise de Clientes":
        st.subheader("Análise de Clientes")
        
        clientes = st.session_state.db.get_clientes()
        propostas = st.session_state.db.get_propostas()
        
        if not clientes.empty and not propostas.empty:
            # Merge para análise
            analise = propostas.merge(
                clientes,
                left_on='cliente_id',
                right_on='id',
                suffixes=('_proposta', '')
            )
            
            # Análise por cliente
            por_cliente = analise.groupby('nome').agg({
                'valor': 'sum',
                'id_proposta': 'count'
            }).reset_index()
            
            por_cliente.columns = ['Cliente', 'Valor Total', 'Número de Propostas']
            
            st.write("Resumo por Cliente:")
            st.dataframe(por_cliente)
            
            # Gráfico de propostas por cliente
            fig = px.bar(
                por_cliente,
                x='Cliente',
                y='Valor Total',
                title='Valor Total por Cliente'
            )
            st.plotly_chart(fig)
        else:
            st.info("Não há dados suficientes para análise.")
    
    else:  # Status de Propostas
        st.subheader("Status de Propostas")
        
        propostas = st.session_state.db.get_propostas()
        
        if not propostas.empty:
            # Análise por status
            status_count = propostas['status'].value_counts()
            
            # Gráfico de pizza
            fig = px.pie(
                values=status_count.values,
                names=status_count.index,
                title='Distribuição de Propostas por Status'
            )
            st.plotly_chart(fig)
            
            # Tabela de resumo
            st.write("Resumo por Status:")
            resumo_status = propostas.groupby('status').agg({
                'valor': ['count', 'sum', 'mean']
            }).round(2)
            resumo_status.columns = ['Quantidade', 'Valor Total', 'Valor Médio']
            st.dataframe(resumo_status)
        else:
            st.info("Não há propostas cadastradas.")
