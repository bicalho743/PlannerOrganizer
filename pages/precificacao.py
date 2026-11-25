"""
Precificação: quanto vale a hora da organizer e quanto cobrar por um projeto.

Duas abas (seletor no topo):
- Sua hora: os números do mês (renda, custos, tempo vendido, taxas), os parâmetros do preço de projeto e de
  mudança e a lista de materiais. "Salvar meus números" grava tudo no perfil (Database.salvar_precificacao).
- Preço de um projeto: tipo de serviço, ambientes (ou caixas na mudança), equipe e custos; o painel escuro mostra
  o preço sugerido e "Criar proposta com este valor" abre a Nova proposta já preenchida
  (st.session_state["nova_proposta_prefill"]).

Os cálculos ficam em utils/precificacao.py (com testes); aqui só os campos e o resultado. O preço de um projeto
usa só pr.orcamento_completo.
"""
import streamlit as st

from utils import precificacao as pr
from utils.currency_formatter import fmt_brl
from utils.ui import cartao_clicavel, input_moeda
from utils.visual import esc

ABAS = ["Sua hora", "Preço de um projeto"]
MODOS_VOLUME = ["Total de caixas", "Por cômodo", "Pela área"]
FAIXA_MERCADO = (80.0, 350.0)  # guias de preço de 2026: de R$ 80 a R$ 350 por hora no Brasil
# ambientes do cartão de organização (a mudança agora é um tipo de serviço próprio, calculado pelas caixas)
AMBIENTES = [a for a in pr.AMBIENTES_PADRAO if not a.startswith("Mudança")]

# ícones de traço das abas (relógio e grade), desenhados por máscara para pegar a cor do texto
_SVG_RELOGIO = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
                "stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' "
                "cy='13' r='8'/%3E%3Cpath d='M12 9v4l2.5 2.5M10 2h4M12 2v3'/%3E%3C/svg%3E")
_SVG_GRADE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
              "stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='3' "
              "width='16' height='18' rx='2'/%3E%3Cpath d='M8 7h8M8 11h3M13 11h3M8 15h3M13 15h3'/%3E%3C/svg%3E")

