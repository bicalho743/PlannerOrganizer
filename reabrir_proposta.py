"""
Módulo auxiliar para reabrir propostas finalizadas
"""
import traceback
from datetime import date, datetime, timedelta
from utils.database import Database
from sqlalchemy import text

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
        # Buscamos todas as propostas e depois filtramos pelo ID
        propostas = db.get_propostas()
        proposta = propostas[propostas['id'] == proposta_id] if not propostas.empty else None
        
        if proposta is None or proposta.empty:
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
        # Consulta os lançamentos financeiros usando SQL diretamente
        query = text("""
        SELECT COUNT(*) FROM financeiro 
        WHERE proposta_id = :proposta_id
        """)
        resultado_query = db.session.execute(query, {"proposta_id": proposta_id}).scalar()
        tem_lancamentos = resultado_query > 0
        
        # Atualizar status da proposta
        # Adicionar um pouco mais de informação para depuração
        print(f"DEBUG: Reabrindo proposta ID={proposta_id} - status anterior: {status}, status_execucao anterior: {status_execucao}")
        
        # Configurar para não gerar transações financeiras ao reabrir
        resultado = db.atualizar_proposta(
            proposta_id=proposta_id,
            status="Em andamento",
            status_execucao="Em execução",
            gerar_transacoes_automaticas=False
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
                "lancamentos_encontrados": resultado_query
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