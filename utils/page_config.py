import streamlit as st

def apply_page_header(page_title=None, breadcrumb_items=None):
    """
    Aplica um cabeçalho padronizado em todas as páginas do sistema.

    Args:
        page_title: Título da página atual
        breadcrumb_items: Lista de itens para o breadcrumb ['Home', 'Seção', 'Página Atual']
    """

    # SOLUÇÃO CONSOLIDADA: Juntar todos os scripts HTML em um único bloco
    combined_html = """
    <!-- SEO Meta Tags -->
    <meta name="description" content="Sistema Profissional de Gestão Personal Organizer - Planner Organizer">
    <meta name="keywords" content="personal organizer, gestão, organização, planejamento">
    <meta name="author" content="Planner Organizer">
    <meta property="og:title" content="Planner Organizer - Sistema Profissional">
    <meta property="og:description" content="Sistema completo para Personal Organizers">

    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX');
    </script>

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
      fbq('init', 'YOUR_PIXEL_ID');
      fbq('track', 'PageView');
    </script>

    <!-- Module Fix for Render -->
    <script>
      if (typeof window !== 'undefined') {
        window.global = window;
        if (typeof process === 'undefined') {
          window.process = { env: {} };
        }
      }
    </script>
    """

    # OTIMIZAÇÃO: Cache scripts pesados para evitar re-execução
    if 'scripts_injected' not in st.session_state:
        st.components.v1.html(combined_html, height=0, width=0)
        st.session_state.scripts_injected = True

    # CSS para esconder o contêiner dos iframes
    st.markdown("""
    <style>
    /* Esconder contêineres de iframes */
    iframe[title='st.iframe'] { display: none !important; }
    iframe[title='st.iframe'] + div { display: none !important; }

    /* Cabeçalho fixo otimizado */
    .app-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background-color: #1E2547;
        padding: 0.3rem 0.8rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        font-family: "Poppins", sans-serif;
        min-height: 60px;
        max-height: 60px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Ajuste do conteúdo principal - colado no cabeçalho */
    .main .block-container {
        margin-top: calc(var(--header-height, 60px) + 2px) !important;
        padding-top: 0 !important;
    }

    /* Remove header nativo do Streamlit */
    header[data-testid="stHeader"] { 
        display: none !important; 
        height: 0 !important; 
        margin: 0 !important; 
        padding: 0 !important; 
    }

    /* Reset completo de espaçamentos */
    [data-testid="stAppViewContainer"] > div:first-child,
    [data-testid="stAppViewContainer"] > section:first-of-type,
    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important; 
        margin-top: 0 !important; 
    }

    /* Esconder elementos vazios que criam espaçamento */
    .element-container:empty,
    .stElementContainer:empty,
    [data-testid="element-container"]:empty {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Responsividade do cabeçalho */
    @media (max-width: 768px) {
        .app-header {
            min-height: 50px;
            max-height: 50px;
            --header-height: 50px;
        }
        .main .block-container {
            margin-top: calc(var(--header-height, 50px) + 1px) !important;
        }
        
        /* OCULTAR TEXTO DO CABEÇALHO NO MOBILE */
        .app-header h2,
        .app-header p {
            display: none !important;
        }
        
        /* Centralizar área do usuário quando texto está oculto */
        .app-header > div:last-child {
            margin-left: 0 !important;
            flex: 1 !important;
            display: flex !important;
            justify-content: center !important;
        }
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        background-color: #1E2547 !important;
    }

    [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: rgba(255,255,255,0.8) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        border-radius: 12px !important;
        margin: 4px 0 !important;
        padding: 12px 16px !important;
    }

    [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255,255,255,0.15) !important;
        border-color: rgba(255,255,255,0.3) !important;
        color: rgba(255,255,255,1) !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3), 0 0 20px rgba(255,255,255,0.1) !important;
    }

    /* Boas-vindas */
    .user-welcome {
        position: absolute;
        top: 0.5rem;
        right: 1rem;
        font-size: 0.85rem;
        color: #1E366F;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 0.3rem 0.7rem;
        border-radius: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        font-family: "Poppins", sans-serif;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

    nome_usuario = "Usuário"
    if "usuario" in st.session_state and st.session_state.usuario:
        if isinstance(st.session_state.usuario, dict) and "nome" in st.session_state.usuario:
            nome_usuario = st.session_state.usuario["nome"]
        elif hasattr(st.session_state.usuario, "nome"):
            nome_usuario = st.session_state.usuario.nome

    from datetime import datetime, timezone, timedelta
    fuso_brasilia = timezone(timedelta(hours=-3))
    data_atual = datetime.now(fuso_brasilia)
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_formatada = f"{data_atual.day} de {meses[data_atual.month-1]} de {data_atual.year}"

    st.markdown(f"""
    <div class="app-header">
        <div style="flex: 1;">
            <h2 style="color: rgba(255,255,255,0.95); margin: 0; padding: 0; font-family: 'Poppins', sans-serif; font-size: 1.3rem; font-weight: 600; line-height: 1.2;">Planner Organizer</h2>
            <p style="color: rgba(255,255,255,0.85); margin: 0; padding: 0; font-size: 0.8rem; font-family: 'Poppins', sans-serif; line-height: 1.2;">
                Sistema Profissional de Gestão Personal Organizer
            </p>
        </div>
        <div style="background-color: rgba(255,255,255,0.15); padding: 0.3rem 0.8rem; border-radius: 0.8rem; text-align: center; border: 1px solid rgba(255,255,255,0.2); margin-left: 1rem;">
            <span style="color: rgba(255,255,255,0.95); font-size: 0.75rem; font-family: 'Poppins', sans-serif; display: block; font-weight: 500;">Bem-vindo(a), {nome_usuario}</span>
            <span style="color: rgba(255,255,255,0.8); font-size: 0.7rem; font-family: 'Poppins', sans-serif; display: block;">📅 {data_formatada}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if breadcrumb_items:
        breadcrumb_html = '<div class="page-breadcrumb">'
        for item in breadcrumb_items:
            breadcrumb_html += f'<span class="breadcrumb-item">{item}</span>'
        breadcrumb_html += '</div>'
        st.markdown(breadcrumb_html, unsafe_allow_html=True)
    elif page_title:
        breadcrumb_html = f'<div class="page-breadcrumb"><span class="breadcrumb-item">📊 {page_title}</span></div>'
        st.markdown(breadcrumb_html, unsafe_allow_html=True)

def apply_page_footer():
    """
    Aplica um rodapé padronizado em todas as páginas do sistema
    """
    footer_css = """
    <style>
    .footer-container {
        position: fixed; bottom: 0; left: 280px; right: 0;
        background-color: #1E2547;
        color: white;
        padding: 12px 20px; text-align: center;
        font-size: 13px; z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    @media screen and (max-width: 768px) {
        .footer-container {
            left: 0;
        }
    }
    .footer-container a {
        color: #7AB8FF; text-decoration: none; margin: 0 5px;
    }
    .footer-container a:hover {
        color: #ffffff; text-decoration: underline;
    }
    .main .block-container { padding-bottom: 50px !important; margin-bottom: 0px !important; }
    [data-testid="stAppViewContainer"] .main { margin-bottom: 0px !important; }
    body { margin-bottom: 0px !important; padding-bottom: 0px !important; }
    </style>
    """
    st.markdown(footer_css, unsafe_allow_html=True)

    footer_html = """
    <div class="footer-container">
        © 2025 Planner Organizer. Todos os direitos reservados. | 
        <a href="https://plannerorganiza.com.br/?show_termos=true" target="_blank">Termos de Uso</a> | 
        <a href="https://plannerorganiza.com.br/?show_politica=true" target="_blank">Política de Privacidade</a> | 
        Contato: contato@plannerorganiza.com.br
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)