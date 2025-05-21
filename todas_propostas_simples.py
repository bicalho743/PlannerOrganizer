import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Todas as Propostas",
    page_icon="📋",
    layout="wide"
)

# Título da página
st.title("Todas as Propostas")
st.markdown("### Visualização de todas as propostas cadastradas no sistema")

# Conectar ao banco de dados
from utils.database import Database

# Inicializar banco de dados se necessário
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        st.stop()

# Função para classificar propostas por status
def classificar_proposta(row):
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

# Função principal
try:
    # Carregar todas as propostas
    propostas = st.session_state.db.get_propostas()
    
    if propostas.empty:
        st.warning("Não há propostas cadastradas no sistema.")
    else:
        # Adicionar classificação por status
        propostas['categoria'] = propostas.apply(classificar_proposta, axis=1)
        
        # Mostrar estatísticas gerais
        total_propostas = len(propostas)
        st.success(f"Total de propostas: {total_propostas}")
        
        # Filtros básicos
        st.subheader("Filtros")
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por status
            status_options = ['Todas'] + sorted(propostas['categoria'].unique().tolist())
            status_filtro = st.selectbox("Status:", status_options)
        
        with col2:
            # Filtro por cliente
            clientes = ['Todos'] + sorted(propostas['cliente_nome'].unique().tolist())
            cliente_filtro = st.selectbox("Cliente:", clientes)
        
        # Aplicar filtros
        propostas_filtradas = propostas.copy()
        
        # Filtrar por status
        if status_filtro != 'Todas':
            propostas_filtradas = propostas_filtradas[propostas_filtradas['categoria'] == status_filtro]
        
        # Filtrar por cliente
        if cliente_filtro != 'Todos':
            propostas_filtradas = propostas_filtradas[propostas_filtradas['cliente_nome'] == cliente_filtro]
        
        # Mostrar quantidade após filtros
        st.write(f"Propostas encontradas após filtros: {len(propostas_filtradas)}")
        
        # Formatar valor para exibição
        def formatar_valor(valor):
            if pd.isna(valor):
                return "R$ 0,00"
            try:
                return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except:
                return f"R$ {valor}"
        
        propostas_filtradas['valor_formatado'] = propostas_filtradas['valor'].apply(formatar_valor)
        
        # Tabela de propostas
        st.subheader("Lista de Propostas")
        
        # Selecionar colunas para exibição
        colunas_exibir = [
            'numero', 'cliente_nome', 'descricao', 'valor_formatado', 
            'categoria', 'status', 'status_execucao'
        ]
        
        # Mapear nomes das colunas
        nomes_colunas = {
            'numero': 'Número',
            'cliente_nome': 'Cliente',
            'descricao': 'Descrição',
            'valor_formatado': 'Valor',
            'categoria': 'Categoria',
            'status': 'Status',
            'status_execucao': 'Status Execução'
        }
        
        # Exibir tabela
        st.dataframe(
            propostas_filtradas[colunas_exibir].rename(columns=nomes_colunas),
            use_container_width=True,
            hide_index=True
        )
        
        # Resumo por categoria
        st.subheader("Resumo por Categoria")
        contagem_categorias = propostas['categoria'].value_counts().reset_index()
        contagem_categorias.columns = ['Categoria', 'Quantidade']
        
        # Gráfico de barras
        st.bar_chart(contagem_categorias, x='Categoria', y='Quantidade')
        
        # Botão para retornar ao dashboard
        if st.button("Voltar ao Dashboard"):
            st.info("Redirecionando para o dashboard...")
            st.stop()
        
except Exception as e:
    st.error(f"Ocorreu um erro: {str(e)}")
    import traceback
    st.error(traceback.format_exc())