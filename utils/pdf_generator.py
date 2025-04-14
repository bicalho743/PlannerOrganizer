from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
import traceback

def gerar_pdf_cliente(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão para cliente da proposta, com detalhes necessários 
    para o cliente, sem informações financeiras internas
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão pública)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF para cliente - proposta #{proposta.get('numero', 'N/A')}")
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

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        story.append(Paragraph(f"Relatório de Serviço", title_style))
        story.append(Paragraph(f"Proposta #{proposta['numero']} - {cliente['nome']}", styles["Heading2"]))
        story.append(Paragraph(f"{datetime.now().strftime('%d/%m/%Y')}", styles["Heading3"]))
        story.append(Spacer(1, 12))

        # Informações do Cliente
        story.append(Paragraph("<b>Informações do Cliente</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Nome:</b> {cliente['nome']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Email:</b> {cliente.get('email', 'Não informado')}", styles["Normal"]))
        story.append(Paragraph(f"<b>Telefone:</b> {cliente.get('telefone', 'Não informado')}", styles["Normal"]))
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
        story.append(Spacer(1, 20))

        # Serviços Realizados
        story.append(Paragraph("<b>Serviços Realizados</b>", styles["Heading3"]))
        
        # Tabela de serviços
        data_servicos = [["Descrição", "Valor"]]
        
        # Valor base sempre vai para a tabela
        data_servicos.append([
            "Serviço Base", 
            f"R$ {float(proposta['valor']):.2f}"
        ])
        
        # Processar apenas acréscimos relevantes para o cliente
        total_servicos = float(proposta['valor'])
        
        if not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                # Filtrar apenas tipos específicos para mostrar ao cliente
                if acrescimo['tipo'].lower() in ['assistente', 'organização', 'outro']:
                    descricao = f"{acrescimo['tipo']}"
                    if acrescimo.get('descricao'):
                        descricao += f" - {acrescimo['descricao']}"
                    
                    valor = float(acrescimo['valor'])
                    
                    data_servicos.append([
                        descricao,
                        f"R$ {valor:.2f}"
                    ])
                    total_servicos += valor

        # Tabela style para serviços
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

        # Criar e adicionar tabela de serviços
        table = Table(data_servicos, colWidths=[4.5*inch, 2*inch])
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Total:</b> R$ {total_servicos:.2f}", 
                             ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("Observações:", styles["Heading4"]))
        story.append(Paragraph("1. Este documento representa o relatório para cliente dos serviços prestados.", styles["Normal"]))
        story.append(Paragraph("2. Para quaisquer dúvidas sobre os serviços, entre em contato conosco.", styles["Normal"]))
        story.append(Paragraph("3. Agradecemos a confiança em nossos serviços.", styles["Normal"]))

        # Informações da Empresa
        story.append(Spacer(1, 30))
        story.append(Paragraph("Planner Organizer", styles["Heading4"]))
        story.append(Paragraph("contato@plannerorganizer.com.br", styles["Normal"]))
        story.append(Paragraph("(11) 98765-4321", styles["Normal"]))
        story.append(Paragraph("www.plannerorganizer.com.br", styles["Normal"]))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF para cliente gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF para cliente: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF para cliente: {str(e)}")
    
