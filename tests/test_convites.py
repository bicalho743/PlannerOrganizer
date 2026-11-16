"""Convites: cada código vale uma vez, dá os dias certos e entra no cálculo do trial."""
import pytest
from sqlalchemy import create_engine

from utils.convites import novo_convite, resgatar, dias_do_convite, ConviteInvalido
from utils.trial import trial_expirado, DIAS_TRIAL


@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:")


def test_codigo_resgatado_uma_vez(engine):
    codigo = novo_convite(engine, dias=30)
    assert resgatar(engine, "uid-a", codigo) == 30
    assert dias_do_convite(engine, "uid-a") == 30
    with pytest.raises(ConviteInvalido):
        resgatar(engine, "uid-b", codigo)


def test_conta_usa_um_convite_so(engine):
    c1 = novo_convite(engine, dias=30)
    c2 = novo_convite(engine, dias=30)
    resgatar(engine, "uid-a", c1)
    with pytest.raises(ConviteInvalido):
        resgatar(engine, "uid-a", c2)


def test_codigo_digitado_sem_hifen_e_minusculo(engine):
    codigo = novo_convite(engine, dias=30)
    assert resgatar(engine, "uid-a", codigo.replace("-", "").lower()) == 30


def test_codigo_inexistente(engine):
    with pytest.raises(ConviteInvalido):
        resgatar(engine, "uid-a", "NAOEXISTE")


def test_sem_convite_dias_none(engine):
    assert dias_do_convite(engine, "uid-x") is None


def test_trial_de_30_dias_nao_expira_no_dia_8():
    from datetime import date, timedelta
    perfil = {"plano": "gratuito", "data_cadastro": (date.today() - timedelta(days=8)).isoformat()}
    assert trial_expirado(perfil) is True                 # padrão de 7 dias
    assert trial_expirado(perfil, 30) is False            # convite de 30 dias
