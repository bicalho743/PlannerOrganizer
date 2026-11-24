"""Programa de afiliadas: inscrição, vínculo, comissão de 30% por 12 meses, estorno e pagamento."""
from datetime import date

import pytest
from sqlalchemy import create_engine

from utils import afiliados as af
from utils import convites


@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:")
    af.criar_tabelas(e)
    convites.criar_tabelas(e)
    return e


def _aprovada(engine, uid="uid-tamara", nome="Tâmara Cavalcante", email="tamara@x.com"):
    codigo = af.inscrever(engine, uid, nome, email, "123.456.789-00", "tamara@pix")
    af.mudar_status(engine, codigo, "aprovada")
    return codigo


def test_inscricao_gera_codigo_pelo_nome_e_fica_pendente(engine):
    codigo = af.inscrever(engine, "uid-1", "Tâmara Cavalcante", "t@x.com", "12345678900", "pix")
    assert codigo == "TAMARA"
    assert af.afiliada_da_conta(engine, "uid-1")["status"] == "pendente"
    with pytest.raises(af.AfiliadoInvalido):
        af.vincular(engine, "uid-2", codigo)  # pendente não vale


def test_codigo_repetido_ganha_numero(engine):
    c1 = af.inscrever(engine, "uid-1", "Ana", "a@x.com", "12345678900", "pix", codigo_desejado="ANA")
    c2 = af.inscrever(engine, "uid-2", "Ana", "b@x.com", "12345678901", "pix2", codigo_desejado="ANA")
    assert (c1, c2) == ("ANA", "ANA2")


def test_cpf_e_pix_obrigatorios(engine):
    with pytest.raises(af.AfiliadoInvalido):
        af.inscrever(engine, "uid-1", "Ana", "a@x.com", "123", "pix")
    with pytest.raises(af.AfiliadoInvalido):
        af.inscrever(engine, "uid-1", "Ana", "a@x.com", "12345678900", "")


def test_vinculo_uma_vez_e_sem_autoindicacao(engine):
    codigo = _aprovada(engine)
    with pytest.raises(af.AfiliadoInvalido):
        af.vincular(engine, "uid-tamara", codigo)
    with pytest.raises(af.AfiliadoInvalido):
        af.vincular(engine, "uid-outra", codigo, email_conta="TAMARA@x.com")
    af.vincular(engine, "uid-maria", codigo.lower())
    assert af.codigo_da_indicacao(engine, "uid-maria") == codigo
    with pytest.raises(af.AfiliadoInvalido):
        af.vincular(engine, "uid-maria", codigo)


