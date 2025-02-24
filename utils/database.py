import os
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

# Ensure proper SSL configuration for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    connect_args={'sslmode': 'require'} if 'postgresql' in DATABASE_URL else {},
    pool_pre_ping=True,
    pool_recycle=3600
)

Base = declarative_base()

# Create scoped session
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)

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
    __table_args__ = (
        Index('idx_cliente_nome', 'nome'),
        Index('idx_cliente_email', 'email'),
    )
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
    descricao = Column(String, nullable=False)
    contato = Column(String)
    categoria = Column(String)
    tipo_conta = Column(String, nullable=False)
    pix = Column(String)
    recorrente = Column(Boolean, default=False)
    observacoes = Column(String)
    valor = Column(Float, nullable=True)
    data_vencimento = Column(Date, nullable=True)
    data_pagamento = Column(Date, nullable=True)
    status = Column(String, nullable=True)


class Assistente(Base):
    __tablename__ = 'assistentes'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    telefone = Column(String)
    endereco = Column(String)
    pix = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())
    observacoes = Column(String)

class Parceiro(Base):
    __tablename__ = 'parceiros'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    telefone = Column(String)
    email = Column(String)
    area_atuacao = Column(String)
    tipo_parceria = Column(String)
    pix = Column(String)
    observacoes = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())

class CategoriaDespesa(Base):
    __tablename__ = 'categorias_despesa'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    tipo_conta = Column(String)

class Proposta(Base):
    __tablename__ = 'propostas'
    id = Column(Integer, primary_key=True)
    numero = Column(Integer, nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    descricao = Column(String)
    valor = Column(Float)
    status = Column(String)
    tipo_proposta = Column(String)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    prazo_entrega = Column(Date)
    data_proposta = Column(Date, default=datetime.now().date())
    status_pagamento_base = Column(String, default='Pendente')  # New column

    cliente = relationship("Cliente", back_populates="propostas")
    produtos = relationship("ProdutoOrganizador", back_populates="proposta", cascade="all, delete-orphan")
    acrescimos = relationship("AcrescimoProposta", back_populates="proposta", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_proposta_numero', 'numero', unique=True),
    )

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
    tipo = Column(String)  # 'receita', 'despesa', 'receita_a_receber'
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date, default=datetime.now().date())
    categoria = Column(String)
    tipo_receita = Column(String)
    origem_id = Column(Integer)
    origem_tipo = Column(String)
    tipo_conta = Column(String, default='PF')
    status = Column(String, default='Pendente')  # 'Pendente', 'Recebido', 'Cancelado'
    data_recebimento = Column(Date, nullable=True)

class AcrescimoProposta(Base):
    __tablename__ = 'acrescimos_proposta'
    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'))
    tipo = Column(String, nullable=False)
    fornecedor = Column(String)
    descricao = Column(String)
    valor = Column(Float, nullable=False)
    status_pagamento = Column(String, default='Pendente')
    data_cadastro = Column(Date, default=datetime.now().date())

    proposta = relationship("Proposta", back_populates="acrescimos")