CSS = """
<style>
.pc-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.pc-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.pc-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.pc-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 10px; }
.st-key-pc_aba { margin-bottom: 10px; }

/* seletor de abas */
.st-key-pc_aba [data-testid="stButtonGroup"] { background: #ECE7DC; border-radius: 14px; padding: 5px; display: inline-flex; width: auto; }
.st-key-pc_aba [data-testid="stButtonGroup"] > div { gap: 4px; flex-wrap: nowrap; }
.st-key-pc_aba button { background: transparent !important; border: 0 !important; border-radius: 10px !important;
                        padding: 9px 18px !important; min-height: 0 !important; box-shadow: none !important; color: #5B6B80 !important; }
.st-key-pc_aba button p { font-weight: 600 !important; font-size: 1rem !important; color: #5B6B80 !important;
                          display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; }
.st-key-pc_aba button[aria-checked="true"] { background: #fff !important;
        box-shadow: inset 0 -3px 0 var(--gold), 0 1px 3px rgba(0,0,0,.08) !important; }
.st-key-pc_aba button[aria-checked="true"] p { color: var(--navy) !important; }
.st-key-pc_aba button p::before { content: ""; width: 17px; height: 17px; flex: none; background: currentColor;
        -webkit-mask: var(--ic) center / contain no-repeat; mask: var(--ic) center / contain no-repeat; }
.st-key-pc_aba button:nth-of-type(1) p::before { --ic: url("RELOGIO"); }
.st-key-pc_aba button:nth-of-type(2) p::before { --ic: url("GRADE"); }

/* seções (cartões brancos numerados) */
[class*="st-key-pc_sec_"] { background: #fff; border: 1px solid #E7E2D6 !important; border-radius: 16px !important; padding: 22px !important; }
.pc-h3 { display: flex; align-items: center; gap: 8px; font-size: 1.06rem; font-weight: 700; color: var(--navy); margin: 0; }
.pc-n { flex: none; display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 50%;
        background: #F6EDD3; color: #9C7A22; font-size: .8rem; font-weight: 700; }
.pc-novo { background: #F6EDD3; color: #9C7A22; border-radius: 999px; padding: 2px 10px; font-size: .74rem; font-weight: 700; margin-left: 4px; }
.pc-d { font-size: .9rem; color: #5B6B80; margin: 2px 0 4px; }
.pc-rot { font-size: .82rem; color: #5B6B80; margin: 8px 0 2px; }
.pc-dica { font-size: .76rem; color: #8A8F98; margin-top: -10px; }
[class*="st-key-pc_sec_"] label p { font-size: .82rem !important; color: #5B6B80 !important; font-weight: 400 !important; }
[class*="st-key-pc_sec_"] [data-testid="stNumberInputStepUp"], [class*="st-key-pc_sec_"] [data-testid="stNumberInputStepDown"] { display: none; }
[class*="st-key-pc_sec_"] .stNumberInput input, [class*="st-key-pc_sec_"] .stTextInput input {
        border-color: #E7E2D6 !important; border-radius: 10px !important; min-height: 44px; }
.st-key-pc_salvar_box { align-items: flex-end; }
.st-key-pc_salvar_box .stButton > button { padding: 10px 22px; }

/* painel escuro */
.pc-res { background: var(--navy); color: #fff; border-radius: 18px; padding: 24px; }
.st-key-pc_res { background: var(--navy); border-radius: 18px; padding: 24px; gap: 0 !important; }
.pc-res .l, .st-key-pc_res .l { font-size: .82rem; color: rgba(255,255,255,.72); }
.pc-v { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 3.1rem; color: var(--gold); font-weight: 600; line-height: 1.1;
        margin: 4px 0 2px; }
.pc-ln { display: flex; justify-content: space-between; gap: 10px; font-size: .9rem; color: #fff; padding: 8px 0;
         border-top: 1px solid rgba(255,255,255,.12); }
.pc-ln b { font-variant-numeric: tabular-nums; white-space: nowrap; }
.pc-ln b.ouro { color: var(--gold); }
.pc-lns { margin-top: 16px; }
.pc-barra { height: 10px; border-radius: 6px; background: rgba(255,255,255,.12); margin: 10px 0 4px; position: relative; }
.pc-barra i { position: absolute; left: 0; top: 0; bottom: 0; background: var(--gold); border-radius: 6px; }
.pc-faixa { display: flex; justify-content: space-between; font-size: .74rem; color: rgba(255,255,255,.7); }
.pc-nota { background: #fff; border: 1px solid #E7E2D6; border-radius: 14px; padding: 16px; margin-top: 14px; font-size: .9rem; color: #5B6B80; }
.pc-nota b { color: var(--navy); }
.pc-nota.peq { font-size: .82rem; }
.st-key-cta_pc_proposta { margin-top: 18px; }
.st-key-cta_pc_proposta .stButton > button { min-height: 46px; }
.pc-mini { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
.pc-mini div { background: #fff; border: 1px solid #E7E2D6; border-radius: 12px; padding: 12px 14px; min-width: 0; }
.pc-mini b { display: block; font-size: 1.35rem; color: var(--navy); font-variant-numeric: tabular-nums; white-space: nowrap; }
.pc-mini span { font-size: .76rem; color: #5B6B80; }

/* cartões de escolha (tipo de serviço, ambientes, cômodos) */
.kanban-card.pc-card { border: 1.5px solid #E7E2D6 !important; border-radius: 14px !important; background: #fff; box-shadow: none !important;
        padding: 14px 16px !important; margin: 0 !important; min-height: 84px; }
.kanban-card.pc-card.on { border-color: var(--gold) !important; background: #F6EDD3; }
.kanban-card.pc-card.tipo { min-height: 0; padding: 15px 16px !important; }
.kanban-card.pc-card.outro { border-style: dashed !important; }
[class*="st-key-kcard_pc"]:hover .kanban-card.pc-card { border-color: #C9A84C !important; box-shadow: 0 2px 8px rgba(16,24,40,.06) !important; }
.pc-card b, .pc-amb-t b { color: var(--navy); font-size: .98rem; overflow-wrap: anywhere; }
.pc-card .h { display: block; font-size: .82rem; color: #5B6B80; margin-top: 2px; }
.pc-card.outro b { color: #9C7A22; }
.pc-amb-t { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.pc-chip { flex: none; border-radius: 999px; padding: 2px 9px; font-size: .74rem; font-weight: 700; background: #F1EEE7; color: #5B6B80; white-space: nowrap; }
.pc-chip.on { background: #F6EDD3; color: #9C7A22; }
[class*="st-key-pcon_"] { border: 1.5px solid var(--gold) !important; border-radius: 14px !important; background: #fff;
        padding: 14px 13px 14px 16px !important; gap: 8px !important; min-height: 84px; }
[class*="st-key-pcstep_"] [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important;
        gap: 6px !important; align-items: center !important; }
[class*="st-key-pcstep_"] [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
[class*="st-key-pcstep_"] [data-testid="stColumn"]:last-child { flex: 1 1 auto !important; }
[class*="st-key-pcstep_"] .stButton > button { width: 30px !important; height: 30px !important; min-height: 30px !important; padding: 0 !important;
        border-radius: 8px !important; border: 1px solid #E7E2D6 !important; background: #fff !important; }
[class*="st-key-pcstep_"] .stButton > button p { font-weight: 700 !important; color: var(--navy) !important; font-size: 1rem !important; }
.pc-q { font-weight: 700; color: var(--navy); min-width: 18px; text-align: center; display: block; }
.pc-qr { font-size: .82rem; color: #5B6B80; white-space: nowrap; }

/* grades de cartões: uma linha de colunas que quebra em 3, 2 ou 1 por linha */
.st-key-pc_grade_tipo, [class*="st-key-pc_grade_"] { container-type: inline-size; }
[class*="st-key-pc_grade_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
        flex-direction: row !important; flex-wrap: wrap !important; gap: 12px !important; align-items: stretch !important; }
[class*="st-key-pc_grade_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 0 0 calc((100% - 24px) / 3) !important; width: calc((100% - 24px) / 3) !important; min-width: 0 !important; }
[class*="st-key-pc_grade_"] [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height: 100%; }
[class*="st-key-pc_grade_"] [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"],
[class*="st-key-pc_grade_"] [class*="st-key-kcard_pc"],
[class*="st-key-pc_grade_"] [class*="st-key-kcard_pc"] [data-testid="stElementContainer"]:has(.stMarkdown),
[class*="st-key-pc_grade_"] [class*="st-key-kcard_pc"] .stMarkdown,
[class*="st-key-pc_grade_"] [class*="st-key-kcard_pc"] .stMarkdown > div,
[class*="st-key-pc_grade_"] [class*="st-key-kcard_pc"] [data-testid="stMarkdownContainer"],
[class*="st-key-pc_grade_"] [class*="st-key-kcard_pc"] .kanban-card,
[class*="st-key-pc_grade_"] [class*="st-key-pcon_"] { flex: 1 1 auto; display: flex; flex-direction: column; }
[class*="st-key-pc_grade_"] [class*="st-key-pcon_"] { gap: 10px !important; container-type: inline-size; }
[class*="st-key-pcon_"] [data-testid="stMarkdownContainer"], [class*="st-key-kcard_pc"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[class*="st-key-pcon_"] [data-testid="stElementContainer"] { height: auto !important; }
@container (max-width: 140px) { .pc-qr { display: none; } }
[class*="st-key-pcstep_"] [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height: 30px; justify-content: center; }
[class*="st-key-pcstep_"] [data-testid="stElementContainer"] { height: 30px !important; display: flex; align-items: center; }
[class*="st-key-pcstep_"] .stButton { height: 30px; }
[class*="st-key-pcstep_"] [data-testid="stMarkdownContainer"] p { margin: 0 !important; }
.st-key-cta_pc_proposta .stButton > button:disabled { background: rgba(255,255,255,.10) !important; border-color: transparent !important; }
.st-key-cta_pc_proposta .stButton > button:disabled p { color: rgba(255,255,255,.5) !important; }
@container (max-width: 560px) {
  [class*="st-key-pc_grade_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 0 0 calc((100% - 12px) / 2) !important; width: calc((100% - 12px) / 2) !important; }
  .st-key-pc_grade_tipo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 0 0 100% !important; width: 100% !important; }
}
@container (max-width: 260px) {
  [class*="st-key-pc_grade_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 0 0 100% !important; width: 100% !important; }
}

/* complexidade e modo do volume */
.st-key-pc_compl button, .st-key-pc_modo_vol button { border: 1.5px solid #E7E2D6 !important; border-radius: 10px !important;
        background: #fff !important; box-shadow: none !important; }
.st-key-pc_compl [data-testid="stButtonGroup"] > div, .st-key-pc_modo_vol [data-testid="stButtonGroup"] > div { gap: 8px; }
.st-key-pc_compl button p, .st-key-pc_modo_vol button p { font-weight: 600 !important; color: var(--navy) !important; }
.st-key-pc_compl button[aria-checked="true"], .st-key-pc_modo_vol button[aria-checked="true"] {
        border-color: var(--gold) !important; background: #F6EDD3 !important; }

/* botões só-texto dourados */
[class*="st-key-pc_lnk"] button, [class*="st-key-pc_lnk"] button p { color: #9C7A22 !important; font-weight: 700 !important; }
[class*="st-key-pc_lnk"] button:hover p { text-decoration: underline; }

/* materiais */
.pc-mat-cab { font-size: .78rem; color: #5B6B80; }
.st-key-pcmat_cab { margin-bottom: -12px; }
[class*="st-key-pcmat_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { gap: 12px !important; align-items: center !important; }
[class*="st-key-pcmat_"] .stButton > button { min-height: 44px; }
.pc-mq { display: flex; justify-content: space-between; gap: 8px; }
.pc-mq b { color: var(--navy); font-size: .95rem; overflow-wrap: anywhere; }
.pc-mq span { display: block; font-size: .8rem; color: #5B6B80; }
[class*="st-key-pcmq_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
        flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; gap: 12px !important; }
[class*="st-key-pcmq_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        flex: 0 0 110px !important; width: 110px !important; min-width: 0 !important; }
[class*="st-key-pcmq_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        min-width: 0 !important; }
.pc-tot { margin-top: 6px; font-size: .9rem; color: #5B6B80; }
.pc-tot b { color: var(--navy); }

/* corpo: formulário à esquerda e painel à direita; empilha em tela média */
.st-key-pc_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { gap: 22px !important; flex-wrap: nowrap !important; }
.st-key-pc_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        flex: 1 1 0 !important; width: auto !important; min-width: 0 !important; }
.st-key-pc_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        flex: 0 0 360px !important; width: 360px !important; position: sticky; top: 3.5rem; align-self: flex-start; }
@media (max-width: 1280px) {
  .st-key-pc_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-pc_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-pc_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        flex: 1 1 100% !important; width: 100% !important; position: static; }
}
@media (max-width: 640px) {
  h1.pc-titulo { font-size: 2.1rem !important; }
  [class*="st-key-pc_sec_"] { padding: 16px !important; }
  .st-key-pc_aba button { padding: 8px 12px !important; }
  .st-key-pc_aba button p { font-size: .92rem !important; }
  .pc-v { font-size: 2.6rem; }
  .st-key-pcmat_cab { display: none; }
  [class*="st-key-pcmat_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; row-gap: 8px !important; }
  [class*="st-key-pcmat_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        flex: 1 1 100% !important; width: 100% !important; }
  [class*="st-key-pcmat_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:not(:first-child) {
        flex: 1 1 0 !important; width: auto !important; min-width: 0 !important; }
  [class*="st-key-pcmat_"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        flex: 0 0 44px !important; }
  [class*="st-key-pc_campos"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  [class*="st-key-pc_campos"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 calc(50% - 8px) !important; width: calc(50% - 8px) !important; min-width: 0 !important; }
}
</style>
""".replace("RELOGIO", _SVG_RELOGIO).replace("GRADE", _SVG_GRADE)


