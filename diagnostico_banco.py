"""
Script de diagnóstico para problemas de banco de dados no Render.
Este script verifica a conectividade com o banco, estrutura das tabelas
e tenta acessar os dados usando o SQLAlchemy de maneira similar ao app.
"""
import os
import sys
import time
import traceback
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, inspect

# Print informação sobre o ambiente de execução
print("=== DIAGNÓSTICO DE BANCO DE DADOS ===")
print(f"Python: {sys.version}")
print(f"SQLAlchemy: {sqlalchemy.__version__}")

# Obter a URL do banco de dados do ambiente
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("ERRO: Variável DATABASE_URL não encontrada no ambiente!")
    sys.exit(1)

# Reportar informação básica (sem mostrar senha)
db_url_safe = database_url.replace("://", "://***:***@")
print(f"URL do banco: {db_url_safe}")

try:
    # Criar conexão com o banco de dados
    print("\nTentando conectar ao banco de dados...")
    engine = create_engine(database_url)
    
    # Verificar conexão
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        print(f"Conectado ao banco: {db_info[0]} como usuário: {db_info[1]}")
        
        # Verificar a tabela clientes
        print("\nVerificando metadados da tabela clientes...")
        meta = MetaData()
        meta.reflect(bind=engine, only=['clientes'])
        
        if 'clientes' in meta.tables:
            clientes = meta.tables['clientes']
            print("Colunas na tabela clientes:")
            for col in clientes.columns:
                print(f"- {col.name}: {col.type}")
                
            # Verificar especificamente a coluna usuario_id
            if 'usuario_id' in clientes.columns:
                print("\nColuna usuario_id encontrada na tabela clientes.")
                
                # Tentar fazer uma consulta similar ao app
                try:
                    print("\nTentando consulta similar ao app...")
                    query = text("SELECT * FROM clientes WHERE usuario_id = :uid LIMIT 1")
                    result = conn.execute(query, {"uid": "7NDbX2b7hAcFqWzwsgi2BXiFZad2"})
                    row = result.fetchone()
                    if row:
                        print(f"Consulta bem sucedida! Encontrado cliente: {row.nome}")
                    else:
                        print("Nenhum cliente encontrado com este ID de usuário.")
                        
                    # Verificar permissões
                    print("\nVerificando permissões da tabela...")
                    perms_query = text("""
                        SELECT grantee, privilege_type 
                        FROM information_schema.role_table_grants 
                        WHERE table_name = 'clientes'
                    """)
                    perms = conn.execute(perms_query).fetchall()
                    for perm in perms:
                        print(f"- {perm.grantee}: {perm.privilege_type}")
                        
                except Exception as e:
                    print(f"ERRO ao consultar dados: {str(e)}")
                    traceback.print_exc()
            else:
                print("ERRO: Coluna usuario_id NÃO encontrada na tabela clientes!")
        else:
            print("ERRO: Tabela clientes não encontrada no banco de dados!")
        
        # Ver se há problemas de cache do SQLAlchemy
        print("\nTestando problema de cache do SQLAlchemy...")
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('clientes')]
        print(f"Colunas na tabela clientes (via inspect): {columns}")
        if 'usuario_id' in columns:
            print("Coluna usuario_id encontrada via inspect!")
        else:
            print("ERRO: Coluna usuario_id NÃO encontrada via inspect!")
            
except Exception as e:
    print(f"\nERRO GERAL: {str(e)}")
    traceback.print_exc()

print("\n=== FIM DO DIAGNÓSTICO ===")