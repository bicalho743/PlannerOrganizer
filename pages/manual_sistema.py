import os
import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

NAVY_RGB = colors.HexColor('#0D1B2A')
NAVY_LIGHT_RGB = colors.HexColor('#162840')
GOLD_RGB = colors.HexColor('#C9A84C')
GOLD_DARK_RGB = colors.HexColor('#B8943D')
GOLD_LIGHT_RGB = colors.HexColor('#F5ECD7')
WHITE = colors.white
GRAY_TEXT = colors.HexColor('#4A5568')
GRAY_LIGHT = colors.HexColor('#E2E8F0')
GRAY_BG = colors.HexColor('#F7FAFC')


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY_RGB)
    canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(0, h - 31, w, 3, fill=1, stroke=0)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(72, h - 20, "PLANNER ORGANIZER")
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#A0AEC0'))
    canvas.drawRightString(w - 72, h - 20, "Manual do Sistema")
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(0, 30, w, 2, fill=1, stroke=0)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(GRAY_TEXT)
    canvas.drawString(72, 16, f"© {datetime.now().year} Planner Organizer — Todos os direitos reservados")
    canvas.drawRightString(w - 72, 16, f"Página {doc.page}")
    canvas.restoreState()


def _first_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY_RGB)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(60, h / 2 + 80, w - 120, 3, fill=1, stroke=0)
    canvas.setFont('Helvetica-Bold', 32)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(w / 2, h / 2 + 110, "PLANNER ORGANIZER")
    canvas.setFont('Helvetica', 14)
    canvas.setFillColor(GOLD_RGB)
    canvas.drawCentredString(w / 2, h / 2 + 50, "MANUAL COMPLETO DO SISTEMA")
    canvas.setFont('Helvetica', 11)
    canvas.setFillColor(colors.HexColor('#94A3B8'))
    canvas.drawCentredString(w / 2, h / 2 + 10, "Guia detalhado de funcionalidades e operações")
    canvas.drawCentredString(w / 2, h / 2 - 10, "para Personal Organizers")
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(60, h / 2 - 40, w - 120, 1, fill=1, stroke=0)
    canvas.setFont('Helvetica', 10)
    canvas.setFillColor(colors.HexColor('#64748B'))
    canvas.drawCentredString(w / 2, h / 2 - 70, f"Versão 1.0.4  •  {datetime.now().strftime('%B %Y')}")
    canvas.restoreState()


