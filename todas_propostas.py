import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Todas as Propostas",
    page_icon="📊",
    layout="wide"
)

# Título e descrição
st.title("Todas as Propostas")
st.markdown("### Visualização de todas as propostas cadastradas no sistema")

# Conectar ao banco de dados
from utils.database import Database

try:
    # Inicializar o banco de dados se ainda não estiver inicializado
    if "db" not in st.session_state:
        st.session_state.db = Database()
    
    # Obter todas as propostas do banco de dados
    propostas = st.session_state.db.get_propostas()
    
    if propostas.empty:
        st.warning("Não há propostas cadastradas no sistema.")
    else:
        # Adicionar nova coluna de categorização para facilitar a filtragem
        def categorizar_proposta(row):
            if row['status'] == 'Aberta' or row['status'] == 'Em análise':
                return 'Abertas'
            elif row['status'] == 'Aprovada' and row['status_execucao'] == 'Em execução':
                return 'Em execução'
            elif row['status'] == 'Aprovada' and row['status_execucao'] == 'Finalizada':
                return 'Finalizadas'
            elif row['status'] == 'Recusada' or row['status_execucao'] == 'Cancelada':
                return 'Recusadas'
            else:
                return 'Outras'
        
        propostas['categoria'] = propostas.apply(categorizar_proposta, axis=1)
        
        # Mostrar estatísticas gerais
        st.success(f"Total de propostas: {len(propostas)}")
        
        # Área de filtros
        st.subheader("Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por status
            status_options = ['Todos'] + sorted(propostas['categoria'].unique().tolist())
            status_filter = st.selectbox('Status:', status_options)
        
        with col2:
            # Filtro por cliente
            client_options = ['Todos'] + sorted(propostas['cliente_nome'].unique().tolist())
            client_filter = st.selectbox('Cliente:', client_options)
        
        with col3:
            # Filtro por valor
            min_value = float(propostas['valor'].min())
            max_value = float(propostas['valor'].max())
            value_filter = st.slider('Valor (R$):', 
                               min_value=min_value, 
                               max_value=max_value, 
                               value=(min_value, max_value))
        
        # Aplicar filtros
        filtered_proposals = propostas.copy()
        
        # Filtrar por status
        if status_filter != 'Todos':
            filtered_proposals = filtered_proposals[filtered_proposals['categoria'] == status_filter]
        
        # Filtrar por cliente
        if client_filter != 'Todos':
            filtered_proposals = filtered_proposals[filtered_proposals['cliente_nome'] == client_filter]
        
        # Filtrar por valor
        filtered_proposals = filtered_proposals[
            (filtered_proposals['valor'] >= value_filter[0]) & 
            (filtered_proposals['valor'] <= value_filter[1])
        ]
        
        # Mostrar resultado dos filtros
        st.write(f"Propostas encontradas: {len(filtered_proposals)}")
        
        # Exibir tabela com todas as propostas filtradas
        st.subheader("Lista de Propostas")
        
        # Configurar colunas para exibição
        columns_to_display = [
            'numero', 'cliente_nome', 'descricao', 'valor', 
            'categoria', 'status', 'status_execucao', 
            'data_inicio', 'data_fim'
        ]
        
        # Renomear colunas para exibição
        column_names = {
            'numero': 'Número',
            'cliente_nome': 'Cliente',
            'descricao': 'Descrição',
            'valor': 'Valor (R$)',
            'categoria': 'Categoria',
            'status': 'Status',
            'status_execucao': 'Status Execução',
            'data_inicio': 'Data Início',
            'data_fim': 'Data Fim'
        }
        
        # Preparar DataFrame para exibição
        display_df = filtered_proposals[columns_to_display].rename(columns=column_names)
        
        # Exibir DataFrame
        st.dataframe(display_df, use_container_width=True)
        
        # Adicionar visualização de detalhes da proposta
        st.subheader("Detalhes da Proposta")
        
        # Selecionar proposta
        selected_proposal_number = st.selectbox(
            "Selecione o número da proposta para ver detalhes:",
            options=sorted(filtered_proposals['numero'].unique().tolist())
        )
        
        # Exibir detalhes
        if st.button("Ver Detalhes"):
            # Encontrar a proposta pelo número
            proposal = filtered_proposals[filtered_proposals['numero'] == selected_proposal_number].iloc[0]
            
            # Exibir card com detalhes
            with st.expander("Detalhes completos", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Número:** {proposal['numero']}")
                    st.markdown(f"**Cliente:** {proposal['cliente_nome']}")
                    st.markdown(f"**Descrição:** {proposal['descricao']}")
                    st.markdown(f"**Valor:** R$ {float(proposal['valor']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    if 'tipo_proposta' in proposal and pd.notna(proposal['tipo_proposta']):
                        st.markdown(f"**Tipo de Proposta:** {proposal['tipo_proposta']}")
                
                with col2:
                    st.markdown(f"**Status:** {proposal['status']}")
                    st.markdown(f"**Status Execução:** {proposal['status_execucao']}")
                    st.markdown(f"**Categoria:** {proposal['categoria']}")
                    
                    # Formatar datas
                    if pd.notna(proposal['data_inicio']):
                        data_inicio_fmt = proposal['data_inicio'].strftime('%d/%m/%Y')
                        st.markdown(f"**Data Início:** {data_inicio_fmt}")
                    
                    if pd.notna(proposal['data_fim']):
                        data_fim_fmt = proposal['data_fim'].strftime('%d/%m/%Y')
                        st.markdown(f"**Data Fim:** {data_fim_fmt}")
        
        # Adicionar gráfico de distribuição por categoria
        st.subheader("Distribuição de Propostas por Categoria")
        category_counts = propostas['categoria'].value_counts().reset_index()
        category_counts.columns = ['Categoria', 'Quantidade']
        
        st.bar_chart(category_counts, x='Categoria', y='Quantidade')

except Exception as e:
    st.error(f"Ocorreu um erro ao carregar as propostas: {str(e)}")
    import traceback
    st.error(traceback.format_exc())