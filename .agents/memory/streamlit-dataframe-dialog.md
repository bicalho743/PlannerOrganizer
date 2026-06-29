---
name: st.dataframe seleção vs. ação explícita para abrir detalhes
description: Por que abrir detalhes por seleção de linha em st.dataframe é frágil/confuso; prefira botão explícito
---

Abrir um `@st.dialog` a partir da SELEÇÃO de linha de `st.dataframe(on_select="rerun")`
é frágil e confuso para o usuário:
- A "marca x"/checkbox de seleção não comunica que serve para abrir detalhes (usuários
  reclamam que "não dá para saber").
- A seleção persiste no session_state entre reruns, então fechar o diálogo reabre em
  loop; reabrir a MESMA linha exige trocar de seleção e voltar (não há deselect nativo).

**Regra durável:** use a tabela só para VISUALIZAÇÃO (ordenável pelo cabeçalho) e ofereça
uma AÇÃO EXPLÍCITA para abrir detalhes — `st.selectbox` (label "#nº — Cliente") + botão
"📋 Ver detalhes" que grava o id em um estado compartilhado (ex.: `kanban_selected_proposta`)
e dá `st.rerun()`.

**Por que funciona:** o diálogo compartilhado é renderizado a CADA run enquanto o estado
está setado, então os botões interativos internos (relatórios, excluir, reabrir) não somem
após reruns. Um botão "✖ Fechar" que zera o estado e dá rerun fecha de forma determinística,
sem depender da seleção do dataframe.

**Mapeamento de índice:** ao montar as linhas, mantenha uma lista paralela `id_por_indice`
na mesma ordem passada ao dataframe; construa as opções do selectbox por id estável, não
por posição visual (a ordenação por coluna muda a ordem exibida).

**Anti-padrão abandonado:** o nonce de estado (`hist_dialog_pid`) que só abria o diálogo no
clique inicial — qualquer rerun/botão interno fazia o conteúdo sumir. Não voltar a isso.
