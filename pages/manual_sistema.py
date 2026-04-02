import os
import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.graphics.shapes import Drawing, Line, Rect, Circle, String, Group
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

NAVY_RGB = colors.HexColor('#0D1B2A')
NAVY_LIGHT_RGB = colors.HexColor('#162840')
GOLD_RGB = colors.HexColor('#C9A84C')
GOLD_DARK_RGB = colors.HexColor('#B8943D')
GOLD_LIGHT_RGB = colors.HexColor('#F5ECD7')
GREEN_RGB = colors.HexColor('#38A169')
GREEN_LIGHT_RGB = colors.HexColor('#C6F6D5')
BLUE_RGB = colors.HexColor('#3182CE')
ORANGE_RGB = colors.HexColor('#DD6B20')
WHITE = colors.white
GRAY_TEXT = colors.HexColor('#4A5568')
GRAY_LIGHT = colors.HexColor('#E2E8F0')
GRAY_BG = colors.HexColor('#F7FAFC')
GRAY_DARK = colors.HexColor('#2D3748')


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY_RGB)
    canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(0, h - 31, w, 3, fill=1, stroke=0)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(72, h - 20, "PLANNER ORGANIZER")
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#A0AEC0'))
    canvas.drawRightString(w - 72, h - 20, "Manual do Sistema")
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(0, 30, w, 2, fill=1, stroke=0)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(GRAY_TEXT)
    canvas.drawString(72, 16, f"\u00a9 {datetime.now().year} Planner Organizer \u2014 Todos os direitos reservados")
    canvas.drawRightString(w - 72, 16, f"P\u00e1gina {doc.page}")
    canvas.restoreState()


def _first_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY_RGB)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(60, h / 2 + 80, w - 120, 3, fill=1, stroke=0)
    canvas.setFont('Helvetica-Bold', 32)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(w / 2, h / 2 + 110, "PLANNER ORGANIZER")
    canvas.setFont('Helvetica', 14)
    canvas.setFillColor(GOLD_RGB)
    canvas.drawCentredString(w / 2, h / 2 + 50, "MANUAL COMPLETO DO SISTEMA")
    canvas.setFont('Helvetica', 11)
    canvas.setFillColor(colors.HexColor('#94A3B8'))
    canvas.drawCentredString(w / 2, h / 2 + 10, "Guia detalhado de funcionalidades e opera\u00e7\u00f5es")
    canvas.drawCentredString(w / 2, h / 2 - 10, "para Personal Organizers")
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(60, h / 2 - 40, w - 120, 1, fill=1, stroke=0)
    canvas.setFont('Helvetica', 10)
    canvas.setFillColor(colors.HexColor('#64748B'))
    canvas.drawCentredString(w / 2, h / 2 - 70, f"Vers\u00e3o 1.0.4  \u2022  {datetime.now().strftime('%B %Y')}")
    canvas.restoreState()


