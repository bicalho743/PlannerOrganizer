"""
Componentes de UI reutilizáveis — padronização visual da aplicação.

botao_excluir(): botão destrutivo (contorno vermelho discreto). Uma ação
irreversível (excluir/remover) nunca deve ter o mesmo peso visual das ações
seguras — evita clique acidental. Fonte única para todas as páginas.
"""
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

# Botão destrutivo: transparente com contorno vermelho, texto vermelho.
DESTRUCTIVE_BTN_CSS = """
button {
    background: transparent !important;
    border: 1px solid #E3A9A2 !important;
    box-shadow: none !important;
    min-height: 0 !important;
    padding: 6px 12px !important;
}
button:hover { background: #FDECEA !important; border-color: #C0392B !important; }
button p, button div, button span { color: #C0392B !important; font-weight: 600 !important; }
"""

# Link "Fechar/Cancelar" discreto (sem peso de ação).
CLOSE_LINK_CSS = """
button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    min-height: 0 !important;
}
button p, button div, button span { color: #8B8680 !important; font-weight: 500 !important; font-size: 13px !important; }
button:hover p, button:hover div, button:hover span { color: #4A4A4A !important; }
"""


def botao_excluir(label, key, use_container_width=True, help=None, is_form=False):
    """Renderiza um botão de exclusão com o estilo destrutivo padrão.

    Args:
        label: texto do botão (ex.: "🗑 Excluir").
        key: chave única do botão.
        use_container_width: preenche a largura do container (default True).
        help: tooltip opcional.
        is_form: True se for um st.form_submit_button (dentro de st.form).

    Returns:
        bool — True se clicado.
    """
    with stylable_container(key=f"del_{key}", css_styles=DESTRUCTIVE_BTN_CSS):
        if is_form:
            return st.form_submit_button(label, use_container_width=use_container_width, help=help)
        return st.button(label, key=key, use_container_width=use_container_width, help=help)


def link_fechar(label, key, use_container_width=True):
    """Renderiza um link discreto de fechar/cancelar."""
    with stylable_container(key=f"close_{key}", css_styles=CLOSE_LINK_CSS):
        return st.button(label, key=key, use_container_width=use_container_width)
