import streamlit as st
import pandas as pd
import os
import psycopg2
import time

# Configuração da página
st.set_page_config(
    page_title="Excluir Vendas - Modo Direto",
    page_icon="🗑️",
    layout="wide"
)

# Estilo e cores personalizadas
st.markdown("""
<style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton button {
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        font-size: 18px;
        padding: 15px;
    }
    .stSelectbox [data-testid="stSelectbox"] {
        font-size: 18px;
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
        # Consulta para obter vendas com nomes de clientes
        query = """
        SELECT v.id, v.data_venda, v.valor_total, v.status, v.forma_pagamento,
               c.nome as cliente_nome, v.proposta_id, v.observacoes
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.id DESC
        """
        
        vendas_df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Formatar valores
        if not vendas_df.empty:
            vendas_df['data_venda'] = pd.to_datetime(vendas_df['data_venda']).dt.strftime('%d/%m/%Y')
            vendas_df['valor_total'] = vendas_df['valor_total'].apply(lambda x: f"R$ {x:.2f}")
        
        return vendas_df
    except Exception as e:
        st.error(f"Erro ao buscar vendas: {str(e)}")
        if conn:
            conn.close()
        return pd.DataFrame()

def excluir_venda_sql_direto(venda_id):
    """
    Exclui uma venda usando SQL direto com psycopg2
    """
    conn = get_database_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    success = False
    
    try:
        # Iniciar transação
        cursor.execute("BEGIN;")
        
        # 1. Excluir transações financeiras relacionadas
        cursor.execute(
            "DELETE FROM financeiro WHERE origem_id = %s AND origem_tipo = 'venda';",
            (venda_id,)
        )
        
        # 2. Excluir itens da venda
        cursor.execute(
            "DELETE FROM itens_venda WHERE venda_id = %s;",
            (venda_id,)
        )
        
        # 3. Remover referência à proposta
        cursor.execute(
            "UPDATE vendas SET proposta_id = NULL WHERE id = %s;",
            (venda_id,)
        )
        
        # 4. Finalmente excluir a venda
        cursor.execute(
            "DELETE FROM vendas WHERE id = %s;",
            (venda_id,)
        )
        
        # Commit da transação
        conn.commit()
        success = True
    except Exception as e:
        # Rollback em caso de erro
        conn.rollback()
        st.error(f"Erro ao excluir venda: {str(e)}")
        st.code(str(e))
    finally:
        cursor.close()
        conn.close()
    
    return success

def main():
    st.title("🗑️ EXCLUSÃO DIRETA DE VENDAS")
    st.markdown("### Ferramenta simplificada para excluir vendas")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Carregar vendas
        vendas_df = get_all_vendas()
        
        if vendas_df.empty:
            st.info("Nenhuma venda encontrada no sistema.")
            return
        
        # Mostrar tabela de vendas para referência
        st.subheader("Vendas disponíveis")
        st.dataframe(vendas_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("Exclusão Rápida")
        
        # Selecionar venda para excluir
        venda_excluir_id = st.selectbox(
            "Selecione a venda a excluir",
            options=vendas_df['id'].tolist(),
            format_func=lambda x: f"Venda #{x} - {vendas_df[vendas_df['id'] == x]['cliente_nome'].iloc[0]}",
            key="select_venda_excluir_direto"
        )
        
        # Detalhes básicos
        if venda_excluir_id:
            venda_excluir = vendas_df[vendas_df['id'] == venda_excluir_id].iloc[0]
            st.write(f"**Venda #{venda_excluir_id}**")
            st.write(f"👤 **Cliente:** {venda_excluir['cliente_nome']}")
            st.write(f"📅 **Data:** {venda_excluir['data_venda']}")
            st.write(f"💰 **Valor:** {venda_excluir['valor_total']}")
            
            # Botão de exclusão direta
            if st.button("🗑️ EXCLUIR ESTA VENDA", use_container_width=True):
                with st.spinner("Excluindo venda..."):
                    if excluir_venda_sql_direto(venda_excluir_id):
                        st.success(f"✅ Venda #{venda_excluir_id} excluída com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Falha ao excluir a venda.")

if __name__ == "__main__":
    main()