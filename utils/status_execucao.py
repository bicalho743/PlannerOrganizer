"""
Fonte única de verdade para o vocabulário do campo `propostas.status_execucao`.

Este campo registra a FASE DE EXECUÇÃO da proposta (distinto do campo `status`,
cujo vocabulário vive em `utils/proposta_status.py`).

Historicamente o mesmo conceito era gravado com rótulos diferentes em pontos
diferentes do código ("Concluída", "Vendida", "Iniciada"), o que fazia
propostas concluídas sumirem das telas de finalizadas/acompanhamento (que
filtram por "Finalizada"/"Em execução"). Aqui definimos o conjunto canônico e
um normalizador único para que toda gravação use o mesmo vocabulário.
"""

EXEC_NAO_INICIADA = "Não iniciada"
EXEC_EM_EXECUCAO = "Em execução"
EXEC_FINALIZADA = "Finalizada"
EXEC_CANCELADA = "Cancelada"

CANONICAL_STATUSES = (
    EXEC_NAO_INICIADA,
    EXEC_EM_EXECUCAO,
    EXEC_FINALIZADA,
    EXEC_CANCELADA,
)

_CANON_BY_LOWER = {s.lower(): s for s in CANONICAL_STATUSES}

_LEGACY_TO_CANONICAL = {
    "nao iniciada": EXEC_NAO_INICIADA,
    "não iniciada": EXEC_NAO_INICIADA,
    "iniciada": EXEC_EM_EXECUCAO,
    "em execucao": EXEC_EM_EXECUCAO,
    "em execução": EXEC_EM_EXECUCAO,
    "concluida": EXEC_FINALIZADA,
    "concluída": EXEC_FINALIZADA,
    "vendida": EXEC_FINALIZADA,
    "finalizada": EXEC_FINALIZADA,
    "cancelada": EXEC_CANCELADA,
}


def normalize(raw):
    """Converte qualquer rótulo (legado ou canônico) para o valor canônico.

    Retorna None se o valor for vazio/None. Retorna o input original (sem
    alterar) se não for reconhecido, para não silenciar entrada inesperada.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    low = s.lower()
    if low in _CANON_BY_LOWER:
        return _CANON_BY_LOWER[low]
    return _LEGACY_TO_CANONICAL.get(low, s)


def is_nao_iniciada(status):
    return normalize(status) == EXEC_NAO_INICIADA


def is_em_execucao(status):
    return normalize(status) == EXEC_EM_EXECUCAO


def is_finalizada(status):
    return normalize(status) == EXEC_FINALIZADA


def is_cancelada(status):
    return normalize(status) == EXEC_CANCELADA
