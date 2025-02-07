from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os

def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta, separando valores a receber e a pagar
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

    # Informações da Proposta
    story.append(Paragraph("<b>Informações da Proposta</b>", styles["Heading3"]))
    story.append(Paragraph(f"<b>Tipo:</b> {proposta['tipo_proposta']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Status:</b> {proposta['status']}", styles["Normal"]))

    # Datas
    if proposta.get('data_inicio'):
        story.append(Paragraph(f"<b>Data Início:</b> {proposta['data_inicio'].strftime('%d/%m/%Y')}", styles["Normal"]))
    if proposta.get('data_fim'):
        story.append(Paragraph(f"<b>Data Fim:</b> {proposta['data_fim'].strftime('%d/%m/%Y')}", styles["Normal"]))
    if proposta.get('prazo_entrega'):
        story.append(Paragraph(f"<b>Prazo de Entrega:</b> {proposta['prazo_entrega'].strftime('%d/%m/%Y')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Descrição da Proposta
    story.append(Paragraph("<b>Descrição do Serviço:</b>", styles["Heading3"]))
    story.append(Paragraph(proposta['descricao'], styles["Normal"]))
    story.append(Spacer(1, 12))

    # Separar valores a receber e a pagar
    story.append(Paragraph("<b>Valores a Receber</b>", styles["Heading3"]))
    data_receber = [["Descrição", "Valor", "Status"]]
    data_pagar = [["Descrição", "Valor", "Status"]]

    # Valor base sempre vai para valores a receber
    data_receber.append([
        "Valor Base", 
        f"R$ {float(proposta['valor']):.2f}", 
        proposta.get('status_pagamento_base', 'Pendente')
    ])
    total_receber = float(proposta['valor'])
    total_pagar = 0.0

    # Processar acréscimos
    if not acrescimos.empty:
        for _, acrescimo in acrescimos.iterrows():
            descricao = f"{acrescimo['tipo']}"
            if acrescimo['fornecedor']:
                descricao += f" - {acrescimo['fornecedor']}"
            if acrescimo.get('descricao'):
                descricao += f"\n{acrescimo['descricao']}"

            valor = float(acrescimo['valor'])

            # Se for organização, vai para valores a receber
            if acrescimo['tipo'].lower() == 'organização':
                data_receber.append([
                    descricao,
                    f"R$ {valor:.2f}",
                    acrescimo.get('status_pagamento', 'Pendente')
                ])
                total_receber += valor
            else:
                # Outros tipos vão para valores a pagar
                data_pagar.append([
                    descricao,
                    f"R$ {valor:.2f}",
                    acrescimo.get('status_pagamento', 'Pendente')
                ])
                total_pagar += valor

    # Tabela de valores a receber
    table_style = TableStyle([
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
    ])

    # Criar e adicionar tabela de valores a receber
    table_receber = Table(data_receber, colWidths=[4*inch, 1.5*inch, 1*inch])
    table_receber.setStyle(table_style)
    story.append(table_receber)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Total a Receber:</b> R$ {total_receber:.2f}", 
                         ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

    # Se houver valores a pagar, adicionar tabela
    if len(data_pagar) > 1:  # Se tiver mais que só o cabeçalho
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Valores a Pagar</b>", styles["Heading3"]))
        table_pagar = Table(data_pagar, colWidths=[4*inch, 1.5*inch, 1*inch])
        table_pagar.setStyle(table_style)
        story.append(table_pagar)
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Total a Pagar:</b> R$ {total_pagar:.2f}", 
                             ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

    # Resumo final
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>Resumo Financeiro</b>", styles["Heading3"]))
    story.append(Paragraph(f"Total a Receber: R$ {total_receber:.2f}", styles["Normal"]))
    story.append(Paragraph(f"Total a Pagar: R$ {total_pagar:.2f}", styles["Normal"]))
    story.append(Paragraph(f"<b>Resultado Final: R$ {(total_receber - total_pagar):.2f}</b>", 
                         ParagraphStyle('Final', parent=styles['Normal'], fontSize=14, alignment=2)))

    # Observações Finais
    story.append(Spacer(1, 30))
    story.append(Paragraph("Observações:", styles["Heading4"]))
    story.append(Paragraph("1. Este documento representa o fechamento final da proposta.", styles["Normal"]))
    story.append(Paragraph("2. Os valores apresentados incluem todos os custos e acréscimos.", styles["Normal"]))
    story.append(Paragraph("3. Valores a receber incluem serviços de organização.", styles["Normal"]))
    story.append(Paragraph("4. Valores a pagar incluem fornecedores e outros custos.", styles["Normal"]))
    story.append(Paragraph("5. Para qualquer esclarecimento adicional, entre em contato.", styles["Normal"]))

    # Gerar PDF
    doc.build(story)
    return filename