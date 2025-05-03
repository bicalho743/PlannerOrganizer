"""
Script para limpar o ambiente para produção e preparar para integração com Stripe
"""
import os
import psycopg2
import logging
import json
import shutil
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LimpezaProducao:
    def __init__(self):
        """Inicializa a classe de limpeza de produção"""
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            logger.error("DATABASE_URL não encontrada no ambiente")
            sys.exit(1)
            
        self.arquivos_dev_para_remover = [
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
        ]
        
        self.diretorio_backup = "backup_pre_producao_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    def conectar_bd(self):
        """Estabelece conexão com o banco de dados"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def fazer_backup_antes_limpeza(self):
        """Cria backup dos arquivos que serão modificados ou removidos"""
        logger.info(f"Criando diretório de backup: {self.diretorio_backup}")
        try:
            os.makedirs(self.diretorio_backup, exist_ok=True)
            
            # Backup dos arquivos que serão removidos
            for arquivo in self.arquivos_dev_para_remover:
                if os.path.exists(arquivo):
                    shutil.copy2(arquivo, os.path.join(self.diretorio_backup, arquivo))
                    logger.info(f"Backup do arquivo {arquivo} criado")
                    
            # Backup dos dados do banco antes da limpeza
            self.backup_banco_dados()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao criar backups: {e}")
            return False

    def backup_banco_dados(self):
        """Cria backup do banco de dados"""
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

    def remover_arquivos_desenvolvimento(self):
        """Remove arquivos específicos de desenvolvimento"""
        try:
            arquivos_removidos = 0
            for arquivo in self.arquivos_dev_para_remover:
                if os.path.exists(arquivo):
                    # Checar se já existe backup
                    if os.path.exists(os.path.join(self.diretorio_backup, arquivo)):
                        os.remove(arquivo)
                        arquivos_removidos += 1
                        logger.info(f"Arquivo removido: {arquivo}")
                    else:
                        logger.warning(f"Arquivo {arquivo} não possui backup, pulando remoção")
            
            logger.info(f"Total de {arquivos_removidos} arquivos de desenvolvimento removidos")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover arquivos de desenvolvimento: {e}")
            return False

    def criar_estrutura_stripe(self):
        """Cria estrutura necessária para integração com Stripe"""
        conn = self.conectar_bd()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Verificar se a tabela config_pagamentos existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'config_pagamentos'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                # Criar tabela para configurações de pagamento
                cursor.execute("""
                    CREATE TABLE config_pagamentos (
                        id SERIAL PRIMARY KEY,
                        usuario_id VARCHAR NOT NULL,
                        stripe_customer_id VARCHAR,
                        stripe_subscription_id VARCHAR,
                        plano VARCHAR,
                        status VARCHAR,
                        data_inicio TIMESTAMP,
                        data_proxima_cobranca TIMESTAMP,
                        metodo_pagamento VARCHAR,
                        ultimos_digitos VARCHAR(4),
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("Tabela config_pagamentos criada com sucesso")
            else:
                logger.info("Tabela config_pagamentos já existe")
            
            # Verificar se a tabela pagamentos existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'pagamentos'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                # Criar tabela para histórico de pagamentos
                cursor.execute("""
                    CREATE TABLE pagamentos (
                        id SERIAL PRIMARY KEY,
                        usuario_id VARCHAR NOT NULL,
                        stripe_payment_id VARCHAR,
                        stripe_invoice_id VARCHAR,
                        valor DECIMAL(10, 2),
                        moeda VARCHAR DEFAULT 'BRL',
                        status VARCHAR,
                        data_pagamento TIMESTAMP,
                        periodo_inicio TIMESTAMP,
                        periodo_fim TIMESTAMP,
                        descricao VARCHAR,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("Tabela pagamentos criada com sucesso")
            else:
                logger.info("Tabela pagamentos já existe")
            
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

    def desativar_modo_desenvolvedor(self):
        """Desativa configurações específicas de modo desenvolvedor"""
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
                if os.path.exists(arquivo):
                    # Backup do arquivo
                    backup_path = os.path.join(self.diretorio_backup, arquivo.replace('/', '_'))
                    shutil.copy2(arquivo, backup_path)
                    
                    # Ler conteúdo do arquivo
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    # Desativar flags de desenvolvimento
                    conteudo_modificado = conteudo.replace('DEBUG = True', 'DEBUG = False')
                    conteudo_modificado = conteudo_modificado.replace('DESENVOLVIMENTO = True', 'DESENVOLVIMENTO = False')
                    conteudo_modificado = conteudo_modificado.replace('modo_teste = True', 'modo_teste = False')
                    conteudo_modificado = conteudo_modificado.replace('modo_dev = True', 'modo_dev = False')
                    conteudo_modificado = conteudo_modificado.replace('dev_mode = True', 'dev_mode = False')
                    
                    # Salvar mudanças
                    if conteudo != conteudo_modificado:
                        with open(arquivo, 'w', encoding='utf-8') as f:
                            f.write(conteudo_modificado)
                        logger.info(f"Flags de desenvolvimento desativadas em {arquivo}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao desativar modo desenvolvedor: {e}")
            return False

    def executar_limpeza_completa(self):
        """Executa o processo completo de limpeza e preparação para produção"""
        logger.info("Iniciando processo de limpeza e preparação para produção...")
        
        # 1. Criar backups antes de fazer alterações
        if not self.fazer_backup_antes_limpeza():
            logger.error("Falha ao criar backups. Abortando processo.")
            return False
        
        # 2. Limpar dados de teste do banco
        if not self.limpar_dados_teste():
            logger.warning("Falha ao limpar dados de teste. Continuando com outras etapas...")
        
        # 3. Criar estrutura para integração com Stripe
        if not self.criar_estrutura_stripe():
            logger.warning("Falha ao criar estrutura para Stripe. Continuando com outras etapas...")
        
        # 4. Desativar modo desenvolvedor
        if not self.desativar_modo_desenvolvedor():
            logger.warning("Falha ao desativar modo desenvolvedor. Continuando com outras etapas...")
        
        # 5. Remover arquivos de desenvolvimento
        if not self.remover_arquivos_desenvolvimento():
            logger.warning("Falha ao remover arquivos de desenvolvimento. Continuando com outras etapas...")
        
        logger.info("Processo de limpeza e preparação para produção concluído!")
        logger.info(f"Backup criado no diretório: {self.diretorio_backup}")
        return True

if __name__ == "__main__":
    limpeza = LimpezaProducao()
    
    print("=" * 80)
    print("PREPARAÇÃO DO AMBIENTE PARA PRODUÇÃO E INTEGRAÇÃO STRIPE")
    print("=" * 80)
    print("\nEste script irá:")
    print("1. Criar backups de segurança de todos os dados e arquivos")
    print("2. Remover dados de teste e desenvolvimento do banco de dados")
    print("3. Criar estruturas necessárias para integração com Stripe")
    print("4. Desativar flags e modos de desenvolvimento")
    print("5. Remover arquivos e ferramentas específicas de desenvolvimento")
    print("\nATENÇÃO: Este processo não pode ser desfeito automaticamente.")
    print(f"Backups serão criados no diretório: {limpeza.diretorio_backup}")
    print("=" * 80)
    
    confirmacao = input("\nDeseja continuar? (digite 'SIM' para confirmar): ")
    
    if confirmacao.upper() == "SIM":
        print("\nIniciando processo de limpeza e preparação...")
        sucesso = limpeza.executar_limpeza_completa()
        
        if sucesso:
            print("\n✅ Processo concluído com sucesso!")
            print(f"Backups criados em: {limpeza.diretorio_backup}")
            print("\nAgora você pode proceder com a integração do Stripe.")
        else:
            print("\n❌ Processo concluído com erros!")
            print("Verifique os logs para mais detalhes.")
    else:
        print("\nOperação cancelada pelo usuário.")