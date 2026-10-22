"""
Modo consulta: depois do teste grátis, sem assinatura, a conta continua entrando no app e vendo
tudo, mas não grava nada nem gera PDF.

- O bloqueio de gravação fica no banco (evento do engine): qualquer INSERT/UPDATE/DELETE da conta
  em modo consulta é recusado, venha de que tela vier. A tabela de perfis fica liberada (último
  acesso, tutorial visto e a ativação do plano precisam gravar).
- PDFs: botao_documento/baixar_pdf (utils/ui.py) e st.download_button de PDF abrem o aviso em vez
  de gerar/baixar.
- Quem tentou gravar ou gerar vê, no fim da execução, a janela "Assine para continuar".
"""
import streamlit as st

MENSAGEM = "Seu teste grátis terminou. Assine para voltar a cadastrar, editar e gerar PDFs."


class ContaSomenteLeitura(Exception):
    def __init__(self):
        super().__init__(MENSAGEM)


def ativo():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            return False
        return bool(st.session_state.get("somente_leitura"))
    except Exception:
        return False


def tentou():
    """Marca a tentativa: a janela de assinatura aparece no fim desta execução, e um aviso rápido
    aparece na hora (também dentro de fragmentos, onde o fim da execução do app não roda)."""
    try:
        st.session_state["_bloqueio_tentado"] = True
        st.toast(MENSAGEM, icon=":material/workspace_premium:")
    except Exception:
        pass


_ESCRITA = ("insert", "update", "delete")
_LIBERADAS = ("perfis",)


def _checar(statement):
    if not ativo():
        return
    if isinstance(statement, bytes):
        statement = statement.decode("utf-8", "ignore")
    sql = str(statement).lstrip().lower()
    if not sql.startswith(_ESCRITA):
        return
    cabeca = " ".join(sql[:160].split()) + " "
    if any(f" {t} " in cabeca or f" {t}(" in cabeca or f'"{t}"' in cabeca for t in _LIBERADAS):
        return
    tentou()
    raise ContaSomenteLeitura()


def instalar(engine):
    """Barra gravações da conta em modo consulta: no engine do SQLAlchemy e nas conexões
    psycopg2 abertas direto por alguns módulos (utils/database.py, finalizar_proposta_v2)."""
    from sqlalchemy import event

    @event.listens_for(engine, "before_cursor_execute")
    def _bloquear_escrita(conn, cursor, statement, parameters, context, executemany):
        _checar(statement)

    import psycopg2
    import psycopg2.extensions
    if getattr(psycopg2, "_po_somente_leitura", False):
        return

    class _Cursor(psycopg2.extensions.cursor):
        def execute(self, query, vars=None):
            _checar(query)
            return super().execute(query, vars)

        def executemany(self, query, vars_list):
            _checar(query)
            return super().executemany(query, vars_list)

    _connect = psycopg2.connect

    def _connect_vigiado(*args, **kwargs):
        kwargs.setdefault("cursor_factory", _Cursor)
        return _connect(*args, **kwargs)

    psycopg2.connect = _connect_vigiado
    psycopg2._po_somente_leitura = True


_liberado = __import__("contextvars").ContextVar("po_pdf_liberado", default=False)


class liberar_pdf:
    """Gera PDF mesmo em modo consulta (ex.: o manual do sistema)."""
    def __enter__(self):
        self._t = _liberado.set(True)

    def __exit__(self, *exc):
        _liberado.reset(self._t)


def _barrar_pdf():
    if ativo() and not _liberado.get():
        tentou()
        raise ContaSomenteLeitura()


def _instalar_pdf():
    """Todos os PDFs do app saem do reportlab: barra a montagem do arquivo em modo consulta."""
    try:
        from reportlab.platypus.doctemplate import BaseDocTemplate
        from reportlab.pdfgen.canvas import Canvas
    except Exception:
        return
    if getattr(BaseDocTemplate, "_po_vigiado", False):
        return
    build, save = BaseDocTemplate.build, Canvas.save

    def build_vigiado(self, *a, **k):
        _barrar_pdf()
        return build(self, *a, **k)

    def save_vigiado(self, *a, **k):
        _barrar_pdf()
        return save(self, *a, **k)

    BaseDocTemplate.build, Canvas.save = build_vigiado, save_vigiado
    BaseDocTemplate._po_vigiado = True


_instalar_pdf()

_download_original = st.download_button


def _download_button(label, data=None, file_name=None, mime=None, *args, **kwargs):
    """PDF em modo consulta: mostra o mesmo botão, mas abre o aviso de assinatura."""
    if ativo() and (mime == "application/pdf" or str(file_name or "").lower().endswith(".pdf")) \
            and kwargs.get("key") != "btn_manual_sidebar":
        kw = {k: v for k, v in kwargs.items() if k in ("key", "use_container_width", "icon", "help")}
        if st.button(label, **kw):
            tentou()
        return False
    return _download_original(label, data, file_name, mime, *args, **kwargs)


st.download_button = _download_button


def faixa():
    """Aviso no topo de todas as telas, com o caminho para assinar."""
    if not ativo():
        return
    with st.container(key="aviso_consulta"):
        c1, c2 = st.columns([4, 1.2], vertical_alignment="center")
        c1.markdown('<div class="ro-faixa"><b>Seu teste grátis terminou.</b> Você continua vendo tudo o que '
                    'cadastrou. Para cadastrar, editar e gerar PDFs, assine o Planner Organizer.</div>',
                    unsafe_allow_html=True)
        with c2, st.container(key="cta_assinar_consulta"):
            if st.button("Assinar agora", key="ro_assinar", icon=":material/workspace_premium:", use_container_width=True):
                st.session_state.current_page = "Plano"
                st.rerun()


CSS = """
<style>
.st-key-aviso_consulta { background: #FFF8E6; border: 1px solid #E3CF97; border-radius: 12px; padding: 8px 14px; margin-bottom: 10px; }
.ro-faixa { color: #5C4712; font-size: .92rem; line-height: 1.45; }
</style>
"""


def janela_se_tentou():
    """Chamar no fim da execução: quem tentou gravar ou gerar PDF vê o convite para assinar."""
    if not (ativo() and st.session_state.pop("_bloqueio_tentado", False)):
        return False

    @st.dialog("Assine para continuar")
    def _janela():
        st.markdown("**Seu teste grátis terminou.** Os seus dados estão guardados e você pode consultar "
                    "tudo. Para cadastrar, editar, aprovar propostas e gerar PDFs, escolha um plano.")
        c1, c2 = st.columns(2)
        with c1, st.container(key="cta_ver_planos"):
            if st.button("Ver planos", key="ro_ver_planos", use_container_width=True):
                st.session_state.current_page = "Plano"
                st.rerun()
        if c2.button("Agora não", key="ro_agora_nao", use_container_width=True):
            st.rerun()

    _janela()
    return True
