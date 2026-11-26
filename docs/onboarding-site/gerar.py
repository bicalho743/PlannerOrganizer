"""Telas do onboarding do Planner Organiza (protótipo visual, não é código do app)."""
from pathlib import Path

D = Path(__file__).parent
F = "/tmp/claude-0/-home-user/ac9bca1e-440f-585e-897d-28876c56361c/scratchpad/capa"

CSS = f"""
@font-face{{font-family:'Cormorant';src:url('file://{F}/cormorant_semibold.ttf');font-weight:600}}
@font-face{{font-family:'Cormorant';src:url('file://{F}/cormorant_italic.ttf');font-style:italic;font-weight:500}}
@font-face{{font-family:'DMSans';src:url('file://{F}/dmsans_medium.ttf');font-weight:500}}
@font-face{{font-family:'DMSans';src:url('file://{F}/dmsans_bold.ttf');font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#E9E6DF;font-family:'DMSans',sans-serif;color:#101828}}
.tela{{width:390px;height:844px;background:#F8F6F1;position:relative;overflow:hidden;display:flex;flex-direction:column}}
.status{{height:44px;display:flex;justify-content:space-between;align-items:center;padding:0 26px;font-size:14px;font-weight:700;color:#101828}}
.topo{{display:flex;align-items:center;gap:14px;padding:6px 22px 0}}
.voltar{{width:34px;height:34px;border-radius:17px;background:#fff;border:1px solid #E4E7EC;display:flex;align-items:center;justify-content:center;font-size:18px;color:#0D1B2A}}
.barra{{flex:1;height:6px;border-radius:3px;background:#ECE6D6;overflow:hidden}} .barra i{{display:block;height:100%;background:#C9A84C;border-radius:3px}}
.pular{{font-size:14px;color:#667085}}
.corpo{{flex:1;padding:26px 24px 0;display:flex;flex-direction:column}}
.passo{{font-size:12px;letter-spacing:1.6px;color:#8A6A1C;font-weight:700;text-transform:uppercase;margin-bottom:10px}}
h1{{font-family:'Cormorant';font-weight:600;font-size:34px;line-height:1.08;color:#0D1B2A}}
h1 em{{font-style:italic;font-weight:500;color:#8A6A1C}}
.ajuda{{font-size:15px;color:#667085;line-height:1.45;margin-top:10px}}
.campo{{margin-top:18px}} .campo label{{display:block;font-size:13px;color:#667085;margin-bottom:6px}}
.input{{background:#fff;border:1.5px solid #E4E7EC;border-radius:14px;padding:14px 16px;font-size:16px}}
.input.foco{{border-color:#C9A84C}}
.opc{{background:#fff;border:1.5px solid #E4E7EC;border-radius:16px;padding:15px 16px;font-size:16px;display:flex;align-items:center;gap:12px;margin-top:10px}}
.opc .ic{{width:36px;height:36px;border-radius:10px;background:#F6F0DF;display:flex;align-items:center;justify-content:center;font-size:18px}}
.opc small{{display:block;font-size:13px;color:#667085;margin-top:2px}}
.opc.sel{{border-color:#0D1B2A;background:#0D1B2A;color:#fff}} .opc.sel small{{color:rgba(255,255,255,.65)}} .opc.sel .ic{{background:rgba(201,168,76,.22)}}
.opc .chk{{margin-left:auto;width:22px;height:22px;border-radius:7px;border:1.5px solid #D0D5DD;flex-shrink:0}}
.opc.sel .chk{{background:#C9A84C;border-color:#C9A84C;display:flex;align-items:center;justify-content:center;color:#0D1B2A;font-size:14px;font-weight:700}}
.rodape{{padding:16px 24px 30px}}
.btn{{background:#0D1B2A;color:#E8C97A;border-radius:16px;padding:17px;text-align:center;font-weight:700;font-size:16px}}
.btn.ouro{{background:#C9A84C;color:#0D1B2A}}
.btn2{{text-align:center;color:#667085;font-size:15px;margin-top:14px}}
.nino{{font-size:15px;color:#0D1B2A;background:#fff;border:1px solid #ECE6D6;border-radius:16px 16px 16px 4px;padding:12px 14px;margin-top:16px;line-height:1.45}}
.card{{background:#fff;border:1px solid #E4E7EC;border-radius:18px;padding:16px;margin-top:14px}}
.item{{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid #F0F1F3;font-size:15px}}
.item:last-child{{border-bottom:none}}
.num{{width:28px;height:28px;border-radius:14px;background:#F6F0DF;color:#8A6A1C;font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.feito{{background:#067647;color:#fff}}
.item small{{display:block;color:#667085;font-size:12.5px;margin-top:1px}}
.tag{{display:inline-block;font-size:11px;font-weight:700;color:#8A6A1C;background:#F6F0DF;border-radius:20px;padding:3px 9px;margin-left:6px;vertical-align:2px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}} .chips span{{background:#fff;border:1.5px solid #E4E7EC;border-radius:20px;padding:8px 14px;font-size:14px}}
.chips span.sel{{background:#0D1B2A;border-color:#0D1B2A;color:#fff}}
.tab{{height:78px;background:#fff;border-top:1px solid #E4E7EC;display:flex;justify-content:space-around;align-items:center;font-size:11px;color:#667085;padding-bottom:14px}}
.tab b{{display:block;text-align:center;font-size:20px;color:#98A2B3;font-weight:500}} .tab .on{{color:#0D1B2A}} .tab .on b{{color:#0D1B2A}}
.mais{{width:52px;height:52px;border-radius:26px;background:#0D1B2A;color:#fff;font-size:28px;display:flex;align-items:center;justify-content:center;margin-top:-26px;border:4px solid #fff}}
"""

