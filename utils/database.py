import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String)
    telefone = Column(String)
    endereco = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())
    tipo_conta = Column(String, default='PF')  # PF ou PJ
    cnpj = Column(String)
    razao_social = Column(String)

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

class CategoriaDespesa(Base):
    __tablename__ = 'categorias_despesa'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    tipo_conta = Column(String)  # PF ou PJ

class ContaPagar(Base):
    __tablename__ = 'contas_pagar'

    id = Column(Integer, primary_key=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date)
    status = Column(String, default='Pendente')  # Pendente, Pago, Atrasado
    categoria_id = Column(Integer, ForeignKey('categorias_despesa.id'))
    tipo_conta = Column(String, nullable=False)  # PF ou PJ
    fornecedor = Column(String)
    recorrente = Column(Boolean, default=False)
    observacoes = Column(String)

    categoria = relationship("CategoriaDespesa")

class Transacao(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True)
    tipo = Column(String)  # receita/despesa
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date, default=datetime.now().date())
    categoria = Column(String)
    referencia_id = Column(Integer)
    tipo_conta = Column(String, default='PF')  # PF ou PJ

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    descricao = Column(String)
    valor = Column(Float)
    quantidade = Column(Integer)
    data_cadastro = Column(Date, default=datetime.now().date())

class Database:
    def __init__(self):
        try:
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            self.session = Session()
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            raise e

    def get_clientes(self):
        clientes = self.session.query(Cliente).all()
        return pd.DataFrame([{
            'id': c.id,
            'nome': c.nome,
            'email': c.email,
            'telefone': c.telefone,
            'endereco': c.endereco,
            'data_cadastro': c.data_cadastro,
            'tipo_conta': c.tipo_conta,
            'cnpj': c.cnpj,
            'razao_social': c.razao_social
        } for c in clientes])

    def add_cliente(self, nome, email, telefone, endereco, tipo_conta='PF', cnpj=None, razao_social=None):
        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco,
            tipo_conta=tipo_conta,
            cnpj=cnpj,
            razao_social=razao_social
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
            'referencia_id': t.referencia_id,
            'tipo_conta': t.tipo_conta
        } for t in transacoes])

    def add_transacao(self, tipo, descricao, valor, categoria, referencia_id=None, tipo_conta='PF'):
        transacao = Transacao(
            tipo=tipo,
            descricao=descricao,
            valor=valor,
            categoria=categoria,
            referencia_id=referencia_id,
            tipo_conta=tipo_conta
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

    def add_test_data(self):
        """Add sample data for testing"""
        try:
            # Add test clients
            client1_id = self.add_cliente(
                "Maria Silva",
                "maria@email.com",
                "(11) 99999-9999",
                "Rua das Flores, 123"
            )

            client2_id = self.add_cliente(
                "João Santos",
                "joao@email.com",
                "(11) 88888-8888",
                "Av. Principal, 456"
            )

            # Add test proposals
            self.add_proposta(
                client1_id,
                "Organização do closet",
                1500.00,
                "Aberta"
            )

            self.add_proposta(
                client2_id,
                "Organização da cozinha",
                2000.00,
                "Fechada"
            )

            # Add test transactions
            self.add_transacao(
                "receita",
                "Pagamento - Organização cozinha",
                2000.00,
                "Serviço"
            )

            self.add_transacao(
                "despesa",
                "Compra de materiais",
                500.00,
                "Fornecedor"
            )

            return True

        except Exception as e:
            print(f"Erro ao adicionar dados de teste: {str(e)}")
            return False

    def add_conta_pagar(self, descricao, valor, data_vencimento, categoria_id, tipo_conta, fornecedor=None, recorrente=False, observacoes=None):
        conta = ContaPagar(
            descricao=descricao,
            valor=valor,
            data_vencimento=data_vencimento,
            categoria_id=categoria_id,
            tipo_conta=tipo_conta,
            fornecedor=fornecedor,
            recorrente=recorrente,
            observacoes=observacoes
        )
        self.session.add(conta)
        self.session.commit()
        return conta.id

    def get_contas_pagar(self):
        contas = self.session.query(ContaPagar).all()
        return pd.DataFrame([{
            'id': c.id,
            'descricao': c.descricao,
            'valor': c.valor,
            'data_vencimento': c.data_vencimento,
            'data_pagamento': c.data_pagamento,
            'status': c.status,
            'categoria_id': c.categoria_id,
            'tipo_conta': c.tipo_conta,
            'fornecedor': c.fornecedor,
            'recorrente': c.recorrente,
            'observacoes': c.observacoes
        } for c in contas])

    def add_categoria_despesa(self, nome, descricao, tipo_conta):
        categoria = CategoriaDespesa(
            nome=nome,
            descricao=descricao,
            tipo_conta=tipo_conta
        )
        self.session.add(categoria)
        self.session.commit()
        return categoria.id

    def get_categorias_despesa(self):
        categorias = self.session.query(CategoriaDespesa).all()
        return pd.DataFrame([{
            'id': c.id,
            'nome': c.nome,
            'descricao': c.descricao,
            'tipo_conta': c.tipo_conta
        } for c in categorias])

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()