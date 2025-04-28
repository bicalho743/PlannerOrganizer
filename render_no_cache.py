"""
Script de inicialização especial para o Render com desativação de cache do SQLAlchemy
Executa o render_startup.py e depois força o flush do cache do SQLAlchemy
"""

import os
import sys
import importlib.util
import time

# Carregar render_startup.py se existir
try:
    print("Verificando render_startup.py...")
    
    # Carregar o módulo render_startup dinamicamente
    spec = importlib.util.spec_from_file_location("render_startup", "render_startup.py")
    if spec:
        startup_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(startup_module)
        print("Módulo render_startup executado com sucesso.")
    else:
        print("Arquivo render_startup.py não encontrado, pulando.")
except Exception as e:
    print(f"Erro ao carregar render_startup.py: {e}")

# Aplicar correção de cache do SQLAlchemy
try:
    print("\nAplicando correção de cache do SQLAlchemy...")
    
    # Verificar se o módulo correcao_banco.py existe
    if os.path.exists("correcao_banco.py"):
        print("Executando correcao_banco.py...")
        
        # Carregar o módulo correcao_banco dinamicamente
        spec = importlib.util.spec_from_file_location("correcao_banco", "correcao_banco.py")
        if spec:
            correcao_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(correcao_module)
            print("Módulo correcao_banco executado com sucesso.")
        else:
            print("Erro ao carregar correcao_banco.py.")
    else:
        print("Arquivo correcao_banco.py não encontrado, aplicando correção básica...")
        
        # Aplicar correção básica sem o arquivo
        try:
            import psycopg2
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.pool import NullPool
            
            # Obter a URL do banco de dados
            DATABASE_URL = os.environ.get('DATABASE_URL')
            if not DATABASE_URL:
                print("ERRO: Variável DATABASE_URL não definida!")
            else:
                # Criar engine sem cache
                engine = create_engine(
                    DATABASE_URL, 
                    poolclass=NullPool,
                    isolation_level='AUTOCOMMIT'
                )
                
                # Verificar conexão
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                print(f"Conexão estabelecida. Tabelas disponíveis: {tables}")
                
                # Verificar coluna usuario_id
                if 'clientes' in tables:
                    columns = [c['name'] for c in inspector.get_columns('clientes')]
                    if 'usuario_id' in columns:
                        print("✓ Coluna usuario_id encontrada em clientes!")
                    else:
                        print("❌ Coluna usuario_id NÃO encontrada em clientes!")
                        
                        # Tentar adicionar a coluna
                        try:
                            with engine.connect() as conn:
                                conn.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;")
                                print("Coluna usuario_id adicionada com sucesso!")
                        except Exception as e:
                            print(f"Erro ao adicionar coluna: {e}")
        except Exception as e:
            print(f"Erro na correção básica: {e}")
except Exception as e:
    print(f"Erro ao aplicar correção de cache: {e}")

# Criar arquivo de pronto para o Render
try:
    with open("render_ready.txt", "w") as f:
        f.write(f"Aplicação pronta para iniciar em {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nArquivo render_ready.txt criado com sucesso.")
except Exception as e:
    print(f"Erro ao criar arquivo render_ready.txt: {e}")

print("\nIniciando aplicação...")