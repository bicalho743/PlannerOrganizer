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


def normalize_strict(raw):
    """Como normalize(), mas REJEITA valores desconhecidos com ValueError.

    Use nos pontos de escrita para impedir que `status_execucao` fora do
    vocabulário canônico seja gravado no banco. Retorna None para vazio/None
    (interpretado como "não atualizar este campo").
    """
    canonical = normalize(raw)
    if canonical is None:
        return None
    if canonical not in CANONICAL_STATUSES:
        raise ValueError(
            f"status_execucao inválido: {raw!r}. "
            f"Valores aceitos: {', '.join(CANONICAL_STATUSES)}"
        )
    return canonical


def derive_exec_from_status(status):
    """Retorna o `status_execucao` canônico implícito por um `status` principal.

    Recebe um status principal (legado ou canônico, ex.: "finalizada",
    "Concluída", "em_execucao") e devolve a fase de execução correspondente
    para manter os DOIS campos alinhados. Retorna None quando o status não
    determina uma fase específica (não reconhecido).

    Mantém a regra "proposta finalizada = dois campos": todo caminho de
    escrita que mexe em `status` deve manter `status_execucao` coerente.
    """
    from utils.proposta_status import (
        normalize as _norm_status,
        STATUS_EM_ABERTO, STATUS_APROVADA, STATUS_RECUSADA,
        STATUS_EM_EXECUCAO, STATUS_FINALIZADA,
    )
    canon = _norm_status(status)
    return {
        STATUS_EM_ABERTO: EXEC_NAO_INICIADA,
        STATUS_APROVADA: EXEC_NAO_INICIADA,
        STATUS_EM_EXECUCAO: EXEC_EM_EXECUCAO,
        STATUS_FINALIZADA: EXEC_FINALIZADA,
        STATUS_RECUSADA: EXEC_CANCELADA,
    }.get(canon)


def is_nao_iniciada(status):
    return normalize(status) == EXEC_NAO_INICIADA


def is_em_execucao(status):
    return normalize(status) == EXEC_EM_EXECUCAO


def is_finalizada(status):
    return normalize(status) == EXEC_FINALIZADA


def is_cancelada(status):
    return normalize(status) == EXEC_CANCELADA
