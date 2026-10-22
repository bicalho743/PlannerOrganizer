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
    /* cartão branco da tela de entrada (fundo creme): mesmos tons do login e da landing */
    .legal h1 { color: #0D1B2A; font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 600;
                font-size: 2rem; margin-bottom: .25rem; }
    .legal h3 { color: #0D1B2A; font-size: 1.05rem; font-weight: 700; margin-top: 1.5rem;
                padding-left: 10px; border-left: 3px solid #C9A84C; }
    .legal p, .legal li { color: #3A4E68; line-height: 1.8; font-size: .95rem; }
    .legal ul { margin-left: 1.5rem; }
    .legal em { color: #6B7C94; }
    .legal a { color: #8A6D12; text-decoration: underline; }
    @media (max-width: 600px) { .block-container { padding: 1.5rem 1rem !important; } }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="legal">{para_html(titulo, intro, secoes)}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
