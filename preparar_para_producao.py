"""
Script para preparar o ambiente para produção e integração com Stripe
Este script:
1. Cria um diretório "producao" com uma cópia limpa dos arquivos necessários
2. Remove ferramentas de desenvolvimento e códigos de depuração
3. Prepara o banco de dados para produção 
4. Configura a integração com Stripe
"""
import os
import shutil
import logging
import json
import psycopg2
import sys
from datetime import datetime
import streamlit as st

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PreparadorProducao:
    def __init__(self):
        """Inicializa a classe de preparação para produção"""
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            logger.error("DATABASE_URL não encontrada no ambiente")
            sys.exit(1)
            
        # Diretório base para a versão de produção
        self.diretorio_producao = "producao"
        self.diretorio_backup = "backup_pre_producao_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Arquivos e diretórios essenciais para produção
        self.arquivos_essenciais = [
            'app.py',
            'Procfile',
            'requirements.txt',
            '.streamlit/config.toml',
            'utils',
            'pages',
            'templates',
            'static',
            'assets'
        ]
        
        # Arquivos e diretórios que devem ser excluídos da versão de produção
        self.arquivos_para_excluir = [
            'diagnostico_banco.py',
            'correcao_banco.py',
            'teste_importacao.py',
            'importacao_propostas_debug.py',
            'limpar_lancamentos_automaticos.py',
            'download_fix_proposta.py',
            'excluir_venda_direto.py',
            'excluir_venda_simples.py',
            'excluir_vendas_standalone.py',
            'fix_duplicated_financial_entries.py',
            'fix_duplicate_proposal_entries.py',
            'fix_proposta_render.py',
            'importacao_propostas_simplificada.py',
            'download_fix_render_db.py',
            'download_fix_render_console.py',
            'download_fix_render_final.py',
            'check_database.py',
            'check_port.py',
            'disable_debug.py',
            'limpar_clientes.py',
            'limpar_propostas.py',
            'limpar_vendas.py',
            'download_fix_direto.py',
            'download_fix_direct.py',
            'download_solucao_render.py',
            'download_solucao_final.py',
            'download_alteracoes.py',
            'utils/debug_tools.py',
            'utils/test_utils.py',
            'utils/dev_config.py'
        ]
        
        # Configuração do Stripe
        self.planos_stripe = [
            {
                'id': 'plano_basico',
                'nome': 'Plano Básico',
                'preco_mensal': 29.90,
                'preco_anual': 299.00,
                'recursos': [
                    'Gerenciamento de clientes',
                    'Propostas básicas',
                    'Relatórios essenciais'
                ]
            },
            {
                'id': 'plano_profissional',
                'nome': 'Plano Profissional',
                'preco_mensal': 59.90,
                'preco_anual': 599.00,
                'recursos': [
                    'Tudo do Plano Básico',
                    'Propostas avançadas',
                    'Dashboard financeiro',
                    'Modelos personalizados'
                ]
            },
            {
                'id': 'plano_empresa',
                'nome': 'Plano Empresa',
                'preco_mensal': 99.90,
                'preco_anual': 999.00,
                'recursos': [
                    'Tudo do Plano Profissional',
                    'Relatórios avançados',
                    'Integração com outras ferramentas',
                    'Suporte prioritário'
                ]
            }
        ]

    def conectar_bd(self):
        """Estabelece conexão com o banco de dados"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def fazer_backup_completo(self):
        """Cria um backup completo do projeto e banco de dados antes de qualquer alteração"""
        try:
            # Criar diretório de backup
            os.makedirs(self.diretorio_backup, exist_ok=True)
            logger.info(f"Diretório de backup criado: {self.diretorio_backup}")
            
            # Backup de arquivos importantes
            for item in self.arquivos_essenciais:
                if os.path.exists(item):
                    destino = os.path.join(self.diretorio_backup, item)
                    # Criar diretório pai se necessário
                    os.makedirs(os.path.dirname(destino), exist_ok=True)
                    
                    if os.path.isdir(item):
                        shutil.copytree(item, destino, dirs_exist_ok=True)
                        logger.info(f"Backup do diretório {item} criado")
                    else:
                        shutil.copy2(item, destino)
                        logger.info(f"Backup do arquivo {item} criado")
            
            # Backup do banco de dados
            self.backup_banco_dados()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao criar backup completo: {e}")
            return False

    def backup_banco_dados(self):
        """Cria um backup do banco de dados"""
        conn = self.conectar_bd()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Obter lista de tabelas
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tabelas = [tabela[0] for tabela in cursor.fetchall()]
            
            # Criar diretório para backup de dados
            diretorio_backup_db = os.path.join(self.diretorio_backup, "banco_dados")
            os.makedirs(diretorio_backup_db, exist_ok=True)
            
            # Exportar dados de cada tabela
            for tabela in tabelas:
                try:
                    cursor.execute(f"SELECT * FROM {tabela}")
                    colunas = [desc[0] for desc in cursor.description]
                    dados = cursor.fetchall()
                    
                    # Converter para lista de dicionários
                    registros = []
                    for dado in dados:
                        registro = {}
                        for i, coluna in enumerate(colunas):
                            valor = dado[i]
                            # Converter tipos que não são serializáveis para JSON
                            if isinstance(valor, datetime):
                                valor = valor.isoformat()
                            registro[coluna] = valor
                        registros.append(registro)
                    
                    # Salvar no arquivo
                    with open(os.path.join(diretorio_backup_db, f"{tabela}.json"), 'w') as f:
                        json.dump(registros, f, indent=2, default=str)
                        
                    logger.info(f"Backup da tabela {tabela} com {len(registros)} registros criado")
                except Exception as e:
                    logger.error(f"Erro ao fazer backup da tabela {tabela}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao fazer backup do banco de dados: {e}")
            return False
        finally:
            if conn:
                if 'cursor' in locals():
                    cursor.close()
                conn.close()

    def limpar_dados_teste(self):
        """Remove dados de teste do banco de dados"""
        conn = self.conectar_bd()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # 1. Remover usuários de teste/desenvolvimento
            cursor.execute("""
                DELETE FROM usuarios_firebase 
                WHERE email LIKE '%test%' 
                   OR email LIKE '%exemplo%'
                   OR email LIKE '%example%'
                   OR email = 'dev@plannerorganizer.com.br'
            """)
            usuarios_removidos = cursor.rowcount
            logger.info(f"Removidos {usuarios_removidos} usuários de teste")
            
            # 2. Remover perfis de teste/desenvolvimento
            cursor.execute("""
                DELETE FROM perfis 
                WHERE email LIKE '%test%' 
                   OR email LIKE '%exemplo%'
                   OR email LIKE '%example%'
                   OR email = 'dev@plannerorganizer.com.br'
                   OR nome LIKE '%Teste%'
                   OR nome LIKE '%Test%'
            """)
            perfis_removidos = cursor.rowcount
            logger.info(f"Removidos {perfis_removidos} perfis de teste")
            
            # 3. Remover clientes de teste
            cursor.execute("""
                DELETE FROM clientes 
                WHERE nome LIKE '%Teste%' 
                   OR nome LIKE '%Test%'
                   OR email LIKE '%test%' 
                   OR email LIKE '%exemplo%'
                   OR email LIKE '%example%'
            """)
            clientes_removidos = cursor.rowcount
            logger.info(f"Removidos {clientes_removidos} clientes de teste")
            
            # 4. Remover propostas de teste
            cursor.execute("""
                DELETE FROM propostas
                WHERE descricao LIKE '%Teste%'
                   OR descricao LIKE '%Test%'
                   OR cliente_nome LIKE '%Teste%'
                   OR cliente_nome LIKE '%Test%'
            """)
            propostas_removidas = cursor.rowcount
            logger.info(f"Removidas {propostas_removidas} propostas de teste")
            
            # 5. Remover lançamentos financeiros de teste
            cursor.execute("""
                DELETE FROM financeiro
                WHERE descricao LIKE '%Teste%'
                   OR descricao LIKE '%Test%'
            """)
            lancamentos_removidos = cursor.rowcount
            logger.info(f"Removidos {lancamentos_removidos} lançamentos financeiros de teste")
            
            # 6. Remover vendas de teste
            cursor.execute("""
                DELETE FROM vendas
                WHERE descricao LIKE '%Teste%'
                   OR descricao LIKE '%Test%'
                   OR cliente_nome LIKE '%Teste%'
                   OR cliente_nome LIKE '%Test%'
            """)
            vendas_removidas = cursor.rowcount
            logger.info(f"Removidas {vendas_removidas} vendas de teste")
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao limpar dados de teste: {e}")
            return False
        finally:
            if conn:
                if 'cursor' in locals():
                    cursor.close()
                conn.close()

    def criar_estrutura_stripe(self):
        """Cria estrutura necessária para integração com Stripe"""
        conn = self.conectar_bd()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Verificar se a tabela planos existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'planos'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                # Criar tabela para planos de assinatura
                cursor.execute("""
                    CREATE TABLE planos (
                        id SERIAL PRIMARY KEY,
                        codigo VARCHAR NOT NULL UNIQUE,
                        nome VARCHAR NOT NULL,
                        descricao TEXT,
                        preco_mensal DECIMAL(10,2),
                        preco_anual DECIMAL(10,2),
                        stripe_price_id_mensal VARCHAR,
                        stripe_price_id_anual VARCHAR,
                        ativo BOOLEAN DEFAULT TRUE,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("Tabela planos criada com sucesso")
                
                # Inserir planos padrão
                for plano in self.planos_stripe:
                    cursor.execute("""
                        INSERT INTO planos (codigo, nome, descricao, preco_mensal, preco_anual)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        plano['id'],
                        plano['nome'],
                        json.dumps(plano['recursos']),
                        plano['preco_mensal'],
                        plano['preco_anual']
                    ))
                logger.info(f"Inseridos {len(self.planos_stripe)} planos padrão")
            else:
                logger.info("Tabela planos já existe")
            
            # Verificar se a tabela assinaturas existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'assinaturas'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                # Criar tabela para assinaturas de usuários
                cursor.execute("""
                    CREATE TABLE assinaturas (
                        id SERIAL PRIMARY KEY,
                        usuario_id VARCHAR NOT NULL,
                        plano_id INTEGER REFERENCES planos(id),
                        stripe_customer_id VARCHAR,
                        stripe_subscription_id VARCHAR,
                        status VARCHAR NOT NULL,
                        periodo VARCHAR NOT NULL,
                        data_inicio TIMESTAMP,
                        data_fim TIMESTAMP,
                        data_proxima_cobranca TIMESTAMP,
                        cancelada BOOLEAN DEFAULT FALSE,
                        motivo_cancelamento TEXT,
                        metodo_pagamento VARCHAR,
                        ultimos_digitos VARCHAR(4),
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT unique_usuario_assinatura UNIQUE(usuario_id)
                    );
                """)
                logger.info("Tabela assinaturas criada com sucesso")
            else:
                logger.info("Tabela assinaturas já existe")
                
            # Verificar se a tabela transacoes existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'transacoes'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                # Criar tabela para transações financeiras
                cursor.execute("""
                    CREATE TABLE transacoes (
                        id SERIAL PRIMARY KEY,
                        usuario_id VARCHAR NOT NULL,
                        assinatura_id INTEGER REFERENCES assinaturas(id),
                        stripe_payment_id VARCHAR,
                        stripe_invoice_id VARCHAR,
                        tipo VARCHAR NOT NULL,
                        valor DECIMAL(10, 2) NOT NULL,
                        moeda VARCHAR DEFAULT 'BRL',
                        status VARCHAR NOT NULL,
                        data_transacao TIMESTAMP,
                        descricao VARCHAR,
                        metadados JSONB,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("Tabela transacoes criada com sucesso")
            else:
                logger.info("Tabela transacoes já existe")
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao criar estrutura para Stripe: {e}")
            return False
        finally:
            if conn:
                if 'cursor' in locals():
                    cursor.close()
                conn.close()

    def criar_versao_producao(self):
        """Cria uma versão limpa do projeto para produção"""
        try:
            # Limpar diretório de produção se já existir
            if os.path.exists(self.diretorio_producao):
                shutil.rmtree(self.diretorio_producao)
            
            # Criar diretório de produção
            os.makedirs(self.diretorio_producao, exist_ok=True)
            logger.info(f"Diretório de produção criado: {self.diretorio_producao}")
            
            # Copiar arquivos essenciais
            for item in self.arquivos_essenciais:
                if os.path.exists(item):
                    destino = os.path.join(self.diretorio_producao, item)
                    # Criar diretório pai se necessário
                    os.makedirs(os.path.dirname(destino), exist_ok=True)
                    
                    if os.path.isdir(item):
                        shutil.copytree(item, destino, dirs_exist_ok=True)
                        logger.info(f"Diretório {item} copiado para versão de produção")
                    else:
                        shutil.copy2(item, destino)
                        logger.info(f"Arquivo {item} copiado para versão de produção")
            
            # Remover arquivos desnecessários
            for item in self.arquivos_para_excluir:
                caminho_completo = os.path.join(self.diretorio_producao, item)
                if os.path.exists(caminho_completo):
                    if os.path.isdir(caminho_completo):
                        shutil.rmtree(caminho_completo)
                    else:
                        os.remove(caminho_completo)
                    logger.info(f"Arquivo/diretório removido da versão de produção: {item}")
            
            # Desativar modo desenvolvedor nos arquivos
            self.desativar_modo_desenvolvedor()
            
            # Criar arquivo para integração com Stripe
            self.criar_arquivo_stripe_integracao()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao criar versão de produção: {e}")
            return False

    def desativar_modo_desenvolvedor(self):
        """Desativa configurações específicas de modo desenvolvedor nos arquivos da versão de produção"""
        try:
            # Arquivos que podem conter flags de desenvolvimento
            arquivos_configuracao = [
                'app.py',
                'utils/config.py',
                'utils/database.py',
                'utils/auth.py',
                'utils/firebase_auth.py'
            ]
            
            for arquivo in arquivos_configuracao:
                arquivo_completo = os.path.join(self.diretorio_producao, arquivo)
                if os.path.exists(arquivo_completo):
                    # Ler conteúdo do arquivo
                    with open(arquivo_completo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    # Desativar flags de desenvolvimento
                    conteudo_modificado = conteudo.replace('DEBUG = True', 'DEBUG = False')
                    conteudo_modificado = conteudo_modificado.replace('DESENVOLVIMENTO = True', 'DESENVOLVIMENTO = False')
                    conteudo_modificado = conteudo_modificado.replace('modo_teste = True', 'modo_teste = False')
                    conteudo_modificado = conteudo_modificado.replace('modo_dev = True', 'modo_dev = False')
                    conteudo_modificado = conteudo_modificado.replace('dev_mode = True', 'dev_mode = False')
                    
                    # Salvar mudanças
                    if conteudo != conteudo_modificado:
                        with open(arquivo_completo, 'w', encoding='utf-8') as f:
                            f.write(conteudo_modificado)
                        logger.info(f"Flags de desenvolvimento desativadas em {arquivo}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao desativar modo desenvolvedor: {e}")
            return False

    def criar_arquivo_stripe_integracao(self):
        """Cria o arquivo para integração com o Stripe"""
        try:
            caminho_stripe = os.path.join(self.diretorio_producao, 'utils', 'stripe_integration.py')
            
            conteudo = """\"\"\"
Módulo de integração com Stripe para processamento de pagamentos e assinaturas
\"\"\"
import os
import logging
import stripe
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configuração do Stripe
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Inicializar Stripe
stripe.api_key = STRIPE_SECRET_KEY

class StripeIntegration:
    @staticmethod
    def criar_cliente(email, nome, metadata=None):
        \"\"\"Cria um cliente no Stripe\"\"\"
        try:
            cliente = stripe.Customer.create(
                email=email,
                name=nome,
                metadata=metadata or {}
            )
            return cliente.id
        except Exception as e:
            logger.error(f"Erro ao criar cliente no Stripe: {e}")
            return None
    
    @staticmethod
    def criar_assinatura(customer_id, price_id, metadata=None):
        \"\"\"Cria uma assinatura para o cliente\"\"\"
        try:
            assinatura = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {}
            )
            return assinatura
        except Exception as e:
            logger.error(f"Erro ao criar assinatura no Stripe: {e}")
            return None
    
    @staticmethod
    def cancelar_assinatura(subscription_id):
        \"\"\"Cancela uma assinatura existente\"\"\"
        try:
            return stripe.Subscription.delete(subscription_id)
        except Exception as e:
            logger.error(f"Erro ao cancelar assinatura no Stripe: {e}")
            return None
    
    @staticmethod
    def atualizar_assinatura(subscription_id, price_id):
        \"\"\"Atualiza uma assinatura para um novo plano\"\"\"
        try:
            # Obter a assinatura atual
            assinatura = stripe.Subscription.retrieve(subscription_id)
            
            # Obter o ID do item da assinatura (geralmente há apenas um)
            item_id = assinatura['items']['data'][0].id
            
            # Atualizar a assinatura
            assinatura_atualizada = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': item_id,
                    'price': price_id,
                }]
            )
            return assinatura_atualizada
        except Exception as e:
            logger.error(f"Erro ao atualizar assinatura no Stripe: {e}")
            return None
    
    @staticmethod
    def obter_detalhes_assinatura(subscription_id):
        \"\"\"Obtém detalhes de uma assinatura\"\"\"
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except Exception as e:
            logger.error(f"Erro ao obter detalhes da assinatura: {e}")
            return None
    
    @staticmethod
    def criar_session_checkout(customer_id, price_id, success_url, cancel_url, metadata=None):
        \"\"\"Cria uma sessão de checkout para pagamento\"\"\"
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            return checkout_session
        except Exception as e:
            logger.error(f"Erro ao criar sessão de checkout: {e}")
            return None
    
    @staticmethod
    def processar_webhook(payload, sig_header):
        \"\"\"Processa eventos recebidos via webhook do Stripe\"\"\"
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            
            # Aqui você pode implementar a lógica para cada tipo de evento
            # Por exemplo:
            if event['type'] == 'checkout.session.completed':
                # Processar pagamento concluído
                session = event['data']['object']
                customer_id = session.get('customer')
                subscription_id = session.get('subscription')
                # Atualizar banco de dados com informações da assinatura
                
            elif event['type'] == 'invoice.paid':
                # Processar fatura paga
                invoice = event['data']['object']
                # Registrar pagamento no banco de dados
                
            elif event['type'] == 'customer.subscription.updated':
                # Processar atualização de assinatura
                subscription = event['data']['object']
                # Atualizar status da assinatura no banco de dados
                
            elif event['type'] == 'customer.subscription.deleted':
                # Processar cancelamento de assinatura
                subscription = event['data']['object']
                # Atualizar status da assinatura no banco de dados
            
            return True, event
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return False, str(e)
"""
            
            # Criar diretório pai se necessário
            os.makedirs(os.path.dirname(caminho_stripe), exist_ok=True)
            
            # Salvar arquivo
            with open(caminho_stripe, 'w', encoding='utf-8') as f:
                f.write(conteudo)
                
            logger.info(f"Arquivo de integração com Stripe criado: {caminho_stripe}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar arquivo de integração com Stripe: {e}")
            return False
    
    def criar_zip_producao(self):
        """Cria um arquivo ZIP da versão de produção"""
        try:
            nome_zip = f"producao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            shutil.make_archive(nome_zip.replace('.zip', ''), 'zip', self.diretorio_producao)
            
            logger.info(f"Arquivo ZIP da versão de produção criado: {nome_zip}")
            return nome_zip
        except Exception as e:
            logger.error(f"Erro ao criar arquivo ZIP: {e}")
            return None
    
    def executar_preparacao_completa(self):
        """Executa o processo completo de preparação para produção"""
        logger.info("Iniciando processo de preparação para produção...")
        
        # 1. Criar backup completo
        if not self.fazer_backup_completo():
            logger.error("Falha ao criar backup completo. Abortando processo.")
            return False, "Falha ao criar backup"
        
        # 2. Limpar dados de teste do banco
        if not self.limpar_dados_teste():
            logger.warning("Falha ao limpar dados de teste. Continuando com outras etapas...")
        
        # 3. Criar estrutura para Stripe
        if not self.criar_estrutura_stripe():
            logger.warning("Falha ao criar estrutura para Stripe. Continuando com outras etapas...")
        
        # 4. Criar versão limpa para produção
        if not self.criar_versao_producao():
            logger.error("Falha ao criar versão de produção. Abortando processo.")
            return False, "Falha ao criar versão de produção"
        
        # 5. Criar arquivo ZIP para implantação
        zip_file = self.criar_zip_producao()
        if not zip_file:
            logger.error("Falha ao criar arquivo ZIP. Abortando processo.")
            return False, "Falha ao criar arquivo ZIP"
        
        logger.info("Processo de preparação para produção concluído com sucesso!")
        return True, zip_file


# Interface Streamlit
def main():
    st.set_page_config(
        page_title="Preparação para Produção",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Preparação para Produção e Integração Stripe")
    
    st.markdown("""
    Este assistente irá preparar o sistema para produção e integração com o Stripe.
    
    ### O que será feito:
    
    1. **Backup completo** - Será criado um backup de segurança de todos os dados e arquivos
    2. **Limpeza do banco de dados** - Dados de teste serão removidos
    3. **Criação da estrutura para Stripe** - Tabelas necessárias para integração serão criadas
    4. **Versão limpa para produção** - Uma cópia do projeto sem ferramentas de desenvolvimento
    5. **Arquivo ZIP para implantação** - Um arquivo compactado pronto para ser implantado
    
    ⚠️ **ATENÇÃO:** Este processo não pode ser desfeito automaticamente.
    """)
    
    preparador = PreparadorProducao()
    
    if st.button("Iniciar Preparação para Produção", type="primary"):
        with st.spinner("Preparando ambiente para produção..."):
            progresso = st.progress(0)
            
            # 1. Criar backup
            st.write("📦 Criando backup de segurança...")
            sucesso_backup = preparador.fazer_backup_completo()
            progresso.progress(20)
            
            if not sucesso_backup:
                st.error("❌ Falha ao criar backup. Processo interrompido.")
                return
            
            # 2. Limpar dados de teste
            st.write("🧹 Limpando dados de teste do banco de dados...")
            sucesso_limpeza = preparador.limpar_dados_teste()
            progresso.progress(40)
            
            if not sucesso_limpeza:
                st.warning("⚠️ Encontramos problemas ao limpar dados de teste, mas continuaremos o processo.")
            
            # 3. Criar estrutura para Stripe
            st.write("💳 Criando estrutura para integração com Stripe...")
            sucesso_stripe = preparador.criar_estrutura_stripe()
            progresso.progress(60)
            
            if not sucesso_stripe:
                st.warning("⚠️ Encontramos problemas ao criar estrutura para Stripe, mas continuaremos o processo.")
            
            # 4. Criar versão de produção
            st.write("🏭 Criando versão limpa para produção...")
            sucesso_producao = preparador.criar_versao_producao()
            progresso.progress(80)
            
            if not sucesso_producao:
                st.error("❌ Falha ao criar versão de produção. Processo interrompido.")
                return
            
            # 5. Criar ZIP
            st.write("📁 Criando arquivo ZIP para implantação...")
            zip_file = preparador.criar_zip_producao()
            progresso.progress(100)
            
            if not zip_file:
                st.error("❌ Falha ao criar arquivo ZIP. Processo interrompido.")
                return
            
            # Sucesso!
            st.success(f"✅ Preparação para produção concluída com sucesso!")
            st.info(f"📁 Backup criado em: {preparador.diretorio_backup}")
            st.info(f"📁 Versão de produção criada em: {preparador.diretorio_producao}")
            
            # Disponibilizar ZIP para download
            with open(zip_file, "rb") as file:
                st.download_button(
                    label="📥 Baixar versão de produção (ZIP)",
                    data=file,
                    file_name=zip_file,
                    mime="application/zip"
                )
            
            st.markdown("""
            ### Próximos passos:
            
            1. Baixe o arquivo ZIP da versão de produção
            2. Implante a versão de produção no ambiente escolhido (Render, Heroku, etc.)
            3. Configure as seguintes variáveis de ambiente no servidor:
               - `STRIPE_SECRET_KEY` - Chave secreta do Stripe
               - `STRIPE_WEBHOOK_SECRET` - Chave secreta para webhooks do Stripe
            4. Configure os webhooks no dashboard do Stripe apontando para sua aplicação
            """)

if __name__ == "__main__":
    main()