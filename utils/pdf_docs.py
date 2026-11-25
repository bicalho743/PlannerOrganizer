"""
Documentos em PDF no desenho novo (aprovado em 25/11/2026), na cor da marca de cada organizer.

Mesma família da proposta (utils/pdf_proposta.py): página branca, topo com logo ou iniciais, nome do negócio,
tipo do documento e Nº, título serifado, cartões, tabelas leves e rodapé. A cor principal do Perfil é usada
sempre na versão legível (utils.pdf_proposta.cores_legiveis): cores claras escurecem até 4,5:1 sobre o branco
e o texto sobre a cor muda para escuro quando a cor é clara.

- fechamento(dados, caminho, perfil)    → Fechamento do Serviço (para a cliente)
- interno(dados, caminho, perfil)       → Relatório Interno (uso interno)
- fornecedores(dados, caminho, perfil)  → Relatório de Fornecedores (uso interno)
- venda(venda, cliente, itens_df, caminho, perfil) → Produtos / venda (recibo para a cliente)

Os geradores antigos de utils/pdf_generator_v2.py chamam estes, então o site e o app (API) saem iguais,
inclusive para propostas antigas. Textos livres antigos passam por limpar_texto() (símbolos que a fonte do
PDF não tem e linhas de conta soltas, como "2880 - primeiro", não vão para a cliente).
"""
import re
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from utils.pdf_generator_v2 import _hex, _logo, _misturar
from utils.pdf_proposta import (CW, H, LINHA, M, MU, TX, W, _data, _iniciais, brl, cores_legiveis, link_whatsapp,
                                telefone_fmt)

VERDE = colors.HexColor("#2F6B4F")
VERDE_CL = colors.HexColor("#E3F1E8")
VERMELHO = colors.HexColor("#9B2C2C")
OURO_CL = colors.HexColor("#F6EDD3")
OURO_TX = colors.HexColor("#7A5F0B")
RODAPE_H = 20 * mm


# ───────────────────────────── texto ─────────────────────────────

def _cabe(ch):
    try:
        ch.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


_NOTA = re.compile(r"^\s*[\d.,]+\s*([-=:x*/+]\s*[\w\s]{0,14})?\s*$", re.I)


def limpar_texto(txt):
    """Linhas de um texto livre prontas para o PDF: sem símbolos que a fonte não tem (■, emojis), sem linhas
    que são só contas ("2880 - primeiro", "5624") e sem marcadores repetidos ("- - banheiro")."""
    saida = []
    for ln in str(txt or "").replace("\r", "").split("\n"):
        ln = "".join(ch for ch in ln if _cabe(ch)).strip()
        ln = re.sub(r"^([-•*–]\s*)+", "", ln).strip(" -–")
        if not ln or _NOTA.match(ln):
            continue
        saida.append(ln[0].upper() + ln[1:])
    return saida


def _seguro(txt):
    return "".join(ch for ch in str(txt or "").replace("\u2212", "-") if _cabe(ch))


def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


# ───────────────────────────── página ─────────────────────────────

