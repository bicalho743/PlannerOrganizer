"""
Script para corrigir problemas de lançamentos financeiros duplicados.
Este script melhora a detecção de lançamentos existentes para evitar duplicação.
"""
import logging
import os
import psycopg2
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL não encontrada")
            return None
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}")
        return None

def identify_duplicated_entries():
    """Identifica lançamentos financeiros duplicados para a mesma proposta"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.descricao, COUNT(f.id) as lancamentos_count
            FROM propostas p
            JOIN financeiro f ON p.id = f.proposta_id
            WHERE p.status = 'Finalizada'
            GROUP BY p.id, p.descricao
            HAVING COUNT(f.id) > 1
            ORDER BY lancamentos_count DESC;
        """)
        
        duplicates = cursor.fetchall()
        return duplicates
    except Exception as e:
        logger.error(f"Erro ao buscar lançamentos duplicados: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def fix_verification_functions():
    """
    Atualiza as funções de verificação de lançamentos financeiros existentes
    para utilizar o proposta_id em vez de verificar apenas pela descrição
    """
    conn = get_db_connection()
    if not conn:
        return False, "Erro ao conectar ao banco de dados"
    
    try:
        cursor = conn.cursor()
        
        # Verificar se há duplicação de lançamentos
        duplicates = identify_duplicated_entries()
        if duplicates:
            logger.info(f"Encontrados {len(duplicates)} propostas com lançamentos duplicados")
            
            # Para cada proposta com lançamentos duplicados, manter apenas um
            for proposta_id, descricao, count in duplicates:
                logger.info(f"Proposta #{proposta_id} ({descricao}) tem {count} lançamentos")
                
                # Identificar todos os lançamentos para esta proposta
                cursor.execute("""
                    SELECT id, descricao, tipo, data, valor 
                    FROM financeiro 
                    WHERE proposta_id = %s
                    ORDER BY id;
                """, (proposta_id,))
                
                lancamentos = cursor.fetchall()
                lancamento_principal = lancamentos[0]  # Manter o primeiro lançamento (geralmente o mais antigo)
                
                # Remover os lançamentos duplicados (todos exceto o primeiro)
                for lancamento in lancamentos[1:]:
                    logger.info(f"Removendo lançamento duplicado ID={lancamento[0]}")
                    cursor.execute("DELETE FROM financeiro WHERE id = %s;", (lancamento[0],))
                
                # Log do lançamento mantido
                logger.info(f"Mantido lançamento ID={lancamento_principal[0]}")
        
        # Atualizar função SQL para verificar existência de lançamentos por proposta_id
        cursor.execute("""
            CREATE OR REPLACE FUNCTION verificar_lancamento_existe(proposta_id_param INTEGER) 
            RETURNS BOOLEAN AS $$
            DECLARE
                existe BOOLEAN;
            BEGIN
                SELECT EXISTS(
                    SELECT 1 FROM financeiro 
                    WHERE proposta_id = proposta_id_param
                ) INTO existe;
                
                RETURN existe;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        logger.info("Função de verificação de lançamentos atualizada com sucesso")
        
        return True, "Correção aplicada com sucesso"
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao aplicar correção: {str(e)}")
        return False, f"Erro ao aplicar correção: {str(e)}"
    finally:
        cursor.close()
        conn.close()

def main():
    """Função principal"""
    print("Iniciando correção de lançamentos financeiros duplicados...")
    
    sucesso, mensagem = fix_verification_functions()
    
    if sucesso:
        print("✅ " + mensagem)
    else:
        print("❌ " + mensagem)

if __name__ == "__main__":
    main()