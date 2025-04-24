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