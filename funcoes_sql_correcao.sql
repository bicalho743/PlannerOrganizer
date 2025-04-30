-- INSTRUÇÕES:
-- 1. Execute este SQL diretamente no DBeaver ou no console SQL do Render
-- 2. Reinicie o serviço no Render após executar
-- 3. Verifique se a função finalizar_proposta_segura está funcionando 
-- Este script cria todas as funções necessárias para resolver o erro 'finalizar_proposta_segura' is not defined

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