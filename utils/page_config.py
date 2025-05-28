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
        background-color: #1E1F36 !important;
    }
    
    /* Botões transparentes da sidebar com animações */
    [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border-radius: 12px !important;
        margin: 4px 0 !important;
        padding: 12px 16px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: rgba(255, 255, 255, 1) !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3), 0 0 20px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Títulos dos expanders na sidebar com texto branco */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: rgba(255, 255, 255, 1) !important;
    }
    
    /* Conteúdo dos expanders na sidebar com texto branco */
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent h3,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent h4,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent p,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent li,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent ul,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent div {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderContent strong {
        color: rgba(255, 255, 255, 1) !important;
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
    
    /* Estilo para o nome do usuário no canto superior direito */
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
        font-family: "Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        z-index: 1000;
    }
    </style>
    """
    
    # Aplicar CSS para ajustar espaçamento
    st.markdown(header_css, unsafe_allow_html=True)
    
    # Obter nome do usuário da sessão
    nome_usuario = "Usuário"
    
    # Verificar se o objeto de usuário existe na sessão (chave 'usuario')
    if "usuario" in st.session_state and st.session_state.usuario:
        if isinstance(st.session_state.usuario, dict) and "nome" in st.session_state.usuario:
            nome_usuario = st.session_state.usuario["nome"]
        elif hasattr(st.session_state.usuario, "nome"):
            nome_usuario = st.session_state.usuario.nome
    
    # Log para debug (temporário)
    print(f"Dados do usuário na sessão: {st.session_state.get('usuario', 'Não encontrado')}")
    
    # Componente de "Bem-vindo(a)" no canto superior direito
    welcome_html = f"""
    <div class="user-welcome">
        Bem-vindo(a), {nome_usuario}
    </div>
    """
    
    # Obter a data atual formatada em português
    from datetime import datetime
    data_atual = datetime.now()
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", 
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_formatada = f"{data_atual.day} de {meses[data_atual.month-1]} de {data_atual.year}"
    
    # Adicionando o cabeçalho usando a classe CSS definida em style.css
    st.markdown(f"""
    <div class="app-header">
        <h2 style="color: white; margin: 0; padding: 0; font-family: 'Poppins', sans-serif; font-size: 1.5rem; font-weight: 600;">Planner Organizer</h2>
        <p style="color: #E3F2FD; margin: 0.15rem 0 0 0; padding: 0; font-size: 0.85rem; font-family: 'Poppins', sans-serif;">
            Sistema Profissional de Gestão Personal Organizer
        </p>
        <p style="color: #BBD8FF; margin: 0.3rem 0 0 0; padding: 0; font-size: 0.75rem; font-family: 'Poppins', sans-serif; font-style: italic;">
            "Transforme sua organização em resultados: gerencie propostas, clientes e finanças com precisão profissional."
        </p>
        <div style="position: absolute; top: 45%; right: 1rem; transform: translateY(-50%); background-color: rgba(255, 255, 255, 0.2); padding: 0.3rem 0.8rem; border-radius: 1rem; text-align: center;">
            <span style="color: white; font-size: 0.8rem; font-family: 'Poppins', sans-serif; display: block;">Bem-vindo(a), {nome_usuario}</span>
            <span style="color: #BBD8FF; font-size: 0.7rem; font-family: 'Poppins', sans-serif; display: block; margin-top: 0.2rem;">📅 {data_formatada}</span>
        </div>
    </div>
    
    <div class="content-wrapper">
        <!-- Início do conteúdo principal após o cabeçalho -->
    """, unsafe_allow_html=True)
    
    # No final da função, fechamos a div de content-wrapper
    st.markdown("</div>", unsafe_allow_html=True)

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