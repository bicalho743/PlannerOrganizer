"""
Script completo para corrigir problemas de tipo e relacionamentos no Render
Este script aborda:
1. Finalização de propostas
2. Exclusão de clientes
3. Exclusão de propostas
4. Correção de tipos de dados
"""
import os
import psycopg2
from datetime import datetime

def fix_database_type_errors():
    """Corrige problemas de tipos e relacionamentos no banco de dados"""
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
        
        print("1. Verificando e corrigindo estrutura das tabelas...")
        # Verificar estrutura das tabelas
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
            ORDER BY column_name
        """)
        colunas_propostas = cursor.fetchall()
        print("Estrutura da tabela propostas:")
        for col in colunas_propostas:
            print(f"  - {col[0]}: {col[1]}")
            
        # Verificar estrutura da tabela clientes
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'clientes'
            ORDER BY column_name
        """)
        colunas_clientes = cursor.fetchall()
        print("\nEstrutura da tabela clientes:")
        for col in colunas_clientes:
            print(f"  - {col[0]}: {col[1]}")
            
        # Verificar estrutura da tabela financeiro
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
            ORDER BY column_name
        """)
        colunas_financeiro = cursor.fetchall()
        print("\nEstrutura da tabela financeiro:")
        for col in colunas_financeiro:
            print(f"  - {col[0]}: {col[1]}")
        
        # Verificar clientes com dados inconsistentes
        print("\n2. Verificando clientes com dados inconsistentes...")
        cursor.execute("""
            SELECT id, nome, email, telefone 
            FROM clientes 
            WHERE 
                (telefone ~ '[a-zA-Z]' OR telefone IS NULL) OR
                (email IS NULL) OR
                (nome IS NULL)
            LIMIT 10
        """)
        clientes_problematicos = cursor.fetchall()
        if clientes_problematicos:
            print(f"Encontrados {len(clientes_problematicos)} clientes com dados inconsistentes:")
            for c in clientes_problematicos:
                print(f"  - ID: {c[0]}, Nome: {c[1]}, Email: {c[2]}, Telefone: {c[3]}")
                
            # Corrigir valores NULL e telefones com letras
            print("Corrigindo dados de clientes...")
            cursor.execute("""
                UPDATE clientes
                SET 
                    telefone = CASE 
                        WHEN telefone IS NULL THEN '0000000000'
                        WHEN telefone ~ '[a-zA-Z]' THEN regexp_replace(telefone, '[^0-9]', '', 'g')
                        ELSE telefone
                    END,
                    email = COALESCE(email, 'sem_email@example.com'),
                    nome = COALESCE(nome, 'Cliente Sem Nome')
                WHERE 
                    telefone IS NULL OR 
                    telefone ~ '[a-zA-Z]' OR
                    email IS NULL OR
                    nome IS NULL
            """)
            print("Dados de clientes corrigidos com sucesso!")
        else:
            print("Nenhum cliente com dados inconsistentes encontrado.")
        
        # Verificar propostas com valores inconsistentes
        print("\n3. Verificando propostas com valores inconsistentes...")
        cursor.execute("""
            SELECT id, descricao, valor, status, cliente_id 
            FROM propostas 
            WHERE valor IS NULL OR valor::text ~ '[a-zA-Z]'
            LIMIT 10
        """)
        propostas_problematicas = cursor.fetchall()
        if propostas_problematicas:
            print(f"Encontradas {len(propostas_problematicas)} propostas com valores inconsistentes:")
            for p in propostas_problematicas:
                print(f"  - ID: {p[0]}, Título: {p[1]}, Valor: {p[2]}, Status: {p[3]}, Cliente: {p[4]}")
                
            # Corrigir valores de propostas
            print("Corrigindo valores de propostas...")
            cursor.execute("""
                UPDATE propostas
                SET valor = CASE 
                    WHEN valor IS NULL THEN '0' 
                    WHEN valor::text ~ '[a-zA-Z]' THEN '0'
                    ELSE valor::text
                END::numeric
                WHERE valor IS NULL OR valor::text ~ '[a-zA-Z]'
            """)
            print("Valores de propostas corrigidos com sucesso!")
        else:
            print("Nenhuma proposta com valor inconsistente encontrada.")
                
        # Função para finalizar propostas corretamente
        print("\n4. Criando função SQL para finalizar propostas...")
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
                    SELECT 1 FROM financeiro f
                    WHERE f.proposta_id = prop.id AND f.tipo = 'receita_a_receber'
                ) INTO tem_lancamento;
                
                -- Atualizar status e datas
                -- Atualizar status e datas (sem data_finalizacao que não existe no schema)
                UPDATE propostas p
                SET 
                    status = 'Finalizada',
                    data_fim = data_atual, -- Usando data_fim em vez de data_finalizacao
                    data_proposta = COALESCE(p.data_proposta, p.data_inicio, data_atual)
                WHERE p.id = proposta_id;
                
                -- Criar lançamento financeiro se não existir
                IF NOT tem_lancamento THEN
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (
                        'Proposta #' || proposta_id || ' - ' || prop.nome,
                        CASE WHEN prop.valor IS NULL THEN 0 ELSE prop.valor END,
                        data_atual,
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        prop.id,  -- Usando prop.id em vez de proposta_id para evitar ambiguidade
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
        print("Função para finalizar propostas criada com sucesso!")

        # Criar função para desassociar propostas de um cliente        
        print("\n5. Criando função para excluir clientes com propostas associadas...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION desassociar_propostas_cliente(cliente_id_param INTEGER)
            RETURNS INTEGER AS $$
            DECLARE
                total_propostas INTEGER := 0;
            BEGIN
                -- Transferir as propostas para um cliente especial "Cliente Excluído"
                -- Primeiro, verificar se o cliente "Cliente Excluído" existe, senão criar
                IF NOT EXISTS (SELECT 1 FROM clientes WHERE nome = 'Cliente Excluído') THEN
                    INSERT INTO clientes (nome, email, telefone, usuario_id)
                    SELECT 'Cliente Excluído', 'excluido@example.com', '0000000000', usuario_id
                    FROM clientes
                    WHERE id = cliente_id_param;
                END IF;
                
                -- Obter o ID do cliente "Cliente Excluído"
                WITH cliente_excluido AS (
                    SELECT id FROM clientes WHERE nome = 'Cliente Excluído' LIMIT 1
                )
                -- Atualizar as propostas para o cliente "Cliente Excluído"
                UPDATE propostas p
                SET cliente_id = (SELECT id FROM cliente_excluido)
                WHERE p.cliente_id = cliente_id_param
                RETURNING id INTO total_propostas;
                
                RETURN total_propostas;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("Função para desassociar propostas criada com sucesso!")
        
        # Trigger para manter relação entre proposta e financeiro
        print("\n6. Criando trigger para consistência entre tabelas...")
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
        print("Trigger para manter consistência criado com sucesso!")
        
        # Corrigir propostas finalizadas sem lançamento
        print("\n7. Corrigindo propostas finalizadas sem lançamentos...")
        cursor.execute("""
            CREATE OR REPLACE PROCEDURE corrigir_propostas_finalizadas()
            AS $$
            DECLARE
                prop RECORD;
                cliente_nome TEXT;
                tem_lancamento BOOLEAN;
                data_atual DATE := CURRENT_DATE;
                contador INTEGER := 0;
            BEGIN
                -- Para cada proposta finalizada
                FOR prop IN (
                    SELECT p.*, c.nome as cliente_nome
                    FROM propostas p
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.status = 'Finalizada'
                )
                LOOP
                    contador := contador + 1;
                    -- Verificar se tem lançamento financeiro
                    SELECT EXISTS(
                        SELECT 1 FROM financeiro f
                        WHERE f.proposta_id = prop.id AND f.tipo = 'receita_a_receber'
                    ) INTO tem_lancamento;
                    
                    -- Se não tiver lançamento, criar
                    IF NOT tem_lancamento THEN
                        RAISE NOTICE 'Criando lançamento para proposta #% - %', prop.id, prop.cliente_nome;
                        
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                        VALUES (
                            'Proposta #' || prop.id || ' - ' || prop.cliente_nome,
                            CASE WHEN prop.valor IS NULL OR prop.valor::text ~ '[a-zA-Z]' THEN 0 ELSE prop.valor END,
                            COALESCE(prop.data_fim, data_atual),
                            'Serviços de Organização',
                            'receita_a_receber',
                            'Pendente',
                            prop.id,
                            prop.usuario_id
                        );
                    END IF;
                    
                    -- Garantir que data_fim esteja definida (substitui data_finalizacao)
                    IF prop.data_fim IS NULL THEN
                        RAISE NOTICE 'Atualizando data_fim para proposta #%', prop.id;
                        
                        UPDATE propostas
                        SET data_fim = data_atual
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
                
                RAISE NOTICE 'Total de propostas processadas: %', contador;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("Procedimento para corrigir propostas criado com sucesso!")
        
        # Executar a correção
        print("\nExecutando correção de propostas finalizadas...")
        cursor.execute("CALL corrigir_propostas_finalizadas()")
        
        # Estatísticas finais
        print("\n8. Verificando estatísticas finais...")
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM propostas")
        total_propostas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM propostas WHERE status = 'Finalizada'")
        total_finalizadas = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id)
            FROM propostas p
            JOIN financeiro f ON p.id = f.proposta_id
            WHERE p.status = 'Finalizada' AND f.tipo = 'receita_a_receber'
        """)
        total_com_lancamentos = cursor.fetchone()[0]
        
        print(f"Total de clientes: {total_clientes}")
        print(f"Total de propostas: {total_propostas}")
        print(f"Total de propostas finalizadas: {total_finalizadas}")
        print(f"Propostas finalizadas com lançamentos: {total_com_lancamentos}")
        
        print("\n====== CORREÇÃO CONCLUÍDA COM SUCESSO ======")
        print("""
INSTRUÇÕES DE USO:

1. Para finalizar uma proposta, execute no console SQL:
   SELECT finalizar_proposta(ID_DA_PROPOSTA);
   
2. Para excluir um cliente que tem propostas associadas:
   SELECT desassociar_propostas_cliente(ID_DO_CLIENTE);
   -- Em seguida, exclua o cliente normalmente pela interface
   
3. Todas as propostas finalizadas já foram corrigidas e devem ter lançamentos financeiros.

4. Correções aplicadas:
   - Valores inconsistentes nas propostas foram normalizados
   - Dados de clientes com valores nulos foram preenchidos
   - Telefones com formato inválido foram corrigidos
   - Trigger para manter a consistência entre tabelas foi criado
        """)
        
    except Exception as e:
        print(f"Erro: {str(e)}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("Iniciando script de correção geral...")
    fix_database_type_errors()
    print("Script concluído!")