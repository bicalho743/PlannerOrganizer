import streamlit as st
import pandas as pd
import os
import psycopg2
from psycopg2 import sql
import time
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Limpar Vendas",
    page_icon="🧹",
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
    }
    .warning-text {
        color: #ff4b4b;
        font-weight: bold;
    }
    .success-text {
        color: #00cc66;
        font-weight: bold;
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
        st.info("Excluindo transações financeiras relacionadas...")
        cursor.execute(
            "DELETE FROM financeiro WHERE origem_id = %s AND origem_tipo = 'venda';",
            (venda_id,)
        )
        
        # 2. Excluir itens da venda
        st.info("Excluindo itens da venda...")
        cursor.execute(
            "DELETE FROM itens_venda WHERE venda_id = %s;",
            (venda_id,)
        )
        
        # 3. Remover referência à proposta
        st.info("Removendo referência à proposta...")
        cursor.execute(
            "UPDATE vendas SET proposta_id = NULL WHERE id = %s;",
            (venda_id,)
        )
        
        # 4. Finalmente excluir a venda
        st.info("Excluindo venda...")
        cursor.execute(
            "DELETE FROM vendas WHERE id = %s;",
            (venda_id,)
        )
        
        # Commit da transação
        conn.commit()
        success = True
        st.success(f"Venda #{venda_id} excluída com sucesso!")
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
    st.title("🧹 Limpar Vendas")
    st.markdown("### Ferramenta de exclusão direta de vendas")
    st.warning("⚠️ Esta ferramenta exclui permanentemente vendas do sistema usando SQL direto!")
    
    # Carregar vendas
    vendas_df = get_all_vendas()
    
    if vendas_df.empty:
        st.info("Nenhuma venda encontrada no sistema.")
        return
    
    # Mostrar tabela de vendas para seleção
    st.subheader("Vendas disponíveis")
    st.dataframe(vendas_df, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # Seção para excluir venda
    st.subheader("Excluir Venda")
    
    # Selecionar venda para excluir
    venda_excluir_id = st.selectbox(
        "Selecione a venda para excluir",
        options=vendas_df['id'].tolist(),
        format_func=lambda x: f"Venda #{x} - {vendas_df[vendas_df['id'] == x]['cliente_nome'].iloc[0]} - {vendas_df[vendas_df['id'] == x]['valor_total'].iloc[0]}",
        key="select_venda_excluir_direto"
    )
    
    # Detalhes da venda a ser excluída
    if venda_excluir_id:
        venda_excluir = vendas_df[vendas_df['id'] == venda_excluir_id].iloc[0]
        st.info(f"""
        **Detalhes da venda a excluir:**
        - ID: {venda_excluir_id}
        - Cliente: {venda_excluir['cliente_nome']}
        - Data: {venda_excluir['data_venda']}
        - Valor: {venda_excluir['valor_total']}
        - Status: {venda_excluir['status']}
        """)
    
    # Formulário de confirmação
    with st.form(key="form_excluir_venda_direto"):
        st.markdown('<p class="warning-text">⚠️ ATENÇÃO! Esta ação irá EXCLUIR PERMANENTEMENTE a venda selecionada e todos seus itens do sistema.</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="warning-text">Você está excluindo a venda #{venda_excluir_id} de {vendas_df[vendas_df["id"] == venda_excluir_id]["cliente_nome"].iloc[0]}</p>', unsafe_allow_html=True)
        
        # Campo de texto para confirmação
        st.error("Digite 'EXCLUIR' abaixo para confirmar a exclusão permanente")
        confirmacao_texto = st.text_input("Confirmação")
        confirmar_exclusao = st.form_submit_button("EXCLUIR VENDA PERMANENTEMENTE", use_container_width=True)
        
        if confirmar_exclusao:
            if confirmacao_texto != "EXCLUIR":
                st.error("Confirmação incorreta. Digite 'EXCLUIR' em maiúsculas exatamente como mostrado.")
            else:
                # Excluir venda usando SQL direto
                if excluir_venda_sql_direto(venda_excluir_id):
                    time.sleep(2)
                    st.markdown('<p class="success-text">✅ Venda excluída com sucesso! Atualizando página...</p>', unsafe_allow_html=True)
                    time.sleep(1)
                    st.rerun()

if __name__ == "__main__":
    main()