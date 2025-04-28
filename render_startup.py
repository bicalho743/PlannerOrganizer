"""
Script de inicialização para o Render que força limpeza de cache do SQLAlchemy
"""
import os
import sys
import time
import subprocess
import psycopg2

print("=== RENDER STARTUP SCRIPT ===")
print(f"Iniciando em: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Verificar e corrigir o esquema do banco antes de iniciar
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        print("Verificando banco de dados...")
        # Conectar diretamente ao banco
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar e adicionar coluna usuario_id em clientes
        cursor.execute("""
            DO $$
            BEGIN
                BEGIN
                    ALTER TABLE clientes ADD COLUMN usuario_id VARCHAR;
                    RAISE NOTICE 'Coluna usuario_id adicionada à tabela clientes';
                EXCEPTION
                    WHEN duplicate_column THEN
                        RAISE NOTICE 'Coluna usuario_id já existe na tabela clientes';
                END;
            END $$;
        """)
        
        # Atualizar valores nulos
        cursor.execute("""
            UPDATE clientes SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' 
            WHERE usuario_id IS NULL;
        """)
        
        # Criar índice
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_clientes_usuario_id ON clientes (usuario_id);
        """)
        
        # Forçar análise de tabelas
        cursor.execute("ANALYZE clientes;")
        
        # Verificar estrutura final
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'clientes'
            ORDER BY column_name;
        """)
        
        colunas = cursor.fetchall()
        print(f"Colunas da tabela clientes: {[col[0] for col in colunas]}")
        
        # Verificar se usuario_id está presente
        tem_usuario_id = any(col[0] == 'usuario_id' for col in colunas)
        if tem_usuario_id:
            print("✓ Coluna usuario_id confirmada na tabela clientes")
        else:
            print("❌ ALERTA: Coluna usuario_id não encontrada após correção!")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        print("Verificação do banco concluída com sucesso!")
        
    except Exception as e:
        print(f"ERRO ao verificar banco: {str(e)}")
else:
    print("Aviso: DATABASE_URL não encontrada no ambiente")

# Executar o comando Streamlit
try:
    cmd = 'streamlit run app.py --server.port 10000 --server.address 0.0.0.0'
    print(f"Executando: {cmd}")
    os.system(cmd)
except Exception as e:
    print(f"ERRO: {e}")
    sys.exit(1)