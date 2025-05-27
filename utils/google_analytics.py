"""
Utilitário para integração do Google Analytics 4 (GA4) com Streamlit
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_ga4(measurement_id="G-E9KP3F40VT"):
    """
    Injeta o código do Google Analytics 4 na aplicação Streamlit
    
    Args:
        measurement_id (str): ID de medição do GA4
    """
    
    ga4_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{measurement_id}');
    </script>
    """
    
    # Injeta o código GA4 no head da página
    components.html(ga4_code, height=0)

def inject_gtm(gtm_id="GTM-NM45ZQCD"):
    """
    Injeta o código do Google Tag Manager na aplicação Streamlit
    
    Args:
        gtm_id (str): ID do Google Tag Manager
    """
    
    # Código GTM para o head
    gtm_head_code = f"""
    <!-- Google Tag Manager -->
    <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
    new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    }})(window,document,'script','dataLayer','{gtm_id}');</script>
    <!-- End Google Tag Manager -->
    """
    
    # Código GTM para o body (noscript)
    gtm_body_code = f"""
    <!-- Google Tag Manager (noscript) -->
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm_id}"
    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
    <!-- End Google Tag Manager (noscript) -->
    """
    
    # Injeta ambos os códigos
    components.html(gtm_head_code, height=0)
    components.html(gtm_body_code, height=0)

def track_page_view(page_name=None, page_title=None):
    """
    Rastreia uma visualização de página no GA4
    
    Args:
        page_name (str): Nome da página
        page_title (str): Título da página
    """
    
    if not page_name:
        page_name = st.get_option("browser.gatherUsageStats")
    
    if not page_title:
        page_title = "Planner Organizer"
    
    tracking_code = f"""
    <script>
      if (typeof gtag !== 'undefined') {{
        gtag('config', 'G-E9KP3F40VT', {{
          page_title: '{page_title}',
          page_location: window.location.href
        }});
      }}
    </script>
    """
    
    components.html(tracking_code, height=0)

def track_event(event_name, event_parameters=None):
    """
    Rastreia um evento personalizado no GA4
    
    Args:
        event_name (str): Nome do evento
        event_parameters (dict): Parâmetros do evento
    """
    
    if event_parameters is None:
        event_parameters = {}
    
    # Converter parâmetros para string JavaScript
    params_str = "{"
    for key, value in event_parameters.items():
        if isinstance(value, str):
            params_str += f"'{key}': '{value}', "
        else:
            params_str += f"'{key}': {value}, "
    params_str = params_str.rstrip(", ") + "}"
    
    event_code = f"""
    <script>
      if (typeof gtag !== 'undefined') {{
        gtag('event', '{event_name}', {params_str});
      }}
    </script>
    """
    
    components.html(event_code, height=0)

def initialize_ga4():
    """
    Inicializa o Google Analytics 4 e Google Tag Manager para a aplicação
    Deve ser chamado no início de cada página
    """
    # Injeta o GA4 e GTM apenas uma vez por sessão
    if 'ga4_initialized' not in st.session_state:
        inject_ga4()
        inject_gtm()
        st.session_state.ga4_initialized = True