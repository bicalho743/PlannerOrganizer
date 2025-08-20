"""
Módulo para gerar relatórios internos com design profissional.
Usa a biblioteca ReportLab com Canvas para ter mais controle sobre o design.
"""
# Imports do sistema
import os
import sys
import traceback
from datetime import datetime, timedelta

# Imports de bibliotecas externas
import pandas as pd
import textwrap

# Imports do ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm

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
        
        # Título principal no cabeçalho
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(30, height - 30, "Relatório Interno")
        
        # Subtítulo com número da proposta e nome do cliente
        c.setFont("Helvetica", 11)
        c.drawString(30, height - 50, f"#{proposta.get('id', 'N/A')} - {cliente.get('nome', 'Cliente')}")
        
        # Data atual à direita no cabeçalho
        c.setFont("Helvetica", 10)
        agora = datetime.now() - timedelta(hours=3)  # Ajustando para UTC-3 (Brasília)
        c.drawRightString(width - 30, height - 30, f"Data: {agora.strftime('%d/%m/%Y')}")
        
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
                
        # Valor total provisório para cálculo de comissão (sem incluir outros que podem conter comissões)
        valor_total_provisorio = valor_base + valor_produtos_total
        
        # Flag para controlar se a comissão foi encontrada nos acréscimos
        comissao_encontrada = False
        
        # Processar acréscimos para identificar custos específicos
        if not acrescimos.empty and hasattr(acrescimos, 'iterrows'):
            for _, acrescimo in acrescimos.iterrows():
                tipo = acrescimo.get('tipo', '').lower() if hasattr(acrescimo, 'get') else ''
                valor = float(acrescimo.get('valor', 0)) if hasattr(acrescimo, 'get') else 0
                # Tratamento seguro para fornecedor que pode ser None
                fornecedor_raw = acrescimo.get('fornecedor', '') if hasattr(acrescimo, 'get') else ''
                fornecedor_nome = fornecedor_raw.lower() if fornecedor_raw else ''
                
                # Buscar o percentual de comissão diretamente da tabela de fornecedores
                percentual_comissao = 0
                if fornecedor_nome and tipo in ['fornecedor', 'produto', 'marcenaria']:
                    # Verificação direta para Multicoisas (que já sabemos que tem 5% de comissão)
                    if fornecedor_nome and 'multi' in fornecedor_nome:
                        percentual_comissao = 5.0
                        print(f"DEBUG PDF: Definindo comissão direta para {fornecedor_nome}: 5%")
                    else:
                        try:
                            # Consultar diretamente o banco de dados via SQL
                            import psycopg2
                            
                            # Obter conexão do ambiente
                            db_url = os.environ.get("DATABASE_URL")
                            conn = psycopg2.connect(db_url)
                            cursor = conn.cursor()
                            
                            # Buscar o ID do usuário atual
                            import streamlit as st
                            usuario_id = None
                            if 'usuario' in st.session_state and st.session_state.usuario and 'id' in st.session_state.usuario:
                                usuario_id = st.session_state.usuario['id']
                            elif 'user' in st.session_state and st.session_state.user and 'uid' in st.session_state.user:
                                # Obter o ID do usuário Firebase
                                firebase_uid = st.session_state.user['uid']
                                # Buscar o ID interno correspondente
                                cursor.execute("SELECT id FROM usuarios WHERE firebase_uid = %s", (firebase_uid,))
                                user_result = cursor.fetchone()
                                if user_result:
                                    usuario_id = user_result[0]
                            
                            if usuario_id:
                                # Buscar percentual de comissão do fornecedor
                                cursor.execute(
                                    "SELECT percentual_comissao FROM fornecedores WHERE LOWER(nome) = %s AND (usuario_id = %s OR usuario_id IS NULL)",
                                    (fornecedor_nome, usuario_id)
                                )
                                forn_result = cursor.fetchone()
                                if forn_result and forn_result[0] is not None:
                                    percentual_comissao = float(forn_result[0])
                                    print(f"DEBUG PDF: Encontrado percentual de comissão para fornecedor {fornecedor_nome}: {percentual_comissao}%")
                            
                            # Fechar a conexão
                            cursor.close()
                            conn.close()
                        except Exception as e:
                            print(f"DEBUG PDF ERROR: Erro ao buscar percentual de comissão: {str(e)}")
                
                # Log para depuração dos acréscimos
                print(f"DEBUG PDF: Processando acréscimo: tipo={tipo}, valor={valor}, fornecedor={fornecedor_nome}, percentual_comissao={percentual_comissao}")
                
                if tipo == 'assistente':
                    custos_assistentes += valor
                elif tipo in ['fornecedor', 'produto', 'marcenaria']:
                    custos_fornecedores += valor
                    # Verificar se esse fornecedor tem comissão
                    if percentual_comissao > 0:
                        comissao_valor = valor * (percentual_comissao / 100)
                        total_comissoes += comissao_valor
                        comissao_encontrada = True
                        print(f"DEBUG PDF: Comissão calculada para fornecedor ({fornecedor_nome}): {percentual_comissao}% = R$ {comissao_valor:.2f}")
                elif tipo == 'comissão':
                    # Usar o valor da comissão se existir na tabela de acréscimos
                    total_comissoes += valor
                    comissao_encontrada = True
                    print(f"DEBUG PDF: Comissão encontrada diretamente nos acréscimos: R$ {valor:.2f}")
                else:
                    total_outros += valor
        
        # Calcular totais
        custo_cliente_total = valor_base + valor_produtos_total + custos_fornecedores + total_outros
        
        # Verificar se existe comissão definida na tabela de acréscimos
        if not comissao_encontrada:
            # Não calcular automaticamente a comissão se não estiver definida
            print(f"DEBUG PDF: Nenhuma comissão encontrada nos acréscimos. Mantendo em zero.")
        else:
            print(f"DEBUG PDF: Total de comissões encontradas: R$ {total_comissoes:.2f}")
        
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
            ["Personal Organizer", f"R$ {valor_base:.2f}"],
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
        
        # Usar o valor real das comissões calculadas (não fixar em R$ 100)
        valor_comissao_real = total_comissoes
        
        # Calcular o ganho líquido com o valor real de comissão
        meu_ganho_real = valor_base + valor_comissao_real + lucro_produtos_total - custos_assistentes
        
        rows = [
            ["Personal Organizer", f"R$ {valor_base:.2f}"],
            ["Comissões", f"R$ {valor_comissao_real:.2f}"],
            ["Lucro em Produtos", f"R$ {lucro_produtos_total:.2f}"],
            ["Pagamento Assistentes", f"R$ -{custos_assistentes:.2f}"],
            ["RECEITA LÍQUIDA TOTAL", f"R$ {meu_ganho_real:.2f}"]
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
        
        # Pulando para a próxima seção diretamente (removido COMPARATIVO E ANÁLISE DE MARGEM)
        
        # Ajuste de posição - sem as seções removidas
        y = y - 40
        
        # Rodapé personalizado
        c.setFillColor(azul_escuro)
        c.rect(0, 0, width, 40, fill=True, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        
        # Aplicar rodapé padronizado
        from utils.pdf_footer_helper import aplicar_rodape_padronizado
        aplicar_rodape_padronizado(c, width, height=40, ajuste_brasilia=True)
        
        # Salvar PDF
        c.save()
        print(f"DEBUG PDF: PDF interno gerado com sucesso: {filename}")
        return filename
    
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF interno: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF interno: {str(e)}")