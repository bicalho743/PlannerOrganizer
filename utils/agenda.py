"""
Agenda: tudo o que tem data no app, num lugar só.

montar_agenda junta, no período pedido:
  - compromissos da Agenda (diárias, visitas, orçamentos), com a situação da receita gerada;
  - início e fim dos serviços aprovados ou em execução (Propostas);
  - retornos de pós-organização pendentes;
  - aniversários das clientes (com link do WhatsApp quando há telefone);
  - vencimentos a receber e a pagar ainda pendentes no Financeiro
    (menos as receitas que nasceram de um compromisso, que já aparecem nele).

Cada item é um dict: data, hora, tipo, titulo, detalhe, valor, cor, situacao, compromisso_id.
"""
from datetime import date, timedelta

import pandas as pd

from utils.indicadores import _data, _num

TIPOS = {
    # tipo: (rótulo, cor, ordem no dia)
    "aniversario": ("Aniversário", "#C05A7B", -1),
    "compromisso": ("Compromisso", "#D9643A", 0),
    "servico": ("Serviço", "#3D6BB3", 1),
    "pos": ("Pós-organização", "#7356BF", 2),
    "receber": ("A receber", "#067647", 3),
    "pagar": ("A pagar", "#B42318", 4),
}

ETAPAS_POS = {
    "agradecimento": "Agradecimento",
    "acompanhamento": "Acompanhamento",
    "ajuste_fino": "Ajuste fino",
    "feedback": "Feedback",
    "continuidade": "Continuidade",
    "retorno_tecnico": "Retorno técnico",
}

SITUACAO_SERVICO = ("aprovada", "em_execucao")
MES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MSG_ANIVERSARIO = "Feliz aniversário, {nome}! Desejo um novo ciclo leve e cheio de alegria. 💛"


