-- Script para popular a coluna usuario_id com um valor padrão 
-- em todas as tabelas onde esta coluna foi adicionada

-- Este script deve ser executado APÓS o update_schema.sql
-- Use o ID de usuário Firebase da sua conta como valor padrão

-- Substitua 'SEU_ID_USUARIO_FIREBASE' pelo ID real do usuário Firebase
-- Por exemplo: UPDATE clientes SET usuario_id = '7Be1aICPHZdrS4ghnHZxc9Jp3Yt1' WHERE usuario_id IS NULL;

-- Tabela clientes
UPDATE clientes SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela produtos
UPDATE produtos SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela propostas
UPDATE propostas SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela financeiro
UPDATE financeiro SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela vendas
UPDATE vendas SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela itens_proposta
UPDATE itens_proposta SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela itens_venda
UPDATE itens_venda SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Tabela acrescimos_proposta
UPDATE acrescimos_proposta SET usuario_id = 'SEU_ID_USUARIO_FIREBASE' WHERE usuario_id IS NULL;

-- Mostrar contagem de registros atualizados por tabela
SELECT 'clientes' as tabela, COUNT(*) as registros FROM clientes WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'produtos', COUNT(*) FROM produtos WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'propostas', COUNT(*) FROM propostas WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'financeiro', COUNT(*) FROM financeiro WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'vendas', COUNT(*) FROM vendas WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'itens_proposta', COUNT(*) FROM itens_proposta WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'itens_venda', COUNT(*) FROM itens_venda WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE'
UNION ALL
SELECT 'acrescimos_proposta', COUNT(*) FROM acrescimos_proposta WHERE usuario_id = 'SEU_ID_USUARIO_FIREBASE';