"""
Script para corrigir problemas de conexão com o banco de dados no Render
Este script deve ser executado uma vez quando o problema "column usuario_id does not exist"
estiver ocorrendo no Render, mesmo após confirmar que a coluna existe no banco.

O problema ocorre devido ao cache de metadados do SQLAlchemy.
"""
import os
import sys
import traceback
from datetime import datetime
import psycopg2
from sqlalchemy import create_engine, inspect, Column, String, Integer, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set!")
    sys.exit(1)

# Secure log - remove password from URL when printing
db_url_safe = DATABASE_URL.replace("://", "://***:***@")
print(f"Using database URL: {db_url_safe}")

try:
    # Connect directly using psycopg2 to verify
    print("\n=== Verificando conexão direta com psycopg2 ===")
    conn_parts = DATABASE_URL.replace("postgresql://", "").split("/")
    db_name = conn_parts[-1]
    conn_string = conn_parts[0].split("@")
    user_pass = conn_string[0].split(":")
    host_port = conn_string[1].split(":")
    
    username = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    
    print(f"Connecting to {host}:{port}/{db_name} as {username}")
    conn = psycopg2.connect(
        dbname=db_name,
        user=username,
        password=password,
        host=host,
        port=port
    )
    
    # Check table structure
    with conn.cursor() as cur:
        print("\n=== Verificando estrutura da tabela clientes ===")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'clientes'
            ORDER BY column_name;
        """)
        columns = cur.fetchall()
        
        has_usuario_id = False
        for col in columns:
            print(f"- {col[0]}: {col[1]}")
            if col[0] == 'usuario_id':
                has_usuario_id = True
        
        if has_usuario_id:
            print("\n✓ Coluna usuario_id encontrada na tabela clientes!")
        else:
            print("\n❌ ERRO: Coluna usuario_id NÃO encontrada na tabela clientes!")
            print("Criando coluna usuario_id na tabela clientes...")
            cur.execute("""
                ALTER TABLE clientes ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
            """)
            conn.commit()
            print("Coluna usuario_id adicionada à tabela clientes.")
            
        # Verificar se há registros na tabela clientes
        print("\n=== Verificando dados da tabela clientes ===")
        cur.execute("SELECT COUNT(*) FROM clientes;")
        count = cur.fetchone()[0]
        print(f"Total de registros na tabela clientes: {count}")
        
        if count > 0:
            # Verificar registros sem usuario_id
            cur.execute("SELECT COUNT(*) FROM clientes WHERE usuario_id IS NULL;")
            null_count = cur.fetchone()[0]
            print(f"Registros sem usuario_id: {null_count}")
            
            if null_count > 0:
                print("Atualizando registros sem usuario_id...")
                
                # Verificar usuários no sistema
                cur.execute("SELECT usuario_id FROM perfis LIMIT 1;")
                user_result = cur.fetchone()
                
                if user_result:
                    default_user_id = user_result[0]
                    print(f"Usando ID de usuário padrão: {default_user_id}")
                    
                    # Atualizar todos os registros sem usuario_id
                    cur.execute(f"""
                        UPDATE clientes 
                        SET usuario_id = '{default_user_id}' 
                        WHERE usuario_id IS NULL;
                    """)
                    conn.commit()
                    print(f"✓ {null_count} registros atualizados com o usuario_id: {default_user_id}")
                else:
                    print("❌ Nenhum perfil de usuário encontrado!")
    
    # Connect with SQLAlchemy
    print("\n=== Conectando com SQLAlchemy ===")
    
    # Use NullPool to avoid connection caching
    engine = create_engine(
        DATABASE_URL, 
        poolclass=NullPool,
        isolation_level='AUTOCOMMIT'
    )
    
    # Define basic model classes
    Base = declarative_base()
    
    class Cliente(Base):
        __tablename__ = 'clientes'
        id = Column(Integer, primary_key=True)
        nome = Column(String, nullable=False)
        telefone = Column(String)
        email = Column(String)
        usuario_id = Column(String)
        
    class Perfil(Base):
        __tablename__ = 'perfis'
        id = Column(Integer, primary_key=True)
        usuario_id = Column(String, unique=True, nullable=False)
        email = Column(String, unique=True, nullable=False)
        nome = Column(String, nullable=False)
        ultimo_login = Column(DateTime, nullable=True)
        ativo = Column(Boolean, default=True)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Force metadata refresh
        print("\n=== Forçando atualização de metadados ===")
        Base.metadata.clear()
        Base.metadata.reflect(bind=engine)
        
        # Check schema
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tabelas disponíveis: {tables}")
        
        # Try a select query with SQLAlchemy
        print("\n=== Testando consulta SQLAlchemy ===")
        result = session.query(Cliente).first()
        if result:
            print(f"Consulta bem-sucedida! Primeiro cliente: {result.nome}")
            print(f"ID do usuário: {result.usuario_id}")
        else:
            print("Nenhum cliente encontrado!")
        
    except Exception as e:
        print(f"ERRO SQLAlchemy: {str(e)}")
        traceback.print_exc()
    finally:
        session.close()
    
    print("\n=== Diagnóstico completo ===")
    print("Se tudo estiver OK, reinicie o servidor no Render.")
    print("Se ainda houver problemas, verifique os logs do Render para mais detalhes.")
    
except Exception as e:
    print(f"ERRO GERAL: {str(e)}")
    traceback.print_exc()