"""
Gerenciador de temas e cores para a aplicação
"""
import streamlit as st

# Definição dos temas disponíveis
TEMAS = {
    "original": {
        "nome": "Tema Original",
        "primary_color": "#1f77b4",
        "background_color": "#ffffff",
        "secondary_background": "#f0f2f6",
        "text_color": "#262730",
        "sidebar_bg": "#f0f2f6"
    },
    "modern_blue": {
        "nome": "Azul Moderno",
        "primary_color": "#0066cc",
        "background_color": "#ffffff",
        "secondary_background": "#f8f9fa",
        "text_color": "#212529",
        "sidebar_bg": "#e3f2fd"
    },
    "professional_green": {
        "nome": "Verde Profissional",
        "primary_color": "#28a745",
        "background_color": "#ffffff",
        "secondary_background": "#f8f9fa",
        "text_color": "#212529",
        "sidebar_bg": "#e8f5e8"
    },
    "elegant_purple": {
        "nome": "Roxo Elegante",
        "primary_color": "#6f42c1",
        "background_color": "#ffffff",
        "secondary_background": "#f8f9fa",
        "text_color": "#212529",
        "sidebar_bg": "#f3e5f5"
    },
    "warm_orange": {
        "nome": "Laranja Acolhedor",
        "primary_color": "#fd7e14",
        "background_color": "#ffffff",
        "secondary_background": "#fef9e7",
        "text_color": "#212529",
        "sidebar_bg": "#fff3cd"
    }
}

def get_current_theme():
    """Retorna o tema atual selecionado"""
    if 'selected_theme' not in st.session_state:
        st.session_state.selected_theme = 'original'
    return st.session_state.selected_theme

def set_theme(theme_key):
    """Define um novo tema"""
    if theme_key in TEMAS:
        st.session_state.selected_theme = theme_key
        return True
    return False

def apply_theme_css():
    """Aplica o CSS do tema selecionado"""
    current_theme = get_current_theme()
    theme_config = TEMAS[current_theme]
    
    css = f"""
    <style>
    /* Tema: {theme_config['nome']} */
    
    /* Cores principais */
    .main .block-container {{
        background-color: {theme_config['background_color']};
        color: {theme_config['text_color']};
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: {theme_config['sidebar_bg']};
    }}
    
    /* Botões principais */
    .stButton > button {{
        background-color: {theme_config['primary_color']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {theme_config['primary_color']}dd;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }}
    
    /* Cards e containers */
    .stContainer, .element-container {{
        background-color: {theme_config['secondary_background']};
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* Métricas */
    [data-testid="metric-container"] {{
        background-color: {theme_config['secondary_background']};
        border: 1px solid {theme_config['primary_color']}30;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    
    /* Selectbox e inputs */
    .stSelectbox > div > div {{
        border-color: {theme_config['primary_color']};
    }}
    
    .stTextInput > div > div > input {{
        border-color: {theme_config['primary_color']};
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {theme_config['secondary_background']};
        border-radius: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {theme_config['text_color']};
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: {theme_config['primary_color']};
        color: white;
    }}
    
    /* Dataframes */
    .stDataFrame {{
        border: 1px solid {theme_config['primary_color']}30;
        border-radius: 8px;
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: {theme_config['primary_color']};
    }}
    
    /* Success/Info boxes */
    .stSuccess {{
        background-color: {theme_config['primary_color']}10;
        border-left: 4px solid {theme_config['primary_color']};
    }}
    
    /* Animações suaves */
    * {{
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def show_theme_selector():
    """Mostra o seletor de temas na sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 **Temas de Cores**")
    
    current_theme = get_current_theme()
    
    # Selectbox para escolher o tema
    theme_options = {key: config['nome'] for key, config in TEMAS.items()}
    selected_theme_name = st.sidebar.selectbox(
        "Escolha um tema:",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_theme),
        key="theme_selector"
    )
    
    # Aplicar tema se mudou
    if selected_theme_name != current_theme:
        set_theme(selected_theme_name)
        st.rerun()
    
    # Botão para resetar para o tema original
    if current_theme != 'original':
        if st.sidebar.button("🔄 Voltar ao Tema Original", key="reset_theme"):
            set_theme('original')
            st.rerun()
    
    # Preview das cores do tema atual
    theme_config = TEMAS[current_theme]
    st.sidebar.markdown("#### Preview de Cores:")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background-color: {theme_config['primary_color']}; height: 30px; border-radius: 5px; margin: 2px;"></div>
        <small>Cor Principal</small>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background-color: {theme_config['secondary_background']}; height: 30px; border-radius: 5px; margin: 2px; border: 1px solid #ddd;"></div>
        <small>Fundo Secundário</small>
        """, unsafe_allow_html=True)

def get_theme_info():
    """Retorna informações do tema atual"""
    current_theme = get_current_theme()
    return TEMAS[current_theme]