"""
E-mail de boas-vindas da equipe Planner Organiza para cada conta nova (site ou app), enviado uma única vez pela Brevo.

- Disparo: quando a conta aparece pela primeira vez (utils/funil.registrar "conta_criada" devolve True) e foi criada
  há no máximo 2 dias (contas antigas do app que só agora ganharam perfil não recebem).
- Uma vez por conta: o envio grava o evento "boas_vindas" em eventos_funil antes de mandar.
- Precisa da variável BREVO_API_KEY no serviço (a mesma da landing). Sem ela, só registra no log.
- O envio roda em segundo plano para não atrasar o login.
- A conta também entra como contato na lista "Leads Planner Organiza" (LISTA_LEADS) da Brevo.
"""
import html
import os
import threading
from datetime import date, timedelta

import requests

REMETENTE = {"name": "Equipe Planner Organiza", "email": "contato@plannerorganiza.com.br"}
RESPONDER_PARA = {"name": "Equipe Planner Organiza", "email": "contato@plannerorganiza.com.br"}
APP_URL = "https://app.plannerorganiza.com.br"
PLAY = "https://play.google.com/store/apps/details?id=com.plannerorganiza.app&referrer=utm_source%3Demail%26utm_medium%3Dboas_vindas"
APP_STORE = "https://apps.apple.com/br/app/planner-organiza/id6832855561"
DIAS_MAXIMOS = 2
LISTA_LEADS = 7  # lista "Leads Planner Organiza" na Brevo (a mesma da landing)


def primeiro_nome(nome: str, email: str = "") -> str:
    n = (nome or "").strip().split()
    if not n:
        return ""
    p = n[0]
    genericos = {"usuário", "usuario", "usuária", "usuaria", "cliente", "teste"}
    if p.lower() in genericos or "@" in p:
        return ""
    return p[:1].upper() + p[1:]


def montar(nome: str, email: str):
    """(assunto, html, texto)."""
    pn = primeiro_nome(nome, email)
    ola = f"Oi, {html.escape(pn)}!" if pn else "Oi!"
    assunto = f"Bem-vinda ao Planner, {pn}! Vamos montar sua 1ª proposta?" if pn else \
        "Bem-vinda ao Planner! Vamos montar sua 1ª proposta?"
    corpo = f"""<!doctype html><html><body style="margin:0;background:#F6F1E7;font-family:Arial,Helvetica,sans-serif;color:#16283E">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F6F1E7;padding:24px 0"><tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden">
<tr><td style="background:#0D1B2A;padding:22px 28px;color:#C9A84C;font-family:Georgia,serif;font-size:22px">Planner <span style="color:#fff">Organiza</span></td></tr>
<tr><td style="padding:28px;font-size:15px;line-height:1.6">
<p style="margin:0 0 14px;font-size:17px"><b>{ola}</b></p>
<p style="margin:0 0 14px">Aqui é a equipe do Planner Organiza. Que bom ter você aqui!</p>
<p style="margin:0 0 14px">Criamos o Planner para a personal organizer gastar menos tempo com orçamento e mais tempo com as clientes.
O melhor jeito de sentir a diferença é fazer a sua <b>primeira proposta</b> hoje. Leva uns 5 minutos:</p>
<ol style="margin:0 0 18px;padding-left:20px">
<li style="margin-bottom:6px"><b>Cadastre um cliente</b> (só o nome já basta).</li>
<li style="margin-bottom:6px"><b>Crie a proposta</b> com o serviço e o valor.</li>
<li style="margin-bottom:6px"><b>Gere o PDF</b> com a sua marca e mande pelo WhatsApp.</li>
</ol>
<p style="margin:0 0 22px;text-align:center"><a href="{APP_URL}" style="background:#C9A84C;color:#0D1B2A;text-decoration:none;font-weight:bold;padding:13px 26px;border-radius:24px;display:inline-block">Criar minha primeira proposta</a></p>
<p style="margin:0 0 14px">Você tem <b>7 dias grátis com tudo liberado</b>. Use também no celular:
<a href="{PLAY}" style="color:#8A6D12">Android</a> · <a href="{APP_STORE}" style="color:#8A6D12">iPhone</a>.</p>
<p style="margin:0 0 14px">Ficou com alguma dúvida? É só <b>responder este e-mail</b> que a gente te ajuda.</p>
<p style="margin:18px 0 0">Um abraço,<br><b>Equipe Planner Organiza</b><br><span style="color:#6B7C94;font-size:13px">Gestão para personal organizers</span></p>
</td></tr>
<tr><td style="padding:16px 28px;background:#FBF6E9;color:#6B7C94;font-size:12px">Você recebeu este e-mail porque criou uma conta no Planner Organiza.</td></tr>
</table></td></tr></table></body></html>"""
    texto = (f"{ola}\n\nAqui é a equipe do Planner Organiza. Que bom ter você aqui!\n\n"
             "Faça a sua primeira proposta hoje (uns 5 minutos):\n1. Cadastre um cliente.\n2. Crie a proposta com o "
             "serviço e o valor.\n3. Gere o PDF com a sua marca e mande pelo WhatsApp.\n\n"
             f"Entrar: {APP_URL}\nAndroid: {PLAY}\niPhone: {APP_STORE}\n\nVocê tem 7 dias grátis com tudo liberado. "
             "Ficou com dúvida? É só responder este e-mail.\n\nUm abraço,\nEquipe Planner Organiza")
    return assunto, corpo, texto


