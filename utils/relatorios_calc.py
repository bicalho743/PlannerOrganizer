"""
Cálculos da tela Relatórios. Funções puras (DataFrame entra, números/DataFrame saem), testadas em
tests/test_relatorios_calc.py. A tela (pages/relatorios.py) só desenha.

Princípios (ver o cabeçalho de pages/relatorios.py):
- todo número tem uma definição e é comparado com outro período (anterior ou o mesmo do ano passado);
- dinheiro conta na data em que entrou ou saiu (regime de caixa), igual ao Início e ao Financeiro;
- pró-labore/retirada não é gasto da empresa: aparece à parte.

Definições usadas:
- Faturamento: receitas recebidas no período.
- Custos diretos: despesas pagas ligadas a um trabalho (com proposta), marcadas como custo direto
  ou de categoria de equipe, assistente, fornecedor, comissão, material ou produto.
- Despesas fixas/operacionais: as demais despesas pagas (sem retiradas).
- Lucro: faturamento − custos diretos − despesas. Margem: lucro ÷ faturamento.
- Trabalho fechado: proposta aprovada, em execução ou finalizada. Conta na data de aprovação
  (ou na data da proposta, quando a aprovação não foi registrada).
- Conversão: fechadas ÷ (fechadas + recusadas) — propostas que ainda aguardam resposta não entram.
"""
import calendar
from datetime import date, timedelta

import pandas as pd

from utils.indicadores import _chave, _data, _num, eh_retirada, movimentos

MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FECHADAS = ("aprovada", "em_execucao", "finalizada")

PERIODOS = ["Este mês", "Mês passado", "Últimos 3 meses", "Últimos 6 meses", "Últimos 12 meses",
            "Este ano", "Ano passado", "Personalizado"]

# palavras (sem acento, minúsculas) que indicam custo direto do trabalho
_CUSTO_DIRETO = ("equipe", "assistente", "fornecedor", "parceir", "comiss", "materia", "produto",
                 "custo", "organizador", "item", "adiciona", "frete", "transporte do trabalho")


# ───────────────────────────── períodos ─────────────────────────────

def _fim_mes(a, m):
    return date(a, m, calendar.monthrange(a, m)[1])


def _soma_meses(a, m, n):
    t = a * 12 + (m - 1) + n
    return t // 12, t % 12 + 1


def intervalo(preset, hoje, ini=None, fim=None):
    """(início, fim) do período escolhido, datas inclusivas."""
    a, m = hoje.year, hoje.month
    if preset == "Este mês":
        return date(a, m, 1), _fim_mes(a, m)
    if preset == "Mês passado":
        pa, pm = _soma_meses(a, m, -1)
        return date(pa, pm, 1), _fim_mes(pa, pm)
    for n, rot in ((3, "Últimos 3 meses"), (6, "Últimos 6 meses"), (12, "Últimos 12 meses")):
        if preset == rot:   # o mês atual e os anteriores, meses inteiros
            pa, pm = _soma_meses(a, m, -(n - 1))
            return date(pa, pm, 1), _fim_mes(a, m)
    if preset == "Este ano":
        return date(a, 1, 1), date(a, 12, 31)
    if preset == "Ano passado":
        return date(a - 1, 1, 1), date(a - 1, 12, 31)
    ini = ini or date(a, m, 1)
    fim = fim or hoje
    return (ini, fim) if ini <= fim else (fim, ini)


def _meses_inteiros(ini, fim):
    """Número de meses se o período vai do dia 1 ao último dia de um mês; senão None."""
    if ini.day != 1 or fim != _fim_mes(fim.year, fim.month):
        return None
    return (fim.year - ini.year) * 12 + fim.month - ini.month + 1


def periodo_anterior(ini, fim):
    """Período de mesmo tamanho logo antes. Meses inteiros comparam com meses inteiros."""
    n = _meses_inteiros(ini, fim)
    if n:
        a, m = _soma_meses(ini.year, ini.month, -n)
        fa, fm = _soma_meses(ini.year, ini.month, -1)
        return date(a, m, 1), _fim_mes(fa, fm)
    dias = (fim - ini).days + 1
    return ini - timedelta(days=dias), ini - timedelta(days=1)


