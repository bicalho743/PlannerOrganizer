from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
import traceback

def gerar_pdf_cliente(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão para cliente da proposta, com detalhes necessários 
    para o cliente, sem informações financeiras internas
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão pública)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF para cliente - proposta #{proposta.get('numero', 'N/A')}")
    print(f"DEBUG PDF: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF: Filename: {filename}")
    print(f"DEBUG PDF: Acréscimos: {len(acrescimos) if not acrescimos.empty else 0} registros")
    
    # Importação específica para buscar produtos da proposta
    from utils.database import Database, ProdutoOrganizador
    db = Database()
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Inicializar documento
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        story.append(Paragraph(f"Relatório de Serviço", title_style))
        story.append(Paragraph(f"Proposta #{proposta['id']} - {cliente['nome']}", styles["Heading2"]))
        story.append(Paragraph(f"{datetime.now().strftime('%d/%m/%Y')}", styles["Heading3"]))
        story.append(Spacer(1, 12))

        # Informações do Cliente
        story.append(Paragraph("<b>Informações do Cliente</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Nome:</b> {cliente['nome']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Email:</b> {cliente.get('email', 'Não informado')}", styles["Normal"]))
        story.append(Paragraph(f"<b>Telefone:</b> {cliente.get('telefone', 'Não informado')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Informações da Proposta
        story.append(Paragraph("<b>Informações da Proposta</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Tipo:</b> {proposta['tipo_proposta']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Status:</b> {proposta['status']}", styles["Normal"]))

        # Datas
        if proposta.get('data_inicio'):
            story.append(Paragraph(f"<b>Data Início:</b> {proposta['data_inicio'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_fim'):
            story.append(Paragraph(f"<b>Data Fim:</b> {proposta['data_fim'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('prazo_entrega'):
            story.append(Paragraph(f"<b>Prazo de Entrega:</b> {proposta['prazo_entrega'].strftime('%d/%m/%Y')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Descrição da Proposta
        story.append(Paragraph("<b>Descrição do Serviço:</b>", styles["Heading3"]))
        story.append(Paragraph(proposta['descricao'], styles["Normal"]))
        story.append(Spacer(1, 20))

        # Serviços Realizados
        story.append(Paragraph("<b>Serviços Realizados</b>", styles["Heading3"]))
        
        # Tabela de serviços
        data_servicos = [["Descrição", "Valor"]]
        
        # Valor base sempre vai para a tabela
        data_servicos.append([
            "Serviço Base", 
            f"R$ {float(proposta['valor']):.2f}"
        ])
        
        # Processar apenas acréscimos relevantes para o cliente
        total_servicos = float(proposta['valor'])
        
        # Listas para separar produtos e itens do tipo "OUTRO"
        produtos_fisicos = []
        outros_itens = []
        
        try:
            # Buscar produtos da proposta usando a instância do Database
            produtos = db.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta['id']).all()
            print(f"DEBUG PDF: Encontrados {len(produtos)} produtos para a proposta")
            
            # Identificar produtos físicos e itens do tipo OUTRO com base no nome
            for produto in produtos:
                # Obter quantidade e calcular valor total
                quantidade = produto.quantidade if hasattr(produto, 'quantidade') and produto.quantidade is not None else 1
                valor_unitario = float(produto.valor) if produto.valor is not None else 0
                valor_total = valor_unitario * quantidade
                
                item = {
                    'nome': produto.nome,
                    'valor_unitario': valor_unitario,
                    'quantidade': quantidade,
                    'valor_total': valor_total
                }
                
                # Verificar se o nome do produto contém "caixa" ou outros termos que indicam ser do tipo OUTRO
                # Isso é uma solução temporária até adicionarmos o campo 'tipo' na tabela de produtos
                nome_lower = produto.nome.lower() if produto.nome else ""
                termos_outros = ['caixa', 'uber', 'transporte', 'serviço', 'servico', 'frete', 'delivery', 'entrega', 'cabide']
                
                if any(termo in nome_lower for termo in termos_outros):
                    outros_itens.append(item)
                    print(f"DEBUG PDF: Item OUTRO identificado pelo nome: {produto.nome} - R$ {valor_unitario:.2f} x {quantidade} = R$ {valor_total:.2f}")
                else:
                    produtos_fisicos.append(item)
                    print(f"DEBUG PDF: Produto físico identificado: {produto.nome} - R$ {valor_unitario:.2f} x {quantidade} = R$ {valor_total:.2f}")
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao buscar produtos: {str(e)}")
            traceback.print_exc()
        
        # Agrupar produtos por nome para combinar aqueles com mesmo nome
        produtos_agrupados = {}
        for produto in produtos_fisicos:
            nome = produto['nome']
            if nome not in produtos_agrupados:
                produtos_agrupados[nome] = {
                    'nome': nome,
                    'quantidade': produto['quantidade'],
                    'valor_total': produto['valor_total'],
                    'valor_unitario': produto['valor_unitario']
                }
            else:
                # Somar quantidade e valor para produtos com mesmo nome
                produtos_agrupados[nome]['quantidade'] += produto['quantidade']
                produtos_agrupados[nome]['valor_total'] += produto['valor_total']
        
        # Adicionar produtos agrupados à tabela principal de serviços
        for nome, produto in produtos_agrupados.items():
            # Criar string com informações de quantidade e valores
            descricao = f"PRODUTO - {produto['nome']}"
            if produto['quantidade'] > 1:
                descricao += f" ({produto['quantidade']} unid.)"
            
            data_servicos.append([
                descricao,
                f"R$ {produto['valor_total']:.2f}"
            ])
            total_servicos += produto['valor_total']
        
        # Processar acréscimos regulares
        if not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                # Excluir apenas os assistentes da seção principal
                if acrescimo['tipo'].lower() != 'assistente':
                    # Construir descrição para o item
                    if acrescimo['tipo'].lower() == 'outro':
                        descricao = f"OUTRO - {acrescimo.get('descricao', 'Item adicional')}"
                    else:
                        descricao = f"{acrescimo['tipo']}"
                        if acrescimo.get('descricao'):
                            descricao += f" - {acrescimo['descricao']}"
                    
                    # Adicionar nome do fornecedor se disponível
                    if acrescimo.get('fornecedor'):
                        descricao += f" ({acrescimo['fornecedor']})"
                    
                    valor = float(acrescimo['valor'])
                    
                    data_servicos.append([
                        descricao,
                        f"R$ {valor:.2f}"
                    ])
                    total_servicos += valor
                    
                    # Se for tipo OUTRO, também coletar para a seção dedicada
                    if acrescimo['tipo'].lower() == 'outro':
                        item = {
                            'nome': acrescimo.get('descricao', 'Item adicional'),
                            'valor': float(acrescimo['valor']),
                            'fornecedor': acrescimo.get('fornecedor', '')
                        }
                        outros_itens.append(item)
                        print(f"DEBUG PDF: Adicionando OUTRO item aos serviços: {descricao} - R$ {valor:.2f}")
                else:
                    # Apenas registrar que estamos pulando um item de assistente
                    print(f"DEBUG PDF: Pulando item de assistente: {acrescimo.get('descricao', 'Sem descrição')} - {acrescimo.get('fornecedor', 'Sem fornecedor')}")

        # Tabela style para serviços
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ])

        # Criar e adicionar tabela de serviços
        table = Table(data_servicos, colWidths=[4.5*inch, 2*inch])
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Total:</b> R$ {total_servicos:.2f}", 
                             ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("Observações:", styles["Heading4"]))
        story.append(Paragraph("1. Este documento representa o relatório para cliente dos serviços prestados.", styles["Normal"]))
        story.append(Paragraph("2. Para quaisquer dúvidas sobre os serviços, entre em contato conosco.", styles["Normal"]))
        story.append(Paragraph("3. Agradecemos a confiança em nossos serviços.", styles["Normal"]))

        # Informações da Empresa
        story.append(Spacer(1, 30))
        story.append(Paragraph("Planner Organizer", styles["Heading4"]))
        story.append(Paragraph("contato@plannerorganizer.com.br", styles["Normal"]))
        story.append(Paragraph("(11) 98765-4321", styles["Normal"]))
        story.append(Paragraph("www.plannerorganizer.com.br", styles["Normal"]))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF para cliente gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF para cliente: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF para cliente: {str(e)}")
    
def gerar_pdf_interno(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com a versão interna da proposta, incluindo todos os detalhes
    financeiros, custos e margens
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta (versão completa)
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF interno para proposta #{proposta.get('id', 'N/A')}")
    print(f"DEBUG PDF: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF: Filename: {filename}")
    print(f"DEBUG PDF: Acréscimos: {len(acrescimos) if not acrescimos.empty else 0} registros")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Inicializar documento
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        story.append(Paragraph(f"RELATÓRIO INTERNO - #{proposta['id']} - {cliente['nome']}", title_style))
        story.append(Paragraph(f"{datetime.now().strftime('%d/%m/%Y')}", styles["Heading3"]))
        story.append(Spacer(1, 12))

        # Espaço após título
        story.append(Spacer(1, 12))

        # Informações da Proposta
        story.append(Paragraph("<b>Informações da Proposta</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Tipo:</b> {proposta['tipo_proposta']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Status:</b> {proposta['status']}", styles["Normal"]))

        # Apenas as datas solicitadas
        if proposta.get('data_inicio_execucao'):
            story.append(Paragraph(f"<b>Data Início Execução:</b> {proposta['data_inicio_execucao'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_fim'):
            story.append(Paragraph(f"<b>Data Fim:</b> {proposta['data_fim'].strftime('%d/%m/%Y')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Descrição da Proposta
        story.append(Paragraph("<b>Descrição do Serviço:</b>", styles["Heading3"]))
        story.append(Paragraph(proposta['descricao'], styles["Normal"]))
        story.append(Spacer(1, 20))

        # Produtos associados à proposta
        produtos_fisicos = []
        outros_itens = []
        
        try:
            # Buscar produtos da proposta
            from utils.database import Database, ProdutoOrganizador, Produto
            db = Database()
            produtos = db.session.query(ProdutoOrganizador).filter_by(proposta_id=proposta['id']).all()
            print(f"DEBUG PDF: Interno - Encontrados {len(produtos)} produtos para a proposta")
            
            # Buscar todos os produtos do estoque para usar no cálculo de lucro
            produtos_estoque = {}
            try:
                # Criar um dicionário com os produtos do estoque para facilitar a busca por nome
                for prod in db.session.query(Produto).all():
                    produtos_estoque[prod.nome.lower()] = {
                        'id': prod.id,
                        'preco_custo': prod.preco_custo,
                        'preco_venda': prod.preco_venda
                    }
                print(f"DEBUG PDF: Interno - Encontrados {len(produtos_estoque)} produtos no estoque")
            except Exception as e:
                print(f"DEBUG PDF ERROR: Erro ao buscar produtos do estoque: {str(e)}")
                
            # Identificar produtos físicos e itens do tipo OUTRO
            for produto in produtos:
                # Obter quantidade e calcular valor total
                quantidade = produto.quantidade if hasattr(produto, 'quantidade') and produto.quantidade is not None else 1
                valor_unitario = float(produto.valor) if produto.valor is not None else 0
                valor_total = valor_unitario * quantidade
                
                # Buscar informações de custo no estoque
                preco_custo = 0
                lucro_total = 0
                lucro_unitario = 0
                margem_percentual = 0
                
                if produto.nome and produto.nome.lower() in produtos_estoque:
                    preco_custo = produtos_estoque[produto.nome.lower()]['preco_custo']
                    lucro_unitario = valor_unitario - preco_custo
                    lucro_total = lucro_unitario * quantidade
                    # Calcular margem percentual
                    if valor_unitario > 0:
                        margem_percentual = (lucro_unitario / valor_unitario) * 100
                
                item = {
                    'nome': produto.nome,
                    'valor_unitario': valor_unitario,
                    'quantidade': quantidade,
                    'valor_total': valor_total,
                    'preco_custo': preco_custo,
                    'lucro_unitario': lucro_unitario,
                    'lucro_total': lucro_total,
                    'margem_percentual': margem_percentual
                }
                
                # Verificar se o nome do produto contém termos que indicam ser do tipo OUTRO
                nome_lower = produto.nome.lower() if produto.nome else ""
                termos_outros = ['caixa', 'uber', 'transporte', 'serviço', 'servico', 'frete', 'delivery', 'entrega', 'cabide']
                
                if any(termo in nome_lower for termo in termos_outros):
                    # Incluir tanto nos outros_itens quanto nos produtos_fisicos para aparecer em ambas as tabelas
                    outros_itens.append(item)
                    produtos_fisicos.append(item)  # Adicionando aqui para aparecer na tabela de serviços
                    print(f"DEBUG PDF: Interno - Item OUTRO identificado: {produto.nome} - R$ {valor_unitario:.2f} x {quantidade} = R$ {valor_total:.2f}")
                else:
                    produtos_fisicos.append(item)
                    print(f"DEBUG PDF: Interno - Produto físico identificado: {produto.nome} - R$ {valor_unitario:.2f} x {quantidade} = R$ {valor_total:.2f}")
                    if preco_custo > 0:
                        print(f"DEBUG PDF: Interno - Custo: R$ {preco_custo:.2f}, Lucro: R$ {lucro_total:.2f}, Margem: {margem_percentual:.2f}%")
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao buscar produtos para relatório interno: {str(e)}")
            traceback.print_exc()
            
        # Agrupar produtos por nome para combinar aqueles com mesmo nome
        produtos_agrupados = {}
        for produto in produtos_fisicos:
            nome = produto['nome']
            if nome not in produtos_agrupados:
                produtos_agrupados[nome] = {
                    'nome': nome,
                    'quantidade': produto['quantidade'],
                    'valor_total': produto['valor_total'],
                    'valor_unitario': produto['valor_unitario']
                }
            else:
                # Somar quantidade e valor para produtos com mesmo nome
                produtos_agrupados[nome]['quantidade'] += produto['quantidade']
                produtos_agrupados[nome]['valor_total'] += produto['valor_total']
        
        # Cálculos de totais de produtos (sem exibir a tabela) para uso no resumo
        if produtos_agrupados:
            total_produtos = 0.0
            total_custo = 0.0
            total_lucro = 0.0
            
            # Encontrar valores de custo e lucro para os produtos agrupados
            for nome_produto, produto in produtos_agrupados.items():
                # Inicializar valores de custo e lucro para este produto
                preco_custo = 0
                lucro_unitario = 0
                lucro_total = 0
                margem_percentual = 0
                
                # Buscar informações de custo/lucro nos produtos originais
                for prod_original in produtos_fisicos:
                    if prod_original['nome'] == nome_produto:
                        preco_custo = prod_original['preco_custo']
                        lucro_unitario = prod_original['lucro_unitario']
                        lucro_total = lucro_unitario * produto['quantidade']
                        margem_percentual = prod_original['margem_percentual']
                        break
                
                # Atualizar produto com valores de custo e lucro
                produto['preco_custo'] = preco_custo
                produto['lucro_unitario'] = lucro_unitario
                produto['lucro_total'] = lucro_total
                produto['margem_percentual'] = margem_percentual
                
                # Somar aos totais
                total_produtos += produto['valor_total']
                total_custo += (preco_custo * produto['quantidade'])
                total_lucro += lucro_total
            
            # Calcular margem percentual média
            margem_media = (total_lucro / total_produtos * 100) if total_produtos > 0 else 0
            
            # Registrar totais para debug
            print(f"DEBUG PDF: Totais dos produtos: Valor={total_produtos:.2f}, Lucro={total_lucro:.2f}, Margem={margem_media:.1f}%")
            
            story.append(Spacer(1, 12))
        
        # Seção de Outros Itens (cabides, etc.)
        if outros_itens:
            story.append(Paragraph("<b>Outros Itens e Serviços</b>", styles["Heading4"]))
            
            # Agrupar outros itens pelo nome para evitar duplicações
            outros_agrupados = {}
            
            for item in outros_itens:
                nome = item['nome']
                
                if nome in outros_agrupados:
                    # Se o item já existe, somar quantidade e valor
                    outros_agrupados[nome]['quantidade'] += item.get('quantidade', 1)
                    outros_agrupados[nome]['valor_total'] += item['valor_total']
                else:
                    # Se o item não existe, adicioná-lo
                    outros_agrupados[nome] = {
                        'nome': nome,
                        'descricao': item.get('descricao', ''),
                        'valor_unitario': item['valor_unitario'],
                        'quantidade': item.get('quantidade', 1),
                        'valor_total': item['valor_total']
                    }
            
            # Preparar dados para a tabela
            data_outros = [["Item", "Descrição", "Valor Unitário", "Quantidade", "Valor Total"]]
            total_outros_valor = 0.0
            
            for nome, item in outros_agrupados.items():
                data_outros.append([
                    item['nome'],
                    item['descricao'],
                    f"R$ {item['valor_unitario']:.2f}",
                    f"{item['quantidade']}",
                    f"R$ {item['valor_total']:.2f}"
                ])
                total_outros_valor += item['valor_total']
            
            # Adicionar linha de total
            data_outros.append([
                "TOTAL OUTROS ITENS",
                "",
                "", 
                "",
                f"R$ {total_outros_valor:.2f}"
            ])
            
            # Estilo para tabela de outros itens
            outros_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
                # Destacar linha de total
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ])
            
            # Criar e adicionar tabela de outros itens
            table = Table(data_outros, colWidths=[1.5*inch, 2.5*inch, 1*inch, 0.7*inch, 1*inch])
            table.setStyle(outros_style)
            story.append(table)
            
            story.append(Spacer(1, 12))
            print(f"DEBUG PDF: Tabela de Outros Itens adicionada com {len(outros_agrupados)} itens, total R$ {total_outros_valor:.2f}")
        
        # Inicializar variável valor_base para uso posterior
        valor_base = float(proposta['valor'])
        
        # Espaçamento antes das análises
        story.append(Spacer(1, 15))
        
        # Acréscimos - não exibir a tabela detalhada, mas calcular os valores
        total_acrescimos = 0.0
        custos_fornecedores = 0.0
        custos_assistentes = 0.0
        
        if not acrescimos.empty:
            # Processar os acréscimos para cálculos, mas não mostrar a tabela
            for _, acrescimo in acrescimos.iterrows():
                valor = float(acrescimo['valor'])
                total_acrescimos += valor
                
                # Classificar os custos
                if acrescimo['tipo'].lower() == 'assistente':
                    custos_assistentes += valor
                elif acrescimo['tipo'].lower() in ['fornecedor', 'produto', 'marcenaria']:
                    custos_fornecedores += valor
                elif acrescimo['tipo'].lower() == 'outro':
                    # Criar item para adicionar à lista de outros_itens para exibição na seção específica
                    outro_item = {
                        'nome': acrescimo['fornecedor'] if 'fornecedor' in acrescimo else "Item adicional",
                        'valor_unitario': valor,
                        'quantidade': 1,
                        'valor_total': valor,
                        'descricao': acrescimo['descricao'] if 'descricao' in acrescimo else ""
                    }
                    outros_itens.append(outro_item)
                    print(f"DEBUG PDF: Interno - Item OUTRO adicionado: {outro_item['nome']} - R$ {valor:.2f}")
        
        # Cálculos financeiros
        valor_total = valor_base + total_acrescimos
        total_custos = custos_fornecedores + custos_assistentes
        margem_bruta = valor_total - total_custos
        margem_percentual = (margem_bruta / valor_total * 100) if valor_total > 0 else 0
        
        # Resumo financeiro com duas visões
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>ANÁLISE FINANCEIRA COMPLETA</b>", 
                           ParagraphStyle('TitleFinancial', parent=styles['Heading3'], 
                                         fontSize=14, alignment=1, spaceAfter=10, textColor=colors.darkblue)))
        
        # Adicionar explicação sobre as duas visões
        story.append(Paragraph(
            """Este relatório apresenta duas análises financeiras complementares da proposta:
            
            <b>1. CUSTO TOTAL DO CLIENTE:</b> Mostra todos os valores que compõem o custo final para o cliente.
            <b>2. MEU GANHO:</b> Mostra o ganho real para a organização, considerando comissões, lucro de produtos 
            e descontando pagamentos a assistentes.
            """, 
            ParagraphStyle('Explanation', parent=styles['Normal'], 
                         alignment=0, spaceBefore=5, spaceAfter=15, leading=14)
        ))
        
        # Inicializar variáveis para evitar erro caso não sejam definidas anteriormente
        total_produtos = 0.0
        total_lucro = 0.0
        
        # Verificar se os produtos foram processados anteriormente
        if produtos_agrupados:
            # Usar os valores já calculados na seção de produtos
            valor_produtos_total = total_produtos
            lucro_produtos_total = total_lucro
        else:
            # Calcular totais dos produtos a partir dos dados brutos da proposta
            valor_produtos_total = 0.0
            lucro_produtos_total = 0.0
            
            # Verificar se há produtos
            if produtos_fisicos:
                for produto in produtos_fisicos:
                    valor_produtos_total += produto['valor_total']
                    if 'lucro_total' in produto:
                        lucro_produtos_total += produto['lucro_total']
                    elif 'lucro_unitario' in produto and 'quantidade' in produto:
                        lucro_produtos_total += produto['lucro_unitario'] * produto['quantidade']
                print(f"DEBUG PDF: Calculados valores de produtos: Total={valor_produtos_total:.2f}, Lucro={lucro_produtos_total:.2f}")
            
        # Calcular custo dos produtos (preço - lucro)
        custo_produtos = valor_produtos_total - lucro_produtos_total
        
        # Categorizar acréscimos
        total_comissoes = 0.0
        total_outros = 0.0
        
        # Se houver acréscimos, classificá-los
        if not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                tipo_lower = acrescimo['tipo'].lower() if 'tipo' in acrescimo else ''
                valor = float(acrescimo['valor'])
                
                # Adicionar debug para verificar cada tipo de acréscimo
                print(f"DEBUG PDF: Classificando acréscimo: {tipo_lower} - R$ {valor:.2f}")
                
                # Identificar comissões - procurar por tipo comissão, categoria Comissão ou tipo_receita comissão
                # Mostrar detalhes de cada acréscimo
                if 'categoria' in acrescimo:
                    print(f"DEBUG PDF: DETALHES - categoria={acrescimo['categoria']}, tipo={tipo_lower}")
                if 'subcategoria' in acrescimo:
                    print(f"DEBUG PDF: DETALHES - subcategoria={acrescimo['subcategoria']}")
                if 'tipo_receita' in acrescimo:
                    print(f"DEBUG PDF: DETALHES - tipo_receita={acrescimo['tipo_receita']}")
                
                # Verificar se o tipo contém 'comissao' ou 'comissão'
                comissao_tipo = 'comissao' in tipo_lower or 'comissão' in tipo_lower
                
                # Verificar se a subcategoria contém 'comissao' ou 'comissão'
                comissao_subcategoria = False
                if 'subcategoria' in acrescimo and acrescimo['subcategoria']:
                    if isinstance(acrescimo['subcategoria'], str):
                        comissao_subcategoria = 'comiss' in acrescimo['subcategoria'].lower()
                
                # Verificar se a categoria contém 'comissao' ou 'comissão'
                comissao_categoria = False
                if 'categoria' in acrescimo and acrescimo['categoria']:
                    if isinstance(acrescimo['categoria'], str):
                        comissao_categoria = 'comiss' in acrescimo['categoria'].lower()
                
                # Verificar se o tipo_receita contém 'comissao' ou 'comissão'
                comissao_tipo_receita = False
                if 'tipo_receita' in acrescimo and acrescimo['tipo_receita']:
                    if isinstance(acrescimo['tipo_receita'], str):
                        comissao_tipo_receita = 'comiss' in acrescimo['tipo_receita'].lower()
                
                # Verificar se qualquer um dos campos identifica uma comissão
                if comissao_tipo or comissao_subcategoria or comissao_categoria or comissao_tipo_receita:
                    total_comissoes += valor
                    print(f"DEBUG PDF: Adicionado COMISSÃO: R$ {valor:.2f}, Total: R$ {total_comissoes:.2f}")
                    # Mostrar em qual condição a comissão foi identificada
                    if comissao_tipo:
                        print(f"DEBUG PDF: Comissão identificada pelo TIPO={tipo_lower}")
                    elif comissao_subcategoria:
                        print(f"DEBUG PDF: Comissão identificada pela SUBCATEGORIA={acrescimo['subcategoria']}")
                    elif comissao_categoria:
                        print(f"DEBUG PDF: Comissão identificada pela CATEGORIA={acrescimo['categoria']}")
                    elif comissao_tipo_receita:
                        print(f"DEBUG PDF: Comissão identificada pelo TIPO_RECEITA={acrescimo['tipo_receita']}")
                # Identificar assistentes (para garantir contabilização correta)
                elif tipo_lower == 'assistente':
                    # Custos de assistentes já são processados na seção anterior
                    print(f"DEBUG PDF: Verificado ASSISTENTE: R$ {valor:.2f}, Total: R$ {custos_assistentes:.2f}")
                # Identificar outros itens que não são classificados como fornecedores ou assistentes
                elif tipo_lower not in ['assistente', 'fornecedor', 'produto', 'marcenaria']:
                    total_outros += valor
                    print(f"DEBUG PDF: Adicionado OUTROS: R$ {valor:.2f}, Total: R$ {total_outros:.2f}")
        
        # 1. CUSTO TOTAL DO CLIENTE
        custo_cliente_total = valor_base + valor_produtos_total + custos_fornecedores + total_outros
        
        # 2. MEU GANHO
        meu_ganho = valor_base + total_comissoes + lucro_produtos_total - custos_assistentes
        
        # Definir cores para melhorar a distinção visual
        cor_cliente = colors.dodgerblue
        cor_ganho = colors.forestgreen
        
        # PRIMEIRA VISÃO - Custo total do cliente
        story.append(Spacer(1, 10))
        
        # Cabeçalho da tabela com cores diferentes para identificação visual
        cliente_header = ParagraphStyle(
            'ClienteHeader', 
            parent=styles['Heading4'],
            textColor=cor_cliente,
            borderWidth=1,
            borderColor=cor_cliente,
            borderPadding=5,
            borderRadius=5,
            alignment=0
        )
        
        story.append(Paragraph("<b>VISÃO 1: CUSTO TOTAL DO CLIENTE</b>", cliente_header))
        story.append(Paragraph("Esta seção mostra todos os valores que o cliente está pagando na proposta.", 
                           ParagraphStyle('ExplanationClient', parent=styles['Normal'], fontSize=9, leading=10)))
        story.append(Spacer(1, 5))
        
        # Tabela de resumo - Custo total do cliente
        data_custo_cliente = [
            ["Item", "Valor"],
            ["Valor Base", f"R$ {valor_base:.2f}"],
            ["Produtos", f"R$ {valor_produtos_total:.2f}"],
            ["Fornecedores", f"R$ {custos_fornecedores:.2f}"],
            ["Outros", f"R$ {total_outros:.2f}"],
            ["CUSTO TOTAL DO CLIENTE", f"R$ {custo_cliente_total:.2f}"]
        ]
        
        # Estilo para tabela - Custo total do cliente
        cliente_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cor_cliente),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            # Destacar valor total
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightskyblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ])
        
        cliente_table = Table(data_custo_cliente, colWidths=[3.5*inch, 3*inch])
        cliente_table.setStyle(cliente_style)
        story.append(cliente_table)
        
        # SEGUNDA VISÃO - Meu ganho
        story.append(Spacer(1, 20))
        
        ganho_header = ParagraphStyle(
            'GanhoHeader', 
            parent=styles['Heading4'],
            textColor=cor_ganho,
            borderWidth=1,
            borderColor=cor_ganho,
            borderPadding=5,
            borderRadius=5,
            alignment=0
        )
        
        story.append(Paragraph("<b>VISÃO 2: MEU GANHO (ORGANIZADORA)</b>", ganho_header))
        story.append(Paragraph("Esta seção mostra o ganho real da organizadora, considerando o valor base, comissões, \
lucro na venda de produtos menos o pagamento a assistentes.", 
                           ParagraphStyle('ExplanationGanho', parent=styles['Normal'], fontSize=9, leading=10)))
        story.append(Spacer(1, 5))
        
        # Tabela de resumo - Meu ganho
        data_meu_ganho = [
            ["Item", "Valor"],
            ["Valor Base", f"R$ {valor_base:.2f}"],
            ["Comissões", f"R$ {total_comissoes:.2f}"],
            ["Lucro em Produtos", f"R$ {lucro_produtos_total:.2f}"],
            ["Pagamento Assistentes", f"R$ -{custos_assistentes:.2f}"],
            ["MEU GANHO TOTAL", f"R$ {meu_ganho:.2f}"]
        ]
        
        # Estilo para tabela - Meu ganho
        ganho_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cor_ganho),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            # Destacar valores importantes
            ('BACKGROUND', (0, 2), (-1, 2), colors.palegreen),
            ('BACKGROUND', (0, 3), (-1, 3), colors.palegreen),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ])
        
        ganho_table = Table(data_meu_ganho, colWidths=[3.5*inch, 3*inch])
        ganho_table.setStyle(ganho_style)
        story.append(ganho_table)
        
        # Tabela de comparação
        story.append(Spacer(1, 20))
        
        analise_header = ParagraphStyle(
            'AnaliseHeader', 
            parent=styles['Heading4'],
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5,
            borderRadius=5,
            alignment=0
        )
        
        story.append(Paragraph("<b>COMPARATIVO E ANÁLISE DE MARGEM</b>", analise_header))
        story.append(Paragraph("Comparação direta entre o custo total do cliente e o ganho da organizadora, \
mostrando a margem de lucro percentual.", 
                           ParagraphStyle('ExplanationGanho', parent=styles['Normal'], fontSize=9, leading=10)))
        story.append(Spacer(1, 5))
        
        # Calcular margem de lucro sobre o total
        margem_percentual = (meu_ganho / custo_cliente_total * 100) if custo_cliente_total > 0 else 0
        
        # Mostrar formato diferente para margem (verde se estiver acima de 30%, amarelo entre 20-30%, vermelho abaixo de 20%)
        cor_margem = colors.green if margem_percentual >= 30 else (colors.orange if margem_percentual >= 20 else colors.red)
        avaliacao = "IDEAL" if margem_percentual >= 30 else ("BOA" if margem_percentual >= 20 else "ABAIXO DO IDEAL")
        
        # Tabela de análise detalhada com gráfico visual
        data_analise = [
            ["Item", "Valor", "Avaliação"],
            ["Custo Total do Cliente", f"R$ {custo_cliente_total:.2f}", ""],
            ["Meu Ganho Total", f"R$ {meu_ganho:.2f}", ""],
            ["MARGEM PERCENTUAL", f"{margem_percentual:.2f}%", avaliacao]
        ]
        
        # Estilo para tabela de análise
        analise_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            # Destacar margem
            ('BACKGROUND', (0, -1), (-1, -1), colors.palegreen),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (2, -1), (2, -1), cor_margem),
            ('FONTNAME', (2, -1), (2, -1), 'Helvetica-Bold'),
        ])
        
        analise_table = Table(data_analise, colWidths=[3*inch, 2*inch, 1.5*inch])
        analise_table.setStyle(analise_style)
        story.append(analise_table)
        
        # Adicionar explicação sobre a margem ideal
        if margem_percentual < 30:
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<font color='{cor_margem.hexval()}'><b>ATENÇÃO:</b> A margem atual de {margem_percentual:.2f}% está abaixo do ideal de 30%. "
                f"Considere rever os valores da proposta ou reduzir custos para aumentar a lucratividade.</font>", 
                ParagraphStyle('AvisoMargem', parent=styles['Normal'], alignment=0, spaceBefore=5)
            ))
        else:
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<font color='green'><b>EXCELENTE:</b> A margem atual de {margem_percentual:.2f}% está acima do ideal de 30%. "
                f"Esta proposta tem uma boa lucratividade para a organização.</font>", 
                ParagraphStyle('AvisoMargem', parent=styles['Normal'], alignment=0, spaceBefore=5)
            ))
        
        # Alertas e observações
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Análise e Recomendações</b>", styles["Heading4"]))
        
        if margem_percentual < 30:
            story.append(Paragraph(f"<font color='red'><b>ALERTA:</b> Margem abaixo do recomendado ({margem_percentual:.2f}%)</font>", styles["Normal"]))
            story.append(Paragraph("Recomendação: Analisar custos e considerar revisão de valores em projetos futuros similares.", styles["Normal"]))
        else:
            story.append(Paragraph(f"<font color='green'><b>POSITIVO:</b> Margem dentro do esperado ({margem_percentual:.2f}%)</font>", styles["Normal"]))
        
        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>Observações Finais</b>", styles["Heading4"]))
        story.append(Paragraph("1. Este documento é CONFIDENCIAL e de uso interno.", styles["Normal"]))
        story.append(Paragraph("2. A margem ideal deve ser de no mínimo 30% do valor total.", styles["Normal"]))
        story.append(Paragraph("3. Custos com assistentes são despesas da empresa.", styles["Normal"]))
        story.append(Paragraph("4. Custos com fornecedores são normalmente repassados ao cliente.", styles["Normal"]))

        # Data e responsável
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", 
                            ParagraphStyle('DataGeracao', fontSize=8, alignment=1)))
        story.append(Paragraph("CONFIDENCIAL - USO INTERNO", 
                            ParagraphStyle('Confidencial', fontSize=10, alignment=1, textColor=colors.red)))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF interno gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF interno: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF interno: {str(e)}")
    
