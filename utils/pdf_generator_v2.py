# utils/pdf_generator_v2.py
# Gerador unificado de PDFs — design Navy/Gold
# Nome e dados personalizados via perfil do usuário

import os
import re
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

W, H = A4

# ── Paleta ──────────────────────────────────────────────────
NAVY     = colors.HexColor("#0D1B2A")
GOLD     = colors.HexColor("#C9A84C")
GOLD_LT  = colors.HexColor("#F5EDD6")
WHITE    = colors.white
GRAY1    = colors.HexColor("#F7F7F5")
GRAY2    = colors.HexColor("#E8E6E0")
GRAY3    = colors.HexColor("#9A9890")
DARK     = colors.HexColor("#1C1C1A")
GREEN    = colors.HexColor("#1D6A4A")
GREEN_LT = colors.HexColor("#A8EDBC")
RED      = colors.HexColor("#C0392B")
TEAL     = colors.HexColor("#0F5E6E")
TEAL_LT  = colors.HexColor("#E0F4F7")

# ── Marca da organizadora ────────────────────────────────────
# As cores e o logotipo vêm do perfil da conta (Perfil e marca). P lê a paleta da
# geração em andamento (ContextVar: cada sessão/thread tem a sua).
from contextvars import ContextVar
from io import BytesIO
import base64

_paleta = ContextVar("pdf_paleta", default=None)


def _hex(cor, padrao):
    cor = (cor or "").strip()
    return cor if re.fullmatch(r"#[0-9A-Fa-f]{6}", cor) else padrao


def _misturar(c1, c2, t):
    """Mistura c1 com c2 (t=0 → c1, t=1 → c2)."""
    return colors.Color(c1.red + (c2.red - c1.red) * t, c1.green + (c2.green - c1.green) * t,
                        c1.blue + (c2.blue - c1.blue) * t)


def _montar_paleta(perfil):
    principal = colors.HexColor(_hex((perfil or {}).get("cor_principal"), "#0D1B2A"))
    destaque = colors.HexColor(_hex((perfil or {}).get("cor_secundaria"), "#C9A84C"))
    return {"NAVY": principal, "GOLD": destaque, "GOLD_LT": _misturar(destaque, WHITE, 0.78),
            "NAVY_CLARO": _misturar(principal, WHITE, 0.10), "NAVY_MEDIO": _misturar(principal, WHITE, 0.25)}


class _P:
    def __getattr__(self, nome):
        pal = _paleta.get() or _montar_paleta(None)
        return pal[nome]


P = _P()


def _perfil_da_conta():
    """Perfil salvo da conta atual (cores, logo, contatos); {} se não houver."""
    try:
        from utils.database import Database, conta_atual
        if not conta_atual():
            return {}
        return Database(usuario_id=conta_atual()).get_perfil_usuario() or {}
    except Exception as e:
        print(f"[pdf] perfil da conta indisponível: {e}")
        return {}


def _perfil_efetivo(perfil):
    """Perfil salvo da conta completado/sobrescrito pelos campos preenchidos de `perfil`."""
    base = dict(_perfil_da_conta())
    base.update({k: v for k, v in (perfil or {}).items() if v not in (None, "")})
    return base


def _logo(perfil):
    url = (perfil or {}).get("logo") or ""
    if not url.startswith("data:image/"):
        return None
    try:
        from reportlab.lib.utils import ImageReader
        return ImageReader(BytesIO(base64.b64decode(url.split(",", 1)[1])))
    except Exception as e:
        print(f"[pdf] logo inválido: {e}")
        return None


def com_marca(fn):
    """Decorador dos geradores: resolve o perfil da conta e aplica a paleta durante a geração."""
    import functools

    @functools.wraps(fn)
    def gerar(*args, perfil=None, **kwargs):
        perfil = _perfil_efetivo(perfil)
        token = _paleta.set(_montar_paleta(perfil))
        try:
            return fn(*args, perfil=perfil, **kwargs)
        finally:
            _paleta.reset(token)
    return gerar


# ── Perfil padrão (fallback) ─────────────────────────────────
DEFAULT_PERFIL = {
    'nome':      'Personal Organizer',
    'empresa':   'Planner Organiza',
    'instagram': '@plannerorganiza',
    'cargo':     'Personal Organizer',
}

