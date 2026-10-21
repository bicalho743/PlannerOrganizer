from datetime import date

import pandas as pd

from utils.indicadores import movimentos, entrou_gastou, previsto, funil

HOJE = date(2026, 10, 21)


def _fin(linhas):
    return pd.DataFrame(linhas, columns=["tipo", "classificacao", "status", "valor", "data", "data_recebimento", "categoria", "descricao"])


def test_lucro_do_mes_usa_data_em_que_o_dinheiro_entrou():
    fin = _fin([
        ("Receita", "contas_a_receber", "Recebido", "1000", "2026-09-30", "2026-10-02", "Serviço", "a"),  # recebida em outubro
        ("receita", None, "Recebido", 500.0, "2026-10-10", None, "Serviço", "b"),
        ("Receita", "receita", "Pendente", 800.0, "2026-10-25", None, "Serviço", "c"),  # ainda não entrou
        ("Despesa", "contas_a_pagar", "Pago", 300.0, "2026-10-05", None, "Material", "d"),
        ("despesa", None, "Pago", 99.0, "2026-09-05", None, "Material", "e"),  # mês anterior
    ])
    mov = movimentos(fin)
    assert entrou_gastou(mov, 2026, 10) == (1500.0, 300.0)
    assert previsto(mov, 2026, 10) == (800.0, 0.0)


def test_movimentos_vazio():
    assert entrou_gastou(movimentos(pd.DataFrame()), 2026, 10) == (0.0, 0.0)


def test_funil_conta_so_propostas_respondidas_na_conversao():
    props = pd.DataFrame([
        ("em_aberto", 1000, "2026-10-01"),
        ("Aprovada", 2000, "2026-09-15"),
        ("finalizada", 3000, "2026-08-01"),
        ("recusada", 500, "2026-10-10"),
        ("finalizada", 9999, "2025-01-01"),  # fora da janela de 90 dias
    ], columns=["status", "valor", "data_proposta"])
    f = funil(props, HOJE)
    assert (f["enviadas"], f["aguardando"], f["fechadas"], f["concluidas"], f["recusadas"]) == (4, 1, 2, 1, 1)
    assert f["valor_fechado"] == 5000 and f["valor_aguardando"] == 1000
    assert abs(f["conversao"] - 2 / 3) < 1e-9


def test_funil_sem_respostas_nao_inventa_taxa():
    props = pd.DataFrame([("em_aberto", 1000, "2026-10-01")], columns=["status", "valor", "data_proposta"])
    assert funil(props, HOJE)["conversao"] is None
    assert funil(pd.DataFrame(), HOJE)["enviadas"] == 0
