"""
Render Deploy Helper

Este script ajuda a verificar se o ambiente do Render está configurado corretamente
e prepara o sistema para o primeiro deploy.

Quando o Render inicia o deploy com problemas de Git, este script pode ajudar
a estabilizar o ambiente e iniciar o serviço mesmo com problemas de Git.
"""

import os
import sys
import time
import logging
from subprocess import check_output, CalledProcessError

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verifica se o ambiente do Render está configurado corretamente."""
    logger.info("Verificando ambiente do Render...")
    
    # Verificar variáveis de ambiente
    required_vars = ["DATABASE_URL", "PORT"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.warning(f"Variáveis de ambiente faltando: {', '.join(missing_vars)}")
    else:
        logger.info("Todas as variáveis de ambiente necessárias estão configuradas.")

def check_database_connection():
    """Verifica a conexão com o banco de dados."""
    logger.info("Verificando conexão com o banco de dados...")
    
    try:
        import psycopg2
        from psycopg2 import OperationalError
        
        # Recuperar DATABASE_URL do ambiente
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            logger.error("DATABASE_URL não configurado. Verifique as variáveis de ambiente.")
            return False
        
        # Tentar conexão
        try:
            conn = psycopg2.connect(database_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Verificar tabelas
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public');")
            has_tables = cursor.fetchone()
            
            if has_tables and has_tables[0]:
                logger.info("Conexão com banco de dados estabelecida com sucesso. Banco possui tabelas.")
            else:
                logger.info("Conexão com banco de dados estabelecida com sucesso. Banco está vazio.")
            
            conn.close()
            return True
        except OperationalError as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            return False
    except ImportError:
        logger.error("psycopg2 não instalado. Execute 'pip install psycopg2-binary'.")
        return False

def wait_for_database(max_attempts=30, delay=5):
    """Espera até que o banco de dados esteja disponível."""
    logger.info("Aguardando o banco de dados ficar disponível...")
    
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        if check_database_connection():
            logger.info(f"Banco de dados disponível após {attempt} tentativas.")
            return True
        else:
            logger.warning(f"Tentativa {attempt}/{max_attempts} - Banco de dados ainda não disponível. Aguardando {delay}s...")
            time.sleep(delay)
    
    logger.error(f"Banco de dados não disponível após {max_attempts} tentativas.")
    return False

def create_render_status_file():
    """Cria um arquivo de status para ajudar o Render a detectar que o app está pronto."""
    status_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status")
    os.makedirs(status_dir, exist_ok=True)
    
    status_file = os.path.join(status_dir, "render_ready.txt")
    with open(status_file, "w") as f:
        f.write(f"Render deployment status: READY\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Environment: {os.environ.get('RENDER_ENVIRONMENT', 'unknown')}\n")
    
    logger.info(f"Arquivo de status criado em {status_file}")

def check_port():
    """Verifica se a porta está configurada corretamente."""
    port = os.environ.get("PORT")
    if not port:
        logger.warning("Variável PORT não encontrada. Usando valor padrão 10000.")
        os.environ["PORT"] = "10000"
    else:
        logger.info(f"Usando porta {port} para o serviço.")

def main():
    """Função principal."""
    logger.info("Iniciando Render Deploy Helper...")
    
    # Verificar ambiente
    check_environment()
    
    # Verificar porta
    check_port()
    
    # Aguardar banco de dados
    database_ready = wait_for_database()
    
    # Criar arquivo de status
    create_render_status_file()
    
    if database_ready:
        logger.info("Ambiente pronto para iniciar a aplicação!")
        return 0
    else:
        logger.error("Problemas detectados no ambiente. Verifique os logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())