"""
Script para injetar códigos de analytics diretamente no HTML da página
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_analytics_tags():
    """
    Injeta as tags do Google Analytics e Google Tag Manager diretamente no head da página
    """
    
    # Código combinado de GA4 + GTM
    analytics_code = """
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-E9KP3F40VT"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-E9KP3F40VT');
    </script>
    
    <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','GTM-NM45ZQCD');</script>
    
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NM45ZQCD"
    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
    
    <script>
    // Verificação de carregamento das tags
    setTimeout(function() {
        if (typeof gtag !== 'undefined') {
            console.log('Google Analytics carregado com sucesso');
        }
        if (typeof dataLayer !== 'undefined') {
            console.log('DataLayer inicializado com sucesso');
        }
    }, 2000);
    </script>
    """
    
    # Injeta o código no head usando components.html
    components.html(analytics_code, height=0)

def track_page_view(page_name="Home"):
    """
    Rastreia uma visualização de página
    """
    tracking_script = """
    <script>
    setTimeout(function() {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view', {
                page_title: '""" + page_name + """',
                page_location: window.location.href
            });
            console.log('Page view tracked: """ + page_name + """');
        } else {
            console.log('gtag not available yet');
        }
    }, 1000);
    </script>
    """
    
    components.html(tracking_script, height=0)