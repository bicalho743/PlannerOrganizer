-- Migração de banco de dados para suporte à integração com Stripe
-- Adiciona colunas necessárias para rastreamento de pagamentos e assinaturas

-- Adicionar colunas relacionadas ao Stripe na tabela 'perfis'
ALTER TABLE perfis ADD COLUMN IF NOT EXISTS cliente_stripe_id VARCHAR;
ALTER TABLE perfis ADD COLUMN IF NOT EXISTS assinatura_stripe_id VARCHAR;
ALTER TABLE perfis ADD COLUMN IF NOT EXISTS assinatura_inicio TIMESTAMP;
ALTER TABLE perfis ADD COLUMN IF NOT EXISTS assinatura_expiracao TIMESTAMP;
ALTER TABLE perfis ADD COLUMN IF NOT EXISTS metodo_pagamento VARCHAR;

-- Criar tabela para rastreamento de transações do Stripe
CREATE TABLE IF NOT EXISTS stripe_transacoes (
    id SERIAL PRIMARY KEY,
    stripe_event_id VARCHAR NOT NULL UNIQUE,
    stripe_customer_id VARCHAR,
    usuario_id VARCHAR NOT NULL,
    tipo VARCHAR NOT NULL, -- 'pagamento', 'reembolso', 'falha', etc.
    status VARCHAR NOT NULL,
    valor NUMERIC(10, 2),
    moeda VARCHAR DEFAULT 'BRL',
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadados JSONB
);

-- Criar tabela para rastreamento de assinaturas 
CREATE TABLE IF NOT EXISTS stripe_assinaturas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR NOT NULL,
    stripe_subscription_id VARCHAR NOT NULL UNIQUE,
    stripe_customer_id VARCHAR NOT NULL,
    plano VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    data_inicio TIMESTAMP NOT NULL,
    data_proximo_pagamento TIMESTAMP,
    data_cancelamento TIMESTAMP,
    data_encerramento TIMESTAMP,
    valor_periodico NUMERIC(10, 2),
    intervalo VARCHAR, -- 'mes', 'ano'
    metadados JSONB,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para melhorar performance de consultas
CREATE INDEX IF NOT EXISTS idx_perfis_stripe_customer ON perfis(cliente_stripe_id);
CREATE INDEX IF NOT EXISTS idx_stripe_transacoes_usuario ON stripe_transacoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_stripe_transacoes_customer ON stripe_transacoes(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_stripe_assinaturas_usuario ON stripe_assinaturas(usuario_id);

-- Criar visualização simplificada de status de assinatura por usuário
CREATE OR REPLACE VIEW vw_status_assinatura AS
SELECT
    p.id,
    p.usuario_id,
    p.email,
    p.nome,
    p.plano,
    p.cliente_stripe_id,
    p.assinatura_stripe_id,
    p.assinatura_inicio,
    p.assinatura_expiracao,
    CASE
        WHEN p.plano = 'gratuito' THEN 'Gratuito'
        WHEN p.assinatura_expiracao IS NULL THEN 'Indeterminado'
        WHEN p.assinatura_expiracao < CURRENT_TIMESTAMP THEN 'Expirado'
        ELSE 'Ativo'
    END AS status_assinatura,
    CASE
        WHEN p.assinatura_expiracao IS NOT NULL THEN
            p.assinatura_expiracao - CURRENT_TIMESTAMP
        ELSE NULL
    END AS dias_restantes
FROM
    perfis p;