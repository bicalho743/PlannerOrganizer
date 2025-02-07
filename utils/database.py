import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, Sequence
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
    andamentos = relationship("AndamentoProposta", back_populates="proposta")
    produtos = relationship("ProdutoOrganizador", back_populates="proposta")

class AndamentoProposta(Base):
    __tablename__ = 'andamento_propostas'

    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'))
    data = Column(Date, default=datetime.now().date())
    status = Column(String)
    observacao = Column(String)
    comodo = Column(String)

    proposta = relationship("Proposta", back_populates="andamentos")

class ProdutoOrganizador(Base):
    __tablename__ = 'produtos_organizadores'

    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'))
    nome = Column(String, nullable=False)
    descricao = Column(String)
    valor = Column(Float)
    quantidade = Column(Integer)
    comodo = Column(String, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey('fornecedores.id'))
    data_cadastro = Column(Date, default=datetime.now().date())

    proposta = relationship("Proposta", back_populates="produtos")
    fornecedor = relationship("Fornecedor", back_populates="produtos")

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

    produtos = relationship("ProdutoOrganizador", back_populates="fornecedor")

class CategoriaDespesa(Base):
    __tablename__ = 'categorias_despesa'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    tipo_conta = Column(String)

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

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    descricao = Column(String)
    valor = Column(Float)
    quantidade = Column(Integer)
    data_cadastro = Column(Date, default=datetime.now().date())

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    empresa = Column(String)
    tipo = Column(String, default='usuario')  # 'admin' ou 'usuario'
    ativo = Column(Boolean, default=True)
    data_cadastro = Column(Date, default=datetime.now().date())

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

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

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, prazo_entrega=None, data_inicio=None, data_fim=None):
        proposta = Proposta(
            cliente_id=cliente_id,
            descricao=descricao,
            valor=valor,
            status=status,
            tipo_proposta=tipo_proposta,
            prazo_entrega=prazo_entrega,
            data_inicio=data_inicio,
            data_fim=data_fim
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
        try:
            # Add test clients
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

            client3_id = self.add_cliente(
                nome="Empresa ABC Ltda",
                email="contato@empresaabc.com",
                telefone="(11) 3333-3333",
                endereco="Av. Comercial, 789",
                cnpj="12.345.678/0001-90",
                razao_social="ABC Comércio e Serviços Ltda",
                origem_cliente="Site",
                tipo_conta="PJ"
            )

            # Add test fornecedores
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

            fornecedor2_id = self.add_fornecedor(
                nome="Móveis Planejados SA",
                descricao="Fornecedor de móveis planejados",
                valor=0,
                data_vencimento=None,
                categoria="Móveis",
                tipo_conta="PJ",
                pix="98765432109",
                contato="(11) 96666-6666",
                recorrente=False
            )

            # Add test propostas
            proposta1_id = self.add_proposta(
                client1_id,
                "Organização do closet",
                1500.00,
                "Aberta",
                tipo_proposta="Organização"
            )

            proposta2_id = self.add_proposta(
                client2_id,
                "Organização da cozinha",
                2000.00,
                "Fechada",
                tipo_proposta="Organização"
            )

            proposta3_id = self.add_proposta(
                client3_id,
                "Consultoria para escritório",
                3500.00,
                "Aberta",
                tipo_proposta="Consultoria Online"
            )

            # Add test produtos organizadores
            self.add_produto_organizador(
                proposta_id=proposta1_id,
                nome="Caixa Organizadora Grande",
                descricao="Caixa transparente com tampa",
                valor=50.00,
                quantidade=5,
                comodo="Closet",
                fornecedor_id=fornecedor1_id
            )

            self.add_produto_organizador(
                proposta_id=proposta2_id,
                nome="Divisor de Gavetas",
                descricao="Kit com 6 divisores",
                valor=80.00,
                quantidade=2,
                comodo="Cozinha",
                fornecedor_id=fornecedor1_id
            )

            # Add test transactions
            self.add_transacao(
                tipo="receita",
                descricao="Pagamento - Organização cozinha",
                valor=2000.00,
                categoria="Serviço",
                tipo_receita="organização",
                origem_id=client2_id,
                origem_tipo="cliente"
            )

            self.add_transacao(
                tipo="despesa",
                descricao="Compra de materiais",
                valor=500.00,
                categoria="Fornecedor",
                origem_id=fornecedor1_id,
                origem_tipo="fornecedor"
            )

            return True

        except Exception as e:
            print(f"Erro ao adicionar dados de teste: {str(e)}")
            return False

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

    def add_produto_organizador(self, proposta_id, nome, descricao, valor, quantidade, comodo, fornecedor_id):
        produto = ProdutoOrganizador(
            proposta_id=proposta_id,
            nome=nome,
            descricao=descricao,
            valor=valor,
            quantidade=quantidade,
            comodo=comodo,
            fornecedor_id=fornecedor_id
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
            'fornecedor_id': p.fornecedor_id,
            'data_cadastro': p.data_cadastro
        } for p in produtos])

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()

    def registrar_usuario(self, email, senha, nome, empresa=None, tipo='usuario'):
        """Registra um novo usuário no sistema"""
        try:
            # Verificar se o email já existe
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