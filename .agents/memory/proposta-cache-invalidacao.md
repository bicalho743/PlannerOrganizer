---
name: Cache de propostas vs. finalização
description: get_propostas() cacheia por sessão; TODO caminho de escrita que muda status deve invalidar o cache, senão a leitura mostra status antigo até o rerun.
---

`Database.get_propostas()` usa `set_cache`/`get_cache` (chave
`cache_propostas_{usuario_id}`) e devolve o DataFrame em cache enquanto ele
existir. `invalidar_cache()` limpa `cache_clientes/propostas/financeiro` do
usuário.

**Regra durável:** todo caminho de escrita que altera o status de uma proposta
deve chamar `invalidar_cache()` (ou o equivalente, quando grava por conexão
direta). Caso contrário, na mesma sessão Streamlit a leitura volta em cache
stale e a proposta finalizada "some" do filtro de finalizadas até um rerun.

Caminhos que mudam status e precisam invalidar: `add_proposta`,
`criar_venda_de_proposta`, `update_proposta`, `atualizar_proposta` (métodos do
`Database`) e `finalizar_proposta_v2` (módulo separado que grava via psycopg2 —
invalida o cache do app importando `remove_cache` e limpando as chaves do
`usuario_id` após o commit).

**Why:** descoberto ao escrever o teste de integração da invariante
"finalizada = dois campos": o banco estava correto, mas a leitura via
`get_propostas` voltava em cache stale, fazendo o assert falhar. A venda em
particular nem invalidava o cache.

**How to apply:** ao criar um NOVO caminho de escrita que muda status de
proposta, invalide o cache no fim do caminho. Em testes, para provar essa
invariante, aqueça o cache com `db.get_propostas()` ANTES da escrita e releia
SEM invalidar manualmente (só `session.expire_all()` para o identity map do
ORM) — se faltar a invalidação no produto, o teste falha.
