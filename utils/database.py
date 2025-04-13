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

# Ensure proper SSL configuration for PostgreSQL
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            'sslmode': 'require',
            'connect_timeout': 10
        } if 'postgresql' in DATABASE_URL else {},
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_timeout=30,
        max_overflow=10,
        pool_size=5
    )
except Exception as e:
    print(f"Error creating database engine: {str(e)}")
    raise

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
    telefone = Column(String)  # Novo campo
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
    status_pagamento_base = Column(String, default='Pendente')
    previsao_dias = Column(Integer)  # Dias previstos para execução
    data_inicio_execucao = Column(Date)  # Data de início efetivo da execução
    status_execucao = Column(String, default='Não iniciada')  # Status da execução: 'Não iniciada', 'Em execução', 'Concluída'

    cliente = relationship("Cliente", back_populates="propostas")
    produtos = relationship("ProdutoOrganizador", back_populates="proposta", cascade="all, delete-orphan")
    acrescimos = relationship("AcrescimoProposta", back_populates="proposta", cascade="all, delete-orphan")
    vendas = relationship("Venda", back_populates="proposta") # Relacionamento com vendas

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
    subcategoria = Column(String)  # Nova subcategoria para classificação mais detalhada
    tipo_receita = Column(String)
    origem_id = Column(Integer)
    origem_tipo = Column(String)
    tipo_conta = Column(String, default='PF')
    status = Column(String, default='Pendente')  # 'Pendente', 'Recebido', 'Cancelado'
    data_recebimento = Column(Date, nullable=True)
    proposta_id = Column(Integer, ForeignKey('propostas.id'), nullable=True)  # Referência direta à proposta
    classificacao = Column(String)  # 'receita', 'custo_direto', 'despesa_operacional'
    
    # Relacionamento com proposta
    proposta = relationship("Proposta")

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
    
    # Relacionamento com vendas
    vendas_itens = relationship("ItemVenda", back_populates="produto", cascade="all, delete-orphan")

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
    
    # Relacionamentos
    cliente = relationship("Cliente")
    proposta = relationship("Proposta", back_populates="vendas")  # Relacionamento com proposta
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")

