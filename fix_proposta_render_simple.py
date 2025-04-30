"""
Script simplificado para resolver problemas de finalização de propostas no Render
Este script deve ser copiado e executado diretamente no console do Render
"""
import os
import psycopg2
from datetime import datetime

def fix_propostas():
    """Corrige problemas de finalização de propostas no Render"""
    # Obter a string de conexão do ambiente
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("Erro: DATABASE_URL não encontrada")
        return
    
    print("Conectando ao banco de dados...")
    conn = None
    try:
        # Conectar ao banco
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Verificando estrutura da tabela propostas...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
        """)
        colunas_propostas = [row[0] for row in cursor.fetchall()]
        print(f"Colunas encontradas: {', '.join(colunas_propostas)}")
        
        # Verificar se já existe trigger de consistência de usuario_id
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
        print("Trigger criado para manter consistência entre propostas e financeiro")

        # Adicionar uma função direta no banco para finalizar propostas
        cursor.execute("""
            CREATE OR REPLACE FUNCTION finalizar_proposta(proposta_id INTEGER)
            RETURNS BOOLEAN AS $$
            DECLARE
                prop RECORD;
                cliente_nome TEXT;
                data_atual DATE := CURRENT_DATE;
                tem_lancamento BOOLEAN;
            BEGIN
                -- Obter dados da proposta
                SELECT p.*, c.nome INTO prop
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = proposta_id;
                
                IF prop IS NULL THEN
                    RAISE NOTICE 'Proposta #% não encontrada', proposta_id;
                    RETURN FALSE;
                END IF;
                
                -- Verificar se já tem lançamento
                SELECT EXISTS(
                    SELECT 1 FROM financeiro
                    WHERE proposta_id = prop.id AND tipo = 'receita_a_receber'
                ) INTO tem_lancamento;
                
                -- Atualizar status e datas
                UPDATE propostas
                SET 
                    status = 'Finalizada',
                    data_finalizacao = data_atual,
                    data_proposta = COALESCE(data_proposta, data_inicio, data_atual)
                WHERE id = proposta_id;
                
                -- Criar lançamento financeiro se não existir
                IF NOT tem_lancamento THEN
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (
                        'Proposta #' || proposta_id || ' - ' || prop.nome,
                        prop.valor::NUMERIC,
                        data_atual,
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        proposta_id,
                        prop.usuario_id
                    );
                END IF;
                
                RETURN TRUE;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Erro ao finalizar proposta: %', SQLERRM;
                    RETURN FALSE;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("Função finalizar_proposta criada com sucesso no banco de dados")
        
        # Criar procedimento para corrigir propostas já finalizadas
        cursor.execute("""
            CREATE OR REPLACE PROCEDURE corrigir_propostas_finalizadas()
            AS $$
            DECLARE
                prop RECORD;
                cliente_nome TEXT;
                tem_lancamento BOOLEAN;
                data_atual DATE := CURRENT_DATE;
            BEGIN
                -- Para cada proposta finalizada
                FOR prop IN (
                    SELECT p.*, c.nome as cliente_nome
                    FROM propostas p
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.status = 'Finalizada'
                )
                LOOP
                    -- Verificar se tem lançamento financeiro
                    SELECT EXISTS(
                        SELECT 1 FROM financeiro
                        WHERE proposta_id = prop.id AND tipo = 'receita_a_receber'
                    ) INTO tem_lancamento;
                    
                    -- Se não tiver lançamento, criar
                    IF NOT tem_lancamento THEN
                        RAISE NOTICE 'Criando lançamento para proposta #% - %', prop.id, prop.cliente_nome;
                        
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                        VALUES (
                            'Proposta #' || prop.id || ' - ' || prop.cliente_nome,
                            prop.valor::NUMERIC,
                            COALESCE(prop.data_finalizacao, data_atual),
                            'Serviços de Organização',
                            'receita_a_receber',
                            'Pendente',
                            prop.id,
                            prop.usuario_id
                        );
                    END IF;
                    
                    -- Garantir que data_finalizacao esteja definida
                    IF prop.data_finalizacao IS NULL THEN
                        RAISE NOTICE 'Atualizando data_finalizacao para proposta #%', prop.id;
                        
                        UPDATE propostas
                        SET data_finalizacao = data_atual
                        WHERE id = prop.id;
                    END IF;
                    
                    -- Garantir que data_proposta esteja definida
                    IF prop.data_proposta IS NULL THEN
                        RAISE NOTICE 'Atualizando data_proposta para proposta #%', prop.id;
                        
                        UPDATE propostas
                        SET data_proposta = COALESCE(prop.data_inicio, data_atual)
                        WHERE id = prop.id;
                    END IF;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("Procedimento corrigir_propostas_finalizadas criado com sucesso")
        
        # Chamar o procedimento para corrigir propostas existentes
        cursor.execute("CALL corrigir_propostas_finalizadas()")
        print("Procedimento executado com sucesso")
        
        # Verificar quantas propostas estão finalizadas e quantas têm lançamentos
        cursor.execute("""
            SELECT COUNT(*) 
            FROM propostas
            WHERE status = 'Finalizada'
        """)
        total_finalizadas = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id)
            FROM propostas p
            JOIN financeiro f ON p.id = f.proposta_id
            WHERE p.status = 'Finalizada' AND f.tipo = 'receita_a_receber'
        """)
        total_com_lancamentos = cursor.fetchone()[0]
        
        print(f"Total de propostas finalizadas: {total_finalizadas}")
        print(f"Propostas finalizadas com lançamentos: {total_com_lancamentos}")
        
        if total_finalizadas == total_com_lancamentos:
            print("✅ Todas as propostas finalizadas têm lançamentos financeiros correspondentes")
        else:
            print(f"⚠️ Há {total_finalizadas - total_com_lancamentos} propostas sem lançamentos financeiros")
        
        print("\nTodas as correções foram aplicadas com sucesso!")
        print("Agora você pode usar a função finalizar_proposta diretamente do SQL para finalizar uma proposta.")
        print("Exemplo: SELECT finalizar_proposta(123); -- onde 123 é o ID da proposta")
        
    except Exception as e:
        print(f"Erro: {str(e)}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("Iniciando script de correção...")
    fix_propostas()
    print("Script concluído!")