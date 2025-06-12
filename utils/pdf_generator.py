"""
Módulo para geração de PDFs de propostas
"""
import streamlit as st
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import pandas as pd
import io

def gerar_pdf_proposta(proposta_id):
    """
    Gera PDF de uma proposta específica
    
    Args:
        proposta_id: ID da proposta
        
    Returns:
        bytes: Conteúdo do PDF gerado
    """
    try:
        if 'db' not in st.session_state:
            raise Exception('Database não inicializado')
            
        db = st.session_state.db
        
        # Buscar dados da proposta
        propostas = db.get_propostas()
        if propostas.empty:
            raise Exception('Nenhuma proposta encontrada')
            
        proposta = propostas[propostas['id'] == proposta_id]
        if proposta.empty:
            raise Exception('Proposta não encontrada')
            
        proposta_data = proposta.iloc[0]
        
        # Criar buffer para o PDF
        buffer = io.BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        # Conteúdo do PDF
        story = []
        
        # Título
        story.append(Paragraph(f"Proposta #{proposta_data['numero']}", title_style))
        story.append(Spacer(1, 12))
        
        # Informações principais
        data_info = [
            ['Cliente:', proposta_data.get('cliente_nome', 'N/A')],
            ['Descrição:', proposta_data.get('descricao', 'N/A')],
            ['Valor:', f"R$ {proposta_data.get('valor', 0):.2f}"],
            ['Status:', proposta_data.get('status', 'N/A')],
            ['Data de Criação:', proposta_data.get('data_criacao', datetime.now()).strftime('%d/%m/%Y') if pd.notna(proposta_data.get('data_criacao')) else 'N/A']
        ]
        
        info_table = Table(data_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 24))
        
        # Observações se existirem
        if proposta_data.get('observacoes'):
            story.append(Paragraph("Observações:", styles['Heading2']))
            story.append(Paragraph(proposta_data['observacoes'], styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Rodapé
        story.append(Spacer(1, 24))
        story.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        
        # Construir PDF
        doc.build(story)
        
        # Retornar conteúdo
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

def gerar_pdf_relatorio_propostas(filtro_status=None):
    """
    Gera PDF com relatório de propostas
    
    Args:
        filtro_status: Status para filtrar propostas
        
    Returns:
        bytes: Conteúdo do PDF gerado
    """
    try:
        if 'db' not in st.session_state:
            raise Exception('Database não inicializado')
            
        db = st.session_state.db
        
        # Buscar propostas
        propostas = db.get_propostas()
        if propostas.empty:
            raise Exception('Nenhuma proposta encontrada')
            
        # Aplicar filtro se especificado
        if filtro_status:
            propostas = propostas[propostas['status'] == filtro_status]
        
        # Criar buffer para o PDF
        buffer = io.BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        # Conteúdo do PDF
        story = []
        
        # Título
        titulo = "Relatório de Propostas"
        if filtro_status:
            titulo += f" - Status: {filtro_status}"
        story.append(Paragraph(titulo, title_style))
        story.append(Spacer(1, 12))
        
        # Tabela de propostas
        data_table = [['Número', 'Cliente', 'Valor', 'Status']]
        
        for _, proposta in propostas.iterrows():
            data_table.append([
                str(proposta.get('numero', 'N/A')),
                proposta.get('cliente_nome', 'N/A')[:30],  # Limitar tamanho
                f"R$ {proposta.get('valor', 0):.2f}",
                proposta.get('status', 'N/A')
            ])
        
        propostas_table = Table(data_table, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1.5*inch])
        propostas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(propostas_table)
        story.append(Spacer(1, 24))
        
        # Resumo
        total_propostas = len(propostas)
        valor_total = propostas['valor'].sum() if 'valor' in propostas.columns else 0
        
        story.append(Paragraph("Resumo:", styles['Heading2']))
        story.append(Paragraph(f"Total de propostas: {total_propostas}", styles['Normal']))
        story.append(Paragraph(f"Valor total: R$ {valor_total:.2f}", styles['Normal']))
        
        # Rodapé
        story.append(Spacer(1, 24))
        story.append(Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        
        # Construir PDF
        doc.build(story)
        
        # Retornar conteúdo
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        raise Exception(f"Erro ao gerar relatório PDF: {str(e)}")