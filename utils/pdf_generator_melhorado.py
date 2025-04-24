from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import os
import traceback
import pandas as pd

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
        
        # Bloco de investimento
        y -= 40
        
        # Fundo do bloco de investimento
        c.setFillColor(azul_claro)
        c.rect(30, y - 40, width - 60, 60, fill=True, stroke=0)
        
        # Título "Investimento"
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y + 5, "Investimento")
        
        # Processar a descrição para exibir como itens
        descricao_itens = []
        if proposta.get('descricao'):
            for linha in proposta['descricao'].split('\n'):
                linha = linha.strip()
                if linha:
                    descricao_itens.append(linha)
        
        # Garantir que temos pelo menos três colunas, mesmo sem itens
        if not descricao_itens:
            descricao_itens = ["Serviço Base"]
        
        # Distribuir os itens em colunas
        num_itens = len(descricao_itens)
        itens_por_coluna = 1
        num_colunas = min(3, num_itens)  # No máximo 3 colunas
        
        # Posições X para as colunas
        x_pos = [40, 150, 280]
        
        # Exibir os itens em colunas
        for i in range(min(num_itens, num_colunas)):
            c.setFillColor(cinza_medio)
            c.setFont("Helvetica", 11)
            c.drawString(x_pos[i], y - 15, f"• {descricao_itens[i]}")
        
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
        c.drawString(40, y, "1. Os valores apresentados incluem todos os custos e acréscimos.")
        y -= 16
        c.drawString(40, y, "2. Valores a receber incluem base e serviços de organização.")
        y -= 16
        c.drawString(40, y, "3. Valores a pagar a lojas/fornecedores são responsabilidade do cliente.")
        
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