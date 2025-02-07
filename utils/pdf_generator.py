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

    # Separar valores a receber (do cliente) e a pagar (assistentes)
    story.append(Paragraph("<b>Valores a Receber do Cliente</b>", styles["Heading3"]))
    data_receber = [["Descrição", "Valor", "Status"]]
    data_pagar_assistentes = [["Descrição", "Valor", "Status"]]
    data_pagar_lojas = [["Descrição", "Valor", "Status"]]

    # Valor base sempre vai para valores a receber
    data_receber.append([
        "Valor Base", 
        f"R$ {float(proposta['valor']):.2f}", 
        proposta.get('status_pagamento_base', 'Pendente')
    ])
    total_receber = float(proposta['valor'])
    total_pagar_assistentes = 0.0
    total_pagar_lojas = 0.0

    # Processar acréscimos
    if not acrescimos.empty:
        for _, acrescimo in acrescimos.iterrows():
            descricao = f"{acrescimo['tipo']}"
            if acrescimo['fornecedor']:
                descricao += f" - {acrescimo['fornecedor']}"
            if acrescimo.get('descricao'):
                descricao += f"\n{acrescimo['descricao']}"

            valor = float(acrescimo['valor'])

            # Classificar os valores
            if acrescimo['tipo'].lower() == 'assistente':
                data_pagar_assistentes.append([
                    descricao,
                    f"R$ {valor:.2f}",
                    acrescimo.get('status_pagamento', 'Pendente')
                ])
                total_pagar_assistentes += valor
            elif acrescimo['tipo'].lower() in ['fornecedor', 'produto', 'marcenaria']:
                data_pagar_lojas.append([
                    descricao,
                    f"R$ {valor:.2f}",
                    acrescimo.get('status_pagamento', 'Pendente')
                ])
                total_pagar_lojas += valor
            else:
                # Tipo "Organização" e outros vão para valores a receber
                data_receber.append([
                    descricao,
                    f"R$ {valor:.2f}",
                    acrescimo.get('status_pagamento', 'Pendente')
                ])
                total_receber += valor

    # Tabela style
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
    story.append(Paragraph(f"<b>Total a Receber do Cliente:</b> R$ {total_receber:.2f}", 
                         ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

    # Se houver valores a pagar para lojas/fornecedores
    if len(data_pagar_lojas) > 1:  # Se tiver mais que só o cabeçalho
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Valores a Pagar a Lojas/Fornecedores</b>", styles["Heading3"]))
        table_pagar_lojas = Table(data_pagar_lojas, colWidths=[4*inch, 1.5*inch, 1*inch])
        table_pagar_lojas.setStyle(table_style)
        story.append(table_pagar_lojas)
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Total a Pagar a Lojas/Fornecedores:</b> R$ {total_pagar_lojas:.2f}", 
                             ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

    # Se houver valores a pagar para assistentes
    if len(data_pagar_assistentes) > 1:  # Se tiver mais que só o cabeçalho
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Valores a Pagar aos Assistentes</b>", styles["Heading3"]))
        table_pagar_assistentes = Table(data_pagar_assistentes, colWidths=[4*inch, 1.5*inch, 1*inch])
        table_pagar_assistentes.setStyle(table_style)
        story.append(table_pagar_assistentes)
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Total a Pagar aos Assistentes:</b> R$ {total_pagar_assistentes:.2f}", 
                             ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

    # Resumo final
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>Resumo Financeiro</b>", styles["Heading3"]))
    story.append(Paragraph(f"Total a Receber do Cliente: R$ {total_receber:.2f}", styles["Normal"]))
    story.append(Paragraph(f"Total a Pagar a Lojas/Fornecedores: R$ {total_pagar_lojas:.2f}", styles["Normal"]))
    story.append(Paragraph(f"Total a Pagar aos Assistentes: R$ {total_pagar_assistentes:.2f}", styles["Normal"]))
    story.append(Paragraph(f"<b>Resultado Final: R$ {(total_receber - total_pagar_assistentes - total_pagar_lojas):.2f}</b>", 
                         ParagraphStyle('Final', parent=styles['Normal'], fontSize=14, alignment=2)))

    # Observações Finais
    story.append(Spacer(1, 30))
    story.append(Paragraph("Observações:", styles["Heading4"]))
    story.append(Paragraph("1. Este documento representa o fechamento final da proposta.", styles["Normal"]))
    story.append(Paragraph("2. Os valores apresentados incluem todos os custos e acréscimos.", styles["Normal"]))
    story.append(Paragraph("3. Valores a receber incluem base e serviços de organização.", styles["Normal"]))
    story.append(Paragraph("4. Valores a pagar aos assistentes são responsabilidade da Organizer.", styles["Normal"]))
    story.append(Paragraph("5. Valores a pagar a lojas/fornecedores são responsabilidade do cliente.", styles["Normal"]))

    # Gerar PDF
    doc.build(story)
    return filename