class Doc:
    """Uma folha A4 com a marca: topo, títulos, cartões, tabelas, caixas e rodapé, quebrando página quando
    precisa (o topo se repete em versão curta nas páginas seguintes)."""

    def __init__(self, caminho, perfil, tipo, numero="", data_txt="", interno=False, titulo_arquivo=""):
        self.perfil = perfil or {}
        base = colors.HexColor(_hex(self.perfil.get("cor_principal"), "#0D1B2A"))
        self.fundo = base
        self.cor, self.sobre = cores_legiveis(base)
        self.claro = _misturar(base, colors.white, 0.92)
        self.tipo, self.numero, self.data_txt, self.interno = tipo, numero, data_txt, interno
        self.c = canvas.Canvas(caminho, pagesize=A4)
        self.c.setTitle(titulo_arquivo or tipo)
        self.pagina = 1
        self._topo()

    # topo e quebra de página
    def _topo(self):
        c, p = self.c, self.perfil
        empresa = _seguro(p.get("empresa") or p.get("nome") or "Personal Organizer").strip()
        sub = " · ".join(x for x in [_seguro(p.get("cargo") or "Personal Organizer").strip(),
                                     _seguro(p.get("instagram") or "").strip()] if x)
        topo = H - 16 * mm
        logo = _logo(p)
        if logo:
            c.drawImage(logo, M, topo - 14 * mm, 16 * mm, 16 * mm, preserveAspectRatio=True, mask="auto")
        else:
            c.setFillColor(self.fundo); c.roundRect(M, topo - 14 * mm, 16 * mm, 16 * mm, 4 * mm, fill=1, stroke=0)
            c.setFillColor(self.sobre); c.setFont("Times-Roman", 17)
            c.drawCentredString(M + 8 * mm, topo - 8.3 * mm, _iniciais(empresa))
        c.setFillColor(TX); c.setFont("Times-Roman", 19); c.drawString(M + 20 * mm, topo - 5 * mm, empresa[:42])
        c.setFillColor(MU); c.setFont("Helvetica", 8.5); c.drawString(M + 20 * mm, topo - 10.5 * mm, sub[:70])
        y = topo - 1 * mm
        if self.interno:
            self._selo("USO INTERNO", W - M, y + 1.2 * mm, OURO_CL, OURO_TX, direita=True)
            y -= 6 * mm
        c.setFillColor(MU); c.setFont("Helvetica", 8); c.drawRightString(W - M, y, self.tipo)
        if self.numero not in (None, ""):
            n = f"Nº {int(self.numero):03d}" if str(self.numero).isdigit() else f"Nº {self.numero}"
            c.setFillColor(self.cor); c.setFont("Helvetica-Bold", 14); c.drawRightString(W - M, y - 6 * mm, n)
        if self.data_txt:
            c.setFillColor(MU); c.setFont("Helvetica", 8); c.drawRightString(W - M, y - 11 * mm, self.data_txt)
        c.setStrokeColor(self.fundo); c.setLineWidth(2.2)
        linha = topo - (23 if self.interno else 19) * mm
        c.line(0, linha, W, linha)
        self.y = linha - 14 * mm

    def falta(self, h):
        if self.y - h < RODAPE_H + 8 * mm:
            self.rodape()
            self.c.showPage()
            self.pagina += 1
            self.c.setFillColor(MU); self.c.setFont("Helvetica", 8)
            self.c.drawRightString(W - M, H - 12 * mm, f"{self.tipo} · continuação")
            self.y = H - 22 * mm

    # peças
    def _selo(self, txt, x, y, fundo, cor, direita=False, tam=7):
        w = self.c.stringWidth(txt, "Helvetica-Bold", tam) + 6 * mm
        x0 = x - w if direita else x
        self.c.setFillColor(fundo); self.c.roundRect(x0, y - 1.6 * mm, w, 5.2 * mm, 2.6 * mm, fill=1, stroke=0)
        self.c.setFillColor(cor); self.c.setFont("Helvetica-Bold", tam); self.c.drawString(x0 + 3 * mm, y, txt)
        return w

    def titulo(self, antes, destaque="", depois=""):
        c, tam = self.c, 24
        x = M
        for parte, cor in ((antes, TX), (destaque, self.cor), (depois, TX)):
            parte = _seguro(parte)
            if parte:
                c.setFillColor(cor); c.setFont("Times-Roman", tam); c.drawString(x, self.y, parte)
                x += c.stringWidth(parte, "Times-Roman", tam)
        self.y -= 7 * mm

    def linha_fina(self, txt):
        for ln in simpleSplit(_seguro(txt), "Helvetica", 10.5, CW):
            self.c.setFillColor(MU); self.c.setFont("Helvetica", 10.5); self.c.drawString(M, self.y, ln)
            self.y -= 5 * mm
        self.y -= 2 * mm

    def cartoes(self, itens):
        """itens: [(rótulo, valor, estilo)] com estilo '' | 'verde' | 'escuro' | 'grande'."""
        if not itens:
            return
        gap, h = 4 * mm, 15 * mm
        w = (CW - gap * (len(itens) - 1)) / len(itens)
        self.falta(h + 4 * mm)
        for i, (rot, val, est) in enumerate(itens):
            x = M + i * (w + gap)
            fundo = {"verde": VERDE_CL, "escuro": colors.HexColor("#0D1B2A")}.get(est, self.claro)
            self.c.setFillColor(fundo); self.c.roundRect(x, self.y - h, w, h, 3 * mm, fill=1, stroke=0)
            self.c.setFillColor(colors.HexColor("#C9A84C") if est == "escuro" else MU)
            self.c.setFont("Helvetica-Bold", 6.8); self.c.drawString(x + 4 * mm, self.y - 5 * mm, rot.upper())
            cor_v = {"verde": VERDE, "escuro": colors.white}.get(est, TX)
            tam = 13 if est in ("verde", "escuro", "grande") else 10.5
            val = _seguro(val) if val else "—"
            while tam > 8 and self.c.stringWidth(val, "Helvetica-Bold", tam) > w - 8 * mm:
                tam -= 0.5
            val = simpleSplit(val, "Helvetica-Bold", tam, w - 8 * mm)[0]
            self.c.setFillColor(cor_v); self.c.setFont("Helvetica-Bold", tam)
            self.c.drawString(x + 4 * mm, self.y - (11.2 if tam > 11 else 10.5) * mm, val)
        self.y -= h + 2 * mm

    def secao(self, txt):
        self.falta(16 * mm)
        self.y -= 6 * mm
        self.c.setFillColor(self.cor); self.c.setFont("Helvetica-Bold", 8.5); self.c.drawString(M, self.y, txt.upper())
        self.y -= 5 * mm

    def etiquetas(self, nomes):
        x, h = M, 7 * mm
        self.falta(h + 2 * mm)
        for n in nomes:
            n = _seguro(n)[:40]
            w = self.c.stringWidth(n, "Helvetica-Bold", 9) + 8 * mm
            if x + w > W - M:
                x = M
                self.y -= h + 2 * mm
                self.falta(h + 2 * mm)
            self.c.setFillColor(self.claro); self.c.roundRect(x, self.y - h + 2 * mm, w, h, 3.5 * mm, fill=1, stroke=0)
            self.c.setFillColor(TX); self.c.setFont("Helvetica-Bold", 9); self.c.drawString(x + 4 * mm, self.y - 2.6 * mm, n)
            x += w + 2.5 * mm
        self.y -= h + 1 * mm

    def marcadores(self, linhas, tam=9.5, junto=False):
        if junto:
            n = sum(len(simpleSplit(_seguro(i), "Helvetica", tam, CW - 5 * mm)) for i in linhas)
            self.falta(n * 4.4 * mm + len(linhas) * 0.8 * mm)
        for item in linhas:
            partes = simpleSplit(_seguro(item), "Helvetica", tam, CW - 5 * mm)
            self.falta(len(partes) * 4.4 * mm + 1 * mm)
            self.c.setFillColor(self.cor); self.c.circle(M + 1.2 * mm, self.y + 1.2 * mm, 0.8 * mm, fill=1, stroke=0)
            for ln in partes:
                self.c.setFillColor(TX); self.c.setFont("Helvetica", tam); self.c.drawString(M + 5 * mm, self.y, ln)
                self.y -= 4.4 * mm
            self.y -= 0.8 * mm

    def tabela(self, colunas, linhas, total=None):
        """colunas: [(título, fração da largura, 'e'|'d')]; linhas: listas de textos; total: (rótulo, valor)."""
        xs, x = [], M
        for _, frac, _a in colunas:
            xs.append((x, x + frac * CW))
            x += frac * CW
        self.falta(14 * mm)
        self.c.setFillColor(MU); self.c.setFont("Helvetica-Bold", 7)
        for (tit, _f, al), (x0, x1) in zip(colunas, xs):
            (self.c.drawRightString(x1, self.y, tit.upper()) if al == "d" else self.c.drawString(x0, self.y, tit.upper()))
        self.y -= 2.5 * mm
        self.c.setStrokeColor(TX); self.c.setLineWidth(0.9); self.c.line(M, self.y, W - M, self.y)
        self.y -= 5 * mm
        for lin in linhas:
            self.falta(7 * mm)
            for i, ((tit, _f, al), (x0, x1)) in enumerate(zip(colunas, xs)):
                txt = _seguro(lin[i] if i < len(lin) else "")
                negrito = i == 0 and isinstance(lin, tuple) and len(lin) > len(colunas) and lin[-1] == "b"
                fonte = "Helvetica-Bold" if negrito else "Helvetica"
                self.c.setFillColor(TX if i in (0, len(colunas) - 1) else MU); self.c.setFont(fonte, 9.5)
                txt = simpleSplit(txt, fonte, 9.5, (x1 - x0) - 2 * mm)[0] if txt else ""
                (self.c.drawRightString(x1, self.y, txt) if al == "d" else self.c.drawString(x0, self.y, txt))
            self.y -= 2.3 * mm
            self.c.setStrokeColor(LINHA); self.c.setLineWidth(0.6); self.c.line(M, self.y, W - M, self.y)
            self.y -= 3.9 * mm
        if total:
            self.y -= 0.6 * mm
            self.c.setStrokeColor(TX); self.c.setLineWidth(1.4); self.c.line(M, self.y + 4 * mm, W - M, self.y + 4 * mm)
            self.c.setFillColor(TX); self.c.setFont("Helvetica-Bold", 10.5)
            self.c.drawString(M, self.y - 1 * mm, _seguro(total[0])); self.c.drawRightString(W - M, self.y - 1 * mm, total[1])
            self.y -= 7 * mm

    def lista(self, pares, x=M, largura=CW, total=None, cor_total=None):
        """pares: [(rótulo, valor, negativo?)] em linhas com fio; total: (rótulo, valor). Devolve o y final."""
        y = self.y
        for rot, val, neg in pares:
            self.c.setFillColor(TX); self.c.setFont("Helvetica", 9.8)
            self.c.drawString(x, y, simpleSplit(_seguro(rot), "Helvetica", 9.8, largura * 0.62)[0])
            self.c.setFillColor(VERMELHO if neg else TX); self.c.setFont("Helvetica-Bold", 9.8)
            self.c.drawRightString(x + largura, y, ("- " if neg else "") + val)
            y -= 2.8 * mm
            self.c.setStrokeColor(LINHA); self.c.setLineWidth(0.6); self.c.line(x, y, x + largura, y)
            y -= 4.6 * mm
        if total:
            self.c.setStrokeColor(TX); self.c.setLineWidth(1.4); self.c.line(x, y + 4.4 * mm, x + largura, y + 4.4 * mm)
            self.c.setFillColor(TX); self.c.setFont("Helvetica-Bold", 10.5); self.c.drawString(x, y - 0.6 * mm, total[0])
            self.c.setFillColor(cor_total or TX); self.c.drawRightString(x + largura, y - 0.6 * mm, total[1])
            y -= 6 * mm
        return y

    def caixa_total(self, linhas, rotulo, valor, cor=None, nota=""):
        cor = cor or self.cor
        h = (len(linhas) * 6 + (16 if not nota else 22)) * mm
        self.falta(h + 3 * mm)
        top = self.y + 1 * mm
        self.c.setStrokeColor(cor); self.c.setLineWidth(1.4)
        self.c.roundRect(M, top - h, CW, h, 4 * mm, fill=0, stroke=1)
        y = top - 7 * mm
        for rot, val in linhas:
            self.c.setFillColor(MU); self.c.setFont("Helvetica", 9.5)
            self.c.drawString(M + 6 * mm, y, _seguro(rot)); self.c.drawRightString(W - M - 6 * mm, y, val)
            y -= 6 * mm
        if linhas:
            self.c.setStrokeColor(LINHA); self.c.setLineWidth(0.6)
            self.c.line(M + 6 * mm, y + 2.5 * mm, W - M - 6 * mm, y + 2.5 * mm)
        self.c.setFillColor(TX); self.c.setFont("Helvetica-Bold", 11); self.c.drawString(M + 6 * mm, y - 5 * mm, rotulo)
        self.c.setFillColor(cor); self.c.setFont("Helvetica-Bold", 19); self.c.drawRightString(W - M - 6 * mm, y - 5.5 * mm, valor)
        if nota:
            self.c.setFillColor(MU); self.c.setFont("Helvetica", 8.5); self.c.drawString(M + 6 * mm, y - 11.5 * mm, _seguro(nota)[:110])
        self.y = top - h

    def nota(self, txt):
        partes = simpleSplit(_seguro(txt), "Helvetica", 9, CW - 10 * mm)
        h = len(partes) * 4.4 * mm + 6 * mm
        self.y -= 4 * mm
        self.falta(h + 2 * mm)
        self.c.setFillColor(colors.HexColor("#FBF6E8")); self.c.setStrokeColor(colors.HexColor("#EDDDAE"))
        self.c.setLineWidth(0.6); self.c.roundRect(M, self.y - h + 3 * mm, CW, h, 3 * mm, fill=1, stroke=1)
        y = self.y - 1.5 * mm
        for ln in partes:
            self.c.setFillColor(colors.HexColor("#5C4712")); self.c.setFont("Helvetica", 9); self.c.drawString(M + 5 * mm, y, ln)
            y -= 4.4 * mm
        self.y -= h

    def barra(self, partes):
        """partes: [(rótulo, valor, cor)] — barra única com a legenda embaixo."""
        tot = sum(v for _, v, _ in partes if v > 0)
        if tot <= 0:
            return
        self.falta(14 * mm)
        x = M
        for _, v, cor in partes:
            if v <= 0:
                continue
            w = CW * v / tot
            self.c.setFillColor(cor); self.c.rect(x, self.y - 3.5 * mm, w, 3.5 * mm, fill=1, stroke=0)
            x += w
        self.y -= 8.5 * mm
        x = M
        for rot, v, cor in partes:
            if v <= 0:
                continue
            txt = f"{rot} {brl(v)}"
            self.c.setFillColor(cor); self.c.rect(x, self.y - 0.3 * mm, 2.6 * mm, 2.6 * mm, fill=1, stroke=0)
            self.c.setFillColor(MU); self.c.setFont("Helvetica", 8.5); self.c.drawString(x + 4 * mm, self.y, txt)
            x += self.c.stringWidth(txt, "Helvetica", 8.5) + 10 * mm
        self.y -= 4 * mm

    def passos(self, itens):
        """[(quando, o quê)] em duas colunas, com o prazo em destaque."""
        meio = CW / 2
        for i in range(0, len(itens), 2):
            self.falta(9 * mm)
            for j, (quando, oque) in enumerate(itens[i:i + 2]):
                x = M + j * meio
                self.c.setFillColor(self.cor); self.c.setFont("Helvetica-Bold", 9.5); self.c.drawString(x, self.y, quando)
                self.c.setFillColor(TX); self.c.setFont("Helvetica", 9.5)
                self.c.drawString(x + 17 * mm, self.y, simpleSplit(_seguro(oque), "Helvetica", 9.5, meio - 20 * mm)[0])
            self.y -= 7 * mm

    # rodapé
    def rodape(self, botao=None, mensagem=""):
        c, p = self.c, self.perfil
        c.setFillColor(self.claro); c.rect(0, 0, W, RODAPE_H, fill=1, stroke=0)
        if self.interno:
            c.setFillColor(self.cor); c.setFont("Helvetica-Bold", 9.5); c.drawString(M, 12 * mm, "Documento de uso interno")
            c.setFillColor(MU); c.setFont("Helvetica", 8.5)
            c.drawString(M, 7.5 * mm, f"Não envie para a cliente · gerado pelo Planner Organiza em {date.today():%d/%m/%Y}")
            c.drawRightString(W - M, 9.5 * mm, _seguro(p.get("empresa") or p.get("nome") or "")[:40])
            return
        empresa = _seguro(p.get("empresa") or p.get("nome") or "").strip()
        contatos = " · ".join(x for x in [telefone_fmt(p.get("telefone")) if len(re.sub(r"\D", "", str(p.get("telefone") or ""))) >= 10 else "",
                                           _seguro(p.get("email") or "").strip(), _seguro(p.get("instagram") or "").strip(),
                                           ("CNPJ " + _seguro(p.get("cnpj")).strip()) if p.get("cnpj") else ""] if x)
        c.setFillColor(self.cor); c.setFont("Helvetica-Bold", 9.5); c.drawString(M, 12 * mm, empresa[:50])
        c.setFillColor(TX); c.setFont("Helvetica", 8.5); c.drawString(M, 7.5 * mm, contatos[:95])
        link = link_whatsapp(p.get("telefone"), mensagem) if botao else ""
        if link:
            bw, bh = 46 * mm, 9 * mm
            x, y = W - M - bw, (RODAPE_H - bh) / 2
            c.setFillColor(self.fundo); c.roundRect(x, y, bw, bh, 2.5 * mm, fill=1, stroke=0)
            c.setFillColor(self.sobre); c.setFont("Helvetica-Bold", 9.5); c.drawCentredString(x + bw / 2, y + 3.1 * mm, botao)
            c.linkURL(link, (x, y, x + bw, y + bh), relative=0)

    def salvar(self, botao=None, mensagem=""):
        self.rodape(botao, mensagem)
        self.c.save()


