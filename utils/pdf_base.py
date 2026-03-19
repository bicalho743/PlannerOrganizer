"""
Base compartilhada de design para todos os PDFs do sistema.
Design: Navy/Gold profissional conforme padrão visual do sistema.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import datetime, timedelta

W, H = A4

NAVY    = colors.HexColor("#0D1B2A")
GOLD    = colors.HexColor("#C9A84C")
GOLD_LT = colors.HexColor("#F5EDD6")
WHITE   = colors.white
GRAY1   = colors.HexColor("#F7F7F5")
GRAY2   = colors.HexColor("#E8E6E0")
GRAY3   = colors.HexColor("#9A9890")
DARK    = colors.HexColor("#1C1C1A")
GREEN   = colors.HexColor("#1D6A4A")
GREEN_LT= colors.HexColor("#A8EDBC")
RED     = colors.HexColor("#C0392B")
TEAL    = colors.HexColor("#0F5E6E")
TEAL_LT = colors.HexColor("#E0F4F7")


def fmt(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = 0.0
    return f"R$ {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def rr(c, x, y, w, h, r, fill, stroke=None, sw=0.5):
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.setLineWidth(sw)
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    c.drawPath(p, fill=1, stroke=1 if stroke else 0)
    c.restoreState()


def _dados_perfil():
    try:
        import streamlit as st
        if "db" in st.session_state:
            perfil = st.session_state.db.get_perfil_usuario()
            if perfil:
                nome  = perfil.get("empresa") or perfil.get("nome") or "Planner Organizer"
                cargo = perfil.get("cargo") or "Personal Organizer"
                insta = perfil.get("instagram") or "@plannerorganizer"
                return nome, cargo, insta
    except Exception:
        pass
    return "Planner Organizer", "Personal Organizer", "@plannerorganizer"


def header(c, titulo, numero_proposta, margin, content_w):
    nome_empresa, cargo, instagram = _dados_perfil()
    subtitulo = f"{nome_empresa}  ·  {cargo}  ·  {instagram}"
    agora = datetime.now() - timedelta(hours=3)
    agora_str = agora.strftime("%d/%m/%Y")

    c.setFillColor(NAVY)
    c.rect(0, H - 52 * mm, W, 52 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 52 * mm, W, 1.2 * mm, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#1A2E45"))
    c.setFont("Helvetica-Bold", 72)
    c.drawRightString(W - margin, H - 42 * mm, str(numero_proposta))

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin, H - 24 * mm, titulo)

    c.setFillColor(GOLD)
    c.setFont("Helvetica", 11)
    c.drawString(margin, H - 32 * mm, subtitulo)

    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 9)
    meta = f"Gerado em {agora_str}  ·  {nome_empresa}  ·  {instagram}"
    c.drawString(margin, H - 40 * mm, meta)


def info_cards(c, margin, content_w, infos):
    top_y  = H - 68 * mm
    card_h = 18 * mm
    n      = len(infos)
    card_w = (content_w - (n - 1) * 4 * mm) / n
    for i, (label, value) in enumerate(infos):
        cx = margin + i * (card_w + 4 * mm)
        rr(c, cx, top_y - card_h, card_w, card_h, 4, GRAY1, GRAY2, 0.5)
        c.setFillColor(GRAY3)
        c.setFont("Helvetica", 8)
        c.drawString(cx + 4 * mm, top_y - 7 * mm, label.upper())
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 10)
        val_str = str(value)
        if len(val_str) > 28:
            val_str = val_str[:25] + "..."
        c.drawString(cx + 4 * mm, top_y - 14 * mm, val_str)
    return top_y - card_h - 10 * mm


def section_title(c, margin, content_w, y, titulo, subtitulo, line_color):
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, titulo)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8.5)
    c.drawString(margin, y - 5 * mm, subtitulo)
    c.setStrokeColor(line_color)
    c.setLineWidth(1)
    c.line(margin, y - 7 * mm, margin + content_w, y - 7 * mm)
    return y - 14 * mm


def table_rows(c, margin, content_w, start_y, items, row_h=9 * mm):
    y = start_y
    for idx, (nome, valor, is_neg) in enumerate(items):
        bg = GRAY1 if idx % 2 == 0 else WHITE
        rr(c, margin, y - row_h + 1.5 * mm, content_w, row_h - 1 * mm, 3, bg)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 10)
        nome_str = str(nome)
        if len(nome_str) > 65:
            nome_str = nome_str[:62] + "..."
        c.drawString(margin + 4 * mm, y - 4.5 * mm, nome_str)
        c.setFillColor(RED if is_neg else DARK)
        c.setFont("Helvetica-Bold", 10)
        prefix = "– " if is_neg else ""
        c.drawRightString(margin + content_w - 4 * mm, y - 4.5 * mm, prefix + fmt(valor))
        y -= row_h
    return y


def total_row(c, margin, content_w, y, label, valor, bg, text_color, val_color, row_h=9 * mm):
    rr(c, margin, y - row_h + 1 * mm, content_w, row_h, 4, bg)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(margin + 4 * mm, y - 4.5 * mm, label)
    c.setFillColor(val_color)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(margin + content_w - 4 * mm, y - 4.5 * mm, fmt(valor))
    return y - row_h


def margem_block(c, margin, content_w, y, pct):
    rr(c, margin, y - 14 * mm, content_w, 14 * mm, 6, GOLD_LT, GOLD, 0.8)
    c.setFillColor(colors.HexColor("#7A5C1A"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 5 * mm, y - 5.5 * mm, "Margem sobre o faturamento total do projeto")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(margin + content_w - 5 * mm, y - 9 * mm,
                      f"{pct:.1f}%".replace(".", ","))


def footer(c, margin):
    nome_empresa, cargo, instagram = _dados_perfil()
    c.setFillColor(GRAY2)
    c.rect(0, 0, W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(GRAY3)
    c.setFont("Helvetica", 8)
    c.drawString(margin, 5 * mm, "Documento de uso interno — Planner Organizer")
    c.drawRightString(W - margin, 5 * mm, f"{nome_empresa}  ·  {instagram}")
