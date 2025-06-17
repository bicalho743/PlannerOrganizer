"""
Módulo para visualização de transições de status das propostas
Este módulo fornece componentes visuais para exibir o fluxo de status
das propostas de forma intuitiva.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Configuração dos status possíveis e suas transições
STATUS_PROPOSTAS = {
    "Nova": {
        "cor": "#3498db",  # Azul
        "icone": "🆕",
        "proximos": ["Em Análise", "Aprovada", "Recusada"]
    },
    "Em Análise": {
        "cor": "#f39c12",  # Laranja
        "icone": "🔍",
        "proximos": ["Aprovada", "Recusada", "Nova"]
    },
    "Aprovada": {
        "cor": "#2ecc71",  # Verde
        "icone": "✅",
        "proximos": ["Em Execução", "Finalizada"]
    },
    "Recusada": {
        "cor": "#e74c3c",  # Vermelho
        "icone": "❌",
        "proximos": ["Nova"]
    },
    "Em Execução": {
        "cor": "#9b59b6",  # Roxo
        "icone": "⚙️",
        "proximos": ["Finalizada", "Cancelada"]
    },
    "Finalizada": {
        "cor": "#27ae60",  # Verde escuro
        "icone": "🏁",
        "proximos": []
    },
    "Cancelada": {
        "cor": "#7f8c8d",  # Cinza
        "icone": "🚫",
        "proximos": []
    }
}

def exibir_fluxo_status(status_atual=None):
    """
    Exibe um diagrama visual do fluxo de status das propostas
    
    Args:
        status_atual: Status atual da proposta, para destacar
    """
    st.markdown("### Fluxo de Status da Proposta")
    
    # Desenhar as caixas de status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        exibir_caixa_status("Nova", status_atual)
    
    with col2:
        exibir_caixa_status("Em Análise", status_atual)
        
    with col3:
        exibir_caixa_status("Aprovada", status_atual)
        
    with col4:
        exibir_caixa_status("Recusada", status_atual)
    
    # Segunda linha para os status finais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        exibir_caixa_status("Em Execução", status_atual)
        
    with col2:
        exibir_caixa_status("Finalizada", status_atual)
        
    with col3:
        exibir_caixa_status("Cancelada", status_atual)

def exibir_caixa_status(status, status_atual=None):
    """
    Exibe uma caixa para um status específico
    
    Args:
        status: Nome do status a exibir
        status_atual: Status atual da proposta, para destacar
    """
    if status not in STATUS_PROPOSTAS:
        return
    
    config = STATUS_PROPOSTAS[status]
    icone = config["icone"]
    cor = config["cor"]
    
    # Destacar o status atual
    estilo = ""
    if status == status_atual:
        estilo = f"border: 3px solid {cor}; box-shadow: 0 0 10px {cor};"
    else:
        estilo = f"border: 1px solid {cor};"
    
    # Criar caixa com HTML/CSS
    html = f"""
    <div style="padding: 10px; border-radius: 5px; background-color: {cor}20; {estilo} text-align: center; margin-bottom: 10px;">
        <div style="font-size: 24px;">{icone}</div>
        <div style="font-weight: bold; color: {cor};">{status}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    # Mostrar próximos status possíveis
    if status == status_atual and config["proximos"]:
        with st.expander("Próximos status possíveis"):
            for proximo in config["proximos"]:
                st.markdown(f"• {STATUS_PROPOSTAS[proximo]['icone']} {proximo}")

def gerar_grafico_transicao_status(df_andamento, proposta_id=None):
    """
    Gera um gráfico de linha do tempo mostrando as transições de status da proposta
    
    Args:
        df_andamento: DataFrame com o histórico de status (colunas: proposta_id, data, status)
        proposta_id: ID da proposta para filtrar, ou None para todas
    
    Returns:
        fig: Figura do Plotly com o gráfico de linha do tempo
    """
    # Filtrar para a proposta específica se fornecida
    if proposta_id is not None:
        df = df_andamento[df_andamento['proposta_id'] == proposta_id].copy()
    else:
        df = df_andamento.copy()
    
    # Ordenar por data
    df = df.sort_values('data')
    
    # Criar gráfico
    fig = px.timeline(
        df, 
        x_start='data',
        x_end='data',  # Mesma data para início e fim
        y='proposta_id',
        color='status',
        hover_name='status',
        labels={"proposta_id": "Proposta", "data": "Data", "status": "Status"},
        color_discrete_map={
            status: config["cor"] 
            for status, config in STATUS_PROPOSTAS.items()
        }
    )
    
    # Adicionar rótulos com ícones
    for i, row in df.iterrows():
        status = row['status']
        if status in STATUS_PROPOSTAS:
            fig.add_annotation(
                x=row['data'],
                y=row['proposta_id'],
                text=STATUS_PROPOSTAS[status]["icone"],
                showarrow=False,
                font=dict(size=16)
            )
    
    # Configurar layout
    fig.update_layout(
        title="Histórico de Status da Proposta",
        xaxis_title="Data",
        yaxis_title="Proposta",
        height=300,
        margin=dict(l=10, r=10, t=50, b=30)
    )
    
    return fig