def tela(conteudo, status_cor=None):
    return f'<div class="tela">{conteudo}</div>'

def topo(n, total=4, pular=True, voltar=True):
    v = '<div class="voltar">‹</div>' if voltar else '<div style="width:34px"></div>'
    p = '<span class="pular">Pular</span>' if pular else '<span style="width:34px"></span>'
    return f'<div class="status"><span>9:41</span><span>●●● 100%</span></div><div class="topo">{v}<div class="barra"><i style="width:{100*n/total:.0f}%"></i></div>{p}</div>'

T = {}

T["01-nome"] = tela(topo(1) + """
<div class="corpo">
  <div class="passo">1 de 4 · leva 1 minuto</div>
  <h1>Que bom ter você aqui!<br><em>Como quer ser chamada?</em></h1>
  <div class="campo"><label>Seu nome</label><div class="input foco">Ana</div></div>
  <div class="campo"><label>Nome do seu negócio</label><div class="input">Ana Lima Organização</div></div>
  <div class="nino">✨ O nome do seu negócio já sai no topo das suas propostas em PDF.</div>
</div>
<div class="rodape"><div class="btn">Continuar</div></div>""")

T["02-tempo"] = tela(topo(2) + """
<div class="corpo">
  <div class="passo">2 de 4</div>
  <h1>Há quanto tempo você atua como <em>personal organizer?</em></h1>
  <p class="ajuda">Assim eu sei por onde começar com você.</p>
  <div class="opc"><div class="ic">🌱</div><div>Estou começando<small>Ainda montando preços e clientes</small></div></div>
  <div class="opc sel"><div class="ic">📈</div><div>Até 2 anos<small>Já atendo, quero organizar o negócio</small></div></div>
  <div class="opc"><div class="ic">🏆</div><div>Mais de 2 anos<small>Tenho clientes e quero ganhar tempo</small></div></div>
</div>
<div class="rodape"><div class="btn">Continuar</div></div>""")

T["03-dores"] = tela(topo(3) + """
<div class="corpo">
  <div class="passo">3 de 4</div>
  <h1>O que mais <em>pesa</em> hoje?</h1>
  <p class="ajuda">Pode marcar mais de uma.</p>
  <div class="opc sel"><div class="ic">💰</div><div>Saber quanto cobrar</div><div class="chk">✓</div></div>
  <div class="opc"><div class="ic">📄</div><div>Propostas com cara profissional</div><div class="chk"></div></div>
  <div class="opc sel"><div class="ic">🔔</div><div>Lembrar dos retornos às clientes</div><div class="chk">✓</div></div>
  <div class="opc"><div class="ic">📊</div><div>Controlar o dinheiro do mês</div><div class="chk"></div></div>
  <div class="opc"><div class="ic">🧾</div><div>MEI e impostos</div><div class="chk"></div></div>
</div>
<div class="rodape"><div class="btn">Continuar</div></div>""")

