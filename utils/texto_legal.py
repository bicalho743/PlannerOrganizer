"""
Renderização comum dos textos legais (Termos de Uso e Política de Privacidade).

Cada texto é uma lista de seções (título, parágrafos, itens). A mesma lista gera o
HTML do modal de cadastro e a página aberta por ?show_termos / ?show_politica.
"""
import streamlit as st

CONTATO = "contato@plannerorganiza.com.br"
ATUALIZADO_EM = "21 de outubro de 2026"


def para_html(titulo, intro, secoes):
    partes = [f"<h1>{titulo}</h1>", f"<p><em>Atualizado em {ATUALIZADO_EM}.</em></p>", f"<p>{intro}</p>"]
    for nome, paragrafos, itens in secoes:
        if nome:
            partes.append(f"<h3>{nome}</h3>")
        partes += [f"<p>{p}</p>" for p in (paragrafos or [])]
        if itens:
            partes.append("<ul>" + "".join(f"<li>{i}</li>" for i in itens) + "</ul>")
    return "\n".join(partes)


def mostrar_pagina(titulo, intro, secoes):
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .block-container { max-width: 900px !important; margin: 0 auto !important; padding: 2rem 3rem !important; }
    .legal h1 { color: #C9A84C; font-size: 1.8rem; margin-bottom: .25rem; }
    .legal h3 { color: #C9A84C; font-size: 1.1rem; margin-top: 1.5rem; }
    .legal p, .legal li { color: rgba(245,240,232,0.85); line-height: 1.8; font-size: .95rem; }
    .legal ul { margin-left: 1.5rem; }
    .legal em { color: rgba(245,240,232,0.55); }
    .legal a { color: #C9A84C; }
    @media (max-width: 600px) { .block-container { padding: 1.5rem 1rem !important; } }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="legal">{para_html(titulo, intro, secoes)}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