def _menos_um_ano(d):
    try:
        return d.replace(year=d.year - 1)
    except ValueError:          # 29/02
        return d.replace(year=d.year - 1, day=28)


def mesmo_periodo_ano_passado(ini, fim):
    if _meses_inteiros(ini, fim):
        fa = _menos_um_ano(fim)
        return _menos_um_ano(ini), _fim_mes(fa.year, fa.month)
    return _menos_um_ano(ini), _menos_um_ano(fim)


def ate_hoje(ini, fim, cini, cfim, hoje):
    """Período que ainda não terminou: corta em hoje e corta a comparação no mesmo número de dias.

    Comparar outubro até o dia 21 com setembro inteiro faz qualquer mês em andamento parecer pior.
    Devolve (ini, fim, cini, cfim, cortado)."""
    if not (ini <= hoje < fim):
        return ini, fim, cini, cfim, False
    return ini, hoje, cini, min(cfim, cini + (hoje - ini)), True


def rotulo_periodo(ini, fim):
    if ini.day == 1 and fim == _fim_mes(fim.year, fim.month):
        if (ini.year, ini.month) == (fim.year, fim.month):
            return f"{MESES_ABREV[ini.month - 1]}/{ini.year}"
        return f"{MESES_ABREV[ini.month - 1]}/{ini.year} a {MESES_ABREV[fim.month - 1]}/{fim.year}"
    return f"{ini:%d/%m/%Y} a {fim:%d/%m/%Y}"


def meses_do_periodo(ini, fim):
    out, a, m = [], ini.year, ini.month
    while (a, m) <= (fim.year, fim.month):
        out.append((a, m))
        a, m = _soma_meses(a, m, 1)
    return out


def variacao(atual, anterior):
    """Variação relativa (0.15 = +15%); None quando não há base para comparar."""
    if anterior is None or abs(anterior) < 0.005:
        return None
    return (atual - anterior) / abs(anterior)


# ───────────────────────────── dinheiro ─────────────────────────────

def movimentos_rel(fin):
    """movimentos() do Início/Financeiro + proposta_id e classificacao (para custo direto e lucro por trabalho)."""
    mov = movimentos(fin)
    if mov.empty:
        return mov.assign(proposta_id=pd.Series(dtype=float), classificacao=pd.Series(dtype=str))
    extra = fin.loc[mov.index]
    mov = mov.copy()
    mov["proposta_id"] = pd.to_numeric(extra["proposta_id"], errors="coerce") if "proposta_id" in extra else float("nan")
    mov["classificacao"] = extra["classificacao"].astype(str).str.lower() if "classificacao" in extra else ""
    return mov


def eh_custo_direto(categoria, classificacao="", proposta_id=None):
    if str(classificacao or "").lower() == "custo_direto":
        return True
    if proposta_id is not None and not pd.isna(proposta_id):
        return True
    k = _chave(categoria)
    return any(p in k for p in _CUSTO_DIRETO)


def _realizados(mov, ini, fim):
    if mov.empty:
        return mov
    return mov[mov["realizado"] & mov["quando"].apply(lambda d: bool(d) and ini <= d <= fim)]


def _tipo_saida(r):
    if eh_retirada(r["categoria"]):
        return "retirada"
    return "custo" if eh_custo_direto(r["categoria"], r.get("classificacao", ""), r.get("proposta_id")) else "despesa"


def resultado(mov, ini, fim):
    """DRE simplificada do período (regime de caixa)."""
    f = _realizados(mov, ini, fim)
    r = {"faturamento": 0.0, "custos": 0.0, "despesas": 0.0, "retiradas": 0.0, "n_recebimentos": 0}
    if not f.empty:
        ent = f[f["lado"] == "entra"]
        sai = f[f["lado"] == "sai"].copy()
        r["faturamento"] = float(ent["valor"].sum())
        r["n_recebimentos"] = int(len(ent))
        if not sai.empty:
            sai["t"] = sai.apply(_tipo_saida, axis=1)
            for t, k in (("custo", "custos"), ("despesa", "despesas"), ("retirada", "retiradas")):
                r[k] = float(sai[sai["t"] == t]["valor"].sum())
    r["margem_bruta"] = r["faturamento"] - r["custos"]
    r["lucro"] = r["faturamento"] - r["custos"] - r["despesas"]
    r["margem"] = r["lucro"] / r["faturamento"] if r["faturamento"] else None
    r["caixa"] = r["lucro"] - r["retiradas"]   # o que ficou na empresa depois das retiradas
    return r


