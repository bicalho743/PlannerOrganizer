---
name: Proposta status handling
description: Dual-field status model and the legacy-label vs canonical mismatch trap in Database methods
---

# Status de propostas: dois campos + armadilha de rótulos

- `proposta.status` guarda valores **canônicos snake_case** (`em_aberto`, `aprovada`, `recusada`, `em_execucao`, `finalizada`), definidos em `utils/proposta_status.py`. Sempre normalize com `normalize()` antes de comparar.
- `proposta.status_execucao` é um campo **separado** com strings de exibição (`'Não iniciada'`, `'Em execução'`, `'Finalizada'`, `'Cancelada'`). O kanban da coluna "Em Execução" filtra por `status_execucao == 'Em execução'`, NÃO por `status`.

**Why:** Vários métodos em `utils/database.py` (`update_proposta_status`, `add_proposta`, `atualizar_proposta`) historicamente comparavam `status` contra rótulos legados em pt-BR (`"Em execução"`, `"Aprovada"`, `"Em elaboração"`, `"Finalizada"`). Como a UI passa valores canônicos, essas comparações ficavam sempre falsas — ex.: "Iniciar Execução" gravava `status='em_execucao'` mas nunca setava `status_execucao='Em execução'`, fazendo a proposta sumir de todas as colunas do kanban.

**How to apply:** Em qualquer método que receba/compare status de proposta, normalize a entrada e compare com as constantes `STATUS_*`. Ao mudar para execução, lembre de setar TAMBÉM `status_execucao='Em execução'` (o kanban depende disso). `atualizar_proposta` (método legado) e o endpoint `PUT /propostas/{id}` em `api/router.py` ainda têm comparações/UPDATE-SQL legados não corrigidos — o endpoint também faz UPDATE direto sem filtrar por `usuario_id` (IDOR latente) e fora do fluxo web (a web chama `update_proposta_status` direto).
