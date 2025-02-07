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
                            tipo, descricao, valor, categoria
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
        financeiro = st.session_state.db.get_financeiro()
        
        # Aplicar filtros
        if tipo_filtro:
            financeiro = financeiro[financeiro['tipo'].isin(tipo_filtro)]
        if categoria_filtro:
            financeiro = financeiro[financeiro['categoria'].isin(categoria_filtro)]
        
        # Exibir extrato
        if not financeiro.empty:
            st.dataframe(
                financeiro[['data', 'tipo', 'descricao', 'valor', 'categoria']],
                use_container_width=True
            )
            
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
        else:
            st.info("Não há dados suficientes para gerar o dashboard.")
