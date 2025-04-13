#!/usr/bin/env python3
# Criar um PDF de template básico para uso com a função de preenchimento

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Criar PDF
doc = SimpleDocTemplate(
    "proposta_template.pdf",
    pagesize=letter,
    rightMargin=72,
    leftMargin=72,
    topMargin=100,  # Maior margem para texto sobreposto
    bottomMargin=72
)

styles = getSampleStyleSheet()
elements = []

# Criar estilo personalizado para título
title_style = ParagraphStyle(
    'Title',
    parent=styles['Title'],
    textColor=colors.blue,
    alignment=1  # centralizado
)

# Adicionar título
elements.append(Paragraph("TEMPLATE DE PROPOSTA", title_style))
elements.append(Spacer(1, 60))  # espaço para texto sobreposto

# Adicionar espaço para os campos que serão preenchidos
for _ in range(5):
    elements.append(Paragraph("", styles['Normal']))
    elements.append(Spacer(1, 20))

# Adicionar nota de rodapé
footer_style = ParagraphStyle(
    'Footer',
    parent=styles['Normal'],
    textColor=colors.gray,
    alignment=1,
    fontSize=8
)
elements.append(Spacer(1, 40))
elements.append(Paragraph("Template para Proposta - Planner Organizer", footer_style))

# Construir o PDF
doc.build(elements)
print("Template PDF criado com sucesso!")