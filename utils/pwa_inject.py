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

    # Registrar Service Worker
    components.html("""
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/app/static/sw.js')
          .then(function(reg) { console.log('SW registrado:', reg.scope); })
          .catch(function(err) { console.log('SW erro:', err); });
      });
    }
    </script>
    """, height=0)