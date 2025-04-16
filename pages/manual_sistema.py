import os
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.graphics.shapes import Drawing, Line

def gerar_manual_sistema():
    """
    Gera um manual do sistema em PDF com explicações detalhadas de todas as funcionalidades
    """
    # Configurar diretório para salvar o PDF
    pdf_dir = "pdfs"
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    
    # Caminho do arquivo PDF
    pdf_path = os.path.join(pdf_dir, "Manual_Planner_Organizer.pdf")
    
    # Criar documento
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Lista de elementos para o PDF
    elementos = []
    
    # Estilos de parágrafo
    estilos = getSampleStyleSheet()
    
    # Criar estilos personalizados
    titulo_estilo = ParagraphStyle(
        'TituloEstilo',
        parent=estilos['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1E366F'),
        spaceAfter=12,
        spaceBefore=12,
        alignment=1  # Centralizado
    )
    
    subtitulo_estilo = ParagraphStyle(
        'SubtituloEstilo',
        parent=estilos['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=8,
        spaceBefore=8
    )
    
    texto_estilo = ParagraphStyle(
        'TextoEstilo',
        parent=estilos['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    secao_estilo = ParagraphStyle(
        'SecaoEstilo',
        parent=estilos['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=6,
        spaceBefore=6
    )
    
    # Função para adicionar uma linha separadora
    def adicionar_linha():
        d = Drawing(500, 1)
        line = Line(0, 0, 450, 0)
        line.strokeColor = colors.HexColor('#E0E0E0')
        line.strokeWidth = 1
        d.add(line)
        elementos.append(d)
        elementos.append(Spacer(1, 10))
    
    # Titulo do documento
    elementos.append(Paragraph("MANUAL DO SISTEMA", titulo_estilo))
    elementos.append(Paragraph("Planner Organizer 1.0.4", subtitulo_estilo))
    elementos.append(Spacer(1, 20))
    
    # Introdução
    elementos.append(Paragraph("Introdução", secao_estilo))
    elementos.append(Paragraph(
        "O Planner Organizer é um sistema completo para gerenciamento de propostas, clientes, "
        "vendas e controle financeiro, desenvolvido especialmente para Personal Organizers. "
        "Este manual tem como objetivo apresentar todas as funcionalidades do sistema e "
        "orientar sua utilização de forma simples e objetiva.",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    adicionar_linha()
    
    # Visão Geral do Sistema
    elementos.append(Paragraph("Visão Geral do Sistema", subtitulo_estilo))
    elementos.append(Paragraph(
        "O sistema está organizado em módulos distintos, cada um responsável por um "
        "aspecto específico da gestão do negócio. A navegação é feita através do "
        "menu principal, que dá acesso a todos os módulos:",
        texto_estilo
    ))
    
    # Tabela com os módulos
    dados_modulos = [
        ["Módulo", "Descrição"],
        ["Dashboard", "Visão geral do negócio com métricas, alertas e indicadores financeiros"],
        ["Cadastros", "Gerenciamento de clientes, fornecedores, parceiros e assistentes"],
        ["Propostas", "Ciclo completo de propostas desde elaboração até finalização"],
        ["Vendas", "Controle de produtos vendidos, quantidades e valores por cliente"],
        ["Financeiro", "Gestão de receitas, despesas, contas a pagar e receber"],
        ["Relatórios", "Análises e visualizações detalhadas de desempenho"]
    ]
    
    tabela_modulos = Table(dados_modulos, colWidths=[100, 300])
    tabela_modulos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#1E366F')),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
    ]))
    elementos.append(tabela_modulos)
    elementos.append(Spacer(1, 15))
    
    # Adicionar descrições detalhadas de cada módulo
    elementos.append(Paragraph("1. Módulo Dashboard", secao_estilo))
    elementos.append(Paragraph(
        "O Dashboard é a página inicial do sistema, fornecendo uma visão geral "
        "do seu negócio em tempo real. Nele você encontra:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Métricas principais: número de propostas em andamento, receita prevista, etc.",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Alertas: propostas próximas do prazo de vencimento (60 dias)",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Gráficos: distribuição de propostas por status, evolução de receitas",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Indicadores financeiros: valores a receber e a pagar, saldo projetado",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("2. Módulo Cadastros", secao_estilo))
    elementos.append(Paragraph(
        "O módulo de Cadastros é responsável pelo gerenciamento de todas as entidades "
        "do sistema, dividido em quatro seções principais:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Clientes: gerenciamento completo dos dados de clientes, incluindo informações "
        "de contato, endereço e observações",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Fornecedores: cadastro de fornecedores com percentuais de comissão para "
        "cálculos automáticos nas propostas",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Parceiros: cadastro de parceiros de negócio para referência em projetos",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Assistentes: cadastro de assistentes que colaboram nos projetos, com valores "
        "a pagar quando propostas são finalizadas",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("3. Módulo Propostas", secao_estilo))
    elementos.append(Paragraph(
        "O módulo de Propostas é o coração do sistema, gerenciando todo o ciclo de vida "
        "das propostas comerciais, desde a elaboração até a finalização:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Fluxo completo: Em elaboração → Aguardando aprovação → Aprovada → Em execução → Finalizada",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Cadastro completo: cliente, descrição, valores, prazos, tipo de proposta",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Edição direta: todos os campos podem ser editados diretamente na tabela",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Integração automática: quando uma proposta é finalizada, gera automaticamente "
        "registros financeiros e de vendas",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Importação em lote: possibilidade de importar múltiplas propostas via CSV",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("4. Módulo Vendas", secao_estilo))
    elementos.append(Paragraph(
        "O módulo de Vendas controla os produtos vendidos para cada cliente, "
        "com geração automática a partir de propostas finalizadas:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Registro de produtos: controle de produtos vendidos com quantidades e valores",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Vinculação automática: produtos são automaticamente vinculados ao cliente da proposta",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Geração de receitas: cada venda gera automaticamente registros financeiros a receber",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("5. Módulo Financeiro", secao_estilo))
    elementos.append(Paragraph(
        "O módulo Financeiro gerencia todas as transações financeiras, incluindo "
        "receitas, despesas, contas a pagar e a receber:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Receitas: registro de valores a receber de clientes, gerados automaticamente "
        "a partir de propostas e vendas",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Despesas: registro de valores a pagar a fornecedores, assistentes e outros",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Filtros: possibilidade de filtrar transações por tipo, data, status, etc",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Controle de pagamentos: marcação de transações como pagas/recebidas",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("6. Módulo Relatórios", secao_estilo))
    elementos.append(Paragraph(
        "O módulo de Relatórios oferece análises detalhadas de desempenho do negócio, "
        "com gráficos e tabelas personalizáveis:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Desempenho de vendas: análise por cliente, período, tipo de proposta",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Análise financeira: receitas vs despesas, projeções, fluxo de caixa",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Exportação: possibilidade de exportar relatórios em diversos formatos",
        texto_estilo
    ))
    elementos.append(Spacer(1, 15))
    
    adicionar_linha()
    
    # Funcionalidades Especiais
    elementos.append(Paragraph("Funcionalidades Especiais", subtitulo_estilo))
    
    elementos.append(Paragraph("1. Integração entre Módulos", secao_estilo))
    elementos.append(Paragraph(
        "Uma das principais vantagens do sistema é a integração automática entre "
        "os módulos, que elimina a necessidade de cadastro manual duplicado:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Quando uma proposta é marcada como finalizada, são gerados automaticamente:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "  - Registros de produtos na seção Vendas",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "  - Lançamentos financeiros para receber valores dos produtos",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "  - Comissões para fornecedores baseadas no percentual cadastrado",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "  - Pagamentos para assistentes envolvidos no projeto",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "  - Lançamento para receber o valor base da proposta do cliente",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("2. Sistema de Importação em Lote", secao_estilo))
    elementos.append(Paragraph(
        "O sistema oferece ferramentas para importação em lote de clientes e propostas, "
        "facilitando a migração de dados de outros sistemas:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Importação de clientes: através de arquivos CSV com modelo padronizado",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Importação de propostas: permite vincular propostas a clientes existentes",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Validação de dados: verificação automática para evitar inconsistências",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("3. Sistema de Backup", secao_estilo))
    elementos.append(Paragraph(
        "O sistema conta com ferramenta de backup para garantir a segurança dos dados:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Backup manual: possibilidade de criar pontos de backup a qualquer momento",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Backup automático: programação de backups periódicos",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Restauração: permite recuperar o sistema a partir de um backup anterior",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("4. Seleção Múltipla para Exclusões", secao_estilo))
    elementos.append(Paragraph(
        "O sistema permite selecionar múltiplos registros para exclusão em lote, "
        "facilitando a limpeza de dados:",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Checkboxes: seleção individual ou em grupo",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Exclusão em lote: remoção de múltiplos registros com um único clique",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Confirmação simplificada: processo otimizado sem confirmações textuais",
        texto_estilo
    ))
    elementos.append(Spacer(1, 15))
    
    adicionar_linha()
    
    # Dicas e Melhores Práticas
    elementos.append(Paragraph("Dicas e Melhores Práticas", subtitulo_estilo))
    
    elementos.append(Paragraph(
        "Para aproveitar ao máximo o sistema, recomendamos seguir estas práticas:",
        texto_estilo
    ))
    
    elementos.append(Paragraph("1. Fluxo de Trabalho Recomendado", secao_estilo))
    elementos.append(Paragraph(
        "• Mantenha o fluxo de propostas sempre atualizado, seguindo a sequência: "
        "Em elaboração → Aguardando aprovação → Aprovada → Em execução → Finalizada",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Atualize o status regularmente para ter métricas precisas no Dashboard",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Finalize as propostas assim que o trabalho for concluído, para que os "
        "lançamentos financeiros sejam gerados automaticamente",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("2. Cadastros Completos", secao_estilo))
    elementos.append(Paragraph(
        "• Mantenha o cadastro de clientes sempre atualizado com informações de contato",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Cadastre corretamente os percentuais de comissão para fornecedores",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Registre todos os assistentes que participam dos projetos",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("3. Backup Regular", secao_estilo))
    elementos.append(Paragraph(
        "• Crie pontos de backup regularmente, especialmente antes de fazer grandes "
        "mudanças no sistema",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Verifique periodicamente se os backups automáticos estão funcionando corretamente",
        texto_estilo
    ))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("4. Monitoramento do Dashboard", secao_estilo))
    elementos.append(Paragraph(
        "• Consulte regularmente o Dashboard para identificar propostas próximas do prazo",
        texto_estilo
    ))
    elementos.append(Paragraph(
        "• Utilize os indicadores financeiros para planejar melhor seu fluxo de caixa",
        texto_estilo
    ))
    elementos.append(Spacer(1, 15))
    
    adicionar_linha()
    
    # Conclusão
    elementos.append(Paragraph("Conclusão", subtitulo_estilo))
    elementos.append(Paragraph(
        "O Planner Organizer foi desenvolvido para facilitar a gestão completa do seu "
        "negócio, integrando todas as etapas em um único sistema. Com uma interface "
        "intuitiva e funcionalidades automatizadas, você pode se concentrar no que "
        "realmente importa: atender seus clientes com excelência. Para dúvidas ou "
        "sugestões, entre em contato com nossa equipe de suporte.",
        texto_estilo
    ))
    elementos.append(Spacer(1, 15))
    
    elementos.append(Paragraph(
        "© 2025 Planner Organizer - Versão 1.0.4",
        ParagraphStyle(
            'RodapeEstilo',
            parent=estilos['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # Centralizado
        )
    ))
    
    # Construir o PDF
    doc.build(elementos)
    
    return pdf_path

def show():
    st.set_page_config(
        page_title="Manual do Sistema",
        page_icon="📘",
        layout="centered"
    )
    
    st.title("📘 Manual do Sistema Planner Organizer")
    
    st.write("""
    Este módulo gera um manual completo do Planner Organizer em formato PDF,
    com explicações detalhadas de todas as funcionalidades do sistema.
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("""
        O manual contém:
        - Visão geral do sistema
        - Descrição detalhada de cada módulo
        - Funcionalidades especiais
        - Dicas e melhores práticas
        - Fluxos de trabalho recomendados
        """)
    
    if st.button("📥 Gerar Manual do Sistema", type="primary"):
        with st.spinner("Gerando manual em PDF..."):
            try:
                pdf_path = gerar_manual_sistema()
                
                # Ler o arquivo PDF para exibição
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                    
                    st.success("Manual gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar Manual do Sistema (PDF)",
                        data=pdf_bytes,
                        file_name="Manual_Planner_Organizer.pdf",
                        mime="application/pdf",
                        key='download-pdf'
                    )
            except Exception as e:
                st.error(f"Erro ao gerar o manual: {str(e)}")
                st.info("Verifique se todas as dependências estão instaladas. O ReportLab é necessário para gerar o PDF.")