-- Migração do banco de dados para integração com Stripe
-- Este script adiciona novas tabelas e colunas necessárias para gerenciar assinaturas

-- --------------------------------------------------------
-- TABELAS PARA ASSINATURAS E PLANOS
-- --------------------------------------------------------

-- Tabela para armazenar os planos disponíveis
CREATE TABLE IF NOT EXISTS planos (
    id SERIAL PRIMARY KEY,
    stripe_price_id VARCHAR(255) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    valor NUMERIC(10, 2) NOT NULL,
    intervalo VARCHAR(20) NOT NULL DEFAULT 'month', -- 'month' ou 'year'
    limite_clientes INTEGER NOT NULL DEFAULT 50,
    limite_propostas INTEGER NOT NULL DEFAULT 100,
    limite_produtos INTEGER NOT NULL DEFAULT 50,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);

-- Tabela para armazenar as assinaturas dos usuários
CREATE TABLE IF NOT EXISTS assinaturas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(255) NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL,
    plano_id INTEGER REFERENCES planos(id),
    status VARCHAR(50) NOT NULL DEFAULT 'incompleta',
    data_inicio TIMESTAMP WITH TIME ZONE,
    data_fim TIMESTAMP WITH TIME ZONE,
    data_cancelamento TIMESTAMP WITH TIME ZONE,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    motivo_cancelamento TEXT,
    UNIQUE(usuario_id)
);

-- Tabela para armazenar o histórico de pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
    id SERIAL PRIMARY KEY,
    assinatura_id INTEGER REFERENCES assinaturas(id),
    stripe_payment_intent_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    valor NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_pagamento TIMESTAMP WITH TIME ZONE,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------
-- MODIFICAÇÕES NAS TABELAS EXISTENTES
-- --------------------------------------------------------

-- Adicionar coluna de tipo_plano à tabela perfis (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'perfis' AND column_name = 'tipo_plano'
    ) THEN
        ALTER TABLE perfis ADD COLUMN tipo_plano VARCHAR(20) DEFAULT 'gratuito';
    END IF;
END $$;

-- Adicionar coluna para contar uso dos limites
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'perfis' AND column_name = 'contagem_clientes'
    ) THEN
        ALTER TABLE perfis ADD COLUMN contagem_clientes INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'perfis' AND column_name = 'contagem_propostas'
    ) THEN
        ALTER TABLE perfis ADD COLUMN contagem_propostas INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'perfis' AND column_name = 'contagem_produtos'
    ) THEN
        ALTER TABLE perfis ADD COLUMN contagem_produtos INTEGER DEFAULT 0;
    END IF;
END $$;

-- --------------------------------------------------------
-- VIEWS
-- --------------------------------------------------------

-- View para consultar o status atual das assinaturas
CREATE OR REPLACE VIEW vw_status_assinatura AS
SELECT 
    p.usuario_id,
    p.email,
    p.nome,
    p.tipo_plano,
    COALESCE(a.status, 'sem_assinatura') AS status_assinatura,
    pl.nome AS plano_nome,
    pl.valor AS plano_valor,
    pl.intervalo AS plano_intervalo,
    pl.limite_clientes,
    pl.limite_propostas,
    pl.limite_produtos,
    a.data_inicio,
    a.data_fim,
    p.contagem_clientes,
    p.contagem_propostas,
    p.contagem_produtos,
    CASE 
        WHEN p.contagem_clientes >= pl.limite_clientes THEN TRUE 
        ELSE FALSE 
    END AS limite_clientes_atingido,
    CASE 
        WHEN p.contagem_propostas >= pl.limite_propostas THEN TRUE 
        ELSE FALSE 
    END AS limite_propostas_atingido,
    CASE 
        WHEN p.contagem_produtos >= pl.limite_produtos THEN TRUE 
        ELSE FALSE 
    END AS limite_produtos_atingido
FROM 
    perfis p
LEFT JOIN 
    assinaturas a ON p.usuario_id = a.usuario_id AND a.status != 'cancelada'
LEFT JOIN 
    planos pl ON a.plano_id = pl.id;

-- --------------------------------------------------------
-- FUNÇÕES E TRIGGERS
-- --------------------------------------------------------

-- Função para atualizar as contagens quando um cliente é inserido/excluído
CREATE OR REPLACE FUNCTION atualizar_contagem_clientes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE perfis SET contagem_clientes = contagem_clientes + 1
        WHERE usuario_id = NEW.usuario_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE perfis SET contagem_clientes = contagem_clientes - 1
        WHERE usuario_id = OLD.usuario_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Função para atualizar as contagens quando uma proposta é inserida/excluída
