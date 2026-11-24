"""
Conta criada pelo app ganha perfil no primeiro acesso à API (garantir_perfil), com a data de criação da conta
no Firebase. Sem isso o teste grátis nunca acabava para quem se cadastrou pelo celular.
"""
import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


@pytest.fixture
def conta():
    from utils.database import engine
    uid = f"app-{uuid.uuid4().hex[:8]}"
    yield uid, engine
    with engine.begin() as c:
        c.execute(text("DELETE FROM perfis WHERE usuario_id = :u OR email LIKE :e"), {"u": uid, "e": f"{uid}%"})


def _ms(d):
    return str(int(d.timestamp() * 1000))


def test_cria_perfil_com_data_do_firebase_e_teste_acaba(conta):
    import api.router as router
    from utils.trial import trial_expirado
    uid, engine = conta
    criado = datetime.now() - timedelta(days=20)
    router.garantir_perfil({"localId": uid, "email": f"{uid}@Teste.local", "createdAt": _ms(criado)})
    with engine.connect() as c:
        p = c.execute(text("SELECT email, nome, plano, data_cadastro FROM perfis WHERE usuario_id = :u"),
                      {"u": uid}).mappings().first()
    assert p["email"] == f"{uid}@teste.local" and p["plano"] == "gratuito"
    assert p["data_cadastro"] == criado.date()
    assert router._em_modo_consulta(uid) is True  # 20 dias: teste de 7 dias já acabou


def test_conta_nova_fica_no_teste(conta):
    import api.router as router
    uid, _ = conta
    router.garantir_perfil({"localId": uid, "email": f"{uid}@teste.local", "createdAt": _ms(datetime.now())})
    assert router._em_modo_consulta(uid) is False


def test_nao_duplica_nem_mexe_em_perfil_existente(conta):
    import api.router as router
    uid, engine = conta
    with engine.begin() as c:
        c.execute(text("INSERT INTO perfis (usuario_id, email, nome, plano, data_cadastro) "
                       "VALUES (:u, :e, 'Ana', 'pro', :d)"), {"u": uid, "e": f"{uid}@teste.local", "d": datetime.now()})
    router._PERFIS_CONFERIDOS.discard(uid)
    router.garantir_perfil({"localId": uid, "email": f"{uid}@teste.local", "createdAt": _ms(datetime(2025, 1, 1))})
    router.garantir_perfil({"localId": uid + "-nova", "email": f"{uid}@teste.local", "createdAt": _ms(datetime.now())})
    with engine.connect() as c:
        linhas = c.execute(text("SELECT usuario_id, nome, plano FROM perfis WHERE email = :e"),
                           {"e": f"{uid}@teste.local"}).all()
    assert [tuple(l) for l in linhas] == [(uid, "Ana", "pro")]
