import os
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, func, Index, text, select, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# Ensure proper SSL configuration for PostgreSQL
try:
    # Importar NullPool para evitar caching de conexões
    from sqlalchemy.pool import NullPool
    
    # Criar engine sem pool para evitar caching de conexões
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            'sslmode': 'require',
            'connect_timeout': 10
        } if 'postgresql' in DATABASE_URL else {},
        # Usar NullPool para desativar caching de conexões
        poolclass=NullPool,
        # Desativar mecanismos de caching para garantir acesso às colunas mais recentes
        isolation_level='AUTOCOMMIT'
    )
    
    # Forçar informar que estamos atualizando o esquema de metadados
    print("Iniciando motor de banco com caching desativado para resolver problemas de esquema")
except Exception as e:
    print(f"Error creating database engine: {str(e)}")
    raise

Base = declarative_base()

# Create scoped session
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)

# Função auxiliar para obter o ID do usuário da sessão do Streamlit
def get_usuario_id_from_session():
    """
    Obtém o ID do usuário atualmente autenticado no Streamlit
    
    Returns:
        str: ID do usuário autenticado ou None se não há usuário na sessão
    """
    if 'user' in st.session_state and st.session_state.user:
        # Usar o localId do Firebase como usuario_id
        if 'localId' in st.session_state.user:
            return st.session_state.user['localId']
        
        # Verificar alternativas
        if 'usuario_id' in st.session_state.user:
            return st.session_state.user['usuario_id']
            
    return None

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
    cor_principal = Column(String)
    cor_secundaria = Column(String)
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
    descricao = Column(String, nullable=False)
    contato = Column(String)
    categoria = Column(String)
    estado = Column(String)  # Novo campo
    cidade = Column(String)  # Novo campo
    bairro = Column(String)  # Novo campo
    endereco = Column(String)
    pix = Column(String)
    recorrente = Column(Boolean, default=False)
    observacoes = Column(String)
    valor = Column(Float, nullable=True)
    data_vencimento = Column(Date, nullable=True)
    data_pagamento = Column(Date, nullable=True)
    status = Column(String, nullable=True)
    tipo_conta = Column(String, default='PF')  # Adicionado campo tipo_conta
    percentual_comissao = Column(Float, default=0.0)  # Percentual de comissão para o fornecedor


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
    status_execucao = Column(String, default='Não iniciada')  # Status da execução: 'Não iniciada', 'Em execução', 'Concluída'
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
    
    # Relacionamentos
    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto", back_populates="vendas_itens")

