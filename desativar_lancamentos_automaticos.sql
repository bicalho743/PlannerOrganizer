-- Script para limpar e desabilitar lançamentos financeiros automáticos

-- 1. Remover todos os lançamentos relacionados a propostas
DELETE FROM financeiro 
WHERE proposta_id IS NOT NULL
   OR descricao LIKE 'Proposta #%';

-- 2. Criar uma função SQL que sempre retorna TRUE para bloquear novos lançamentos
CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER) 
RETURNS BOOLEAN AS $$
BEGIN
    -- Sempre retorna TRUE para bloquear criação de novos lançamentos
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 3. Criar um trigger para impedir inserções com proposta_id
CREATE OR REPLACE FUNCTION bloquear_lancamento_proposta() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.proposta_id IS NOT NULL THEN
        RAISE NOTICE 'Tentativa de inserção de lançamento automático bloqueada para proposta %', NEW.proposta_id;
        RETURN NULL; -- Não permite a inserção
    END IF;
    
    -- Verificar pela descrição também
    IF NEW.descricao LIKE 'Proposta #%' THEN
        RAISE NOTICE 'Tentativa de inserção de lançamento automático bloqueada: %', NEW.descricao;
        RETURN NULL; -- Não permite a inserção
    END IF;
    
    RETURN NEW; -- Permite outros lançamentos
END;
$$ LANGUAGE plpgsql;

-- Verificar se o trigger já existe antes de criar
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'impedir_lancamento_proposta'
    ) THEN
        CREATE TRIGGER impedir_lancamento_proposta
        BEFORE INSERT ON financeiro
        FOR EACH ROW
        EXECUTE FUNCTION bloquear_lancamento_proposta();
    END IF;
END $$;