class Database:
    def __init__(self):
        try:
            Base.metadata.create_all(engine)
            self.session = Session()
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            raise e

    def _safe_query(self, query_func):
        """Wrapper para executar queries com tratamento de erro"""
        try:
            if not self.session.is_active:
                self.session = Session()
            result = query_func()
            self.session.commit()
            return result
        except Exception as e:
            if self.session.is_active:
                self.session.rollback()
            raise e
        finally:
            self.session.close()
            Session.remove()

    def get_clientes(self):
        def query():
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
        return self._safe_query(query)

    def add_cliente(self, nome, email, telefone, endereco, cpf=None, data_aniversario=None, 
                    origem_cliente=None, tipo_conta='PF', cnpj=None, razao_social=None):
        def query():
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
            return cliente.id
        return self._safe_query(query)

    def get_propostas(self):
        def query():
            propostas = self.session.query(Proposta).all()
            return pd.DataFrame([{
                'id': p.id,
                'numero': p.numero,
                'cliente_id': p.cliente_id,
                'descricao': p.descricao,
                'valor': p.valor,
                'status': p.status,
                'tipo_proposta': p.tipo_proposta,
                'data_inicio': p.data_inicio,
                'data_fim': p.data_fim,
                'prazo_entrega': p.prazo_entrega,
                'data_proposta': p.data_proposta,
                'status_pagamento_base': p.status_pagamento_base
            } for p in propostas])
        return self._safe_query(query)

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, 
                    data_inicio=None, data_fim=None, prazo_entrega=None):
        def query():
            # Gerar próximo número de proposta
            ultimo_numero = self.session.query(func.max(Proposta.numero)).scalar()
            proximo_numero = 1 if ultimo_numero is None else ultimo_numero + 1

            proposta = Proposta(
                numero=proximo_numero,
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
            return proposta.id
        return self._safe_query(query)

    def get_financeiro(self):
        def query():
            transacoes = self.session.query(Transacao).order_by(Transacao.data.desc()).limit(1000).all()
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
                'tipo_conta': t.tipo_conta,
                'status': t.status,
                'data_recebimento': t.data_recebimento
            } for t in transacoes])
        return self._safe_query(query)

    def add_transacao(self, tipo, descricao, valor, categoria, tipo_receita=None, 
                     origem_id=None, origem_tipo=None, tipo_conta='PF', status='Pendente'):
        def query():
            transacao = Transacao(
                tipo=tipo,
                descricao=descricao,
                valor=valor,
                categoria=categoria,
                tipo_receita=tipo_receita,
                origem_id=origem_id,
                origem_tipo=origem_tipo,
                tipo_conta=tipo_conta,
                status=status
            )
            self.session.add(transacao)
            return transacao.id
        return self._safe_query(query)

    def atualizar_status_transacao(self, transacao_id, status, data_recebimento=None):
        def query():
            transacao = self.session.query(Transacao).filter_by(id=transacao_id).first()
            if transacao:
                transacao.status = status
                if status == 'Recebido':
                    transacao.data_recebimento = data_recebimento or datetime.now().date()
                return True
            return False
        return self._safe_query(query)

    def get_contas_receber(self):
        def query():
            contas = self.session.query(Transacao).filter(
                Transacao.tipo.in_(['receita_a_receber']),
            ).order_by(Transacao.data.desc()).all()

            return pd.DataFrame([{
                'id': t.id,
                'descricao': t.descricao,
                'valor': t.valor,
                'data': t.data,
                'categoria': t.categoria,
                'tipo_receita': t.tipo_receita,
                'origem_tipo': t.origem_tipo,
                'tipo_conta': t.tipo_conta,
                'status': t.status,
                'data_recebimento': t.data_recebimento
            } for t in contas])
        return self._safe_query(query)

    def add_fornecedor(self, descricao, contato, categoria, tipo_conta, pix=None, recorrente=False, observacoes=None, valor=None, data_vencimento=None, data_pagamento=None, status=None):
        def query():
            fornecedor = Fornecedor(
                descricao=descricao,
                contato=contato,
                categoria=categoria,
                tipo_conta=tipo_conta,
                pix=pix,
                recorrente=recorrente,
                observacoes=observacoes,
                valor=valor,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                status=status
            )
            self.session.add(fornecedor)
            return fornecedor.id
        return self._safe_query(query)

    def get_fornecedores(self):
        def query():
            fornecedores = self.session.query(Fornecedor).all()
            return pd.DataFrame([{
                'id': f.id,
                'descricao': f.descricao,
                'contato': f.contato,
                'categoria': f.categoria,
                'tipo_conta': f.tipo_conta,
                'pix': f.pix,
                'recorrente': f.recorrente,
                'observacoes': f.observacoes,
                'valor': f.valor,
                'data_vencimento': f.data_vencimento,
                'data_pagamento': f.data_pagamento,
                'status': f.status
            } for f in fornecedores])
        return self._safe_query(query)

    def add_categoria_despesa(self, nome, descricao, tipo_conta):
        def query():
            categoria = CategoriaDespesa(
                nome=nome,
                descricao=descricao,
                tipo_conta=tipo_conta
            )
            self.session.add(categoria)
            return categoria.id
        return self._safe_query(query)

    def get_categorias_despesa(self):
        def query():
            categorias = self.session.query(CategoriaDespesa).all()
            return pd.DataFrame([{
                'id': c.id,
                'nome': c.nome,
                'descricao': c.descricao,
                'tipo_conta': c.tipo_conta
            } for c in categorias])
        return self._safe_query(query)

    def add_andamento_proposta(self, proposta_id, status, observacao, comodo=None):
        def query():
            andamento = AndamentoProposta(
                proposta_id=proposta_id,
                status=status,
                observacao=observacao,
                comodo=comodo
            )
            self.session.add(andamento)
            return andamento.id
        return self._safe_query(query)

    def get_andamentos_proposta(self, proposta_id):
        def query():
            andamentos = self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).all()
            return pd.DataFrame([{
                'id': a.id,
                'data': a.data,
                'status': a.status,
                'observacao': a.observacao,
                'comodo': a.comodo
            } for a in andamentos])
        return self._safe_query(query)

    def add_produto_organizador(self, proposta_id, nome, descricao, valor, quantidade, comodo):
        def query():
            produto = ProdutoOrganizador(
                proposta_id=proposta_id,
                nome=nome,
                descricao=descricao,
                valor=valor,
                quantidade=quantidade,
                comodo=comodo
            )
            self.session.add(produto)
            return produto.id
        return self._safe_query(query)

    def get_produtos_organizadores(self, proposta_id=None):
        def query():
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
        return self._safe_query(query)

    def add_produto_fornecedor(self, produto_id, fornecedor_id, valor, observacoes=None):
        """Adiciona um fornecedor e seu preço para um produto"""
        def query():
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

            self._atualizar_valor_produto(produto_id)
            return True
        return self._safe_query(query)


    def _atualizar_valor_produto(self, produto_id):
        """Atualiza o valor do produto com o menor valor entre os fornecedores"""
        def query():
            menor_valor = self.session.query(func.min(ProdutoFornecedor.valor))\
                .filter_by(produto_id=produto_id)\
                .scalar()

            if menor_valor is not None:
                produto = self.session.query(ProdutoOrganizador)\
                    .filter_by(id=produto_id)\
                    .first()
                if produto:
                    produto.valor = menor_valor
                    return True
            return False
        return self._safe_query(query)

    def get_produto_fornecedores(self, produto_id):
        """Retorna todos os fornecedores e preços de um produto"""
        def query():
            fornecedores = self.session.query(ProdutoFornecedor).filter_by(produto_id=produto_id).all()
            return pd.DataFrame([{
                'id': f.id,
                'produto_id': f.produto_id,
                'fornecedor_id': f.fornecedor_id,
                'fornecedor_nome': f.fornecedor.descricao if f.fornecedor else None,
                'valor': f.valor,
                'data_cotacao': f.data_cotacao,
                'observacoes': f.observacoes
            } for f in fornecedores])
        return self._safe_query(query)


    def registrar_usuario(self, email, senha, nome, empresa=None, tipo='usuario'):
        """Registra um novo usuário no sistema"""
        def query():
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
            return True, "Usuário cadastrado com sucesso"
        return self._safe_query(query)


    def autenticar_usuario(self, email, senha):
        """Autentica um usuário"""
        def query():
            usuario = self.session.query(Usuario).filter_by(email=email).first()
            if usuario and usuario.check_senha(senha) and usuario.ativo:
                return True, usuario
            return False, None
        return self._safe_query(query)

    def get_usuarios(self):
        """Retorna lista de usuários cadastrados"""
        def query():
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
        return self._safe_query(query)

    def atualizar_status_usuario(self, usuario_id, ativo):
        """Atualiza o status de ativo/inativo de um usuário"""
        def query():
            usuario = self.session.query(Usuario).filter_by(id=usuario_id).first()
            if usuario:
                usuario.ativo = ativo
                return True
            return False
        return self._safe_query(query)

    def atualizar_tipo_usuario(self, usuario_id, tipo):
        """Atualiza o tipo de um usuário (admin/usuario)"""
        def query():
            usuario = self.session.query(Usuario).filter_by(id=usuario_id).first()
            if usuario:
                usuario.tipo = tipo
                return True
            return False
        return self._safe_query(query)

    def add_test_data(self):
        def query():
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
                descricao="Organizadores Express",
                contato="(11) 97777-7777",
                categoria="Produtos",
                tipo_conta="PJ",
                pix="12345678901",
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
        try:
            return self._safe_query(query)
        except Exception as e:
            print(f"Erro ao adicionar dados de teste: {str(e)}")
            return False

    def add_assistente(self, nome, telefone, endereco, pix=None, observacoes=None):
        def query():
            assistente = Assistente(
                nome=nome,
                telefone=telefone,
                endereco=endereco,
                pix=pix,
                observacoes=observacoes
            )
            self.session.add(assistente)
            return assistente.id
        return self._safe_query(query)

    def get_assistentes(self):
        def query():
            assistentes = self.session.query(Assistente).all()
            return pd.DataFrame([{
                'id': a.id,
                'nome': a.nome,
                'telefone': a.telefone,
                'endereco': a.endereco,
                'pix': a.pix,
                'data_cadastro': a.data_cadastro,
                'observacoes': a.observacoes
            } for a in assistentes])
        return self._safe_query(query)

    def add_parceiro(self, nome, telefone, email, area_atuacao, tipo_parceria, pix=None, observacoes=None):
        """Adiciona um novo parceiro"""
        def query():
            parceiro = Parceiro(
                nome=nome,
                telefone=telefone,
                email=email,
                area_atuacao=area_atuacao,
                tipo_parceria=tipo_parceria,
                pix=pix,
                observacoes=observacoes
            )
            self.session.add(parceiro)
            return parceiro.id
        return self._safe_query(query)

    def get_parceiros(self):
        """Retorna lista de parceiros cadastrados"""
        def query():
            parceiros = self.session.query(Parceiro).all()
            return pd.DataFrame([{
                'id': p.id,
                'nome': p.nome,
                'telefone': p.telefone,
                'email': p.email,
                'area_atuacao': p.area_atuacao,
                'tipo_parceria': p.tipo_parceria,
                'pix': p.pix,
                'observacoes': p.observacoes,
                'data_cadastro': p.data_cadastro
            } for p in parceiros])
        return self._safe_query(query)

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
            Session.remove()

    def atualizar_status_pagamento_proposta(self, proposta_id, status_pagamento_base, valor_base):
        def query():
            # Converter ID para int nativo do Python
            proposta_id = int(proposta_id)
            valor_base = float(valor_base)

            proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
            if proposta:
                proposta.status_pagamento_base = status_pagamento_base
                proposta.valor = valor_base
                return True
            return False
        return self._safe_query(query)

    def add_acrescimo_proposta(self, proposta_id, tipo, valor, descricao=None, fornecedor=None, status_pagamento='Pendente'):
        def query():
            acrescimo = AcrescimoProposta(
                proposta_id=proposta_id,
                tipo=tipo,
                fornecedor=fornecedor,
                descricao=descricao,
                valor=valor,
                status_pagamento=status_pagamento
            )
            self.session.add(acrescimo)
            return acrescimo.id
        return self._safe_query(query)

    def get_acrescimos_proposta(self, proposta_id):
        # Converter proposta_id para int nativo do Python antes da função query
        proposta_id = int(proposta_id) if proposta_id is not None else None

        def query():
            acrescimos = self.session.query(AcrescimoProposta).filter_by(proposta_id=proposta_id).all()
            return pd.DataFrame([{
                'id': int(a.id),  # Garantir que todos os IDs sejam int nativos
                'tipo': a.tipo,
                'fornecedor': a.fornecedor,
                'descricao': a.descricao,
                'valor': float(a.valor) if a.valor is not None else None,  # Converter para float nativo
                'status_pagamento': a.status_pagamento,
                'data_cadastro': a.data_cadastro
            } for a in acrescimos])
        return self._safe_query(query)

    def get_pagamentos_pendentes(self):
        def query():
            # Get propostas with pending base payments
            propostas = self.session.query(Proposta).filter_by(status_pagamento_base='Pendente').all()
            pendentes = []

            # Add pending base values
            for p in propostas:
                pendentes.append({
                    'cliente': p.cliente.nome,
                    'proposta': p.numero,
                    'tipo': 'Valor Base',
                    'valor': p.valor,
                    'fornecedor': None
                })

            # Add pending acrescimos
            acrescimos = self.session.query(AcrescimoProposta).filter_by(status_pagamento='Pendente').all()
            for a in acrescimos:
                pendentes.append({
                    'cliente': a.proposta.cliente.nome,
                    'proposta': a.proposta.numero,
                    'tipo': a.tipo,
                    'valor': a.valor,
                    'fornecedor': a.fornecedor
                })

            return pd.DataFrame(pendentes)
        return self._safe_query(query)