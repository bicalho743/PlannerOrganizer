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

    def get_cliente(self, cliente_id):
        """Get a specific client by ID"""
        return self.session.query(Cliente).filter(Cliente.id == cliente_id).first()

    def update_cliente(self, cliente_id, **kwargs):
        """Update client information"""
        def update():
            cliente = self.get_cliente(cliente_id)
            if cliente:
                for key, value in kwargs.items():
                    if hasattr(cliente, key):
                        setattr(cliente, key, value)
            return cliente
        return self._safe_query(update)

    def delete_cliente(self, cliente_id):
        """Soft delete a client by setting ativo=False"""
        return self.update_cliente(cliente_id, ativo=False)

    def __del__(self):
        """Cleanup database connection"""
        self.Session.remove()