T["04-formal"] = tela(topo(4) + """
<div class="corpo">
  <div class="passo">4 de 4</div>
  <h1>Como o seu negócio é <em>formalizado?</em></h1>
  <p class="ajuda">Eu já deixo o financeiro e os impostos no jeito.</p>
  <div class="opc sel"><div class="ic">🧾</div><div>MEI<small>Acompanho o DAS e o limite do ano</small></div></div>
  <div class="opc"><div class="ic">🏢</div><div>Simples Nacional</div></div>
  <div class="opc"><div class="ic">🙂</div><div>Ainda não sou formalizada</div></div>
  <p class="ajuda" style="font-size:13px;margin-top:16px">O app organiza, mas não substitui o seu contador.</p>
</div>
<div class="rodape"><div class="btn">Ver meu Planner</div></div>""")

T["05-pronto"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:18px">
  <div style="font-size:40px">🎉</div>
  <h1 style="margin-top:6px">Seu Planner está pronto, <em>Ana.</em></h1>
  <p class="ajuda">Montei seus primeiros passos na ordem do que você me contou.</p>
  <div class="card" style="padding:6px 16px">
    <div class="item"><div class="num">1</div><div>Criar sua primeira proposta<small>Cerca de 5 minutos, com PDF pronto para enviar</small></div></div>
    <div class="item"><div class="num">2</div><div>Descobrir quanto cobrar <span class="tag">você marcou</span><small>Hora, diária e preço de projeto</small></div></div>
    <div class="item"><div class="num">3</div><div>Ligar o aviso de retornos <span class="tag">você marcou</span><small>O app lembra quando falar com cada cliente</small></div></div>
    <div class="item"><div class="num">4</div><div>Colocar seu logo no PDF</div></div>
    <div class="item"><div class="num">5</div><div>Marcar um compromisso</div></div>
  </div>
</div>
<div class="rodape"><div class="btn ouro">Guardar meu Planner</div><div class="btn2">Grátis por 7 dias, sem cartão</div></div>""")

T["06-cliente"] = tela(topo(1, 3, pular=False) + """
<div class="corpo">
  <div class="passo">Primeira proposta · 1 de 3</div>
  <h1>Para quem é a <em>proposta?</em></h1>
  <div class="campo"><label>Nome da cliente</label><div class="input foco">Fernanda Costa</div></div>
  <div class="campo"><label>WhatsApp (para enviar o PDF)</label><div class="input">(31) 99876-5432</div></div>
  <div class="nino">💡 A cliente fica salva nos seus cadastros, com aniversário e histórico.</div>
  <div style="flex:1"></div>
  <div class="opc" style="border-style:dashed;margin-bottom:6px"><div class="ic">🧪</div><div>Ainda não tenho cliente agora<small>Fazer com uma cliente de exemplo (dá para apagar)</small></div></div>
</div>
<div class="rodape"><div class="btn">Continuar</div></div>""")

T["07-servico"] = tela(topo(2, 3, pular=False) + """
<div class="corpo">
  <div class="passo">Primeira proposta · 2 de 3</div>
  <h1>O que você vai <em>organizar?</em></h1>
  <div class="chips"><span class="sel">Closet</span><span class="sel">Cozinha</span><span>Casa toda</span><span>Mudança</span><span>Escritório</span><span>Quarto do bebê</span></div>
  <div class="campo"><label>Descrição</label><div class="input" style="min-height:70px">Organização de closet e cozinha, com categorização e etiquetas.</div></div>
  <div style="display:flex;gap:10px">
    <div class="campo" style="flex:1"><label>Valor total</label><div class="input foco">R$ 2.400,00</div></div>
    <div class="campo" style="flex:1"><label>Sinal</label><div class="input">R$ 1.200,00</div></div>
  </div>
  <div class="nino">Não sabe quanto cobrar? <b style="color:#8A6A1C">Calcular agora ›</b></div>
</div>
<div class="rodape"><div class="btn">Gerar a proposta</div></div>""")

T["08-pdf"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:14px;align-items:center;text-align:center">
  <div style="font-size:40px">🎉</div>
  <h1 style="margin-top:4px">Sua primeira proposta <em>está pronta!</em></h1>
  <div style="width:240px;background:#fff;border-radius:12px;box-shadow:0 14px 34px rgba(13,27,42,.16);margin-top:18px;overflow:hidden;text-align:left">
    <div style="background:#0D1B2A;color:#E8C97A;padding:12px 14px;font-family:'Cormorant';font-weight:600;font-size:18px">Ana Lima Organização</div>
    <div style="padding:12px 14px;font-size:11px;color:#667085">
      <div style="font-weight:700;color:#0D1B2A;font-size:13px">Proposta de Serviço nº 1</div>
      Cliente: Fernanda Costa<br>Closet e cozinha
      <div style="height:6px;background:#F2F4F7;border-radius:3px;margin:8px 0 5px;width:90%"></div>
      <div style="height:6px;background:#F2F4F7;border-radius:3px;margin-bottom:5px;width:70%"></div>
      <div style="display:flex;justify-content:space-between;margin-top:10px;font-weight:700;color:#0D1B2A;font-size:12px"><span>Total</span><span>R$ 2.400,00</span></div>
    </div>
  </div>
  <p class="ajuda" style="margin-top:16px">Quando a cliente aprovar, o sinal entra sozinho no seu financeiro.</p>
</div>
<div class="rodape"><div class="btn" style="background:#25D366;color:#fff">Enviar pelo WhatsApp</div><div class="btn2">Ver o PDF · <b style="color:#8A6A1C">Colocar meu logo</b></div></div>""")

