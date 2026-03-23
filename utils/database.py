import os
import numpy as np
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

# Função auxiliar para obter o ID do usuário (desacoplada do Streamlit)
def get_usuario_id(usuario_id_override=None):
    """
    Retorna o ID do usuário atual.
    Aceita override direto para uso fora do contexto Streamlit.
    
    Args:
        usuario_id_override: ID fornecido externamente (sobrescreve a sessão)
        
    Returns:
        str: ID do usuário ou None se não disponível
    """
    if usuario_id_override is not None:
        return usuario_id_override
    try:
        import streamlit as st
        return st.session_state.get('usuario_id')
    except Exception:
        return None

# Função para obter um valor do cache da sessão (desacoplada do Streamlit)
def get_cache(key):
    """
    Obtém um valor do cache da sessão Streamlit.
    Retorna None se não estiver em Streamlit ou se a chave não existe.
    """
    try:
        import streamlit as st
        return st.session_state.get(key)
    except Exception:
        return None

# Função para definir um valor no cache da sessão (desacoplada do Streamlit)
def set_cache(key, value):
    """
    Define um valor no cache da sessão Streamlit.
    Falha silenciosamente se não estiver em Streamlit.
    """
    try:
        import streamlit as st
        st.session_state[key] = value
    except Exception:
        pass

# Função para remover um valor do cache da sessão (desacoplada do Streamlit)
def remove_cache(key):
    """
    Remove um valor do cache da sessão Streamlit.
    Falha silenciosamente se não estiver em Streamlit.
    """
    try:
        import streamlit as st
        if key in st.session_state:
            del st.session_state[key]
    except Exception:
        pass

# Função auxiliar para obter o ID do usuário da sessão do Streamlit
def get_usuario_id_from_session():
    """
    Obtém o ID do usuário atualmente autenticado no Streamlit
    
    Returns:
        str: ID do usuário autenticado ou None se não há usuário na sessão
    """
    # INÍCIO DA SOLUÇÃO DEFINITIVA: Prioridade 1 - Verificar session_state.usuario_id diretamente
    # Este é o método preferencial e mais direto
    if 'usuario_id' in st.session_state:
        usuario_id = st.session_state.usuario_id
        return usuario_id
    
    # Prioridade 2 - Verificar session_state.user (padrão do Firebase)
    if 'user' in st.session_state and st.session_state.user:
        
        # Usar o localId do Firebase como usuario_id
        if 'localId' in st.session_state.user:
            usuario_id = st.session_state.user['localId']
            
            # IMPORTANTE: Definir explicitamente em session_state.usuario_id para futuras chamadas
            st.session_state.usuario_id = usuario_id
            
            return usuario_id
        
        # Verificar alternativas
        if 'usuario_id' in st.session_state.user:
            usuario_id = st.session_state.user['usuario_id']
            
            # IMPORTANTE: Definir explicitamente em session_state.usuario_id para futuras chamadas
            st.session_state.usuario_id = usuario_id
            
            return usuario_id
    
    # Prioridade 3 - Verificar session_state.usuario (para compatibilidade)
    if 'usuario' in st.session_state and st.session_state.usuario:
        
        if isinstance(st.session_state.usuario, dict):
            # Verificar diferentes campos possíveis para ID
            for campo in ['id', 'usuario_id', 'localId', 'uid']:
                if campo in st.session_state.usuario:
                    usuario_id = st.session_state.usuario[campo]
                    
                    # IMPORTANTE: Definir explicitamente em session_state.usuario_id para futuras chamadas
                    st.session_state.usuario_id = usuario_id
                    
                    return usuario_id
            
    # Fallback para ID de demonstração em ambiente de desenvolvimento
    # Isso é um hack temporário que deve ser removido em produção ou quando houver login real
    if os.getenv('REPLIT_SLUG') or os.getenv('DEVELOPMENT_ENV'):
        default_id = "demo-user-id"
        
        # IMPORTANTE: Definir explicitamente em session_state.usuario_id para futuras chamadas
        st.session_state.usuario_id = default_id
        
        return default_id
                
    return None


# Importar modelos do módulo separado
from utils.models import *

