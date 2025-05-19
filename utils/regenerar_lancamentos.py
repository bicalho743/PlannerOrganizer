"""
Módulo com funções para regenerar lançamentos financeiros para propostas finalizadas

Este módulo contém a função para:
1. Remover lançamentos existentes para uma proposta
2. Recriar todos os lançamentos necessários utilizando a função de finalização aprimorada
"""
import logging
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar a função melhorada para finalização de propostas
from utils.finalizar_proposta_improved import regenerar_lancamentos_proposta

def regenerar_lancamentos(proposta_id: int) -> Dict[str, Any]:
    """
    Regenera todos os lançamentos financeiros para uma proposta específica
    
    Esta função simplesmente chama a versão aprimorada da finalização de proposta,
    que já lida com a remoção e recriação dos lançamentos financeiros corretos.
    
    Args:
        proposta_id: ID da proposta para regenerar lançamentos
        
    Returns:
        Dict com status da operação, mensagens e contagem de lançamentos
    """
    logger.info(f"Iniciando regeneração de lançamentos para proposta #{proposta_id}")
    
    try:
        # Chamar função melhorada que já implementa toda a lógica necessária
        resultado = regenerar_lancamentos_proposta(proposta_id)
        
        if resultado["status"]:
            logger.info(f"Regeneração concluída com sucesso: {resultado['lancamentos']['gerados']} lançamentos")
            
            # Criar um resultado compatível com a interface da aplicação
            return {
                "status": True,
                "mensagem": resultado["mensagem"],
                "lancamentos_gerados": resultado["lancamentos"]["gerados"],
                "detalhes": resultado["lancamentos"]["valores"]
            }
        else:
            logger.error(f"Falha na regeneração: {resultado['mensagem']}")
            return {
                "status": False,
                "mensagem": resultado["mensagem"],
                "lancamentos_gerados": 0,
                "detalhes": {}
            }
    
    except Exception as e:
        logger.exception("Erro inesperado ao regenerar lançamentos")
        return {
            "status": False,
            "mensagem": f"Erro inesperado: {str(e)}",
            "lancamentos_gerados": 0,
            "detalhes": {}
        }