"""
Script para atualizar o banco de dados no Render para incluir colunas usuario_id
em todas as tabelas necessárias para isolamento multi-tenant.
"""
import os
import psycopg2
import streamlit as st

# SQL para adicionar a coluna usuario_id às tabelas principais
SQL_COMMANDS = [
    # Tabela clientes
    """
    ALTER TABLE clientes 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela produtos
    """
    ALTER TABLE produtos 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela propostas
    """
    ALTER TABLE propostas 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela financeiro
    """
    ALTER TABLE financeiro 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela vendas
    """
    ALTER TABLE vendas 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela perfil (verifica se já existe)
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'perfil'
        ) THEN
            CREATE TABLE perfil (
                id SERIAL PRIMARY KEY,
                usuario_id VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                nome VARCHAR(255) NOT NULL,
                telefone VARCHAR(50),
                empresa VARCHAR(255),
                instagram VARCHAR(255),
                website VARCHAR(255),
                cor_principal VARCHAR(50),
                cor_secundaria VARCHAR(50),
                role VARCHAR(50) DEFAULT 'user',
                plano VARCHAR(50) DEFAULT 'gratuito',
                data_cadastro DATE,
                ultimo_login TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            );
        END IF;
    END
    $$;
    """,
    
    # Tabela itens_proposta
    """
    ALTER TABLE itens_proposta 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela itens_venda
    """
    ALTER TABLE itens_venda 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """,
    
    # Tabela acrescimos_proposta
    """
    ALTER TABLE acrescimos_proposta 
    ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);
    """
]

def conectar_banco():
    """Conecta ao banco de dados usando a URL de conexão do ambiente"""
    try:
        # Usar a variável de ambiente DATABASE_URL para conexão
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            st.error("Variável de ambiente DATABASE_URL não encontrada!")
            return None
            
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

def executar_sql(conn, sql):
    """Executa um comando SQL e retorna o status"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        return True, "Comando executado com sucesso"
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao executar SQL: {str(e)}"

def atualizar_banco():
    """Função principal para atualizar o banco de dados"""
    st.title("Atualização do Banco de Dados no Render")
    
    st.write("""
    Este script irá atualizar o banco de dados no Render para adicionar as colunas 
    necessárias para o isolamento multi-tenant (coluna usuario_id em todas as tabelas).
    """)
    
    st.warning("""
    ⚠️ **ATENÇÃO**: Este script modifica a estrutura do banco de dados. 
    Certifique-se de que você tem um backup antes de prosseguir.
    """)
    
    # Botão para confirmar a execução
    if st.button("Executar Atualização do Banco de Dados"):
        conn = conectar_banco()
        
        if conn:
            with st.spinner("Atualizando o banco de dados..."):
                # Container para mostrar o progresso
                progress_container = st.container()
                
                for i, sql in enumerate(SQL_COMMANDS, 1):
                    progress_text = f"Executando comando {i}/{len(SQL_COMMANDS)}"
                    progress_container.text(progress_text)
                    
                    success, message = executar_sql(conn, sql)
                    if success:
                        progress_container.success(f"✓ {progress_text}")
                    else:
                        progress_container.error(f"✗ {progress_text}: {message}")
                        st.stop()
                
                # Verificar se todas as tabelas têm a coluna usuario_id
                check_sql = """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE column_name = 'usuario_id'
                ORDER BY table_name;
                """
                
                cursor = conn.cursor()
                cursor.execute(check_sql)
                columns = cursor.fetchall()
                cursor.close()
                
                st.success("✅ Atualização do banco de dados concluída com sucesso!")
                
                st.write("### Tabelas atualizadas com a coluna usuario_id:")
                for table, column in columns:
                    st.write(f"✓ {table}.{column}")
                
                conn.close()
        else:
            st.error("Não foi possível conectar ao banco de dados.")

if __name__ == "__main__":
    atualizar_banco()