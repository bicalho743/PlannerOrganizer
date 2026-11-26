from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "/tmp/claude-0/-home-user/ac9bca1e-440f-585e-897d-28876c56361c/scratchpad/servicos/Servicos_e_custos_Candeia_Tec_2026-11-24.xlsx"
NAVY, GOLD, CREME = "0D1B2A", "C9A84C", "FBF6E9"
H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor=NAVY)
T = Font(bold=True, size=14, color=NAVY)
fino = Side(style="thin", color="E3D9C2"); B = Border(left=fino, right=fino, top=fino, bottom=fino)
COR = {"Verificado": "D9F2E3", "Estimado": "FFF3CD", "A confirmar": "F8D7DA"}
wb = Workbook()

# ---------- Parâmetros ----------
p = wb.active; p.title = "Leia primeiro"
p["A1"] = "Serviços, custos e gargalos — Candeia Tec / Planner Organiza"; p["A1"].font = T
linhas = [
    "Levantamento de 24/11/2026, feito lendo as contas conectadas (Render, RevenueCat, Expo, Codemagic, Supabase,",
    "Meta Ads, ElevenLabs, Kairogen, Viral, Windsor) e o código dos sistemas.",
    "",
    "Coluna \"Situação do dado\":",
    "  Verificado  = lido na conta hoje (plano, saldo, gasto).",
    "  Estimado    = preço de tabela do serviço; confira na fatura e corrija a coluna Valor.",
    "  A confirmar = não consigo ver daqui; preencha o plano e o valor.",
    "",
    "Os totais recalculam sozinhos quando você muda Valor, Moeda ou a cotação abaixo.",
]
for i, t in enumerate(linhas, 3): p[f"A{i}"] = t
p["A14"] = "Cotação do dólar (R$ por US$)"; p["A14"].font = Font(bold=True)
p["B14"] = 5.40; p["B14"].number_format = '"R$" #,##0.00'; p["B14"].fill = PatternFill("solid", fgColor="FFF3CD")
p["C14"] = "← edite se quiser"
p.column_dimensions["A"].width = 110; p.column_dimensions["B"].width = 14
COT = "'Leia primeiro'!$B$14"

def tabela(ws, cab, larguras, dados, linha0=3):
    for j, (c, w) in enumerate(zip(cab, larguras), 1):
        cel = ws.cell(row=linha0, column=j, value=c); cel.font = H; cel.fill = HF
        cel.alignment = Alignment(wrap_text=True, vertical="center"); cel.border = B
        ws.column_dimensions[get_column_letter(j)].width = w
    for i, linha in enumerate(dados, linha0 + 1):
        for j, v in enumerate(linha, 1):
            cel = ws.cell(row=i, column=j, value=v); cel.border = B
            cel.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = ws.cell(row=linha0 + 1, column=3)
    ws.auto_filter.ref = f"A{linha0}:{get_column_letter(len(cab))}{linha0 + len(dados)}"
    return linha0 + len(dados)

# ---------- Serviços ----------
s = wb.create_sheet("Serviços")
s["A1"] = "Todos os serviços em uso"; s["A1"].font = T
cab = ["Área", "Serviço", "Para que serve", "Marca / app", "Plano hoje", "Moeda", "Valor", "Cobrança",
       "Custo mensal (R$)", "Situação do dado", "Gargalo / observação"]
