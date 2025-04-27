# Alterações feitas no sistema

## Simplificação do filtro no Histórico Financeiro

Foi realizada a simplificação do filtro no histórico financeiro para mostrar apenas as opções "Receita" e "Despesa", em vez de exibir também "receita_a_receber" e "despesa_a_pagar".

### Arquivo modificado: `pages/financeiro.py`

#### Alteração 1: Modificação do filtro de tipos
```python
# Antes:
tipos_disponiveis = ["receita", "receita_a_receber", "despesa", "despesa_a_pagar"]

# Depois:
tipos_disponiveis = ["receita", "despesa"]
```

#### Alteração 2: Modificação nos cálculos de valores por tipo
```python
# Antes:
receitas = historico[historico['tipo'].isin(['receita', 'receita_a_receber'])]['valor'].sum()
despesas = historico[historico['tipo'].isin(['despesa', 'despesa_a_pagar'])]['valor'].sum()

# Depois:
receitas = historico[historico['tipo'] == 'receita']['valor'].sum()
despesas = historico[historico['tipo'] == 'despesa']['valor'].sum()
```

#### Alteração 3: Modificação no filtro para distribuição por tipo de receita
```python
# Antes:
receitas = financeiro[financeiro['tipo'].isin(['receita', 'receita_a_receber'])]

# Depois:
receitas = financeiro[financeiro['tipo'] == 'receita']
```

### Observações

- A função `formatar_tipo()` foi mantida para garantir compatibilidade com registros existentes, convertendo "receita_a_receber" para "Receita" e "despesa_a_pagar" para "Despesa"
- Os filtros na interface do usuário agora mostram apenas "Receita" e "Despesa" como opções
- Todos os cálculos e filtros agora consideram apenas os tipos simplificados