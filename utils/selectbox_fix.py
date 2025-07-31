"""
MÓDULO DESATIVADO - CSS centralizado no arquivo .streamlit/style.css
Problema: Texto dos selectbox aparece invisível/branco
Solução: CSS unificado no arquivo principal
"""

# import streamlit as st

def inject_selectbox_fix():
    """
    Injeta CSS e JavaScript para corrigir problemas de visibilidade dos selectbox
    Deve ser chamado no início de cada página que usa selectbox
    """
    st.html("""
    <style>
    /* CORREÇÃO EXTREMA PARA SELECTBOX - FORÇA MÁXIMA */
    
    /* Todos os containers de selectbox */
    div[data-testid="stSelectbox"],
    .stSelectbox,
    [data-testid="stSelectbox"] {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
    }

    /* TODOS os elementos dentro de selectbox */
    div[data-testid="stSelectbox"] *,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stSelectbox"] span,
    div[data-testid="stSelectbox"] input,
    div[data-testid="stSelectbox"] p,
    .stSelectbox *,
    .stSelectbox div,
    .stSelectbox span,
    .stSelectbox input,
    .stSelectbox p {
        color: #1e1e1e !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        opacity: 1 !important;
        visibility: visible !important;
        text-shadow: none !important;
        box-shadow: none !important;
    }

    /* Elementos baseweb específicos do Streamlit */
    div[data-testid="stSelectbox"] [data-baseweb="select"],
    div[data-testid="stSelectbox"] [data-baseweb="select"] *,
    div[data-testid="stSelectbox"] [data-baseweb="select"] div,
    div[data-testid="stSelectbox"] [data-baseweb="select"] span,
    div[data-testid="stSelectbox"] [data-baseweb="input"],
    div[data-testid="stSelectbox"] [data-baseweb="input"] *,
    .stSelectbox [data-baseweb="select"],
    .stSelectbox [data-baseweb="select"] *,
    .stSelectbox [data-baseweb="select"] div,
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="input"],
    .stSelectbox [data-baseweb="input"] * {
        color: #1e1e1e !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Labels */
    div[data-testid="stSelectbox"] > label,
    .stSelectbox > label,
    [data-testid="stSelectbox"] > label {
        color: #1e1e1e !important;
        font-weight: 600 !important;
    }

    /* Dropdown menu quando expandido */
    div[data-testid="stSelectbox"] ul,
    div[data-testid="stSelectbox"] li,
    .stSelectbox ul,
    .stSelectbox li {
        color: #1e1e1e !important;
        background-color: #ffffff !important;
    }

    /* Setas e ícones */
    div[data-testid="stSelectbox"] svg,
    .stSelectbox svg {
        color: #1e1e1e !important;
        fill: #1e1e1e !important;
    }
    </style>

    <script>
    // CORREÇÃO JAVASCRIPT EXTREMA PARA SELECTBOX
    function extremeSelectboxFix() {
        // Buscar TODOS os possíveis selectbox
        const allSelectboxes = document.querySelectorAll(
            '[data-testid="stSelectbox"], .stSelectbox, div[data-testid="stSelectbox"], ' +
            '[role="combobox"], [role="listbox"], select, ' +
            '[data-baseweb="select"], [data-baseweb="input"]'
        );
        
        allSelectboxes.forEach(selectbox => {
            // FORÇA MÁXIMA - aplicar a TODOS os elementos filhos
            const allChildren = selectbox.querySelectorAll('*');
            allChildren.forEach(el => {
                // Usar setProperty com 'important' para máxima força
                el.style.setProperty('color', '#1e1e1e', 'important');
                el.style.setProperty('background-color', '#ffffff', 'important');
                el.style.setProperty('font-weight', '500', 'important');
                el.style.setProperty('opacity', '1', 'important');
                el.style.setProperty('visibility', 'visible', 'important');
                el.style.setProperty('text-shadow', 'none', 'important');
                el.style.setProperty('box-shadow', 'none', 'important');
                
                // Se tiver texto, garantir que seja visível
                if (el.textContent && el.textContent.trim() !== '') {
                    el.style.setProperty('color', '#1e1e1e', 'important');
                }
                
                // Se for input, garantir cor
                if (el.tagName === 'INPUT') {
                    el.style.setProperty('color', '#1e1e1e', 'important');
                    el.style.setProperty('background-color', '#ffffff', 'important');
                }
            });
            
            // Container principal
            selectbox.style.setProperty('background-color', '#ffffff', 'important');
            selectbox.style.setProperty('color', '#1e1e1e', 'important');
        });
        
        // EXTRA: Buscar por qualquer elemento que possa conter texto de selectbox
        const allTextElements = document.querySelectorAll('span, div, input, p');
        allTextElements.forEach(el => {
            const parent = el.closest('[data-testid="stSelectbox"], .stSelectbox');
            if (parent && (el.textContent || el.value)) {
                el.style.setProperty('color', '#1e1e1e', 'important');
                el.style.setProperty('background-color', '#ffffff', 'important');
            }
        });
    }
    
    // Executar imediatamente
    extremeSelectboxFix();
    
    // Executar muito frequentemente
    setInterval(extremeSelectboxFix, 25);
    
    // Observer para mudanças no DOM
    const extremeObserver = new MutationObserver(function(mutations) {
        setTimeout(extremeSelectboxFix, 5);
    });

    extremeObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class', 'data-testid']
    });
    </script>
    """)

def apply_selectbox_theme_override():
    """
    Aplica uma correção mais agressiva ao tema do Streamlit
    para garantir que selectbox sejam sempre visíveis
    """
    # CSS ainda mais específico com classes baseadas no tema
    st.html("""
    <style>
    /* OVERRIDE COMPLETO DO TEMA - SELECTBOX */
    
    /* Força absoluta - sobrescrever qualquer tema */
    .main div[data-testid="stSelectbox"] *,
    .main .stSelectbox *,
    [data-theme="light"] div[data-testid="stSelectbox"] *,
    [data-theme="dark"] div[data-testid="stSelectbox"] *,
    html div[data-testid="stSelectbox"] *,
    body div[data-testid="stSelectbox"] * {
        color: #1e1e1e !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Container específico para tema escuro */
    [data-theme="dark"] div[data-testid="stSelectbox"],
    [data-theme="dark"] .stSelectbox {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
    }
    
    /* Forçar cor em qualquer contexto */
    * div[data-testid="stSelectbox"] * {
        color: #1e1e1e !important;
        background-color: #ffffff !important;
    }
    </style>
    """)