CREATE OR REPLACE FUNCTION atualizar_contagem_propostas()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE perfis SET contagem_propostas = contagem_propostas + 1
        WHERE usuario_id = NEW.usuario_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE perfis SET contagem_propostas = contagem_propostas - 1
        WHERE usuario_id = OLD.usuario_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Verificar e criar trigger para contagem de clientes
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_atualizar_contagem_clientes'
    ) THEN
        CREATE TRIGGER trigger_atualizar_contagem_clientes
        AFTER INSERT OR DELETE ON clientes
        FOR EACH ROW
        EXECUTE FUNCTION atualizar_contagem_clientes();
    END IF;
END $$;

-- Verificar e criar trigger para contagem de propostas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_atualizar_contagem_propostas'
    ) THEN
        CREATE TRIGGER trigger_atualizar_contagem_propostas
        AFTER INSERT OR DELETE ON propostas
        FOR EACH ROW
        EXECUTE FUNCTION atualizar_contagem_propostas();
    END IF;
END $$;

-- --------------------------------------------------------
-- DADOS INICIAIS
-- --------------------------------------------------------

-- Inserir planos padrão se a tabela estiver vazia
INSERT INTO planos (stripe_price_id, nome, descricao, valor, intervalo, limite_clientes, limite_propostas, limite_produtos)
SELECT 'price_inicial_mensal', 'Plano Inicial', 'Ideal para profissionais em início de carreira', 29.90, 'month', 50, 100, 50
WHERE NOT EXISTS (SELECT 1 FROM planos);

INSERT INTO planos (stripe_price_id, nome, descricao, valor, intervalo, limite_clientes, limite_propostas, limite_produtos)
SELECT 'price_inicial_anual', 'Plano Inicial (Anual)', 'Ideal para profissionais em início de carreira', 299.00, 'year', 50, 100, 50
WHERE NOT EXISTS (SELECT 1 FROM planos WHERE intervalo = 'year');

INSERT INTO planos (stripe_price_id, nome, descricao, valor, intervalo, limite_clientes, limite_propostas, limite_produtos)
SELECT 'price_profissional_mensal', 'Plano Profissional', 'Para profissionais com carteira de clientes estabelecida', 59.90, 'month', 150, 300, 100
WHERE NOT EXISTS (SELECT 1 FROM planos WHERE nome = 'Plano Profissional');

INSERT INTO planos (stripe_price_id, nome, descricao, valor, intervalo, limite_clientes, limite_propostas, limite_produtos)
SELECT 'price_profissional_anual', 'Plano Profissional (Anual)', 'Para profissionais com carteira de clientes estabelecida', 599.00, 'year', 150, 300, 100
WHERE NOT EXISTS (SELECT 1 FROM planos WHERE nome = 'Plano Profissional (Anual)');

-- --------------------------------------------------------
-- ATUALIZAÇÃO DE ESTATÍSTICAS
-- --------------------------------------------------------

-- Atualizar contagens atuais para usuários existentes
WITH cliente_counts AS (
    SELECT usuario_id, COUNT(*) as count
    FROM clientes
    GROUP BY usuario_id
)
UPDATE perfis p
SET contagem_clientes = c.count
FROM cliente_counts c
WHERE p.usuario_id = c.usuario_id;

WITH proposta_counts AS (
    SELECT usuario_id, COUNT(*) as count
    FROM propostas
    GROUP BY usuario_id
)
UPDATE perfis p
SET contagem_propostas = c.count
FROM proposta_counts c
WHERE p.usuario_id = c.usuario_id;

-- --------------------------------------------------------
-- ÍNDICES PARA MELHORAR DESEMPENHO
-- --------------------------------------------------------

-- Índices nas tabelas de assinatura
CREATE INDEX IF NOT EXISTS idx_assinaturas_usuario_id ON assinaturas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_assinaturas_stripe_subscription_id ON assinaturas(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_assinaturas_status ON assinaturas(status);

-- Índices em pagamentos
CREATE INDEX IF NOT EXISTS idx_pagamentos_assinatura_id ON pagamentos(assinatura_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_stripe_invoice_id ON pagamentos(stripe_invoice_id);

-- Índice para consulta rápida de planos ativos
CREATE INDEX IF NOT EXISTS idx_planos_ativo ON planos(ativo);