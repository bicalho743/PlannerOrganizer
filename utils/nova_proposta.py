"""
Nova proposta em 4 passos (tela Propostas do site), igual aos protótipos nova2 e nova4:

1 Cliente (escolher ou cadastrar rápido) · 2 Serviço (tipo, volume e materiais) · 3 Equipe e valores ·
4 Revisar e enviar (prévia na cor da marca, cor e logotipo, WhatsApp e PDF).

O preço é sempre pr.orcamento_completo (utils/precificacao.py). A proposta é gravada ao entrar no passo 4
(em aberto, marcada como rascunho no histórico) e atualizada se ela voltar e mudar algo; o envio pelo WhatsApp
marca "Enviada". O PDF é o da cliente (utils/propostas_helper.gerar_pdf_cliente_proposta → utils/pdf_proposta).

Entradas de outras telas:
- st.session_state["kanban_nova_proposta_open"] = True abre a Nova proposta;
- st.session_state["nova_proposta_prefill"] = {"tipo", "ambientes", "caixas", "assistentes", "km", "outros",
  "complexidade", "total"} (botão "Criar proposta com este valor" da Precificação) preenche os passos 2 e 3.
"""
import os
import urllib.parse
from datetime import timedelta

import streamlit as st

from utils import precificacao as pr
from utils import propostas_dados as dados
from utils.onboarding_novo import CORES
from utils.visual import esc, hoje

CHAVE = "_np"
PREFILL = "nova_proposta_prefill"
ABERTA = "kanban_nova_proposta_open"
ORDEM_CORES = ["Ameixa", "Azul-marinho", "Verde", "Rosa", "Dourado", "Azul"]   # ordem do protótipo
COR_PADRAO = "#0D1B2A"
AMBIENTES = {k: v for k, v in pr.AMBIENTES_PADRAO.items() if k != "Mudança (por cômodo)"}
PASSOS = [("Cliente", "Quem vai receber"), ("Serviço", "Tipo, volume e materiais"),
          ("Equipe e valores", "Dias, equipe e sinal"), ("Proposta", "Revisar e enviar")]
MODOS = {"total": ("Total de caixas", "Você já sabe o volume"), "comodo": ("Por cômodo", "Caixas de cada ambiente"),
         "area": ("Pela área (m²)", "Estimativa sem vistoria")}


# ---------------------------------------------------------------- estado

def _novo():
    return {"passo": 1, "cliente_id": None, "tipo": "organizacao", "amb": {}, "amb_extra": {}, "amb_horas": {}, "complexidade": "Média",
            "modo": "comodo", "caixas_total": 0, "comodos": {}, "com_extra": {}, "m2": 0.0, "mats": {}, "obs": "",
            "assist": 0, "km": 0.0, "outros": 0.0, "sinal_pct": None, "valor_final": None, "data_inicio": None,
            "mostrar_obs": True, "pid": None, "numero": None, "enviada": False}


def _limpar_widgets():
    for k in [k for k in st.session_state.keys() if str(k).startswith("np_")]:
        st.session_state.pop(k, None)


def iniciar():
    """Começa uma proposta do zero (botão "+ Nova proposta")."""
    _limpar_widgets()
    st.session_state[CHAVE] = _novo()
    st.session_state[ABERTA] = True


def fechar():
    _limpar_widgets()
    st.session_state.pop(CHAVE, None)
    st.session_state[ABERTA] = False


def estado():
    o = st.session_state.get(CHAVE)
    if not isinstance(o, dict):
        o = st.session_state[CHAVE] = _novo()
    return o


def preparar():
    """Chamada pela tela Propostas antes de desenhar: aplica o pré-preenchimento da Precificação (e apaga a
    chave) e decide se a Nova proposta abre. Devolve True se ela deve aparecer."""
    entrou = st.session_state.get("_last_page_rendered") != "Propostas"
    pf = st.session_state.pop(PREFILL, None)
    if isinstance(pf, dict):
        aplicar_prefill(pf)
        st.session_state[ABERTA] = True
    elif st.session_state.get(ABERTA) and entrou:
        # aberta por outra tela (Início, Agenda, botão + do celular): se a anterior já foi salva, começa outra;
        # se ainda não (ela foi à Precificação no meio), continua de onde parou
        o = st.session_state.get(CHAVE)
        if not isinstance(o, dict) or o.get("pid"):
            iniciar()
    if not st.session_state.get(ABERTA):
        return False
    estado()
    cid = st.session_state.pop("nova_proposta_cliente_id", None)
    if cid:   # "Nova proposta para <nome>" (Clientes, Pós-organização): cliente escolhida, já no passo 2
        o = estado()
        if o.get("pid"):
            iniciar()
            o = estado()
        try:
            o["cliente_id"] = int(cid)
            st.session_state.pop("np_cli_sel", None)
            if o["passo"] == 1:
                o["passo"] = 2
        except (TypeError, ValueError):
            pass
    return True


def aplicar_prefill(pf):
    """Preenche os passos 2 e 3 com o cálculo da Precificação, mantendo a cliente já escolhida."""
    velho = st.session_state.get(CHAVE)
    o = _novo()
    if isinstance(velho, dict) and not velho.get("pid"):
        o["cliente_id"] = velho.get("cliente_id")
    tipo = pf.get("tipo") if pf.get("tipo") in pr.TIPOS_SERVICO else "organizacao"
    o["tipo"] = tipo
    amb = {str(k): int(v or 0) for k, v in (pf.get("ambientes") or {}).items() if int(v or 0) > 0}
    caixas = int(pf.get("caixas") or 0)
    o["amb_horas"] = {str(k): float(v) for k, v in (pf.get("horas_ambientes") or {}).items() if v}
    if tipo == "organizacao":
        for nome, q in amb.items():
            if nome in AMBIENTES:
                o["amb"][nome] = q
            else:
                o["amb_extra"][nome] = 3.0
                o["amb"][nome] = q
    else:
        if amb and sum(amb.values()) == caixas:
            o["modo"] = "comodo"
            for nome, q in amb.items():
                (o["comodos"] if nome in pr.CAIXAS_POR_COMODO else o["com_extra"])[nome] = q
        else:
            o["modo"], o["caixas_total"] = "total", caixas
    try:
        cx = float(pf.get("complexidade") or 1.0)
        o["complexidade"] = min(pr.COMPLEXIDADE, key=lambda k: abs(pr.COMPLEXIDADE[k] - cx))
    except (TypeError, ValueError):
        pass
    o["assist"] = max(int(pf.get("assistentes") or 0), 0)
    o["km"] = max(float(pf.get("km") or 0), 0.0)
    o["outros"] = max(float(pf.get("outros") or 0), 0.0)
    o["passo"] = 2 if o["cliente_id"] else 1
    try:
        total = float(pf.get("total") or 0)
        if total > 0 and abs(total - calculo(o, _p())["total"]) > 0.5:
            o["valor_final"] = total          # "Criar proposta com este valor": vale o valor que ela viu
    except Exception as e:
        print(f"[nova_proposta] prefill: {e}")
    _limpar_widgets()
    st.session_state[CHAVE] = o


# ---------------------------------------------------------------- contas

def _p():
    if "_np_param" not in st.session_state:
        st.session_state["_np_param"] = dados.parametros(st.session_state.db)
    return st.session_state["_np_param"]


def horas_ambiente(o, nome):
    return float(o.setdefault("amb_horas", {}).get(nome) or o["amb_extra"].get(nome) or AMBIENTES.get(nome, 3.0))


