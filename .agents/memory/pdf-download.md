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
Oferecer VISUALIZAÇÃO inline dentro do app por uma URL REAL servida pelo
Streamlit (NÃO `data:`/`blob:null`/`file://`). O componente roda num iframe
`srcdoc` de origem nula; Chrome BLOQUEIA renderizar PDF via `data:`/`blob:null`
ali (inclusive o link de fallback `data:` não abre em nova aba). Tentar
`<object>/<embed>` com `data:` URI = tela vazia = "não funciona".

Solução confiável: `enableStaticServing = true` + gravar o PDF em `static/pdfs/`
→ servido em `/app/static/pdfs/<arquivo>.pdf`. No `components.html`, computar a
ORIGEM absoluta no cliente (`window.location.ancestorOrigins[0]` ou
`document.referrer`, pois srcdoc não resolve URL relativa) e carregar a URL
real num `<iframe>`; o mesmo URL serve para "Abrir em nova aba". Nome de arquivo
estável por proposta/tipo para sobrescrever (sem acúmulo). Helpers:
`_serve_pdf_static()` + `_pdf_inline_viewer(static_rel_url, ...)` em
`pages/propostas_unificado.py`, sob `st.toggle` (carregamento sob demanda).

Alternativa para o usuário: abrir o app numa aba própria do navegador (não
embutida) — aí o "abrir" do arquivo baixado funciona normalmente.

**Why:** o ambiente de execução real é frequentemente um iframe; qualquer
solução que dependa de o navegador abrir um arquivo local vai falhar.
**How to apply:** ao entregar arquivos binários (PDF) no Streamlit, prefira
download_button para baixar E um viewer inline via Blob para visualizar;
nunca dependa de abrir `file://`.
