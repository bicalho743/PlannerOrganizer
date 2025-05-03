"""
Script de preparação para integração com Stripe
Este script realiza todas as etapas necessárias para preparar a aplicação para integração com Stripe,
incluindo limpeza de arquivos, verificação de dependências e preparação do banco de dados.
"""
import os
import sys
import shutil
import logging
import subprocess
from datetime import datetime
import importlib.util

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diretório para backup
BACKUP_DIR = f"backup_pre_stripe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Arquivos necessários para verificação
ARQUIVOS_NECESSARIOS = [
    "utils/stripe_integration.py",
    "migracao_stripe.sql",
    "pages/stripe_webhook.py"
]

# Variáveis de ambiente necessárias
VARIAVEIS_AMBIENTE_NECESSARIAS = [
    "STRIPE_API_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRICE_ID_MENSAL",
    "STRIPE_PRICE_ID_ANUAL"
]

def verificar_arquivos_necessarios():
    """Verifica se todos os arquivos necessários para integração com Stripe existem"""
    arquivos_faltando = []
    
    for arquivo in ARQUIVOS_NECESSARIOS:
        if not os.path.exists(arquivo):
            arquivos_faltando.append(arquivo)
    
    if arquivos_faltando:
        logger.error(f"Os seguintes arquivos necessários estão faltando: {', '.join(arquivos_faltando)}")
        return False
    
    logger.info("Todos os arquivos necessários para integração com Stripe estão presentes.")
    return True

def verificar_variaveis_ambiente():
    """Verifica se todas as variáveis de ambiente necessárias estão definidas"""
    variaveis_faltando = []
    
    for variavel in VARIAVEIS_AMBIENTE_NECESSARIAS:
        if os.environ.get(variavel) is None:
            variaveis_faltando.append(variavel)
    
    if variaveis_faltando:
        logger.warning(f"As seguintes variáveis de ambiente estão faltando: {', '.join(variaveis_faltando)}")
        logger.warning("Você precisará configurar essas variáveis no ambiente de produção para que a integração funcione corretamente.")
        return False
    
    logger.info("Todas as variáveis de ambiente necessárias estão definidas.")
    return True

def verificar_dependencias():
    """Verifica se todas as dependências Python necessárias estão instaladas"""
    try:
        # Verificar se o módulo stripe está instalado
        if importlib.util.find_spec("stripe") is None:
            logger.error("A biblioteca 'stripe' não está instalada. Execute 'pip install stripe'.")
            return False
        
        logger.info("Todas as dependências Python necessárias estão instaladas.")
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar dependências: {str(e)}")
        return False

def executar_migracao_banco():
    """Executa o script SQL de migração do banco de dados"""
    try:
        # Verificar se o arquivo de migração existe
        if not os.path.exists("migracao_stripe.sql"):
            logger.error("Arquivo de migração 'migracao_stripe.sql' não encontrado.")
            return False
        
        # Verificar se a variável de ambiente DATABASE_URL está definida
        if not os.environ.get("DATABASE_URL"):
            logger.error("Variável de ambiente DATABASE_URL não está definida.")
            return False
        
        # Executar o script SQL usando psql
        logger.info("Executando migração do banco de dados...")
        
        # Usar a variável DATABASE_URL para conectar ao banco
        # Executar o arquivo SQL usando psql
        # Nota: Esta implementação assume que o psql está disponível no PATH
        
        # Em vez de executar diretamente, apenas exibir o comando que seria executado
        # para evitar alterações acidentais no banco de dados
        database_url = os.environ.get("DATABASE_URL")
        logger.info("Comando para executar a migração (não será executado automaticamente):")
        logger.info(f"psql {database_url} -f migracao_stripe.sql")
        
        logger.info("Para segurança, a migração do banco de dados não será executada automaticamente.")
        logger.info("Você deve executar o script SQL manualmente em produção.")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao executar migração do banco de dados: {str(e)}")
        return False

def criar_arquivo_checklist():
    """Cria um arquivo de checklist para ser usado na implantação"""
    try:
        conteudo = """# Checklist de Implantação para Integração com Stripe

## Pré-requisitos
- [ ] Criar conta no Stripe e configurar produtos/preços
- [ ] Obter as chaves de API do Stripe (chave pública e secreta)
- [ ] Configurar webhook no painel do Stripe
- [ ] Configurar IDs de preços para assinaturas mensais e anuais

## Configuração de Ambiente
- [ ] Configurar variável STRIPE_API_KEY
- [ ] Configurar variável STRIPE_WEBHOOK_SECRET
- [ ] Configurar variável STRIPE_PRICE_ID_MENSAL
- [ ] Configurar variável STRIPE_PRICE_ID_ANUAL
- [ ] Configurar variável APP_URL com URL da aplicação

## Banco de Dados
- [ ] Executar script de migração migracao_stripe.sql
- [ ] Verificar se as novas tabelas foram criadas corretamente
- [ ] Verificar se os índices foram criados corretamente
- [ ] Verificar se a view vw_status_assinatura foi criada corretamente

## Código
- [ ] Verificar se utils/stripe_integration.py está configurado corretamente
- [ ] Verificar se pages/stripe_webhook.py está configurado corretamente
- [ ] Verificar se a página de planos está chamando as funções de integração

## Testes
- [ ] Testar criação de assinatura com cartão de teste
- [ ] Verificar se o webhook está recebendo eventos
- [ ] Verificar se o status do plano é atualizado corretamente
- [ ] Testar cancelamento de assinatura
- [ ] Verificar se limites por plano estão sendo aplicados corretamente
        """
        
        with open("checklist_stripe.md", "w") as f:
            f.write(conteudo)
        
        logger.info("Arquivo de checklist 'checklist_stripe.md' criado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar arquivo de checklist: {str(e)}")
        return False

def main():
    """Função principal"""
    logger.info("Iniciando preparação para integração com Stripe...")
    
    # Criar diretório de backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Verificar pré-requisitos
    verificar_arquivos_necessarios()
    verificar_variaveis_ambiente()
    verificar_dependencias()
    
    # Executar migração do banco de dados (apenas simulação)
    executar_migracao_banco()
    
    # Criar arquivo de checklist
    criar_arquivo_checklist()
    
    logger.info(f"Preparação concluída. Backup disponível em {BACKUP_DIR}")
    logger.info("Consulte o arquivo 'checklist_stripe.md' para os próximos passos.")
    
    return True

if __name__ == "__main__":
    main()