def caixas(o):
    if o["tipo"] == "organizacao":
        return 0
    if o["modo"] == "total":
        return int(o["caixas_total"] or 0)
    if o["modo"] == "area":
        return pr.caixas_por_area(o["m2"])
    return int(sum(o["comodos"].values()) + sum(o["com_extra"].values()))


def itens(o):
    """[(nome, quantidade)] dos ambientes (organização) ou dos cômodos (mudança por cômodo)."""
    if o["tipo"] == "organizacao":
        return [(n, q) for n, q in o["amb"].items() if q]
    if o["modo"] == "comodo":
        return [(n, q) for n, q in list(o["comodos"].items()) + list(o["com_extra"].items()) if q]
    return []


def materiais_escolhidos(o, p):
    lista = []
    for m in pr.materiais(p):
        q = o["mats"].get(m.get("nome"))
        if q:
            lista.append((m["nome"], q, float(m.get("preco") or 0)))
    return lista


def calculo(o, p):
    horas = sum(horas_ambiente(o, n) * q for n, q in o["amb"].items() if q) if o["tipo"] == "organizacao" else 0.0
    return pr.orcamento_completo(p, o["tipo"], horas_ambientes=horas, caixas=caixas(o),
                                 complexidade=pr.COMPLEXIDADE.get(o["complexidade"], 1.0), assistentes=o["assist"],
                                 km=o["km"], outros=o["outros"], materiais_escolhidos=materiais_escolhidos(o, p))


def valor_final(o, r):
    return float(o["valor_final"]) if o.get("valor_final") else float(r["total"])


def sinal_pct(o, p):
    return float(o["sinal_pct"] if o.get("sinal_pct") is not None else (p.get("sinal_pct") or 0))


def descricao(o, r, p):
    return dados.montar_descricao(o["tipo"], itens(o), caixas(o), r["dias"], o["assist"],
                                  [n for n, _, _ in materiais_escolhidos(o, p)], o["obs"], o["mostrar_obs"])


def brl0(v):
    """R$ 2.480 (sem centavos quando redondo) ou R$ 6,50."""
    v = float(v or 0)
    txt = f"{v:,.0f}" if abs(v - round(v)) < 0.005 else f"{v:,.2f}"
    return "R$ " + txt.replace(",", "X").replace(".", ",").replace("X", ".")


def brl(v):
    return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- banco

def _cliente(cid):
    try:
        df = st.session_state.db.get_clientes()
        linha = df[df["id"] == int(cid)]
        return linha.iloc[0].to_dict() if not linha.empty else {}
    except Exception:
        return {}


def _perfil():
    try:
        return st.session_state.db.get_perfil_usuario() or {}
    except Exception:
        return {}


def limpar_pdfs(pid):
    """Esquece os PDFs já gerados desta proposta (o próximo clique gera de novo, com os dados atuais)."""
    for k in [k for k in st.session_state.keys() if str(k).startswith("_pdf_") and str(k).endswith(f"_{pid}")
              or str(k).startswith("_pdf_") and f"_{pid}_" in str(k)]:
        st.session_state.pop(k, None)


def limpar_todos_pdfs():
    """A marca mudou (cor ou logotipo): todo PDF guardado na sessão fica velho."""
    for k in [k for k in st.session_state.keys() if str(k).startswith("_pdf_")]:
        st.session_state.pop(k, None)


def salvar(o, p):
    """Grava (ou atualiza) a proposta em aberto. Devolve o id."""
    from utils.proposta_status import STATUS_EM_ABERTO
    db = st.session_state.db
    r = calculo(o, p)
    valor = valor_final(o, r)
    dias = max(int(r["dias"] or 0), 1)
    sinal = round(valor * sinal_pct(o, p) / 100, 2)
    campos = dict(descricao=descricao(o, r, p), valor=valor, tipo_proposta=pr.TIPOS_SERVICO[o["tipo"]][0],
                  previsao_dias=dias)
    ini = o.get("data_inicio")
    if o.get("pid"):
        extra = {"data_inicio": ini, "data_fim": ini + timedelta(days=dias - 1)} if ini else {}
        db.update_proposta(o["pid"], sinal=sinal, **campos, **extra)
    else:
        pid = db.add_proposta(cliente_id=int(o["cliente_id"]), status=STATUS_EM_ABERTO,
                              data_inicio=ini, data_fim=(ini + timedelta(days=dias - 1)) if ini else None,
                              gerar_transacoes_automaticas=False, **campos)
        if not pid:
            raise RuntimeError("Não foi possível salvar a proposta.")
        o["pid"] = int(pid)
        # add_proposta usa a data de início como data da proposta; a proposta é de hoje
        db.update_proposta(o["pid"], data_proposta=hoje(), **({"sinal": sinal} if sinal > 0 else {}))
        dados.marcar(db, o["pid"], "Rascunho", "Proposta criada")
        try:   # ativação: a 1ª proposta da conta vira evento no Analytics e no Pixel
            if len(db.get_propostas()) <= 1:
                from utils.rastreamento import evento
                evento("primeira_proposta", "PrimeiraProposta", meta_custom=True,
                       uma_vez=f"po_1a_proposta_{st.session_state.get('usuario_id', '')}")
        except Exception as _e:
            print(f"[rastreamento] {_e}")
    if (o.get("obs") or "").strip():
        dados.marcar(db, o["pid"], dados.VISITA, o["obs"].strip(), substituir=True)
    else:
        dados.apagar_marca(db, o["pid"], dados.VISITA)
    try:
        db.invalidar_cache()
        prop = db.get_propostas()
        o["numero"] = int(prop[prop["id"] == o["pid"]].iloc[0]["numero"])
    except Exception:
        o["numero"] = o.get("numero") or o["pid"]
    limpar_pdfs(o["pid"])
    return o["pid"]


def mensagem_whatsapp(cliente_nome, tipo, valor):
    primeiro = str(cliente_nome or "").split(" ")[0] or "tudo bem"
    return (f"Oi, {primeiro}! Tudo bem? Segue a proposta do serviço de {str(tipo or 'organização').lower()}, "
            f"no valor de {brl(valor)}. Vou te mandar o PDF aqui na conversa. Qualquer dúvida, é só me chamar!")


def link_whatsapp(telefone, msg):
    from utils.whatsapp_helper import whatsapp_link
    return whatsapp_link(telefone, msg) or f"https://wa.me/?text={urllib.parse.quote(msg)}"


# ---------------------------------------------------------------- aparência

