-- Script SQL simples para adicionar função de verificação de lançamentos existentes
-- Esta função deve ser usada no código que finaliza propostas para evitar criar lançamentos duplicados

-- Função para verificar se já existe lançamento para uma proposta
CREATE OR REPLACE FUNCTION ja_existe_lancamento_proposta(proposta_id_param INTEGER) 
RETURNS BOOLEAN AS $$
DECLARE
    existe BOOLEAN;
BEGIN
    -- Verifica se já existe algum lançamento financeiro associado à proposta
    SELECT EXISTS(
        SELECT 1 FROM financeiro 
        WHERE proposta_id = proposta_id_param
        AND tipo = 'receita_a_receber'
    ) INTO existe;
    
    RETURN existe;
END;
$$ LANGUAGE plpgsql;

-- Exemplo de como utilizar esta função no código Python:
/*
# Verificar se já existe lançamento para esta proposta
cursor.execute("SELECT ja_existe_lancamento_proposta(%s)", (proposta_id,))
ja_existe = cursor.fetchone()[0]

# Criar lançamento financeiro apenas se não existir
if not ja_existe:
    # Código para criar o lançamento
    adicionar_lancamento_financeiro(descricao, valor, data, ...)
else:
    # Log ou mensagem informando que o lançamento já existe
    logger.info(f"Proposta #{proposta_id} já possui lançamento financeiro, não será criado outro")
*/