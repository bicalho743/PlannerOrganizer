-- Script para adicionar as colunas usuario_id em todas as tabelas
-- Execute este script diretamente no banco de dados no Render

-- Tabela clientes
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela produtos
ALTER TABLE produtos 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela propostas
ALTER TABLE propostas 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela financeiro
ALTER TABLE financeiro 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela vendas
ALTER TABLE vendas 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela itens_proposta
ALTER TABLE itens_proposta 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela itens_venda
ALTER TABLE itens_venda 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Tabela acrescimos_proposta
ALTER TABLE acrescimos_proposta 
ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(255);

-- Verifica se a tabela perfil existe e a cria se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'perfil'
    ) THEN
        CREATE TABLE perfil (
            id SERIAL PRIMARY KEY,
            usuario_id VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            nome VARCHAR(255) NOT NULL,
            telefone VARCHAR(50),
            empresa VARCHAR(255),
            instagram VARCHAR(255),
            website VARCHAR(255),
            cor_principal VARCHAR(50),
            cor_secundaria VARCHAR(50),
            role VARCHAR(50) DEFAULT 'user',
            plano VARCHAR(50) DEFAULT 'gratuito',
            data_cadastro DATE,
            ultimo_login TIMESTAMP,
            ativo BOOLEAN DEFAULT TRUE
        );
    END IF;
END
$$;

-- Verifica quais tabelas têm a coluna usuario_id para confirmação
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'usuario_id'
ORDER BY table_name;