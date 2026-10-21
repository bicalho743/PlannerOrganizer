"""
Componentes de UI reutilizáveis — padronização visual da aplicação.

botao_excluir(): botão destrutivo (contorno vermelho discreto). Uma ação
irreversível (excluir/remover) nunca deve ter o mesmo peso visual das ações
seguras — evita clique acidental. Fonte única para todas as páginas.
"""
import streamlit as st

# Botão destrutivo (vermelho) e link de fechar (cinza): o estilo fica em .streamlit/style.css,
# preso ao container de cada um (classes st-key-del_* e st-key-close_*). Antes era passado ao
# stylable_container, que só prefixava a PRIMEIRA regra do texto: as seguintes (hover, cor do
# texto) valiam para todos os botões da página — e pintavam de vermelho as setas dos seletores.


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
    with st.container(key=f"del_{key}"):
        if is_form:
            return st.form_submit_button(label, use_container_width=use_container_width, help=help)
        return st.button(label, key=key, use_container_width=use_container_width, help=help)


def link_fechar(label, key, use_container_width=True):
    """Renderiza um link discreto de fechar/cancelar."""
    with st.container(key=f"close_{key}"):
        return st.button(label, key=key, use_container_width=use_container_width)


def input_moeda(label, key, value=0.0, step=100.0, help=None):
    """Campo de valor em R$ com digitação natural.

    O `st.number_input` com format="%.2f" e valor 0.0 mostra "0,00" e a
    digitação vai para depois da vírgula (o número não "entra"). Aqui o campo
    começa VAZIO (placeholder "0,00") quando não há valor, então cada dígito
    digitado entra normalmente pela frente. Mostra o valor atual quando > 0
    (edição). Retorna sempre float (0.0 se vazio).
    """
    v = None
    try:
        v = float(value) if value not in (None, "") and float(value) > 0 else None
    except (TypeError, ValueError):
        v = None
    r = st.number_input(
        label, min_value=0.0, value=v, step=step,
        placeholder="0,00", key=key, help=help,
    )
    try:
        return float(r) if r is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def cartao_clicavel(html_cartao, key, rotulo="Abrir detalhes", selecionado=False):
    """Cartão (HTML) que abre os detalhes ao ser clicado — no lugar do botão "Ver Detalhes"
    embaixo de cada cartão. Por cima do cartão fica um botão transparente do tamanho dele
    (CSS em .streamlit/style.css, classes st-key-kcard_*); o rótulo serve para leitor de tela.

    Returns:
        bool — True se clicado.
    """
    with st.container(key=f"kcard_{key}"):
        if selecionado:
            html_cartao = html_cartao.replace('class="kanban-card"', 'class="kanban-card selecionado"', 1)
        st.markdown(html_cartao, unsafe_allow_html=True)
        return st.button(rotulo, key=key, use_container_width=True)