def _get_linha_perfil(perfil: dict) -> str:
    """Monta a linha de identificação do cabeçalho a partir do perfil."""
    p = perfil or DEFAULT_PERFIL
    nome = p.get('nome') or DEFAULT_PERFIL['nome']
    cargo = p.get('cargo') or DEFAULT_PERFIL['cargo']
    instagram = p.get('instagram') or ''
    partes = [nome, cargo]
    if instagram:
        partes.append(_instagram(instagram))
    return '  ·  '.join(partes)

def _get_linha_rodape(perfil: dict) -> str:
    """Monta a linha do rodapé."""
    p = perfil or DEFAULT_PERFIL
    nome = p.get('nome') or DEFAULT_PERFIL['nome']
    instagram = p.get('instagram') or ''
    if instagram:
        return f"{nome}  ·  {instagram}"
    return nome

# ── Utilitários ─────────────────────────────────────────────
def fmt(v):
    return f"R$ {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def rr(c, x, y, w, h, r, fill, stroke=None, sw=0.5):
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.setLineWidth(sw)
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    c.drawPath(p, fill=1, stroke=1 if stroke else 0)
    c.restoreState()

def _header(c, titulo, proposta, margin, perfil=None):
    linha = _get_linha_perfil(perfil)
    logo = _logo(perfil)
    c.setFillColor(P.NAVY)
    c.rect(0, H - 52*mm, W, 52*mm, fill=1, stroke=0)
    c.setFillColor(P.GOLD)
    c.rect(0, H - 52*mm, W, 1.2*mm, fill=1, stroke=0)
    gerado = f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    if logo:
        # logotipo num cartão branco à direita; o número vai para a linha de data
        lado = 34*mm
        x0, y0 = W - margin - lado, H - 46*mm
        rr(c, x0, y0, lado, lado, 6, WHITE)
        iw, ih = logo.getSize()
        esc = min((lado - 6*mm) / iw, (lado - 6*mm) / ih)
        c.drawImage(logo, x0 + (lado - iw * esc) / 2, y0 + (lado - ih * esc) / 2, iw * esc, ih * esc, mask="auto")
        gerado = f"{proposta}  ·  {gerado}"
    else:
        c.setFillColor(P.NAVY_CLARO)
        c.setFont("Helvetica-Bold", 72)
        c.drawRightString(W - margin, H - 42*mm, proposta)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin, H - 24*mm, titulo)
    c.setFillColor(P.GOLD)
    c.setFont("Helvetica", 11)
    c.drawString(margin, H - 32*mm, linha)
    c.setFillColor(_misturar(P.NAVY, WHITE, 0.6))
    c.setFont("Helvetica", 9)
    c.drawString(margin, H - 40*mm, gerado)

def _info_cards(c, margin, content_w, infos):
    top_y = H - 68*mm
    card_h = 18*mm
    n = len(infos)
    card_w = (content_w - (n-1)*4*mm) / n
    for i, (label, value) in enumerate(infos):
        cx = margin + i*(card_w + 4*mm)
        rr(c, cx, top_y - card_h, card_w, card_h, 4, GRAY1, GRAY2, 0.5)
        c.setFillColor(GRAY3)
        c.setFont("Helvetica", 8)
        c.drawString(cx + 4*mm, top_y - 7*mm, label.upper())
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(cx + 4*mm, top_y - 14*mm, str(value))
    return top_y - card_h - 10*mm

def _section_title(c, margin, content_w, y, titulo, subtitulo, line_color):
    c.setFillColor(P.NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, titulo)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8.5)
    c.drawString(margin, y - 5*mm, subtitulo)
    c.setStrokeColor(line_color)
    c.setLineWidth(1)
    c.line(margin, y - 7*mm, margin + content_w, y - 7*mm)
    return y - 14*mm

