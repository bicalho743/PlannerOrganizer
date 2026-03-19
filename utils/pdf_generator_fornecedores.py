"""
Relatório de Fornecedores — design Navy/Gold.
"""
import os
import traceback

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from utils.pdf_base import (
    W, H, NAVY, TEAL, TEAL_LT, WHITE, GRAY3, DARK,
    fmt, rr, header, info_cards, section_title, table_rows, total_row, footer,
)


def gerar_pdf_fornecedores(proposta, cliente, itens_fornecedores, filename):
    """
    Gera o relatório de fornecedores com design Navy/Gold.

    Args:
        proposta (dict): dados da proposta
        cliente  (dict): dados do cliente
        itens_fornecedores (list[dict]): lista com 'descricao' e 'valor'
        filename (str): caminho do PDF a gerar

    Returns:
        str: caminho do PDF gerado
    """
    print(f"PDF FORNECEDORES: proposta #{proposta.get('id','?')} | cliente {cliente.get('nome','?')}")
    try:
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        margin = 18 * mm
        cw = W - 2 * margin

        num_proposta = f"#{proposta.get('id', '')}"
        header(c, "Relatório de Fornecedores", num_proposta, margin, cw)

        y = info_cards(c, margin, cw, [
            ("Cliente",   cliente.get("nome", "—")),
            ("Telefone",  cliente.get("telefone", "—")),
            ("Tipo",      proposta.get("tipo_proposta", "—")),
            ("Status",    proposta.get("status", "—")),
        ])

        # ── Seção Fornecedores ───────────────────────────────────────────
        y = section_title(c, margin, cw, y,
                          "Fornecedores",
                          "Valores pagos a fornecedores neste projeto",
                          TEAL)

        itens = itens_fornecedores or []
        rows  = [(i.get("descricao", "—"), float(i.get("valor", 0) or 0), False)
                 for i in itens]

        if rows:
            y = table_rows(c, margin, cw, y, rows)
        else:
            rr(c, margin, y - 9 * mm, cw, 9 * mm, 3, colors.HexColor("#F7F7F5"))
            c.setFillColor(GRAY3)
            c.setFont("Helvetica", 10)
            c.drawString(margin + 4 * mm, y - 4.5 * mm, "Nenhum fornecedor encontrado")
            y -= 9 * mm

        total = sum(r[1] for r in rows)
        y = total_row(c, margin, cw, y,
                      "TOTAL FORNECEDORES", total,
                      TEAL, WHITE, colors.HexColor("#A8DDE8"))

        # ── Bloco de resumo ──────────────────────────────────────────────
        if len(itens) > 0:
            y -= 12 * mm
            rr(c, margin, y - 20 * mm, cw, 20 * mm, 6, TEAL_LT,
               colors.HexColor("#5DAAB8"), 0.5)
            c.setFillColor(TEAL)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin + 5 * mm, y - 7 * mm,
                         f"{len(itens)} fornecedor{'es' if len(itens) > 1 else ''} envolvido{'s' if len(itens) > 1 else ''} neste projeto")
            if len(itens) > 1 and total > 0:
                maior = max(itens, key=lambda i: float(i.get("valor", 0) or 0))
                pct   = float(maior.get("valor", 0) or 0) / total * 100
                c.setFillColor(colors.HexColor("#0F5E6E"))
                c.setFont("Helvetica", 9)
                nome_maior = str(maior.get("descricao", ""))[:40]
                c.drawString(margin + 5 * mm, y - 13 * mm,
                             f"{nome_maior} representa {pct:.0f}% do custo total de fornecedores")

        footer(c, margin)
        c.save()
        print(f"PDF FORNECEDORES gerado: {filename}")
        return filename

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de fornecedores: {e}")
