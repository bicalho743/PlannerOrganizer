"""
Script para injetar códigos de analytics diretamente no HTML da página
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_analytics_tags():
    """
    Injeta as tags do Google Analytics, Google Tag Manager e Facebook Pixel na página
    """
    
    # Código combinado de GA4 + GTM + Facebook Pixel
    analytics_code = """
    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-E9KP3F40VT"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-E9KP3F40VT');
    </script>
    
    <!-- Google Tag Manager -->
    <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','GTM-NM45ZQCD');</script>
    
    <!-- Facebook Pixel -->
    <script>
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', '654529850558184');
    fbq('track', 'PageView');
    </script>
    
    <!-- Brevo Tracking -->
    <script src="https://cdn.brevo.com/js/sdk-loader.js" async></script>
    <script>
        // Version: 2.0
        window.Brevo = window.Brevo || [];
        Brevo.push([
            "init",
            {
            client_key: "awheq5vyxe050fhs5oxcejmb",
            // Optional: Add other initialization options, see documentation
            }
        ]);
    </script>
    
    <!-- Noscript tags -->
    <noscript>
        <iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NM45ZQCD"
        height="0" width="0" style="display:none;visibility:hidden"></iframe>
        <img height="1" width="1" style="display:none"
        src="https://www.facebook.com/tr?id=654529850558184&ev=PageView&noscript=1" />
    </noscript>
    
    <script>
    // Verificação de carregamento das tags
    setTimeout(function() {
        if (typeof gtag !== 'undefined') {
            console.log('Google Analytics carregado com sucesso');
        }
        if (typeof dataLayer !== 'undefined') {
            console.log('DataLayer inicializado com sucesso');
        }
        if (typeof fbq !== 'undefined') {
            console.log('Facebook Pixel carregado com sucesso');
        }
        if (typeof Brevo !== 'undefined') {
            console.log('Brevo tracking carregado com sucesso');
        }
    }, 2000);
    </script>
    """
    
    # Injeta o código no head usando components.html
    components.html(analytics_code, height=0)

def track_page_view(page_name="Home"):
    """
    Rastreia uma visualização de página no Google Analytics e Facebook Pixel
    """
    tracking_script = """
    <script>
    setTimeout(function() {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view', {
                page_title: '""" + page_name + """',
                page_location: window.location.href
            });
            console.log('GA4 Page view tracked: """ + page_name + """');
        }
        
        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', 'PageView');
            console.log('Facebook Pixel PageView tracked: """ + page_name + """');
        }
    }, 1000);
    </script>
    """
    
    components.html(tracking_script, height=0)

def track_facebook_event(event_name, parameters=None):
    """
    Rastreia eventos específicos no Facebook Pixel
    
    Args:
        event_name (str): Nome do evento (ex: 'Lead', 'Purchase', 'AddToCart')
        parameters (dict): Parâmetros adicionais do evento
    """
    params_str = ""
    if parameters:
        import json
        params_str = f", {json.dumps(parameters)}"
    
    tracking_script = f"""
    <script>
    setTimeout(function() {{
        if (typeof fbq !== 'undefined') {{
            fbq('track', '{event_name}'{params_str});
            console.log('Facebook Pixel event tracked: {event_name}');
        }} else {{
            console.log('Facebook Pixel not available yet');
        }}
    }}, 500);
    </script>
    """
    
    components.html(tracking_script, height=0)