CSS = """
<style>
.np-ey { font-size:.74rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#9C7A22; margin:0 0 4px; }
h1.np-tit { margin:0 !important; padding:0 !important; font-family:'Cormorant Garamond',Georgia,serif !important;
            font-size:2.6rem !important; font-weight:600 !important; color:var(--navy) !important; line-height:1.15 !important; }
h1.np-tit::after { content:""; display:block; width:40px; height:3px; border-radius:2px; background:var(--gold); margin-top:8px; }
.np-sub { color:#5B6B80; font-size:.98rem; margin:10px 0 4px; }
.np-cl { display:inline-flex; align-items:center; gap:10px; background:#fff; border:1px solid #E7E2D6; border-radius:999px;
         padding:6px 14px 6px 6px; font-size:.9rem; margin-top:10px; color:#1A202C; max-width:100%; }
.np-cl i { font-style:normal; flex:none; width:28px; height:28px; border-radius:50%; background:#F6EDD3; color:#9C7A22;
           display:grid; place-items:center; font-weight:700; font-size:.72rem; }
.np-steps { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); margin:22px 0 6px; background:#fff;
            border:1px solid #E7E2D6; border-radius:16px; overflow:hidden; }
.np-st { padding:14px 18px; display:flex; gap:12px; align-items:center; border-right:1px solid #E7E2D6; min-width:0; }
.np-st:last-child { border-right:0; }
.np-st i { font-style:normal; flex:none; width:28px; height:28px; border-radius:50%; border:1.5px solid #E7E2D6; display:grid;
           place-items:center; font-weight:700; font-size:.8rem; color:#5B6B80; }
.np-st i svg { display:block; }
.np-st b { display:block; font-size:.9rem; color:var(--navy); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.np-st span { display:block; font-size:.76rem; color:#5B6B80; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.np-st div { min-width:0; }
.np-st.ok i { background:#E3F1E8; border-color:#2F6B4F; color:#2F6B4F; }
.np-st.on { background:#F6EDD3; box-shadow:inset 0 -3px 0 #C9A84C; }
.np-st.on i { background:#C9A84C; border-color:#C9A84C; color:var(--navy); }
[class*="st-key-npsec_"] { background:#fff; border:1px solid #E7E2D6 !important; border-radius:16px !important;
                           padding:18px 20px 16px !important; }
.np-h3 { font-size:1.06rem; font-weight:700; color:var(--navy); display:flex; align-items:center; gap:8px; margin:2px 0 0; }
.np-h3 .n { display:inline-grid; place-items:center; flex:none; width:24px; height:24px; border-radius:50%; background:#F6EDD3;
            color:#9C7A22; font-size:.8rem; font-weight:700; }
.np-d { font-size:.88rem; color:#5B6B80; margin:2px 0 10px; }
.np-o { border:1.5px solid #E7E2D6; border-radius:14px; background:#fff; padding:13px 16px; min-height:68px; }
.np-o b { display:block; color:var(--navy); font-size:.95rem; }
.np-o span { font-size:.8rem; color:#5B6B80; }
.np-o.on { border-color:#C9A84C; background:#F6EDD3; }
[class*="st-key-kcard_npop_"]:hover .np-o { border-color:#C9A84C; }
[class*="st-key-npamb_"], [class*="st-key-npcom_"] { border:1.5px solid #E7E2D6 !important; border-radius:12px !important;
       padding:4px 6px 6px !important; background:#fff; gap:4px !important; }
.np-amb { display:flex; justify-content:space-between; align-items:center; gap:6px; min-height:24px; padding:2px 0 12px; }
.np-amb b { color:var(--navy); font-size:.9rem; line-height:1.2; }
.np-amb .h { flex:none; font-size:.72rem; font-weight:700; color:#5B6B80; background:#F2EFE7; border-radius:999px; padding:2px 8px; }
.np-amb .h.on { background:#F6EDD3; color:#9C7A22; }
[class*="st-key-npamb_"] [data-testid="stNumberInput"] input, [class*="st-key-npcom_"] [data-testid="stNumberInput"] input { font-weight:700; text-align:center; }
[class*="st-key-npmat_"] { border:1px solid #E7E2D6 !important; border-radius:10px !important; padding:2px 6px 4px !important;
                           background:#fff; gap:2px !important; }
[class*="st-key-npmat_"] [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:nowrap !important; }
[class*="st-key-npmat_"] [data-testid="stColumn"] { min-width:0 !important; width:auto !important; }
.np-mq { font-size:.78rem; color:#5B6B80; margin:0 0 4px 28px; }
.np-mq b { color:var(--navy); }
.np-mp { text-align:right; font-weight:700; color:var(--navy); font-size:.86rem; padding-top:0; white-space:nowrap; }
.np-res { background:var(--navy); color:#fff; border-radius:18px; padding:22px 22px 14px; }
.np-res .l { font-size:.8rem; color:rgba(255,255,255,.7); }
.np-res .v { font-family:'Cormorant Garamond',Georgia,serif; font-size:2.9rem; color:#C9A84C; font-weight:600; line-height:1.1;
             font-variant-numeric:tabular-nums; }
.np-res .ln { display:flex; justify-content:space-between; gap:10px; font-size:.88rem; padding:8px 0;
              border-top:1px solid rgba(255,255,255,.12); }
.np-res .ln b { white-space:nowrap; font-variant-numeric:tabular-nums; }
.np-res .ln.aj b { color:#E8D5A3; }
.np-mini { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:14px; }
.np-mini div { background:#fff; border:1px solid #E7E2D6; border-radius:12px; padding:12px; }
.np-mini b { font-size:1.35rem; color:var(--navy); display:block; font-variant-numeric:tabular-nums; }
.np-mini span { font-size:.75rem; color:#5B6B80; }
.np-resm { display:none; }
.np-dica { font-size:.82rem; color:#5B6B80; margin-top:-4px; }
.np-dica b { color:var(--navy); }
[class*="st-key-np_links"] button, [class*="st-key-np_links"] button p { color:#9C7A22 !important; font-weight:700 !important; }
.st-key-np_links_x .stButton { display:flex; justify-content:flex-end; }
.st-key-np_links_x button p { white-space:nowrap; }
[class*="st-key-np_links"] button:hover p { color:var(--navy) !important; }
.st-key-np_nav [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:nowrap !important; }
.st-key-np_nav [data-testid="stColumn"] { min-width:0 !important; width:auto !important; }
.st-key-np_nav .stButton > button { min-height:46px; padding:0 20px; font-weight:700; }
.st-key-np_nav [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] { align-items:flex-end; }
/* prévia da proposta */
.np-pdf { background:#fff; border:1px solid #E7E2D6; border-radius:14px; overflow:hidden; box-shadow:0 10px 30px rgba(13,27,42,.08); }
.np-pdf .cab { background:var(--c); color:var(--s); padding:22px 26px; display:flex; justify-content:space-between; align-items:center; gap:12px; }
.np-pdf .cab .em { display:flex; align-items:center; gap:12px; min-width:0; }
.np-pdf .cab img { width:44px; height:44px; object-fit:contain; background:#fff; border-radius:8px; padding:3px; flex:none; }
.np-pdf .cab b { font-size:1.3rem; font-family:'Cormorant Garamond',Georgia,serif; font-weight:600; display:block; line-height:1.2; }
.np-pdf .cab span { font-size:.8rem; opacity:.85; }
.np-pdf .cp { padding:20px 26px 22px; font-size:.9rem; color:#1F2A37; }
.np-pdf h4 { color:var(--t); font-size:.76rem; letter-spacing:.12em; margin:18px 0 6px; font-weight:700; text-transform:uppercase; }
.np-pdf table { width:100%; border-collapse:collapse; border:none !important; margin:0 !important; }
.np-pdf tr { border:none !important; background:transparent !important; }
.np-pdf td { padding:8px 0 !important; border:none !important; border-bottom:1px solid #EEE !important; vertical-align:top; background:transparent !important; }
.np-pdf td:last-child { text-align:right; white-space:nowrap; padding-left:12px; }
.np-pdf .obs { color:#555; font-size:.86rem; white-space:pre-wrap; overflow-wrap:anywhere; }
.np-pdf .tot { display:flex; justify-content:space-between; gap:10px; background:var(--cl); border-radius:10px; padding:12px 14px;
               margin-top:14px; font-weight:700; color:var(--t); font-size:1.02rem; }
.np-pdf .sin { font-size:.8rem; color:#666; margin-top:6px; }
[class*="st-key-npsec_marca"] { padding:10px 12px 8px !important; }
.np-sw { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-top:1px solid #E7E2D6; font-size:.9rem; }
.np-logo { display:flex; align-items:center; gap:10px; padding:10px 0 4px; border-top:1px solid #E7E2D6; font-size:.9rem; }
.np-logo img { width:40px; height:40px; object-fit:contain; border:1px solid #E7E2D6; border-radius:8px; background:#fff; }
.np-pe { font-size:.8rem; color:#5B6B80; text-align:center; margin-top:10px; }
.np-pe b { color:#5B6B80; }
.np-ok { background:#E3F1E8; color:#2F6B4F; border-radius:12px; padding:12px 14px; font-size:.88rem; margin-top:10px; }
.st-key-np_cor [role="radiogroup"] { gap:10px !important; flex-wrap:wrap; margin:4px 0 6px; }
.st-key-np_cor [role="radiogroup"] label > div > div:first-child { width:30px !important; height:30px !important;
     border:none !important; border-radius:50% !important; margin:0 !important; cursor:pointer;
     box-shadow:0 0 0 3px #FFFFFF, 0 0 0 4px #E7E2D6; }
.st-key-np_cor [role="radiogroup"] label > div > div:first-child > div { display:none !important; }
.st-key-np_cor [role="radiogroup"] > div[data-selected="true"] label > div > div:first-child,
.st-key-np_cor [role="radiogroup"] label:has(input:checked) > div > div:first-child { box-shadow:0 0 0 3px #FFFFFF, 0 0 0 5px #C9A84C !important; }
.st-key-np_cor [data-testid="stMarkdownContainer"] { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }
.st-key-np_zap .stLinkButton a, .st-key-np_zap a { background:#C9A84C !important; border-color:#C9A84C !important; min-height:52px;
     border-radius:10px !important; width:100%; }
.st-key-np_zap a p, .st-key-np_zap a span { color:var(--navy) !important; font-weight:700 !important; font-size:1rem !important; }
.st-key-np_zap a:hover { background:#B8943D !important; }
[class*="st-key-wa_"] a > div { flex:0 0 auto !important; width:auto !important; }
[class*="st-key-btndoc_np_pdf_"] .stButton > button, .st-key-np_pdfwrap [data-testid="stDownloadButton"] button {
     background:#fff !important; border:1px solid #E7E2D6 !important; min-height:48px; }
[class*="st-key-btndoc_np_pdf_"] .stButton > button *, .st-key-np_pdfwrap [data-testid="stDownloadButton"] button * {
     color:var(--navy) !important; font-weight:700 !important; }
@media (max-width: 1300px) {
  .st-key-np_grid > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:wrap !important; }
  .st-key-np_grid > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:1 1 100% !important; width:100% !important; }
  .np-resm { display:flex; justify-content:space-between; align-items:center; background:var(--navy); color:#fff; border-radius:14px;
             padding:12px 16px; margin:4px 0 2px; font-size:.86rem; }
  .np-resm b { font-family:'Cormorant Garamond',Georgia,serif; color:#C9A84C; font-size:1.6rem; font-weight:600; }
}
[class*="st-key-npg_"] { container-type:inline-size; }
@container (max-width: 560px) {
  [class*="st-key-npg_"] [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:wrap !important; row-gap:10px; }
  [class*="st-key-npg_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:1 1 45% !important; width:45% !important; min-width:0 !important; }
}
@container (max-width: 340px) {
  [class*="st-key-npg_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:1 1 100% !important; width:100% !important; }
}
@media (max-width: 760px) {
  .np-steps { grid-template-columns:repeat(4,minmax(0,1fr)); }
  .np-st { padding:10px 6px; flex-direction:column; gap:4px; text-align:center; }
  .np-st span { display:none; }
  .np-st b { font-size:.72rem; white-space:normal; }
  h1.np-tit { font-size:2.05rem !important; }
  .np-pdf .cab, .np-pdf .cp { padding-left:16px; padding-right:16px; }
}
</style>
"""

