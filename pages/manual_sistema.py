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
from reportlab.graphics.shapes import Drawing, Line, Rect, Circle, String
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from utils.design_tokens import CORES_MODULO
from utils.trial import DIAS_TRIAL

# Mesma identidade do app e da landing: azul-marinho, dourado e creme; títulos com serifa
# (a landing usa Cormorant Garamond; no PDF, Times é a serifa disponível sem arquivo de fonte).
# O conteúdo descreve o app como ele é: ao mudar uma tela, mude o capítulo correspondente.
VERSAO = "2.1"

NAVY_RGB = colors.HexColor('#0D1B2A')
GOLD_RGB = colors.HexColor('#C9A84C')
GOLD_DARK_RGB = colors.HexColor('#8A6D12')
GOLD_LIGHT_RGB = colors.HexColor('#FBF5E6')
CREME_RGB = colors.HexColor('#F8F6F1')
GREEN_RGB = colors.HexColor('#2F855A')
CORAL_RGB = colors.HexColor('#D9653B')
BLUE_RGB = colors.HexColor('#3D6BB3')
RED_RGB = colors.HexColor('#C0392B')
WHITE = colors.white
GRAY_TEXT = colors.HexColor('#475467')
GRAY_LIGHT = colors.HexColor('#E4E7EC')
GRAY_BG = colors.HexColor('#F9FAFB')

SERIFA, SERIFA_NEGRITO = 'Times-Roman', 'Times-Bold'
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY_RGB)
    canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(0, h - 31, w, 3, fill=1, stroke=0)
    canvas.setFont(SERIFA, 11)
    canvas.setFillColor(WHITE)
    canvas.drawString(60, h - 20, "Planner Organiza")
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#A0AEC0'))
    canvas.drawRightString(w - 60, h - 19, "Manual do sistema")
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(0, 30, w, 2, fill=1, stroke=0)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(GRAY_TEXT)
    canvas.drawString(60, 16, f"© {datetime.now().year} Planner Organiza — plannerorganiza.com.br")
    canvas.drawRightString(w - 60, 16, f"Página {doc.page}")
    canvas.restoreState()


