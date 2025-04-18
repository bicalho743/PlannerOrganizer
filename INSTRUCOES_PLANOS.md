# Instruções para Implementação da Seção de Planos

Este documento explica como integrar a nova seção de planos com destaque visual no seu aplicativo Planner Organizer.

## O que foi implementado

1. **Módulo de Planos Completo**
   - Criamos um módulo reutilizável em `utils/planos.py` que pode ser facilmente integrado em qualquer página
   - Inclui design moderno com cartões de planos e destaque visual no plano anual (plano do meio)
   - Todos os planos contêm informações precisas sobre valores e benefícios

2. **Seção de Benefícios**
   - Grid visual de 4 benefícios principais com ícones
   - Destaque para as funcionalidades mais valorizadas pelos clientes

3. **Design Otimizado**
   - Cartão do plano do meio (anual) com destaque visual e etiqueta "RECOMENDADO"
   - Efeitos de hover e animações sutis para melhor experiência do usuário
   - Layout totalmente responsivo (adapta-se a dispositivos móveis)

4. **Botões Prontos para Stripe**
   - Implementação pronta para integração com pagamentos Stripe
   - Redirecionamento para páginas de checkout (basta adicionar as URLs do Stripe)

## Como Integrar no Seu Aplicativo

### Opção 1: Importar o módulo no app.py (Recomendado)

Para incorporar a seção de planos diretamente na sua página de login, adicione o seguinte código ao seu arquivo `app.py`:

```python
# Importar o módulo de planos
from utils.planos import mostrar_planos

# Na parte onde você quer mostrar os planos (após o login ou em uma aba separada)
mostrar_planos(
    com_titulo=True,
    com_prova_social=True,
    com_teste_gratis=True,
    com_destaque_plano_medio=True,
    stripe_ready=True
)
```

### Opção 2: Página Independente

Você também pode manter uma página separada apenas para os planos:

1. Use o arquivo `planos_landing.py` ou `planos_simple.py` como ponto de partida
2. Configure um workflow separado para esta página
3. Crie links do seu app principal para esta página

## Parâmetros Personalizáveis

O módulo `mostrar_planos()` aceita os seguintes parâmetros:

- `com_titulo`: Se True, exibe o título principal "Escolha o Plano Ideal..."
- `com_prova_social`: Se True, exibe os depoimentos de clientes
- `com_teste_gratis`: Se True, exibe a seção de teste gratuito
- `com_destaque_plano_medio`: Se True, destaca visualmente o plano anual
- `stripe_ready`: Se True, adiciona funcionalidade aos botões para integração com Stripe

## Integração com Stripe

Para conectar os botões ao Stripe:

1. Crie produtos e preços no seu painel do Stripe
2. Substitua as ações dos botões pelo código de redirecionamento para o Stripe
3. Exemplo de integração:

```python
if btn_mensal:
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1234567890',  # ID do preço no Stripe
            'quantity': 1,
        }],
        mode='subscription',
        success_url='https://seusite.com/success',
        cancel_url='https://seusite.com/cancel',
    )
    st.markdown(f"""
    <script>
    window.location.href = '{checkout_session.url}';
    </script>
    """, unsafe_allow_html=True)
```

## Arquivos Incluídos

1. `utils/planos.py` - Módulo principal com a implementação da seção de planos
2. `planos_simple.py` - Versão simplificada e independente da página de planos
3. `planos_landing.py` - Versão completa da landing page com planos
4. `app_planos_layout.py` - Exemplo de como integrar no app.py principal

## Suporte

Para qualquer dúvida sobre a implementação, entre em contato com o suporte.