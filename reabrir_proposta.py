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
        
        # Contadores para o relatório final
        lancamentos_encontrados = 0
        lancamentos_excluidos = 0
        
        # Verificar e gerenciar lançamentos financeiros associados
        try:
            # Buscar diretamente do banco usando SQL em vez de usar método do Database
            db_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Contar lançamentos financeiros associados à proposta
            cursor.execute("""
                SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s
            """, (proposta_id,))
            resultado = cursor.fetchone()
            lancamentos_encontrados = resultado[0] if resultado else 0
            logger.info(f"Encontrados {lancamentos_encontrados} lançamentos financeiros para proposta #{proposta_id}")
            
            # Primeiro, verificar quais lançamentos existem
            cursor.execute("""
                SELECT id, descricao, tipo FROM financeiro 
                WHERE proposta_id = %s 
                ORDER BY id
            """, (proposta_id,))
            lancamentos_existentes = cursor.fetchall()
            logger.info(f"Lançamentos encontrados: {lancamentos_existentes}")
            
            # Identificar o lançamento original (primeiro de receita com "Aprovação")
            lancamento_original_id = None
            for lanc_id, descricao, tipo in lancamentos_existentes:
                if tipo == 'Receita' and 'Aprovação' in descricao:
                    lancamento_original_id = lanc_id
                    break
            
            if lancamento_original_id:
                # Remover todos os lançamentos EXCETO o original
                cursor.execute("""
                    DELETE FROM financeiro 
                    WHERE proposta_id = %s 
                    AND id != %s
                    RETURNING id
                """, (proposta_id, lancamento_original_id))
            else:
                # Se não encontrar o original, remover todos os lançamentos
                cursor.execute("""
                    DELETE FROM financeiro 
                    WHERE proposta_id = %s
                    RETURNING id
                """, (proposta_id,))
            
            # Contar quantos lançamentos foram excluídos
            resultado_exclusao = cursor.fetchall()
            lancamentos_excluidos = len(resultado_exclusao)
            logger.info(f"Excluídos {lancamentos_excluidos} lançamentos relacionados à finalização")
            
            # Confirmar as alterações
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao gerenciar lançamentos financeiros: {e}")
            # Não interromper o processo por falha nesta etapa
        
        # Reabrir a proposta diretamente via SQL para garantir que funcione
        try:
            # Conectar diretamente ao banco de dados para operações críticas
            db_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Atualizar status da proposta
            data_atual = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                UPDATE propostas 
                SET status = 'Aprovada', 
                    status_execucao = 'Em execução'
                WHERE id = %s
            """, (proposta_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Decidir o tipo de retorno com base nos lançamentos encontrados e excluídos
            if lancamentos_encontrados > 0:
                return {
                    "status": "sucesso_com_alerta",
                    "mensagem": f"Proposta #{proposta_id} reaberta com sucesso",
                    "alerta": f"Foram excluídos {lancamentos_excluidos} de {lancamentos_encontrados} lançamentos financeiros.",
                    "lancamentos_encontrados": lancamentos_encontrados,
                    "lancamentos_excluidos": lancamentos_excluidos
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
                
                # Adicionar data de atualização para indicar que a proposta foi modificada
                data_atual = datetime.now().strftime('%Y-%m-%d')
                
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
                
                # Retornar resultado com informações dos lançamentos
                return {
                    "status": "sucesso",
                    "mensagem": f"Proposta #{proposta_id} reaberta com sucesso (método alternativo)",
                    "lancamentos_encontrados": lancamentos_encontrados,
                    "lancamentos_excluidos": lancamentos_excluidos
                }
            except Exception as e2:
                logger.error(f"Segunda tentativa falhou: {e2}")
                # Se ainda falhar, retornar erro
                return {
                    "status": "erro",
                    "mensagem": f"Erro ao reabrir proposta: {str(e2)}"
                }
    except Exception as e:
        logger.error(f"Erro ao reabrir proposta: {e}")
        return {
            "status": "erro",
            "mensagem": f"Erro ao reabrir proposta: {str(e)}"
        }