import os
import sys
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_database(max_attempts=12, delay=10):
    """
    Espera até que a conexão com o banco de dados esteja disponível
    
    Isso é útil para o Render, onde o banco de dados pode levar alguns segundos
    para ficar disponível após a inicialização do serviço.
    
    Aumento no número de tentativas e delay para resolver problemas de DNS
    em ambientes cloud como o Render.
    """
    from sqlalchemy import create_engine
    import socket
    import psycopg2
    
    # Get database URL from environment variable
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL is None:
        logger.error("DATABASE_URL environment variable is not set")
        return False
    
    # Extrair o host do DATABASE_URL para verificação de DNS
    host = None
    if '@' in DATABASE_URL:
        host_part = DATABASE_URL.split('@')[-1].split('/')[0]
        if ':' in host_part:
            host = host_part.split(':')[0]
        else:
            host = host_part
    
    logger.info(f"Verificando conexão com o banco de dados (mascarado): ...@{DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'url-inválida'}")
    
    # Tentar resolver o host primeiro para identificar problemas de DNS
    if host:
        logger.info(f"Verificando resolução DNS para o host: {host}")
        dns_resolved = False
        for dns_attempt in range(1, 6):
            try:
                socket.gethostbyname(host)
                logger.info(f"Resolução DNS bem-sucedida para {host}")
                dns_resolved = True
                break
            except socket.gaierror as e:
                logger.warning(f"Tentativa {dns_attempt}/5 de resolução DNS falhou: {str(e)}")
                time.sleep(5)
        
        if not dns_resolved:
            logger.warning("Não foi possível resolver o DNS do host. Continuando mesmo assim...")
    
    # Tentar conexão direta via psycopg2 primeiro (menos abstrações)
    if 'postgresql' in DATABASE_URL:
        logger.info("Tentando conexão direta via psycopg2...")
        for psql_attempt in range(1, 4):
            try:
                # Extrair os parâmetros de conexão da URL
                conn_parts = DATABASE_URL.replace('postgresql://', '').split('@')
                user_pass = conn_parts[0].split(':')
                host_db = conn_parts[1].split('/')
                
                user = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ''
                
                host_port = host_db[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 5432
                
                dbname = host_db[1]
                
                # Conectar diretamente
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password,
                    connect_timeout=15,
                    sslmode='require'
                )
                conn.close()
                logger.info("Conexão direta via psycopg2 bem-sucedida!")
                break
            except Exception as e:
                logger.warning(f"Tentativa {psql_attempt}/3 de conexão direta falhou: {str(e)}")
                time.sleep(5)
    
    # Tentar com SQLAlchemy como backup
    for attempt in range(1, max_attempts + 1):
        try:
            # Aumentar o timeout para ambientes de nuvem
            engine = create_engine(
                DATABASE_URL,
                connect_args={
                    'sslmode': 'require',
                    'connect_timeout': 30,  # Aumentado para 30 segundos
                    'application_name': 'planner_organizer_render'
                } if 'postgresql' in DATABASE_URL else {},
                pool_pre_ping=True,  # Verifica a conexão antes de usar
                pool_recycle=1800,   # Recicla conexões após 30 minutos
            )
            
            # Tenta executar uma query simples
            with engine.connect() as conn:
                conn.execute("SELECT 1")
                
            logger.info("Conexão com o banco de dados estabelecida com sucesso!")
            return True
            
        except Exception as e:
            logger.warning(f"Tentativa {attempt}/{max_attempts} falhou: {str(e)}")
            if attempt < max_attempts:
                # Aumentar o tempo de espera progressivamente
                adaptive_delay = delay * (1 + (attempt * 0.2))
                logger.info(f"Tentando novamente em {adaptive_delay:.1f} segundos...")
                time.sleep(adaptive_delay)
    
    logger.error("Não foi possível conectar ao banco de dados após várias tentativas")
    return False

if __name__ == "__main__":
    logger.info("=== Iniciando script de preparação para o Render ===")
    
    # Esperar até que o banco de dados esteja disponível
    db_available = wait_for_database()
    
    if db_available:
        logger.info("Banco de dados está pronto, continuando startup...")
        
        # Adicionar diretório raiz ao path
        project_root = os.path.abspath(os.path.dirname(__file__))
        if project_root not in sys.path:
            sys.path.append(project_root)
            logger.info(f"Adicionado {project_root} ao sys.path")
            
        # Importar o modelo do banco de dados e criar as tabelas
        try:
            from utils.database import Base, engine
            logger.info("Criando tabelas do banco de dados...")
            Base.metadata.create_all(engine)
            logger.info("Tabelas criadas com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {str(e)}")
            sys.exit(1)
    else:
        logger.error("Falha na inicialização: Banco de dados não está disponível")
        sys.exit(1)
        
    logger.info("=== Preparação concluída com sucesso ===")
    sys.exit(0)