"""
Gerador de PDF para Relatório de Fornecedores.
Mesmo layout, cores e padrão do Relatório de Serviço.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os
from datetime import datetime, timedelta
import traceback

AZUL_ESCURO = colors.HexColor("#1E366F")
CINZA_TEXTO = colors.HexColor("#5A6A85")
AZUL_CLARO = colors.HexColor("#e9f2ff")
BRANCO = colors.white


def gerar_pdf_fornecedores(proposta, cliente, itens_fornecedores, filename):
    """
    Gera um PDF de relatório de fornecedores com design padronizado.

    Args:
        proposta (dict): Dicionário com dados da proposta
        cliente (dict): Dicionário com dados do cliente
        itens_fornecedores (list): Lista de dicts com 'descricao' e 'valor'
        filename (str): Caminho para salvar o arquivo PDF

    Returns:
        str: Caminho do arquivo PDF gerado
    """
    try:
        print(f"DEBUG PDF FORNECEDORES: Gerando PDF para proposta #{proposta.get('id', 'N/A')}")
        print(f"DEBUG PDF FORNECEDORES: Cliente: {cliente.get('nome', 'N/A')}")
        print(f"DEBUG PDF FORNECEDORES: Filename: {filename}")
        print(f"DEBUG PDF FORNECEDORES: Itens: {len(itens_fornecedores) if itens_fornecedores else 0} registros")

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        c.setFillColor(AZUL_ESCURO)
        c.rect(0, height - 60, width, 60, fill=True, stroke=0)
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(BRANCO)
        c.drawString(30, height - 30, "Relatório de Fornecedores")

        c.setFont("Helvetica", 10)
        data_atual = (datetime.now() - timedelta(hours=3)).strftime('%d/%m/%Y')
        c.drawRightString(width - 30, height - 30, f"Data: {data_atual}")
        c.setFont("Helvetica", 11)
        c.drawString(30, height - 50, f"#{proposta.get('id', 'N/A')} - {cliente.get('nome', '')}")

        y = height - 100
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(AZUL_ESCURO)
        c.drawString(40, y, "Informações do Cliente")
        y -= 20
        c.setFont("Helvetica", 10)
        c.setFillColor(CINZA_TEXTO)
        c.drawString(40, y, f"Nome: {cliente.get('nome', '-')}")
        y -= 15
        c.drawString(40, y, f"Email: {cliente.get('email', '-')}")
        y -= 15
        c.drawString(40, y, f"Telefone: {cliente.get('telefone', '-')}")

        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(AZUL_ESCURO)
        c.drawString(40, y, "Informações da Proposta")
        y -= 20
        c.setFont("Helvetica", 10)
        c.setFillColor(CINZA_TEXTO)
        c.drawString(40, y, f"Tipo: {proposta.get('tipo_proposta', '-')}")
        y -= 15
        c.drawString(40, y, f"Status: {proposta.get('status', '-')}")

        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(AZUL_ESCURO)
        c.drawString(40, y, "Fornecedores")
        y -= 20

        c.setFillColor(AZUL_ESCURO)
        c.rect(40, y, 510, 18, fill=True)
        c.setFillColor(BRANCO)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, y + 4, "Descrição")
        c.drawRightString(540, y + 4, "Valor")
        y -= 18

        total = 0
        alternar = False

        if itens_fornecedores and len(itens_fornecedores) > 0:
            for item in itens_fornecedores:
                if alternar:
                    c.setFillColor(AZUL_CLARO)
                    c.rect(40, y, 510, 16, fill=True, stroke=0)
                alternar = not alternar
                c.setFillColor(CINZA_TEXTO)
                c.setFont("Helvetica", 10)

                item_desc = item.get('descricao', '')
                if len(item_desc) > 60:
                    item_desc = item_desc[:57] + "..."
                c.drawString(45, y + 3, item_desc)

                item_valor_raw = item.get('valor', 0)
                try:
                    item_valor = float(item_valor_raw)
                except (ValueError, TypeError):
                    item_valor = 0

                c.drawRightString(540, y + 3, f"R$ {item_valor:.2f}")
                total += item_valor
                y -= 16
        else:
            c.setFillColor(CINZA_TEXTO)
            c.setFont("Helvetica", 10)
            c.drawString(45, y + 3, "Nenhum fornecedor encontrado")
            y -= 16

        y -= 5

        c.setFillColor(AZUL_ESCURO)
        c.rect(40, y, 510, 18, fill=True)
        c.setFillColor(BRANCO)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, y + 4, "Total")
        c.drawRightString(540, y + 4, f"R$ {total:.2f}")
        y -= 30

        from utils.pdf_footer_helper import aplicar_rodape_padronizado
        aplicar_rodape_padronizado(c, width, height=40, ajuste_brasilia=True)

        c.save()
        print(f"PDF de fornecedores gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF FORNECEDORES ERROR: Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de fornecedores: {str(e)}")
