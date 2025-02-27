
import streamlit as st

def card(title, content, icon="📄", color="#F1A208"):
    """
    Cria um cartão estilizado para exibir informações
    
    Parâmetros:
        title (str): Título do cartão
        content (str): Conteúdo do cartão
        icon (str): Ícone para exibir no cartão (emoji)
        color (str): Cor do título
    """
    st.markdown(f"""
    <div style="
        background-color: #2E2E2E;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h3 style="
            color: {color};
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 1.2rem;">{icon} {title}</h3>
        <div style="color: #F5F5F5;">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def status_badge(status, text=None):
    """
    Cria um badge de status colorido
    
    Parâmetros:
        status (str): Status ('success', 'warning', 'danger', 'info')
        text (str): Texto para exibir (opcional)
    """
    colors = {
        'success': '#28A745',
        'warning': '#FFC107',
        'danger': '#DC3545',
        'info': '#17A2B8',
        'primary': '#F1A208'
    }
    
    if text is None:
        text = status.capitalize()
    
    color = colors.get(status.lower(), colors['primary'])
    
    st.markdown(f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;">{text}</span>
    """, unsafe_allow_html=True)