# ---------- formatação ----------

def _r(v):
    """R$ sem centavos, com ponto de milhar."""
    return "R$ " + f"{round(float(v or 0)):,}".replace(",", ".")


def _h(v):
    v = float(v or 0)
    return f"{round(v)} h" if abs(v - round(v)) < 0.05 else f"{v:.1f} h".replace(".", ",")


def _num_br(v):
    v = float(v or 0)
    return f"{v:g}".replace(".", ",")


def _sec(n, titulo, desc="", novo=False):
    chip = '<span class="pc-novo">novo</span>' if novo else ""
    d = f'<div class="pc-d">{desc}</div>' if desc else ""
    return f'<div class="pc-h3"><span class="pc-n">{n}</span>{titulo}{chip}</div>{d}'


def _md(html):
    st.markdown(html, unsafe_allow_html=True)


# ---------- estado ----------

def _parametros():
    """Números salvos da organizer (ou os padrões), carregados uma vez por sessão."""
    if "_pc_param" not in st.session_state:
        salvos = {}
        try:
            salvos = st.session_state.db.get_precificacao() or {}
        except Exception as e:
            print(f"[precificacao] {e}")
        st.session_state["_pc_param"] = {**pr.PADROES, **salvos}
    return st.session_state["_pc_param"]


def _materiais_estado(p):
    """Linhas da lista de materiais em edição (com um id estável só para as chaves dos campos)."""
    if "_pc_mats" not in st.session_state:
        st.session_state["_pc_mats"] = [{"id": i, "nome": str(m.get("nome") or ""), "preco": float(m.get("preco") or 0),
                                         "unidade": str(m.get("unidade") or "")}
                                        for i, m in enumerate(pr.materiais(p))]
        st.session_state["_pc_mats_seq"] = len(st.session_state["_pc_mats"])
    return st.session_state["_pc_mats"]


