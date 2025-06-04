import streamlit as st

def apply_page_header(page_title=None, breadcrumb_items=None):
    """
    Aplica um cabeçalho padronizado em todas as páginas do sistema

    Args:
        page_title: Título da página atual
        breadcrumb_items: Lista de itens para o breadcrumb ['Home', 'Ção', 'Página Atual']
    """
    # CSS para ajustar espaçamento e visual
    header_css = """
    <style>
    /* Cabeçalho fixo no topo */
    .app-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background-color: #1E1F36;
        padding: 0.4rem 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        font-family: "Poppins", sans-serif;
        min-height: 50px;
        display: flex;
        align-items: center;
    }
    
    /* Responsividade do cabeçalho */
    @media (max-width: 768px) {
        .app-header {
            padding: 0.3rem 0.8rem;
            min-height: 45px;
        }
        .app-header h1 {
            font-size: 1.2rem !important;
            line-height: 1.3 !important;
            margin: 0 !important;
        }
        .app-header h3 {
            font-size: 0.9rem !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }
    }

    /* Ajusta o conteúdo para não ficar escondido */
    .main .block-container {
        padding-top: 30px !important;
        margin-top: 0 !important;
    }

    /* Remove header nativo do Streamlit */
    header[data-testid="stHeader"] { display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; }
    [data-testid="stAppViewContainer"] > div:first-child { padding-top: 0 !important; margin-top: 0 !important; }
    [data-testid="stAppViewContainer"] > section:first-of-type { padding-top: 0 !important; margin-top: 0 !important; }

    /* Sidebar e botões */
    [data-testid="stSidebar"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        background-color: #1E1F36 !important;
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
    """
    st.markdown(header_css, unsafe_allow_html=True)

    nome_usuario = "Usuário"
    if "usuario" in st.session_state and st.session_state.usuario:
        if isinstance(st.session_state.usuario, dict) and "nome" in st.session_state.usuario:
            nome_usuario = st.session_state.usuario["nome"]
        elif hasattr(st.session_state.usuario, "nome"):
            nome_usuario = st.session_state.usuario.nome

    from datetime import datetime
    data_atual = datetime.now()
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_formatada = f"{data_atual.day} de {meses[data_atual.month-1]} de {data_atual.year}"

    st.markdown(f"""
    <div class="app-header">
        <h2 style="color: rgba(255,255,255,0.95); margin: 0; padding: 0; font-family: 'Poppins', sans-serif; font-size: 1.6rem; font-weight: 600;">Planner Organizer</h2>
        <p style="color: rgba(255,255,255,0.85); margin: 0.1rem 0 0 0; padding: 0; font-size: 1rem; font-family: 'Poppins', sans-serif;">
            Sistema Profissional de Gestão Personal Organizer
        </p>
        <div style="position: absolute; top: 45%; right: 1rem; transform: translateY(-50%); background-color: rgba(255,255,255,0.15); padding: 0.4rem 1rem; border-radius: 1rem; text-align: center; border: 1px solid rgba(255,255,255,0.2);">
            <span style="color: rgba(255,255,255,0.95); font-size: 0.9rem; font-family: 'Poppins', sans-serif; display: block; font-weight: 500;">Bem-vindo(a), {nome_usuario}</span>
            <span style="color: rgba(255,255,255,0.8); font-size: 0.8rem; font-family: 'Poppins', sans-serif; display: block; margin-top: 0.2rem;">📅 {data_formatada}</span>
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
        position: fixed; bottom: 0; left: 0; right: 0;
        background-color: #1E1F36; color: white;
        padding: 12px 20px; text-align: center;
        font-size: 13px; z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    .footer-container a {
        color: #4A90E2; text-decoration: none; margin: 0 5px;
    }
    .footer-container a:hover {
        color: #7AB8FF; text-decoration: underline;
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
