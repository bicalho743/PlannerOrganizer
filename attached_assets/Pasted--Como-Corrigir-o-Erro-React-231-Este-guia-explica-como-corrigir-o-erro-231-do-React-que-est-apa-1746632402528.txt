# Como Corrigir o Erro React #231

Este guia explica como corrigir o erro #231 do React que está aparecendo no console:

```
Uncaught Error: Minified React error #231; visit https://reactjs.org/docs/error-decoder.html?invariant=231&args[]=onClick&args[]=string for the full message or use the non-minified dev environment for full errors and additional helpful warnings.
```

## O Problema

Este erro ocorre quando você tenta passar uma string para o manipulador de eventos `onClick` no React, em vez de uma função. O React espera que os manipuladores de eventos sejam funções, não strings.

### Exemplo incorreto que causa o erro:

```jsx
// INCORRETO ❌ - Esta sintaxe causa o erro #231
<button onClick="handleCheckout('mensal')">
  Assinar Mensal
</button>
```

## A Solução

Altere todos os manipuladores de eventos para usar arrow functions (funções de flecha):

```jsx
// CORRETO ✅ - Esta sintaxe funciona no React
<button onClick={() => handleCheckout('mensal')}>
  Assinar Mensal
</button>
```

## Como Implementar a Solução

Você tem duas opções:

### Opção 1: Usar o Componente Corrigido

Se você estiver usando React, substitua seu componente atual pelo novo componente corrigido:

1. Importe o componente em vez de usar o código atual:

```jsx
import PlanosSolucao from './components/PlanosSolucao';

// Em seu renderizador:
return (
  <div>
    <PlanosSolucao />
  </div>
);
```

### Opção 2: Usar Links Diretos para o Stripe sem React

Você pode usar HTML puro com links diretos para o Stripe:

1. Abra o arquivo `planos_direct.html` que criamos
2. Copie o código HTML e use-o diretamente em sua página
3. Essa abordagem evita o JavaScript completamente, usando apenas links HTML

## Arquivos Prontos para Uso

- `src/components/PlanosSolucao.jsx` - Componente React corrigido
- `planos_direct.html` - Versão HTML pura sem JavaScript

## Localizando Outras Instâncias do Problema

Se o erro persistir, você precisa encontrar todos os locais com o problema:

1. Procure em seu código por `onClick="` (com aspas)
2. Substitua por `onClick={() => ...}`

## Importante

Lembre-se que no React, manipuladores de eventos:
- Usam camelCase (onClick, onChange, etc.)
- Devem receber funções, não strings
- Quando precisam passar parâmetros, devem usar arrow functions:
  `onClick={() => minhaFuncao(param)}`