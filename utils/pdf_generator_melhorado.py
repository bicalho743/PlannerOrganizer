from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import os
import traceback
import pandas as pd


def gerar_pdf_relatorio_servico(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o relatório de serviço para o cliente, formatado com design profissional
    com cabeçalho e rodapé azul
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão pública)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    print("DEBUG: Usando o gerador de relatório de serviço!")
    # Logs para debugging
    print("DEBUG PDF NOVO: Gerando relatório de serviço para proposta #{} com novo design".format(proposta.get('id', 'N/A')))
    print("DEBUG PDF NOVO: Cliente: {}".format(cliente.get('nome', 'N/A')))
    print("DEBUG PDF NOVO: Filename: {}".format(filename))
    print("DEBUG PDF NOVO: Acréscimos: {} registros".format(len(acrescimos) if hasattr(acrescimos, 'empty') and not acrescimos.empty else 0))
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Configurações da página
        width, height = A4
        
        # Cores padrão para melhor consistência
        azul_principal = colors.HexColor("#1E366F")  # Azul escuro para cabeçalhos
        azul_claro = colors.HexColor("#EEF2FF")      # Azul claro para fundos
        cinza_claro = colors.HexColor("#F5F5F5")     # Cinza claro para alternância
        cinza_medio = colors.HexColor("#666666")     # Cinza médio para textos normais
        
        # Criação do canvas diretamente para maior controle do layout
        c = canvas.Canvas(filename, pagesize=A4)
        c.setTitle(f"Relatório de Serviço - {cliente['nome']}")
        
        # Carregar dados do perfil do usuário
        try:
            from utils.perfil_loader import carregar_perfil_usuario
            perfil = carregar_perfil_usuario()
            print(f"DEBUG PDF: Perfil do usuário carregado: {perfil.get('empresa', 'N/A')}")
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao carregar perfil do usuário: {str(e)}")
            perfil = {'empresa': 'Planner Organizer', 'telefone': '(11) 98765-4321', 'email': 'contato@plannerorganizer.com.br'}
            
        # ===== CABEÇALHO COM FAIXA AZUL =====
        c.setFillColor(azul_principal)
        c.rect(0, height-60, width, 60, fill=True, stroke=0)
        
        # Título no cabeçalho
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height-35, "RELATÓRIO DE SERVIÇO")
        
        # Número da proposta e cliente
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height-55, f"Proposta #{proposta['id']} - {cliente['nome']}")
        
        # ===== INFORMAÇÕES DO CLIENTE =====
        y = height - 100  # Começando abaixo do cabeçalho
        
        # Título da seção
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Informações do Cliente")
        
        # Linha decorativa sob o título
        c.setStrokeColor(azul_principal)
        c.line(40, y-5, 200, y-5)
        
        # Dados do cliente
        y -= 25
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Nome: {cliente['nome']}")
        y -= 15
        c.drawString(40, y, f"Email: {cliente.get('email', 'N/A')}")
        y -= 15
        c.drawString(40, y, f"Telefone: {cliente.get('telefone', 'N/A')}")
        
        # ===== INFORMAÇÕES DA PROPOSTA =====
        y -= 30
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Informações da Proposta")
        
        # Linha decorativa sob o título
        c.setStrokeColor(azul_principal)
        c.line(40, y-5, 220, y-5)
        
        # Dados da proposta em duas colunas
        col1_x = 40
        col2_x = width/2
        y -= 25
        
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        # Coluna 1
        c.drawString(col1_x, y, f"Tipo: {proposta.get('tipo_proposta', 'N/A')}")
        y -= 15
        c.drawString(col1_x, y, f"Status: {proposta.get('status', 'N/A')}")
        
        # Coluna 2 - alinhada
        y_col2 = y + 15  # Reinicia na mesma altura da primeira linha da coluna 1
        
        # Datas formatadas
        data_inicio_str = "N/A"
        if proposta.get('data_inicio'):
            if hasattr(proposta['data_inicio'], 'strftime'):
                data_inicio_str = proposta['data_inicio'].strftime('%d/%m/%Y')
            else:
                data_inicio_str = str(proposta['data_inicio'])
                
        data_fim_str = "N/A"
        if proposta.get('data_fim'):
            if hasattr(proposta['data_fim'], 'strftime'):
                data_fim_str = proposta['data_fim'].strftime('%d/%m/%Y')
            else:
                data_fim_str = str(proposta['data_fim'])
                
        # Prazo de entrega
        prazo_str = "N/A"
        if proposta.get('prazo_entrega'):
            if hasattr(proposta['prazo_entrega'], 'strftime'):
                prazo_str = proposta['prazo_entrega'].strftime('%d/%m/%Y')
            else:
                prazo_str = str(proposta['prazo_entrega'])
            
        # Adicionando datas na coluna 2
        c.drawString(col2_x, y_col2, f"Data Início: {data_inicio_str}")
        y_col2 -= 15
        c.drawString(col2_x, y_col2, f"Data Fim: {data_fim_str}")
        y_col2 -= 15
        c.drawString(col2_x, y_col2, f"Prazo de Entrega: {prazo_str}")
        
        # Ajusta Y para o menor valor entre as duas colunas
        y = min(y, y_col2) - 15
        
        # ===== DESCRIÇÃO DO SERVIÇO =====
        y -= 15
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "DESCRIÇÃO DO SERVIÇO")
        
        # Fundo colorido para a descrição
        c.setFillColor(azul_claro)
        c.rect(40, y-40, width-80, 30, fill=True, stroke=False)
        
        # Texto da descrição
        y -= 25
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        # Se a descrição for longa, podemos implementar quebra de linhas
        descricao = proposta.get('descricao', 'Sem descrição')
        c.drawString(50, y, descricao)
        
        # ===== SERVIÇOS REALIZADOS (TABELA) =====
        y -= 45
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "ITENS INCLUSOS")
        
        # Cabeçalho da tabela
        y -= 25
        table_width = width - 80
        desc_col_width = table_width * 0.75
        valor_col_width = table_width * 0.25
        
        # Desenhar fundo do cabeçalho
        c.setFillColor(azul_principal)
        c.rect(40, y-15, desc_col_width, 15, fill=True, stroke=False)
        c.rect(40+desc_col_width, y-15, valor_col_width, 15, fill=True, stroke=False)
        
        # Texto do cabeçalho
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(40 + desc_col_width/2, y-12, "Descrição")
        c.drawCentredString(40 + desc_col_width + valor_col_width/2, y-12, "Valor")
        
        # Conteúdo da tabela
        y -= 15
        linha = 0
        
        # Serviço base
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 9)
        
        # Alternância de cores para linhas
        if linha % 2 == 0:
            c.setFillColor(azul_claro)
            c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
            
        c.setFillColor(cinza_medio)
        c.drawString(50, y-12, "Serviço Base")
        c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {float(proposta['valor']):.2f}")
        
        y -= 15
        linha += 1
        
        # Total para cálculo
        total = float(proposta['valor'])
        
        # Adicionar acréscimos, exceto os de tipo 'assistente'
        for _, acrescimo in acrescimos.iterrows():
            tipo = acrescimo.get('tipo', 'OUTRO')
            
            # Pular itens de assistentes que não devem aparecer no relatório para o cliente
            if tipo.lower() == 'assistente':
                continue
                
            descricao = acrescimo.get('descricao', 'Item adicional')
            fornecedor = acrescimo.get('fornecedor', '')
            valor = float(acrescimo.get('valor', 0))
            
            # Formatar descrição completa com tipo e fornecedor
            descricao_formatada = f"{tipo.upper()} - {descricao}"
            if fornecedor:
                descricao_formatada += f" ({fornecedor})"
            
            # Alternância de cores para linhas
            if linha % 2 == 0:
                c.setFillColor(azul_claro)
                c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
            
            # Adicionar item à tabela
            c.setFillColor(cinza_medio)
            c.drawString(50, y-12, descricao_formatada)
            c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {valor:.2f}")
            
            total += valor
            y -= 15
            linha += 1
        
        # Linha de total com fundo destacado
        c.setFillColor(azul_principal)
        c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y-12, "Total:")
        c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {total:.2f}")
        
        # ===== OBSERVAÇÕES =====
        y -= 40
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Observações:")
        
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        observacoes = [
            "1. Este documento representa o relatório para cliente dos serviços prestados.",
            "2. Para quaisquer dúvidas sobre os serviços, entre em contato conosco.",
            "3. Agradecemos a confiança em nossos serviços."
        ]
        
        for obs in observacoes:
            c.drawString(40, y, obs)
            y -= 15
            
        # ===== RODAPÉ COM FAIXA AZUL =====
        c.setFillColor(azul_principal)
        c.rect(0, 0, width, 60, fill=True, stroke=0)
        
        # Informações de contato no rodapé
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        y_rodape = 40
        
        c.drawCentredString(width/2, y_rodape, f"{perfil.get('empresa', 'Planner Organizer')}")
        y_rodape -= 12
        c.setFont("Helvetica", 9)
        c.drawCentredString(width/2, y_rodape, f"{perfil.get('email', 'contato@plannerorganizer.com.br')}")
        y_rodape -= 12
        c.drawCentredString(width/2, y_rodape, f"{perfil.get('telefone', '(11) 98765-4321')} | www.plannerorganizer.com.br")
        
        # Data de geração pequena no rodapé
        c.setFont("Helvetica", 7)
        c.drawCentredString(width/2, 5, f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        
        # Salvar PDF
        c.save()
        
        print(f"DEBUG PDF NOVO: Relatório de serviço gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar relatório de serviço: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar relatório de serviço: {str(e)}")


def gerar_pdf_cliente_melhorado(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão para cliente da proposta, com design profissional
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão pública)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Para facilitar a manutenção, direcionamos para o relatório de serviço
    # conforme solicitado pelo usuário
    if proposta.get('status') == 'Concluída':
        # Se a proposta estiver concluída, gerar relatório de serviço
        return gerar_pdf_relatorio_servico(proposta, cliente, acrescimos, filename)
        
    # Se não for concluída, continua com o código original para proposta
    # Logs para debugging
    print("DEBUG PDF NOVO: Gerando PDF para proposta #{} com novo design".format(proposta.get('id', 'N/A')))
    print("DEBUG PDF NOVO: Cliente: {}".format(cliente.get('nome', 'N/A')))
    print("DEBUG PDF NOVO: Filename: {}".format(filename))
    print("DEBUG PDF NOVO: Acréscimos: {} registros".format(len(acrescimos) if hasattr(acrescimos, 'empty') and not acrescimos.empty else 0))
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Criação do documento
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Inicialização dos elementos
        story = []
        styles = getSampleStyleSheet()
        
        # Carregar dados do perfil do usuário
        try:
            from utils.perfil_loader import carregar_perfil_usuario
            perfil = carregar_perfil_usuario()
            print(f"DEBUG PDF: Perfil do usuário carregado: {perfil.get('empresa', 'N/A')}")
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao carregar perfil do usuário: {str(e)}")
            perfil = {'empresa': 'Planner Organizer'}
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor("#1E366F"),
            alignment=1,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#1E366F"),
            spaceBefore=10,
            spaceAfter=10
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceBefore=4,
            spaceAfter=4
        )
        
        # Cabeçalho com título centralizados
        story.append(Paragraph(f"{perfil.get('empresa', 'Planner Organizer')}", title_style))
        story.append(Paragraph(f"PROPOSTA DE SERVIÇO #{proposta['id']} - {cliente['nome']}", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Informações do Cliente em parágrafos separados (mais seguro)
        story.append(Paragraph(f"<b>Cliente:</b> {cliente['nome']}", normal_style))
        story.append(Paragraph(f"<b>Endereço:</b> {cliente.get('endereco', 'N/A')}", normal_style))
        story.append(Paragraph(f"<b>Telefone:</b> {cliente.get('telefone', 'N/A')}", normal_style))
        story.append(Paragraph(f"<b>Email:</b> {cliente.get('email', 'N/A')}", normal_style))
        story.append(Spacer(1, 10))
        
        # Informações da Proposta em um bloco separado com fundo colorido
        proposal_style = ParagraphStyle(
            'ProposalStyle',
            parent=normal_style,
            backColor=colors.HexColor("#EEF2FF"),
            borderColor=colors.HexColor("#1E366F"),
            borderWidth=1,
            borderPadding=8,
            borderRadius=5,
            spaceBefore=10,
            spaceAfter=10
        )
        
        proposal_date = proposta['data_proposta'].strftime('%d/%m/%Y') if proposta.get('data_proposta') else 'N/A'
        
        # Informações da proposta em parágrafos separados com estilo personalizado
        story.append(Paragraph(f"<b>Tipo de Serviço:</b> {proposta['tipo_proposta']}", proposal_style))
        story.append(Paragraph(f"<b>Data da Proposta:</b> {proposal_date}", proposal_style))
        story.append(Paragraph(f"<b>Status:</b> {proposta['status']}", proposal_style))
        story.append(Paragraph(f"<b>Valor Total:</b> R$ {float(proposta['valor']):.2f}", proposal_style))
        story.append(Spacer(1, 15))
        
        # Descrição do Serviço com título destacado
        service_title = ParagraphStyle(
            'ServiceTitle',
            parent=subtitle_style,
            backColor=colors.HexColor("#1E366F"),
            textColor=colors.white,
            borderPadding=5,
            borderRadius=5,
            alignment=0
        )
        
        story.append(Paragraph("DESCRIÇÃO DO SERVIÇO", service_title))
        story.append(Spacer(1, 10))
        story.append(Paragraph(proposta['descricao'], normal_style))
        story.append(Spacer(1, 15))
        
        # Tabela de Acréscimos/Itens com design profissional - apenas se houver acréscimos
        if not acrescimos.empty:
            story.append(Paragraph("ITENS INCLUSOS", service_title))
            story.append(Spacer(1, 10))
            
            # Dados para a tabela de acréscimos
            data = [["Item", "Descrição", "Valor"]]
            total = float(proposta['valor'])
            
            for _, acrescimo in acrescimos.iterrows():
                # Suprimir dados internos como fornecedor, tipo, etc.
                # Mostrar apenas o que o cliente precisa ver
                descricao = acrescimo.get('descricao', '')
                valor = float(acrescimo['valor'])
                
                # Adicionar à tabela apenas dados relevantes para o cliente
                data.append([
                    "Item adicional",  # Simplificado para o cliente
                    descricao,
                    f"R$ {valor:.2f}"
                ])
                
                total += valor
            
            # Adicionar linha de total
            data.append(["TOTAL", "", f"R$ {total:.2f}"])
            
            # Estilização profissional da tabela
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E366F")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#EEF2FF")),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#BBCBEA")),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#1E366F")),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ])
            
            # Criar e adicionar tabela
            col_widths = [2.0*inch, 3.0*inch, 1.5*inch]
            table = Table(data, colWidths=col_widths)
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Condições de Pagamento e Observações
        story.append(Paragraph("CONDIÇÕES DA PROPOSTA", service_title))
        story.append(Spacer(1, 10))
        
        # Texto das condições com formatação em itens (parágrafos separados)
        story.append(Paragraph("<b>1. Pagamento:</b> O pagamento deve ser realizado conforme acordo prévio, podendo ser à vista ou parcelado, via transferência bancária, PIX ou boleto.", normal_style))
        story.append(Spacer(1, 6))
        
        story.append(Paragraph("<b>2. Custos adicionais:</b> Despesas não previstas nesta proposta serão apresentadas para aprovação antes de sua execução.", normal_style))
        story.append(Spacer(1, 6))
        
        story.append(Paragraph("<b>3. Documentação:</b> Os documentos produzidos durante o serviço serão entregues em formato digital ou físico conforme acordado.", normal_style))
        story.append(Spacer(1, 6))
        
        story.append(Paragraph("<b>4. Treinamento:</b> Caso seja necessário, sessões de treinamento para utilização dos sistemas organizados serão agendadas.", normal_style))
        story.append(Spacer(1, 6))
        
        story.append(Paragraph("<b>5. Produtos:</b> Caso a proposta inclua produtos, estes serão entregues conforme especificado nos itens da proposta.", normal_style))
        story.append(Spacer(1, 15))
        
        # Assinaturas
        story.append(Paragraph("APROVAÇÃO", service_title))
        story.append(Spacer(1, 10))
        
        # Texto de aprovação - formato simplificado
        story.append(Paragraph("Proposta válida por 30 dias a partir da data de emissão. Para formalizar sua aceitação, por favor, assine abaixo.", normal_style))
        story.append(Spacer(1, 30))
        
        # Linhas de Assinatura
        signature_data = [
            ["_______________________________", "_______________________________"],
            [f"{cliente['nome']}", f"{perfil.get('nome', 'Representante')}"],
            ["Cliente", f"{perfil.get('empresa', 'Planner Organizer')}"]
        ]
        
        signature_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
            ('LINEABOVE', (1, 0), (1, 0), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
        ])
        
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(signature_style)
        story.append(signature_table)
        
        # Data e Local
        story.append(Spacer(1, 30))
        
        # Estilo centrado para a data
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1  # Centro
        )
        
        story.append(Paragraph(f"Local e data: ________________________, _____ de _______________ de {datetime.now().year}", date_style))
        
        # Rodapé com dados de contato
        story.append(Spacer(1, 40))
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,  # Centro
            textColor=colors.HexColor("#1E366F")
        )
        
        company = perfil.get('empresa', 'Planner Organizer')
        phone = perfil.get('telefone', '')
        email = perfil.get('email', '')
        
        # Montar texto do rodapé conforme dados disponíveis
        footer_parts = []
        if company:
            footer_parts.append(company)
        if phone:
            footer_parts.append(f"Tel: {phone}")
        if email:
            footer_parts.append(f"Email: {email}")
            
        footer_text = " | ".join(footer_parts)
        
        story.append(Paragraph(footer_text, footer_style))
        
        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF NOVO: PDF gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF para cliente: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF para cliente: {str(e)}")


