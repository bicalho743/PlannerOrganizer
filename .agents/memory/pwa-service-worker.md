---
name: PWA Service Worker quebrava o carregamento do app
description: "App não carrega" só em alguns navegadores — causa e fix do service worker
---

# Sintoma
"A aplicação não está carregando" / tela em branco — mas SÓ no navegador do
usuário. Em carga limpa (browser headless/screenshot, aba anônima) o app
abre normal. Console mostrava `SW erro: ... unsupported MIME type
('text/plain')`.

# Causa
Havia um service worker (`static/sw.js`, cache `planner-v1`) registrado por
`utils/pwa_inject.py`. Ele cacheava o app shell do Streamlit. O Streamlit
serve assets com HASH no nome; a cada atualização/restart o index cacheado
aponta para arquivos que não existem mais -> tela em branco. O registro até
falhava (MIME text/plain), mas SWs antigos já instalados continuavam ativos
servindo cache velho.

# Fix (kill-switch)
Em `inject_pwa()`, em vez de registrar o SW, rodar SEMPRE um script que
`navigator.serviceWorker.getRegistrations()` -> `unregister()` em todos e
`caches.keys()` -> `caches.delete()` em todos. Isso força o navegador a
buscar a versão atual. Confirmação: a linha `SW erro` some do console.

**Why:** PWA com cache de app shell + assets versionados por hash =
combinação que quebra SPAs após cada deploy/restart.
**How to apply:** ao ver "não carrega só pra mim/usuário" num app Streamlit
com PWA, suspeitar de SW em cache; preferir kill-switch a tentar consertar o
cache. Usuário precisa recarregar UMA vez para o kill-switch rodar.
