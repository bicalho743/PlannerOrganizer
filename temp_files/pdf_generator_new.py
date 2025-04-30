#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de geração de PDF para o sistema de Planner Organizer
Este módulo foi refatorado para remover código legado e utilizar 
as versões melhoradas do gerador de PDF.
"""

# Importações necessárias
import os
import traceback
from datetime import datetime
from io import BytesIO
import base64

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm

import pandas as pd


def gerar_pdf_cliente(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão para cliente da proposta
    
    Esta função é um redirecionamento para a versão melhorada.
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão pública)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Usar a versão melhorada com layout profissional
    print("DEBUG: Usando o gerador de PDF cliente melhorado!")
    from utils.pdf_generator_melhorado import gerar_pdf_cliente_melhorado
    return gerar_pdf_cliente_melhorado(proposta, cliente, acrescimos, filename)


def gerar_pdf_interno(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão interna da proposta, incluindo todos os detalhes
    financeiros, custos e margens
    
    Esta função é um redirecionamento para a versão melhorada.
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão completa)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Usar a versão melhorada com layout profissional
    print("DEBUG: Usando o gerador de PDF interno melhorado!")
    from utils.pdf_generator_interno_melhorado import gerar_pdf_interno_melhorado
    return gerar_pdf_interno_melhorado(proposta, cliente, acrescimos, filename)


def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta com o novo formato solicitado
    
    Esta função é um redirecionamento para a versão melhorada.
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Usar a versão melhorada com layout profissional
    print("DEBUG: Usando o gerador de PDF fechamento melhorado!")
    from utils.pdf_generator_melhorado import gerar_pdf_fechamento_novo
    return gerar_pdf_fechamento_novo(proposta, cliente, acrescimos, filename)


def get_pdf_as_base64(filename):
    """
    Converte um arquivo PDF para base64 para exibição no Streamlit
    
    Args:
        filename: Nome do arquivo PDF
        
    Returns:
        str: String base64 com o conteúdo do PDF
    """
    try:
        with open(filename, "rb") as f:
            pdf_bytes = f.read()
            
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        return base64_pdf
    except Exception as e:
        print(f"Erro ao converter PDF para base64: {str(e)}")
        return None