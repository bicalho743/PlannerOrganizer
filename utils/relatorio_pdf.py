"""
PDF da tela Relatórios ("Baixar PDF"): capa com o período, os números principais e as tabelas de cada aba,
já formatadas como texto (R$, %, datas) por pages/relatorios.py. Usa só o reportlab (já no requirements).
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0D1B2A")
GOLD = colors.HexColor("#C9A84C")
GOLD_DK = colors.HexColor("#9C7A22")
CREME = colors.HexColor("#F8F6F1")
CINZA = colors.HexColor("#5B6B80")
BORDA = colors.HexColor("#E7E2D6")

_ST = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=8, textColor=GOLD_DK, leading=10),
    "titulo": ParagraphStyle("titulo", fontName="Times-Bold", fontSize=24, textColor=NAVY, leading=28, spaceAfter=2),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=9.5, textColor=CINZA, leading=13),
    "secao": ParagraphStyle("secao", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY, leading=14,
                            spaceBefore=12, spaceAfter=6),
    "cel": ParagraphStyle("cel", fontName="Helvetica", fontSize=8, textColor=NAVY, leading=10),
    "cab": ParagraphStyle("cab", fontName="Helvetica-Bold", fontSize=7.5, textColor=colors.white, leading=9),
    "kr": ParagraphStyle("kr", fontName="Helvetica-Bold", fontSize=7, textColor=CINZA, leading=9),
    "kv": ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY, leading=17),
    "ks": ParagraphStyle("ks", fontName="Helvetica", fontSize=7.5, textColor=CINZA, leading=9.5),
    "rod": ParagraphStyle("rod", fontName="Helvetica", fontSize=7.5, textColor=CINZA, leading=10),
}


def _agora():
    from utils.visual import agora
    return agora()


def _p(txt, st):
    from xml.sax.saxutils import escape
    return Paragraph(escape(str(txt if txt is not None else "")), _ST[st])


def gerar_pdf(titulo, periodo, conta, resumo, tabelas, max_linhas=40):
    """resumo: [(rótulo, valor, detalhe)]; tabelas: {nome: DataFrame já formatado como texto}. Devolve bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=titulo, author="Planner Organiza")
    largura = A4[0] - 32 * mm
    hist = [_p("COMO O SEU NEGÓCIO ESTÁ INDO", "eyebrow"), Spacer(1, 3), _p(titulo, "titulo"),
            _p(" · ".join(x for x in (conta, periodo) if x), "sub"), Spacer(1, 10)]

    if resumo:
        cel = [[_p(r.upper(), "kr"), Spacer(1, 2), _p(v, "kv"), _p(d or "", "ks")] for r, v, d in resumo]
        por_linha = 4
        linhas = [cel[i:i + por_linha] for i in range(0, len(cel), por_linha)]
        for ln in linhas:
            ln += [""] * (por_linha - len(ln))
            t = Table([ln], colWidths=[largura / por_linha] * por_linha)
            t.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.6, BORDA), ("INNERGRID", (0, 0), (-1, -1), 0.6, BORDA),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
            hist += [t, Spacer(1, 6)]

    for nome, df in tabelas.items():
        if df is None or df.empty:
            continue
        cols = [str(c) for c in df.columns]
        dados = [[_p(c, "cab") for c in cols]]
        for _, r in df.head(max_linhas).iterrows():
            dados.append([_p(v, "cel") for v in r.tolist()])
        t = Table(dados, colWidths=[largura / len(cols)] * len(cols), repeatRows=1)
        estilo = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("LINEBELOW", (0, 0), (-1, 0), 1.2, GOLD),
                  ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDA), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                  ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                  ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        for i in range(2, len(dados), 2):
            estilo.append(("BACKGROUND", (0, i), (-1, i), CREME))
        t.setStyle(TableStyle(estilo))
        bloco = [_p(nome, "secao"), t]
        if len(df) > max_linhas:
            bloco.append(_p(f"Mostrando {max_linhas} de {len(df)} linhas. A planilha em Excel traz todas.", "rod"))
        hist.append(KeepTogether(bloco) if len(dados) < 18 else bloco[0])
        if len(dados) >= 18:
            hist += bloco[1:]

    hist += [Spacer(1, 14), _p(f"Gerado em {_agora():%d/%m/%Y %H:%M} pelo Planner Organiza. Relatório gerencial, "
                               "pela data em que o dinheiro entrou ou saiu. Não substitui a contabilidade: o Planner "
                               "organiza, mas não substitui o seu contador.", "rod")]
    doc.build(hist)
    return buf.getvalue()
