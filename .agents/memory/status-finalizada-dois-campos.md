---
name: Propostas finalizadas exigem dois campos
description: Telas/filtros de "finalizadas" e a coluna Finalizada do kanban exigem status principal E status_execucao alinhados; qualquer caminho de fechamento deve setar AMBOS.
---

# Proposta "finalizada" depende de DOIS campos alinhados

Uma proposta só aparece nas telas de finalizadas / coluna Finalizada do kanban
quando **ambos** estão setados juntos:
- `status` (principal, lowercase canônico) = `finalizada`
- `status_execucao` (Title-case canônico) = `Finalizada`

**Why:** os filtros estritos (filtro_propostas, propostas_finalizadas) e o kanban
fazem AND dos dois campos. Caminhos que mudavam só um dos campos (ex.: venda
gravava `status_execucao='Vendida'` sem mexer no `status`; cadastro retroativo
gravava `status_execucao='Concluída'`) faziam a proposta "sumir" — nem em aberto,
nem em finalizada.

**How to apply:** todo fluxo de fechamento/venda/finalização deve setar os dois
campos em conjunto. Vocabulário canônico de `status_execucao` vive em
`utils/status_execucao.py` (use `normalize()` + constantes `EXEC_*`); o de
`status` em `utils/proposta_status.py` (`STATUS_*`). Legados mapeados:
`Concluída`/`Vendida`→`Finalizada`, `Iniciada`→`Em execução`.

Nos pontos de escrita (ORM e SQL direto), grave SEMPRE o status canônico
(`proposta_status.normalize`) e derive a fase com
`status_execucao.derive_exec_from_status(status)` quando o caller não passar
`status_execucao` explicitamente — assim os dois campos nunca divergem. Esses
endurecimentos só valem para gravações NOVAS; linhas antigas no banco podem
continuar híbridas até uma migração de dado.
