"""
Fonte única de verdade para o vocabulário do campo `propostas.status`.

Banco usa apenas valores canônicos em snake_case minúsculo.
Interface (badges, PDFs, e-mails) exibe rótulos amigáveis via label_for().
Entradas legadas (CSV, formulários antigos) são convertidas com normalize().
"""

STATUS_EM_ABERTO = "em_aberto"
STATUS_APROVADA = "aprovada"
STATUS_RECUSADA = "recusada"
STATUS_EM_EXECUCAO = "em_execucao"
STATUS_FINALIZADA = "finalizada"

CANONICAL_STATUSES = (
    STATUS_EM_ABERTO,
    STATUS_APROVADA,
    STATUS_RECUSADA,
    STATUS_EM_EXECUCAO,
    STATUS_FINALIZADA,
)

STATUS_LABELS = {
    STATUS_EM_ABERTO: "Em Aberto",
    STATUS_APROVADA: "Aprovada",
    STATUS_RECUSADA: "Recusada",
    STATUS_EM_EXECUCAO: "Em Execução",
    STATUS_FINALIZADA: "Finalizada",
}

_LEGACY_TO_CANONICAL = {
    "em elaboracao": STATUS_EM_ABERTO,
    "em elaboração": STATUS_EM_ABERTO,
    "aberta": STATUS_EM_ABERTO,
    "aguardando": STATUS_EM_ABERTO,
    "aguardando aprovacao": STATUS_EM_ABERTO,
    "aguardando aprovação": STATUS_EM_ABERTO,
    "em analise": STATUS_EM_ABERTO,
    "em análise": STATUS_EM_ABERTO,
    "aprovada": STATUS_APROVADA,
    "recusada": STATUS_RECUSADA,
    "em execucao": STATUS_EM_EXECUCAO,
    "em execução": STATUS_EM_EXECUCAO,
    "finalizada": STATUS_FINALIZADA,
    "fechada": STATUS_FINALIZADA,
    "concluida": STATUS_FINALIZADA,
    "concluída": STATUS_FINALIZADA,
}


def normalize(raw):
    """Converte qualquer rótulo (legado ou canônico) para o valor canônico.

    Retorna None se o valor for vazio/None. Retorna o input original se não
    reconhecido (não silencia entrada inesperada).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    low = s.lower()
    if low in CANONICAL_STATUSES:
        return low
    return _LEGACY_TO_CANONICAL.get(low, s)


def normalize_strict(raw):
    """Como normalize(), mas REJEITA valores desconhecidos com ValueError.

    Use nos pontos de escrita (ORM/SQL) para impedir que rótulos fora do
    vocabulário canônico sejam gravados no banco. Retorna None para vazio/None
    (interpretado como "não atualizar este campo").
    """
    canonical = normalize(raw)
    if canonical is None:
        return None
    if canonical not in CANONICAL_STATUSES:
        raise ValueError(
            f"Status de proposta inválido: {raw!r}. "
            f"Valores aceitos: {', '.join(CANONICAL_STATUSES)}"
        )
    return canonical


def label_for(status):
    """Retorna o rótulo amigável para exibição. Faz normalize() defensivo."""
    if status is None:
        return ""
    canonical = normalize(status)
    return STATUS_LABELS.get(canonical, str(status))


# Propostas "ativas" = ainda não concluídas (nem finalizada, nem recusada).
STATUS_ATIVAS = (STATUS_EM_ABERTO, STATUS_APROVADA, STATUS_EM_EXECUCAO)


def is_ativa(status):
    """True para propostas ainda não concluídas (em aberto, aprovada ou em execução)."""
    return normalize(status) in STATUS_ATIVAS


def is_em_aberto(status):
    return normalize(status) == STATUS_EM_ABERTO


def is_aprovada(status):
    return normalize(status) == STATUS_APROVADA


def is_recusada(status):
    return normalize(status) == STATUS_RECUSADA


def is_em_execucao(status):
    return normalize(status) == STATUS_EM_EXECUCAO


def is_finalizada(status):
    return normalize(status) == STATUS_FINALIZADA


def is_aberto_ou_aguardando(status):
    """True para qualquer estado pré-aprovação (compat com filtros legados)."""
    return normalize(status) == STATUS_EM_ABERTO
