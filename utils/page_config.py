import streamlit as st

def apply_page_header():
    """
    Aplica um cabeçalho padronizado em todas as páginas do sistema
    """
    # CSS para colocar o cabeçalho mais próximo do topo da página
    # e padronizar o espaçamento dos elementos da interface
    header_css = """
    <style>
    /* Reduzir o espaço acima do cabeçalho */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: 0 !important;
    }
    
    /* Garantir que o header do Streamlit não interfira */
    header[data-testid="stHeader"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Remove espaços extras no topo do corpo da página */
    [data-testid="stAppViewContainer"] > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Ajusta o topo da área principal */
    [data-testid="stAppViewContainer"] > section:first-of-type {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Ajusta a barra lateral para minimizar espaçamento */
    [data-testid="stSidebar"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Reduz espaçamento nos elementos da barra lateral */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Ajusta dimensões da barra lateral */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Garante que títulos em todas as páginas tenham o mesmo estilo e espaçamento */
    h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        font-family: "Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    </style>
    """
    
    # Aplicar CSS para ajustar espaçamento
    st.markdown(header_css, unsafe_allow_html=True)
    
    # Adicionando o cabeçalho no topo da página - mais compacto
    st.markdown("""
    <div style="background-color: #1E366F; padding: 0.7rem; border-radius: 0.5rem; margin-bottom: 0.7rem; text-align: center;">
        <h2 style="color: white; margin: 0; padding: 0; font-family: 'Poppins', sans-serif; font-size: 1.5rem;">Planner Organizer</h2>
        <p style="color: #E3F2FD; margin: 0.15rem 0 0 0; padding: 0; font-size: 0.85rem; font-family: 'Poppins', sans-serif;">
            Sistema Profissional de Gestão Personal Organizer
        </p>
        <p style="color: #BBD8FF; margin: 0.3rem 0 0 0; padding: 0; font-size: 0.75rem; font-family: 'Poppins', sans-serif; font-style: italic;">
            "Transforme sua organização em resultados: gerencie propostas, clientes e finanças com precisão profissional."
        </p>
    </div>
    """, unsafe_allow_html=True)

def apply_page_footer():
    """
    Aplica um rodapé padronizado em todas as páginas do sistema
    """
    # CSS para posicionar o rodapé na parte inferior da página
    footer_css = """
    <style>
    .footer-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #f5f7fa;
        padding: 10px 20px;
        text-align: center;
        border-top: 1px solid #eaeaea;
        font-size: 0.85rem;
        color: #5A6A85;
        z-index: 999;
    }
    
    .footer-container a {
        color: #1E366F;
        text-decoration: none;
    }
    
    .footer-container a:hover {
        text-decoration: underline;
    }
    
    /* Adicionar espaço no final da página para evitar que o conteúdo fique escondido pelo rodapé */
    .main .block-container {
        padding-bottom: 50px;
    }
    </style>
    """
    
    # HTML do rodapé
    footer_html = """
    <div class="footer-container">
        &copy; 2025 Planner Organizer | 
        <a href="?show_termos=true" target="_blank">Termos de Uso</a> | 
        <a href="?show_politica=true" target="_blank">Política de Privacidade</a> | 
        Contato: contato@plannerorganizer.com.br
    </div>
    """
    
    # Aplicar o CSS e o rodapé
    st.markdown(footer_css, unsafe_allow_html=True)
    st.markdown(footer_html, unsafe_allow_html=True)