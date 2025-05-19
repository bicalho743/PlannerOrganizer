"""
Script para testar a nova versão melhorada da função de finalização de propostas
que garante a correta geração de todos os lançamentos financeiros.
"""
import os
import sys
import logging
from datetime import datetime
import psycopg2

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_finalizar_improved')

# Importar a função melhorada
from utils.finalizar_proposta_improved import finalizar_proposta_improved, regenerar_lancamentos_proposta

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

def main():
    """
    Testa a função finalizar_proposta_improved com uma proposta específica
    """
    # Verificar argumentos da linha de comando ou usar proposta #15 como padrão
    if len(sys.argv) > 1:
        try:
            proposta_id = int(sys.argv[1])
        except ValueError:
            logger.error("ID de proposta inválido. Use um número inteiro.")
            sys.exit(1)
    else:
        # Usar a proposta #15 como caso de teste padrão
        conn = get_db_connection()
        if not conn:
            logger.error("Não foi possível conectar ao banco de dados")
            sys.exit(1)
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM propostas WHERE numero = 15")
        result = cursor.fetchone()
        
        if not result:
            logger.error("Proposta #15 não encontrada")
            conn.close()
            sys.exit(1)
            
        proposta_id = result[0]
        cursor.close()
        
    logger.info(f"Iniciando teste com proposta ID={proposta_id}")
    
    # Etapa 1: Verificar detalhes da proposta
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        sys.exit(1)
        
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.numero, p.descricao, p.valor, p.status, p.status_execucao, 
               p.cliente_id, c.nome
        FROM propostas p
        JOIN clientes c ON p.cliente_id = c.id
        WHERE p.id = %s
    """, (proposta_id,))
    
    proposta_info = cursor.fetchone()
    if not proposta_info:
        logger.error(f"Proposta ID={proposta_id} não encontrada")
        conn.close()
        sys.exit(1)
        
    logger.info(f"Proposta #{proposta_info[1]} - {proposta_info[2]} - Cliente: {proposta_info[7]}")
    logger.info(f"Status atual: {proposta_info[4]}/{proposta_info[5]}")
    
    # Etapa 2: Verificar acréscimos da proposta
    cursor.execute("""
        SELECT tipo, fornecedor, descricao, valor, percentual_comissao
        FROM acrescimos_proposta 
        WHERE proposta_id = %s
        ORDER BY tipo, id
    """, (proposta_id,))
    
    acrescimos = cursor.fetchall()
    logger.info(f"Acréscimos encontrados: {len(acrescimos)}")
    
    for acrescimo in acrescimos:
        tipo, fornecedor, descricao, valor, percentual = acrescimo
        logger.info(f"- {tipo}: {fornecedor} - {descricao} - R$ {valor}")
    
    # Etapa 3: Verificar lançamentos existentes e removê-los
    cursor.execute("SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s", (proposta_id,))
    count = cursor.fetchone()[0]
    logger.info(f"Lançamentos existentes: {count}")
    
    if count > 0:
        cursor.execute("DELETE FROM financeiro WHERE proposta_id = %s", (proposta_id,))
        conn.commit()
        logger.info(f"Removidos {count} lançamentos existentes")
    
    # Etapa 4: Executar a função melhorada
    logger.info("Executando finalizar_proposta_improved...")
    resultado = finalizar_proposta_improved(proposta_id)
    
    if resultado['status']:
        logger.info(f"Resultado: Sucesso - {resultado['mensagem']}")
        logger.info(f"Lançamentos gerados: {resultado['lancamentos']['gerados']}")
        
        for tipo, valor in resultado['lancamentos']['valores'].items():
            if valor > 0:
                logger.info(f"- {tipo}: R$ {valor:.2f}")
    else:
        logger.error(f"Erro: {resultado['mensagem']}")
    
    # Etapa 5: Verificar os lançamentos gerados no banco
    cursor.execute("""
        SELECT id, tipo, descricao, valor, categoria, subcategoria
        FROM financeiro 
        WHERE proposta_id = %s
        ORDER BY id
    """, (proposta_id,))
    
    lancamentos = cursor.fetchall()
    logger.info(f"Lançamentos no banco: {len(lancamentos)}")
    
    for lancamento in lancamentos:
        id_lancamento, tipo, descricao, valor, categoria, subcategoria = lancamento
        logger.info(f"- #{id_lancamento}: {tipo} - {categoria}/{subcategoria} - {descricao} - R$ {valor}")
    
    # Etapa 6: Verificar se todos os tipos esperados foram gerados
    tipos_esperados = ['Receita - valor base', 'Receita - Venda de produtos', 
                       'Receita - Serviços adicionais', 'Receita - Comissão', 
                       'Despesa - Assistentes']
    
    categorias_encontradas = set()
    for lancamento in lancamentos:
        categorias_encontradas.add(lancamento[4])
    
    logger.info(f"Categorias encontradas: {categorias_encontradas}")
    
    # Fechar conexão
    cursor.close()
    conn.close()
    
    logger.info("Teste concluído com sucesso!")

if __name__ == '__main__':
    main()