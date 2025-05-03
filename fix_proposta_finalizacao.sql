-- Script SQL para corrigir problema de lançamentos financeiros duplicados
-- O problema: lançamentos sendo criados tanto na aprovação quanto na finalização da proposta
-- A solução: criar lançamento apenas na aprovação e verificar existência antes de criar novos

-- 1. FUNÇÕES DE VERIFICAÇÃO E PADRONIZAÇÃO

-- Função para verificar se já existe lançamento para uma proposta
CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER) 
RETURNS BOOLEAN AS $$
DECLARE
    existe BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM financeiro 
        WHERE proposta_id = proposta_id_param
        AND tipo = 'receita_a_receber'
    ) INTO existe;
    
    RETURN existe;
END;
$$ LANGUAGE plpgsql;

-- Função para gerar descrição padronizada de lançamentos
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

-- Trigger para padronizar descrições de lançamentos financeiros
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

-- 2. CORREÇÃO DE LANÇAMENTOS DUPLICADOS

-- Remover lançamentos duplicados e manter apenas o mais antigo
DO $$
DECLARE
    r RECORD;
    primeiro_lancamento_id INTEGER;
    descricao_padrao TEXT;
BEGIN
    -- Para cada proposta com lançamentos duplicados
    FOR r IN 
        SELECT 
            p.id as proposta_id, 
            c.nome as cliente_nome,
            COUNT(f.id) as total_lancamentos
        FROM propostas p
        JOIN clientes c ON p.cliente_id = c.id
        JOIN financeiro f ON p.id = f.proposta_id
        WHERE f.tipo = 'receita_a_receber'
        GROUP BY p.id, c.nome
        HAVING COUNT(f.id) > 1
    LOOP
        -- Obter descrição padronizada
        descricao_padrao := gerar_descricao_lancamento(r.proposta_id);
        
        -- Identificar o lançamento mais antigo (por data ou por ID se data for igual)
        SELECT MIN(id) INTO primeiro_lancamento_id
        FROM financeiro
        WHERE proposta_id = r.proposta_id
        AND tipo = 'receita_a_receber';
        
        -- Atualizar a descrição do lançamento mantido
        UPDATE financeiro
        SET descricao = descricao_padrao
        WHERE id = primeiro_lancamento_id;
        
        -- Excluir lançamentos duplicados (mantendo apenas o mais antigo)
        DELETE FROM financeiro
        WHERE proposta_id = r.proposta_id
        AND tipo = 'receita_a_receber'
        AND id != primeiro_lancamento_id;
        
        RAISE NOTICE 'Proposta #% - %: Removidos % lançamentos duplicados, mantido ID %', 
            r.proposta_id, 
            r.cliente_nome,
            r.total_lancamentos - 1,
            primeiro_lancamento_id;
    END LOOP;
END $$;

-- 3. EXEMPLO DE CORREÇÃO DO CÓDIGO DE FINALIZAÇÃO DE PROPOSTA

-- Essa é a parte que precisa ser adaptada no seu código Python:
-- Adicionar verificação antes de criar lançamentos financeiros

/*
EXEMPLO EM PSEUDOCÓDIGO (ADAPTE PARA SUA IMPLEMENTAÇÃO):

function finalizar_proposta(proposta_id):
    # Atualizar status da proposta
    atualizar_status_proposta(proposta_id, 'Finalizada')
    
    # NOVO: Verificar se já existe lançamento antes de criar um novo
    if not ja_existe_lancamento_proposta(proposta_id):
        # Só cria o lançamento se não existir um para essa proposta
        criar_lancamento_financeiro(proposta_id)
    else:
        print("Lançamento já existe, não será criado novamente")
*/

-- 4. PADRONIZAÇÃO DAS DESCRIÇÕES DE LANÇAMENTOS EXISTENTES

-- Padronizar descrições de todos os lançamentos existentes
DO $$
DECLARE
    r RECORD;
    descricao_padrao TEXT;
    total_atualizados INTEGER := 0;
BEGIN
    FOR r IN 
        SELECT DISTINCT proposta_id
        FROM financeiro
        WHERE proposta_id IS NOT NULL AND proposta_id > 0
    LOOP
        descricao_padrao := gerar_descricao_lancamento(r.proposta_id);
        
        UPDATE financeiro
        SET descricao = descricao_padrao
        WHERE proposta_id = r.proposta_id
        AND descricao != descricao_padrao;
        
        IF FOUND THEN
            total_atualizados := total_atualizados + 1;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Total de lançamentos com descrição padronizada: %', total_atualizados;
END $$;