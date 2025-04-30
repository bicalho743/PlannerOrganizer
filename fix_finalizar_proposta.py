"""
Script para corrigir problema de finalização de propostas no Render
Este script deve ser executado diretamente no ambiente Render
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_sql_fix():
    """
    Executa correções SQL para resolver o problema de finalização de propostas no Render
    """
    logger.info("Iniciando script de correção para finalização de propostas")
    
    # Verificar variável de ambiente DATABASE_URL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL não encontrada nas variáveis de ambiente")
        sys.exit(1)
    
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info("Conectado ao banco de dados com sucesso")
        
        # 1. Verificar coluna usuario_id na tabela financeiro
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'financeiro' AND column_name = 'usuario_id'
            );
        """)
        has_usuario_id = cursor.fetchone()[0]
        
        if not has_usuario_id:
            logger.info("Adicionando coluna usuario_id à tabela financeiro")
            cursor.execute("ALTER TABLE financeiro ADD COLUMN usuario_id VARCHAR;")
            logger.info("Coluna usuario_id adicionada com sucesso")
        else:
            logger.info("Coluna usuario_id já existe na tabela financeiro")
        
        # 2. Verificar se há lançamentos sem usuario_id
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro WHERE usuario_id IS NULL;
        """)
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            logger.info(f"Encontrados {null_count} lançamentos sem usuario_id")
            
            # Atualizar lançamentos sem usuario_id
            cursor.execute("""
                UPDATE financeiro f
                SET usuario_id = p.usuario_id
                FROM propostas p
                WHERE f.proposta_id = p.id AND f.usuario_id IS NULL;
            """)
            logger.info("Lançamentos atualizados com sucesso")
        
        # 3. Criar função trigger para garantir que novos lançamentos terão usuario_id
        cursor.execute("""
            CREATE OR REPLACE FUNCTION set_usuario_id_from_proposta()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.usuario_id IS NULL AND NEW.proposta_id IS NOT NULL THEN
                    NEW.usuario_id := (SELECT usuario_id FROM propostas WHERE id = NEW.proposta_id);
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS financeiro_usuario_id_trigger ON financeiro;
            
            CREATE TRIGGER financeiro_usuario_id_trigger
            BEFORE INSERT OR UPDATE ON financeiro
            FOR EACH ROW
            EXECUTE FUNCTION set_usuario_id_from_proposta();
        """)
        logger.info("Trigger de atualização de usuario_id criado com sucesso")
        
        # 4. Verificar e corrigir se existem propostas finalizadas sem lançamentos
        cursor.execute("""
            SELECT p.id
            FROM propostas p
            LEFT JOIN financeiro f ON p.id = f.proposta_id
            WHERE p.status = 'Finalizada' AND f.id IS NULL;
        """)
        
        propostas_sem_lancamentos = cursor.fetchall()
        
        if propostas_sem_lancamentos:
            logger.info(f"Encontradas {len(propostas_sem_lancamentos)} propostas finalizadas sem lançamentos")
            
            for proposta_id in propostas_sem_lancamentos:
                cursor.execute("""
                    SELECT p.id, p.valor, p.usuario_id, c.nome as cliente_nome
                    FROM propostas p
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.id = %s;
                """, (proposta_id[0],))
                
                proposta = cursor.fetchone()
                
                if proposta:
                    # Criar lançamento principal para a proposta
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        f"Proposta #{proposta[0]} - {proposta[3]}",
                        proposta[1],
                        datetime.now().date(),
                        "Serviços de Organização",
                        "receita_a_receber",
                        "Pendente",
                        "",
                        proposta[0],
                        proposta[2]
                    ))
                    
                    logger.info(f"Criado lançamento para proposta finalizada #{proposta[0]}")
        
        logger.info("Script de correção executado com sucesso")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro durante a execução das correções: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_sql_fix()