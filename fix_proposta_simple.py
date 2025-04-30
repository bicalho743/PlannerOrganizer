"""
Script simples para corrigir o erro 'finalizar_proposta_segura is not defined'
Este script cria a função SQL necessária no banco de dados e pode ser executado diretamente
no shell do Render.
"""
import os
import psycopg2

def fix_database():
    """Corrige os problemas no banco de dados do Render"""
    print("Iniciando correção para finalizar_proposta_segura...")
    
    # Conexão com o banco de dados
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERRO: Variável de ambiente DATABASE_URL não encontrada")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Verificar se a função já existe
        cursor.execute("SELECT EXISTS(SELECT * FROM pg_proc WHERE proname = 'finalizar_proposta');")
        function_exists = cursor.fetchone()[0]
        
        if function_exists:
            print("A função 'finalizar_proposta' já existe no banco de dados.")
        else:
            # Criar a função SQL finalizar_proposta
            sql_function = """
            CREATE OR REPLACE FUNCTION finalizar_proposta(proposta_id_param INTEGER) 
            RETURNS BOOLEAN AS $$
            DECLARE
                v_finalizada BOOLEAN;
                v_valor NUMERIC;
                v_forma_pagamento TEXT;
                v_cliente_id INTEGER;
                v_data_inicio DATE;
                v_usuario_id TEXT;
                v_categoria TEXT;
                v_descricao TEXT;
            BEGIN
                -- Verificar se a proposta já está finalizada
                SELECT (status = 'Finalizada') INTO v_finalizada 
                FROM propostas 
                WHERE id = proposta_id_param;
                
                IF v_finalizada THEN
                    RAISE NOTICE 'Proposta % já está finalizada', proposta_id_param;
                    RETURN TRUE;
                END IF;
                
                -- Obter dados da proposta
                SELECT 
                    valor_total, 
                    COALESCE(forma_pagamento, 'Não informada'),
                    cliente_id,
                    COALESCE(data_inicio, CURRENT_DATE),
                    usuario_id,
                    CONCAT('Proposta #', id, ' - ', COALESCE(nome_cliente, 'Cliente'))
                INTO 
                    v_valor, 
                    v_forma_pagamento,
                    v_cliente_id,
                    v_data_inicio,
                    v_usuario_id,
                    v_descricao
                FROM propostas 
                WHERE id = proposta_id_param;
                
                -- Definir categoria para o lançamento financeiro
                v_categoria := 'Serviços de Organização';
                
                -- Atualizar o status da proposta para Finalizada
                UPDATE propostas 
                SET 
                    status = 'Finalizada',
                    data_fim = CURRENT_DATE
                WHERE id = proposta_id_param;
                
                -- Inserir lançamento financeiro (receita)
                INSERT INTO financeiro (
                    descricao, 
                    valor, 
                    data, 
                    categoria, 
                    tipo, 
                    status, 
                    proposta_id,
                    usuario_id
                ) VALUES (
                    v_descricao, 
                    v_valor, 
                    v_data_inicio, 
                    v_categoria, 
                    'Receita', 
                    'Pendente', 
                    proposta_id_param,
                    v_usuario_id
                );
                
                RAISE NOTICE 'Proposta % finalizada com sucesso', proposta_id_param;
                RETURN TRUE;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Erro ao finalizar proposta %: %', proposta_id_param, SQLERRM;
                    RETURN FALSE;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            cursor.execute(sql_function)
            
            # Criar um wrapper Python para finalizar_proposta_segura
            sql_wrapper = """
            CREATE OR REPLACE FUNCTION finalizar_proposta_segura(proposta_id_param INTEGER) 
            RETURNS BOOLEAN AS $$
            BEGIN
                RETURN finalizar_proposta(proposta_id_param);
            END;
            $$ LANGUAGE plpgsql;
            """
            cursor.execute(sql_wrapper)
            
            # Criar um trigger para manter consistência
            create_trigger = """
            CREATE OR REPLACE FUNCTION atualizar_usuario_id_financeiro() RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.proposta_id IS NOT NULL AND (NEW.usuario_id IS NULL OR NEW.usuario_id = '') THEN
                    NEW.usuario_id := (SELECT usuario_id FROM propostas WHERE id = NEW.proposta_id);
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS financeiro_usuario_id_trigger ON financeiro;
            
            CREATE TRIGGER financeiro_usuario_id_trigger
            BEFORE INSERT OR UPDATE ON financeiro
            FOR EACH ROW
            EXECUTE FUNCTION atualizar_usuario_id_financeiro();
            """
            cursor.execute(create_trigger)
            
            conn.commit()
            print("Função SQL 'finalizar_proposta' e wrapper 'finalizar_proposta_segura' criados com sucesso.")
        
        # Verificar se a função está funcionando
        print("\nTestando funções criadas no banco de dados...")
        cursor.execute("SELECT proname FROM pg_proc WHERE proname LIKE 'finalizar_proposta%';")
        functions = cursor.fetchall()
        
        print(f"Funções disponíveis: {', '.join([f[0] for f in functions])}")
        
        print("\nCORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("Agora você pode finalizar propostas usando a interface ou via SQL com:")
        print("SELECT finalizar_proposta(ID_DA_PROPOSTA);")
        print("\nReinicie o serviço no Render para aplicar todas as alterações.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERRO ao corrigir banco de dados: {str(e)}")
        return False

if __name__ == "__main__":
    fix_database()