def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    ALIAS para compatibilidade.
    """
    return gerar_pdf_fechamento_novo(proposta, cliente, acrescimos, filename)

def gerar_pdf_fechamento_novo(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta utilizando o novo design
    mais profissional e organizado.
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF NOVO: Gerando PDF para proposta #{proposta.get('id', 'N/A')} com novo design")
    print(f"DEBUG PDF NOVO: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF NOVO: Filename: {filename}")
    print(f"DEBUG PDF NOVO: Acréscimos: {len(acrescimos) if isinstance(acrescimos, pd.DataFrame) and not acrescimos.empty else 0} registros")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Canvas approach (mais flexível para layout e design)
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Definir cores personalizadas
        cinza_claro = colors.HexColor("#f5f7fa")     # fundo
        cinza_medio = colors.HexColor("#5A6A85")     # textos
        azul_escuro = colors.HexColor("#1E366F")     # acentos (cabeçalho)
        azul_claro = colors.HexColor("#e9f2ff")      # destaque
        
        # Tons adicionais para melhorar o contraste visual
        cinza_muito_claro = colors.HexColor("#f8f9fc")  # fundo ainda mais claro para áreas de destaque
        azul_destaque = colors.HexColor("#d4e5fd")      # azul bem claro para seções de conteúdo

        # Cabeçalho
        c.setFillColor(azul_escuro)
        c.rect(0, height - 60, width, 60, fill=True, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(30, height - 40, f"Proposta #{proposta.get('id', 'N/A')} - {cliente.get('nome', 'Cliente')}")
        
        # Data
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        c.drawString(30, height - 70, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Informações da Proposta
        y = height - 100
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "Informações da Proposta")
        y -= 20
        
        # Tipo da proposta
        c.setFont("Helvetica", 11)
        c.drawString(40, y, f"Tipo: {proposta.get('tipo_proposta', 'Organização')}")
        y -= 16
        
        # Status da proposta
        c.drawString(40, y, f"Status: {proposta.get('status', 'Em elaboração')}")
        y -= 16
        
        # Data de início
        data_inicio_str = "N/A"
        if proposta.get('data_inicio'):
            if hasattr(proposta['data_inicio'], 'strftime'):
                data_inicio_str = proposta['data_inicio'].strftime('%d/%m/%Y')
            else:
                data_inicio_str = str(proposta['data_inicio'])
        c.drawString(40, y, f"Data Início: {data_inicio_str}")
        y -= 16
        
        # Data de fim
        data_fim_str = "N/A"
        if proposta.get('data_fim'):
            if hasattr(proposta['data_fim'], 'strftime'):
                data_fim_str = proposta['data_fim'].strftime('%d/%m/%Y')
            else:
                data_fim_str = str(proposta['data_fim'])
        c.drawString(40, y, f"Data Fim: {data_fim_str}")
        y -= 16
        
        # Prazo de entrega
        prazo_str = "N/A"
        if proposta.get('data_inicio') and proposta.get('data_fim'):
            if hasattr(proposta['data_inicio'], 'days') and hasattr(proposta['data_fim'], 'days'):
                dias = (proposta['data_fim'] - proposta['data_inicio']).days
                prazo_str = f"{dias} dias"
        c.drawString(40, y, f"Prazo de Entrega: {prazo_str}")
        
        # Layout completamente redesenhado - seção única e mais limpa
        y -= 40
        
        # Título principal e subtítulo em vez de caixas
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y + 5, "Descrição e Investimento")
        
        # Desenhar linha separadora horizontal
        c.setStrokeColor(azul_escuro)
        c.setLineWidth(1)
        c.line(40, y - 5, width - 40, y - 5)
        
        # Processar o texto da descrição diretamente
        import textwrap
        
        # Espaço para descrição do serviço
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Descrição do Serviço:")
        
        # Processar o texto da descrição
        descricao_text = proposta.get('descricao', 'Serviço Base')
        
        # Substituir caracteres problemáticos e remover formatação inconsistente
        descricao_text = descricao_text.replace("•", "- ")
        descricao_text = descricao_text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Separar em parágrafos
        paragrafos = descricao_text.split('\n')
        
        # Depois, cada parágrafo quebrar por tamanho
        max_chars_per_line = 85  # Um pouco maior para aproveitar o espaço
        todas_linhas = []
        for paragrafo in paragrafos:
            if paragrafo.strip():  # Ignorar linhas vazias
                linhas_quebradas = textwrap.wrap(paragrafo.strip(), max_chars_per_line)
                todas_linhas.extend(linhas_quebradas)
        
        # Se não tiver nenhuma linha, adicionar um texto padrão
        if not todas_linhas:
            todas_linhas = ["Serviço Base"]
        
        # Configurar a área de texto
        y -= 20
        line_height = 14
        
        # Desenhar as linhas (limitado a 6 para não ficar muito grande)
        max_lines = 6  
        for i, linha in enumerate(todas_linhas[:max_lines]):
            c.setFont("Helvetica", 10)
            c.drawString(50, y - (i * line_height), linha)
        
        # Se houver mais linhas, indicar
        if len(todas_linhas) > max_lines:
            linhas_extras = len(todas_linhas) - max_lines
            c.setFillColor(azul_escuro)
            texto_mais = f"... e mais {linhas_extras} {'linha' if linhas_extras == 1 else 'linhas'}"
            c.drawString(50, y - (max_lines * line_height), texto_mais)
        
        # Ajustar a posição Y considerando o número de linhas mostradas
        linhas_mostradas = min(len(todas_linhas), max_lines) 
        y -= (linhas_mostradas * line_height + 25)
        
        # Exibir valor e status
        valor_str = f"R$ {float(proposta.get('valor', 0)):.2f}"
        status_str = proposta.get('status_pagamento_base', 'Pendente')
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(azul_escuro)
        c.drawString(40, y - 35, f"Total: {valor_str} – Status: {status_str}")
        
        # Observações
        y -= 80
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "Observações:")
        c.setFont("Helvetica", 11)
        
        # Lista de observações
        y -= 20
        
        # Definir as observações padrão
        observacoes = [
            "1. Pagamento sinal, na reserva da data, via PIX",
            "2. Os valores apresentados incluem todos os custos.",
            "3. Não está incluído a organização de documentos.",
            "4. No caso da proposta incluir treinamento, é necessário a presença de funcionário no período da organização",
            "5. Não incluido produtos e organizadores, caso o cliente opte por adquirí-los"
        ]
        
        # Função para quebrar linhas muito longas
        import textwrap
        max_largura_obs = 80
        
        # Desenhar cada observação, tratando quebras de linha para items muito longos
        for obs in observacoes:
            # Se a linha for muito longa, quebrar
            if len(obs) > max_largura_obs:
                # Obter o prefixo (número e ponto)
                prefixo = obs.split(". ")[0] + ". "
                
                # Obter o texto após o prefixo
                texto = obs[len(prefixo):]
                
                # Adicionar o prefixo
                c.drawString(40, y, prefixo)
                
                # Quebrar o texto restante
                linhas_quebradas = textwrap.wrap(texto, max_largura_obs)
                
                # Desenhar a primeira linha após o prefixo
                c.drawString(40 + c.stringWidth(prefixo, "Helvetica", 11), y, linhas_quebradas[0])
                
                # Desenhar linhas adicionais, se houver
                for i, linha in enumerate(linhas_quebradas[1:], 1):
                    y -= 14
                    c.drawString(45, y, linha)
            else:
                # Se a linha for curta, apenas desenhar
                c.drawString(40, y, obs)
            
            # Avançar para a próxima observação
            y -= 18
        
        # Adicionar informações do usuário/empresa no rodapé
        c.setFillColor(azul_escuro)
        c.rect(0, 0, width, 40, fill=True, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        
        # Obter informações do usuário logado (se disponível)
        import streamlit as st
        
        nome_empresa = "Planner Organizer"
        email_contato = "contato@plannerorganizer.com.br"
        website = "www.plannerorganizer.com.br"
        
        # Usar informações do usuário logado, se disponíveis
        if "usuario" in st.session_state and st.session_state.usuario:
            usuario = st.session_state.usuario
            
            # Obter nome do usuário ou empresa
            if isinstance(usuario, dict):
                if usuario.get("empresa"):
                    nome_empresa = usuario.get("empresa")
                elif usuario.get("nome"):
                    nome_empresa = usuario.get("nome")
                
                # Obter email do usuário
                if usuario.get("email"):
                    email_contato = usuario.get("email")
        
        # Adicionar informações personalizadas ao rodapé
        footer_text = f"{nome_empresa} | {email_contato} | {website}"
        c.drawString(30, 15, footer_text)
        
        # Salvar o PDF
        c.save()
        print(f"DEBUG PDF NOVO: PDF gerado com sucesso: {filename}")
        return filename
    
    except Exception as e:
        print(f"DEBUG PDF NOVO ERROR: Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

# Renomear para ser compatível com a chamada original
gerar_pdf_fechamento = gerar_pdf_fechamento_novo