# ───────────────────────────── ajudantes de dados ─────────────────────────────

def _primeiro_nome(nome):
    p = _seguro(nome).strip().split()
    return p[0] if p else "você"


def _itens_cliente(itens):
    """Itens no formato antigo (dicts nome/valor/quantidade/valor_unit/is_neg) → linhas da tabela."""
    linhas = []
    for it in itens or []:
        if isinstance(it, dict):
            nome = it.get("nome") or it.get("descricao") or it.get("produto_nome") or ""
            valor = _num(it.get("total", it.get("valor", it.get("subtotal", 0))))
            q, u = it.get("quantidade"), it.get("valor_unit")
            neg = bool(it.get("is_neg"))
        else:
            nome, valor = it[0], _num(it[1] if len(it) > 1 else 0)
            q = u = None
            neg = bool(it[2]) if len(it) > 2 else False
        nome = re.sub(r"^Personal Organizer\s*-\s*", "Serviço de ", str(nome)).strip()
        nome = nome[0].upper() + nome[1:] if nome else nome
        try:
            qtxt = str(int(float(q))) if q is not None else "1"
            utxt = brl(u) if u is not None else "—"
        except (TypeError, ValueError):
            qtxt, utxt = "1", "—"
        servico = q is None
        linhas.append(((nome, qtxt, utxt, ("- " if neg else "") + brl(valor)) + (("b",) if servico else ())))
    return linhas


