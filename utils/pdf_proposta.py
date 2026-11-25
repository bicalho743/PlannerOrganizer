"""
PDF da proposta para a cliente (modelo aprovado em 25/11/2026).

Uma cor só (a cor principal da marca da organizer, em Perfil e marca), sem o dourado do Planner:
topo com logo (ou iniciais), nome do negócio, Nº da proposta, data e validade; "Proposta para
<cliente>"; serviço, prazo e início; descrição; o que está incluído; investimento com o sinal e o
restante; condições; rodapé com contatos e o botão "Aprovar pelo WhatsApp" (link para o WhatsApp
da organizer, com a mensagem pronta).

Os outros documentos (fechamento, relatórios, venda) continuam em utils/pdf_generator_v2.py.
"""
import re
import urllib.parse
from datetime import date, datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from utils.pdf_generator_v2 import _hex, _logo, _misturar, com_marca

W, H = A4
M = 20 * mm                     # margem
CW = W - 2 * M                  # largura do conteúdo
TX = colors.HexColor("#1F2A37")
MU = colors.HexColor("#6B7280")
LINHA = colors.HexColor("#E5E7EB")
VALIDADE_DIAS = 10

CONDICOES_PADRAO = [
    "O sinal reserva a data e é pago por Pix na aprovação.",
    "Os valores já incluem todos os custos do serviço.",
    "Produtos organizadores não estão incluídos; posso indicar e orçar à parte.",
    "Organização de documentos não está incluída.",
]


def brl(v):
    return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def telefone_fmt(t):
    d = re.sub(r"\D", "", str(t or ""))
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return str(t or "").strip()


def link_whatsapp(t, texto):
    d = re.sub(r"\D", "", str(t or ""))
    if len(d) < 10:
        return ""
    if not d.startswith("55"):
        d = "55" + d
    return f"https://wa.me/{d}?text={urllib.parse.quote(texto)}"


def condicoes(texto):
    """Lista de condições: o texto do perfil (uma por linha, sem a numeração) ou o padrão."""
    linhas = [re.sub(r"^\s*(\d+[.)-]|[-•*])\s*", "", x).strip() for x in str(texto or "").splitlines()]
    linhas = [x for x in linhas if x]
    antigo = any("Não incluido produtos" in x or "Pagamento sinal, na reserva" in x for x in linhas)
    return CONDICOES_PADRAO if (not linhas or antigo) else linhas


def _data(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.fromisoformat(str(v)[:10]).date()
    except Exception:
        return None


def _lum(c):
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c.red) + 0.7152 * ch(c.green) + 0.0722 * ch(c.blue)