def _table_rows(c, margin, content_w, start_y, items, row_h=9*mm):
    y = start_y
    for idx, item in enumerate(items):
        if isinstance(item, dict):
            nome = item.get('descricao', item.get('nome', item.get('produto_nome', '')))
            valor = item.get('total', item.get('valor', item.get('subtotal', 0)))
            is_neg = item.get('is_neg', False)
        elif isinstance(item, (list, tuple)):
            nome = item[0]
            valor = item[1]
            is_neg = item[2] if len(item) > 2 else False
        else:
            nome = str(item)
            valor = 0
            is_neg = False
        bg = GRAY1 if idx % 2 == 0 else WHITE
        rr(c, margin, y - row_h + 1.5*mm, content_w, row_h - 1*mm, 3, bg)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 10)
        c.drawString(margin + 4*mm, y - 4.5*mm, str(nome))
        c.setFillColor(RED if is_neg else DARK)
        c.setFont("Helvetica-Bold", 10)
        prefix = "– " if is_neg else ""
        c.drawRightString(margin + content_w - 4*mm, y - 4.5*mm, prefix + fmt(valor))
        y -= row_h
    return y


def _table_rows_itemizado(c, margin, content_w, start_y, items, row_h=9*mm):
    """Como _table_rows, mas com cabeçalho e colunas Qtd / Vlr. Unitário
    quando o item traz quantidade e valor_unit (produtos). Itens sem esses
    campos (serviço, acréscimos) exibem essas colunas em branco."""
    muted = colors.HexColor("#6B7280")
    y = start_y
    col_prod = margin
    col_qtd  = margin + content_w * 0.54
    col_unit = margin + content_w * 0.66
    col_sub  = margin + content_w - 4*mm
    # Cabeçalho
    rr(c, margin, y - row_h + 1.5*mm, content_w, row_h - 1*mm, 3, P.NAVY)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(col_prod + 4*mm, y - 4.5*mm, "Item")
    c.drawString(col_qtd,  y - 4.5*mm, "Qtd")
    c.drawString(col_unit, y - 4.5*mm, "Vlr. Unitário")
    c.drawRightString(col_sub, y - 4.5*mm, "Subtotal")
    y -= row_h
    for idx, item in enumerate(items):
        qtd = None
        unit = None
        if isinstance(item, dict):
            nome = item.get('nome', item.get('descricao', item.get('produto_nome', '')))
            valor = item.get('total', item.get('valor', item.get('subtotal', 0)))
            is_neg = item.get('is_neg', False)
            if item.get('quantidade') is not None and item.get('valor_unit') is not None:
                try:
                    qtd = int(float(item.get('quantidade')))
                    unit = float(item.get('valor_unit'))
                except Exception:
                    qtd = unit = None
        elif isinstance(item, (list, tuple)):
            nome = item[0]
            valor = item[1]
            is_neg = item[2] if len(item) > 2 else False
        else:
            nome = str(item)
            valor = 0
            is_neg = False
        bg = GRAY1 if idx % 2 == 0 else WHITE
        rr(c, margin, y - row_h + 1.5*mm, content_w, row_h - 1*mm, 3, bg)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 9.5)
        c.drawString(col_prod + 4*mm, y - 4.5*mm, str(nome))
        if qtd is not None and unit is not None:
            c.setFillColor(muted)
            c.setFont("Helvetica", 9)
            c.drawString(col_qtd,  y - 4.5*mm, str(qtd))
            c.drawString(col_unit, y - 4.5*mm, fmt(unit))
        c.setFillColor(RED if is_neg else DARK)
        c.setFont("Helvetica-Bold", 9.5)
        prefix = "– " if is_neg else ""
        c.drawRightString(col_sub, y - 4.5*mm, prefix + fmt(valor))
        y -= row_h
    return y

def _total_row(c, margin, content_w, y, label, valor, bg, text_color, val_color, row_h=9*mm):
    rr(c, margin, y - row_h + 1*mm, content_w, row_h, 4, bg)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(margin + 4*mm, y - 4.5*mm, label)
    c.setFillColor(val_color)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(margin + content_w - 4*mm, y - 4.5*mm, fmt(valor))
    return y - row_h

