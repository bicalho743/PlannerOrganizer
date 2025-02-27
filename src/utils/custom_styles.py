
import streamlit as st

def load_custom_styles():
    """Carrega estilos CSS personalizados para a aplicação"""
    
    # Estilos CSS personalizados
    st.markdown("""
    <style>
        /* Estilos para botões de menu */
        .stButton > button {
            background-color: #262730;
            color: white;
            border: 1px solid #4F8BF9;
            border-radius: 5px;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            background-color: #4F8BF9;
            color: white;
            border: 1px solid #4F8BF9;
        }
        
        /* Espaçamento para o menu superior */
        div.block-container {
            padding-top: 1rem;
        }
        
        /* Título do menu */
        h1 {
            font-size: 1.8rem !important;
            text-align: center;
            margin-bottom: 1rem !important;
        }
        
        /* Separador após o menu */
        hr {
            margin-top: 0.5rem;
            margin-bottom: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

def load_custom_styles():
    """Carrega estilos CSS personalizados para a aplicação"""
    
    st.markdown("""
    <style>
    /* Estilo para cabeçalhos */
    h1, h2, h3 {
        color: #F1A208;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Estilos para cartões/expanders */
    div.streamlit-expanderHeader {
        background-color: #2E2E2E;
        border-radius: 5px 5px 0px 0px;
        padding: 0.5rem;
    }
    
    div.streamlit-expanderContent {
        background-color: #2E2E2E;
        border-radius: 0px 0px 5px 5px;
        padding: 1rem;
    }
    
    /* Estilo para botões */
    div.stButton > button {
        background-color: #F1A208;
        color: #1C1C1C;
        font-weight: 600;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #FFC457;
        color: #1C1C1C;
        box-shadow: 0px 3px 5px rgba(0, 0, 0, 0.2);
    }
    
    /* Estilo para sidebar */
    section[data-testid="stSidebar"] {
        background-color: #262730;
        padding: 1rem;
    }
    
    /* Estilo para métricas */
    div[data-testid="metric-container"] {
        background-color: #2E2E2E;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="metric-container"] > div:first-child {
        color: #F1A208;
    }
    
    /* Estilo para tabelas */
    .stDataFrame {
        border-radius: 5px;
        overflow: hidden;
    }
    
    .stDataFrame thead tr th {
        background-color: #3D3D3D !important;
        color: #F1A208 !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #2A2A2A !important;
    }
    
    /* Estilo para widgets de entrada */
    div.stTextInput > div > div > input, 
    div.stNumberInput > div > div > input,
    div.stDateInput > div > div > input,
    div.stSelectbox > div > div > select {
        background-color: #3D3D3D;
        color: #F5F5F5;
        border-radius: 5px;
        border: 1px solid #4D4D4D;
    }
    </style>
    """, unsafe_allow_html=True)
