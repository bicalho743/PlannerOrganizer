"""
Script para corrigir problemas de esquema no banco de dados do Render
Contorna o SQLAlchemy e usa SQL direto para garantir que as colunas existam
"""
import os
import sys
import time
import traceback
import psycopg2

print("=== FIX RENDER DATABASE SCHEMA ===")
print(f"Iniciando em: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set!")
    sys.exit(1)

try:
    # Parse connection info
    print("\n=== Conectando ao banco de dados ===")
    conn_parts = DATABASE_URL.replace("postgresql://", "").split("/")
    db_name = conn_parts[-1]
    conn_string = conn_parts[0].split("@")
    user_pass = conn_string[0].split(":")
    host_port = conn_string[1].split(":")
    
    username = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    
    print(f"Conectando a {host}:{port}/{db_name} como {username}")
    
    # Connect to the database
    conn = psycopg2.connect(
        dbname=db_name,
        user=username,
        password=password,
        host=host,
        port=port
    )
    
    # Set autocommit
    conn.autocommit = True
    
    # Execute SQL script
    print("\n=== Executando correção de esquema ===")
    cursor = conn.cursor()
    
    # Step 1: Check if clientes table exists
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'clientes')")
    clientes_exists = cursor.fetchone()[0]
    
    if clientes_exists:
        print("✓ Tabela clientes encontrada")
        
        # Step 2: Check if usuario_id column exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'clientes' AND column_name = 'usuario_id')")
        usuario_id_exists = cursor.fetchone()[0]
        
        if usuario_id_exists:
            print("✓ Coluna usuario_id encontrada na tabela clientes")
        else:
            print("❌ Coluna usuario_id não encontrada na tabela clientes. Adicionando...")
            cursor.execute("ALTER TABLE clientes ADD COLUMN usuario_id VARCHAR")
            print("✓ Coluna usuario_id adicionada à tabela clientes")
        
        # Step 3: Update null usuario_id values
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE usuario_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"! Encontrados {null_count} registros com usuario_id NULL. Atualizando...")
            cursor.execute("UPDATE clientes SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL")
            print(f"✓ {null_count} registros atualizados com usuario_id padrão")
        else:
            print("✓ Todos os registros em clientes têm usuario_id")
        
        # Step 4: Create index
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cliente_usuario_id ON clientes(usuario_id)")
            print("✓ Índice criado/verificado para usuario_id em clientes")
        except psycopg2.errors.DuplicateTable:
            print("! Índice já existe para usuario_id em clientes")
    else:
        print("❌ ERRO CRÍTICO: Tabela clientes não encontrada!")
    
    # Step 5: Check perfil table
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'perfil')")
    perfil_exists = cursor.fetchone()[0]
    
    if perfil_exists:
        print("✓ Tabela perfil encontrada")
    else:
        print("❌ Tabela perfil não encontrada. Criando...")
        cursor.execute("""
            CREATE TABLE perfil (
                id SERIAL PRIMARY KEY,
                usuario_id VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                nome VARCHAR NOT NULL,
                telefone VARCHAR,
                empresa VARCHAR,
                instagram VARCHAR,
                website VARCHAR,
                cor_principal VARCHAR,
                cor_secundaria VARCHAR,
                role VARCHAR DEFAULT 'user',
                plano VARCHAR DEFAULT 'gratuito',
                data_cadastro DATE DEFAULT CURRENT_DATE,
                ultimo_login TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
        """)
        print("✓ Tabela perfil criada com sucesso")
    
    # Step 6: Check perfis table (plural name might also exist)
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'perfis')")
    perfis_exists = cursor.fetchone()[0]
    
    if perfis_exists:
        print("✓ Tabela perfis encontrada (versão plural)")
        
        # Check if usuario_id exists in perfis
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'perfis' AND column_name = 'usuario_id')")
        perfis_usuario_id_exists = cursor.fetchone()[0]
        
        if not perfis_usuario_id_exists:
            print("❌ Coluna usuario_id não encontrada na tabela perfis. Adicionando...")
            cursor.execute("ALTER TABLE perfis ADD COLUMN usuario_id VARCHAR")
            print("✓ Coluna usuario_id adicionada à tabela perfis")
    
    # Step 7: Analise todas as tabelas para atualizar estatísticas
    print("\n=== Analisando tabelas para atualizar estatísticas ===")
    cursor.execute("ANALYZE")
    print("✓ Análise concluída")
    
    # Step 8: Print final table structure
    print("\n=== Estrutura final da tabela clientes ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'clientes'
        ORDER BY column_name
    """)
    
    for column in cursor.fetchall():
        print(f"- {column[0]}: {column[1]}")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\n=== CORREÇÃO DE ESQUEMA CONCLUÍDA COM SUCESSO ===")
    print(f"Concluído em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
except Exception as e:
    print(f"\n❌ ERRO: {str(e)}")
    traceback.print_exc()
    sys.exit(1)