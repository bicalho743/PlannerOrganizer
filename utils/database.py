import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, Sequence, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    empresa = Column(String)
    tipo = Column(String, default='usuario')
    ativo = Column(Boolean, default=True)
    data_cadastro = Column(Date, default=datetime.now().date())

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String)
    telefone = Column(String)
    endereco = Column(String)
    cpf = Column(String)
    data_aniversario = Column(Date)
    origem_cliente = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())
    tipo_conta = Column(String, default='PF')
    cnpj = Column(String)
    razao_social = Column(String)

    propostas = relationship("Proposta", back_populates="cliente")

class Fornecedor(Base):
    __tablename__ = 'fornecedores'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    valor = Column(Float)
    data_vencimento = Column(Date)
    data_pagamento = Column(Date)
    status = Column(String, default='Pendente')
    categoria = Column(String)
    pix = Column(String)
    contato = Column(String)
    tipo_conta = Column(String, nullable=False)
    recorrente = Column(Boolean, default=False)
    observacoes = Column(String)

class CategoriaDespesa(Base):
    __tablename__ = 'categorias_despesa'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    tipo_conta = Column(String)

class Proposta(Base):
    __tablename__ = 'propostas'
    id = Column(Integer, primary_key=True)
    numero = Column(Integer, Sequence('proposta_seq'), unique=True, nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    descricao = Column(String)
    valor = Column(Float)
    status = Column(String)
    tipo_proposta = Column(String)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    prazo_entrega = Column(Date)
    data_proposta = Column(Date, default=datetime.now().date())

    cliente = relationship("Cliente", back_populates="propostas")
    produtos = relationship("ProdutoOrganizador", back_populates="proposta", cascade="all, delete-orphan")

class ProdutoOrganizador(Base):
    __tablename__ = 'produtos_organizadores'
    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'))
    nome = Column(String, nullable=False)
    descricao = Column(String)
    valor = Column(Float)
    quantidade = Column(Integer)
    comodo = Column(String, nullable=False)
    data_cadastro = Column(Date, default=datetime.now().date())

    proposta = relationship("Proposta", back_populates="produtos")
    fornecedores = relationship("ProdutoFornecedor", back_populates="produto", cascade="all, delete-orphan")

class ProdutoFornecedor(Base):
    __tablename__ = 'produtos_fornecedores'
    id = Column(Integer, primary_key=True)
    produto_id = Column(Integer, ForeignKey('produtos_organizadores.id'))
    fornecedor_id = Column(Integer, ForeignKey('fornecedores.id'))
    valor = Column(Float)
    data_cotacao = Column(Date, default=datetime.now().date())
    observacoes = Column(String)

    produto = relationship("ProdutoOrganizador", back_populates="fornecedores")
    fornecedor = relationship("Fornecedor")

class AndamentoProposta(Base):
    __tablename__ = 'andamento_propostas'
    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'))
    data = Column(Date, default=datetime.now().date())
    status = Column(String)
    observacao = Column(String)
    comodo = Column(String)

    proposta = relationship("Proposta")

class Transacao(Base):
    __tablename__ = 'financeiro'
    id = Column(Integer, primary_key=True)
    tipo = Column(String)
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date, default=datetime.now().date())
    categoria = Column(String)
    tipo_receita = Column(String)
    origem_id = Column(Integer)
    origem_tipo = Column(String)
    tipo_conta = Column(String, default='PF')

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
            'numero': p.numero,
            'cliente_id': p.cliente_id,
            'descricao': p.descricao,
            'valor': p.valor,
            'status': p.status,
            'data_proposta': p.data_proposta,
            'tipo_proposta': p.tipo_proposta,
            'data_inicio': p.data_inicio,
            'data_fim': p.data_fim,
            'prazo_entrega': p.prazo_entrega
        } for p in propostas])

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, data_inicio=None, data_fim=None, prazo_entrega=None):
        proposta = Proposta(
            cliente_id=cliente_id,
            descricao=descricao,
            valor=valor,
            status=status,
            tipo_proposta=tipo_proposta,
            data_inicio=data_inicio,
            data_fim=data_fim,
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

    def add_fornecedor(self, nome, descricao, valor, data_vencimento, categoria, tipo_conta, pix=None, contato=None, recorrente=False, observacoes=None):
        fornecedor = Fornecedor(
            nome=nome,
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

    def get_fornecedores(self):
        fornecedores = self.session.query(Fornecedor).all()
        return pd.DataFrame([{
            'id': f.id,
            'nome': f.nome,
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

    def add_andamento_proposta(self, proposta_id, status, observacao, comodo=None):
        andamento = AndamentoProposta(
            proposta_id=proposta_id,
            status=status,
            observacao=observacao,
            comodo=comodo
        )
        self.session.add(andamento)
        self.session.commit()
        return andamento.id

    def get_andamentos_proposta(self, proposta_id):
        andamentos = self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).all()
        return pd.DataFrame([{
            'id': a.id,
            'data': a.data,
            'status': a.status,
            'observacao': a.observacao,
            'comodo': a.comodo
        } for a in andamentos])

    def add_produto_organizador(self, proposta_id, nome, descricao, valor, quantidade, comodo):
        produto = ProdutoOrganizador(
            proposta_id=proposta_id,
            nome=nome,
            descricao=descricao,
            valor=valor,
            quantidade=quantidade,
            comodo=comodo
        )
        self.session.add(produto)
        self.session.commit()
        return produto.id

    def get_produtos_organizadores(self, proposta_id=None):
        query = self.session.query(ProdutoOrganizador)
        if proposta_id:
            query = query.filter_by(proposta_id=proposta_id)
        produtos = query.all()
        return pd.DataFrame([{
            'id': p.id,
            'nome': p.nome,
            'descricao': p.descricao,
            'valor': p.valor,
            'quantidade': p.quantidade,
            'comodo': p.comodo,
            'data_cadastro': p.data_cadastro
        } for p in produtos])

    def add_produto_fornecedor(self, produto_id, fornecedor_id, valor, observacoes=None):
        """Adiciona um fornecedor e seu preço para um produto"""
        try:
            existente = self.session.query(ProdutoFornecedor).filter_by(
                produto_id=produto_id,
                fornecedor_id=fornecedor_id
            ).first()

            if existente:
                existente.valor = valor
                existente.observacoes = observacoes
                existente.data_cotacao = datetime.now().date()
            else:
                fornecedor = ProdutoFornecedor(
                    produto_id=produto_id,
                    fornecedor_id=fornecedor_id,
                    valor=valor,
                    observacoes=observacoes
                )
                self.session.add(fornecedor)

            self.session.commit()
            self._atualizar_valor_produto(produto_id)
            return True
        except Exception as e:
            self.session.rollback()
            raise e

    def _atualizar_valor_produto(self, produto_id):
        """Atualiza o valor do produto com o menor valor entre os fornecedores"""
        try:
            menor_valor = self.session.query(func.min(ProdutoFornecedor.valor))\
                .filter_by(produto_id=produto_id)\
                .scalar()

            if menor_valor is not None:
                produto = self.session.query(ProdutoOrganizador)\
                    .filter_by(id=produto_id)\
                    .first()
                if produto:
                    produto.valor = menor_valor
                    self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_produto_fornecedores(self, produto_id):
        """Retorna todos os fornecedores e preços de um produto"""
        fornecedores = self.session.query(ProdutoFornecedor).filter_by(produto_id=produto_id).all()
        return pd.DataFrame([{
            'id': f.id,
            'produto_id': f.produto_id,
            'fornecedor_id': f.fornecedor_id,
            'fornecedor_nome': f.fornecedor.nome if f.fornecedor else None,
            'valor': f.valor,
            'data_cotacao': f.data_cotacao,
            'observacoes': f.observacoes
        } for f in fornecedores])

    def registrar_usuario(self, email, senha, nome, empresa=None, tipo='usuario'):
        """Registra um novo usuário no sistema"""
        try:
            if self.session.query(Usuario).filter_by(email=email).first():
                return False, "Email já cadastrado"

            usuario = Usuario(
                email=email,
                nome=nome,
                empresa=empresa,
                tipo=tipo
            )
            usuario.set_senha(senha)

            self.session.add(usuario)
            self.session.commit()
            return True, "Usuário cadastrado com sucesso"
        except Exception as e:
            self.session.rollback()
            return False, str(e)

    def autenticar_usuario(self, email, senha):
        """Autentica um usuário"""
        try:
            usuario = self.session.query(Usuario).filter_by(email=email).first()
            if usuario and usuario.check_senha(senha) and usuario.ativo:
                return True, usuario
            return False, None
        except Exception as e:
            return False, str(e)

    def get_usuarios(self):
        """Retorna lista de usuários cadastrados"""
        usuarios = self.session.query(Usuario).all()
        return pd.DataFrame([{
            'id': u.id,
            'email': u.email,
            'nome': u.nome,
            'empresa': u.empresa,
            'tipo': u.tipo,
            'ativo': u.ativo,
            'data_cadastro': u.data_cadastro
        } for u in usuarios])

    def atualizar_status_usuario(self, usuario_id, ativo):
        """Atualiza o status de ativo/inativo de um usuário"""
        try:
            usuario = self.session.query(Usuario).filter_by(id=usuario_id).first()
            if usuario:
                usuario.ativo = ativo
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            return False

    def atualizar_tipo_usuario(self, usuario_id, tipo):
        """Atualiza o tipo de um usuário (admin/usuario)"""
        try:
            usuario = self.session.query(Usuario).filter_by(id=usuario_id).first()
            if usuario:
                usuario.tipo = tipo
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            return False

    def add_test_data(self):
        try:
            client1_id = self.add_cliente(
                nome="Maria Silva",
                email="maria@email.com",
                telefone="(11) 99999-9999",
                endereco="Rua das Flores, 123",
                cpf="123.456.789-00",
                data_aniversario=datetime.now().date(),
                origem_cliente="Indicação",
                tipo_conta="PF"
            )

            client2_id = self.add_cliente(
                nome="João Santos",
                email="joao@email.com",
                telefone="(11) 88888-8888",
                endereco="Av. Principal, 456",
                cpf="987.654.321-00",
                data_aniversario=datetime.now().date(),
                origem_cliente="Redes Sociais",
                tipo_conta="PF"
            )

            fornecedor1_id = self.add_fornecedor(
                nome="Organizadores Express",
                descricao="Fornecedor de produtos organizadores",
                valor=0,
                data_vencimento=None,
                categoria="Produtos",
                tipo_conta="PJ",
                pix="12345678901",
                contato="(11) 97777-7777",
                recorrente=False
            )

            proposta1_id = self.add_proposta(
                client1_id,
                "Organização do closet",
                1500.00,
                "Aberta",
                tipo_proposta="Organização"
            )

            produto1_id = self.add_produto_organizador(
                proposta_id=proposta1_id,
                nome="Caixa Organizadora Grande",
                descricao="Caixa transparente com tampa",
                valor=50.00,
                quantidade=5,
                comodo="Closet"
            )

            self.add_produto_fornecedor(produto1_id, fornecedor1_id, 50.00)

            return True
        except Exception as e:
            print(f"Erro ao adicionar dados de teste: {str(e)}")
            return False

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()