M = "Mensal"; A = "Anual"; U = "Única"; P = "Por uso / % da venda"
d = [
 # Infra do Planner
 ["Servidores", "Render · PlannerOrganizer", "Site do sistema (app.plannerorganiza.com.br)", "Planner", "Starter", "USD", 7, M, None, "Estimado", "Reinicia ~2 min a cada publicação. Servidor nos EUA (Virgínia): mais lento para quem está no Brasil."],
 ["Servidores", "Render · plannerorganiza-api", "API do app (celular)", "Planner", "0,5 CPU / 512 MB", "USD", 7, M, None, "Estimado", "Mesmo servidor nos EUA."],
 ["Servidores", "Render · Pagina_de_vendas_planner", "Landing plannerorganiza.com.br", "Planner", "0,5 CPU / 512 MB", "USD", 7, M, None, "Estimado", "Erro na chave da Brevo nos registros de 24/11 (caractere inválido)."],
 ["Servidores", "Render · PlannerOrganizer_db", "Banco de dados (Postgres)", "Planner", "Basic 256 MB, disco 1 GB", "USD", 6, M, None, "Estimado", "Banco pequeno (256 MB de memória, 1 GB de disco). Hoje basta; vira gargalo com mais clientes."],
 ["Servidores", "Render · plannerorganizer-teste", "Cópia de teste do site", "Planner", "Free", "USD", 0, M, None, "Verificado", "Sobra: pode ser apagado."],
 ["Servidores", "Render · Contrato-facil", "Sistema antigo", "Contrato Fácil", "Suspenso", "USD", 0, M, None, "Verificado", "Suspenso: não cobra. Apagar se não for voltar."],
 ["Servidores", "Render · sites Enxoval em Dia e Meu Studio em Dia", "Sites estáticos", "Enxoval / Studio", "Free", "USD", 0, M, None, "Verificado", ""],
 ["Servidores", "Render · workspace", "Conta do Render", "Todas", "A confirmar (Hobby ou Professional)", "USD", 0, M, None, "A confirmar", "Se for Professional, ~US$ 19 por usuário/mês."],
 ["Login e dados", "Firebase (planner-organizer-68a23)", "Login das contas, Realtime DB antigo", "Planner", "A confirmar (Spark grátis ou Blaze)", "USD", 0, M, None, "A confirmar", "Leituras do Realtime DB dão erro 401 nos registros (sobra de código antigo)."],
 ["Login e dados", "Supabase (org Solano Bicalho)", "Candeia CRM e Financeiro_Solano (ativos); Tâmara_whatsapp_bot e Livro_caixa_Tamara (parados)", "CRM / financeiro", "A confirmar", "USD", 0, M, None, "A confirmar", "Plano grátis permite só 2 projetos ativos; já são 2. Um 3º exige o Pro (~US$ 25/mês)."],
 ["Apps", "Expo / EAS", "Builds e envio do app às lojas", "Planner e apps Expo", "Starter (ativo)", "USD", 19, M, None, "Estimado", "Plano verificado; valor de tabela."],
 ["Apps", "Codemagic", "Builds iOS dos apps Capacitor e scripts do App Store Connect", "Todos os apps", "Sem Linux, Mac mini M2", "USD", 0, P, None, "A confirmar", "1 build por vez (fila). Cobra por minuto de máquina Mac."],
 ["Apps", "Apple Developer Program", "Publicar na App Store", "Todos os apps", "Individual (Solano)", "USD", 99, A, None, "Estimado", "Renovação anual."],
 ["Apps", "Google Play Console", "Publicar na Google Play", "Todos os apps", "Taxa única", "USD", 25, U, None, "Estimado", "Já paga; não se repete."],
 ["Apps", "GitHub", "Código de todos os sistemas", "Todos", "A confirmar", "USD", 0, M, None, "A confirmar", ""],
 ["Pagamentos", "RevenueCat", "Assinaturas do iPhone e Android", "Planner e apps", "Pro, sem cartão cadastrado", "USD", 0, P, None, "Verificado", "Receita rastreada US$ 0. Grátis até ~US$ 2.500/mês de receita; depois cobra % (confirmar). Sem cartão: cadastrar antes de crescer."],
 ["Pagamentos", "Stripe (Coruja Labs)", "Assinaturas pelo site", "Planner", "Sem mensalidade", "BRL", 0, P, None, "Verificado", "3,99% + R$ 0,39 por cobrança (veja a aba Taxas por venda)."],
 ["Pagamentos", "Kiwify", "Venda de ebooks e cursos", "Tâmara / Frei Miguel", "% por venda", "BRL", 0, P, None, "A confirmar", "Taxa por venda: confirmar no painel."],
 ["E-mail", "Brevo", "Leads da landing e e-mail de boas-vindas", "Planner", "A confirmar (grátis até 300/dia)", "BRL", 0, M, None, "A confirmar", "Chave salva em 3 serviços em 24/11."],
 ["E-mail", "Gmail (contas @gmail)", "Caixas das marcas", "Todas", "Grátis", "BRL", 0, M, None, "Verificado", "candeiatec.app, plannerorganiza.app, meustudioemdia, enxovalemdia, freimiguellucero."],
 ["IA", "Anthropic API (Cléo)", "Assistente de voz dentro do app e do site", "Planner", "Por uso", "USD", 0, P, None, "A confirmar", "Custo sobe com o uso da Cléo."],
 ["IA", "Claude (este assistente)", "Desenvolvimento e operação", "Todas", "A confirmar", "USD", 0, M, None, "A confirmar", ""],
 ["Integrações", "Executor", "Liga ElevenLabs, Upload-Post, Meta Ads, Gmail, Drive e Stripe", "Todas", "A confirmar", "USD", 0, M, None, "A confirmar", ""],
 ["Integrações", "n8n", "Automações do CRM", "CRM", "A confirmar", "USD", 0, M, None, "A confirmar", "Hospedagem a confirmar."],
 ["Métricas", "Google Analytics e Pixel da Meta", "Medir visitas, cadastros e compras", "Todas", "Grátis", "BRL", 0, M, None, "Verificado", "Pixel de compra não registra vendas na campanha Casa em Ordem."],
 ["Domínios", "Domínios .com.br (7)", "plannerorganiza, candeiatec, tamaracavalcante, agendamei, minhadiaria, vidaemmetodo, freimiguellucero", "Todas", "Registro anual", "BRL", 7 * 40, A, None, "Estimado", "~R$ 40 por domínio/ano. Conferir onde estão registrados."],
 ["Domínios", "Domínios .app (4)", "plannerorganiza.app, agendamei.app, minhadiaria.app, nailpro.app", "Apps", "Registro anual", "USD", 4 * 14, A, None, "Estimado", "~US$ 14 por domínio/ano."],
 # Conteúdo e redes
 ["Conteúdo", "ElevenLabs", "Voz clonada da Tâmara nos stories", "Tâmara / Planner", "Pay as you go", "USD", 0, P, None, "Verificado", "2.788 de 10.000 créditos usados no ciclo."],
 ["Conteúdo", "Kairogen", "Imagens e vídeos com IA", "Todas", "Essential mensal", "BRL", 49, M, None, "Verificado", "Próxima cobrança 19/12/2026. Pix automático RECUSADO: risco de o plano cair."],
 ["Conteúdo", "Viral (doti)", "Imagens, vídeos e influencer com IA", "Todas", "Starter, 1.000 créditos/ciclo", "BRL", 0, M, None, "A confirmar", "Saldo 563 créditos, ciclo até 14/12/2026. Preço a confirmar."],
 ["Conteúdo", "Canva", "Design de posts", "Todas", "A confirmar", "BRL", 0, M, None, "A confirmar", ""],
 ["Conteúdo", "Unsplash", "Fotos de banco de imagens", "Todas", "Grátis", "BRL", 0, M, None, "Verificado", ""],
 ["Redes sociais", "Upload-Post", "Agendar stories e posts; resposta automática (AutoDM)", "Tâmara / Planner", "A confirmar", "USD", 0, M, None, "A confirmar", "Há 2 contas: a do Executor (ativa, usada nos stories) e outra marcada para exclusão em 17/12/2026."],
 ["Redes sociais", "Windsor.ai", "Coleta de métricas das redes", "Candeia Tec", "Free", "BRL", 0, M, None, "Verificado", ""],
 ["Anúncios", "Meta Ads · conta tamaraorganiza", "Anúncios do Planner, Casa em Ordem e WhatsApp", "Tâmara / Planner", "Gasto por campanha", "BRL", 1368.08, M, None, "Verificado", "Gasto dos últimos 30 dias (veja a aba Redes e anúncios)."],
]
fim = tabela(s, cab, [14, 30, 38, 18, 24, 8, 11, 16, 15, 14, 60], d)
for i in range(4, fim + 1):
    s[f"G{i}"].number_format = '#,##0.00'
    s[f"I{i}"] = (f'=IF(H{i}="Única",0,IF(F{i}="USD",G{i}*{COT},G{i})/IF(H{i}="Anual",12,1))')
    s[f"I{i}"].number_format = '"R$" #,##0.00'
    sit = s[f"J{i}"].value
    if sit in COR: s[f"J{i}"].fill = PatternFill("solid", fgColor=COR[sit])
