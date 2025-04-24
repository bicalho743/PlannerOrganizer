import streamlit as st

def apply_page_header():
    """
    Aplica um cabeçalho padronizado em todas as páginas do sistema
    """
    # Adicionando o cabeçalho no topo da página
    st.markdown("""
    <div style="background-color: #1E366F; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center;">
        <h2 style="color: white; margin: 0; padding: 0; font-family: 'Poppins', sans-serif;">Planner Organizer</h2>
        <p style="color: #E3F2FD; margin: 0.2rem 0 0 0; padding: 0; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">
            Sistema Profissional de Gestão Personal Organizer
        </p>
        <p style="color: #BBD8FF; margin: 0.5rem 0 0 0; padding: 0; font-size: 0.8rem; font-family: 'Poppins', sans-serif; font-style: italic;">
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