def dia_mes_aniversario(valor):
    """(dia, mês) de data_aniversario, guardada como "05/out" (também aceita "05/10" e datas). None se inválida."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if hasattr(valor, "month") and hasattr(valor, "day"):
        return valor.day, valor.month
    txt = str(valor).strip().lower()
    try:
        partes = txt.replace("-", "/").split("/")
        if len(partes) >= 3 and len(partes[0]) == 4:  # 1990-10-05
            return int(partes[2][:2]), int(partes[1])
        dia, mes = int(partes[0]), partes[1].strip()
        mes_n = int(mes) if mes.isdigit() else MES_ABREV.index(mes[:3]) + 1
        if 1 <= dia <= 31 and 1 <= mes_n <= 12:
            return dia, mes_n
    except (ValueError, IndexError):
        pass
    return None


def semana_de(d):
    """(segunda, domingo) da semana de d."""
    seg = d - timedelta(days=d.weekday())
    return seg, seg + timedelta(days=6)


def mes_de(d):
    """(primeiro dia, último dia) do mês de d."""
    ini = d.replace(day=1)
    prox = date(ini.year + (ini.month == 12), ini.month % 12 + 1, 1)
    return ini, prox - timedelta(days=1)


def _item(tipo, d, titulo, detalhe="", valor=0.0, hora="", situacao="", compromisso_id=None, whatsapp=""):
    return {"data": d, "hora": hora or "", "tipo": tipo, "titulo": titulo, "detalhe": detalhe,
            "valor": float(valor or 0), "cor": TIPOS[tipo][1], "situacao": situacao,
            "compromisso_id": compromisso_id, "whatsapp": whatsapp}


def _linhas(df):
    if df is None or getattr(df, "empty", True):
        return []
    return df.to_dict("records")


def montar_agenda(inicio, fim, compromissos=None, propostas=None, acoes_pos=None, financeiro=None, clientes=None):
    """Itens da agenda entre inicio e fim (inclusive), em ordem de dia, hora e tipo."""
    from utils.proposta_status import normalize

    def no_periodo(d):
        return d is not None and inicio <= d <= fim

    itens, ids_do_compromisso = [], set()
    for c in _linhas(compromissos):
        if c.get("transacao_id") and not pd.isna(c.get("transacao_id")):
            ids_do_compromisso.add(int(c["transacao_id"]))
        d = _data(c.get("data"))
        if not no_periodo(d):
            continue
        valor = _num(c.get("valor"))
        recebido = str(c.get("status_receita") or "") in ("Recebido", "Pago")
        situacao = ("recebido" if recebido else "a receber") if valor > 0 else ""
        detalhe = " · ".join(x for x in (c.get("cliente_nome"), c.get("local")) if x)
        itens.append(_item("compromisso", d, c.get("titulo") or "Compromisso", detalhe, valor,
                           c.get("hora"), situacao, int(c["id"])))

    from utils.whatsapp_helper import whatsapp_link
    for c in _linhas(clientes):
        dm = dia_mes_aniversario(c.get("data_aniversario"))
        if not dm:
            continue
        for ano in range(inicio.year, fim.year + 1):
            try:
                d = date(ano, dm[1], dm[0])
            except ValueError:  # 29/02 fora de ano bissexto
                continue
            if no_periodo(d):
                nome = str(c.get("nome") or "Cliente")
                itens.append(_item("aniversario", d, nome, "Dê os parabéns",
                                   whatsapp=whatsapp_link(c.get("telefone"),
                                                          MSG_ANIVERSARIO.format(nome=nome.split(" ")[0]))))

    for p in _linhas(propostas):
        if normalize(p.get("status") or "") not in SITUACAO_SERVICO:
            continue
        nome = f"Proposta #{p.get('numero')}"
        cliente = p.get("cliente_nome") or ""
        ini = _data(p.get("data_inicio")) or _data(p.get("data_inicio_execucao"))
        fim_p = _data(p.get("data_fim"))
        if no_periodo(ini):
            itens.append(_item("servico", ini, f"Início do serviço · {cliente}".strip(" ·"), nome))
        if no_periodo(fim_p) and fim_p != ini:
            itens.append(_item("servico", fim_p, f"Fim do serviço · {cliente}".strip(" ·"), nome))

    for a in _linhas(acoes_pos):
        d = _data(a.get("due_date"))
        if not no_periodo(d):
            continue
        etapa = ETAPAS_POS.get(a.get("action_type"), str(a.get("action_type") or "Retorno"))
        num = a.get("proposta_numero")
        itens.append(_item("pos", d, f"{etapa} · {a.get('cliente_nome') or ''}".strip(" ·"),
                           f"Proposta #{num}" if num else ""))

    for t in _linhas(financeiro):
        if str(t.get("status") or "") != "Pendente":
            continue
        try:
            if int(t.get("id")) in ids_do_compromisso:
                continue
        except (TypeError, ValueError):
            pass
        d = _data(t.get("data"))
        if not no_periodo(d):
            continue
        tipo = str(t.get("tipo") or "").lower()
        classif = str(t.get("classificacao") or "").lower()
        if tipo.startswith("receita") or classif == "contas_a_receber":
            lado = "receber"
        elif tipo.startswith("despesa") or classif == "contas_a_pagar":
            lado = "pagar"
        else:
            continue
        itens.append(_item(lado, d, t.get("descricao") or TIPOS[lado][0], t.get("categoria") or "",
                           _num(t.get("valor"))))

    itens.sort(key=lambda i: (i["data"], i["hora"] or "99:99", TIPOS[i["tipo"]][2]))
    return itens


def totais(itens):
    """Quanto entra e sai no período pelos itens da agenda (compromissos já recebidos não contam)."""
    entra = sum(i["valor"] for i in itens if i["tipo"] == "receber"
                or (i["tipo"] == "compromisso" and i["situacao"] == "a receber"))
    sai = sum(i["valor"] for i in itens if i["tipo"] == "pagar")
    return entra, sai
