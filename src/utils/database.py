import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import sqlalchemy as sa

class Database:
    def __init__(self):
        self.DATABASE_URL = os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.DATABASE_URL)
        self.initialize_tables()

    def initialize_tables(self):
        # Criar tabelas se não existirem
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    telefone VARCHAR(50),
                    endereco TEXT,
                    cpf VARCHAR(14),
                    data_aniversario DATE,
                    origem_cliente VARCHAR(50),
                    tipo_conta VARCHAR(2),
                    cnpj VARCHAR(18),
                    razao_social VARCHAR(255),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS propostas (
                    id SERIAL PRIMARY KEY,
                    numero INTEGER NOT NULL,
                    cliente_id INTEGER REFERENCES clientes(id),
                    descricao TEXT,
                    valor DECIMAL(10,2),
                    status VARCHAR(50),
                    tipo_proposta VARCHAR(50),
                    data_inicio DATE,
                    data_fim DATE,
                    prazo_entrega DATE,
                    data_proposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS financeiro (
                    id SERIAL PRIMARY KEY,
                    tipo VARCHAR(50),
                    descricao TEXT,
                    valor DECIMAL(10,2),
                    categoria VARCHAR(50),
                    tipo_receita VARCHAR(50),
                    origem_id INTEGER,
                    origem_tipo VARCHAR(50),
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()

    def get_clientes(self):
        try:
            return pd.read_sql('SELECT * FROM clientes', self.engine)
        except:
            return pd.DataFrame()

    def get_propostas(self):
        try:
            return pd.read_sql('SELECT * FROM propostas', self.engine)
        except:
            return pd.DataFrame()

    def get_financeiro(self):
        try:
            return pd.read_sql('SELECT * FROM financeiro', self.engine)
        except:
            return pd.DataFrame()

    def add_test_data(self):
        try:
            # Adicionar cliente de teste
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO clientes (nome, email, telefone, tipo_conta)
                    VALUES ('Cliente Teste', 'teste@email.com', '(11) 99999-9999', 'PF')
                """))
                conn.commit()
            return True
        except:
            return False

    def get_pagamentos_pendentes(self):
        try:
            query = """
                SELECT p.numero as proposta, c.nome as cliente, 
                       'Valor Base' as tipo, p.valor as valor
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.status = 'Aberta'
            """
            return pd.read_sql(query, self.engine)
        except:
            return pd.DataFrame()
