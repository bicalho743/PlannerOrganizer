-- Script para corrigir problemas de cache da interface no Render
-- Este script ajusta os dados para garantir que propostas finalizadas apareçam corretamente na interface

-- 1. Verificar campos essenciais para propostas finalizadas
SELECT 
    column_name 
FROM 
    information_schema.columns 
WHERE 
    table_name = 'propostas' 
    AND column_name IN ('status', 'data_finalizacao', 'data_proposta', 'data_inicio')
ORDER BY 
    ordinal_position;

-- 2. Verificar propostas que podem ter problemas de visualização na interface
SELECT 
    id, 
    status, 
    data_inicio, 
    data_proposta, 
    data_finalizacao,
    ativo,
    usuario_id
FROM 
    propostas
WHERE 
    (status = 'Finalizada' AND data_finalizacao IS NULL)
    OR (status = 'Finalizada' AND data_proposta IS NULL)
    OR (status = 'Em execução' AND data_finalizacao IS NOT NULL)
ORDER BY 
    id DESC;

-- 3. Verificar propostas finalizadas que não têm lançamentos financeiros
SELECT 
    p.id, 
    p.descricao, 
    p.status, 
    p.valor,
    p.data_finalizacao,
    p.usuario_id,
    c.nome as cliente_nome
FROM 
    propostas p
JOIN 
    clientes c ON p.cliente_id = c.id
LEFT JOIN 
    financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
WHERE 
    p.status = 'Finalizada' 
    AND f.id IS NULL
ORDER BY 
    p.id DESC;

-- 4. Script para corrigir inconsistências em todas as propostas finalizadas
DO $$
DECLARE
    data_atual DATE := CURRENT_DATE;
BEGIN
    -- Garantir que todas as propostas finalizadas tenham data_finalizacao
    UPDATE propostas 
    SET data_finalizacao = data_atual
    WHERE status = 'Finalizada' AND data_finalizacao IS NULL;
    
    -- Garantir que todas as propostas finalizadas tenham data_proposta
    UPDATE propostas 
    SET data_proposta = COALESCE(data_inicio, data_atual)
    WHERE status = 'Finalizada' AND data_proposta IS NULL;
    
    -- Garantir que todas as propostas em execução não tenham data_finalizacao
    UPDATE propostas 
    SET data_finalizacao = NULL
    WHERE status <> 'Finalizada' AND data_finalizacao IS NOT NULL;
    
    -- Criar lançamentos financeiros para propostas finalizadas que não os têm
    INSERT INTO financeiro 
    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
    SELECT 
        'Proposta #' || p.id || ' - ' || c.nome,
        p.valor,
        COALESCE(p.data_finalizacao, data_atual),
        'Serviços de Organização',
        'receita_a_receber',
        'Pendente',
        p.id,
        p.usuario_id
    FROM propostas p
    JOIN clientes c ON p.cliente_id = c.id
    LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
    WHERE p.status = 'Finalizada' AND f.id IS NULL;
    
    -- Garantir que não existam propostas no status "Em análise" mas com data_finalizacao
    UPDATE propostas
    SET status = 'Finalizada'
    WHERE status = 'Em análise' AND data_finalizacao IS NOT NULL;
    
    RAISE NOTICE 'Todas as inconsistências de dados corrigidas';
END $$;

-- 5. Script para corrigir apenas uma proposta específica
-- ALTERE O NÚMERO 9 PARA O ID DA SUA PROPOSTA
DO $$
DECLARE
    p_id INTEGER := 9; -- ALTERE ESTE VALOR para o ID da proposta que deseja corrigir
    data_atual DATE := CURRENT_DATE;
    p_exists BOOLEAN;
    p_status VARCHAR;
    p_data_proposta DATE;
    p_data_inicio DATE;
    p_data_finalizacao DATE;
    p_usuario_id VARCHAR;
BEGIN
    -- Verificar se a proposta existe
    SELECT 
        TRUE,
        status, 
        data_proposta, 
        data_inicio, 
        data_finalizacao,
        usuario_id
    INTO 
        p_exists,
        p_status,
        p_data_proposta,
        p_data_inicio,
        p_data_finalizacao,
        p_usuario_id
    FROM propostas 
    WHERE id = p_id;
    
    IF p_exists IS NULL THEN
        RAISE EXCEPTION 'Proposta #% não encontrada', p_id;
    END IF;
    
    -- Verificar e corrigir a proposta específica
    IF p_status = 'Finalizada' THEN
        -- Garantir que a proposta finalizada tenha data_finalizacao
        IF p_data_finalizacao IS NULL THEN
            UPDATE propostas 
            SET data_finalizacao = data_atual
            WHERE id = p_id;
            RAISE NOTICE 'Adicionada data_finalizacao: %', data_atual;
        END IF;
        
        -- Garantir que a proposta finalizada tenha data_proposta
        IF p_data_proposta IS NULL THEN
            UPDATE propostas 
            SET data_proposta = COALESCE(p_data_inicio, data_atual)
            WHERE id = p_id;
            RAISE NOTICE 'Adicionada data_proposta: %', COALESCE(p_data_inicio, data_atual);
        END IF;
        
        -- Garantir que a proposta finalizada tenha lançamento financeiro
        IF NOT EXISTS (
            SELECT 1 FROM financeiro 
            WHERE proposta_id = p_id AND tipo = 'receita_a_receber'
        ) THEN
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
            SELECT 
                'Proposta #' || p.id || ' - ' || c.nome,
                p.valor,
                COALESCE(p.data_finalizacao, data_atual),
                'Serviços de Organização',
                'receita_a_receber',
                'Pendente',
                p.id,
                p.usuario_id
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = p_id;
            RAISE NOTICE 'Adicionado lançamento financeiro';
        END IF;
    ELSE
        -- Não está finalizada, remover data_finalizacao se existir
        IF p_data_finalizacao IS NOT NULL THEN
            UPDATE propostas 
            SET data_finalizacao = NULL
            WHERE id = p_id;
            RAISE NOTICE 'Removida data_finalizacao';
        END IF;
    END IF;
    
    RAISE NOTICE 'Proposta #% verificada e corrigida com sucesso', p_id;
END $$;

-- 6. Forçar uma proposta a aparecer como finalizada (use em último caso)
-- ALTERE O NÚMERO 9 PARA O ID DA SUA PROPOSTA
DO $$
DECLARE
    p_id INTEGER := 9; -- ALTERE ESTE VALOR
    data_atual DATE := CURRENT_DATE;
BEGIN
    -- Forçar finalização completa
    UPDATE propostas 
    SET 
        status = 'Finalizada',
        data_finalizacao = data_atual,
        data_proposta = COALESCE(data_proposta, data_inicio, data_atual),
        ativo = TRUE -- Garantir que esteja ativa
    WHERE id = p_id;
    
    -- Garantir que existe lançamento financeiro
    IF NOT EXISTS (
        SELECT 1 FROM financeiro 
        WHERE proposta_id = p_id AND tipo = 'receita_a_receber'
    ) THEN
        INSERT INTO financeiro 
        (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
        SELECT 
            'Proposta #' || p.id || ' - ' || c.nome,
            p.valor,
            data_atual,
            'Serviços de Organização',
            'receita_a_receber',
            'Pendente',
            p.id,
            p.usuario_id
        FROM propostas p
        JOIN clientes c ON p.cliente_id = c.id
        WHERE p.id = p_id;
    END IF;
    
    RAISE NOTICE 'Proposta #% forçada como finalizada com sucesso', p_id;
END $$;