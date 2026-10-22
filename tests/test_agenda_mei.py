"""Regras da Agenda (utils/agenda.py) e do MEI (DAS mês a mês, faturamento para a DASN, prazo)."""
from datetime import date

import pandas as pd
import pytest

from utils.agenda import montar_agenda, totais, semana_de, mes_de
from utils.indicadores import das_do_ano, faturamento_ano, prazo_dasn, movimentos

INI, FIM = date(2026, 11, 9), date(2026, 11, 15)


def _fin(linhas):
    base = {"classificacao": "", "data_recebimento": None, "categoria": "", "descricao": ""}
    return pd.DataFrame([{**base, **l} for l in linhas])


def test_periodos():
    assert semana_de(date(2026, 11, 12)) == (date(2026, 11, 9), date(2026, 11, 15))
    assert mes_de(date(2026, 12, 5)) == (date(2026, 12, 1), date(2026, 12, 31))


def test_agenda_junta_tudo_que_tem_data_sem_repetir_a_receita_do_compromisso():
    comp = pd.DataFrame([
        {"id": 1, "data": date(2026, 11, 10), "hora": "09:00", "titulo": "Diária com Ana", "cliente_nome": "Ana",
         "local": "", "valor": 200.0, "transacao_id": 50, "status_receita": "Pendente"},
        {"id": 2, "data": date(2026, 11, 20), "hora": "", "titulo": "Fora do período", "cliente_nome": "",
         "local": "", "valor": 0.0, "transacao_id": None, "status_receita": ""},
    ])
    props = pd.DataFrame([
        {"numero": 7, "status": "aprovada", "cliente_nome": "Bia", "data_inicio": date(2026, 11, 11),
         "data_fim": date(2026, 11, 12), "data_inicio_execucao": None},
        {"numero": 8, "status": "em_aberto", "cliente_nome": "Cris", "data_inicio": date(2026, 11, 11),
         "data_fim": None, "data_inicio_execucao": None},
    ])
    pos = pd.DataFrame([{"action_type": "feedback", "due_date": date(2026, 11, 13), "cliente_nome": "Dani",
                         "proposta_numero": 3}])
    fin = _fin([
        {"id": 50, "tipo": "Receita", "valor": 200, "data": date(2026, 11, 10), "status": "Pendente", "descricao": "Diária"},
        {"id": 51, "tipo": "despesa", "valor": 80, "data": date(2026, 11, 14), "status": "Pendente", "descricao": "Aluguel"},
        {"id": 52, "tipo": "receita", "valor": 500, "data": date(2026, 11, 14), "status": "Pendente", "descricao": "Saldo #7"},
        {"id": 53, "tipo": "receita", "valor": 900, "data": date(2026, 11, 14), "status": "Recebido", "descricao": "Já entrou"},
    ])
    itens = montar_agenda(INI, FIM, comp, props, pos, fin)
    assert [(i["data"].day, i["tipo"]) for i in itens] == [
        (10, "compromisso"), (11, "servico"), (12, "servico"), (13, "pos"), (14, "receber"), (14, "pagar")]
    assert itens[0]["situacao"] == "a receber" and itens[0]["compromisso_id"] == 1
    assert itens[1]["titulo"] == "Início do serviço · Bia" and itens[3]["titulo"] == "Feedback · Dani"
    assert totais(itens) == (700.0, 80.0)


def test_compromisso_recebido_nao_conta_como_a_receber():
    comp = pd.DataFrame([{"id": 1, "data": INI, "hora": "", "titulo": "Diária", "cliente_nome": "", "local": "",
                          "valor": 200.0, "transacao_id": 9, "status_receita": "Recebido"}])
    itens = montar_agenda(INI, FIM, compromissos=comp)
    assert itens[0]["situacao"] == "recebido" and totais(itens) == (0, 0)


def _das(quando, valor=86.05, descricao="DAS", categoria="Impostos (DAS)"):
    return {"tipo": "despesa", "valor": valor, "data": quando, "status": "Pago", "data_recebimento": quando,
            "categoria": categoria, "descricao": descricao}