def serie_mensal(mov, ini, fim):
    """Uma linha por mês do período: faturamento, custos, despesas, lucro e retiradas."""
    linhas = []
    for a, m in meses_do_periodo(ini, fim):
        i, f = max(ini, date(a, m, 1)), min(fim, _fim_mes(a, m))
        r = resultado(mov, i, f)
        linhas.append({"mes": f"{MESES_ABREV[m - 1]}/{str(a)[2:]}", "ano": a, "m": m,
                       "faturamento": r["faturamento"], "custos": r["custos"], "despesas": r["despesas"],
                       "lucro": r["lucro"], "retiradas": r["retiradas"]})
    return pd.DataFrame(linhas, columns=["mes", "ano", "m", "faturamento", "custos", "despesas", "lucro", "retiradas"])


def por_categoria(mov, ini, fim, lado):
    """DataFrame categoria/valor do período, do maior para o menor (junta grafias diferentes)."""
    f = _realizados(mov, ini, fim)
    if f.empty:
        return pd.DataFrame(columns=["categoria", "valor"])
    f = f[f["lado"] == lado].copy()
    if lado == "sai":
        f = f[~f["categoria"].map(eh_retirada).astype(bool)]
    if f.empty:
        return pd.DataFrame(columns=["categoria", "valor"])
    f["cat"] = f["categoria"].fillna("").astype(str).str.strip().replace("", "Sem categoria")
    f["k"] = f["cat"].apply(_chave)
    nomes = f.groupby("k")["cat"].agg(lambda c: c.value_counts().index[0])
    soma = f.groupby("k")["valor"].sum().sort_values(ascending=False)
    return pd.DataFrame([{"categoria": nomes[k], "valor": float(v)} for k, v in soma.items() if v],
                        columns=["categoria", "valor"])


def destaques(atual, comp, cat_atual_sai, cat_comp_sai, rotulo_comp):
    """Frases curtas que explicam a variação do lucro (o que mais mudou)."""
    from utils.currency_formatter import fmt_brl
    out = []
    dl = atual["lucro"] - comp["lucro"]
    if abs(dl) >= 1 and (atual["faturamento"] or comp["faturamento"]):
        d_fat = atual["faturamento"] - comp["faturamento"]
        d_gas = (atual["custos"] + atual["despesas"]) - (comp["custos"] + comp["despesas"])
        if abs(d_fat) >= abs(d_gas):
            motivo = f"faturamento {'maior' if d_fat > 0 else 'menor'} ({'+' if d_fat > 0 else '−'}{fmt_brl(abs(d_fat))})"
        else:
            motivo = f"gastos {'maiores' if d_gas > 0 else 'menores'} ({'+' if d_gas > 0 else '−'}{fmt_brl(abs(d_gas))})"
        motivo = ("pelo " if motivo.startswith("faturamento") else "pelos ") + motivo
        out.append(f"O lucro {'subiu' if dl > 0 else 'caiu'} {fmt_brl(abs(dl))} em relação a {rotulo_comp}, "
                   f"principalmente {motivo}.")
    if not cat_atual_sai.empty:
        chaves = cat_atual_sai["categoria"].map(_chave)
        a = dict(zip(chaves, cat_atual_sai["valor"]))
        nomes = dict(zip(chaves, cat_atual_sai["categoria"]))
        c = dict(zip(cat_comp_sai["categoria"].map(_chave), cat_comp_sai["valor"])) if not cat_comp_sai.empty else {}
        k, d = max(((k, v - c.get(k, 0.0)) for k, v in a.items()), key=lambda x: x[1])
        if d >= 50:
            out.append(f"O gasto que mais cresceu foi {nomes[k]}: +{fmt_brl(d)}.")
    if atual["faturamento"] and atual["retiradas"] > atual["lucro"] > -1:
        out.append(f"As retiradas passaram o lucro em {fmt_brl(atual['retiradas'] - atual['lucro'])}: "
                   "o caixa da empresa diminuiu no período.")
    return out


