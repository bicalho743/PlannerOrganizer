import streamlit as st
import pandas as pd
import os
import psycopg2
import time

# Configuração da página
st.set_page_config(
    page_title="Exclusão Ultra Simples",
    page_icon="⚡",
    layout="wide"
)

# Mensagens iniciais
st.title("🔴 Exclusão Direta de Vendas")
st.warning("Use esta ferramenta apenas para excluir vendas que não podem ser excluídas pelo método normal")

# Conectar ao banco de dados diretamente com psycopg2
def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Obter todas as vendas
def get_all_vendas():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Consulta SQL simples para obter vendas com nome do cliente
        query = """
        SELECT v.id, c.nome as cliente_nome, v.data_venda, v.valor_total, v.status 
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.id DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        # Formatar valores para exibição
        if not df.empty:
            df['data_venda'] = pd.to_datetime(df['data_venda']).dt.strftime('%d/%m/%Y')
            df['valor_total'] = df['valor_total'].apply(lambda x: f"R$ {x:.2f}")
        
        return df
    except Exception as e:
        st.error(f"Erro ao buscar vendas: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# Função para excluir uma venda diretamente com SQL
def excluir_venda_sql_direto(venda_id):
    conn = get_db_connection()
    if not conn:
        return False, ["Falha na conexão com o banco de dados"]
    
    cursor = conn.cursor()
    logs = []
    
    try:
        # Iniciar transação para garantir exclusão atômica
        logs.append("Iniciando transação...")
        
        # 1. Excluir registros financeiros relacionados
        cursor.execute("""
            DELETE FROM financeiro 
            WHERE origem_id = %s AND origem_tipo = 'venda'
        """, (venda_id,))
        logs.append(f"1. Registros financeiros excluídos: {cursor.rowcount}")
        
        # 2. Excluir itens da venda
        cursor.execute("""
            DELETE FROM itens_venda 
            WHERE venda_id = %s
        """, (venda_id,))
        logs.append(f"2. Itens de venda excluídos: {cursor.rowcount}")
        
        # 3. Remover referência à proposta
        cursor.execute("""
            UPDATE vendas 
            SET proposta_id = NULL 
            WHERE id = %s
        """, (venda_id,))
        logs.append(f"3. Referência à proposta removida")
        
        # 4. Finalmente excluir a venda
        cursor.execute("""
            DELETE FROM vendas 
            WHERE id = %s
        """, (venda_id,))
        logs.append(f"4. Venda excluída: {cursor.rowcount}")
        
        # Commit da transação
        conn.commit()
        logs.append("✅ Transação concluída com sucesso!")
        
        return True, logs
    except Exception as e:
        # Rollback em caso de erro
        conn.rollback()
        logs.append(f"❌ ERRO: {str(e)}")
        return False, logs
    finally:
        cursor.close()
        conn.close()

# Interface principal
vendas_df = get_all_vendas()

if vendas_df.empty:
    st.info("Não foram encontradas vendas no banco de dados.")
else:
    # Layout em duas colunas
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Lista de Vendas")
        st.dataframe(vendas_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Ferramenta de Exclusão")
        
        # Seleção de venda para excluir
        venda_id = st.selectbox(
            "Selecione a venda para excluir:",
            options=vendas_df["id"].tolist(),
            format_func=lambda x: f"#{x} - {vendas_df[vendas_df['id'] == x]['cliente_nome'].iloc[0]}"
        )
        
        # Exibição dos detalhes da venda selecionada
        if venda_id:
            venda = vendas_df[vendas_df["id"] == venda_id].iloc[0]
            st.write(f"**Venda #{venda_id}**")
            st.write(f"**Cliente:** {venda['cliente_nome']}")
            st.write(f"**Data:** {venda['data_venda']}")
            st.write(f"**Valor:** {venda['valor_total']}")
            st.write(f"**Status:** {venda['status']}")
        
        # Botão de exclusão
        if st.button("🗑️ EXCLUIR ESTA VENDA", type="primary", use_container_width=True):
            with st.spinner("Excluindo venda..."):
                success, logs = excluir_venda_sql_direto(venda_id)
                
                if success:
                    st.success(f"✅ Venda #{venda_id} excluída com sucesso!")
                    
                    # Exibir logs para diagnóstico
                    with st.expander("Detalhes da operação"):
                        for log in logs:
                            st.write(log)
                    
                    # Recarregar a página após 2 segundos
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Falha ao excluir a venda!")
                    
                    # Exibir logs para diagnóstico
                    with st.expander("Detalhes do erro", expanded=True):
                        for log in logs:
                            st.write(log)