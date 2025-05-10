#!/usr/bin/env python3
"""
Script para testar as funcionalidades de finalização e regeneração de lançamentos
"""
import os
import sys
import logging
from datetime import datetime

# Configuração de log
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("teste_finalizar")

from utils.finalizar_proposta_fix import finalizar_proposta_sql, finalizar_proposta_segura, get_db_connection
from utils.regenerar_lancamentos import regenerar_lancamentos

def main():
    # Testar a finalização e regeneração em um único script
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return
    
    cursor = conn.cursor()
    proposta_id = None
    
    try:
        # Criar uma proposta de teste para verificar o funcionamento
        cursor.execute("""
            INSERT INTO propostas (cliente_id, descricao, valor, status, status_execucao, 
                                 data_inicio, data_fim, data_proposta, numero)
            VALUES (2, 'Teste Proposta Automática', 1500, 'Aprovada', 'Finalizada', 
                   CURRENT_DATE, CURRENT_DATE, CURRENT_DATE, 9999)
            RETURNING id
        """)
        proposta_id = cursor.fetchone()[0]
        logger.info(f'Proposta de teste criada com ID {proposta_id}')

        # Adicionar itens de teste à proposta
        cursor.execute("""
            INSERT INTO acrescimos_proposta (proposta_id, tipo, fornecedor, descricao, valor)
            VALUES 
            (%s, 'FORNECEDOR', 'Fornecedor Teste', 'Produtos diversos', 3000),
            (%s, 'ASSISTENTE', 'Assistente Teste', 'Serviço de assistente', 500),
            (%s, 'OUTRO', 'Serviço Extra', 'Serviço adicional de teste', 800)
        """, (proposta_id, proposta_id, proposta_id))

        conn.commit()
        logger.info('Itens adicionados à proposta')

        # Finalizar a proposta
        logger.info('Finalizando proposta...')
        resultado_finalizacao = finalizar_proposta_segura(proposta_id)
        logger.info(f'Resultado da finalização: {resultado_finalizacao}')

        # Verificar os lançamentos gerados
        cursor.execute("""
            SELECT id, tipo, categoria, subcategoria, descricao, valor, origem_tipo, origem_id 
            FROM financeiro WHERE proposta_id = %s
            ORDER BY id
        """, (proposta_id,))

        lancamentos = cursor.fetchall()
        logger.info(f'Lançamentos gerados na finalização: {len(lancamentos)}')

        for lancamento in lancamentos:
            logger.info(f'ID: {lancamento[0]}, Tipo: {lancamento[1]}, Categoria: {lancamento[2]}, Valor: {lancamento[5]}')

        # Agora vamos limpar os lançamentos e regenerá-los
        cursor.execute('DELETE FROM financeiro WHERE proposta_id = %s', (proposta_id,))
        conn.commit()
        logger.info('Lançamentos removidos')

        # Regenerar os lançamentos
        logger.info('Regenerando lançamentos...')
        resultado_regeneracao = regenerar_lancamentos(proposta_id)
        logger.info(f'Resultado da regeneração: {resultado_regeneracao}')

        # Verificar os lançamentos regenerados
        cursor.execute("""
            SELECT id, tipo, categoria, subcategoria, descricao, valor, origem_tipo, origem_id 
            FROM financeiro WHERE proposta_id = %s
            ORDER BY id
        """, (proposta_id,))

        lancamentos_regenerados = cursor.fetchall()
        logger.info(f'Lançamentos regenerados: {len(lancamentos_regenerados)}')

        for lancamento in lancamentos_regenerados:
            logger.info(f'ID: {lancamento[0]}, Tipo: {lancamento[1]}, Categoria: {lancamento[2]}, Valor: {lancamento[5]}')

    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if proposta_id:
            # Limpar dados de teste
            try:
                cursor.execute('DELETE FROM financeiro WHERE proposta_id = %s', (proposta_id,))
                cursor.execute('DELETE FROM acrescimos_proposta WHERE proposta_id = %s', (proposta_id,))
                cursor.execute('DELETE FROM propostas WHERE id = %s', (proposta_id,))
                conn.commit()
                logger.info('Dados de teste removidos')
            except Exception as cleanup_error:
                logger.error(f"Erro ao limpar dados de teste: {str(cleanup_error)}")
                conn.rollback()

        if conn:
            conn.close()
        logger.info('Teste concluído')

if __name__ == "__main__":
    main()