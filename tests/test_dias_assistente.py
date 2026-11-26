from utils import precificacao as pr


def _p():
    p = dict(pr.PADROES)
    p["valor_hora_assistente"] = 25
    p["horas_dia"] = 6
    return p


def test_sem_dias_assistente_divide_igual():
    o = pr.orcamento_completo(_p(), "organizacao", horas_ambientes=24, assistentes=1)
    assert o["suas_horas"] == 12 and o["horas_cada_assistente"] == 12 and o["assistente"] == 300


def test_assistente_so_um_dia():
    o = pr.orcamento_completo(_p(), "organizacao", horas_ambientes=24, assistentes=1, dias_assistente=1)
    assert o["horas_cada_assistente"] == 6 and o["assistente"] == 150
    assert o["suas_horas"] == 18 and o["dias"] == 3 and o["dias_assistente"] == 1


def test_dias_a_mais_nao_aumenta():
    base = pr.orcamento_completo(_p(), "organizacao", horas_ambientes=24, assistentes=1)
    o = pr.orcamento_completo(_p(), "organizacao", horas_ambientes=24, assistentes=1, dias_assistente=10)
    assert o["total"] == base["total"]