def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
    """
    Gera um PDF com o fechamento da proposta com o novo formato solicitado
    
    Args:
        proposta: Dicionário com os dados da proposta
        cliente: Dicionário com os dados do cliente
        acrescimos: DataFrame com os acréscimos da proposta
        filename: Nome do arquivo PDF a ser gerado
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Logs para debugging
    print(f"DEBUG PDF: Gerando PDF para proposta #{proposta.get('id', 'N/A')}")
    print(f"DEBUG PDF: Cliente: {cliente.get('nome', 'N/A')}")
    print(f"DEBUG PDF: Filename: {filename}")
    print(f"DEBUG PDF: Acréscimos: {len(acrescimos) if not acrescimos.empty else 0} registros")
    
    try:
        # Certificar que o diretório existe
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Inicializar documento
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Título centralizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        # Título único centralizado com o ID da proposta e nome do cliente
        story.append(Paragraph(f"Proposta #{proposta['id']} - {cliente['nome']}", title_style))
        story.append(Paragraph(f"{datetime.now().strftime('%d/%m/%Y')}", styles["Heading3"]))
        story.append(Spacer(1, 12))

        # Informações da Proposta
        story.append(Paragraph("<b>Informações da Proposta</b>", styles["Heading3"]))
        story.append(Paragraph(f"<b>Tipo:</b> {proposta['tipo_proposta']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Status:</b> {proposta['status']}", styles["Normal"]))

        # Datas
        if proposta.get('data_inicio'):
            story.append(Paragraph(f"<b>Data Início:</b> {proposta['data_inicio'].strftime('%d/%m/%Y')}", styles["Normal"]))
        if proposta.get('data_fim'):
            story.append(Paragraph(f"<b>Data Fim:</b> {proposta['data_fim'].strftime('%d/%m/%Y')}", styles["Normal"]))
            
            # Calcular prazo de entrega em dias se ambas as datas estiverem disponíveis
            if proposta.get('data_inicio'):
                dias = (proposta['data_fim'] - proposta['data_inicio']).days
                story.append(Paragraph(f"<b>Prazo de Entrega:</b> {dias} dias", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Renomear "Valores a Receber do Cliente" para "Investimento"
        story.append(Paragraph("<b>Investimento</b>", styles["Heading3"]))
        data_receber = [["Descrição", "Valor", "Status"]]
        data_pagar_assistentes = [["Descrição", "Valor", "Status"]]
        data_pagar_lojas = [["Descrição", "Valor", "Status"]]

        # Processar a descrição para usar como item da tabela
        descricao_completa = ""
        descricao_linhas = proposta['descricao'].split('\n')
        for linha in descricao_linhas:
            linha = linha.strip()
            if linha:
                descricao_completa += f"• {linha}\n"
        
        # Usar a descrição do serviço no lugar de "Valor Base"
        data_receber.append([
            descricao_completa, 
            f"R$ {float(proposta['valor']):.2f}", 
            proposta.get('status_pagamento_base', 'Pendente')
        ])
        total_receber = float(proposta['valor'])
        total_pagar_assistentes = 0.0
        total_pagar_lojas = 0.0

        # Processar acréscimos
        if not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                descricao = f"{acrescimo['tipo']}"
                if acrescimo['fornecedor']:
                    descricao += f" - {acrescimo['fornecedor']}"
                if acrescimo.get('descricao'):
                    descricao += f"\n{acrescimo['descricao']}"

                valor = float(acrescimo['valor'])

                # Classificar os valores
                if acrescimo['tipo'].lower() == 'assistente':
                    data_pagar_assistentes.append([
                        descricao,
                        f"R$ {valor:.2f}",
                        acrescimo.get('status_pagamento', 'Pendente')
                    ])
                    total_pagar_assistentes += valor
                elif acrescimo['tipo'].lower() in ['fornecedor', 'produto', 'marcenaria']:
                    data_pagar_lojas.append([
                        descricao,
                        f"R$ {valor:.2f}",
                        acrescimo.get('status_pagamento', 'Pendente')
                    ])
                    total_pagar_lojas += valor
                else:
                    # Tipo "Organização" e outros vão para valores a receber
                    data_receber.append([
                        descricao,
                        f"R$ {valor:.2f}",
                        acrescimo.get('status_pagamento', 'Pendente')
                    ])
                    total_receber += valor

        # Tabela style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ])

        # Criar e adicionar tabela de valores a receber
        table_receber = Table(data_receber, colWidths=[4*inch, 1.5*inch, 1*inch])
        table_receber.setStyle(table_style)
        story.append(table_receber)
        story.append(Spacer(1, 12))
        
        # Removido "Total a receber do Cliente" conforme solicitado

        # Se houver valores a pagar para lojas/fornecedores
        if len(data_pagar_lojas) > 1:  # Se tiver mais que só o cabeçalho
            story.append(Spacer(1, 20))
            story.append(Paragraph("<b>Valores a Pagar a Lojas/Fornecedores</b>", styles["Heading3"]))
            table_pagar_lojas = Table(data_pagar_lojas, colWidths=[4*inch, 1.5*inch, 1*inch])
            table_pagar_lojas.setStyle(table_style)
            story.append(table_pagar_lojas)
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Total a Pagar a Lojas/Fornecedores:</b> R$ {total_pagar_lojas:.2f}", 
                                 ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

        # Se houver valores a pagar para assistentes
        if len(data_pagar_assistentes) > 1:  # Se tiver mais que só o cabeçalho
            story.append(Spacer(1, 20))
            story.append(Paragraph("<b>Valores a Pagar aos Assistentes</b>", styles["Heading3"]))
            table_pagar_assistentes = Table(data_pagar_assistentes, colWidths=[4*inch, 1.5*inch, 1*inch])
            table_pagar_assistentes.setStyle(table_style)
            story.append(table_pagar_assistentes)
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Total a Pagar aos Assistentes:</b> R$ {total_pagar_assistentes:.2f}", 
                                 ParagraphStyle('Total', parent=styles['Normal'], fontSize=12, alignment=2)))

        # Removido "Resumo Financeiro" e "Resultado Final" conforme solicitado

        # Observações Finais
        story.append(Spacer(1, 30))
        story.append(Paragraph("Observações:", styles["Heading4"]))
        # Apenas as observações solicitadas
        story.append(Paragraph("2. Os valores apresentados incluem todos os custos e acréscimos.", styles["Normal"]))
        story.append(Paragraph("3. Valores a receber incluem base e serviços de organização.", styles["Normal"]))
        story.append(Paragraph("5. Valores a pagar a lojas/fornecedores são responsabilidade do cliente.", styles["Normal"]))

        # Gerar PDF
        doc.build(story)
        print(f"DEBUG PDF: PDF gerado com sucesso: {filename}")
        return filename
    except Exception as e:
        print(f"DEBUG PDF ERROR: Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Erro ao gerar PDF: {str(e)}")