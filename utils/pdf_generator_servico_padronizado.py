"""
Relatório de Serviço (Cliente) — design Navy/Gold.
"""
import os
import textwrap
import traceback

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from utils.pdf_base import (
    W, H, NAVY, GOLD, GOLD_LT, WHITE, GRAY1, GRAY2, GRAY3, DARK,
    fmt, rr, header, info_cards, section_title, table_rows, total_row, footer,
)


def gerar_pdf_servico_padronizado(proposta, cliente, itens_servico, filename):
    """
    Gera o relatório de serviço para o cliente com design Navy/Gold.

    Args:
        proposta (dict): dados da proposta
        cliente  (dict): dados do cliente
        itens_servico (list[dict]): lista com 'descricao' e 'valor'
        filename (str): caminho do PDF a gerar

    Returns:
        str: caminho do PDF gerado
    """
    print(f"PDF SERVIÇO: proposta #{proposta.get('id','?')} | cliente {cliente.get('nome','?')}")
    try:
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        margin = 18 * mm
        cw = W - 2 * margin

        num_proposta = f"#{proposta.get('id', '')}"
        header(c, "Relatório de Serviço", num_proposta, margin, cw)

        y = info_cards(c, margin, cw, [
            ("Cliente",   cliente.get("nome", "—")),
            ("Telefone",  cliente.get("telefone", "—")),
            ("Tipo",      proposta.get("tipo_proposta", "—")),
            ("Status",    proposta.get("status", "—")),
        ])

        # ── Bloco de descrição do serviço ────────────────────────────────
        descricao = str(proposta.get("descricao") or "Serviço de Personal Organizer").strip()
        rr(c, margin, y - 12 * mm, cw, 12 * mm, 4, GOLD_LT, GOLD, 0.5)
        c.setFillColor(colors.HexColor("#7A5C1A"))
        c.setFont("Helvetica", 9)
        c.drawString(margin + 5 * mm, y - 4 * mm, "Descrição do serviço")
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 10)
        desc_curta = descricao if len(descricao) <= 80 else descricao[:77] + "..."
        c.drawString(margin + 5 * mm, y - 9.5 * mm, desc_curta)
        y -= 22 * mm

        # ── Seção Itens Inclusos ─────────────────────────────────────────
        y = section_title(c, margin, cw, y,
                          "Itens Inclusos",
                          "Todos os itens e serviços prestados nesta proposta",
                          NAVY)

        itens = itens_servico or []
        rows  = [(i.get("descricao", "—"), float(i.get("valor", 0) or 0), False)
                 for i in itens]

        if rows:
            y = table_rows(c, margin, cw, y, rows)
        else:
            rr(c, margin, y - 9 * mm, cw, 9 * mm, 3, GRAY1)
            c.setFillColor(GRAY3)
            c.setFont("Helvetica", 10)
            c.drawString(margin + 4 * mm, y - 4.5 * mm, "Nenhum item encontrado")
            y -= 9 * mm

        total = sum(r[1] for r in rows)
        valor_base = float(proposta.get("valor", 0) or 0)
        y = total_row(c, margin, cw, y,
                      "TOTAL DO SERVIÇO", total,
                      NAVY, WHITE, GOLD)

        # ── Bloco de valor base ──────────────────────────────────────────
        y -= 10 * mm
        rr(c, margin, y - 16 * mm, cw, 16 * mm, 6, GRAY1, GRAY2, 0.5)
        c.setFillColor(GRAY3)
        c.setFont("Helvetica", 8.5)
        c.drawString(margin + 5 * mm, y - 5 * mm, "Valor base do serviço de Personal Organizer")
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin + 5 * mm, y - 12 * mm, fmt(valor_base))
        adicionais = total - valor_base
        if adicionais > 0:
            c.setFillColor(GRAY3)
            c.setFont("Helvetica", 8.5)
            c.drawRightString(margin + cw - 5 * mm, y - 8.5 * mm,
                              f"Adicionais: {fmt(adicionais)}")

        footer(c, margin)
        c.save()
        print(f"PDF SERVIÇO gerado: {filename}")
        return filename

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de serviço: {e}")
