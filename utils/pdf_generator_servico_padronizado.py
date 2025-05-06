"""
Gerador de PDF para relatórios de serviço com design padronizado.
Versão padronizada com layout consistente com os outros relatórios do sistema.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os
from datetime import datetime, timedelta
import traceback

# Cores e layout padrão
AZUL_ESCURO = colors.HexColor("#1E366F")
CINZA_TEXTO = colors.HexColor("#5A6A85")
AZUL_CLARO = colors.HexColor("#e9f2ff")
BRANCO = colors.white

def gerar_pdf_servico_padronizado(proposta, cliente, itens_servico, filename):
    """
    Gera um PDF de relatório de serviço com design padronizado.
    
    Args:
        proposta (dict): Dicionário com dados da proposta
        cliente (dict): Dicionário com dados do cliente
        itens_servico (list): Lista de itens de serviço com descrição e valor
        filename (str): Caminho para salvar o arquivo PDF
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    try:
        print(f"DEBUG PDF SERVIÇO: Gerando PDF para proposta #{proposta.get('id', 'N/A')}")
        print(f"DEBUG PDF SERVIÇO: Cliente: {cliente.get('nome', 'N/A')}")
        print(f"DEBUG PDF SERVIÇO: Filename: {filename}")
        print(f"DEBUG PDF SERVIÇO: Itens: {len(itens_servico) if itens_servico else 0} registros")
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        # Cabeçalho azul escuro
        c.setFillColor(AZUL_ESCURO)
        c.rect(0, height - 60, width, 60, fill=True, stroke=0)
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(BRANCO)
        c.drawString(30, height - 30, "Relatório de Serviço")

        c.setFont("Helvetica", 10)
        data_atual = (datetime.now() - timedelta(hours=3)).strftime('%d/%m/%Y')
        c.drawRightString(width - 30, height - 30, f"Data: {data_atual}")
        c.setFont("Helvetica", 11)
        c.drawString(30, height - 50, f"#{proposta.get('id', 'N/A')} - {cliente.get('nome', '')}")

        # Informações do cliente
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

        # Informações da proposta
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
        y -= 15
        
        # Tratamento seguro do valor monetário
        valor_proposta = proposta.get('valor', 0)
        if isinstance(valor_proposta, str) and 'R$' in valor_proposta:
            # Apenas remover o R$ e converter vírgula em ponto, não remover os pontos dos milhares
            valor_limpo = valor_proposta.replace("R$", "").replace(",", ".").strip()
            try:
                valor_num = float(valor_limpo)
            except ValueError:
                valor_num = 0
        else:
            try:
                valor_num = float(valor_proposta)
            except (ValueError, TypeError):
                valor_num = 0
                
        c.drawString(40, y, f"Valor: R$ {valor_num:.2f}")

        # Descrição
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(AZUL_ESCURO)
        c.drawString(40, y, "Descrição do Serviço")
        y -= 20
        c.setFillColor(CINZA_TEXTO)
        c.setFont("Helvetica", 10)
        
        descricao = proposta.get('descricao', 'Sem descrição')
        if descricao:
            descricao = descricao.replace('\n', ' ').strip()
            # Quebrar o texto em linhas para evitar ultrapassar a largura da página
            max_width = width - 80  # Margem de 40 de cada lado
            words = descricao.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                    line = test_line
                else:
                    c.drawString(45, y, line)
                    y -= 15
                    line = word
            # Desenhar a última linha
            if line:
                c.drawString(45, y, line)
                y -= 15
        else:
            c.drawString(45, y, "Sem descrição disponível")
            y -= 15

        # Itens
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(AZUL_ESCURO)
        c.drawString(40, y, "Itens Inclusos")
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
        
        if itens_servico and len(itens_servico) > 0:
            for item in itens_servico:
                if alternar:
                    c.setFillColor(AZUL_CLARO)
                    c.rect(40, y, 510, 16, fill=True, stroke=0)
                alternar = not alternar
                c.setFillColor(CINZA_TEXTO)
                c.setFont("Helvetica", 10)
                
                item_desc = item.get('descricao', '')
                if len(item_desc) > 60:  # Limitar tamanho para evitar overflow
                    item_desc = item_desc[:57] + "..."
                c.drawString(45, y + 3, item_desc)
                
                # Tratamento seguro do valor
                item_valor_raw = item.get('valor', 0)
                if isinstance(item_valor_raw, str) and 'R$' in item_valor_raw:
                    # Apenas remover o R$ e converter vírgula em ponto
                    valor_limpo = item_valor_raw.replace("R$", "").replace(",", ".").strip()
                    try:
                        item_valor = float(valor_limpo)
                    except ValueError:
                        item_valor = 0
                else:
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
            c.drawString(45, y + 3, "Nenhum item encontrado")
            y -= 16

        # Total
        c.setFillColor(AZUL_ESCURO)
        c.rect(40, y, 510, 18, fill=True)
        c.setFillColor(BRANCO)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, y + 4, "Total")
        c.drawRightString(540, y + 4, f"R$ {total:.2f}")
        y -= 30

        # Rodapé
        c.setFillColor(AZUL_ESCURO)
        c.rect(0, 0, width, 40, fill=True, stroke=0)
        c.setFillColor(BRANCO)
        c.setFont("Helvetica", 9)
        c.drawCentredString(width / 2, 25, "Planner Organizer | contato@plannerorganizer.com.br | www.plannerorganizer.com.br")
        c.setFont("Helvetica", 7)
        c.drawCentredString(width / 2, 10, f"Gerado em {data_atual} às {(datetime.now() - timedelta(hours=3)).strftime('%H:%M')}")

        c.save()
        print(f"✅ PDF de serviço gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF SERVIÇO ERROR: Erro ao gerar PDF de serviço: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de serviço: {str(e)}")