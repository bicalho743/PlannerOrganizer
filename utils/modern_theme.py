"""
Tema moderno azul simplificado para o sistema
"""
import streamlit as st

def apply_modern_blue_theme():
    """
    Aplica o tema moderno azul com CSS simplificado
    """
    
    css = """
    <style>
    /* FORÇA EXTREMA PARA APLICAR CORES NA SIDEBAR */
    
    /* Todos os possíveis seletores da sidebar */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div,
    section[data-testid="stSidebar"] .css-1d391kg,
    .css-1d391kg,
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    div[data-testid="stSidebar"],
    .st-emotion-cache-1d391kg,
    .st-emotion-cache-1cypcdb {
        background: #2c2d3d !important;
        background-color: #2c2d3d !important;
        background-image: none !important;
    }
    
    /* Força máxima com JavaScript inline */
    </style>
    <script>
    setTimeout(function() {
        // Força a aplicação da cor via JavaScript
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.setProperty('background', '#2c2d3d', 'important');
            sidebar.style.setProperty('background-color', '#2c2d3d', 'important');
            
            // Aplica em todos os filhos também
            const children = sidebar.querySelectorAll('*');
            children.forEach(child => {
                if (child.style) {
                    child.style.setProperty('background-color', '#2c2d3d', 'important');
                }
            });
        }
        
        // Procura por outros seletores comuns
        const altSidebars = document.querySelectorAll('.css-1d391kg, .st-emotion-cache-1d391kg');
        altSidebars.forEach(el => {
            el.style.setProperty('background', '#2c2d3d', 'important');
            el.style.setProperty('background-color', '#2c2d3d', 'important');
        });
    }, 100);
    </script>
    
    /* Força texto branco em TUDO na sidebar */
    section[data-testid="stSidebar"] *,
    .css-1d391kg *,
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Botões da sidebar com múltiplos seletores */
    section[data-testid="stSidebar"] button,
    .css-1d391kg button,
    [data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .stButton > button,
    .css-1d391kg .stButton > button {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        width: 100% !important;
        text-align: left !important;
        padding: 12px 16px !important;
        margin: 4px 0 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Hover dos botões */
    section[data-testid="stSidebar"] button:hover,
    .css-1d391kg button:hover,
    [data-testid="stSidebar"] button:hover {
        background: rgba(59, 130, 246, 0.5) !important;
        transform: translateX(6px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Fundo principal */
    .main,
    [data-testid="stAppViewContainer"] .main {
        background: #f1f5f9 !important;
    }
    
    /* Títulos azuis */
    h1, h2, h3, h4, h5, h6 {
        color: #1e40af !important;
        font-weight: 600 !important;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)