def itens_da_descricao(desc):
    """Descrição antiga em lista ("Organização de:" + "- closet" ...) → (frase de abertura, [itens curtos]).
    Devolve ([], ...) quando o texto é corrido e deve sair como parágrafos."""
    linhas = limpar_texto(desc)
    abre = ""
    if linhas and linhas[0].endswith(":"):
        abre, linhas = linhas[0].rstrip(":").strip(), linhas[1:]
    if len(linhas) >= 2 and all(len(x) <= 32 and not x.endswith(".") for x in linhas):
        return abre, linhas
    return abre, []


def _ambientes(dados):
    from utils.pdf_proposta import ambientes_da_descricao
    amb = [n for n, _ in ambientes_da_descricao(dados.get("descricao"))]
    return amb or itens_da_descricao(dados.get("descricao"))[1]


def _periodo_curto(txt):
    m = re.match(r"\s*(\d{2}/\d{2})/(\d{4})\s*[–-]\s*(\d{2}/\d{2}/\d{4})\s*$", str(txt or ""))
    return f"{m.group(1)} a {m.group(3)}" if m else str(txt or "")


# ───────────────────────────── documentos ─────────────────────────────

def fechamento(dados, caminho, perfil=None):
    """Fechamento do Serviço (para a cliente). Mesmo dict de pdf_generator_v2.gerar_pdf_cliente."""
    cli = dados.get("cliente", "")
    doc = Doc(caminho, perfil, "Fechamento do Serviço", dados.get("proposta_id", ""), _seguro(_periodo_curto(dados.get("periodo", ""))),
              titulo_arquivo=f"Fechamento - {cli}")
    concluido = str(dados.get("status", "")).strip().lower() in ("finalizada", "concluída", "concluida", "finalizado")
    doc.titulo("Serviço concluído, " if concluido else "Resumo do serviço, ", _primeiro_nome(cli))
    doc.linha_fina("Obrigada pela confiança. Aqui está o resumo do que foi feito." if concluido
                   else "Aqui está o resumo do serviço contratado.")
    amb = _ambientes(dados)
    doc.cartoes([("Serviço", dados.get("tipo") or "Organização", ""), ("Período", _periodo_curto(dados.get("periodo")) or "—", ""),
                 ("Ambientes", str(len(amb)) if amb else "—", ""),
                 ("Situação", "Concluído" if concluido else (dados.get("status") or "—"), "verde" if concluido else "")])
    if amb:
        doc.secao("Ambientes organizados" if concluido else "Ambientes")
        doc.etiquetas(amb)
    else:
        linhas = limpar_texto(dados.get("descricao"))
        if linhas:
            doc.secao("O que foi feito" if concluido else "Descrição do serviço")
            doc.marcadores(linhas)
    doc.secao("O que foi entregue" if concluido else "O que está incluído")
    total = _num(dados.get("total"))
    doc.tabela([("Item", .55, "e"), ("Qtd", .1, "d"), ("Unitário", .15, "d"), ("Valor", .2, "d")],
               _itens_cliente(dados.get("itens")), total=("Total do serviço", brl(total)))
    servico, produtos = 0.0, 0.0
    for i, it in enumerate(dados.get("itens") or []):
        v = _num(it.get("total", it.get("valor", 0))) if isinstance(it, dict) else _num(it[1] if len(it) > 1 else 0)
        if i == 0 and not isinstance(it, dict):
            servico += v
        else:
            produtos += v
    pares = [("Serviço de organização", brl(servico), False)] if servico else []
    if produtos:
        pares.append(("Produtos e adicionais", brl(produtos), False))
    sinal = _num(dados.get("sinal"))
    if sinal > 0:
        pares.append(("Sinal pago", brl(sinal), False))
        if not concluido:
            pares.append(("Saldo a pagar", brl(max(total - sinal, 0)), False))
    doc.secao("Pagamento")
    doc.falta(len(pares) * 7.4 * mm + 10 * mm)
    doc.y = doc.lista(pares, total=("Total", brl(total)), cor_total=doc.cor)
    if concluido:
        doc.secao("Próximos cuidados")
        doc.passos([("1 dia", "Mensagem de agradecimento"), ("7 dias", "Como você está se sentindo na casa"),
                    ("30 dias", "Ajuste fino, se precisar"), ("45 dias", "Sua opinião sobre a experiência")])
    doc.salvar("Falar no WhatsApp", f"Olá! Sobre o serviço Nº {dados.get('proposta_id', '')}.")
    return caminho


