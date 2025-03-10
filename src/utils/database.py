import os
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create base class for declarative models
Base = declarative_base()

# Define database models
class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    telefone = Column(String)
    email = Column(String)
    cpf = Column(String)
    estado = Column(String)
    cidade = Column(String)
    bairro = Column(String)
    endereco = Column(String)
    data_aniversario = Column(String)  # Format: DD/MMM
    origem_cliente = Column(String)
    observacoes = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date)
    ativo = Column(Boolean, default=True)

class Proposta(Base):
    __tablename__ = 'propostas'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    descricao = Column(String)
    valor = Column(Float)
    status = Column(String)  # Aberta, Fechada, Recusada
    tipo_proposta = Column(String)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    prazo_entrega = Column(Date)
    cliente = relationship("Cliente")

class Financeiro(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True)
    tipo = Column(String)  # receita, despesa
    valor = Column(Float)
    status = Column(String)  # pendente, pago, cancelado
    data_vencimento = Column(Date)
    data_pagamento = Column(Date)

class Database:
    def __init__(self):
        """Initialize database connection and create tables"""
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)

        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        self.session = self.Session()

    def _safe_query(self, query_func):
        """Execute a query safely with proper session handling"""
        try:
            result = query_func()
            self.session.commit()
            return result
        except Exception as e:
            self.session.rollback()
            raise e

    def add_cliente(self, nome, telefone=None, email=None, cpf=None,
                   estado=None, cidade=None, bairro=None, endereco=None,
                   data_aniversario=None, origem_cliente=None, observacoes=None):
        """Add a new client to the database"""
        cliente = Cliente(
            nome=nome,
            telefone=telefone,
            email=email,
            cpf=cpf,
            estado=estado,
            cidade=cidade,
            bairro=bairro,
            endereco=endereco,
            data_aniversario=data_aniversario,
            origem_cliente=origem_cliente,
            observacoes=observacoes
        )
        return self._safe_query(lambda: self.session.add(cliente))

    def get_clientes(self, ativo=True):
        """Get all active clients"""
        query = self.session.query(Cliente).filter(Cliente.ativo == ativo)
        return pd.read_sql(query.statement, self.engine)

    def get_propostas(self):
        """Get all proposals with client information"""
        query = self.session.query(
            Proposta, Cliente.nome.label('cliente_nome')
        ).join(Cliente)
        df = pd.read_sql(query.statement, self.engine)
        return df if not df.empty else pd.DataFrame()

    def get_financeiro(self):
        """Get all financial records"""
        query = self.session.query(Financeiro)
        return pd.read_sql(query.statement, self.engine)

    def add_test_data(self):
        """Add test data to the database"""
        try:
            # Add test client
            cliente = Cliente(
                nome="Cliente Teste",
                telefone="(11) 99999-9999",
                email="teste@email.com",
                data_aniversario=datetime.now().strftime('%d/%b'),
                origem_cliente="Teste"
            )
            self.session.add(cliente)
            self.session.flush()

            # Add test proposal
            proposta = Proposta(
                cliente_id=cliente.id,
                descricao="Proposta de teste",
                valor=1000.0,
                status="Aberta",
                tipo_proposta="Organização",
                data_inicio=datetime.now().date()
            )
            self.session.add(proposta)

            # Add test financial record
            financeiro = Financeiro(
                tipo="receita",
                valor=1000.0,
                status="pendente",
                data_vencimento=datetime.now().date()
            )
            self.session.add(financeiro)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error adding test data: {str(e)}")
            return False

    def __del__(self):
        """Cleanup database connection"""
        self.Session.remove()