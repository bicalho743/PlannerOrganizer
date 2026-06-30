---
name: Cache de propostas vs. finalização
description: get_propostas() cacheia por sessão; nem todo caminho de escrita invalida — leitura pode mostrar status antigo até o rerun.
---

`Database.get_propostas()` usa `set_cache`/`get_cache` (chave
`cache_propostas_{usuario_id}`) e devolve o DataFrame em cache enquanto ele
existir. `invalidar_cache()` limpa `cache_clientes/propostas/financeiro`.

**Gotcha:** nem todo caminho de escrita chama `invalidar_cache()`. Em
particular `criar_venda_de_proposta()` grava `status=finalizada` +
`status_execucao=Finalizada` no banco, mas NÃO invalida o cache de propostas.
No app real o cache morre no rerun do Streamlit, então some; mas em testes
(ou qualquer leitura na mesma sessão) `get_propostas_finalizadas()` pode
continuar enxergando a proposta como não-finalizada até invalidar.

**Why:** descoberto ao escrever o teste de integração da invariante
"finalizada = dois campos": o banco estava correto, mas a leitura via
`get_propostas` voltava em cache stale, fazendo o assert falhar.

**How to apply:** ao verificar estado pós-escrita de propostas fora de um
rerun do Streamlit, chame `db.invalidar_cache()` antes de reler. Se for
corrigir o produto, considere invalidar o cache dentro dos caminhos de
escrita que mudam status (ex.: venda) para não depender só do rerun.