dv = DataValidation(type="list", formula1='"Verificado,Estimado,A confirmar"', allow_blank=True); s.add_data_validation(dv); dv.add(f"J4:J{fim}")
dv2 = DataValidation(type="list", formula1='"Mensal,Anual,Única,Por uso / % da venda"', allow_blank=True); s.add_data_validation(dv2); dv2.add(f"H4:H{fim}")
s[f"H{fim+2}"] = "Total mensal estimado"; s[f"H{fim+2}"].font = Font(bold=True)
s[f"I{fim+2}"] = f"=SUM(I4:I{fim})"; s[f"I{fim+2}"].number_format = '"R$" #,##0.00'; s[f"I{fim+2}"].font = Font(bold=True)
s[f"H{fim+3}"] = "Sem anúncios"; s[f"I{fim+3}"] = f'=I{fim+2}-SUMIF(A4:A{fim},"Anúncios",I4:I{fim})'; s[f"I{fim+3}"].number_format = '"R$" #,##0.00'
s[f"H{fim+4}"] = "Itens a confirmar"; s[f"I{fim+4}"] = f'=COUNTIF(J4:J{fim},"A confirmar")'
s[f"K{fim+2}"] = "Não inclui taxas por venda (Stripe, lojas, Kiwify) nem itens \"A confirmar\" sem valor."