# ───────────────────────────── propostas e clientes ─────────────────────────────

def _prep_propostas(propostas):
    from utils.proposta_status import normalize
    if propostas is None or propostas.empty:
        return pd.DataFrame(columns=["id", "numero", "cliente_id", "cliente_nome", "valor", "st", "criada", "fechada_em", "aprovacao", "tipo"])
    df = propostas.copy()
    df["st"] = df["status"].apply(normalize) if "status" in df else None
    df["valor"] = df["valor"].apply(_num) if "valor" in df else 0.0
    criada = df["data_proposta"].apply(_data) if "data_proposta" in df else pd.Series(None, index=df.index)
    inicio = df["data_inicio"].apply(_data) if "data_inicio" in df else pd.Series(None, index=df.index)
    df["criada"] = [c or i for c, i in zip(criada, inicio)]
    aprov = df["data_aprovacao"].apply(_data) if "data_aprovacao" in df else pd.Series(None, index=df.index)
    df["fechada_em"] = [(ap or c) if s in FECHADAS else None for ap, c, s in zip(aprov, df["criada"], df["st"])]
    df["aprovacao"] = list(aprov)
    tipo = df["tipo_proposta"].astype(str).str.strip() if "tipo_proposta" in df else pd.Series("", index=df.index)
    df["tipo"] = tipo.where(~tipo.str.lower().isin(["", "none", "nan"]), "Sem tipo")
    return df


def _no(d, ini, fim):
    return bool(d) and ini <= d <= fim


def _entre(df, col, ini, fim):
    """Linhas com a data da coluna dentro do período (máscara booleana: funciona também com df vazio)."""
    if df.empty:
        return df
    return df[df[col].apply(lambda d: _no(d, ini, fim)).astype(bool)]


def propostas_periodo(propostas, ini, fim):
    """Funil das propostas feitas no período, por quantidade e por valor."""
    df = _prep_propostas(propostas)
    df = _entre(df, "criada", ini, fim)
    fech = df[df["st"].isin(FECHADAS)]
    rec = df[df["st"] == "recusada"]
    agu = df[df["st"] == "em_aberto"]
    dec = len(fech) + len(rec)
    vdec = float(fech["valor"].sum() + rec["valor"].sum())
    dias = [(ap - c).days for ap, c in zip(fech["aprovacao"], fech["criada"]) if ap and c and ap >= c]
    return {
        "enviadas": int(len(df)), "fechadas": int(len(fech)), "recusadas": int(len(rec)), "aguardando": int(len(agu)),
        "valor_enviado": float(df["valor"].sum()), "valor_fechado": float(fech["valor"].sum()),
        "valor_recusado": float(rec["valor"].sum()), "valor_aguardando": float(agu["valor"].sum()),
        "conversao": len(fech) / dec if dec else None,
        "conversao_valor": float(fech["valor"].sum()) / vdec if vdec else None,
        "ticket_fechado": float(fech["valor"].mean()) if len(fech) else None,
        "ticket_recusado": float(rec["valor"].mean()) if len(rec) else None,
        "dias_para_fechar": float(pd.Series(dias).median()) if dias else None,
    }


def propostas_por_tipo(propostas, ini, fim):
    df = _prep_propostas(propostas)
    df = _entre(df, "criada", ini, fim)
    if df.empty:
        return pd.DataFrame(columns=["tipo", "enviadas", "fechadas", "recusadas", "conversao", "valor_fechado", "ticket"])
    linhas = []
    for t, g in df.groupby("tipo"):
        fech, rec = g[g["st"].isin(FECHADAS)], g[g["st"] == "recusada"]
        dec = len(fech) + len(rec)
        linhas.append({"tipo": t, "enviadas": len(g), "fechadas": len(fech), "recusadas": len(rec),
                       "conversao": len(fech) / dec if dec else None, "valor_fechado": float(fech["valor"].sum()),
                       "ticket": float(fech["valor"].mean()) if len(fech) else None})
    return pd.DataFrame(linhas).sort_values("valor_fechado", ascending=False).reset_index(drop=True)


