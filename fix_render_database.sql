-- Script SQL para corrigir problemas de esquema no banco de dados
-- Este script adiciona as colunas usuario_id necessárias e repara metadados

-- Adiciona coluna usuario_id à tabela clientes se não existir
DO $$ 
BEGIN
    BEGIN
        ALTER TABLE clientes ADD COLUMN usuario_id VARCHAR;
        RAISE NOTICE 'Coluna usuario_id adicionada à tabela clientes';
    EXCEPTION
        WHEN duplicate_column THEN
            RAISE NOTICE 'Coluna usuario_id já existe na tabela clientes';
    END;
END $$;

-- Atualiza valores nulos de usuario_id em clientes
UPDATE clientes SET usuario_id = '7NDbX2b7hAcFqWzwsgi2BXiFZad2' WHERE usuario_id IS NULL;

-- Adiciona coluna usuario_id à tabela perfil se não existir
DO $$ 
BEGIN
    BEGIN
        ALTER TABLE perfil ADD COLUMN usuario_id VARCHAR;
        RAISE NOTICE 'Coluna usuario_id adicionada à tabela perfil';
    EXCEPTION
        WHEN duplicate_column THEN
            RAISE NOTICE 'Coluna usuario_id já existe na tabela perfil';
        WHEN undefined_table THEN
            CREATE TABLE perfil (
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
            RAISE NOTICE 'Tabela perfil criada com sucesso';
    END;
END $$;

-- Cria índice para otimizar consultas por usuario_id
DO $$ 
BEGIN
    BEGIN
        CREATE INDEX idx_cliente_usuario_id ON clientes (usuario_id);
        RAISE NOTICE 'Índice idx_cliente_usuario_id criado com sucesso';
    EXCEPTION
        WHEN duplicate_table THEN
            RAISE NOTICE 'Índice idx_cliente_usuario_id já existe';
    END;
END $$;

-- Criar uma versão legada da tabela clientes para compatibilidade
DO $$ 
BEGIN
    BEGIN
        DROP VIEW IF EXISTS clientes_view;
        CREATE VIEW clientes_view AS SELECT * FROM clientes;
        RAISE NOTICE 'View clientes_view criada com sucesso';
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'Erro ao criar view clientes_view: %', SQLERRM;
    END;
END $$;

-- Forçar análise da tabela para atualizar estatísticas
ANALYZE clientes;

-- Mostrar estrutura final da tabela
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'clientes' 
ORDER BY column_name;