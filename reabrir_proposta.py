"""
Módulo auxiliar para reabrir propostas finalizadas
"""
import traceback
from datetime import date, datetime, timedelta
from utils.database import Database, Transacao
from sqlalchemy import text, delete

def remover_lancamentos_financeiros(db, proposta_id):
    """
    Remove todos os lançamentos financeiros relacionados a uma proposta
    
    Args:
        db: Instância do Database
        proposta_id: ID da proposta
        
    Returns:
        dict: Resultado da operação com status, mensagem e quantidade de lançamentos removidos
    """
    try:
        # Usar SQL direto para excluir os lançamentos
        query_delete = text("""
        DELETE FROM financeiro
        WHERE proposta_id = :proposta_id
        """)
        result = db.session.execute(query_delete, {"proposta_id": proposta_id})
        
        # Obter o número de linhas afetadas
        num_lancamentos_removidos = result.rowcount
        db.session.commit()
        
        print(f"DEBUG: Removidos {num_lancamentos_removidos} lançamentos financeiros da proposta ID={proposta_id}")
        
        return {
            "status": "sucesso", 
            "mensagem": f"Removidos {num_lancamentos_removidos} lançamentos financeiros",
            "lancamentos_removidos": num_lancamentos_removidos
        }
    except Exception as e:
        db.session.rollback()
        print(f"ERRO: Falha ao remover lançamentos financeiros: {str(e)}")
        traceback.print_exc()
        return {
            "status": "erro",
            "mensagem": f"Erro ao remover lançamentos financeiros: {str(e)}",
            "lancamentos_removidos": 0
        }

def reabrir_proposta_finalizada(proposta_id):
    """
    Reabre uma proposta finalizada, voltando seu status para "Em execução"
    
    Args:
        proposta_id: ID da proposta a ser reaberta
        
    Returns:
        dict: Resultado da operação com status e mensagens
    """
    try:
        # Converter proposta_id para inteiro
        try:
            proposta_id = int(proposta_id)
        except (ValueError, TypeError):
            return {
                "status": "erro",
                "mensagem": f"ID de proposta inválido: {proposta_id}"
            }
            
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
        
        # Usar SQL direto para garantir a atualização da proposta
        try:
            # Atualizar o status da proposta usando SQL diretamente
            query_update = text("""
            UPDATE propostas
            SET status = 'Em execução', status_execucao = 'Em execução'
            WHERE id = :proposta_id
            """)
            db.session.execute(query_update, {"proposta_id": proposta_id})
            db.session.commit()
            resultado = {"status": "sucesso", "mensagem": "Proposta atualizada com sucesso"}
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao executar SQL direto: {str(e)}")
            
            # Se o SQL direto falhar, tentar o método normal
            resultado = db.atualizar_proposta(
                proposta_id=proposta_id,
                status="Em execução",
                status_execucao="Em execução",
                gerar_transacoes_automaticas=False
            )
        
        if resultado.get('status') != 'sucesso':
            return {
                "status": "erro",
                "mensagem": f"Erro ao atualizar proposta: {resultado.get('mensagem', 'Erro desconhecido')}"
            }
        
        # Se existirem lançamentos financeiros, remova-os
        # É melhor criar uma nova sessão de banco de dados para evitar problemas de transação
        resultado_remocao = {"lancamentos_removidos": 0}
        if tem_lancamentos:
            # Fechamos a sessão atual para garantir que a transação de atualização de proposta finalize
            db.session.commit()
            # Então usamos uma nova conexão para a remoção de lançamentos
            db_remove = Database()
            resultado_remocao = remover_lancamentos_financeiros(db_remove, proposta_id)
            if resultado_remocao["status"] != "sucesso":
                # Houve um erro ao remover os lançamentos, mas a proposta já foi reaberta
                # Alertar o usuário
                return {
                    "status": "sucesso_parcial",
                    "mensagem": "Proposta reaberta com sucesso, mas houve problemas para remover lançamentos existentes",
                    "alerta": resultado_remocao["mensagem"]
                }
        
        # Gerar novos lançamentos financeiros para a proposta
        # Importante: precisamos usar um novo objeto Database para evitar problemas de transação
        try:
            # Criar nova conexão com o banco para evitar o erro de sessão em estado 'prepared'
            db_new = Database()
            # Gerar lançamentos financeiros
            db_new.gerar_lancamentos_financeiros_proposta_concluida(proposta_id)
            print(f"DEBUG: Lançamentos financeiros regenerados para a proposta ID={proposta_id}")
        except Exception as e:
            print(f"ERRO: Falha ao gerar novos lançamentos financeiros: {str(e)}")
            return {
                "status": "sucesso_parcial",
                "mensagem": "Proposta reaberta com sucesso, mas houve problemas para gerar novos lançamentos financeiros",
                "alerta": f"Erro ao gerar lançamentos: {str(e)}",
                "lancamentos_removidos": resultado_remocao.get("lancamentos_removidos", 0)
            }
            
        # Retornar resultado com informações sobre os lançamentos
        return {
            "status": "sucesso",
            "mensagem": "Proposta reaberta com sucesso",
            "info": "Lançamentos financeiros foram removidos e regenerados automaticamente",
            "lancamentos_removidos": resultado_remocao.get("lancamentos_removidos", 0)
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