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
        
        # Configurações de cores (padrão da empresa)
        azul_principal = colors.HexColor("#1E366F")
        azul_claro = colors.HexColor("#EEF2FF")
        cinza_medio = colors.HexColor("#444444")
        
        # Carregar dados do perfil
        try:
            from utils.perfil_loader import carregar_perfil_usuario
            perfil = carregar_perfil_usuario()
        except:
            # Se falhar, usar padrão
            perfil = {'empresa': 'Planner Organizer'}
            
        # Configurações do documento
        width, height = A4
        c = canvas.Canvas(filename, pagesize=A4)
        
        # ===== CABEÇALHO COM FAIXA AZUL =====
        c.setFillColor(azul_principal)
        c.rect(0, height-60, width, 60, fill=True, stroke=0)
        
        # Título principal no cabeçalho
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(30, height-30, "Relatório de Serviço")
        
        # Subtítulo com número da proposta e nome do cliente
        c.setFont("Helvetica", 11)
        c.drawString(30, height-50, f"#{proposta.get('id')} - {cliente['nome']}")
        
        # Data no canto direito
        agora = datetime.now() - timedelta(hours=3)  # Ajustando para UTC-3 (Brasília)
        c.setFont("Helvetica", 10)
        data_str = agora.strftime('%d/%m/%Y')
        c.drawRightString(width-30, height-30, f"Data: {data_str}")
        
        # ===== INFORMAÇÕES DO CLIENTE =====
        y = height - 100  # Começando abaixo do cabeçalho
        
        # Título da seção
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Informações do Cliente")
        
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
        
        # Dados da proposta
        y -= 25
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        # Tipo e Status
        c.drawString(40, y, f"Tipo: {proposta.get('tipo_proposta', 'N/A')}")
        y -= 15
        c.drawString(40, y, f"Status: {proposta.get('status', 'N/A')}")
        y -= 15
        
        # Datas formatadas
        data_inicio_str = "N/A"
        if proposta.get('data_inicio'):
            if hasattr(proposta['data_inicio'], 'strftime'):
                data_inicio_str = proposta['data_inicio'].strftime('%d/%m/%Y')
            else:
                data_inicio_str = str(proposta['data_inicio'])
        c.drawString(40, y, f"Data Início: {data_inicio_str}")
        y -= 15
                
        data_fim_str = "N/A"
        if proposta.get('data_fim'):
            if hasattr(proposta['data_fim'], 'strftime'):
                data_fim_str = proposta['data_fim'].strftime('%d/%m/%Y')
            else:
                data_fim_str = str(proposta['data_fim'])
        c.drawString(40, y, f"Data Fim: {data_fim_str}")
        y -= 15
        
        # Prazo de entrega em dias
        prazo_dias = "N/A"
        if proposta.get('data_inicio') and proposta.get('data_fim'):
            if hasattr(proposta['data_inicio'], 'toordinal') and hasattr(proposta['data_fim'], 'toordinal'):
                dias = (proposta['data_fim'] - proposta['data_inicio']).days
                prazo_dias = f"{dias} dias"
            elif isinstance(proposta['data_inicio'], str) and isinstance(proposta['data_fim'], str):
                # Tentativa de converter strings para data
                try:
                    inicio = datetime.strptime(proposta['data_inicio'], "%Y-%m-%d")
                    fim = datetime.strptime(proposta['data_fim'], "%Y-%m-%d")
                    dias = (fim - inicio).days
                    prazo_dias = f"{dias} dias"
                except:
                    pass
        c.drawString(40, y, f"Prazo de Entrega: {prazo_dias}")
        
        # ===== DESCRIÇÃO DO SERVIÇO =====
        y -= 35
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "DESCRIÇÃO DO SERVIÇO")
        
        # Texto da descrição
        y -= 25
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        # Processar a descrição para remover caracteres indesejados e quebrar em linhas se necessário
        descricao = proposta.get('descricao', 'Sem descrição')
        # Limpar caracteres especiais que podem aparecer como ■
        descricao = descricao.replace('■', ' ').replace('\r\n', ' ').replace('\n', ' ').strip()
        # Substituir múltiplos espaços por um único espaço
        descricao = re.sub(r'\s+', ' ', descricao)
        
        # Quebrar texto em múltiplas linhas se for muito longo
        linhas_descricao = textwrap.wrap(descricao, width=80)
        for linha in linhas_descricao[:3]:  # Limitar a 3 linhas para não ocupar muito espaço
            c.drawString(40, y, linha)
            y -= 15
        
        # ===== ITENS INCLUSOS (TABELA) =====
        y -= 25
        c.setFillColor(azul_principal)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "ITENS INCLUSOS")
        
        # Configuração da tabela
        y -= 25
        table_width = width - 80
        desc_col_width = table_width * 0.75
        valor_col_width = table_width * 0.25
        
        # Cabeçalho da tabela
        c.setFillColor(azul_principal)
        c.rect(40, y-15, desc_col_width, 15, fill=True, stroke=False)
        c.rect(40+desc_col_width, y-15, valor_col_width, 15, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y-12, "Descrição")
        c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, "Valor")
        
        # Conteúdo da tabela
        y -= 15
        linha = 0
        
        # Serviço base - sempre incluir "Personal Organizer" como primeiro item
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 9)
        
        # Alternância de cores para linhas
        if linha % 2 == 0:
            c.setFillColor(azul_claro)
            c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
            
        c.setFillColor(cinza_medio)
        c.drawString(50, y-12, "Personal Organizer")
        c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {float(proposta['valor']):.2f}")
        
        y -= 15
        linha += 1
        
        # Inicializar total com o valor base da proposta
        total = float(proposta['valor'])
        
        # Processar acréscimos dinâmicos da proposta, mas excluir assistentes
        if hasattr(acrescimos, 'empty') and not acrescimos.empty:
            print(f"DEBUG PDF: Processando {len(acrescimos)} acréscimos para o relatório")
            
            # Agrupar acréscimos por categoria para facilitar a visualização
            categorias = {'produtos': [], 'fornecedores': [], 'outros': []}
            
            for _, acrescimo in acrescimos.iterrows():
                tipo = acrescimo.get('tipo', '').lower()
                fornecedor = acrescimo.get('fornecedor', '')
                descricao = acrescimo.get('descricao', '')
                valor = float(acrescimo.get('valor', 0))
                quantidade = acrescimo.get('quantidade', 1)
                
                # Pular assistentes que não devem aparecer no relatório para cliente
                if tipo == 'assistente':
                    print(f"DEBUG PDF: Pulando item assistente: {descricao}")
                    continue
                
                # Formatar descrição do item
                if quantidade > 1:
                    descricao_formatada = f"{descricao} ({quantidade} un.)"
                else:
                    descricao_formatada = descricao
                    
                # Adicionar fornecedor se disponível
                if fornecedor and not descricao_formatada.endswith(f"({fornecedor})") and not fornecedor.lower() in descricao_formatada.lower():
                    descricao_formatada = f"{descricao_formatada} - {fornecedor}"
                
                # Classificar o item na categoria apropriada
                if tipo == 'produto' or tipo == 'venda':
                    categorias['produtos'].append({'descricao': descricao_formatada, 'valor': valor})
                elif tipo == 'fornecedor':
                    categorias['fornecedores'].append({'descricao': descricao_formatada, 'valor': valor})
                else:
                    categorias['outros'].append({'descricao': descricao_formatada, 'valor': valor})
                    
                # Adicionar ao total
                total += valor
            
            # Adicionar produtos primeiro
            for item in categorias['produtos']:
                # Alternância de cores para linhas
                if linha % 2 == 0:
                    c.setFillColor(azul_claro)
                    c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
                    
                c.setFillColor(cinza_medio)
                c.drawString(50, y-12, item['descricao'])
                c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {item['valor']:.2f}")
                
                y -= 15
                linha += 1
            
            # Adicionar outros itens
            for item in categorias['outros']:
                # Alternância de cores para linhas
                if linha % 2 == 0:
                    c.setFillColor(azul_claro)
                    c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
                    
                c.setFillColor(cinza_medio)
                c.drawString(50, y-12, item['descricao'])
                c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {item['valor']:.2f}")
                
                y -= 15
                linha += 1
            
            # Adicionar fornecedores por último
            for item in categorias['fornecedores']:
                # Alternância de cores para linhas
                if linha % 2 == 0:
                    c.setFillColor(azul_claro)
                    c.rect(40, y-15, table_width, 15, fill=True, stroke=False)
                    
                c.setFillColor(cinza_medio)
                c.drawString(50, y-12, item['descricao'])
                c.drawRightString(40 + desc_col_width + valor_col_width - 10, y-12, f"R$ {item['valor']:.2f}")
                
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
        
        y -= 25
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
        
        # Data de geração pequena no rodapé com horário de Brasília (UTC-3)
        c.setFont("Helvetica", 7)
        c.drawCentredString(width/2, 5, f"Relatório gerado em {agora.strftime('%d/%m/%Y às %H:%M')}")
        
        # Salvar PDF
        c.save()
        
        print(f"DEBUG PDF NOVO: Relatório de serviço gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar relatório de serviço: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar relatório de serviço: {str(e)}")