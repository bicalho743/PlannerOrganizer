"""E-mail de boas-vindas: uma vez por conta, só para contas novas, com o primeiro nome quando ele é real."""
import os
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from utils import boas_vindas

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


@pytest.fixture
def ambiente(monkeypatch):
    from utils.database import engine
    enviados = []
    monkeypatch.setattr(boas_vindas, "_enviar", lambda email, nome: enviados.append((email, nome)) or True)
    pre = f"bv-{uuid.uuid4().hex[:6]}"
    yield pre, engine, enviados
    with engine.begin() as c:
        c.execute(text("DELETE FROM eventos_funil WHERE usuario_id LIKE :p"), {"p": pre + "%"})


def test_envia_uma_vez_so_para_conta_nova(ambiente):
    pre, engine, enviados = ambiente
    assert boas_vindas.enviar_se_nova(engine, pre + "a", "ana@x.com", "Ana Souza", date.today(), False) is True
    assert boas_vindas.enviar_se_nova(engine, pre + "a", "ana@x.com", "Ana Souza", date.today(), False) is False
    assert boas_vindas.enviar_se_nova(engine, pre + "b", "b@x.com", "B", date.today() - timedelta(days=10), False) is False
    assert boas_vindas.enviar_se_nova(engine, pre + "c", "sem-arroba", "C", date.today(), False) is False
    assert enviados == [("ana@x.com", "Ana Souza")]


def test_texto_usa_primeiro_nome_real():
    assunto, corpo, texto = boas_vindas.montar("ana souza", "ana@x.com")
    assert "Ana" in assunto and "Oi, Ana!" in texto and "Criar minha primeira proposta" in corpo
    assunto2, _, texto2 = boas_vindas.montar("Usuário", "joana@x.com")
    assert assunto2.startswith("Bem-vinda ao Planner!") and texto2.startswith("Oi!")
    assert boas_vindas.primeiro_nome("joana@x.com") == ""
