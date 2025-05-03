-- Script SQL para corrigir problemas de duplicação de lançamentos financeiros
-- Este script identifica e corrige lançamentos duplicados para a mesma proposta
-- e implementa funções e triggers para evitar duplicações futuras

-- Função para verificar existência de lançamentos por proposta_id e tipo
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

-- Função para gerar descrição padronizada para lançamentos financeiros
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

-- Função para padronizar descrições de lançamentos existentes
CREATE OR REPLACE FUNCTION padronizar_descricoes_existentes()
RETURNS INTEGER AS $$
DECLARE
    total_atualizados INTEGER := 0;
    proposta_rec RECORD;
    descricao_padrao TEXT;
BEGIN
    -- Para cada proposta com lançamentos financeiros
    FOR proposta_rec IN 
        SELECT DISTINCT proposta_id 
        FROM financeiro 
        WHERE proposta_id IS NOT NULL AND proposta_id > 0
    LOOP
        -- Gerar descrição padronizada
        descricao_padrao := gerar_descricao_lancamento(proposta_rec.proposta_id);
        
        -- Atualizar descrições
        UPDATE financeiro
        SET descricao = descricao_padrao
        WHERE proposta_id = proposta_rec.proposta_id
        AND descricao != descricao_padrao;
        
        -- Incrementar contador
        total_atualizados := total_atualizados + 1;
    END LOOP;
    
    RETURN total_atualizados;
END;
$$ LANGUAGE plpgsql;

-- Função trigger para garantir que novos lançamentos usem descrição padronizada
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

-- Criar trigger para padronizar descrições automaticamente
DROP TRIGGER IF EXISTS financeiro_descricao_trigger ON financeiro;

CREATE TRIGGER financeiro_descricao_trigger
BEFORE INSERT OR UPDATE ON financeiro
FOR EACH ROW
WHEN (NEW.proposta_id IS NOT NULL AND NEW.proposta_id > 0)
EXECUTE FUNCTION padronizar_descricao_financeiro();

-- Remover lançamentos duplicados mantendo apenas o mais antigo para cada proposta
DO $$
DECLARE
    lancamento_record RECORD;
    lancamentos_duplicados RECORD;
    primeiro_lancamento_id INTEGER;
    descricao_padrao TEXT;
BEGIN
    -- Para cada proposta com lançamentos duplicados
    FOR lancamentos_duplicados IN 
        SELECT 
            proposta_id, 
            COUNT(*) as total
        FROM financeiro
        WHERE proposta_id IS NOT NULL
        AND tipo = 'receita_a_receber'
        GROUP BY proposta_id
        HAVING COUNT(*) > 1
    LOOP
        -- Obter descrição padronizada
        descricao_padrao := gerar_descricao_lancamento(lancamentos_duplicados.proposta_id);
        
        -- Identificar o lançamento mais antigo (pelo ID mais baixo)
        SELECT MIN(id) INTO primeiro_lancamento_id
        FROM financeiro
        WHERE proposta_id = lancamentos_duplicados.proposta_id
        AND tipo = 'receita_a_receber';
        
        -- Atualizar a descrição do lançamento mantido para o formato padronizado
        UPDATE financeiro
        SET descricao = descricao_padrao
        WHERE id = primeiro_lancamento_id;
        
        -- Remover os lançamentos duplicados (mantendo o mais antigo)
        DELETE FROM financeiro
        WHERE proposta_id = lancamentos_duplicados.proposta_id
        AND tipo = 'receita_a_receber'
        AND id != primeiro_lancamento_id;
        
        RAISE NOTICE 'Proposta #% - Removidos % lançamentos duplicados, mantido ID %', 
            lancamentos_duplicados.proposta_id, 
            lancamentos_duplicados.total - 1,
            primeiro_lancamento_id;
    END LOOP;
END $$;

-- Padronizar descrições de todos os lançamentos existentes
SELECT padronizar_descricoes_existentes();