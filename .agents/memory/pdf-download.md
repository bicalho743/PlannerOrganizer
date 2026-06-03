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

# Como resolver
Oferecer VISUALIZAÇÃO inline dentro do app, sem depender de `file://`:
decodificar os bytes em um Blob no próprio documento do componente e
renderizar num `<iframe src=blobURL>` via `components.html`. Padrão usado:
helper `_pdf_inline_viewer()` em `pages/propostas_unificado.py`, exposto num
expander junto ao `st.download_button`.

Alternativa para o usuário: abrir o app numa aba própria do navegador (não
embutida) — aí o "abrir" do arquivo baixado funciona normalmente.

**Why:** o ambiente de execução real é frequentemente um iframe; qualquer
solução que dependa de o navegador abrir um arquivo local vai falhar.
**How to apply:** ao entregar arquivos binários (PDF) no Streamlit, prefira
download_button para baixar E um viewer inline via Blob para visualizar;
nunca dependa de abrir `file://`.
