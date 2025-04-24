"""
Módulo para gerar relatórios internos com design profissional.
Usa a biblioteca ReportLab com Canvas para ter mais controle sobre o design.
"""
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
import textwrap

def gerar_pdf_interno_melhorado(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão interna da proposta, com design profissional,
    incluindo todos os detalhes financeiros, custos e margens
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão completa)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF interno para proposta #{proposta.get('id', 'N/A')} com design profissional")
    print(f"DEBUG PDF: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF: Filename: {filename}")
    print(f"DEBUG PDF: Acréscimos: {len(acrescimos) if hasattr(acrescimos, 'empty') and not acrescimos.empty else 0} registros")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Usar Canvas para mais controle sobre o layout
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Definir cores personalizadas para design profissional
        cinza_claro = colors.HexColor("#f5f7fa")       # fundo
        cinza_medio = colors.HexColor("#5A6A85")       # textos normais
        azul_escuro = colors.HexColor("#1E366F")       # cabeçalho e títulos
        azul_claro = colors.HexColor("#e9f2ff")        # blocos de destaque
        azul_destaque = colors.HexColor("#d4e5fd")     # blocos de conteúdo
        verde_claro = colors.HexColor("#cfe8cf")       # valores positivos
        laranja_claro = colors.HexColor("#ffebcc")     # alertas
        vermelho_claro = colors.HexColor("#ffcccc")    # valores negativos
        
        # Cabeçalho com fundo azul escuro
        c.setFillColor(azul_escuro)
        c.rect(0, height - 70, width, 70, fill=True, stroke=0)
        
        # Título do relatório em branco sobre o fundo azul
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 30, f"RELATÓRIO INTERNO - #{proposta.get('id', 'N/A')} - {cliente.get('nome', 'Cliente')}")
        
        # Data atual à direita no cabeçalho
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 30, height - 50, f"{datetime.now().strftime('%d/%m/%Y')}")
        
        # Posição Y inicial para começar o conteúdo
        y = height - 90
        
        # Bloco de informações da proposta com fundo claro
        c.setFillColor(azul_claro)
        c.rect(30, y - 100, width - 60, 90, fill=True, stroke=0)
        
        # Título do bloco
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y - 20, "Informações da Proposta")
        
        # Informações específicas da proposta
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        c.drawString(40, y - 40, f"Tipo: {proposta.get('tipo_proposta', 'N/A')}")
        c.drawString(40, y - 55, f"Status: {proposta.get('status', 'N/A')}")
        
        # Datas
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
        
        c.drawString(40, y - 70, f"Data Início Execução: {data_inicio_str}")
        c.drawString(40, y - 85, f"Data Fim: {data_fim_str}")
        
        # Descrição do serviço
        y -= 120
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Descrição do Serviço:")
        
        # Processar o texto da descrição
        descricao_text = proposta.get('descricao', 'Serviço Base')
        
        # Preparar o texto para exibição
        descricao_text = descricao_text.replace("•", "- ")
        descricao_text = descricao_text.replace("\r\n", "\n").replace("\r", "\n")
        paragrafos = descricao_text.split('\n')
        
        # Quebrar em linhas para exibição adequada
        max_chars_per_line = 85
        y -= 15
        line_height = 14
        
        # Exibir cada linha da descrição
        for paragrafo in paragrafos:
            if paragrafo.strip():
                linhas = textwrap.wrap(paragrafo.strip(), max_chars_per_line)
                for linha in linhas:
                    c.setFont("Helvetica", 10)
                    c.setFillColor(cinza_medio)
                    c.drawString(50, y, linha)
                    y -= line_height
        
        # Título da seção de análise financeira
        y -= 20
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, y, "ANÁLISE FINANCEIRA COMPLETA")
        y -= 30
        
        # Seção CUSTO TOTAL DO CLIENTE
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, "CUSTO TOTAL DO CLIENTE")
        
        # Descrição da seção
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 9)
        c.drawString(40, y, "Esta seção mostra todos os valores que o cliente está pagando na proposta.")
        
        # Tabela de custos do cliente
        y -= 30
        
        # Coletar valores das diversas fontes
        valor_base = float(proposta.get('valor', 0))
        
        # Calcular valor de produtos
        valor_produtos_total = 0.0
        try:
            # Implementar lógica para calcular valor total de produtos
            # (esta é uma versão simplificada)
            from utils.database import Database, ProdutoOrganizador
            db = Database()
            produtos = db.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta['id']).all()
            
            for produto in produtos:
                quantidade = produto.quantidade if hasattr(produto, 'quantidade') and produto.quantidade is not None else 1
                valor_unitario = float(produto.valor) if produto.valor is not None else 0
                valor_total = valor_unitario * quantidade
                valor_produtos_total += valor_total
                
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao buscar produtos: {str(e)}")
        
        # Calcular custos com fornecedores e outros
        custos_fornecedores = 0.0
        custos_assistentes = 0.0
        total_outros = 0.0
        total_comissoes = 0.0
        lucro_produtos_total = 0.0  # Estimado em 50% do valor total dos produtos
        
        # Se temos produtos, estimamos lucro
        if valor_produtos_total > 0:
            lucro_produtos_total = valor_produtos_total * 0.5  # Estimativa padrão de 50% de lucro
        
        if not acrescimos.empty and hasattr(acrescimos, 'iterrows'):
            for _, acrescimo in acrescimos.iterrows():
                tipo = acrescimo.get('tipo', '').lower() if hasattr(acrescimo, 'get') else ''
                valor = float(acrescimo.get('valor', 0)) if hasattr(acrescimo, 'get') else 0
                
                if tipo == 'assistente':
                    custos_assistentes += valor
                elif tipo in ['fornecedor', 'produto', 'marcenaria']:
                    custos_fornecedores += valor
                elif tipo == 'comissão':
                    total_comissoes += valor
                else:
                    total_outros += valor
        
        # Calcular totais
        custo_cliente_total = valor_base + valor_produtos_total + custos_fornecedores + total_outros
        meu_ganho = valor_base + total_comissoes + lucro_produtos_total - custos_assistentes
        
        # Calcular margem percentual
        margem_percentual = (meu_ganho / custo_cliente_total * 100) if custo_cliente_total > 0 else 0
        
        # Desenhar tabela de custos do cliente
        c.setFillColor(azul_claro)
        c.rect(width/2 - 150, y - 140, 300, 130, fill=True, stroke=0)
        
        # Borda da tabela
        c.setStrokeColor(azul_escuro)
        c.setLineWidth(0.5)
        c.rect(width/2 - 150, y - 140, 300, 130, fill=False, stroke=1)
        
        # Cabeçalhos
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width/2 - 100, y - 20, "Item")
        c.drawCentredString(width/2 + 100, y - 20, "Valor")
        
        # Linha separadora dos cabeçalhos
        c.line(width/2 - 150, y - 25, width/2 + 150, y - 25)
        
        # Dados da tabela
        row_height = 20
        rows = [
            ["Valor Base", f"R$ {valor_base:.2f}"],
            ["Produtos", f"R$ {valor_produtos_total:.2f}"],
            ["Fornecedores", f"R$ {custos_fornecedores:.2f}"],
            ["Outros", f"R$ {total_outros:.2f}"],
            ["CUSTO TOTAL DO CLIENTE", f"R$ {custo_cliente_total:.2f}"]
        ]
        
        for i, row in enumerate(rows):
            text_y = y - 40 - (i * row_height)
            
            # Destacar a última linha (total)
            if i == len(rows) - 1:
                c.setFillColor(azul_escuro)
                c.setFont("Helvetica-Bold", 10)
                c.rect(width/2 - 150, text_y - 5, 300, row_height, fill=False, stroke=1)
            else:
                c.setFillColor(cinza_medio)
                c.setFont("Helvetica", 10)
            
            c.drawString(width/2 - 140, text_y, row[0])
            c.drawRightString(width/2 + 140, text_y, row[1])
        
        # Seção RECEITA LÍQUIDA PROJETO
        y = y - 160
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, "RECEITA LÍQUIDA PROJETO")
        
        # Descrição da seção
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 9)
        c.drawString(40, y, "Esta seção mostra o ganho real da Personal, considerando o valor base, comissões, lucro na venda de produtos")
        y -= 12
        c.drawString(40, y, "menos o pagamento a assistentes.")
        
        # Tabela de receita líquida
        y -= 30
        
        # Desenhar tabela de receita líquida
        c.setFillColor(azul_claro)
        c.rect(width/2 - 150, y - 140, 300, 130, fill=True, stroke=0)
        
        # Borda da tabela
        c.setStrokeColor(azul_escuro)
        c.setLineWidth(0.5)
        c.rect(width/2 - 150, y - 140, 300, 130, fill=False, stroke=1)
        
        # Cabeçalhos
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width/2 - 100, y - 20, "Item")
        c.drawCentredString(width/2 + 100, y - 20, "Valor")
        
        # Linha separadora dos cabeçalhos
        c.line(width/2 - 150, y - 25, width/2 + 150, y - 25)
        
        # Dados da tabela
        row_height = 20
        rows = [
            ["Valor Base", f"R$ {valor_base:.2f}"],
            ["Comissões", f"R$ {total_comissoes:.2f}"],
            ["Lucro em Produtos", f"R$ {lucro_produtos_total:.2f}"],
            ["Pagamento Assistentes", f"R$ -{custos_assistentes:.2f}"],
            ["RECEITA LÍQUIDA TOTAL", f"R$ {meu_ganho:.2f}"]
        ]
        
        for i, row in enumerate(rows):
            text_y = y - 40 - (i * row_height)
            
            # Destacar a última linha (total)
            if i == len(rows) - 1:
                c.setFillColor(azul_escuro)
                c.setFont("Helvetica-Bold", 10)
                c.rect(width/2 - 150, text_y - 5, 300, row_height, fill=False, stroke=1)
            else:
                c.setFillColor(cinza_medio)
                c.setFont("Helvetica", 10)
            
            c.drawString(width/2 - 140, text_y, row[0])
            c.drawRightString(width/2 + 140, text_y, row[1])
        
        # Seção COMPARATIVO E ANÁLISE DE MARGEM
        y = y - 160
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, "COMPARATIVO E ANÁLISE DE MARGEM")
        
        # Descrição da seção
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 9)
        c.drawString(40, y, "Comparação direta entre o custo total do cliente e a receita líquida da Personal, mostrando a margem de lucro")
        y -= 12
        c.drawString(40, y, "percentual.")
        
        # Tabela de comparativo
        y -= 30
        
        # Desenhar tabela de comparativo
        c.setFillColor(azul_claro)
        c.rect(width/2 - 150, y - 100, 300, 90, fill=True, stroke=0)
        
        # Borda da tabela
        c.setStrokeColor(azul_escuro)
        c.setLineWidth(0.5)
        c.rect(width/2 - 150, y - 100, 300, 90, fill=False, stroke=1)
        
        # Cabeçalhos
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width/2 - 100, y - 20, "Item")
        c.drawCentredString(width/2 + 30, y - 20, "Valor")
        c.drawCentredString(width/2 + 100, y - 20, "Avaliação")
        
        # Linha separadora dos cabeçalhos
        c.line(width/2 - 150, y - 25, width/2 + 150, y - 25)
        
        # Determinando a avaliação da margem
        avaliacao = "IDEAL" if margem_percentual >= 30 else ("BOA" if margem_percentual >= 20 else "ABAIXO DO IDEAL")
        cor_avaliacao = verde_claro if margem_percentual >= 30 else (laranja_claro if margem_percentual >= 20 else vermelho_claro)
        
        # Dados da tabela
        row_height = 20
        rows = [
            ["Custo Total do Cliente", f"R$ {custo_cliente_total:.2f}", ""],
            ["Receita Líquida Total", f"R$ {meu_ganho:.2f}", ""],
            ["MARGEM PERCENTUAL", f"{margem_percentual:.2f}%", avaliacao]
        ]
        
        for i, row in enumerate(rows):
            text_y = y - 40 - (i * row_height)
            
            # Destacar a última linha (margem percentual)
            if i == len(rows) - 1:
                c.setFillColor(azul_escuro)
                c.setFont("Helvetica-Bold", 10)
                c.rect(width/2 - 150, text_y - 5, 300, row_height, fill=False, stroke=1)
                
                # Adicionar cor de fundo para avaliação
                c.setFillColor(cor_avaliacao)
                c.rect(width/2 + 50, text_y - 5, 100, row_height, fill=True, stroke=0)
            else:
                c.setFillColor(cinza_medio)
                c.setFont("Helvetica", 10)
            
            c.setFillColor(cinza_medio) if i < len(rows) - 1 else c.setFillColor(azul_escuro)
            c.drawString(width/2 - 140, text_y, row[0])
            c.drawString(width/2 + 10, text_y, row[1])
            
            if i == len(rows) - 1:
                c.setFillColor(azul_escuro)
                c.drawCentredString(width/2 + 100, text_y, row[2])
        
        # Texto de análise da margem
        y = y - 120
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 10)
        
        if margem_percentual >= 30:
            c.drawString(40, y, f"EXCELENTE: A margem atual de {margem_percentual:.2f}% está acima do ideal de 30%. Esta proposta tem uma boa")
            y -= 15
            c.drawString(40, y, "lucratividade para a organização.")
        elif margem_percentual >= 20:
            c.drawString(40, y, f"BOA: A margem atual de {margem_percentual:.2f}% está dentro do aceitável. Considere aumentar os valores")
            y -= 15
            c.drawString(40, y, "em propostas futuras para atingir a margem ideal de 30%.")
        else:
            c.drawString(40, y, f"ATENÇÃO: A margem atual de {margem_percentual:.2f}% está abaixo do ideal. Revisar custos e valores")
            y -= 15
            c.drawString(40, y, "para futuras propostas semelhantes.")
        
        # Seção Análise e Recomendações
        y -= 30
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Análise e Recomendações")
        
        # Texto de análise
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        if margem_percentual >= 30:
            c.drawString(40, y, f"POSITIVO: Margem dentro do esperado ({margem_percentual:.2f}%)")
        elif margem_percentual >= 20:
            c.drawString(40, y, f"ATENÇÃO: Margem abaixo do ideal ({margem_percentual:.2f}%), considerar ajustes em propostas futuras")
        else:
            c.drawString(40, y, f"NEGATIVO: Margem baixa ({margem_percentual:.2f}%), revisar estrutura de custos e valores")
        
        # Seção Observações Finais
        y -= 40
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Observações Finais")
        
        # Observações
        y -= 20
        c.setFillColor(cinza_medio)
        c.setFont("Helvetica", 10)
        
        observacoes = [
            "1. A margem ideal deve ser de no mínimo 30% do valor total.",
            "2. Custos com assistentes são despesas da empresa.",
            "3. Custos com fornecedores são normalmente repassados ao cliente."
        ]
        
        for obs in observacoes:
            c.drawString(40, y, obs)
            y -= 15
        
        # Rodapé com data e hora de geração
        c.setFillColor(azul_escuro)
        c.rect(0, 0, width, 30, fill=True, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 9)
        c.drawCentredString(width/2, 10, f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        
        # Salvar PDF
        c.save()
        print(f"DEBUG PDF: PDF interno gerado com sucesso: {filename}")
        return filename
    
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF interno: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF interno: {str(e)}")