def test_das_mes_a_mes():
    mov = movimentos(_fin([
        _das(date(2026, 1, 15)),                                   # é o DAS de dezembro/2025: não conta em 2026
        _das(date(2026, 2, 18)),                                   # janeiro
        _das(date(2026, 4, 2), descricao="DAS MEI competência 03/2026", categoria="Outros"),  # março, pela descrição
        _das(date(2026, 4, 10)),                                   # fevereiro, pago atrasado
    ]))
    meses = das_do_ano(mov, 2026, date(2026, 5, 25))
    situ = {m["mes"]: m["situacao"] for m in meses}
    assert situ[1] == situ[2] == situ[3] == "pago"
    assert meses[1]["pago_em"] == date(2026, 4, 10) and meses[2]["pago_em"] == date(2026, 4, 2)
    assert situ[4] == "atrasado"            # venceu 20/05
    assert situ[5] == "a vencer"            # vence 20/06
    assert situ[6] == "futuro" and meses[11]["vencimento"] == date(2027, 1, 20)


def test_faturamento_separa_servicos_e_produtos_e_prazo_da_declaracao():
    mov = movimentos(_fin([
        {"tipo": "receita", "valor": 1000, "data": date(2025, 3, 1), "status": "Recebido", "categoria": "Serviços de Organização"},
        {"tipo": "receita", "valor": 300, "data": date(2025, 4, 1), "status": "Recebido", "categoria": "Venda de Produtos"},
        {"tipo": "receita", "valor": 999, "data": date(2025, 4, 1), "status": "Pendente", "categoria": "Serviços"},
    ]))
    assert faturamento_ano(mov, 2025) == {"total": 1300.0, "comercio": 300.0, "servicos": 1000.0}
    assert prazo_dasn(date(2026, 5, 1)) == (2025, date(2026, 5, 31), 30)
    assert prazo_dasn(date(2026, 10, 22))[:2] == (2026, date(2027, 5, 31))


def test_aliquota_efetiva_do_anexo_iii():
    from utils.indicadores import aliquota_efetiva
    assert aliquota_efetiva(0) == 0.06 and aliquota_efetiva(150000) == 0.06
    assert aliquota_efetiva(240000) == pytest.approx((240000 * 0.112 - 9360) / 240000)   # 7,3%


def test_simples_estima_das_pelos_12_meses_anteriores():
    from utils.indicadores import simples_do_ano
    linhas = [{"tipo": "receita", "valor": 20000, "data": date(2025, m, 10), "status": "Recebido",
               "categoria": "Serviços"} for m in range(1, 13)]
    linhas.append({"tipo": "receita", "valor": 10000, "data": date(2026, 1, 10), "status": "Recebido", "categoria": "Serviços"})
    mov = movimentos(_fin(linhas))
    jan = simples_do_ano(mov, 2026, date(2026, 1, 25))[0]
    assert jan["rbt12"] == 240000 and jan["receita"] == 10000
    assert jan["das_estimado"] == pytest.approx(10000 * (240000 * 0.112 - 9360) / 240000)
    assert simples_do_ano(mov, 2026, date(2026, 1, 25), aliquota_informada=8)[0]["das_estimado"] == pytest.approx(800)


def test_simples_mes_sem_receita_nao_fica_atrasado():
    from utils.indicadores import simples_do_ano
    meses = simples_do_ano(movimentos(_fin([])), 2026, date(2026, 5, 25))
    assert meses[0]["situacao"] == "sem receita" and meses[4]["situacao"] == "sem receita"
    assert meses[6]["situacao"] == "futuro"


def test_aniversario_da_cliente_entra_na_agenda_com_whatsapp():
    from utils.agenda import dia_mes_aniversario
    assert dia_mes_aniversario("05/out") == (5, 10) and dia_mes_aniversario("05/10") == (5, 10)
    assert dia_mes_aniversario("") is None and dia_mes_aniversario("xx") is None
    clientes = pd.DataFrame([
        {"nome": "Ana Paula", "telefone": "(31) 99999-0000", "data_aniversario": "12/nov"},
        {"nome": "Bia", "telefone": None, "data_aniversario": "13/nov"},
        {"nome": "Cris", "telefone": "31988887777", "data_aniversario": "20/dez"},
    ])
    itens = montar_agenda(INI, FIM, clientes=clientes)
    assert [(i["data"].day, i["titulo"]) for i in itens] == [(12, "Ana Paula"), (13, "Bia")]
    assert itens[0]["whatsapp"].startswith("https://wa.me/5531999990000?text=Feliz") and itens[1]["whatsapp"] == ""
    virada = montar_agenda(date(2026, 12, 28), date(2027, 1, 3),
                           clientes=pd.DataFrame([{"nome": "Dani", "telefone": "", "data_aniversario": "02/jan"}]))
    assert virada[0]["data"] == date(2027, 1, 2)
