import streamlit as st
import pandas as pd
from datetime import datetime
from utils.currency_formatter import fmt_brl
import os
import sys

# Configuração da página
st.set_page_config(
    page_title="Todas as Propostas",
    page_icon="📊",
    layout="wide"
)

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Importar módulos necessários
from utils.database import Database
from utils.auth import check_authentication

# Verificar autenticação
if not check_authentication():
    st.error("Você precisa estar logado para acessar esta página.")
    st.stop()

# Título da página
st.title("Todas as Propostas")
st.markdown("### Visualização completa de todas as propostas cadastradas no sistema")

# Inicializar banco de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

try:
    # Carregar todas as propostas do banco de dados
    propostas = st.session_state.db.get_propostas()
    
    if propostas.empty:
        st.warning("Não há propostas cadastradas no sistema.")
    else:
        # Mostrar estatísticas
        st.success(f"Total de propostas: {len(propostas)}")
        
        # Adicionar classificação por status
        def classificar_status(row):
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
        
        propostas['categoria'] = propostas.apply(classificar_status, axis=1)
        
        # Criar filtros em colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por status
            categorias = ['Todas'] + sorted(propostas['categoria'].unique().tolist())
            filtro_status = st.selectbox("Filtrar por status:", categorias)
        
        with col2:
            # Filtro por cliente
            clientes = ['Todos'] + sorted(propostas['cliente_nome'].unique().tolist())
            filtro_cliente = st.selectbox("Filtrar por cliente:", clientes)
        
        with col3:
            # Filtro por período
            opcoes_periodo = ['Todos', 'Este mês', 'Últimos 3 meses', 'Este ano']
            filtro_periodo = st.selectbox("Filtrar por período:", opcoes_periodo)
        
        # Aplicar filtros
        propostas_filtradas = propostas.copy()
        
        # Filtrar por status
        if filtro_status != 'Todas':
            propostas_filtradas = propostas_filtradas[propostas_filtradas['categoria'] == filtro_status]
        
        # Filtrar por cliente
        if filtro_cliente != 'Todos':
            propostas_filtradas = propostas_filtradas[propostas_filtradas['cliente_nome'] == filtro_cliente]
        
        # Filtrar por período
        hoje = datetime.now()
        if filtro_periodo == 'Este mês':
            mes_atual = hoje.month
            ano_atual = hoje.year
            propostas_filtradas = propostas_filtradas[
                (propostas_filtradas['data_inicio'].dt.month == mes_atual) & 
                (propostas_filtradas['data_inicio'].dt.year == ano_atual)
            ]
        elif filtro_periodo == 'Últimos 3 meses':
            tres_meses_atras = hoje - pd.Timedelta(days=90)
            propostas_filtradas = propostas_filtradas[propostas_filtradas['data_inicio'] >= tres_meses_atras]
        elif filtro_periodo == 'Este ano':
            ano_atual = hoje.year
            propostas_filtradas = propostas_filtradas[propostas_filtradas['data_inicio'].dt.year == ano_atual]
        
        # Mostrar contagem após filtros
        st.write(f"Propostas encontradas após filtros: {len(propostas_filtradas)}")
        
        # Preparar dados para exibição
        propostas_filtradas['valor_formatado'] = propostas_filtradas['valor'].apply(fmt_brl)
        
        # Exibir tabela com todas as propostas filtradas
        colunas_exibir = [
            'numero', 'cliente_nome', 'descricao', 'valor_formatado', 
            'categoria', 'status', 'status_execucao', 'data_inicio', 'data_fim'
        ]
        
        # Mapear nomes das colunas para exibição
        nomes_colunas = {
            'numero': 'Número',
            'cliente_nome': 'Cliente',
            'descricao': 'Descrição',
            'valor_formatado': 'Valor',
            'categoria': 'Categoria',
            'status': 'Status',
            'status_execucao': 'Status Execução',
            'data_inicio': 'Data Início',
            'data_fim': 'Data Fim'
        }
        
        st.dataframe(
            propostas_filtradas[colunas_exibir].rename(columns=nomes_colunas),
            use_container_width=True,
            hide_index=True
        )
        
        # Seção para visualizar detalhes de proposta específica
        st.subheader("Visualizar Detalhes")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            numeros_propostas = sorted(propostas_filtradas['numero'].astype(str).tolist())
            proposta_selecionada = st.selectbox("Selecione uma proposta:", numeros_propostas)
        
        with col2:
            if st.button("Ver detalhes da proposta"):
                # Encontrar a proposta selecionada
                proposta = propostas_filtradas[propostas_filtradas['numero'].astype(str) == proposta_selecionada].iloc[0]
                
                # Exibir detalhes em um card expandido
                with st.expander("Detalhes da Proposta", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Número:** {proposta['numero']}")
                        st.markdown(f"**Cliente:** {proposta['cliente_nome']}")
                        st.markdown(f"**Descrição:** {proposta['descricao']}")
                        st.markdown(f"**Valor:** {proposta['valor_formatado']}")
                        if 'tipo_proposta' in proposta:
                            st.markdown(f"**Tipo de Proposta:** {proposta['tipo_proposta']}")
                    
                    with col2:
                        st.markdown(f"**Status:** {proposta['status']}")
                        st.markdown(f"**Status Execução:** {proposta['status_execucao']}")
                        st.markdown(f"**Categoria:** {proposta['categoria']}")
                        
                        # Formatar datas se disponíveis
                        if pd.notna(proposta['data_inicio']):
                            data_inicio = proposta['data_inicio'].strftime('%d/%m/%Y')
                            st.markdown(f"**Data Início:** {data_inicio}")
                        
                        if pd.notna(proposta['data_fim']):
                            data_fim = proposta['data_fim'].strftime('%d/%m/%Y')
                            st.markdown(f"**Data Fim:** {data_fim}")
                        
                        if 'data_criacao' in proposta and pd.notna(proposta['data_criacao']):
                            st.markdown(f"**Data Criação:** {proposta['data_criacao']}")
                    
                    # Informar sobre ações disponíveis
                    st.markdown("---")
                    st.subheader("Ações disponíveis:")
                    
                    if proposta['categoria'] == "Em execução":
                        st.info("Para finalizar esta proposta, acesse a página Propostas > Em Execução")
                    
                    if proposta['categoria'] == "Finalizadas":
                        st.info("Para reabrir esta proposta, acesse a página Propostas > Propostas Finalizadas")
        
        # Adicionar contagem por status
        st.subheader("Distribuição de Propostas por Status")
        contagem_status = propostas['categoria'].value_counts().reset_index()
        contagem_status.columns = ['Status', 'Quantidade']
        
        st.bar_chart(
            contagem_status, 
            x='Status', 
            y='Quantidade',
            use_container_width=True
        )
        
        # Botão para voltar ao dashboard
        if st.button("Voltar para o Dashboard"):
            js = """
            <script>
            window.location.href = '/';
            </script>
            """
            st.components.v1.html(js)

except Exception as e:
    st.error(f"Ocorreu um erro ao carregar as propostas: {str(e)}")
    import traceback
    st.error(traceback.format_exc())