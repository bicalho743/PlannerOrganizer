-- Script para recriar as tabelas relacionadas ao Stripe caso necessário
-- Este script foi gerado automaticamente durante a remoção da integração anterior

-- Recriação da tabela assinaturas
CREATE TABLE IF NOT EXISTS assinaturas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR NOT NULL,
    plano VARCHAR NOT NULL,
    customer_id VARCHAR,
    subscription_id VARCHAR,
    status VARCHAR NOT NULL,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    data_criacao TIMESTAMP NOT NULL,
    data_atualizacao TIMESTAMP,
    motivo_cancelamento TEXT
);

-- Recriação da tabela planos
CREATE TABLE IF NOT EXISTS planos (
    id SERIAL PRIMARY KEY,
    stripe_price_id VARCHAR NOT NULL,
    nome VARCHAR NOT NULL,
    descricao TEXT,
    valor NUMERIC NOT NULL,
    intervalo VARCHAR NOT NULL,
    limite_clientes INTEGER NOT NULL,
    limite_propostas INTEGER NOT NULL,
    limite_produtos INTEGER NOT NULL,
    data_criacao TIMESTAMP WITH TIME ZONE,
    ativo BOOLEAN
);

-- Recriação da tabela pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
    id SERIAL PRIMARY KEY,
    proposta_id INTEGER,
    stripe_payment_intent_id VARCHAR,
    valor DOUBLE PRECISION NOT NULL,
    status VARCHAR NOT NULL,
    data_criacao TIMESTAMP,
    data_pagamento TIMESTAMP,
    metodo_pagamento VARCHAR,
    descricao VARCHAR
);

-- Restaurar dados dos backups se necessário (descomente as linhas abaixo)
-- INSERT INTO assinaturas SELECT * FROM assinaturas_backup;
-- INSERT INTO planos SELECT * FROM planos_backup;
-- INSERT INTO pagamentos SELECT * FROM pagamentos_backup;