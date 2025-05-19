"""
Módulo de compatibilidade para integração da nova função de finalização de propostas 
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

# Importar a função melhorada
from utils.finalizar_proposta_improved import finalizar_proposta_improved

def finalizar_proposta_segura(proposta_id: int) -> Dict[str, Any]:
    """
    Função wrapper para manter compatibilidade com o código existente
    
    Esta função simplesmente chama a versão aprimorada e adapta 
    o resultado para o formato esperado pelo código legado.
    
    Args:
        proposta_id: ID da proposta a ser finalizada
        
    Returns:
        Dict com status da operação e mensagens no formato esperado pelo front-end
    """
    logger.info(f"Wrapper chamado para finalizar proposta #{proposta_id}")
    
    try:
        # Chamar a nova implementação
        resultado = finalizar_proposta_improved(proposta_id)
        
        if resultado["status"]:
            logger.info(f"Finalização concluída com sucesso: {resultado['lancamentos']['gerados']} lançamentos")
            
            # Formato compatível com o código existente
            return {
                "status": True,
                "mensagem": resultado["mensagem"],
                "message": resultado["mensagem"],  # Para compatibilidade com código legado
                "proposta_numero": resultado.get("proposta_numero", ""),
                "lancamentos_gerados": resultado["lancamentos"]["gerados"]
            }
        else:
            logger.error(f"Falha na finalização: {resultado['mensagem']}")
            return {
                "status": False,
                "mensagem": resultado["mensagem"],
                "message": resultado["mensagem"]  # Para compatibilidade com código legado
            }
    
    except Exception as e:
        logger.exception("Erro inesperado ao finalizar proposta")
        return {
            "status": False,
            "mensagem": f"Erro inesperado: {str(e)}",
            "message": f"Erro inesperado: {str(e)}"  # Para compatibilidade com código legado
        }