def _projeto():
    """O que ela marcou no preço de um projeto (fica entre as abas; os campos se recriam a partir daqui)."""
    if "_pc_proj" not in st.session_state:
        st.session_state["_pc_proj"] = {
            "tipo": "organizacao", "qtd": {}, "horas": {}, "extras": [], "novo_amb": False, "ajustar": False,
            "modo_vol": MODOS_VOLUME[0], "caixas_total": 0, "comodos": {}, "area": 0.0, "mat_qtd": {},
            "compl": "Média", "assistentes": 0, "km": 0.0, "outros": 0.0,
        }
    return st.session_state["_pc_proj"]


def _mudar(dic, nome, delta):
    dic[nome] = max(0, int(dic.get(nome, 0)) + delta)


def _manter_escolha(chave, guardado, padrao):
    """Segmented control: clicar de novo no selecionado não deixa a escolha vazia."""
    if not st.session_state.get(chave):
        st.session_state[chave] = st.session_state.get(guardado) or padrao


# ---------- cabeçalho e abas ----------

def _cabecalho():
    _md('<div class="pc-eyebrow">Seus números, seu preço</div><h1 class="pc-titulo">Precificação</h1>'
        '<div class="pc-sub">Quanto vale a sua hora e quanto cobrar por cada projeto, com os seus números.</div>')
    st.session_state.setdefault("_pc_aba_ult", ABAS[0])
    if not st.session_state.get("pc_aba"):
        st.session_state["pc_aba"] = st.session_state["_pc_aba_ult"]
    aba = st.segmented_control("Aba", ABAS, key="pc_aba", label_visibility="collapsed",
                               on_change=_manter_escolha, args=("pc_aba", "_pc_aba_ult", ABAS[0]))
    aba = aba or st.session_state["_pc_aba_ult"]
    st.session_state["_pc_aba_ult"] = aba
    return aba


# ---------- aba Sua hora ----------

def _campos(chave, n=2):
    with st.container(key=f"pc_campos_{chave}"):
        return st.columns(n, gap="small")


def _secao_materiais():
    linhas = st.session_state["_pc_mats"]

    def _remover(i):
        st.session_state["_pc_mats"] = [m for m in st.session_state["_pc_mats"] if m["id"] != i]

    def _adicionar():
        seq = st.session_state.get("_pc_mats_seq", len(st.session_state["_pc_mats"]))
        st.session_state["_pc_mats"].append({"id": seq, "nome": "", "preco": 0.0, "unidade": "un"})
        st.session_state["_pc_mats_seq"] = seq + 1

    with st.container(key="pcmat_cab"):
        for col, rot in zip(st.columns([3, 1.3, 1.2, 0.36], gap="small"), ("Material", "Preço (R$)", "Unidade", "")):
            col.markdown(f'<div class="pc-mat-cab">{rot}</div>', unsafe_allow_html=True)
    for m in linhas:
        i = m["id"]
        with st.container(key=f"pcmat_{i}"):
            c1, c2, c3, c4 = st.columns([3, 1.3, 1.2, 0.36], gap="small", vertical_alignment="center")
            m["nome"] = c1.text_input("Material", m["nome"], key=f"pc_mat_n_{i}", label_visibility="collapsed",
                                      placeholder="Nome do material", max_chars=60)
            m["preco"] = float(c2.number_input("Preço (R$)", 0.0, 100000.0, float(m["preco"]), 0.5, format="%.2f",
                                               key=f"pc_mat_p_{i}", label_visibility="collapsed"))
            m["unidade"] = c3.text_input("Unidade", m["unidade"], key=f"pc_mat_u_{i}", label_visibility="collapsed",
                                         placeholder="un, rolo, kit", max_chars=20)
            c4.button("", key=f"pc_mat_x_{i}", icon=":material/delete:", type="tertiary", help="Remover este material",
                      on_click=_remover, args=(i,))
    with st.container(key="pc_lnk_mat"):
        st.button("+ Adicionar material", key="pc_mat_add", type="tertiary", on_click=_adicionar)


def _painel_hora(p):
    minima, sugerida = pr.hora_minima(p), pr.hora_sugerida(p)
    horas_dia = float(p.get("horas_dia") or 0)
    lo, hi = FAIXA_MERCADO
    pos = min(max((sugerida - lo) / (hi - lo), 0.0), 1.0) * 100
    _md(f'<div class="pc-res"><div class="l">Sua hora sugerida</div><div class="pc-v">{_r(sugerida)}</div>'
        f'<div class="l">com {float(p.get("margem_pct") or 0):g}% de margem</div>'
        f'<div class="pc-lns"><div class="pc-ln"><span>Hora mínima</span><b>{_r(minima)}</b></div>'
        f'<div class="pc-ln"><span>Horas que você vende</span><b>{pr.horas_vendidas(p):.0f} h/mês</b></div>'
        f'<div class="pc-ln"><span>Custos fixos</span><b>{_r(pr.custos_fixos(p))}/mês</b></div>'
        f'<div class="pc-ln"><span>Diária sugerida ({_h(horas_dia)})</span>'
        f'<b class="ouro">{_r(round(sugerida) * horas_dia)}</b></div></div>'
        f'<div class="l" style="margin-top:12px">Onde você está na faixa do mercado</div>'
        f'<div class="pc-barra"><i style="width:{max(pos, 4):.0f}%"></i></div>'
        f'<div class="pc-faixa"><span>{_r(lo)}</span><span>{_r(hi)}/h</span></div></div>')
    _md(f'<div class="pc-nota"><b>Abaixo de {_r(minima)} a hora, a conta do mês não fecha.</b> Use a sua conta, '
        'não a média do mercado: ela mostra o que o seu negócio precisa. Guias de preço de 2026 apontam de R$ 80 a '
        'R$ 350 por hora no Brasil, conforme cidade e experiência.</div>')
    _md('<div class="pc-nota peq">O Planner Organiza não é contador. Em dúvida sobre impostos e alíquota, '
        'procure um contador.</div>')


