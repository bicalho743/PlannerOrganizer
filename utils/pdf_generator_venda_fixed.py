"""
Gerador de PDF para relatórios de venda com estilo consistente com o relatório interno
Versão completamente nova e simplificada
"""
import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import traceback

# Paleta de cores igual ao relatório interno
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
        # Garantir que o diretório existe
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Verificar se temos itens para exibir
        if hasattr(itens_venda, 'empty') and not itens_venda.empty:
            print(f"DEBUG PDF VENDA: Produtos encontrados:")
            for _, item in itens_venda.iterrows():
                print(f"  - {item.get('produto_nome', 'N/A')}: {item.get('quantidade', 0)} x R${item.get('preco_unitario', 0):.2f}")
        else:
            print("DEBUG PDF VENDA: ATENÇÃO - Nenhum item encontrado para a venda!")
        
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
        agora = datetime.now() - timedelta(hours=3)
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 30, height - 30, f"Data: {agora.strftime('%d/%m/%Y')}")

        # Bloco de informações da venda
        y = height - 100
        c.setFillColor(AZUL_CLARO)
        c.rect(30, y - 110, width - 60, 100, fill=True, stroke=0)
        c.setFillColor(AZUL_ESCURO)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y - 20, "Detalhes da Venda")

        # Tratar valor_total da venda para garantir formatação correta
        valor_total_raw = venda.get('valor_total', 0)
        if isinstance(valor_total_raw, str) and 'R$' in valor_total_raw:
            valor_total = valor_total_raw  # Mantém o valor como string formatada
        else:
            # Arredondar e formatar corretamente
            valor_num = round(float(valor_total_raw), 2)
            valor_total = f"R$ {valor_num:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

        c.setFillColor(CINZA_TEXTO)
        c.setFont("Helvetica", 10)
        c.drawString(40, y - 40, f"Cliente: {cliente.get('nome', '-')}")
        c.drawString(40, y - 55, f"Status: {venda.get('status', '-')}")
        c.drawString(40, y - 70, f"Forma de Pagamento: {venda.get('forma_pagamento', '-')}")
        c.drawString(40, y - 85, f"Valor Total: {valor_total}")
        y -= 130

        # Título da seção de itens
        c.setFillColor(AZUL_ESCURO)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Itens da Venda:")
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

                # Preço unitário (tratando string com "R$")
                preco_unit_raw = item.get("preco_unitario", 0)
                if isinstance(preco_unit_raw, str) and 'R$' in preco_unit_raw:
                    preco_unit_str = preco_unit_raw  # Mantém a string original para exibição
                    # Convertemos para cálculo
                    # Apenas remover o R$ e converter vírgula em ponto, não remover os pontos dos milhares
                    valor_limpo = preco_unit_raw.replace("R$", "").replace(",", ".").strip()
                    preco_unit = float(valor_limpo)
                else:
                    preco_unit = float(preco_unit_raw)
                    preco_unit_str = f"R$ {preco_unit:.2f}"

                # Subtotal (também trata string com "R$")
                subtotal_raw = item.get("subtotal", preco_unit * quantidade)
                if isinstance(subtotal_raw, str) and 'R$' in subtotal_raw:
                    subtotal_str = subtotal_raw  # Mantém a string original para exibição
                    # Convertemos para cálculo
                    # Apenas remover o R$ e converter vírgula em ponto, não remover os pontos dos milhares
                    valor_limpo = subtotal_raw.replace("R$", "").replace(",", ".").strip()
                    subtotal = float(valor_limpo)
                else:
                    subtotal = float(subtotal_raw)
                    subtotal_str = f"R$ {subtotal:.2f}"

                total += subtotal

                if y < 80:
                    c.showPage()
                    y = height - 80

                c.drawString(50, y, str(produto))
                c.drawString(220, y, str(quantidade))
                c.drawString(270, y, preco_unit_str)
                c.drawString(370, y, "-")
                c.drawString(470, y, subtotal_str)
                y -= row_height

            # Total
            y -= 5
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(AZUL_ESCURO)
            total_formatado = f"R$ {total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
            c.drawRightString(540, y, f"TOTAL: {total_formatado}")
        else:
            c.drawString(50, y, "Nenhum item encontrado.")

        # Aplicar rodapé padronizado
        from utils.pdf_footer_helper import aplicar_rodape_padronizado
        aplicar_rodape_padronizado(c, width, height=40, ajuste_brasilia=True)

        c.save()
        print(f"✅ PDF de venda gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF VENDA ERROR: Erro ao gerar PDF de venda: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de venda: {str(e)}")