class Database:
    def refresh_schema_metadata(self):
        """
        Força a atualização dos metadados do esquema do banco de dados.
        Isso é útil quando o cache do SQLAlchemy não reflete mudanças recentes no esquema.
        """
        try:
            # Limpar o cache de metadados
            Base.metadata.clear()
            
            # Forçar uma nova leitura do esquema
            Base.metadata.reflect(bind=engine)
            
            # Exibir informações de debug
            insp = inspect(engine)
            tables = insp.get_table_names()
            print(f"Schema atualizado. Tabelas disponíveis: {tables}")
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar schema: {str(e)}")
            return False

    def __init__(self, usuario_id=None):
        """
        Inicializa a conexão com o banco de dados e configura o contexto de usuário
        
        Args:
            usuario_id (str, optional): ID do usuário para filtrar os dados.
                                       Se None, tenta obter o ID do usuário da sessão do Streamlit.
        """
        # Forçar atualização de metadados para resolver problemas com colunas
        self.refresh_schema_metadata()
        
        try:
            # Criar tabelas se não existirem
            Base.metadata.create_all(engine)
            self.session = Session()
            
            # Configurar o contexto de usuário para filtrar os dados
            if usuario_id:
                self.usuario_id = usuario_id
            else:
                # Tenta obter o ID do usuário da sessão do Streamlit
                self.usuario_id = get_usuario_id_from_session()
                
            if self.usuario_id:
                print(f"Banco de dados inicializado para o usuário: {self.usuario_id}")
            else:
                print("Banco de dados inicializado sem contexto de usuário")
                
            # Verificar e criar perfil do usuário se necessário
            if self.usuario_id and 'user' in st.session_state:
                self._ensure_user_profile()
                
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            raise e
            
    def _ensure_user_profile(self):
        """
        Garante que o perfil do usuário existe no banco de dados
        Cria um novo perfil se não existir
        """
        try:
            # Verificar se o perfil já existe
            perfil = self.session.query(Perfil).filter_by(usuario_id=self.usuario_id).first()
            
            if not perfil and 'user' in st.session_state:
                # Criar novo perfil com os dados disponíveis na sessão
                user_data = st.session_state.user
                
                nome = user_data.get('nome') or user_data.get('name') or 'Usuário'
                email = user_data.get('email') or 'sem-email'
                empresa = user_data.get('empresa') or 'Planner Organizer'
                telefone = user_data.get('telefone') or ''
                
                novo_perfil = Perfil(
                    usuario_id=self.usuario_id,
                    email=email,
                    nome=nome,
                    telefone=telefone,
                    empresa=empresa,
                    ultimo_login=datetime.now()
                )
                
                self.session.add(novo_perfil)
                self.session.commit()
                print(f"Perfil criado para usuário: {self.usuario_id}")
        except Exception as e:
            print(f"Erro ao verificar/criar perfil: {str(e)}")
            self.session.rollback()
            
    def create_perfil(self, usuario_id, email, nome, telefone=None, empresa=None, 
                     instagram=None, website=None, cor_principal=None, cor_secundaria=None, 
                     role="user", plano="gratuito"):
        """
        Cria um novo perfil de usuário no banco de dados PostgreSQL
        
        Args:
            usuario_id (str): ID do usuário no Firebase Auth (UID)
            email (str): Email do usuário
            nome (str): Nome do usuário
            telefone (str, optional): Telefone do usuário
            empresa (str, optional): Empresa do usuário
            instagram (str, optional): Instagram do usuário
            website (str, optional): Website do usuário
            cor_principal (str, optional): Cor principal do tema
            cor_secundaria (str, optional): Cor secundária do tema
            role (str, optional): Papel do usuário (padrão: "user")
            plano (str, optional): Plano do usuário (padrão: "gratuito")
            
        Returns:
            bool: True se o perfil foi criado com sucesso, False em caso de erro
        """
        def query():
            try:
                # Verificar se já existe um perfil com este usuario_id
                perfil_existente = self.session.query(Perfil).filter_by(usuario_id=usuario_id).first()
                if perfil_existente:
                    print(f"Perfil já existe para o usuário ID: {usuario_id}")
                    
                    # Atualizar último login
                    perfil_existente.ultimo_login = datetime.now()
                    self.session.commit()
                    
                    return True
                
                # Verificar se já existe um perfil com este email
                perfil_email = self.session.query(Perfil).filter_by(email=email).first()
                if perfil_email:
                    print(f"Já existe um perfil com o email: {email}")
                    
                    # Se o perfil existente tem um usuario_id diferente, podemos ter um problema
                    # de duplicação ou de migração de conta
                    if perfil_email.usuario_id != usuario_id:
                        print(f"AVISO: Email já cadastrado com outro ID de usuário.")
                        print(f"  - Atual: {usuario_id}")
                        print(f"  - Existente: {perfil_email.usuario_id}")
                    
                    # Atualizar último login de qualquer forma
                    perfil_email.ultimo_login = datetime.now()
                    self.session.commit()
                    
                    return True
                
                # Criar novo perfil
                novo_perfil = Perfil(
                    usuario_id=usuario_id,
                    email=email,
                    nome=nome,
                    telefone=telefone or "",
                    empresa=empresa or "Planner Organizer",
                    instagram=instagram,
                    website=website,
                    cor_principal=cor_principal,
                    cor_secundaria=cor_secundaria,
                    role=role,
                    plano=plano,
                    data_cadastro=datetime.now().date(),
                    ultimo_login=datetime.now(),
                    ativo=True
                )
                
                self.session.add(novo_perfil)
                self.session.commit()
                
                print(f"Perfil criado com sucesso para: {email} (ID: {usuario_id})")
                return True
                
            except Exception as e:
                print(f"Erro ao criar perfil: {str(e)}")
                self.session.rollback()
                return False
                
        return self._safe_query(query)
        
    def get_perfil_by_email(self, email):
        """
        Busca um perfil de usuário pelo email
        
        Args:
            email (str): Email do usuário
            
        Returns:
            dict: Dicionário com os dados do perfil ou None se não encontrado
        """
        def query():
            try:
                perfil = self.session.query(Perfil).filter_by(email=email).first()
                
                if not perfil:
                    print(f"Perfil não encontrado para o email: {email}")
                    return None
                
                # Converter objeto para dicionário para facilitar uso
                perfil_dict = {
                    'id': perfil.id,
                    'usuario_id': perfil.usuario_id,
                    'email': perfil.email,
                    'nome': perfil.nome,
                    'telefone': perfil.telefone,
                    'empresa': perfil.empresa,
                    'instagram': perfil.instagram,
                    'website': perfil.website,
                    'cor_principal': perfil.cor_principal,
                    'cor_secundaria': perfil.cor_secundaria,
                    'role': perfil.role,
                    'plano': perfil.plano,
                    'data_cadastro': perfil.data_cadastro,
                    'ultimo_login': perfil.ultimo_login,
                    'ativo': perfil.ativo
                }
                
                return perfil_dict
                
            except Exception as e:
                print(f"Erro ao buscar perfil por email: {str(e)}")
                return None
                
        return self._safe_query(query)

    def _safe_query(self, query_func):
        """
        Wrapper para executar queries com tratamento de erro
        
        Esta função garante que as operações no banco de dados sejam executadas
        em uma transação segura, com tratamento adequado de erros e conversão de tipos.
        """
        # Verificar se já existe uma transação em andamento
        nested_transaction = False
        in_transaction = False
        
        try:
            # Verificar o estado da sessão e recuperar de estados errôneos
            try:
                # Verificar se tem uma sessão em estado problemático
                session_state = str(getattr(self.session.transaction, '_state', ''))
                if 'PREPARE' in session_state or 'FINISHED' in session_state:
                    # # print(f"DEBUG: Detectado estado problemático na sessão: {session_state}")
                    try:
                        self.session.close()
                    except:
                        pass
                    self.session = Session()
                    # Removido log de debug sobre recriação de sessão
                elif not self.session.is_active:
                    self.session = Session()
                    # Removido log de debug sobre criação de nova sessão
            except Exception as session_check_error:
                # # print(f"DEBUG: Erro ao verificar estado da sessão: {str(session_check_error)}")
                try:
                    self.session.close()
                except:
                    pass
                self.session = Session()
                # Removido log de debug sobre criação de nova sessão
                
            # Verificar se já existe uma transação
            try:
                in_transaction = self.session.in_transaction()
                if in_transaction:
                    nested_transaction = True
                    # print("DEBUG: Transação aninhada detectada, não será feito commit automático")
            except Exception as tx_error:
                # print(f"DEBUG: Erro ao verificar transação: {str(tx_error)}")
                # Se não conseguirmos verificar, consideramos que não está em transação
                pass
            
            # Executar a função de query
            # print("DEBUG: Executando query")
            result = query_func()
            
            # Commit da transação somente se não for aninhada
            if not nested_transaction:
                try:
                    # Removido log de debug sobre commit
                    self.session.commit()
                    # Removido log de debug sobre sucesso do commit
                except Exception as commit_error:
                    # Removido log de debug sobre erro de commit
                    # Tentar rollback em caso de erro de commit
                    try:
                        self.session.rollback()
                        # Removido log de debug sobre rollback
                    except:
                        pass
                    # Criar nova sessão se necessário
                    try:
                        self.session.close()
                    except:
                        pass
                    self.session = Session()
                    # Removido log de debug sobre nova sessão

            # Se o resultado for um DataFrame, converter tipos numéricos
            if isinstance(result, pd.DataFrame):
                # Converter colunas numéricas para tipos nativos Python
                for col in result.select_dtypes(include=['int64', 'float64', 'Int64']).columns:
                    result[col] = result[col].astype(object).where(pd.notnull(result[col]), None)
                # # print(f"DEBUG: DataFrame processado com {len(result)} registros")

            # Se o resultado for um número, garantir que seja tipo nativo Python
            elif isinstance(result, (np.int64, np.float64)):
                result = result.item()
                # # print(f"DEBUG: Valor numérico convertido: {result}")
            
            # Removido log de debug sobre sessão ativa
            return result
            
        except Exception as e:
            # Em caso de erro, fazer rollback
            # Removido log de debug sobre erro
            
            # Sempre tentar rollback para recuperar a sessão
            try:
                if self.session.is_active:
                    # Removido log de debug sobre rollback
                    self.session.rollback()
                    # Removido log de debug sobre sucesso do rollback
            except Exception as rollback_error:
                # Removido log de debug sobre falha no rollback
                # Em caso de falha no rollback, criar nova sessão
                try:
                    self.session.close()
                except:
                    pass
                self.session = Session()
                # Removido log de debug sobre nova sessão
            
            # Logar e re-levantar a exceção com mais informações
            import traceback
            traceback.print_exc()
            
            # Re-lançar a exceção com mais contexto
            raise Exception(f"Erro ao executar operação no banco de dados: {str(e)}")
            
        finally:
            # A sessão só será fechada se close_session=True
            # mas continuará utilizável para futuras transações
            # evitando o erro "Object has been detached or deleted"
            pass  # Manter sessão ativa para futuras transações
            
    def get_clientes(self):
        """
        Retorna todos os clientes do usuário atual
        """
        def query():
            # Aplicar filtro por usuário se disponível
            query = self.session.query(Cliente)
            
            if self.usuario_id:
                query = query.filter(Cliente.usuario_id == self.usuario_id)
                
            clientes = query.all()
            
            return pd.DataFrame([{
                'id': c.id,
                'nome': c.nome,
                'email': c.email,
                'telefone': c.telefone,
                'estado': c.estado,
                'cidade': c.cidade,
                'bairro': c.bairro,
                'endereco': c.endereco,
                'cpf': c.cpf,
                'data_aniversario': c.data_aniversario,
                'origem_cliente': c.origem_cliente,
                'data_cadastro': c.data_cadastro,
                'observacoes': c.observacoes,
                'usuario_id': c.usuario_id
            } for c in clientes])
        return self._safe_query(query)
        
    def get_cliente_by_id(self, cliente_id):
        """
        Busca um cliente pelo ID
        
        Args:
            cliente_id: ID do cliente
            
        Returns:
            DataFrame com os dados do cliente ou DataFrame vazio se não encontrado
        """
        def query():
            try:
                # Converter para int nativo do Python
                cliente_id_int = int(cliente_id) if cliente_id is not None else None
                
                if cliente_id_int is None:
                    print("ERRO: ID do cliente é None")
                    return pd.DataFrame()
                
                # Configurar a consulta básica
                query = self.session.query(Cliente).filter_by(id=cliente_id_int)
                
                # Adicionar filtro por usuário se disponível
                if self.usuario_id:
                    query = query.filter(Cliente.usuario_id == self.usuario_id)
                
                # Buscar cliente pelo ID e filtros adicionais
                cliente = query.first()
                
                if not cliente:
                    print(f"AVISO: Cliente ID={cliente_id_int} não encontrado")
                    return pd.DataFrame()
                
                # Retornar como DataFrame
                return pd.DataFrame([{
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'estado': cliente.estado,
                    'cidade': cliente.cidade,
                    'bairro': cliente.bairro,
                    'endereco': cliente.endereco,
                    'cpf': cliente.cpf,
                    'data_aniversario': cliente.data_aniversario,
                    'origem_cliente': cliente.origem_cliente,
                    'data_cadastro': cliente.data_cadastro,
                    'observacoes': cliente.observacoes,
                    'usuario_id': cliente.usuario_id
                }])
            except Exception as e:
                print(f"ERRO ao buscar cliente por ID: {str(e)}")
                return pd.DataFrame()
        
        return self._safe_query(query)
        
    def limpar_clientes(self):
        """Remove todos os registros da tabela de clientes"""
        def query():
            # Verifique se existem propostas vinculadas aos clientes
            propostas_count = self.session.query(func.count()).select_from(Proposta).scalar()
            
            if propostas_count > 0:
                # Primeiro limpar as propostas, já que elas têm foreign key para clientes
                # Remover acréscimos de propostas
                self.session.query(AcrescimoProposta).delete()
                
                # Remover produtos associados às propostas
                for prod_org in self.session.query(ProdutoOrganizador).all():
                    # Remover fornecedores de produtos
                    self.session.query(ProdutoFornecedor).filter(
                        ProdutoFornecedor.produto_id == prod_org.id
                    ).delete()
                
                # Agora é seguro remover os produtos
                self.session.query(ProdutoOrganizador).delete()
                
                # Remover andamentos de propostas
                self.session.query(AndamentoProposta).delete()
                
                # Remover transações financeiras vinculadas a propostas
                self.session.query(Transacao).filter(
                    Transacao.origem_tipo == 'proposta'
                ).delete()
                
                # Agora podemos remover as propostas
                self.session.query(Proposta).delete()
            
            # Remover vendas e itens de venda relacionados a clientes
            vendas = self.session.query(Venda).all()
            for venda in vendas:
                # Remover itens de venda
                self.session.query(ItemVenda).filter(
                    ItemVenda.venda_id == venda.id
                ).delete()
            
            # Remover vendas
            self.session.query(Venda).delete()
            
            # Finalmente, remover os clientes
            self.session.query(Cliente).delete()
            
            return True
        
        return self._safe_query(query)

    def add_cliente(self, nome, email=None, telefone=None, estado=None, cidade=None, bairro=None, 
                   endereco=None, cpf=None, data_aniversario=None, origem_cliente=None, observacoes=None):
        """
        Adiciona um cliente ao banco de dados
        
        Args:
            nome (str): Nome do cliente
            email (str, optional): Email do cliente
            telefone (str, optional): Telefone do cliente
            estado (str, optional): Estado (UF)
            cidade (str, optional): Cidade
            bairro (str, optional): Bairro
            endereco (str, optional): Endereço
            cpf (str, optional): CPF
            data_aniversario (str, optional): Data de aniversário
            origem_cliente (str, optional): Origem do cliente
            observacoes (str, optional): Observações
            
        Returns:
            int: ID do cliente adicionado
        """
        def query():
            # Obter o maior ID atual
            max_id = self.session.query(func.max(Cliente.id)).scalar()

            # Se não houver clientes, começar do 1
            # Se houver, usar o próximo número na sequência
            next_id = 1 if max_id is None else max_id + 1

            cliente = Cliente(
                id=next_id,  # Definir ID explicitamente
                nome=nome,
                email=email,
                telefone=telefone,
                estado=estado,
                cidade=cidade,
                bairro=bairro,
                endereco=endereco,
                cpf=cpf,
                data_aniversario=data_aniversario,
                origem_cliente=origem_cliente,
                observacoes=observacoes,
                usuario_id=self.usuario_id  # Adicionar o ID do usuário atual
            )
            self.session.add(cliente)
            return cliente.id
        return self._safe_query(query)
        
    def add_cliente_with_id(self, id, nome, email=None, telefone=None, estado=None, cidade=None, bairro=None, 
                           endereco=None, cpf=None, data_aniversario=None, origem_cliente=None, observacoes=None):
        """
        Adiciona um cliente com um ID específico (para importação)
        
        Args:
            id (int): ID específico do cliente
            nome (str): Nome do cliente
            email (str, optional): Email do cliente
            telefone (str, optional): Telefone do cliente
            estado (str, optional): Estado (UF)
            cidade (str, optional): Cidade
            bairro (str, optional): Bairro
            endereco (str, optional): Endereço
            cpf (str, optional): CPF
            data_aniversario (str, optional): Data de aniversário
            origem_cliente (str, optional): Origem do cliente
            observacoes (str, optional): Observações
            
        Returns:
            int: ID do cliente adicionado
        """
        def query():
            cliente = Cliente(
                id=id,  # Usar o ID especificado
                nome=nome,
                email=email,
                telefone=telefone,
                estado=estado,
                cidade=cidade,
                bairro=bairro,
                endereco=endereco,
                cpf=cpf,
                data_aniversario=data_aniversario,
                origem_cliente=origem_cliente,
                observacoes=observacoes,
                usuario_id=self.usuario_id  # Adicionar o ID do usuário atual
            )
            self.session.add(cliente)
            return cliente.id
        return self._safe_query(query)

    def get_propostas(self):
        """
        Retorna todas as propostas do usuário atual
        """
        def query():
            try:
                # Construir consulta base
                query = self.session.query(
                    Proposta, Cliente.nome.label('cliente_nome')
                ).outerjoin(
                    Cliente, Proposta.cliente_id == Cliente.id
                )
                
                # Adicionar filtro por usuário se disponível
                if self.usuario_id:
                    query = query.filter(Proposta.usuario_id == self.usuario_id)
                
                # Executar consulta
                propostas_com_clientes = query.all()
                
                result = []
                for p, cliente_nome in propostas_com_clientes:
                    try:
                        # Conversão robusta para tipos numéricos
                        try:
                            proposta_id = int(p.id) if p.id is not None else None
                        except (ValueError, TypeError):
                            print(f"Erro ao converter ID para int: {p.id}")
                            proposta_id = None
                            
                        try:
                            proposta_numero = int(p.numero) if p.numero is not None else None
                        except (ValueError, TypeError):
                            print(f"Erro ao converter numero para int: {p.numero}")
                            proposta_numero = None
                            
                        try:
                            cliente_id = int(p.cliente_id) if p.cliente_id is not None else None
                        except (ValueError, TypeError):
                            print(f"Erro ao converter cliente_id para int: {p.cliente_id}")
                            cliente_id = None
                            
                        try:
                            valor = float(p.valor) if p.valor is not None else 0.0
                        except (ValueError, TypeError):
                            print(f"Erro ao converter valor para float: {p.valor}")
                            valor = 0.0
                            
                        try:
                            previsao_dias = int(p.previsao_dias) if p.previsao_dias is not None else None
                        except (ValueError, TypeError):
                            print(f"Erro ao converter previsao_dias para int: {p.previsao_dias}")
                            previsao_dias = None
                        
                        # Garantir que todos os valores sejam do tipo correto
                        proposta_dict = {
                            'id': proposta_id,
                            'numero': proposta_numero,
                            'cliente_id': cliente_id,
                            'descricao': str(p.descricao) if p.descricao is not None else "",
                            'valor': valor,
                            'status': str(p.status) if p.status is not None else "",
                            'tipo_proposta': str(p.tipo_proposta) if p.tipo_proposta is not None else "",
                            'data_inicio': p.data_inicio,
                            'data_fim': p.data_fim,
                            'prazo_entrega': p.prazo_entrega,
                            'data_proposta': p.data_proposta,
                            'data_aprovacao': p.data_aprovacao,
                            'status_pagamento_base': str(p.status_pagamento_base) if p.status_pagamento_base is not None else "",
                            'previsao_dias': previsao_dias,
                            'data_inicio_execucao': p.data_inicio_execucao,
                            'status_execucao': str(p.status_execucao) if p.status_execucao is not None else "",
                            'cliente_nome': str(cliente_nome) if cliente_nome is not None else "",
                            'usuario_id': p.usuario_id
                        }
                        result.append(proposta_dict)
                    except Exception as e:
                        # Logar erro para depuração mas continuar processando outras propostas
                        print(f"Erro ao processar proposta {getattr(p, 'id', 'desconhecido')}: {str(e)}")
                
                df = pd.DataFrame(result)
                # Converter explicitamente as colunas numéricas para seus tipos corretos
                if not df.empty:
                    numeric_cols = ['id', 'numero', 'cliente_id', 'valor', 'previsao_dias']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
            except Exception as e:
                print(f"Erro ao recuperar propostas: {str(e)}")
                # Retornar DataFrame vazio em caso de erro
                return pd.DataFrame()
        
        return self._safe_query(query)

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, 
                    data_inicio=None, data_fim=None, prazo_entrega=None, previsao_dias=None, 
                    gerar_transacoes_automaticas=True):
        """
        VERSÃO MODIFICADA PARA EVITAR PROBLEMAS DE ESCOPO
        Função para adicionar proposta ao banco de dados
        
        Os parâmetros são renomeados para evitar conflitos de escopo
        """
        # Verificações mais robustas dos valores antes de convertê-los
        if cliente_id is None:
            raise ValueError("Cliente ID não pode ser nulo")
            
        if valor is None:
            raise ValueError("Valor da proposta não pode ser nulo")
            
        try:
            # Salvar valores em variáveis com nomes diferentes para evitar colisão
            cliente_id_local = int(cliente_id)
            descricao_local = descricao
            valor_local = float(valor)
            status_local = status
            tipo_proposta_local = tipo_proposta
            
            # Para datas, vamos garantir que não sejam None antes de usar
            data_inicio_local = data_inicio if data_inicio is not None else None
            data_fim_local = data_fim if data_fim is not None else None
            prazo_entrega_local = prazo_entrega if prazo_entrega is not None else None
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erro ao converter valores: {str(e)}")
        
        def query():
            # Gerar próximo número de proposta igual ao ID (criar com ID=1 se for a primeira proposta)
            ultimo_id = self.session.query(func.max(Proposta.id)).scalar()
            proximo_id = 1 if ultimo_id is None else int(ultimo_id) + 1

            # Criar dicionário com valores para a proposta
            proposta_data = {
                'numero': proximo_id,  # Usar o mesmo valor do ID como número
                'cliente_id': cliente_id_local,
                'descricao': descricao_local,
                'valor': valor_local,
                'status': status_local,
                'usuario_id': self.usuario_id,  # Adicionar o ID do usuário atual
            }
            
            # Adicionar valores opcionais apenas se não forem None
            if tipo_proposta_local is not None:
                proposta_data['tipo_proposta'] = tipo_proposta_local
            if data_inicio_local is not None:
                proposta_data['data_inicio'] = data_inicio_local
                # Usar a data de início como data da proposta quando disponível
                proposta_data['data_proposta'] = data_inicio_local
            if data_fim_local is not None:
                proposta_data['data_fim'] = data_fim_local
            if prazo_entrega_local is not None:
                proposta_data['prazo_entrega'] = prazo_entrega_local
                
            # Criar a proposta com os valores filtrados
            proposta = Proposta(**proposta_data)
            self.session.add(proposta)
            
            # Garantir que temos um ID válido
            self.session.flush()
            proposta_id = int(proposta.id) if proposta.id is not None else 0
            
            # Gerar transações financeiras automaticamente se a proposta for criada com status "Aprovada"
            if status_local == "Aprovada" and gerar_transacoes_automaticas and proposta_id > 0:
                try:
                    # Buscar o cliente da proposta
                    cliente = self.session.query(Cliente).filter_by(id=cliente_id_local).first()
                    if cliente:
                        # Criar transação de receita
                        if valor_local > 0:
                            self._criar_transacao_receita(proposta, cliente)
                except Exception as e:
                    print(f"Erro ao gerar transações automáticas para a proposta {proposta_id}: {str(e)}")
            
            return proposta_id
        
        return self._safe_query(query)

    def get_financeiro(self, include_all=True, categorias=None, limit=1000):
        """
        Retorna os dados financeiros (transações) do usuário atual
        
        Args:
            include_all (bool): Se True, inclui todas as transações. Se False, inclui apenas transações pendentes
            categorias (list): Lista de categorias para filtrar
            limit (int): Limite de registros a serem retornados
        
        Returns:
            DataFrame: DataFrame com as transações
        """
        def query():
            # Criar query base
            query = self.session.query(Transacao)
            
            # Aplicar filtro por usuário se disponível
            if self.usuario_id:
                query = query.filter(Transacao.usuario_id == self.usuario_id)
            
            # Aplicar filtros se necessário
            if not include_all:
                query = query.filter(Transacao.status == 'Pendente')
                
            if categorias:
                query = query.filter(Transacao.categoria.in_(categorias))
            
            # Ordenar e limitar
            transacoes = query.order_by(Transacao.data.desc()).limit(limit).all()
            
            # Converter para DataFrame
            df = pd.DataFrame([{
                'id': t.id,
                'tipo': t.tipo,
                'descricao': t.descricao,
                'valor': float(t.valor) if hasattr(t, 'valor') and t.valor is not None else 0.0,
                'data': t.data,
                'categoria': t.categoria,
                'subcategoria': t.subcategoria,
                'tipo_receita': t.tipo_receita,
                'origem_id': t.origem_id,
                'origem_tipo': t.origem_tipo,
                'tipo_conta': t.tipo_conta,
                'status': t.status,
                'data_recebimento': t.data_recebimento,
                'proposta_id': t.proposta_id,
                'classificacao': t.classificacao,
                # Campos calculados para facilitar a análise
                'receita': float(t.valor) if t.tipo in ['receita', 'receita_a_receber'] else 0.0,
                'despesa': float(t.valor) if t.tipo == 'despesa' else 0.0,
                'usuario_id': t.usuario_id
            } for t in transacoes])
            
            return df
        return self._safe_query(query)

    def add_transacao(self, tipo, descricao, valor, categoria, tipo_receita=None, 
                     origem_id=None, origem_tipo=None, tipo_conta='PF', status='Pendente',
                     proposta_id=None, subcategoria=None, classificacao=None, usuario_id=None):
        """
        Adiciona uma transação financeira
        
        Args:
            tipo (str): Tipo da transação (receita, despesa, receita_a_receber)
            descricao (str): Descrição da transação
            valor (float): Valor da transação
            categoria (str): Categoria da transação
            tipo_receita (str, optional): Tipo de receita (para receitas)
            origem_id (int, optional): ID da origem da transação (cliente, fornecedor, etc.)
            origem_tipo (str, optional): Tipo da origem (cliente, fornecedor, proposta, etc.)
            tipo_conta (str, optional): Tipo de conta (PF, PJ)
            status (str, optional): Status da transação (Pendente, Recebido, Cancelado)
            proposta_id (int, optional): ID da proposta relacionada
            subcategoria (str, optional): Subcategoria da transação
            classificacao (str, optional): Classificação contábil
            usuario_id (str, optional): ID do usuário proprietário da transação (para multi-tenant)
            
        Returns:
            int: ID da transação adicionada
        """
        def query():
            transacao = Transacao(
                tipo=tipo,
                descricao=descricao,
                valor=valor,
                categoria=categoria,
                subcategoria=subcategoria,
                tipo_receita=tipo_receita,
                origem_id=origem_id,
                origem_tipo=origem_tipo,
                tipo_conta=tipo_conta,
                status=status,
                proposta_id=proposta_id,
                classificacao=classificacao,
                usuario_id=self.usuario_id  # Adicionar o ID do usuário atual
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

    def update_transacao(self, transacao_id, tipo, descricao, valor, categoria, tipo_receita=None,
                      subcategoria=None, classificacao=None, proposta_id=None):
        """Atualiza uma transação existente"""
        def query():
            transacao = self.session.query(Transacao).filter_by(id=transacao_id).first()
            if transacao:
                transacao.tipo = tipo
                transacao.descricao = descricao
                transacao.valor = valor
                transacao.categoria = categoria
                transacao.tipo_receita = tipo_receita
                
                if subcategoria is not None:
                    transacao.subcategoria = subcategoria
                    
                if classificacao is not None:
                    transacao.classificacao = classificacao
                    
                if proposta_id is not None:
                    transacao.proposta_id = proposta_id
                    
                return True
            return False
        return self._safe_query(query)
        
    def gerar_transacoes_proposta(self, proposta_id):
        """
        Gera transações financeiras a partir de uma proposta
        - Cria uma transação de receita com base no valor da proposta
        - Cria transações de despesa para cada acréscimo da proposta
        
        Args:
            proposta_id: ID da proposta
            
        Returns:
            dict: Dicionário com os IDs das transações criadas
        """
        def query():
            try:
                # Garantir que proposta_id seja um inteiro
                try:
                    proposta_id_int = int(proposta_id)
                except (ValueError, TypeError):
                    raise ValueError(f"ID de proposta inválido: {proposta_id}")
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    raise ValueError(f"Proposta ID {proposta_id_int} não encontrada")
                
                # Garantir que cliente_id seja um inteiro
                try:
                    cliente_id_int = int(proposta.cliente_id) if proposta.cliente_id is not None else None
                except (ValueError, TypeError):
                    raise ValueError(f"ID de cliente inválido: {proposta.cliente_id}")
                
                if cliente_id_int is None:
                    raise ValueError("Cliente ID não pode ser nulo")
                
                # Buscar o cliente da proposta
                cliente = self.session.query(Cliente).filter_by(id=cliente_id_int).first()
                if not cliente:
                    raise ValueError(f"Cliente ID {cliente_id_int} não encontrado")
                
                # Verificar se já existem transações para esta proposta
                transacoes_existentes = self.session.query(Transacao).filter_by(
                    proposta_id=proposta_id_int
                ).count()
                
                if transacoes_existentes > 0:
                    # Já existem transações, não criar novamente
                    return {"status": "já existem transações", "count": transacoes_existentes}
                
                # Garantir que valor seja um float
                try:
                    valor = float(proposta.valor) if proposta.valor is not None else 0.0
                except (ValueError, TypeError):
                    print(f"Erro ao converter valor para float: {proposta.valor}, usando 0.0")
                    valor = 0.0
                
                # Criar transação de receita
                receita_id = None
                if valor > 0:
                    receita_id = self._criar_transacao_receita(proposta, cliente)
                
                # Buscar acréscimos da proposta
                acrescimos = self.session.query(AcrescimoProposta).filter_by(proposta_id=proposta_id_int).all()
                
                # Criar transações de despesa para cada acréscimo
                despesa_ids = []
                for acrescimo in acrescimos:
                    try:
                        acrescimo_valor = float(acrescimo.valor) if acrescimo.valor is not None else 0.0
                    except (ValueError, TypeError):
                        print(f"Erro ao converter valor do acréscimo para float: {acrescimo.valor}, usando 0.0")
                        acrescimo_valor = 0.0
                    
                    if acrescimo_valor > 0:
                        despesa_id = self._criar_transacao_despesa(acrescimo, proposta)
                        despesa_ids.append(despesa_id)
                
                return {
                    "status": "sucesso",
                    "receita_id": receita_id,
                    "despesa_ids": despesa_ids,
                    "total_despesas": len(despesa_ids)
                }
            except Exception as e:
                print(f"Erro ao gerar transações para proposta {proposta_id}: {str(e)}")
                raise
        
        return self._safe_query(query)
    
    def _criar_transacao_receita(self, proposta, cliente):
        """Cria uma transação de receita para a proposta"""
        try:
            # Nome do cliente para a descrição da transação
            nome_cliente = str(cliente.nome) if cliente and hasattr(cliente, 'nome') else "Cliente"
            
            # Garantir conversão correta de tipos
            try:
                proposta_id = int(proposta.id) if proposta.id is not None else 0
            except (ValueError, TypeError):
                print(f"Erro ao converter ID da proposta para int: {proposta.id}")
                proposta_id = 0
                
            try:
                valor = float(proposta.valor) if proposta.valor is not None else 0.0
            except (ValueError, TypeError):
                print(f"Erro ao converter valor para float: {proposta.valor}")
                valor = 0.0
                
            # Garantir que temos uma descrição válida
            descricao = str(proposta.descricao) if proposta.descricao is not None else "Sem descrição"
            
            # Garantir que temos um tipo de proposta válido
            tipo_proposta = str(proposta.tipo_proposta) if proposta.tipo_proposta is not None else "Geral"
            
            # Data da proposta ou data atual
            data_proposta = proposta.data_proposta if hasattr(proposta, 'data_proposta') and proposta.data_proposta is not None else datetime.now().date()
            
            # Obter usuario_id da proposta para garantir isolamento de dados
            usuario_id = proposta.usuario_id if hasattr(proposta, 'usuario_id') else None
            
            transacao = Transacao(
                tipo="receita_a_receber",
                descricao=f"Proposta #{proposta_id} - {descricao} - {nome_cliente}",
                valor=valor,
                categoria="Receita - serviços de organização",  # Alterado para exatamente "Receita - serviços de organização"
                subcategoria=tipo_proposta,
                tipo_receita="Projeto",
                origem_id=proposta_id,
                origem_tipo="proposta",
                tipo_conta="PF",
                status="Pendente",
                proposta_id=proposta_id,
                classificacao="receita",
                data=data_proposta,
                usuario_id=usuario_id
            )
            self.session.add(transacao)
            self.session.flush()
            return transacao.id
        except Exception as e:
            print(f"Erro ao criar transação de receita: {str(e)}")
            raise
    
    def _criar_transacao_despesa(self, acrescimo, proposta):
        """Cria uma transação de despesa para um acréscimo de proposta"""
        try:
            # Garantir conversão correta de tipos
            try:
                proposta_id = int(proposta.id) if proposta.id is not None else 0
            except (ValueError, TypeError):
                print(f"Erro ao converter ID da proposta para int: {proposta.id}")
                proposta_id = 0
                
            try:
                acrescimo_id = int(acrescimo.id) if acrescimo.id is not None else 0
            except (ValueError, TypeError):
                print(f"Erro ao converter ID do acréscimo para int: {acrescimo.id}")
                acrescimo_id = 0
                
            try:
                valor = float(acrescimo.valor) if acrescimo.valor is not None else 0.0
            except (ValueError, TypeError):
                print(f"Erro ao converter valor para float: {acrescimo.valor}")
                valor = 0.0
                
            # Garantir que temos uma descrição válida
            descricao = str(acrescimo.descricao) if hasattr(acrescimo, 'descricao') and acrescimo.descricao is not None else "Despesa do projeto"
            
            # Garantir que temos um tipo de acréscimo válido
            tipo_acrescimo = str(acrescimo.tipo) if hasattr(acrescimo, 'tipo') and acrescimo.tipo is not None else "Geral"
            
            # Data do cadastro ou data atual
            data_cadastro = acrescimo.data_cadastro if hasattr(acrescimo, 'data_cadastro') and acrescimo.data_cadastro is not None else datetime.now().date()
            
            # Obter usuario_id da proposta para garantir isolamento de dados
            usuario_id = proposta.usuario_id if hasattr(proposta, 'usuario_id') else None
            
            transacao = Transacao(
                tipo="despesa",
                descricao=f"Despesa: {descricao} - Proposta #{proposta_id}",
                valor=valor,
                categoria="Custos de Projeto",
                subcategoria=tipo_acrescimo,
                origem_id=acrescimo_id,
                origem_tipo="acrescimo",
                tipo_conta="PF",
                status="Pendente",
                proposta_id=proposta_id,
                classificacao="custo_direto",
                data=data_cadastro,
                usuario_id=usuario_id
            )
            self.session.add(transacao)
            self.session.flush()
            return transacao.id
        except Exception as e:
            print(f"Erro ao criar transação de despesa: {str(e)}")
            raise

    def delete_transacao(self, transacao_id):
        """Exclui uma transação"""
        def query():
            transacao = self.session.query(Transacao).filter_by(id=transacao_id).first()
            if transacao:
                self.session.delete(transacao)
                return True
            return False
        return self._safe_query(query)

    def get_contas_receber(self):
        def query():
            # Atualizado para incluir transações do tipo Receita com status Pendente
            query = self.session.query(Transacao).filter(
                (
                    # Todos os lançamentos com classificação contas_a_receber
                    (Transacao.classificacao == 'contas_a_receber') |
                    # Todos os lançamentos do tipo Receita com status Pendente
                    ((Transacao.tipo == 'Receita') & (Transacao.status == 'Pendente')) |
                    # Manter compatibilidade com tipos antigos
                    (Transacao.tipo == 'receita_a_receber')
                )
            )
            
            # Aplicar filtro por usuário se disponível (multi-tenant)
            if self.usuario_id:
                query = query.filter(Transacao.usuario_id == self.usuario_id)
                
            # Ordenar e obter resultados
            contas = query.order_by(Transacao.data.desc()).all()

            return pd.DataFrame([{
                'id': t.id,
                'descricao': t.descricao,
                'valor': t.valor,
                'data': t.data,
                'categoria': t.categoria,
                'subcategoria': t.subcategoria,
                'tipo_receita': t.tipo_receita,
                'origem_tipo': t.origem_tipo,
                'tipo_conta': t.tipo_conta,
                'status': t.status,
                'data_recebimento': t.data_recebimento,
                'proposta_id': t.proposta_id,
                'classificacao': t.classificacao
            } for t in contas])
        return self._safe_query(query)

    def add_fornecedor(self, descricao, contato, categoria, estado=None, cidade=None, 
                  bairro=None, endereco=None, pix=None, recorrente=False, observacoes=None, 
                  valor=None, data_vencimento=None, data_pagamento=None, status=None, tipo_conta='PF',
                  percentual_comissao=0.0):
        def query():
            fornecedor = Fornecedor(
                descricao=descricao,
                contato=contato,
                categoria=categoria,
                estado=estado,
                cidade=cidade,
                bairro=bairro,
                endereco=endereco,
                pix=pix,
                recorrente=recorrente,
                observacoes=observacoes,
                valor=valor,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                status=status,
                tipo_conta=tipo_conta,
                percentual_comissao=percentual_comissao
            )
            self.session.add(fornecedor)
            return fornecedor.id
        return self._safe_query(query)

    def update_fornecedor(self, fornecedor_id, descricao=None, contato=None, categoria=None, 
                        estado=None, cidade=None, bairro=None, endereco=None, pix=None, 
                        recorrente=None, observacoes=None, valor=None, data_vencimento=None, 
                        data_pagamento=None, status=None, tipo_conta=None, percentual_comissao=None):
        """
        Atualiza os dados de um fornecedor existente.
        
        Args:
            fornecedor_id: ID do fornecedor a ser atualizado
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        def query():
            # Buscar o fornecedor pelo ID
            fornecedor = self.session.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
            
            if not fornecedor:
                raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrado")
            
            # Atualizar campos se fornecidos
            if descricao is not None:
                fornecedor.descricao = descricao
            if contato is not None:
                fornecedor.contato = contato
            if categoria is not None:
                fornecedor.categoria = categoria
            if estado is not None:
                fornecedor.estado = estado
            if cidade is not None:
                fornecedor.cidade = cidade
            if bairro is not None:
                fornecedor.bairro = bairro
            if endereco is not None:
                fornecedor.endereco = endereco
            if pix is not None:
                fornecedor.pix = pix
            if recorrente is not None:
                fornecedor.recorrente = recorrente
            if observacoes is not None:
                fornecedor.observacoes = observacoes
            if valor is not None:
                fornecedor.valor = valor
            if data_vencimento is not None:
                fornecedor.data_vencimento = data_vencimento
            if data_pagamento is not None:
                fornecedor.data_pagamento = data_pagamento
            if status is not None:
                fornecedor.status = status
            if tipo_conta is not None:
                fornecedor.tipo_conta = tipo_conta
            if percentual_comissao is not None:
                fornecedor.percentual_comissao = percentual_comissao
                
            return True
            
        return self._safe_query(query)
        
    def update_parceiro(self, parceiro_id, nome=None, telefone=None, area_atuacao=None, 
                       tipo_parceria=None, estado=None, cidade=None, bairro=None, 
                       endereco=None, pix=None, observacoes=None):
        """
        Atualiza os dados de um parceiro existente.
        
        Args:
            parceiro_id: ID do parceiro a ser atualizado
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        def query():
            # Buscar o parceiro pelo ID
            parceiro = self.session.query(Parceiro).filter(Parceiro.id == parceiro_id).first()
            
            if not parceiro:
                raise ValueError(f"Parceiro com ID {parceiro_id} não encontrado")
            
            # Atualizar campos se fornecidos
            if nome is not None:
                parceiro.nome = nome
            if telefone is not None:
                parceiro.telefone = telefone
            if area_atuacao is not None:
                parceiro.area_atuacao = area_atuacao
            if tipo_parceria is not None:
                parceiro.tipo_parceria = tipo_parceria
            if estado is not None:
                parceiro.estado = estado
            if cidade is not None:
                parceiro.cidade = cidade
            if bairro is not None:
                parceiro.bairro = bairro
            if endereco is not None:
                parceiro.endereco = endereco
            if pix is not None:
                parceiro.pix = pix
            if observacoes is not None:
                parceiro.observacoes = observacoes
                
            return True
            
        return self._safe_query(query)
        
    def update_assistente(self, assistente_id, nome=None, telefone=None, endereco=None,
                          disponibilidade=None, pix=None, observacoes=None):
        """
        Atualiza os dados de um assistente existente.
        
        Args:
            assistente_id: ID do assistente a ser atualizado
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        def query():
            # Buscar o assistente pelo ID
            assistente = self.session.query(Assistente).filter(Assistente.id == assistente_id).first()
            
            if not assistente:
                raise ValueError(f"Assistente com ID {assistente_id} não encontrado")
            
            # Atualizar campos se fornecidos
            if nome is not None:
                assistente.nome = nome
            if telefone is not None:
                assistente.telefone = telefone
            if endereco is not None:
                assistente.endereco = endereco
            if disponibilidade is not None:
                assistente.disponibilidade = disponibilidade
            if pix is not None:
                assistente.pix = pix
            if observacoes is not None:
                assistente.observacoes = observacoes
                
            return True
            
        return self._safe_query(query)

    def get_fornecedores(self):
        def query():
            fornecedores = self.session.query(Fornecedor).all()
            return pd.DataFrame([{
                'id': f.id,
                'descricao': f.descricao,
                'contato': f.contato,
                'categoria': f.categoria,
                'estado': f.estado,
                'cidade': f.cidade,
                'bairro': f.bairro,
                'endereco': f.endereco,
                'pix': f.pix,
                'recorrente': f.recorrente,
                'observacoes': f.observacoes,
                'valor': f.valor,
                'data_vencimento': f.data_vencimento,
                'data_pagamento': f.data_pagamento,
                'status': f.status,
                'percentual_comissao': f.percentual_comissao
            } for f in fornecedores])
        return self._safe_query(query)

    def add_categoria_despesa(self, nome, descricao):
        def query():
            categoria = CategoriaDespesa(
                nome=nome,
                descricao=descricao
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
                'descricao': c.descricao
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

    def gerar_lancamentos_proposta_aprovada(self, proposta_id, forcar_geracao=False):
        """
        Gera lançamentos financeiros automáticos quando uma proposta é aprovada
        
        Gera:
        1. Receita a receber do cliente (valor base da proposta) no extrato
        2. Lançamento nas contas a receber (valor base da proposta)
        
        Args:
            proposta_id: ID da proposta aprovada
            forcar_geracao: Se True, remove lançamentos existentes e gera novos
            
        Returns:
            dict: Resumo dos lançamentos gerados
        """
        def query():
            try:
                # Converter para inteiro se for string
                proposta_id_int = int(proposta_id)
                print(f"DEBUG LANCAMENTOS APROVAÇÃO: Gerando lançamentos para proposta aprovada ID={proposta_id_int}")
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    print(f"DEBUG LANCAMENTOS APROVAÇÃO: Proposta ID {proposta_id} não encontrada")
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
                print(f"DEBUG LANCAMENTOS APROVAÇÃO: Proposta encontrada: #{proposta.numero} - {proposta.descricao}")
                
                # Buscar cliente da proposta
                cliente = self.session.query(Cliente).filter_by(id=proposta.cliente_id).first()
                if not cliente:
                    print(f"DEBUG LANCAMENTOS APROVAÇÃO: Cliente ID {proposta.cliente_id} não encontrado")
                    raise ValueError(f"Cliente ID {proposta.cliente_id} não encontrado")
                
                print(f"DEBUG LANCAMENTOS APROVAÇÃO: Cliente encontrado: {cliente.nome}")
                
                # Verificar se já existem lançamentos do tipo "receita_a_receber_aprovacao" para esta proposta
                lancamentos_existentes = self.session.query(Transacao)\
                    .filter_by(proposta_id=proposta_id_int, tipo="receita_a_receber_aprovacao")\
                    .count()
                
                print(f"DEBUG LANCAMENTOS APROVAÇÃO: Lançamentos existentes: {lancamentos_existentes}")
                
                # Se já existirem lançamentos, verificar se devemos forçar a regeneração
                if lancamentos_existentes > 0:
                    if forcar_geracao:
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO: Removendo {lancamentos_existentes} lançamentos existentes")
                        # Remover todos os lançamentos existentes relacionados à aprovação
                        # Alterado para verificar Receita em vez de receita_a_receber_aprovacao
                        self.session.query(Transacao).filter_by(
                            proposta_id=proposta_id_int, 
                            tipo="Receita"
                        ).delete()
                        
                        # Também remover as contas a receber criadas automaticamente para esta proposta
                        self.session.query(Transacao).filter_by(
                            proposta_id=proposta_id_int, 
                            tipo="contas_a_receber"
                        ).delete()
                        
                        self.session.flush()
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO: Lançamentos existentes removidos com sucesso")
                    else:
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO: Já existem lançamentos. Pulando.")
                        return {
                            "status": "já existe", 
                            "mensagem": "Lançamentos já existem para esta proposta aprovada"
                        }
                
                # Resultados para retornar
                result = {
                    "valor_base": 0,
                    "lancamentos_gerados": 0
                }
                
                # Obter dados da proposta
                valor_base = float(proposta.valor) if proposta.valor else 0
                print(f"DEBUG LANCAMENTOS APROVAÇÃO: Valor base da proposta: R$ {valor_base:.2f}")
                
                # Data dos lançamentos (usar data de aprovação se disponível, senão data atual)
                data_lancamento = proposta.data_aprovacao if proposta.data_aprovacao else datetime.now().date()
                
                # Obter usuario_id da proposta para garantir isolamento de dados
                usuario_id = proposta.usuario_id if hasattr(proposta, 'usuario_id') else None
                
                # Verificação adicional para prevenção de erros
                data_str = data_lancamento.strftime('%Y-%m-%d') if data_lancamento else datetime.now().strftime('%Y-%m-%d')
                
                if valor_base > 0:
                    # Usar SQL direto para garantir que os lançamentos sejam salvos
                    try:
                        import psycopg2
                        import os
                        
                        db_url = os.environ.get('DATABASE_URL')
                        print(f"DEBUG SQL FINANCEIRO: Conectando ao banco via psycopg2")
                        
                        conn = psycopg2.connect(db_url)
                        cursor = conn.cursor()
                        
                        # Sanitizar descrições
                        descricao_receita = f"Proposta #{proposta.numero} - {proposta.descricao[:50]}... - {cliente.nome} (Aprovação)"
                        descricao_receita = descricao_receita.replace("'", "''")
                        
                        descricao_contas_receber = f"Valor a receber - Proposta #{proposta.numero} - {cliente.nome}"
                        descricao_contas_receber = descricao_contas_receber.replace("'", "''")
                        
                        # Tipo de proposta como subcategoria (ou "Organização" como padrão)
                        subcategoria = proposta.tipo_proposta or "Organização"
                        subcategoria = subcategoria.replace("'", "''")
                        
                        # 1. Apenas o lançamento com (Aprovação)
                        sql_receita = f"""
                        INSERT INTO financeiro (
                            tipo, descricao, valor, data, categoria, subcategoria, 
                            tipo_receita, origem_id, origem_tipo, tipo_conta, 
                            status, proposta_id, classificacao, usuario_id
                        ) VALUES (
                            'Receita', 
                            '{descricao_receita}', 
                            {valor_base}, 
                            '{data_str}', 
                            'Serviços de organização', 
                            '{subcategoria}', 
                            'organização', 
                            {proposta.cliente_id}, 
                            'cliente', 
                            'PF', 
                            'Pendente', 
                            {proposta_id_int}, 
                            'receita', 
                            '{usuario_id or ''}'
                        ) RETURNING id;
                        """
                        
                        cursor.execute(sql_receita)
                        id_receita = cursor.fetchone()[0]
                        print(f"DEBUG SQL FINANCEIRO: Lançamento de receita com (Aprovação) criado com ID {id_receita}")
                        
                        # Removido o lançamento de "Valor a receber" para evitar duplicidade
                        print(f"DEBUG SQL FINANCEIRO: Não criando mais lançamento de 'Valor a receber' para evitar duplicidade")
                        
                        # 2. Lançamento de comissão sobre fornecedores (valor zero como placeholder)
                        sql_comissao = f"""
                        INSERT INTO financeiro (
                            tipo, descricao, valor, data, categoria, subcategoria, 
                            tipo_receita, origem_id, origem_tipo, tipo_conta, 
                            status, proposta_id, classificacao, usuario_id
                        ) VALUES (
                            'Receita', 
                            'Comissão de fornecedores - Proposta #{proposta.numero} - {cliente.nome}', 
                            0, 
                            '{data_str}', 
                            'Comissão sobre fornecedores', 
                            'Fornecedores', 
                            'comissao', 
                            {proposta.cliente_id}, 
                            'cliente', 
                            'PF', 
                            'Pendente', 
                            {proposta_id_int}, 
                            'receita', 
                            '{usuario_id or ''}'
                        ) RETURNING id;
                        """
                        
                        cursor.execute(sql_comissao)
                        id_comissao = cursor.fetchone()[0]
                        print(f"DEBUG SQL FINANCEIRO: Lançamento de comissão sobre fornecedores criado com ID {id_comissao}")
                        
                        # 3. Lançamento de despesa para equipe/assistentes (valor zero como placeholder)
                        sql_assistentes = f"""
                        INSERT INTO financeiro (
                            tipo, descricao, valor, data, categoria, subcategoria, 
                            origem_id, origem_tipo, tipo_conta, 
                            status, proposta_id, classificacao, usuario_id
                        ) VALUES (
                            'Despesa', 
                            'Pagamento Equipe/Assistentes - Proposta #{proposta.numero} - {cliente.nome}', 
                            0, 
                            '{data_str}', 
                            'Pagamento Equipe/Assistentes', 
                            'Assistentes', 
                            {proposta.cliente_id}, 
                            'cliente', 
                            'PF', 
                            'Pendente', 
                            {proposta_id_int}, 
                            'despesa_a_pagar', 
                            '{usuario_id or ''}'
                        ) RETURNING id;
                        """
                        
                        cursor.execute(sql_assistentes)
                        id_assistentes = cursor.fetchone()[0]
                        print(f"DEBUG SQL FINANCEIRO: Lançamento de pagamento equipe/assistentes criado com ID {id_assistentes}")
                        
                        # Garantir que tudo seja confirmado
                        conn.commit()
                        print(f"DEBUG SQL FINANCEIRO: Transação confirmada com sucesso!")
                        
                        # Fechar a conexão
                        cursor.close()
                        conn.close()
                        
                        result["valor_base"] = valor_base
                        result["lancamentos_gerados"] = 3  # Três lançamentos: receita principal, comissão e despesa
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO: Lançamentos criados com sucesso (Receita, Comissão, Despesa)")
                        
                    except Exception as sql_error:
                        print(f"ERRO EM SQL DIRETO: {str(sql_error)}")
                        import traceback
                        traceback.print_exc()
                        
                        # Em caso de falha no SQL direto, tentar o método ORM original como fallback
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO: Tentando método ORM como alternativa")
                        
                        # 1. Apenas o lançamento com (Aprovação) no método ORM
                        transacao_receita = Transacao(
                            tipo="Receita",  # Usamos tipo unificado para simplificar
                            descricao=f"Proposta #{proposta.numero} - {proposta.descricao[:50]}... - {cliente.nome} (Aprovação)",
                            valor=valor_base,
                            data=data_lancamento,
                            categoria="Serviços de organização",
                            subcategoria=proposta.tipo_proposta or "Organização",
                            tipo_receita="organização",
                            origem_id=proposta.cliente_id,
                            origem_tipo="cliente",
                            tipo_conta="PF",
                            status="Pendente",
                            proposta_id=proposta_id_int,
                            classificacao="receita",
                            usuario_id=usuario_id
                        )
                        self.session.add(transacao_receita)
                        
                        # Removido o lançamento de "Valor a receber" para evitar duplicidade
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO (ORM): Não criando mais lançamento de 'Valor a receber' para evitar duplicidade")
                        
                        # 2. Lançamento de comissão sobre fornecedores (valor zero como placeholder)
                        transacao_comissao = Transacao(
                            tipo="Receita",
                            descricao=f"Comissão de fornecedores - Proposta #{proposta.numero} - {cliente.nome}",
                            valor=0,
                            data=data_lancamento,
                            categoria="Comissão sobre fornecedores",
                            subcategoria="Fornecedores",
                            tipo_receita="comissao",
                            origem_id=proposta.cliente_id,
                            origem_tipo="cliente",
                            tipo_conta="PF",
                            status="Pendente",
                            proposta_id=proposta_id_int,
                            classificacao="receita",
                            usuario_id=usuario_id
                        )
                        self.session.add(transacao_comissao)
                        
                        # 3. Lançamento de despesa para equipe/assistentes (valor zero como placeholder)
                        transacao_assistentes = Transacao(
                            tipo="Despesa",
                            descricao=f"Pagamento Equipe/Assistentes - Proposta #{proposta.numero} - {cliente.nome}",
                            valor=0,
                            data=data_lancamento,
                            categoria="Pagamento Equipe/Assistentes",
                            subcategoria="Assistentes",
                            origem_id=proposta.cliente_id,
                            origem_tipo="cliente",
                            tipo_conta="PF",
                            status="Pendente",
                            proposta_id=proposta_id_int,
                            classificacao="despesa_a_pagar",
                            usuario_id=usuario_id
                        )
                        self.session.add(transacao_assistentes)
                        
                        self.session.flush()  # Forçar um flush para detectar erros antes do commit
                        
                        result["valor_base"] = valor_base
                        result["lancamentos_gerados"] += 3  # Três lançamentos: receita principal, comissão e despesa
                        print(f"DEBUG LANCAMENTOS APROVAÇÃO (ORM): Lançamentos criados com sucesso (Receita, Comissão, Despesa)")
                
                return result
                
            except Exception as e:
                print(f"ERRO em gerar_lancamentos_proposta_aprovada: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
        
        return self._safe_query(query)
        
    def update_proposta_status(self, proposta_id, novo_status, data_aprovacao=None):
        """
        Atualiza o status de uma proposta e opcionalmente define a data de aprovação
        Se o status for "Em execução", automaticamente:
        - Define data_inicio_execucao para a data de início da proposta (não a data atual)
        - Define status_execucao como "Em execução" (anteriormente "Iniciada")
        - Cria transação financeira para cliente a receber
        
        Args:
            proposta_id: ID da proposta a ser atualizada
            novo_status: Novo status da proposta 
            data_aprovacao: Data de aprovação (opcional)
        
        Returns:
            dict: Dicionário com status da operação e mensagem
        """
        def query():
            # Inicializar data_aprovacao localmente para garantir que existe
            data_aprovacao_local = data_aprovacao
            
            # Buscar a proposta por ID
            proposta = self.session.query(Proposta).filter(Proposta.id == proposta_id).first()
            
            if proposta is None:
                print(f"DEBUG: Proposta com ID {proposta_id} não encontrada")
                return {"status": False, "message": f"Proposta ID {proposta_id} não encontrada"}
            
            # Armazenar o status antigo para verificação simples
            status_antigo = proposta.status
            
            # Verificar se já existem lançamentos para esta proposta para evitar duplicidade
            # Agora verificamos diretamente por lançamentos 'Receita' (não mais receita_a_receber_aprovacao)
            lancamentos_existentes = self.session.query(Transacao)\
                .filter_by(proposta_id=proposta_id, tipo="Receita")\
                .count()
            
            # Atualizar campos
            proposta.status = novo_status
            if data_aprovacao_local:
                proposta.data_aprovacao = data_aprovacao_local
                
            # Definir campos adicionais se o status for "Em execução"
            if novo_status == "Em execução":
                # Sempre usar a data de início da proposta como data de início de execução
                proposta.data_inicio_execucao = proposta.data_inicio
                # Alterar para "Em execução" em vez de "Iniciada" para consistência
                proposta.status_execucao = "Em execução"
                print(f"DEBUG: Proposta {proposta_id} entrando em execução, data_inicio={proposta.data_inicio}, status_execucao={proposta.status_execucao}")
            
            # Salvar as alterações para garantir que tudo esteja atualizado antes de gerar lançamentos
            self.session.flush()
            
            # Preparar objeto de resultado
            resultado = {"status": True, "message": f"Proposta {proposta_id} atualizada com status '{novo_status}'"}
            
            # Gerar lançamentos apenas se não existirem e a proposta estiver mudando para "Em execução" ou "Aprovada"
            if lancamentos_existentes == 0 and status_antigo in ["Em elaboração", "Aguardando aprovação"] and (novo_status == "Em execução" or novo_status == "Aprovada"):
                try:
                    # Gerar lançamentos financeiros para proposta aprovada (receita a receber e contas a receber)
                    self.gerar_lancamentos_proposta_aprovada(proposta_id)
                    print(f"DEBUG: Lançamentos financeiros gerados para proposta em execução {proposta_id}")
                    resultado["lancamentos"] = {"status": "success", "message": "Lançamentos financeiros gerados com sucesso"}
                except Exception as e:
                    print(f"ERRO ao gerar lançamentos para proposta em execução: {str(e)}")
                    resultado["lancamentos"] = {"status": "error", "message": f"Erro ao gerar lançamentos: {str(e)}"}
            elif lancamentos_existentes > 0:
                print(f"DEBUG: Proposta {proposta_id} já possui {lancamentos_existentes} lançamentos. Pulando geração automática.")
                resultado["lancamentos"] = {"status": "ignored", "message": "Proposta já possui lançamentos financeiros"}
            
            # Registrar a mudança de status
            print(f"DEBUG: Proposta {proposta_id} atualizada com status '{novo_status}', status_execucao='{proposta.status_execucao}'")
            return resultado
            
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

    def add_produto_via_sql_direto(self, proposta_id, nome, descricao, valor, quantidade, comodo):
        """
        Adiciona um produto usando SQL direto, evitando camadas ORM
        
        Args:
            proposta_id: ID da proposta
            nome: Nome do produto
            descricao: Descrição do produto
            valor: Valor do produto
            quantidade: Quantidade do produto
            comodo: Nome do cômodo onde será usado
            
        Returns:
            int: ID do produto adicionado ou None em caso de erro
        """
        try:
            # Verificar se os tipos de dados estão corretos
            proposta_id_int = int(proposta_id)
            valor_float = float(valor)
            quantidade_int = int(quantidade)
            comodo_final = comodo or "Geral"
            descricao_final = descricao or ""
            
            # Sanitizar strings para evitar SQL injection
            nome_sanitizado = nome.replace("'", "''")
            descricao_sanitizada = descricao_final.replace("'", "''")
            comodo_sanitizado = comodo_final.replace("'", "''")
            
            # Usar psycopg2 diretamente para evitar problemas com SQLAlchemy
            import psycopg2
            import os
            from datetime import datetime
            
            # Obter a conexão diretamente do ambiente
            db_url = os.environ.get('DATABASE_URL')
            
            # Conectar diretamente com psycopg2
            print(f"DEBUG SQL PRODUTO: Conectando diretamente com psycopg2")
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            try:
                # Buscar o usuario_id da proposta
                get_usuario_sql = f"SELECT usuario_id FROM propostas WHERE id = {proposta_id_int}"
                cursor.execute(get_usuario_sql)
                usuario_result = cursor.fetchone()
                
                if not usuario_result or usuario_result[0] is None:
                    print(f"DEBUG SQL PRODUTO: Proposta ID={proposta_id_int} não encontrada ou sem usuario_id")
                    if self.usuario_id:
                        usuario_id = self.usuario_id
                        print(f"DEBUG SQL PRODUTO: Usando usuario_id da sessão atual: {usuario_id}")
                    else:
                        print(f"DEBUG SQL PRODUTO: Nenhum usuario_id disponível, impossível continuar")
                        return None
                else:
                    usuario_id = usuario_result[0]
                    print(f"DEBUG SQL PRODUTO: Encontrado usuario_id={usuario_id} para a proposta ID={proposta_id_int}")
                
                # Executar a inserção
                # Nota: A tabela produtos_organizadores não possui o campo usuario_id
                # A associação com o usuário é feita via proposta_id
                sql = f"""
                INSERT INTO produtos_organizadores 
                (proposta_id, nome, descricao, valor, quantidade, comodo, data_cadastro) 
                VALUES 
                ({proposta_id_int}, '{nome_sanitizado}', '{descricao_sanitizada}', {valor_float}, {quantidade_int}, '{comodo_sanitizado}', NOW())
                RETURNING id;
                """
                
                print(f"DEBUG SQL PRODUTO: Executando SQL direto para adicionar produto")
                print(f"DEBUG SQL PRODUTO: Proposta ID={proposta_id_int}, Nome='{nome_sanitizado}'")
                
                cursor.execute(sql)
                result = cursor.fetchone()
                conn.commit()
                
                if result and result[0]:
                    produto_id = result[0]
                    print(f"DEBUG SQL PRODUTO: Produto adicionado com ID={produto_id}")
                    
                    # Verificar se o produto foi realmente adicionado
                    verify_sql = f"SELECT COUNT(*) FROM produtos_organizadores WHERE id = {produto_id}"
                    cursor.execute(verify_sql)
                    verify_result = cursor.fetchone()
                    if verify_result and verify_result[0] > 0:
                        print(f"DEBUG SQL PRODUTO: Verificação OK - Produto ID={produto_id} encontrado no banco")
                    else:
                        print(f"DEBUG SQL PRODUTO: ALERTA - Produto ID={produto_id} não encontrado na verificação!")
                    
                    return produto_id
                else:
                    print("DEBUG SQL PRODUTO: Nenhum ID retornado da inserção")
                    return None
            finally:
                # Sempre fechar a conexão
                cursor.close()
                conn.close()
                print(f"DEBUG SQL PRODUTO: Conexão psycopg2 fechada")
                
        except Exception as e:
            print(f"DEBUG SQL PRODUTO: ERRO ao adicionar produto via SQL: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def add_produto_organizador(self, proposta_id, nome, descricao, valor, quantidade, comodo):
        """
        Adiciona um produto à proposta de organização
        
        Args:
            proposta_id: ID da proposta
            nome: Nome do produto
            descricao: Descrição do produto
            valor: Valor do produto
            quantidade: Quantidade do produto
            comodo: Nome do cômodo onde será usado
            
        Returns:
            int: ID do produto adicionado
        """
        # Primeiro tentar a adição via SQL direto
        produto_id = self.add_produto_via_sql_direto(proposta_id, nome, descricao, valor, quantidade, comodo)
        if produto_id is not None:
            return produto_id
            
        # Se não funcionou, tentar o método tradicional
        try:
            # print(f"DEBUG PRODUTO: SQL direto falhou, tentando método ORM")
            # print(f"DEBUG PRODUTO: Adicionando produto '{nome}' à proposta ID={proposta_id}")
            
            # Verificar se os tipos de dados estão corretos
            proposta_id_int = int(proposta_id)
            valor_float = float(valor)
            quantidade_int = int(quantidade)
            
            # Criar o objeto produto 
            # Nota: ProdutoOrganizador não possui o campo usuario_id
            # A associação com o usuário é feita via proposta_id
            produto = ProdutoOrganizador(
                proposta_id=proposta_id_int,
                nome=nome,
                descricao=descricao,
                valor=valor_float,
                quantidade=quantidade_int,
                comodo=comodo or "Geral"
            )
            
            # Adicionar ao banco de dados usando uma transação isolada
            self.session = Session()  # Nova sessão limpa
            self.session.add(produto)
            self.session.flush()  # Para obter o ID do produto
            self.session.commit()
            
            print(f"DEBUG PRODUTO: Produto ORM adicionado com ID: {produto.id}")
            return produto.id
            
        except Exception as e:
            print(f"DEBUG PRODUTO: ERRO no método ORM: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Propagar erro original
            raise ValueError(f"Não foi possível adicionar o produto: {str(e)}")

    def get_produtos_organizadores_sql_direto(self, proposta_id=None):
        """
        Busca produtos usando SQL direto com psycopg2 para evitar problemas de transação
        """
        try:
            # Usar psycopg2 diretamente para evitar problemas com SQLAlchemy
            import psycopg2
            import psycopg2.extras
            import os
            import pandas as pd
            from datetime import datetime
            
            # Obter a conexão diretamente do ambiente
            db_url = os.environ.get('DATABASE_URL')
            
            # Conectar diretamente com psycopg2
            # Removido logs de debug
            conn = psycopg2.connect(db_url)
            
            # Usar DictCursor para facilitar acesso aos campos por nome
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                # Executar a busca SQL
                if proposta_id:
                    # Converter explicitamente para int Python padrão (mesmo que seja numpy.int64)
                    proposta_id_int = int(proposta_id)
                    
                    # Não há o campo usuario_id na tabela produtos_organizadores
                    # A filtragem por usuário é feita indiretamente através do proposta_id
                    sql = f"SELECT * FROM produtos_organizadores WHERE proposta_id = {proposta_id_int}"
                    
                    # Se precisar filtrar por usuário, precisaremos fazer um JOIN com a tabela propostas
                    if self.usuario_id:
                        sql = f"""
                            SELECT po.* FROM produtos_organizadores po
                            JOIN propostas p ON po.proposta_id = p.id
                            WHERE po.proposta_id = {proposta_id_int}
                            AND p.usuario_id = '{self.usuario_id}'
                        """
                else:
                    # Busca geral
                    if self.usuario_id:
                        # Com filtro de usuário - precisa fazer JOIN
                        sql = f"""
                            SELECT po.* FROM produtos_organizadores po
                            JOIN propostas p ON po.proposta_id = p.id
                            WHERE p.usuario_id = '{self.usuario_id}'
                        """
                    else:
                        sql = "SELECT * FROM produtos_organizadores"
                
                # Removido logs de debug
                cursor.execute(sql)
                result = cursor.fetchall()
                
                # Criar DataFrame manualmente
                if result:
                    df_data = []
                    for row in result:
                        data_cadastro = row['data_cadastro'] if 'data_cadastro' in row else datetime.now().date()
                        df_data.append({
                            'id': row['id'],
                            'nome': row['nome'],
                            'descricao': row['descricao'],
                            'valor': row['valor'],
                            'quantidade': row['quantidade'],
                            'comodo': row['comodo'],
                            'data_cadastro': data_cadastro
                        })
                    
                    df = pd.DataFrame(df_data)
                    # Removido log de debug
                    return df
                else:
                    # Removido log de debug
                    return pd.DataFrame()
            finally:
                cursor.close()
                conn.close()
                # Removido log de debug
        except Exception as e:
            # Removido log de debug
            # import traceback
            # traceback.print_exc()
            # Em caso de erro, retornar DataFrame vazio
            import pandas as pd
            return pd.DataFrame()

    def _ensure_int(self, value):
        """
        Garante que o valor seja um inteiro Python padrão, mesmo que seja numpy.int64
        """
        if value is None:
            return None
        return int(value)
        
    def get_perfil_by_email(self, email):
        """
        Busca o perfil do usuário pelo email
        
        Args:
            email: Email do usuário
            
        Returns:
            dict: Dados do perfil ou None se não encontrado
        """
        def query():
            try:
                print(f"Buscando perfil para o email: {email}")
                
                # Buscar na tabela de usuários (que já sabemos que existe)
                try:
                    usuario = self.session.query(Usuario).filter_by(email=email).first()
                    if usuario:
                        print(f"Usuário encontrado com email {email}")
                        perfil_dict = {
                            'id': usuario.id,
                            'nome': usuario.nome,
                            'email': usuario.email,
                            'tipo': usuario.tipo,
                            'empresa': usuario.empresa if hasattr(usuario, 'empresa') else 'Planner Organizer',
                            'role': 'user'  # Valor padrão
                        }
                        # Adicionar telefone se existir
                        if hasattr(usuario, 'telefone') and usuario.telefone:
                            perfil_dict['telefone'] = usuario.telefone
                        return perfil_dict
                except Exception as e:
                    print(f"Erro ao buscar usuário por email: {str(e)}")
                
                # Tentar na tabela de clientes como alternativa
                try:
                    cliente = self.session.query(Cliente).filter_by(email=email).first()
                    if cliente:
                        print(f"Cliente encontrado com email {email}")
                        perfil_dict = {
                            'id': cliente.id,
                            'nome': cliente.nome,
                            'email': cliente.email,
                            'telefone': cliente.telefone if cliente.telefone else '',
                            'empresa': 'Planner Organizer'  # Valor padrão
                        }
                        # Adicionar campos adicionais se existirem
                        for field in ['endereco', 'cidade', 'estado']:
                            if hasattr(cliente, field) and getattr(cliente, field):
                                perfil_dict[field] = getattr(cliente, field)
                        
                        return perfil_dict
                except Exception as e:
                    print(f"Erro ao buscar cliente por email: {str(e)}")
                
                # Tentar com uma consulta SQL direta para tabela 'perfis' (se existir)
                try:
                    # Tentar consulta SQL direta
                    sql = text("SELECT * FROM perfis WHERE email = :email")
                    result = self.session.execute(sql, {'email': email}).fetchone()
                    if result:
                        print("Perfil encontrado na tabela 'perfis' via SQL direta")
                        # Converter resultado para dicionário
                        perfil_dict = {}
                        for column, value in result.items():
                            perfil_dict[column] = value
                        return perfil_dict
                except Exception as e:
                    print(f"Erro ao buscar via SQL direta: {str(e)}")
                
                # Se chegou aqui, não encontrou o perfil em nenhuma fonte
                print(f"Perfil não encontrado para o email: {email}")
                return None
            except Exception as e:
                print(f"ERRO geral ao buscar perfil por email: {str(e)}")
                return None
        
        return self._safe_query(query)
        
    def get_produtos_organizadores(self, proposta_id=None):
        """
        Obtém produtos de uma proposta. Tenta primeiro via SQL direto, e depois via ORM.
        """
        # Primeiro tentar via SQL direto
        df_produtos = self.get_produtos_organizadores_sql_direto(proposta_id)
        if not df_produtos.empty:
            return df_produtos
        
        # Se falhou, tentar via ORM normal
        def query():
            query = self.session.query(ProdutoOrganizador)
            
            # Aplicar filtros
            if proposta_id:
                # Converter explicitamente para int Python padrão
                proposta_id_int = self._ensure_int(proposta_id)
                query = query.filter_by(proposta_id=proposta_id_int)
                
            # Não filtramos ProdutoOrganizador por usuario_id diretamente
            # pois esta tabela não possui este campo
            # A filtragem por usuário já é feita indiretamente via proposta_id
                
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


    def registrar_usuario(self, email, senha, nome, telefone=None, empresa=None, tipo='usuario'):
        """Registra um novo usuário no sistema"""
        def query():
            if self.session.query(Usuario).filter_by(email=email).first():
                return False, "Email já cadastrado"

            usuario = Usuario(
                email=email,
                nome=nome,
                telefone=telefone,  # Novo campo
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
                # Converter o objeto Usuario para dicionário antes de retornar
                usuario_dict = {
                    'id': usuario.id,
                    'nome': usuario.nome,
                    'email': usuario.email,
                    'tipo': usuario.tipo,
                    'empresa': usuario.empresa,
                    'ativo': usuario.ativo
                }
                return True, usuario_dict
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
                estado="SP",
                cidade="São Paulo",
                bairro="Vila Madalena",
                cpf="123.456.789-00",
                data_aniversario=datetime.now().date(),
                origem_cliente="Indicação"
            )

            client2_id = self.add_cliente(
                nome="João Santos",
                email="joao@email.com",
                telefone="(11) 88888-8888",
                endereco="Av. Principal, 456",
                estado="RJ",
                cidade="Rio de Janeiro",
                bairro="Copacabana",
                cpf="987.654.321-00",
                data_aniversario=datetime.now().date(),
                origem_cliente="Redes Sociais"
            )

            fornecedor1_id = self.add_fornecedor(
                descricao="Organizadores Express",
                contato="(11) 97777-7777",
                categoria="Produtos",
                pix="12345678901",
                recorrente=False,
                estado="SP",
                cidade="São Paulo",
                bairro="Pinheiros",
                endereco="Rua Augusta, 100"
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

    def add_assistente(self, nome, telefone, endereco=None, pix=None, observacoes=None):
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
            # Criar uma nova sessão para evitar problemas com estado 'prepared'
            # Isso resolve o erro "This session is in 'prepared' state"
            session = Session()
            try:
                assistentes = session.query(Assistente).all()
                return pd.DataFrame([{
                    'id': a.id,
                    'nome': a.nome,
                    'telefone': a.telefone,
                    'endereco': a.endereco,
                    'pix': a.pix,
                    'observacoes': a.observacoes
                } for a in assistentes])
            finally:
                session.close()
        return self._safe_query(query)

    def add_parceiro(self, nome, telefone, area_atuacao, tipo_parceria, 
                estado=None, cidade=None, bairro=None, endereco=None, 
                pix=None, observacoes=None):
        def query():
            parceiro = Parceiro(
                nome=nome,
                telefone=telefone,
                area_atuacao=area_atuacao,
                tipo_parceria=tipo_parceria,
                estado=estado,
                cidade=cidade,
                bairro=bairro,
                endereco=endereco,
                pix=pix,
                observacoes=observacoes
            )
            self.session.add(parceiro)
            return parceiro.id
        return self._safe_query(query)

    def get_parceiros(self):
        def query():
            # Criar uma nova sessão para evitar problemas com estado 'prepared'
            # Isso resolve o erro "This session is in 'prepared' state"
            session = Session()
            try:
                parceiros = session.query(Parceiro).all()
                return pd.DataFrame([{
                    'id': p.id,
                    'nome': p.nome,
                    'telefone': p.telefone,
                    'area_atuacao': p.area_atuacao,
                    'tipo_parceria': p.tipo_parceria,
                    'estado': p.estado,
                    'cidade': p.cidade,
                    'bairro': p.bairro,
                    'endereco': p.endereco,
                    'pix': p.pix,
                    'observacoes': p.observacoes,
                    'data_cadastro': p.data_cadastro
                } for p in parceiros])
            finally:
                session.close()
        return self._safe_query(query)

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
            Session.remove()

    def atualizar_status_pagamento_proposta(self, proposta_id, status_pagamento_base, valor_base):
        """Atualiza o status de pagamento e valor base de uma proposta"""
        def query():
            try:
                # Converter ID para int nativo do Python
                proposta_id_int = int(proposta_id)
                valor_base_float = float(valor_base)

                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if proposta:
                    proposta.status_pagamento_base = status_pagamento_base
                    proposta.valor = valor_base_float
                    return True
                return False
            except (ValueError, TypeError) as e:
                raise Exception(f"Erro ao converter valores: {str(e)}")
        return self._safe_query(query)
        
    def atualizar_proposta(self, proposta_id, descricao=None, valor=None, status=None, 
                          tipo_proposta=None, data_inicio=None, data_fim=None, prazo_entrega=None,
                          data_proposta=None, previsao_dias=None, data_inicio_execucao=None,
                          status_execucao=None, gerar_transacoes_automaticas=True):
        """
        Atualiza os dados de uma proposta existente
        
        Args:
            proposta_id: ID da proposta a ser atualizada
            descricao: Nova descrição (opcional)
            valor: Novo valor (opcional)
            status: Novo status (opcional)
            tipo_proposta: Novo tipo de proposta (opcional)
            data_inicio: Nova data de início (opcional)
            data_fim: Nova data de fim (opcional)
            prazo_entrega: Nova data de prazo de entrega (opcional)
            data_proposta: Nova data da proposta (opcional)
            previsao_dias: Nova previsão de dias (opcional)
            data_inicio_execucao: Data de início da execução (opcional)
            status_execucao: Status de execução (opcional)
            gerar_transacoes_automaticas: Se True, gerará transações financeiras automaticamente quando o status for alterado para "Aprovada"
            
        Returns:
            dict: Resultado da operação com status, mensagem e info das transações (se aplicável)
        """
        def query():
            try:
                # Converter proposta_id para inteiro
                proposta_id_int = int(proposta_id)
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    return {"status": False, "message": f"Proposta ID {proposta_id} não encontrada"}
                
                # Verificar se precisamos gerar transações automaticamente
                proposta_aprovada = False
                proposta_finalizada = False
                
                # Verificar mudança de status para "Aprovada"
                if status is not None and status == "Aprovada" and proposta.status != "Aprovada":
                    proposta_aprovada = True
                    # Registrar a data de aprovação
                    proposta.data_aprovacao = datetime.now().date()
                
                # Verificar mudança de status para "Concluída"
                if status is not None and status == "Concluída" and proposta.status != "Concluída":
                    proposta_finalizada = True
                    # Se não foi fornecida uma data_fim, usar a data atual
                    if data_fim is None:
                        proposta.data_fim = datetime.now().date()
                
                # Atualizar apenas os campos fornecidos
                if descricao is not None:
                    proposta.descricao = descricao
                
                if valor is not None:
                    proposta.valor = float(valor)
                
                if status is not None:
                    proposta.status = status
                
                if tipo_proposta is not None:
                    proposta.tipo_proposta = tipo_proposta
                
                if data_inicio is not None:
                    proposta.data_inicio = data_inicio
                    # Quando a data de início for atualizada, também atualizar a data de início de execução
                    # se a proposta já estiver aprovada ou em execução
                    if proposta.status in ['Aprovada', 'Em execução', 'Finalizada']:
                        proposta.data_inicio_execucao = data_inicio
                
                if data_fim is not None:
                    proposta.data_fim = data_fim
                
                if prazo_entrega is not None:
                    proposta.prazo_entrega = prazo_entrega
                
                if data_proposta is not None:
                    proposta.data_proposta = data_proposta
                
                if previsao_dias is not None:
                    proposta.previsao_dias = previsao_dias
                
                # Sempre garantir que a data de início de execução seja a data de início da proposta
                if data_inicio_execucao is not None:
                    # Ignorar o valor passado e usar a data de início da proposta
                    proposta.data_inicio_execucao = proposta.data_inicio
                    
                if status_execucao is not None:
                    proposta.status_execucao = status_execucao
                
                # Salvar as alterações antes de gerar transações
                self.session.flush()
                
                # Gerar transações financeiras automaticamente se a proposta foi aprovada ou finalizada
                resultado = {"status": True, "message": "Proposta atualizada com sucesso"}
                
                # Tratar proposta finalizada - gerar lançamentos de conclusão e registrar vendas
                if proposta_finalizada and gerar_transacoes_automaticas:
                    try:
                        # Buscar o cliente da proposta
                        cliente = self.session.query(Cliente).filter_by(id=proposta.cliente_id).first()
                        if not cliente:
                            resultado["lancamentos_finalizacao"] = {
                                "status": "erro",
                                "message": f"Cliente ID {proposta.cliente_id} não encontrado para gerar lançamentos de finalização"
                            }
                        else:
                            # Gerar lançamentos financeiros para proposta concluída
                            # Usar forcar_geracao=True para garantir que todos os lançamentos são gerados,
                            # incluindo para "OUTROS" e "DESPESA ASSISTENTE"
                            lancamentos_result = self.gerar_lancamentos_financeiros_proposta_concluida(
                                proposta_id=proposta_id_int, 
                                forcar_geracao=True
                            )
                            
                            # Buscar produtos da proposta para registrar vendas
                            produtos_proposta = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_int).all()
                            if produtos_proposta:
                                try:
                                    # Registrar vendas dos produtos (usando forcar_geracao=True)
                                    venda_id = self._registrar_venda_produtos(proposta, cliente, produtos_proposta, forcar_geracao=True)
                                    if venda_id:
                                        lancamentos_result["venda_id"] = venda_id
                                        lancamentos_result["produtos_vendidos"] = len(produtos_proposta)
                                except Exception as e:
                                    print(f"ERRO ao registrar venda de produtos: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                                    lancamentos_result["erro_venda"] = str(e)
                            
                            resultado["lancamentos_finalizacao"] = lancamentos_result
                    except Exception as e:
                        print(f"ERRO ao gerar lançamentos de finalização: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        resultado["lancamentos_finalizacao"] = {
                            "status": "erro",
                            "message": f"Erro ao gerar lançamentos de finalização: {str(e)}"
                        }
                
                # Continuar processando proposta aprovada
                if proposta_aprovada and gerar_transacoes_automaticas:
                    try:
                        # Usar o método gerar_lancamentos_proposta_aprovada para consistência
                        lancamentos_result = self.gerar_lancamentos_proposta_aprovada(proposta_id_int)
                        
                        # Verificar o resultado
                        if lancamentos_result.get("status") == "já existe":
                            resultado["transacoes"] = {
                                "status": "já existem transações",
                                "message": "Já existem lançamentos para esta proposta."
                            }
                        else:
                            # Buscar acréscimos da proposta para despesas relacionadas
                            acrescimos = self.session.query(AcrescimoProposta).filter_by(proposta_id=proposta_id_int).all()
                            
                            # Criar transações de despesa para cada acréscimo
                            despesa_ids = []
                            for acrescimo in acrescimos:
                                if acrescimo.valor and acrescimo.valor > 0:
                                    despesa_id = self._criar_transacao_despesa(acrescimo, proposta)
                                    despesa_ids.append(despesa_id)
                            
                            # Adicionar informações de despesas ao resultado
                            lancamentos_result["despesa_ids"] = despesa_ids
                            lancamentos_result["total_despesas"] = len(despesa_ids)
                            
                            resultado["transacoes"] = {
                                "status": "sucesso",
                                "lancamentos_base": lancamentos_result,
                                "despesa_ids": despesa_ids,
                                "total_despesas": len(despesa_ids),
                                "message": f"Lançamentos financeiros gerados automaticamente para a proposta #{proposta.numero}"
                            }
                    except Exception as e:
                        print(f"ERRO ao gerar lançamentos para proposta aprovada: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        resultado["transacoes"] = {
                            "status": "erro",
                            "message": f"Erro ao gerar lançamentos: {str(e)}"
                        }
                
                return resultado
            except Exception as e:
                raise Exception(f"Erro ao atualizar proposta: {str(e)}")
        
        return self._safe_query(query)

    def add_acrescimo_proposta(self, proposta_id, tipo, valor, descricao=None, fornecedor=None, 
                               status_pagamento='Pendente', percentual_comissao=None):
        """
        Adiciona um acréscimo a uma proposta
        
        Args:
            proposta_id: ID da proposta
            tipo: Tipo de acréscimo (Organização, Assistente, Fornecedor, Marcenaria, Produto)
            valor: Valor do acréscimo
            descricao: Descrição do acréscimo (opcional)
            fornecedor: Nome do fornecedor ou assistente (opcional)
            status_pagamento: Status do pagamento (Pendente, Pago)
            percentual_comissao: Percentual de comissão para acréscimos do tipo Fornecedor (opcional)
            
        Returns:
            dict: Informações sobre o acréscimo adicionado e transações geradas
        """
        # Log para diagnóstico apenas em modo de depuração avançada
        # # print(f"DEBUG: Adicionando acréscimo à proposta ID={proposta_id}, tipo={tipo}, fornecedor={fornecedor}, valor={valor}")
        
        # Converter valores para tipos nativos Python antes da consulta
        try:
            proposta_id_int = int(proposta_id)
            valor_float = float(valor) if valor is not None else 0.0
            
            # Fornecer um valor padrão para o fornecedor se não foi fornecido
            fornecedor_nome = str(fornecedor) if fornecedor else f"{tipo} Padrão"
            
            # Garantir que a descrição não seja None
            descricao_texto = str(descricao) if descricao else f"Acréscimo de {tipo}"
            
            # Converter percentual_comissao se fornecido
            percentual_comissao_float = None
            if percentual_comissao is not None:
                try:
                    percentual_comissao_float = float(percentual_comissao)
                    if percentual_comissao_float < 0 or percentual_comissao_float > 100:
                        percentual_comissao_float = None
                except (ValueError, TypeError):
                    percentual_comissao_float = None
                    
            def query():
                # Verificar se a proposta existe na sessão atual
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada no banco de dados")
                
                cliente = self.session.query(Cliente).filter_by(id=proposta.cliente_id).first()
                if not cliente:
                    raise ValueError(f"Cliente ID {proposta.cliente_id} não encontrado no banco de dados")
                
                try:
                    # # print(f"DEBUG: Criando acréscimo para proposta ID={proposta_id_int}, tipo={tipo}, fornecedor={fornecedor_nome}")
                    
                    # Criar objeto de acréscimo com valores já verificados
                    # Garantir que o tipo esteja em maiúsculas para consistência
                    tipo_upper = tipo.upper() if tipo else "OUTROS"
                    # # print(f"DEBUG: Convertendo tipo de acréscimo para maiúsculas: {tipo} -> {tipo_upper}")
                    
                    acrescimo = AcrescimoProposta(
                        proposta_id=proposta_id_int,
                        tipo=tipo_upper,
                        fornecedor=fornecedor_nome,
                        descricao=descricao_texto,
                        valor=valor_float,
                        status_pagamento=status_pagamento,
                        data_cadastro=datetime.now().date()
                    )
                    
                    # Adicionar à sessão
                    self.session.add(acrescimo)
                    self.session.flush()  # Flush para obter o ID sem commitar ainda
                    
                    # Estrutura para armazenar os resultados
                    resultado = {
                        "acrescimo_id": None,
                        "comissao_gerada": False,
                        "comissao_id": None,
                        "valor_comissao": 0.0,
                        "despesa_gerada": False,
                        "despesa_id": None,
                        "valor_despesa": 0.0
                    }
                    
                    # Garantir que temos um ID inteiro válido
                    if acrescimo.id is not None:
                        acrescimo_id = int(acrescimo.id)
                        # # print(f"DEBUG: Acréscimo criado com sucesso, ID={acrescimo_id}")
                        
                        resultado["acrescimo_id"] = acrescimo_id
                        
                        # Não gerar mais transações automáticas de comissão ou assistente aqui
                        # Elas serão geradas apenas na finalização da proposta (gerar_lancamentos_financeiros_proposta_concluida)
                        
                        # Apenas armazenar a informação do percentual de comissão para uso posterior
                        if tipo_upper == "FORNECEDOR" and percentual_comissao_float is not None and percentual_comissao_float > 0:
                            resultado["comissao_percentual"] = percentual_comissao_float
                        # Remover a geração automática de despesa para assistentes
                        elif tipo_upper == "ASSISTENTE":
                            resultado["assistente_valor"] = valor_float
                        
                        return resultado
                    else:
                        raise ValueError("Não foi possível obter ID do acréscimo após flush")
                    
                except Exception as e:
                    print(f"DEBUG ERROR: Erro ao criar acréscimo: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    self.session.rollback()  # Fazer rollback em caso de erro
                    raise e
                    
            # Usar _safe_query para garantir transação adequada
            resultado = self._safe_query(query)
            # # print(f"DEBUG: Resultado final da adição de acréscimo: {resultado}")
            return resultado
            
        except Exception as e:
            print(f"DEBUG CRITICAL: Exceção crítica ao adicionar acréscimo: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Erro ao adicionar acréscimo: {str(e)}")

    def get_acrescimos_proposta(self, proposta_id):
        """
        Retorna todos os acréscimos de uma proposta em um DataFrame
        
        Args:
            proposta_id: ID da proposta
            
        Returns:
            DataFrame com os acréscimos da proposta, ou DataFrame vazio se não houver acréscimos
        """
        # Converter proposta_id para int nativo do Python antes da função query
        proposta_id = int(proposta_id) if proposta_id is not None else None
        
        # # print(f"DEBUG: Buscando acréscimos para proposta ID={proposta_id}")

        def query():
            try:
                # Verificar se a proposta existe
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                if not proposta:
                    print(f"DEBUG WARNING: Proposta ID={proposta_id} não encontrada ao buscar acréscimos")
                    # Retornar DataFrame vazio em vez de levantar exceção
                    return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
                # Buscar acréscimos
                acrescimos = self.session.query(AcrescimoProposta).filter_by(proposta_id=proposta_id).all()
                # # print(f"DEBUG: Encontrados {len(acrescimos)} acréscimos para proposta ID={proposta_id}")
                
                # Se não houver acréscimos, retornar DataFrame vazio
                if not acrescimos:
                    return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
                # Converter para DataFrame
                return pd.DataFrame([{
                    'id': int(a.id),  # Garantir que todos os IDs sejam int nativos
                    'tipo': a.tipo,
                    'fornecedor': a.fornecedor,
                    'descricao': a.descricao,
                    'valor': float(a.valor) if a.valor is not None else None,  # Converter para float nativo
                    'status_pagamento': a.status_pagamento,
                    'data_cadastro': a.data_cadastro
                } for a in acrescimos])
            except Exception as e:
                print(f"DEBUG ERROR: Erro ao buscar acréscimos para proposta ID={proposta_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                # Ainda retorna DataFrame vazio em caso de erro para evitar quebrar a UI
                return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
        return self._safe_query(query)
        
    def get_acrescimos_proposta_por_tipo(self, proposta_id, tipo):
        """
        Retorna os acréscimos de uma proposta filtrados por tipo
        
        Args:
            proposta_id (int): ID da proposta
            tipo (str): Tipo de acréscimo (FORNECEDOR, ASSISTENTE, OUTROS)
            
        Returns:
            DataFrame: Acréscimos do tipo especificado
        """
        # Converter proposta_id para int nativo do Python
        proposta_id = int(proposta_id) if proposta_id is not None else None
        
        # # print(f"DEBUG: Buscando acréscimos do tipo {tipo} para proposta ID={proposta_id}")

        def query():
            try:
                # Verificar se a proposta existe
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                if not proposta:
                    # # print(f"DEBUG: Proposta ID={proposta_id} não encontrada")
                    return pd.DataFrame()
                
                # Obter acréscimos do tipo especificado (garantindo que o tipo seja maiúsculo)
                tipo_upper = tipo.upper() if tipo else "OUTROS"
                # # print(f"DEBUG: Buscando acréscimos com tipo={tipo_upper}")
                
                acrescimos = self.session.query(AcrescimoProposta).filter_by(
                    proposta_id=proposta_id, 
                    tipo=tipo_upper
                ).order_by(AcrescimoProposta.data_cadastro).all()
                
                if not acrescimos:
                    # # print(f"DEBUG: Nenhum acréscimo do tipo {tipo} encontrado para proposta ID={proposta_id}")
                    return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
                # # print(f"DEBUG: Encontrados {len(acrescimos)} acréscimos do tipo {tipo}")
                
                # Converter para dataframe
                result = []
                for a in acrescimos:
                    result.append({
                        'id': a.id,
                        'tipo': a.tipo,
                        'fornecedor': a.fornecedor,
                        'descricao': a.descricao,
                        'valor': a.valor,
                        'status_pagamento': a.status_pagamento,
                        'data_cadastro': a.data_cadastro
                    })
                
                return pd.DataFrame(result)
                
            except Exception as e:
                # # print(f"DEBUG: Erro ao obter acréscimos do tipo {tipo} para proposta ID={proposta_id}: {str(e)}")
                return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
        
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

    def update_cliente(self, cliente_id, nome=None, email=None, telefone=None, estado=None, 
                      cidade=None, bairro=None, endereco=None, cpf=None, 
                      data_aniversario=None, origem_cliente=None, observacoes=None):
        """Atualiza os dados de um cliente"""
        def query():
            cliente = self.session.query(Cliente).filter_by(id=cliente_id).first()
            if not cliente:
                return False

            if nome is not None:
                cliente.nome = nome
            if email is not None:
                cliente.email = email
            if telefone is not None:
                cliente.telefone = telefone
            if estado is not None:
                cliente.estado = estado
            if cidade is not None:
                cliente.cidade = cidade
            if bairro is not None:
                cliente.bairro = bairro
            if endereco is not None:
                cliente.endereco = endereco
            if cpf is not None:
                cliente.cpf = cpf
            if data_aniversario is not None:
                cliente.data_aniversario = data_aniversario
            if origem_cliente is not None:
                cliente.origem_cliente = origem_cliente
            if observacoes is not None:
                cliente.observacoes = observacoes

            return True
        return self._safe_query(query)

    def delete_cliente(self, cliente_id):
        """Exclui um cliente do banco de dados"""
        def query():
            cliente = self.session.query(Cliente).filter_by(id=cliente_id).first()
            if cliente:
                # Verificar se existem propostas associadas a este cliente
                propostas = self.session.query(Proposta).filter_by(cliente_id=cliente_id).all()
                if propostas:
                    return False, f"Não é possível excluir o cliente pois existem {len(propostas)} propostas associadas."
                
                # Verificar se existem vendas associadas a este cliente
                vendas = self.session.query(Venda).filter_by(cliente_id=cliente_id).all()
                if vendas:
                    return False, f"Não é possível excluir o cliente pois existem {len(vendas)} vendas associadas."
                
                # Se não houver registros associados, podemos excluir
                self.session.delete(cliente)
                return True, "Cliente excluído com sucesso."
            return False, "Cliente não encontrado."
        return self._safe_query(query)
        
    def delete_multiple_clientes(self, cliente_ids):
        """Exclui múltiplos clientes do banco de dados"""
        def query():
            resultados = {
                "sucesso": [],
                "erro": []
            }
            
            # Primeiro verifica se todos os IDs são válidos
            clientes_validos = []
            for cliente_id in cliente_ids:
                # Verificar se o ID é um número inteiro válido
                try:
                    cliente_id = int(cliente_id)
                    cliente = self.session.query(Cliente).filter_by(id=cliente_id).first()
                    if cliente:
                        clientes_validos.append((cliente_id, cliente))
                    else:
                        resultados["erro"].append({
                            "id": cliente_id,
                            "nome": "Desconhecido",
                            "mensagem": "Cliente não encontrado"
                        })
                except (ValueError, TypeError):
                    resultados["erro"].append({
                        "id": str(cliente_id),
                        "nome": "Inválido",
                        "mensagem": "ID de cliente inválido"
                    })
            
            # Processa os clientes válidos
            for cliente_id, cliente in clientes_validos:
                # Verificar se existem propostas associadas a este cliente
                propostas = self.session.query(Proposta).filter_by(cliente_id=cliente_id).all()
                if propostas:
                    resultados["erro"].append({
                        "id": cliente_id,
                        "nome": cliente.nome,
                        "mensagem": f"Existem {len(propostas)} propostas associadas"
                    })
                    continue
                
                # Verificar se existem vendas associadas a este cliente
                vendas = self.session.query(Venda).filter_by(cliente_id=cliente_id).all()
                if vendas:
                    resultados["erro"].append({
                        "id": cliente_id,
                        "nome": cliente.nome,
                        "mensagem": f"Existem {len(vendas)} vendas associadas"
                    })
                    continue
                
                # Se não houver registros associados, podemos excluir
                self.session.delete(cliente)
                resultados["sucesso"].append({
                    "id": cliente_id,
                    "nome": cliente.nome
                })
            
            # Commit se houver exclusões bem-sucedidas
            if resultados["sucesso"]:
                self.session.commit()
            
            return resultados
        
        return self._safe_query(query)

    def excluir_proposta(self, proposta_id_param):
        """Exclui uma proposta e seus registros relacionados usando o ID da proposta"""
        def query():
            # Usar o parâmetro recebido dentro da função query
            proposta_id = proposta_id_param
            
            # Converter para int se for string
            try:
                if isinstance(proposta_id, str):
                    proposta_id = int(proposta_id)
                
                print(f"DEBUG DATABASE: Excluindo proposta ID: {proposta_id} - Tipo: {type(proposta_id)}")
                
                # Verificar se a proposta existe
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                print(f"DEBUG DATABASE: Proposta encontrada: {proposta is not None}")
                
                if proposta:
                    try:
                        # Excluir registros financeiros relacionados primeiro
                        # Esta é a tabela que estava causando a violação de chave estrangeira
                        transacoes = self.session.query(Transacao).filter_by(proposta_id=proposta_id).all()
                        print(f"DEBUG DATABASE: {len(transacoes)} transações financeiras encontradas para exclusão")
                        self.session.query(Transacao).filter_by(proposta_id=proposta_id).delete()
                    
                        # Excluir outros registros relacionados
                        andamentos = self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).all()
                        print(f"DEBUG DATABASE: {len(andamentos)} andamentos encontrados para exclusão")
                        self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).delete()
                        
                        produtos = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id).all()
                        print(f"DEBUG DATABASE: {len(produtos)} produtos encontrados para exclusão")
                        self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id).delete()
                        
                        # Usar SQL direto em vez de ORM para evitar problemas com a coluna percentual_comissao
                        from sqlalchemy import text
                        # Contar acréscimos primeiro
                        count_result = self.session.execute(text(f"SELECT COUNT(*) FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                        count = count_result.scalar()
                        print(f"DEBUG DATABASE: {count} acréscimos encontrados para exclusão")
                        
                        # Usar SQL direto para excluir
                        self.session.execute(text(f"DELETE FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                        
                        # Excluir vendas que foram geradas automaticamente a partir desta proposta
                        # 1. Identificar vendas relacionadas
                        vendas_result = self.session.execute(text(f"""
                            SELECT id FROM vendas 
                            WHERE proposta_id = {proposta_id} 
                            OR observacoes LIKE '%Venda gerada%proposta%{proposta_id}%'
                            OR observacoes LIKE '%Venda gerada%proposta%#{proposta.numero}%'
                        """))
                        
                        vendas_ids = [row[0] for row in vendas_result]
                        if vendas_ids:
                            print(f"DEBUG DATABASE: Encontradas {len(vendas_ids)} vendas relacionadas à proposta para exclusão")
                            
                            # Para cada venda, excluir seus itens
                            for venda_id in vendas_ids:
                                # Excluir itens da venda
                                self.session.execute(text(f"DELETE FROM itens_venda WHERE venda_id = {venda_id}"))
                                
                                # Excluir transações relacionadas à venda
                                self.session.execute(text(f"DELETE FROM financeiro WHERE origem_id = {venda_id} AND origem_tipo = 'venda'"))
                                
                                # Excluir a venda
                                self.session.execute(text(f"DELETE FROM vendas WHERE id = {venda_id}"))
                            
                            print(f"DEBUG DATABASE: Vendas relacionadas excluídas com sucesso")
                        
                        # Excluir a proposta
                        print(f"DEBUG DATABASE: Excluindo proposta ID: {proposta_id}")
                        self.session.delete(proposta)
                        print(f"DEBUG DATABASE: Proposta excluída com sucesso")
                        
                        return True, "Proposta excluída com sucesso"
                    except Exception as e:
                        self.session.rollback()
                        print(f"DEBUG DATABASE ERROR: Erro ao excluir proposta: {str(e)}")
                        return False, f"Erro ao excluir proposta: {str(e)}"
                else:
                    print(f"DEBUG DATABASE: Proposta ID {proposta_id} não encontrada")
                    return False, f"Proposta ID {proposta_id} não encontrada"
            except Exception as e:
                print(f"DEBUG DATABASE ERROR: Erro ao processar ID da proposta: {str(e)}")
                return False, f"Erro ao processar ID da proposta: {str(e)}"
                
        return self._safe_query(query)
    
    def excluir_proposta_por_numero(self, numero_proposta):
        """
        Exclui uma proposta pelo seu número (não pelo ID)
        
        Returns:
            dict: Dicionário com as chaves 'status' (bool) e 'message' (str)
        """
        def query():
            try:
                proposta = self.session.query(Proposta).filter_by(numero=numero_proposta).first()
                if proposta:
                    # Armazenar o ID em uma variável local
                    proposta_id_local = proposta.id
                    
                    print(f"DEBUG DATABASE: Excluindo proposta #{numero_proposta} (ID: {proposta_id_local})")
                    
                    try:
                        # Excluir registros financeiros relacionados primeiro
                        # Esta é a tabela que estava causando a violação de chave estrangeira
                        transacoes = self.session.query(Transacao).filter_by(proposta_id=proposta_id_local).all()
                        print(f"DEBUG DATABASE: {len(transacoes)} transações financeiras encontradas para exclusão")
                        self.session.query(Transacao).filter_by(proposta_id=proposta_id_local).delete()
                    
                        # Excluir outros registros relacionados
                        andamentos = self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id_local).all()
                        print(f"DEBUG DATABASE: {len(andamentos)} andamentos encontrados para exclusão")
                        self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id_local).delete()
                        
                        produtos = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_local).all()
                        print(f"DEBUG DATABASE: {len(produtos)} produtos encontrados para exclusão")
                        self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_local).delete()
                        
                        # Usar SQL direto em vez de ORM para evitar problemas com a coluna percentual_comissao
                        from sqlalchemy import text
                        # Contar acréscimos primeiro
                        count_result = self.session.execute(text(f"SELECT COUNT(*) FROM acrescimos_proposta WHERE proposta_id = {proposta_id_local}"))
                        count = count_result.scalar()
                        print(f"DEBUG DATABASE: {count} acréscimos encontrados para exclusão")
                        
                        # Usar SQL direto para excluir
                        self.session.execute(text(f"DELETE FROM acrescimos_proposta WHERE proposta_id = {proposta_id_local}"))
                        
                        # Excluir vendas que foram geradas automaticamente a partir desta proposta
                        # 1. Identificar vendas relacionadas
                        vendas_result = self.session.execute(text(f"""
                            SELECT id FROM vendas 
                            WHERE proposta_id = {proposta_id_local} 
                            OR observacoes LIKE '%Venda gerada%proposta%{proposta_id_local}%'
                            OR observacoes LIKE '%Venda gerada%proposta%#{numero_proposta}%'
                        """))
                        
                        vendas_ids = [row[0] for row in vendas_result]
                        if vendas_ids:
                            print(f"DEBUG DATABASE: Encontradas {len(vendas_ids)} vendas relacionadas à proposta para exclusão")
                            
                            # Para cada venda, excluir seus itens
                            for venda_id in vendas_ids:
                                # Excluir itens da venda
                                self.session.execute(text(f"DELETE FROM itens_venda WHERE venda_id = {venda_id}"))
                                
                                # Excluir transações relacionadas à venda
                                self.session.execute(text(f"DELETE FROM financeiro WHERE origem_id = {venda_id} AND origem_tipo = 'venda'"))
                                
                                # Excluir a venda
                                self.session.execute(text(f"DELETE FROM vendas WHERE id = {venda_id}"))
                            
                            print(f"DEBUG DATABASE: Vendas relacionadas excluídas com sucesso")
                        
                        # Excluir a proposta
                        print(f"DEBUG DATABASE: Excluindo proposta")
                        self.session.delete(proposta)
                        print(f"DEBUG DATABASE: Proposta excluída com sucesso")
                        
                        return {"status": True, "message": "Proposta excluída com sucesso"}
                    except Exception as e:
                        self.session.rollback()
                        print(f"DEBUG DATABASE ERROR: Erro ao excluir proposta: {str(e)}")
                        return {"status": False, "message": f"Erro ao excluir proposta: {str(e)}"}
                else:
                    print(f"DEBUG DATABASE: Proposta #{numero_proposta} não encontrada")
                    return {"status": False, "message": f"Proposta #{numero_proposta} não encontrada"}
            except Exception as e:
                print(f"DEBUG DATABASE ERROR: Erro ao processar número da proposta: {str(e)}")
                return {"status": False, "message": f"Erro ao processar número da proposta: {str(e)}"}
        return self._safe_query(query)

    def remover_acrescimo(self, acrescimo_id):
        """
        Remove um acréscimo da proposta pelo ID
        
        Args:
            acrescimo_id (int): ID do acréscimo a ser removido
            
        Returns:
            bool: True se removido com sucesso, False se não encontrou o acréscimo
        """
        def query():
            try:
                # Converter para int para garantir tipo correto
                acrescimo_id_int = int(acrescimo_id)
                
                # Utilizar SQL direto em vez de ORM para evitar problemas com a coluna percentual_comissao
                from sqlalchemy import text
                
                # Verificar se o acréscimo existe
                count_result = self.session.execute(
                    text(f"SELECT COUNT(*) FROM acrescimos_proposta WHERE id = {acrescimo_id_int}")
                )
                count = count_result.scalar()
                
                if count == 0:
                    print(f"DEBUG: Acréscimo ID={acrescimo_id_int} não encontrado")
                    return False
                
                # Remover acréscimo com SQL direto
                self.session.execute(
                    text(f"DELETE FROM acrescimos_proposta WHERE id = {acrescimo_id_int}")
                )
                self.session.flush()
                
                print(f"DEBUG: Acréscimo ID={acrescimo_id_int} removido com sucesso")
                return True
                
            except Exception as e:
                print(f"ERRO ao remover acréscimo: {str(e)}")
                import traceback
                traceback.print_exc()
                raise Exception(f"Erro ao remover acréscimo: {str(e)}")
                
        return self._safe_query(query)
        
    def remover_produto_organizador(self, produto_id):
        """
        Remove um produto organizador da proposta pelo ID
        
        Args:
            produto_id (int): ID do produto organizador a ser removido
            
        Returns:
            bool: True se removido com sucesso, False se não encontrou o produto
        """
        def query():
            try:
                # Converter para int para garantir tipo correto
                produto_id_int = int(produto_id)
                
                # Verificar se o produto existe usando o ORM
                produto = self.session.query(ProdutoOrganizador).filter_by(id=produto_id_int).first()
                
                if not produto:
                    print(f"DEBUG: Produto Organizador ID={produto_id_int} não encontrado")
                    return False
                
                # Verificar isolamento de dados através da proposta
                if self.usuario_id:
                    proposta = self.session.query(Proposta).filter_by(id=produto.proposta_id).first()
                    if proposta and proposta.usuario_id != self.usuario_id:
                        print(f"DEBUG: VIOLAÇÃO DE ISOLAMENTO! Tentativa de remover produto de outro usuário")
                        raise ValueError("Você não tem permissão para remover este produto")
                
                # Excluir o produto
                self.session.delete(produto)
                self.session.flush()
                
                print(f"DEBUG: Produto Organizador ID={produto_id_int} removido com sucesso")
                return True
                
            except Exception as e:
                print(f"ERRO ao remover produto organizador: {str(e)}")
                import traceback
                traceback.print_exc()
                raise Exception(f"Erro ao remover produto organizador: {str(e)}")
                
        return self._safe_query(query)
        
    def atualizar_status_pagamento_acrescimo(self, proposta_id, tipo, status):
        """Atualiza o status de pagamento de um acréscimo"""
        def query():
            # Usar SQL direto em vez de ORM para evitar problemas com a coluna percentual_comissao
            from sqlalchemy import text
            
            # Verificar se o acréscimo existe
            count_result = self.session.execute(
                text(f"SELECT COUNT(*) FROM acrescimos_proposta WHERE proposta_id = {proposta_id} AND tipo = '{tipo}'")
            )
            count = count_result.scalar()
            
            if count > 0:
                # Usar SQL direto para atualizar
                self.session.execute(
                    text(f"UPDATE acrescimos_proposta SET status_pagamento = '{status}' WHERE proposta_id = {proposta_id} AND tipo = '{tipo}'")
                )
                return True
            return False
        return self._safe_query(query)

    def atualizar_pagamento_base_proposta(self, proposta_id, status_pagamento_base="Recebido"):
        """
        Atualiza o status de pagamento do valor base de uma proposta
        
        Args:
            proposta_id: ID da proposta
            status_pagamento_base: Status do pagamento ("Pendente", "Recebido")
            
        Returns:
            bool: True se atualizado com sucesso, False se não encontrou a proposta
        """
        # # print(f"DEBUG: Atualizando status de pagamento da proposta ID={proposta_id} para {status_pagamento_base}")
        
        def query():
            try:
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                
                if not proposta:
                    # # print(f"DEBUG: Proposta ID={proposta_id} não encontrada")
                    return False
                
                # Atualizar status de pagamento
                proposta.status_pagamento_base = status_pagamento_base
                
                # Se marcou como recebido, registrar data de recebimento
                if status_pagamento_base == "Recebido":
                    # Verificar se já existe uma transação para esta proposta
                    transacao_existente = self.session.query(Transacao).filter_by(
                        proposta_id=proposta_id,
                        tipo_receita="Valor Base"
                    ).first()
                    
                    # Se não existir transação, criar uma nova
                    if not transacao_existente:
                        transacao = Transacao(
                            tipo="receita",
                            descricao=f"Pagamento do valor base da proposta #{proposta.numero} - {proposta.descricao}",
                            valor=proposta.valor,
                            categoria="Proposta",
                            subcategoria=proposta.tipo_proposta if proposta.tipo_proposta else "Outros",
                            tipo_receita="Valor Base",
                            origem_id=proposta.id,
                            origem_tipo="proposta",
                            proposta_id=proposta.id,
                            tipo_conta="PF",
                            status="Recebido",
                            data_recebimento=datetime.now().date(),
                            classificacao="receita"
                        )
                        self.session.add(transacao)
                    
                # # print(f"DEBUG: Status de pagamento da proposta ID={proposta_id} atualizado com sucesso")
                return True
            
            except Exception as e:
                print(f"DEBUG ERROR: Erro ao atualizar status de pagamento da proposta: {str(e)}")
                import traceback
                traceback.print_exc()
                self.session.rollback()
                raise e
        
        return self._safe_query(query)

    def get_historico_pagamentos(self):
        """Retorna o histórico de pagamentos recebidos"""
        def query():
            # Buscar pagamentos de propostas
            propostas = self.session.query(Proposta).filter_by(status_pagamento_base='Recebido').all()
            historico = []

            # Adicionar valores base recebidos
            for p in propostas:
                historico.append({
                    'proposta': p.numero,
                    'cliente': p.cliente.nome,
                    'tipo': 'Valor Base',
                    'valor': p.valor,
                    'data_recebimento': p.data_proposta
                })

            # Adicionar acréscimos recebidos usando SQL direto em vez de ORM
            from sqlalchemy import text
            acrescimos_query = text("""
                SELECT a.id, a.tipo, a.valor, a.data_cadastro, p.numero as proposta_numero, c.nome as cliente_nome
                FROM acrescimos_proposta a
                JOIN propostas p ON a.proposta_id = p.id
                JOIN clientes c ON p.cliente_id = c.id
                WHERE a.status_pagamento = 'Recebido'
            """)
            acrescimos_result = self.session.execute(acrescimos_query)
            
            for row in acrescimos_result:
                historico.append({
                    'proposta': row.proposta_numero,
                    'cliente': row.cliente_nome,
                    'tipo': row.tipo,
                    'valor': row.valor,
                    'data_recebimento': row.data_cadastro
                })

            return pd.DataFrame(historico)
        return self._safe_query(query)
        
    # Métodos para gerenciamento de produtos
    def add_produto(self, nome, preco_custo, preco_venda, descricao=None, categoria=None, estoque=0):
        """Adiciona um novo produto ao catálogo"""
        def query():
            produto = Produto(
                nome=nome,
                descricao=descricao,
                preco_custo=float(preco_custo),
                preco_venda=float(preco_venda),
                categoria=categoria,
                estoque=int(estoque),
                usuario_id=self.usuario_id  # Adicionar o ID do usuário atual
            )
            self.session.add(produto)
            return produto.id
        return self._safe_query(query)
        
    def get_produtos(self):
        """Retorna todos os produtos cadastrados do usuário atual"""
        def query():
            # Criar consulta base
            query = self.session.query(Produto)
            
            # Adicionar filtro por usuário se disponível
            if self.usuario_id:
                query = query.filter(Produto.usuario_id == self.usuario_id)
                
            # Executar consulta
            produtos = query.all()
            
            return pd.DataFrame([{
                'id': p.id,
                'nome': p.nome,
                'descricao': p.descricao,
                'preco_custo': p.preco_custo,
                'preco_venda': p.preco_venda,
                'categoria': p.categoria,
                'estoque': p.estoque,
                'data_cadastro': p.data_cadastro,
                'usuario_id': p.usuario_id
            } for p in produtos])
        return self._safe_query(query)
        
    def update_produto(self, produto_id, nome=None, preco_custo=None, preco_venda=None, 
                      descricao=None, categoria=None, estoque=None):
        """Atualiza os dados de um produto"""
        def query():
            produto = self.session.query(Produto).filter_by(id=produto_id).first()
            if not produto:
                return False
                
            if nome is not None:
                produto.nome = nome
            if preco_custo is not None:
                produto.preco_custo = float(preco_custo)
            if preco_venda is not None:
                produto.preco_venda = float(preco_venda)
            if descricao is not None:
                produto.descricao = descricao
            if categoria is not None:
                produto.categoria = categoria
            if estoque is not None:
                produto.estoque = int(estoque)
                
            return True
        return self._safe_query(query)
        
    def delete_produto(self, produto_id):
        """Remove um produto do catálogo"""
        def query():
            produto = self.session.query(Produto).filter_by(id=produto_id).first()
            if produto:
                self.session.delete(produto)
                return True
            return False
        return self._safe_query(query)
        
    def atualizar_estoque(self, produto_id, quantidade):
        """Atualiza o estoque de um produto"""
        def query():
            produto = self.session.query(Produto).filter_by(id=produto_id).first()
            if produto:
                produto.estoque += quantidade
                return produto.estoque
            return None
        return self._safe_query(query)
        
    # Métodos para gerenciamento de vendas
    def add_venda(self, cliente_id, itens, forma_pagamento=None, observacoes=None):
        """
        Adiciona uma nova venda
        
        Args:
            cliente_id: ID do cliente
            itens: Lista de dicionários com produto_id, quantidade e preco_unitario
            forma_pagamento: Forma de pagamento
            observacoes: Observações sobre a venda
            
        Returns:
            ID da venda criada
        """
        def query():
            # Calcular valor total
            valor_total = 0
            
            venda = Venda(
                cliente_id=cliente_id,
                valor_total=0,  # Será atualizado após adicionar os itens
                forma_pagamento=forma_pagamento,
                observacoes=observacoes,
                usuario_id=self.usuario_id  # Adicionar o ID do usuário atual
            )
            self.session.add(venda)
            self.session.flush()  # Para obter o ID da venda
            
            # Adicionar itens
            for item in itens:
                produto_id = item['produto_id']
                quantidade = item['quantidade']
                
                # Obter produto e verificar estoque
                produto = self.session.query(Produto).filter_by(id=produto_id).first()
                if not produto:
                    raise Exception(f"Produto com ID {produto_id} não encontrado")
                
                if produto.estoque < quantidade:
                    raise Exception(f"Estoque insuficiente para o produto {produto.nome}")
                
                # Atualizar estoque
                produto.estoque -= quantidade
                
                # Adicionar item
                preco_unitario = item.get('preco_unitario', produto.preco_venda)
                subtotal = preco_unitario * quantidade
                
                item_venda = ItemVenda(
                    venda_id=venda.id,
                    produto_id=produto_id,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    subtotal=subtotal
                )
                self.session.add(item_venda)
                
                # Atualizar valor total
                valor_total += subtotal
            
            # Atualizar valor total da venda
            venda.valor_total = valor_total
            
            # Registrar transação financeira
            cliente = self.session.query(Cliente).filter_by(id=cliente_id).first()
            descricao = f"Venda para {cliente.nome}" if cliente else "Venda"
            
            self.add_transacao(
                tipo="receita",
                descricao=descricao,
                valor=valor_total,
                categoria="Vendas",
                origem_id=venda.id,
                origem_tipo="venda"
            )
            
            return venda.id
        return self._safe_query(query)
        
    def get_vendas(self):
        """Retorna todas as vendas realizadas do usuário atual"""
        def query():
            # Criar consulta base
            query = self.session.query(Venda)
            
            # Adicionar filtro por usuário se disponível
            if self.usuario_id:
                query = query.filter(Venda.usuario_id == self.usuario_id)
                
            # Executar consulta ordenada
            vendas = query.order_by(Venda.data_venda.desc()).all()
            
            return pd.DataFrame([{
                'id': v.id,
                'cliente_nome': v.cliente.nome if v.cliente else "Cliente não encontrado",
                'valor_total': v.valor_total,
                'data_venda': v.data_venda,
                'status': v.status,
                'forma_pagamento': v.forma_pagamento,
                'observacoes': v.observacoes,
                'usuario_id': v.usuario_id
            } for v in vendas])
        return self._safe_query(query)
        
    def get_itens_venda(self, venda_id):
        """Retorna os itens de uma venda específica"""
        def query():
            itens = self.session.query(ItemVenda).filter_by(venda_id=venda_id).all()
            return pd.DataFrame([{
                'id': i.id,
                'produto_nome': i.produto.nome if i.produto else i.descricao,
                'quantidade': i.quantidade,
                'preco_unitario': i.preco_unitario,
                'subtotal': i.subtotal,
                'lucro': (i.preco_unitario - (i.produto.preco_custo if i.produto else 0)) * i.quantidade
            } for i in itens])
        return self._safe_query(query)
        
    def cancelar_venda(self, venda_id):
        """Cancela uma venda e estorna os produtos para o estoque"""
        def query():
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if not venda or venda.status == 'Cancelada':
                return False
                
            venda.status = 'Cancelada'
            
            # Estornar produtos para o estoque
            for item in venda.itens:
                produto = item.produto
                if produto:
                    produto.estoque += item.quantidade
            
            # Cancelar transação financeira relacionada
            transacao = self.session.query(Transacao).filter_by(
                origem_id=venda_id,
                origem_tipo='venda'
            ).first()
            
            if transacao:
                transacao.status = 'Cancelado'
            
            return True
        return self._safe_query(query)
        
    def excluir_venda_com_sql(self, venda_id):
        """
        Exclui completamente uma venda usando SQL direto para evitar problemas de ORM.
        """
        def query():
            try:
                # # print(f"DEBUG: Excluindo venda ID {venda_id} com SQL direto")
                
                # Obter informações da venda antes de excluí-la para estornar produtos
                venda = self.session.query(Venda).filter_by(id=venda_id).first()
                
                if not venda:
                    # # print(f"DEBUG: Venda ID {venda_id} não encontrada")
                    return False
                
                # Estornar produtos para o estoque
                if venda.status != 'Cancelada' and hasattr(venda, 'itens'):
                    # # print(f"DEBUG: Estornando produtos para o estoque")
                    for item in venda.itens:
                        if hasattr(item, 'produto') and item.produto is not None:
                            # # print(f"DEBUG: Estornando {item.quantidade} unidades do produto {item.produto.id}")
                            item.produto.estoque += item.quantidade
                
                # Executar SQL para excluir na ordem correta
                # 1. Excluir transações financeiras relacionadas
                transacoes_stmt = text("""
                    DELETE FROM financeiro 
                    WHERE origem_id = :venda_id AND origem_tipo = 'venda'
                """)
                self.session.execute(transacoes_stmt, {"venda_id": venda_id})
                print("DEBUG: Excluídas transações financeiras relacionadas")
                
                # 2. Excluir itens da venda
                itens_stmt = text("""
                    DELETE FROM itens_venda
                    WHERE venda_id = :venda_id
                """)
                self.session.execute(itens_stmt, {"venda_id": venda_id})
                print("DEBUG: Excluídos itens da venda")
                
                # 3. Finalmente excluir a venda
                venda_stmt = text("""
                    DELETE FROM vendas
                    WHERE id = :venda_id
                """)
                self.session.execute(venda_stmt, {"venda_id": venda_id})
                # # print(f"DEBUG: Venda ID {venda_id} excluída com sucesso")
                
                return True
            except Exception as e:
                print(f"ERRO ao excluir venda: {str(e)}")
                import traceback
                print(traceback.format_exc())
                # Fazer rollback em caso de erro
                self.session.rollback()
                raise
        return self._safe_query(query)
    
    def excluir_venda(self, venda_id):
        """
        Exclui completamente uma venda e seus itens do banco de dados.
        Esta função tenta primeiro a abordagem ORM e, se falhar, usa SQL direto.
        
        Esta função deve ser usada com cautela, pois remove permanentemente os registros.
        Recomenda-se usar cancelar_venda() para a maioria dos casos para manter o histórico.
        """
        def query():
            try:
                # # print(f"DEBUG: Excluindo venda ID {venda_id}")
                venda = self.session.query(Venda).filter_by(id=venda_id).first()
                
                if not venda:
                    # # print(f"DEBUG: Venda ID {venda_id} não encontrada")
                    return False
                
                # # print(f"DEBUG: Venda encontrada: {venda.id} - status: {venda.status}")
                
                # Estornar produtos para o estoque antes de excluir
                if hasattr(venda, 'itens'):
                    # # print(f"DEBUG: Processando {len(venda.itens)} itens da venda")
                    for item in venda.itens:
                        if hasattr(item, 'produto') and item.produto is not None:
                            # # print(f"DEBUG: Estornando {item.quantidade} unidades do produto {item.produto.id}")
                            if venda.status != 'Cancelada':
                                item.produto.estoque += item.quantidade
                        else:
                            # # print(f"DEBUG: Item sem produto associado")
                            pass
                else:
                    # # print(f"DEBUG: Venda não possui itens relacionados")
                    pass
                
                # Verificar e excluir transações financeiras relacionadas
                transacoes = self.session.query(Transacao).filter_by(
                    origem_id=venda_id,
                    origem_tipo='venda'
                ).all()
                
                # # print(f"DEBUG: Encontradas {len(transacoes)} transações financeiras relacionadas")
                for transacao in transacoes:
                    # # print(f"DEBUG: Excluindo transação ID {transacao.id}")
                    self.session.delete(transacao)
                
                # Para lidar com possíveis referências à proposta
                print("DEBUG: Verificando se venda está relacionada a uma proposta")
                if hasattr(venda, 'proposta_id') and venda.proposta_id:
                    # # print(f"DEBUG: Venda relacionada à proposta ID {venda.proposta_id}")
                    # Apenas desvincular, não excluir a proposta
                    venda.proposta_id = None
                
                # Remover itens da venda primeiro (devido à restrição de chave estrangeira)
                if hasattr(venda, 'itens'):
                    itens = list(venda.itens)  # Criar uma cópia da lista para evitar problemas de iteração
                    for item in itens:
                        # # print(f"DEBUG: Excluindo item de venda ID {item.id}")
                        self.session.delete(item)
                
                # Por precaução, realizar flush antes de excluir a venda
                self.session.flush()
                
                # Remover a venda
                # # print(f"DEBUG: Finalmente excluindo a venda ID {venda_id}")
                self.session.delete(venda)
                
                # Realizar flush novamente para garantir a exclusão
                self.session.flush()
                
                # # print(f"DEBUG: Venda ID {venda_id} excluída com sucesso com ORM")
                return True
            except Exception as e:
                print(f"ERRO ao excluir venda com ORM: {str(e)}")
                print("Tentando excluir com SQL direto...")
                self.session.rollback()  # Garantir que a sessão está limpa
                
                # Tentar com SQL direto
                try:
                    # Obter informações da venda antes de excluí-la para estornar produtos
                    venda = self.session.query(Venda).filter_by(id=venda_id).first()
                    
                    if not venda:
                        # # print(f"DEBUG: Venda ID {venda_id} não encontrada")
                        return False
                    
                    # Estornar produtos para o estoque
                    if venda.status != 'Cancelada' and hasattr(venda, 'itens'):
                        # # print(f"DEBUG: Estornando produtos para o estoque")
                        for item in venda.itens:
                            if hasattr(item, 'produto') and item.produto is not None:
                                # # print(f"DEBUG: Estornando {item.quantidade} unidades do produto {item.produto.id}")
                                item.produto.estoque += item.quantidade
                    
                    # Executar SQL para excluir na ordem correta
                    # 1. Excluir transações financeiras relacionadas
                    self.session.execute(text("""
                        DELETE FROM financeiro 
                        WHERE origem_id = :venda_id AND origem_tipo = 'venda'
                    """), {"venda_id": venda_id})
                    print("DEBUG: Excluídas transações financeiras relacionadas")
                    
                    # 2. Excluir itens da venda
                    self.session.execute(text("""
                        DELETE FROM itens_venda
                        WHERE venda_id = :venda_id
                    """), {"venda_id": venda_id})
                    print("DEBUG: Excluídos itens da venda")
                    
                    # 3. Atualizar vendas para remover referência à proposta
                    self.session.execute(text("""
                        UPDATE vendas
                        SET proposta_id = NULL
                        WHERE id = :venda_id
                    """), {"venda_id": venda_id})
                    print("DEBUG: Removida referência à proposta")
                    
                    # 4. Finalmente excluir a venda
                    self.session.execute(text("""
                        DELETE FROM vendas
                        WHERE id = :venda_id
                    """), {"venda_id": venda_id})
                    # # print(f"DEBUG: Venda ID {venda_id} excluída com sucesso com SQL direto")
                    
                    return True
                except Exception as e2:
                    print(f"ERRO ao excluir venda com SQL direto: {str(e2)}")
                    import traceback
                    print(traceback.format_exc())
                    raise
        return self._safe_query(query)
        
    def adicionar_venda_a_proposta(self, proposta_id, itens, forma_pagamento=None, observacoes=None):
        """
        Adiciona uma venda diretamente a uma proposta existente, criando um acréscimo do tipo "Produto"
        
        Args:
            proposta_id: ID da proposta
            itens: Lista de itens da venda, onde cada item é um dicionário com as chaves:
                   - produto_id: ID do produto
                   - quantidade: quantidade do produto
                   - preco_unitario: preço unitário do produto
            forma_pagamento: Forma de pagamento (opcional)
            observacoes: Observações sobre a venda (opcional)
            
        Returns:
            int: ID da venda criada, ou None em caso de erro
        """
        def query():
            # Primeiro recuperar a proposta para obter cliente_id
            proposta = self.session.query(Proposta).filter(Proposta.id == proposta_id).first()
            
            if not proposta:
                raise ValueError(f"Proposta {proposta_id} não encontrada")
                
            cliente_id = proposta.cliente_id
            
            # 1. Criar a venda normalmente
            # Criar objeto de venda
            venda = Venda(
                cliente_id=cliente_id,
                data_venda=datetime.now(),
                status='Concluída',
                forma_pagamento=forma_pagamento or 'Vinculada à Proposta',
                observacoes=observacoes
            )
            self.session.add(venda)
            self.session.flush()  # Obter o ID da venda
            
            # Calcular valor total da venda
            valor_total = 0
            
            # Adicionar itens da venda
            for item_data in itens:
                produto_id = item_data['produto_id']
                quantidade = item_data['quantidade']
                preco_unitario = item_data['preco_unitario']
                subtotal = quantidade * preco_unitario
                
                produto = self.session.query(Produto).filter(Produto.id == produto_id).first()
                if not produto:
                    raise ValueError(f"Produto {produto_id} não encontrado")
                
                # Criar item de venda
                item = ItemVenda(
                    venda_id=venda.id,
                    produto_id=produto_id,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    subtotal=subtotal
                )
                self.session.add(item)
                
                # Atualizar valor total
                valor_total += subtotal
            
            # 2. Adicionar o valor da venda como acréscimo na proposta
            # Detalhes para o acréscimo
            desc_acrescimo = f"Venda #{venda.id} - {len(itens)} itens"
            if observacoes:
                desc_acrescimo += f" - {observacoes}"
                
            # Criar acréscimo
            acrescimo = AcrescimoProposta(
                proposta_id=proposta_id,
                tipo="Produto",
                fornecedor=f"Venda interna #{venda.id}",
                descricao=desc_acrescimo,
                valor=valor_total
            )
            self.session.add(acrescimo)
            
            # Atualizar valor total da venda
            venda.valor_total = valor_total
            
            # Criar um registro para vincular a venda à proposta
            proposta.observacoes = (proposta.observacoes or '') + f"\nVenda #{venda.id} adicionada em {datetime.now().strftime('%d/%m/%Y')}"
            
            # Não precisamos chamar commit explicitamente pois _safe_query faz isso
            return venda.id
            
        return self._safe_query(query)
    
    def criar_venda_de_proposta(self, proposta_id, produtos=None, forma_pagamento='À vista'):
        """
        Cria uma venda a partir de uma proposta
        
        Args:
            proposta_id: ID da proposta
            produtos: Lista opcional de produtos da proposta a incluir na venda
                      Se None, serão incluídos todos os produtos da proposta
            forma_pagamento: Forma de pagamento da venda
            
        Returns:
            dict: Dicionário com informações sobre a venda criada
        """
        def query():
            # Buscar a proposta
            proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
            if not proposta:
                raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
            # Verificar se a proposta já tem uma venda associada
            venda_existente = self.session.query(Venda).filter_by(proposta_id=proposta_id).first()
            if venda_existente:
                return {
                    "status": "venda_existente", 
                    "venda_id": venda_existente.id,
                    "message": f"Já existe uma venda (ID: {venda_existente.id}) para esta proposta"
                }
            
            # Buscar produtos da proposta
            produtos_proposta = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id).all()
            if not produtos_proposta:
                # Criar uma venda apenas com o valor da proposta como serviço
                venda = Venda(
                    cliente_id=proposta.cliente_id,
                    valor_total=proposta.valor,
                    forma_pagamento=forma_pagamento,
                    observacoes=f"Venda gerada da proposta #{proposta.numero} - {proposta.descricao}",
                    proposta_id=proposta_id,
                    status="Concluída"
                )
                self.session.add(venda)
                self.session.flush()
                
                # Criar um item virtual para representar o serviço
                item_venda = ItemVenda(
                    venda_id=venda.id,
                    produto_id=None,  # Sem produto físico
                    quantidade=1,
                    preco_unitario=proposta.valor,
                    subtotal=proposta.valor,
                    descricao=f"Serviço: {proposta.descricao}"
                )
                self.session.add(item_venda)
                
                # Registrar transação financeira se já não existir
                self._registrar_transacao_venda(venda, proposta)
                
                # Atualizar status da proposta para vendida
                proposta.status_execucao = "Vendida"
                
                return {
                    "status": "sucesso",
                    "venda_id": venda.id,
                    "valor": venda.valor_total,
                    "tipo": "serviço",
                    "message": "Venda de serviço criada com sucesso"
                }
            
            # Lista para armazenar os itens da venda
            itens_venda = []
            valor_total = 0
            
            # Filtrar produtos se uma lista específica foi fornecida
            if produtos and len(produtos) > 0:
                produtos_filtrados = [p for p in produtos_proposta if p.id in produtos]
            else:
                produtos_filtrados = produtos_proposta
                
            # Preparar itens de venda
            for produto in produtos_filtrados:
                item = {
                    "produto_id": produto.id,
                    "quantidade": produto.quantidade,
                    "preco_unitario": produto.valor
                }
                itens_venda.append(item)
                valor_total += produto.valor * produto.quantidade
            
            # Criar venda
            venda = Venda(
                cliente_id=proposta.cliente_id,
                valor_total=valor_total,
                forma_pagamento=forma_pagamento,
                observacoes=f"Venda gerada da proposta #{proposta.numero} - {proposta.descricao}",
                proposta_id=proposta_id,
                status="Concluída"
            )
            self.session.add(venda)
            self.session.flush()
            
            # Adicionar itens à venda
            for item in itens_venda:
                item_venda = ItemVenda(
                    venda_id=venda.id,
                    produto_id=item["produto_id"],
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco_unitario"],
                    subtotal=item["quantidade"] * item["preco_unitario"]
                )
                self.session.add(item_venda)
            
            # Registrar transação financeira
            self._registrar_transacao_venda(venda, proposta)
            
            # Atualizar status da proposta
            proposta.status_execucao = "Vendida"
            
            return {
                "status": "sucesso",
                "venda_id": venda.id,
                "valor": valor_total,
                "tipo": "produtos",
                "itens": len(itens_venda),
                "message": f"Venda com {len(itens_venda)} itens criada com sucesso"
            }
        
        return self._safe_query(query)
    
    def _registrar_transacao_venda(self, venda, proposta):
        """Registra transações financeiras para a venda, incluindo comissões de fornecedores"""
        resultados = []
        
        # 1. Registrar a transação principal da venda
        # Verificar se já existe uma transação para esta venda
        transacao_existente = self.session.query(Transacao).filter_by(
            origem_id=venda.id,
            origem_tipo="venda"
        ).first()
        
        if not transacao_existente:
            transacao = Transacao(
                tipo="receita",
                descricao=f"Venda da proposta #{proposta.numero} - {proposta.descricao}",
                valor=venda.valor_total,
                categoria="Vendas",
                subcategoria=proposta.tipo_proposta,
                tipo_receita="Venda",
                origem_id=venda.id,
                origem_tipo="venda",
                proposta_id=proposta.id,
                tipo_conta="PF",
                status="Recebido",
                data_recebimento=datetime.now().date(),
                classificacao="receita"
            )
            self.session.add(transacao)
            self.session.flush()
            resultados.append(transacao.id)
            
            # 2. Registrar comissões de fornecedores
            # Buscar os acréscimos do tipo FORNECEDOR para esta proposta
            # # print(f"DEBUG: Buscando acréscimos do tipo FORNECEDOR para proposta ID={proposta.id}")
            fornecedores = self.session.query(AcrescimoProposta).filter(
                AcrescimoProposta.proposta_id == proposta.id,
                AcrescimoProposta.tipo == "FORNECEDOR"
            ).all()
            
            # # print(f"DEBUG: Encontrados {len(fornecedores)} acréscimos do tipo FORNECEDOR")
            
            # Para cada fornecedor, verificar se tem percentual de comissão e gerar receita
            for fornecedor in fornecedores:
                # Verificar se já existe comissão para este fornecedor
                comissao_existente = self.session.query(Transacao).filter(
                    Transacao.proposta_id == proposta.id,
                    Transacao.descricao.like(f"%Comissão%{fornecedor.fornecedor}%")
                ).first()
                
                if not comissao_existente and fornecedor.percentual_comissao and fornecedor.percentual_comissao > 0:
                    # # print(f"DEBUG: Gerando comissão para fornecedor {fornecedor.fornecedor} com percentual {fornecedor.percentual_comissao}%")
                    
                    # Calcular valor da comissão
                    valor_comissao = fornecedor.valor * (fornecedor.percentual_comissao / 100.0)
                    
                    # Criar transação de comissão a receber
                    comissao = Transacao(
                        tipo="receita_a_receber",
                        descricao=f"Comissão de {fornecedor.percentual_comissao}% - {fornecedor.fornecedor} - Proposta #{proposta.numero}",
                        valor=valor_comissao,
                        categoria="Comissões",
                        subcategoria="Comissão de Fornecedor",
                        tipo_receita="Comissão",
                        origem_id=venda.id,
                        origem_tipo="venda",
                        proposta_id=proposta.id,
                        tipo_conta="PF",
                        status="Pendente",
                        data_vencimento=datetime.now().date() + timedelta(days=30),
                        classificacao="receita_a_receber"
                    )
                    self.session.add(comissao)
                    self.session.flush()
                    resultados.append(comissao.id)
                    # # print(f"DEBUG: Comissão registrada com ID {comissao.id} e valor {valor_comissao}")
                elif comissao_existente:
                    # # print(f"DEBUG: Comissão já existente para fornecedor {fornecedor.fornecedor}: {comissao_existente.id}")
                    pass
                else:
                    # # print(f"DEBUG: Fornecedor {fornecedor.fornecedor} sem percentual de comissão ou com percentual zero")
                    pass
            
        return resultados
        
    def add_fornecedor_proposta(self, proposta_id, fornecedor_id, valor, observacoes=None, percentual_comissao=None):
        """
        Adiciona um fornecedor à proposta como um acréscimo
        
        Args:
            proposta_id: ID da proposta
            fornecedor_id: ID do fornecedor
            valor: Valor do fornecimento
            observacoes: Observações (opcional)
            percentual_comissao: Parâmetro mantido por compatibilidade, mas será ignorado em favor do percentual cadastrado no fornecedor
            
        Returns:
            dict: Informações sobre o acréscimo adicionado e comissão gerada
        """
        try:
            # Converter para tipos nativos
            proposta_id_int = int(proposta_id)
            fornecedor_id_int = int(fornecedor_id)
            valor_float = float(valor)
            
            def query():
                # Buscar fornecedor
                fornecedor = self.session.query(Fornecedor).filter_by(id=fornecedor_id_int).first()
                if not fornecedor:
                    raise ValueError(f"Fornecedor ID {fornecedor_id} não encontrado")
                    
                # Buscar proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
                # Usar SEMPRE o percentual cadastrado no fornecedor
                percentual_fornecedor = fornecedor.percentual_comissao if fornecedor.percentual_comissao is not None else 0.0
                # # print(f"DEBUG: Usando percentual de comissão do fornecedor: {percentual_fornecedor}%")
                
                # Criar acréscimo usando a função existente
                resultado = self.add_acrescimo_proposta(
                    proposta_id=proposta_id_int,
                    tipo="FORNECEDOR",  # Garantir que o tipo está em maiúsculo
                    valor=valor_float,
                    descricao=observacoes if observacoes else f"Fornecimento de {fornecedor.descricao}",
                    fornecedor=fornecedor.descricao,
                    status_pagamento="Pendente",
                    percentual_comissao=percentual_fornecedor
                )
                
                return resultado
                
            return self._safe_query(query)
            
        except Exception as e:
            print(f"ERRO ao adicionar fornecedor à proposta: {str(e)}")
            raise
    
    def add_assistente_proposta(self, proposta_id, assistente_id, valor, observacoes=None):
        """
        Adiciona um assistente à proposta como um acréscimo
        
        Args:
            proposta_id: ID da proposta
            assistente_id: ID do assistente
            valor: Valor do serviço
            observacoes: Observações (opcional)
            
        Returns:
            dict: Informações sobre o acréscimo adicionado e despesa gerada
        """
        try:
            # Converter para tipos nativos
            proposta_id_int = int(proposta_id)
            assistente_id_int = int(assistente_id)
            valor_float = float(valor)
            
            def query():
                # Buscar assistente
                assistente = self.session.query(Assistente).filter_by(id=assistente_id_int).first()
                if not assistente:
                    raise ValueError(f"Assistente ID {assistente_id} não encontrado")
                    
                # Buscar proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
                # Usar a função add_acrescimo_proposta para criar o acréscimo e gerar a despesa automaticamente
                # # print(f"DEBUG: Adicionando assistente {assistente.nome} à proposta {proposta_id_int} com valor {valor_float}")
                resultado = self.add_acrescimo_proposta(
                    proposta_id=proposta_id_int,
                    tipo="ASSISTENTE",  # Garantir que o tipo está em maiúsculo
                    valor=valor_float,
                    descricao=observacoes if observacoes else f"Serviço de {assistente.nome}",
                    fornecedor=assistente.nome,
                    status_pagamento="Pendente"
                )
                
                # # print(f"DEBUG: Resultado da adição de assistente: {resultado}")
                return resultado
                
            return self._safe_query(query)
            
        except Exception as e:
            print(f"ERRO ao adicionar assistente à proposta: {str(e)}")
            raise
            
    def limpar_propostas(self):
        """
        Remove todas as propostas e dados relacionados, reiniciando a sequência de numeração.
        Mantém os clientes, fornecedores e assistentes intactos.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        def query():
            try:
                # Deletar tabelas na ordem correta para evitar violação de chave estrangeira
                # Primeiro os andamentos de proposta
                self.session.query(AndamentoProposta).delete()
                
                # Remover produtos associados a propostas
                self.session.query(ProdutoOrganizador).delete()
                
                # Remover acréscimos
                self.session.query(AcrescimoProposta).delete()
                
                # Remover transações financeiras relacionadas a propostas
                # (isso é opcional, dependendo da sua estrutura de dados)
                receitas = self.session.query(Receita).filter(Receita.tipo == "Proposta").all()
                for receita in receitas:
                    self.session.delete(receita)
                
                despesas = self.session.query(Despesa).filter(Despesa.tipo == "Proposta").all()
                for despesa in despesas:
                    self.session.delete(despesa)
                
                # Finalmente, remover as propostas
                self.session.query(Proposta).delete()
                
                # Reset da sequência (específico para PostgreSQL)
                self.session.execute("ALTER SEQUENCE propostas_id_seq RESTART WITH 1;")
                self.session.execute("ALTER SEQUENCE propostas_numero_seq RESTART WITH 1;")
                
                # Commit das alterações
                self.session.commit()
                return True
                
            except Exception as e:
                self.session.rollback()
                print(f"Erro ao limpar propostas: {str(e)}")
                raise
                
        return self._safe_query(query)
        
    def gerar_lancamentos_financeiros_proposta_concluida(self, proposta_id, forcar_geracao=False):
        """
        Gera lançamentos financeiros automáticos quando uma proposta é marcada como concluída
        
        Gera:
        1. Produtos a receber (valor total dos produtos)
        2. Comissão a receber por fornecedor (com % registrado no cadastro) - APENAS para propostas concluídas
        3. Assistentes a pagar (um registro por assistente) - APENAS para propostas concluídas
        4. Cliente a receber (valor base da proposta)
        
        Args:
            proposta_id: ID da proposta concluída
            forcar_geracao: Se True, remove lançamentos existentes e gera novos (para reabertura)
            
        Returns:
            dict: Resumo dos lançamentos gerados
        """
        def query():
            try:
                # Converter para inteiro se for string
                proposta_id_int = int(proposta_id)
                print(f"DEBUG LANCAMENTOS: Gerando lançamentos financeiros para proposta ID={proposta_id_int}")
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    print(f"DEBUG LANCAMENTOS: Proposta ID {proposta_id} não encontrada")
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
                print(f"DEBUG LANCAMENTOS: Proposta encontrada: #{proposta.numero} - {proposta.descricao}")
                
                # Buscar cliente da proposta
                cliente = self.session.query(Cliente).filter_by(id=proposta.cliente_id).first()
                if not cliente:
                    print(f"DEBUG LANCAMENTOS: Cliente ID {proposta.cliente_id} não encontrado")
                    raise ValueError(f"Cliente ID {proposta.cliente_id} não encontrado")
                
                print(f"DEBUG LANCAMENTOS: Cliente encontrado: {cliente.nome}")
                    
                # Verificar se já existem lançamentos para esta proposta para evitar duplicação
                lancamentos_existentes = self.session.query(Transacao)\
                    .filter_by(proposta_id=proposta_id_int, tipo="receita_a_receber")\
                    .count()
                
                print(f"DEBUG LANCAMENTOS: Lançamentos existentes: {lancamentos_existentes}")
                    
                # Se já existirem lançamentos, verificar se devemos forçar a regeneração
                if lancamentos_existentes > 0:
                    # Se forçar_geracao=True, remover os lançamentos existentes e continuar
                    if forcar_geracao:
                        print(f"DEBUG LANCAMENTOS: Removendo {lancamentos_existentes} lançamentos existentes para regeneração")
                        # Remover lançamentos existentes
                        self.session.query(Transacao).filter_by(proposta_id=proposta_id_int).delete()
                        self.session.flush()
                        print(f"DEBUG LANCAMENTOS: Lançamentos existentes removidos com sucesso")
                    else:
                        # Verificar se existem transações do tipo produto especificamente
                        transacoes_produtos = self.session.query(Transacao)\
                            .filter_by(proposta_id=proposta_id_int, categoria="Venda de Produtos")\
                            .count()
                            
                        if transacoes_produtos > 0:
                            print(f"DEBUG LANCAMENTOS: Já existem lançamentos para produtos ({transacoes_produtos}). Pulando.")
                            return {"status": "já existe", "mensagem": "Lançamentos já existem para esta proposta"}
                        else:
                            print(f"DEBUG LANCAMENTOS: Não existem lançamentos específicos para produtos. Continuando com a geração.")
                            # Continuamos a execução para gerar os lançamentos de produtos
                
                # Resultados para retornar
                result = {
                    "valor_base": 0,
                    "valor_produtos": 0,
                    "valor_fornecedores": 0,
                    "valor_assistentes": 0,
                    "lancamentos_gerados": 0
                }
                
                # Converter proposta_id para inteiro nativo do Python para evitar problemas com numpy.int64
                proposta_id_python_int = self._ensure_int(proposta_id_int)
                
                # 1. Lançamento do valor base (cliente a receber)
                valor_base = float(proposta.valor) if proposta.valor else 0
                print(f"DEBUG LANCAMENTOS: Valor base da proposta: R$ {valor_base:.2f}")
                
                # Obter usuario_id da proposta para garantir isolamento de dados
                usuario_id = proposta.usuario_id if hasattr(proposta, 'usuario_id') else None
                
                # Data dos lançamentos - usar a data de finalização ou data atual
                data_lancamento = datetime.now().date()
                if hasattr(proposta, 'data_fim') and proposta.data_fim:
                    data_lancamento = proposta.data_fim
                
                if valor_base > 0:
                    # Transação no extrato financeiro
                    transacao_base = Transacao(
                        tipo="receita_a_receber",
                        descricao=f"Proposta #{proposta.numero} - {proposta.descricao[:50]}... - {cliente.nome}",
                        valor=valor_base,
                        data=data_lancamento,
                        categoria="Serviços de Organização",
                        subcategoria=proposta.tipo_proposta or "Organização",
                        tipo_receita="organizacao",
                        origem_id=proposta.cliente_id,
                        origem_tipo="cliente",
                        tipo_conta="PF",
                        status="Pendente",
                        proposta_id=proposta_id_int,
                        classificacao="receita",
                        usuario_id=usuario_id
                    )
                    self.session.add(transacao_base)
                    
                    # Removido a transação duplicada nas contas a receber
                    
                    result["valor_base"] = valor_base
                    result["lancamentos_gerados"] += 1
                    print(f"DEBUG LANCAMENTOS: Lançamento do valor base criado")
                
                # 2. Produtos a receber
                produtos = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_python_int).all()
                print(f"DEBUG LANCAMENTOS: Produtos encontrados: {len(produtos)}")
                
                # Query direto para confirmar problemas
                try:
                    produtos_sql = self.session.execute(text(f"SELECT * FROM produtos_organizadores WHERE proposta_id = {proposta_id_python_int}")).fetchall()
                    print(f"DEBUG LANCAMENTOS SQL: Produtos via SQL direto: {len(produtos_sql)}")
                    
                    if produtos_sql:
                        for p in produtos_sql:
                            print(f"DEBUG LANCAMENTOS SQL: Produto ID={p.id}, Nome={p.nome}, Valor={p.valor}")
                    else:
                        print(f"DEBUG LANCAMENTOS SQL: Nenhum produto encontrado via SQL direto")
                except Exception as e:
                    print(f"DEBUG LANCAMENTOS SQL: Erro ao consultar produtos diretamente: {str(e)}")
                
                # Agrupar produtos por tipo (físicos vs. serviços)
                produtos_fisicos = []
                produtos_servicos = []
                
                # Palavras-chave para identificar serviços em vez de produtos físicos
                termos_servicos = ['uber', 'transporte', 'serviço', 'servico', 'frete', 'delivery', 'entrega']
                
                # Categorizar produtos
                for produto in produtos:
                    nome_lower = produto.nome.lower() if produto.nome else ""
                    if any(termo in nome_lower for termo in termos_servicos):
                        produtos_servicos.append(produto)
                        print(f"DEBUG LANCAMENTOS: Classificado como SERVIÇO: {produto.nome}")
                    else:
                        produtos_fisicos.append(produto)
                        print(f"DEBUG LANCAMENTOS: Classificado como PRODUTO FÍSICO: {produto.nome}")
                
                # Calcular valores
                valor_total_produtos_fisicos = 0
                valor_total_servicos = 0
                
                # Processar produtos físicos
                for produto in produtos_fisicos:
                    valor_produto = float(produto.valor) * produto.quantidade
                    valor_total_produtos_fisicos += valor_produto
                    print(f"DEBUG LANCAMENTOS: Produto '{produto.nome}': R$ {produto.valor} x {produto.quantidade} = R$ {valor_produto:.2f}")
                
                # Processar serviços
                for produto in produtos_servicos:
                    valor_servico = float(produto.valor) * produto.quantidade
                    valor_total_servicos += valor_servico
                    print(f"DEBUG LANCAMENTOS: Serviço '{produto.nome}': R$ {produto.valor} x {produto.quantidade} = R$ {valor_servico:.2f}")
                
                print(f"DEBUG LANCAMENTOS: Valor total dos produtos físicos: R$ {valor_total_produtos_fisicos:.2f}")
                print(f"DEBUG LANCAMENTOS: Valor total dos serviços: R$ {valor_total_servicos:.2f}")
                
                # Obter usuario_id da proposta para garantir isolamento de dados
                usuario_id = proposta.usuario_id if hasattr(proposta, 'usuario_id') else None
                
                # Data dos lançamentos - usar a data de finalização ou data atual
                data_lancamento = datetime.now().date()
                if hasattr(proposta, 'data_fim') and proposta.data_fim:
                    data_lancamento = proposta.data_fim
                
                # Criar lançamento para produtos físicos no extrato (1 - Produtos a receber)
                if valor_total_produtos_fisicos > 0:
                    # Primeiro registrar a venda para obter o ID da venda
                    venda_id = None
                    try:
                        # Criar registro de venda e obter o ID
                        venda_id = self._registrar_venda_produtos(proposta, cliente, produtos_fisicos, forcar_geracao)
                        print(f"DEBUG LANCAMENTOS: Venda registrada com ID {venda_id} para produtos da proposta #{proposta.numero}")
                    except Exception as e:
                        print(f"ERRO ao registrar venda de produtos: {str(e)}")
                    
                    # Depois criar o lançamento financeiro, já com a referência à venda
                    transacao_produtos = Transacao(
                        tipo="receita_a_receber",
                        descricao=f"Produtos da Proposta #{proposta.numero} - {cliente.nome}",
                        valor=valor_total_produtos_fisicos,
                        data=data_lancamento,
                        categoria="Venda de Produtos",
                        subcategoria="Produtos",
                        tipo_receita="venda",
                        origem_id=venda_id if venda_id else proposta.cliente_id,  # Usar ID da venda se disponível
                        origem_tipo="venda" if venda_id else "cliente",  # Alterar o tipo de origem
                        tipo_conta="PF",
                        status="Pendente",
                        proposta_id=proposta_id_int,
                        classificacao="receita",
                        usuario_id=usuario_id
                    )
                    self.session.add(transacao_produtos)
                    
                    # Removido o lançamento duplicado nas contas a receber para produtos
                    
                    result["valor_produtos"] = valor_total_produtos_fisicos
                    result["lancamentos_gerados"] += 1  # Apenas um lançamento agora
                    print(f"DEBUG LANCAMENTOS: Lançamento de produtos criado: R$ {valor_total_produtos_fisicos:.2f}")
                
                # Criar lançamento para serviços (separado dos produtos físicos)
                if valor_total_servicos > 0:
                    # Transação no extrato
                    transacao_servicos = Transacao(
                        tipo="receita_a_receber",
                        descricao=f"Serviços da Proposta #{proposta.numero} - {cliente.nome}",
                        valor=valor_total_servicos,
                        data=data_lancamento,
                        categoria="Serviços de Organização",
                        subcategoria="Serviços Adicionais",
                        tipo_receita="servico",
                        origem_id=proposta.cliente_id,
                        origem_tipo="cliente",
                        tipo_conta="PF",
                        status="Pendente",
                        proposta_id=proposta_id_int,
                        classificacao="receita",
                        usuario_id=usuario_id
                    )
                    self.session.add(transacao_servicos)
                    
                    # Removido o lançamento duplicado nas contas a receber
                    
                    # Adicionar ao valor total de outros
                    result["valor_outros"] = result.get("valor_outros", 0) + valor_total_servicos
                    result["lancamentos_gerados"] += 1
                    print(f"DEBUG LANCAMENTOS: Lançamento de serviços criado: R$ {valor_total_servicos:.2f}")
                
                # Garantir que todos os lançamentos estão salvos
                self.session.flush()
                
                # Não registramos novamente a venda, pois já foi feita antes da criação do lançamento financeiro
                # Esta seção foi removida para evitar duplicação de registros de venda
                
                # Vamos adicionar processamento de itens tipo "OUTRO"
                outros = self.session.query(AcrescimoProposta)\
                    .filter_by(proposta_id=proposta_id_python_int, tipo="OUTRO")\
                    .all()
                    
                print(f"DEBUG LANCAMENTOS: Itens tipo OUTRO encontrados: {len(outros)}")
                
                valor_total_outros = 0
                for outro_item in outros:
                    valor_outro = float(outro_item.valor) if outro_item.valor else 0
                    valor_total_outros += valor_outro
                    print(f"DEBUG LANCAMENTOS: Item OUTRO '{outro_item.fornecedor}': R$ {valor_outro:.2f}")
                
                print(f"DEBUG LANCAMENTOS: Valor total de itens OUTRO: R$ {valor_total_outros:.2f}")
                
                # Verificar se já existem lançamentos para Outros a receber
                transacoes_outros = self.session.query(Transacao)\
                    .filter_by(proposta_id=proposta_id_int, 
                              categoria="Outros", 
                              classificacao="contas_a_receber")\
                    .count()
                
                # Criar lançamento para itens OUTRO apenas se não existir ou se forçado
                if valor_total_outros > 0 and (transacoes_outros == 0 or forcar_geracao):
                    print(f"DEBUG LANCAMENTOS: Criando lançamento para Outros a receber: R$ {valor_total_outros:.2f}")
                    
                    # Transação no extrato
                    transacao_outros = Transacao(
                        tipo="receita_a_receber",
                        descricao=f"Itens adicionais da Proposta #{proposta.numero} - {cliente.nome}",
                        valor=valor_total_outros,
                        data=data_lancamento,
                        categoria="Outros",
                        subcategoria="Itens Adicionais",
                        tipo_receita="outros",
                        origem_id=proposta.cliente_id,
                        origem_tipo="cliente",
                        tipo_conta="PF",
                        status="Pendente",
                        proposta_id=proposta_id_int,
                        classificacao="receita",
                        usuario_id=usuario_id
                    )
                    self.session.add(transacao_outros)
                    
                    # Removido o lançamento duplicado nas contas a receber
                    
                    result["valor_outros"] = valor_total_outros
                    result["lancamentos_gerados"] += 1
                    print(f"DEBUG LANCAMENTOS: Lançamento de itens OUTRO criado: R$ {valor_total_outros:.2f}")
                else:
                    if transacoes_outros > 0:
                        print(f"DEBUG LANCAMENTOS: Já existem lançamentos para Outros a receber ({transacoes_outros}). Pulando.")
                    result["valor_outros"] = valor_total_outros
                
                # 3. Comissões a receber por fornecedor - APENAS para propostas concluídas
                # Verificar se a proposta está concluída antes de gerar lançamentos para fornecedores
                gerar_lancamentos_comissao = False
                if proposta.status == "Concluída" or (hasattr(proposta, 'status_execucao') and proposta.status_execucao == "Concluída"):
                    gerar_lancamentos_comissao = True
                    print(f"DEBUG LANCAMENTOS: Proposta está concluída. Gerando lançamentos de comissão e assistentes.")
                else:
                    print(f"DEBUG LANCAMENTOS: Proposta NÃO está concluída (Status={proposta.status}, Status execução={proposta.status_execucao if hasattr(proposta, 'status_execucao') else 'N/A'}). Pulando lançamentos de comissão e assistentes.")
                
                # Inicializar variável para total de fornecedores
                valor_total_fornecedores = 0
                
                # Só processar comissões se a proposta estiver concluída ou se forcar_geracao=True
                if gerar_lancamentos_comissao or forcar_geracao:
                    fornecedores = self.session.query(AcrescimoProposta)\
                        .filter_by(proposta_id=proposta_id_python_int, tipo="FORNECEDOR")\
                        .all()
                    
                    for fornecedor_item in fornecedores:
                        valor_fornecedor = float(fornecedor_item.valor) if fornecedor_item.valor else 0
                        valor_total_fornecedores += valor_fornecedor
                        
                        # Buscar o percentual de comissão (pode estar no item ou precisamos buscar no cadastro)
                        percentual_comissao = None
                        for attr in dir(fornecedor_item):
                            if attr == 'percentual_comissao':
                                percentual_comissao = getattr(fornecedor_item, attr)
                                break
                        
                        # Se não tiver percentual no item, buscar no cadastro do fornecedor
                        nome_fornecedor = fornecedor_item.fornecedor
                        fornecedor_cadastro = self.session.query(Fornecedor).filter(Fornecedor.descricao == nome_fornecedor).first()
                        
                        if not percentual_comissao and fornecedor_cadastro and hasattr(fornecedor_cadastro, 'percentual_comissao'):
                            percentual_comissao = fornecedor_cadastro.percentual_comissao
                        
                        # Se tiver percentual de comissão, calcular o valor e gerar o lançamento
                        if percentual_comissao and percentual_comissao > 0:
                            valor_comissao = valor_fornecedor * (percentual_comissao / 100)
                            
                            if valor_comissao > 0:
                                # Verificar se já existe uma transação de comissão para este fornecedor nesta proposta
                                comissao_existente = self.session.query(Transacao).filter(
                                    Transacao.proposta_id == proposta_id_int,
                                    Transacao.categoria == "Comissão",
                                    Transacao.subcategoria == "Comissão de Fornecedor",
                                    Transacao.descricao.like(f"%{nome_fornecedor}%")
                                ).first()
                                
                                if comissao_existente:
                                    print(f"DEBUG LANCAMENTOS: Comissão para {nome_fornecedor} já existe. ID={comissao_existente.id}. Pulando.")
                                    continue
                                
                                # Transação no extrato
                                transacao_comissao = Transacao(
                                    tipo="receita_a_receber",
                                    descricao=f"Comissão de {percentual_comissao}% - {nome_fornecedor} - Proposta #{proposta.numero}",
                                    valor=valor_comissao,
                                    data=data_lancamento,
                                    categoria="Comissão",
                                    subcategoria="Comissão de Fornecedor",
                                    tipo_receita="comissao",
                                    origem_id=fornecedor_cadastro.id if fornecedor_cadastro else None,
                                    origem_tipo="fornecedor",
                                    tipo_conta="PF",
                                    status="Pendente",
                                    proposta_id=proposta_id_int,
                                    classificacao="receita",
                                    usuario_id=usuario_id
                                )
                                self.session.add(transacao_comissao)
                                
                                # Removido o lançamento duplicado nas contas a receber
                                
                                result["lancamentos_gerados"] += 1
                                print(f"DEBUG LANCAMENTOS: Lançamento de comissão criado: R$ {valor_comissao:.2f}")
                else:
                    print(f"DEBUG LANCAMENTOS: Pulando geração de lançamentos de comissão (proposta não está concluída).")
                
                # 4. Assistentes a pagar - APENAS para propostas concluídas
                # Inicializar variável para total de assistentes
                valor_total_assistentes = 0
                
                # Só processar assistentes se a proposta estiver concluída ou se forcar_geracao=True
                if gerar_lancamentos_comissao or forcar_geracao:
                    assistentes = self.session.query(AcrescimoProposta)\
                        .filter_by(proposta_id=proposta_id_python_int, tipo="ASSISTENTE")\
                        .all()
                    
                    for assistente_item in assistentes:
                        valor_assistente = float(assistente_item.valor) if assistente_item.valor else 0
                        valor_total_assistentes += valor_assistente
                        print(f"DEBUG LANCAMENTOS: Assistente '{assistente_item.fornecedor}': R$ {valor_assistente:.2f}")
                    
                    print(f"DEBUG LANCAMENTOS: Valor total de assistentes: R$ {valor_total_assistentes:.2f}")
                    
                    # Verificar se já existem lançamentos para Assistentes a pagar
                    transacoes_assistentes = self.session.query(Transacao)\
                        .filter_by(proposta_id=proposta_id_int, 
                                  categoria="Assistente", 
                                  classificacao="contas_a_pagar")\
                        .count()
                        
                    print(f"DEBUG LANCAMENTOS: Lançamentos existentes para Assistentes a pagar: {transacoes_assistentes}")
                    
                    # Criar lançamentos individuais para cada assistente (verificando duplicidade por assistente)
                    if valor_total_assistentes > 0:
                        print(f"DEBUG LANCAMENTOS: Verificando lançamentos para Assistentes a pagar: R$ {valor_total_assistentes:.2f}")
                        
                        for assistente_item in assistentes:
                            valor_assistente = float(assistente_item.valor) if assistente_item.valor else 0
                            
                            if valor_assistente > 0:
                                nome_assistente = assistente_item.fornecedor  # o campo "fornecedor" armazena o nome do assistente
                                
                                # Verificar se já existe uma transação de pagamento para este assistente nesta proposta
                                assistente_existente = self.session.query(Transacao).filter(
                                    Transacao.proposta_id == proposta_id_int,
                                    Transacao.categoria == "Assistente",
                                    Transacao.subcategoria == "Pagamento de Serviço",
                                    Transacao.descricao.like(f"%{nome_assistente}%")
                                ).first()
                                
                                if assistente_existente:
                                    print(f"DEBUG LANCAMENTOS: Pagamento para assistente {nome_assistente} já existe. ID={assistente_existente.id}. Pulando.")
                                    continue
                                
                                # Transação no extrato
                                transacao_assistente = Transacao(
                                    tipo="despesa",
                                    descricao=f"Pagamento Assistente {nome_assistente} - Proposta #{proposta.numero}",
                                    valor=valor_assistente,
                                    data=data_lancamento,
                                    categoria="Assistente",
                                    subcategoria="Pagamento de Serviço",
                                    tipo_receita="assistente",  # Usaremos tipo_receita mesmo para despesas
                                    origem_id=assistente_item.id,
                                    origem_tipo="assistente",
                                    tipo_conta="PF",
                                    status="Pendente",
                                    proposta_id=proposta_id_int,
                                    classificacao="custo_direto",
                                    usuario_id=usuario_id
                                )
                                self.session.add(transacao_assistente)
                                
                                # Removido o lançamento duplicado nas contas a pagar
                                
                                result["lancamentos_gerados"] += 1
                                print(f"DEBUG LANCAMENTOS: Lançamento criado para assistente {nome_assistente}: R$ {valor_assistente:.2f}")
                    else:
                        if transacoes_assistentes > 0:
                            print(f"DEBUG LANCAMENTOS: Já existem lançamentos para Assistentes a pagar ({transacoes_assistentes}). Pulando.")
                else:
                    print(f"DEBUG LANCAMENTOS: Pulando geração de lançamentos de assistentes (proposta não está concluída).")
                
                result["valor_fornecedores"] = valor_total_fornecedores
                result["valor_assistentes"] = valor_total_assistentes
                
                # Resumo dos resultados
                result["total_lancamentos"] = (
                    result["valor_base"] + 
                    result["valor_produtos"] + 
                    result["valor_fornecedores"] + 
                    result["valor_assistentes"]
                )
                
                return result
                
            except Exception as e:
                print(f"ERRO ao gerar lançamentos financeiros: {str(e)}")
                import traceback
                traceback.print_exc()
                raise Exception(f"Erro ao gerar lançamentos financeiros: {str(e)}")
            
        return self._safe_query(query)
    
    def _registrar_venda_produtos(self, proposta, cliente, produtos, forcar_geracao=False):
        """
        Registra uma venda de produtos a partir de uma proposta finalizada
        
        Args:
            proposta: Objeto Proposta
            cliente: Objeto Cliente
            produtos: Lista de objetos ProdutoOrganizador
            forcar_geracao: Se True, remove vendas existentes e gera novos registros (para reabertura)
        
        Returns:
            int: ID da venda criada ou None em caso de erro
        """
        # Resolver o problema de "concurrent operations are not permitted"
        # usando uma nova sessão isolada para esta operação
        import os
        from sqlalchemy.orm import Session as SQLSession
        from sqlalchemy import create_engine
        
        # Usar diretamente a variável de ambiente para o DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERRO: DATABASE_URL não encontrada no ambiente")
            return None
            
        # Criar uma nova sessão independente para esta operação
        engine_local = create_engine(database_url)
        session_local = SQLSession(bind=engine_local)
        
        try:
            print(f"DEBUG VENDAS: Iniciando registro de venda para proposta #{proposta.numero}")
            print(f"DEBUG VENDAS: Cliente: {cliente.nome} (ID: {cliente.id})")
            print(f"DEBUG VENDAS: Total de produtos: {len(produtos)}")
            
            # Buscar proposta e cliente pela ID na sessão local
            proposta_id = proposta.id
            cliente_id = cliente.id
            proposta_numero = proposta.numero
            usuario_id = proposta.usuario_id
            
            # Verificar se já existe uma venda para esta proposta na sessão local
            venda_existente = session_local.query(Venda).filter_by(proposta_id=proposta_id).first()
            if venda_existente:
                print(f"DEBUG VENDAS: Já existe uma venda (ID: {venda_existente.id}) para esta proposta")
                
                # Se forçar geração, remover a venda existente e seus itens
                if forcar_geracao:
                    print(f"DEBUG VENDAS: Forçando regeneração da venda. Removendo venda existente ID: {venda_existente.id}")
                    # Primeiro remover os itens relacionados
                    try:
                        # Remover transações financeiras relacionadas à venda
                        session_local.query(Transacao).filter_by(
                            origem_id=venda_existente.id,
                            origem_tipo='venda'
                        ).delete()
                        print(f"DEBUG VENDAS: Transações financeiras da venda removidas")
                        
                        # Remover itens da venda
                        session_local.query(ItemVenda).filter_by(venda_id=venda_existente.id).delete()
                        print(f"DEBUG VENDAS: Itens da venda removidos")
                        
                        # Depois remover a venda
                        session_local.query(Venda).filter_by(id=venda_existente.id).delete()
                        session_local.flush()
                        print(f"DEBUG VENDAS: Venda removida com sucesso")
                    except Exception as e:
                        print(f"ERRO ao remover venda existente: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        session_local.rollback()
                else:
                    # Verificar se a venda tem itens
                    itens = session_local.query(ItemVenda).filter_by(venda_id=venda_existente.id).count()
                    print(f"DEBUG VENDAS: Venda existente tem {itens} itens")
                    
                    if itens == 0:
                        print(f"DEBUG VENDAS: Venda existe mas não tem itens. Removendo venda vazia para regeneração.")
                        # Remover a venda sem itens
                        session_local.query(Venda).filter_by(id=venda_existente.id).delete()
                        session_local.flush()
                    else:
                        # Se não forçar, retornar o ID da venda existente
                        print(f"DEBUG VENDAS: Usando venda existente com itens")
                        venda_id = venda_existente.id
                        session_local.close()
                        return venda_id
            
            # Calcular valor total dos produtos
            valor_total = 0
            produtos_info = []  # Lista para armazenar informações dos produtos
            
            for i, produto in enumerate(produtos):
                valor_produto = float(produto.valor) * produto.quantidade
                valor_total += valor_produto
                produtos_info.append({
                    'nome': produto.nome,
                    'valor': float(produto.valor),
                    'quantidade': produto.quantidade,
                    'subtotal': valor_produto,
                    'produto_id': produto.produto_id if hasattr(produto, 'produto_id') else None
                })
                print(f"DEBUG VENDAS: Produto {i+1}: {produto.nome}, Valor: R$ {produto.valor}, Quantidade: {produto.quantidade}, Subtotal: R$ {valor_produto:.2f}")
                
            print(f"DEBUG VENDAS: Valor total dos produtos: R$ {valor_total:.2f}")
                
            # Criar a venda
            venda = Venda(
                cliente_id=cliente_id,
                proposta_id=proposta_id,
                data_venda=datetime.now().date(),
                valor_total=valor_total,
                status="Concluída",
                forma_pagamento="Proposta",
                observacoes=f"Venda gerada automaticamente da proposta #{proposta_numero}",
                usuario_id=usuario_id  # Importante: manter o mesmo usuário da proposta
            )
            session_local.add(venda)
            session_local.flush()  # Para obter o ID da venda
            venda_id = venda.id
            print(f"DEBUG VENDAS: Venda criada com ID: {venda_id}")
            
            # Adicionar itens da venda
            for produto_info in produtos_info:
                # Criar o objeto ItemVenda com campos compatíveis
                try:
                    # Tentar criar o objeto com campos básicos primeiro (compatível com produção)
                    item = ItemVenda(
                        venda_id=venda_id,
                        produto_id=produto_info['produto_id'],
                        quantidade=produto_info['quantidade'],
                        preco_unitario=produto_info['valor'],
                        subtotal=produto_info['subtotal']
                    )
                    
                    # Tentar adicionar o campo descricao somente se for suportado
                    if hasattr(ItemVenda, 'descricao'):
                        try:
                            item.descricao = produto_info['nome']
                        except Exception as descr_e:
                            print(f"AVISO: Não foi possível adicionar o campo descricao: {str(descr_e)}")
                except Exception as e:
                    print(f"ERRO ao criar item de venda: {str(e)}")
                    # Garantir que pelo menos os campos obrigatórios são incluídos
                    item = ItemVenda(
                        venda_id=venda_id,
                        produto_id=None,
                        quantidade=produto_info['quantidade'],
                        preco_unitario=produto_info['valor'],
                        subtotal=produto_info['subtotal']
                    )
                session_local.add(item)
                print(f"DEBUG VENDAS: Item adicionado à venda: {produto_info['nome']}, Subtotal: R$ {produto_info['subtotal']:.2f}")
            
            # Forçar commit para garantir que a venda seja salva
            session_local.commit()
            print(f"DEBUG VENDAS: Venda registrada com sucesso, ID: {venda_id}")
            return venda_id
            
        except Exception as e:
            session_local.rollback()
            print(f"ERRO ao registrar venda de produtos: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Sempre fechar a sessão local no final para liberar os recursos
            session_local.close()