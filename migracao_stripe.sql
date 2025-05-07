-- Script de migração para remover tabelas relacionadas ao Stripe
-- Criado em 07/05/2025

-- 1. Criar tabelas de backup primeiro
CREATE TABLE IF NOT EXISTS assinaturas_backup AS SELECT * FROM assinaturas;
CREATE TABLE IF NOT EXISTS planos_backup AS SELECT * FROM planos;
CREATE TABLE IF NOT EXISTS pagamentos_backup AS SELECT * FROM pagamentos;

-- 2. Remover tabelas originais relacionadas ao Stripe
DROP TABLE IF EXISTS assinaturas;
DROP TABLE IF EXISTS planos;
DROP TABLE IF EXISTS pagamentos;

-- Nota: As tabelas de backup foram mantidas para referência futura.
-- Para restaurar o estado original, use o script recreate_stripe_tables.sql