"""
Relatório de Venda — design Navy/Gold.
"""
import os
import traceback
from datetime import datetime, timedelta

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from utils.pdf_base import (
    W, H, NAVY, GOLD, GOLD_LT, WHITE, GRAY1, GRAY2, GRAY3, DARK, GREEN, GREEN_LT,
    fmt, rr, header, info_cards, section_title, table_rows, total_row, footer,
)


def _fmt_data(d):
    if not d:
        return "—"
    if isinstance(d, str):
        try:
            if "T" in d:
                d = datetime.fromisoformat(d.replace("Z", "+00:00"))
            else:
                d = datetime.strptime(d[:10], "%Y-%m-%d")
        except Exception:
            return d
    if hasattr(d, "strftime"):
        return d.strftime("%d/%m/%Y")
    return str(d)


def gerar_pdf_venda(venda, cliente, itens_venda, filename, proposta_descricao=None):
    """
    Gera o relatório de venda com design Navy/Gold.

    Args:
        venda (dict): dados da venda (id, status, forma_pagamento, valor_total, data_venda, observacoes)
        cliente (dict): dados do cliente (nome)
        itens_venda (DataFrame): produtos da venda
        filename (str): caminho do PDF a gerar
        proposta_descricao (str, optional): descrição da proposta vinculada

    Returns:
        str: caminho do PDF gerado
    """
    print(f"PDF VENDA: venda #{venda.get('id','?')} | cliente {cliente.get('nome','?')}")
    try:
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        c = canvas.Canvas(filename, pagesize=A4)
        margin = 18 * mm
        cw = W - 2 * margin

        num_venda = f"#{venda.get('id', '')}"
        header(c, "Relatório de Venda", num_venda, margin, cw)

        data_venda = _fmt_data(venda.get("data_venda"))
        pagamento  = venda.get("forma_pagamento") or "—"
        status     = venda.get("status") or "—"

        y = info_cards(c, margin, cw, [
            ("Cliente",    cliente.get("nome", "—")),
            ("Data",       data_venda),
            ("Pagamento",  pagamento),
            ("Status",     status),
        ])

        # ── Seção Itens da Venda ────────────────────────────────────────
        y = section_title(c, margin, cw, y,
                          "Itens da Venda",
                          "Produtos e serviços incluídos nesta venda",
                          NAVY)

        tem_itens = hasattr(itens_venda, "empty") and not itens_venda.empty

        rows = []
        if tem_itens:
            for _, item in itens_venda.iterrows():
                nome     = str(item.get("produto_nome", "") or "Produto")
                qty      = float(item.get("quantidade", 1) or 1)
                unit_raw = item.get("preco_unitario", 0)
                if isinstance(unit_raw, str) and "R$" in unit_raw:
                    unit_raw = unit_raw.replace("R$", "").replace(",", ".").strip()
                unit = float(unit_raw or 0)
                sub  = unit * qty
                rows.append((f"{nome}  ×{int(qty)}", sub, False))
        else:
            valor_total_num = float(venda.get("valor_total", 0) or 0)
            if proposta_descricao:
                desc = str(proposta_descricao).strip()
            elif venda.get("observacoes"):
                desc = str(venda["observacoes"]).strip()
            else:
                desc = "Serviço prestado"
            rows.append((desc, valor_total_num, False))

        y = table_rows(c, margin, cw, y, rows)
        total = sum(r[1] for r in rows)
        y = total_row(c, margin, cw, y,
                      "TOTAL DA VENDA", total,
                      NAVY, WHITE, GOLD)

        # ── Observações (se existir) ────────────────────────────────────
        obs = str(venda.get("observacoes") or "").strip()
        if obs:
            y -= 10 * mm
            rr(c, margin, y - 16 * mm, cw, 16 * mm, 6, GRAY1, GRAY2, 0.5)
            c.setFillColor(GRAY3)
            c.setFont("Helvetica", 8.5)
            c.drawString(margin + 5 * mm, y - 5 * mm, "Observações")
            c.setFillColor(DARK)
            c.setFont("Helvetica", 10)
            obs_curta = obs if len(obs) <= 90 else obs[:87] + "..."
            c.drawString(margin + 5 * mm, y - 12 * mm, obs_curta)

        footer(c, margin)
        c.save()
        print(f"PDF VENDA gerado: {filename}")
        return filename

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de venda: {e}")
