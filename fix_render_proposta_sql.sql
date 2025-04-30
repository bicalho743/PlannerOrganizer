-- Script SQL para corrigir propostas no Render
-- Executar no console SQL do banco de dados

-- 1. Verificar estrutura da tabela propostas
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'propostas'
ORDER BY ordinal_position;

-- 2. Verificar estado das propostas
SELECT id, status, data_inicio, data_proposta, data_finalizacao
FROM propostas
WHERE id = 9; -- ALTERE ESTE VALOR para o ID da proposta que deseja verificar

-- 3. Script para finalizar completamente uma proposta específica
-- ALTERE O NÚMERO 9 PARA O ID DA SUA PROPOSTA
DO $$
DECLARE
    p_id INTEGER := 9; -- ALTERE ESTE VALOR para o ID da proposta que deseja finalizar
    p_status VARCHAR;
    p_data_proposta DATE;
    p_data_inicio DATE;
    p_data_finalizacao DATE;
    data_atual DATE := CURRENT_DATE;
BEGIN
    -- Verificar se a proposta existe
    SELECT status, data_proposta, data_inicio, data_finalizacao 
    INTO p_status, p_data_proposta, p_data_inicio, p_data_finalizacao
    FROM propostas 
    WHERE id = p_id;
    
    IF p_status IS NULL THEN
        RAISE EXCEPTION 'Proposta #% não encontrada', p_id;
    END IF;
    
    RAISE NOTICE 'Processando proposta #% (status atual: %)', p_id, p_status;
    
    -- Verificar se já está finalizada
    IF p_status = 'Finalizada' THEN
        RAISE NOTICE 'Proposta #% já está marcada como finalizada', p_id;
        
        -- Verificar data_finalizacao
        IF p_data_finalizacao IS NULL THEN
            UPDATE propostas 
            SET data_finalizacao = data_atual
            WHERE id = p_id;
            RAISE NOTICE '  Adicionada data de finalização: %', data_atual;
        END IF;
    ELSE
        -- Não está finalizada, fazer o processo completo
        UPDATE propostas 
        SET status = 'Finalizada',
            data_finalizacao = data_atual
        WHERE id = p_id;
        RAISE NOTICE '  Atualizado status para ''Finalizada'' e data_finalizacao para %', data_atual;
    END IF;
    
    -- Garantir que a data_proposta esteja preenchida
    IF p_data_proposta IS NULL AND p_data_inicio IS NOT NULL THEN
        UPDATE propostas 
        SET data_proposta = p_data_inicio 
        WHERE id = p_id;
        RAISE NOTICE '  Atualizada data_proposta para %', p_data_inicio;
    END IF;
    
    -- Verificar se existe lançamento financeiro
    IF NOT EXISTS (
        SELECT 1 FROM financeiro 
        WHERE proposta_id = p_id AND tipo = 'receita_a_receber'
    ) THEN
        -- Criar lançamento financeiro
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
        RAISE NOTICE '  Adicionado lançamento financeiro';
    END IF;
    
    RAISE NOTICE 'Proposta #% finalizada com sucesso', p_id;
END $$;

-- 4. Script simplificado para finalizar rapidamente uma proposta
-- ALTERE O NÚMERO 9 PARA O ID DA SUA PROPOSTA
UPDATE propostas 
SET status = 'Finalizada',
    data_finalizacao = CURRENT_DATE
WHERE id = 9; -- ALTERE ESTE VALOR

INSERT INTO financeiro 
(descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
SELECT 
    'Proposta #' || p.id || ' - ' || c.nome,
    p.valor,
    CURRENT_DATE,
    'Serviços de Organização',
    'receita_a_receber',
    'Pendente',
    p.id,
    p.usuario_id
FROM propostas p
JOIN clientes c ON p.cliente_id = c.id
WHERE p.id = 9 -- ALTERE ESTE VALOR
AND NOT EXISTS (
    SELECT 1 FROM financeiro 
    WHERE proposta_id = p.id AND tipo = 'receita_a_receber'
);

-- 5. Script para finalizar TODAS as propostas pendentes
DO $$
DECLARE
    data_atual DATE := CURRENT_DATE;
BEGIN
    -- Criar lançamentos financeiros para todas as propostas não finalizadas
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
    WHERE p.status IN ('Em execução', 'Em análise')
    AND NOT EXISTS (
        SELECT 1 FROM financeiro f 
        WHERE f.proposta_id = p.id AND f.tipo = 'receita_a_receber'
    );
    
    -- Atualizar data_proposta para todas as propostas que não têm
    UPDATE propostas 
    SET data_proposta = data_inicio
    WHERE data_proposta IS NULL 
    AND data_inicio IS NOT NULL;
    
    -- Atualizar status de todas as propostas não finalizadas
    UPDATE propostas 
    SET status = 'Finalizada',
        data_finalizacao = data_atual
    WHERE status IN ('Em execução', 'Em análise');
    
    RAISE NOTICE 'Todas as propostas pendentes foram finalizadas';
END $$;