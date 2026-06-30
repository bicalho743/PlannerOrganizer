---
name: PDF download/view em Streamlit embutido
description: Por que PDFs "não abrem" (file:// ERR_FAILED) e como entregar de forma confiável
---

# Sintoma
Usuária relata que o PDF "não gera" / mostra no navegador:
`file:///C:/Users/.../Downloads/Algo (3).pdf — ERR_FAILED`.

# Causa real
O PDF É gerado e baixado com sucesso (o sufixo "(N)" no nome prova várias
cópias na pasta Downloads). O erro `file://` acontece quando o navegador
tenta ABRIR o arquivo já baixado de dentro do app embutido em iframe
(preview do Replit, ou app dentro de outro iframe). Um iframe não navega
para `file://`. Logo, a falha é no ABRIR, não no baixar.

**Por isso trocar o mecanismo de download (anchor data-URI ↔ st.download_button)
NÃO resolve esse erro** — ambos baixam para Downloads e o "abrir" continua
falhando no contexto embutido.

# Cuidado de performance
`components.html` (e qualquer viewer inline) renderiza mesmo dentro de
`st.expander` colapsado — o iframe carrega na hora. Em telas com VÁRIOS
relatórios (ex.: 4 cards de PDF por proposta), isso faz a página "não
carregar" (trava/pesada). Sempre tornar o viewer SOB DEMANDA: gate com
`st.toggle`/`st.checkbox` e só chamar `components.html` quando ativado.

# Como resolver
NÃO usar `data:`/`blob:null`/`file://`: o componente roda num iframe `srcdoc`
de origem nula e o Chrome BLOQUEIA renderizar PDF (plugin nativo) via esses
esquemas ali — `<object>/<embed>` com `data:` URI = tela vazia = "não funciona",
e o link de fallback `data:` também não abre em nova aba.

Para documentos PRIVADOS (app multi-tenant), NÃO servir de `static/` (é
público e sem auth; URL adivinhável = vazamento entre usuários). Em vez disso,
renderizar com **pdf.js** (canvas) a partir dos BYTES embutidos (base64) no
próprio `components.html`: os bytes só chegam ao navegador do dono logado, nada
vira arquivo público. "Abrir em nova aba" = `window.open` + render com pdf.js
na nova aba (sandbox do Streamlit permite popups). Sob `st.toggle` (sob
demanda). Helper: `_pdf_inline_viewer(pdf_bytes, key, height)` em
`pages/propostas_unificado.py`. O `st.download_button` (bytes autenticados) já
cobre o "baixar".

**Armadilha do static serving para libs JS:** `/app/static/...` responde com
`Content-Type: text/plain` + `X-Content-Type-Options: nosniff`, então o
navegador RECUSA executar um `.js` servido de `static/` via `<script src>`.
Por isso pdf.js é carregado do CDN (lib pública; nenhum dado de usuário vai
ao CDN). Não adianta baixar pdf.js para `static/` e apontar `<script>` pra lá.

Alternativa para o usuário: abrir o app numa aba própria do navegador (não
embutida) — aí o "abrir" do arquivo baixado funciona normalmente.

**Why:** o ambiente de execução real é frequentemente um iframe; qualquer
solução que dependa de o navegador abrir um arquivo local vai falhar.
**How to apply:** ao entregar arquivos binários (PDF) no Streamlit, prefira
download_button para baixar E um viewer inline via Blob para visualizar;
nunca dependa de abrir `file://`.
