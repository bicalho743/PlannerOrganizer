"""
Arquivo com consultas SQL para corrigir problemas no banco de dados do Render

Como usar:
1. Copie estas consultas
2. Execute-as no console SQL do Render
"""

# Verificar estrutura da tabela financeiro
VERIFICAR_ESTRUTURA = """
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'financeiro'
ORDER BY ordinal_position;
"""

# Adicionar coluna usuario_id à tabela financeiro se não existir
ADICIONAR_COLUNA_USUARIO_ID = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'financeiro' AND column_name = 'usuario_id'
    ) THEN
        ALTER TABLE financeiro ADD COLUMN usuario_id VARCHAR;
    END IF;
END $$;
"""

# Preencher coluna usuario_id com valores corretos baseados na proposta
PREENCHER_USUARIO_ID = """
UPDATE financeiro f
SET usuario_id = p.usuario_id
FROM propostas p
WHERE f.proposta_id = p.id AND f.usuario_id IS NULL;
"""

# Criar trigger para manter consistência da coluna usuario_id
CRIAR_TRIGGER_USUARIO_ID = """
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
"""

# Finalizar proposta específica
FINALIZAR_PROPOSTA = """
-- Substitua 9 pelo ID da proposta que deseja finalizar
DO $$
DECLARE
    proposta_id INTEGER := 9; -- ALTERE ESTE VALOR
    proposta_valor NUMERIC;
    proposta_usuario_id VARCHAR;
    cliente_nome VARCHAR;
    tem_forma_pagamento BOOLEAN;
BEGIN
    -- Verificar se existe coluna forma_pagamento
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'financeiro' AND column_name = 'forma_pagamento'
    ) INTO tem_forma_pagamento;

    -- Obter informações da proposta
    SELECT p.valor, p.usuario_id, c.nome 
    INTO proposta_valor, proposta_usuario_id, cliente_nome
    FROM propostas p
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.id = proposta_id;
    
    IF proposta_valor IS NULL THEN
        RAISE EXCEPTION 'Proposta #% não encontrada', proposta_id;
    END IF;
    
    -- Verificar se já existe lançamento para esta proposta
    IF EXISTS (
        SELECT 1 FROM financeiro 
        WHERE proposta_id = proposta_id AND tipo = 'receita_a_receber'
    ) THEN
        RAISE NOTICE 'Proposta #% já possui lançamento financeiro', proposta_id;
    ELSE
        -- Inserir lançamento financeiro adaptado à estrutura da tabela
        IF tem_forma_pagamento THEN
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
            VALUES 
            (CONCAT('Proposta #', proposta_id, ' - ', cliente_nome),
             proposta_valor,
             CURRENT_DATE,
             'Serviços de Organização',
             'receita_a_receber',
             'Pendente',
             '',
             proposta_id,
             proposta_usuario_id);
        ELSE
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
            VALUES 
            (CONCAT('Proposta #', proposta_id, ' - ', cliente_nome),
             proposta_valor,
             CURRENT_DATE,
             'Serviços de Organização',
             'receita_a_receber',
             'Pendente',
             proposta_id,
             proposta_usuario_id);
        END IF;
        
        RAISE NOTICE 'Lançamento financeiro criado para proposta #%', proposta_id;
    END IF;
    
    -- Atualizar status da proposta para Finalizada
    UPDATE propostas SET status = 'Finalizada' WHERE id = proposta_id;
    RAISE NOTICE 'Proposta #% finalizada com sucesso', proposta_id;
    
END $$;
"""

# Finalizar todas as propostas em execução
FINALIZAR_TODAS_PROPOSTAS = """
DO $$
DECLARE
    p RECORD;
    tem_forma_pagamento BOOLEAN;
BEGIN
    -- Verificar se existe coluna forma_pagamento
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'financeiro' AND column_name = 'forma_pagamento'
    ) INTO tem_forma_pagamento;

    -- Para cada proposta não finalizada
    FOR p IN 
        SELECT p.id, p.valor, p.usuario_id, c.nome as cliente_nome
        FROM propostas p
        JOIN clientes c ON p.cliente_id = c.id
        WHERE p.status IN ('Em execução', 'Em análise')
    LOOP
        -- Verificar se já existe lançamento para esta proposta
        IF EXISTS (
            SELECT 1 FROM financeiro 
            WHERE proposta_id = p.id AND tipo = 'receita_a_receber'
        ) THEN
            RAISE NOTICE 'Proposta #% já possui lançamento financeiro', p.id;
        ELSE
            -- Inserir lançamento financeiro adaptado à estrutura da tabela
            IF tem_forma_pagamento THEN
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                VALUES 
                (CONCAT('Proposta #', p.id, ' - ', p.cliente_nome),
                 p.valor,
                 CURRENT_DATE,
                 'Serviços de Organização',
                 'receita_a_receber',
                 'Pendente',
                 '',
                 p.id,
                 p.usuario_id);
            ELSE
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                VALUES 
                (CONCAT('Proposta #', p.id, ' - ', p.cliente_nome),
                 p.valor,
                 CURRENT_DATE,
                 'Serviços de Organização',
                 'receita_a_receber',
                 'Pendente',
                 p.id,
                 p.usuario_id);
            END IF;
            
            RAISE NOTICE 'Lançamento financeiro criado para proposta #%', p.id;
        END IF;
        
        -- Atualizar status da proposta para Finalizada
        UPDATE propostas SET status = 'Finalizada' WHERE id = p.id;
        RAISE NOTICE 'Proposta #% finalizada com sucesso', p.id;
    END LOOP;
END $$;
"""

# Mostrar as primeiras propostas para diagnóstico
VERIFICAR_PROPOSTAS = """
SELECT p.id, p.descricao, p.valor, p.status, p.usuario_id, c.nome as cliente_nome
FROM propostas p
JOIN clientes c ON p.cliente_id = c.id
ORDER BY p.id DESC
LIMIT 10;
"""

# Verificar lançamentos financeiros
VERIFICAR_LANCAMENTOS = """
SELECT f.id, f.descricao, f.valor, f.categoria, f.tipo, f.status, f.proposta_id, f.usuario_id
FROM financeiro f
ORDER BY f.id DESC
LIMIT 10;
"""