T["09-avisos"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:40px">
  <div style="font-size:46px">🔔</div>
  <h1 style="margin-top:8px">Quer que eu te avise <em>de manhã?</em></h1>
  <p class="ajuda">Um resumo por dia, só com o que importa:</p>
  <div class="card" style="padding:6px 16px">
    <div class="item"><div class="num">☎</div><div>Retornos às clientes<small>"Hoje: acompanhamento da Fernanda"</small></div></div>
    <div class="item"><div class="num">R$</div><div>Cobranças e contas do dia</div></div>
    <div class="item"><div class="num">🎂</div><div>Aniversários das clientes</div></div>
  </div>
  <p class="ajuda" style="font-size:13px;margin-top:14px">Você pode desligar quando quiser.</p>
</div>
<div class="rodape"><div class="btn">Sim, me avise</div><div class="btn2">Agora não</div></div>""")

T["10-inicio"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:8px">
  <h1 style="font-size:32px">Olá, Ana</h1><p class="ajuda" style="margin-top:2px;font-size:13px">Terça-feira, 18 de novembro</p>
  <div class="card" style="border:1.5px solid #C9A84C;padding:14px 16px 6px">
    <div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:15px;color:#0D1B2A">Primeiros passos</b><span style="font-size:13px;color:#8A6A1C;font-weight:700">2 de 5</span></div>
    <div class="barra" style="margin:10px 0 4px"><i style="width:40%"></i></div>
    <div class="item"><div class="num feito">✓</div><div style="color:#667085;text-decoration:line-through">Criar sua primeira proposta</div></div>
    <div class="item"><div class="num feito">✓</div><div style="color:#667085;text-decoration:line-through">Ligar o aviso de retornos</div></div>
    <div class="item"><div class="num">3</div><div>Descobrir quanto cobrar<small>Hora, diária e preço de projeto</small></div><span style="margin-left:auto;color:#8A6A1C;font-size:20px">›</span></div>
    <div class="item"><div class="num">4</div><div>Colocar seu logo no PDF</div></div>
    <div class="item"><div class="num">5</div><div>Marcar um compromisso</div></div>
  </div>
  <div style="display:flex;gap:10px;margin-top:12px">
    <div class="card" style="flex:1;margin:0;background:#0D1B2A;color:#fff"><small style="font-size:10px;letter-spacing:1px;color:#E8C97A">A RECEBER</small><div style="font-size:19px;font-weight:700;margin-top:4px">R$ 1.200,00</div></div>
    <div class="card" style="flex:1;margin:0"><small style="font-size:10px;letter-spacing:1px;color:#667085">PROPOSTAS</small><div style="font-size:19px;font-weight:700;margin-top:4px">1 em aberto</div></div>
  </div>
</div>
<div class="tab"><div class="on"><b>⌂</b>Início</div><div><b>▤</b>Propostas</div><div class="mais">+</div><div><b>▣</b>Financeiro</div><div><b>≡</b>Menu</div></div>""")