def _draw_benefit_card(x, y, icon_text, title, desc, accent_color):
    d = Drawing(220, 80)
    d.add(Rect(0, 0, 215, 76, rx=8, ry=8, fillColor=WHITE, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
    d.add(Rect(0, 0, 4, 76, fillColor=accent_color, strokeColor=accent_color, strokeWidth=0))
    d.add(String(14, 52, icon_text, fontSize=18, fillColor=accent_color, fontName='Helvetica'))
    d.add(String(38, 54, title, fontSize=10, fillColor=NAVY_RGB, fontName='Helvetica-Bold'))
    words = desc.split()
    line1 = []
    line2 = []
    current = line1
    for w_item in words:
        test = ' '.join(current + [w_item])
        if len(test) > 34 and current is line1:
            current = line2
        current.append(w_item)
    d.add(String(14, 32, ' '.join(line1), fontSize=8, fillColor=GRAY_TEXT, fontName='Helvetica'))
    if line2:
        d.add(String(14, 20, ' '.join(line2), fontSize=8, fillColor=GRAY_TEXT, fontName='Helvetica'))
    return d


def _draw_flow_diagram():
    d = Drawing(470, 70)
    statuses = [
        ("Em elabora\u00e7\u00e3o", colors.HexColor('#718096')),
        ("Aguardando", GOLD_RGB),
        ("Aprovada", BLUE_RGB),
        ("Em execu\u00e7\u00e3o", ORANGE_RGB),
        ("Finalizada", GREEN_RGB),
    ]
    box_w = 78
    gap = 10
    arrow_len = gap
    total_w = len(statuses) * box_w + (len(statuses) - 1) * gap
    start_x = (470 - total_w) / 2
    y = 20
    for i, (label, col) in enumerate(statuses):
        x = start_x + i * (box_w + gap)
        d.add(Rect(x, y, box_w, 30, rx=6, ry=6, fillColor=col, strokeColor=col, strokeWidth=0))
        d.add(String(x + box_w / 2, y + 11, label, fontSize=7.5, fillColor=WHITE,
                     fontName='Helvetica-Bold', textAnchor='middle'))
        if i < len(statuses) - 1:
            ax = x + box_w + 1
            d.add(Line(ax, y + 15, ax + arrow_len - 2, y + 15, strokeColor=GOLD_RGB, strokeWidth=1.5))
            d.add(Line(ax + arrow_len - 5, y + 18, ax + arrow_len - 2, y + 15, strokeColor=GOLD_RGB, strokeWidth=1.5))
            d.add(Line(ax + arrow_len - 5, y + 12, ax + arrow_len - 2, y + 15, strokeColor=GOLD_RGB, strokeWidth=1.5))
    d.add(String(235, 58, "Fluxo de Status das Propostas", fontSize=9, fillColor=NAVY_RGB,
                 fontName='Helvetica-Bold', textAnchor='middle'))
    return d


def _draw_pos_org_timeline():
    d = Drawing(470, 140)
    d.add(String(235, 128, "Jornada P\u00f3s-Organiza\u00e7\u00e3o \u2014 Timeline de Atendimento",
                 fontSize=9, fillColor=NAVY_RGB, fontName='Helvetica-Bold', textAnchor='middle'))
    etapas = [
        ("D+1", "\U0001F64F", "Agradecimento", "Mensagem elegante de encerramento"),
        ("D+7", "\U0001F4DE", "Acompanhamento", "Saber como a cliente est\u00e1"),
        ("D+30", "\U0001F527", "Ajuste Fino", "Visita gratuita para ajustes"),
        ("D+45", "\U0001F4AC", "Feedback", "Colher opini\u00e3o da experi\u00eancia"),
        ("D+60", "\U0001F91D", "Continuidade", "Oferta de servi\u00e7o cont\u00ednuo"),
    ]
    line_y = 85
    d.add(Line(30, line_y, 440, line_y, strokeColor=GOLD_RGB, strokeWidth=2))
    for i, (dia, emoji, nome, desc) in enumerate(etapas):
        cx = 50 + i * 98
        d.add(Circle(cx, line_y, 8, fillColor=NAVY_RGB, strokeColor=GOLD_RGB, strokeWidth=1.5))
        d.add(String(cx, line_y - 3, dia, fontSize=6, fillColor=WHITE,
                     fontName='Helvetica-Bold', textAnchor='middle'))
        d.add(String(cx, line_y + 16, nome, fontSize=7.5, fillColor=NAVY_RGB,
                     fontName='Helvetica-Bold', textAnchor='middle'))
        words = desc.split()
        l1 = []
        l2 = []
        cur = l1
        for w_item in words:
            test = ' '.join(cur + [w_item])
            if len(test) > 18 and cur is l1:
                cur = l2
            cur.append(w_item)
        d.add(String(cx, line_y - 22, ' '.join(l1), fontSize=6.5, fillColor=GRAY_TEXT,
                     fontName='Helvetica', textAnchor='middle'))
        if l2:
            d.add(String(cx, line_y - 32, ' '.join(l2), fontSize=6.5, fillColor=GRAY_TEXT,
                         fontName='Helvetica', textAnchor='middle'))
    return d


def _draw_kanban_diagram():
    d = Drawing(470, 105)
    d.add(String(235, 92, "Painel Financeiro Kanban \u2014 Vis\u00e3o de Controle",
                 fontSize=9, fillColor=NAVY_RGB, fontName='Helvetica-Bold', textAnchor='middle'))
    cols = [
        ("\U0001F4B0 A Receber", BLUE_RGB, ["Valor base proposta", "Vendas de produtos", "Outros cr\u00e9ditos"]),
        ("\U0001F4B3 A Pagar", ORANGE_RGB, ["Comiss\u00f5es fornecedores", "Pagto. assistentes", "Outros d\u00e9bitos"]),
        ("\u2705 Aprovadas/Pagas", GREEN_RGB, ["Receitas recebidas", "Despesas quitadas", "Hist\u00f3rico completo"]),
    ]
    col_w = 140
    gap = 14
    start_x = (470 - (3 * col_w + 2 * gap)) / 2
    for i, (titulo, cor, itens) in enumerate(cols):
        x = start_x + i * (col_w + gap)
        d.add(Rect(x, 0, col_w, 78, rx=6, ry=6, fillColor=GRAY_BG, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
        d.add(Rect(x, 62, col_w, 16, rx=6, ry=6, fillColor=cor, strokeColor=cor, strokeWidth=0))
        d.add(Rect(x, 62, col_w, 8, fillColor=cor, strokeColor=cor, strokeWidth=0))
        d.add(String(x + col_w / 2, 66, titulo, fontSize=7.5, fillColor=WHITE,
                     fontName='Helvetica-Bold', textAnchor='middle'))
        for j, item in enumerate(itens):
            iy = 44 - j * 16
            d.add(Rect(x + 6, iy, col_w - 12, 13, rx=3, ry=3, fillColor=WHITE,
                       strokeColor=GRAY_LIGHT, strokeWidth=0.3))
            d.add(String(x + 12, iy + 3, item, fontSize=7, fillColor=GRAY_TEXT, fontName='Helvetica'))
    return d


def _draw_integration_diagram():
    d = Drawing(470, 115)
    d.add(String(235, 103, "Integra\u00e7\u00e3o Autom\u00e1tica entre M\u00f3dulos",
                 fontSize=9, fillColor=NAVY_RGB, fontName='Helvetica-Bold', textAnchor='middle'))
    cx, cy = 235, 48
    d.add(Circle(cx, cy, 28, fillColor=NAVY_RGB, strokeColor=GOLD_RGB, strokeWidth=2))
    d.add(String(cx, cy + 5, "Proposta", fontSize=8, fillColor=WHITE,
                 fontName='Helvetica-Bold', textAnchor='middle'))
    d.add(String(cx, cy - 7, "Finalizada", fontSize=7, fillColor=GOLD_RGB,
                 fontName='Helvetica', textAnchor='middle'))
    targets = [
        (80, 80, "Vendas", GREEN_RGB),
        (80, 16, "Receitas", BLUE_RGB),
        (390, 80, "Comiss\u00f5es", ORANGE_RGB),
        (390, 16, "Pagamentos", colors.HexColor('#805AD5')),
    ]
    for tx, ty, label, col in targets:
        d.add(Line(cx + (28 if tx > cx else -28), cy + (5 if ty > cy else -5),
                   tx + (25 if tx < cx else -25), ty, strokeColor=GOLD_RGB, strokeWidth=1))
        d.add(Rect(tx - 30, ty - 12, 60, 24, rx=5, ry=5, fillColor=col, strokeColor=col, strokeWidth=0))
        d.add(String(tx, ty - 3, label, fontSize=7.5, fillColor=WHITE,
                     fontName='Helvetica-Bold', textAnchor='middle'))
    return d


def _draw_control_dashboard():
    d = Drawing(470, 85)
    d.add(String(235, 74, "Controle Operacional \u2014 Indicadores em Tempo Real",
                 fontSize=9, fillColor=NAVY_RGB, fontName='Helvetica-Bold', textAnchor='middle'))
    cards_data = [
        ("Propostas Ativas", "12", NAVY_RGB),
        ("Receita Prevista", "R$ 45.800", GREEN_RGB),
        ("A Pagar", "R$ 12.350", ORANGE_RGB),
        ("Saldo Projetado", "R$ 33.450", BLUE_RGB),
    ]
    card_w = 105
    gap = 10
    start_x = (470 - (4 * card_w + 3 * gap)) / 2
    for i, (label, valor, cor) in enumerate(cards_data):
        x = start_x + i * (card_w + gap)
        d.add(Rect(x, 0, card_w, 55, rx=6, ry=6, fillColor=WHITE, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
        d.add(Rect(x, 0, card_w, 4, fillColor=cor, strokeColor=cor, strokeWidth=0))
        d.add(String(x + card_w / 2, 35, valor, fontSize=13, fillColor=cor,
                     fontName='Helvetica-Bold', textAnchor='middle'))
        d.add(String(x + card_w / 2, 15, label, fontSize=7, fillColor=GRAY_TEXT,
                     fontName='Helvetica', textAnchor='middle'))
    return d


def gerar_manual_sistema():
    import streamlit as st
    from utils.auth_guard import require_auth
    require_auth()
    pdf_dir = "pdfs"
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    pdf_path = os.path.join(pdf_dir, "Manual_Planner_Organizer.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=52,
        bottomMargin=50
    )

    estilos = getSampleStyleSheet()

    st_titulo = ParagraphStyle(
        'ManualTitulo', parent=estilos['Heading1'],
        fontSize=20, textColor=NAVY_RGB, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=24, alignment=TA_LEFT
    )
    st_subtitulo = ParagraphStyle(
        'ManualSubtitulo', parent=estilos['Heading2'],
        fontSize=14, textColor=GOLD_DARK_RGB, fontName='Helvetica-Bold',
        spaceAfter=8, spaceBefore=18
    )
    st_secao = ParagraphStyle(
        'ManualSecao', parent=estilos['Heading3'],
        fontSize=12, textColor=NAVY_RGB, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=14
    )
    st_texto = ParagraphStyle(
        'ManualTexto', parent=estilos['Normal'],
        fontSize=10, textColor=GRAY_TEXT, leading=15,
        spaceAfter=5, alignment=TA_JUSTIFY
    )
    st_bullet = ParagraphStyle(
        'ManualBullet', parent=st_texto,
        leftIndent=18, bulletIndent=6, spaceAfter=4
    )
    st_sub_bullet = ParagraphStyle(
        'ManualSubBullet', parent=st_texto,
        leftIndent=36, bulletIndent=24, spaceAfter=3,
        fontSize=9.5
    )
    st_destaque = ParagraphStyle(
        'ManualDestaque', parent=st_texto,
        backColor=GOLD_LIGHT_RGB, borderPadding=(8, 10, 8, 10),
        leftIndent=12, rightIndent=12, spaceAfter=10, spaceBefore=8,
        fontSize=10, textColor=NAVY_RGB, leading=15
    )
    st_destaque_navy = ParagraphStyle(
        'ManualDestaqueNavy', parent=st_texto,
        backColor=colors.HexColor('#EDF2F7'), borderPadding=(8, 10, 8, 10),
        leftIndent=12, rightIndent=12, spaceAfter=10, spaceBefore=8,
        fontSize=10, textColor=NAVY_RGB, leading=15
    )
    st_rodape = ParagraphStyle(
        'ManualRodape', parent=estilos['Normal'],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER
    )

    e = []

    def _gold_line():
        d = Drawing(480, 4)
        line = Line(0, 2, 470, 2)
        line.strokeColor = GOLD_RGB
        line.strokeWidth = 1.5
        d.add(line)
        e.append(d)
        e.append(Spacer(1, 8))

    def _gray_line():
        d = Drawing(480, 2)
        line = Line(0, 1, 470, 1)
        line.strokeColor = GRAY_LIGHT
        line.strokeWidth = 0.5
        d.add(line)
        e.append(d)
        e.append(Spacer(1, 6))

    def _navy_table(dados, col_widths=None):
        if col_widths is None:
            col_widths = [120, 350]
        t = Table(dados, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_RGB),
            ('TEXTCOLOR', (0, 0), (-1, 0), GOLD_RGB),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), GRAY_TEXT),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        e.append(t)
        e.append(Spacer(1, 12))

    def _bullet(texto):
        e.append(Paragraph(f"<bullet>&bull;</bullet> {texto}", st_bullet))

    def _sub_bullet(texto):
        e.append(Paragraph(f"<bullet>\u2013</bullet> {texto}", st_sub_bullet))

    e.append(PageBreak())

    # ── INTRODUÇÃO ─────────────────────────────────────────────────────
    e.append(Paragraph("Introdu\u00e7\u00e3o", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O <b>Planner Organizer</b> \u00e9 uma plataforma de gest\u00e3o empresarial desenvolvida "
        "exclusivamente para <b>Personal Organizers</b>. O sistema centraliza todas as "
        "opera\u00e7\u00f5es do seu neg\u00f3cio \u2014 desde a capta\u00e7\u00e3o de clientes e "
        "elabora\u00e7\u00e3o de propostas at\u00e9 o controle financeiro completo e o "
        "acompanhamento p\u00f3s-organiza\u00e7\u00e3o \u2014 em um \u00fanico ambiente digital integrado.",
        st_texto
    ))
    e.append(Paragraph(
        "Projetado para eliminar planilhas dispersas e processos manuais, o Planner Organizer "
        "automatiza tarefas repetitivas, gera relat\u00f3rios profissionais em PDF e oferece "
        "visibilidade em tempo real sobre a sa\u00fade financeira do seu neg\u00f3cio.",
        st_texto
    ))
    e.append(Spacer(1, 10))

    # ── BENEFÍCIOS ─────────────────────────────────────────────────────
    e.append(Paragraph("Benef\u00edcios para o seu Neg\u00f3cio", st_titulo))
    _gold_line()

    benefits_row1 = Table([[
        _draw_benefit_card(0, 0, "\u23f1", "Economia de Tempo",
                           "Automatiza\u00e7\u00f5es eliminam trabalho manual repetitivo e retrabalho", GOLD_RGB),
        _draw_benefit_card(0, 0, "\U0001F4B0", "Controle Financeiro",
                           "Vis\u00e3o completa de receitas, despesas e saldo projetado em tempo real", GREEN_RGB),
    ]], colWidths=[235, 235])
    benefits_row1.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    e.append(benefits_row1)
    e.append(Spacer(1, 8))

    benefits_row2 = Table([[
        _draw_benefit_card(0, 0, "\U0001F4C4", "Relat\u00f3rios Profissionais",
                           "PDFs com design Navy & Gold prontos para enviar aos seus clientes", BLUE_RGB),
        _draw_benefit_card(0, 0, "\U0001F91D", "Fideliza\u00e7\u00e3o de Clientes",
                           "Jornada p\u00f3s-organiza\u00e7\u00e3o com 6 etapas autom\u00e1ticas de follow-up", ORANGE_RGB),
    ]], colWidths=[235, 235])
    benefits_row2.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    e.append(benefits_row2)
    e.append(Spacer(1, 8))

    benefits_row3 = Table([[
        _draw_benefit_card(0, 0, "\U0001F504", "Integra\u00e7\u00e3o Total",
                           "Propostas, vendas e finan\u00e7as conectados automaticamente sem duplicidade", NAVY_RGB),
        _draw_benefit_card(0, 0, "\U0001F512", "Seguran\u00e7a Multi-Tenant",
                           "Cada usu\u00e1rio acessa apenas seus pr\u00f3prios dados com autentica\u00e7\u00e3o segura",
                           colors.HexColor('#805AD5')),
    ]], colWidths=[235, 235])
    benefits_row3.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    e.append(benefits_row3)
    e.append(Spacer(1, 10))

    e.append(Paragraph(
        "<b>Resultado:</b> Menos tempo em tarefas administrativas, mais tempo para transformar "
        "ambientes e encantar clientes. O Planner Organizer cuida da gest\u00e3o para que voc\u00ea "
        "possa focar no que faz de melhor.",
        st_destaque
    ))
    e.append(Spacer(1, 6))

    # ── ARQUITETURA ────────────────────────────────────────────────────
    e.append(Paragraph("Arquitetura do Sistema", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O sistema \u00e9 organizado em m\u00f3dulos independentes, por\u00e9m integrados. "
        "A navega\u00e7\u00e3o \u00e9 feita pelo menu lateral, sempre vis\u00edvel em todas as telas:",
        st_texto
    ))
    _navy_table([
        ["M\u00f3dulo", "Descri\u00e7\u00e3o"],
        ["\U0001F4CA Dashboard", "P\u00e1gina inicial com m\u00e9tricas, alertas de prazos, gr\u00e1ficos e indicadores financeiros em tempo real."],
        ["\U0001F465 Cadastros", "Base centralizada de clientes, fornecedores, parceiros e assistentes para todas as opera\u00e7\u00f5es."],
        ["\U0001F4DD Propostas", "Ciclo completo: elabora\u00e7\u00e3o, precifica\u00e7\u00e3o com itens, acompanhamento por status e finaliza\u00e7\u00e3o autom\u00e1tica."],
        ["\U0001F6D2 Vendas", "Produtos vendidos por cliente, com vincula\u00e7\u00e3o autom\u00e1tica a propostas e gera\u00e7\u00e3o de receitas."],
        ["\U0001F4B0 Financeiro", "Painel Kanban \u2014 contas a receber, a pagar e aprovadas/pagas com filtros e an\u00e1lise visual."],
        ["\U0001F4CB P\u00f3s-Organiza\u00e7\u00e3o", "Jornada de 6 etapas de follow-up p\u00f3s-projeto para fideliza\u00e7\u00e3o."],
        ["\U0001F4C8 Relat\u00f3rios", "An\u00e1lises com gr\u00e1ficos interativos, comparativos e exporta\u00e7\u00e3o de dados."],
        ["\U0001F9D1\u200D\U0001F4BC Perfil", "Configura\u00e7\u00f5es pessoais da conta e prefer\u00eancias do sistema."],
    ])

    e.append(PageBreak())

    # ── 1. DASHBOARD ───────────────────────────────────────────────────
    e.append(Paragraph("1. Dashboard", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O Dashboard \u00e9 a vis\u00e3o executiva do seu neg\u00f3cio. Ao acessar o sistema, "
        "voc\u00ea encontra imediatamente os indicadores mais importantes para a tomada de decis\u00e3o.",
        st_texto
    ))
    e.append(Spacer(1, 6))
    e.append(_draw_control_dashboard())
    e.append(Spacer(1, 8))
    e.append(Paragraph("M\u00e9tricas e Alertas", st_secao))
    _bullet("Cards de resumo: total de propostas ativas, receita prevista, valores em aberto e saldo projetado")
    _bullet("Atualiza\u00e7\u00e3o em tempo real conforme propostas s\u00e3o criadas, aprovadas ou finalizadas")
    _bullet("Alertas autom\u00e1ticos para propostas pr\u00f3ximas do prazo (60 dias)")
    _bullet("Notifica\u00e7\u00e3o visual de propostas em atraso ou pendentes de aprova\u00e7\u00e3o")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Gr\u00e1ficos e Visualiza\u00e7\u00f5es", st_secao))
    _bullet("Distribui\u00e7\u00e3o de propostas por status com gr\u00e1ficos de pizza")
    _bullet("Evolu\u00e7\u00e3o de receitas ao longo do tempo com gr\u00e1ficos de tend\u00eancia")
    _bullet("Comparativo receitas vs. despesas e saldo projetado")
    e.append(Spacer(1, 10))

    # ── 2. CADASTROS ───────────────────────────────────────────────────
    e.append(Paragraph("2. Cadastros", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "A base de dados centralizada do sistema. Todas as entidades ficam dispon\u00edveis "
        "automaticamente nos demais m\u00f3dulos.",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Clientes", st_secao))
    _bullet("Cadastro completo com nome, e-mail, telefone, endere\u00e7o e observa\u00e7\u00f5es")
    _bullet("Hist\u00f3rico autom\u00e1tico: propostas, vendas e transa\u00e7\u00f5es vinculadas")
    _bullet("Busca e filtros para localizar clientes rapidamente")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Fornecedores", st_secao))
    _bullet("Cadastro com dados de contato e <b>percentual de comiss\u00e3o</b>")
    _bullet("Comiss\u00e3o usada automaticamente no c\u00e1lculo de propostas")
    _bullet("Lan\u00e7amento financeiro autom\u00e1tico de pagamento ao finalizar proposta")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Parceiros e Assistentes", st_secao))
    _bullet("Parceiros de neg\u00f3cio para refer\u00eancia e indica\u00e7\u00e3o em projetos")
    _bullet("Assistentes com valores de pagamento por projeto \u2014 lan\u00e7amento autom\u00e1tico ao finalizar")
    e.append(Spacer(1, 10))

    # ── 3. PROPOSTAS ──────────────────────────────────────────────────
    e.append(PageBreak())
    e.append(Paragraph("3. Propostas", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O cora\u00e7\u00e3o operacional do Planner Organizer. Gerencie todo o ciclo de vida "
        "de cada proposta comercial, desde a elabora\u00e7\u00e3o at\u00e9 a finaliza\u00e7\u00e3o.",
        st_texto
    ))
    e.append(Spacer(1, 6))
    e.append(_draw_flow_diagram())
    e.append(Spacer(1, 10))
    e.append(Paragraph("Estrutura de uma Proposta", st_secao))
    _bullet("<b>Dados b\u00e1sicos:</b> cliente, descri\u00e7\u00e3o, tipo, valor base (honor\u00e1rios), prazo")
    _bullet("<b>Produtos:</b> itens a adquirir (caixas, organizadores), com quantidade e valor unit\u00e1rio")
    _bullet("<b>Fornecedores:</b> servi\u00e7os terceirizados com valor e comiss\u00e3o autom\u00e1tica")
    _bullet("<b>Assistentes:</b> profissionais auxiliares com valores de pagamento")
    _bullet("<b>Outros itens:</b> custos adicionais (transporte, materiais especiais)")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Relat\u00f3rios em PDF", st_secao))
    e.append(Paragraph(
        "Tr\u00eas tipos de relat\u00f3rios profissionais no design Navy & Gold:",
        st_texto
    ))
    _bullet("<b>Relat\u00f3rio para o Cliente:</b> proposta formal com itens, valores e condi\u00e7\u00f5es")
    _bullet("<b>Relat\u00f3rio Interno:</b> margens, custos detalhados e an\u00e1lise de rentabilidade")
    _bullet("<b>Relat\u00f3rio de Fornecedores:</b> lista completa de terceiros e servi\u00e7os")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Andamentos e Acompanhamento", st_secao))
    _bullet("Registre andamentos descrevendo o progresso de cada projeto")
    _bullet("Hist\u00f3rico cronol\u00f3gico acess\u00edvel a qualquer momento")
    _bullet("Barra de progresso visual baseada na data de prazo")
    e.append(Spacer(1, 10))

    # ── 4. VENDAS ──────────────────────────────────────────────────────
    e.append(Paragraph("4. Vendas", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "Controle de todos os produtos vendidos, com gera\u00e7\u00e3o autom\u00e1tica a partir "
        "de propostas finalizadas:",
        st_texto
    ))
    _bullet("Ao finalizar uma proposta, todos os produtos s\u00e3o convertidos em registros de venda")
    _bullet("Vincula\u00e7\u00e3o autom\u00e1tica ao cliente com rastreabilidade completa")
    _bullet("Visualiza\u00e7\u00e3o por cliente com cards de resumo (total de itens e valor)")
    _bullet("Gera\u00e7\u00e3o de PDF de venda para registro ou envio ao cliente")
    _bullet("Cadastro manual de vendas avulsas (independentes de propostas)")
    e.append(Spacer(1, 10))

    # ── 5. FINANCEIRO ──────────────────────────────────────────────────
    e.append(PageBreak())
    e.append(Paragraph("5. Financeiro", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O m\u00f3dulo Financeiro apresenta todas as transa\u00e7\u00f5es em um painel visual "
        "no formato Kanban, organizado em tr\u00eas colunas:",
        st_texto
    ))
    e.append(Spacer(1, 6))
    e.append(_draw_kanban_diagram())
    e.append(Spacer(1, 10))

    e.append(Paragraph("Controle Completo", st_secao))
    _bullet("<b>Cards de resumo:</b> Total a Receber, Total a Pagar e Saldo Projetado no topo")
    _bullet("<b>Nova transa\u00e7\u00e3o:</b> bot\u00e3o dourado para cadastrar receitas ou despesas manualmente")
    _bullet("<b>Filtros avan\u00e7ados:</b> por tipo (receita/despesa), per\u00edodo, status ou descri\u00e7\u00e3o")
    _bullet("<b>Painel de detalhes:</b> clique em uma transa\u00e7\u00e3o para ver informa\u00e7\u00f5es completas")
    _bullet("<b>Hist\u00f3rico e an\u00e1lise:</b> gr\u00e1ficos Plotly com evolu\u00e7\u00e3o e distribui\u00e7\u00e3o financeira")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Gera\u00e7\u00e3o Autom\u00e1tica de Lan\u00e7amentos", st_secao))
    e.append(Paragraph(
        "Ao finalizar uma proposta, o sistema cria automaticamente:",
        st_texto
    ))
    _sub_bullet("<b>Receita:</b> valor base da proposta (honor\u00e1rios) \u2014 A Receber do cliente")
    _sub_bullet("<b>Receita:</b> valor de cada produto vendido \u2014 A Receber")
    _sub_bullet("<b>Despesa:</b> comiss\u00e3o de cada fornecedor \u2014 calculada pelo percentual, A Pagar")
    _sub_bullet("<b>Despesa:</b> pagamento de cada assistente \u2014 conforme valor definido, A Pagar")
    e.append(Spacer(1, 10))

    # ── 6. PÓS-ORGANIZAÇÃO ────────────────────────────────────────────
    e.append(PageBreak())
    e.append(Paragraph("6. P\u00f3s-Organiza\u00e7\u00e3o", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O m\u00f3dulo de P\u00f3s-Organiza\u00e7\u00e3o \u00e9 o diferencial competitivo do "
        "Planner Organizer. Ele estrutura uma <b>jornada completa de acompanhamento</b> ap\u00f3s "
        "a conclus\u00e3o de cada projeto, garantindo satisfa\u00e7\u00e3o, fideliza\u00e7\u00e3o e "
        "oportunidades de novos neg\u00f3cios.",
        st_texto
    ))
    e.append(Spacer(1, 6))
    e.append(_draw_pos_org_timeline())
    e.append(Spacer(1, 8))

    e.append(Paragraph("As 6 Etapas da Jornada", st_secao))
    _navy_table([
        ["Etapa", "Quando", "Objetivo"],
        ["\U0001F64F Agradecimento", "D+1", "Mensagem elegante de encerramento, refor\u00e7ando o cuidado e a aten\u00e7\u00e3o ao cliente."],
        ["\U0001F4DE Acompanhamento", "D+7", "Contato para saber como a cliente est\u00e1 se sentindo com a organiza\u00e7\u00e3o no dia a dia."],
        ["\U0001F527 Ajuste Fino", "D+30", "Visita gratuita para pequenos ajustes ap\u00f3s uso real \u2014 posicione como cuidado inclu\u00eddo no servi\u00e7o."],
        ["\U0001F4AC Feedback", "D+45", "Coletar opini\u00e3o genu\u00edna da experi\u00eancia para aprimorar seus servi\u00e7os."],
        ["\U0001F91D Continuidade", "D+60", "Oferta elegante de servi\u00e7o cont\u00ednuo \u2014 acompanhamento peri\u00f3dico pago."],
        ["\U0001F504 Retorno T\u00e9cnico", "Sob demanda", "Visita t\u00e9cnica agendada conforme necessidade espec\u00edfica do cliente."],
    ], col_widths=[110, 65, 295])

    e.append(Paragraph("Benef\u00edcios do P\u00f3s-Organiza\u00e7\u00e3o", st_secao))
    _bullet("<b>Fideliza\u00e7\u00e3o:</b> clientes acompanhadas se tornam clientes recorrentes e indicam novos projetos")
    _bullet("<b>Profissionalismo:</b> o follow-up estruturado diferencia voc\u00ea no mercado")
    _bullet("<b>Receita recorrente:</b> a etapa de Continuidade (D+60) abre portas para contratos de manuten\u00e7\u00e3o")
    _bullet("<b>Melhoria cont\u00ednua:</b> o feedback sistematizado ajuda a aprimorar seus servi\u00e7os")
    e.append(Spacer(1, 4))

    e.append(Paragraph("Como Funciona na Pr\u00e1tica", st_secao))
    _bullet("Quando uma proposta \u00e9 finalizada, o sistema cria automaticamente o plano de p\u00f3s-organiza\u00e7\u00e3o")
    _bullet("Cada etapa possui <b>templates de mensagem</b> personaliz\u00e1veis com o nome da cliente")
    _bullet("Cards visuais mostram o status de cada etapa (pendente, conclu\u00edda, em atraso)")
    _bullet("A etapa de Ajuste Fino \u00e9 sinalizada como <b>gratuita</b> \u2014 faz parte do padr\u00e3o de atendimento")
    _bullet("Dicas estrat\u00e9gicas (hints) orientam a abordagem ideal em cada contato")
    e.append(Spacer(1, 6))

    e.append(Paragraph(
        "<b>Dica profissional:</b> Na visita de Ajuste Fino (D+30), n\u00e3o mencione desconto \u2014 "
        "posicione como cuidado inclu\u00eddo no servi\u00e7o. \u00c9 o momento ideal para apresentar "
        "o acompanhamento peri\u00f3dico pago na etapa de Continuidade (D+60).",
        st_destaque
    ))
    e.append(Spacer(1, 10))

    # ── 7. RELATÓRIOS ──────────────────────────────────────────────────
    e.append(Paragraph("7. Relat\u00f3rios", st_titulo))
    _gold_line()
    _bullet("Desempenho de vendas por cliente, per\u00edodo e tipo de proposta")
    _bullet("An\u00e1lise financeira: receitas vs. despesas, fluxo de caixa, proje\u00e7\u00f5es")
    _bullet("Gr\u00e1ficos interativos com filtros din\u00e2micos")
    _bullet("Exporta\u00e7\u00e3o de dados para an\u00e1lise externa")
    e.append(Spacer(1, 10))

    # ── INTEGRAÇÃO AUTOMÁTICA ──────────────────────────────────────────
    e.append(PageBreak())
    e.append(Paragraph("Integra\u00e7\u00e3o Autom\u00e1tica entre M\u00f3dulos", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "A principal vantagem do Planner Organizer \u00e9 a integra\u00e7\u00e3o inteligente. "
        "Ao finalizar uma proposta, o sistema executa automaticamente todas as opera\u00e7\u00f5es necess\u00e1rias:",
        st_texto
    ))
    e.append(Spacer(1, 6))
    e.append(_draw_integration_diagram())
    e.append(Spacer(1, 8))

    e.append(Paragraph(
        "<b>1.</b> Cria registros de venda para cada produto listado na proposta<br/>"
        "<b>2.</b> Gera lan\u00e7amento de receita (A Receber) com o valor base<br/>"
        "<b>3.</b> Gera receita para cada produto vendido<br/>"
        "<b>4.</b> Calcula e lan\u00e7a comiss\u00e3o de cada fornecedor (A Pagar)<br/>"
        "<b>5.</b> Lan\u00e7a pagamento de cada assistente (A Pagar)<br/>"
        "<b>6.</b> Cria o plano de p\u00f3s-organiza\u00e7\u00e3o com 6 etapas de follow-up",
        st_destaque
    ))
    e.append(Paragraph(
        "Essa automa\u00e7\u00e3o elimina erros de digita\u00e7\u00e3o, evita duplicidade e garante que "
        "todas as informa\u00e7\u00f5es estejam sempre sincronizadas.",
        st_texto
    ))
    e.append(Spacer(1, 10))

    # ── CONTROLE OPERACIONAL ───────────────────────────────────────────
    e.append(Paragraph("Controle Operacional e Gest\u00e3o", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O Planner Organizer oferece controle total sobre todas as opera\u00e7\u00f5es do seu neg\u00f3cio. "
        "Veja os principais recursos de controle dispon\u00edveis:",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Controle de Propostas", st_subtitulo))
    _bullet("<b>Rastreabilidade completa:</b> cada proposta registra todo o hist\u00f3rico de mudan\u00e7as de status")
    _bullet("<b>Barra de progresso:</b> indicador visual do tempo restante at\u00e9 o prazo")
    _bullet("<b>Andamentos:</b> hist\u00f3rico cronol\u00f3gico de cada etapa do projeto")
    _bullet("<b>Alertas de prazo:</b> notifica\u00e7\u00e3o autom\u00e1tica quando o prazo est\u00e1 pr\u00f3ximo (60 dias)")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Controle Financeiro", st_subtitulo))
    _bullet("<b>Painel Kanban:</b> vis\u00e3o instant\u00e2nea de todas as transa\u00e7\u00f5es organizadas por status")
    _bullet("<b>Saldo projetado:</b> c\u00e1lculo autom\u00e1tico do saldo futuro (a receber \u2013 a pagar)")
    _bullet("<b>Marca\u00e7\u00e3o de status:</b> atualize transa\u00e7\u00f5es como pagas/recebidas com um clique")
    _bullet("<b>Gr\u00e1ficos de an\u00e1lise:</b> evolu\u00e7\u00e3o financeira e distribui\u00e7\u00e3o de receitas vs. despesas")
    _bullet("<b>Filtragem avan\u00e7ada:</b> por tipo, per\u00edodo, status ou descri\u00e7\u00e3o")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Controle de Clientes", st_subtitulo))
    _bullet("<b>Vis\u00e3o 360\u00b0:</b> ao acessar um cliente, veja todas as propostas, vendas e finan\u00e7as vinculadas")
    _bullet("<b>Jornada completa:</b> desde o primeiro contato at\u00e9 o p\u00f3s-organiza\u00e7\u00e3o")
    _bullet("<b>Hist\u00f3rico de intera\u00e7\u00f5es:</b> todas as a\u00e7\u00f5es de follow-up registradas automaticamente")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Controle de Custos e Comiss\u00f5es", st_subtitulo))
    _bullet("<b>Comiss\u00f5es autom\u00e1ticas:</b> calculadas com base no percentual cadastrado do fornecedor")
    _bullet("<b>Vis\u00e3o de rentabilidade:</b> relat\u00f3rio interno mostra margens reais de cada proposta")
    _bullet("<b>Custos detalhados:</b> produtos, fornecedores, assistentes e outros itens discriminados")
    e.append(Spacer(1, 10))

    # ── FUNCIONALIDADES AVANÇADAS ──────────────────────────────────────
    e.append(PageBreak())
    e.append(Paragraph("Funcionalidades Avan\u00e7adas", st_titulo))
    _gold_line()

    e.append(Paragraph("Importa\u00e7\u00e3o em Lote", st_subtitulo))
    _bullet("<b>Clientes:</b> importa\u00e7\u00e3o via CSV com modelo padronizado para migrar grandes volumes")
    _bullet("<b>Propostas:</b> vincule propostas a clientes existentes via arquivo CSV")
    _bullet("<b>Valida\u00e7\u00e3o autom\u00e1tica:</b> verifica\u00e7\u00e3o de inconsist\u00eancias antes da importa\u00e7\u00e3o")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Sistema de Backup e Restaura\u00e7\u00e3o", st_subtitulo))
    _bullet("<b>Backup manual:</b> crie pontos de backup a qualquer momento")
    _bullet("<b>Restaura\u00e7\u00e3o:</b> recupere o sistema a partir de um backup anterior")
    _bullet("Inclui todos os cadastros, propostas, vendas e transa\u00e7\u00f5es financeiras")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Relat\u00f3rios PDF Profissionais", st_subtitulo))
    _bullet("Design <b>Navy & Gold</b> em todos os relat\u00f3rios \u2014 pronto para envio ao cliente")
    _bullet("Tr\u00eas tipos por proposta: Cliente, Interno e Fornecedores")
    _bullet("PDF de vendas por cliente para download direto")
    _bullet("Manual do sistema (este documento) gerado diretamente pela sidebar")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Sele\u00e7\u00e3o M\u00faltipla e Opera\u00e7\u00f5es em Lote", st_subtitulo))
    _bullet("Sele\u00e7\u00e3o individual ou em grupo de registros para exclus\u00e3o")
    _bullet("Remo\u00e7\u00e3o de m\u00faltiplos registros com um \u00fanico clique")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Controle de Acesso Multi-Tenant", st_subtitulo))
    _bullet("Autentica\u00e7\u00e3o segura com Firebase Auth")
    _bullet("Cada usu\u00e1rio acessa apenas dados da sua organiza\u00e7\u00e3o")
    _bullet("Perfis: usu\u00e1rio padr\u00e3o e administrador")
    e.append(Spacer(1, 10))

    # ── BOAS PRÁTICAS ──────────────────────────────────────────────────
    e.append(PageBreak())
    e.append(Paragraph("Boas Pr\u00e1ticas de Uso", st_titulo))
    _gold_line()

    e.append(Paragraph("Fluxo de Trabalho Recomendado", st_subtitulo))
    _bullet("Mantenha o fluxo de propostas atualizado: <b>Em elabora\u00e7\u00e3o \u2192 Aguardando aprova\u00e7\u00e3o \u2192 Aprovada \u2192 Em execu\u00e7\u00e3o \u2192 Finalizada</b>")
    _bullet("Finalize propostas assim que conclu\u00eddas \u2014 lan\u00e7amentos financeiros e vendas s\u00e3o gerados automaticamente")
    _bullet("Consulte o Dashboard regularmente para pend\u00eancias e prazos")
    _bullet("Utilize andamentos para manter hist\u00f3rico detalhado")
    e.append(Spacer(1, 6))

    e.append(Paragraph("P\u00f3s-Organiza\u00e7\u00e3o como Estrat\u00e9gia", st_subtitulo))
    _bullet("Complete todas as 6 etapas da jornada p\u00f3s-organiza\u00e7\u00e3o para maximizar fideliza\u00e7\u00e3o")
    _bullet("Personalize os templates de mensagem para cada cliente")
    _bullet("Use a visita de Ajuste Fino (D+30) como oportunidade de demonstrar cuidado")
    _bullet("Na etapa de Continuidade (D+60), apresente o acompanhamento peri\u00f3dico como investimento")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Cadastros Completos", st_subtitulo))
    _bullet("Clientes com telefone, e-mail e endere\u00e7o atualizados")
    _bullet("Percentuais de comiss\u00e3o corretos para c\u00e1lculo autom\u00e1tico")
    _bullet("Todos os assistentes registrados com valores definidos")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Monitoramento Financeiro", st_subtitulo))
    _bullet("Acompanhe o painel Kanban diariamente para receitas pendentes e despesas")
    _bullet("Marque transa\u00e7\u00f5es como pagas/recebidas para manter o saldo atualizado")
    _bullet("Use gr\u00e1ficos de an\u00e1lise para identificar tend\u00eancias e planejar fluxo de caixa")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Seguran\u00e7a e Backup", st_subtitulo))
    _bullet("Crie backups regularmente, especialmente antes de altera\u00e7\u00f5es significativas")
    _bullet("Ap\u00f3s importa\u00e7\u00f5es em lote, verifique se os dados foram importados corretamente")
    _bullet("Mantenha credenciais de acesso em local seguro")
    e.append(Spacer(1, 16))

    # ── CONCLUSÃO ──────────────────────────────────────────────────────
    _gold_line()
    e.append(Spacer(1, 8))
    e.append(Paragraph(
        "O Planner Organizer foi desenvolvido para simplificar e profissionalizar a gest\u00e3o do "
        "seu neg\u00f3cio de Personal Organizer. Com processos automatizados, dados integrados e "
        "uma jornada completa de p\u00f3s-organiza\u00e7\u00e3o, voc\u00ea pode dedicar mais tempo ao "
        "que realmente importa: transformar ambientes e a vida dos seus clientes.",
        st_texto
    ))
    e.append(Spacer(1, 12))
    e.append(Paragraph(
        f"\u00a9 {datetime.now().year} Planner Organizer \u2014 Vers\u00e3o 1.0.4",
        st_rodape
    ))

    doc.build(e, onFirstPage=_first_page, onLaterPages=_header_footer)
    return pdf_path
