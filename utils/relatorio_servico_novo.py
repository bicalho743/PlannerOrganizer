#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de geração de relatório de serviço para proposta finalizada
Esta versão segue exatamente o layout solicitado pelo cliente
"""

from datetime import datetime, timedelta
import textwrap
import re
import os
import traceback

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
        
        # Configurações de cores exatamente iguais ao relatório interno
        cinza_claro = colors.HexColor("#f5f7fa")       # fundo
        cinza_medio = colors.HexColor("#5A6A85")       # textos normais
        azul_escuro = colors.HexColor("#1E366F")       # cabeçalho e títulos
        azul_claro = colors.HexColor("#e9f2ff")        # blocos de destaque
        azul_destaque = colors.HexColor("#d4e5fd")     # blocos de conteúdo
        
        # Cor do cabeçalho da tabela (igual ao relatório interno)
        azul_tabela = azul_escuro                      # Cor do cabeçalho da tabela
        cinza_texto = cinza_medio                      # Usando o mesmo cinza do relatório interno
        
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
        
        # ===== CABEÇALHO COM FAIXA AZUL ESCURA (mesma altura do relatório interno) =====
        c.setFillColor(azul_escuro)
        c.rect(0, height-70, width, 70, fill=True, stroke=0)
        
        # Título principal no cabeçalho (mesmo estilo e posição do relatório interno)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(30, height-30, "Relatório de Serviço")
        
        # Data no canto direito (data atual) (mesma posição do relatório interno)
        c.setFont("Helvetica", 10)
        data_atual = datetime.now().strftime('%d/%m/%Y')
        c.drawRightString(width-30, height-30, f"Data: {data_atual}")
        
        # Subtítulo com ID da proposta e nome do cliente (mesma posição do relatório interno)
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.white)
        c.drawString(30, height-50, f"#{proposta.get('id', 'N/A')} - {cliente.get('nome', 'Cliente')}")
        
        # ===== INFORMAÇÕES DO CLIENTE =====
        y = height - 90  # Começando abaixo do cabeçalho (mesma posição que relatório interno)
        
        # Título da seção com linha decorativa abaixo
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "Informações do Cliente")  # Mesma margem do relatório interno (30px)
        c.setStrokeColor(azul_escuro)
        c.line(30, y-5, 250, y-5)  # Ajustando a linha para iniciar na mesma posição
        
        # Dados do cliente
        y -= 25
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 10)
        c.drawString(30, y, f"Nome: {cliente.get('nome', 'N/A')}")  # Ajustando para mesma margem
        y -= 15
        c.drawString(30, y, f"Email: {cliente.get('email', 'N/A')}")
        y -= 15
        c.drawString(30, y, f"Telefone: {cliente.get('telefone', 'N/A')}")
        
        # ===== INFORMAÇÕES DA PROPOSTA =====
        y -= 30
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "Informações da Proposta")  # Mesma margem do relatório interno
        c.setStrokeColor(azul_escuro)
        c.line(30, y-5, 250, y-5)  # Ajustando a linha para iniciar na mesma posição
        
        # Dados da proposta - separados em duas colunas
        y -= 25
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 10)
        
        # Coluna da esquerda
        c.drawString(30, y, f"Tipo: {proposta.get('tipo_proposta', 'Organização')}")  # Mesma margem
        y -= 15
        c.drawString(30, y, f"Status: {proposta.get('status', 'Concluída')}")  # Mesma margem
        
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
        c.drawString(30, y, "DESCRIÇÃO DO SERVIÇO")  # Ajustado para mesma margem do relatório interno
        
        # Área com fundo claro para a descrição
        y -= 10
        c.setFillColor(azul_claro)
        c.rect(30, y-30, width-60, 30, fill=True, stroke=False)  # Ajustado para mesma margem/largura
        
        # Adicionar a descrição real da proposta dentro da área clara
        # Limitar o tamanho do texto para caber na área
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 9)
        
        # Obter a descrição da proposta, limitada a 100 caracteres
        descricao = proposta.get('descricao', '')
        if len(descricao) > 100:
            descricao = descricao[:97] + '...'
            
        c.drawString(40, y-20, descricao)  # Ajustado para mesma margem
        
        # ===== ITENS INCLUSOS (TABELA) =====
        y -= 40
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica", 12)  # Removido negrito conforme solicitado
        c.drawString(30, y, "ITENS INCLUSOS")  # Ajustado para mesma margem
        
        # Configuração da tabela
        y -= 25
        table_width = width - 60  # Mesma largura que o relatório interno
        desc_col_width = table_width * 0.75
        valor_col_width = table_width * 0.25
        
        # Cabeçalho da tabela
        c.setFillColor(azul_tabela)
        c.rect(30, y-15, desc_col_width, 15, fill=True, stroke=False)  # Mesma margem
        c.rect(30+desc_col_width, y-15, valor_col_width, 15, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(30 + desc_col_width/2, y-12, "Descrição")
        c.drawCentredString(30 + desc_col_width + valor_col_width/2, y-12, "Valor")
        
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
        produtos_da_tabela = []  # Lista para armazenar produtos da tabela produtos_organizadores
        
        # NOVO: Obter produtos diretamente da tabela produtos_organizadores
        try:
            import psycopg2
            import os
            
            # Obter conexão do ambiente
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                
                # Buscar produtos associados à proposta diretamente
                proposta_id = proposta.get('id')
                if proposta_id:
                    cursor.execute("""
                        SELECT nome, descricao, quantidade, valor, comodo
                        FROM produtos_organizadores
                        WHERE proposta_id = %s
                    """, (proposta_id,))
                    
                    produtos_tabela = cursor.fetchall()
                    for produto in produtos_tabela:
                        nome_produto, descricao_produto, quantidade, valor, comodo = produto
                        valor_total_produto = float(valor) * int(quantidade)
                        
                        # Adicionar à lista de produtos com detalhes
                        produtos_da_tabela.append({
                            "nome": nome_produto,
                            "descricao": descricao_produto,
                            "quantidade": quantidade,
                            "valor": valor_total_produto,
                            "comodo": comodo
                        })
                        
                        # Adicionar ao total de produtos
                        produtos_valor_total += valor_total_produto
                        produtos_encontrados = True
                        print(f"DEBUG PDF: Encontrou produto na tabela: {nome_produto} - {quantidade} x R$ {valor:.2f} = R$ {valor_total_produto:.2f}")
                
                # Fechar cursor e conexão
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao buscar produtos da proposta: {str(e)}")
        
        # Adicionar os acréscimos se existirem, mas excluir assistentes
        if acrescimos is not None and not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                nome = acrescimo.get('descricao', '')
                tipo = acrescimo.get('tipo', '')
                fornecedor = acrescimo.get('fornecedor', '')
                valor = acrescimo.get('valor', 0)
                
                # Se for tipo produto (maiúsculo ou minúsculo), adicionar ao total de produtos
                if tipo and tipo.lower() == 'produto':
                    produtos_valor_total += valor
                    produtos_encontrados = True
                    print(f"DEBUG PDF: Encontrou produto nos acréscimos: {fornecedor} - R$ {valor:.2f}")
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
        
        # NOVO: Adicionar produtos individuais da tabela produtos_organizadores
        for produto in produtos_da_tabela:
            # Formatar a descrição do produto incluindo a quantidade e cômodo se disponível
            descricao_produto = f"{produto['nome']} ({produto['quantidade']}x)"
            if produto['comodo'] and produto['comodo'].lower() != 'geral':
                descricao_produto += f" - {produto['comodo']}"
            
            # Adicionar à lista de itens
            itens_reais.append({
                "descricao": descricao_produto,
                "valor": produto['valor']
            })
            
            # Não adicionar ao valor_total aqui, pois já adicionaremos o valor total de produtos abaixo
        
        # Adicionar a linha de produtos apenas se encontrou produtos reais mas não os detalhamos individualmente
        # (mantemos apenas para compatibilidade com versões antigas)
        if produtos_encontrados and len(produtos_da_tabela) == 0:
            # Usar o valor total calculado dos produtos
            itens_reais.append({
                "descricao": "Produtos",
                "valor": produtos_valor_total
            })
            # Adicionar o valor real dos produtos ao total
            valor_total += produtos_valor_total
            print(f"DEBUG PDF: Adicionando produtos consolidados com valor total de R$ {produtos_valor_total:.2f}")
        elif produtos_encontrados:
            # Se detalhamos os produtos individualmente, adicionar o valor total ao total geral
            valor_total += produtos_valor_total
            print(f"DEBUG PDF: Valor total de produtos incluídos: R$ {produtos_valor_total:.2f}")
        
        # Se não houver itens reais suficientes, usar os exemplos
        if len(itens_reais) < 2:
            # Adicionar pelo menos um item de exemplo adicional
            itens_reais.append({
                "descricao": "Item adicional (exemplo)",
                "valor": 0
            })
        
        # Adicionar itens à tabela
        for item in itens_reais:
            # Alternância de cores para linhas (mesmo estilo do relatório interno)
            if linha % 2 == 0:
                # Sem cor de fundo para linhas pares
                c.setFillColor(cinza_texto)
            else:
                # Cor de fundo azul claro para linhas ímpares (mesmo azul claro do relatório interno)
                c.setFillColor(azul_claro)
                c.rect(30, y-15, table_width, 15, fill=True, stroke=False)  # Mesma margem
                c.setFillColor(cinza_texto)
            
            c.drawString(40, y-12, item["descricao"])  # Ajustado para mesma margem
            c.drawRightString(30 + desc_col_width + valor_col_width - 10, y-12, f"R$ {item['valor']:.2f}")  # Ajustado
            
            y -= 15
            linha += 1
        
        # Linha de total com fundo azul escuro
        c.setFillColor(azul_tabela)
        c.rect(30, y-15, table_width, 15, fill=True, stroke=False)  # Mesma margem
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y-12, "Total:")  # Ajustado para mesma margem
        c.drawRightString(30 + desc_col_width + valor_col_width - 10, y-12, f"R$ {valor_total:.2f}")  # Ajustado
        
        # ===== OBSERVAÇÕES =====
        y -= 40
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica", 12)  # Removido negrito conforme solicitado
        c.drawString(30, y, "Observações:")  # Mesma margem
        
        y -= 25
        c.setFillColor(cinza_texto)
        c.setFont("Helvetica", 10)
        
        observacoes = [
            "1. Este documento representa o relatório para cliente dos serviços prestados.",
            "2. Para quaisquer dúvidas sobre os serviços, entre em contato conosco.",
            "3. Agradecemos a confiança em nossos serviços."
        ]
        
        for obs in observacoes:
            c.drawString(30, y, obs)  # Mesma margem
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
        raise Exception(f"Erro ao gerar relatório de serviço: {str(e)}")