def _first_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY_RGB)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFont(SERIFA, 40)
    largura = canvas.stringWidth("Planner Organiza", SERIFA, 40)
    x0 = (w - largura - 22) / 2  # quadradinho dourado + nome, centralizados juntos (como o logo do app)
    canvas.setFillColor(GOLD_RGB)
    canvas.roundRect(x0, h / 2 + 116, 11, 11, 2, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.drawString(x0 + 22, h / 2 + 110, "Planner Organiza")
    canvas.setFillColor(GOLD_RGB)
    canvas.rect(w / 2 - 40, h / 2 + 88, 80, 2, fill=1, stroke=0)
    canvas.setFont('Helvetica', 11)
    canvas.drawCentredString(w / 2, h / 2 + 58, "MANUAL DO SISTEMA")
    canvas.setFont(SERIFA, 14)
    canvas.setFillColor(colors.HexColor('#CBD5E1'))
    canvas.drawCentredString(w / 2, h / 2 + 22, "Como usar cada tela, do primeiro cadastro ao pós-organização")
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#94A3B8'))
    hoje = datetime.now()
    canvas.drawCentredString(w / 2, 60, f"Versão {VERSAO}  •  {MESES[hoje.month - 1]} de {hoje.year}")
    canvas.restoreState()


def _draw_status_flow():
    d = Drawing(470, 78)
    d.add(String(235, 66, "Caminho de uma proposta", fontSize=11, fillColor=NAVY_RGB,
                 fontName=SERIFA_NEGRITO, textAnchor='middle'))
    etapas = [("Em aberto", colors.HexColor('#667085')), ("Aprovada", BLUE_RGB),
              ("Em execução", colors.HexColor('#7356BF')), ("Finalizada", GREEN_RGB)]
    box_w, gap = 92, 22
    start_x = (470 - (len(etapas) * box_w + (len(etapas) - 1) * gap)) / 2
    y = 24
    for i, (label, col) in enumerate(etapas):
        x = start_x + i * (box_w + gap)
        d.add(Rect(x, y, box_w, 28, rx=6, ry=6, fillColor=col, strokeColor=col, strokeWidth=0))
        d.add(String(x + box_w / 2, y + 10, label, fontSize=8.5, fillColor=WHITE,
                     fontName='Helvetica-Bold', textAnchor='middle'))
        if i < len(etapas) - 1:
            ax = x + box_w + 3
            d.add(Line(ax, y + 14, ax + gap - 6, y + 14, strokeColor=GOLD_RGB, strokeWidth=1.5))
            d.add(Line(ax + gap - 10, y + 18, ax + gap - 6, y + 14, strokeColor=GOLD_RGB, strokeWidth=1.5))
            d.add(Line(ax + gap - 10, y + 10, ax + gap - 6, y + 14, strokeColor=GOLD_RGB, strokeWidth=1.5))
    d.add(String(start_x + box_w / 2, 8, "ou Recusada", fontSize=7.5, fillColor=RED_RGB,
                 fontName='Helvetica', textAnchor='middle'))
    return d


def _draw_pos_org_timeline():
    d = Drawing(470, 110)
    d.add(String(235, 98, "Retornos automáticos depois do serviço finalizado", fontSize=11,
                 fillColor=NAVY_RGB, fontName=SERIFA_NEGRITO, textAnchor='middle'))
    etapas = [("D+1", "Agradecimento", "mensagem de encerramento"),
              ("D+7", "Acompanhamento", "como a cliente está"),
              ("D+30", "Ajuste fino", "pequenos ajustes"),
              ("D+45", "Feedback", "opinião da experiência"),
              ("D+60", "Continuidade", "serviço contínuo")]
    line_y = 58
    d.add(Line(30, line_y, 440, line_y, strokeColor=GOLD_RGB, strokeWidth=2))
    for i, (dia, nome, desc) in enumerate(etapas):
        cx = 50 + i * 92.5
        d.add(Circle(cx, line_y, 13, fillColor=NAVY_RGB, strokeColor=GOLD_RGB, strokeWidth=1.5))
        d.add(String(cx, line_y - 3, dia, fontSize=7, fillColor=WHITE, fontName='Helvetica-Bold', textAnchor='middle'))
        d.add(String(cx, line_y + 20, nome, fontSize=8, fillColor=NAVY_RGB, fontName='Helvetica-Bold', textAnchor='middle'))
        d.add(String(cx, line_y - 26, desc, fontSize=7, fillColor=GRAY_TEXT, fontName='Helvetica', textAnchor='middle'))
    return d


def _draw_board(titulo, colunas):
    """Quadro de colunas (Financeiro, Vendas). colunas = [(título, cor, [itens])]."""
    d = Drawing(470, 112)
    d.add(String(235, 100, titulo, fontSize=11, fillColor=NAVY_RGB, fontName=SERIFA_NEGRITO, textAnchor='middle'))
    col_w, gap = 140, 14
    start_x = (470 - (len(colunas) * col_w + (len(colunas) - 1) * gap)) / 2
    for i, (nome, cor, itens) in enumerate(colunas):
        x = start_x + i * (col_w + gap)
        d.add(Rect(x, 0, col_w, 84, rx=6, ry=6, fillColor=GRAY_BG, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
        d.add(Rect(x, 66, col_w, 18, rx=6, ry=6, fillColor=cor, strokeColor=cor, strokeWidth=0))
        d.add(Rect(x, 66, col_w, 8, fillColor=cor, strokeColor=cor, strokeWidth=0))
        d.add(String(x + col_w / 2, 71, nome, fontSize=8, fillColor=WHITE, fontName='Helvetica-Bold', textAnchor='middle'))
        for j, item in enumerate(itens):
            iy = 46 - j * 18
            d.add(Rect(x + 6, iy, col_w - 12, 15, rx=3, ry=3, fillColor=WHITE, strokeColor=GRAY_LIGHT, strokeWidth=0.3))
            d.add(String(x + 12, iy + 4, item, fontSize=7.5, fillColor=GRAY_TEXT, fontName='Helvetica'))
    return d


def _draw_inicio_cards():
    d = Drawing(470, 82)
    d.add(String(235, 70, "Os quatro números do Início", fontSize=11, fillColor=NAVY_RGB,
                 fontName=SERIFA_NEGRITO, textAnchor='middle'))
    cards = [("LUCRO DO MÊS", "R$ 6.200", NAVY_RGB, True), ("A RECEBER", "R$ 4.800", GREEN_RGB, False),
             ("A PAGAR", "R$ 1.350", CORAL_RGB, False), ("CONVERSÃO", "75%", BLUE_RGB, False)]
    card_w, gap = 108, 12
    start_x = (470 - (4 * card_w + 3 * gap)) / 2
    for i, (rot, val, cor, destaque) in enumerate(cards):
        x = start_x + i * (card_w + gap)
        fundo = NAVY_RGB if destaque else WHITE
        d.add(Rect(x, 0, card_w, 56, rx=6, ry=6, fillColor=fundo, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
        d.add(Rect(x, 53, card_w, 3, fillColor=GOLD_RGB if destaque else cor, strokeWidth=0))
        d.add(String(x + 10, 36, rot, fontSize=6.5, fillColor=GOLD_RGB if destaque else cor, fontName='Helvetica-Bold'))
        d.add(String(x + 10, 14, val, fontSize=14, fillColor=WHITE if destaque else NAVY_RGB, fontName='Helvetica-Bold'))
    return d


def _draw_integracao():
    d = Drawing(470, 128)
    d.add(String(235, 116, "O que o sistema lança sozinho", fontSize=11, fillColor=NAVY_RGB,
                 fontName=SERIFA_NEGRITO, textAnchor='middle'))
    blocos = [
        (20, "Ao aprovar", BLUE_RGB, ["Receita a receber: valor − sinal", "Sinal: receita já recebida"]),
        (245, "Ao finalizar", GREEN_RGB, ["Produtos viram venda (a receber)", "Outros itens: receita",
                                          "Comissão do fornecedor: receita", "Assistentes: despesa a pagar",
                                          "Retornos de pós-organização"]),
    ]
    for x, titulo, cor, itens in blocos:
        d.add(Rect(x, 0, 205, 104, rx=6, ry=6, fillColor=GRAY_BG, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
        d.add(Rect(x, 86, 205, 18, rx=6, ry=6, fillColor=cor, strokeWidth=0))
        d.add(Rect(x, 86, 205, 8, fillColor=cor, strokeWidth=0))
        d.add(String(x + 102, 91, titulo, fontSize=8.5, fillColor=WHITE, fontName='Helvetica-Bold', textAnchor='middle'))
        for j, item in enumerate(itens):
            d.add(String(x + 12, 70 - j * 15, "•  " + item, fontSize=7.8, fillColor=GRAY_TEXT, fontName='Helvetica'))
    return d


def _draw_botoes():
    d = Drawing(470, 128)
    d.add(String(235, 116, "Cada cor de botão tem um papel", fontSize=11, fillColor=NAVY_RGB,
                 fontName=SERIFA_NEGRITO, textAnchor='middle'))
    papeis = [
        ("Nova venda", GOLD_RGB, NAVY_RGB, None, "Criar: a chamada da tela"),
        ("Salvar", NAVY_RGB, WHITE, None, "Gravar ou confirmar"),
        ("Editar", colors.HexColor('#EAF0F8'), colors.HexColor('#1F3A60'), colors.HexColor('#C7D3E6'), "Editar, reabrir, duplicar"),
        ("Baixar PDF", GOLD_LIGHT_RGB, colors.HexColor('#5C4712'), colors.HexColor('#E3CF97'), "Gerar ou baixar documento"),
        ("Voltar", WHITE, GRAY_TEXT, colors.HexColor('#D0D5DD'), "Cancelar, voltar, abrir"),
        ("Excluir", RED_RGB, WHITE, None, "Apagar ou cancelar (pede confirmação)"),
    ]
    for i, (rot, fundo, texto, borda, desc) in enumerate(papeis):
        col, lin = i % 2, i // 2
        x, y = 10 + col * 235, 78 - lin * 34
        d.add(Rect(x, y, 84, 22, rx=5, ry=5, fillColor=fundo, strokeColor=borda or fundo, strokeWidth=0.8 if borda else 0))
        d.add(String(x + 42, y + 7.5, rot, fontSize=8, fillColor=texto, fontName='Helvetica-Bold', textAnchor='middle'))
        d.add(String(x + 94, y + 7.5, desc, fontSize=8, fillColor=GRAY_TEXT, fontName='Helvetica'))
    return d


def gerar_manual_sistema(verificar_auth=True):
    if verificar_auth:
        from utils.auth_guard import require_auth
        require_auth()
    pdf_dir = "pdfs"
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    pdf_path = os.path.join(pdf_dir, "Manual_Planner_Organiza.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=60, leftMargin=60, topMargin=52, bottomMargin=50,
                            title="Manual do Planner Organiza", author="Planner Organiza")

    estilos = getSampleStyleSheet()
    st_titulo = ParagraphStyle('ManualTitulo', parent=estilos['Heading1'], fontSize=24, leading=28,
                               textColor=NAVY_RGB, fontName=SERIFA, spaceAfter=4, spaceBefore=18, alignment=TA_LEFT)
    st_secao = ParagraphStyle('ManualSecao', parent=estilos['Heading3'], fontSize=11.5, textColor=NAVY_RGB,
                              fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=10)
    st_texto = ParagraphStyle('ManualTexto', parent=estilos['Normal'], fontSize=10, textColor=GRAY_TEXT,
                              leading=15, spaceAfter=5, alignment=TA_JUSTIFY)
    st_bullet = ParagraphStyle('ManualBullet', parent=st_texto, leftIndent=16, bulletIndent=5, spaceAfter=3,
                               alignment=TA_LEFT)
    st_destaque = ParagraphStyle('ManualDestaque', parent=st_texto, backColor=GOLD_LIGHT_RGB,
                                 borderPadding=(8, 10, 8, 10), leftIndent=10, rightIndent=10,
                                 spaceAfter=10, spaceBefore=8, textColor=NAVY_RGB)
    st_celula = ParagraphStyle('ManualCelula', parent=st_texto, fontSize=9, leading=12.5, spaceAfter=0,
                               alignment=TA_LEFT)
    st_celula_b = ParagraphStyle('ManualCelulaB', parent=st_celula, fontName='Helvetica-Bold', textColor=NAVY_RGB)
    st_rodape = ParagraphStyle('ManualRodape', parent=estilos['Normal'], fontSize=8, textColor=colors.grey,
                               alignment=TA_CENTER)

    e = []

    def titulo(texto, modulo=None):
        """Título de capítulo com o filete na cor do módulo (a mesma do menu e das telas)."""
        cor = colors.HexColor(CORES_MODULO.get(modulo, '#C9A84C'))
        bloco = [Paragraph(texto, st_titulo)]
        d = Drawing(470, 6)
        d.add(Rect(0, 2, 40, 3, fillColor=cor, strokeWidth=0))
        d.add(Line(46, 3.5, 470, 3.5, strokeColor=GRAY_LIGHT, strokeWidth=0.5))
        bloco += [d, Spacer(1, 8)]
        return bloco

    def capitulo(texto, modulo=None, intro=None, junto=None):
        """Título + introdução (+ o primeiro desenho, em `junto`) sempre na mesma página."""
        bloco = titulo(texto, modulo)
        if intro:
            bloco.append(Paragraph(intro, st_texto))
        if junto is not None:
            bloco.append(junto)
        e.append(KeepTogether(bloco))

    def secao(texto):
        e.append(Paragraph(texto, st_secao))

    def bullet(texto):
        e.append(Paragraph(f"<bullet>&bull;</bullet> {texto}", st_bullet))

    def texto(t):
        e.append(Paragraph(t, st_texto))

    def destaque(t):
        e.append(Paragraph(t, st_destaque))

    def tabela(linhas, larguras, cabecalho=True):
        dados = [[Paragraph(f'<font color="#C9A84C"><b>{c}</b></font>', st_celula) if (cabecalho and i == 0)
                  else Paragraph(c, st_celula_b if j == 0 else st_celula)
                  for j, c in enumerate(l)] for i, l in enumerate(linhas)]
        t = Table(dados, colWidths=larguras, repeatRows=1 if cabecalho else 0)
        estilo = [('GRID', (0, 0), (-1, -1), 0.4, GRAY_LIGHT), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                  ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                  ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                  ('ROWBACKGROUNDS', (0, 1 if cabecalho else 0), (-1, -1), [WHITE, CREME_RGB])]
        if cabecalho:
            estilo += [('BACKGROUND', (0, 0), (-1, 0), NAVY_RGB)]
        t.setStyle(TableStyle(estilo))
        e.append(t)
        e.append(Spacer(1, 10))

    e.append(PageBreak())

    # ── APRESENTAÇÃO ───────────────────────────────────────────────────
    capitulo("Bem-vinda ao Planner Organiza", intro=(
        "O Planner Organiza reúne num só lugar o que uma Personal Organizer usa no dia a dia: "
        "agenda, clientes, propostas, vendas de produtos, financeiro, MEI e os retornos depois do serviço. "
        "Este manual segue o menu do sistema, na mesma ordem e com os mesmos nomes."))
    destaque("<b>Importante:</b> o Planner Organiza organiza o seu negócio, mas <b>não é contador e não substitui "
             "um</b>. Os números de impostos (DAS, limite do MEI, Simples Nacional, declarações) são estimativas feitas "
             "com o que você lança. Em caso de dúvida, procure um contador.")
    secao("O menu")
    tabela([
        ["Menu", "Para que serve"],
        ['<font color="%s">■</font> Início' % CORES_MODULO["Dashboard"], "Os números do mês e tudo o que precisa de atenção hoje."],
        ['<font color="%s">■</font> Agenda' % CORES_MODULO["Agenda"], "Compromissos e tudo o que tem data: serviços, retornos e contas."],
        ['<font color="%s">■</font> Clientes' % CORES_MODULO["Clientes"], "Cadastro, busca e importação de clientes."],
        ['<font color="%s">■</font> Propostas' % CORES_MODULO["Propostas"], "Do orçamento à finalização do serviço, com os PDFs para a cliente."],
        ['<font color="%s">■</font> Precificação' % CORES_MODULO["Precificacao"], "Quanto vale a sua hora e quanto cobrar por um projeto."],
        ['<font color="%s">■</font> Vendas' % CORES_MODULO["Vendas"], "Venda de produtos, recebimento, parcelas, estoque e lucro."],
        ['<font color="%s">■</font> Pós-organização' % CORES_MODULO["PosOrganizacao"], "Retornos para a cliente depois do serviço, com mensagem pronta no WhatsApp."],
        ['<font color="%s">■</font> Financeiro' % CORES_MODULO["Financeiro"], "O mês em números, contas a receber e a pagar e a aba MEI (DAS e declaração)."],
        ['<font color="%s">■</font> Relatórios' % CORES_MODULO["Relatórios"], "Resultado, clientes, propostas e trabalhos por período, com Excel."],
        ['<font color="%s">■</font> Cadastros' % CORES_MODULO["Cadastros"], "Fornecedores, parceiros, assistentes e produtos."],
        ['<font color="%s">■</font> Perfil e marca' % CORES_MODULO["Perfil"], "Seu logotipo, cores e contatos em todos os PDFs."],
        ['<font color="%s">■</font> Plano e cobrança' % CORES_MODULO["Plano"], "Teste grátis, assinatura e pagamentos."],
    ], [130, 340])
    texto("Cada módulo tem uma cor, que aparece no ícone do menu, no filete sob o título da tela e neste manual.")
    texto("<b>Tutorial rápido</b>: na primeira entrada, uma janela mostra em 12 passos o que cada parte do menu faz. "
          "Para rever, clique em <b>Tutorial rápido</b>, no fim do menu.")
    e.append(Spacer(1, 6))
    e.append(_draw_botoes())
    e.append(Spacer(1, 4))
    texto("<b>No celular</b>, uma barra embaixo leva ao Início, às Propostas e ao Financeiro; o botão "
          "<b>+</b> cria uma proposta, uma cliente, um compromisso ou um lançamento, e <b>Menu</b> abre o menu completo.")
    texto("<b>App para Android</b>: o Planner Organiza também está na Google Play. O link fica na tela de entrada e "
          "no menu, em <b>App para Android</b>.")

    # ── INÍCIO ─────────────────────────────────────────────────────────
    capitulo("Início", "Dashboard",
             "A primeira tela depois de entrar. Mostra como está o mês e o que precisa ser feito hoje.",
             junto=_draw_inicio_cards())
    e.append(Spacer(1, 6))
    bullet("<b>Lucro do mês</b>: o que entrou menos o que saiu no mês, pela data em que o dinheiro entrou ou saiu.")
    bullet("<b>A receber</b> e <b>A pagar</b>: o que está em aberto, com destaque para o que está atrasado ou vence em 7 dias.")
    bullet("<b>Conversão</b>: das propostas respondidas nos últimos 90 dias, quantas foram fechadas.")
    secao("Para fazer")
    texto("Uma lista do dia, cada item com ação pronta: retornos de pós-organização (com botão do WhatsApp, "
          "<b>Feito</b> e <b>Adiar 3 dias</b>), recebimentos e pagamentos vencendo, propostas paradas que pedem "
          "follow-up e aniversários de clientes.")
    secao("Funil e propostas em andamento")
    texto("O funil mostra propostas enviadas, fechadas e concluídas nos últimos 90 dias. Ao lado, as propostas "
          "aprovadas e em execução. Numa conta nova, o Início mostra os <b>Primeiros passos</b>: colocar a "
          "marca, cadastrar a primeira cliente e criar a primeira proposta.")

    # ── AGENDA ─────────────────────────────────────────────────────────
    capitulo("Agenda", "Agenda",
             "Seus compromissos e tudo o que já tem data no sistema, por semana ou por mês.")
    bullet("<b>Novo compromisso</b> (botão dourado): o que é, dia, hora, cliente, local e valor. Serve para "
           "diárias, visitas de orçamento e reuniões.")
    bullet("<b>Com valor</b>, o compromisso entra sozinho em <b>A receber</b> no Financeiro, na data dele. Mudar o "
           "valor ou a data muda o lançamento; excluir o compromisso tira o que ainda não foi recebido.")
    bullet("Clique no compromisso para <b>Recebi</b>, <b>Editar</b> ou <b>Excluir</b>.")
    bullet("A agenda também mostra, cada um com sua cor: aniversários das clientes (com o símbolo do WhatsApp para "
           "dar os parabéns), início e fim dos serviços aprovados ou em execução, retornos de pós-organização e "
           "contas a receber e a pagar que vencem no período.")
    destaque("<b>Assistente de organizer?</b> Cadastre em <b>Clientes</b> as organizers que contratam você e lance "
             "cada diária como compromisso: a agenda e o que você tem a receber ficam no mesmo lugar.")

    # ── CLIENTES ───────────────────────────────────────────────────────
    capitulo("Clientes", "Clientes", "A base de clientes usada em propostas, vendas e mensagens.")
    bullet("<b>Nova cliente</b> (botão dourado): nome e telefone já bastam; o resto (CPF, endereço, aniversário, "
           "origem, observações) pode vir depois.")
    bullet("<b>Busca</b> por nome, telefone, cidade ou bairro, e tabela com todos os dados para conferir e editar.")
    bullet("<b>Origem da cliente</b> (indicação, Instagram etc.) alimenta o relatório de onde vêm as clientes.")
    bullet("<b>Importar planilha</b>: baixe o modelo, preencha e envie (Excel ou CSV).")
    bullet("<b>Excluir múltiplos</b>: marque várias clientes e exclua de uma vez, com confirmação.")

    # ── PROPOSTAS ──────────────────────────────────────────────────────
    capitulo("Propostas", "Propostas",
             "O centro do trabalho: do orçamento à finalização, com os documentos para a cliente.")
    e.append(_draw_status_flow())
    secao("Criar")
    bullet("<b>Nova proposta</b>: cliente, descrição do serviço (ambientes e itens), valor, prazo e data de início. "
           "Se a cliente já pagou um sinal, informe-o.")
    bullet("<b>Cadastro retroativo</b>: registra trabalhos antigos já aprovados, em execução ou finalizados.")
    secao("Aprovar")
    texto("Na proposta em aberto, confira o <b>sinal / entrada</b> e clique em <b>Aprovar proposta</b>. O sistema "
          "lança no Financeiro a receita a receber com o saldo (valor menos sinal) e o sinal como receita já "
          "recebida. Mudar valor ou sinal depois, em <b>Editar serviço</b>, ajusta esses lançamentos.")
    secao("Executar")
    texto("Em <b>Itens e custos</b> entram os produtos a comprar, os fornecedores (com a sua comissão), as assistentes "
          "e outros itens. Registre <b>andamentos</b> para guardar o histórico; a barra de prazo mostra quantos dias "
          "faltam. Quando terminar, clique em <b>Finalizar projeto</b>.")
    e.append(_draw_integracao())
    secao("Documentos")
    bullet("<b>Baixar proposta em PDF</b>: a proposta para enviar à cliente, com seu logotipo e suas cores.")
    bullet("Na proposta finalizada: <b>relatório do cliente</b>, <b>relatório interno</b> (margens e custos, só para "
           "você), <b>relatório de fornecedores</b> e <b>relatório de produtos</b>. Um clique gera e baixa.")
    secao("Outras ações")
    bullet("<b>Reabrir proposta</b>: volta para Em execução; os retornos de pós-organização somem até ela ser finalizada de novo.")
    bullet("<b>Duplicar proposta</b>: cria uma nova proposta em aberto a partir de outra. <b>Excluir</b> pede confirmação.")

    # ── PRECIFICAÇÃO ───────────────────────────────────────────────────
    capitulo("Precificação", "Precificacao",
             "Para quem está começando ou quer rever os preços: a conta feita com os seus números.")
    bullet("<b>Sua hora</b>: quanto quer ganhar por mês, seus custos fixos (DAS, transporte, ferramentas) e quantas "
           "horas consegue atender. O sistema mostra a <b>hora mínima</b> (abaixo dela a conta do mês não fecha) e a "
           "<b>hora sugerida</b>, com a sua margem. <b>Salvar meus números</b> guarda tudo para a próxima vez.")
    bullet("<b>Preço de um projeto</b>: marque os ambientes, a complexidade, as assistentes e os custos do projeto. "
           "Aparecem o preço sugerido, o preço mínimo, o sinal e quanto fica para você.")
    texto("As horas por ambiente são só um ponto de partida: ajuste pela sua experiência. Para saber quais impostos "
          "entram na conta e qual alíquota usar, em caso de dúvida, procure um contador.")

    # ── VENDAS ─────────────────────────────────────────────────────────
    capitulo("Vendas", "Vendas", "Venda de produtos (caixas, cabides, organizadores), avulsa ou vinda de uma proposta.")
    bullet("<b>Nova venda</b>: cliente, produtos e quantidades. O estoque é baixado e o custo do produto fica gravado "
           "na venda, para o lucro não mudar se o custo mudar depois.")
    bullet("<b>Pagamento</b>: recebido na hora (entra no Financeiro na data da venda) ou a receber, com entrada e "
           "parcelas mensais.")
    bullet("<b>Quadro</b> com as colunas Paga, A receber e Cancelada, de todas as datas; o período escolhido vale para "
           "os números do topo. A lista <b>Todas as vendas</b> mostra cada venda com o nome da cliente: clique na "
           "linha para abrir. A busca pelo nome procura em todas as datas.")
    bullet("<b>Detalhes da venda</b>: editar itens (quantidade e preço são gravados em <b>Salvar e fechar</b>), "
           "baixar o PDF da venda ou cancelar. Cancelar devolve o estoque e tira do Financeiro o que faltava receber.")
    bullet("<b>Análise por período</b>: vendas, receita, lucro, margem e ticket médio por dia, semana, mês, trimestre ou ano.")

    # ── PÓS-ORGANIZAÇÃO ───────────────────────────────────────────────
    capitulo("Pós-organização", "PosOrganizacao",
             "Quando uma proposta é finalizada, o sistema agenda cinco retornos para a cliente. Eles aparecem no "
             "Início no dia certo, com a mensagem pronta para enviar pelo WhatsApp.")
    e.append(_draw_pos_org_timeline())
    tabela([
        ["Retorno", "Quando", "Objetivo"],
        ["Agradecimento", "D+1", "Mensagem de encerramento, reforçando o cuidado com a cliente."],
        ["Acompanhamento", "D+7", "Saber como a cliente está se sentindo com a organização no dia a dia."],
        ["Ajuste fino", "D+30", "Propor pequenos ajustes depois do uso, como cuidado incluído no serviço."],
        ["Feedback", "D+45", "Colher a opinião sobre a experiência."],
        ["Continuidade", "D+60", "Oferecer o acompanhamento periódico pago."],
        ["Retorno técnico", "Quando precisar", "Visita técnica agendada por você."],
    ], [110, 80, 280])
    texto("Cada retorno pode ser marcado como <b>Feito</b> ou <b>adiado 3 dias</b>. Os retornos só valem para serviço "
          "finalizado: se a proposta for reaberta, eles saem da lista até a nova finalização, que remarca as datas.")
    destaque("<b>Dica:</b> no Ajuste fino (D+30), não fale em desconto: apresente como cuidado incluído. É o "
             "momento de preparar a oferta de acompanhamento periódico da Continuidade (D+60).")

    # ── FINANCEIRO ─────────────────────────────────────────────────────
    capitulo("Financeiro", "Financeiro", "O dinheiro do negócio, pela data em que entrou ou saiu.")
    secao("O mês em números")
    texto("<b>Entrou</b>, <b>Gastou</b>, <b>Retirado para você</b> (o que foi para a sua conta pessoal) e <b>Sobrou</b>, "
          "com <b>de onde veio</b> e <b>para onde foi</b> o dinheiro por categoria. Para quem é MEI, o "
          "<b>limite do MEI</b> mostra quanto do faturamento do ano já foi usado.")
    texto("O Financeiro tem duas abas: <b>Lançamentos</b> (tudo o que está abaixo) e <b>MEI</b>, que vira "
          "<b>Impostos</b> para quem não é MEI.")
    e.append(_draw_board("O quadro do Financeiro", [
        ("A receber", GREEN_RGB, ["Propostas aprovadas", "Vendas e parcelas", "Comissões"]),
        ("A pagar", CORAL_RGB, ["Assistentes", "Contas e fornecedores", "Lançamentos manuais"]),
        ("Recebidas e pagas", colors.HexColor('#667085'), ["Receitas recebidas", "Despesas pagas", "Histórico"]),
    ]))
    e.append(Spacer(1, 4))
    bullet("<b>Novo lançamento</b> (botão dourado): receita ou despesa feita fora das propostas e vendas.")
    bullet("Clique num cartão para ver os detalhes: <b>Receber</b> ou <b>Pagar</b> marca a data, <b>Editar</b> muda os "
           "dados e <b>Excluir</b> pede confirmação.")
    bullet("<b>Histórico financeiro</b> com filtros e <b>Últimos 6 meses</b> com a evolução do que entrou e saiu.")
    secao("Aba MEI")
    destaque("Tudo o que esta aba mostra é estimativa, para você se organizar. O app não é contador: em caso de "
             "dúvida sobre impostos, enquadramento ou declarações, procure um contador.")
    bullet("<b>Limite do ano</b>: quanto já foi faturado (só o que foi recebido) dos R$ 81 mil e a projeção para o "
           "ano no ritmo atual.")
    bullet("<b>DAS mês a mês</b>: pago, a vencer, atrasado ou futuro. O DAS de cada mês vence no dia 20 do mês "
           "seguinte. <b>Lançar DAS pago</b> registra o pagamento; <b>Gerar a guia do DAS</b> abre o PGMEI da Receita.")
    bullet("<b>Declaração anual (DASN-SIMEI)</b>: o prazo (31 de maio) e a receita bruta do ano separada em serviços "
           "e venda de produtos, como a declaração pede.")
    secao("Quem não é MEI")
    texto("No alto da aba, em <b>Sua empresa é</b>, escolha o tipo de empresa. A escolha fica guardada.")
    bullet("<b>Simples Nacional (ME)</b>: receita dos últimos 12 meses, alíquota efetiva (Anexo III, ou a que a "
           "contadora informar) e o DAS estimado de cada mês, com pago, a vencer ou atrasado. Mês sem receita não "
           "tem DAS. O valor oficial sai do PGDAS-D, que abre por um botão.")
    bullet("<b>Outro regime ou autônoma</b>: o que entrou e os impostos pagos mês a mês, para conferir com a contadora.")

    # ── RELATÓRIOS ─────────────────────────────────────────────────────
    capitulo("Relatórios", "Relatórios",
             "Escolha um período e compare com o anterior ou com o mesmo período do ano passado.")
    tabela([
        ["Aba", "O que mostra"],
        ["Resultado", "Faturamento, custos, despesas, lucro e margem, com o demonstrativo e as categorias."],
        ["Clientes", "Clientes atendidas, as que voltam, valor por cliente, de onde vêm e dependência das maiores."],
        ["Propostas", "Propostas feitas, taxa de fechamento, tempo para fechar, por tipo e por mês."],
        ["Trabalhos", "Lucro e margem de cada trabalho fechado, com os custos ligados a ele."],
        ["Próximos meses", "O que entra e sai nos próximos 30 dias e as propostas aguardando resposta."],
    ], [110, 360])
    texto("<b>Baixar este relatório em Excel</b> gera uma planilha já formatada, com uma aba por tabela, valores em "
          "R$ e percentuais, filtro e cabeçalho fixo, pronta para enviar ao contador. Os relatórios são gerenciais e não "
          "substituem a contabilidade da empresa.")

    # ── CADASTROS ──────────────────────────────────────────────────────
    capitulo("Cadastros", "Cadastros", "As listas usadas dentro das propostas e vendas. Cada uma pode ser importada de planilha.")
    bullet("<b>Fornecedores</b>: contato e percentual de comissão. A comissão entra como receita sua quando a proposta é finalizada.")
    bullet("<b>Parceiros</b>: quem indica clientes ou trabalha junto com você.")
    bullet("<b>Assistentes</b>: a equipe. O valor de cada assistente na proposta vira despesa a pagar ao finalizar.")
    bullet("<b>Produtos</b>: preço de custo, preço de venda e estoque, usados nas vendas e nas propostas.")

    # ── PERFIL E MARCA / PLANO ─────────────────────────────────────────
    capitulo("Perfil e marca", "Perfil",
             "Sua marca em todos os documentos: logotipo, cores, nome da empresa, CNPJ e contatos. A prévia mostra o "
             "cabeçalho e <b>Gerar PDF de exemplo</b> mostra uma proposta pronta antes de enviar a uma cliente.")
    capitulo("Plano e cobrança", "Plano",
             f"Toda conta começa com <b>{DIAS_TRIAL} dias grátis</b>, com tudo liberado e sem cartão. Depois, escolha o "
             "plano <b>mensal (R$ 39,90)</b> ou <b>anual (R$ 297, o equivalente a R$ 24,75 por mês)</b>, com acesso "
             "completo nos dois. Nesta tela também ficam o portal de pagamentos, para trocar o cartão, ver as "
             "faturas ou cancelar.")
    texto("<b>Quando o teste grátis termina</b> sem assinatura, a conta entra em <b>modo consulta</b>: você continua "
          "entrando e vendo tudo o que cadastrou, mas não cadastra, não edita e não gera PDFs. Um aviso no topo das "
          "telas leva aos planos; ao assinar, tudo volta a ser liberado na hora.")

    # ── BOAS PRÁTICAS ──────────────────────────────────────────────────
    capitulo("Boas práticas")
    bullet("Coloque sua marca em <b>Perfil e marca</b> antes de enviar a primeira proposta.")
    bullet("Aprove a proposta no sistema assim que a cliente aceitar, com o sinal: o Financeiro fica certo desde o início.")
    bullet("Finalize o projeto quando terminar: vendas, comissões, pagamentos e retornos são lançados sozinhos.")
    bullet("Abra o <b>Início</b> todo dia e resolva a lista <b>Para fazer</b>; na <b>Agenda</b>, veja a semana.")
    bullet("Sendo MEI, lance o DAS todo mês e confira a aba <b>MEI</b> antes de 31 de maio.")
    bullet("Marque recebimentos e pagamentos no Financeiro para o lucro e o saldo baterem com o banco.")
    bullet("Uma vez por mês, veja os <b>Relatórios</b> e baixe o Excel para o contador.")
    bullet("Impostos, enquadramento (MEI, Simples) e declarações: o app ajuda a acompanhar, mas a palavra final é "
           "do contador. Em caso de dúvida, procure um.")
    e.append(Spacer(1, 14))
    texto("Dúvidas ou sugestões: <b>contato@plannerorganiza.com.br</b> ou o WhatsApp do suporte, em "
          "plannerorganiza.com.br.")
    e.append(Spacer(1, 10))
    e.append(Paragraph(f"© {datetime.now().year} Planner Organiza — Versão {VERSAO}", st_rodape))

    doc.build(e, onFirstPage=_first_page, onLaterPages=_header_footer)
    return pdf_path
