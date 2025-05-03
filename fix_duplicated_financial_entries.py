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
            SELECT 
                p.id, 
                p.descricao, 
                c.nome as cliente_nome,
                p.valor,
                COUNT(f.id) as lancamentos_count,
                array_agg(f.id) as lancamento_ids,
                array_agg(f.descricao) as lancamento_descricoes,
                array_agg(f.data) as lancamento_datas
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN financeiro f ON p.id = f.proposta_id
            WHERE p.status = 'Finalizada'
            AND f.tipo = 'receita_a_receber'
            GROUP BY p.id, p.descricao, c.nome, p.valor
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

def padronizar_descricao_lancamento(proposta_id, cliente_nome):
    """Gera uma descrição padronizada para lançamentos financeiros"""
    return f"Proposta #{proposta_id} - {cliente_nome}"

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
            
            # Para cada proposta com lançamentos duplicados, manter apenas um e corrigir o formato
            for proposta_id, descricao, cliente_nome, valor, lancamentos_count, lancamento_ids, lancamento_descricoes, lancamento_datas in duplicates:
                logger.info(f"Proposta #{proposta_id} ({descricao}) tem {lancamentos_count} lançamentos")
                
                # Criar descrição padronizada
                descricao_padrao = padronizar_descricao_lancamento(proposta_id, cliente_nome)
                
                # Decidir qual lançamento manter (preferir o mais antigo)
                # Converter as datas de string para objetos de data para comparação
                datas_lancamentos = []
                for i in range(len(lancamento_datas)):
                    try:
                        datas_lancamentos.append((i, lancamento_datas[i]))
                    except Exception as e:
                        logger.warning(f"Erro ao processar data do lancamento {lancamento_ids[i]}: {str(e)}")
                        datas_lancamentos.append((i, datetime.now().date())) # Fallback para data atual
                
                # Ordenar por data, o mais antigo primeiro
                datas_lancamentos.sort(key=lambda x: x[1])
                
                # Índice do lançamento mais antigo
                idx_principal = datas_lancamentos[0][0] if datas_lancamentos else 0
                
                # ID do lançamento a manter
                id_principal = lancamento_ids[idx_principal]
                
                # Atualizar descrição do lançamento principal para o formato padronizado
                cursor.execute("""
                    UPDATE financeiro
                    SET descricao = %s
                    WHERE id = %s
                    RETURNING id;
                """, (descricao_padrao, id_principal))
                
                # Remover os lançamentos duplicados (todos exceto o principal)
                for i, lancamento_id in enumerate(lancamento_ids):
                    if i != idx_principal:
                        logger.info(f"Removendo lançamento duplicado ID={lancamento_id} com descrição '{lancamento_descricoes[i]}'")
                        cursor.execute("DELETE FROM financeiro WHERE id = %s;", (lancamento_id,))
                
                # Log do lançamento mantido e atualizado
                logger.info(f"Mantido e padronizado lançamento ID={id_principal} com nova descrição '{descricao_padrao}'")
        else:
            logger.info("Nenhuma proposta com lançamentos duplicados encontrada")
        
        # Atualizar função SQL para verificar existência de lançamentos por proposta_id e tipo
        cursor.execute("""
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
        """)
        
        # Criar função para padronizar descrições de lançamentos
        cursor.execute("""
            CREATE OR REPLACE FUNCTION gerar_descricao_lancamento(proposta_id_param INTEGER)
            RETURNS TEXT AS $$
            DECLARE
                cliente_nome TEXT;
                descricao_padrao TEXT;
            BEGIN
                -- Obter nome do cliente da proposta
                SELECT c.nome INTO cliente_nome
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = proposta_id_param;
                
                -- Gerar descrição padronizada
                descricao_padrao := 'Proposta #' || proposta_id_param || ' - ' || COALESCE(cliente_nome, 'Cliente');
                
                RETURN descricao_padrao;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Criar trigger para garantir que novos lançamentos usem a descrição padronizada
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
        logger.info("Funções e triggers de padronização de lançamentos criados com sucesso")
        
        return True, "Correção aplicada com sucesso: lançamentos padronizados e funções atualizadas"
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