class ItemVenda(Base):
    __tablename__ = 'itens_venda'
    id = Column(Integer, primary_key=True)
    venda_id = Column(Integer, ForeignKey('vendas.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relacionamentos
    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto", back_populates="vendas_itens")

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

            # Se o resultado for um DataFrame, converter tipos numéricos
            if isinstance(result, pd.DataFrame):
                # Converter colunas numéricas para tipos nativos Python
                for col in result.select_dtypes(include=['int64', 'float64', 'Int64']).columns:
                    result[col] = result[col].astype(object).where(pd.notnull(result[col]), None)

            # Se o resultado for um número, garantir que seja tipo nativo Python
            elif isinstance(result, (np.int64, np.float64)):
                result = result.item()

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
                'estado': c.estado,
                'cidade': c.cidade,
                'bairro': c.bairro,
                'endereco': c.endereco,
                'cpf': c.cpf,
                'data_aniversario': c.data_aniversario,
                'origem_cliente': c.origem_cliente,
                'data_cadastro': c.data_cadastro,
                'observacoes': c.observacoes # Added observations to get_clientes
            } for c in clientes])
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
                observacoes=observacoes
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
                observacoes=observacoes
            )
            self.session.add(cliente)
            return cliente.id
        return self._safe_query(query)

    def get_propostas(self):
        def query():
            propostas = self.session.query(Proposta).all()
            return pd.DataFrame([{
                'id': int(p.id),  # Converter para int nativo
                'numero': int(p.numero),  # Converter para int nativo
                'cliente_id': int(p.cliente_id) if p.cliente_id else None,  # Converter para int nativo
                'descricao': p.descricao,
                'valor': float(p.valor) if p.valor is not None else None,  # Converter para float nativo
                'status': p.status,
                'tipo_proposta': p.tipo_proposta,
                'data_inicio': p.data_inicio,
                'data_fim': p.data_fim,
                'prazo_entrega': p.prazo_entrega,
                'data_proposta': p.data_proposta,
                'status_pagamento_base': p.status_pagamento_base,
                'previsao_dias': p.previsao_dias,
                'data_inicio_execucao': p.data_inicio_execucao,
                'status_execucao': p.status_execucao
            } for p in propostas])
        return self._safe_query(query)

    def add_proposta(self, cliente_id, descricao, valor, status, tipo_proposta=None, 
                    data_inicio=None, data_fim=None, prazo_entrega=None):
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
            # Gerar próximo número de proposta
            ultimo_numero = self.session.query(func.max(Proposta.numero)).scalar()
            proximo_numero = 1 if ultimo_numero is None else int(ultimo_numero) + 1

            # Criar dicionário com valores para a proposta
            proposta_data = {
                'numero': proximo_numero,
                'cliente_id': cliente_id_local,
                'descricao': descricao_local,
                'valor': valor_local,
                'status': status_local,
            }
            
            # Adicionar valores opcionais apenas se não forem None
            if tipo_proposta_local is not None:
                proposta_data['tipo_proposta'] = tipo_proposta_local
            if data_inicio_local is not None:
                proposta_data['data_inicio'] = data_inicio_local
            if data_fim_local is not None:
                proposta_data['data_fim'] = data_fim_local
            if prazo_entrega_local is not None:
                proposta_data['prazo_entrega'] = prazo_entrega_local
                
            # Criar a proposta com os valores filtrados
            proposta = Proposta(**proposta_data)
            self.session.add(proposta)
            
            # Garantir que temos um ID válido
            self.session.flush()
            return int(proposta.id) if proposta.id is not None else 0
        
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
                'subcategoria': t.subcategoria,
                'tipo_receita': t.tipo_receita,
                'origem_id': t.origem_id,
                'origem_tipo': t.origem_tipo,
                'tipo_conta': t.tipo_conta,
                'status': t.status,
                'data_recebimento': t.data_recebimento,
                'proposta_id': t.proposta_id,
                'classificacao': t.classificacao
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

    def update_transacao(self, transacao_id, tipo, descricao, valor, categoria, tipo_receita=None):
        """Atualiza uma transação existente"""
        def query():
            transacao = self.session.query(Transacao).filter_by(id=transacao_id).first()
            if transacao:
                transacao.tipo = tipo
                transacao.descricao = descricao
                transacao.valor = valor
                transacao.categoria = categoria
                transacao.tipo_receita = tipo_receita
                return True
            return False
        return self._safe_query(query)

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
            contas = self.session.query(Transacao).filter(
                Transacao.tipo.in_(['receita_a_receber']),
            ).order_by(Transacao.data.desc()).all()

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
            assistentes = self.session.query(Assistente).all()
            return pd.DataFrame([{
                'id': a.id,
                'nome': a.nome,
                'telefone': a.telefone,
                'endereco': a.endereco,
                'pix': a.pix,
                'observacoes': a.observacoes
            } for a in assistentes])
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
            parceiros = self.session.query(Parceiro).all()
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
                          data_proposta=None, previsao_dias=None):
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
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
        """
        def query():
            try:
                # Converter proposta_id para inteiro
                proposta_id_int = int(proposta_id)
                
                # Buscar a proposta
                proposta = self.session.query(Proposta).filter_by(id=proposta_id_int).first()
                if not proposta:
                    return False
                
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
                
                if data_fim is not None:
                    proposta.data_fim = data_fim
                
                if prazo_entrega is not None:
                    proposta.prazo_entrega = prazo_entrega
                
                if data_proposta is not None:
                    proposta.data_proposta = data_proposta
                
                if previsao_dias is not None:
                    proposta.previsao_dias = previsao_dias
                
                return True
            except Exception as e:
                raise Exception(f"Erro ao atualizar proposta: {str(e)}")
        
        return self._safe_query(query)

    def add_acrescimo_proposta(self, proposta_id, tipo, valor, descricao=None, fornecedor=None, status_pagamento='Pendente'):
        def query():
            # Converter proposta_id e valor para tipos nativos Python
            proposta_id = int(proposta_id)
            valor = float(valor) if valor is not None else None

            acrescimo = AcrescimoProposta(
                proposta_id=proposta_id,
                tipo=tipo,
                fornecedor=fornecedor,
                descricao=descricao,
                valor=valor,
                status_pagamento=status_pagamento
            )
            self.session.add(acrescimo)
            return int(acrescimo.id)  # Converter para int nativo
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
                self.session.delete(cliente)
                return True
            return False
        return self._safe_query(query)

    def excluir_proposta(self, proposta_id):
        """Exclui uma proposta e seus registros relacionados"""
        def query():
            proposta = self.session.query(Proposta).filter_by(id=proposta_id).first()
            if proposta:
                # Excluir registros relacionados
                self.session.query(AndamentoProposta).filter_by(proposta_id=proposta_id).delete()
                self.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta_id).delete()
                self.session.query(AcrescimoProposta).filter_by(proposta_id=proposta_id).delete()

                # Excluir a proposta
                self.session.delete(proposta)
                return True, "Proposta excluída com sucesso"
            return False, "Proposta não encontrada"
        return self._safe_query(query)

    def atualizar_status_pagamento_acrescimo(self, proposta_id, tipo, status):
        """Atualiza o status de pagamento de um acréscimo"""
        def query():
            acrescimo = self.session.query(AcrescimoProposta).filter_by(
                proposta_id=proposta_id,
                tipo=tipo
            ).first()
            if acrescimo:
                acrescimo.status_pagamento = status
                return True
            return False
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

            # Adicionar acréscimos recebidos
            acrescimos = self.session.query(AcrescimoProposta).filter_by(status_pagamento='Recebido').all()
            for a in acrescimos:
                historico.append({
                    'proposta': a.proposta.numero,
                    'cliente': a.proposta.cliente.nome,
                    'tipo': a.tipo,
                    'valor': a.valor,
                    'data_recebimento': a.data_cadastro
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
                estoque=int(estoque)
            )
            self.session.add(produto)
            return produto.id
        return self._safe_query(query)
        
    def get_produtos(self):
        """Retorna todos os produtos cadastrados"""
        def query():
            produtos = self.session.query(Produto).all()
            return pd.DataFrame([{
                'id': p.id,
                'nome': p.nome,
                'descricao': p.descricao,
                'preco_custo': p.preco_custo,
                'preco_venda': p.preco_venda,
                'categoria': p.categoria,
                'estoque': p.estoque,
                'data_cadastro': p.data_cadastro
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
                observacoes=observacoes
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
        """Retorna todas as vendas realizadas"""
        def query():
            vendas = self.session.query(Venda).order_by(Venda.data_venda.desc()).all()
            return pd.DataFrame([{
                'id': v.id,
                'cliente_nome': v.cliente.nome if v.cliente else "Cliente não encontrado",
                'valor_total': v.valor_total,
                'data_venda': v.data_venda,
                'status': v.status,
                'forma_pagamento': v.forma_pagamento,
                'observacoes': v.observacoes
            } for v in vendas])
        return self._safe_query(query)
        
    def get_itens_venda(self, venda_id):
        """Retorna os itens de uma venda específica"""
        def query():
            itens = self.session.query(ItemVenda).filter_by(venda_id=venda_id).all()
            return pd.DataFrame([{
                'id': i.id,
                'produto_nome': i.produto.nome if i.produto else "Produto não encontrado",
                'quantidade': i.quantidade,
                'preco_unitario': i.preco_unitario,
                'subtotal': i.subtotal
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