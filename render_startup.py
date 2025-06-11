"""
Script de inicialização para ambiente Render
"""
import os
import logging

logger = logging.getLogger(__name__)

def initialize_render_environment():
    """Inicializa configurações específicas do Render"""
    logger.info("Inicializando ambiente Render...")
    
    # Configurar variáveis de ambiente específicas do Render
    if not os.getenv('PORT'):
        os.environ['PORT'] = '5000'
    
    # Outras configurações específicas do Render podem ser adicionadas aqui
    logger.info("Ambiente Render inicializado com sucesso")

# Executar inicialização automaticamente quando importado
initialize_render_environment()