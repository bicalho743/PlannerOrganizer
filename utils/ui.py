"""
Componentes de UI reutilizáveis — padronização visual da aplicação.

botao_excluir(): botão destrutivo (contorno vermelho discreto). Uma ação
irreversível (excluir/remover) nunca deve ter o mesmo peso visual das ações
seguras — evita clique acidental. Fonte única para todas as páginas.
"""
import os

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


_PASTA_PDF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "_pdf")


def publicar_pdf(caminho_ou_bytes, nome):
    """Copia o PDF para static/_pdf/<código aleatório>/<nome> e devolve o endereço (app/static/...).

    Antes o download usava o arquivo temporário do Streamlit, que some quando a tela se atualiza: o botão dava
    404 e o arquivo baixava com nome em código. O endereço aqui não expira com a tela (o arquivo é apagado depois
    de 2 horas) e o código aleatório de 32 letras não dá para adivinhar."""
    import re
    import secrets
    import shutil
    import time
    os.makedirs(_PASTA_PDF, exist_ok=True)
    agora = time.time()
    for d in os.listdir(_PASTA_PDF):   # limpeza: PDFs com mais de 2 horas
        cam = os.path.join(_PASTA_PDF, d)
        try:
            if agora - os.path.getmtime(cam) > 7200:
                shutil.rmtree(cam, ignore_errors=True)
        except OSError:
            pass
    nome = re.sub(r"[^\w.\-]+", "_", str(nome or "documento.pdf"), flags=re.ASCII).strip("_") or "documento.pdf"
    if not nome.lower().endswith(".pdf"):
        nome += ".pdf"
    token = secrets.token_hex(16)
    pasta = os.path.join(_PASTA_PDF, token)
    os.makedirs(pasta)
    destino = os.path.join(pasta, nome)
    if isinstance(caminho_ou_bytes, (bytes, bytearray)):
        with open(destino, "wb") as f:
            f.write(caminho_ou_bytes)
    else:
        shutil.copyfile(caminho_ou_bytes, destino)
    return f"app/static/_pdf/{token}/{nome}", nome


def link_pdf(rotulo, url, nome, key, auto=False):
    """Botão (link) de download para um PDF publicado com publicar_pdf. auto=True baixa sozinho na hora."""
    import html as _h
    import streamlit.components.v1 as components
    st.markdown(f'<a class="po-baixar-pdf" id="lnk_{_h.escape(key)}" href="{_h.escape(url)}" download="{_h.escape(nome)}" '
                f'target="_blank" rel="noopener"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v12"/>'
                f'<path d="m6 11 6 6 6-6"/><path d="M5 20h14"/></svg>{_h.escape(rotulo)}</a>', unsafe_allow_html=True)
    if auto:
        components.html(f"""<script>
(function(){{
  var n = 0, t = setInterval(function(){{
    var a = window.parent.document.getElementById('lnk_{key}');
    if (a) {{ clearInterval(t); a.click(); }} else if (++n > 40) clearInterval(t);
  }}, 100);
}})();
</script>""", height=0)


CSS_BAIXAR_PDF = """<style>
a.po-baixar-pdf { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; min-height: 40px;
  padding: 8px 14px; border-radius: 10px; border: 1px solid #E7E2D6; background: #F6EDD3; color: #0D1B2A !important;
  font-weight: 600; text-decoration: none !important; box-sizing: border-box; }
a.po-baixar-pdf:hover { border-color: #C9A84C; }
</style>"""


def baixar_pdf_pronto(rotulo, dados, nome, key):
    """Link de download para um PDF já gerado (bytes), no lugar do st.download_button (que dava 404 e nome em código
    depois que a tela se atualizava). Publica uma vez por conteúdo: redesenhar a tela não cria outra cópia."""
    import hashlib
    h = hashlib.md5(dados).hexdigest()
    salvo = st.session_state.get(f"_pdfb_{key}")
    if not (salvo and salvo[0] == h and os.path.exists(os.path.join(_PASTA_PDF, salvo[1].split("/_pdf/", 1)[1]))):
        url, nome_pub = publicar_pdf(dados, nome)
        salvo = (h, url, nome_pub)
        st.session_state[f"_pdfb_{key}"] = salvo
    st.markdown(CSS_BAIXAR_PDF, unsafe_allow_html=True)
    link_pdf(rotulo, salvo[1], salvo[2], f"dlb_{key}")


def baixar_pdf(rotulo, key, gerar, legenda=None):
    """Botão "Baixar ..." de um clique para um PDF gerado só quando a pessoa pede.

    gerar() devolve (caminho, nome_arquivo, erro). No primeiro clique o PDF é gerado, publicado num endereço que
    não expira com a tela (publicar_pdf) e baixado na hora; depois o botão vira um link direto para ele."""
    estado, auto = f"_pdf_{key}", f"_pdf_{key}_auto"
    salvo = st.session_state.get(estado)
    st.markdown(CSS_BAIXAR_PDF, unsafe_allow_html=True)
    if isinstance(salvo, dict) and salvo.get("url") and os.path.exists(
            os.path.join(_PASTA_PDF, salvo["url"].split("/_pdf/", 1)[1])):
        link_pdf(rotulo, salvo["url"], salvo["name"], f"dl_{key}", auto=st.session_state.pop(auto, False))
        if legenda:
            st.caption(legenda)
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
            try:
                url, nome_pub = publicar_pdf(caminho, nome or os.path.basename(caminho))
            except Exception as e:
                st.error(f"Não foi possível preparar o download: {e}")
                return
            st.session_state[estado] = {"url": url, "name": nome_pub}
            st.session_state[auto] = True
            try:  # funil de conversão: primeiro PDF gerado pela conta (utils/funil.py)
                from utils import funil
                from utils.database import engine as _eng, get_usuario_id_from_session
                funil.registrar(_eng, get_usuario_id_from_session(), "primeiro_pdf", "site")
            except Exception as _e:
                print(f"[funil] pdf: {_e}")
            st.rerun()
        else:
            st.error(erro or "Erro ao gerar o PDF.")
