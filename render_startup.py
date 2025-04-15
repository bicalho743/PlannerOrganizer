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

def wait_for_database(max_attempts=5, delay=5):
    """
    Espera até que a conexão com o banco de dados esteja disponível
    
    Isso é útil para o Render, onde o banco de dados pode levar alguns segundos
    para ficar disponível após a inicialização do serviço.
    """
    from sqlalchemy import create_engine
    
    # Get database URL from environment variable
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL is None:
        logger.error("DATABASE_URL environment variable is not set")
        return False
    
    logger.info(f"Verificando conexão com o banco de dados (mascarado): ...@{DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'url-inválida'}")
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Tenta criar um engine e conectar
            engine = create_engine(
                DATABASE_URL,
                connect_args={
                    'sslmode': 'require',
                    'connect_timeout': 10
                } if 'postgresql' in DATABASE_URL else {},
            )
            
            # Tenta executar uma query simples
            with engine.connect() as conn:
                conn.execute("SELECT 1")
                
            logger.info("Conexão com o banco de dados estabelecida com sucesso!")
            return True
            
        except Exception as e:
            logger.warning(f"Tentativa {attempt}/{max_attempts} falhou: {str(e)}")
            if attempt < max_attempts:
                logger.info(f"Tentando novamente em {delay} segundos...")
                time.sleep(delay)
    
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