def _contraste(c1, c2):
    l1, l2 = sorted((_lum(c1), _lum(c2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def cores_legiveis(cor):
    """(cor para texto e linhas sobre o branco, cor do texto sobre a cor). Escurece cores claras até
    ficarem legíveis no branco (4,5:1) e usa texto escuro sobre fundos claros."""
    texto = cor
    for _ in range(12):
        if _contraste(texto, colors.white) >= 4.5:
            break
        texto = _misturar(texto, colors.black, 0.12)
    sobre = colors.white if _contraste(cor, colors.white) >= 3.0 else TX
    return texto, sobre


def _iniciais(nome):
    p = [x for x in re.split(r"\s+", str(nome or "").strip()) if x and x[0].isalpha()]
    return ((p[0][0] + (p[1][0] if len(p) > 1 else "")) if p else "PO").upper()


class _Pagina:
    def __init__(self, c, cor, perfil, numero):
        self.fundo = cor                                  # cor da marca, como ela escolheu (logo, botão, faixa)
        self.cor, self.sobre = cores_legiveis(cor)        # versão legível para textos; texto sobre a cor
        self.c, self.perfil, self.numero = c, perfil, numero
        self.claro = _misturar(cor, colors.white, 0.92)
        self.y = H - M

    def falta(self, h):
        """Quebra a página se não houver espaço para h (reservando o rodapé)."""
        if self.y - h < 30 * mm:
            self.c.showPage()
            self.c.setFillColor(MU); self.c.setFont("Helvetica", 8)
            self.c.drawRightString(W - M, H - 12 * mm, f"Proposta Nº {self.numero} · continuação")
            self.y = H - 20 * mm

    def titulo_secao(self, txt):
        self.falta(16 * mm)
        self.y -= 9 * mm
        self.c.setFillColor(self.cor); self.c.setFont("Helvetica-Bold", 8.5)
        self.c.drawString(M, self.y, txt.upper())
        self.y -= 5 * mm

    def texto(self, txt, tam=10, cor=TX, fonte="Helvetica", larg=None, x=None, entre=4.6 * mm):
        larg = larg or CW
        for ln in simpleSplit(str(txt), fonte, tam, larg):
            self.falta(entre)
            self.c.setFillColor(cor); self.c.setFont(fonte, tam)
            self.c.drawString(x if x is not None else M, self.y, ln)
            self.y -= entre


def _topo(pg, dados, perfil):
    c, cor = pg.c, pg.cor
    empresa = (perfil.get("empresa") or perfil.get("nome") or "Personal Organizer").strip()
    sub = " · ".join(x for x in [(perfil.get("cargo") or "Personal organizer").strip(),
                                 (perfil.get("instagram") or "").strip()] if x)
    topo = H - 16 * mm
    logo = _logo(perfil)
    if logo:
        c.drawImage(logo, M, topo - 14 * mm, 16 * mm, 16 * mm, preserveAspectRatio=True, mask="auto")
    else:
        c.setFillColor(pg.fundo); c.roundRect(M, topo - 14 * mm, 16 * mm, 16 * mm, 4 * mm, fill=1, stroke=0)
        c.setFillColor(pg.sobre); c.setFont("Times-Roman", 17)
        c.drawCentredString(M + 8 * mm, topo - 8.3 * mm, _iniciais(empresa))
    c.setFillColor(TX); c.setFont("Times-Roman", 19)
    c.drawString(M + 20 * mm, topo - 5 * mm, empresa[:42])
    c.setFillColor(MU); c.setFont("Helvetica", 8.5)
    c.drawString(M + 20 * mm, topo - 10.5 * mm, sub[:70])
    emitida = _data(dados.get("data")) or date.today()
    validade = emitida + timedelta(days=VALIDADE_DIAS)
    c.setFont("Helvetica", 8); c.drawRightString(W - M, topo - 1 * mm, "Proposta de Serviço")
    c.setFillColor(cor); c.setFont("Helvetica-Bold", 14)
    c.drawRightString(W - M, topo - 7 * mm, f"Nº {int(dados['numero']):03d}" if str(dados.get("numero", "")).isdigit()
                      else f"Nº {dados.get('numero', '')}")
    c.setFillColor(MU); c.setFont("Helvetica", 8)
    c.drawRightString(W - M, topo - 12 * mm, f"{emitida:%d/%m/%Y} · válida até {validade:%d/%m/%Y}")
    c.setStrokeColor(pg.fundo); c.setLineWidth(2.2)
    c.line(0, topo - 19 * mm, W, topo - 19 * mm)
    pg.y = topo - 33 * mm


def _cabecalho_cliente(pg, dados):
    c = pg.c
    c.setFont("Times-Roman", 24)
    pre = "Proposta para "
    c.setFillColor(TX); c.drawString(M, pg.y, pre)
    c.setFillColor(pg.cor); c.drawString(M + c.stringWidth(pre, "Times-Roman", 24), pg.y,
                                        str(dados.get("cliente") or "você")[:40])
    pg.y -= 7 * mm
    if dados.get("subtitulo"):
        pg.texto(dados["subtitulo"], 10.5, MU)
    pg.y -= 3 * mm
    cards = [("SERVIÇO", dados.get("tipo") or "Organização"), ("PRAZO", dados.get("prazo") or "a combinar"),
             ("INÍCIO", dados.get("inicio") or "a combinar")]
    gap, h = 4 * mm, 14 * mm
    w = (CW - 2 * gap) / 3
    for i, (rot, val) in enumerate(cards):
        x = M + i * (w + gap)
        c.setFillColor(pg.claro); c.roundRect(x, pg.y - h, w, h, 3 * mm, fill=1, stroke=0)
        c.setFillColor(MU); c.setFont("Helvetica-Bold", 7); c.drawString(x + 4 * mm, pg.y - 5 * mm, rot)
        c.setFillColor(TX); c.setFont("Helvetica-Bold", 10.5)
        c.drawString(x + 4 * mm, pg.y - 10.5 * mm, simpleSplit(str(val), "Helvetica-Bold", 10.5, w - 8 * mm)[0])
    pg.y -= h


def ambientes_da_descricao(desc):
    """'Pós-mudança: Cozinha, Sala (2). Prazo...' → [('Cozinha', '1 ambiente'), ('Sala', '2 ambientes')]."""
    m = re.match(r"^[^:.]{3,40}(?::| de )\s*([^.]+)\.", str(desc or ""))
    if not m:
        return []
    saida = []
    for parte in m.group(1).split(","):
        parte = parte.strip()
        q = re.search(r"\((\d+)\)$", parte)
        n = int(q.group(1)) if q else 1
        nome = re.sub(r"\s*\(\d+\)$", "", parte).strip()
        if nome:
            saida.append((nome, f"{n} ambiente{'s' if n > 1 else ''}"))
    return saida if len(saida) >= 1 else []


def _incluido(pg, dados):
    itens = dados.get("itens") or []
    amb = ambientes_da_descricao(dados.get("descricao")) if len(itens) <= 1 else []
    if amb:   # proposta montada por ambientes: lista um por linha (o valor fica no Investimento)
        itens = [(n, d, 0) for n, d in amb] + ([("Equipe", dados["equipe"], 0)] if dados.get("equipe") else [])
    elif dados.get("descricao"):
        pg.titulo_secao("Descrição do serviço")
        pg.texto(dados["descricao"], 10)
    if not itens:
        return
    pg.titulo_secao("O que está incluído")
    com_valor = len(itens) > 1
    for nome, detalhe, valor in itens:
        pg.falta(9 * mm)
        pg.y -= 1.5 * mm
        pg.c.setFillColor(TX); pg.c.setFont("Helvetica", 10)
        pg.c.drawString(M, pg.y, simpleSplit(str(nome), "Helvetica", 10, CW * 0.68)[0])
        direita = brl(valor) if (com_valor and valor) else (detalhe or "")
        pg.c.setFillColor(MU); pg.c.drawRightString(W - M, pg.y, str(direita))
        pg.y -= 3.5 * mm
        pg.c.setStrokeColor(LINHA); pg.c.setLineWidth(0.6); pg.c.line(M, pg.y, W - M, pg.y)
        pg.y -= 2.5 * mm


def _investimento(pg, dados):
    total = float(dados.get("total") or 0)
    sinal = float(dados.get("sinal") or 0)
    pago = bool(dados.get("sinal_pago"))
    linhas = [("Serviço completo", brl(total))]
    if sinal > 0:
        pct = f" ({sinal / total * 100:.0f}%)" if total else ""
        linhas.append(("Sinal já pago" + pct if pago else "Sinal na aprovação" + pct, brl(sinal)))
        linhas.append(("Restante, no último dia" if not pago else "Saldo a pagar", brl(max(total - sinal, 0))))
    h = (len(linhas) * 6.5 + 20) * mm
    pg.titulo_secao("Investimento")
    pg.falta(h + 2 * mm)
    c, top = pg.c, pg.y + 1 * mm
    c.setStrokeColor(pg.cor); c.setLineWidth(1.4)
    c.roundRect(M, top - h, CW, h, 4 * mm, fill=0, stroke=1)
    y = top - 7 * mm
    for rot, val in linhas:
        c.setFillColor(MU); c.setFont("Helvetica", 9.5)
        c.drawString(M + 6 * mm, y, rot); c.drawRightString(W - M - 6 * mm, y, val)
        y -= 6.5 * mm
    c.setStrokeColor(LINHA); c.setLineWidth(0.6); c.line(M + 6 * mm, y + 2.5 * mm, W - M - 6 * mm, y + 2.5 * mm)
    c.setFillColor(TX); c.setFont("Helvetica-Bold", 11); c.drawString(M + 6 * mm, y - 5 * mm, "Total")
    c.setFillColor(pg.cor); c.setFont("Helvetica-Bold", 19); c.drawRightString(W - M - 6 * mm, y - 5.5 * mm, brl(total))
    pg.y = top - h


def _condicoes(pg, dados):
    pg.titulo_secao("Condições")
    for item in dados.get("condicoes") or CONDICOES_PADRAO:
        linhas = simpleSplit(item, "Helvetica", 9.5, CW - 5 * mm)
        pg.falta(len(linhas) * 4.4 * mm + 1 * mm)
        pg.c.setFillColor(pg.cor); pg.c.circle(M + 1.2 * mm, pg.y + 1.2 * mm, 0.8 * mm, fill=1, stroke=0)
        for ln in linhas:
            pg.c.setFillColor(TX); pg.c.setFont("Helvetica", 9.5); pg.c.drawString(M + 5 * mm, pg.y, ln)
            pg.y -= 4.4 * mm
        pg.y -= 1 * mm


def _rodape(pg, dados, perfil):
    c, h = pg.c, 20 * mm
    c.setFillColor(pg.claro); c.rect(0, 0, W, h, fill=1, stroke=0)
    empresa = (perfil.get("empresa") or perfil.get("nome") or "").strip()
    contatos = " · ".join(x for x in [telefone_fmt(perfil.get("telefone")), (perfil.get("email") or "").strip(),
                                       (perfil.get("instagram") or "").strip()] if x)
    c.setFillColor(pg.cor); c.setFont("Helvetica-Bold", 9.5); c.drawString(M, 12 * mm, empresa[:50])
    c.setFillColor(TX); c.setFont("Helvetica", 8.5); c.drawString(M, 7.5 * mm, contatos[:95])
    link = link_whatsapp(perfil.get("telefone"),
                         f"Olá! Quero aprovar a proposta Nº {dados.get('numero', '')}.")
    if link:
        bw, bh = 46 * mm, 9 * mm
        x, y = W - M - bw, (h - bh) / 2
        c.setFillColor(pg.fundo); c.roundRect(x, y, bw, bh, 2.5 * mm, fill=1, stroke=0)
        c.setFillColor(pg.sobre); c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(x + bw / 2, y + 3.1 * mm, "Aprovar pelo WhatsApp")
        c.linkURL(link, (x, y, x + bw, y + bh), relative=0)


@com_marca
def gerar_pdf_proposta(dados, output_path, perfil=None):
    """dados: numero, cliente, tipo, subtitulo, prazo, inicio, data, descricao, itens [(nome, detalhe, valor)],
    total, sinal, sinal_pago, condicoes."""
    perfil = perfil or {}
    cor = colors.HexColor(_hex(perfil.get("cor_principal"), "#0D1B2A"))
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(f"Proposta Nº {dados.get('numero', '')} - {dados.get('cliente', '')}")
    pg = _Pagina(c, cor, perfil, dados.get("numero", ""))
    _topo(pg, dados, perfil)
    _cabecalho_cliente(pg, dados)
    _incluido(pg, dados)
    _investimento(pg, dados)
    _condicoes(pg, dados)
    _rodape(pg, dados, perfil)
    c.save()
    return output_path
