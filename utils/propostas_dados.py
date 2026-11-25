"""
Dados da tela Propostas que o banco não guarda em coluna própria.

- Parâmetros da Precificação (os salvos da organizer por cima dos padrões, como em pages/precificacao.py).
- Marcas no histórico da proposta (tabela andamento_propostas): "Rascunho" quando a Nova proposta salva,
  "Enviada" quando ela manda pelo WhatsApp, "Lembrete" no follow-up e "Visita" com as observações da visita.
  Gravadas aqui com usuario_id e a data de hoje (Brasília): o Database.add_andamento_proposta deixa o
  usuario_id vazio (o filtro por conta esconde a linha) e a data fica presa no dia em que o servidor subiu.
- Descrição da proposta montada pela Nova proposta (é o que o PDF mostra; o PDF lista os ambientes quando a
  descrição começa como "Organização de Cozinha, Sala (2). ...").
- Textos curtos dos cartões do quadro.
"""
from datetime import date, datetime

import pandas as pd
from sqlalchemy import text

from utils import precificacao as pr
from utils.visual import hoje

ENVIO = ("Rascunho", "Enviada")     # status das marcas de envio, em ordem
LEMBRETE = "Lembrete"
VISITA = "Visita"


def parametros(db):
    """Números da Precificação da conta (salvos por cima dos padrões)."""
    salvos = {}
    try:
        salvos = db.get_precificacao() or {}
    except Exception as e:
        print(f"[propostas] precificação: {e}")
    return {**pr.PADROES, **salvos}


def _engine():
    from utils.database import engine
    return engine


def marcar(db, proposta_id, status, observacao="", substituir=False):
    """Grava uma marca no histórico da proposta. substituir=True apaga as marcas anteriores do mesmo status."""
    uid = getattr(db, "usuario_id", None)
    if not uid or not proposta_id:
        return False
    try:
        with _engine().begin() as c:
            if substituir:
                c.execute(text("DELETE FROM andamento_propostas WHERE proposta_id = :p AND usuario_id = :u "
                               "AND status = :s"), {"p": int(proposta_id), "u": uid, "s": status})
            c.execute(text("INSERT INTO andamento_propostas (proposta_id, data, status, observacao, usuario_id) "
                           "VALUES (:p, :d, :s, :o, :u)"),
                      {"p": int(proposta_id), "d": hoje(), "s": status, "o": observacao or "", "u": uid})
        return True
    except Exception as e:
        print(f"[propostas] marcar {status}: {e}")
        return False


def apagar_marca(db, proposta_id, status):
    uid = getattr(db, "usuario_id", None)
    if not uid or not proposta_id:
        return
    try:
        with _engine().begin() as c:
            c.execute(text("DELETE FROM andamento_propostas WHERE proposta_id = :p AND usuario_id = :u AND status = :s"),
                      {"p": int(proposta_id), "u": uid, "s": status})
    except Exception as e:
        print(f"[propostas] apagar {status}: {e}")


def historicos(db, ids=None):
    """{proposta_id: [{"data", "status", "observacao"}]} da conta, em ordem de data (uma consulta só)."""
    uid = getattr(db, "usuario_id", None)
    if not uid:
        return {}
    sql = ("SELECT id, proposta_id, data, status, observacao FROM andamento_propostas WHERE usuario_id = :u"
           + (" AND proposta_id = ANY(:ids)" if ids else "") + " ORDER BY data, id")
    try:
        with _engine().connect() as c:
            linhas = c.execute(text(sql), {"u": uid, **({"ids": [int(i) for i in ids]} if ids else {})}).mappings().all()
    except Exception as e:
        print(f"[propostas] histórico: {e}")
        return {}
    saida = {}
    for r in linhas:
        saida.setdefault(int(r["proposta_id"]), []).append(
            {"data": _data(r["data"]), "status": r["status"] or "", "observacao": r["observacao"] or ""})
    return saida


