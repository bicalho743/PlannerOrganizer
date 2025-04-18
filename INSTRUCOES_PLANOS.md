# Instruções de Integração com Planos de Assinatura

## Visão Geral

Este documento fornece instruções sobre como integrar os planos de assinatura do Planner Organizer com sua aplicação usando o Stripe. Foram criadas várias opções de implementação para dar flexibilidade na escolha do método que melhor se adapta às suas necessidades.

## Opções de Implementação

### 1. HTML Puro com Stripe.js

**Arquivos:**
- `api/static/index.html` - Página completa de planos com layout responsivo
- `api/static/checkout-simple.html` - Página simples de checkout

**Funcionamento:**
- Páginas HTML estáticas que usam JavaScript para se comunicar com a API do Stripe
- Design responsivo e pronto para produção
- Funciona com a API Stripe rodando em `/create-checkout-session`

**Para usar:**
- Coloque as páginas no diretório de arquivos estáticos do seu servidor web
- Substitua `pk_test_SUA_CHAVE_PUBLICA_DO_STRIPE` pela sua chave publicável do Stripe
- Certifique-se de que a API do Stripe esteja rodando e acessível

### 2. API FastAPI para Stripe

**Arquivos:**
- `api/stripe_integration.py` - API completa com todos os recursos do Stripe
- `api/stripe_simple.py` - Versão simplificada da API

**Endpoints Principais:**
- `/create-checkout-session` - Cria uma sessão de checkout para pagamento único
- `/create-checkout-session/{plan_id}` - Cria uma sessão para um plano específico (mensal, anual, vitalício)
- `/plans` - Retorna informações sobre os planos disponíveis
- `/subscription/{subscription_id}` - Obtém detalhes de uma assinatura

**Para usar:**
- Configure a variável de ambiente `STRIPE_API_KEY` com sua chave secreta do Stripe
- Execute a API com `uvicorn api.stripe_simple:app --host 0.0.0.0 --port 8001`
- Ou para a versão completa: `uvicorn api.stripe_integration:app --host 0.0.0.0 --port 8000`

### 3. Página Streamlit com Planos

**Arquivos:**
- `planos_minimal.py` - Interface Streamlit simplificada de planos
- `planos_landing.py` - Página completa de landing page com planos

**Para usar:**
- Execute `streamlit run planos_minimal.py`
- Certifique-se de que a API do Stripe esteja rodando para processamento de pagamentos

### 4. Helper para Integração Direta

**Arquivo:**
- `utils/stripe_helper.py` - Funções auxiliares para integração direta com o Stripe

**Principais funções:**
- `get_stripe_status()` - Verifica se o Stripe está configurado corretamente
- `format_price()` - Formata preços de acordo com a moeda
- `get_all_products_and_prices()` - Obtém produtos e preços do Stripe
- `create_checkout_session()` - Cria uma sessão de checkout
- `render_checkout_button()` - Cria botões de checkout no Streamlit

**Para usar:**
- Importe as funções necessárias em seu código
- Exemplo: `from utils.stripe_helper import render_checkout_button`
- Chame a função no seu aplicativo: `render_checkout_button('price_id', 'Assinar Agora')`

## Configuração do Ambiente

1. **Configurar Chaves do Stripe:**
   ```
   export STRIPE_API_KEY=sk_test_sua_chave_secreta
   export STRIPE_PUBLISHABLE_KEY=pk_test_sua_chave_publica
   ```

2. **Criar produtos e preços no Stripe:**
   - Crie 3 produtos: Mensal, Anual e Vitalício
   - Defina os preços recorrentes para mensal e anual
   - Defina um preço único para o plano vitalício

3. **Configurar Webhook (opcional):**
   - Configure um endpoint webhook no Stripe para receber notificações de eventos
   - Aponte para `/stripe-webhook` na sua API

## Preços Sugeridos

- **Plano Mensal**: R$ 9,70/mês
- **Plano Anual**: R$ 97,00/ano (economia de 17% em relação ao mensal)
- **Acesso Vitalício**: R$ 247,00 (pagamento único)

## Próximos Passos

1. Escolha uma das opções de implementação acima
2. Configure as chaves do Stripe no ambiente
3. Personalize os preços conforme necessário
4. Integre com o sistema de autenticação existente

## Observações Importantes

- A integração atual exige configuração das chaves do Stripe para funcionar corretamente
- Em ambiente de desenvolvimento, use as chaves de teste do Stripe
- Em produção, use as chaves de produção e certifique-se de que as URLs de redirecionamento estejam configuradas corretamente