def propostas_mensal(propostas, ini, fim):
    df = _prep_propostas(propostas)
    linhas = []
    for a, m in meses_do_periodo(ini, fim):
        i, f = max(ini, date(a, m, 1)), min(fim, _fim_mes(a, m))
        g = _entre(df, "criada", i, f)
        fech, rec = g[g["st"].isin(FECHADAS)], g[g["st"] == "recusada"]
        dec = len(fech) + len(rec)
        linhas.append({"mes": f"{MESES_ABREV[m - 1]}/{str(a)[2:]}", "enviadas": len(g), "fechadas": len(fech),
                       "recusadas": len(rec), "conversao": len(fech) / dec if dec else None})
    return pd.DataFrame(linhas, columns=["mes", "enviadas", "fechadas", "recusadas", "conversao"])


def _trabalhos(propostas):
    """Trabalhos fechados (todas as datas), com cliente e data de fechamento."""
    df = _prep_propostas(propostas)
    df = df[df["st"].isin(FECHADAS) & df["fechada_em"].notna()].copy()
    df["cliente_id"] = pd.to_numeric(df["cliente_id"], errors="coerce") if "cliente_id" in df else float("nan")
    return df


def clientes_periodo(propostas, clientes, ini, fim):
    """Clientes atendidas no período: novas × que voltaram, valor por cliente, concentração e recompra."""
    from utils.origem_cliente import origem_para_exibicao
    tr = _trabalhos(propostas)
    vazio = {"atendidas": 0, "novas": 0, "voltaram": 0, "valor": 0.0, "valor_por_cliente": None, "trabalhos": 0,
             "concentracao_top3": None, "recompra": None, "clientes_base": 0,
             "ranking": pd.DataFrame(columns=["cliente", "trabalhos", "valor", "primeira_vez"]),
             "origem": pd.DataFrame(columns=["origem", "clientes", "trabalhos", "valor"])}
    tr = tr[tr["cliente_id"].notna()]
    if tr.empty:
        return vazio
    primeira = tr.groupby("cliente_id")["fechada_em"].min()
    no = _entre(tr, "fechada_em", ini, fim)
    # recompra: entre todas as clientes com trabalho fechado até o fim do período, quantas fecharam 2 ou mais
    ate = tr[tr["fechada_em"].apply(lambda d: d <= fim)]
    por_cli = ate.groupby("cliente_id").size()
    out = dict(vazio)
    out["clientes_base"] = int(len(por_cli))
    out["recompra"] = float((por_cli >= 2).sum() / len(por_cli)) if len(por_cli) else None
    if no.empty:
        return out
    g = no.groupby("cliente_id").agg(trabalhos=("id", "count"), valor=("valor", "sum")).reset_index()
    g["primeira_vez"] = g["cliente_id"].map(primeira).apply(lambda d: _no(d, ini, fim))
    nomes = {}
    origens = {}
    if clientes is not None and not clientes.empty and "id" in clientes:
        cid = pd.to_numeric(clientes["id"], errors="coerce")
        nomes = dict(zip(cid, clientes.get("nome", pd.Series("", index=clientes.index)).astype(str)))
        if "origem_cliente" in clientes:
            origens = dict(zip(cid, clientes["origem_cliente"].apply(origem_para_exibicao)))
    if "cliente_nome" in no:
        for c, n in zip(no["cliente_id"], no["cliente_nome"].astype(str)):
            nomes.setdefault(c, n)
    g["cliente"] = g["cliente_id"].map(lambda c: nomes.get(c) or f"Cliente #{int(c)}")
    g["origem"] = g["cliente_id"].map(lambda c: origens.get(c) or "Não informado")
    g = g.sort_values("valor", ascending=False).reset_index(drop=True)
    total = float(g["valor"].sum())
    out.update({
        "atendidas": int(len(g)), "novas": int(g["primeira_vez"].sum()), "voltaram": int((~g["primeira_vez"]).sum()),
        "valor": total, "trabalhos": int(g["trabalhos"].sum()),
        "valor_por_cliente": total / len(g) if len(g) else None,
        "concentracao_top3": float(g["valor"].head(3).sum() / total) if total else None,
        "ranking": g[["cliente", "trabalhos", "valor", "primeira_vez"]],
        "origem": (g.groupby("origem").agg(clientes=("cliente_id", "count"), trabalhos=("trabalhos", "sum"),
                                           valor=("valor", "sum")).reset_index()
                   .sort_values("valor", ascending=False).reset_index(drop=True)),
    })
    return out


