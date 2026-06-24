"""
Cole essa função no utils/pwa_inject.py e chame inject_pwa()
no início do app.py logo após o st.set_page_config()
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_pwa():
    """Injeta os meta tags e service worker para PWA."""
    st.markdown("""
    <link rel="manifest" href="/app/static/manifest.json"/>
    <meta name="mobile-web-app-capable" content="yes"/>
    <meta name="apple-mobile-web-app-capable" content="yes"/>
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
    <meta name="apple-mobile-web-app-title" content="Planner Organiza"/>
    <meta name="theme-color" content="#C9A84C"/>
    <link rel="apple-touch-icon" href="/app/static/icon-192.png"/>
    <link rel="icon" type="image/png" sizes="192x192" href="/app/static/icon-192.png"/>
    """, unsafe_allow_html=True)

    # Kill-switch do Service Worker:
    # O SW antigo (planner-v1) cacheava o app shell do Streamlit. Como o
    # Streamlit usa assets com hash no nome, após cada atualização o index
    # cacheado aponta para arquivos inexistentes -> tela em branco / "não
    # carrega". Aqui removemos qualquer SW registrado e limpamos os caches
    # para garantir que o navegador sempre busque a versão atual.
    components.html("""
    <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations()
        .then(function(regs) { regs.forEach(function(r) { r.unregister(); }); })
        .catch(function() {});
    }
    if (window.caches && caches.keys) {
      caches.keys()
        .then(function(keys) { keys.forEach(function(k) { caches.delete(k); }); })
        .catch(function() {});
    }
    </script>
    """, height=0)