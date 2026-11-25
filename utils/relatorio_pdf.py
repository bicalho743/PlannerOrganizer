"""
PDF da tela Relatórios ("Baixar PDF"): o Relatório do negócio (financeiro, clientes, propostas, lucro por trabalho,
a receber e a pagar), no mesmo desenho dos outros documentos (utils/pdf_docs.py): topo com logo ou iniciais e o nome
do negócio, selo "Uso interno", linha na cor da marca (versão legível, utils.pdf_proposta.cores_legiveis), cartões
claros com os números principais, tabelas leves e rodapé "Documento de uso interno".
As tabelas chegam já formatadas como texto (R$, %, datas) por pages/relatorios.py.
"""
import io
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

W, H = A4
M = 20 * mm
TX = colors.HexColor("#1F2A37")
MU = colors.HexColor("#6B7280")
LINHA = colors.HexColor("#E5E7EB")
OURO_CL = colors.HexColor("#F6EDD3")
OURO_TX = colors.HexColor("#7A5F0B")
VERMELHO = colors.HexColor("#9B2C2C")


def _agora():
    from utils.visual import agora
    return agora()


def _estilos(cor):
    return {
        "titulo": ParagraphStyle("titulo", fontName="Times-Roman", fontSize=24, textColor=TX, leading=28),
        "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=10.5, textColor=MU, leading=14),
        "secao": ParagraphStyle("secao", fontName="Helvetica-Bold", fontSize=8.5, textColor=cor, leading=11,
                                spaceBefore=14, spaceAfter=5),
        "cel": ParagraphStyle("cel", fontName="Helvetica", fontSize=8.5, textColor=TX, leading=10.5),
        "celd": ParagraphStyle("celd", fontName="Helvetica", fontSize=8.5, textColor=TX, leading=10.5, alignment=2),
        "celneg": ParagraphStyle("celneg", fontName="Helvetica", fontSize=8.5, textColor=VERMELHO, leading=10.5, alignment=2),
        "cab": ParagraphStyle("cab", fontName="Helvetica-Bold", fontSize=6.8, textColor=MU, leading=8.5),
        "cabd": ParagraphStyle("cabd", fontName="Helvetica-Bold", fontSize=6.8, textColor=MU, leading=8.5, alignment=2),
        "kr": ParagraphStyle("kr", fontName="Helvetica-Bold", fontSize=6.8, textColor=MU, leading=8.5),
        "kv": ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=13, textColor=TX, leading=16),
        "ks": ParagraphStyle("ks", fontName="Helvetica", fontSize=7.5, textColor=MU, leading=9.5),
        "rod": ParagraphStyle("rod", fontName="Helvetica", fontSize=7.5, textColor=MU, leading=10),
    }


def _seguro(txt):
    saida = []
    for ch in str(txt if txt is not None else "").replace("\u2212", "-"):
        try:
            ch.encode("cp1252")
            saida.append(ch)
        except UnicodeEncodeError:
            pass
    return "".join(saida)


def _p(txt, st):
    return Paragraph(escape(_seguro(txt)), st)


_NUM = re.compile(r"^\s*[-−+]?\s*(R\$\s*)?[-−]?[\d.,]+\s*%?\s*$")