def _data(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if hasattr(v, "date") and callable(v.date):
        return v.date()
    try:
        return datetime.fromisoformat(str(v)[:10]).date()
    except ValueError:
        return None


def envio(proposta, marcas):
    """('rascunho', data) se a Nova proposta salvou e ela ainda não mandou; senão ('enviada', data do envio).
    Proposta sem marca (feita antes desta tela) conta como enviada na data da proposta."""
    ult = [m for m in (marcas or []) if m["status"] in ENVIO]
    if ult:
        m = ult[-1]
        return ("rascunho" if m["status"] == "Rascunho" else "enviada"), m["data"]
    return "enviada", _data(proposta.get("data_proposta")) or _data(proposta.get("data_inicio"))


def observacoes_visita(marcas):
    vis = [m for m in (marcas or []) if m["status"] == VISITA]
    return vis[-1]["observacao"] if vis else ""


# ---------------------------------------------------------------- textos

def juntar(itens):
    itens = [str(x) for x in itens if str(x).strip()]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def montar_descricao(tipo, itens, caixas=0, dias=1, assistentes=0, materiais=None, observacoes="", mostrar_obs=True):
    """Descrição da proposta (vai para o PDF).

    itens: [(nome, quantidade)] dos ambientes (organização) ou dos cômodos (mudança; a quantidade são as caixas).
    Só com ambientes/cômodos, sem materiais e sem observações à mostra, sai no formato que o PDF transforma
    na lista "O que está incluído" ("Organização de Cozinha, Sala (2). Prazo ..."). Com materiais ou observações
    sai como texto corrido ("Pré-mudança. Cômodos: ... "), que o PDF mostra inteiro em "Descrição do serviço"."""
    rotulo = pr.TIPOS_SERVICO.get(tipo, pr.TIPOS_SERVICO["organizacao"])[0]
    org = tipo not in ("pre", "pos")
    n = max(int(assistentes or 0), 0)
    equipe = f"com {n} assistente{'s' if n > 1 else ''}" if n else "atendimento individual"
    prazo = f"Prazo estimado: {max(int(dias or 0), 1)} dia(s), {equipe}."
    nomes = [(str(a).strip(), int(q or 0)) for a, q in (itens or []) if str(a).strip() and int(q or 0) > 0]
    lista = ", ".join((f"{a} ({q})" if q > 1 else a) if org else a for a, q in nomes)
    extra = []
    if not org and int(caixas or 0) > 0:
        extra.append(f"Volume estimado: {int(caixas)} caixas.")
    mats = [str(m).strip() for m in (materiais or []) if str(m).strip()]
    if mats:
        extra.append("Materiais inclusos: " + juntar([m[0].lower() + m[1:] for m in mats]) + ".")
    obs = (observacoes or "").strip() if mostrar_obs else ""
    if lista and not mats and not obs:
        base = f"{rotulo} de {lista}." if org else f"{rotulo}: {lista}."
        return " ".join([base, prazo] + extra)
    partes = [f"{rotulo}."]
    if lista:
        partes.append(("Ambientes: " if org else "Cômodos: ") + lista + ".")
    partes += extra + [prazo]
    texto = " ".join(partes)
    if obs:
        texto += "\n\nObservações da visita: " + obs
    return texto


def servico_curto(proposta, limite=34):
    """'Closet e Quarto de casal', 'Cozinha, Sala +2' ou o tipo da proposta, para o cartão."""
    import re
    desc = str(proposta.get("descricao") or "")
    nomes = []
    m = (re.match(r"^(?:Organização de |Pré-mudança: |Pós-mudança: )([^.]+)\.", desc)
         or re.search(r"(?:Ambientes|Cômodos): ([^.]+)\.", desc))
    if m:
        nomes = [re.sub(r"\s*\(\d+\)$", "", x).strip() for x in m.group(1).split(",") if x.strip()]
    else:
        from utils.pdf_proposta import ambientes_da_descricao
        nomes = [n for n, _ in ambientes_da_descricao(desc)]
    tipo = str(proposta.get("tipo_proposta") or "").strip()
    if nomes:
        txt = juntar(nomes[:2]) + (f" +{len(nomes) - 2}" if len(nomes) > 2 else "")
        if len(txt) <= limite:
            return txt
        return nomes[0][:limite] + (f" +{len(nomes) - 1}" if len(nomes) > 1 else "")
    if tipo:
        return tipo
    return desc[:limite].strip() or "Serviço"


def quando(d, ref=None):
    ref = ref or hoje()
    if not d:
        return ""
    n = (ref - d).days
    if n <= 0:
        return "hoje"
    if n == 1:
        return "ontem"
    return f"há {n} dias"


def dia_do_servico(proposta, ref=None):
    """(dia atual, total de dias) de um serviço em execução; None se não der para saber."""
    ref = ref or hoje()
    ini = _data(proposta.get("data_inicio_execucao")) or _data(proposta.get("data_inicio"))
    if not ini:
        return None
    fim = _data(proposta.get("data_fim"))
    try:
        prev = int(float(proposta.get("previsao_dias") or 0))
    except (TypeError, ValueError):
        prev = 0
    total = (fim - ini).days + 1 if fim and fim >= ini else max(prev, 1)
    if total > 60:
        total = max(prev, 1)
    k = (ref - ini).days + 1
    return (min(max(k, 1), max(total, 1)), max(total, 1)) if k >= 1 else None
