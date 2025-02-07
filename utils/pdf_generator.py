from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os

def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta
    """
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    story.append(Paragraph(f"Fechamento de Proposta #{proposta['numero']}", title_style))
    story.append(Spacer(1, 12))

    # Informações do Cliente
    story.append(Paragraph(f"<b>Cliente:</b> {cliente['nome']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Descrição da Proposta
    story.append(Paragraph("<b>Descrição do Serviço:</b>", styles["Heading3"]))
    story.append(Paragraph(proposta['descricao'], styles["Normal"]))
    story.append(Spacer(1, 12))

    # Valor Base
    story.append(Paragraph("<b>Valor Base:</b>", styles["Heading3"]))
    data = [["Descrição", "Valor", "Status"]]
    data.append(["Valor Base", f"R$ {float(proposta['valor']):.2f}", 
                 proposta.get('status_pagamento_base', 'Pendente')])

    # Acréscimos
    if not acrescimos.empty:
        story.append(Paragraph("<b>Acréscimos:</b>", styles["Heading3"]))
        for _, acrescimo in acrescimos.iterrows():
            descricao = f"{acrescimo['tipo']}"
            if acrescimo['fornecedor']:
                descricao += f" - {acrescimo['fornecedor']}"
            data.append([
                descricao,
                f"R$ {float(acrescimo['valor']):.2f}",
                acrescimo.get('status_pagamento', 'Pendente')
            ])

    # Criar tabela
    table = Table(data, colWidths=[4*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    story.append(table)

    # Valor Total
    story.append(Spacer(1, 20))
    valor_total = float(proposta['valor'])
    if not acrescimos.empty:
        valor_total += float(acrescimos['valor'].astype(float).sum())
    
    story.append(Paragraph(f"<b>Valor Total:</b> R$ {valor_total:.2f}", 
                         ParagraphStyle('Total', 
                                      parent=styles['Normal'],
                                      fontSize=14,
                                      alignment=2)))

    # Gerar PDF
    doc.build(story)
    return filename