def gerar_pdf(titulo, periodo, conta, resumo, tabelas, max_linhas=40, perfil=None):
    """resumo: [(rótulo, valor, detalhe)]; tabelas: {nome: DataFrame já formatado como texto}. Devolve bytes."""
    from utils.pdf_generator_v2 import _hex, _logo, _misturar
    from utils.pdf_proposta import _iniciais, cores_legiveis
    perfil = dict(perfil or {})
    if conta and not (perfil.get("empresa") or perfil.get("nome")):
        perfil["empresa"] = conta
    fundo = colors.HexColor(_hex(perfil.get("cor_principal"), "#0D1B2A"))
    cor, sobre = cores_legiveis(fundo)
    claro = _misturar(fundo, colors.white, 0.92)
    st = _estilos(cor)
    empresa = _seguro(perfil.get("empresa") or perfil.get("nome") or "Personal Organizer").strip()
    sub = " · ".join(x for x in [_seguro(perfil.get("cargo") or "Personal Organizer").strip(),
                                 _seguro(perfil.get("instagram") or "").strip()] if x)
    logo = _logo(perfil)
    gerado = f"{_agora():%d/%m/%Y}"

    def _rodape(c):
        c.setFillColor(claro); c.rect(0, 0, W, 20 * mm, fill=1, stroke=0)
        c.setFillColor(cor); c.setFont("Helvetica-Bold", 9.5); c.drawString(M, 12 * mm, "Documento de uso interno")
        c.setFillColor(MU); c.setFont("Helvetica", 8.5)
        c.drawString(M, 7.5 * mm, f"Gerado pelo Planner Organiza em {gerado} · não substitui a contabilidade")
        c.drawRightString(W - M, 9.5 * mm, f"Página {c.getPageNumber()}")

    def _primeira(c, doc):
        c.saveState()
        topo = H - 16 * mm
        if logo:
            c.drawImage(logo, M, topo - 14 * mm, 16 * mm, 16 * mm, preserveAspectRatio=True, mask="auto")
        else:
            c.setFillColor(fundo); c.roundRect(M, topo - 14 * mm, 16 * mm, 16 * mm, 4 * mm, fill=1, stroke=0)
            c.setFillColor(sobre); c.setFont("Times-Roman", 17)
            c.drawCentredString(M + 8 * mm, topo - 8.3 * mm, _iniciais(empresa))
        c.setFillColor(TX); c.setFont("Times-Roman", 19); c.drawString(M + 20 * mm, topo - 5 * mm, empresa[:42])
        c.setFillColor(MU); c.setFont("Helvetica", 8.5); c.drawString(M + 20 * mm, topo - 10.5 * mm, sub[:70])
        selo = "USO INTERNO"
        w = c.stringWidth(selo, "Helvetica-Bold", 7) + 6 * mm
        c.setFillColor(OURO_CL); c.roundRect(W - M - w, topo - 0.4 * mm, w, 5.2 * mm, 2.6 * mm, fill=1, stroke=0)
        c.setFillColor(OURO_TX); c.setFont("Helvetica-Bold", 7); c.drawString(W - M - w + 3 * mm, topo + 1.2 * mm, selo)
        c.setFillColor(MU); c.setFont("Helvetica", 8); c.drawRightString(W - M, topo - 5 * mm, "Relatório do negócio")
        c.setFillColor(MU); c.setFont("Helvetica", 8); c.drawRightString(W - M, topo - 10 * mm, f"Gerado em {gerado}")
        c.setStrokeColor(fundo); c.setLineWidth(2.2); c.line(0, topo - 21 * mm, W, topo - 21 * mm)
        _rodape(c)
        c.restoreState()

    def _seguintes(c, doc):
        c.saveState()
        c.setFillColor(MU); c.setFont("Helvetica", 8)
        c.drawString(M, H - 12 * mm, empresa[:50])
        c.drawRightString(W - M, H - 12 * mm, "Relatório do negócio · continuação")
        c.setStrokeColor(fundo); c.setLineWidth(1); c.line(M, H - 14.5 * mm, W - M, H - 14.5 * mm)
        _rodape(c)
        c.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=M - 6, rightMargin=M - 6, topMargin=20 * mm, bottomMargin=26 * mm,
                            title=titulo, author=empresa)
    largura = doc.width - 12   # a moldura do SimpleDocTemplate tem 6 pt de folga de cada lado
    hist = [Spacer(1, 26 * mm), _p(titulo, st["titulo"]), Spacer(1, 3), _p(periodo or "", st["sub"]), Spacer(1, 10)]

    if resumo:
        por_linha = 4
        cel = []
        for r, v, d in resumo:
            cel.append([_p(str(r).upper(), st["kr"]), Spacer(1, 2), _p(v, st["kv"]), _p(d or "", st["ks"])])
        for i in range(0, len(cel), por_linha):
            ln = cel[i:i + por_linha]
            ln += [""] * (por_linha - len(ln))
            gap = 4 * mm
            larg = (largura - gap * (por_linha - 1)) / por_linha
            linha, cols = [], []
            for j, x in enumerate(ln):
                linha.append(x)
                cols.append(larg)
                if j < por_linha - 1:
                    linha.append("")
                    cols.append(gap)
            t = Table([linha], colWidths=cols)
            estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                      ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm), ("TOPPADDING", (0, 0), (-1, -1), 3.5 * mm),
                      ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5 * mm)]
            for j, x in enumerate(ln):
                if x != "":
                    estilo += [("BACKGROUND", (2 * j, 0), (2 * j, 0), claro),
                               ("ROUNDEDCORNERS", [8, 8, 8, 8])]
            t.setStyle(TableStyle(estilo))
            hist += [t, Spacer(1, 4 * mm)]

    for nome, df in tabelas.items():
        if df is None or df.empty:
            continue
        cols = [str(c) for c in df.columns]
        amostra = df.head(max_linhas)
        direita = [j > 0 and all(_NUM.match(str(v)) or str(v).strip() in ("", "—", "-") for v in amostra.iloc[:, j])
                   for j in range(len(cols))]
        dados = [[_p(c.upper(), st["cabd"] if direita[j] else st["cab"]) for j, c in enumerate(cols)]]
        for _, r in amostra.iterrows():
            linha = []
            for j, v in enumerate(r.tolist()):
                txt = str(v)
                neg = direita[j] and txt.strip().startswith(("-", "−"))
                linha.append(_p(txt, st["celneg"] if neg else (st["celd"] if direita[j] else st["cel"])))
            dados.append(linha)
        larg0 = largura * (0.34 if len(cols) > 2 else 0.5)
        resto = (largura - larg0) / max(len(cols) - 1, 1)
        t = Table(dados, colWidths=[larg0] + [resto] * (len(cols) - 1), repeatRows=1)
        t.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, TX), ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
        bloco = [_p(str(nome).upper(), st["secao"]), t]
        if len(df) > max_linhas:
            bloco.append(_p(f"Mostrando {max_linhas} de {len(df)} linhas. A planilha em Excel traz todas.", st["rod"]))
        if len(dados) < 18:
            hist.append(KeepTogether(bloco))
        else:
            hist += bloco

    hist += [Spacer(1, 12), _p("Relatório gerencial, pela data em que o dinheiro entrou ou saiu. O Planner organiza, "
                               "mas não substitui o seu contador.", st["rod"])]
    doc.build(hist, onFirstPage=_primeira, onLaterPages=_seguintes)
    return buf.getvalue()
