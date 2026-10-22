"""
Indicadores calculados a partir dos dados da conta, usados no Início e no Financeiro.

- movimentos(fin): receitas e despesas com valor numérico, data prevista e data em que
  o dinheiro de fato entrou ou saiu (quando já recebido/pago).
- entrou_gastou(mov, ano, mes): quanto entrou e quanto saiu no mês.
- funil(propostas, hoje, dias): propostas enviadas na janela e quantas viraram trabalho.
- mei(mov, hoje): faturamento do ano contra o limite do MEI e situação do DAS.
- cor_categoria(nome): cor fixa de cada categoria, a mesma em todas as telas.

Retiradas (pró-labore) não contam como gasto da empresa: aparecem à parte, para separar
o dinheiro do negócio do dinheiro pessoal.
"""
import re
import unicodedata
from datetime import date, datetime, timedelta

import pandas as pd

REALIZADO = ("Recebido", "Pago", "Aprovado")
LIMITE_MEI = 81000.0
DAS_MEI = 86.05          # 2026, prestação de serviços: 5% do salário mínimo (R$ 1.621) + R$ 5 de ISS
CATEGORIA_RETIRADA = "Pró-labore / retirada"
CATEGORIA_IMPOSTO = "Impostos (DAS)"

# cor por palavra-chave da categoria (sem acento, minúscula); a primeira que casar vale
_CORES = [
    (("pro-labore", "pro labore", "retirada"), "#2E90FA"),
    (("imposto", "das", "taxa"), "#D92D20"),
    (("adiciona",), "#7A5AF8"),
    (("organiza", "servico"), "#0D1B2A"),
    (("produto", "venda"), "#0E9384"),
    (("comiss",), "#C9A84C"),
    (("equipe", "assistente"), "#F79009"),
    (("parceir", "fornecedor"), "#B54708"),
    (("operaciona", "materia", "transporte", "caixa"), "#475467"),
    (("administra",), "#98A2B3"),
]
COR_OUTROS = "#D0D5DD"


def _chave(txt):
    txt = unicodedata.normalize("NFKD", str(txt or "")).encode("ascii", "ignore").decode().lower()
    return txt.strip()


def cor_categoria(nome):
    k = _chave(nome)
    for palavras, cor in _CORES:
        if any(re.search(rf"\b{re.escape(p)}", k) for p in palavras):
            return cor
    return COR_OUTROS


def eh_retirada(categoria):
    k = _chave(categoria)
    return "retirada" in k or "pro-labore" in k or "pro labore" in k
FECHADAS = ("aprovada", "em_execucao", "finalizada")


