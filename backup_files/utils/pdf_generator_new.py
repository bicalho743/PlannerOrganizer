from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
import traceback

def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta com o novo formato solicitado
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF para proposta #{proposta.get('id', 'N/A')}")
    print(f"DEBUG PDF: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF: Filename: {filename}")
    print(f"DEBUG PDF: Acréscimos: {len(acrescimos) if not acrescimos.empty else 0} registros")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Inicializar documento
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Título centralizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        # Título único centralizado com o ID da proposta e nome do cliente
        story.append(Paragraph(f"Proposta #{proposta['id']} - {cliente['nome']}", title_style))
        story.append(Paragraph(f"{datetime.now().strftime('%d/%m/%Y')}", styles["Heading3"]))
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
            
            # Calcular prazo de entrega em dias se ambas as datas estiverem disponíveis
            if proposta.get('data_inicio'):
                dias = (proposta['data_fim'] - proposta['data_inicio']).days
                story.append(Paragraph(f"<b>Prazo de Entrega:</b> {dias} dias", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Descrição da Proposta (formato lista, um item por linha)
        story.append(Paragraph("<b>Descrição do Serviço:</b>", styles["Heading3"]))
        # Separar a descrição em linhas
        descricao_linhas = proposta['descricao'].split('\n')
        for linha in descricao_linhas:
            # Remover espaços extras e verificar se há conteúdo
            linha = linha.strip()
            if linha:
                story.append(Paragraph(f"• {linha}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Renomear "Valores a Receber do Cliente" para "Investimento"
        story.append(Paragraph("<b>Investimento</b>", styles["Heading3"]))
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
        
        # Removido "Total a receber do Cliente" conforme solicitado

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

        # Removido "Resumo Financeiro" e "Resultado Final" conforme solicitado

        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("Observações:", styles["Heading4"]))
        # Apenas as observações solicitadas
        story.append(Paragraph("2. Os valores apresentados incluem todos os custos e acréscimos.", styles["Normal"]))
        story.append(Paragraph("3. Valores a receber incluem base e serviços de organização.", styles["Normal"]))
        story.append(Paragraph("5. Valores a pagar a lojas/fornecedores são responsabilidade do cliente.", styles["Normal"]))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

# Funções auxiliares para gerar o PDF apropriado
def gerar_pdf_cliente(proposta, cliente, acrescimos, filename):
    # Pode ser implementado ou manter o código original
    from utils.pdf_generator import gerar_pdf_cliente as original_gerar_pdf_cliente
    return original_gerar_pdf_cliente(proposta, cliente, acrescimos, filename)

def gerar_pdf_interno(proposta, cliente, acrescimos, filename):
    # Pode ser implementado ou manter o código original
    from utils.pdf_generator import gerar_pdf_interno as original_gerar_pdf_interno
    return original_gerar_pdf_interno(proposta, cliente, acrescimos, filename)