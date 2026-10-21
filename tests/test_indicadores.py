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


def test_retirada_fica_fora_do_gasto_e_cores_sao_fixas():
    from utils.indicadores import retirado, cor_categoria, por_categoria, mei
    fin = _fin([
        ("Receita", "receita", "Recebido", 4000.0, "2026-10-03", None, "Serviços de organização", "x"),
        ("Receita", "receita", "Recebido", 1000.0, "2026-10-04", None, "Servicos de organizacao", "y"),
        ("Despesa", "contas_a_pagar", "Pago", 1500.0, "2026-10-05", None, "Pró-labore / retirada", "salário"),
        ("Despesa", "contas_a_pagar", "Pago", 86.05, "2026-10-20", None, "Impostos (DAS)", "DAS outubro"),
    ])
    mov = movimentos(fin)
    assert entrou_gastou(mov, 2026, 10) == (5000.0, 86.05)
    assert retirado(mov, 2026, 10) == 1500.0
    assert por_categoria(mov, 2026, 10, "entra") == [("Serviços de organização", 5000.0)]
    assert cor_categoria("Serviços adicionais") != cor_categoria("Serviços de organização")
    assert cor_categoria("SERVICOS DE ORGANIZACAO") == cor_categoria("Serviços de organização")
    m = mei(mov, HOJE)
    assert m["faturado"] == 5000.0 and m["das_pago"] is True and m["projecao"] > 5000


def test_mes_so_com_entradas_nao_quebra():
    from utils.indicadores import retirado
    mov = movimentos(_fin([("Receita", "receita", "Recebido", 100.0, "2026-10-03", None, "Serviços", "x")]))
    assert entrou_gastou(mov, 2026, 10) == (100.0, 0.0)
    assert retirado(mov, 2026, 10) == 0.0
