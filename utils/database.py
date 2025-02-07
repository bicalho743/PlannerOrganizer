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
    cpf = Column(String)
    data_aniversario = Column(Date)
    origem_cliente = Column(String)  # onde conheceu a personal
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
    tipo_proposta = Column(String, default='Serviço Regular')
    loja_consignada = Column(String)
    prazo_consignacao = Column(Integer)
    marceneiro = Column(String)
    prazo_entrega = Column(Date)
    data_proposta = Column(Date, default=datetime.now().date())

    cliente = relationship("Cliente", back_populates="propostas")

class CategoriaDespesa(Base):
    __tablename__ = 'categorias_despesa'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    tipo_conta = Column(String)  # PF ou PJ

class Fornecedor(Base): # Renamed to Fornecedor
    __tablename__ = 'fornecedores'

    id = Column(Integer, primary_key=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date)
    status = Column(String, default='Pendente')  # Pendente, Pago, Atrasado
    categoria = Column(String)
    pix = Column(String)
    contato = Column(String)
    tipo_conta = Column(String, nullable=False)  # PF ou PJ
    recorrente = Column(Boolean, default=False)
    observacoes = Column(String)


class Transacao(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True)
    tipo = Column(String)  # receita/despesa
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date, default=datetime.now().date())
    categoria = Column(String)
    tipo_receita = Column(String)  # organização, comissão, venda
    origem_id = Column(Integer)  # ID do cliente ou fornecedor
    origem_tipo = Column(String)  # cliente ou fornecedor
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
            'cpf': c.cpf,
            'data_aniversario': c.data_aniversario,
            'origem_cliente': c.origem_cliente,
            'data_cadastro': c.data_cadastro,
            'tipo_conta': c.tipo_conta,
            'cnpj': c.cnpj,
            'razao_social': c.razao_social
        } for c in clientes])

    def add_cliente(self, nome, email, telefone, endereco, cpf=None, data_aniversario=None, 
                    origem_cliente=None, tipo_conta='PF', cnpj=None, razao_social=None):
        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco,
            cpf=cpf,
            data_aniversario=data_aniversario,
            origem_cliente=origem_cliente,
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
            'data_proposta': p.data_proposta,
            'tipo_proposta': p.tipo_proposta if hasattr(p, 'tipo_proposta') else None
        } for p in propostas])

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, 
                     loja_consignada=None, prazo_consignacao=None, marceneiro=None, prazo_entrega=None):
        proposta = Proposta(
            cliente_id=cliente_id,
            descricao=descricao,
            valor=valor,
            status=status,
            tipo_proposta=tipo_proposta,
            loja_consignada=loja_consignada,
            prazo_consignacao=prazo_consignacao,
            marceneiro=marceneiro,
            prazo_entrega=prazo_entrega
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
            'tipo_receita': t.tipo_receita,
            'origem_id': t.origem_id,
            'origem_tipo': t.origem_tipo,
            'tipo_conta': t.tipo_conta
        } for t in transacoes])

    def add_transacao(self, tipo, descricao, valor, categoria, tipo_receita=None, 
                     origem_id=None, origem_tipo=None, tipo_conta='PF'):
        transacao = Transacao(
            tipo=tipo,
            descricao=descricao,
            valor=valor,
            categoria=categoria,
            tipo_receita=tipo_receita,
            origem_id=origem_id,
            origem_tipo=origem_tipo,
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

    def add_fornecedor(self, descricao, valor, data_vencimento, categoria, tipo_conta, pix=None, contato=None, recorrente=False, observacoes=None): #Updated method
        fornecedor = Fornecedor( #Renamed to Fornecedor
            descricao=descricao,
            valor=valor,
            data_vencimento=data_vencimento,
            categoria=categoria,
            tipo_conta=tipo_conta,
            pix=pix,
            contato=contato,
            recorrente=recorrente,
            observacoes=observacoes
        )
        self.session.add(fornecedor)
        self.session.commit()
        return fornecedor.id

    def get_fornecedores(self): #Added method
        fornecedores = self.session.query(Fornecedor).all()
        return pd.DataFrame([{
            'id': f.id,
            'descricao': f.descricao,
            'valor': f.valor,
            'data_vencimento': f.data_vencimento,
            'data_pagamento': f.data_pagamento,
            'status': f.status,
            'categoria': f.categoria,
            'pix': f.pix,
            'contato': f.contato,
            'tipo_conta': f.tipo_conta,
            'recorrente': f.recorrente,
            'observacoes': f.observacoes
        } for f in fornecedores])



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