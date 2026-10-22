"""Cálculos da aba Precificação (utils/precificacao.py), com valores conferidos à mão."""
import pytest

from utils import precificacao as pr

P = dict(pr.PADROES)  # renda 5000, custos 80+400+150, 12 dias × 6 h, sem imposto, margem 20%, assistente R$ 30/h


def test_hora_minima_cobre_renda_e_custos_do_mes():
    assert pr.custos_fixos(P) == 630
    assert pr.horas_vendidas(P) == 72
    assert pr.hora_minima(P) == pytest.approx(5630 / 72)            # R$ 78,19
    assert pr.hora_sugerida(P) == pytest.approx(5630 / 72 * 1.2)    # R$ 93,83


def test_imposto_sobre_a_venda_entra_por_fora():
    p = dict(P, imposto_pct=6)
    assert pr.hora_minima(p) == pytest.approx(5630 / 72 / 0.94)
    # depois de pagar 6% sobre a hora mínima, sobra a hora líquida
    assert pr.hora_minima(p) * 0.94 == pytest.approx(pr.hora_liquida(p))


def test_projeto_com_assistente_divide_as_horas_e_soma_o_custo_dela():
    r = pr.preco_projeto(P, horas_ambientes=10, assistentes=1, deslocamento=50)
    assert r["pessoas"] == 2 and r["suas_horas"] == 5 and r["horas_assistentes"] == 5
    assert r["custo_equipe"] == 150 and r["custos_diretos"] == 200
    trabalho = 5 * 5630 / 72
    assert r["preco_minimo"] == pytest.approx(trabalho + 200)
    assert r["preco_sugerido"] == pytest.approx((trabalho + 200) * 1.2)
    assert r["lucro"] == pytest.approx(r["preco_sugerido"] - 200)
    assert r["hora_efetiva"] == pytest.approx(r["lucro"] / 5)
    assert r["dias_no_local"] == pytest.approx(5 / 6)


def test_complexidade_multiplica_as_horas():
    leve = pr.preco_projeto(P, 10, complexidade=pr.COMPLEXIDADE["Leve"])
    pesada = pr.preco_projeto(P, 10, complexidade=pr.COMPLEXIDADE["Pesada (muito acúmulo)"])
    assert leve["horas_trabalho"] == pytest.approx(8) and pesada["horas_trabalho"] == pytest.approx(13)
    assert pesada["preco_sugerido"] > leve["preco_sugerido"]


def test_preco_com_imposto_deixa_o_mesmo_valor_liquido():
    p = dict(P, imposto_pct=6)
    sem = pr.preco_projeto(P, 10, deslocamento=50)
    com = pr.preco_projeto(p, 10, deslocamento=50)
    assert com["preco_sugerido"] * 0.94 == pytest.approx(sem["preco_sugerido"])
    assert com["lucro"] == pytest.approx(sem["lucro"])


def test_sem_horas_nao_divide_por_zero():
    p = dict(P, dias_mes=0)
    assert pr.hora_minima(p) == 0
    assert pr.preco_projeto(P, 0)["hora_efetiva"] == 0