def test_comissao_30_por_cento_do_liquido_e_sem_duplicar(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-maria", codigo)
    c = af.registrar_pagamento(engine, "uid-maria", "apple", "tx-1", 59.90, date(2026, 12, 1))
    assert c["valor_liquido"] == 50.91 and c["comissao"] == 12.73
    assert af.registrar_pagamento(engine, "uid-maria", "apple", "tx-1", 59.90, date(2026, 12, 1)) is None
    s = af.registrar_pagamento(engine, "uid-maria", "stripe", "in_2", 479.90, date(2026, 12, 2))
    assert s["valor_liquido"] == round(479.90 * (1 - 0.0399) - 0.39, 2)
    assert af.registrar_pagamento(engine, "uid-sem-indicacao", "stripe", "in_3", 59.90) is None


def test_takehome_do_revenuecat(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-maria", codigo)
    c = af.registrar_pagamento(engine, "uid-maria", "google", "gpa-1", 100.0, date(2026, 12, 1), takehome=0.70)
    assert c["comissao"] == 17.5


def test_so_12_meses_de_comissao(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-maria", codigo)
    assert af.registrar_pagamento(engine, "uid-maria", "stripe", "m1", 59.90, date(2026, 1, 15))
    assert af.registrar_pagamento(engine, "uid-maria", "stripe", "m12", 59.90, date(2027, 1, 14))
    assert af.registrar_pagamento(engine, "uid-maria", "stripe", "m13", 59.90, date(2027, 1, 15)) is None


def test_liberacao_em_30_dias_estorno_e_pagamento(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-maria", codigo)
    af.vincular(engine, "uid-joana", codigo)
    af.registrar_pagamento(engine, "uid-maria", "stripe", "a", 479.90, date(2026, 11, 1))
    af.registrar_pagamento(engine, "uid-joana", "stripe", "b", 479.90, date(2026, 11, 20))
    af.registrar_pagamento(engine, "uid-joana", "stripe", "c", 59.90, date(2026, 11, 21))
    assert af.estornar(engine, "c") is True
    p = af.painel(engine, codigo, date(2026, 12, 5))
    assert p["indicadas"] == 2 and p["assinantes"] == 2
    assert p["liberado"] > 0 and p["a_liberar"] > 0
    pagar = af.a_pagar(engine, date(2026, 12, 5))
    assert [x["codigo"] for x in pagar] == [codigo]
    total = af.marcar_pago(engine, codigo, date(2026, 12, 5))
    assert total == p["liberado"]
    p2 = af.painel(engine, codigo, date(2026, 12, 5))
    assert p2["liberado"] == 0 and p2["recebido"] == total
    assert af.estornar(engine, "a") is False  # já paga: não estorna


def test_minimo_de_50_reais(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-maria", codigo)
    af.registrar_pagamento(engine, "uid-maria", "stripe", "x", 59.90, date(2026, 11, 1))
    assert af.a_pagar(engine, date(2026, 12, 5)) == []


def test_codigo_da_afiliada_no_campo_de_convite(engine):
    codigo = _aprovada(engine)
    assert convites.resgatar(engine, "uid-maria", codigo) == af.DIAS_TESTE_INDICADA
    assert af.codigo_da_indicacao(engine, "uid-maria") == codigo
    assert convites.dias_do_convite(engine, "uid-maria") is None  # teste padrão, sem dias extras


def test_evento_da_loja_gera_e_estorna_comissao(engine, monkeypatch):
    from utils import assinatura
    monkeypatch.setattr(assinatura, "_engine", lambda: engine)
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-maria", codigo)
    ev = {"type": "INITIAL_PURCHASE", "transaction_id": "1000", "currency": "BRL",
          "price_in_purchased_currency": 149.90, "takehome_percentage": 0.85, "purchased_at_ms": 1795000000000}
    assinatura._comissao_loja(ev, "INITIAL_PURCHASE", "apple", ["uid-maria"])
    p = af.painel(engine, codigo)
    assert len(p["comissoes"]) == 1 and float(p["comissoes"][0]["comissao"]) == round(round(149.90 * 0.85, 2) * 0.25, 2)
    assinatura._comissao_loja({"type": "CANCELLATION", "transaction_id": "1000", "cancel_reason": "CUSTOMER_SUPPORT"},
                              "CANCELLATION", "apple", ["uid-maria"])
    assert af.painel(engine, codigo)["comissoes"][0]["status"] == "cancelada"
    # teste grátis e moeda estrangeira não geram comissão
    assinatura._comissao_loja({**ev, "transaction_id": "2", "period_type": "TRIAL"}, "INITIAL_PURCHASE", "apple", ["uid-maria"])
    assinatura._comissao_loja({**ev, "transaction_id": "3", "currency": "USD"}, "INITIAL_PURCHASE", "apple", ["uid-maria"])
    assert len(af.painel(engine, codigo)["comissoes"]) == 1


def test_cpf_e_pix_unicos_e_desconto_da_indicada(engine):
    codigo = _aprovada(engine)
    with pytest.raises(af.AfiliadoInvalido):  # mesmo CPF
        af.inscrever(engine, "uid-x", "Outra", "o@x.com", "123.456.789-00", "outro@pix")
    with pytest.raises(af.AfiliadoInvalido):  # mesma chave Pix
        af.inscrever(engine, "uid-y", "Outra", "o@x.com", "98765432100", "TAMARA@pix")
    assert af.tem_desconto_indicada(engine, "uid-maria") is False
    af.vincular(engine, "uid-maria", codigo)
    assert af.tem_desconto_indicada(engine, "uid-maria") is True


def test_excluir_afiliada_de_teste(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-indicada", codigo)
    r = af.excluir(engine, codigo)
    assert r["indicacoes"] == 1
    assert af.afiliada_da_conta(engine, "uid-tamara") is None
    assert af.codigo_da_indicacao(engine, "uid-indicada") is None
    with pytest.raises(af.AfiliadoInvalido):
        af.excluir(engine, codigo)


def test_nao_exclui_quem_ja_recebeu(engine):
    codigo = _aprovada(engine)
    af.vincular(engine, "uid-indicada", codigo)
    af.registrar_pagamento(engine, "uid-indicada", "stripe", "inv_1", 59.90, pago_em=date(2026, 1, 1))
    af.marcar_pago(engine, codigo, hoje=date(2026, 3, 1))
    with pytest.raises(af.AfiliadoInvalido):
        af.excluir(engine, codigo)
