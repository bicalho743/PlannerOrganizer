"""
Módulo auxiliar para reabrir propostas finalizadas
"""
import traceback
from datetime import date, datetime, timedelta
from utils.database import Database

def reabrir_proposta_finalizada(proposta_id):
    """
    Reabre uma proposta finalizada, voltando seu status para "Em execução"
    
    Args:
        proposta_id: ID da proposta a ser reaberta
        
    Returns:
        dict: Resultado da operação com status e mensagens
    """
    try:
        db = Database()
        # Verificar se a proposta existe e está finalizada
        proposta = db.get_proposta_by_id(proposta_id)
        
        if not proposta or proposta.empty:
            return {
                "status": "erro",
                "mensagem": "Proposta não encontrada"
            }
            
        status = proposta.iloc[0].get('status', None)
        status_execucao = proposta.iloc[0].get('status_execucao', None)
            
        if status != "Concluída" or status_execucao != "Finalizada":
            return {
                "status": "erro",
                "mensagem": "Apenas propostas concluídas podem ser reabertas"
            }
        
        # Verificar se existem lançamentos financeiros relacionados
        lancamentos = db.get_lancamentos_por_referencia('proposta', proposta_id)
        tem_lancamentos = not lancamentos.empty if lancamentos is not None else False
        
        # Atualizar status da proposta
        resultado = db.atualizar_proposta(
            proposta_id=proposta_id,
            status="Aprovada",
            status_execucao="Em execução"
        )
        
        if resultado.get('status') != 'sucesso':
            return {
                "status": "erro",
                "mensagem": f"Erro ao atualizar proposta: {resultado.get('mensagem', 'Erro desconhecido')}"
            }
        
        # Retornar resultado com alerta se necessário
        if tem_lancamentos:
            return {
                "status": "sucesso_com_alerta",
                "mensagem": "Proposta reaberta com sucesso",
                "alerta": "Esta proposta já possui lançamentos financeiros gerados. Considere revisar os registros financeiros.",
                "lancamentos_encontrados": len(lancamentos)
            }
        else:
            return {
                "status": "sucesso",
                "mensagem": "Proposta reaberta com sucesso"
            }
            
    except Exception as e:
        print(f"Erro ao reabrir proposta: {str(e)}")
        traceback.print_exc()
        return {
            "status": "erro",
            "mensagem": f"Erro ao reabrir proposta: {str(e)}"
        }

# Exemplo de uso:
# resultado = reabrir_proposta_finalizada(123)
# print(resultado)