"""
Indicadores calculados a partir dos dados da conta, usados no Início e no Financeiro.

- movimentos(fin): receitas e despesas com valor numérico, data prevista e data em que
  o dinheiro de fato entrou ou saiu (quando já recebido/pago).
- entrou_gastou(mov, ano, mes): quanto entrou e quanto saiu no mês.
- funil(propostas, hoje, dias): propostas enviadas na janela e quantas viraram trabalho.
"""
from datetime import date, datetime, timedelta

import pandas as pd

REALIZADO = ("Recebido", "Pago", "Aprovado")
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


def entrou_gastou(mov, ano, mes):
    """(entrou, gastou) já realizados no mês."""
    if mov.empty:
        return 0.0, 0.0
    feito = mov[mov["realizado"] & _no_mes(mov["quando"], ano, mes)]
    return float(feito[feito["lado"] == "entra"]["valor"].sum()), float(feito[feito["lado"] == "sai"]["valor"].sum())


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
