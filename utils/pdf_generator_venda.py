"""
Gerador de PDF para relatórios de venda com estilo consistente com outros relatórios
"""
import os
import pandas as pd
from datetime import datetime
import traceback

# Importações do ReportLab para geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm

# Cores e estilos padrão
COR_AZUL = colors.HexColor('#1450A0')  # Azul padrão da Planner
COR_CINZA = colors.HexColor('#555555')  # Cor de texto secundário
COR_CINZA_CLARO = colors.HexColor('#EEEEEE')  # Cor de fundo alternada para tabelas


def gerar_pdf_venda(venda, cliente, itens_venda, filename):
    """
    Gera um PDF com o relatório de venda para o cliente, formatado com design profissional
    com cabeçalho e rodapé azul
    
    Args:
        venda: Dicionário com os dados da venda
        cliente: Dicionário com os dados do cliente
        itens_venda: DataFrame com os itens da venda
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    print(f"DEBUG PDF VENDA: Gerando PDF para venda #{venda.get('id', 'N/A')}")
    print(f"DEBUG PDF VENDA: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF VENDA: Filename: {filename}")
    print(f"DEBUG PDF VENDA: Itens: {len(itens_venda) if hasattr(itens_venda, 'empty') and not itens_venda.empty else 0} registros")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Configuração do documento
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Inicializar elementos
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo para o título
        styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=COR_AZUL,
            alignment=1,  # Centralizado
            spaceAfter=10*mm
        ))
        
        # Estilo para subtítulos
        styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=COR_AZUL,
            spaceAfter=5*mm
        ))
        
        # Estilo para o corpo do texto
        styles.add(ParagraphStyle(
            name='CorpoTexto',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=COR_CINZA,
            spaceAfter=2*mm
        ))
        
        # Estilos para tabelas
        styles.add(ParagraphStyle(
            name='CelulaTabela',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=COR_CINZA
        ))
        
        # Estilo para rodapé
        styles.add(ParagraphStyle(
            name='Rodape',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.white,
            alignment=1  # Centralizado
        ))
        
        # Não precisamos adicionar título ao corpo, já está no cabeçalho
        
        # Informações do cliente em fonte normal, sem destacar
        story.append(Paragraph(f"Cliente: {cliente.get('nome', '-')}", styles['CorpoTexto']))
        
        # Adicionando venda número em fonte normal também
        story.append(Paragraph(f"Venda #{venda.get('id', '')}", styles['CorpoTexto']))
        story.append(Spacer(1, 5*mm))
        
        # Informações adicionais do cliente
        data = [
            ["Telefone:", cliente.get('telefone', '-')],
            ["Email:", cliente.get('email', '-')],
            ["Endereço:", f"{cliente.get('endereco', '-')}, {cliente.get('bairro', '-')}, {cliente.get('cidade', '-')}, {cliente.get('estado', '-')}"]
        ]
        
        t = Table(data, colWidths=[doc.width * 0.3, doc.width * 0.7])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 0), (-1, -1), COR_CINZA),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
        ]))
        story.append(t)
        story.append(Spacer(1, 10*mm))
        
        # Detalhes da venda
        story.append(Paragraph("DETALHES DA VENDA", styles['Subtitulo']))
        data = [
            ["Data:", venda.get('data_venda', '-')],
            ["Status:", venda.get('status', '-')],
            ["Valor Total:", venda.get('valor_total', '-')],
            ["Forma de Pagamento:", venda.get('forma_pagamento', '-')],
            ["Observações:", venda.get('observacoes', '-')]
        ]
        
        t = Table(data, colWidths=[doc.width * 0.3, doc.width * 0.7])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 0), (-1, -1), COR_CINZA),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
        ]))
        story.append(t)
        story.append(Spacer(1, 10*mm))
        
        # Itens da venda
        story.append(Paragraph("ITENS", styles['Subtitulo']))
        
        if hasattr(itens_venda, 'empty') and not itens_venda.empty:
            # Cabeçalho da tabela
            header = ["Produto", "Quantidade", "Preço Unit.", "Cômodo/Área", "Subtotal"]
            data = [header]
            
            # Adicionar itens
            for _, item in itens_venda.iterrows():
                # Usamos a coluna descricao para o nome do produto
                produto = item['produto_nome']
                quantidade = str(item['quantidade'])
                preco_unitario = f"R$ {item['preco_unitario']}" if isinstance(item['preco_unitario'], (int, float)) else item['preco_unitario']
                # Cômodo/Área vazio, conforme solicitado
                comodo = ""
                subtotal = f"R$ {item['subtotal']}" if isinstance(item['subtotal'], (int, float)) else item['subtotal']
                
                data.append([produto, quantidade, preco_unitario, comodo, subtotal])
            
            # Adicionar linha de total
            valor_total = 0
            for _, item in itens_venda.iterrows():
                if isinstance(item['subtotal'], (int, float)):
                    valor_total += item['subtotal']
                else:
                    try:
                        # Tentar extrair valor numérico da string formatada
                        val = item['subtotal'].replace('R$', '').replace(',', '.').strip()
                        valor_total += float(val)
                    except:
                        pass
            
            data.append(["", "", "", "TOTAL", f"R$ {valor_total:.2f}"])
            
            t = Table(data, colWidths=[doc.width * 0.3, doc.width * 0.15, doc.width * 0.15, doc.width * 0.2, doc.width * 0.2])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Centraliza cabeçalho
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Alinha produtos à esquerda
                ('ALIGN', (1, 1), (4, -2), 'CENTER'),  # Centraliza os valores (exceto o total)
                ('ALIGN', (3, -1), (4, -1), 'RIGHT'),  # Alinha "TOTAL" e valor à direita
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Cabeçalho em negrito
                ('FONT', (0, 1), (-1, -2), 'Helvetica'),      # Corpo em fonte normal
                ('FONT', (3, -1), (4, -1), 'Helvetica-Bold'),  # "TOTAL" em negrito
                ('TEXTCOLOR', (0, 0), (-1, -1), COR_CINZA),
                ('BACKGROUND', (0, 0), (-1, 0), COR_AZUL),  # Fundo azul para cabeçalho
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Texto branco para cabeçalho
                ('GRID', (0, 0), (-1, -2), 0.5, COR_CINZA),  # Grade para as linhas de itens
                ('LINEABOVE', (3, -1), (4, -1), 1, COR_AZUL),  # Linha acima do total
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            # Cores alternadas para as linhas
            for i in range(1, len(data) - 1):  # Excluindo o cabeçalho e a linha de total
                if i % 2 == 0:  # Linhas pares
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), COR_CINZA_CLARO)
                    ]))
            
            story.append(t)
        else:
            story.append(Paragraph("Nenhum item encontrado.", styles['CorpoTexto']))
        
        # Adicionar rodapé padrão
        footer_parts = [
            f"Planner Organizer",
            f"Data: {datetime.now().strftime('%d/%m/%Y')}",
            "Sistema de Gestão"
        ]
        footer_text = " | ".join(footer_parts)
        
        # Construir o PDF com cabeçalho e rodapé customizados
        class DocTemplate(SimpleDocTemplate):
            def __init__(self, *args, **kwargs):
                SimpleDocTemplate.__init__(self, *args, **kwargs)
                self.header_text = kwargs.get('header_text', '')
                self.footer_text = kwargs.get('footer_text', '')
            
            def build(self, flowables, **kwargs):
                # Criar função para cabeçalho e rodapé
                def header_footer(canvas, doc):
                    # Salvar estado
                    canvas.saveState()
                    page_width, page_height = A4
                    
                    # Desenhar cabeçalho (mesmo padrão do relatório interno - faixa azul no topo)
                    canvas.setFillColor(COR_AZUL)
                    canvas.rect(0, page_height - 70, page_width, 70, fill=1)
                    
                    # Texto do cabeçalho à esquerda (como no relatório interno) em caixa alta e baixa
                    canvas.setFont('Helvetica-Bold', 18)
                    canvas.setFillColor(colors.white)
                    canvas.drawString(30, page_height - 30, "Relatório de Vendas")
                    
                    # Data no canto direito (mesma posição do relatório interno)
                    canvas.setFont('Helvetica', 10)
                    data_atual = datetime.now().strftime('%d/%m/%Y')
                    canvas.drawRightString(page_width - 30, page_height - 30, f"Data: {data_atual}")
                    
                    # Informação do cliente na segunda linha (mesma posição do relatório interno)
                    nome_cliente = doc.cliente_nome if hasattr(doc, 'cliente_nome') else ''
                    venda_id = doc.venda_id if hasattr(doc, 'venda_id') else ''
                    canvas.setFont('Helvetica', 11)
                    canvas.drawString(30, page_height - 50, f"#{venda_id} - {nome_cliente}")
                    
                    # Linha fina abaixo do cabeçalho não é necessária com o novo layout
                    
                    # Adicionar rodapé
                    canvas.setFillColor(COR_AZUL)
                    canvas.rect(0, 0, page_width, 15*mm, fill=1)
                    
                    # Texto do rodapé
                    canvas.setFont('Helvetica', 8)
                    canvas.setFillColor(colors.white)
                    canvas.drawCentredString(page_width/2, 7*mm, self.footer_text)
                    
                    # Número da página
                    canvas.drawRightString(page_width - 20*mm, 7*mm, f"Página {doc.page}")
                    
                    # Restaurar estado
                    canvas.restoreState()
                
                # Construir documento
                SimpleDocTemplate.build(self, flowables, onFirstPage=header_footer, onLaterPages=header_footer, **kwargs)
        
        # Substituir o documento pelo template customizado
        doc = DocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=70,  # Margem superior maior para acomodar o cabeçalho maior
            bottomMargin=20*mm,
            footer_text=footer_text
        )
        
        # Adicionar atributos para o cliente e venda
        doc.cliente_nome = cliente.get('nome', '-')
        doc.venda_id = venda.get('id', '')
        
        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF VENDA: PDF gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF VENDA ERROR: Erro ao gerar PDF de venda: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF de venda: {str(e)}")