def interno(dados, caminho, perfil=None):
    """Relatório Interno. Mesmo dict de pdf_generator_v2.gerar_pdf_interno."""
    cli = dados.get("cliente", "")
    doc = Doc(caminho, perfil, "Relatório Interno", dados.get("proposta_id", ""), f"Gerado em {date.today():%d/%m/%Y}",
              interno=True, titulo_arquivo=f"Relatorio Interno - {cli}")
    doc.titulo("Quanto o projeto da ", _primeiro_nome(cli), " deixou")
    doc.linha_fina(" · ".join(x for x in [dados.get("tipo"), dados.get("periodo"), dados.get("status")] if x))

    nomes = {"personal organizer": "Serviço de organização", "comissões": "Comissão de fornecedores",
             "lucro em produtos": "Lucro nos produtos", "pagamento assistentes": "Assistentes"}

    def _pares(itens, custo=False):
        out = []
        for it in itens or []:
            if isinstance(it, dict):
                n, v, neg = it.get("descricao") or it.get("nome") or "", _num(it.get("valor", it.get("total", 0))), bool(it.get("is_neg"))
            else:
                n, v, neg = it[0], _num(it[1]), bool(it[2]) if len(it) > 2 else False
            n = str(n).strip()
            n = ("Seu serviço" if custo and n.lower() == "personal organizer" else nomes.get(n.lower(), n))
            n = re.sub(r"^Assistente:\s*", "Assistente · ", n)
            if v or not neg:
                out.append((n, v, neg))
        return out
    custo = _pares(dados.get("itens_custo"), custo=True)
    receita = [x for x in _pares(dados.get("itens_receita")) if x[1] or x[2]]
    total_cli = _num(dados.get("total_custo")) or sum(v for _, v, _ in custo)
    sobrou = _num(dados.get("total_receita"))
    entrou = sum(v for _, v, neg in receita if not neg)
    saiu = sum(v for _, v, neg in receita if neg)
    margem = f"{sobrou / total_cli * 100:.1f}%".replace(".", ",") if total_cli else "—"
    doc.cartoes([("A cliente investiu", brl(total_cli), "grande"), ("Sua equipe e custos", brl(saiu), "grande"),
                 ("Sobrou para você", brl(sobrou), "verde"), ("Margem", margem, "escuro")])
    tons = [colors.HexColor("#0D1B2A"), colors.HexColor("#C9A84C"), colors.HexColor("#9AA8B8"), colors.HexColor("#D9CFB8")]
    partes = [(n, v, tons[i % len(tons)]) for i, (n, v, _) in enumerate([x for x in custo if x[1] > 0])]
    if partes:
        doc.secao("Para onde foi o dinheiro da cliente")
        doc.barra(partes)
    doc.secao("O que entrou para você  ·  o que saiu")
    meio = CW / 2 - 4 * mm
    y0 = doc.y
    doc.falta(max(len(receita), 4) * 7.5 * mm + 10 * mm)
    y0 = doc.y
    ya = doc.lista([(n, brl(v), False) for n, v, neg in receita if not neg], x=M, largura=meio,
                   total=("Total que entrou", brl(entrou)))
    doc.y = y0
    yb = doc.lista([(n, brl(v), True) for n, v, neg in receita if neg] or [("Nada saiu", brl(0), False)],
                   x=M + meio + 8 * mm, largura=meio, total=("Total que saiu", ("- " if saiu else "") + brl(saiu)),
                   cor_total=VERMELHO if saiu else None)
    doc.y = min(ya, yb) - 3 * mm
    doc.caixa_total([], "Sobrou para você neste projeto", brl(sobrou), cor=VERDE,
                    nota=f"{brl(entrou)} que entraram - {brl(saiu)} de equipe e custos · {margem} do que a cliente investiu")
    doc.salvar()
    return caminho


