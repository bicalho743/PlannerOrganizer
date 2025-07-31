"""
Módulo para aplicar correções de espaçamento CSS
"""

import streamlit as st

def apply_spacing_fix():
    """
    Aplica CSS específico para eliminar o espaçamento excessivo entre o cabeçalho e o conteúdo
    """
    
    spacing_css = """
    <style>
    /* CSS FORÇADO PARA CORRIGIR ESPAÇAMENTO */
    
    /* Força o container principal a ficar colado no cabeçalho */
    .main .block-container {
        padding-top: 0px !important;
        margin-top: 82px !important;
    }
    
    /* Remove espaços do container de aplicação */
    [data-testid="stAppViewContainer"] .main {
        padding-top: 0px !important;
        margin-top: 0px !important;
    }
    
    /* Remove espaços do primeiro elemento */
    [data-testid="stAppViewContainer"] .main > div:first-child {
        padding-top: 0px !important;
        margin-top: 0px !important;
    }
    
    /* Remove qualquer espaço extra do bloco principal */
    [data-testid="stAppViewContainer"] .main .block-container > div:first-child {
        padding-top: 0px !important;
        margin-top: 0px !important;
    }
    
    /* JavaScript para forçar a aplicação após carregamento */
    </style>
    
    <script>
    // Força a aplicação do CSS após carregamento da página
    setTimeout(function() {
        var containers = document.querySelectorAll('.block-container');
        containers.forEach(function(container) {
            container.style.marginTop = '82px';
            container.style.paddingTop = '0px';
        });
        
        var mainContainers = document.querySelectorAll('.main');
        mainContainers.forEach(function(main) {
            main.style.paddingTop = '0px';
            main.style.marginTop = '0px';
        });
    }, 50);
    
    // Repetir após um tempo maior para garantir
    setTimeout(function() {
        var containers = document.querySelectorAll('.block-container');
        containers.forEach(function(container) {
            container.style.marginTop = '82px';
            container.style.paddingTop = '0px';
        });
    }, 500);
    </script>
    """
    
    st.markdown(spacing_css, unsafe_allow_html=True)