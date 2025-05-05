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
        
        # Configurações de cores iguais às do relatório interno
        cinza_claro = colors.HexColor("#f5f7fa")       # fundo
        cinza_medio = colors.HexColor("#5A6A85")       # textos normais
        azul_escuro = colors.HexColor("#1E366F")       # cabeçalho e títulos
        azul_claro = colors.HexColor("#e9f2ff")        # blocos de destaque
        azul_destaque = colors.HexColor("#d4e5fd")     # blocos de conteúdo
        azul_tabela = azul_escuro                      # cabeçalho da tabela
        cinza_texto = cinza_medio                      # textos normais
        
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
        
        # Data no canto direito (data atual)
        c.setFont("Helvetica", 10)
        data_atual = datetime.now().strftime('%d/%m/%Y')
        c.drawRightString(width-43, height-30, f"Data: {data_atual}")
        
        # Subtítulo com número da proposta e nome do cliente
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.white)
        c.drawString(43, height-50, f"#{proposta.get('numero', 'N/A')} - {cliente.get('nome', 'Cliente')}")
        
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
        c.drawString(43, y, f"Nome: {cliente.get('nome', 'N/A')}")
        y -= 15
        c.drawString(43, y, f"Email: {cliente.get('email', 'N/A')}")
        y -= 15
        c.drawString(43, y, f"Telefone: {cliente.get('telefone', 'N/A')}")
        
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
        c.drawString(43, y, f"Tipo: {proposta.get('tipo_proposta', 'Organização')}")
        y -= 15
        c.drawString(43, y, f"Status: {proposta.get('status', 'Concluída')}")
        
        # Coluna da direita
        coluna_direita = width / 2
        y_direita = y + 15  # Reinicia na altura da primeira linha da coluna esquerda
        
        # Formatar datas se estiverem disponíveis
        data_inicio = proposta.get('data_inicio', '28/04/2025')
        data_fim = proposta.get('data_fim', '13/05/2025')
        prazo = proposta.get('prazo_entrega', '15 dias')
        
        # Se as datas forem objetos datetime, formatar adequadamente
        if hasattr(data_inicio, 'strftime'):
            data_inicio = data_inicio.strftime('%d/%m/%Y')
        if hasattr(data_fim, 'strftime'):
            data_fim = data_fim.strftime('%d/%m/%Y')
        
        c.drawString(coluna_direita, y_direita, f"Data Início: {data_inicio}")
        y_direita -= 15
        c.drawString(coluna_direita, y_direita, f"Data Fim: {data_fim}")
        y_direita -= 15
        c.drawString(coluna_direita, y_direita, f"Prazo de Entrega: {prazo}")
        
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
        
        # Adicionar a descrição real da proposta dentro da área clara
        # Limitar o tamanho do texto para caber na área
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 9)
        
        # Obter a descrição da proposta, limitada a 100 caracteres
        descricao = proposta.get('descricao', '')
        if len(descricao) > 100:
            descricao = descricao[:97] + '...'
            
        c.drawString(50, y-20, descricao)
        
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
        valor_total = proposta.get('valor', 0)
        
        # Tentar usar os acréscimos reais da proposta
        itens_reais = []
        
        # Sempre adicionar o serviço principal como primeiro item
        itens_reais.append({
            "descricao": f"Personal Organizer - {proposta.get('tipo_proposta', 'Organização')}",
            "valor": valor_total
        })
        
        # Variáveis para rastrear produtos
        produtos_valor_total = 0
        produtos_encontrados = False
        
        # Adicionar os acréscimos se existirem, mas excluir assistentes
        if acrescimos is not None and not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                nome = acrescimo.get('descricao', '')
                tipo = acrescimo.get('tipo', '')
                fornecedor = acrescimo.get('fornecedor', '')
                valor = acrescimo.get('valor', 0)
                
                # Se for tipo produto, adicionar ao total de produtos
                if tipo == 'produto':
                    produtos_valor_total += valor
                    produtos_encontrados = True
                    continue
                
                # Pular qualquer acréscimo de assistente, especialmente "andreia"
                if tipo == 'assistente' or (fornecedor and fornecedor.lower() == 'andreia'):
                    continue
                
                if tipo and fornecedor:
                    descricao_item = f"{fornecedor} - Acréscimo de {tipo.upper()}"
                elif tipo:
                    descricao_item = f"Acréscimo de {tipo.upper()}"
                elif fornecedor:
                    descricao_item = f"Fornecimento de {fornecedor}"
                else:
                    descricao_item = nome if nome else "Item adicional"
                
                itens_reais.append({
                    "descricao": descricao_item,
                    "valor": valor
                })
                
                # Adicionar este valor ao total
                valor_total += valor
        
        # Adicionar a linha de produtos - se encontrou produtos reais usa o valor, senão usa R$ 120,00
        if produtos_encontrados:
            # Usar o valor total calculado dos produtos
            itens_reais.append({
                "descricao": "Produtos",
                "valor": produtos_valor_total
            })
            # Adicionar o valor real dos produtos ao total
            valor_total += produtos_valor_total
            print(f"DEBUG PDF: Adicionando produtos reais com valor total de R$ {produtos_valor_total:.2f}")
        else:
            # Adicionar um produto fixo de R$ 120,00 caso não tenha encontrado produtos reais
            valor_produtos_fixo = 120.00
            itens_reais.append({
                "descricao": "Produtos",
                "valor": valor_produtos_fixo
            })
            # Adicionar o valor fixo ao total
            valor_total += valor_produtos_fixo
            print(f"DEBUG PDF: Adicionando produtos com valor fixo de R$ {valor_produtos_fixo:.2f}")
        
        # Se não houver itens reais suficientes, usar os exemplos
        if len(itens_reais) < 2:
            # Adicionar pelo menos um item de exemplo adicional
            itens_reais.append({
                "descricao": "Item adicional (exemplo)",
                "valor": 0
            })
        
        # Adicionar itens à tabela
        for item in itens_reais:
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
        
        # Linha de total com fundo azul escuro
        c.setFillColor(azul_tabela)
        c.rect(43, y-15, table_width, 15, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y-12, "Total:")
        c.drawRightString(43 + desc_col_width + valor_col_width - 10, y-12, f"R$ {valor_total:.2f}")
        
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
        
        # Data de geração no rodapé com a data e hora atual
        c.setFont("Helvetica", 7)
        data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
        c.drawCentredString(width/2, 5, f"Relatório gerado em {data_geracao}")
        
        # Salvar PDF
        c.save()
        
        print(f"DEBUG PDF NOVO: Relatório de serviço gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar relatório de serviço: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar relatório de serviço: {str(e)}")