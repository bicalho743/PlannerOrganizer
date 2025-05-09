"""
Página de demonstração do visualizador de status de propostas
Esta página permite testar os componentes visuais de transição de status
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.status_visualizer import (
    exibir_fluxo_status,
    exibir_historico_status,
    gerar_grafico_transicao_status,
    seletor_mudar_status,
    mostrar_gauge_progresso,
    STATUS_PROPOSTAS
)

# Configurações da página
st.set_page_config(
    page_title="Demo Status Propostas",
    page_icon="📊",
    layout="wide"
)

# Título da página
st.title("Demonstração - Visualizador de Status de Propostas")
st.markdown("Esta página demonstra os componentes visuais para exibir e gerenciar o fluxo de status das propostas.")

# Dados de exemplo para o histórico de status
@st.cache_data
def gerar_dados_exemplo():
    """Gera dados de exemplo para o histórico de status"""
    # Datas para o histórico, começando de 30 dias atrás
    datas = [
        (datetime.now() - timedelta(days=30)),  # Nova
        (datetime.now() - timedelta(days=25)),  # Em Análise
        (datetime.now() - timedelta(days=20)),  # Aprovada
        (datetime.now() - timedelta(days=15)),  # Em Execução
        (datetime.now() - timedelta(days=5)),   # Finalizada
    ]
    
    # Status correspondentes
    status_list = ["Nova", "Em Análise", "Aprovada", "Em Execução", "Finalizada"]
    
    # Observações de exemplo
    observacoes = [
        "Proposta cadastrada no sistema",
        "Enviado para análise do gerente",
        "Cliente aprovou orçamento",
        "Iniciado trabalho de organização",
        "Serviço concluído com sucesso"
    ]
    
    # Criar DataFrame
    df = pd.DataFrame({
        'proposta_id': [1] * len(datas),
        'data': datas,
        'status': status_list,
        'observacao': observacoes
    })
    
    # Adicionar outra proposta com status diferentes
    datas2 = [
        (datetime.now() - timedelta(days=20)),  # Nova
        (datetime.now() - timedelta(days=15)),  # Em Análise
        (datetime.now() - timedelta(days=10)),  # Recusada
    ]
    
    status_list2 = ["Nova", "Em Análise", "Recusada"]
    
    observacoes2 = [
        "Proposta cadastrada no sistema",
        "Enviado para análise do gerente",
        "Cliente não aprovou orçamento"
    ]
    
    df2 = pd.DataFrame({
        'proposta_id': [2] * len(datas2),
        'data': datas2,
        'status': status_list2,
        'observacao': observacoes2
    })
    
    # Concatenar os DataFrames
    return pd.concat([df, df2], ignore_index=True)

# Função para simular a atualização de status
def atualizar_status(proposta_id, novo_status, observacao):
    """Simula a atualização de status no banco de dados"""
    # Em um sistema real, aqui você faria a atualização no banco de dados
    st.session_state.df_andamento = pd.concat([
        st.session_state.df_andamento,
        pd.DataFrame({
            'proposta_id': [proposta_id],
            'data': [datetime.now()],
            'status': [novo_status],
            'observacao': [observacao]
        })
    ], ignore_index=True)
    
    st.success(f"Status atualizado para: {novo_status}")
    st.session_state.status_atual = novo_status

# Inicializar sessão
if 'df_andamento' not in st.session_state:
    st.session_state.df_andamento = gerar_dados_exemplo()
    
if 'proposta_id' not in st.session_state:
    st.session_state.proposta_id = 1
    
if 'status_atual' not in st.session_state:
    # Obter o status mais recente da proposta selecionada
    df_filtrado = st.session_state.df_andamento[
        st.session_state.df_andamento['proposta_id'] == st.session_state.proposta_id
    ]
    if not df_filtrado.empty:
        ultimo_status = df_filtrado.sort_values('data', ascending=False).iloc[0]
        st.session_state.status_atual = ultimo_status['status']
    else:
        st.session_state.status_atual = "Nova"

# Sidebar para seleção de proposta
st.sidebar.header("Opções de Demonstração")

# Seletor de proposta
proposta_ids = st.session_state.df_andamento['proposta_id'].unique()
proposta_selecionada = st.sidebar.selectbox(
    "Selecione a proposta:",
    proposta_ids,
    index=list(proposta_ids).index(st.session_state.proposta_id) if st.session_state.proposta_id in proposta_ids else 0
)

if proposta_selecionada != st.session_state.proposta_id:
    st.session_state.proposta_id = proposta_selecionada
    # Atualizar status atual para o último status da proposta selecionada
    df_filtrado = st.session_state.df_andamento[
        st.session_state.df_andamento['proposta_id'] == st.session_state.proposta_id
    ]
    if not df_filtrado.empty:
        ultimo_status = df_filtrado.sort_values('data', ascending=False).iloc[0]
        st.session_state.status_atual = ultimo_status['status']
    st.rerun()

# Layout principal
st.markdown("## Visualização do Fluxo de Status")

# Exibir fluxo de status
exibir_fluxo_status(st.session_state.status_atual)

# Divisão em colunas para layout
col1, col2 = st.columns(2)

with col1:
    # Exibir histórico
    exibir_historico_status(st.session_state.df_andamento, st.session_state.proposta_id)

with col2:
    # Mostrar gauge de progresso
    mostrar_gauge_progresso(st.session_state.status_atual)
    
    # Seletor para mudar status
    novo_status = seletor_mudar_status(
        st.session_state.status_atual, 
        st.session_state.proposta_id, 
        atualizar_status
    )

# Gráfico de linha do tempo
st.markdown("## Linha do Tempo")
fig = gerar_grafico_transicao_status(st.session_state.df_andamento, st.session_state.proposta_id)
st.plotly_chart(fig, use_container_width=True)

# Exibir dados brutos (somente para desenvolvimento)
with st.expander("Dados de Exemplo (somente para desenvolvimento)"):
    st.dataframe(st.session_state.df_andamento)