_CHECK = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" '
          'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>')


def _iniciais(nome):
    p = [x for x in str(nome or "").split() if x[:1].isalpha()]
    return ((p[0][0] + (p[-1][0] if len(p) > 1 else "")) if p else "?").upper()


def _resumos(o, r, p, cli):
    """Linha de baixo de cada passo já feito."""
    tipo = pr.TIPOS_SERVICO[o["tipo"]][0]
    if o["tipo"] == "organizacao":
        n = sum(q for _, q in itens(o))
        serv = f"{tipo} · {n} ambiente{'s' if n != 1 else ''}"
    else:
        serv = f"{tipo} · {caixas(o)} caixas"
    pessoas = r["pessoas"]
    equipe = f"{max(r['dias'], 1)} dia{'s' if r['dias'] > 1 else ''} · {pessoas} pessoa{'s' if pessoas > 1 else ''}"
    return [cli.get("nome") or PASSOS[0][1], serv, equipe, PASSOS[3][1]]


def _cabecalho(o, titulo, sub, cli):
    st.markdown(f'<div class="np-ey">Nova proposta</div><h1 class="np-tit">{titulo}</h1><div class="np-sub">{sub}</div>',
                unsafe_allow_html=True)
    if cli and o["passo"] in (2, 3):
        lugar = ", ".join(x for x in [str(cli.get("bairro") or "").strip(), str(cli.get("cidade") or "").strip()] if x)
        st.markdown(f'<div class="np-cl"><i>{esc(_iniciais(cli.get("nome")))}</i>{esc(cli.get("nome"))}'
                    f'{" · " + esc(lugar) if lugar else ""}</div>', unsafe_allow_html=True)


def _barra(o, r, p, cli):
    res = _resumos(o, r, p, cli)
    html = '<div class="np-steps">'
    for i, (rot, sub) in enumerate(PASSOS, 1):
        cls = "ok" if i < o["passo"] else ("on" if i == o["passo"] else "")
        marca = _CHECK if i < o["passo"] else str(i)
        txt = res[i - 1] if i < o["passo"] else sub
        html += f'<div class="np-st {cls}"><i>{marca}</i><div><b>{rot}</b><span>{esc(txt)}</span></div></div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def _secao(n, titulo, desc, chave):
    box = st.container(border=True, key=f"npsec_{chave}")
    box.markdown(f'<div class="np-h3"><span class="n">{n}</span>{titulo}</div>'
                 + (f'<div class="np-d">{desc}</div>' if desc else ""), unsafe_allow_html=True)
    return box


def _opcoes(opcoes, atual, chave):
    """Cartões de escolha (um clique escolhe). opcoes: {valor: (título, detalhe)}. Devolve o valor clicado."""
    from utils.ui import cartao_clicavel
    escolhido = None
    cols = st.columns(len(opcoes))
    for col, (k, (tit, det)) in zip(cols, opcoes.items()):
        with col:
            html = f'<div class="np-o{" on" if k == atual else ""}"><b>{tit}</b><span>{det}</span></div>'
            if cartao_clicavel(html, key=f"npop_{chave}_{k}", rotulo=tit):
                escolhido = k
    return escolhido


