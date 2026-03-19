from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

W, H = A4

# Paleta
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

def rr(c, x, y, w, h, r, fill, stroke=None, sw=0.5):
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.setLineWidth(sw)
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    c.drawPath(p, fill=1, stroke=1 if stroke else 0)
    c.restoreState()

def fmt(v):
    return f"R$ {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def header(c, titulo, subtitulo, proposta, margin, content_w):
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
    c.drawString(margin, H - 32*mm, subtitulo)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 9)
    c.drawString(margin, H - 40*mm, "Gerado em 16/03/2026  ·  Tâmara Cavalcante  ·  @tamaraorganiza")

def info_cards(c, margin, content_w, infos):
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
        c.drawString(cx + 4*mm, top_y - 14*mm, value)
    return top_y - card_h - 10*mm

def section_title(c, margin, content_w, y, titulo, subtitulo, line_color):
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

def table_rows(c, margin, content_w, start_y, items, row_h=9*mm):
    y = start_y
    for idx, (nome, valor, is_neg) in enumerate(items):
        bg = GRAY1 if idx % 2 == 0 else WHITE
        rr(c, margin, y - row_h + 1.5*mm, content_w, row_h - 1*mm, 3, bg)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 10)
        c.drawString(margin + 4*mm, y - 4.5*mm, nome)
        c.setFillColor(RED if is_neg else DARK)
        c.setFont("Helvetica-Bold", 10)
        prefix = "– " if is_neg else ""
        c.drawRightString(margin + content_w - 4*mm, y - 4.5*mm, prefix + fmt(valor))
        y -= row_h
    return y

def total_row(c, margin, content_w, y, label, valor, bg, text_color, val_color, row_h=9*mm):
    rr(c, margin, y - row_h + 1*mm, content_w, row_h, 4, bg)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(margin + 4*mm, y - 4.5*mm, label)
    c.setFillColor(val_color)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(margin + content_w - 4*mm, y - 4.5*mm, fmt(valor))
    return y - row_h

def margem_block(c, margin, content_w, y, pct):
    rr(c, margin, y - 14*mm, content_w, 14*mm, 6, GOLD_LT, GOLD, 0.8)
    c.setFillColor(colors.HexColor("#7A5C1A"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 5*mm, y - 5.5*mm, "Margem sobre o faturamento total do projeto")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(margin + content_w - 5*mm, y - 9*mm, f"{pct:.1f}%".replace(".", ","))

def footer(c, margin):
    c.setFillColor(GRAY2)
    c.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8)
    c.drawString(margin, 5*mm, "Documento de uso interno — Planner Organizer")
    c.drawRightString(W - margin, 5*mm, "Tâmara Cavalcante  ·  @tamaraorganiza")

