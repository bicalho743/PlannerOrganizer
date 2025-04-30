-- Script para preencher a coluna usuario_id em todas as tabelas
-- Este script deve ser executado uma única vez no banco do Render

-- Adiciona e preenche usuario_id na tabela clientes
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
UPDATE clientes SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Adiciona e preenche usuario_id na tabela propostas
ALTER TABLE propostas ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
UPDATE propostas SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Adiciona e preenche usuario_id na tabela produtos
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
UPDATE produtos SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Adiciona e preenche usuario_id na tabela financeiro
ALTER TABLE financeiro ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
UPDATE financeiro SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Adiciona e preenche usuario_id na tabela documentos
ALTER TABLE documentos ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
UPDATE documentos SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Adiciona e preenche usuario_id na tabela vendas
ALTER TABLE vendas ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
UPDATE vendas SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Cria índices para melhorar performance de filtro por usuario_id
CREATE INDEX IF NOT EXISTS idx_clientes_usuario_id ON clientes (usuario_id);
CREATE INDEX IF NOT EXISTS idx_propostas_usuario_id ON propostas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_produtos_usuario_id ON produtos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_usuario_id ON financeiro (usuario_id);
CREATE INDEX IF NOT EXISTS idx_documentos_usuario_id ON documentos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id);

-- Criar ou atualizar tabela perfil (pode variar entre perfil e perfis)
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

-- Verificar tabela perfis (nome plural)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'perfis') THEN
        ALTER TABLE perfis ADD COLUMN IF NOT EXISTS usuario_id VARCHAR;
        CREATE INDEX IF NOT EXISTS idx_perfis_usuario_id ON perfis (usuario_id);
    END IF;
END $$;

-- Analizar tabelas para atualizar estatísticas
ANALYZE;