def gerar_manual_sistema():
    pdf_dir = "pdfs"
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    pdf_path = os.path.join(pdf_dir, "Manual_Planner_Organizer.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=52,
        bottomMargin=50
    )

    estilos = getSampleStyleSheet()

    st_titulo = ParagraphStyle(
        'ManualTitulo', parent=estilos['Heading1'],
        fontSize=20, textColor=NAVY_RGB, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=24, alignment=TA_LEFT
    )
    st_subtitulo = ParagraphStyle(
        'ManualSubtitulo', parent=estilos['Heading2'],
        fontSize=14, textColor=GOLD_DARK_RGB, fontName='Helvetica-Bold',
        spaceAfter=8, spaceBefore=18
    )
    st_secao = ParagraphStyle(
        'ManualSecao', parent=estilos['Heading3'],
        fontSize=12, textColor=NAVY_RGB, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=14
    )
    st_texto = ParagraphStyle(
        'ManualTexto', parent=estilos['Normal'],
        fontSize=10, textColor=GRAY_TEXT, leading=15,
        spaceAfter=5, alignment=TA_JUSTIFY
    )
    st_bullet = ParagraphStyle(
        'ManualBullet', parent=st_texto,
        leftIndent=18, bulletIndent=6, spaceAfter=4
    )
    st_sub_bullet = ParagraphStyle(
        'ManualSubBullet', parent=st_texto,
        leftIndent=36, bulletIndent=24, spaceAfter=3,
        fontSize=9.5
    )
    st_destaque = ParagraphStyle(
        'ManualDestaque', parent=st_texto,
        backColor=GOLD_LIGHT_RGB, borderPadding=(8, 10, 8, 10),
        leftIndent=12, rightIndent=12, spaceAfter=10, spaceBefore=8,
        fontSize=10, textColor=NAVY_RGB, leading=15
    )
    st_rodape = ParagraphStyle(
        'ManualRodape', parent=estilos['Normal'],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER
    )

    e = []

    def _gold_line():
        d = Drawing(480, 4)
        line = Line(0, 2, 470, 2)
        line.strokeColor = GOLD_RGB
        line.strokeWidth = 1.5
        d.add(line)
        e.append(d)
        e.append(Spacer(1, 8))

    def _gray_line():
        d = Drawing(480, 2)
        line = Line(0, 1, 470, 1)
        line.strokeColor = GRAY_LIGHT
        line.strokeWidth = 0.5
        d.add(line)
        e.append(d)
        e.append(Spacer(1, 6))

    def _navy_table(dados, col_widths=None):
        if col_widths is None:
            col_widths = [120, 350]
        t = Table(dados, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_RGB),
            ('TEXTCOLOR', (0, 0), (-1, 0), GOLD_RGB),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), GRAY_TEXT),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        e.append(t)
        e.append(Spacer(1, 12))

    def _bullet(texto):
        e.append(Paragraph(f"<bullet>&bull;</bullet> {texto}", st_bullet))

    def _sub_bullet(texto):
        e.append(Paragraph(f"<bullet>–</bullet> {texto}", st_sub_bullet))

    e.append(PageBreak())

    e.append(Paragraph("Introdução", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O <b>Planner Organizer</b> é uma plataforma de gestão empresarial desenvolvida "
        "exclusivamente para <b>Personal Organizers</b>. O sistema centraliza todas as "
        "operações do seu negócio — desde a captação de clientes e elaboração de propostas "
        "até o controle financeiro completo — em um único ambiente digital integrado.",
        st_texto
    ))
    e.append(Paragraph(
        "Projetado para eliminar planilhas dispersas e processos manuais, o Planner Organizer "
        "automatiza tarefas repetitivas, gera relatórios profissionais em PDF e oferece visibilidade "
        "em tempo real sobre a saúde financeira do seu negócio. Este manual apresenta cada recurso "
        "disponível de forma detalhada, para que você possa aproveitar ao máximo todas as funcionalidades.",
        st_texto
    ))
    e.append(Spacer(1, 8))
    e.append(Paragraph(
        "<b>Destaques da plataforma:</b> Gestão de propostas com fluxo completo de status • "
        "Geração automática de lançamentos financeiros • Cálculo de comissões de fornecedores • "
        "Relatórios em PDF com design profissional • Dashboard com métricas em tempo real • "
        "Importação em lote de dados • Sistema multi-tenant com controle de acesso.",
        st_destaque
    ))
    e.append(Spacer(1, 10))

    e.append(Paragraph("Arquitetura do Sistema", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O sistema é organizado em módulos independentes, porém integrados entre si. "
        "Cada módulo é responsável por um aspecto específico da gestão do negócio, e a "
        "navegação é feita através do menu lateral, sempre visível em todas as telas.",
        st_texto
    ))
    _navy_table([
        ["Módulo", "Descrição"],
        ["📊 Dashboard", "Página inicial com métricas consolidadas, alertas de prazos, gráficos de desempenho e indicadores financeiros em tempo real."],
        ["👥 Cadastros", "Gerenciamento completo de clientes, fornecedores, parceiros e assistentes — base de dados centralizada para todas as operações."],
        ["📝 Propostas", "Ciclo completo de propostas comerciais: elaboração, precificação com itens detalhados, acompanhamento por status e finalização com geração automática de vendas e finanças."],
        ["🛒 Vendas", "Registro de produtos vendidos por cliente, com vinculação automática a propostas finalizadas e geração de receitas."],
        ["💰 Financeiro", "Painel Kanban de transações — contas a receber, contas a pagar e transações aprovadas/pagas, com filtros e análise visual."],
        ["📋 Pós-Organização", "Acompanhamento pós-projeto para garantir satisfação do cliente e registrar observações de follow-up."],
        ["📈 Relatórios", "Análises detalhadas de desempenho com gráficos interativos, comparativos por período e exportação de dados."],
        ["🧑‍💼 Perfil", "Configurações pessoais da conta, dados do usuário e preferências do sistema."],
    ])

    e.append(PageBreak())

    e.append(Paragraph("1. Dashboard", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O Dashboard é a visão executiva do seu negócio. Ao acessar o sistema, você encontra "
        "imediatamente os indicadores mais importantes para a tomada de decisão:",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Métricas Principais", st_secao))
    _bullet("Cards de resumo no topo: total de propostas ativas, receita prevista, valores em aberto e saldo projetado")
    _bullet("Atualização em tempo real conforme propostas são criadas, aprovadas ou finalizadas")
    _bullet("Indicadores visuais com cores diferenciadas para facilitar a leitura rápida")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Sistema de Alertas", st_secao))
    _bullet("Propostas próximas do prazo de vencimento (alerta de 60 dias) são destacadas automaticamente")
    _bullet("Notificação visual quando há propostas em atraso ou pendentes de aprovação")
    _bullet("Os alertas são calculados com base na data de prazo cadastrada na proposta")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Gráficos e Visualizações", st_secao))
    _bullet("Distribuição de propostas por status (Em elaboração, Aguardando aprovação, Aprovada, Em execução, Finalizada)")
    _bullet("Evolução de receitas ao longo do tempo com gráficos de tendência")
    _bullet("Indicadores financeiros: valores a receber vs. a pagar, saldo projetado para o período")
    e.append(Spacer(1, 10))

    e.append(Paragraph("2. Cadastros", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O módulo de Cadastros é a base de dados do sistema. Todas as entidades que participam "
        "das operações são gerenciadas aqui e ficam disponíveis automaticamente nos demais módulos.",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Clientes", st_secao))
    _bullet("Cadastro completo com nome, e-mail, telefone, endereço e observações")
    _bullet("Histórico automático: ao acessar um cliente, você visualiza todas as propostas, vendas e transações vinculadas")
    _bullet("Busca e filtros para localizar clientes rapidamente")
    _bullet("Edição direta dos dados a qualquer momento")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Fornecedores", st_secao))
    _bullet("Cadastro de fornecedores com dados de contato e <b>percentual de comissão</b>")
    _bullet("O percentual de comissão é utilizado automaticamente no cálculo de propostas")
    _bullet("Quando uma proposta é finalizada, o sistema gera automaticamente um lançamento financeiro de pagamento ao fornecedor com base na comissão cadastrada")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Parceiros", st_secao))
    _bullet("Cadastro de parceiros de negócio para referência e indicação em projetos")
    _bullet("Acompanhamento de parcerias ativas e histórico de colaborações")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Assistentes", st_secao))
    _bullet("Cadastro de assistentes que colaboram nos projetos de organização")
    _bullet("Definição de valores a pagar por projeto")
    _bullet("Quando uma proposta é finalizada, o sistema gera automaticamente o lançamento de pagamento ao assistente")
    e.append(Spacer(1, 10))

    e.append(PageBreak())

    e.append(Paragraph("3. Propostas", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O módulo de Propostas é o coração operacional do Planner Organizer. Aqui você gerencia "
        "todo o ciclo de vida de cada proposta comercial, desde a elaboração inicial até a "
        "finalização com geração automática de vendas e finanças.",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Fluxo de Status", st_secao))
    e.append(Paragraph(
        "Cada proposta segue um fluxo sequencial de status que reflete o andamento real do projeto:",
        st_texto
    ))
    _navy_table([
        ["Status", "Descrição"],
        ["Em elaboração", "Proposta em fase de construção. Você pode adicionar e editar itens, ajustar valores e definir prazos livremente."],
        ["Aguardando aprovação", "Proposta finalizada e enviada ao cliente para análise. Os relatórios em PDF podem ser gerados neste estágio."],
        ["Aprovada", "Cliente aprovou a proposta. O projeto está pronto para iniciar a execução."],
        ["Em execução", "Projeto em andamento. Registre andamentos e acompanhe o progresso."],
        ["Finalizada", "Projeto concluído. O sistema gera automaticamente registros de vendas, receitas e pagamentos."],
    ], col_widths=[110, 360])
    e.append(Spacer(1, 4))
    e.append(Paragraph("Estrutura de uma Proposta", st_secao))
    _bullet("<b>Dados básicos:</b> cliente, descrição do projeto, tipo de proposta, valor base (honorários da Personal Organizer), data de prazo")
    _bullet("<b>Produtos:</b> itens que serão adquiridos para o projeto (caixas, organizadores, etc.), com quantidade e valor unitário")
    _bullet("<b>Fornecedores:</b> serviços terceirizados necessários, com valor e comissão calculada automaticamente")
    _bullet("<b>Assistentes:</b> profissionais auxiliares no projeto, com valores de pagamento definidos")
    _bullet("<b>Outros itens:</b> custos adicionais diversos (transporte, materiais especiais, etc.)")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Relatórios em PDF", st_secao))
    e.append(Paragraph(
        "Para cada proposta, o sistema gera três tipos de relatórios profissionais em PDF no design Navy & Gold:",
        st_texto
    ))
    _bullet("<b>Relatório para o Cliente:</b> proposta formal com os itens, valores e condições — pronto para envio ao cliente")
    _bullet("<b>Relatório Interno:</b> visão completa com margens, custos detalhados e análise de rentabilidade")
    _bullet("<b>Relatório de Fornecedores:</b> lista de todos os fornecedores e serviços envolvidos no projeto")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Registro de Andamentos", st_secao))
    _bullet("Para cada proposta, você pode registrar andamentos descrevendo o progresso do projeto")
    _bullet("Histórico cronológico de todas as etapas, acessível a qualquer momento")
    _bullet("Barra de progresso visual baseada na data de prazo da proposta")
    e.append(Spacer(1, 10))

    e.append(Paragraph("4. Vendas", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O módulo de Vendas controla todos os produtos vendidos para cada cliente. "
        "A principal característica é a <b>geração automática</b> a partir de propostas finalizadas:",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Como Funciona", st_secao))
    _bullet("Quando uma proposta é marcada como <b>Finalizada</b>, todos os produtos cadastrados nela são automaticamente convertidos em registros de venda")
    _bullet("Cada venda é vinculada ao cliente da proposta, mantendo a rastreabilidade completa")
    _bullet("Valores unitários e quantidades são preservados exatamente como definidos na proposta")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Funcionalidades", st_secao))
    _bullet("Visualização de vendas por cliente com cards de resumo (total de itens e valor)")
    _bullet("Detalhamento de cada produto vendido, incluindo proposta de origem")
    _bullet("Geração de PDF de venda para registro ou envio ao cliente")
    _bullet("Cadastro manual de vendas avulsas (independentes de propostas)")
    e.append(Spacer(1, 10))

    e.append(PageBreak())

    e.append(Paragraph("5. Financeiro", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O módulo Financeiro apresenta todas as transações em um painel visual no formato Kanban, "
        "organizado em três colunas para facilitar o acompanhamento do fluxo de caixa:",
        st_texto
    ))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Painel Kanban", st_secao))
    _navy_table([
        ["Coluna", "Descrição"],
        ["💰 A Receber", "Todas as receitas pendentes — valores de propostas finalizadas, vendas de produtos e outros créditos."],
        ["💳 A Pagar", "Todas as despesas pendentes — comissões de fornecedores, pagamentos de assistentes e outros débitos."],
        ["✅ Aprovadas / Pagas", "Transações já quitadas — receitas recebidas e despesas pagas, com data de conclusão."],
    ], col_widths=[110, 360])
    e.append(Spacer(1, 4))
    e.append(Paragraph("Cards de Resumo", st_secao))
    _bullet("No topo do módulo, três cards apresentam: <b>Total a Receber</b>, <b>Total a Pagar</b> e <b>Saldo Projetado</b>")
    _bullet("Os valores são calculados em tempo real com base nas transações ativas")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Funcionalidades", st_secao))
    _bullet("<b>Nova transação:</b> botão dourado para cadastrar receitas ou despesas manualmente")
    _bullet("<b>Filtros:</b> filtre transações por tipo (receita/despesa), período, status ou descrição")
    _bullet("<b>Painel de detalhes:</b> clique em uma transação para ver informações completas e alterar status")
    _bullet("<b>Histórico e análise:</b> gráficos Plotly com evolução financeira e distribuição de receitas vs. despesas")
    e.append(Spacer(1, 4))
    e.append(Paragraph("Geração Automática de Lançamentos", st_secao))
    e.append(Paragraph(
        "Quando uma proposta é finalizada, o sistema cria automaticamente os seguintes lançamentos financeiros:",
        st_texto
    ))
    _sub_bullet("<b>Receita:</b> valor base da proposta (honorários) — lançado como A Receber do cliente")
    _sub_bullet("<b>Receita:</b> valor de cada produto vendido — lançado como A Receber")
    _sub_bullet("<b>Despesa:</b> comissão de cada fornecedor — calculada pelo percentual cadastrado, lançada como A Pagar")
    _sub_bullet("<b>Despesa:</b> pagamento de cada assistente — conforme valor definido na proposta, lançado como A Pagar")
    e.append(Spacer(1, 10))

    e.append(Paragraph("6. Pós-Organização", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O módulo de Pós-Organização permite acompanhar o cliente após a conclusão do projeto, "
        "garantindo satisfação e fidelização:",
        st_texto
    ))
    _bullet("Registro de observações de follow-up após a entrega do projeto")
    _bullet("Acompanhamento de satisfação do cliente")
    _bullet("Histórico de interações pós-projeto para referência futura")
    e.append(Spacer(1, 10))

    e.append(Paragraph("7. Relatórios", st_titulo))
    _gold_line()
    e.append(Paragraph(
        "O módulo de Relatórios oferece análises detalhadas para apoiar decisões estratégicas:",
        st_texto
    ))
    _bullet("Desempenho de vendas por cliente, período e tipo de proposta")
    _bullet("Análise financeira: comparativo receitas vs. despesas, fluxo de caixa, projeções")
    _bullet("Gráficos interativos com filtros dinâmicos")
    _bullet("Exportação de dados para análise externa")
    e.append(Spacer(1, 10))

    e.append(PageBreak())

    e.append(Paragraph("Funcionalidades Avançadas", st_titulo))
    _gold_line()

    e.append(Paragraph("Integração Automática entre Módulos", st_subtitulo))
    e.append(Paragraph(
        "A principal vantagem do Planner Organizer é a integração inteligente. Ao finalizar uma proposta, "
        "o sistema executa automaticamente as seguintes operações:",
        st_texto
    ))
    e.append(Paragraph(
        "<b>1.</b> Cria registros de venda para cada produto listado na proposta<br/>"
        "<b>2.</b> Gera lançamento financeiro de receita (A Receber) com o valor base da proposta<br/>"
        "<b>3.</b> Gera lançamento de receita para cada produto vendido<br/>"
        "<b>4.</b> Calcula e lança a comissão de cada fornecedor (A Pagar) com base no percentual cadastrado<br/>"
        "<b>5.</b> Lança o pagamento de cada assistente envolvido (A Pagar) conforme valor definido",
        st_destaque
    ))
    e.append(Paragraph(
        "Essa automação elimina erros de digitação, evita duplicidade e garante que todas as informações "
        "financeiras estejam sempre sincronizadas com as operações comerciais.",
        st_texto
    ))
    e.append(Spacer(1, 8))

    e.append(Paragraph("Importação em Lote", st_subtitulo))
    _bullet("<b>Importação de clientes:</b> através de arquivo CSV com modelo padronizado, permitindo migrar grandes volumes de dados de outras ferramentas")
    _bullet("<b>Importação de propostas:</b> vincule propostas a clientes existentes via arquivo CSV")
    _bullet("<b>Validação automática:</b> o sistema verifica inconsistências antes de importar, evitando dados duplicados ou incompletos")
    e.append(Spacer(1, 8))

    e.append(Paragraph("Sistema de Backup e Restauração", st_subtitulo))
    _bullet("<b>Backup manual:</b> crie pontos de backup a qualquer momento para proteger seus dados")
    _bullet("<b>Restauração:</b> recupere o sistema a partir de um backup anterior em caso de necessidade")
    _bullet("Os backups incluem todos os cadastros, propostas, vendas e transações financeiras")
    e.append(Spacer(1, 8))

    e.append(Paragraph("Relatórios PDF Profissionais", st_subtitulo))
    _bullet("Todos os relatórios são gerados no padrão visual <b>Navy & Gold</b> com design profissional")
    _bullet("Três tipos de relatório por proposta: Cliente, Interno e Fornecedores")
    _bullet("PDF de vendas por cliente disponível para download direto")
    _bullet("Manual do sistema (este documento) gerado diretamente pela barra lateral")
    e.append(Spacer(1, 8))

    e.append(Paragraph("Seleção Múltipla e Operações em Lote", st_subtitulo))
    _bullet("Seleção individual ou em grupo de registros para exclusão")
    _bullet("Remoção de múltiplos registros com um único clique")
    _bullet("Processo simplificado sem confirmações textuais excessivas")
    e.append(Spacer(1, 8))

    e.append(Paragraph("Controle de Acesso Multi-Tenant", st_subtitulo))
    _bullet("Sistema de autenticação com Firebase Auth")
    _bullet("Cada usuário acessa apenas os dados da sua organização")
    _bullet("Perfis de acesso: usuário padrão e administrador")
    _bullet("Sessão segura com controle de expiração")
    e.append(Spacer(1, 10))

    e.append(PageBreak())

    e.append(Paragraph("Boas Práticas de Uso", st_titulo))
    _gold_line()

    e.append(Paragraph("Fluxo de Trabalho Recomendado", st_subtitulo))
    _bullet("Mantenha o fluxo de propostas sempre atualizado, avançando os status conforme o projeto evolui: <b>Em elaboração → Aguardando aprovação → Aprovada → Em execução → Finalizada</b>")
    _bullet("Finalize as propostas assim que o trabalho for concluído — os lançamentos financeiros e de vendas são gerados automaticamente neste momento")
    _bullet("Consulte o Dashboard regularmente para identificar propostas próximas do prazo e pendências financeiras")
    _bullet("Utilize os andamentos para manter um histórico detalhado de cada projeto")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Cadastros Completos e Atualizados", st_subtitulo))
    _bullet("Mantenha o cadastro de clientes atualizado com telefone, e-mail e endereço corretos")
    _bullet("Cadastre os percentuais de comissão dos fornecedores corretamente — eles são usados no cálculo automático")
    _bullet("Registre todos os assistentes que participam dos projetos, com valores definidos")
    _bullet("Quanto mais completos os cadastros, mais precisos serão os relatórios e cálculos automatizados")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Segurança e Backup", st_subtitulo))
    _bullet("Crie pontos de backup regularmente, especialmente antes de alterações significativas")
    _bullet("Após importações em lote, verifique se os dados foram importados corretamente")
    _bullet("Mantenha suas credenciais de acesso em local seguro e não compartilhe com terceiros")
    e.append(Spacer(1, 6))

    e.append(Paragraph("Monitoramento Financeiro", st_subtitulo))
    _bullet("Utilize o painel Kanban do Financeiro para acompanhar receitas pendentes e despesas a pagar")
    _bullet("Marque as transações como pagas/recebidas conforme ocorrem para manter o saldo atualizado")
    _bullet("Consulte os gráficos de análise para identificar tendências e planejar o fluxo de caixa")
    e.append(Spacer(1, 16))

    _gold_line()
    e.append(Spacer(1, 8))
    e.append(Paragraph(
        "O Planner Organizer foi desenvolvido para simplificar e profissionalizar a gestão do seu negócio "
        "de Personal Organizer. Com processos automatizados e dados integrados, você pode dedicar mais "
        "tempo ao que realmente importa: transformar ambientes e a vida dos seus clientes.",
        st_texto
    ))
    e.append(Spacer(1, 12))
    e.append(Paragraph(
        f"© {datetime.now().year} Planner Organizer — Versão 1.0.4",
        st_rodape
    ))

    doc.build(e, onFirstPage=_first_page, onLaterPages=_header_footer)
    return pdf_path
