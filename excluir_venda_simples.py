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

# Estilo básico
st.markdown("""
<style>
.big-button {
    background-color: #FF0000 !important;
    color: white !important;
    font-size: 24px !important;
    font-weight: bold !important;
    padding: 20px !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

def get_database_connection():
    """Conecta diretamente ao banco de dados usando psycopg2"""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

def get_all_vendas():
    """Obtém todas as vendas do banco de dados"""
    conn = get_database_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT v.id, v.data_venda, v.valor_total, c.nome as cliente_nome
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.id DESC
        """
        
        vendas_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not vendas_df.empty:
            vendas_df['data_venda'] = pd.to_datetime(vendas_df['data_venda']).dt.strftime('%d/%m/%Y')
            vendas_df['valor_total'] = vendas_df['valor_total'].apply(lambda x: f"R$ {x:.2f}")
        
        return vendas_df
    except Exception as e:
        st.error(f"Erro ao buscar vendas: {str(e)}")
        if conn:
            conn.close()
        return pd.DataFrame()

def execute_sql_direto(venda_id):
    """Executa SQL direto para excluir a venda"""
    conn = get_database_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    log_messages = []
    
    try:
        log_messages.append("Iniciando exclusão...")
        
        # 1. Excluir transações financeiras relacionadas
        cursor.execute("DELETE FROM financeiro WHERE origem_id = %s AND origem_tipo = 'venda';", (venda_id,))
        rows_affected = cursor.rowcount
        log_messages.append(f"1. {rows_affected} transações financeiras excluídas")
        
        # 2. Excluir itens da venda
        cursor.execute("DELETE FROM itens_venda WHERE venda_id = %s;", (venda_id,))
        rows_affected = cursor.rowcount
        log_messages.append(f"2. {rows_affected} itens de venda excluídos")
        
        # 3. Remover referência à proposta
        cursor.execute("UPDATE vendas SET proposta_id = NULL WHERE id = %s;", (venda_id,))
        rows_affected = cursor.rowcount
        log_messages.append(f"3. Referência à proposta removida ({rows_affected} linhas)")
        
        # 4. Finalmente excluir a venda
        cursor.execute("DELETE FROM vendas WHERE id = %s;", (venda_id,))
        rows_affected = cursor.rowcount
        log_messages.append(f"4. Venda excluída ({rows_affected} linhas)")
        
        # Commit da transação
        conn.commit()
        log_messages.append("✅ Transação concluída com sucesso!")
        return True, log_messages
    except Exception as e:
        # Rollback em caso de erro
        conn.rollback()
        log_messages.append(f"❌ Erro: {str(e)}")
        return False, log_messages
    finally:
        cursor.close()
        conn.close()

# Interface principal
st.title("⚡ Exclusão Ultra Rápida de Vendas")
st.write("### Selecione uma venda e clique no botão vermelho para excluir imediatamente")

vendas_df = get_all_vendas()
if vendas_df.empty:
    st.warning("Nenhuma venda encontrada no banco de dados.")
else:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(vendas_df, hide_index=True, use_container_width=True)
    
    with col2:
        venda_id = st.selectbox(
            "Escolha a venda para excluir:",
            options=vendas_df['id'].tolist(),
            format_func=lambda x: f"#{x} - {vendas_df[vendas_df['id'] == x]['cliente_nome'].iloc[0]}"
        )
        
        # Container para botão grande centralizado
        st.write("")
        st.write("")
        
        if st.button("🗑️ EXCLUIR VENDA", key="btn_excluir_direto", use_container_width=True):
            with st.spinner("Processando exclusão..."):
                success, logs = execute_sql_direto(venda_id)
                
                if success:
                    st.success(f"Venda #{venda_id} excluída com sucesso!")
                    
                    # Log de detalhes para debug
                    with st.expander("Detalhes da operação"):
                        for log in logs:
                            st.write(log)
                            
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Falha ao excluir a venda.")
                    with st.expander("Detalhes do erro", expanded=True):
                        for log in logs:
                            st.write(log)