def gerar_pdf_interno(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão interna da proposta, incluindo todos os detalhes
    financeiros, custos e margens
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão completa)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF interno para proposta #{proposta.get('numero', 'N/A')}")
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

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        story.append(Paragraph(f"RELATÓRIO INTERNO - CONFIDENCIAL", title_style))
        story.append(Paragraph(f"Proposta #{proposta['numero']} - {cliente['nome']}", styles["Heading2"]))
        story.append(Paragraph(f"{datetime.now().strftime('%d/%m/%Y')}", styles["Heading3"]))
        story.append(Spacer(1, 12))

        # Informações do Cliente
        story.append(Paragraph("<b>Informações do Cliente</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Nome:</b> {cliente['nome']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Email:</b> {cliente.get('email', 'Não informado')}", styles["Normal"]))
        story.append(Paragraph(f"<b>Telefone:</b> {cliente.get('telefone', 'Não informado')}", styles["Normal"]))
        story.append(Paragraph(f"<b>Endereço:</b> {cliente.get('endereco', 'Não informado')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Informações da Proposta
        story.append(Paragraph("<b>Informações da Proposta</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Tipo:</b> {proposta['tipo_proposta']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Status:</b> {proposta['status']}", styles["Normal"]))

        # Datas
        if proposta.get('data_proposta'):
            story.append(Paragraph(f"<b>Data da Proposta:</b> {proposta['data_proposta'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_aprovacao'):
            story.append(Paragraph(f"<b>Data de Aprovação:</b> {proposta['data_aprovacao'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_inicio'):
            story.append(Paragraph(f"<b>Data Início:</b> {proposta['data_inicio'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_inicio_execucao'):
            story.append(Paragraph(f"<b>Data Início Execução:</b> {proposta['data_inicio_execucao'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_fim'):
            story.append(Paragraph(f"<b>Data Fim:</b> {proposta['data_fim'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('prazo_entrega'):
            story.append(Paragraph(f"<b>Prazo de Entrega:</b> {proposta['prazo_entrega'].strftime('%d/%m/%Y')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Descrição da Proposta
        story.append(Paragraph("<b>Descrição do Serviço:</b>", styles["Heading3"]))
        story.append(Paragraph(proposta['descricao'], styles["Normal"]))
        story.append(Spacer(1, 20))

        # Valor Total e Custos
        story.append(Paragraph("<b>Análise Financeira</b>", styles["Heading3"]))
        
        # Valor base
        valor_base = float(proposta['valor'])
        story.append(Paragraph(f"<b>Valor Base:</b> R$ {valor_base:.2f}", styles["Normal"]))
        
        # Acréscimos
        total_acrescimos = 0.0
        custos_fornecedores = 0.0
        custos_assistentes = 0.0
        
        if not acrescimos.empty:
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>Detalhamento de Acréscimos e Custos</b>", styles["Heading4"]))
            
            data_acrescimos = [["Tipo", "Fornecedor/Assistente", "Descrição", "Valor", "Status"]]
            
            for _, acrescimo in acrescimos.iterrows():
                valor = float(acrescimo['valor'])
                total_acrescimos += valor
                
                # Classificar os custos
                if acrescimo['tipo'].lower() == 'assistente':
                    custos_assistentes += valor
                elif acrescimo['tipo'].lower() in ['fornecedor', 'produto', 'marcenaria']:
                    custos_fornecedores += valor
                
                data_acrescimos.append([
                    acrescimo['tipo'],
                    acrescimo['fornecedor'] if 'fornecedor' in acrescimo else "-",
                    acrescimo['descricao'] if 'descricao' in acrescimo else "-",
                    f"R$ {valor:.2f}",
                    acrescimo.get('status_pagamento', 'Pendente')
                ])
            
            # Tabela style para acréscimos
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ])
            
            # Criar e adicionar tabela de acréscimos
            table = Table(data_acrescimos, colWidths=[1*inch, 1.5*inch, 2*inch, 1*inch, 1*inch])
            table.setStyle(table_style)
            story.append(table)
        
        # Cálculos financeiros
        valor_total = valor_base + total_acrescimos
        total_custos = custos_fornecedores + custos_assistentes
        margem_bruta = valor_total - total_custos
        margem_percentual = (margem_bruta / valor_total * 100) if valor_total > 0 else 0
        
        # Resumo financeiro
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Resumo Financeiro</b>", styles["Heading4"]))
        
        # Tabela de resumo financeiro
        data_resumo = [
            ["Item", "Valor"],
            ["Valor Base", f"R$ {valor_base:.2f}"],
            ["Total de Acréscimos", f"R$ {total_acrescimos:.2f}"],
            ["VALOR TOTAL", f"R$ {valor_total:.2f}"],
            ["Custos com Fornecedores", f"R$ {custos_fornecedores:.2f}"],
            ["Custos com Assistentes", f"R$ {custos_assistentes:.2f}"],
            ["TOTAL DE CUSTOS", f"R$ {total_custos:.2f}"],
            ["MARGEM BRUTA", f"R$ {margem_bruta:.2f}"],
            ["MARGEM PERCENTUAL", f"{margem_percentual:.2f}%"]
        ]
        
        # Estilo para tabela de resumo
        resumo_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            # Destacar valores totais
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightskyblue),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 6), (-1, 6), colors.lightskyblue),
            ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 7), (-1, 7), colors.palegreen),
            ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 8), (-1, 8), colors.palegreen),
            ('FONTNAME', (0, 8), (-1, 8), 'Helvetica-Bold'),
        ])
        
        resumo_table = Table(data_resumo, colWidths=[3.5*inch, 3*inch])
        resumo_table.setStyle(resumo_style)
        story.append(resumo_table)
        
        # Alertas e observações
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Análise e Recomendações</b>", styles["Heading4"]))
        
        if margem_percentual < 30:
            story.append(Paragraph(f"<font color='red'><b>ALERTA:</b> Margem abaixo do recomendado ({margem_percentual:.2f}%)</font>", styles["Normal"]))
            story.append(Paragraph("Recomendação: Analisar custos e considerar revisão de valores em projetos futuros similares.", styles["Normal"]))
        else:
            story.append(Paragraph(f"<font color='green'><b>POSITIVO:</b> Margem dentro do esperado ({margem_percentual:.2f}%)</font>", styles["Normal"]))
        
        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>Observações Finais</b>", styles["Heading4"]))
        story.append(Paragraph("1. Este documento é CONFIDENCIAL e de uso interno.", styles["Normal"]))
        story.append(Paragraph("2. A margem ideal deve ser de no mínimo 30% do valor total.", styles["Normal"]))
        story.append(Paragraph("3. Custos com assistentes são despesas da empresa.", styles["Normal"]))
        story.append(Paragraph("4. Custos com fornecedores são normalmente repassados ao cliente.", styles["Normal"]))

        # Data e responsável
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", 
                            ParagraphStyle('DataGeracao', fontSize=8, alignment=1)))
        story.append(Paragraph("CONFIDENCIAL - USO INTERNO", 
                            ParagraphStyle('Confidencial', fontSize=10, alignment=1, textColor=colors.red)))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF interno gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF interno: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF interno: {str(e)}")
    
def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta, separando valores a receber e a pagar
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF para proposta #{proposta.get('numero', 'N/A')}")
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

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        story.append(Paragraph(f"Fechamento de Projeto", title_style))
        story.append(Paragraph(f"Proposta #{proposta['numero']} - {cliente['nome']}", styles["Heading2"]))
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
        story.append(Paragraph(f"<b>Resultado Final: R$ {(total_receber - total_pagar_assistentes):.2f}</b>", 
                             ParagraphStyle('Final', parent=styles['Normal'], fontSize=14, alignment=2)))

        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("Observações:", styles["Heading4"]))
        story.append(Paragraph("1. Este documento representa o fechamento final da proposta.", styles["Normal"]))
        story.append(Paragraph("2. Os valores apresentados incluem todos os custos e acréscimos.", styles["Normal"]))
        story.append(Paragraph("3. Valores a receber incluem base e serviços de organização.", styles["Normal"]))
        story.append(Paragraph("4. Valores a pagar aos assistentes são responsabilidade da Organizer.", styles["Normal"]))
        story.append(Paragraph("5. Valores a pagar a lojas/fornecedores são responsabilidade do cliente.", styles["Normal"]))
        story.append(Paragraph("6. O Resultado Final representa o valor a receber menos os pagamentos aos assistentes.", styles["Normal"]))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF: {str(e)}")