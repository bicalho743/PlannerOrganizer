import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    
from utils.database import Database
from utils.auth import verificar_autenticacao, redirecionar_login

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Todas as Propostas - Sistema de Gerenciamento",
        page_icon="🔍",
        layout="wide"
    )

    # Verificar autenticação
    if not verificar_autenticacao():
        redirecionar_login()
        return

    # Título principal
    st.title("Visualização Completa de Propostas")
    st.markdown("### Todas as propostas do sistema em uma única visão")
    
    # Inicializar conexão com o banco de dados se ainda não estiver na sessão
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Carregar as propostas com uma consulta SQL direta para evitar problemas de tipo
    try:
        with st.spinner("Carregando todas as propostas..."):
            # Usar SQL direto para melhor controle dos tipos de dados
            with st.session_state.db.engine.connect() as conn:
                query = """
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
                """
                
                # Executar a consulta
                result = conn.execute(pd.read_sql_query(
                    query, 
                    conn, 
                    params={"usuario_id": st.session_state.get('usuario_id', '')}
                ))
                
                # Processar os resultados em um DataFrame
                df = pd.DataFrame(result)
                
                # Se não houver propostas, mostrar mensagem
                if df.empty:
                    st.warning("Não há propostas cadastradas no sistema.")
                    return
                
                # Processar os dados para exibição
                df_processado = processar_dados_propostas(df)
                
                # Mostrar informações gerais
                st.success(f"Total de propostas encontradas: {len(df_processado)}")
                
                # Criar seção de filtros
                st.subheader("Filtros")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Adicionar categoria_status para facilitar filtragem
                    categorias = ["Todas"] + sorted(df_processado["categoria_status"].unique().tolist())
                    status_selecionado = st.selectbox("Status:", categorias)
                
                with col2:
                    # Filtro por cliente
                    clientes = ["Todos"] + sorted(df_processado["cliente_nome"].unique().tolist())
                    cliente_selecionado = st.selectbox("Cliente:", clientes)
                
                with col3:
                    # Filtro por período
                    opcoes_periodo = ["Todos", "Últimos 30 dias", "Últimos 60 dias", "Últimos 90 dias", "Este ano"]
                    periodo_selecionado = st.selectbox("Período:", opcoes_periodo)
                
                # Aplicar filtros
                df_filtrado = aplicar_filtros(df_processado, status_selecionado, cliente_selecionado, periodo_selecionado)
                
                # Exibir resultados
                st.write(f"Propostas após filtros: {len(df_filtrado)}")
                
                # Tabela principal com todas as propostas filtradas
                st.subheader("Lista de Propostas")
                
                # Selecionar colunas para exibição
                colunas_exibir = [
                    "numero", "cliente_nome", "descricao", "valor_formatado", 
                    "categoria_status", "data_inicio_formatada", "data_fim_formatada"
                ]
                
                # Renomear colunas para exibição
                nomes_colunas = {
                    "numero": "Número",
                    "cliente_nome": "Cliente",
                    "descricao": "Descrição",
                    "valor_formatado": "Valor",
                    "categoria_status": "Status",
                    "data_inicio_formatada": "Data Início",
                    "data_fim_formatada": "Data Fim"
                }
                
                # Exibir tabela
                st.dataframe(
                    df_filtrado[colunas_exibir].rename(columns=nomes_colunas), 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Seção para visualizar detalhes de uma proposta específica
                st.subheader("Detalhes da Proposta")
                
                # Seleção da proposta
                col1, col2 = st.columns([1, 2])
                with col1:
                    numeros_propostas = sorted(df_filtrado["numero"].astype(str).unique().tolist())
                    if numeros_propostas:
                        proposta_selecionada = st.selectbox("Selecione uma proposta:", numeros_propostas)
                    else:
                        st.warning("Nenhuma proposta disponível para seleção.")
                        proposta_selecionada = None
                
                with col2:
                    if proposta_selecionada and st.button("Ver Detalhes"):
                        # Encontrar a proposta selecionada
                        proposta = df_filtrado[df_filtrado["numero"].astype(str) == proposta_selecionada].iloc[0]
                        
                        # Mostrar card com detalhes
                        with st.expander("Detalhes da Proposta", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Número:** {proposta['numero']}")
                                st.markdown(f"**Cliente:** {proposta['cliente_nome']}")
                                st.markdown(f"**Descrição:** {proposta['descricao']}")
                                st.markdown(f"**Valor:** {proposta['valor_formatado']}")
                                st.markdown(f"**Tipo de Proposta:** {proposta['tipo_proposta']}")
                            
                            with col2:
                                st.markdown(f"**Status:** {proposta['status']}")
                                st.markdown(f"**Status Execução:** {proposta['status_execucao']}")
                                st.markdown(f"**Categoria:** {proposta['categoria_status']}")
                                st.markdown(f"**Data Início:** {proposta['data_inicio_formatada']}")
                                st.markdown(f"**Data Fim:** {proposta['data_fim_formatada']}")
                                st.markdown(f"**Data Criação:** {proposta['data_criacao']}")
                            
                            # Adicionar botões de ação (apenas informativo)
                            st.markdown("---")
                            st.subheader("Ações disponíveis para esta proposta:")
                            
                            if proposta['categoria_status'] == "Em execução":
                                st.info("⚠️ Para finalizar esta proposta, vá até a página 'Propostas > Em Execução'")
                            
                            if proposta['categoria_status'] == "Finalizadas":
                                st.info("🔄 Para reabrir esta proposta, vá até a página 'Propostas > Propostas Finalizadas'")
                                
                # Resumo visual
                if not df_filtrado.empty:
                    st.subheader("Resumo por Status")
                    status_contagem = df_filtrado['categoria_status'].value_counts().reset_index()
                    status_contagem.columns = ['Status', 'Quantidade']
                    
                    # Criar gráfico de barras
                    fig = go.Figure(data=[
                        go.Bar(
                            x=status_contagem['Status'],
                            y=status_contagem['Quantidade'],
                            marker_color=['#FFA07A', '#87CEFA', '#98FB98', '#FFB6C1'][:len(status_contagem)]
                        )
                    ])
                    
                    fig.update_layout(
                        title='Distribuição de Propostas por Status',
                        xaxis_title='Status',
                        yaxis_title='Quantidade',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                # Botão para voltar à página principal
                if st.button("Voltar para o Dashboard"):
                    st.switch_page("app.py")
                
    except Exception as e:
        st.error(f"Erro ao carregar as propostas: {str(e)}")
        st.error("Detalhes técnicos:")
        st.exception(e)

def processar_dados_propostas(df):
    """Processa o DataFrame de propostas para exibição adequada"""
    # Criar cópia para não modificar o original
    df_processado = df.copy()
    
    # Formatar datas
    df_processado['data_inicio_formatada'] = df_processado['data_inicio'].apply(
        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "-"
    )
    df_processado['data_fim_formatada'] = df_processado['data_fim'].apply(
        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "-"
    )
    
    # Formatar valores monetários
    df_processado['valor_formatado'] = df_processado['valor'].apply(
        lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "R$ 0,00"
    )
    
    # Criar categoria de status para facilitar filtragem
    def determinar_categoria(row):
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
    
    df_processado['categoria_status'] = df_processado.apply(determinar_categoria, axis=1)
    
    return df_processado

def aplicar_filtros(df, status_selecionado, cliente_selecionado, periodo_selecionado):
    """Aplica os filtros selecionados ao DataFrame"""
    df_filtrado = df.copy()
    
    # Filtro por status
    if status_selecionado != "Todas":
        df_filtrado = df_filtrado[df_filtrado['categoria_status'] == status_selecionado]
    
    # Filtro por cliente
    if cliente_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['cliente_nome'] == cliente_selecionado]
    
    # Filtro por período
    hoje = datetime.now()
    
    if periodo_selecionado == "Últimos 30 dias":
        # Filtrar propostas dos últimos 30 dias
        inicio_periodo = hoje - pd.Timedelta(days=30)
        df_filtrado = df_filtrado[df_filtrado['data_inicio'] >= inicio_periodo]
        
    elif periodo_selecionado == "Últimos 60 dias":
        # Filtrar propostas dos últimos 60 dias
        inicio_periodo = hoje - pd.Timedelta(days=60)
        df_filtrado = df_filtrado[df_filtrado['data_inicio'] >= inicio_periodo]
        
    elif periodo_selecionado == "Últimos 90 dias":
        # Filtrar propostas dos últimos 90 dias
        inicio_periodo = hoje - pd.Timedelta(days=90)
        df_filtrado = df_filtrado[df_filtrado['data_inicio'] >= inicio_periodo]
        
    elif periodo_selecionado == "Este ano":
        # Filtrar propostas do ano atual
        ano_atual = hoje.year
        df_filtrado = df_filtrado[df_filtrado['data_inicio'].dt.year == ano_atual]
    
    return df_filtrado

if __name__ == "__main__":
    main()