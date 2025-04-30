"""
Script para corrigir problemas de tipos de dados no PostgreSQL no ambiente Render
Este script deve ser executado no ambiente Render para corrigir problemas com
finalização de propostas e inconsistências em lançamentos financeiros.
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_message(message, level='info'):
    """Registra uma mensagem no log e imprime no console"""
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    if level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'warning':
        logger.warning(message)

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        log_message("Variável de ambiente DATABASE_URL não encontrada", 'error')
        return None
        
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        log_message(f"Erro ao conectar ao banco de dados: {str(e)}", 'error')
        return None

def check_function_exists(conn, function_name):
    """Verifica se uma função específica já existe no banco de dados"""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = '{function_name}'
            );
        """)
        result = cursor.fetchone()
        exists = False
        if result and len(result) > 0:
            exists = result[0]
        return exists
    except Exception as e:
        log_message(f"Erro ao verificar função {function_name}: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def check_trigger_exists(conn, trigger_name):
    """Verifica se um trigger específico já existe no banco de dados"""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM pg_trigger
                WHERE tgname = '{trigger_name}'
            );
        """)
        result = cursor.fetchone()
        exists = False
        if result and len(result) > 0:
            exists = result[0]
        return exists
    except Exception as e:
        log_message(f"Erro ao verificar trigger {trigger_name}: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def create_finalizar_proposta_function(conn):
    """Cria ou atualiza a função finalizar_proposta no banco de dados"""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE OR REPLACE FUNCTION finalizar_proposta(proposta_id INTEGER)
            RETURNS BOOLEAN AS $$
            DECLARE
                v_proposta RECORD;
                v_lancamento_id INTEGER;
                v_data_atual DATE;
            BEGIN
                -- Obter informações da proposta
                SELECT p.*, c.nome as cliente_nome 
                INTO v_proposta
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = proposta_id;
                
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Proposta % não encontrada', proposta_id;
                    RETURN FALSE;
                END IF;
                
                -- Definir data atual
                v_data_atual := CURRENT_DATE;
                
                -- Atualizar proposta
                UPDATE propostas 
                SET 
                    status = 'Finalizada',
                    data_finalizacao = v_data_atual,
                    data_proposta = COALESCE(data_proposta, data_inicio, v_data_atual)
                WHERE id = proposta_id;
                
                -- Verificar se já existe lançamento financeiro
                PERFORM id FROM financeiro 
                WHERE proposta_id = proposta_id AND tipo = 'receita_a_receber';
                
                IF NOT FOUND THEN
                    -- Criar lançamento financeiro
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (
                        'Proposta #' || proposta_id || ' - ' || v_proposta.cliente_nome,
                        v_proposta.valor,
                        v_data_atual,
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        proposta_id,
                        v_proposta.usuario_id
                    )
                    RETURNING id INTO v_lancamento_id;
                END IF;
                
                RETURN TRUE;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE WARNING 'Erro ao finalizar proposta %: %', proposta_id, SQLERRM;
                    RETURN FALSE;
            END;
            $$ LANGUAGE plpgsql;
        """)
        log_message("Função finalizar_proposta criada com sucesso")
        return True
    except Exception as e:
        log_message(f"Erro ao criar função finalizar_proposta: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def create_desassociar_propostas_cliente_function(conn):
    """Cria ou atualiza a função desassociar_propostas_cliente no banco de dados"""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE OR REPLACE FUNCTION desassociar_propostas_cliente(cliente_id INTEGER)
            RETURNS INTEGER AS $$
            DECLARE
                propostas_atualizadas INTEGER := 0;
            BEGIN
                -- Atualizar status das propostas para 'Cancelada'
                UPDATE propostas
                SET status = 'Cancelada', 
                    status_execucao = 'Cancelada'
                WHERE cliente_id = cliente_id
                AND status NOT IN ('Finalizada', 'Cancelada');
                
                GET DIAGNOSTICS propostas_atualizadas = ROW_COUNT;
                
                RETURN propostas_atualizadas;
            END;
            $$ LANGUAGE plpgsql;
        """)
        log_message("Função desassociar_propostas_cliente criada com sucesso")
        return True
    except Exception as e:
        log_message(f"Erro ao criar função desassociar_propostas_cliente: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def create_atualizar_usuario_id_function_and_trigger(conn):
    """Cria a função e trigger para manter usuario_id consistente na tabela financeiro"""
    cursor = None
    try:
        cursor = conn.cursor()
        # Criar a função para o trigger
        cursor.execute("""
            CREATE OR REPLACE FUNCTION atualizar_usuario_id_financeiro()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Se usuario_id estiver vazio mas proposta_id estiver preenchido
                IF (NEW.usuario_id IS NULL OR NEW.usuario_id = '') AND NEW.proposta_id IS NOT NULL THEN
                    -- Preencher usuario_id do financeiro com usuario_id da proposta
                    NEW.usuario_id := (SELECT usuario_id FROM propostas WHERE id = NEW.proposta_id);
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Verificar se o trigger já existe e criar se não existir
        if not check_trigger_exists(conn, 'atualizar_usuario_id_financeiro_trigger'):
            cursor.execute("""
                CREATE TRIGGER atualizar_usuario_id_financeiro_trigger
                BEFORE INSERT OR UPDATE ON financeiro
                FOR EACH ROW
                EXECUTE PROCEDURE atualizar_usuario_id_financeiro();
            """)
        
        log_message("Função e trigger atualizar_usuario_id_financeiro criados com sucesso")
        return True
    except Exception as e:
        log_message(f"Erro ao criar função e trigger atualizar_usuario_id_financeiro: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def corrigir_inconsistencias_valores(conn):
    """Corrige inconsistências de valores nas tabelas propostas e financeiro"""
    cursor = None
    try:
        cursor = conn.cursor()
        # Corrigir valores vazios em propostas.valor
        cursor.execute("""
            UPDATE propostas 
            SET valor = 0 
            WHERE valor IS NULL OR valor = '';
        """)
        
        # Corrigir valores vazios em financeiro.valor
        cursor.execute("""
            UPDATE financeiro 
            SET valor = 0 
            WHERE valor IS NULL OR valor = '';
        """)
        
        # Corrigir valores vazios em usuario_id
        cursor.execute("""
            UPDATE financeiro f
            SET usuario_id = (SELECT p.usuario_id FROM propostas p WHERE p.id = f.proposta_id)
            WHERE (f.usuario_id IS NULL OR f.usuario_id = '') AND f.proposta_id IS NOT NULL;
        """)
        
        log_message("Correção de inconsistências de valores realizada com sucesso")
        return True
    except Exception as e:
        log_message(f"Erro ao corrigir inconsistências de valores: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def corrigir_datas_propostas(conn):
    """Corrige datas inconsistentes nas propostas"""
    cursor = None
    try:
        cursor = conn.cursor()
        # Corrigir propostas sem data_proposta
        cursor.execute("""
            UPDATE propostas 
            SET data_proposta = COALESCE(data_inicio, data_finalizacao, CURRENT_DATE)
            WHERE data_proposta IS NULL;
        """)
        
        log_message("Correção de datas em propostas realizada com sucesso")
        return True
    except Exception as e:
        log_message(f"Erro ao corrigir datas em propostas: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def corrigir_categorias_financeiro(conn):
    """Corrige categorias obsoletas na tabela financeiro"""
    cursor = None
    try:
        cursor = conn.cursor()
        # Atualizar categoria 'Propostas' para 'Serviços de Organização'
        cursor.execute("""
            UPDATE financeiro 
            SET categoria = 'Serviços de Organização'
            WHERE categoria = 'Propostas';
        """)
        
        log_message("Correção de categorias em financeiro realizada com sucesso")
        return True
    except Exception as e:
        log_message(f"Erro ao corrigir categorias em financeiro: {str(e)}", 'error')
        return False
    finally:
        if cursor:
            cursor.close()

def main():
    """Função principal que aplica todas as correções"""
    log_message("\n" + "="*50 + "\nINICIANDO CORREÇÕES NO BANCO DE DADOS\n" + "="*50)
    
    # Obter conexão com o banco de dados
    conn = get_db_connection()
    if not conn:
        log_message("Não foi possível estabelecer conexão com o banco de dados", 'error')
        return False
    
    try:
        # 1. Criar ou atualizar função finalizar_proposta
        log_message("Criando função finalizar_proposta...")
        create_finalizar_proposta_function(conn)
        
        # 2. Criar ou atualizar função desassociar_propostas_cliente
        log_message("Criando função desassociar_propostas_cliente...")
        create_desassociar_propostas_cliente_function(conn)
        
        # 3. Criar ou atualizar função e trigger para atualizar usuario_id em financeiro
        log_message("Criando função e trigger para atualizar usuario_id...")
        create_atualizar_usuario_id_function_and_trigger(conn)
        
        # 4. Corrigir inconsistências de valores
        log_message("Corrigindo inconsistências de valores...")
        corrigir_inconsistencias_valores(conn)
        
        # 5. Corrigir datas em propostas
        log_message("Corrigindo datas em propostas...")
        corrigir_datas_propostas(conn)
        
        # 6. Corrigir categorias em financeiro
        log_message("Corrigindo categorias em financeiro...")
        corrigir_categorias_financeiro(conn)
        
        log_message("\n" + "="*50 + "\nCORREÇÕES APLICADAS COM SUCESSO\n" + "="*50)
        return True
    except Exception as e:
        log_message(f"Erro ao aplicar correções: {str(e)}", 'error')
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()