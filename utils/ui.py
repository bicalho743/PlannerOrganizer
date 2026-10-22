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


# Papéis dos botões (estilo em .streamlit/style.css):
#   chamada da tela (Nova ...)  dourado sólido   -> container "cta_..."
#   gravar/confirmar            azul-marinho     -> type="primary"
#   editar/reabrir/duplicar     azul claro       -> botao_editar  (container "btned_...")
#   gerar/baixar documento      dourado claro    -> botao_documento / baixar_pdf / st.download_button
#   cancelar/voltar/abrir       branco com borda -> padrão
#   fechar                      só texto         -> type="tertiary"
#   excluir/cancelar venda      vermelho         -> botao_excluir


def botao_editar(label, key, **kwargs):
    """Botão de editar (azul claro, ícone de lápis). Aceita os mesmos argumentos de st.button."""
    kwargs.pop("type", None)
    kwargs.setdefault("icon", ":material/edit:")
    with st.container(key=f"btned_{key}"):
        return st.button(label, key=key, **kwargs)


def botao_documento(label, key, **kwargs):
    """Botão que gera um documento (dourado claro, ícone de documento). Em modo consulta (teste
    grátis encerrado) o clique abre o convite para assinar em vez de gerar."""
    from utils import somente_leitura
    kwargs.pop("type", None)
    kwargs.setdefault("icon", ":material/description:")
    with st.container(key=f"btndoc_{key}"):
        clicou = st.button(label, key=key, **kwargs)
    if clicou and somente_leitura.ativo():
        somente_leitura.tentou()
        return False
    return clicou


def _somente_leitura():
    from utils import somente_leitura
    if somente_leitura.ativo():
        somente_leitura.tentou()
        return True
    return False


def baixar_pdf(rotulo, key, gerar, legenda=None):
    """Botão "Baixar ..." de um clique para um PDF gerado só quando a pessoa pede.

    gerar() devolve (caminho, nome_arquivo, erro). No primeiro clique o PDF é gerado e a tela
    volta com o botão de download no mesmo lugar, que um script aciona sozinho; os cliques
    seguintes na mesma sessão baixam direto. (O st.download_button aceita gerar no clique, mas
    roda fora da sessão: o PDF ficaria sem o banco e o perfil da conta.)"""
    import os
    import streamlit.components.v1 as components
    estado, auto, dl_key = f"_pdf_{key}", f"_pdf_{key}_auto", f"dl_{key}"
    salvo = st.session_state.get(estado)
    if isinstance(salvo, dict) and salvo.get("path") and os.path.exists(salvo["path"]):
        with open(salvo["path"], "rb") as f:
            st.download_button(rotulo, data=f.read(), file_name=salvo["name"], mime="application/pdf",
                               key=dl_key, icon=":material/download:", use_container_width=True)
        if legenda:
            st.caption(legenda)
        if st.session_state.pop(auto, False):
            components.html(f"""<script>
(function(){{
  var n = 0, t = setInterval(function(){{
    var b = window.parent.document.querySelector('.st-key-{dl_key} button');
    if (b) {{ clearInterval(t); b.click(); }} else if (++n > 40) clearInterval(t);
  }}, 100);
}})();
</script>""", height=0)
        return
    with st.container(key=f"btndoc_{key}"):
        clicou = st.button(rotulo, key=f"gen_{key}", icon=":material/download:", use_container_width=True)
    if legenda:
        st.caption(legenda)
    if clicou and _somente_leitura():
        return
    if clicou:
        with st.spinner("Preparando o PDF…"):
            caminho, nome, erro = gerar()
        if caminho:
            st.session_state[estado] = {"path": caminho, "name": nome}
            st.session_state[auto] = True
            st.rerun()
        else:
            st.error(erro or "Erro ao gerar o PDF.")