def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _data(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        d = pd.to_datetime(str(v), dayfirst=False, errors="coerce")
        return None if pd.isna(d) else d.date()
    except Exception:
        return None


def movimentos(fin):
    """Receitas e despesas normalizadas: colunas lado ('entra'/'sai'), valor, d, quando, realizado."""
    cols = ["lado", "valor", "d", "quando", "realizado", "categoria", "descricao", "status"]
    if fin is None or fin.empty:
        return pd.DataFrame(columns=cols)
    df = fin.copy()
    tipo = df["tipo"].astype(str).str.lower()
    classif = df["classificacao"].astype(str).str.lower() if "classificacao" in df else pd.Series("", index=df.index)
    df["lado"] = None
    df.loc[tipo.str.startswith("receita") | (classif == "contas_a_receber"), "lado"] = "entra"
    df.loc[tipo.str.startswith("despesa") | (classif == "contas_a_pagar"), "lado"] = "sai"
    df = df[df["lado"].notna()].copy()
    df["valor"] = df["valor"].apply(_num)
    df["d"] = df["data"].apply(_data)
    drec = df["data_recebimento"].apply(_data) if "data_recebimento" in df else pd.Series(None, index=df.index)
    df["realizado"] = df["status"].isin(REALIZADO)
    df["quando"] = [r if r else d for r, d in zip(drec, df["d"])]
    for c in ("categoria", "descricao"):
        if c not in df:
            df[c] = ""
    return df[cols]


def _no_mes(serie, ano, mes):
    return serie.apply(lambda d: bool(d) and d.year == ano and d.month == mes)


def realizados_no_mes(mov, ano, mes):
    if mov.empty:
        return mov
    return mov[mov["realizado"] & _no_mes(mov["quando"], ano, mes)]


def entrou_gastou(mov, ano, mes):
    """(entrou, gastou) já realizados no mês; retiradas ficam fora do gasto."""
    feito = realizados_no_mes(mov, ano, mes)
    if feito.empty:
        return 0.0, 0.0
    saidas = feito[feito["lado"] == "sai"]
    gasto = saidas[~saidas["categoria"].map(eh_retirada).astype(bool)]
    return float(feito[feito["lado"] == "entra"]["valor"].sum()), float(gasto["valor"].sum())


def retirado(mov, ano, mes):
    """Quanto saiu no mês como pró-labore/retirada."""
    feito = realizados_no_mes(mov, ano, mes)
    if feito.empty:
        return 0.0
    saidas = feito[feito["lado"] == "sai"]
    return float(saidas[saidas["categoria"].map(eh_retirada).astype(bool)]["valor"].sum())


def por_categoria(mov, ano, mes, lado):
    """[(categoria, valor)] realizados no mês, do maior para o menor."""
    feito = realizados_no_mes(mov, ano, mes)
    if feito.empty:
        return []
    f = feito[feito["lado"] == lado].copy()
    f["cat"] = f["categoria"].fillna("").astype(str).str.strip().replace("", "Sem categoria")
    # junta grafias diferentes da mesma categoria ("Serviços de organização" x "Servicos de organizacao")
    f["k"] = f["cat"].apply(_chave)
    nomes = f.groupby("k")["cat"].agg(lambda c: c.value_counts().index[0])
    soma = f.groupby("k")["valor"].sum().sort_values(ascending=False)
    return [(nomes[k], float(v)) for k, v in soma.items() if v]


def mei(mov, hoje):
    """Faturamento do ano (receitas recebidas), projeção para o ano e se o DAS do mês já foi pago."""
    ano = hoje.year
    if mov.empty:
        fat = 0.0
        das_pago = False
    else:
        rec = mov[(mov["lado"] == "entra") & mov["realizado"]]
        fat = float(rec[rec["quando"].apply(lambda d: bool(d) and d.year == ano)]["valor"].sum())
        sai = realizados_no_mes(mov, ano, hoje.month)
        sai = sai[sai["lado"] == "sai"]
        texto = (sai["categoria"].astype(str) + " " + sai["descricao"].astype(str)).apply(_chave)
        das_pago = bool(texto.str.contains(r"\bdas\b|imposto|simples nacional", regex=True).any())
    dia_do_ano = hoje.timetuple().tm_yday
    projecao = fat / dia_do_ano * (366 if ano % 4 == 0 else 365) if fat else 0.0
    return {"faturado": fat, "limite": LIMITE_MEI, "uso": fat / LIMITE_MEI, "projecao": projecao,
            "das": DAS_MEI, "das_pago": das_pago, "ano": ano}


def previsto(mov, ano, mes):
    """(a entrar, a sair) ainda pendentes com vencimento até o fim do mês (inclui atrasados)."""
    if mov.empty:
        return 0.0, 0.0
    fim = (date(ano + (mes == 12), mes % 12 + 1, 1) - timedelta(days=1))
    pend = mov[~mov["realizado"] & mov["d"].apply(lambda d: bool(d) and d <= fim)]
    return float(pend[pend["lado"] == "entra"]["valor"].sum()), float(pend[pend["lado"] == "sai"]["valor"].sum())


def funil(propostas, hoje, dias=90):
    """Propostas feitas nos últimos `dias`: enviadas, aguardando, fechadas, concluídas, recusadas e conversão."""
    from utils.proposta_status import normalize
    vazio = {"enviadas": 0, "aguardando": 0, "fechadas": 0, "concluidas": 0, "recusadas": 0,
             "valor_aguardando": 0.0, "valor_fechado": 0.0, "conversao": None, "dias": dias}
    if propostas is None or propostas.empty:
        return vazio
    df = propostas.copy()
    df["st"] = df["status"].apply(normalize)
    quando = df["data_proposta"].apply(_data) if "data_proposta" in df else pd.Series(None, index=df.index)
    if "data_inicio" in df:
        quando = [q or _data(i) for q, i in zip(quando, df["data_inicio"])]
    df["quando"] = list(quando)
    df = df[df["quando"].apply(lambda d: bool(d) and d >= hoje - timedelta(days=dias))]
    if df.empty:
        return vazio
    df["valor"] = df["valor"].apply(_num)
    fechadas = df[df["st"].isin(FECHADAS)]
    aguard = df[df["st"] == "em_aberto"]
    decididas = len(fechadas) + int((df["st"] == "recusada").sum())
    return {
        "enviadas": len(df),
        "aguardando": len(aguard),
        "fechadas": len(fechadas),
        "concluidas": int((df["st"] == "finalizada").sum()),
        "recusadas": int((df["st"] == "recusada").sum()),
        "valor_aguardando": float(aguard["valor"].sum()),
        "valor_fechado": float(fechadas["valor"].sum()),
        # só conta propostas já respondidas: as que aguardam resposta não puxam a taxa para baixo
        "conversao": (len(fechadas) / decididas) if decididas else None,
        "dias": dias,
    }


def _eh_das(categoria, descricao):
    return bool(re.search(r"\bdas\b|imposto|simples nacional", _chave(f"{categoria} {descricao}")))


def _competencia_no_texto(descricao):
    """(ano, mês) de "competência 03/2026" na descrição, se houver."""
    m = re.search(r"competencia\s+(\d{1,2})/(\d{4})", _chave(descricao))
    if m and 1 <= int(m.group(1)) <= 12:
        return int(m.group(2)), int(m.group(1))
    return None


def das_do_ano(mov, ano, hoje):
    """Situação do DAS de cada mês (competência) do ano.

    O DAS de um mês vence no dia 20 do mês seguinte. Um pagamento conta para a competência
    escrita na descrição ("competência 03/2026", como o app lança); os demais pagamentos de
    imposto vão, em ordem de data, para o mês mais antigo ainda em aberto cujo vencimento já
    começou a correr (pago a partir do 1º dia do mês seguinte à competência).

    Devolve 12 dicts: mes, vencimento, situacao ('pago', 'atrasado', 'a vencer', 'futuro'),
    pago_em, valor_pago."""
    pagos = []
    if not mov.empty:
        sai = mov[(mov["lado"] == "sai") & mov["realizado"]]
        for _, r in sai.iterrows():
            if r["quando"] and _eh_das(r["categoria"], r["descricao"]):
                pagos.append((r["quando"], float(r["valor"]), _competencia_no_texto(r["descricao"])))
    pagos.sort(key=lambda p: p[0])

    meses = []
    for mes in range(1, 13):
        venc = date(ano + (mes == 12), mes % 12 + 1, 20)
        meses.append({"mes": mes, "vencimento": venc, "pago_em": None, "valor_pago": 0.0})
    livres = []
    for quando, valor, comp in pagos:
        if comp and comp[0] == ano:
            m = meses[comp[1] - 1]
            if m["pago_em"] is None:
                m["pago_em"], m["valor_pago"] = quando, valor
                continue
        if comp is None:
            livres.append((quando, valor))
    for quando, valor in livres:
        for m in meses:
            inicio_pagto = date(ano + (m["mes"] == 12), m["mes"] % 12 + 1, 1)
            if m["pago_em"] is None and quando >= inicio_pagto:
                m["pago_em"], m["valor_pago"] = quando, valor
                break
    for m in meses:
        if m["pago_em"]:
            m["situacao"] = "pago"
        elif date(ano, m["mes"], 1) > hoje:
            m["situacao"] = "futuro"
        elif m["vencimento"] < hoje:
            m["situacao"] = "atrasado"
        else:
            m["situacao"] = "a vencer"
    return meses


def faturamento_ano(mov, ano):
    """Receita bruta recebida no ano, separada como pede a declaração anual do MEI (DASN-SIMEI):
    venda de produtos (comércio) e serviços."""
    vazio = {"total": 0.0, "comercio": 0.0, "servicos": 0.0}
    if mov.empty:
        return vazio
    rec = mov[(mov["lado"] == "entra") & mov["realizado"]]
    rec = rec[rec["quando"].apply(lambda d: bool(d) and d.year == ano)]
    if rec.empty:
        return vazio
    eh_produto = rec["categoria"].apply(lambda c: bool(re.search(r"produto|\bvenda", _chave(c))))
    comercio = float(rec[eh_produto]["valor"].sum())
    total = float(rec["valor"].sum())
    return {"total": total, "comercio": comercio, "servicos": total - comercio}


def prazo_dasn(hoje):
    """Próximo prazo da declaração anual (DASN-SIMEI): (ano declarado, data limite, dias que faltam)."""
    limite = date(hoje.year, 5, 31)
    if hoje > limite:
        limite = date(hoje.year + 1, 5, 31)
    return limite.year - 1, limite, (limite - hoje).days
