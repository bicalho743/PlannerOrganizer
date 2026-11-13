"""
De onde vem a assinatura de cada conta: site (Stripe), Google Play ou App Store.

A conta tem um plano só (`perfis.plano`), valha de onde valer. `perfis.assinatura_origem` guarda
o canal ('stripe', 'google' ou 'apple') e `perfis.assinatura_expira_em` a validade informada pela
loja. Um canal só derruba o plano que ele mesmo deu: o cancelamento de uma assinatura antiga do
site não tira o acesso de quem passou a pagar pelo celular, e vice-versa.

As compras das lojas chegam pelo RevenueCat, que usa como identificador o UID do Firebase:
- webhook (`/webhook/revenuecat`), com o cabeçalho Authorization igual a REVENUECAT_WEBHOOK_AUTH;
- conferência direta (`sincronizar_revenuecat`), chamada pelo app logo depois da compra, com a
  chave secreta REVENUECAT_SECRET_KEY, para liberar na hora sem esperar o webhook.
"""
import os
from datetime import datetime, timezone

import requests
from sqlalchemy import text

ENTITLEMENT = "pro"
LOJAS = {"APP_STORE": "apple", "MAC_APP_STORE": "apple", "PLAY_STORE": "google",
         "app_store": "apple", "mac_app_store": "apple", "play_store": "google"}

# eventos que dão (ou mantêm) acesso; cancelamento e problema de cobrança não tiram nada:
# a pessoa usa até o fim do período pago (e a loja tenta cobrar de novo)
EVENTOS_ATIVA = {"INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION", "PRODUCT_CHANGE",
                 "SUBSCRIPTION_EXTENDED", "TEMPORARY_ENTITLEMENT_GRANT", "NON_RENEWING_PURCHASE"}
EVENTOS_ENCERRA = {"EXPIRATION"}


def _engine():
    from utils.database import engine
    return engine


def _ms_para_data(ms):
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).replace(tzinfo=None) if ms else None
    except Exception:
        return None


def dados_assinatura(uid: str) -> dict:
    """{'origem': 'stripe'|'google'|'apple'|None, 'expira_em': datetime|None}."""
    try:
        with _engine().begin() as c:
            r = c.execute(text("SELECT assinatura_origem, assinatura_expira_em FROM perfis WHERE usuario_id = :u"),
                          {"u": uid}).fetchone()
        if r:
            return {"origem": r[0], "expira_em": r[1]}
    except Exception as e:
        print(f"[assinatura] erro ao ler {uid}: {e}")
    return {"origem": None, "expira_em": None}


def ativar_loja(uid: str, origem: str, expira_em=None) -> bool:
    with _engine().begin() as c:
        r = c.execute(text("UPDATE perfis SET plano = 'pro', ativo = TRUE, assinatura_origem = :o, "
                           "assinatura_expira_em = :e WHERE usuario_id = :u"),
                      {"o": origem, "e": expira_em, "u": uid})
        return r.rowcount > 0


def encerrar_loja(uid: str, origem: str) -> bool:
    """Tira o plano só se ele veio desta loja."""
    with _engine().begin() as c:
        r = c.execute(text("UPDATE perfis SET plano = 'cancelado' WHERE usuario_id = :u "
                           "AND assinatura_origem = :o AND plano = 'pro'"), {"o": origem, "u": uid})
        return r.rowcount > 0


def _contas_do_evento(ev: dict):
    """UIDs do evento que existem em perfis (o app entra no RevenueCat com o UID do Firebase;
    os ids anônimos '$RCAnonymousID:...' não são contas)."""
    ids = [ev.get("app_user_id"), ev.get("original_app_user_id")] + list(ev.get("aliases") or [])
    ids = [i for i in dict.fromkeys(ids) if i and not str(i).startswith("$RCAnonymousID")]
    if not ids:
        return []
    with _engine().begin() as c:
        return [r[0] for r in c.execute(text("SELECT usuario_id FROM perfis WHERE usuario_id = ANY(:ids)"),
                                        {"ids": ids})]


def aplicar_evento_revenuecat(ev: dict) -> str:
    tipo = ev.get("type") or ""
    if tipo == "TEST":
        return "teste"
    if tipo == "TRANSFER":  # a compra passou de uma conta para outra (restaurar com outro login)
        origem = LOJAS.get(ev.get("store") or "", "")
        for uid in ev.get("transferred_from") or []:
            if origem:
                encerrar_loja(uid, origem)
        for uid in ev.get("transferred_to") or []:
            if origem and not str(uid).startswith("$RCAnonymousID"):
                sincronizar_revenuecat(uid)
        return "transferida"
    origem = LOJAS.get(ev.get("store") or "")
    if not origem:
        return "loja ignorada"  # compras feitas pelo site são tratadas pelo webhook do Stripe
    if ev.get("entitlement_ids") is not None and ENTITLEMENT not in (ev.get("entitlement_ids") or []):
        return "sem o acesso pro"
    contas = _contas_do_evento(ev)
    if not contas:
        print(f"[revenuecat] {tipo}: nenhuma conta para {ev.get('app_user_id')}")
        return "conta não encontrada"
    for uid in contas:
        if tipo in EVENTOS_ATIVA:
            ativar_loja(uid, origem, _ms_para_data(ev.get("expiration_at_ms")))
        elif tipo in EVENTOS_ENCERRA:
            encerrar_loja(uid, origem)
        print(f"[revenuecat] {tipo} {origem}: conta={uid}")
    return "ok"


def _data_iso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None) if s else None
    except Exception:
        return None


def sincronizar_revenuecat(uid: str) -> dict:
    """Pergunta ao RevenueCat se a conta tem o acesso 'pro' ativo por uma loja e grava o resultado.
    Devolve {'pro': bool, 'origem': ...}. Sem a chave configurada, não faz nada."""
    chave = os.environ.get("REVENUECAT_SECRET_KEY", "")
    if not chave:
        return {"pro": None, "origem": None, "motivo": "REVENUECAT_SECRET_KEY não configurada"}
    r = requests.get(f"https://api.revenuecat.com/v1/subscribers/{uid}",
                     headers={"Authorization": f"Bearer {chave}"}, timeout=15)
    if r.status_code != 200:
        print(f"[revenuecat] consulta {uid}: HTTP {r.status_code}")
        return {"pro": None, "origem": None, "motivo": f"HTTP {r.status_code}"}
    sub = (r.json() or {}).get("subscriber") or {}
    ent = (sub.get("entitlements") or {}).get(ENTITLEMENT)
    agora = datetime.utcnow()
    if ent:
        expira = _data_iso(ent.get("expires_date"))
        assinatura = (sub.get("subscriptions") or {}).get(ent.get("product_identifier") or "") or {}
        origem = LOJAS.get(assinatura.get("store") or "")
        if origem and (expira is None or expira > agora):
            ativar_loja(uid, origem, expira)
            return {"pro": True, "origem": origem}
    atual = dados_assinatura(uid).get("origem")
    if atual in ("google", "apple"):
        encerrar_loja(uid, atual)
    return {"pro": False, "origem": atual}