def _aba_hora(p):
    _materiais_estado(p)
    with st.container(key="pc_corpo"):
        esq, dir_ = st.columns([2, 1], gap="medium")
    with esq:
        with st.container(key="pc_sec_ganhar"):
            _md(_sec(1, "Quanto você quer ganhar", "O valor que precisa sobrar para você no fim do mês."))
            c1, c2 = _campos("ganhar")
            with c1:
                p["renda_desejada"] = input_moeda("Por mês (R$)", "pc_renda", p["renda_desejada"])
            with c2:
                p["margem_pct"] = float(st.number_input("Margem de lucro (%)", 0.0, 200.0, float(p["margem_pct"]), 5.0,
                                                        format="%g", key="pc_margem"))
                _md('<div class="pc-dica">Para reinvestir, imprevistos e meses fracos</div>')

        with st.container(key="pc_sec_gastos"):
            _md(_sec(2, "Quanto você gasta para trabalhar"))
            desc = st.empty()
            c1, c2 = _campos("gastos")
            with c1:
                p["custo_impostos_fixos"] = input_moeda("Impostos fixos (DAS do MEI)", "pc_das",
                                                        p["custo_impostos_fixos"], step=10.0)
                p["custo_ferramentas"] = input_moeda("Ferramentas, celular, marketing e cursos", "pc_ferr",
                                                     p["custo_ferramentas"], step=50.0)
            with c2:
                p["custo_transporte"] = input_moeda("Transporte", "pc_transp", p["custo_transporte"], step=50.0)
                p["custo_outros"] = input_moeda("Outros custos", "pc_outros", p["custo_outros"], step=50.0)
            desc.markdown(f'<div class="pc-d">Custos que existem mesmo sem cliente. Somam '
                          f'{_r(pr.custos_fixos(p))} por mês.</div>', unsafe_allow_html=True)

        with st.container(key="pc_sec_tempo"):
            _md(_sec(3, "Quanto tempo você vende",
                     "Só as horas na casa da cliente. Orçamento, compras e deslocamento não contam."))
            c1, c2 = _campos("tempo")
            with c1:
                p["dias_mes"] = int(st.number_input("Dias de atendimento no mês", 1, 31, int(p["dias_mes"]), 1,
                                                    key="pc_dias"))
            with c2:
                p["horas_dia"] = float(st.number_input("Horas por dia de atendimento", 1.0, 14.0, float(p["horas_dia"]),
                                                       0.5, format="%g", key="pc_horas_dia"))

        with st.container(key="pc_sec_taxas"):
            _md(_sec(4, "Taxas de cada venda", "Entram em todo preço de projeto e de mudança.", novo=True))
            c1, c2 = _campos("taxas")
            with c1:
                p["imposto_pct"] = float(st.number_input("Imposto sobre a venda (%)", 0.0, 30.0, float(p["imposto_pct"]),
                                                         0.5, format="%g", key="pc_imp"))
                _md('<div class="pc-dica">MEI: 0 (o DAS já está nos custos). Simples Nacional: a sua alíquota.</div>')
            with c2:
                p["taxa_cartao_pct"] = float(st.number_input("Taxa do cartão / maquininha (%)", 0.0, 30.0,
                                                             float(p["taxa_cartao_pct"]), 0.1, format="%g",
                                                             key="pc_taxa"))
            c1, c2 = _campos("taxas2")
            with c1:
                p["km_valor"] = input_moeda("Valor por km rodado (R$)", "pc_km_valor", p["km_valor"], step=0.1)
            with c2:
                p["valor_hora_assistente"] = input_moeda("Hora de cada assistente (R$)", "pc_v_assist",
                                                         p["valor_hora_assistente"], step=5.0)

        with st.container(key="pc_sec_projetos"):
            _md(_sec(5, "Projetos e mudanças",
                     "Usados no preço de cada projeto: a margem de segurança, o sinal e quantas caixas uma pessoa "
                     "faz por dia na mudança."))
            c1, c2 = _campos("projetos")
            with c1:
                p["seguranca_pct"] = float(st.number_input("Margem de segurança (%)", 0.0, 100.0,
                                                           float(p["seguranca_pct"]), 1.0, format="%g",
                                                           key="pc_seg"))
                p["caixas_dia_pre"] = int(st.number_input("Caixas por pessoa por dia, para embalar", 1, 200,
                                                          int(p["caixas_dia_pre"]), 1, key="pc_cx_pre"))
            with c2:
                p["sinal_pct"] = float(st.number_input("Sinal na aprovação (%)", 0.0, 100.0, float(p["sinal_pct"]), 5.0,
                                                       format="%g", key="pc_sinal_h"))
                p["caixas_dia_pos"] = int(st.number_input("Caixas por pessoa por dia, para desembalar", 1, 200,
                                                          int(p["caixas_dia_pos"]), 1, key="pc_cx_pos"))

        with st.container(key="pc_sec_materiais"):
            _md(_sec(6, "Seus materiais", "O preço de cada material que você leva ou compra. Entram no preço "
                                          "das mudanças."))
            _secao_materiais()

        p["materiais"] = [{"nome": m["nome"].strip(), "preco": float(m["preco"] or 0),
                           "unidade": (m["unidade"] or "").strip()}
                          for m in st.session_state["_pc_mats"] if (m["nome"] or "").strip()]

        with st.container(key="pc_salvar_box"):
            salvar = st.button("Salvar meus números", type="primary", key="pc_salvar")
        if salvar:
            dados = {k: p[k] for k in pr.PADROES}
            dados["materiais"] = p["materiais"]
            if st.session_state.db.salvar_precificacao(dados):
                st.success("Números salvos. Eles valem para o preço de cada projeto e para a Nova proposta.")
            else:
                st.error("Não consegui salvar agora. Tente de novo.")
    with dir_:
        _painel_hora(p)


# ---------- aba Preço de um projeto ----------

