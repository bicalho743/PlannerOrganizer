---
name: Proposta status handling
description: Modelo de dois campos de status de proposta e a armadilha de rótulos legados vs canônicos
---

# Status de propostas: dois campos + armadilha de rótulos

- `proposta.status` guarda valores **canônicos snake_case** (`em_aberto`, `aprovada`, `recusada`, `em_execucao`, `finalizada`), definidos em `utils/proposta_status.py`. Sempre normalize com `normalize()` antes de comparar — nunca compare contra rótulos pt-BR ("Aprovada", "Em execução", etc.).
- `proposta.status_execucao` é um campo **auxiliar separado** com strings de exibição (`'Não iniciada'`, `'Em execução'`, `'Concluída'`/`'Finalizada'`, `'Cancelada'`).

**Why (bug recorrente):** A coluna "Em Execução" do kanban dependia *só* de `status_execucao == 'Em execução'`. Quando algum caminho gravava `status='em_execucao'` mas não sincronizava `status_execucao` (ex.: app rodando código antigo, ou form que não setava o auxiliar), a proposta ficava num limbo: não casava em nenhuma coluna (aberto/aprovada/execução/finalizada) e **sumia inteira** do kanban. Já aconteceu com múltiplas propostas.

**How to apply:**
- A fonte de verdade para "em execução" é o `status` canônico (`STATUS_EM_EXECUCAO`). O kanban hoje filtra por `status == STATUS_EM_EXECUCAO` com *fallback* para `status_execucao == 'Em execução'` (helper `_mask_em_execucao` em `pages/propostas_unificado.py`). Mantenha esse padrão; não volte a filtrar coluna de execução só pelo auxiliar.
- Ao mover uma proposta para execução, ainda assim sete `status_execucao='Em execução'` (consumido por outras telas).
- Se aparecerem propostas "sumidas", procure por `status='em_execucao'` com `status_execucao` dessincronizado e repare o auxiliar.
- O endpoint `PUT /propostas/{id}` (`api/router.py`) faz UPDATE de status via SQL direto, sem normalização e sem filtrar por `usuario_id` (IDOR latente). Fora do fluxo web atual (a web chama `update_proposta_status` direto), mas corrigir se a API for exposta.
