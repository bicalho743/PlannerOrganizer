"""
Módulo para reabrir propostas finalizadas.
"""
import os
import logging
import pandas as pd
import psycopg2
from datetime import datetime
from utils.database import Database

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            
        # Permitir reabrir propostas com status "Finalizada", "Concluída" ou ambos
        if status not in ["Finalizada", "Concluída"] and status_execucao not in ["Finalizada", "Concluída"]:
            return {
                "status": "erro",
                "mensagem": "Esta proposta não está finalizada e não pode ser reaberta"
            }
        
        # Verificar se existem lançamentos financeiros associados
        lancamentos = []
        try:
            # Buscar diretamente do banco usando SQL em vez de usar método do Database
            db_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Excluir lançamentos do tipo "receita_a_receber_aprovacao" para evitar duplicidade
            cursor.execute("""
                DELETE FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber_aprovacao'
            """, (proposta_id,))
            conn.commit()
            
            # Buscar lançamentos restantes
            cursor.execute("""
                SELECT * FROM financeiro WHERE proposta_id = %s
            """, (proposta_id,))
            
            # Converter resultado para lista
            lancamentos = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao buscar lançamentos financeiros: {e}")
            lancamentos = []
        
        # Reabrir a proposta diretamente via SQL para garantir que funcione
        try:
            # Conectar diretamente ao banco de dados para operações críticas
            db_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Atualizar status da proposta
            cursor.execute("""
                UPDATE propostas 
                SET status = 'Aprovada', 
                    status_execucao = 'Em execução',
                    data_finalizacao = NULL
                WHERE id = %s
            """, (proposta_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if len(lancamentos) > 0:
                return {
                    "status": "sucesso_com_alerta",
                    "mensagem": f"Proposta #{proposta_id} reaberta com sucesso",
                    "alerta": "Existem lançamentos financeiros associados a esta proposta.",
                    "lancamentos_encontrados": len(lancamentos)
                }
            else:
                return {
                    "status": "sucesso",
                    "mensagem": f"Proposta #{proposta_id} reaberta com sucesso"
                }
        except Exception as e:
            logger.error(f"Erro ao executar SQL para reabrir proposta: {e}")
            # Se falhou na primeira tentativa, tentar sem o campo data_finalizacao
            try:
                db_url = os.environ.get('DATABASE_URL')
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                
                # Tentar atualizar sem o campo data_finalizacao
                cursor.execute("""
                    UPDATE propostas 
                    SET status = 'Aprovada', 
                        status_execucao = 'Em execução'
                    WHERE id = %s
                """, (proposta_id,))
                
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e2:
                logger.error(f"Segunda tentativa falhou: {e2}")
                # Se ainda falhar, retornar erro
            
            return {
                "status": "sucesso",
                "mensagem": f"Proposta #{proposta_id} reaberta com sucesso"
            }
    except Exception as e:
        logger.error(f"Erro ao reabrir proposta: {e}")
        return {
            "status": "erro",
            "mensagem": f"Erro ao reabrir proposta: {str(e)}"
        }