def fornecedores(dados, caminho, perfil=None):
    """Relatório de Fornecedores. Mesmo dict de pdf_generator_v2.gerar_pdf_fornecedores."""
    cli = dados.get("cliente", "")
    doc = Doc(caminho, perfil, "Relatório de Fornecedores", dados.get("proposta_id", ""),
              f"Gerado em {date.today():%d/%m/%Y}", interno=True, titulo_arquivo=f"Fornecedores - {cli}")
    doc.titulo("Fornecedores do projeto da ", _primeiro_nome(cli))
    doc.linha_fina(" · ".join(x for x in [dados.get("tipo"), dados.get("status")] if x))
    itens = []
    for it in dados.get("itens") or []:
        if isinstance(it, dict):
            itens.append((it.get("descricao") or it.get("nome") or "", _num(it.get("valor", it.get("total", 0)))))
        else:
            itens.append((it[0], _num(it[1])))
    total = _num(dados.get("total")) or sum(v for _, v in itens)
    doc.cartoes([("Fornecedores", str(len(itens)), ""), ("Total pago", brl(total), "grande"),
                 ("Cliente", cli or "—", "")])
    doc.secao("Pagamentos a fornecedores")
    doc.tabela([("Fornecedor / o que forneceu", .75, "e"), ("Valor", .25, "d")],
               [(n, brl(v)) for n, v in itens] or [("Nenhum fornecedor neste projeto", "")],
               total=("Total", brl(total)))
    if dados.get("telefone"):
        doc.secao("Contato da cliente")
        doc.y = doc.lista([(cli, telefone_fmt(dados.get("telefone")), False)])
    doc.salvar()
    return caminho


