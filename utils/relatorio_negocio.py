"""
Relatório do negócio sem tela: as mesmas contas da página Relatórios (pages/relatorios.py), para o PDF e o Excel do
site e para o PDF do app (API GET /pdf/relatorio). Tudo vem de utils/relatorios_calc.

- periodo(preset, comparar, hoje, ini, fim) → datas e rótulos (corta o período em andamento em hoje);
- exportacao(mov, propostas, clientes, p, hoje) → {"_resumo": [(rótulo, valor, detalhe)], "<tabela>": DataFrame};
- df_texto(df) → tabela formatada como texto (R$, %, inteiros, datas);
- pdf(exp, p, perfil) → bytes do PDF (utils/relatorio_pdf.gerar_pdf).
"""
from datetime import timedelta

import pandas as pd

from utils import relatorios_calc as rc
from utils.currency_formatter import fmt_brl

COMPARAR = ["Período anterior", "Mesmo período do ano passado"]

XL_NOMES = {"valor": "Valor", "valor_fechado": "Valor fechado", "ticket": "Ticket médio", "conversao": "Conversão",
            "margem": "Margem", "custos": "Custos", "lucro": "Lucro", "recebido": "Recebido", "dias": "Dias parada",
            "numero": "Proposta", "cliente": "Cliente", "tipo": "Tipo", "mes": "Mês", "enviadas": "Enviadas",
            "fechadas": "Fechadas", "recusadas": "Recusadas", "em_aberto": "Em aberto", "categoria": "Categoria"}
XL_PCT = ("conversão", "margem", "taxa", "%")
XL_INTEIRO = ("trabalhos", "clientes", "enviadas", "fechadas", "recusadas", "em aberto", "dias", "qtd")

LINHAS_DRE = [("Faturamento", "faturamento"), ("(−) Custos diretos", "custos"), ("= Margem bruta", "margem_bruta"),
              ("(−) Despesas fixas", "despesas"), ("= Lucro", "lucro"), ("(−) Retiradas", "retiradas"),
              ("= Ficou na empresa", "caixa")]


def pct(v, casas=0):
    return "—" if v is None else f"{v * 100:.{casas}f}%".replace(".", ",")


def xl_formato(coluna, serie):
    """Formato numérico do Excel pela coluna: %, inteiro ou R$ (o resto dos números é dinheiro)."""
    if not pd.api.types.is_numeric_dtype(serie) or pd.api.types.is_bool_dtype(serie):
        return None
    nome = str(coluna).lower()
    if any(k in nome for k in XL_PCT):
        return "0.0%"
    if "proposta" in nome:
        return "0"
    if any(k in nome for k in XL_INTEIRO):
        return "#,##0"
    return '"R$" #,##0.00;[Red]-"R$" #,##0.00'


def df_texto(df):
    """Tabela pronta para o PDF: mesmos nomes de coluna e formatos (R$, %, inteiro, data) do Excel, como texto."""
    d = df.rename(columns=lambda c: XL_NOMES.get(c, str(c).replace("_", " ").capitalize() if "_" in str(c) else c))
    out = pd.DataFrame(index=d.index)
    for col in d.columns:
        serie = d[col]
        if pd.api.types.is_bool_dtype(serie):
            out[col] = serie.map({True: "Sim", False: "Não"})
            continue
        fmt = xl_formato(col, serie)

        def f(v, fmt=fmt):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return ""
            if hasattr(v, "strftime"):
                return v.strftime("%d/%m/%Y")
            if fmt == "0.0%":
                return pct(v, 1)
            if fmt in ("0", "#,##0"):
                return f"{v:,.0f}".replace(",", ".")
            if fmt:
                return fmt_brl(v)
            return str(v)
        out[col] = serie.apply(f)
    return out


def periodo(preset, comparar, hoje, ini_c=None, fim_c=None):
    """Datas e rótulos do período, iguais aos da tela Relatórios."""
    preset = preset if preset in rc.PERIODOS else "Últimos 6 meses"
    comparar = comparar if comparar in COMPARAR else COMPARAR[0]
    ini, fim = rc.intervalo(preset, hoje, ini_c, fim_c)
    anterior = comparar == COMPARAR[0]
    cini, cfim = rc.periodo_anterior(ini, fim) if anterior else rc.mesmo_periodo_ano_passado(ini, fim)
    rot, rot_comp = rc.rotulo_periodo(ini, fim), rc.rotulo_periodo(cini, cfim)
    ini, fim, cini, cfim, cortado = rc.ate_hoje(ini, fim, cini, cfim, hoje)
    if cortado:
        rot, rot_comp = f"{rot} até {fim:%d/%m}", f"{rot_comp} até {cfim:%d/%m}"
    return {"ini": ini, "fim": fim, "cini": cini, "cfim": cfim, "rot": rot, "rot_comp": rot_comp,
            "curto": "o período anterior" if anterior else "o mesmo período do ano passado"}


def delta_texto(atual, comp, base):
    """'+12% que o período anterior' (texto puro, para o PDF)."""
    if comp is None or atual is None:
        return "sem base para comparar"
    v = rc.variacao(atual, comp)
    if v is None:
        return "sem base para comparar"
    if abs(v) < 0.005:
        return f"igual a {base}"
    return f'{"+" if v > 0 else "-"}{pct(abs(v))} que {base}'


