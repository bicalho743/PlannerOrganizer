import streamlit as st
from utils.design_tokens import NAVY, NAVY_HOVER, GOLD, GOLD_DARK, GOLD_LIGHT, GLOBAL_CSS_VARS

def apply_page_header(page_title=None, breadcrumb_items=None):
    """
    Aplica um cabeçalho padronizado em todas as páginas do sistema.

    Args:
        page_title: Título da página atual
        breadcrumb_items: Lista de itens para o breadcrumb ['Home', 'Seção', 'Página Atual']
    """

    st.markdown(f"<style>{GLOBAL_CSS_VARS}</style>", unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* Esconder contêineres de iframes */
    iframe[title='st.iframe'] { display: none !important; }
    iframe[title='st.iframe'] + div { display: none !important; }

    /* Remove header nativo do Streamlit */
    header[data-testid="stHeader"] { 
        display: none !important; 
        height: 0 !important; 
        margin: 0 !important; 
        padding: 0 !important; 
    }

    /* Esconder elementos vazios que criam espaçamento */
    .element-container:empty,
    .stElementContainer:empty,
    [data-testid="element-container"]:empty {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Colapsar contêineres invisíveis que geram o espaço entre o cabeçalho
       e o conteúdo: cada elemento do fluxo recebe 1rem de gap do Streamlit,
       mesmo com altura zero. Iframes de injeção (height=0) e markdowns que
       só contêm <style>/<link>/<meta> não devem ocupar fluxo.
       (display:none não impede a execução dos scripts dos iframes.) */
    div[data-testid="stElementContainer"]:has(iframe[height="0"]),
    div.element-container:has(iframe[height="0"]),
    div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] > style:only-child),
    div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] link),
    div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] > p:only-child:empty) {
        display: none !important;
    }


    </style>
    """, unsafe_allow_html=True)

    if breadcrumb_items:
        breadcrumb_html = '<div class="page-breadcrumb">'
        for item in breadcrumb_items:
            breadcrumb_html += f'<span class="breadcrumb-item">{item}</span>'
        breadcrumb_html += '</div>'
        st.markdown(breadcrumb_html, unsafe_allow_html=True)
    elif page_title:
        breadcrumb_html = f'<div class="page-breadcrumb"><span class="breadcrumb-item">{page_title}</span></div>'
        st.markdown(breadcrumb_html, unsafe_allow_html=True)

def apply_page_footer():
    """
    Termos, privacidade e contato no fim do menu lateral (antes era uma barra fixa
    que ocupava o rodapé de todas as telas).
    """
    st.sidebar.markdown(
        '<div class="sb-rodape">'
        '<a href="https://plannerorganiza.com.br/?show_termos=true" target="_blank">Termos de uso</a> · '
        '<a href="https://plannerorganiza.com.br/?show_politica=true" target="_blank">Privacidade</a><br>'
        'contato@plannerorganiza.com.br</div>',
        unsafe_allow_html=True)
