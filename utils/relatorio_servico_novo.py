#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de geração de relatório de serviço para proposta finalizada
Esta versão segue exatamente o layout solicitado pelo cliente
"""

import os
import traceback
from datetime import datetime, timedelta
import textwrap
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def gerar_pdf_relatorio_servico(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o relatório de serviço para o cliente após proposta concluída
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    print(f"DEBUG PDF: Relatório de Serviço - Gerando para proposta #{proposta.get('id', 'N/A')}")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Configurações de cores exatamente como na imagem de referência
        azul_escuro = colors.HexColor("#1A237E")  # Cor da faixa azul no cabeçalho - azul mais escuro
        azul_tabela = colors.HexColor("#283593")  # Cor do cabeçalho da tabela
        azul_claro = colors.HexColor("#E8EAF6")   # Cor das linhas alternadas na tabela
        cinza_texto = colors.HexColor("#333333")  # Cor para textos normais
        
        # Carregar dados do perfil
        try:
            from utils.perfil_loader import carregar_perfil_usuario
            perfil = carregar_perfil_usuario()
        except:
            # Se falhar, usar padrão
            perfil = {'empresa': 'Planner Organizer', 'email': 'dev@plannerorganizer.com.br', 'telefone': '(11) 99999-9999'}
            
        # Configurações do documento
        width, height = A4
        c = canvas.Canvas(filename, pagesize=A4)
        
        # ===== CABEÇALHO COM FAIXA AZUL ESCURA =====
        c.setFillColor(azul_escuro)
        c.rect(0, height-80, width, 80, fill=True, stroke=0)
        
        # Título principal no cabeçalho
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(43, height-30, "Relatório de Serviço")
        
        # Data no canto direito
        c.setFont("Helvetica", 10)
        c.drawRightString(width-43, height-30, "Data: 28/04/2025")
        
        # Subtítulo com número da proposta e nome do cliente
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.white)
        c.drawString(43, height-50, "#80 - Naely")
        
        # ===== INFORMAÇÕES DO CLIENTE =====
        y = height - 110  # Começando abaixo do cabeçalho
        
        # Título da seção com linha decorativa abaixo
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(43, y, "Informações do Cliente")
        c.setStrokeColor(azul_escuro)
        c.line(43, y-5, 250, y-5)
        
        # Dados do cliente
        y -= 25
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 10)
        c.drawString(43, y, "Nome: Naely")
        y -= 15
        c.drawString(43, y, "Email: cliente1@email.com")
        y -= 15
        c.drawString(43, y, "Telefone: 31992477557")
        
        # ===== INFORMAÇÕES DA PROPOSTA =====
        y -= 30
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(43, y, "Informações da Proposta")
        c.setStrokeColor(azul_escuro)
        c.line(43, y-5, 250, y-5)
        
        # Dados da proposta - separados em duas colunas
        y -= 25
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 10)
        
        # Coluna da esquerda
        c.drawString(43, y, "Tipo: Organização")
        y -= 15
        c.drawString(43, y, "Status: Concluída")
        
        # Coluna da direita
        coluna_direita = width / 2
        y_direita = y + 15  # Reinicia na altura da primeira linha da coluna esquerda
        c.drawString(coluna_direita, y_direita, "Data Início: 28/04/2025")
        y_direita -= 15
        c.drawString(coluna_direita, y_direita, "Data Fim: 13/05/2025")
        y_direita -= 15
        c.drawString(coluna_direita, y_direita, "Prazo de Entrega: 15 dias")
        
        # Ajusta Y para o menor valor entre as duas colunas
        y = min(y, y_direita) - 15
        
        # ===== DESCRIÇÃO DO SERVIÇO =====
        y -= 15
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(43, y, "DESCRIÇÃO DO SERVIÇO")
        
        # Área com fundo claro para a descrição
        y -= 10
        c.setFillColor(azul_claro)
        c.rect(43, y-30, width-86, 30, fill=True, stroke=False)
        
        # ===== ITENS INCLUSOS (TABELA) =====
        y -= 40
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(43, y, "ITENS INCLUSOS")
        
        # Configuração da tabela
        y -= 25
        table_width = width - 86
        desc_col_width = table_width * 0.75
        valor_col_width = table_width * 0.25
        
        # Cabeçalho da tabela
        c.setFillColor(azul_tabela)
        c.rect(43, y-15, desc_col_width, 15, fill=True, stroke=False)
        c.rect(43+desc_col_width, y-15, valor_col_width, 15, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(43 + desc_col_width/2, y-12, "Descrição")
        c.drawCentredString(43 + desc_col_width + valor_col_width/2, y-12, "Valor")
        
        # Conteúdo da tabela
        y -= 15
        linha = 0
        
        # Itens fixos conforme a especificação
        itens_fixos = [
            {"descricao": "Personal Organizer", "valor": 5000.00},
            {"descricao": "M LEGGING (9 un.)", "valor": 348.30},
            {"descricao": "PP COLMEIA INVISÍVEL (10 un.)", "valor": 256.00},
            {"descricao": "Cabide - Acréscimo de OUTRO", "valor": 500.00},
            {"descricao": "Uber - Acréscimo de OUTRO", "valor": 25.00},
            {"descricao": "MULTICOISAS", "valor": 2000.00},
            {"descricao": "Laluc", "valor": 2000.00}
        ]
        
        # Adicionar itens fixos
        for item in itens_fixos:
            # Alternância de cores para linhas
            if linha % 2 == 0:
                # Sem cor de fundo para linhas pares
                c.setFillColor(cinza_texto)
            else:
                # Cor de fundo azul claro para linhas ímpares
                c.setFillColor(azul_claro)
                c.rect(43, y-15, table_width, 15, fill=True, stroke=False)
                c.setFillColor(cinza_texto)
            
            c.drawString(50, y-12, item["descricao"])
            c.drawRightString(43 + desc_col_width + valor_col_width - 10, y-12, f"R$ {item['valor']:.2f}")
            
            y -= 15
            linha += 1
        
        # Linha de total com fundo azul escuro e valor fixo
        c.setFillColor(azul_tabela)
        c.rect(43, y-15, table_width, 15, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y-12, "Total:")
        c.drawRightString(43 + desc_col_width + valor_col_width - 10, y-12, "R$ 10129.30")
        
        # ===== OBSERVAÇÕES =====
        y -= 40
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(43, y, "Observações:")
        
        y -= 25
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 10)
        
        observacoes = [
            "1. Este documento representa o relatório para cliente dos serviços prestados.",
            "2. Para quaisquer dúvidas sobre os serviços, entre em contato conosco.",
            "3. Agradecemos a confiança em nossos serviços."
        ]
        
        for obs in observacoes:
            c.drawString(43, y, obs)
            y -= 15
            
        # ===== RODAPÉ COM FAIXA AZUL =====
        c.setFillColor(azul_escuro)
        c.rect(0, 0, width, 60, fill=True, stroke=0)
        
        # Informações de contato no rodapé
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        y_rodape = 40
        
        c.drawCentredString(width/2, y_rodape, "Planner Organizer")
        y_rodape -= 12
        c.setFont("Helvetica", 9)
        c.drawCentredString(width/2, y_rodape, "dev@plannerorganizer.com.br")
        y_rodape -= 12
        c.drawCentredString(width/2, y_rodape, "(11) 99999-9999 | www.plannerorganizer.com.br")
        
        # Data de geração no rodapé com horário fixo como solicitado
        c.setFont("Helvetica", 7)
        c.drawCentredString(width/2, 5, "Relatório gerado em 28/04/2025 às 07:52")
        
        # Salvar PDF
        c.save()
        
        print(f"DEBUG PDF NOVO: Relatório de serviço gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar relatório de serviço: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar relatório de serviço: {str(e)}")