def _footer(c, margin, perfil=None, interno=False):
    p = perfil or {}
    c.setFillColor(GRAY2)
    c.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8)
    empresa = p.get('empresa') or p.get('nome') or 'Planner Organiza'
    if p.get('cnpj'):
        empresa += f"  ·  CNPJ {p['cnpj']}"
    c.drawString(margin, 5*mm, f"Documento de uso interno — {empresa}" if interno else empresa)
    contatos = [x for x in (p.get('telefone'), _instagram(p.get('instagram')), p.get('website') or p.get('email')) if x]
    c.drawRightString(W - margin, 5*mm, "  ·  ".join(contatos) if contatos else _get_linha_rodape(perfil))


def _instagram(valor):
    valor = (valor or "").strip()
    return ("@" + valor.lstrip("@")) if valor else ""

# ── Relatórios ───────────────────────────────────────────────

@com_marca
def gerar_pdf_interno(dados, output_path, perfil=None):
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Relatório Interno", f"#{dados['proposta_id']}", margin, perfil)
    y = _info_cards(c, margin, cw, [
        ("Cliente",  dados.get('cliente', '')),
        ("Tipo",     dados.get('tipo', '')),
        ("Status",   dados.get('status', '')),
        ("Período",  dados.get('periodo', '')),
    ])
    y = _section_title(c, margin, cw, y, "Custo Total do Cliente",
        "Todos os valores cobrados ao cliente nesta proposta", P.GOLD)
    y = _table_rows(c, margin, cw, y, dados.get('itens_custo', []))
    y = _total_row(c, margin, cw, y, "CUSTO TOTAL DO CLIENTE",
        dados.get('total_custo', 0), P.NAVY, WHITE, P.GOLD)
    y -= 12*mm
    y = _section_title(c, margin, cw, y, "Receita Líquida do Projeto",
        "Ganho real considerando comissões, lucro em produtos e pagamentos", GREEN)
    y = _table_rows(c, margin, cw, y, dados.get('itens_receita', []))
    y = _total_row(c, margin, cw, y, "RECEITA LÍQUIDA TOTAL",
        dados.get('total_receita', 0), GREEN, WHITE, GREEN_LT)
    if dados.get('total_custo', 0) > 0:
        y -= 10*mm
        pct = (dados.get('total_receita', 0) / dados.get('total_custo', 1)) * 100
        rr(c, margin, y - 14*mm, cw, 14*mm, 6, P.GOLD_LT, P.GOLD, 0.8)
        c.setFillColor(colors.HexColor("#7A5C1A"))
        c.setFont("Helvetica", 9)
        c.drawString(margin + 5*mm, y - 5.5*mm, "Margem sobre o faturamento total do projeto")
        c.setFillColor(P.NAVY)
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(margin + cw - 5*mm, y - 9*mm, f"{pct:.1f}%".replace(".", ","))
    _footer(c, margin, perfil, interno=True)
    c.save()

