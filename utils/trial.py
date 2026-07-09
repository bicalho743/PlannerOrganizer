"""
Regra de trial/assinatura — fonte única compartilhada na web.

Trial de 7 dias a partir de `data_cadastro`. Depois disso, sem plano pago,
o acesso é bloqueado (quem chama aplica o bloqueio). Plano pro/ativo/admin,
role admin ou e-mail na allowlist (TRIAL_ISENTOS) ficam isentos.

Espelha a lógica do app mobile em app/_layout.tsx (diasPassados < 7).
"""
import os
from datetime import datetime, date

DIAS_TRIAL = 7


def _isento_por_email(perfil) -> bool:
    """E-mails em TRIAL_ISENTOS (separados por vírgula) nunca são bloqueados.
    Rede de segurança para o dono/admins não se trancarem para fora."""
    brutos = os.environ.get("TRIAL_ISENTOS", "")
    isentos = {e.strip().lower() for e in brutos.split(",") if e.strip()}
    email = ((perfil or {}).get("email") or "").strip().lower()
    return bool(email) and email in isentos


def is_pro(perfil) -> bool:
    """pro/ativo/admin (ou role admin) contam como plano ativo — isentos do trial."""
    if not perfil:
        return False
    plano = (perfil.get("plano") or "gratuito").lower()
    role = (perfil.get("role") or "").lower()
    return plano in ("pro", "ativo", "admin") or role == "admin"


def _data_cadastro_para_date(dc):
    if isinstance(dc, datetime):
        return dc.date()
    if isinstance(dc, date):
        return dc
    if isinstance(dc, str) and dc.strip():
        try:
            return datetime.fromisoformat(dc[:10]).date()
        except Exception:
            return None
    return None


def dias_restantes_trial(perfil, dias_trial: int = DIAS_TRIAL) -> int:
    """Dias restantes do trial (0 se já expirou). Sem data confiável, assume
    início hoje — nunca bloqueia por falta de dado."""
    dc = _data_cadastro_para_date((perfil or {}).get("data_cadastro"))
    if dc is None:
        return dias_trial
    dias_passados = (date.today() - dc).days
    return max(0, dias_trial - dias_passados)


def trial_expirado(perfil, dias_trial: int = DIAS_TRIAL) -> bool:
    """True quando NÃO é plano pago/isento e o trial de N dias já acabou."""
    if not perfil:
        return False  # perfil não carregado: fail-open, não bloqueia
    if is_pro(perfil) or _isento_por_email(perfil):
        return False
    return dias_restantes_trial(perfil, dias_trial) <= 0
