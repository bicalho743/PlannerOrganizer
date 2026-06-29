---
name: st.dataframe selection + st.dialog reopen trap
description: Como abrir um st.dialog ao selecionar linha de st.dataframe sem reabrir em loop ao fechar
---

Ao usar `st.dataframe(on_select="rerun", selection_mode="single-row")` para abrir um
`@st.dialog` com os detalhes da linha selecionada, NÃO dispare a abertura só pela
presença de seleção: a seleção do dataframe persiste no session_state entre reruns,
então ao fechar o diálogo no "X" (que dispara rerun) o diálogo reabre em loop.

**Regra:** use um nonce de estado (ex.: `hist_dialog_pid`). Abra o diálogo só quando
`sel_pid != st.session_state['hist_dialog_pid']`; grave `sel_pid` nesse estado ao abrir;
zere para None quando nada estiver selecionado. Assim, fechar no "X" não reabre
(seleção continua igual), e selecionar outra linha abre o diálogo dela.

**Efeito colateral:** reabrir a MESMA linha exige trocar de seleção e voltar (não há
deselect nativo em single-row). Se precisar reabrir a mesma, ofereça um botão que
limpa a seleção via `st.session_state.pop('<df_key>', None)`.

**Mapeamento de índice:** `evento.selection.rows` retorna posições na ordem do
dataframe FONTE (não a ordem visual após clicar para ordenar). Mantenha uma lista
paralela `id_por_indice` na mesma ordem das linhas passadas ao dataframe.

**Por que importa:** evita o bug clássico "não consigo fechar o modal" e o
desalinhamento de qual proposta abriu após o usuário ordenar por coluna.