# ══════════════════════════════════════════════════════════════
# 1. RELATÓRIO INTERNO
# ══════════════════════════════════════════════════════════════
def gerar_interno(path):
    c = canvas.Canvas(path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin

    header(c, "Relatório Interno", "Tâmara Cavalcante  ·  Personal Organizer  ·  @tamaraorganiza", "#104", margin, cw)

    y = info_cards(c, margin, cw, [
        ("Cliente",  "Keila"),
        ("Tipo",     "Organização"),
        ("Status",   "Finalizada"),
        ("Período",  "09 – 11/03/2026"),
    ])

    # Custo total
    y = section_title(c, margin, cw, y, "Custo Total do Cliente",
        "Todos os valores cobrados ao cliente nesta proposta", GOLD)
    y = table_rows(c, margin, cw, y, [
        ("Personal Organizer", 3000.00, False),
        ("Produtos",            550.80, False),
        ("Fornecedores",       6729.97, False),
        ("Outros",              785.60, False),
    ])
    total_custo = 11066.37
    y = total_row(c, margin, cw, y, "CUSTO TOTAL DO CLIENTE", total_custo, NAVY, WHITE, GOLD)

    y -= 12*mm

    # Receita líquida
    y = section_title(c, margin, cw, y, "Receita Líquida do Projeto",
        "Ganho real da Personal, considerando comissões, lucro em produtos e pagamentos", GREEN)
    y = table_rows(c, margin, cw, y, [
        ("Personal Organizer",   3000.00, False),
        ("Comissões",             336.50, False),
        ("Lucro em Produtos",     275.40, False),
        ("Outros",                785.60, False),
        ("Pagamento Assistentes",1340.00, True),
    ])
    total_receita = 3057.50
    y = total_row(c, margin, cw, y, "RECEITA LÍQUIDA TOTAL", total_receita, GREEN, WHITE, GREEN_LT)

    y -= 10*mm
    margem_block(c, margin, cw, y, (total_receita / total_custo) * 100)

    footer(c, margin)
    c.save()
    print("✅ Relatório Interno gerado")

# ══════════════════════════════════════════════════════════════
# 2. RELATÓRIO DE FORNECEDORES
# ══════════════════════════════════════════════════════════════
def gerar_fornecedores(path):
    c = canvas.Canvas(path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin

    header(c, "Relatório de Fornecedores", "Tâmara Cavalcante  ·  Personal Organizer  ·  @tamaraorganiza", "#104", margin, cw)

    y = info_cards(c, margin, cw, [
        ("Cliente",    "Keila"),
        ("Telefone",   "31 99148-4882"),
        ("Tipo",       "Organização"),
        ("Status",     "Finalizada"),
    ])

    # Fornecedores
    y = section_title(c, margin, cw, y, "Fornecedores",
        "Valores pagos a fornecedores neste projeto", TEAL)

    y = table_rows(c, margin, cw, y, [
        ("Fornecimento de Laluc",      4643.81, False),
        ("Fornecimento de Multicoisas",2086.16, False),
    ])
    total = 6729.97
    y = total_row(c, margin, cw, y, "TOTAL FORNECEDORES", total, TEAL, WHITE,
                  colors.HexColor("#A8DDE8"))

    # Bloco info
    y -= 12*mm
    rr(c, margin, y - 20*mm, cw, 20*mm, 6, TEAL_LT, colors.HexColor("#5DAAB8"), 0.5)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 5*mm, y - 7*mm, "2 fornecedores envolvidos neste projeto")
    c.setFillColor(colors.HexColor("#0F5E6E"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 5*mm, y - 13*mm, "Laluc representa 69% do custo total de fornecedores")

    footer(c, margin)
    c.save()
    print("✅ Relatório de Fornecedores gerado")

# ══════════════════════════════════════════════════════════════
# 3. RELATÓRIO DO CLIENTE (Serviço)
# ══════════════════════════════════════════════════════════════
def gerar_cliente(path):
    c = canvas.Canvas(path, pagesize=A4)
    margin = 18*mm
    cw = W - 2*margin

    header(c, "Relatório de Serviço", "Tâmara Cavalcante  ·  Personal Organizer  ·  @tamaraorganiza", "#104", margin, cw)

    y = info_cards(c, margin, cw, [
        ("Cliente",   "Keila"),
        ("Telefone",  "31 99148-4882"),
        ("Tipo",      "Organização"),
        ("Status",    "Finalizada"),
    ])

    # Descrição do serviço
    rr(c, margin, y - 12*mm, cw, 12*mm, 4, GOLD_LT, GOLD, 0.5)
    c.setFillColor(colors.HexColor("#7A5C1A"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 5*mm, y - 4*mm, "Descrição do serviço")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 5*mm, y - 9.5*mm, "Serviço de Personal Organizer")
    y -= 22*mm

    # Itens inclusos
    y = section_title(c, margin, cw, y, "Itens Inclusos",
        "Todos os itens e serviços prestados nesta proposta", NAVY)

    items = [
        ("Personal Organizer — Organização", 3000.00, False),
        ("Transporte — combustível",           285.60, False),
        ("Treinamento Funcionária (2h)",        500.00, False),
        ("Organza G (45x)",                    202.50, False),
        ("Colmeia M Legging (9x)",             348.30, False),
    ]
    y = table_rows(c, margin, cw, y, items)

    total = 4336.40
    y = total_row(c, margin, cw, y, "TOTAL DO SERVIÇO", total, NAVY, WHITE, GOLD)

    # Nota de valor base
    y -= 10*mm
    rr(c, margin, y - 16*mm, cw, 16*mm, 6, GRAY1, GRAY2, 0.5)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8.5)
    c.drawString(margin + 5*mm, y - 5*mm, "Valor base do serviço de Personal Organizer")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 5*mm, y - 12*mm, "R$ 3.000,00")
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(margin + cw - 5*mm, y - 8.5*mm, "Adicionais: R$ 1.336,40")

    footer(c, margin)
    c.save()
    print("✅ Relatório de Serviço (Cliente) gerado")

# ── Gerar todos ───────────────────────────────────────────────
gerar_interno(     "/mnt/user-data/outputs/Relatorio_Interno_104_Keila.pdf")
gerar_fornecedores("/mnt/user-data/outputs/Relatorio_Fornecedores_104_Keila.pdf")
gerar_cliente(     "/mnt/user-data/outputs/Relatorio_Servico_104_Keila.pdf")