def exportacao(mov, propostas, clientes, p, hoje):
    """Resumo e tabelas do relatório (as mesmas do Excel e do PDF da tela Relatórios)."""
    ini, fim, cini, cfim, rot, rot_comp = p["ini"], p["fim"], p["cini"], p["cfim"], p["rot"], p["rot_comp"]
    exp = {}
    # Resultado
    a, c = rc.resultado(mov, ini, fim), rc.resultado(mov, cini, cfim)
    cat_e, cat_s = rc.por_categoria(mov, ini, fim, "entra"), rc.por_categoria(mov, ini, fim, "sai")
    pr = rc.propostas_periodo(propostas, ini, fim)
    cl = rc.clientes_periodo(propostas, clientes, ini, fim)
    decididas = pr["fechadas"] + pr["recusadas"]
    voltam_n = int(round((cl["recompra"] or 0) * cl["clientes_base"]))
    exp["_resumo"] = [
        ("Lucro", fmt_brl(a["lucro"]), f'margem de {pct(a["margem"])}' if a["margem"] is not None else "lucro ÷ faturamento"),
        ("Faturamento", fmt_brl(a["faturamento"]), delta_texto(a["faturamento"], c["faturamento"], p["curto"])),
        ("Taxa de fechamento", pct(pr["conversao"]),
         f'{pr["fechadas"]} de {decididas} propostas' if decididas else "nenhuma proposta respondida"),
        ("Clientes que voltam", pct(cl["recompra"]),
         f'{voltam_n} de {cl["clientes_base"]}' if cl["clientes_base"] else "nenhum trabalho fechado ainda"),
        ("Gastos da empresa", fmt_brl(a["custos"] + a["despesas"]), "sem as retiradas"),
        ("Retiradas", fmt_brl(a["retiradas"]), "pró-labore"),
        ("Propostas feitas", str(pr["enviadas"]), fmt_brl(pr["valor_enviado"])),
        ("Clientes atendidas", str(cl["atendidas"]), f'{cl["novas"]} novas · {cl["voltaram"]} voltaram')]
    serie = rc.serie_mensal(mov, ini, fim)
    exp["Resultado mês a mês"] = serie.drop(columns=["ano", "m"]).rename(columns={
        "mes": "Mês", "faturamento": "Faturamento", "custos": "Custos diretos", "despesas": "Despesas",
        "lucro": "Lucro", "retiradas": "Retiradas"})
    exp["Demonstrativo"] = pd.DataFrame([{"Linha": r, rot: a[k], rot_comp: c[k]} for r, k in LINHAS_DRE])
    exp["Receitas por categoria"] = cat_e.rename(columns={"categoria": "Categoria", "valor": "Valor"})
    exp["Gastos por categoria"] = cat_s.rename(columns={"categoria": "Categoria", "valor": "Valor"})
    # Clientes
    if not cl["origem"].empty:   # no cadastro "Cliente" quer dizer indicação de outra cliente
        cl["origem"] = cl["origem"].assign(origem=cl["origem"]["origem"].replace({"Cliente": "Indicação de cliente"}))
    exp["Clientes"] = cl["ranking"].rename(columns={"cliente": "Cliente", "trabalhos": "Trabalhos", "valor": "Valor fechado",
                                                     "primeira_vez": "Primeira vez no período"})
    exp["Origem das clientes"] = cl["origem"].rename(columns={"origem": "Origem", "clientes": "Clientes",
                                                              "trabalhos": "Trabalhos", "valor": "Valor fechado"})
    # Propostas
    exp["Propostas por tipo"] = rc.propostas_por_tipo(propostas, ini, fim)
    exp["Propostas por mês"] = rc.propostas_mensal(propostas, ini, fim)
    # Trabalhos
    t = rc.lucro_por_trabalho(mov, propostas, ini, fim)
    if not t.empty:
        exp["Lucro por trabalho"] = t
    # Próximos meses
    faixas, _atrasados = rc.agenda_pendente(mov, hoje)
    exp["A receber e a pagar"] = faixas.rename(columns={"faixa": "Vencimento", "a_receber": "A receber", "a_pagar": "A pagar"})
    exp["Propostas aguardando"] = rc.propostas_aguardando(propostas, hoje)
    return exp


def carregar(db):
    """(movimentos, propostas, clientes) da conta, como a tela Relatórios carrega."""
    fin = db.get_financeiro()
    if fin is not None and len(fin) >= 1000:   # get_financeiro() traz no máximo 1.000 transações
        fin = db.get_financeiro(limit=200000, force_reload=True)
    try:
        propostas = db.get_propostas()
    except Exception:
        propostas = pd.DataFrame()
    try:
        clientes = db.get_clientes()
    except Exception:
        clientes = pd.DataFrame()
    return rc.movimentos_rel(fin if fin is not None else pd.DataFrame()), propostas, clientes


def pdf(exp, p, perfil=None):
    from utils.relatorio_pdf import gerar_pdf
    perfil = perfil or {}
    conta = perfil.get("empresa") or perfil.get("nome") or ""
    tabelas = {n: df_texto(df) for n, df in exp.items() if isinstance(df, pd.DataFrame) and not df.empty}
    return gerar_pdf("Relatório do negócio", f'{p["rot"]} · comparado com {p["rot_comp"]}', conta,
                     exp.get("_resumo", []), tabelas, perfil=perfil)


__all__ = ["COMPARAR", "carregar", "df_texto", "exportacao", "pdf", "periodo", "timedelta"]