def venda(venda_dados, cliente_dados, itens_df, caminho, perfil=None):
    """Produtos / venda (recibo para a cliente). Mesmos argumentos de pdf_generator_v2.gerar_pdf_venda_v2."""
    import pandas as pd
    cli = (cliente_dados or {}).get("nome", "")
    dv = venda_dados.get("data_venda", "")
    dv = dv.strftime("%d/%m/%Y") if hasattr(dv, "strftime") else (str(dv)[:10] if dv else "")
    d = _data(venda_dados.get("data_venda"))
    doc = Doc(caminho, perfil, "Produtos", venda_dados.get("id", ""), d.strftime("%d/%m/%Y") if d else dv,
              titulo_arquivo=f"Produtos - {cli}")
    da_proposta = str(venda_dados.get("status") or "").strip().lower() == "proposta"
    if da_proposta:
        doc.titulo("Produtos do projeto da ", _primeiro_nome(cli))
    else:
        doc.titulo("Produtos para ", _primeiro_nome(cli) if cli else "você")
    doc.linha_fina("Organizadores escolhidos para a sua casa.")
    linhas, total_calc, qtd_tot = [], 0.0, 0
    if isinstance(itens_df, pd.DataFrame) and not itens_df.empty:
        for _, row in itens_df.iterrows():
            nome = str(row.get("produto_nome", row.get("nome", "Produto")))
            q = int(_num(row.get("quantidade", 1)) or 1)
            u = _num(row.get("preco_unitario", row.get("valor", 0)))
            total_calc += q * u
            qtd_tot += q
            linhas.append((nome[0].upper() + nome[1:] if nome else nome, str(q), brl(u), brl(q * u)))
    total = _num(venda_dados.get("valor_total")) or total_calc
    situ = str(venda_dados.get("status") or "").strip()
    pago = situ.lower() in ("pago", "paga", "recebido", "concluida", "concluída")
    forma = str(venda_dados.get("forma_pagamento") or "").strip()
    if forma.upper() in ("", "N/A", "NA", "-", "—"):
        forma = "junto com o serviço" if da_proposta else "a combinar"
    cards = [("Itens", str(qtd_tot or len(linhas)), ""), ("Pagamento", forma, "")]
    if situ and not da_proposta:
        cards.append(("Situação", "Pago" if pago else situ, "verde" if pago else ""))
    cards.append(("Total", brl(total), "grande"))
    doc.cartoes(cards)
    doc.secao("Itens")
    doc.tabela([("Produto", .55, "e"), ("Qtd", .1, "d"), ("Unitário", .15, "d"), ("Valor", .2, "d")],
               linhas or [("Nenhum item", "", "", "")], total=("Total", brl(total)))
    doc.salvar("Falar no WhatsApp", "Olá! Sobre os produtos que comprei.")
    return caminho