def lucro_por_trabalho(mov, propostas, ini, fim):
    """Trabalhos fechados no período com o que já entrou e saiu ligado a cada um (todas as datas)."""
    tr = _trabalhos(propostas)
    tr = _entre(tr, "fechada_em", ini, fim)
    cols = ["numero", "cliente", "tipo", "valor", "recebido", "custos", "lucro", "margem"]
    if tr.empty:
        return pd.DataFrame(columns=cols)
    feito = mov[mov["realizado"] & mov["proposta_id"].notna()] if not mov.empty else mov
    linhas = []
    for _, p in tr.iterrows():
        m = feito[feito["proposta_id"] == p["id"]] if not feito.empty else feito
        rec = float(m[m["lado"] == "entra"]["valor"].sum()) if not m.empty else 0.0
        cus = float(m[(m["lado"] == "sai") & ~m["categoria"].map(eh_retirada).astype(bool)]["valor"].sum()) if not m.empty else 0.0
        linhas.append({"numero": p.get("numero"), "cliente": p.get("cliente_nome") or "", "tipo": p["tipo"],
                       "valor": float(p["valor"]), "recebido": rec, "custos": cus, "lucro": rec - cus,
                       "margem": (rec - cus) / rec if rec else None})
    return pd.DataFrame(linhas, columns=cols).sort_values("lucro", ascending=False).reset_index(drop=True)


# ───────────────────────────── o que vem pela frente ─────────────────────────────

FAIXAS = ["Atrasado", "Até 30 dias", "31 a 60 dias", "61 a 90 dias", "Depois de 90 dias", "Sem data"]


def _faixa(d, hoje):
    if not d:
        return "Sem data"
    n = (d - hoje).days
    if n < 0:
        return "Atrasado"
    return "Até 30 dias" if n <= 30 else "31 a 60 dias" if n <= 60 else "61 a 90 dias" if n <= 90 else "Depois de 90 dias"


def agenda_pendente(mov, hoje):
    """A receber e a pagar ainda pendentes, por faixa de vencimento (atrasado, 30, 60, 90 dias…)."""
    base = pd.DataFrame({"faixa": FAIXAS, "a_receber": 0.0, "a_pagar": 0.0})
    if mov.empty:
        return base, mov
    pend = mov[~mov["realizado"] & (mov["status"].astype(str).str.lower() != "cancelado")].copy()
    if pend.empty:
        return base, pend
    pend["faixa"] = pend["d"].apply(lambda d: _faixa(d, hoje))
    for lado, col in (("entra", "a_receber"), ("sai", "a_pagar")):
        s = pend[pend["lado"] == lado].groupby("faixa")["valor"].sum()
        base[col] = base["faixa"].map(s).fillna(0.0)
    atrasados = pend[pend["faixa"] == "Atrasado"].sort_values("d")
    return base, atrasados


def propostas_aguardando(propostas, hoje):
    """Propostas em aberto, com quantos dias estão paradas (mais antigas primeiro)."""
    df = _prep_propostas(propostas)
    df = df[df["st"] == "em_aberto"].copy()
    if df.empty:
        return pd.DataFrame(columns=["numero", "cliente", "valor", "dias"])
    df["dias"] = df["criada"].apply(lambda d: (hoje - d).days if d else None)
    df["cliente"] = df["cliente_nome"] if "cliente_nome" in df else ""
    return df[["numero", "cliente", "valor", "dias"]].sort_values("dias", ascending=False, na_position="last").reset_index(drop=True)