def exibir_historico_status(df_andamento, proposta_id):
    """
    Exibe o histórico de status de uma proposta específica
    
    Args:
        df_andamento: DataFrame com o histórico de status (colunas: proposta_id, data, status, observacao)
        proposta_id: ID da proposta para exibir
    """
    # Filtrar andamentos da proposta específica
    andamentos = df_andamento[df_andamento['proposta_id'] == proposta_id].copy()
    
    if andamentos.empty:
        st.info("Não há histórico de status para esta proposta.")
        return
    
    # Ordenar por data (mais recente primeiro)
    andamentos = andamentos.sort_values('data', ascending=False)
    
    # Adicionar informações de ícone e cor
    andamentos['icone'] = andamentos['status'].apply(
        lambda x: STATUS_PROPOSTAS.get(x, {}).get('icone', '📝')
    )
    andamentos['cor'] = andamentos['status'].apply(
        lambda x: STATUS_PROPOSTAS.get(x, {}).get('cor', '#777777')
    )
    
    # Exibir linha do tempo
    st.markdown("### Histórico de Status")
    
    for i, row in andamentos.iterrows():
        data_str = row['data'].strftime('%d/%m/%Y')
        status = row['status']
        observacao = row.get('observacao', '')
        icone = row['icone']
        cor = row['cor']
        
        # Criar caixa de histórico com HTML/CSS
        html = f"""
        <div style="display: flex; margin-bottom: 15px;">
            <div style="font-size: 24px; margin-right: 10px;">{icone}</div>
            <div style="flex-grow: 1; border-left: 3px solid {cor}; padding-left: 10px;">
                <div style="font-weight: bold; color: {cor};">{status}</div>
                <div style="color: #666; font-size: 0.9em;">{data_str}</div>
                <div style="margin-top: 5px;">{observacao}</div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

def seletor_mudar_status(status_atual, proposta_id, callback_on_change=None):
    """
    Exibe um seletor para mudar o status da proposta
    
    Args:
        status_atual: Status atual da proposta
        proposta_id: ID da proposta
        callback_on_change: Função a ser chamada quando o status for alterado
    
    Returns:
        novo_status: O novo status selecionado, ou None se não houver alteração
    """
    if status_atual not in STATUS_PROPOSTAS:
        st.warning(f"Status atual '{status_atual}' não reconhecido.")
        return None
    
    config = STATUS_PROPOSTAS[status_atual]
    proximos_status = config["proximos"]
    
    if not proximos_status:
        st.info(f"Esta proposta já está em um status final: {config['icone']} {status_atual}")
        return None
    
    # Criar seletor de status
    st.markdown("### Atualizar Status")
    
    # Adicionar opções de status com ícones
    opcoes = [f"{STATUS_PROPOSTAS[s]['icone']} {s}" for s in proximos_status]
    opcao_selecionada = st.selectbox("Novo status:", opcoes)
    
    observacao = st.text_area("Observação (opcional):", "")
    
    if st.button("Atualizar Status", type="primary"):
        # Extrair apenas o nome do status (sem o ícone)
        novo_status = opcao_selecionada.split(" ", 1)[1]
        
        # Chamar callback se fornecido
        if callback_on_change:
            callback_on_change(proposta_id, novo_status, observacao)
        
        return novo_status
    
    return None

def mostrar_gauge_progresso(status_atual):
    """
    Exibe um medidor de progresso da proposta baseado no status atual
    
    Args:
        status_atual: Status atual da proposta
    """
    # Mapear status para porcentagem de progresso
    mapa_progresso = {
        "Nova": 0,
        "Em Análise": 25,
        "Aprovada": 50,
        "Em Execução": 75,
        "Finalizada": 100,
        "Recusada": 100,
        "Cancelada": 100
    }
    
    # Obter porcentagem de progresso
    progresso = mapa_progresso.get(status_atual, 0)
    
    # Criar gráfico de medidor
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = progresso,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Progresso"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': STATUS_PROPOSTAS.get(status_atual, {}).get('cor', '#777777')},
            'steps': [
                {'range': [0, 25], 'color': 'rgba(52, 152, 219, 0.2)'},
                {'range': [25, 50], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [50, 75], 'color': 'rgba(155, 89, 182, 0.2)'},
                {'range': [75, 100], 'color': 'rgba(46, 204, 113, 0.2)'}
            ],
            'threshold': {
                'line': {'color': STATUS_PROPOSTAS.get(status_atual, {}).get('cor', '#777777'), 'width': 4},
                'thickness': 0.75,
                'value': progresso
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=30))
    
    st.plotly_chart(fig, use_container_width=True)