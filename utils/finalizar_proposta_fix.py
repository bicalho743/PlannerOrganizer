"""
Módulo para finalização segura de propostas
Este módulo implementa a função finalizar_proposta_sql que utiliza SQL direto
para garantir a finalização correta de propostas.
"""
import os
import logging
import psycopg2
from datetime import datetime, date
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
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

def verificar_funcao_sql_existe(conn=None):
    """Verifica se a função SQL finalizar_proposta existe no banco de dados"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'finalizar_proposta'
            );
        """)
        result = cursor.fetchone()
        
        exists = False
        if result and len(result) > 0:
            exists = result[0]
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return exists
    except Exception as e:
        logger.error(f"Erro ao verificar função SQL: {str(e)}")
        if close_conn and conn:
            conn.close()
        return False

def buscar_proposta(proposta_id: int, conn=None) -> Dict[str, Any]:
    """Busca informações de uma proposta no banco de dados"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return {}
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.id, p.cliente_id, p.usuario_id, p.data_inicio, p.data_proposta,
                p.data_fim, p.valor, p.status, p.status_execucao,
                c.nome as cliente_nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
        """, (proposta_id,))
        
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        
        proposta = {}
        if result:
            proposta = dict(zip(columns, result))
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return proposta
    except Exception as e:
        logger.error(f"Erro ao buscar proposta: {str(e)}")
        if close_conn and conn:
            conn.close()
        return {}

def verificar_lancamento_financeiro_existe(proposta_id: int, conn=None) -> bool:
    """Verifica se já existe um lançamento financeiro para a proposta"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber'
            )
        """, (proposta_id,))
        
        result = cursor.fetchone()
        exists = False
        if result and len(result) > 0:
            exists = result[0]
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return exists
    except Exception as e:
        logger.error(f"Erro ao verificar lançamento financeiro: {str(e)}")
        if close_conn and conn:
            conn.close()
        return False

def criar_lancamento_financeiro(proposta_id: int, proposta: Dict[str, Any], conn=None) -> int:
    """Cria um lançamento financeiro para a proposta finalizada"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return 0
        
    try:
        cursor = conn.cursor()
        data_atual = date.today()
        
        cursor.execute("""
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
        """, (
            f"Proposta #{proposta_id} - {proposta.get('cliente_nome', 'Cliente')}",
            proposta.get('valor', 0),
            data_atual,
            'Serviços de Organização',
            'receita_a_receber',
            'Pendente',
            proposta_id,
            proposta.get('usuario_id', '')
        ))
        
        result = cursor.fetchone()
        lancamento_id = 0
        if result and len(result) > 0:
            lancamento_id = result[0]
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return lancamento_id
    except Exception as e:
        logger.error(f"Erro ao criar lançamento financeiro: {str(e)}")
        if close_conn and conn:
            conn.close()
        return 0

def finalizar_proposta_sql(proposta_id: int, usuario_id: Optional[str] = None) -> bool:
    """
    Finaliza uma proposta utilizando SQL direto para contornar problemas de tipo
    """
    logger.info(f"Iniciando finalização da proposta #{proposta_id} via SQL")
    
    # Verificar se a função SQL existe no banco
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return False
        
    try:
        # Se a função SQL finalizar_proposta existe, usá-la
        if verificar_funcao_sql_existe(conn):
            logger.info("Usando função SQL finalizar_proposta")
            cursor = conn.cursor()
            cursor.execute("SELECT finalizar_proposta(%s)", (proposta_id,))
            result = cursor.fetchone()
            success = False
            if result and len(result) > 0:
                success = result[0]
                
            cursor.close()
            conn.close()
            
            logger.info(f"Proposta #{proposta_id} finalizada com {'sucesso' if success else 'falha'}")
            return success
            
        # Caso contrário, implementar a finalização manualmente
        logger.info("Função SQL não encontrada, implementando finalização manualmente")
        
        # Buscar informações da proposta
        proposta = buscar_proposta(proposta_id, conn)
        if not proposta:
            logger.error(f"Proposta #{proposta_id} não encontrada")
            conn.close()
            return False
            
        # Se usuario_id foi fornecido, verificar se é o proprietário da proposta
        if usuario_id and proposta.get('usuario_id') != usuario_id:
            logger.error(f"Usuário {usuario_id} não é o proprietário da proposta #{proposta_id}")
            conn.close()
            return False
            
        # Atualizar o status da proposta para 'Finalizada'
        data_atual = date.today()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE propostas 
            SET 
                status = 'Finalizada',
                data_fim = %s,
                data_proposta = COALESCE(data_proposta, data_inicio, %s)
            WHERE id = %s
        """, (data_atual, data_atual, proposta_id))
        
        # Verificar se já existe um lançamento financeiro
        if not verificar_lancamento_financeiro_existe(proposta_id, conn):
            # Criar um lançamento financeiro
            lancamento_id = criar_lancamento_financeiro(proposta_id, proposta, conn)
            logger.info(f"Criado lançamento financeiro #{lancamento_id} para a proposta #{proposta_id}")
            
        cursor.close()
        conn.close()
        
        logger.info(f"Proposta #{proposta_id} finalizada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta #{proposta_id}: {str(e)}")
        if conn:
            conn.close()
        return False

