"""
Relatório Interno — design Navy/Gold.
Exibe Custo Total do Cliente, Receita Líquida e Margem.
"""
import os
import traceback
from datetime import datetime, timedelta

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from utils.pdf_base import (
    W, H, NAVY, GOLD, GOLD_LT, WHITE, GRAY1, GRAY2, GRAY3, DARK,
    GREEN, GREEN_LT, RED,
    fmt, rr, header, info_cards, section_title, table_rows, total_row,
    margem_block, footer,
)


def gerar_pdf_interno_melhorado(proposta, cliente, acrescimos, filename):
    """
    Gera o relatório interno com design profissional Navy/Gold.

    Args:
        proposta (dict): dados da proposta
        cliente  (dict): dados do cliente
        acrescimos (DataFrame): acréscimos da proposta
        filename (str): caminho do PDF a gerar

    Returns:
        str: caminho do PDF gerado
    """
    print(f"PDF INTERNO: proposta #{proposta.get('id','?')} | cliente {cliente.get('nome','?')}")
    try:
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        margin = 18 * mm
        cw = W - 2 * margin

        num_proposta = f"#{proposta.get('id', '')}"
        header(c, "Relatório Interno", num_proposta, margin, cw)

        # ── Datas formatadas ─────────────────────────────────────────────
        def _fmt_data(d):
            if not d:
                return "—"
            if hasattr(d, "strftime"):
                return d.strftime("%d/%m/%Y")
            return str(d)[:10]

        data_inicio = _fmt_data(proposta.get("data_inicio"))
        data_fim    = _fmt_data(proposta.get("data_fim"))
        periodo     = f"{data_inicio} – {data_fim}" if data_inicio != "—" else "—"

        y = info_cards(c, margin, cw, [
            ("Cliente",  cliente.get("nome", "—")),
            ("Tipo",     proposta.get("tipo_proposta", "—")),
            ("Status",   proposta.get("status", "—")),
            ("Período",  periodo),
        ])

        # ── Calcular valores ─────────────────────────────────────────────
        valor_base      = float(proposta.get("valor", 0) or 0)
        valor_produtos  = 0.0
        custos_forn     = 0.0
        custos_assist   = 0.0
        total_outros    = 0.0
        total_comissoes = 0.0

        try:
            from utils.database import Database, ProdutoOrganizador
            db_local = Database()
            for p in db_local.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta["id"]).all():
                q = float(p.quantidade or 1)
                v = float(p.valor or 0)
                valor_produtos += q * v
        except Exception:
            pass

        lucro_produtos = valor_produtos * 0.5

        if not acrescimos.empty and hasattr(acrescimos, "iterrows"):
            for _, ac in acrescimos.iterrows():
                tipo    = str(ac.get("tipo", "")).lower()
                valor   = float(ac.get("valor", 0) or 0)
                forn_nm = str(ac.get("fornecedor", "") or "").lower()

                if tipo == "assistente":
                    custos_assist += valor
                elif tipo in ("fornecedor", "produto", "marcenaria"):
                    custos_forn += valor
                    pct = 0.0
                    if forn_nm and "multi" in forn_nm:
                        pct = 5.0
                    else:
                        try:
                            import psycopg2, streamlit as st
                            conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
                            cur  = conn.cursor()
                            uid  = st.session_state.get("usuario_id")
                            cur.execute(
                                """SELECT percentual_comissao FROM fornecedores
                                   WHERE LOWER(descricao)=%s
                                   AND (usuario_id=%s OR usuario_id IS NULL)
                                   AND percentual_comissao IS NOT NULL AND percentual_comissao>0
                                   ORDER BY CASE WHEN usuario_id=%s THEN 0 ELSE 1 END LIMIT 1""",
                                (forn_nm, uid, uid),
                            )
                            row = cur.fetchone()
                            if row:
                                pct = float(row[0])
                            cur.close(); conn.close()
                        except Exception:
                            pass
                    total_comissoes += valor * (pct / 100)
                elif tipo == "comissão":
                    total_comissoes += valor
                else:
                    total_outros += valor

        custo_total = valor_base + valor_produtos + custos_forn + total_outros
        receita_liq = valor_base + total_comissoes + lucro_produtos + total_outros - custos_assist
        margem_pct  = (receita_liq / custo_total * 100) if custo_total > 0 else 0.0

        # ── Seção Custo Total ────────────────────────────────────────────
        y = section_title(c, margin, cw, y,
                          "Custo Total do Cliente",
                          "Todos os valores cobrados ao cliente nesta proposta",
                          GOLD)
        itens_custo = [
            ("Personal Organizer", valor_base,     False),
            ("Produtos",            valor_produtos, False),
            ("Fornecedores",        custos_forn,    False),
            ("Outros",              total_outros,   False),
        ]
        y = table_rows(c, margin, cw, y, itens_custo)
        y = total_row(c, margin, cw, y,
                      "CUSTO TOTAL DO CLIENTE", custo_total,
                      NAVY, WHITE, GOLD)

        y -= 12 * mm

        # ── Seção Receita Líquida ────────────────────────────────────────
        y = section_title(c, margin, cw, y,
                          "Receita Líquida do Projeto",
                          "Ganho real considerando comissões, lucro em produtos e pagamentos",
                          GREEN)
        itens_rec = [
            ("Personal Organizer",    valor_base,      False),
            ("Comissões",              total_comissoes, False),
            ("Lucro em Produtos",      lucro_produtos,  False),
            ("Outros",                 total_outros,    False),
            ("Pagamento Assistentes",  custos_assist,   True),
        ]
        y = table_rows(c, margin, cw, y, itens_rec)
        y = total_row(c, margin, cw, y,
                      "RECEITA LÍQUIDA TOTAL", receita_liq,
                      GREEN, WHITE, GREEN_LT)

        y -= 10 * mm
        margem_block(c, margin, cw, y, margem_pct)

        footer(c, margin)
        c.save()
        print(f"PDF INTERNO gerado: {filename}")
        return filename

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF interno: {e}")
