"""
SQLAlchemy Models para o sistema Planner Organizer
Contém todas as classes declarativas (Perfil, Usuario, Cliente, etc.)
"""
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, func, Index, text, select, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# Ensure proper SSL configuration for PostgreSQL
try:
    from sqlalchemy.pool import QueuePool
    import time as _time
    
    _connect_args = {}
    if 'postgresql' in DATABASE_URL:
        _connect_args = {
            'sslmode': 'require',
            'connect_timeout': 30,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    
    def _create_engine_with_retry(max_retries=3):
        for attempt in range(max_retries):
            try:
                eng = create_engine(
                    DATABASE_URL,
                    connect_args=_connect_args,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=300,
                    pool_pre_ping=True,
                    isolation_level='AUTOCOMMIT'
                )
                with eng.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("Iniciando motor de banco com conexão estável e pool_pre_ping ativo")
                return eng
            except Exception as e:
                print(f"Tentativa {attempt + 1}/{max_retries} de conexão falhou: {str(e)}")
                if attempt < max_retries - 1:
                    _time.sleep(2 * (attempt + 1))
                else:
                    raise
    
    engine = _create_engine_with_retry()
except Exception as e:
    print(f"Error creating database engine: {str(e)}")
    raise

Base = declarative_base()

# Create scoped session
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)


# =========== MODELOS ===========

class Perfil(Base):
    """
    Tabela de perfis de usuários para sistema multi-tenant
    Cada usuário deve ter seu registro aqui antes de poder usar o sistema
    """
    __tablename__ = 'perfis'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(String, unique=True, nullable=False)  # Corresponde ao Firebase UID
    email = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    telefone = Column(String)
    empresa = Column(String)
    instagram = Column(String)
    website = Column(String)
    cargo = Column(String)  # Campo para cargo/função do usuário
    cor_principal = Column(String)
    cor_secundaria = Column(String)
    mensagem_padrao = Column(String)  # Campo para mensagem de agradecimento nos relatórios
    observacoes_relatorio = Column(String)  # Campo para observações personalizadas do usuário nos relatórios
    role = Column(String, default='user')
    plano = Column(String, default='gratuito')
    data_cadastro = Column(Date, default=datetime.now().date())
    ultimo_login = Column(DateTime)
    ativo = Column(Boolean, default=True)

class Usuario(Base):
    """
    Tabela legada de usuários
    Nota: esta tabela será mantida por retrocompatibilidade, 
    mas novos usuários devem usar a tabela 'perfis'
    """
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    telefone = Column(String)
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
        Index('idx_cliente_usuario_id', 'usuario_id'),  # Índice para otimizar filtro por usuário
    )
    nome = Column(String, nullable=False)
    telefone = Column(String)
    cpf = Column(String)
    email = Column(String)
    estado = Column(String)
    cidade = Column(String)
    bairro = Column(String)
    endereco = Column(String)
    data_aniversario = Column(String)  # Alterado de Date para String para aceitar formato DD/MMM
    origem_cliente = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())
    observacoes = Column(String)  # Adicionado campo observacoes
    usuario_id = Column(String, nullable=True)  # ID do usuário proprietário do registro (multi-tenant)

    propostas = relationship("Proposta", back_populates="cliente")

class Fornecedor(Base):
    __tablename__ = 'fornecedores'
    id = Column(Integer, primary_key=True)
    # Removida coluna nome que não existe no banco de produção
    descricao = Column(String, nullable=False)  # Este campo é usado como nome no banco de produção
    contato = Column(String)
    categoria = Column(String)
    estado = Column(String)
    cidade = Column(String)
    bairro = Column(String)
    endereco = Column(String)
    pix = Column(String)
    recorrente = Column(Boolean, default=False)
    observacoes = Column(String)
    valor = Column(Float, nullable=True)
    data_vencimento = Column(Date, nullable=True)
    data_pagamento = Column(Date, nullable=True)
    status = Column(String, nullable=True)
    tipo_conta = Column(String, default='PF')
    percentual_comissao = Column(Float, default=0.0)  # Percentual de comissão para o fornecedor
    usuario_id = Column(String, nullable=True)  # CORREÇÃO: Adicionar campo usuario_id
    
    # Propriedade para compatibilidade com código que usa f.nome
    @property
    def nome(self):
        return self.descricao


class Assistente(Base):
    __tablename__ = 'assistentes'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    telefone = Column(String)
    endereco = Column(String)
    disponibilidade = Column(String)
    pix = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())
    observacoes = Column(String)
    usuario_id = Column(String, nullable=True)  # CORREÇÃO: Adicionar campo usuario_id

class Parceiro(Base):
    __tablename__ = 'parceiros'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    telefone = Column(String)
    area_atuacao = Column(String)
    tipo_parceria = Column(String)
    estado = Column(String)  # Novo campo
    cidade = Column(String)  # Novo campo
    bairro = Column(String)  # Novo campo
    endereco = Column(String)
    pix = Column(String)
    observacoes = Column(String)
    data_cadastro = Column(Date, default=datetime.now().date())
    usuario_id = Column(String, nullable=True)  # CORREÇÃO: Adicionar campo usuario_id