T["11-vazia"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:8px">
  <div style="display:flex;justify-content:space-between;align-items:center"><h1 style="font-size:32px">Propostas</h1><span style="background:#C9A84C;color:#0D1B2A;border-radius:20px;padding:8px 16px;font-weight:700">+ Nova</span></div>
  <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 10px">
    <div style="font-size:52px">📄</div>
    <h1 style="font-size:28px;margin-top:10px">Sua primeira proposta <em>em 5 minutos</em></h1>
    <p class="ajuda">Com o nome do seu negócio, os ambientes, o valor e o sinal. Sai em PDF, pronta para o WhatsApp.</p>
    <div class="card" style="text-align:left;width:100%;padding:6px 16px">
      <div class="item"><div class="num">1</div><div>Escolha a cliente</div></div>
      <div class="item"><div class="num">2</div><div>Diga o que vai organizar e o valor</div></div>
      <div class="item"><div class="num">3</div><div>Envie o PDF</div></div>
    </div>
  </div>
</div>
<div class="rodape" style="padding-bottom:12px"><div class="btn">Criar minha primeira proposta</div><div class="btn2">Ver um PDF de exemplo</div></div>
<div class="tab"><div><b>⌂</b>Início</div><div class="on"><b>▤</b>Propostas</div><div class="mais">+</div><div><b>▣</b>Financeiro</div><div><b>≡</b>Menu</div></div>""")

T["12-dica"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:8px">
  <h1 style="font-size:32px">Financeiro</h1>
  <div class="card" style="padding:6px 16px">
    <div class="item"><div class="num" style="background:#E7F6EC;color:#067647">↑</div><div>Sinal · Fernanda Costa<small>Proposta nº 1 · recebido hoje</small></div><b style="margin-left:auto;color:#067647">R$ 1.200,00</b></div>
    <div class="item"><div class="num">↑</div><div>Saldo · Fernanda Costa<small>a receber na conclusão</small></div><b style="margin-left:auto;color:#8A6A1C">R$ 1.200,00</b></div>
  </div>
  <div style="position:relative;margin-top:16px;background:#0D1B2A;color:#fff;border-radius:16px;padding:16px">
    <div style="position:absolute;top:-8px;left:40px;width:16px;height:16px;background:#0D1B2A;transform:rotate(45deg)"></div>
    <b style="color:#E8C97A">Isso entrou sozinho ✨</b>
    <p style="font-size:14px;line-height:1.45;margin-top:6px;color:rgba(255,255,255,.85)">Quando a proposta foi aprovada, o sinal e o saldo vieram para cá. Você só marca "recebido".</p>
    <div style="text-align:right;margin-top:10px;font-weight:700;color:#E8C97A">Entendi</div>
  </div>
  <div class="card" style="margin-top:16px;border:1px dashed #C9A84C;background:#FFFCF4">
    <b style="color:#0D1B2A">🎙️ Sabia que dá para falar com o app?</b>
    <p style="font-size:13.5px;color:#667085;margin-top:6px;line-height:1.45">Com a Cléo (Plano Pro), você diz "lança uma despesa de 80 reais de material" e ela preenche.</p>
  </div>
</div>
<div class="tab"><div><b>⌂</b>Início</div><div><b>▤</b>Propostas</div><div class="mais">+</div><div class="on"><b>▣</b>Financeiro</div><div><b>≡</b>Menu</div></div>""")

T["13-teste"] = tela("""<div style="height:100%;background:linear-gradient(160deg,#2B3A55,#0D1B2A);color:#fff;padding:60px 18px 0">
  <div style="text-align:center;font-size:64px;font-weight:300;letter-spacing:-1px">9:41</div>
  <div style="text-align:center;font-size:16px;opacity:.8;margin-bottom:34px">terça-feira, 18 de novembro</div>
  """ + "".join(f"""<div style="background:rgba(255,255,255,.88);color:#101828;border-radius:18px;padding:12px 14px;margin-bottom:10px;display:flex;gap:10px">
    <div style="width:34px;height:34px;border-radius:9px;background:#0D1B2A;color:#C9A84C;display:flex;align-items:center;justify-content:center;font-family:'Cormorant';font-weight:600;font-size:18px;flex-shrink:0">P</div>
    <div style="font-size:13.5px;line-height:1.35"><b>Planner Organiza</b> <span style="color:#667085;font-size:12px">· {d}</span><br>{t}</div></div>""" for d, t in [
    ("dia 1 do teste", "Que tal sua primeira proposta? Leva 5 minutos e já sai em PDF com o seu nome."),
    ("dia 3 do teste", "Você sabe quanto vale a sua hora? Coloque seus custos e o app mostra quanto cobrar."),
    ("dia 6 do teste", "Seu teste termina amanhã. Você já criou 2 propostas e cadastrou 3 clientes. Veja os planos."),
  ]) + """
  <div style="text-align:center;font-size:12px;opacity:.6;margin-top:18px">Avisos do período de teste (no celular e por e-mail)</div>
</div>""")