# ---------- Redes e anúncios ----------
r = wb.create_sheet("Redes e anúncios")
r["A1"] = "Perfis, contas de anúncio e resultado dos últimos 30 dias"; r["A1"].font = T
cab = ["Tipo", "Canal", "Endereço / conta", "Marca", "Gasto 30 dias (R$)", "Resultado medido", "Quantidade", "Custo por resultado (R$)", "Situação", "Gargalo / observação"]
d = [
 ["Perfil", "Instagram", "instagram.com/plannerorganiza", "Planner", None, "", None, None, "Ativo", ""],
 ["Perfil", "TikTok", "tiktok.com/@plannerorganiza", "Planner", None, "", None, None, "Ativo", ""],
 ["Perfil", "YouTube", "youtube.com/@Plannerorganiza", "Planner", None, "", None, None, "Ativo", ""],
 ["Perfil", "Instagram", "@tamaraorganiza", "Tâmara", None, "", None, None, "Ativo", "15 stories agendados (21/11 a 05/12) com \"Comente PLANNER\". Confirmar se a AutoDM está respondendo."],
 ["Perfil", "WhatsApp", "WhatsApp da Tâmara", "Tâmara", None, "", None, None, "Ativo", "Recebe as conversas dos anúncios de mudança."],
 ["Anúncio", "Meta Ads", "PLANNER_TESTE_20261121", "Planner", 178.97, "Cadastros (pixel)", 10, None, "Ativa", "No banco, 11 contas vieram do Facebook e nenhuma assinou ainda."],
 ["Anúncio", "Meta Ads", "CASAEMORDEM_ABO_TESTE_20261121", "Tâmara (Casa em Ordem)", 281.21, "Compras (pixel)", 0, None, "Ativa", "Nenhuma compra registrada: ou não vendeu, ou o pixel de compra não está medindo (Kiwify)."],
 ["Anúncio", "Meta Ads", "WhatsApp - Mudança Alto Luxo Nova Lima - Nov 2026", "Tâmara (presencial)", 607.14, "Conversas no WhatsApp", 23, None, "Pausada", "Maior gasto do mês. Quantas viraram orçamento fechado?"],
 ["Anúncio", "Meta Ads", "Post do Instagram: Vai mudar de casa? (2 impulsionamentos)", "Tâmara (presencial)", 220.92, "Conversas no WhatsApp", 0, None, "Ativa", "Sem resultado medido."],
 ["Anúncio", "Meta Ads", "WhatsApp - Alto Luxo Nova Lima - Out 2026", "Tâmara (presencial)", 79.84, "Conversas no WhatsApp", 0, None, "Ativa", "Sem resultado medido no período."],
 ["Conta de anúncio", "Meta Ads", "Enxoval em Dia - Anúncios", "Enxoval em Dia", 0, "", None, None, "Sem forma de pagamento", ""],
 ["Conta de anúncio", "Meta Ads", "Meu Studio em Dia - Anúncios", "Meu Studio em Dia", 0, "", None, None, "Sem forma de pagamento", ""],
]
fim = tabela(r, cab, [16, 12, 44, 22, 14, 22, 11, 16, 20, 60], d)
for i in range(4, fim + 1):
    r[f"E{i}"].number_format = '"R$" #,##0.00'
    r[f"H{i}"] = f'=IF(AND(ISNUMBER(G{i}),G{i}>0),E{i}/G{i},IF(AND(ISNUMBER(E{i}),E{i}>0),"sem resultado",""))'
    r[f"H{i}"].number_format = '"R$" #,##0.00'
