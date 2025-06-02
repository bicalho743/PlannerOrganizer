"""
Implementação robusta do Google Analytics 4 para Streamlit
"""
import streamlit as st

def inject_ga4_head():
    """
    Injeta o Google Analytics 4 diretamente no head da página
    usando uma abordagem que funciona melhor com Streamlit
    """
    
    # Google Analytics 4 - Implementação direta
    ga4_script = """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-E9KP3F40VT"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-E9KP3F40VT');
    </script>
    """
    
    # Injeta usando st.markdown com unsafe_allow_html
    st.markdown(ga4_script, unsafe_allow_html=True)

def inject_ga4_verification():
    """
    Adiciona script de verificação para confirmar se o GA4 carregou
    """
    verification_script = """
    <script>
    // Verifica se o Google Analytics carregou
    setTimeout(function() {
        if (typeof gtag !== 'undefined') {
            console.log('✅ Google Analytics 4 carregado com sucesso');
            gtag('event', 'page_view', {
                page_title: document.title,
                page_location: window.location.href
            });
        } else {
            console.warn('❌ Google Analytics 4 não carregou');
        }
    }, 3000);
    </script>
    """
    st.markdown(verification_script, unsafe_allow_html=True)

def setup_google_analytics():
    """
    Configura o Google Analytics 4 completo
    """
    inject_ga4_head()
    inject_ga4_verification()