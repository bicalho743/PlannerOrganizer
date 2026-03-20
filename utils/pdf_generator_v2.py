# utils/pdf_generator_v2.py
# Gerador unificado de PDFs — substitui todos os pdf_generator_*.py
# Design: Tâmara Cavalcante | Planner Organizer

import os
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

def _header(c, titulo, proposta, margin):
    c.setFillColor(NAVY)
    c.rect(0, H - 52*mm, W, 52*mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 52*mm, W, 1.2*mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1A2E45"))
    c.setFont("Helvetica-Bold", 72)
    c.drawRightString(W - margin, H - 42*mm, proposta)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin, H - 24*mm, titulo)
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 11)
    c.drawString(margin, H - 32*mm, "Tâmara Cavalcante  ·  Personal Organizer  ·  @tamaraorganiza")
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 9)
    from datetime import datetime
    c.drawString(margin, H - 40*mm, f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")

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
    c.setFillColor(NAVY)
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
    for idx, (nome, valor, is_neg) in enumerate(items):
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

def _total_row(c, margin, content_w, y, label, valor, bg, text_color, val_color, row_h=9*mm):
    rr(c, margin, y - row_h + 1*mm, content_w, row_h, 4, bg)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(margin + 4*mm, y - 4.5*mm, label)
    c.setFillColor(val_color)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(margin + content_w - 4*mm, y - 4.5*mm, fmt(valor))
    return y - row_h

def _footer(c, margin):
    c.setFillColor(GRAY2)
    c.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8)
    c.drawString(margin, 5*mm, "Documento de uso interno — Planner Organizer")
    c.drawRightString(W - margin, 5*mm, "Tâmara Cavalcante  ·  @tamaraorganiza")

# ── Relatórios públicos ──────────────────────────────────────
def gerar_pdf_interno(dados, output_path):
    """Relatório interno com análise financeira completa."""
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Relatório Interno", f"#{dados['proposta_id']}", margin)
    y = _info_cards(c, margin, cw, [
        ("Cliente",  dados.get('cliente', '')),
        ("Tipo",     dados.get('tipo', '')),
        ("Status",   dados.get('status', '')),
        ("Período",  dados.get('periodo', '')),
    ])
    y = _section_title(c, margin, cw, y, "Custo Total do Cliente",
        "Todos os valores cobrados ao cliente nesta proposta", GOLD)
    y = _table_rows(c, margin, cw, y, dados.get('itens_custo', []))
    y = _total_row(c, margin, cw, y, "CUSTO TOTAL DO CLIENTE",
        dados['total_custo'], NAVY, WHITE, GOLD)
    y -= 12*mm
    y = _section_title(c, margin, cw, y, "Receita Líquida do Projeto",
        "Ganho real da Personal, considerando comissões e pagamentos", GREEN)
    y = _table_rows(c, margin, cw, y, dados.get('itens_receita', []))
    y = _total_row(c, margin, cw, y, "RECEITA LÍQUIDA TOTAL",
        dados['total_receita'], GREEN, WHITE, GREEN_LT)
    if dados.get('total_custo', 0) > 0:
        y -= 10*mm
        pct = (dados['total_receita'] / dados['total_custo']) * 100
        rr(c, margin, y - 14*mm, cw, 14*mm, 6, GOLD_LT, GOLD, 0.8)
        c.setFillColor(colors.HexColor("#7A5C1A"))
        c.setFont("Helvetica", 9)
        c.drawString(margin + 5*mm, y - 5.5*mm, "Margem sobre o faturamento total do projeto")
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(margin + cw - 5*mm, y - 9*mm, f"{pct:.1f}%".replace(".", ","))
    _footer(c, margin)
    c.save()

def gerar_pdf_cliente(dados, output_path):
    """Relatório de serviço para o cliente."""
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Relatório de Serviço", f"#{dados['proposta_id']}", margin)
    y = _info_cards(c, margin, cw, [
        ("Cliente",  dados.get('cliente', '')),
        ("Telefone", dados.get('telefone', '')),
        ("Tipo",     dados.get('tipo', '')),
        ("Status",   dados.get('status', '')),
    ])
    rr(c, margin, y - 12*mm, cw, 12*mm, 4, GOLD_LT, GOLD, 0.5)
    c.setFillColor(colors.HexColor("#7A5C1A"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 5*mm, y - 4*mm, "Descrição do serviço")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 5*mm, y - 9.5*mm, dados.get('descricao', ''))
    y -= 22*mm
    y = _section_title(c, margin, cw, y, "Itens Inclusos",
        "Todos os itens e serviços prestados nesta proposta", NAVY)
    y = _table_rows(c, margin, cw, y, dados.get('itens', []))
    _total_row(c, margin, cw, y, "TOTAL DO SERVIÇO",
        dados['total'], NAVY, WHITE, GOLD)
    _footer(c, margin)
    c.save()

def gerar_pdf_fornecedores(dados, output_path):
    """Relatório de fornecedores do projeto."""
    c = canvas.Canvas(output_path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Relatório de Fornecedores", f"#{dados['proposta_id']}", margin)
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
        dados['total'], TEAL, WHITE, colors.HexColor("#A8DDE8"))
    _footer(c, margin)
    c.save()

