"""
Módulo de compatibilidade para integração da nova função de finalização v2 de propostas 
com a interface existente do sistema.

Este módulo serve como uma "ponte" para chamar a função melhorada de finalização
mantendo a compatibilidade com o resto do código.
"""
import logging
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar a função melhorada V2
from utils.finalizar_proposta_v2 import finalizar_proposta_v2

def finalizar_proposta_segura_v2(proposta_id: int) -> Dict[str, Any]:
    """
    Função wrapper para manter compatibilidade com o código existente,
    chamando a versão V2 da função de finalização
    
    Args:
        proposta_id: ID da proposta a ser finalizada
        
    Returns:
        Dict com status da operação e mensagens no formato esperado pelo front-end
    """
    # Adicionar mensagem de log mais visível para depuração
    print(f"===== WRAPPER V2 CHAMADO PARA FINALIZAR PROPOSTA #{proposta_id} =====")
    logger.info(f"Wrapper V2 chamado para finalizar proposta #{proposta_id}")
    
    try:
        # Chamar a nova implementação V2
        resultado = finalizar_proposta_v2(proposta_id)
        
        if resultado["status"]:
            logger.info(f"Finalização V2 concluída com sucesso: {resultado['lancamentos']['gerados']} lançamentos")
            
            # Formato compatível com o código existente
            return {
                "status": True,
                "mensagem": resultado["mensagem"],
                "message": resultado["mensagem"],  # Para compatibilidade com código legado
                "proposta_numero": resultado.get("proposta_numero", ""),
                "lancamentos_gerados": resultado["lancamentos"]["gerados"]
            }
        else:
            logger.error(f"Falha na finalização V2: {resultado['mensagem']}")
            return {
                "status": False,
                "mensagem": resultado["mensagem"],
                "message": resultado["mensagem"]  # Para compatibilidade com código legado
            }
    
    except Exception as e:
        logger.exception("Erro inesperado ao finalizar proposta com V2")
        return {
            "status": False,
            "mensagem": f"Erro inesperado: {str(e)}",
            "message": f"Erro inesperado: {str(e)}"  # Para compatibilidade com código legado
        }