# Checklist de Implantação para Integração com Stripe

## Pré-requisitos
- [ ] Criar conta no Stripe e configurar produtos/preços
- [ ] Obter as chaves de API do Stripe (chave pública e secreta)
- [ ] Configurar webhook no painel do Stripe
- [ ] Configurar IDs de preços para assinaturas mensais e anuais

## Configuração de Ambiente
- [ ] Configurar variável STRIPE_API_KEY
- [ ] Configurar variável STRIPE_WEBHOOK_SECRET
- [ ] Configurar variável STRIPE_PRICE_ID_MENSAL
- [ ] Configurar variável STRIPE_PRICE_ID_ANUAL
- [ ] Configurar variável APP_URL com URL da aplicação

## Banco de Dados
- [ ] Executar script de migração migracao_stripe.sql
- [ ] Verificar se as novas tabelas foram criadas corretamente
- [ ] Verificar se os índices foram criados corretamente
- [ ] Verificar se a view vw_status_assinatura foi criada corretamente

## Código
- [ ] Verificar se utils/stripe_integration.py está configurado corretamente
- [ ] Verificar se pages/stripe_webhook.py está configurado corretamente
- [ ] Verificar se a página de planos está chamando as funções de integração

## Testes
- [ ] Testar criação de assinatura com cartão de teste
- [ ] Verificar se o webhook está recebendo eventos
- [ ] Verificar se o status do plano é atualizado corretamente
- [ ] Testar cancelamento de assinatura
- [ ] Verificar se limites por plano estão sendo aplicados corretamente
        