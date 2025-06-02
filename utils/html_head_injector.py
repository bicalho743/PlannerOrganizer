"""
Injeta código HTML diretamente no head da página usando uma abordagem mais robusta
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_head_content():
    """
    Injeta todo o conteúdo necessário no head da página de uma só vez
    """
    
    head_content = """
    <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-E9KP3F40VT"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-E9KP3F40VT');
        </script>
        
        <!-- Meta tags SEO -->
        <meta name="description" content="Organize clientes, propostas e finanças em um só lugar. Sistema completo para Personal Organizers. Teste grátis por 7 dias!">
        <meta name="keywords" content="personal organizer, sistema organizador, gestão clientes, propostas, organização profissional">
        <meta name="author" content="Planner Organizer">
        <meta property="og:title" content="Planner Organizer | Sistema para Personal Organizers">
        <meta property="og:description" content="Organize clientes, propostas e finanças em um só lugar. Sistema completo para Personal Organizers. Teste grátis por 7 dias!">
        <meta property="og:type" content="website">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Planner Organizer | Sistema para Personal Organizers">
        <meta name="twitter:description" content="Organize clientes, propostas e finanças em um só lugar. Sistema completo para Personal Organizers. Teste grátis por 7 dias!">
    </head>
    
    <script>
    // Adiciona os elementos diretamente ao head da página
    (function() {
        // Verifica se já foi injetado
        if (document.querySelector('meta[name="ga-injected"]')) {
            return;
        }
        
        // Marca como injetado
        var marker = document.createElement('meta');
        marker.name = 'ga-injected';
        marker.content = 'true';
        document.head.appendChild(marker);
        
        // Carrega Google Analytics
        var gaScript = document.createElement('script');
        gaScript.async = true;
        gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-E9KP3F40VT';
        document.head.appendChild(gaScript);
        
        // Configura Google Analytics
        var gaConfig = document.createElement('script');
        gaConfig.innerHTML = `
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-E9KP3F40VT');
            console.log('Google Analytics carregado via head injection');
        `;
        document.head.appendChild(gaConfig);
        
        // Verifica carregamento após 3 segundos
        setTimeout(function() {
            if (typeof gtag !== 'undefined') {
                console.log('✅ Google Analytics funcionando corretamente');
                gtag('event', 'page_view', {
                    page_title: document.title,
                    page_location: window.location.href
                });
            } else {
                console.warn('❌ Google Analytics ainda não carregou');
            }
        }, 3000);
    })();
    </script>
    """
    
    # Injeta usando components.html com altura 0
    components.html(head_content, height=0)