def gerar_pdf_venda(venda, cliente, itens_venda, filename, proposta_descricao=None):
    """Relatório de venda avulsa — mantém compatibilidade com interface antigo."""
    # Preparar dados no formato esperado pela nova função
    
    # Extrair ID de venda
    if isinstance(venda, dict):
        venda_id = venda.get('id', '')
    else:
        venda_id = getattr(venda, 'id', '')
    
    # Extrair nome do cliente
    if isinstance(cliente, dict):
        cliente_nome = cliente.get('nome', '')
    else:
        cliente_nome = getattr(cliente, 'nome', '')
    
    # Extrair data
    if isinstance(venda, dict):
        data = venda.get('data_venda', '')
    else:
        data = str(getattr(venda, 'data_venda', ''))
    
    # Extrair status
    if isinstance(venda, dict):
        status = venda.get('status', '')
    else:
        status = getattr(venda, 'status', '')
    
    # Extrair forma de pagamento
    if isinstance(venda, dict):
        forma_pagamento = venda.get('forma_pagamento', '')
    else:
        forma_pagamento = getattr(venda, 'forma_pagamento', '')
    
    # Extrair total
    if isinstance(venda, dict):
        total = venda.get('valor_total', 0)
    else:
        total = getattr(venda, 'valor_total', 0)
    
    # Processar itens — podem ser tuples, dicts ou objetos
    itens_processados = []
    if itens_venda:
        for i in itens_venda:
            if isinstance(i, tuple):
                # Formato tuple: (nome, valor, is_negativo)
                nome = i[0]
                valor = i[1]
                is_neg = i[2] if len(i) > 2 else False
            elif isinstance(i, dict):
                # Formato dict
                nome = i.get('descricao', i.get('produto_nome', i.get('nome', '')))
                valor = i.get('subtotal', i.get('valor', 0))
                is_neg = False
            else:
                # Formato objeto
                nome = getattr(i, 'descricao', getattr(i, 'produto_nome', getattr(i, 'nome', '')))
                valor = getattr(i, 'subtotal', getattr(i, 'valor', 0))
                is_neg = False
            itens_processados.append((nome, valor, is_neg))
    
    dados = {
        'venda_id': venda_id,
        'cliente': cliente_nome,
        'data': data,
        'status': status,
        'forma_pagamento': forma_pagamento,
        'itens': itens_processados,
        'total': total
    }
    
    c = canvas.Canvas(filename, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin
    _header(c, "Comprovante de Venda", f"#{dados.get('venda_id','')}", margin)
    y = _info_cards(c, margin, cw, [
        ("Cliente", dados.get('cliente', '')),
        ("Data",    dados.get('data', '')),
        ("Status",  dados.get('status', '')),
        ("Forma",   dados.get('forma_pagamento', '')),
    ])
    y = _section_title(c, margin, cw, y, "Itens da Venda",
        "Produtos e quantidades desta venda", NAVY)
    y = _table_rows(c, margin, cw, y, dados.get('itens', []))
    _total_row(c, margin, cw, y, "TOTAL DA VENDA",
        dados['total'], NAVY, WHITE, GOLD)
    _footer(c, margin)
    c.save()


def gerar_pdf_venda(venda_dados, cliente_dados, itens_df, filename):
    """
    Gera PDF de venda/produtos da proposta com design Navy/Gold
    
    Args:
        venda_dados: dict com id, status, forma_pagamento, valor_total, data_venda, observacoes
        cliente_dados: dict com nome, email (opcional)
        itens_df: DataFrame com colunas: produto_nome, quantidade, preco_unitario
        filename: caminho do arquivo PDF a ser gerado
    
    Returns:
        str: caminho do arquivo gerado
    """
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=A4)
    margin = 30*mm
    cw = W - 2*margin
    
    # Cabeçalho
    _header(c, "Produtos da Proposta", f"#{venda_dados.get('id','')}", margin)
    
    # Informações da venda
    y = _info_cards(c, margin, cw, [
        ("Cliente", cliente_dados.get('nome', 'N/A')),
        ("Data", venda_dados.get('data_venda', datetime.now().strftime('%d/%m/%Y'))),
        ("Status", venda_dados.get('status', 'Proposta')),
        ("Forma de Pagamento", venda_dados.get('forma_pagamento', 'A definir')),
    ])
    
    # Seção de itens
    y = _section_title(c, margin, cw, y, "Produtos Inclusos", 
        "Lista de produtos e quantidades", NAVY)
    
    # Preparar itens para a tabela
    itens_lista = []
    if isinstance(itens_df, pd.DataFrame) and not itens_df.empty:
        for _, row in itens_df.iterrows():
            nome = str(row.get('produto_nome', row.get('nome', 'Produto')))
            qtd = int(row.get('quantidade', 1))
            valor = float(row.get('preco_unitario', row.get('valor', 0)))
            itens_lista.append({
                'descricao': nome,
                'quantidade': qtd,
                'valor': valor,
                'total': qtd * valor
            })
    
    # Renderizar tabela
    y = _table_rows(c, margin, cw, y, itens_lista)
    
    # Total
    total = venda_dados.get('valor_total', 0)
    _total_row(c, margin, cw, y, "TOTAL DA PROPOSTA", total, NAVY, WHITE, GOLD)
    
    # Rodapé
    _footer(c, margin)
    
    c.save()
    return filename
