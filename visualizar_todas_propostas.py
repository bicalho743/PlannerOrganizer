import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
try:
    st.set_page_config(
        page_title="Visualizar Todas as Propostas",
        page_icon="📊",
        layout="wide"
    )
except:
    pass

st.title("📊 Visualizar Todas as Propostas")
st.write("Dashboard completo de todas as propostas do sistema.")

# Inicializar banco de dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_propostas():
    try:
        from utils.database import Database
        db = Database()
        return db.get_propostas()
    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")
        return pd.DataFrame()

# Carregar dados
propostas = load_propostas()

if propostas.empty:
    st.warning("Nenhuma proposta encontrada no sistema.")
    st.stop()

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_propostas = len(propostas)
    st.metric("Total de Propostas", total_propostas)

with col2:
    if 'valor' in propostas.columns:
        valor_total = propostas['valor'].sum()
        st.metric("Valor Total", f"R$ {valor_total:,.2f}")
    else:
        st.metric("Valor Total", "N/A")

with col3:
    if 'status' in propostas.columns:
        aprovadas = len(propostas[propostas['status'] == 'Aprovada'])
        st.metric("Propostas Aprovadas", aprovadas)
    else:
        st.metric("Propostas Aprovadas", "N/A")

with col4:
    if 'valor' in propostas.columns and len(propostas) > 0:
        valor_medio = propostas['valor'].mean()
        st.metric("Valor Médio", f"R$ {valor_medio:,.2f}")
    else:
        st.metric("Valor Médio", "N/A")

# Filtros
st.markdown("---")
st.subheader("🔍 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    # Filtro por status
    if 'status' in propostas.columns:
        status_options = ['Todos'] + list(propostas['status'].unique())
        status_filter = st.selectbox("Status", status_options)
    else:
        status_filter = 'Todos'

with col2:
    # Filtro por cliente
    if 'cliente_nome' in propostas.columns:
        cliente_options = ['Todos'] + list(propostas['cliente_nome'].unique())
        cliente_filter = st.selectbox("Cliente", cliente_options)
    else:
        cliente_filter = 'Todos'

with col3:
    # Filtro por período
    if 'data_criacao' in propostas.columns:
        min_date = propostas['data_criacao'].min().date() if pd.notna(propostas['data_criacao'].min()) else datetime.now().date()
        max_date = propostas['data_criacao'].max().date() if pd.notna(propostas['data_criacao'].max()) else datetime.now().date()
        
        date_range = st.date_input(
            "Período",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = None

# Aplicar filtros
propostas_filtradas = propostas.copy()

if status_filter != 'Todos' and 'status' in propostas.columns:
    propostas_filtradas = propostas_filtradas[propostas_filtradas['status'] == status_filter]

if cliente_filter != 'Todos' and 'cliente_nome' in propostas.columns:
    propostas_filtradas = propostas_filtradas[propostas_filtradas['cliente_nome'] == cliente_filter]

if date_range and len(date_range) == 2 and 'data_criacao' in propostas.columns:
    start_date, end_date = date_range
    propostas_filtradas = propostas_filtradas[
        (propostas_filtradas['data_criacao'].dt.date >= start_date) &
        (propostas_filtradas['data_criacao'].dt.date <= end_date)
    ]

# Gráficos
st.markdown("---")
st.subheader("📈 Análises")

if not propostas_filtradas.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de status
        if 'status' in propostas_filtradas.columns:
            st.markdown("**Distribuição por Status**")
            status_counts = propostas_filtradas['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Propostas por Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Gráfico de valores por mês
        if 'data_criacao' in propostas_filtradas.columns and 'valor' in propostas_filtradas.columns:
            st.markdown("**Valores por Mês**")
            propostas_filtradas['mes'] = propostas_filtradas['data_criacao'].dt.to_period('M')
            valores_mes = propostas_filtradas.groupby('mes')['valor'].sum().reset_index()
            valores_mes['mes'] = valores_mes['mes'].astype(str)
            
            fig_valores = px.bar(
                valores_mes,
                x='mes',
                y='valor',
                title="Valor Total por Mês"
            )
            st.plotly_chart(fig_valores, use_container_width=True)

# Tabela detalhada
st.markdown("---")
st.subheader("📋 Detalhes das Propostas")
st.write(f"Mostrando {len(propostas_filtradas)} de {len(propostas)} propostas")

# Preparar dados para exibição
if not propostas_filtradas.empty:
    display_columns = []
    
    # Selecionar colunas relevantes para exibição
    available_columns = propostas_filtradas.columns.tolist()
    preferred_columns = ['numero', 'cliente_nome', 'descricao', 'valor', 'status', 'data_criacao']
    
    for col in preferred_columns:
        if col in available_columns:
            display_columns.append(col)
    
    # Adicionar outras colunas importantes
    for col in available_columns:
        if col not in display_columns and col not in ['id', 'usuario_id']:
            display_columns.append(col)
    
    # Formatação de dados
    display_df = propostas_filtradas[display_columns].copy()
    
    # Formatar valores monetários
    if 'valor' in display_df.columns:
        display_df['valor'] = display_df['valor'].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00")
    
    # Formatar datas
    date_columns = [col for col in display_df.columns if 'data' in col.lower()]
    for col in date_columns:
        if display_df[col].dtype == 'datetime64[ns]':
            display_df[col] = display_df[col].dt.strftime('%d/%m/%Y')
    
    # Exibir tabela
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Opção de download
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Baixar CSV",
        data=csv,
        file_name=f"propostas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    st.info("Nenhuma proposta encontrada com os filtros aplicados.")

# Botão de atualização
st.markdown("---")
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()