class CategoriaDespesa(Base):
    __tablename__ = 'categorias_despesa'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)

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
    data_aprovacao = Column(Date, nullable=True)  # Data de aprovação da proposta
    status_pagamento_base = Column(String, default='Pendente')
    previsao_dias = Column(Integer)  # Dias previstos para execução
    data_inicio_execucao = Column(Date)  # Data de início efetivo da execução
    status_execucao = Column(String, default='Não iniciada')  # Vocabulário canônico (utils/status_execucao.py): 'Não iniciada', 'Em execução', 'Finalizada', 'Cancelada'
    usuario_id = Column(String, nullable=True)  # ID do usuário proprietário do registro (multi-tenant)

    cliente = relationship("Cliente", back_populates="propostas")
    produtos = relationship("ProdutoOrganizador", back_populates="proposta", cascade="all, delete-orphan")
    acrescimos = relationship("AcrescimoProposta", back_populates="proposta", cascade="all, delete-orphan")
    vendas = relationship("Venda", back_populates="proposta") # Relacionamento com vendas

    __table_args__ = (
        Index('idx_proposta_numero', 'numero', unique=True),
        Index('idx_proposta_usuario_id', 'usuario_id'),  # Índice para otimizar filtro por usuário
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
    usuario_id = Column(String, nullable=True)  # Campo para isolamento multi-tenant

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
    usuario_id = Column(String)  # Adicionado campo usuario_id

    proposta = relationship("Proposta")

class Transacao(Base):
    __tablename__ = 'financeiro'
    id = Column(Integer, primary_key=True)
    tipo = Column(String)  # 'receita', 'despesa', 'receita_a_receber'
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date, default=datetime.now().date())
    categoria = Column(String)
    subcategoria = Column(String)  # Nova subcategoria para classificação mais detalhada
    tipo_receita = Column(String)
    origem_id = Column(Integer)
    origem_tipo = Column(String)
    tipo_conta = Column(String, default='PF')
    status = Column(String, default='Pendente')  # 'Pendente', 'Recebido', 'Cancelado'
    data_recebimento = Column(Date, nullable=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'), nullable=True)  # Referência direta à proposta
    classificacao = Column(String)  # 'receita', 'custo_direto', 'despesa_operacional'
    usuario_id = Column(String, nullable=True)  # ID do usuário proprietário do registro (multi-tenant)
    
    # Relacionamento com proposta
    proposta = relationship("Proposta")
    
    __table_args__ = (
        Index('idx_financeiro_usuario_id', 'usuario_id'),  # Índice para otimizar filtro por usuário
        Index('idx_financeiro_data', 'data'),  # Índice para otimizar consultas por data
        Index('idx_financeiro_tipo', 'tipo'),  # Índice para otimizar consultas por tipo de transação
    )

# Funções fábrica para criar objetos Transacao como receitas ou despesas
def Receita(**kwargs):
    """
    Função fábrica para criar objetos Transacao como receitas.
    Mapeia as propriedades esperadas para uma receita para os campos da Transacao.
    """
    transacao_kwargs = {}
    
    # Mapeamento de campos
    if 'cliente_id' in kwargs:
        transacao_kwargs['origem_id'] = kwargs['cliente_id']
        transacao_kwargs['origem_tipo'] = 'cliente'
    
    if 'data_vencimento' in kwargs:
        transacao_kwargs['data'] = kwargs['data_vencimento']
    
    # Copiar campos que existem diretamente em Transacao
    for field in ['tipo_receita', 'categoria', 'descricao', 'valor', 'status', 
                  'proposta_id', 'data_recebimento', 'usuario_id']:
        if field in kwargs:
            transacao_kwargs[field] = kwargs[field]
    
    # Definir sempre como receita
    transacao_kwargs['tipo'] = 'receita'
    
    # Criar e retornar a transação
    return Transacao(**transacao_kwargs)

def Despesa(**kwargs):
    """
    Função fábrica para criar objetos Transacao como despesas.
    Mapeia as propriedades esperadas para uma despesa para os campos da Transacao.
    """
    transacao_kwargs = {}
    
    # Mapeamento de campos
    if 'fornecedor_id' in kwargs:
        transacao_kwargs['origem_id'] = kwargs['fornecedor_id']
        transacao_kwargs['origem_tipo'] = 'fornecedor'
    
    if 'data_vencimento' in kwargs:
        transacao_kwargs['data'] = kwargs['data_vencimento']
    
    # Copiar campos que existem diretamente em Transacao
    for field in ['categoria', 'descricao', 'valor', 'status', 
                  'proposta_id', 'data_recebimento', 'usuario_id']:
        if field in kwargs:
            transacao_kwargs[field] = kwargs[field]
    
    # Definir sempre como despesa
    transacao_kwargs['tipo'] = 'despesa'
    
    # Criar e retornar a transação
    return Transacao(**transacao_kwargs)

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
    percentual_comissao = Column(Float, nullable=True)  # Adicionado campo para percentual de comissão
    usuario_id = Column(String, nullable=True)  # Campo para isolamento multi-tenant

    proposta = relationship("Proposta", back_populates="acrescimos")

class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco_custo = Column(Float, nullable=False)
    preco_venda = Column(Float, nullable=False)
    categoria = Column(String)
    estoque = Column(Integer, default=0)
    data_cadastro = Column(Date, default=datetime.now().date())
    usuario_id = Column(String, nullable=True)  # ID do usuário proprietário do registro (multi-tenant)
    
    # Relacionamento com vendas
    vendas_itens = relationship("ItemVenda", back_populates="produto", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_produto_usuario_id', 'usuario_id'),  # Índice para otimizar filtro por usuário
    )

class Venda(Base):
    __tablename__ = 'vendas'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    proposta_id = Column(Integer, ForeignKey('propostas.id'), nullable=True)  # Referência à proposta
    data_venda = Column(Date, default=datetime.now().date())
    valor_total = Column(Float, nullable=False)
    status = Column(String, default='Concluída')  # Concluída, Cancelada, Pendente
    forma_pagamento = Column(String)
    observacoes = Column(String)
    usuario_id = Column(String, nullable=True)  # ID do usuário proprietário do registro (multi-tenant)
    
    # Relacionamentos
    cliente = relationship("Cliente")
    proposta = relationship("Proposta", back_populates="vendas")  # Relacionamento com proposta
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_venda_usuario_id', 'usuario_id'),  # Índice para otimizar filtro por usuário
    )