def proposta_de_dados_antigos(dados, caminho, perfil=None):
    """Proposta no modelo novo a partir do dict antigo (proposta_id, itens em tuplas/dicts, observacoes), usado
    pela API do app e por chamadas antigas."""
    from utils.pdf_proposta import condicoes, gerar_pdf_proposta
    tipo = dados.get("tipo") or "Organização"
    itens = []
    for it in dados.get("itens") or []:
        if isinstance(it, dict):
            q = it.get("quantidade")
            itens.append((it.get("nome") or it.get("descricao") or "", f"{int(_num(q) or 1)} un." if q is not None else "",
                          _num(it.get("total", it.get("valor", 0)))))
        else:
            nome = str(it[0])
            if nome.startswith("Personal Organizer - "):
                nome = f"Serviço de {str(tipo).lower()}"
            itens.append((nome, "", _num(it[1] if len(it) > 1 else 0)))
    obs = (dados.get("observacoes") or (perfil or {}).get("observacoes_relatorio") or "").strip()
    return gerar_pdf_proposta({
        "numero": dados.get("proposta_id", ""), "cliente": dados.get("cliente", ""), "tipo": tipo,
        "data": dados.get("data"), "descricao": dados.get("descricao", ""), "itens": itens,
        "total": _num(dados.get("total")), "sinal": _num(dados.get("sinal")), "condicoes": condicoes(obs),
    }, caminho, perfil=perfil)
