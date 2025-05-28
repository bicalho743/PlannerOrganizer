"""
Tema moderno baseado no design React fornecido
"""
import streamlit as st

def apply_modern_blue_theme():
    """
    Aplica o tema moderno azul inspirado no design React
    """
    
    css = """
    <style>
    /* Importar fonte mais moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Reset e configurações gerais */
    .main .block-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        max-width: none !important;
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Sidebar com design moderno azul */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e40af 0%, #1d4ed8 100%) !important;
        color: white !important;
        border-right: none !important;
        box-shadow: 4px 0 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Logo/Título da sidebar */
    .css-1d391kg .element-container:first-child h1,
    .css-1d391kg .element-container:first-child h2,
    .css-1d391kg .element-container:first-child h3 {
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin-bottom: 2rem !important;
        padding: 1rem 0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Botões da sidebar */
    .css-1d391kg .stButton > button {
        background: transparent !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        width: 100% !important;
        text-align: left !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        margin: 0.25rem 0 !important;
        box-shadow: none !important;
    }
    
    .css-1d391kg .stButton > button:hover {
        background: rgba(59, 130, 246, 0.3) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    .css-1d391kg .stButton > button:active {
        background: rgba(59, 130, 246, 0.5) !important;
    }
    
    /* Texto na sidebar */
    .css-1d391kg .stMarkdown,
    .css-1d391kg .stSelectbox label,
    .css-1d391kg .stText,
    .css-1d391kg p {
        color: white !important;
    }
    
    /* Conteúdo principal */
    .main {
        background: #f8fafc !important;
    }
    
    /* Headers principais */
    h1, h2, h3 {
        color: #1e40af !important;
        font-weight: 600 !important;
        margin-bottom: 1.5rem !important;
    }
    
    h1 {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
    }
    
    /* Cards e containers */
    .element-container {
        background: white !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Métricas com design moderno */
    [data-testid="metric-container"] {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: 0 4px 16px rgba(30, 64, 175, 0.1) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Botões principais */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Tabs modernas */
    .stTabs [data-baseweb="tab-list"] {
        background: white !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        gap: 0.5rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #64748b !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Inputs e formulários */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* DataFrames com design moderno */
    .stDataFrame {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess {
        background: #ecfdf5 !important;
        border: 1px solid #22c55e !important;
        border-left: 4px solid #22c55e !important;
        border-radius: 8px !important;
        color: #15803d !important;
    }
    
    .stInfo {
        background: #eff6ff !important;
        border: 1px solid #3b82f6 !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 8px !important;
        color: #1d4ed8 !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #f59e0b !important;
        border-left: 4px solid #f59e0b !important;
        border-radius: 8px !important;
        color: #d97706 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 1px solid #ef4444 !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 8px !important;
        color: #dc2626 !important;
    }
    
    /* Sidebar logout button especial */
    .css-1d391kg .stButton:last-child > button {
        background: rgba(239, 68, 68, 0.2) !important;
        color: #fca5a5 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }
    
    .css-1d391kg .stButton:last-child > button:hover {
        background: rgba(239, 68, 68, 0.3) !important;
        color: #fecaca !important;
    }
    
    /* Animações suaves */
    * {
        transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)