r[f"D{fim+2}"] = "Total gasto em anúncios (30 dias)"; r[f"D{fim+2}"].font = Font(bold=True)
r[f"E{fim+2}"] = f"=SUM(E4:E{fim})"; r[f"E{fim+2}"].number_format = '"R$" #,##0.00'; r[f"E{fim+2}"].font = Font(bold=True)
r[f"D{fim+3}"] = "Gasto sem nenhum resultado medido"
r[f"E{fim+3}"] = f'=SUMIFS(E4:E{fim},G4:G{fim},0)'; r[f"E{fim+3}"].number_format = '"R$" #,##0.00'

# ---------- Taxas por venda ----------
t = wb.create_sheet("Taxas por venda")
t["A1"] = "Quanto sobra de cada venda do Planner (preços do Brasil)"; t["A1"].font = T
cab = ["Canal", "Plano", "Preço (R$)", "Taxa % do canal", "Taxa fixa (R$)", "Líquido (R$)", "Afiliada 25% (se indicada)", "Sobra sem afiliada (R$)", "Sobra com afiliada (R$)"]
d = [
 ["Site (Stripe)", "Mensal", 59.90, 0.0399, 0.39], ["Site (Stripe)", "Trimestral", 149.90, 0.0399, 0.39],
 ["Site (Stripe)", "Anual", 479.90, 0.0399, 0.39], ["Site (Stripe)", "Anual indicação (10% off)", 431.90, 0.0399, 0.39],
 ["App Store / Google Play", "Mensal", 59.90, 0.15, 0], ["App Store / Google Play", "Trimestral", 149.90, 0.15, 0],
 ["App Store / Google Play", "Anual", 479.90, 0.15, 0], ["App Store / Google Play", "Anual indicação (10% off)", 431.90, 0.15, 0],
]
d = [row + [None] * 4 for row in d]
fim = tabela(t, cab, [24, 26, 12, 14, 13, 13, 16, 18, 18], d)
for i in range(4, fim + 1):
    t[f"F{i}"] = f"=C{i}*(1-D{i})-E{i}"; t[f"G{i}"] = f"=F{i}*0.25"; t[f"H{i}"] = f"=F{i}"; t[f"I{i}"] = f"=F{i}-G{i}"
    t[f"D{i}"].number_format = "0.00%"
    for c in "CEFGHI": t[f"{c}{i}"].number_format = '"R$" #,##0.00'
t[f"A{fim+2}"] = "Lojas: 15% vale para quem fatura até US$ 1 milhão/ano no programa de pequenas empresas (Apple e Google). RevenueCat pode cobrar % acima de ~US$ 2.500/mês."