class ItemVenda(Base):
    __tablename__ = 'itens_venda'
    id = Column(Integer, primary_key=True)
    venda_id = Column(Integer, ForeignKey('vendas.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    descricao = Column(String(255), nullable=True)  # Campo para armazenar o nome do produto
    usuario_id = Column(String(255), nullable=True)  # Campo para multi-tenant
    
    # Relacionamentos
    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto", back_populates="vendas_itens")

# =========================================
# MÓDULO PÓS-ORGANIZAÇÃO
# =========================================

class PostOrganization(Base):
    """
    Registro de pós-organização vinculado a uma proposta finalizada.
    Gerencia ações de acompanhamento pós-serviço.
    """
    __tablename__ = 'post_organizations'
    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'), nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    data_final_projeto = Column(Date, nullable=False)
    status = Column(String, default='ATIVO')  # ATIVO, CONCLUIDO
    created_at = Column(DateTime, default=datetime.now)
    usuario_id = Column(String, nullable=True)  # Multi-tenant
    
    # Relacionamentos
    proposta = relationship("Proposta")
    cliente = relationship("Cliente")
    acoes = relationship("PostOrganizationAction", back_populates="post_organization", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_post_org_usuario_id', 'usuario_id'),
        Index('idx_post_org_proposta_id', 'proposta_id'),
        Index('idx_post_org_status', 'status'),
    )

class PostOrganizationAction(Base):
    """
    Ações individuais de pós-organização (agradecimento, acompanhamento, ajuste_fino, feedback, continuidade, retorno_tecnico)
    """
    __tablename__ = 'post_organization_actions'
    id = Column(Integer, primary_key=True)
    post_organization_id = Column(Integer, ForeignKey('post_organizations.id'), nullable=False)
    action_type = Column(String, nullable=False)  # agradecimento, acompanhamento, ajuste_fino, feedback, continuidade, retorno_tecnico
    due_date = Column(Date, nullable=False)
    status = Column(String, default='PENDENTE')  # PENDENTE, FEITO, CANCELADO
    notes = Column(String, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    usuario_id = Column(String, nullable=True)  # Multi-tenant
    ordem = Column(Integer)  # Ordem de exibição

    # Relacionamento
    post_organization = relationship("PostOrganization", back_populates="acoes")

    __table_args__ = (
        Index('idx_post_action_status', 'status'),
        Index('idx_post_action_due_date', 'due_date'),
        Index('idx_post_action_type', 'action_type'),
    )


class PostOrgTemplate(Base):
    """
    Templates de mensagem por etapa do pós-organização.
    """
    __tablename__ = 'post_org_templates'
    id = Column(Integer, primary_key=True)
    etapa = Column(String(50), nullable=False, unique=True)
    nome = Column(String(100), nullable=False)
    dias_apos = Column(Integer, nullable=False)
    emoji = Column(String(10), nullable=True)
    texto = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.now)
    gratuito = Column(Boolean, default=False)
    hint = Column(String, nullable=True)

    __table_args__ = (
        Index('idx_templates_etapa', 'etapa'),
    )
