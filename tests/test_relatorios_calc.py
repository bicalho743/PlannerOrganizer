from datetime import date

import pandas as pd

from utils import relatorios_calc as rc

HOJE = date(2026, 10, 21)


def _fin(linhas):
    return pd.DataFrame(linhas, columns=["tipo", "classificacao", "status", "valor", "data", "data_recebimento",
                                         "categoria", "descricao", "proposta_id"])


FIN = _fin([
    ("Receita", "receita", "Recebido", 3000.0, "2026-10-05", None, "Serviços de organização", "a", 1),
    ("Receita", "receita", "Recebido", 1000.0, "2026-09-10", None, "Serviços de organização", "b", 2),
    ("Despesa", None, "Pago", 600.0, "2026-10-06", None, "Assistente", "c", None),          # custo direto (categoria)
    ("Despesa", None, "Pago", 200.0, "2026-10-07", None, "Material", "d", 1),               # custo direto (proposta)
    ("Despesa", None, "Pago", 150.0, "2026-10-08", None, "Internet", "e", None),            # despesa fixa
    ("Despesa", None, "Pago", 1000.0, "2026-10-09", None, "Pró-labore / retirada", "f", None),
    ("Receita", "contas_a_receber", "Pendente", 800.0, "2026-10-01", None, "Serviços", "g", None),   # atrasada
    ("Receita", "contas_a_receber", "Pendente", 500.0, "2026-12-01", None, "Serviços", "h", None),   # 41 dias
    ("Despesa", "contas_a_pagar", "Pendente", 90.0, "2026-10-30", None, "Internet", "i", None),
])

PROPS = pd.DataFrame([
    # id, numero, cliente_id, cliente_nome, valor, status, tipo, data_proposta, data_aprovacao
    (1, 101, 10, "Ana", 3000.0, "finalizada", "Organização completa", "2026-09-20", "2026-10-01"),
    (2, 102, 11, "Bia", 1000.0, "aprovada", "Consultoria", "2026-09-01", "2026-09-05"),
    (3, 103, 10, "Ana", 1500.0, "em_execucao", "Organização completa", "2026-10-10", "2026-10-12"),
    (4, 104, 12, "Carla", 2000.0, "recusada", "Organização completa", "2026-10-03", None),
    (5, 105, 13, "Duda", 1200.0, "em_aberto", "Consultoria", "2026-10-02", None),
], columns=["id", "numero", "cliente_id", "cliente_nome", "valor", "status", "tipo_proposta", "data_proposta", "data_aprovacao"])

CLIENTES = pd.DataFrame([(10, "Ana", "Instagram"), (11, "Bia", "indicação da Ana"), (12, "Carla", None), (13, "Duda", "google")],
                        columns=["id", "nome", "origem_cliente"])


def test_periodos():
    assert rc.intervalo("Este mês", HOJE) == (date(2026, 10, 1), date(2026, 10, 31))
    assert rc.intervalo("Mês passado", date(2026, 1, 15)) == (date(2025, 12, 1), date(2025, 12, 31))
    assert rc.intervalo("Últimos 3 meses", HOJE) == (date(2026, 8, 1), date(2026, 10, 31))
    assert rc.periodo_anterior(date(2026, 8, 1), date(2026, 10, 31)) == (date(2026, 5, 1), date(2026, 7, 31))
    assert rc.periodo_anterior(date(2026, 3, 1), date(2026, 3, 31)) == (date(2026, 2, 1), date(2026, 2, 28))
    assert rc.periodo_anterior(date(2026, 10, 10), date(2026, 10, 19)) == (date(2026, 9, 30), date(2026, 10, 9))
    assert rc.mesmo_periodo_ano_passado(date(2024, 2, 1), date(2024, 2, 29)) == (date(2023, 2, 1), date(2023, 2, 28))
    assert rc.variacao(150, 100) == 0.5 and rc.variacao(10, 0) is None
    # mês em andamento: outubro até 21 contra setembro até 21
    i, f = rc.intervalo("Este mês", HOJE)
    ci, cf = rc.periodo_anterior(i, f)
    assert rc.ate_hoje(i, f, ci, cf, HOJE) == (date(2026, 10, 1), HOJE, date(2026, 9, 1), date(2026, 9, 21), True)
    assert rc.ate_hoje(date(2026, 9, 1), date(2026, 9, 30), ci, cf, HOJE)[4] is False


