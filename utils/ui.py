"""
Componentes de UI reutilizáveis — padronização visual da aplicação.

botao_excluir(): botão destrutivo (contorno vermelho discreto). Uma ação
irreversível (excluir/remover) nunca deve ter o mesmo peso visual das ações
seguras — evita clique acidental. Fonte única para todas as páginas.
"""
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

# Botão destrutivo: fundo vermelho sólido. O texto herda o branco que o CSS
# global do app já força em todo botão — visível no vermelho, sem depender de
# vencer a "briga" de especificidade (que quebrava conforme a versão do
# Streamlit, deixando o rótulo branco/invisível no contorno). Discreto pelo
# tamanho pequeno + posição centralizada de quem chama.
DESTRUCTIVE_BTN_CSS = """
button {
    background: #C0392B !important;
    border: none !important;
    box-shadow: none !important;
    min-height: 0 !important;
    padding: 8px 14px !important;
}
button:hover { background: #A93226 !important; }
"""

# Link "Fechar/Cancelar" discreto: fundo cinza claro, texto branco (global).
CLOSE_LINK_CSS = """
button {
    background: #8B8680 !important;
    border: none !important;
    box-shadow: none !important;
    min-height: 0 !important;
    padding: 7px 14px !important;
    font-size: 13px !important;
}
button:hover { background: #6B6660 !important; }
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