def _desc_box(c, margin, cw, y, desc):
    """Caixa 'Descrição do serviço' com QUEBRA de linha e altura dinâmica.
    Antes usava drawString de linha única em caixa fixa (12mm): descrição
    longa saía da página e 'sumia'. Retorna o novo y."""
    from reportlab.lib.utils import simpleSplit
    texto = str(desc) if str(desc).startswith('-') else f"- {desc}"
    linhas = simpleSplit(texto, "Helvetica-Bold", 10, cw - 10*mm) or [""]
    box_h = 8*mm + len(linhas) * 4.8*mm
    rr(c, margin, y - box_h, cw, box_h, 4, P.GOLD_LT, P.GOLD, 0.5)
    c.setFillColor(colors.HexColor("#7A5C1A"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 5*mm, y - 4*mm, "Descrição do serviço")
    c.setFillColor(P.NAVY)
    c.setFont("Helvetica-Bold", 10)
    ly = y - 9*mm
    for ln in linhas:
        c.drawString(margin + 5*mm, ly, ln)
        ly -= 4.8*mm
    return y - (box_h + 10*mm)


@com_marca
def gerar_pdf_cliente(dados, output_path, perfil=None, titulo="Fechamento do Serviço"):
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, titulo, f"#{dados['proposta_id']}", margin, perfil)
    y = _info_cards(c, margin, cw, [
        ("Cliente",  dados.get('cliente', '')),
        ("Tipo",     dados.get('tipo', '')),
        ("Status",   dados.get('status', '')),
        ("Período",  dados.get('periodo', '')),
    ])
    desc = dados.get('descricao', '')
    if desc:
        y = _desc_box(c, margin, cw, y, desc)
    y = _section_title(c, margin, cw, y, "Investimento",
        "Valores do serviço contratado", P.NAVY)
    y = _table_rows_itemizado(c, margin, cw, y, dados.get('itens', []))
    _total_invest = dados.get('total', 0) or 0
    _sinal = float(dados.get('sinal', 0) or 0)
    if _sinal > 0:
        y = _total_row(c, margin, cw, y, "TOTAL DO INVESTIMENTO",
            _total_invest, P.NAVY_MEDIO, WHITE, WHITE)
        y = _table_rows(c, margin, cw, y, [
            {'descricao': "Sinal / entrada já pago", 'valor': _sinal, 'is_neg': True},
        ])
        y = _total_row(c, margin, cw, y, "SALDO A PAGAR",
            max(_total_invest - _sinal, 0), P.NAVY, WHITE, P.GOLD)
    else:
        y = _total_row(c, margin, cw, y, "TOTAL DO INVESTIMENTO",
            _total_invest, P.NAVY, WHITE, P.GOLD)
    obs_texto = (dados.get('observacoes', '') or '').strip()
    if not obs_texto:
        obs_texto = (perfil or {}).get('observacoes_relatorio', '') or ''
    if obs_texto:
        linhas_obs = [ln.rstrip() for ln in obs_texto.split('\n') if ln.strip()]
        bloco_h = 14*mm + len(linhas_obs) * 5*mm
        y -= 10*mm
        if y - bloco_h < 22*mm:
            c.showPage()
            y = H - 22*mm
        y = _section_title(c, margin, cw, y, "Observações",
            "Condições e informações importantes desta proposta", P.GOLD)
        rr(c, margin, y - bloco_h, cw, bloco_h, 4, P.GOLD_LT, P.GOLD, 0.5)
        c.setFillColor(P.NAVY)
        c.setFont("Helvetica", 9.5)
        ly = y - 6*mm
        for ln in linhas_obs:
            c.drawString(margin + 5*mm, ly, ln)
            ly -= 5*mm
    _footer(c, margin, perfil)
    c.save()
    return output_path

@com_marca
def gerar_pdf_fornecedores(dados, output_path, perfil=None):
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Relatório de Fornecedores", f"#{dados['proposta_id']}", margin, perfil)
    y = _info_cards(c, margin, cw, [
        ("Cliente",  dados.get('cliente', '')),
        ("Telefone", dados.get('telefone', '')),
        ("Tipo",     dados.get('tipo', '')),
        ("Status",   dados.get('status', '')),
    ])
    y = _section_title(c, margin, cw, y, "Fornecedores",
        "Valores pagos a fornecedores neste projeto", TEAL)
    y = _table_rows(c, margin, cw, y, dados.get('itens', []))
    _total_row(c, margin, cw, y, "TOTAL FORNECEDORES",
        dados.get('total', 0), TEAL, WHITE, colors.HexColor("#A8DDE8"))
    _footer(c, margin, perfil, interno=True)
    c.save()
    return output_path

