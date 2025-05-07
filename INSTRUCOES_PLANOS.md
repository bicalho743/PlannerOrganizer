# Guia de Implementação de Planos e Checkout com Stripe

Este guia explica as diferentes abordagens para implementar a página de planos com integração ao Stripe, destacando a solução para o problema encontrado com os botões de checkout.

## O Problema
O erro #231 estava ocorrendo porque os manipuladores de eventos (onClick) estavam sendo passados como strings em vez de funções callback. Em React, isso é um erro comum que precisa ser corrigido.

## Solução Implementada

### 1. Correção dos onClick Handlers

O problema foi corrigido substituindo a antiga sintaxe:
```jsx
// Incorreto ❌
<button onClick="handleCheckout('mensal')">ASSINAR MENSAL</button>
```

Pela sintaxe correta usando arrow functions:
```jsx
// Correto ✅
<button onClick={() => handleCheckout('mensal')}>ASSINAR MENSAL</button>
```

### 2. Implementação da função handleCheckout com URLs diretas

A solução mais simples e direta é usar uma função handleCheckout que apenas redireciona para uma URL do Stripe:

```jsx
const handleCheckout = (url) => {
    window.location.href = url;
};

// Uso no botão
<button
    onClick={() => handleCheckout("https://buy.stripe.com/test_28og2t34LeLJ6mQ144")}
    className="w-full text-white bg-blue-500 hover:bg-blue-600 rounded-xl py-2"
>
    Assinar Mensal
</button>
```

### 3. Abordagem alternativa (mais complexa) com API

Como alternativa, também é possível implementar uma função assíncrona que utiliza axios para fazer a requisição HTTP:

```jsx
const handleCheckout = async (planType) => {
  setLoading(true);
  setError(null);
  
  try {
    // Importante: use axios.post para fazer a requisição ao endpoint
    const response = await axios.post('/api/create-checkout-session', {
      plan_type: planType,
    });
    
    // Redirecionar para a URL de checkout fornecida pelo Stripe
    window.location.href = response.data.url;
  } catch (err) {
    console.error('Erro ao iniciar sessão de checkout:', err);
    setError('Ocorreu um erro ao processar seu pedido. Por favor, tente novamente.');
  } finally {
    setLoading(false);
  }
};
```

## Abordagens Alternativas

Criamos múltiplas abordagens para implementar a página de planos:

### 1. Componente React (StripeCheckout.jsx)
Um componente React completo que utiliza a abordagem correta para os handlers de eventos e inclui gerenciamento de estado para loading e erros.

**Arquivo:** `src/components/StripeCheckout.jsx`

### 2. HTML Puro com Links Diretos do Stripe
Uma página HTML pura que utiliza links diretos do Stripe para checkout, eliminando a necessidade de JavaScript.

**Arquivo:** `planos_html.html`

### 3. Streamlit com Componente HTML
Uma implementação usando Streamlit que carrega o componente HTML puro.

**Arquivo:** `planos_leve.py`

### 4. Streamlit com Links Diretos
Implementação usando Streamlit com botões que apontam diretamente para os links do Stripe.

**Arquivo:** `planos_simplificado.py`

### 5. Utilidades para Facilitar a Integração
Funções utilitárias para facilitar a integração do Stripe em qualquer parte da aplicação.

**Arquivo:** `utils/stripe_links.py`

## URLs dos Planos Stripe

As URLs de checkout direto do Stripe são geradas no Dashboard do Stripe e nunca expiram, permitindo uma integração mais simples:

- **Plano Mensal:** `https://buy.stripe.com/test_28og2t34LeLJ6mQ144`
- **Plano Anual:** `https://buy.stripe.com/test_7sI7vRcJ56T29z8dQQ`
- **Plano Vitalício:** `https://buy.stripe.com/test_eVa2bv34L1Aw29yfYZ`

## Como Usar o Componente React StripeCheckout

1. Importe o componente:
   ```jsx
   import StripeCheckout from '@/components/StripeCheckout';
   ```

2. Adicione-o ao seu componente principal:
   ```jsx
   function App() {
     return (
       <div>
         <h1>Minha Aplicação</h1>
         <StripeCheckout />
       </div>
     );
   }
   ```

## Como Usar Links Diretos do Stripe em Streamlit

```python
import streamlit as st
from utils.stripe_links import exibir_planos_streamlit

# Configuração da página
st.set_page_config(
    page_title="Planos - Planner Organizer",
    page_icon="🏆",
    layout="centered"
)

# Exibir planos usando a função da utils/stripe_links.py
exibir_planos_streamlit()
```

## Recomendação

Para a maior compatibilidade e facilidade de manutenção, recomendamos usar a versão com links diretos do Stripe (abordagem 2 ou 4), pois essa solução:

1. Não depende de JavaScript complexo
2. Funciona em qualquer ambiente
3. Não requer atualizações constantes
4. Não apresenta problemas de CORS ou autenticação

Caso necessite de uma solução mais integrada com a aplicação, use o componente React com as correções implementadas.