def _cartao_opcao(chave, titulo, sub, chip="", on=False, cls=""):
    """Cartão que se toca inteiro (tipo de serviço, ambiente ou cômodo fora do projeto)."""
    chip_html = f'<span class="pc-chip{" on" if on else ""}">{chip}</span>' if chip else ""
    html = (f'<div class="kanban-card pc-card {cls}{" on" if on else ""}"><div class="pc-amb-t"><b>{titulo}</b>'
            f'{chip_html}</div><span class="h">{sub}</span></div>')
    return cartao_clicavel(html, key=f"pc{chave}", rotulo=titulo)


def _cartao_incluido(chave, titulo, chip, dic, nome, singular, plural, horas=None):
    """Cartão já no projeto: − quantidade +. horas: dict onde fica o tempo por ambiente (ela muda ali mesmo)."""
    with st.container(key=f"pcon_{chave}"):
        _md(f'<div class="pc-amb-t"><b>{titulo}</b><span class="pc-chip on">{chip}</span></div>')
        q = int(dic.get(nome, 0))
        with st.container(key=f"pcstep_{chave}"):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 3], gap="small", vertical_alignment="center")
            c1.button("−", key=f"pc_menos_{chave}", on_click=_mudar, args=(dic, nome, -1))
            c2.markdown(f'<span class="pc-q">{q}</span>', unsafe_allow_html=True)
            c3.button("+", key=f"pc_mais_{chave}", on_click=_mudar, args=(dic, nome, 1))
            c4.markdown(f'<span class="pc-qr">{singular if q == 1 else plural}</span>', unsafe_allow_html=True)
        if horas is not None:
            atual = float(horas.get(nome, pr.AMBIENTES_PADRAO.get(nome, 3.0)))
            horas[nome] = float(st.number_input("Horas neste ambiente", 0.5, 80.0, atual, 0.5, format="%g",
                                                key=f"pc_hcard_{chave}", help="Tempo que você gasta neste ambiente. "
                                                "Vale para este projeto."))


def _grade_cartoes(prefixo, itens, dic, singular, plural, extra=None, horas=None):
    """itens: [(nome, chip)]. extra: (titulo, sub) do cartão tracejado do fim, ou None. Devolve True se o extra
    foi tocado."""
    total = len(itens) + (1 if extra else 0)
    tocou_extra = False
    with st.container(key=f"pc_grade_{prefixo}"):
        cols = st.columns(total, gap="small")
    for i, (nome, chip) in enumerate(itens):
        with cols[i]:
            if int(dic.get(nome, 0)) > 0:
                _cartao_incluido(f"{prefixo}{i}", esc(nome), chip, dic, nome, singular, plural, horas)
            elif _cartao_opcao(f"{prefixo}{i}", esc(nome), "Toque para incluir", chip):
                dic[nome] = 1
                st.rerun()
    if extra:
        with cols[-1]:
            tocou_extra = _cartao_opcao(f"{prefixo}_outro", extra[0], extra[1], cls="outro")
    return tocou_extra


def _secao_ambientes(proj, n):
    with st.container(key="pc_sec_ambientes"):
        _md(_sec(n, "Quais ambientes?", "Toque para incluir. As horas são um ponto de partida: ajuste pela sua "
                                        "experiência."))
        nomes = AMBIENTES + [e for e in proj["extras"] if e not in AMBIENTES]
        itens = [(a, _h(proj["horas"].get(a, pr.AMBIENTES_PADRAO.get(a, 0)))) for a in nomes]
        for i, a in enumerate(nomes):   # horas mudadas no cartão valem já para o chip
            if f"pc_hcard_amb{i}" in st.session_state and int(proj["qtd"].get(a, 0)):
                proj["horas"][a] = float(st.session_state[f"pc_hcard_amb{i}"])
        itens = [(a, _h(proj["horas"].get(a, pr.AMBIENTES_PADRAO.get(a, 0)))) for a in nomes]
        if _grade_cartoes("amb", itens, proj["qtd"], "ambiente", "ambientes",
                          extra=("+ Outro ambiente", "Garagem, área gourmet…"), horas=proj["horas"]):
            proj["novo_amb"] = not proj["novo_amb"]
            st.rerun()

        if proj["novo_amb"]:
            with st.form("pc_form_amb", clear_on_submit=True, border=False):
                c1, c2 = st.columns([2, 1], gap="small")
                nome = c1.text_input("Nome do ambiente", placeholder="Ex.: Garagem", max_chars=40)
                horas = c2.number_input("Horas", 0.5, 40.0, 4.0, 0.5, format="%.1f")
                b1, b2 = st.columns([1, 1], gap="small")
                incluir = b1.form_submit_button("Incluir ambiente", type="primary", use_container_width=True)
                cancelar = b2.form_submit_button("Cancelar", use_container_width=True)
            if incluir:
                nome = (nome or "").strip()
                if not nome:
                    st.warning("Escreva o nome do ambiente.")
                elif nome in nomes:
                    st.warning("Esse ambiente já está na lista.")
                else:
                    proj["extras"].append(nome)
                    proj["horas"][nome] = float(horas)
                    proj["qtd"][nome] = 1
                    proj["novo_amb"] = False
                    st.rerun()
            if cancelar:
                proj["novo_amb"] = False
                st.rerun()

        with st.container(key="pc_lnk_ajustar"):
            if st.button("Fechar o ajuste das horas" if proj["ajustar"] else "Ajustar as horas de cada ambiente",
                         key="pc_ajustar", type="tertiary"):
                proj["ajustar"] = not proj["ajustar"]
                st.rerun()
        if proj["ajustar"]:
            with st.container(key="pc_campos_horas"):
                cols = st.columns(3, gap="small")
            for i, a in enumerate(nomes):
                with cols[i % 3]:
                    padrao = proj["horas"].get(a, pr.AMBIENTES_PADRAO.get(a, 0))
                    proj["horas"][a] = float(st.number_input(f"{a} (h)", 0.0, 80.0, float(padrao), 0.5, format="%g",
                                                             key=f"pc_h_{i}"))
                    if a in proj["extras"]:
                        with st.container(key=f"pc_lnk_rm{i}"):
                            if st.button(f"Remover {a}", key=f"pc_rm_amb_{i}", type="tertiary"):
                                proj["extras"].remove(a)
                                proj["qtd"].pop(a, None)
                                proj["horas"].pop(a, None)
                                st.rerun()
    horas = sum(int(proj["qtd"].get(a, 0)) * float(proj["horas"].get(a, pr.AMBIENTES_PADRAO.get(a, 0)))
                for a in nomes)
    qtd = sum(int(proj["qtd"].get(a, 0)) for a in nomes)
    return horas, qtd