# Importar queries de módulos separados
from utils.queries_pos_org import *


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
        # OTIMIZAÇÃO: Cache metadata refresh para evitar consultas desnecessárias
        if not hasattr(self.__class__, '_metadata_refreshed'):
            self.refresh_schema_metadata()
            self.__class__._metadata_refreshed = True
        
        try:
            # Criar tabelas se não existirem
            Base.metadata.create_all(engine)
            self.session = Session()
            
            # Configurar o contexto de usuário para filtrar os dados
            self.usuario_id = None
            
            # 1. Usar ID fornecido explicitamente (prioridade máxima)
            if usuario_id:
                self.usuario_id = usuario_id
                
                # IMPORTANTE: Sempre manter o ID do usuário na sessão para garantir consistência
                # entre diferentes instâncias do Database
                try:
                    if hasattr(st, 'session_state'):
                        if 'usuario_id' not in st.session_state or st.session_state.usuario_id != usuario_id:
                            st.session_state.usuario_id = usuario_id
                except Exception as session_error:
                    print(f"Erro: {session_error}")
            else:
                # 2. Tentar obter o ID do usuário da sessão do Streamlit
                # Esta função agora tem lógica aprimorada para garantir que o ID seja sempre encontrado
                session_usuario_id = get_usuario_id_from_session()
                
                if session_usuario_id:
                    self.usuario_id = session_usuario_id
                else:
                    # 3. Última alternativa: tentar criar um ID de usuário temporário por sessão
                    # Isso serve para isolamento em desenvolvimento/demonstração
                    import uuid
                    temp_id = f"temp-user-{uuid.uuid4().hex[:8]}"
                    self.usuario_id = temp_id
                    
                    # Manter na sessão para consistência
                    try:
                        if hasattr(st, 'session_state'):
                            st.session_state.usuario_id = temp_id
                    except Exception as session_error:
                        print(f"Erro: {session_error}")

            # Status final do tenant
            if self.usuario_id:
                
                # PATCH FINAL: Verificar se já existem dados no banco sem usuario_id
                # NÃO atribuir mais automaticamente o ID do usuário para registros sem proprietário
                # Isso estava causando problemas de compartimentalização
                
                # Apenas mostrar quantos registros não têm proprietário para fins de diagnóstico
                try:
                    for tabela in ['propostas', 'clientes', 'financeiro', 'produtos']:
                        query = text(f"""
                            SELECT COUNT(*) FROM {tabela} 
                            WHERE usuario_id IS NULL OR usuario_id = ''
                        """)
                        result = self.session.execute(query).scalar()
                        if result > 0:
                            pass
                    
                except Exception as patch_error:
                    self.session.rollback()
            else:
                pass

            # Verificar e criar perfil do usuário se necessário
            if self.usuario_id:
                # Sempre que temos um ID de usuário válido, garantir que o perfil exista
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
        
    def salvar_perfil_usuario(self, dados_perfil):
        """
        Salva ou atualiza o perfil do usuário no banco de dados
        
        Args:
            dados_perfil (dict): Dicionário com os dados do perfil
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        def query():
            try:
                # Procurar perfil existente do usuário atual
                perfil = self.session.query(Perfil).filter_by(usuario_id=self.usuario_id).first()
                
                if perfil:
                    # Atualizar perfil existente
                    perfil.nome = dados_perfil.get('nome', perfil.nome)
                    perfil.telefone = dados_perfil.get('telefone', perfil.telefone)
                    perfil.empresa = dados_perfil.get('empresa', perfil.empresa)
                    perfil.instagram = dados_perfil.get('instagram', perfil.instagram)
                    perfil.website = dados_perfil.get('website', perfil.website)
                    perfil.cargo = dados_perfil.get('cargo', perfil.cargo)
                    perfil.mensagem_padrao = dados_perfil.get('mensagem_padrao', perfil.mensagem_padrao)
                    perfil.cor_principal = dados_perfil.get('cor_principal', perfil.cor_principal)
                    perfil.cor_secundaria = dados_perfil.get('cor_secundaria', perfil.cor_secundaria)
                    perfil.observacoes_relatorio = dados_perfil.get('observacoes_relatorio', perfil.observacoes_relatorio)
                    perfil.ultimo_login = datetime.now()
                else:
                    # Criar novo perfil - precisa de email válido
                    email = dados_perfil.get('email')
                    if not email:
                        print("Erro: Email é obrigatório para criar perfil")
                        return False
                    
                    perfil = Perfil(
                        usuario_id=self.usuario_id,
                        email=email,
                        nome=dados_perfil.get('nome', 'Usuário'),
                        telefone=dados_perfil.get('telefone', ''),
                        empresa=dados_perfil.get('empresa', ''),
                        instagram=dados_perfil.get('instagram', ''),
                        website=dados_perfil.get('website', ''),
                        cargo=dados_perfil.get('cargo', ''),
                        mensagem_padrao=dados_perfil.get('mensagem_padrao', ''),
                        cor_principal=dados_perfil.get('cor_principal', ''),
                        cor_secundaria=dados_perfil.get('cor_secundaria', ''),
                        observacoes_relatorio=dados_perfil.get('observacoes_relatorio', ''),
                        ultimo_login=datetime.now()
                    )
                    self.session.add(perfil)
                
                self.session.commit()
                print(f"Perfil salvo com sucesso para usuário: {self.usuario_id}")
                return True
                
            except Exception as e:
                print(f"Erro ao salvar perfil: {str(e)}")
                self.session.rollback()
                return False
                
        return self._safe_query(query)
        
    def get_perfil_usuario(self):
        """
        Obtém o perfil do usuário atual
        
        Returns:
            dict: Dados do perfil ou None se não encontrado
        """
        def query():
            try:
                perfil = self.session.query(Perfil).filter_by(usuario_id=self.usuario_id).first()
                
                if perfil:
                    return {
                        'id': perfil.id,
                        'usuario_id': perfil.usuario_id,
                        'email': perfil.email,
                        'nome': perfil.nome,
                        'telefone': perfil.telefone,
                        'empresa': perfil.empresa,
                        'instagram': perfil.instagram,
                        'website': perfil.website,
                        'cargo': perfil.cargo,
                        'mensagem_padrao': perfil.mensagem_padrao,
                        'cor_principal': perfil.cor_principal,
                        'cor_secundaria': perfil.cor_secundaria,
                        'observacoes_relatorio': perfil.observacoes_relatorio,
                        'role': perfil.role,
                        'plano': perfil.plano,
                        'data_cadastro': perfil.data_cadastro,
                        'ultimo_login': perfil.ultimo_login,
                        'ativo': perfil.ativo
                    }
                else:
                    return None
                    
            except Exception as e:
                print(f"Erro ao buscar perfil: {str(e)}")
                return None
                
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
        Wrapper para executar queries com tratamento de erro e filtragem automática por usuário
        
        Esta função garante que as operações no banco de dados sejam executadas
        em uma transação segura, com tratamento adequado de erros e conversão de tipos.
        Também aplica automaticamente o filtro de usuário para garantir compartimentalização multiusuário.
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
                    try:
                        self.session.close()
                    except Exception as e:
                        print(f"Erro: {e}")
                    self.session = Session()
                    # Removido log de debug sobre recriação de sessão
                elif not self.session.is_active:
                    self.session = Session()
                    # Removido log de debug sobre criação de nova sessão
            except Exception as session_check_error:
                try:
                    self.session.close()
                except Exception as e:
                    print(f"Erro: {e}")
                self.session = Session()
                # Removido log de debug sobre criação de nova sessão
                
            # Verificar se já existe uma transação
            try:
                in_transaction = self.session.in_transaction()
                if in_transaction:
                    nested_transaction = True
            except Exception as tx_error:
                # Se não conseguirmos verificar, consideramos que não está em transação
                pass
            
            # INÍCIO DO PATCH PARA MULTIUSUÁRIO
            # Verificar se o ID do usuário está definido para implementar o filtro multiusuário
            if hasattr(self, 'usuario_id') and self.usuario_id:
                # Verificamos se estamos obtendo registros de tabelas que precisam de isolamento
                # Criar um wrapper para a função original
                original_query = query_func
                
                def tenant_query_wrapper():
                    # Executar a consulta original
                    result = original_query()
                    
                    # Aplicar filtro multiusuário para DataFrames
                    if isinstance(result, pd.DataFrame) and 'usuario_id' in result.columns:
                        # Filtrar por usuario_id, com tratamento correto para nulos
                        original_count = len(result)
                        
                        # Consideramos que registros pertencem ao usuário atual se:
                        # 1. usuário_id é igual ao ID do usuário atual, OU
                        # 2. usuário_id é nulo (comportamento legado)
                        result = result[(result['usuario_id'] == self.usuario_id) | 
                                        (result['usuario_id'].isna())]
                                        
                        filtered_count = len(result)
                        
                        # Registrar diagnóstico se houver diferença
                        if original_count != filtered_count:
                            print(f"MULTIUSUÁRIO: Filtrado {original_count-filtered_count} registros de outros usuários")
                    
                    return result
                
                # Substituir a função original pelo wrapper
                result = tenant_query_wrapper()
            else:
                # Executar a função de query original se não tiver usuario_id
                result = query_func()
            # FIM DO PATCH PARA MULTIUSUÁRIO
            
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
                    except Exception as e:
                        print(f"Erro: {e}")
                    # Criar nova sessão se necessário
                    try:
                        self.session.close()
                    except Exception as e:
                        print(f"Erro: {e}")
                    self.session = Session()
                    # Removido log de debug sobre nova sessão

            # Se o resultado for um DataFrame, converter tipos numéricos
            if isinstance(result, pd.DataFrame):
                # Converter colunas numéricas para tipos nativos Python
                for col in result.select_dtypes(include=['int64', 'float64', 'Int64']).columns:
                    result[col] = result[col].astype(object).where(pd.notnull(result[col]), None)
                
                # VERIFICAÇÃO FINAL DE SEGURANÇA MULTIUSUÁRIO
                # Garantir que nenhum registro de outro usuário seja retornado
                # Esta é uma segunda camada de proteção, caso algum registro não tenha sido filtrado pelo wrapper
                if hasattr(self, 'usuario_id') and self.usuario_id and 'usuario_id' in result.columns:
                    original_count = len(result)
                    # Mesma lógica de filtro melhorada: registros do usuário atual OU registros sem usuário_id (legados)
                    result = result[(result['usuario_id'] == self.usuario_id) | (result['usuario_id'].isna())]
                    if original_count != len(result):
                        print(f"ALERTA SEGURANÇA: Filtro secundário removeu {original_count - len(result)} registros de outros usuários")

            # Se o resultado for um número, garantir que seja tipo nativo Python
            elif isinstance(result, (np.int64, np.float64)):
                result = result.item()
            
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
                except Exception as e:
                    print(f"Erro: {e}")
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
        Retorna todos os clientes do usuário atual - com filtro obrigatório por multilocação
        """
        # Cache por usuário
        cache_key = f"cache_clientes_{self.usuario_id}"
        cached_result = get_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        def query():
            # SEMPRE aplicar filtro por usuário para garantir isolamento de dados
            query = self.session.query(Cliente)
            
            if self.usuario_id:
        
                # Filtro ESTRITO: apenas clientes explicitamente associados ao usuário atual
                query = query.filter(Cliente.usuario_id == self.usuario_id)
            else:
                # Comportamento de segurança: se não há ID de usuário, não retornar nenhum cliente

                return pd.DataFrame(columns=['id', 'nome', 'telefone', 'email', 'estado', 'cidade', 
                                            'bairro', 'endereco', 'data_aniversario', 
                                            'origem_cliente', 'data_cadastro', 'observacoes', 'usuario_id'])
                
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
        resultado = self._safe_query(query)
        set_cache(cache_key, resultado)
        return resultado
        
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
        # Invalidar cache quando novo cliente é adicionado
        self.invalidar_cache()
        
        def query():
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar o cliente sem proprietário.")
                
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
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar o cliente sem proprietário.")
                
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
        # Cache por usuário
        cache_key = f"cache_propostas_{self.usuario_id}"
        cached_result = get_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        def query():
            try:
                # Construir consulta base
                query = self.session.query(
                    Proposta, Cliente.nome.label('cliente_nome')
                ).outerjoin(
                    Cliente, Proposta.cliente_id == Cliente.id
                )
                
                # FIXADO: SEMPRE filtrar por usuário para garantir compartimentalização
                # Se não tivermos usuario_id, usar o método get_usuario_id_from_session novamente
                if not self.usuario_id:
                    try:
                        session_usuario_id = get_usuario_id_from_session()
                        if session_usuario_id:
                            self.usuario_id = session_usuario_id
                    except Exception as e:
                        print(f"Erro: {e}")
                
                # Aplicar filtro de usuário - com segurança aprimorada
                if self.usuario_id:
                    # Filtro ESTRITO: apenas propostas explicitamente associadas ao usuário atual
                    query = query.filter(Proposta.usuario_id == self.usuario_id)
                else:
                    # Comportamento de segurança: se não há ID de usuário válido, retornar lista vazia
                    colunas = ['id', 'numero', 'cliente_id', 'cliente_nome', 'descricao', 'valor', 
                              'status', 'tipo_proposta', 'data_inicio', 'data_fim', 'status_pagamento_base',
                              'prazo_entrega', 'data_proposta', 'status_execucao', 'usuario_id']
                    return pd.DataFrame(columns=colunas)
                
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
                            # Limpeza mais robusta do valor monetário
                            if p.valor is None:
                                valor = 0.0
                            elif isinstance(p.valor, str):
                                # Remove caracteres não numéricos exceto pontos e vírgulas
                                valor_limpo = p.valor.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                                valor = float(valor_limpo) if valor_limpo else 0.0
                            else:
                                valor = float(p.valor)
                        except (ValueError, TypeError) as e:
                            print(f"Erro ao converter valor para float: {p.valor} - {str(e)}")
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
        
        resultado = self._safe_query(query)
        set_cache(cache_key, resultado)
        return resultado

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, 
                    data_inicio=None, data_fim=None, prazo_entrega=None, previsao_dias=None, 
                    gerar_transacoes_automaticas=True):
        """
        VERSÃO MODIFICADA PARA EVITAR PROBLEMAS DE ESCOPO
        Função para adicionar proposta ao banco de dados
        
        Os parâmetros são renomeados para evitar conflitos de escopo
        """
        # Invalidar cache quando nova proposta é adicionada
        self.invalidar_cache()
        
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
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar a proposta sem proprietário.")
                
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

    def get_financeiro(self, include_all=True, categorias=None, limit=1000, force_reload=False):
        """
        Retorna os dados financeiros (transações) do usuário atual
        
        Args:
            include_all (bool): Se True, inclui todas as transações. Se False, inclui apenas transações pendentes
            categorias (list): Lista de categorias para filtrar
            limit (int): Limite de registros a serem retornados
            force_reload (bool): Se True, cria uma nova sessão para evitar caching de dados
        
        Returns:
            DataFrame: DataFrame com as transações
        """
        # Cache por usuário (skip se force_reload)
        cache_key = f"cache_financeiro_{self.usuario_id}"
        if not force_reload:
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Importações no escopo da função principal
        import pandas as pd
        
        def query():
            if force_reload:
                # Criar uma nova sessão para garantir dados atualizados
                from sqlalchemy.orm import Session as SQLSession
                from sqlalchemy import text
                
                session = SQLSession(engine)
                try:
                    # Construir a consulta SQL diretamente
                    sql = """
                        SELECT * FROM financeiro 
                        WHERE 1=1 
                    """
                    
                    # SEMPRE aplicar filtro por usuário para garantir isolamento de dados
                    params = {}
                    if self.usuario_id:
        
                        sql += " AND usuario_id = :usuario_id"
                        params['usuario_id'] = self.usuario_id
                    else:
                        # Comportamento de segurança: se não há ID de usuário válido, retornar lista vazia
                        session.close()
                        colunas = ['id', 'tipo', 'descricao', 'valor', 'data_vencimento', 'data_pagamento', 
                                  'status', 'categoria', 'proposta_id', 'cliente_id', 'usuario_id']
                        return pd.DataFrame(columns=colunas)
                    
                    # Adicionar filtro de status se necessário
                    if not include_all:
                        sql += " AND status = 'Pendente'"
                    
                    # Adicionar filtro de categorias se necessário
                    if categorias:
                        placeholders = ", ".join([f":cat{i}" for i in range(len(categorias))])
                        sql += f" AND categoria IN ({placeholders})"
                        for i, cat in enumerate(categorias):
                            params[f"cat{i}"] = cat
                    
                    # Adicionar ordenação e limite
                    sql += " ORDER BY data DESC"
                    sql += f" LIMIT {limit}"
                    
                    # Executar a consulta
                    result = session.execute(text(sql), params)
                    
                    # Converter para DataFrame
                    df = pd.DataFrame(result.fetchall())
                    
                    # Renomear colunas para o formato esperado
                    if not df.empty:
                        # Adicionar campos calculados
                        if 'tipo' in df.columns and 'valor' in df.columns:
                            df['receita'] = df.apply(
                                lambda row: float(row['valor']) if row['tipo'] in ['receita', 'receita_a_receber'] else 0.0, 
                                axis=1
                            )
                            df['despesa'] = df.apply(
                                lambda row: float(row['valor']) if row['tipo'] == 'despesa' else 0.0, 
                                axis=1
                            )
                    
                    return df
                finally:
                    session.close()
            else:
                # Usar o método original com cache do ORM
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
        resultado = self._safe_query(query)
        set_cache(cache_key, resultado)
        return resultado

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
        # Invalidar cache quando nova transação é adicionada
        self.invalidar_cache()
        
        def query():
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar a transação sem proprietário.")
                
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
        
        # Executar diretamente sem usar o _safe_query para ter mais controle
        try:
            transacao = self.session.query(Transacao).filter_by(id=transacao_id).first()
            
            if transacao:
                transacao.status = status
                if status == 'Recebido' or status == 'Pago':
                    transacao.data_recebimento = data_recebimento or datetime.now().date()
                
                # Commit explícito
                self.session.commit()
                return True
            
            return False
        except Exception as e:
            self.session.rollback()
            return False

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

    def get_contas_receber(self, force_reload=False):
        """
        Retorna as contas a receber (transações do tipo receita com status pendente)
        
        Args:
            force_reload (bool): Se True, cria uma nova sessão para evitar caching de dados
            
        Returns:
            DataFrame: DataFrame com as contas a receber
        """
        # Importações no escopo da função principal
        import pandas as pd
        
        def query():
            if force_reload:
                # Criar uma nova sessão para garantir dados atualizados
                from sqlalchemy.orm import Session as SQLSession
                from sqlalchemy import text
                
                session = SQLSession(engine)
                try:
                    # Construir a consulta SQL diretamente
                    sql = """
                        SELECT * FROM financeiro 
                        WHERE (
                            (classificacao = 'contas_a_receber') OR
                            ((tipo = 'Receita' OR tipo = 'receita') AND status = 'Pendente') OR
                            (tipo = 'receita_a_receber')
                        )
                    """
                    
                    # Adicionar filtro de usuário se necessário
                    params = {}
                    if self.usuario_id:
                        sql += " AND usuario_id = :usuario_id"
                        params['usuario_id'] = self.usuario_id
                    
                    # Adicionar ordenação
                    sql += " ORDER BY data DESC"
                    
                    # Executar a consulta
                    result = session.execute(text(sql), params)
                    
                    # Converter para DataFrame
                    df = pd.DataFrame(result.fetchall())
                    
                    return df
                finally:
                    session.close()
            else:
                # Uso do método original com cache do ORM
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
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar o fornecedor sem proprietário.")
            
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
                percentual_comissao=percentual_comissao,
                usuario_id=self.usuario_id  # Adicionar ID do usuário atual
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

    def delete_fornecedor(self, fornecedor_id):
        """
        Exclui um fornecedor pelo ID, apenas se pertencer ao usuário logado.
        """
        def query():
            fornecedor = self.session.query(Fornecedor).filter(
                Fornecedor.id == fornecedor_id,
                Fornecedor.usuario_id == self.usuario_id
            ).first()
            if not fornecedor:
                raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrado ou sem permissão.")
            self.session.delete(fornecedor)
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
            try:
                # Buscar fornecedores filtrando por usuário
                fornecedores = self.session.query(Fornecedor).filter(
                    (Fornecedor.usuario_id == self.usuario_id) | 
                    (Fornecedor.usuario_id.is_(None))
                ).all()
                
                # Construir DataFrame com os dados
                resultado = pd.DataFrame([{
                    'id': f.id,
                    'nome': f.nome,
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
                    'percentual_comissao': f.percentual_comissao,
                    'usuario_id': f.usuario_id
                } for f in fornecedores])
                
                return resultado
            except Exception as e:
                print(f"ERRO ao obter fornecedores: {str(e)}")
                return pd.DataFrame()
                
        return self._safe_query(query)

    def add_categoria_despesa(self, nome, descricao):
        def query():
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar a categoria sem proprietário.")
            
            categoria = CategoriaDespesa(
                nome=nome,
                descricao=descricao,
                usuario_id=self.usuario_id  # Adicionar ID do usuário atual
            )
            self.session.add(categoria)
            return categoria.id
        return self._safe_query(query)

    def get_categorias_despesa(self):
        def query():
            try:
                categorias = self.session.query(CategoriaDespesa).filter(
                    (CategoriaDespesa.usuario_id == self.usuario_id) | 
                    (CategoriaDespesa.usuario_id.is_(None))
                ).all()
                return pd.DataFrame([{
                    'id': c.id,
                    'nome': c.nome,
                    'descricao': c.descricao,
                    'usuario_id': c.usuario_id
                } for c in categorias])
            except Exception as e:
                print(f"ERRO ao obter categorias de despesa: {str(e)}")
                return pd.DataFrame()
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
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
                
                # Buscar cliente da proposta
                cliente = self.session.query(Cliente).filter_by(id=proposta.cliente_id).first()
                if not cliente:
                    raise ValueError(f"Cliente ID {proposta.cliente_id} não encontrado")
                
                
                # Verificar se já existem lançamentos do tipo "receita_a_receber_aprovacao" para esta proposta
                lancamentos_existentes = self.session.query(Transacao)\
                    .filter_by(proposta_id=proposta_id_int, tipo="receita_a_receber_aprovacao")\
                    .count()
                
                
                # Se já existirem lançamentos, verificar se devemos forçar a regeneração
                if lancamentos_existentes > 0:
                    if forcar_geracao:
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
                    else:
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
                        
                        try:
                            cursor.execute(sql_receita)
                            id_receita_result = cursor.fetchone()
                            if id_receita_result and len(id_receita_result) > 0:
                                id_receita = id_receita_result[0]
                            else:
                                pass
                            
                            # Removido o lançamento de "Valor a receber" para evitar duplicidade
                            
                            # Removidos os lançamentos de comissão sobre fornecedores e pagamento de equipe/assistentes
                            # Mantemos apenas o lançamento principal de receita
                            
                            # Garantir que tudo seja confirmado
                            conn.commit()
                        except Exception as cursor_error:
                            conn.rollback()
                            raise
                        finally:
                            # Fechar a conexão apenas se ainda estiver aberta
                            if not cursor.closed:
                                cursor.close()
                            if conn and not conn.closed:
                                conn.close()
                        
                        result["valor_base"] = valor_base
                        result["lancamentos_gerados"] = 1  # Apenas um lançamento: receita principal
                        
                    except Exception as sql_error:
                        print(f"ERRO EM SQL DIRETO: {str(sql_error)}")
                        import traceback
                        traceback.print_exc()
                        
                        # Em caso de falha no SQL direto, tentar o método ORM original como fallback
                        
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
                        
                        # Removidos os lançamentos de comissão sobre fornecedores e pagamento de equipe/assistentes
                        # Mantemos apenas o lançamento principal de receita
                        
                        self.session.flush()  # Forçar um flush para detectar erros antes do commit
                        
                        result["valor_base"] = valor_base
                        result["lancamentos_gerados"] += 1  # Apenas um lançamento: receita principal
                
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
            
            # Salvar as alterações para garantir que tudo esteja atualizado antes de gerar lançamentos
            self.session.flush()
            
            # Preparar objeto de resultado
            resultado = {"status": True, "message": f"Proposta {proposta_id} atualizada com status '{novo_status}'"}
            
            # Gerar lançamentos quando a proposta estiver mudando para "Em execução" ou "Aprovada"
            # Removida a verificação de lancamentos_existentes == 0 para garantir que o lançamento seja gerado
            if status_antigo in ["Em elaboração", "Aguardando aprovação"] and (novo_status == "Em execução" or novo_status == "Aprovada"):
                try:
                    # Forçar regeneração de lançamentos para garantir que o valor base seja criado
                    # O parâmetro forcar_geracao=True remove lançamentos existentes antes de criar novos
                    resultado_lancamentos = self.gerar_lancamentos_proposta_aprovada(proposta_id, forcar_geracao=True)
                    resultado["lancamentos"] = {"status": "success", "message": "Lançamentos financeiros gerados com sucesso"}
                except Exception as e:
                    print(f"ERRO ao gerar lançamentos para proposta em execução: {str(e)}")
                    resultado["lancamentos"] = {"status": "error", "message": f"Erro ao gerar lançamentos: {str(e)}"}
            elif lancamentos_existentes > 0:
                resultado["lancamentos"] = {"status": "ignored", "message": "Proposta já possui lançamentos financeiros"}
            
            # Registrar a mudança de status
            
            # GATILHO: Criar pós-organização quando proposta é FINALIZADA
            if novo_status == "Finalizada" and proposta.status_execucao == "Finalizada":
                try:
                    data_final = proposta.data_fim if proposta.data_fim else datetime.now().date()
                    self.create_post_organization(
                        proposta_id=proposta.id,
                        cliente_id=proposta.cliente_id,
                        data_final_projeto=data_final
                    )
                    resultado["pos_organizacao"] = {"status": "success", "message": "Pós-organização criada automaticamente"}
                except Exception as e:
                    print(f"ERRO ao criar pós-organização: {str(e)}")
                    resultado["pos_organizacao"] = {"status": "error", "message": f"Erro: {str(e)}"}
            
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
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            try:
                # Buscar o usuario_id da proposta
                get_usuario_sql = f"SELECT usuario_id FROM propostas WHERE id = {proposta_id_int}"
                cursor.execute(get_usuario_sql)
                usuario_result = cursor.fetchone()
                
                if not usuario_result or usuario_result[0] is None:
                    if self.usuario_id:
                        usuario_id = self.usuario_id
                    else:
                        return None
                else:
                    usuario_id = usuario_result[0]
                
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
                
                
                cursor.execute(sql)
                result = cursor.fetchone()
                conn.commit()
                
                if result and result[0]:
                    produto_id = result[0]
                    
                    # Verificar se o produto foi realmente adicionado
                    verify_sql = f"SELECT COUNT(*) FROM produtos_organizadores WHERE id = {produto_id}"
                    cursor.execute(verify_sql)
                    verify_result = cursor.fetchone()
                    if verify_result and verify_result[0] > 0:
                        pass
                    else:
                        pass
                    
                    return produto_id
                else:
                    return None
            finally:
                # Sempre fechar a conexão
                cursor.close()
                conn.close()
                
        except Exception as e:
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
            
            return produto.id
            
        except Exception as e:
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
            try:
                query = self.session.query(ProdutoOrganizador).filter(
                    (ProdutoOrganizador.usuario_id == self.usuario_id) | 
                    (ProdutoOrganizador.usuario_id.is_(None))
                )
                
                # Aplicar filtros
                if proposta_id:
                    # Converter explicitamente para int Python padrão
                    proposta_id_int = self._ensure_int(proposta_id)
                    query = query.filter_by(proposta_id=proposta_id_int)
                    
                produtos = query.all()
                return pd.DataFrame([{
                    'id': p.id,
                    'nome': p.nome,
                    'descricao': p.descricao,
                    'valor': p.valor,
                    'quantidade': p.quantidade,
                    'comodo': p.comodo,
                    'data_cadastro': p.data_cadastro,
                    'usuario_id': p.usuario_id
                } for p in produtos])
            except Exception as e:
                print(f"ERRO ao obter produtos organizadores: {str(e)}")
                return pd.DataFrame()
        return self._safe_query(query)
        
    def remove_produto_organizador(self, produto_id):
        """
        Remove um produto de uma proposta
        
        Args:
            produto_id: ID do produto a ser removido
            
        Returns:
            bool: True se o produto foi removido com sucesso, False caso contrário
        """
        # Primeiro tentar remover via SQL direto para evitar problemas de sessão
        try:
            import psycopg2
            import os
            
            # Obter a string de conexão do ambiente
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL não disponível no ambiente")
                
            # Conectar diretamente via psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Executar DELETE
            cursor.execute(
                "DELETE FROM produtos_organizadores WHERE id = %s", 
                (produto_id,)
            )
            
            # Verificar se alguma linha foi afetada
            affected_rows = cursor.rowcount
            
            # Confirmar a operação
            conn.commit()
            cursor.close()
            conn.close()
            
            # Se alguma linha foi afetada, a operação foi bem-sucedida
            if affected_rows > 0:
                print(f"Produto ID {produto_id} removido com sucesso via SQL direto")
                return True
            else:
                print(f"Nenhum produto encontrado com ID {produto_id}")
                return False
                
        except Exception as e:
            print(f"Erro ao remover produto via SQL direto: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Se o SQL direto falhou, tentar via ORM
            try:
                def query():
                    # Buscar o produto
                    produto = self.session.query(ProdutoOrganizador).filter_by(id=produto_id).first()
                    if not produto:
                        raise ValueError(f"Produto não encontrado com ID {produto_id}")
                        
                    # Remover o produto
                    self.session.delete(produto)
                    self.session.commit()
                    
                    return True
                    
                return self._safe_query(query)
            except Exception as e2:
                print(f"Erro ao remover produto via ORM: {str(e2)}")
                traceback.print_exc()
                return False

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
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar o assistente sem proprietário.")
            
            assistente = Assistente(
                nome=nome,
                telefone=telefone,
                endereco=endereco,
                pix=pix,
                observacoes=observacoes,
                usuario_id=self.usuario_id  # Adicionar ID do usuário atual
            )
            self.session.add(assistente)
            return assistente.id
        return self._safe_query(query)

    def get_assistentes(self):
        def query():
            try:
                assistentes = self.session.query(Assistente).filter(
                    (Assistente.usuario_id == self.usuario_id) | 
                    (Assistente.usuario_id.is_(None))
                ).all()
                return pd.DataFrame([{
                    'id': a.id,
                    'nome': a.nome,
                    'telefone': a.telefone,
                    'endereco': a.endereco,
                    'pix': a.pix,
                    'observacoes': a.observacoes,
                    'usuario_id': a.usuario_id
                } for a in assistentes])
            except Exception as e:
                print(f"ERRO ao obter assistentes: {str(e)}")
                return pd.DataFrame()
        return self._safe_query(query)

    def add_parceiro(self, nome, telefone, area_atuacao, tipo_parceria, 
                estado=None, cidade=None, bairro=None, endereco=None, 
                pix=None, observacoes=None):
        def query():
            # Verificar se temos um ID de usuário válido antes de continuar
            if not self.usuario_id:
                raise ValueError("ID de usuário não definido. Não é possível criar o parceiro sem proprietário.")
            
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
                observacoes=observacoes,
                usuario_id=self.usuario_id  # Adicionar ID do usuário atual
            )
            self.session.add(parceiro)
            return parceiro.id
        return self._safe_query(query)

    def get_parceiros(self):
        def query():
            try:
                parceiros = self.session.query(Parceiro).filter(
                    (Parceiro.usuario_id == self.usuario_id) | 
                    (Parceiro.usuario_id.is_(None))
                ).all()
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
                    'data_cadastro': p.data_cadastro,
                    'usuario_id': p.usuario_id
                } for p in parceiros])
            except Exception as e:
                print(f"ERRO ao obter parceiros: {str(e)}")
                return pd.DataFrame()
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
    
    def update_proposta(self, proposta_id, 
                       cliente_id=None, 
                       descricao=None,
                       valor=None, 
                       status=None, 
                       tipo_proposta=None,
                       data_inicio=None, 
                       data_fim=None, 
                       prazo_entrega=None,
                       data_proposta=None,
                       previsao_dias=None,
                       data_inicio_execucao=None,
                       status_execucao=None,
                       **kwargs):
        """
        Método para atualizar uma proposta existente.
        Compatibilidade com o método update_proposta usado em algumas partes do código.
        
        Args:
            proposta_id: ID da proposta a ser atualizada
            cliente_id: ID do cliente (opcional)
            descricao: Descrição da proposta (opcional)
            valor: Valor da proposta (opcional)
            status: Status da proposta (opcional)
            tipo_proposta: Tipo da proposta (opcional)
            data_inicio: Data de início (opcional)
            data_fim: Data de fim (opcional)
            prazo_entrega: Prazo de entrega (opcional)
            data_proposta: Data da proposta (opcional)
            previsao_dias: Previsão em dias (opcional)
            data_inicio_execucao: Data de início da execução (opcional)
            status_execucao: Status de execução (opcional)
            **kwargs: Campos adicionais (opcional)
            
        Returns:
            dict: Status e mensagem do resultado da operação
        """
        def query():
            try:
                # Converter ID para int
                proposta_id_int = int(proposta_id)
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    return {"status": "error", "message": f"Proposta ID {proposta_id} não encontrada"}
                
                # Atualizar os campos fornecidos
                if cliente_id is not None:
                    proposta.cliente_id = cliente_id
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
                if data_fim is not None:
                    proposta.data_fim = data_fim
                if prazo_entrega is not None:
                    proposta.prazo_entrega = prazo_entrega
                if data_proposta is not None:
                    proposta.data_proposta = data_proposta
                if previsao_dias is not None:
                    proposta.previsao_dias = previsao_dias
                if data_inicio_execucao is not None:
                    proposta.data_inicio_execucao = data_inicio_execucao
                if status_execucao is not None:
                    proposta.status_execucao = status_execucao
                
                # Processar campos adicionais passados como kwargs
                for key, value in kwargs.items():
                    if hasattr(proposta, key):
                        setattr(proposta, key, value)
                
                self.session.commit()
                return {"status": "success", "message": f"Proposta {proposta_id} atualizada com sucesso"}
            except Exception as e:
                self.session.rollback()
                return {"status": "error", "message": f"Erro ao atualizar proposta: {str(e)}"}
        
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
                            
                            # GATILHO: Criar pós-organização quando proposta é finalizada
                            try:
                                data_final = proposta.data_fim if proposta.data_fim else datetime.now().date()
                                self.create_post_organization(
                                    proposta_id=proposta.id,
                                    cliente_id=proposta.cliente_id,
                                    data_final_projeto=data_final
                                )
                                resultado["pos_organizacao"] = {"status": "success", "message": "Pós-organização criada automaticamente"}
                            except Exception as po_error:
                                print(f"ERRO ao criar pós-organização: {str(po_error)}")
                                resultado["pos_organizacao"] = {"status": "error", "message": f"Erro: {str(po_error)}"}
                                
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
                    
                    # Criar objeto de acréscimo com valores já verificados
                    # Garantir que o tipo esteja em maiúsculas para consistência
                    tipo_upper = tipo.upper() if tipo else "OUTROS"
                    
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
                    import traceback
                    traceback.print_exc()
                    self.session.rollback()  # Fazer rollback em caso de erro
                    raise e
                    
            # Usar _safe_query para garantir transação adequada
            resultado = self._safe_query(query)
            return resultado
            
        except Exception as e:
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
        

        def query():
            try:
                # Verificar se a proposta existe
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                if not proposta:
                    # Retornar DataFrame vazio em vez de levantar exceção
                    return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
                # Buscar acréscimos
                acrescimos = self.session.query(AcrescimoProposta).filter_by(proposta_id=proposta_id).all()
                
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
                import traceback
                traceback.print_exc()
                # Ainda retorna DataFrame vazio em caso de erro para evitar quebrar a UI
                return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
        return self._safe_query(query)
    
    def update_acrescimo_proposta(self, acrescimo_id, valor=None, descricao=None):
        """
        Atualiza um acréscimo de uma proposta
        
        Args:
            acrescimo_id: ID do acréscimo a ser atualizado
            valor: Novo valor (opcional)
            descricao: Nova descrição (opcional)
            
        Returns:
            bool: True se o acréscimo foi atualizado com sucesso, False caso contrário
        """
        try:
            import psycopg2
            import os
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL não disponível no ambiente")
                
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Construir a query de atualização dinamicamente
            updates = []
            params = []
            
            if valor is not None:
                updates.append("valor = %s")
                params.append(valor)
            
            if descricao is not None:
                updates.append("descricao = %s")
                params.append(descricao)
            
            if not updates:
                return False
            
            params.append(acrescimo_id)
            
            query = f"UPDATE acrescimos_proposta SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, params)
            
            affected_rows = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                print(f"Acréscimo ID {acrescimo_id} atualizado com sucesso")
                return True
            else:
                print(f"Nenhum acréscimo encontrado com ID {acrescimo_id}")
                return False
                
        except Exception as e:
            print(f"Erro ao atualizar acréscimo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    def remove_acrescimo_proposta(self, acrescimo_id):
        """
        Remove um acréscimo de uma proposta
        
        Args:
            acrescimo_id: ID do acréscimo a ser removido
            
        Returns:
            bool: True se o acréscimo foi removido com sucesso, False caso contrário
        """
        # Primeiro tentar remover via SQL direto para evitar problemas de sessão
        try:
            import psycopg2
            import os
            
            # Obter a string de conexão do ambiente
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL não disponível no ambiente")
                
            # Conectar diretamente via psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Executar DELETE
            cursor.execute(
                "DELETE FROM acrescimos_proposta WHERE id = %s", 
                (acrescimo_id,)
            )
            
            # Verificar se alguma linha foi afetada
            affected_rows = cursor.rowcount
            
            # Confirmar a operação
            conn.commit()
            cursor.close()
            conn.close()
            
            # Se alguma linha foi afetada, a operação foi bem-sucedida
            if affected_rows > 0:
                print(f"Acréscimo ID {acrescimo_id} removido com sucesso via SQL direto")
                return True
            else:
                print(f"Nenhum acréscimo encontrado com ID {acrescimo_id}")
                return False
                
        except Exception as e:
            print(f"Erro ao remover acréscimo via SQL direto: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Se o SQL direto falhou, tentar via ORM
            try:
                def query():
                    # Buscar o acréscimo
                    acrescimo = self.session.query(AcrescimoProposta).filter_by(id=acrescimo_id).first()
                    if not acrescimo:
                        raise ValueError(f"Acréscimo não encontrado com ID {acrescimo_id}")
                        
                    # Remover o acréscimo
                    self.session.delete(acrescimo)
                    self.session.commit()
                    
                    return True
                    
                return self._safe_query(query)
            except Exception as e2:
                print(f"Erro ao remover acréscimo via ORM: {str(e2)}")
                traceback.print_exc()
                return False
        
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
        

        def query():
            try:
                # Verificar se a proposta existe
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                if not proposta:
                    return pd.DataFrame()
                
                # Obter acréscimos do tipo especificado (garantindo que o tipo seja maiúsculo)
                tipo_upper = tipo.upper() if tipo else "OUTROS"
                
                acrescimos = self.session.query(AcrescimoProposta).filter_by(
                    proposta_id=proposta_id, 
                    tipo=tipo_upper
                ).order_by(AcrescimoProposta.data_cadastro).all()
                
                if not acrescimos:
                    return pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                
                
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
        
        # Usar o parâmetro recebido diretamente
        proposta_id = proposta_id_param
        
        # Converter para int se for string
        try:
            if isinstance(proposta_id, str):
                proposta_id = int(proposta_id)
            
            
            # Criar uma nova sessão para esta operação
            try:
                # Verificar se a proposta existe
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                
                if proposta:
                    # Excluir registros financeiros relacionados primeiro
                    transacoes = self.session.query(Transacao).filter_by(proposta_id=proposta_id).all()
                    self.session.query(Transacao).filter_by(proposta_id=proposta_id).delete()
                
                    # Excluir outros registros relacionados
                    andamentos = self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).all()
                    self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).delete()
                    
                    produtos = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id).all()
                    self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id).delete()
                    
                    # Usar SQL direto em vez de ORM para evitar problemas com a coluna percentual_comissao
                    from sqlalchemy import text
                    # Contar acréscimos primeiro
                    count_result = self.session.execute(text(f"SELECT COUNT(*) FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                    count = count_result.scalar()
                    
                    # Usar SQL direto para excluir
                    self.session.execute(text(f"DELETE FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                    
                    # Manter a sessão consistente
                    self.session.flush()
                    
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
                        
                        # Para cada venda, excluir seus itens
                        for venda_id in vendas_ids:
                            # Excluir itens da venda
                            self.session.execute(text(f"DELETE FROM itens_venda WHERE venda_id = {venda_id}"))
                            
                            # Excluir transações relacionadas à venda
                            self.session.execute(text(f"DELETE FROM financeiro WHERE origem_id = {venda_id} AND origem_tipo = 'venda'"))
                            
                            # Excluir a venda
                            self.session.execute(text(f"DELETE FROM vendas WHERE id = {venda_id}"))
                        
                    
                    # Manter a sessão consistente
                    self.session.flush()
                    
                    # Excluir a proposta
                    self.session.delete(proposta)
                    
                    # Commit explícito para garantir que tudo seja salvo
                    self.session.commit()
                    
                    return True, "Proposta excluída com sucesso"
                else:
                    return False, f"Proposta ID {proposta_id} não encontrada"
            except Exception as e:
                self.session.rollback()
                return False, f"Erro ao excluir proposta: {str(e)}"
        except Exception as e:
            return False, f"Erro ao processar ID da proposta: {str(e)}"
    
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
                    
                    
                    try:
                        # Excluir registros financeiros relacionados primeiro
                        # Esta é a tabela que estava causando a violação de chave estrangeira
                        transacoes = self.session.query(Transacao).filter_by(proposta_id=proposta_id_local).all()
                        self.session.query(Transacao).filter_by(proposta_id=proposta_id_local).delete()
                    
                        # Excluir outros registros relacionados
                        andamentos = self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id_local).all()
                        self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id_local).delete()
                        
                        produtos = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_local).all()
                        self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_local).delete()
                        
                        # Usar SQL direto em vez de ORM para evitar problemas com a coluna percentual_comissao
                        from sqlalchemy import text
                        # Contar acréscimos primeiro
                        count_result = self.session.execute(text(f"SELECT COUNT(*) FROM acrescimos_proposta WHERE proposta_id = {proposta_id_local}"))
                        count = count_result.scalar()
                        
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
                            
                            # Para cada venda, excluir seus itens
                            for venda_id in vendas_ids:
                                # Excluir itens da venda
                                self.session.execute(text(f"DELETE FROM itens_venda WHERE venda_id = {venda_id}"))
                                
                                # Excluir transações relacionadas à venda
                                self.session.execute(text(f"DELETE FROM financeiro WHERE origem_id = {venda_id} AND origem_tipo = 'venda'"))
                                
                                # Excluir a venda
                                self.session.execute(text(f"DELETE FROM vendas WHERE id = {venda_id}"))
                            
                        
                        # Excluir a proposta
                        self.session.delete(proposta)
                        
                        return {"status": True, "message": "Proposta excluída com sucesso"}
                    except Exception as e:
                        self.session.rollback()
                        return {"status": False, "message": f"Erro ao excluir proposta: {str(e)}"}
                else:
                    return {"status": False, "message": f"Proposta #{numero_proposta} não encontrada"}
            except Exception as e:
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
                    return False
                
                # Remover acréscimo com SQL direto
                self.session.execute(
                    text(f"DELETE FROM acrescimos_proposta WHERE id = {acrescimo_id_int}")
                )
                self.session.flush()
                
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
                    return False
                
                # Verificar isolamento de dados através da proposta
                if self.usuario_id:
                    proposta = self.session.query(Proposta).filter_by(id=produto.proposta_id).first()
                    if proposta and proposta.usuario_id != self.usuario_id:
                        raise ValueError("Você não tem permissão para remover este produto")
                
                # Excluir o produto
                self.session.delete(produto)
                self.session.flush()
                
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
        
        def query():
            try:
                proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
                
                if not proposta:
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
                    
                return True
            
            except Exception as e:
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
    
    def verificar_produto_em_vendas(self, produto_id):
        """Verifica se um produto está sendo usado em vendas"""
        def query():
            from sqlalchemy import func
            # Contar vendas que usam este produto
            count = self.session.query(func.count(ItemVenda.id)).filter(
                ItemVenda.produto_id == produto_id
            ).scalar()
            return count or 0
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
    def add_venda(self, cliente_id, itens, forma_pagamento=None, observacoes=None, data_venda=None):
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
                data_venda=data_venda if data_venda else datetime.now().date(),
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
                'cliente_id': v.cliente_id,
                'cliente_nome': v.cliente.nome if v.cliente else "Cliente não encontrado",
                'valor_total': v.valor_total,
                'data_venda': v.data_venda,
                'status': v.status,
                'forma_pagamento': v.forma_pagamento,
                'observacoes': v.observacoes,
                'usuario_id': v.usuario_id,
                'proposta_id': v.proposta_id,
                'proposta_numero': (v.proposta.numero if v.proposta else None),
                'proposta_descricao': (v.proposta.descricao if v.proposta and v.proposta.descricao else None),
            } for v in vendas])
        return self._safe_query(query)
        
    def get_itens_venda(self, venda_id):
        """Retorna os itens de uma venda específica"""
        def query():
            # Fazer join explícito com produtos para garantir que os nomes sejam carregados
            itens = self.session.query(ItemVenda).join(Produto, ItemVenda.produto_id == Produto.id, isouter=True).filter(ItemVenda.venda_id == venda_id).all()
            
            dados_itens = []
            for i in itens:
                # Priorizar o nome do produto relacionado, depois a descrição
                produto_nome = 'Produto não identificado'
                if i.produto and hasattr(i.produto, 'nome') and i.produto.nome:
                    produto_nome = i.produto.nome
                elif i.descricao and i.descricao.strip():
                    produto_nome = i.descricao
                
                if i.produto:
                    pass
                
                # Calcular lucro usando custo real ou estimativa de 40% de margem
                preco_custo = 0
                if i.produto and hasattr(i.produto, 'preco_custo') and i.produto.preco_custo and i.produto.preco_custo > 0:
                    preco_custo = i.produto.preco_custo
                else:
                    # Usar margem de 40% como estimativa se não tiver custo definido (60% do preço = custo)
                    preco_custo = i.preco_unitario * 0.6
                
                lucro_item = round((i.preco_unitario - preco_custo) * i.quantidade, 2)
                
                item_data = {
                    'id': i.id,
                    'produto_nome': produto_nome,
                    'quantidade': i.quantidade,
                    'preco_unitario': round(i.preco_unitario, 2),
                    'subtotal': round(i.subtotal if i.subtotal else (i.preco_unitario * i.quantidade), 2),
                    'lucro': lucro_item
                }
                dados_itens.append(item_data)
            
            return pd.DataFrame(dados_itens)
        return self._safe_query(query)

    def adicionar_venda(self, cliente_id, data_venda, forma_pagamento, observacoes=""):
        """Adiciona uma nova venda"""
        def query():
            nova_venda = Venda(
                cliente_id=cliente_id,
                data_venda=data_venda,
                valor_total=0.0,  # Será calculado quando itens forem adicionados
                status="Em aberto",
                forma_pagamento=forma_pagamento,
                observacoes=observacoes,
                usuario_id=self.usuario_id
            )
            
            self.session.add(nova_venda)
            self.session.flush()  # Para obter o ID
            return nova_venda.id
        
        return self._safe_query(query)

    def adicionar_item_venda(self, venda_id, produto_id, quantidade, preco_unitario, descricao=""):
        """Adiciona um item a uma venda"""
        def query():
            # Calcular subtotal
            subtotal = quantidade * preco_unitario
            
            novo_item = ItemVenda(
                venda_id=venda_id,
                produto_id=produto_id,
                descricao=descricao,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=subtotal
            )
            
            self.session.add(novo_item)
            
            # Atualizar valor total da venda
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if venda:
                total_itens = self.session.query(func.sum(ItemVenda.subtotal)).filter_by(venda_id=venda_id).scalar() or 0
                venda.valor_total = total_itens + subtotal
            
            self.session.flush()
            return novo_item.id
        
        return self._safe_query(query)

    def finalizar_venda(self, venda_id):
        """Finaliza uma venda alterando seu status"""
        def query():
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if venda:
                venda.status = "Finalizada"
                return True
            return False
        
        return self._safe_query(query)

    def atualizar_estoque_produto(self, produto_id, quantidade_vendida):
        """Atualiza o estoque de um produto após venda"""
        def query():
            produto = self.session.query(Produto).filter_by(id=produto_id).first()
            if produto and hasattr(produto, 'estoque'):
                if produto.estoque >= quantidade_vendida:
                    produto.estoque -= quantidade_vendida
                    return True
                else:
                    raise ValueError(f"Estoque insuficiente. Disponível: {produto.estoque}, Solicitado: {quantidade_vendida}")
            return False
        
        return self._safe_query(query)

    def excluir_venda(self, venda_id):
        """Exclui uma venda e seus itens, devolvendo produtos ao estoque"""
        def query():
            # Buscar a venda
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if not venda:
                raise ValueError(f"Venda com ID {venda_id} não encontrada")
            
            # Buscar itens da venda para devolver ao estoque
            itens = self.session.query(ItemVenda).filter_by(venda_id=venda_id).all()
            
            # Devolver produtos ao estoque
            for item in itens:
                if item.produto_id:
                    produto = self.session.query(Produto).filter_by(id=item.produto_id).first()
                    if produto and hasattr(produto, 'estoque'):
                        produto.estoque += item.quantidade
            
            # Excluir itens da venda
            for item in itens:
                self.session.delete(item)
            
            # Excluir a venda
            self.session.delete(venda)
            
            return True
        
        return self._safe_query(query)

    def atualizar_venda(self, venda_id, cliente_id=None, data_venda=None, forma_pagamento=None, observacoes=None, status=None):
        """Atualiza dados básicos de uma venda"""
        def query():
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if not venda:
                raise ValueError(f"Venda com ID {venda_id} não encontrada")
            
            # Atualizar campos se fornecidos
            if cliente_id is not None:
                venda.cliente_id = cliente_id
            if data_venda is not None:
                venda.data_venda = data_venda
            if forma_pagamento is not None:
                venda.forma_pagamento = forma_pagamento
            if observacoes is not None:
                venda.observacoes = observacoes
            if status is not None:
                venda.status = status
            
            return True
        
        return self._safe_query(query)

    def atualizar_item_venda(self, item_id, quantidade=None, preco_unitario=None):
        """Atualiza um item específico de uma venda"""
        def query():
            item = self.session.query(ItemVenda).filter_by(id=item_id).first()
            if not item:
                raise ValueError(f"Item com ID {item_id} não encontrado")
            
            # Atualizar campos se fornecidos
            if quantidade is not None:
                item.quantidade = quantidade
            if preco_unitario is not None:
                item.preco_unitario = preco_unitario
            
            # Recalcular subtotal
            item.subtotal = item.quantidade * item.preco_unitario
            
            # Atualizar valor total da venda
            venda = self.session.query(Venda).filter_by(id=item.venda_id).first()
            if venda:
                total_itens = self.session.query(func.sum(ItemVenda.subtotal)).filter_by(venda_id=item.venda_id).scalar() or 0
                venda.valor_total = total_itens
            
            return True
        
        return self._safe_query(query)

    def remover_item_venda(self, item_id):
        """Remove um item específico de uma venda"""
        def query():
            item = self.session.query(ItemVenda).filter_by(id=item_id).first()
            if not item:
                raise ValueError(f"Item com ID {item_id} não encontrado")
            
            venda_id = item.venda_id
            
            # Devolver produto ao estoque se aplicável
            if item.produto_id:
                produto = self.session.query(Produto).filter_by(id=item.produto_id).first()
                if produto and hasattr(produto, 'estoque'):
                    produto.estoque += item.quantidade
            
            # Remover item
            self.session.delete(item)
            
            # Atualizar valor total da venda
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if venda:
                total_itens = self.session.query(func.sum(ItemVenda.subtotal)).filter_by(venda_id=venda_id).scalar() or 0
                venda.valor_total = total_itens or 0
            
            return True
        
        return self._safe_query(query)
        
    def update_item_venda(self, item_id, nova_quantidade, novo_preco):
        """Atualiza a quantidade e preço de um item da venda"""
        def query():
            item = self.session.query(ItemVenda).filter_by(id=item_id).first()
            if not item:
                raise ValueError(f"Item não encontrado com ID {item_id}")
            
            # Atualizar valores
            item.quantidade = nova_quantidade
            item.preco_unitario = novo_preco
            item.subtotal = nova_quantidade * novo_preco
            
            # Atualizar valor total da venda
            venda = item.venda
            if venda:
                total = sum(i.subtotal for i in venda.itens)
                venda.valor_total = total
            
            return True
        return self._safe_query(query)
        
    def remove_item_venda(self, item_id):
        """Remove um item da venda"""
        def query():
            item = self.session.query(ItemVenda).filter_by(id=item_id).first()
            if not item:
                raise ValueError(f"Item não encontrado com ID {item_id}")
            
            # Obter a venda antes de remover o item
            venda = item.venda
            
            # Estornar produto ao estoque se houver
            if item.produto:
                item.produto.estoque += item.quantidade
            
            # Remover o item
            self.session.delete(item)
            
            # Atualizar valor total da venda
            if venda:
                total = sum(i.subtotal for i in venda.itens if i.id != item_id)
                venda.valor_total = total
            
            return True
        return self._safe_query(query)

    def add_item_venda(self, venda_id, produto_id, quantidade, preco_unitario):
        """Adiciona um novo item a uma venda existente"""
        def query():
            # Verificar se a venda existe
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if not venda:
                raise ValueError(f"Venda não encontrada com ID {venda_id}")
            
            # Verificar se o produto existe
            produto = self.session.query(Produto).filter_by(id=produto_id).first()
            if not produto:
                raise ValueError(f"Produto não encontrado com ID {produto_id}")
            
            # Verificar se há estoque suficiente
            if produto.estoque < quantidade:
                raise ValueError(f"Estoque insuficiente. Disponível: {produto.estoque}")
            
            # Calcular subtotal
            subtotal = quantidade * preco_unitario
            
            # Criar novo item da venda
            novo_item = ItemVenda(
                venda_id=venda_id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=subtotal,
                usuario_id=venda.usuario_id
            )
            
            # Adicionar ao banco
            self.session.add(novo_item)
            
            # Reduzir estoque
            produto.estoque -= quantidade
            
            # Atualizar valor total da venda
            venda.valor_total = sum(item.subtotal for item in venda.itens) + subtotal
            
            return True
        
        return self._safe_query(query)

    def recalcular_valor_total_venda(self, venda_id):
        """Recalcula o valor total de uma venda baseado nos seus itens"""
        def query():
            venda = self.session.query(Venda).filter_by(id=venda_id).first()
            if not venda:
                raise ValueError(f"Venda não encontrada com ID {venda_id}")
            
            # Calcular total baseado nos itens atuais
            total = sum(item.subtotal for item in venda.itens)
            venda.valor_total = total
            
            return True
        
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
                
                # Obter informações da venda antes de excluí-la para estornar produtos
                venda = self.session.query(Venda).filter_by(id=venda_id).first()
                
                if not venda:
                    return False
                
                # Estornar produtos para o estoque
                if venda.status != 'Cancelada' and hasattr(venda, 'itens'):
                    for item in venda.itens:
                        if hasattr(item, 'produto') and item.produto is not None:
                            item.produto.estoque += item.quantidade
                
                # Executar SQL para excluir na ordem correta
                # 1. Excluir transações financeiras relacionadas
                transacoes_stmt = text("""
                    DELETE FROM financeiro 
                    WHERE origem_id = :venda_id AND origem_tipo = 'venda'
                """)
                self.session.execute(transacoes_stmt, {"venda_id": venda_id})
                
                # 2. Excluir itens da venda
                itens_stmt = text("""
                    DELETE FROM itens_venda
                    WHERE venda_id = :venda_id
                """)
                self.session.execute(itens_stmt, {"venda_id": venda_id})
                
                # 3. Finalmente excluir a venda
                venda_stmt = text("""
                    DELETE FROM vendas
                    WHERE id = :venda_id
                """)
                self.session.execute(venda_stmt, {"venda_id": venda_id})
                
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
                venda = self.session.query(Venda).filter_by(id=venda_id).first()
                
                if not venda:
                    return False
                
                
                # Estornar produtos para o estoque antes de excluir
                if hasattr(venda, 'itens'):
                    for item in venda.itens:
                        if hasattr(item, 'produto') and item.produto is not None:
                            if venda.status != 'Cancelada':
                                item.produto.estoque += item.quantidade
                        else:
                            pass
                else:
                    pass
                
                # Verificar e excluir transações financeiras relacionadas
                transacoes = self.session.query(Transacao).filter_by(
                    origem_id=venda_id,
                    origem_tipo='venda'
                ).all()
                
                for transacao in transacoes:
                    self.session.delete(transacao)
                
                # Para lidar com possíveis referências à proposta
                if hasattr(venda, 'proposta_id') and venda.proposta_id:
                    # Apenas desvincular, não excluir a proposta
                    venda.proposta_id = None
                
                # Remover itens da venda primeiro (devido à restrição de chave estrangeira)
                if hasattr(venda, 'itens'):
                    itens = list(venda.itens)  # Criar uma cópia da lista para evitar problemas de iteração
                    for item in itens:
                        self.session.delete(item)
                
                # Por precaução, realizar flush antes de excluir a venda
                self.session.flush()
                
                # Remover a venda
                self.session.delete(venda)
                
                # Realizar flush novamente para garantir a exclusão
                self.session.flush()
                
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
                        return False
                    
                    # Estornar produtos para o estoque
                    if venda.status != 'Cancelada' and hasattr(venda, 'itens'):
                        for item in venda.itens:
                            if hasattr(item, 'produto') and item.produto is not None:
                                item.produto.estoque += item.quantidade
                    
                    # Executar SQL para excluir na ordem correta
                    # 1. Excluir transações financeiras relacionadas
                    self.session.execute(text("""
                        DELETE FROM financeiro 
                        WHERE origem_id = :venda_id AND origem_tipo = 'venda'
                    """), {"venda_id": venda_id})
                    
                    # 2. Excluir itens da venda
                    self.session.execute(text("""
                        DELETE FROM itens_venda
                        WHERE venda_id = :venda_id
                    """), {"venda_id": venda_id})
                    
                    # 3. Atualizar vendas para remover referência à proposta
                    self.session.execute(text("""
                        UPDATE vendas
                        SET proposta_id = NULL
                        WHERE id = :venda_id
                    """), {"venda_id": venda_id})
                    
                    # 4. Finalmente excluir a venda
                    self.session.execute(text("""
                        DELETE FROM vendas
                        WHERE id = :venda_id
                    """), {"venda_id": venda_id})
                    
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
                # Corrigir: usar None como produto_id para produtos de organização
                # e adicionar a descrição do produto
                produto_org = self.session.query(ProdutoOrganizador).filter_by(id=item["produto_id"]).first()
                descricao = produto_org.nome if produto_org else f"Produto ID {item['produto_id']}"
                
                item_venda = ItemVenda(
                    venda_id=venda.id,
                    produto_id=None,  # Produtos de organização não têm produto_id na tabela produtos
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco_unitario"],
                    subtotal=item["quantidade"] * item["preco_unitario"],
                    descricao=descricao
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
            fornecedores = self.session.query(AcrescimoProposta).filter(
                AcrescimoProposta.proposta_id == proposta.id,
                AcrescimoProposta.tipo == "FORNECEDOR"
            ).all()
            
            
            # Para cada fornecedor, verificar se tem percentual de comissão e gerar receita
            for fornecedor in fornecedores:
                # Verificar se já existe comissão para este fornecedor
                comissao_existente = self.session.query(Transacao).filter(
                    Transacao.proposta_id == proposta.id,
                    Transacao.descricao.like(f"%Comissão%{fornecedor.fornecedor}%")
                ).first()
                
                if not comissao_existente and fornecedor.percentual_comissao and fornecedor.percentual_comissao > 0:
                    
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
                elif comissao_existente:
                    pass
                else:
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
                resultado = self.add_acrescimo_proposta(
                    proposta_id=proposta_id_int,
                    tipo="ASSISTENTE",  # Garantir que o tipo está em maiúsculo
                    valor=valor_float,
                    descricao=observacoes if observacoes else f"Serviço de {assistente.nome}",
                    fornecedor=assistente.nome,
                    status_pagamento="Pendente"
                )
                
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
        
        Gera APENAS:
        1. Produtos a receber (valor total dos produtos)
        
        Nota: A geração automática de lançamentos foi simplificada conforme solicitado:
        - O lançamento de receita principal (valor base) é criado SOMENTE quando a proposta é aprovada, 
          não quando é concluída.
        - Lançamentos de comissão para fornecedores foram removidos.
        - Lançamentos de pagamentos para assistentes foram removidos.
        
        Os valores ainda são calculados para fins de relatório, mas nenhum lançamento 
        financeiro é criado para estes itens.
        
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
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    raise ValueError(f"Proposta ID {proposta_id} não encontrada")
                
                
                # Buscar cliente da proposta
                cliente = self.session.query(Cliente).filter_by(id=proposta.cliente_id).first()
                if not cliente:
                    raise ValueError(f"Cliente ID {proposta.cliente_id} não encontrado")
                
                    
                # Verificar se já existem lançamentos para esta proposta para evitar duplicação
                lancamentos_existentes = self.session.query(Transacao)\
                    .filter_by(proposta_id=proposta_id_int, tipo="receita_a_receber")\
                    .count()
                
                    
                # Se já existirem lançamentos, verificar se devemos forçar a regeneração
                if lancamentos_existentes > 0:
                    # Se forçar_geracao=True, remover os lançamentos existentes e continuar
                    if forcar_geracao:
                        # Remover lançamentos existentes
                        self.session.query(Transacao).filter_by(proposta_id=proposta_id_int).delete()
                        self.session.flush()
                    else:
                        # Verificar se existem transações do tipo produto especificamente
                        transacoes_produtos = self.session.query(Transacao)\
                            .filter_by(proposta_id=proposta_id_int, categoria="Venda de Produtos")\
                            .count()
                            
                        if transacoes_produtos > 0:
                            return {"status": "já existe", "mensagem": "Lançamentos já existem para esta proposta"}
                        else:
                            pass
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
                
                # 1. Valor base (apenas calculado para o resultado, sem criar lançamento)
                valor_base = float(proposta.valor) if proposta.valor else 0
                
                # Obter usuario_id da proposta para garantir isolamento de dados
                usuario_id = proposta.usuario_id if hasattr(proposta, 'usuario_id') else None
                
                # Data dos lançamentos - usar a data de finalização ou data atual
                data_lancamento = datetime.now().date()
                if hasattr(proposta, 'data_fim') and proposta.data_fim:
                    data_lancamento = proposta.data_fim
                
                # Não criamos lançamento de valor base aqui, apenas armazenamos o valor para relatórios
                # O lançamento de receita principal já deve ter sido criado quando a proposta foi aprovada
                if valor_base > 0:
                    # Verificar se já existe uma transação para a receita principal desta proposta
                    transacao_existente = self.session.query(Transacao).filter(
                        Transacao.proposta_id == proposta_id_int,
                        Transacao.categoria == "Serviços de Organização",
                        Transacao.tipo_receita == "organizacao"
                    ).first()
                    
                    if transacao_existente:
                        pass
                    else:
                        pass
                    
                    result["valor_base"] = valor_base
                
                # 2. Produtos a receber
                produtos = self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id_python_int).all()
                
                # Query direto para confirmar problemas
                try:
                    produtos_sql = self.session.execute(text(f"SELECT * FROM produtos_organizadores WHERE proposta_id = {proposta_id_python_int}")).fetchall()
                    
                    if produtos_sql:
                        for p in produtos_sql:
                            pass
                    else:
                        pass
                except Exception as e:
                    print(f"Erro: {e}")
                
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
                    else:
                        produtos_fisicos.append(produto)
                
                # Calcular valores
                valor_total_produtos_fisicos = 0
                valor_total_servicos = 0
                
                # Processar produtos físicos
                for produto in produtos_fisicos:
                    valor_produto = float(produto.valor) * produto.quantidade
                    valor_total_produtos_fisicos += valor_produto
                
                # Processar serviços
                for produto in produtos_servicos:
                    valor_servico = float(produto.valor) * produto.quantidade
                    valor_total_servicos += valor_servico
                
                
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
                
                # Garantir que todos os lançamentos estão salvos
                self.session.flush()
                
                # Não registramos novamente a venda, pois já foi feita antes da criação do lançamento financeiro
                # Esta seção foi removida para evitar duplicação de registros de venda
                
                # Vamos adicionar processamento de itens tipo "OUTRO"
                outros = self.session.query(AcrescimoProposta)\
                    .filter_by(proposta_id=proposta_id_python_int, tipo="OUTRO")\
                    .all()
                    
                
                valor_total_outros = 0
                for outro_item in outros:
                    valor_outro = float(outro_item.valor) if outro_item.valor else 0
                    valor_total_outros += valor_outro
                
                
                # Verificar se já existem lançamentos para Outros a receber
                transacoes_outros = self.session.query(Transacao)\
                    .filter_by(proposta_id=proposta_id_int, 
                              categoria="Outros", 
                              classificacao="contas_a_receber")\
                    .count()
                
                # Criar lançamento para itens OUTRO apenas se não existir ou se forçado
                if valor_total_outros > 0 and (transacoes_outros == 0 or forcar_geracao):
                    
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
                else:
                    if transacoes_outros > 0:
                        pass
                    result["valor_outros"] = valor_total_outros
                
                # 3. Comissões a receber por fornecedor - APENAS para propostas concluídas
                # Verificar se a proposta está concluída antes de gerar lançamentos para fornecedores
                gerar_lancamentos_comissao = False
                if proposta.status == "Concluída" or (hasattr(proposta, 'status_execucao') and proposta.status_execucao == "Concluída"):
                    gerar_lancamentos_comissao = True
                else:
                    pass
                
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
                        
                        # Removidos os lançamentos de comissão sobre fornecedores conforme solicitado
                        if percentual_comissao and percentual_comissao > 0:
                            valor_comissao = valor_fornecedor * (percentual_comissao / 100)
                            
                            if valor_comissao > 0:
                                continue
                else:
                    pass
                
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
                    
                    
                    # Verificar se já existem lançamentos para Assistentes a pagar
                    transacoes_assistentes = self.session.query(Transacao)\
                        .filter_by(proposta_id=proposta_id_int, 
                                  categoria="Assistente", 
                                  classificacao="contas_a_pagar")\
                        .count()
                        
                    
                    # Criar lançamentos individuais para cada assistente (verificando duplicidade por assistente)
                    if valor_total_assistentes > 0:
                        
                        for assistente_item in assistentes:
                            valor_assistente = float(assistente_item.valor) if assistente_item.valor else 0
                            
                            if valor_assistente > 0:
                                nome_assistente = assistente_item.fornecedor  # o campo "fornecedor" armazena o nome do assistente
                                
                                # Removidos os lançamentos de pagamentos para assistentes conforme solicitado
                                continue
                    else:
                        if transacoes_assistentes > 0:
                            pass
                else:
                    pass
                
                result["valor_fornecedores"] = valor_total_fornecedores
                result["valor_assistentes"] = valor_total_assistentes
                
                # Resumo dos resultados - valor monetário total (não confundir com o contador lancamentos_gerados)
                # Mantendo a soma de todos os valores para compatibilidade com código existente
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
            
            # Buscar proposta e cliente pela ID na sessão local
            proposta_id = proposta.id
            cliente_id = cliente.id
            proposta_numero = proposta.numero
            usuario_id = proposta.usuario_id
            
            # Verificar se já existe uma venda para esta proposta na sessão local
            venda_existente = session_local.query(Venda).filter_by(proposta_id=proposta_id).first()
            if venda_existente:
                
                # Se forçar geração, remover a venda existente e seus itens
                if forcar_geracao:
                    # Primeiro remover os itens relacionados
                    try:
                        # Remover transações financeiras relacionadas à venda
                        session_local.query(Transacao).filter_by(
                            origem_id=venda_existente.id,
                            origem_tipo='venda'
                        ).delete()
                        
                        # Remover itens da venda
                        session_local.query(ItemVenda).filter_by(venda_id=venda_existente.id).delete()
                        
                        # Depois remover a venda
                        session_local.query(Venda).filter_by(id=venda_existente.id).delete()
                        session_local.flush()
                    except Exception as e:
                        print(f"ERRO ao remover venda existente: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        session_local.rollback()
                else:
                    # Verificar se a venda tem itens
                    itens = session_local.query(ItemVenda).filter_by(venda_id=venda_existente.id).count()
                    
                    if itens == 0:
                        # Remover a venda sem itens
                        session_local.query(Venda).filter_by(id=venda_existente.id).delete()
                        session_local.flush()
                    else:
                        # Se não forçar, retornar o ID da venda existente
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
                        subtotal=produto_info['subtotal'],
                        usuario_id=usuario_id  # CRÍTICO: Adicionar usuario_id para multi-tenancy
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
                        subtotal=produto_info['subtotal'],
                        usuario_id=usuario_id  # CRÍTICO: Adicionar usuario_id para multi-tenancy
                    )
                session_local.add(item)
            
            # Forçar commit para garantir que a venda seja salva
            session_local.commit()
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

    def get_andamentos(self, proposta_id=None):
        """Busca andamentos filtrados por usuário"""
        def query():
            try:
                # Base query para andamentos
                andamentos_query = self.session.query(AndamentoProposta).filter(
                    (AndamentoProposta.usuario_id == self.usuario_id) | 
                    (AndamentoProposta.usuario_id.is_(None))
                )
                
                # Se proposta_id especificado, filtrar por ele também
                if proposta_id:
                    andamentos_query = andamentos_query.filter(
                        AndamentoProposta.proposta_id == proposta_id
                    )
                
                andamentos = andamentos_query.all()
                
                # Criar DataFrame com compatibilidade total
                df_data = []
                for a in andamentos:
                    row = {
                        'id': a.id,
                        'proposta_id': a.proposta_id,
                        'data': a.data,
                        'status': a.status,
                        'observacao': a.observacao,
                        'descricao': a.observacao,  # Compatibilidade
                        'comodo': a.comodo,
                        'usuario_id': a.usuario_id
                    }
                    df_data.append(row)
                
                df = pd.DataFrame(df_data)
                
                # Se o DataFrame estiver vazio, criar com colunas corretas
                if df.empty:
                    df = pd.DataFrame(columns=['id', 'proposta_id', 'data', 'status', 'observacao', 'descricao', 'comodo', 'usuario_id'])
                
                return df
            except Exception as e:
                print(f"ERRO ao obter andamentos: {str(e)}")
                return pd.DataFrame()
        return self._safe_query(query)

    def add_andamento(self, proposta_id, descricao, data, porcentagem=0, observacoes=""):
        """
        Adiciona um andamento para uma proposta
        
        Args:
            proposta_id: ID da proposta
            descricao: Descrição do andamento
            data: Data do andamento
            porcentagem: Porcentagem de progresso (opcional)
            observacoes: Observações adicionais (opcional)
            
        Returns:
            bool: True se sucesso, False se erro
        """
        def query():
            try:
                # Verificação de segurança
                if not self.usuario_id:
                    raise ValueError("Usuário não autenticado para registrar andamento")
                
                # Criar novo andamento
                andamento = AndamentoProposta(
                    proposta_id=int(proposta_id),
                    observacao=descricao,  # Usar 'observacao' ao invés de 'descricao'
                    data=data,
                    status=f"Progresso: {porcentagem}%",  # Usar status para armazenar a porcentagem
                    usuario_id=self.usuario_id  # Incluir usuario_id para multi-tenant
                )
                
                self.session.add(andamento)
                self.session.commit()
                return True
                
            except Exception as e:
                self.session.rollback()
                raise e
        
        return self._safe_query(query)

    # =========================================
    # MÉTODOS DO MÓDULO PÓS-ORGANIZAÇÃO
    # =========================================
    
    def create_post_organization(self, proposta_id, cliente_id, data_final_projeto):
        """
        Cria um registro de pós-organização e as ações automáticas padrão.
        Chamado automaticamente quando uma proposta é finalizada.
        
        Args:
            proposta_id: ID da proposta finalizada
            cliente_id: ID do cliente
            data_final_projeto: Data de finalização do projeto
            
        Returns:
            int: ID do registro criado ou None se erro
        """
        def query():
            try:
                # Verificar se já existe pós-organização para esta proposta
                existing = self.session.query(PostOrganization).filter(
                    PostOrganization.proposta_id == proposta_id,
                    PostOrganization.usuario_id == self.usuario_id
                ).first()
                
                if existing:
                    print(f"Pós-organização já existe para proposta {proposta_id}")
                    return existing.id
                
                # Criar registro principal
                post_org = PostOrganization(
                    proposta_id=proposta_id,
                    cliente_id=cliente_id,
                    data_final_projeto=data_final_projeto,
                    status='ATIVO',
                    usuario_id=self.usuario_id
                )
                self.session.add(post_org)
                self.session.flush()
                
                # Buscar templates do banco para criar as ações
                templates = self.session.query(PostOrgTemplate).order_by(PostOrgTemplate.dias_apos).all()
                if templates:
                    acoes_padrao = [(t.etapa, data_final_projeto + timedelta(days=t.dias_apos)) for t in templates]
                else:
                    # Fallback com as etapas padrão caso a tabela não exista
                    acoes_padrao = [
                        ('agradecimento',  data_final_projeto + timedelta(days=1)),
                        ('acompanhamento', data_final_projeto + timedelta(days=7)),
                        ('ajuste_fino',    data_final_projeto + timedelta(days=30)),
                        ('feedback',       data_final_projeto + timedelta(days=45)),
                        ('continuidade',   data_final_projeto + timedelta(days=60)),
                    ]

                for action_type, due_date in acoes_padrao:
                    action = PostOrganizationAction(
                        post_organization_id=post_org.id,
                        action_type=action_type,
                        due_date=due_date,
                        status='PENDENTE',
                        usuario_id=self.usuario_id
                    )
                    self.session.add(action)
                
                self.session.commit()
                print(f"Pós-organização criada com sucesso para proposta {proposta_id}")
                return post_org.id
                
            except Exception as e:
                self.session.rollback()
                print(f"Erro ao criar pós-organização: {str(e)}")
                raise e
        
        return self._safe_query(query)
    
    def get_post_organizations(self, status_filter=None):
        """
        Retorna lista de pós-organizações do usuário.
        
        Args:
            status_filter: Filtrar por status ('ATIVO', 'CONCLUIDO') ou None para todos
            
        Returns:
            DataFrame com dados das pós-organizações
        """
        def query():
            try:
                q = self.session.query(PostOrganization).filter(
                    PostOrganization.usuario_id == self.usuario_id
                )
                
                if status_filter:
                    q = q.filter(PostOrganization.status == status_filter)
                
                post_orgs = q.order_by(PostOrganization.created_at.desc()).all()
                
                df_data = []
                for po in post_orgs:
                    # Buscar próxima ação pendente
                    proxima_acao = self.session.query(PostOrganizationAction).filter(
                        PostOrganizationAction.post_organization_id == po.id,
                        PostOrganizationAction.status == 'PENDENTE'
                    ).order_by(PostOrganizationAction.due_date).first()
                    
                    # Buscar nome do cliente
                    cliente = self.session.query(Cliente).filter(Cliente.id == po.cliente_id).first()
                    cliente_nome = cliente.nome if cliente else 'N/A'
                    
                    # Buscar número da proposta
                    proposta = self.session.query(Proposta).filter(Proposta.id == po.proposta_id).first()
                    proposta_numero = proposta.numero if proposta else 'N/A'
                    
                    df_data.append({
                        'id': po.id,
                        'proposta_id': po.proposta_id,
                        'proposta_numero': proposta_numero,
                        'cliente_id': po.cliente_id,
                        'cliente_nome': cliente_nome,
                        'data_final_projeto': po.data_final_projeto,
                        'status': po.status,
                        'created_at': po.created_at,
                        'proxima_acao': proxima_acao.action_type if proxima_acao else None,
                        'proxima_acao_data': proxima_acao.due_date if proxima_acao else None
                    })
                
                return pd.DataFrame(df_data)
                
            except Exception as e:
                print(f"Erro ao buscar pós-organizações: {str(e)}")
                return pd.DataFrame()
        
        return self._safe_query(query)
    
    def get_post_organization_actions(self, post_organization_id):
        """
        Retorna todas as ações de uma pós-organização.
        
        Args:
            post_organization_id: ID da pós-organização
            
        Returns:
            DataFrame com as ações
        """
        def query():
            try:
                actions = self.session.query(PostOrganizationAction).filter(
                    PostOrganizationAction.post_organization_id == post_organization_id
                ).order_by(PostOrganizationAction.due_date).all()
                
                df_data = []
                for a in actions:
                    df_data.append({
                        'id': a.id,
                        'post_organization_id': a.post_organization_id,
                        'action_type': a.action_type,
                        'due_date': a.due_date,
                        'status': a.status,
                        'notes': a.notes,
                        'completed_at': a.completed_at
                    })
                
                return pd.DataFrame(df_data)
                
            except Exception as e:
                print(f"Erro ao buscar ações: {str(e)}")
                return pd.DataFrame()
        
        return self._safe_query(query)
    
    def update_post_organization_action(self, action_id, status, notes=None):
        """
        Atualiza uma ação de pós-organização.
        
        Args:
            action_id: ID da ação
            status: Novo status ('PENDENTE', 'FEITO', 'CANCELADO')
            notes: Observações (opcional)
            
        Returns:
            dict com informações da ação atualizada ou None se erro
        """
        def query():
            try:
                action = self.session.query(PostOrganizationAction).filter(
                    PostOrganizationAction.id == action_id
                ).first()
                
                if not action:
                    return None
                
                action.status = status
                if notes is not None:
                    action.notes = notes
                
                if status == 'FEITO':
                    action.completed_at = datetime.now()
                
                self.session.commit()
                
                # Verificar conclusão automática
                self._check_post_organization_completion(action.post_organization_id)
                
                return {
                    'id': action.id,
                    'action_type': action.action_type,
                    'status': action.status,
                    'post_organization_id': action.post_organization_id
                }
                
            except Exception as e:
                self.session.rollback()
                print(f"Erro ao atualizar ação: {str(e)}")
                raise e
        
        return self._safe_query(query)
    
    def _check_post_organization_completion(self, post_organization_id):
        """
        Verifica se todas as ações obrigatórias estão concluídas e marca a pós-organização como CONCLUIDO.
        Ações obrigatórias: agradecimento, acompanhamento, ajuste_fino, feedback, continuidade
        """
        try:
            acoes_obrigatorias = ['agradecimento', 'acompanhamento', 'ajuste_fino', 'feedback', 'continuidade']

            acoes = self.session.query(PostOrganizationAction).filter(
                PostOrganizationAction.post_organization_id == post_organization_id,
                PostOrganizationAction.action_type.in_(acoes_obrigatorias)
            ).all()

            todas_feitas = all(a.status == 'FEITO' for a in acoes)

            if todas_feitas and len(acoes) > 0:
                post_org = self.session.query(PostOrganization).filter(
                    PostOrganization.id == post_organization_id
                ).first()

                if post_org:
                    post_org.status = 'CONCLUIDO'
                    self.session.commit()
                    print(f"Pós-organização {post_organization_id} marcada como CONCLUIDA")

        except Exception as e:
            print(f"Erro ao verificar conclusão: {str(e)}")
    
    def add_retorno_tecnico_action(self, post_organization_id, due_date):
        """
        Adiciona uma ação de RETORNO_TECNICO manualmente.
        Chamado quando o usuário marca FOLLOW_UP como FEITO e indica necessidade de retorno.
        
        Args:
            post_organization_id: ID da pós-organização
            due_date: Data prevista para o retorno (entre 15 e 30 dias)
            
        Returns:
            int: ID da ação criada ou None se erro
        """
        def query():
            try:
                action = PostOrganizationAction(
                    post_organization_id=post_organization_id,
                    action_type='retorno_tecnico',
                    due_date=due_date,
                    status='PENDENTE',
                    usuario_id=self.usuario_id
                )
                self.session.add(action)
                self.session.commit()
                
                return action.id
                
            except Exception as e:
                self.session.rollback()
                print(f"Erro ao criar retorno técnico: {str(e)}")
                raise e
        
        return self._safe_query(query)
    
    def get_pending_post_actions_for_dashboard(self):
        """
        Retorna ações pendentes para exibição no Dashboard.
        Filtro: status=PENDENTE, ações de acompanhamento (Agradecimento, Manutenção, Follow-up)
        Mostra ações vencidas e próximas (até 3 dias)
        
        Returns:
            DataFrame com ações pendentes para alerta
        """
        def query():
            try:
                from datetime import timedelta
                hoje = datetime.now().date()
                limite = hoje + timedelta(days=3)
                
                actions = self.session.query(PostOrganizationAction).join(
                    PostOrganization
                ).filter(
                    PostOrganization.usuario_id == self.usuario_id,
                    PostOrganizationAction.status == 'PENDENTE',
                    PostOrganizationAction.due_date <= limite,
                    PostOrganizationAction.action_type.in_(['agradecimento', 'acompanhamento', 'ajuste_fino', 'feedback', 'continuidade', 'retorno_tecnico'])
                ).order_by(PostOrganizationAction.due_date).all()
                
                df_data = []
                for a in actions:
                    post_org = self.session.query(PostOrganization).filter(
                        PostOrganization.id == a.post_organization_id
                    ).first()
                    
                    cliente = self.session.query(Cliente).filter(
                        Cliente.id == post_org.cliente_id
                    ).first() if post_org else None
                    
                    proposta = self.session.query(Proposta).filter(
                        Proposta.id == post_org.proposta_id
                    ).first() if post_org else None
                    
                    df_data.append({
                        'action_id': a.id,
                        'action_type': a.action_type,
                        'due_date': a.due_date,
                        'cliente_nome': cliente.nome if cliente else 'N/A',
                        'proposta_numero': proposta.numero if proposta else 'N/A',
                        'post_organization_id': a.post_organization_id
                    })
                
                return pd.DataFrame(df_data)
                
            except Exception as e:
                print(f"Erro ao buscar ações pendentes: {str(e)}")
                return pd.DataFrame()

        return self._safe_query(query)

    def get_post_org_templates(self):
        """
        Retorna todos os templates de mensagem de pós-organização.

        Returns:
            dict: {etapa: {nome, dias_apos, emoji, texto}} ou {} se erro
        """
        def query():
            try:
                templates = self.session.query(PostOrgTemplate).order_by(PostOrgTemplate.dias_apos).all()
                return {t.etapa: {'nome': t.nome, 'dias_apos': t.dias_apos, 'emoji': t.emoji or '', 'texto': t.texto} for t in templates}
            except Exception as e:
                print(f"Erro ao buscar templates: {str(e)}")
                return {}

        return self._safe_query(query) or {}
    
    def invalidar_cache(self):
        """
        Invalida o cache de clientes, propostas e financeiro para o usuário atual.
        Deve ser chamado quando dados são criados ou modificados.
        """
        for key in ["cache_clientes", "cache_propostas", "cache_financeiro"]:
            full_key = f"{key}_{self.usuario_id}"
            remove_cache(full_key)