def desassociar_propostas_cliente_sql(cliente_id: int) -> int:
    """
    Desassocia propostas de um cliente utilizando SQL direto
    Retorna o número de propostas atualizadas
    """
    logger.info(f"Desassociando propostas do cliente #{cliente_id}")
    
    # Verificar se a função SQL existe no banco
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return 0
        
    try:
        # Se a função SQL desassociar_propostas_cliente existe, usá-la
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'desassociar_propostas_cliente'
            );
        """)
        result = cursor.fetchone()
        func_exists = False
        if result and len(result) > 0:
            func_exists = result[0]
            
        if func_exists:
            logger.info("Usando função SQL desassociar_propostas_cliente")
            cursor.execute("SELECT desassociar_propostas_cliente(%s)", (cliente_id,))
            result = cursor.fetchone()
            count = 0
            if result and len(result) > 0:
                count = result[0]
                
            cursor.close()
            conn.close()
            
            logger.info(f"{count} propostas desassociadas do cliente #{cliente_id}")
            return count
            
        # Caso contrário, implementar a desassociação manualmente
        logger.info("Função SQL não encontrada, implementando desassociação manualmente")
        
        cursor.execute("""
            UPDATE propostas
            SET status = 'Cancelada', 
                status_execucao = 'Cancelada'
            WHERE cliente_id = %s
            AND status NOT IN ('Finalizada', 'Cancelada')
        """, (cliente_id,))
        
        count = cursor.rowcount
        cursor.close()
        conn.close()
        
        logger.info(f"{count} propostas desassociadas do cliente #{cliente_id}")
        return count
    except Exception as e:
        logger.error(f"Erro ao desassociar propostas do cliente #{cliente_id}: {str(e)}")
        if conn:
            conn.close()
        return 0

# Function replacement
def finalizar_proposta_segura(proposta_id: int) -> Dict[str, Any]:
    """Função de compatibilidade para código existente"""
    logger.info(f"Iniciando finalização segura da proposta #{proposta_id}")
    conn = get_db_connection()
    if not conn:
        logger.error("Erro de conexão com banco")
        return {"status": False, "mensagem": "Erro de conexão com banco"}

    try:
        cursor = conn.cursor()

        # Atualizar status da proposta (usando data_fim em vez de data_finalizacao)
        cursor.execute("""
            UPDATE propostas 
            SET status = 'Finalizada',
                data_fim = CURRENT_DATE
            WHERE id = %s
            RETURNING id, valor, usuario_id;
        """, (proposta_id,))

        result = cursor.fetchone()
        if not result:
            logger.error(f"Proposta #{proposta_id} não encontrada")
            return {"status": False, "mensagem": "Proposta não encontrada"}

        proposta_id, valor, usuario_id = result
        logger.info(f"Proposta #{proposta_id} encontrada. Valor: {valor}, Usuario: {usuario_id}")

        # Verificar se já existe um lançamento financeiro para esta proposta
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro 
            WHERE proposta_id = %s AND tipo = 'receita_a_receber'
        """, (proposta_id,))
        
        tem_lancamento = cursor.fetchone()[0] > 0
        
        # Criar lançamento financeiro apenas se não existir
        if not tem_lancamento:
            logger.info(f"Criando lançamento financeiro para proposta #{proposta_id}")
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                VALUES (%s, %s, CURRENT_DATE, 'Serviços de Organização', 'receita_a_receber', 'Pendente', %s, %s)
            """, (f"Proposta #{proposta_id}", valor, proposta_id, usuario_id))
        else:
            logger.info(f"Proposta #{proposta_id} já possui lançamento financeiro, pulando criação")

        conn.commit()
        return {
            "status": True,
            "mensagem": "Proposta finalizada com sucesso",
            "lancamentos": {"gerados": 1}
        }
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta: {str(e)}")
        conn.rollback()
        return {"status": False, "mensagem": f"Erro: {str(e)}"}
    finally:
        if conn:
            conn.close()