def test_resultado_separa_custo_direto_despesa_e_retirada():
    mov = rc.movimentos_rel(FIN)
    r = rc.resultado(mov, date(2026, 10, 1), date(2026, 10, 31))
    assert r["faturamento"] == 3000.0
    assert r["custos"] == 800.0          # assistente + material ligado à proposta
    assert r["despesas"] == 150.0
    assert r["retiradas"] == 1000.0
    assert r["lucro"] == 2050.0 and abs(r["margem"] - 2050 / 3000) < 1e-9
    assert r["caixa"] == 1050.0
    serie = rc.serie_mensal(mov, date(2026, 9, 1), date(2026, 10, 31))
    assert list(serie["faturamento"]) == [1000.0, 3000.0]


def test_destaques_explicam_a_variacao():
    mov = rc.movimentos_rel(FIN)
    a = rc.resultado(mov, date(2026, 10, 1), date(2026, 10, 31))
    b = rc.resultado(mov, date(2026, 9, 1), date(2026, 9, 30))
    frases = rc.destaques(a, b, rc.por_categoria(mov, date(2026, 10, 1), date(2026, 10, 31), "sai"),
                          rc.por_categoria(mov, date(2026, 9, 1), date(2026, 9, 30), "sai"), "set/2026")
    assert frases[0] == "O lucro subiu R$ 1.050,00 em relação a set/2026, principalmente pelo faturamento maior (+R$ 2.000,00)."
    assert "Assistente: +R$ 600,00." in frases[1]


def test_propostas_periodo_conversao_por_quantidade_e_valor():
    p = rc.propostas_periodo(PROPS, date(2026, 10, 1), date(2026, 10, 31))
    assert (p["enviadas"], p["fechadas"], p["recusadas"], p["aguardando"]) == (3, 1, 1, 1)
    assert p["conversao"] == 0.5
    assert abs(p["conversao_valor"] - 1500 / 3500) < 1e-9
    assert p["dias_para_fechar"] == 2


def test_clientes_novas_voltaram_recompra_e_origem():
    c = rc.clientes_periodo(PROPS, CLIENTES, date(2026, 10, 1), date(2026, 10, 31))
    # em outubro fecharam: Ana (proposta 1 aprovada 01/10 e proposta 3) — primeira vez da Ana é em outubro
    assert c["atendidas"] == 1 and c["novas"] == 1 and c["trabalhos"] == 2 and c["valor"] == 4500.0
    assert c["recompra"] == 0.5                      # Ana (2 trabalhos) e Bia (1)
    assert c["origem"].iloc[0]["origem"] == "Instagram"
    nov = rc.clientes_periodo(PROPS, CLIENTES, date(2026, 9, 1), date(2026, 10, 31))
    assert nov["concentracao_top3"] == 1.0


def test_lucro_por_trabalho_e_agenda():
    mov = rc.movimentos_rel(FIN)
    t = rc.lucro_por_trabalho(mov, PROPS, date(2026, 10, 1), date(2026, 10, 31))
    linha = t[t["numero"] == 101].iloc[0]
    assert (linha["recebido"], linha["custos"], linha["lucro"]) == (3000.0, 200.0, 2800.0)
    faixas, atrasados = rc.agenda_pendente(mov, HOJE)
    f = faixas.set_index("faixa")
    assert f.loc["Atrasado", "a_receber"] == 800.0
    assert f.loc["31 a 60 dias", "a_receber"] == 500.0
    assert f.loc["Até 30 dias", "a_pagar"] == 90.0
    assert len(atrasados) == 1
    ag = rc.propostas_aguardando(PROPS, HOJE)
    assert list(ag["dias"]) == [19]


def test_tudo_vazio_nao_quebra():
    mov = rc.movimentos_rel(pd.DataFrame())
    ini, fim = date(2026, 10, 1), date(2026, 10, 31)
    assert rc.resultado(mov, ini, fim)["lucro"] == 0.0
    assert rc.propostas_periodo(pd.DataFrame(), ini, fim)["conversao"] is None
    assert rc.clientes_periodo(pd.DataFrame(), pd.DataFrame(), ini, fim)["atendidas"] == 0
    assert rc.lucro_por_trabalho(mov, pd.DataFrame(), ini, fim).empty
    assert rc.agenda_pendente(mov, HOJE)[0]["a_receber"].sum() == 0