@com_marca
def gerar_pdf_venda_v2(venda_dados, cliente_dados, itens_df, filename, perfil=None):
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    c = canvas.Canvas(filename, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Relatório de Venda", f"#{venda_dados.get('id','')}", margin, perfil)
    data_venda = venda_dados.get('data_venda', '')
    if hasattr(data_venda, 'strftime'):
        data_venda = data_venda.strftime('%d/%m/%Y')
    elif data_venda:
        data_venda = str(data_venda)
    y = _info_cards(c, margin, cw, [
        ("Cliente",   cliente_dados.get('nome', 'N/A')),
        ("Data",      data_venda),
        ("Pagamento", venda_dados.get('forma_pagamento', '') or '—'),
        ("Status",    venda_dados.get('status', '')),
    ])
    y = _section_title(c, margin, cw, y, "Itens da Venda",
        "Produtos e serviços incluídos nesta venda", P.NAVY)
    col_produto = margin
    col_qtd  = margin + cw * 0.50
    col_unit = margin + cw * 0.62
    col_sub  = margin + cw - 4*mm
    row_h = 9*mm
    rr(c, margin, y - row_h + 1.5*mm, cw, row_h - 1*mm, 3, P.NAVY)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_produto + 4*mm, y - 5*mm, "Produto")
    c.drawString(col_qtd,  y - 5*mm, "Qtd")
    c.drawString(col_unit, y - 5*mm, "Vlr. Unitário")
    c.drawRightString(col_sub, y - 5*mm, "Subtotal")
    y -= row_h
    total_calc = 0
    idx = 0
    if isinstance(itens_df, pd.DataFrame) and not itens_df.empty:
        for _, row in itens_df.iterrows():
            nome = str(row.get('produto_nome', row.get('nome', 'Produto'))).title()
            qtd  = int(row.get('quantidade', 1))
            valor = float(row.get('preco_unitario', row.get('valor', 0)))
            subtotal = qtd * valor
            total_calc += subtotal
            bg = GRAY1 if idx % 2 == 0 else WHITE
            rr(c, margin, y - row_h + 1.5*mm, cw, row_h - 1*mm, 3, bg)
            c.setFillColor(DARK)
            c.setFont("Helvetica", 9.5)
            c.drawString(col_produto + 4*mm, y - 5*mm, nome)
            c.drawString(col_qtd,  y - 5*mm, str(qtd))
            c.drawString(col_unit, y - 5*mm, fmt(valor))
            c.setFont("Helvetica-Bold", 9.5)
            c.drawRightString(col_sub, y - 5*mm, fmt(subtotal))
            y -= row_h
            idx += 1
    total = venda_dados.get('valor_total', total_calc) or total_calc
    _total_row(c, margin, cw, y, "TOTAL DA VENDA", total, P.NAVY, WHITE, P.GOLD)
    _footer(c, margin, perfil)
    c.save()
    return filename

@com_marca
def gerar_pdf_proposta_comercial(dados, output_path, perfil=None):
    """Proposta comercial — igual ao fechamento cliente mas com título diferente."""
    dados_copia = dict(dados)
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Proposta Comercial", f"#{dados_copia['proposta_id']}", margin, perfil)
    y = _info_cards(c, margin, cw, [
        ("Cliente",  dados_copia.get('cliente', '')),
        ("Tipo",     dados_copia.get('tipo', '')),
        ("Status",   dados_copia.get('status', '')),
        ("Período",  dados_copia.get('periodo', '')),
    ])
    desc = dados_copia.get('descricao', '')
    if desc:
        y = _desc_box(c, margin, cw, y, desc)
    y = _section_title(c, margin, cw, y, "Investimento",
        "Valores do serviço contratado", P.NAVY)
    y = _table_rows_itemizado(c, margin, cw, y, dados_copia.get('itens', []))
    y = _total_row(c, margin, cw, y, "TOTAL DO INVESTIMENTO",
        dados_copia.get('total', 0), P.NAVY, WHITE, P.GOLD)
    obs_texto = (dados_copia.get('observacoes', '') or '').strip()
    if not obs_texto:
        obs_texto = (perfil or {}).get('observacoes_relatorio', '') or ''
    if obs_texto:
        linhas_obs = [ln.rstrip() for ln in obs_texto.split('\n') if ln.strip()]
        bloco_h = 14*mm + len(linhas_obs) * 5*mm
        y -= 10*mm
        if y - bloco_h < 22*mm:
            c.showPage()
            y = H - 22*mm
        y = _section_title(c, margin, cw, y, "Observações",
            "Condições e informações importantes desta proposta", P.GOLD)
        rr(c, margin, y - bloco_h, cw, bloco_h, 4, P.GOLD_LT, P.GOLD, 0.5)
        c.setFillColor(P.NAVY)
        c.setFont("Helvetica", 9.5)
        ly = y - 6*mm
        for ln in linhas_obs:
            c.drawString(margin + 5*mm, ly, ln)
            ly -= 5*mm
    _footer(c, margin, perfil)
    c.save()
    return output_path
