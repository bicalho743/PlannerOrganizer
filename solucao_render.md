# Solução para o problema `'finalizar_proposta_segura' is not defined`

Este documento explica como resolver o problema de função não definida que ocorre no Render, especificamente o erro:
`name 'finalizar_proposta_segura' is not defined` ou `name 'finalizar_proposta_seguro' is not defined`.

## O problema

O erro ocorre porque:

1. O código está chamando uma função chamada `finalizar_proposta_seguro` (com "o" no final)
2. A função definida no sistema é `finalizar_proposta_segura` (com "a" no final)
3. Ou ambas as funções não existem no banco de dados

## A solução (duas opções)

### OPÇÃO 1: Script Python

1. Faça upload do arquivo `utils/finalizar_proposta_fix.py` para seu projeto no Render
2. Execute o script `fix_proposta_simple.py` no console do Render

```python
import os
import psycopg2

def fix_database():
    """Corrige os problemas no banco de dados do Render"""
    # Conexão com o banco de dados
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
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
    
    # Criar wrappers para ambas variações do nome da função
    sql_wrapper1 = """
    CREATE OR REPLACE FUNCTION finalizar_proposta_segura(proposta_id_param INTEGER) 
    RETURNS BOOLEAN AS $$
    BEGIN
        RETURN finalizar_proposta(proposta_id_param);
    END;
    $$ LANGUAGE plpgsql;
    """
    cursor.execute(sql_wrapper1)
    
    sql_wrapper2 = """
    CREATE OR REPLACE FUNCTION finalizar_proposta_seguro(proposta_id_param INTEGER) 
    RETURNS BOOLEAN AS $$
    BEGIN
        RETURN finalizar_proposta(proposta_id_param);
    END;
    $$ LANGUAGE plpgsql;
    """
    cursor.execute(sql_wrapper2)
    
    # Criar trigger para consistência de dados
    sql_trigger = """
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
    cursor.execute(sql_trigger)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("CORREÇÃO CONCLUÍDA COM SUCESSO!")

# Executar a função
fix_database()
```

### OPÇÃO 2: SQL Direto

1. Acesse o console SQL do seu banco de dados no Render ou via DBeaver
2. Execute o seguinte SQL:

```sql
-- Função principal para finalizar proposta
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

-- Função auxilar finalizar_proposta_segura (com 'a' no final)
CREATE OR REPLACE FUNCTION finalizar_proposta_segura(proposta_id_param INTEGER) 
RETURNS BOOLEAN AS $$
BEGIN
    RETURN finalizar_proposta(proposta_id_param);
END;
$$ LANGUAGE plpgsql;

-- Função auxiliar finalizar_proposta_seguro (com 'o' no final)
CREATE OR REPLACE FUNCTION finalizar_proposta_seguro(proposta_id_param INTEGER) 
RETURNS BOOLEAN AS $$
BEGIN
    RETURN finalizar_proposta(proposta_id_param);
END;
$$ LANGUAGE plpgsql;

-- Trigger para consistência de dados
CREATE OR REPLACE FUNCTION atualizar_usuario_id_financeiro() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.proposta_id IS NOT NULL AND (NEW.usuario_id IS NULL OR NEW.usuario_id = '') THEN
        NEW.usuario_id := (SELECT usuario_id FROM propostas WHERE id = NEW.proposta_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Remover trigger se já existir (evita erros)
DROP TRIGGER IF EXISTS financeiro_usuario_id_trigger ON financeiro;

-- Criar trigger
CREATE TRIGGER financeiro_usuario_id_trigger
BEFORE INSERT OR UPDATE ON financeiro
FOR EACH ROW
EXECUTE FUNCTION atualizar_usuario_id_financeiro();
```

## Após aplicar a solução

1. Reinicie o serviço no Render
2. Teste finalizar uma proposta para verificar se o problema foi resolvido

## Explicação técnica

A solução cria três funções SQL no banco de dados:

1. `finalizar_proposta`: Função principal que realmente realiza a finalização da proposta
2. `finalizar_proposta_segura`: Alias para a função principal (com "a" no final)
3. `finalizar_proposta_seguro`: Alias para a função principal (com "o" no final)

Além disso, cria um trigger para garantir que ao criar um lançamento financeiro associado a uma proposta, o campo `usuario_id` seja corretamente preenchido.

Com esta abordagem, independentemente de qual nome de função for chamado no código, a função correta será executada.