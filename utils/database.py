import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String)
    telefone = Column(String)
    endereco = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())

    propostas = relationship("Proposta", back_populates="cliente")

class Proposta(Base):
    __tablename__ = 'propostas'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    descricao = Column(String)
    valor = Column(Float)
    status = Column(String)
    data_proposta = Column(Date, default=datetime.now().date())

    cliente = relationship("Cliente", back_populates="propostas")

class Transacao(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True)
    tipo = Column(String)  # receita/despesa
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date, default=datetime.now().date())
    categoria = Column(String)
    referencia_id = Column(Integer)

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    descricao = Column(String)
    valor = Column(Float)
    quantidade = Column(Integer)
    data_cadastro = Column(Date, default=datetime.now().date())

# Create tables
Base.metadata.create_all(engine)

class Database:
    def __init__(self):
        self.session = Session()

    def get_clientes(self):
        clientes = self.session.query(Cliente).all()
        return pd.DataFrame([{
            'id': c.id,
            'nome': c.nome,
            'email': c.email,
            'telefone': c.telefone,
            'endereco': c.endereco,
            'data_cadastro': c.data_cadastro
        } for c in clientes])

    def add_cliente(self, nome, email, telefone, endereco):
        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco
        )
        self.session.add(cliente)
        self.session.commit()
        return cliente.id

    def get_propostas(self):
        propostas = self.session.query(Proposta).all()
        return pd.DataFrame([{
            'id': p.id,
            'cliente_id': p.cliente_id,
            'descricao': p.descricao,
            'valor': p.valor,
            'status': p.status,
            'data_proposta': p.data_proposta
        } for p in propostas])

    def add_proposta(self, cliente_id, descricao, valor, status):
        proposta = Proposta(
            cliente_id=cliente_id,
            descricao=descricao,
            valor=valor,
            status=status
        )
        self.session.add(proposta)
        self.session.commit()
        return proposta.id

    def get_financeiro(self):
        transacoes = self.session.query(Transacao).all()
        return pd.DataFrame([{
            'id': t.id,
            'tipo': t.tipo,
            'descricao': t.descricao,
            'valor': t.valor,
            'data': t.data,
            'categoria': t.categoria,
            'referencia_id': t.referencia_id
        } for t in transacoes])

    def add_transacao(self, tipo, descricao, valor, categoria, referencia_id=None):
        transacao = Transacao(
            tipo=tipo,
            descricao=descricao,
            valor=valor,
            categoria=categoria,
            referencia_id=referencia_id
        )
        self.session.add(transacao)
        self.session.commit()
        return transacao.id

    def get_produtos(self):
        produtos = self.session.query(Produto).all()
        return pd.DataFrame([{
            'id': p.id,
            'nome': p.nome,
            'descricao': p.descricao,
            'valor': p.valor,
            'quantidade': p.quantidade,
            'data_cadastro': p.data_cadastro
        } for p in produtos])

    def add_produto(self, nome, descricao, valor, quantidade):
        produto = Produto(
            nome=nome,
            descricao=descricao,
            valor=valor,
            quantidade=quantidade
        )
        self.session.add(produto)
        self.session.commit()
        return produto.id

    def __del__(self):
        self.session.close()