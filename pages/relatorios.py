import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from utils.currency_formatter import fmt_brl as _fmt_brl

def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Relatórios Avançados</h1>', unsafe_allow_html=True)

    tipo_relatorio = st.selectbox(
        "Selecione o Relatório",
        ["Desempenho Financeiro", "Análise de Clientes", "Status de Propostas"]
    )

    if tipo_relatorio == "Desempenho Financeiro":
        st.subheader("Análise Financeira Detalhada")

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

        try:
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

                # Análise por tipo de receita (case-insensitive: banco grava 'Receita')
                receitas = financeiro[financeiro['tipo'].astype(str).str.lower().isin(['receita', 'receita_a_receber', 'entrada'])].copy()
                if not receitas.empty:
                    st.subheader("Análise de Receitas")

                    # Rótulo por tipo; cai para a categoria quando tipo_receita é vazio/nulo
                    # (antes o gráfico mostrava "null" porque tipo_receita costuma ser None).
                    _tr = receitas['tipo_receita'].astype(str).str.strip() if 'tipo_receita' in receitas.columns else pd.Series([''] * len(receitas), index=receitas.index)
                    _cat = receitas['categoria'] if 'categoria' in receitas.columns else pd.Series(['Outros'] * len(receitas), index=receitas.index)
                    receitas['tipo_label'] = _tr.where(~_tr.str.lower().isin(['', 'none', 'nan']), _cat).fillna('Outros').replace('', 'Outros')

                    # Gráfico de receitas por tipo
                    fig = px.pie(
                        receitas,
                        values='valor',
                        names='tipo_label',
                        title='Distribuição de Receitas por Tipo'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Tendência de receitas por tipo
                    receitas_mensais = receitas.groupby([
                        receitas['data'].dt.strftime('%Y-%m'),
                        'tipo_label'
                    ])['valor'].sum().reset_index()

                    fig = px.line(
                        receitas_mensais,
                        x='data',
                        y='valor',
                        color='tipo_label',
                        title='Evolução de Receitas por Tipo'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Projeção financeira
                    st.subheader("Projeção Financeira")
                    # Criar série temporal contínua
                    receitas_diarias = receitas.groupby('data')['valor'].sum().reset_index()
                    if len(receitas_diarias) > 1:
                        # Criar índice contínuo de datas
                        date_range = pd.date_range(
                            start=receitas_diarias['data'].min(),
                            end=receitas_diarias['data'].max(),
                            freq='D'
                        )

                        # Reindexar com preenchimento de zeros
                        receitas_diarias = receitas_diarias.set_index('data').reindex(date_range, fill_value=0)
                        receitas_diarias = receitas_diarias.reset_index()
                        receitas_diarias.columns = ['data', 'valor']

                        # Calcular dias desde o início de forma mais robusta
                        data_min = receitas_diarias['data'].min()
                        if isinstance(data_min, pd.Timestamp):
                            data_min = data_min.date()
                        
                        dias_serie = []
                        for data in receitas_diarias['data']:
                            if isinstance(data, pd.Timestamp):
                                data = data.date()
                            dias_serie.append((data - data_min).days)
                        
                        dias_serie = pd.Series(dias_serie)
                        valores_serie = receitas_diarias['valor']
                        
                        try:
                            # Garantir que os dados sejam numéricos
                            dias_serie_numeric = pd.to_numeric(dias_serie, errors='coerce')
                            valores_serie_numeric = pd.to_numeric(valores_serie, errors='coerce')
                            
                            # Remover valores NaN
                            mask = ~(dias_serie_numeric.isna() | valores_serie_numeric.isna())
                            dias_clean = dias_serie_numeric[mask]
                            valores_clean = valores_serie_numeric[mask]
                            
                            # Verificar se temos dados suficientes
                            if len(dias_clean) >= 2:
                                # Calcular tendência
                                z = np.polyfit(dias_clean.values, valores_clean.values, 1)
                                p = np.poly1d(z)
                            else:
                                # Se não há dados suficientes, usar média como projeção
                                media_valores = valores_clean.mean() if len(valores_clean) > 0 else 0
                                z = [0, media_valores]  # Linha horizontal na média
                                p = np.poly1d(z)
                        except Exception as e:
                            st.error(f"Erro na análise de tendência: {str(e)}")
                            # Fallback: usar média simples
                            media_valores = receitas_diarias['valor'].mean()
                            z = [0, media_valores]
                            p = np.poly1d(z)

                        # Criar dados para projeção
                        dias_futuros = pd.date_range(
                            start=receitas_diarias['data'].max(),
                            end=receitas_diarias['data'].max() + timedelta(days=30),
                            freq='D'
                        )

                        try:
                            # Calcular diferença de dias corretamente
                            data_min = receitas_diarias['data'].min()
                            if isinstance(data_min, pd.Timestamp):
                                data_min = data_min.date()
                            
                            # Converter dias_futuros para list de datas se necessário
                            if hasattr(dias_futuros, 'date'):
                                dias_como_datas = [d.date() if hasattr(d, 'date') else d for d in dias_futuros]
                            else:
                                dias_como_datas = dias_futuros
                            
                            # Calcular dias como diferença numérica
                            dias_projecao = [(d - data_min).days if hasattr(d - data_min, 'days') else 0 for d in dias_como_datas]
                            dias_projecao = np.array(dias_projecao)
                            
                            valores_projecao = p(dias_projecao)
                            
                            # Garantir que os valores de projeção sejam não negativos
                            valores_projecao = np.maximum(valores_projecao, 0)
                        except Exception as e:
                            st.error(f"Erro na projeção: {str(e)}")
                            # Fallback: projeção plana
                            media_valores = receitas_diarias['valor'].mean()
                            valores_projecao = np.full(len(dias_futuros), max(media_valores, 0))

                        # Criar gráfico
                        fig = go.Figure()

                        # Dados históricos
                        fig.add_trace(go.Scatter(
                            x=receitas_diarias['data'],
                            y=receitas_diarias['valor'],
                            name='Dados Históricos'
                        ))

                        # Projeção
                        fig.add_trace(go.Scatter(
                            x=dias_futuros,
                            y=valores_projecao,
                            name='Projeção',
                            line=dict(dash='dash')
                        ))

                        fig.update_layout(
                            title='Projeção de Receitas (30 dias)',
                            xaxis_title='Data',
                            yaxis_title='Valor (R$)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados financeiros para análise.")
        except Exception as e:
            st.error(f"Erro ao carregar dados financeiros: {str(e)}")

    elif tipo_relatorio == "Análise de Clientes":
        st.subheader("Análise de Clientes")
        try:
            clientes = st.session_state.db.get_clientes()
            propostas = st.session_state.db.get_propostas()

            if not clientes.empty and not propostas.empty:
                # Métricas de clientes
                col1, col2, col3 = st.columns(3)

                with col1:
                    clientes_ativos = len(clientes)
                    st.metric("Total de Clientes", clientes_ativos)

                with col2:
                    # Coerção numérica + descarte de NaN; sem valores válidos => 0
                    if 'valor' in propostas.columns:
                        _valores = pd.to_numeric(propostas['valor'], errors='coerce').dropna()
                        ticket_medio = float(_valores.mean()) if not _valores.empty else 0.0
                    else:
                        ticket_medio = 0.0
                    st.metric("Ticket Médio", _fmt_brl(ticket_medio))

                with col3:
                    propostas_por_cliente = len(propostas) / len(clientes) if len(clientes) > 0 else 0
                    st.metric("Propostas/Cliente", f"{propostas_por_cliente:.1f}")

                # Análise de origem dos clientes — normalizada para categorias
                # oficiais (sem duplicata por caixa, sem "0", sem nomes próprios).
                if 'origem_cliente' in clientes.columns:
                    st.subheader("Origem dos Clientes")
                    from utils.origem_cliente import origem_para_exibicao
                    origem_norm = clientes['origem_cliente'].apply(origem_para_exibicao)
                    origem_counts = origem_norm.value_counts()
                    fig = px.pie(
                        values=origem_counts.values,
                        names=origem_counts.index,
                        title='Distribuição por Origem'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Análise temporal
                if 'data_cadastro' in clientes.columns:
                    st.subheader("Novos Clientes por Mês")
                    clientes['data_cadastro'] = pd.to_datetime(clientes['data_cadastro'])
                    cadastros_mensais = clientes.groupby(
                        clientes['data_cadastro'].dt.strftime('%Y-%m')
                    ).size().reset_index(name='count')

                    fig = px.line(
                        cadastros_mensais,
                        x='data_cadastro',
                        y='count',
                        title='Evolução de Novos Clientes'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados suficientes para análise de clientes.")
        except Exception as e:
            st.error(f"Erro ao carregar dados de clientes: {str(e)}")

    elif tipo_relatorio == "Status de Propostas":
        st.subheader("Análise de Propostas")
        try:
            propostas = st.session_state.db.get_propostas()

            if not propostas.empty:
                # Métricas principais
                col1, col2, col3 = st.columns(3)

                total_propostas = len(propostas)
                from utils.proposta_status import STATUS_EM_ABERTO, STATUS_FINALIZADA
                propostas_abertas = len(propostas[propostas['status'] == STATUS_EM_ABERTO]) if 'status' in propostas.columns else 0
                propostas_fechadas = len(propostas[propostas['status'] == STATUS_FINALIZADA]) if 'status' in propostas.columns else 0

                col1.metric("Total de Propostas", total_propostas)
                col2.metric("Propostas em Aberto", propostas_abertas)
                col3.metric("Propostas Fechadas", propostas_fechadas)

                # Análise temporal
                if 'data_proposta' in propostas.columns and 'status' in propostas.columns:
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

                # Análise de valores
                if 'valor' in propostas.columns and 'status' in propostas.columns:
                    st.subheader("Distribuição de Valores")
                    fig = px.box(
                        propostas,
                        x='status',
                        y='valor',
                        title='Distribuição de Valores por Status'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há propostas cadastradas para análise.")
        except Exception as e:
            st.error(f"Erro ao carregar dados de propostas: {str(e)}")