def _painel(o, r, p):
    final = valor_final(o, r)
    dias = max(r["dias"], 1) if r["horas"] > 0 else 0
    n_ass = r["pessoas"] - 1
    linhas = [(f"Você ({dias} dia{'s' if dias != 1 else ''})", r["voce"])] if r["voce"] else []
    if n_ass:
        linhas.append((f"Assistente{'s' if n_ass > 1 else ''} ({dias} dia{'s' if dias != 1 else ''})", r["assistente"]))
    if r["materiais"]:
        linhas.append(("Materiais", r["materiais"]))
    if r["deslocamento"]:
        linhas.append((f"Deslocamento ({o['km']:g} km)", r["deslocamento"]))
    if r["outros"]:
        linhas.append(("Outros custos", r["outros"]))
    if r["taxa_cartao"]:
        linhas.append(("Taxa do cartão", r["taxa_cartao"]))
    if r["imposto"]:
        linhas.append(("Imposto", r["imposto"]))
    linhas = [(t, round(v)) for t, v in linhas]
    margem = r["total"] - sum(v for _, v in linhas) if r["total"] else 0
    if r["total"]:
        linhas.append(("Margem de segurança e lucro", margem))
    html = (f'<div class="np-res"><div class="l">Investimento estimado</div><div class="v">{brl0(final)}</div>'
            f'<div class="l" style="margin-bottom:14px">calculado com os seus números</div>')
    html += "".join(f'<div class="ln"><span>{esc(t)}</span><b>{brl0(v)}</b></div>' for t, v in linhas)
    if o.get("valor_final") and abs(final - r["total"]) >= 0.5:
        dif = final - r["total"]
        html += (f'<div class="ln aj"><span>Seu ajuste no valor final</span><b>{"+ " if dif > 0 else "− "}'
                 f'{brl0(abs(dif))}</b></div>')
    if not r["total"]:
        html += '<div class="ln"><span>Escolha o que entra no serviço para ver o valor.</span></div>'
    html += "</div>"
    if o["tipo"] == "organizacao":
        n_amb = sum(q for _, q in itens(o))
        mini = [(f"{round(r['horas'], 1):g}".replace(".", ","), "horas de trabalho"), (dias, "dias de serviço"), (r["pessoas"], "pessoas por dia"),
                (n_amb, "ambientes")]
    else:
        n_com = len(itens(o))
        mini = [(caixas(o), "caixas"), (dias, "dias de serviço"), (r["pessoas"], "pessoas por dia"),
                (n_com if o["modo"] == "comodo" else "–", "cômodos")]
    html += '<div class="np-mini">' + "".join(f"<div><b>{v}</b><span>{t}</span></div>" for v, t in mini) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _resumo_celular(o, r):
    st.markdown(f'<div class="np-resm"><span>Investimento estimado</span><b>{brl0(valor_final(o, r))}</b></div>',
                unsafe_allow_html=True)


def _nav(voltar, avancar, rotulo, chave, desabilitado=False):
    with st.container(key="np_nav"):
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Voltar", key=f"np_v_{chave}", icon=":material/arrow_back:"):
                voltar()
        with c2:
            if st.button(rotulo, key=f"np_a_{chave}", type="primary", icon=":material/arrow_forward:",
                         icon_position="right", disabled=desabilitado):
                avancar()


def _ir(o, passo):
    o["passo"] = passo
    st.rerun()


# ---------------------------------------------------------------- passo 1: cliente