# ---------- Gargalos ----------
g = wb.create_sheet("Gargalos")
g["A1"] = "Gargalos, do mais urgente ao menos urgente"; g["A1"].font = T
cab = ["#", "Gargalo", "Onde", "Impacto", "O que fazer", "Quem", "Prazo sugerido", "Status"]
d = [
 [1, "Ninguém assinou pelas lojas e as contas do app usavam de graça para sempre (sem ficha no banco)", "App / API", "Alto", "Corrigido em 24/11: o teste de 7 dias passou a contar. Acompanhar no Funil de vendas quantas veem os planos e assinam.", "Claude + Solano", "Esta semana", "Em andamento"],
 [2, "Campanha Casa em Ordem gastou R$ 281 sem nenhuma compra registrada", "Meta Ads / Kiwify", "Alto", "Conferir se o pixel de compra da Kiwify está ligado. Se estiver e não vendeu, pausar e trocar criativo ou público.", "Solano", "Hoje", "A fazer"],
 [3, "Maior gasto (R$ 607 no WhatsApp Alto Luxo) sem saber quantas conversas viraram serviço fechado", "Meta Ads / WhatsApp", "Alto", "Anotar, das 23 conversas, quantas pediram orçamento e quantas fecharam. Sem isso não dá para saber se compensa.", "Tâmara", "Esta semana", "A fazer"],
 [4, "Anúncio do Planner: R$ 17,90 por cadastro, mas nenhum cadastro virou assinatura ainda", "Meta Ads / Planner", "Alto", "Esperar o fim dos 7 dias de teste dessas contas e olhar o Funil. Ativar o e-mail de boas-vindas (falta seu sim para publicar).", "Solano", "Até 05/12", "A fazer"],
 [5, "R$ 300 em impulsionamentos sem resultado medido", "Meta Ads", "Médio", "Pausar impulsionamentos de post sem objetivo de conversa ou cadastro; concentrar verba nas campanhas medidas.", "Solano", "Esta semana", "A fazer"],
 [6, "Kairogen: Pix automático recusado; plano pode cair em 19/12", "Kairogen", "Médio", "Trocar a forma de pagamento no painel ou cancelar se outra ferramenta já cobre.", "Solano", "Antes de 19/12", "A fazer"],
 [7, "Duas contas no Upload-Post, uma marcada para exclusão em 17/12", "Upload-Post", "Médio", "Confirmar que os stories e a AutoDM do PLANNER estão na conta ativa (Executor). Deixar a outra ser apagada.", "Claude + Solano", "Antes de 17/12", "A fazer"],
 [8, "Muitas ferramentas de conteúdo com a mesma função (Kairogen, Viral, ElevenLabs, Canva)", "Conteúdo", "Médio", "Escolher 1 para imagem/vídeo e manter a ElevenLabs só para voz. Cancelar o resto.", "Solano", "Dezembro", "A fazer"],
 [9, "Quase nenhum telefone das clientes (3 de 30 contas)", "Planner", "Médio", "Pedir o WhatsApp no questionário inicial (site agora, app na 1.0.20).", "Claude", "1.0.20", "A fazer"],
 [10, "RevenueCat sem cartão cadastrado", "RevenueCat", "Baixo agora", "Cadastrar cartão antes de a receita do app passar de ~US$ 2.500/mês, para não travar as compras.", "Solano", "Quando vender", "A fazer"],
 [11, "Servidores nos EUA e banco pequeno; site fica ~2 min fora a cada publicação", "Render", "Baixo agora", "Publicar fora do horário de uso. Quando passar de ~200 clientes ativas, subir o banco e avaliar região mais perto do Brasil.", "Claude", "Quando crescer", "Acompanhar"],
 [12, "Pix das afiliadas e aprovação são manuais", "Programa de afiliadas", "Baixo agora", "Manual está bem até ~20 afiliadas. Depois, automatizar o Pix.", "Tâmara", "Quando crescer", "Acompanhar"],
 [13, "Serviços sobrando", "Render / Supabase", "Baixo", "Apagar plannerorganizer-teste e Contrato-facil; apagar ou manter parados os projetos Supabase inativos.", "Solano", "Quando puder", "A fazer"],
 [14, "Assinatura anual de indicação no iPhone ainda não foi enviada para revisão", "App Store", "Médio", "Rodar o prompt do Claude no Chrome (trocar a imagem de revisão e enviar).", "Solano (Chrome)", "Esta semana", "A fazer"],
 [15, "Chave da Brevo deu erro de caractere inválido na landing", "Brevo / Render", "Baixo", "Conferir se o valor da BREVO_API_KEY não tem espaço ou linha em branco no fim.", "Solano", "Hoje", "A fazer"],
]
fim = tabela(g, cab, [4, 52, 20, 12, 62, 16, 16, 14], d)
for i in range(4, fim + 1):
    imp = g[f"D{i}"].value
    g[f"D{i}"].fill = PatternFill("solid", fgColor={"Alto": "F8D7DA", "Médio": "FFF3CD"}.get(imp, "D9F2E3"))
dv3 = DataValidation(type="list", formula1='"A fazer,Em andamento,Acompanhar,Feito"', allow_blank=True); g.add_data_validation(dv3); dv3.add(f"H4:H{fim}")

# ---------- A confirmar ----------
c = wb.create_sheet("A confirmar")
c["A1"] = "O que preciso que você preencha (plano e valor)"; c["A1"].font = T
c["A3"] = "Abra a aba Serviços, filtre \"Situação do dado\" = A confirmar e preencha as colunas Plano hoje e Valor."
c["A4"] = "Para os itens Estimado, confira o valor na fatura do mês e corrija se for diferente."
c.column_dimensions["A"].width = 110

wb.move_sheet("Gargalos", offset=-3)
wb.save(OUT); print(OUT)