def _secao_volume(proj, p, tipo, n):
    por_dia = int(p.get(f"caixas_dia_{tipo}") or 0)
    acao = "embala e inventaria" if tipo == "pre" else "desembala e organiza"
    with st.container(key="pc_sec_volume"):
        _md(_sec(n, "Quanto volume?", f"Na mudança, o tempo vem das caixas: uma pessoa {acao} {por_dia} caixas por "
                                      "dia (ajuste em Sua hora)."))
        st.session_state.setdefault("_pc_modo_ult", proj["modo_vol"])
        if not st.session_state.get("pc_modo_vol"):
            st.session_state["pc_modo_vol"] = proj["modo_vol"]
        modo = st.segmented_control("Como contar", MODOS_VOLUME, key="pc_modo_vol", label_visibility="collapsed",
                                    on_change=_manter_escolha, args=("pc_modo_vol", "_pc_modo_ult", MODOS_VOLUME[0]))
        modo = modo or proj["modo_vol"]
        proj["modo_vol"] = st.session_state["_pc_modo_ult"] = modo
        if modo == "Total de caixas":
            with _campos("vol")[0]:
                proj["caixas_total"] = int(st.number_input("Total de caixas", 0, 5000, int(proj["caixas_total"]), 1,
                                                           key="pc_cx_total"))
            caixas = proj["caixas_total"]
        elif modo == "Por cômodo":
            _md('<div class="pc-d">Toque nos cômodos da casa. As caixas de cada um são um ponto de partida.</div>')
            itens = [(c, f"{n_cx} caixas") for c, n_cx in pr.CAIXAS_POR_COMODO.items()]
            _grade_cartoes("com", itens, proj["comodos"], "cômodo", "cômodos")
            caixas = sum(int(proj["comodos"].get(c, 0)) * n_cx for c, n_cx in pr.CAIXAS_POR_COMODO.items())
        else:
            with _campos("vol")[0]:
                proj["area"] = float(st.number_input("Área do imóvel (m²)", 0.0, 5000.0, float(proj["area"]), 5.0,
                                                     format="%g", key="pc_area"))
            caixas = pr.caixas_por_area(proj["area"])
            _md('<div class="pc-d">Estimativa sem vistoria: cerca de uma caixa a cada 3 m².</div>')
        _md(f'<div class="pc-tot">Volume da mudança: <b>{caixas} caixas</b></div>')
    return int(caixas)


def _secao_materiais_projeto(proj, p, n):
    escolhidos = []
    with st.container(key="pc_sec_mat_proj"):
        _md(_sec(n, "Materiais", "Quantos de cada material entram nesta mudança. Os preços vêm da sua lista "
                                 "em Sua hora."))
        lista = pr.materiais(p)
        for i, m in enumerate(lista):
            nome = str(m.get("nome") or "")
            preco = float(m.get("preco") or 0)
            un = str(m.get("unidade") or "")
            preco_txt = f"{fmt_brl(preco)} / {esc(un)}" if preco > 0 else f"preço {esc(un) or 'a definir'}"
            with st.container(key=f"pcmq_{i}"):
                c1, c2 = st.columns([3, 1], gap="small", vertical_alignment="center")
                c1.markdown(f'<div class="pc-mq"><div><b>{esc(nome)}</b><span>{preco_txt}</span></div></div>',
                            unsafe_allow_html=True)
                q = c2.number_input(f"Quantidade de {nome}", 0.0, 10000.0, float(proj["mat_qtd"].get(nome, 0)), 1.0,
                                    format="%g", key=f"pc_mq_{i}", label_visibility="collapsed")
            proj["mat_qtd"][nome] = float(q)
            if q > 0:
                escolhidos.append((nome, float(q), preco))
    return escolhidos


def _secao_equipe(proj, p, tipo, n):
    with st.container(key="pc_sec_equipe"):
        _md(_sec(n, "Equipe e custos", "Quem vai com você e o que entra no preço."))
        compl = 1.0
        if tipo == "organizacao":
            _md('<div class="pc-rot">Complexidade</div>')
            opcoes = list(pr.COMPLEXIDADE)
            st.session_state.setdefault("_pc_compl_ult", proj["compl"])
            if not st.session_state.get("pc_compl"):
                st.session_state["pc_compl"] = proj["compl"]
            nivel = st.segmented_control("Complexidade", opcoes, key="pc_compl", label_visibility="collapsed",
                                         on_change=_manter_escolha, args=("pc_compl", "_pc_compl_ult", "Média"))
            nivel = nivel or proj["compl"]
            proj["compl"] = st.session_state["_pc_compl_ult"] = nivel
            compl = float(pr.COMPLEXIDADE[nivel])
        c1, c2, c3 = _campos("equipe", 3)
        with c1:
            proj["assistentes"] = int(st.number_input("Assistentes", 0, 10, int(proj["assistentes"]), 1,
                                                      key="pc_assist"))
        with c2:
            proj["km"] = float(st.number_input("Deslocamento (km)", 0.0, 5000.0, float(proj["km"]), 1.0,
                                               format="%g", key="pc_km"))
            _md(f'<div class="pc-dica">Ida e volta. {fmt_brl(p["km_valor"])} por km, por dia de serviço</div>')
        with c3:
            proj["outros"] = input_moeda("Outros custos (R$)", "pc_outros_proj", proj["outros"], step=10.0)
            _md('<div class="pc-dica">Estacionamento, etiquetas, consumo</div>')
        c1, c2, c3 = _campos("equipe2", 3)
        with c1:
            p["sinal_pct"] = float(st.number_input("Sinal na aprovação (%)", 0.0, 100.0, float(p["sinal_pct"]), 5.0,
                                                   format="%g", key="pc_sinal"))
        with c2:
            p["taxa_cartao_pct"] = float(st.number_input("Taxa do cartão (%)", 0.0, 30.0, float(p["taxa_cartao_pct"]),
                                                         0.1, format="%g", key="pc_taxa_proj"))
        with c3:
            p["seguranca_pct"] = float(st.number_input("Margem de segurança (%)", 0.0, 100.0, float(p["seguranca_pct"]),
                                                       1.0, format="%g", key="pc_seg_proj"))
    return compl