def _passo_cliente(o, p):
    db = st.session_state.db
    try:
        clientes = db.get_clientes()
    except Exception:
        clientes = None
    sec = _secao(1, "Quem é a cliente?", "Escolha da sua lista ou cadastre rapidinho. Ela aparece na proposta.", "cli")
    with sec:
        ids, nomes = [], {}
        if clientes is not None and not clientes.empty:
            cl = clientes.sort_values("nome")
            ids = [int(x) for x in cl["id"].tolist()]
            nomes = dict(zip(ids, cl["nome"].astype(str).tolist()))
        atual = o.get("cliente_id") if o.get("cliente_id") in nomes else None
        escolha = st.selectbox("Cliente", ids, index=ids.index(atual) if atual else None,
                               format_func=lambda x: nomes.get(x, ""), placeholder="Digite o nome da cliente",
                               key="np_cli_sel")
        if escolha != o.get("cliente_id") and escolha is not None:
            o["cliente_id"] = int(escolha)
    sec2 = _secao(2, "Cliente nova?", "Só o nome já basta. O WhatsApp serve para enviar a proposta.", "clinova")
    with sec2:
        with st.form("np_cli_form", border=False, clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome", placeholder="Ex.: Juliana Ferraz")
            tel = c2.text_input("WhatsApp", placeholder="(11) 98765-4321")
            c3, c4 = st.columns(2)
            bairro = c3.text_input("Bairro (opcional)")
            cidade = c4.text_input("Cidade (opcional)")
            ok = st.form_submit_button("Cadastrar e continuar", type="primary", icon=":material/person_add:")
        if ok:
            if not nome.strip():
                st.error("Escreva o nome da cliente.")
            else:
                try:
                    cid = db.add_cliente(nome=nome.strip(), telefone=tel.strip() or None, bairro=bairro.strip() or None,
                                         cidade=cidade.strip() or None)
                    db.invalidar_cache()
                    o["cliente_id"] = int(cid)
                    st.session_state.pop("np_cli_sel", None)
                    _ir(o, 2)
                except Exception as e:
                    st.error(f"Não foi possível cadastrar: {e}")
    _nav(fechar_e_voltar, lambda: _ir(o, 2), "Serviço", "cli", desabilitado=not o.get("cliente_id"))
    with st.expander("Cadastrar um serviço antigo (retroativo)"):
        st.caption("Para registrar um trabalho que já aconteceu, com a situação, as datas e o financeiro.")
        try:
            from pages.propostas_unificado import _render_nova_proposta_form
            if clientes is not None and not clientes.empty:
                _render_nova_proposta_form(clientes)
            else:
                st.info("Cadastre uma cliente primeiro.")
        except Exception as e:
            st.error(str(e))


def fechar_e_voltar():
    fechar()
    st.rerun()


# ---------------------------------------------------------------- passo 2: serviço

def _cb_caixas_comodo(chave, nome):
    """No primeiro + de um cômodo, já sugere as caixas de partida dele."""
    ant = st.session_state.get(f"{chave}__ant", 0) or 0
    novo = st.session_state.get(chave) or 0
    if ant == 0 and novo == 1 and pr.CAIXAS_POR_COMODO.get(nome, 0) > 1:
        st.session_state[chave] = pr.CAIXAS_POR_COMODO[nome]


def _grade(nomes, render, chave, por_linha=3):
    with st.container(key=f"npg_{chave}"):
        for i in range(0, len(nomes), por_linha):
            cols = st.columns(por_linha)
            for col, nome in zip(cols, nomes[i:i + por_linha]):
                with col:
                    render(nome)


def _passo_servico(o, p, r):
    css_on = []
    sec = _secao(1, "Qual serviço?", "Na mudança, o volume é calculado pelas caixas.", "tipo")
    with sec:
        novo = _opcoes(pr.TIPOS_SERVICO, o["tipo"], "tipo")
        if novo and novo != o["tipo"]:
            o["tipo"] = novo
            st.rerun()
        with st.container(key="np_links_prec"):
            if st.button("Usar o cálculo da Precificação", key="np_ir_prec", type="tertiary", icon=":material/refresh:"):
                st.session_state.current_page = "Precificacao"
                st.rerun()

    if o["tipo"] == "organizacao":
        sec = _secao(2, "Quais ambientes?", "Escolha a quantidade de cada um. As horas vêm da sua experiência "
                     "(ajuste em Precificação).", "amb")
        with sec:
            nomes = list(AMBIENTES) + list(o["amb_extra"])
            for i_, a_ in enumerate(nomes):   # horas mudadas no cartão valem já para o chip
                if f"np_hamb_{i_}" in st.session_state and o["amb"].get(a_):
                    o.setdefault("amb_horas", {})[a_] = float(st.session_state[f"np_hamb_{i_}"])

            def amb(nome):
                i = nomes.index(nome)
                q = int(o["amb"].get(nome, 0))
                with st.container(border=True, key=f"npamb_{i}"):
                    st.markdown(f'<div class="np-amb"><b>{esc(nome)}</b><span class="h{" on" if q else ""}">'
                                f'{horas_ambiente(o, nome):g} h</span></div>', unsafe_allow_html=True)
                    v = st.number_input(f"Quantidade de {nome}", 0, 20, q, 1, key=f"np_amb_{i}",
                                        label_visibility="collapsed")
                    if v:   # tempo neste ambiente: ela muda ali mesmo
                        o["amb_horas"][nome] = float(st.number_input(
                            "Horas neste ambiente", 0.5, 80.0, horas_ambiente(o, nome), 0.5, format="%g",
                            key=f"np_hamb_{i}", help="Tempo que você gasta neste ambiente, nesta proposta."))
                if v:
                    css_on.append(f".st-key-npamb_{i}")
                o["amb"][nome] = int(v or 0)
            _grade(nomes, amb, "amb")
            with st.popover("Outro ambiente", icon=":material/add:"):
                nome = st.text_input("Nome do ambiente", placeholder="Garagem, área gourmet...", key="np_amb_novo")
                horas = st.number_input("Horas de trabalho", 0.5, 40.0, 3.0, 0.5, key="np_amb_novo_h")
                if st.button("Incluir", key="np_amb_novo_ok", type="primary") and nome.strip():
                    o["amb_extra"][nome.strip()] = float(horas)
                    o["amb"][nome.strip()] = 1
                    st.rerun()
            st.markdown('<div class="np-d" style="margin:12px 0 4px">Complexidade</div>', unsafe_allow_html=True)
            cx = st.segmented_control("Complexidade", list(pr.COMPLEXIDADE), default=o["complexidade"],
                                      key="np_cx", label_visibility="collapsed")
            if cx:
                o["complexidade"] = cx
    else:
        sec = _secao(2, "Como estimar o volume?", "Escolha um jeito. As caixas definem os dias e a equipe.", "vol")
        with sec:
            novo = _opcoes(MODOS, o["modo"], "modo")
            if novo and novo != o["modo"]:
                o["modo"] = novo
                st.rerun()
            if o["modo"] == "total":
                o["caixas_total"] = int(st.number_input("Total de caixas", 0, 2000, int(o["caixas_total"]), 5,
                                                        key="np_cx_total") or 0)
            elif o["modo"] == "area":
                c1, c2 = st.columns([1, 1])
                o["m2"] = float(c1.number_input("Área do imóvel (m²)", 0.0, 5000.0, float(o["m2"]), 10.0,
                                                key="np_m2") or 0)
                c2.markdown(f'<div class="np-mp" style="text-align:left;padding-top:34px">≈ {caixas(o)} caixas</div>',
                            unsafe_allow_html=True)
                st.markdown('<div class="np-dica">Cerca de uma caixa a cada 3 m². Confira na visita.</div>',
                            unsafe_allow_html=True)
            else:
                nomes = list(pr.CAIXAS_POR_COMODO) + list(o["com_extra"])

                def com(nome):
                    i = nomes.index(nome)
                    extra = nome in o["com_extra"]
                    q = int((o["com_extra"] if extra else o["comodos"]).get(nome, 0))
                    chave = f"np_com_{i}"
                    with st.container(border=True, key=f"npcom_{i}"):
                        st.markdown(f'<div class="np-amb"><b>{esc(nome)}</b></div>', unsafe_allow_html=True)
                        v = st.number_input(f"Caixas de {nome}", 0, 300, q, 1, key=chave, label_visibility="collapsed",
                                            on_change=_cb_caixas_comodo, args=(chave, nome))
                    st.session_state[f"{chave}__ant"] = int(v or 0)
                    if v:
                        css_on.append(f".st-key-npcom_{i}")
                    (o["com_extra"] if extra else o["comodos"])[nome] = int(v or 0)
                _grade(nomes, com, "com")
                st.markdown('<div class="np-dica">No primeiro <b>+</b> o cômodo já vem com as caixas de costume.</div>',
                            unsafe_allow_html=True)
                with st.popover("Outro cômodo", icon=":material/add:"):
                    nome = st.text_input("Nome do cômodo", placeholder="Varanda, depósito...", key="np_com_novo")
                    qtd = st.number_input("Caixas", 1, 300, 5, 1, key="np_com_novo_q")
                    if st.button("Incluir", key="np_com_novo_ok", type="primary") and nome.strip():
                        o["com_extra"][nome.strip()] = int(qtd)
                        st.rerun()

    sec = _secao(3, "Materiais que você leva", "Marque o que entra no orçamento. Os preços vêm da sua lista em "
                 "Precificação.", "mat")
    with sec:
        mats = pr.materiais(p)
        with st.container(key="npg_mat"):
            for i in range(0, len(mats), 2):
                cols = st.columns(2)
                for col, m in zip(cols, mats[i:i + 2]):
                    j = mats.index(m)
                    nome, preco = m.get("nome", ""), float(m.get("preco") or 0)
                    unid = m.get("unidade") or "un"
                    with col, st.container(border=True, key=f"npmat_{j}"):
                        q = o["mats"].get(nome, 0)
                        a, b = st.columns([1.7, 1], vertical_alignment="center")
                        marcado = a.checkbox(nome, value=bool(q), key=f"np_mat_{j}")
                        if marcado and not q:
                            q = max(caixas(o), 1) if "caixa" in nome.lower() else 1
                        if not marcado:
                            q = 0
                        if marcado:
                            q = int(b.number_input(f"Quantidade de {nome} ({unid})", 1, 999, int(q), 1, key=f"np_matq_{j}",
                                                   label_visibility="collapsed") or 1)
                            a.markdown(f'<div class="np-mq">{q} × {brl0(preco)} = <b>{brl0(q * preco)}</b></div>'
                                       if preco > 0 else '<div class="np-mq">preço a definir</div>', unsafe_allow_html=True)
                            css_on.append(f".st-key-npmat_{j}")
                        else:
                            b.markdown(f'<div class="np-mp">{"a definir" if preco <= 0 else brl0(preco)}</div>',
                                       unsafe_allow_html=True)
                        o["mats"][nome] = q

    sec = _secao(4, "Observações da visita", "Aparecem na proposta (você escolhe no último passo).", "obs")
    with sec:
        o["obs"] = st.text_area("Observações da visita", value=o["obs"], key="np_obs", label_visibility="collapsed",
                                placeholder="Acesso pelo elevador de serviço, louças e cristais frágeis, mudança dia 12/12",
                                height=90)
    if css_on:
        mat = [c for c in css_on if "npmat" in c]
        st.markdown("<style>" + ", ".join(css_on) + " { border-color:#C9A84C !important; }"
                    + (", ".join(mat) + " { background:#FFFCF3 !important; }" if mat else "") + "</style>",
                    unsafe_allow_html=True)


# ---------------------------------------------------------------- passo 3: equipe e valores

def _passo_equipe(o, p, r):
    sec = _secao(1, "Quem vai com você?", "O trabalho se divide entre a equipe: com assistentes, você fica menos dias "
                 "no local.", "eq")
    with sec:
        c1, c2 = st.columns(2)
        o["assist"] = int(c1.number_input("Assistentes", 0, 10, int(o["assist"]), 1, key="np_assist") or 0)
        c2.markdown(f'<div class="np-dica" style="margin-top:34px">Cada assistente: <b>{brl0(p.get("valor_hora_assistente"))}'
                    f'</b> por hora, da sua Precificação.</div>', unsafe_allow_html=True)
        d = st.date_input("Dia previsto para começar (opcional)", value=o.get("data_inicio"), format="DD/MM/YYYY",
                          key="np_data")
        o["data_inicio"] = d or None
        st.markdown('<div class="np-dica">Com a data, o serviço entra na Agenda quando ela aprovar.</div>',
                    unsafe_allow_html=True)
    sec = _secao(2, "Deslocamento e outros custos", "Entram no preço; a cliente vê só o total.", "custos")
    with sec:
        from utils.ui import input_moeda
        c1, c2 = st.columns(2)
        o["km"] = float(c1.number_input("Deslocamento (km ida e volta, por dia)", 0.0, 2000.0, float(o["km"]), 1.0,
                                        key="np_km", format="%.0f") or 0)
        c1.markdown(f'<div class="np-dica">{brl(p.get("km_valor")).replace(",00", "")} por km, da sua Precificação.</div>',
                    unsafe_allow_html=True)
        with c2:
            o["outros"] = input_moeda("Outros custos (R$)", "np_outros", value=o["outros"], step=10.0,
                                      help="Estacionamento, etiquetas, materiais de consumo.")
    r = calculo(o, p)
    sec = _secao(3, "Sinal e valor final", "O valor calculado já cobre seus custos, a taxa do cartão e a sua margem.",
                 "valor")
    with sec:
        from utils.ui import input_moeda
        c1, c2 = st.columns(2)
        o["sinal_pct"] = float(c1.number_input("Sinal na aprovação (%)", 0.0, 100.0, sinal_pct(o, p), 5.0,
                                               key="np_sinal", format="%.0f") or 0)
        with c2:
            v = input_moeda("Valor final da proposta (R$)", f"np_vf_{int(round(r['total']))}",
                            value=valor_final(o, r), step=10.0)
        if v and abs(v - r["total"]) >= 0.5:
            o["valor_final"] = v
        elif v:
            o["valor_final"] = None
        final = valor_final(o, r)
        st.markdown(f'<div class="np-dica">Calculado com os seus números: <b>{brl0(r["total"])}</b> · mínimo para '
                    f'não ter prejuízo: <b>{brl0(r["minimo"])}</b> · sinal de <b>{brl(final * o["sinal_pct"] / 100)}'
                    f'</b></div>', unsafe_allow_html=True)
        if final and final < r["minimo"] - 0.5:
            st.warning("Esse valor fica abaixo do seu mínimo: você pagaria para trabalhar.")
        if o.get("valor_final"):
            with st.container(key="np_links_calc"):
                if st.button("Voltar ao valor calculado", key="np_vf_reset", type="tertiary", icon=":material/undo:"):
                    o["valor_final"] = None
                    st.rerun()
    return r


# ---------------------------------------------------------------- passo 4: revisar e enviar

def _cor_atual(perfil):
    cor = str(perfil.get("cor_principal") or "").strip()
    return cor if cor.startswith("#") and len(cor) in (4, 7) else COR_PADRAO


def _clara(cor, f=0.92):
    try:
        c = cor.lstrip("#")
        if len(c) == 3:
            c = "".join(x * 2 for x in c)
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
        return "#%02X%02X%02X" % tuple(int(v + (255 - v) * f) for v in (r, g, b))
    except Exception:
        return "#F6F3FB"


def _texto_sobre(cor):
    try:
        from utils.pdf_proposta import cores_legiveis
        from reportlab.lib import colors
        texto, sobre = cores_legiveis(colors.HexColor(cor))
        return "#" + texto.hexval()[2:].upper(), ("#FFFFFF" if sobre == colors.white else "#1F2A37")
    except Exception:
        return cor, "#FFFFFF"


def _previa(o, r, p, cli, perfil):
    from utils.pdf_proposta import VALIDADE_DIAS
    cor = _cor_atual(perfil)
    t, s = _texto_sobre(cor)
    empresa = (perfil.get("empresa") or perfil.get("nome") or "Seu negócio").strip()
    numero = o.get("numero")
    num = f"nº {int(numero):03d}" if str(numero or "").isdigit() else ""
    validade = hoje() + timedelta(days=VALIDADE_DIAS)
    lugar = ", ".join(x for x in [str(cli.get("bairro") or "").strip(), str(cli.get("cidade") or "").strip()] if x)
    logo = perfil.get("logo") or ""
    logo_html = f'<img src="{esc(logo)}" alt="">' if str(logo).startswith("data:image/") else ""
    tipo = pr.TIPOS_SERVICO[o["tipo"]][0]
    dias = max(r["dias"], 1)
    its = itens(o)
    if o["tipo"] == "organizacao":
        lista = dados.juntar([f"{n} ({q})" if q > 1 else n for n, q in its]) or "ambientes a combinar"
        serv = f"{tipo}: {lista}"
    else:
        acao = "embalagem e inventário" if o["tipo"] == "pre" else "desembalagem e organização"
        onde = f" de {len(its)} cômodo{'s' if len(its) != 1 else ''}" if its else ""
        serv = f"{tipo}: {acao}{onde} ({caixas(o)} caixas)"
    linhas = [(serv, f"{dias} dia{'s' if dias > 1 else ''}"),
              ("Equipe", f"{r['pessoas']} pessoa{'s' if r['pessoas'] > 1 else ''}" if r["pessoas"] > 1 else "só você")]
    mats = [n for n, _, _ in materiais_escolhidos(o, p)]
    if mats:
        linhas.append(("Materiais: " + dados.juntar([m[0].lower() + m[1:] for m in mats]), "incluso"))
    final = valor_final(o, r)
    sinal = final * o["sinal_pct"] / 100 if o.get("sinal_pct") is not None else final * sinal_pct(o, p) / 100
    obs = (o.get("obs") or "").strip()
    html = (f'<div class="np-pdf" style="--c:{cor};--s:{s};--t:{t};--cl:{_clara(cor)}">'
            f'<div class="cab"><div class="em">{logo_html}<div><b>{esc(empresa)}</b><span>Proposta de Serviço {num}</span>'
            f'</div></div><span>Válida até {validade:%d/%m/%Y}</span></div><div class="cp">'
            f'<div style="font-size:.98rem">Para <b>{esc(cli.get("nome") or "")}</b>{" · " + esc(lugar) if lugar else ""}</div>'
            '<h4>O que está incluído</h4><table>'
            + "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in linhas) + "</table>")
    if obs and o["mostrar_obs"]:
        html += f'<h4>Observações da visita</h4><div class="obs">{esc(obs)}</div>'
    html += (f'<div class="tot"><span>Investimento</span><span>{brl(final)}</span></div>'
             + (f'<div class="sin">Sinal de {o["sinal_pct"]:g}% ({brl(sinal)}) na aprovação · restante no último dia</div>'
                if sinal > 0 else "") + "</div></div>")
    st.markdown(html, unsafe_allow_html=True)


def _salvar_cor(nome):
    hexa = CORES.get(nome)
    if hexa and st.session_state.db.salvar_perfil_usuario({"cor_principal": hexa}):
        limpar_todos_pdfs()


def _marca(o, perfil):
    from utils.pdf_proposta import VALIDADE_DIAS
    with st.container(border=True, key="npsec_marca"):
        st.markdown('<div class="np-h3">Sua marca</div><div class="np-d">A cor vale para esta e as próximas propostas.'
                    '</div>', unsafe_allow_html=True)
        atual = _cor_atual(perfil).upper()
        nomes = ORDEM_CORES
        idx = next((i for i, n in enumerate(nomes) if CORES[n].upper() == atual), None)
        bolas = "".join(f'.st-key-np_cor [role="radiogroup"] > div:nth-child({i}) label > div > div:first-child, '
                        f'.st-key-np_cor [role="radiogroup"] > label:nth-of-type({i}) > div > div:first-child '
                        f'{{ background:{CORES[n]} !important; }}' for i, n in enumerate(nomes, 1))
        st.markdown(f"<style>{bolas}</style>", unsafe_allow_html=True)
        with st.container(key="np_cor"):
            escolha = st.radio("Cor da proposta", nomes, index=idx, horizontal=True, label_visibility="collapsed",
                               key="np_cor_r")
        if escolha and (idx is None or escolha != nomes[idx]):
            _salvar_cor(escolha)
            st.rerun()
        if (o.get("obs") or "").strip():
            c1, c2 = st.columns([3, 1], vertical_alignment="center")
            c1.markdown('<div style="font-size:.9rem">Mostrar observações da visita</div>', unsafe_allow_html=True)
            novo = c2.toggle("Mostrar observações da visita", value=o["mostrar_obs"], key="np_mostrar_obs",
                             label_visibility="collapsed")
            if novo != o["mostrar_obs"]:
                o["mostrar_obs"] = novo
                salvar(o, _p())
                st.rerun()
        st.markdown(f'<div class="np-sw"><span>Validade</span><b>{VALIDADE_DIAS} dias</b></div>', unsafe_allow_html=True)
        logo = str(perfil.get("logo") or "")
        if logo.startswith("data:image/"):
            st.markdown(f'<div class="np-logo"><img src="{esc(logo)}" alt="Logotipo"><span>Seu logotipo</span></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="np-logo"><span>Coloque o seu logotipo: ele sai no topo da proposta.</span></div>',
                        unsafe_allow_html=True)
        n = st.session_state.get("np_logo_n", 0)
        arq = st.file_uploader("Trocar logotipo (PNG ou JPG)" if logo.startswith("data:image/") else
                               "Enviar logotipo (PNG ou JPG)", type=["png", "jpg", "jpeg"], key=f"np_logo_{n}",
                               max_upload_size=5)
        if arq is not None:
            try:
                from pages.perfil import preparar_logo
                if st.session_state.db.salvar_perfil_usuario({"logo": preparar_logo(arq)}):
                    limpar_todos_pdfs()
                    st.session_state["np_logo_n"] = n + 1
                    st.rerun()
                st.error("Não foi possível salvar o logotipo.")
            except ValueError as e:
                st.error(str(e))


def _marcar_enviada():
    o = estado()
    if o.get("pid"):
        dados.marcar(st.session_state.db, o["pid"], "Enviada", "Enviada pelo WhatsApp")
        st.session_state.db.invalidar_cache()
        o["enviada"] = True


def _passo_revisar(o, p, r, cli, perfil):
    final = valor_final(o, r)
    msg = mensagem_whatsapp(cli.get("nome"), pr.TIPOS_SERVICO[o["tipo"]][0], final)
    url = link_whatsapp(cli.get("telefone"), msg)
    _marca(o, perfil)
    with st.container(key="np_zap"), st.container(key="wa_np_zapb"):
        st.link_button("Enviar pelo WhatsApp", url, use_container_width=True, key="np_zap_btn", on_click=_marcar_enviada)
    with st.container(key="np_pdfwrap"):
        from utils.ui import baixar_pdf

        def _gerar():
            from utils.propostas_helper import gerar_pdf_cliente_proposta
            try:
                salvar(o, p)
                ok, m, arq = gerar_pdf_cliente_proposta(st.session_state.db, o["pid"], tipo_documento="proposta")
            except Exception as e:
                return None, None, str(e)
            return (arq, os.path.basename(arq), None) if ok and arq else (None, None, m)
        baixar_pdf("Baixar PDF", f"np_pdf_{o['pid']}", _gerar)
    if o.get("enviada"):
        st.markdown('<div class="np-ok">Mensagem aberta no WhatsApp. Anexe o PDF na conversa. A proposta já está em '
                    '<b>Em aberto</b>, em Propostas.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="np-pe">A proposta fica em <b>Em aberto</b> até a cliente responder.</div>',
                    unsafe_allow_html=True)
    if not str(cli.get("telefone") or "").strip():
        st.caption("A cliente está sem WhatsApp no cadastro: o WhatsApp vai pedir para você escolher a conversa.")
    with st.container(key="np_links_fim"):
        rot = "Concluir e ver em Propostas" if o.get("enviada") else "Salvar e voltar para Propostas"
        if st.button(rot, key="np_fim", type="tertiary", icon=":material/check:", use_container_width=True):
            fechar()
            st.session_state["kanban_selected_proposta"] = None
            st.rerun()


# ---------------------------------------------------------------- tela

def mostrar():
    """Desenha a Nova proposta (a tela Propostas chama quando kanban_nova_proposta_open está ligado)."""
    o = estado()
    p = _p()
    st.markdown(CSS, unsafe_allow_html=True)
    if o["passo"] > 1 and not o.get("cliente_id"):
        o["passo"] = 1
    cli = _cliente(o["cliente_id"]) if o.get("cliente_id") else {}
    if o.get("sinal_pct") is None:
        o["sinal_pct"] = float(p.get("sinal_pct") or 0)
    r = calculo(o, p)
    primeiro = str(cli.get("nome") or "").split(" ")[0]
    titulos = {1: ("Do primeiro olhar à proposta", "Comece pela cliente. Depois você monta o serviço e envia com a sua marca."),
               2: ("Do primeiro olhar à proposta", "Entenda o espaço, planeje o trabalho e envie com a sua marca."),
               3: ("Equipe e valores", "Quem vai com você, os custos do serviço e o sinal."),
               4: ("Revise e envie", f"É assim que {esc(primeiro) if primeiro else 'a cliente'} vai receber. Ajuste a cor "
                   "e o que aparece antes de enviar.")}
    tit, sub = titulos[o["passo"]]
    c_t, c_x = st.columns([5, 1.1], vertical_alignment="top")
    with c_t:
        _cabecalho(o, tit, sub, cli)
    with c_x, st.container(key="np_links_x"):
        if st.button("Fechar", key="np_fechar", type="tertiary", icon=":material/close:"):
            fechar_e_voltar()
    _barra(o, r, p, cli)

    if o["passo"] == 1:
        _passo_cliente(o, p)
        return
    if o["passo"] == 4:
        if not o.get("pid"):
            try:
                salvar(o, p)
            except Exception as e:
                st.error(f"Não foi possível salvar a proposta: {e}")
                o["passo"] = 3
                return
        perfil = _perfil()
        with st.container(key="np_grid"):
            c_esq, c_dir = st.columns([1, 0.62], gap="large")
            with c_esq:
                _previa(o, r, p, cli, perfil)
            with c_dir:
                _passo_revisar(o, p, r, cli, perfil)
        with st.container(key="np_nav"):
            if st.button("Voltar e ajustar", key="np_v_rev", icon=":material/arrow_back:"):
                _ir(o, 3)
        return

    with st.container(key="np_grid"):
        c_esq, c_dir = st.columns([1, 0.46], gap="large")
        with c_esq:
            _resumo_celular(o, r)
            if o["passo"] == 2:
                _passo_servico(o, p, r)
            else:
                r = _passo_equipe(o, p, r)
            r = calculo(o, p)
            if o["passo"] == 2:
                vazio = r["horas"] <= 0
                _nav(lambda: _ir(o, 1), lambda: _ir(o, 3), "Equipe e valores", "serv", desabilitado=vazio)
                if vazio:
                    st.caption("Escolha ao menos um ambiente ou informe as caixas para seguir.")
            else:
                def _revisar():
                    try:
                        salvar(o, p)
                    except Exception as e:
                        st.error(f"Não foi possível salvar a proposta: {e}")
                        return
                    _ir(o, 4)
                _nav(lambda: _ir(o, 2), _revisar, "Revisar e enviar", "eq")
        with c_dir:
            _painel(o, r, p)