def _resultado(engine, uid, ok, detalhe):
    """Guarda o resultado do envio no banco (os registros do site saem atrasados)."""
    if engine is None or not uid:
        return
    try:
        from utils import funil
        funil.registrar(engine, uid, "boas_vindas_ok" if ok else "boas_vindas_erro", str(detalhe)[:20])
    except Exception as e:
        print(f"[boas-vindas] não gravou o resultado: {e}", flush=True)


def _salvar_contato(chave: str, email: str, nome: str) -> bool:
    """Guarda a conta nova na lista de leads da Brevo (precisa da permissão "contato" na chave)."""
    atributos = {"FIRSTNAME": primeiro_nome(nome, email)} if primeiro_nome(nome, email) else {}
    try:
        r = requests.post("https://api.brevo.com/v3/contacts", timeout=15,
                          headers={"api-key": chave, "accept": "application/json", "content-type": "application/json"},
                          json={"email": email, "listIds": [LISTA_LEADS], "updateEnabled": True, "attributes": atributos})
        ok = r.status_code in (200, 201, 204)
        print(f"[boas-vindas] contato {email}: {'salvo' if ok else f'erro {r.status_code} {r.text[:200]}'}", flush=True)
        return ok
    except Exception as e:
        print(f"[boas-vindas] contato {email}: erro {e}", flush=True)
        return False


def _enviar(email: str, nome: str, engine=None, uid=None) -> bool:
    chave = (os.environ.get("BREVO_API_KEY") or "").strip()
    if chave:
        _salvar_contato(chave, email, nome)
    if not chave:
        print(f"[boas-vindas] BREVO_API_KEY não configurada: e-mail para {email} não enviado", flush=True)
        _resultado(engine, uid, False, "sem chave")
        return False
    assunto, corpo, texto = montar(nome, email)
    try:
        r = requests.post("https://api.brevo.com/v3/smtp/email", timeout=15,
                          headers={"api-key": chave, "accept": "application/json", "content-type": "application/json"},
                          json={"sender": REMETENTE, "replyTo": RESPONDER_PARA, "to": [{"email": email}],
                                "subject": assunto, "htmlContent": corpo, "textContent": texto,
                                "tags": ["boas-vindas"]})
        ok = r.status_code in (200, 201, 202)
        print(f"[boas-vindas] {email}: {'enviado' if ok else f'erro {r.status_code} {r.text[:300]}'}", flush=True)
        _resultado(engine, uid, ok, f"HTTP {r.status_code}")
        return ok
    except Exception as e:
        print(f"[boas-vindas] {email}: erro {e}", flush=True)
        _resultado(engine, uid, False, type(e).__name__)
        return False


def enviar_se_nova(engine, uid: str, email: str, nome: str = "", data_cadastro=None, em_segundo_plano=True) -> bool:
    """Envia uma vez por conta, só para contas criadas há no máximo 2 dias. Devolve True se disparou."""
    if not uid or not email or "@" not in email:
        return False
    if data_cadastro and data_cadastro < date.today() - timedelta(days=DIAS_MAXIMOS):
        return False
    from utils import funil
    if not funil.registrar(engine, uid, "boas_vindas", ""):  # já enviado (ou erro ao gravar)
        return False
    if em_segundo_plano:
        threading.Thread(target=_enviar, args=(email.strip(), nome, engine, uid), daemon=True).start()
    else:
        _enviar(email.strip(), nome, engine, uid)
    return True
