-- Script de atualização de esquema para Render
-- Executa modificações necessárias para garantir compatibilidade

-- Tabela clientes
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;

-- Tabela propostas
ALTER TABLE propostas ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;

-- Tabela produtos
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;

-- Tabela financeiro
ALTER TABLE financeiro ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;

-- Tabela documentos
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;

-- Tabela vendas
ALTER TABLE vendas ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;

-- Criar tabela perfil se não existir
CREATE TABLE IF NOT EXISTS perfil (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    nome VARCHAR NOT NULL,
    telefone VARCHAR,
    empresa VARCHAR,
    instagram VARCHAR,
    website VARCHAR,
    cor_principal VARCHAR,
    cor_secundaria VARCHAR,
    role VARCHAR DEFAULT 'user',
    plano VARCHAR DEFAULT 'gratuito',
    data_cadastro DATE DEFAULT CURRENT_DATE,
    ultimo_login TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);

-- Criar ou atualizar tabela perfis (nome plural)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'perfis') THEN
        ALTER TABLE perfis ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
        
        -- Cria um registro padrão se não existir
        IF NOT EXISTS (SELECT 1 FROM perfis WHERE usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2') THEN
            INSERT INTO perfis (usuario_id, email, nome, ativo) 
            VALUES ('7NDbX2b7hAcFqWzwsgi2BXiFZad2', 'admin@exemplo.com', 'Administrador', TRUE);
        END IF;
    END IF;
END $$;

-- Cria índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_clientes_usuario_id ON clientes (usuario_id);
CREATE INDEX IF NOT EXISTS idx_propostas_usuario_id ON propostas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_produtos_usuario_id ON produtos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_usuario_id ON financeiro (usuario_id);
CREATE INDEX IF NOT EXISTS idx_documentos_usuario_id ON documentos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id);

-- Criar visão para compatibilidade legada
CREATE OR REPLACE VIEW vw_clientes AS
SELECT * FROM clientes;