T["00-boas-vindas"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="corpo" style="padding-top:22px;align-items:center;text-align:center">
  <div style="width:300px;background:#fff;border:7px solid #0D1B2A;border-radius:34px;padding:16px;box-shadow:0 18px 40px rgba(13,27,42,.18);text-align:left">
    <div style="font-family:'Cormorant';font-weight:600;font-size:22px;color:#0D1B2A;text-align:center">Propostas</div>
    <div style="background:#0D1B2A;border-radius:16px;padding:14px;margin-top:10px;color:#fff">
      <div style="font-family:'Cormorant';font-style:italic;font-size:30px;color:#E8C97A">R$ 2.400</div>
      <div style="font-size:12px;opacity:.75">Closet e cozinha · Fernanda Costa</div>
      <div style="height:6px;border-radius:3px;background:rgba(255,255,255,.18);margin-top:10px"><div style="width:50%;height:100%;background:#C9A84C;border-radius:3px"></div></div>
      <div style="font-size:11px;opacity:.7;margin-top:5px">Sinal recebido · 50%</div>
    </div>
    <div class="item" style="font-size:13.5px"><div class="num feito" style="width:24px;height:24px">✓</div>Proposta enviada<span style="margin-left:auto;color:#667085;font-size:12px">seg</span></div>
    <div class="item" style="font-size:13.5px"><div class="num" style="width:24px;height:24px">☎</div>Retorno à cliente<span style="margin-left:auto;color:#8A6A1C;font-size:12px;font-weight:700">hoje</span></div>
    <div class="item" style="font-size:13.5px"><div class="num" style="width:24px;height:24px">R$</div>Saldo a receber<span style="margin-left:auto;color:#667085;font-size:12px">sex</span></div>
  </div>
  <h1 style="margin-top:28px;font-size:36px">Você organiza a casa das clientes. <em>Nós organizamos o seu negócio.</em></h1>
  <p class="ajuda">Propostas, agenda, retornos e financeiro, feitos para personal organizers.</p>
</div>
<div class="rodape"><div class="btn">Começar</div><div class="btn2">Já tem uma conta? <b style="color:#0D1B2A">Entrar</b></div></div>""")

T["05b-conta"] = tela("""<div class="status"><span>9:41</span><span>●●● 100%</span></div>
<div class="topo"><div class="voltar">‹</div><div class="barra"><i style="width:100%"></i></div><span style="width:34px"></span></div>
<div class="corpo">
  <h1>Crie sua conta para <em>guardar o seu Planner</em></h1>
  <p class="ajuda">Suas respostas já estão salvas. Com a conta, tudo fica no celular e no computador.</p>
  <div class="opc" style="justify-content:center;font-weight:700;margin-top:22px;background:#000;color:#fff;border-color:#000"> Continuar com Apple</div>
  <div class="opc" style="justify-content:center;font-weight:700"><b style="color:#4285F4">G</b> Continuar com Google</div>
  <div class="opc" style="justify-content:center;font-weight:700">✉️ Continuar com e-mail</div>
  <div class="card" style="background:#FFFCF4;border:1px solid #ECE6D6;text-align:center">
    <b style="color:#0D1B2A">7 dias grátis, sem cartão</b>
    <p style="font-size:13px;color:#667085;margin-top:4px">Depois você escolhe se quer assinar. Nada é cobrado sozinho.</p>
  </div>
  <div style="flex:1"></div>
  <div class="btn2" style="margin-bottom:6px">Tenho um convite</div>
</div>
<div class="rodape" style="padding-top:4px"><div class="btn2" style="font-size:12.5px;margin:0">Ao continuar, você aceita os Termos de Uso e a Política de Privacidade.</div></div>""")

NOMES = {
 "01-nome": "1. Nome e negócio", "02-tempo": "2. Tempo de atuação", "03-dores": "3. O que mais pesa",
 "04-formal": "4. Formalização", "05-pronto": "5. Seu Planner está pronto", "06-cliente": "6. Proposta: cliente",
 "07-servico": "7. Proposta: serviço e valor", "08-pdf": "8. Proposta pronta (PDF)", "09-avisos": "9. Avisos no momento certo",
 "10-inicio": "10. Início com primeiros passos", "11-vazia": "11. Tela vazia que ensina", "12-dica": "12. Dica na hora certa",
 "13-teste": "13. Avisos do teste de 7 dias",
}

(D / "telas").mkdir(exist_ok=True)
for k, html in T.items():
    (D / "telas" / f"{k}.html").write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html}</body></html>", encoding="utf-8")
print("ok", len(T))