def _painel_projeto(o, p, tipo, qtd_amb, prefill):
    vazio = o["total"] <= 0
    linhas = [("Suas horas", _h(o["suas_horas"]))]
    if o["pessoas"] > 1:
        linhas.append(("Assistente" if o["pessoas"] == 2 else "Assistentes", _r(o["assistente"])))
    if o["materiais"] > 0:
        linhas.append(("Materiais", _r(o["materiais"])))
    linhas.append(("Deslocamento", _r(o["deslocamento"])))
    if o["outros"] > 0:
        linhas.append(("Outros custos", _r(o["outros"])))
    linhas.append(("Taxa do cartão", _r(o["taxa_cartao"])))
    if o["imposto"] > 0:
        linhas.append(("Imposto", _r(o["imposto"])))
    linhas.append(("Preço mínimo", _r(o["minimo"])))
    lns = "".join(f'<div class="pc-ln"><span>{a}</span><b>{b}</b></div>' for a, b in linhas)
    lns += f'<div class="pc-ln"><span>Fica para você</span><b class="ouro">{_r(o["fica_para_voce"])}</b></div>'
    if vazio:
        sub = ("Toque em um ambiente para ver o preço" if tipo == "organizacao"
               else "Informe as caixas para ver o preço")
    else:
        sub = f'sinal de {_r(o["sinal"])} ({float(p.get("sinal_pct") or 0):g}%)'
    with st.container(key="pc_res"):
        _md(f'<div class="l">Preço sugerido</div><div class="pc-v">{_r(o["total"])}</div>'
            f'<div class="l" style="margin-bottom:14px">{sub}</div><div>{lns}</div>')
        with st.container(key="cta_pc_proposta"):
            criar = st.button("Criar proposta com este valor", key="pc_criar", use_container_width=True,
                              disabled=vazio)
    if tipo == "organizacao":
        primeiro = (str(qtd_amb), "ambiente" if qtd_amb == 1 else "ambientes")
    else:
        primeiro = (str(o["caixas"]), "caixa" if o["caixas"] == 1 else "caixas")
    mini = [primeiro, (str(o["dias"]), "dia de serviço" if o["dias"] == 1 else "dias de serviço"),
            (str(o["pessoas"]), "pessoa por dia" if o["pessoas"] == 1 else "pessoas por dia"),
            (_r(o["hora_no_local"]), "sua hora no local")]
    _md('<div class="pc-mini">' + "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in mini) + "</div>")
    if criar and not vazio:
        st.session_state["nova_proposta_prefill"] = prefill
        st.session_state["kanban_nova_proposta_open"] = True
        st.session_state.current_page = "Propostas"
        st.rerun()


def _aba_projeto(p):
    proj = _projeto()
    with st.container(key="pc_corpo"):
        esq, dir_ = st.columns([2, 1], gap="medium")
    with esq:
        with st.container(key="pc_sec_tipo"):
            _md(_sec(1, "Qual serviço?", "Escolha o tipo. Na mudança, o volume é calculado pelas caixas."))
            with st.container(key="pc_grade_tipo"):
                cols = st.columns(len(pr.TIPOS_SERVICO), gap="small")
            for col, (chave, (titulo, sub)) in zip(cols, pr.TIPOS_SERVICO.items()):
                with col:
                    if _cartao_opcao(f"tipo_{chave}", titulo, sub, on=proj["tipo"] == chave, cls="tipo"):
                        proj["tipo"] = chave
                        st.rerun()
        tipo = proj["tipo"]
        horas_amb, qtd_amb, caixas, mats = 0.0, 0, 0, []
        if tipo == "organizacao":
            horas_amb, qtd_amb = _secao_ambientes(proj, 2)
            compl = _secao_equipe(proj, p, tipo, 3)
        else:
            caixas = _secao_volume(proj, p, tipo, 2)
            mats = _secao_materiais_projeto(proj, p, 3)
            compl = _secao_equipe(proj, p, tipo, 4)

    o = pr.orcamento_completo(p, tipo, horas_ambientes=horas_amb, caixas=caixas, complexidade=compl,
                              assistentes=proj["assistentes"], km=proj["km"], outros=proj["outros"],
                              materiais_escolhidos=mats)
    if tipo == "organizacao":
        nomes = AMBIENTES + proj["extras"]
        ambientes = {a: int(proj["qtd"][a]) for a in nomes if int(proj["qtd"].get(a, 0)) > 0}
    else:
        ambientes = {}
    prefill = {"tipo": tipo, "ambientes": ambientes, "caixas": int(caixas), "assistentes": int(proj["assistentes"]),
               "km": float(proj["km"]), "outros": float(proj["outros"]), "complexidade": float(compl),
               "total": float(o["total"]),
               # extras (fora do contrato combinado): horas usadas por ambiente e os materiais da mudança
               "horas_ambientes": {a: float(proj["horas"].get(a, pr.AMBIENTES_PADRAO.get(a, 0))) for a in ambientes},
               "materiais": [{"nome": n_, "quantidade": q, "preco": v} for n_, q, v in mats]}
    with dir_:
        _painel_projeto(o, p, tipo, qtd_amb, prefill)


def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown(CSS, unsafe_allow_html=True)
    p = _parametros()
    aba = _cabecalho()
    if aba == ABAS[0]:
        _aba_hora(p)
    else:
        _aba_projeto(p)
