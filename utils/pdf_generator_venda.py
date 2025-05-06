"""
Gerador de PDF para relatórios de venda com estilo consistente com o relatório interno
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import traceback

# Importações do ReportLab para geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Paleta visual do relatório interno
AZUL_ESCURO = colors.HexColor("#1E366F")
AZUL_CLARO = colors.HexColor("#e9f2ff")
CINZA_TEXTO = colors.HexColor("#5A6A85")
BRANCO = colors.white


def gerar_pdf_venda(venda, cliente, itens_venda, filename):
    """
    Gera um PDF de relatório de venda com o mesmo estilo do relatório interno.

    Args:
        venda (dict): informações da venda (id, status, forma_pagamento, valor_total)
        cliente (dict): informações do cliente (nome)
        itens_venda (DataFrame): produtos vendidos
        filename (str): caminho do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    print(f"DEBUG PDF VENDA: Gerando PDF para venda #{venda.get('id', 'N/A')}")
    print(f"DEBUG PDF VENDA: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF VENDA: Filename: {filename}")
    print(f"DEBUG PDF VENDA: Itens: {len(itens_venda) if hasattr(itens_venda, 'empty') and not itens_venda.empty else 0} registros")
    
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        # Cabeçalho
        c.setFillColor(AZUL_ESCURO)
        c.rect(0, height - 70, width, 70, fill=True, stroke=0)
        c.setFillColor(BRANCO)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(30, height - 30, "Relatório de Vendas")
        c.setFont("Helvetica", 11)
        c.drawString(30, height - 50, f"#{venda.get('id', '')} - {cliente.get('nome', '')}")
        agora = datetime.now()
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 30, height - 30, f"Data: {agora.strftime('%d/%m/%Y')}")

        # Bloco de informações da venda
        y = height - 100
        c.setFillColor(AZUL_CLARO)
        c.rect(30, y - 110, width - 60, 100, fill=True, stroke=0)
        c.setFillColor(AZUL_ESCURO)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y - 20, "DETALHES DA VENDA")

        c.setFillColor(CINZA_TEXTO)
        c.setFont("Helvetica", 10)
        c.drawString(40, y - 40, f"Cliente: {cliente.get('nome', '-')}")
        c.drawString(40, y - 55, f"Status: {venda.get('status', '-')}")
        c.drawString(40, y - 70, f"Forma de Pagamento: {venda.get('forma_pagamento', '-')}")
        c.drawString(40, y - 85, f"Valor Total: R$ {venda.get('valor_total', '0.00')}")
        y -= 130
        
        # Título da tabela
        c.setFillColor(AZUL_ESCURO)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "ITENS DA VENDA:")
        y -= 20

        # Cabeçalho da tabela
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Produto")
        c.drawString(220, y, "Qtd")
        c.drawString(270, y, "Unitário")
        c.drawString(370, y, "Área")
        c.drawString(470, y, "Subtotal")
        y -= 10
        c.line(40, y, width - 40, y)
        y -= 15

        # Corpo da tabela
        c.setFont("Helvetica", 10)
        c.setFillColor(CINZA_TEXTO)
        total = 0
        row_height = 18

        if hasattr(itens_venda, 'empty') and not itens_venda.empty:
            for _, item in itens_venda.iterrows():
                produto = item.get("produto_nome", "")
                quantidade = item.get("quantidade", 1)
                
                # Depurar os valores para entender exatamente o formato
                preco_unitario = item.get("preco_unitario", 0)
                print(f"DEBUG PRECO: {preco_unitario} (tipo: {type(preco_unitario)})")
                
                # Tratar valores formatados como string de forma mais robusta
                if isinstance(preco_unitario, str):
                    # Remover qualquer texto e manter apenas dígitos e pontos/vírgulas
                    preco_limpo = ''.join([c for c in preco_unitario if c.isdigit() or c in '.,'])
                    print(f"DEBUG PRECO LIMPO: {preco_limpo}")
                    # Converter vírgula para ponto como separador decimal
                    preco_limpo = preco_limpo.replace(',', '.')
                    # Se houver mais de um ponto, manter apenas o último
                    if preco_limpo.count('.') > 1:
                        partes = preco_limpo.split('.')
                        preco_limpo = ''.join(partes[:-1]) + '.' + partes[-1]
                    try:
                        preco_unit = float(preco_limpo)
                    except:
                        # Fallback para caso ainda haja problemas
                        print(f"ERRO CONVERTING: {preco_limpo}")
                        preco_unit = 0.0
                else:
                    preco_unit = float(preco_unitario) if preco_unitario is not None else 0.0
                
                # Usar a mesma abordagem robusta para o subtotal
                subtotal_valor = item.get("subtotal", preco_unit * quantidade)
                print(f"DEBUG SUBTOTAL: {subtotal_valor} (tipo: {type(subtotal_valor)})")
                
                if isinstance(subtotal_valor, str):
                    # Remover qualquer texto e manter apenas dígitos e pontos/vírgulas
                    sub_limpo = ''.join([c for c in subtotal_valor if c.isdigit() or c in '.,'])
                    print(f"DEBUG SUBTOTAL LIMPO: {sub_limpo}")
                    # Converter vírgula para ponto como separador decimal
                    sub_limpo = sub_limpo.replace(',', '.')
                    # Se houver mais de um ponto, manter apenas o último
                    if sub_limpo.count('.') > 1:
                        partes = sub_limpo.split('.')
                        sub_limpo = ''.join(partes[:-1]) + '.' + partes[-1]
                    try:
                        subtotal = float(sub_limpo)
                    except:
                        # Fallback para caso ainda haja problemas
                        print(f"ERRO CONVERTING: {sub_limpo}")
                        subtotal = 0.0
                else:
                    subtotal = float(subtotal_valor) if subtotal_valor is not None else 0.0
                
                total += subtotal

                if y < 80:
                    c.showPage()
                    y = height - 80

                c.drawString(50, y, str(produto))
                c.drawString(220, y, str(quantidade))
                c.drawString(270, y, f"R$ {preco_unit:.2f}")
                c.drawString(370, y, "-")
                c.drawString(470, y, f"R$ {subtotal:.2f}")
                y -= row_height

            # Linha de total
            y -= 5
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(AZUL_ESCURO)
            c.drawRightString(540, y, f"TOTAL: R$ {total:.2f}")
        else:
            c.drawString(50, y, "Nenhum item encontrado.")

        # Rodapé
        c.setFillColor(AZUL_ESCURO)
        c.rect(0, 0, width, 30, fill=True, stroke=0)
        c.setFillColor(BRANCO)
        c.setFont("Helvetica", 9)
        c.drawCentredString(width / 2, 10, f"Planner Organizer | Relatório gerado em {agora.strftime('%d/%m/%Y às %H:%M')} | Sistema de Gestão")

        c.save()
        print(f"DEBUG PDF VENDA: PDF gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF VENDA ERROR: Erro ao gerar PDF de venda: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de venda: {str(e)}")