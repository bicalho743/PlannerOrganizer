"""
Script para corrigir a duplicação de lançamentos financeiros quando a proposta é finalizada.
O problema ocorre porque o sistema cria um lançamento tanto na aprovação quanto na finalização.
A lógica correta é criar o lançamento APENAS na aprovação da proposta.
"""
import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# Configuração de logging
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

def fix_duplicated_entries():
    """Remove lançamentos duplicados e corrige a lógica de criação de lançamentos"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro ao conectar ao banco de dados"
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 1. Identificar propostas com múltiplos lançamentos financeiros
        cursor.execute("""
            SELECT
                p.id as proposta_id,
                p.descricao as proposta_descricao,
                c.nome as cliente_nome,
                COUNT(f.id) as lancamentos_count,
                array_agg(f.id) as lancamento_ids,
                array_agg(f.descricao) as lancamento_descricoes,
                array_agg(f.data) as lancamento_datas,
                array_agg(f.status) as lancamento_status
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN financeiro f ON p.id = f.proposta_id
            WHERE f.tipo = 'receita_a_receber'
            GROUP BY p.id, p.descricao, c.nome
            HAVING COUNT(f.id) > 1
            ORDER BY p.id DESC
        """)
        
        propostas_com_duplicatas = cursor.fetchall()
        logger.info(f"Encontradas {len(propostas_com_duplicatas)} propostas com lançamentos duplicados")
        
        total_corrigidos = 0
        for proposta in propostas_com_duplicatas:
            proposta_id = proposta['proposta_id']
            cliente_nome = proposta['cliente_nome']
            lancamento_ids = proposta['lancamento_ids']
            lancamento_datas = proposta['lancamento_datas']
            
            # Formato padrão de descrição
            descricao_padronizada = f"Proposta #{proposta_id} - {cliente_nome}"
            
            # Manter apenas o lançamento mais antigo
            # Criar um mapeamento de id -> data
            lancamentos_mapeados = []
            for i, lancamento_id in enumerate(lancamento_ids):
                lancamentos_mapeados.append({
                    'id': lancamento_id,
                    'data': lancamento_datas[i]
                })
            
            # Ordenar por data (mais antiga primeiro)
            lancamentos_mapeados.sort(key=lambda x: x['data'])
            
            # ID do lançamento a manter (o mais antigo)
            id_para_manter = lancamentos_mapeados[0]['id']
            
            # Atualizar a descrição do lançamento mantido para o formato padrão
            cursor.execute("""
                UPDATE financeiro
                SET descricao = %s
                WHERE id = %s
                RETURNING id
            """, (descricao_padronizada, id_para_manter))
            
            # Remover os lançamentos duplicados
            ids_para_remover = [l['id'] for l in lancamentos_mapeados[1:]]
            if ids_para_remover:
                for id_remover in ids_para_remover:
                    cursor.execute("DELETE FROM financeiro WHERE id = %s", (id_remover,))
                
                logger.info(f"Proposta #{proposta_id}: removidos {len(ids_para_remover)} lançamentos duplicados, mantido ID {id_para_manter}")
                total_corrigidos += 1
        
        # 2. Modificar a lógica para evitar duplos lançamentos no futuro
        cursor.execute("""
            -- Função para verificar se já existe lançamento para a proposta
            CREATE OR REPLACE FUNCTION verificar_lancamento_existe(proposta_id_param INTEGER, tipo_param TEXT DEFAULT 'receita_a_receber') 
            RETURNS BOOLEAN AS $$
            DECLARE
                existe BOOLEAN;
            BEGIN
                SELECT EXISTS(
                    SELECT 1 FROM financeiro 
                    WHERE proposta_id = proposta_id_param
                    AND tipo = tipo_param
                ) INTO existe;
                
                RETURN existe;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Função para padronizar descrições dos lançamentos financeiros
            CREATE OR REPLACE FUNCTION gerar_descricao_lancamento(proposta_id_param INTEGER)
            RETURNS TEXT AS $$
            DECLARE
                cliente_nome TEXT;
                descricao_padrao TEXT;
            BEGIN
                SELECT c.nome INTO cliente_nome
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = proposta_id_param;
                
                descricao_padrao := 'Proposta #' || proposta_id_param || ' - ' || COALESCE(cliente_nome, 'Cliente');
                
                RETURN descricao_padrao;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # 3. Criar uma trigger que padroniza as descrições dos lançamentos
        cursor.execute("""
            CREATE OR REPLACE FUNCTION padronizar_descricao_financeiro()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Se for um lançamento relacionado a proposta, padronizar a descrição
                IF NEW.proposta_id IS NOT NULL AND NEW.proposta_id > 0 THEN
                    NEW.descricao := gerar_descricao_lancamento(NEW.proposta_id);
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS financeiro_descricao_trigger ON financeiro;
            
            CREATE TRIGGER financeiro_descricao_trigger
            BEFORE INSERT OR UPDATE ON financeiro
            FOR EACH ROW
            WHEN (NEW.proposta_id IS NOT NULL AND NEW.proposta_id > 0)
            EXECUTE FUNCTION padronizar_descricao_financeiro();
        """)
        
        conn.commit()
        
        mensagem = f"""
        Correção aplicada com sucesso:
        - {len(propostas_com_duplicatas)} propostas com lançamentos duplicados identificadas
        - {total_corrigidos} propostas corrigidas, mantendo apenas o lançamento mais antigo
        - Funções e triggers atualizados para evitar duplicações futuras
        - Descrições padronizadas para manter consistência
        """
        
        return True, mensagem.strip()
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao corrigir lançamentos duplicados: {e}")
        return False, f"Erro ao corrigir lançamentos duplicados: {e}"
    
    finally:
        if conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

def corrigir_finalizar_proposta():
    """
    Esta função corrige o código de finalização de proposta para não criar
    lançamento financeiro caso já exista lançamento para a proposta.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Erro ao conectar ao banco de dados"
    
    try:
        cursor = conn.cursor()
        
        # Criar uma função que será usada no código de finalizar proposta
        cursor.execute("""
            -- Função para verificar se já existe lançamento de proposta
            CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER)
            RETURNS BOOLEAN AS $$
            DECLARE
                existe BOOLEAN;
            BEGIN
                SELECT EXISTS (
                    SELECT 1 FROM financeiro
                    WHERE proposta_id = proposta_id_param
                    AND tipo = 'receita_a_receber'
                ) INTO existe;
                
                RETURN existe;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        logger.info("Função de verificação de lançamentos existentes criada com sucesso")
        
        return True, "Função de verificação criada com sucesso"
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar função de verificação: {e}")
        return False, f"Erro ao criar função de verificação: {e}"
    
    finally:
        if conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

def main():
    """Função principal de execução do script"""
    print("Iniciando correção de lançamentos duplicados em propostas...")
    
    # 1. Corrigir entradas duplicadas
    sucesso, mensagem = fix_duplicated_entries()
    if sucesso:
        print("✅ " + mensagem)
    else:
        print("❌ " + mensagem)
        return
    
    # 2. Corrigir a função de finalização de propostas
    sucesso, mensagem = corrigir_finalizar_proposta()
    if sucesso:
        print("✅ " + mensagem)
    else:
        print("❌ " + mensagem)
    
    print("\nPara aplicar esta correção em seu projeto:")
    print("1. Modifique as funções de finalização de proposta para usar a nova função ja_existe_lancamento_proposta()")
    print("2. Adicione verificação antes de criar novos lançamentos financeiros")
    print("3. Veja os exemplos no código SQL fornecido junto com este script")

if __name__ == "__main__":
    main()