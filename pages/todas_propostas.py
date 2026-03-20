import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import text
from utils.currency_formatter import fmt_brl
import sys
import os

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def carregar_todas_propostas():
    """Carrega todas as propostas diretamente com SQL para evitar problemas de tipos de dados"""
    try:
        # Usar SQL direto para maior controle sobre os tipos
        # Criar conexão com banco de dados
        with st.session_state.db.engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT 
                    p.id, 
                    p.numero, 
                    c.nome as cliente_nome, 
                    p.descricao, 
                    p.status, 
                    p.status_execucao,
                    p.data_inicio,
                    p.data_fim,
                    p.valor,
                    TO_CHAR(p.data_criacao, 'DD/MM/YYYY') as data_criacao,
                    COALESCE(p.tipo_proposta, '') as tipo_proposta
                FROM 
                    propostas p
                JOIN 
                    clientes c ON p.cliente_id = c.id
                WHERE 
                    p.usuario_id = :usuario_id
                ORDER BY 
                    p.numero DESC
                """),
                {"usuario_id": st.session_state.get('usuario_id', '')}
            )
            
            # Processar resultados
            propostas_list = []
            for row in result:
                # Tratar datas
                data_inicio_fmt = row[6].strftime('%d/%m/%Y') if row[6] else "-"
                data_fim_fmt = row[7].strftime('%d/%m/%Y') if row[7] else "-"
                
                # Tratar valor monetário
                valor_fmt = fmt_brl(row[8])
                
                # Definir categoria para agrupar por status
                status_categoria = None
                if row[4] == 'Aberta' or row[4] == 'Em análise':
                    status_categoria = 'Abertas'
                elif row[4] == 'Aprovada' and row[5] == 'Em execução':
                    status_categoria = 'Em execução'
                elif row[4] == 'Aprovada' and row[5] == 'Finalizada':
                    status_categoria = 'Finalizadas'
                elif row[4] == 'Recusada' or row[5] == 'Cancelada':
                    status_categoria = 'Recusadas'
                else:
                    status_categoria = 'Outras'
                
                # Adicionar à lista de propostas
                propostas_list.append({
                    'id': row[0],
                    'numero': str(row[1]),
                    'cliente_nome': row[2],
                    'descricao': row[3],
                    'status': row[4],
                    'status_execucao': row[5],
                    'data_inicio': data_inicio_fmt,
                    'data_fim': data_fim_fmt,
                    'valor': valor_fmt,
                    'data_criacao': row[9],
                    'tipo_proposta': row[10],
                    'categoria_status': status_categoria
                })
            
            return pd.DataFrame(propostas_list)
            
    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")
        return pd.DataFrame()

def mostrar_todas_propostas():
    """Página principal para mostrar todas as propostas"""
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Todas as Propostas</h1>', unsafe_allow_html=True)
    st.info("Esta página mostra todas as propostas, independentemente do status - Abertas, Em execução, Finalizadas e Recusadas.")
    
    # Carregar todas as propostas
    todas_propostas = carregar_todas_propostas()
    
    # Exibir as propostas carregadas
    if todas_propostas.empty:
        st.warning("Não há propostas cadastradas no sistema.")
    else:
        # Mostrar total de propostas
        st.success(f"Total de propostas: {len(todas_propostas)}")
        
        # Criar filtros em 3 colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por status
            cat_status = ['Todas'] + sorted(todas_propostas['categoria_status'].unique().tolist())
            status_selecionado = st.selectbox("Status:", cat_status, key="status_filtro_todas")
        
        with col2:
            # Filtro por cliente
            clientes_lista = ['Todos'] + sorted(todas_propostas['cliente_nome'].unique().tolist())
            cliente_selecionado = st.selectbox("Cliente:", clientes_lista, key="cliente_filtro_todas")
        
        with col3:
            # Opções de filtro de período
            periodo_opcoes = ["Todos", "Últimos 30 dias", "Últimos 60 dias", "Últimos 90 dias", "Este ano"]
            periodo_selecionado = st.selectbox("Período:", periodo_opcoes, key="periodo_filtro_todas")
        
        # Aplicar filtros selecionados
        df_filtrado = todas_propostas.copy()
        
        # Filtro por status
        if status_selecionado != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['categoria_status'] == status_selecionado]
        
        # Filtro por cliente
        if cliente_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['cliente_nome'] == cliente_selecionado]
        
        # Mostrar resultado dos filtros
        st.write(f"Propostas encontradas após filtros: {len(df_filtrado)}")
        
        # Exibir tabela de propostas
        if not df_filtrado.empty:
            # Selecionar e renomear colunas para exibição
            colunas_mostrar = [
                'numero', 'cliente_nome', 'descricao', 'valor', 
                'categoria_status', 'data_inicio', 'data_fim'
            ]
            
            # Mapear nomes das colunas para o português correto
            nomes_colunas = {
                'numero': 'Número',
                'cliente_nome': 'Cliente',
                'descricao': 'Descrição',
                'valor': 'Valor',
                'categoria_status': 'Status',
                'data_inicio': 'Data Início',
                'data_fim': 'Data Fim'
            }
            
            # Criar DataFrame de exibição
            df_exibir = df_filtrado[colunas_mostrar].rename(columns=nomes_colunas)
            
            # Exibir o DataFrame
            st.dataframe(df_exibir, hide_index=True, use_container_width=True)
            
            # Seção para ver detalhes da proposta
            st.subheader("Visualizar detalhes da proposta")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                num_proposta = st.selectbox(
                    "Selecione o número da proposta:", 
                    sorted(df_filtrado['numero'].unique()), 
                    key="selecao_proposta_todas"
                )
            
            with col2:
                if st.button("Ver detalhes completos", key="btn_detalhes_todas"):
                    if num_proposta:
                        # Obter detalhes da proposta selecionada
                        proposta = df_filtrado[df_filtrado['numero'] == num_proposta].iloc[0]
                        
                        # Exibir card com detalhes
                        with st.expander("Detalhes da Proposta", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Número:** {proposta['numero']}")
                                st.markdown(f"**Cliente:** {proposta['cliente_nome']}")
                                st.markdown(f"**Descrição:** {proposta['descricao']}")
                                st.markdown(f"**Valor:** {proposta['valor']}")
                                st.markdown(f"**Tipo de Proposta:** {proposta['tipo_proposta']}")
                            
                            with col2:
                                st.markdown(f"**Status:** {proposta['status']}")
                                st.markdown(f"**Status Execução:** {proposta['status_execucao']}")
                                st.markdown(f"**Categoria:** {proposta['categoria_status']}")
                                st.markdown(f"**Data Início:** {proposta['data_inicio']}")
                                st.markdown(f"**Data Fim:** {proposta['data_fim']}")
                                st.markdown(f"**Data Criação:** {proposta['data_criacao']}")
                            
                            # Adicionar botões para ações específicas
                            st.markdown("---")
                            st.write("**Ações disponíveis:**")
                            
                            if proposta['categoria_status'] == "Em execução":
                                st.info("⚠️ Para finalizar esta proposta, vá até a aba 'Em Execução'")
                            
                            if proposta['categoria_status'] == "Finalizadas":
                                st.info("🔄 Para reabrir esta proposta, vá até a aba 'Propostas Finalizadas'")
            
            # Adicionar gráfico de resumo
            st.subheader("Resumo por Status")
            contagem_status = df_filtrado['categoria_status'].value_counts().reset_index()
            contagem_status.columns = ['Status', 'Quantidade']
            
            # Gerar gráfico de barras
            fig = go.Figure(data=[
                go.Bar(
                    x=contagem_status['Status'],
                    y=contagem_status['Quantidade'],
                    marker_color=['#FFA07A', '#87CEFA', '#98FB98', '#FFB6C1'][:len(contagem_status)]
                )
            ])
            
            fig.update_layout(
                title='Distribuição de Propostas por Status',
                xaxis_title='Status',
                yaxis_title='Quantidade',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Função principal para quando o script é executado diretamente"""
    if 'db' in st.session_state:
        mostrar_todas_propostas()
    else:
        st.error("Nenhuma conexão com o banco de dados disponível.")
        st.info("Por favor, acesse esta página a partir do aplicativo principal.")

if __name__ == "__main__":
    main()