"""Renumerar propostas de uma conta (1, 2, 3... pela data)."""
import os
import uuid
from datetime import date

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa do Postgres de teste")


def test_renumera_pela_data_sem_mexer_em_outra_conta():
    from sqlalchemy import text
    from utils.database import Database, engine
    from utils import renumerar as rn
    contas = []
    for _ in range(2):
        uid = "ren-" + uuid.uuid4().hex[:10]
        db = Database(usuario_id=uid)
        db.create_perfil(uid, f"{uid}@t.com", "X")
        cli = db.add_cliente(nome="C")
        for d in (date(2026, 5, 1), date(2026, 1, 1), date(2026, 3, 1)):
            db.add_proposta(cliente_id=cli, descricao="x", valor=10, status="em_aberto", data_inicio=d,
                            gerar_transacoes_automaticas=False)
        contas.append(uid)
    with engine.begin() as c:   # simula conta antiga: números salteados
        c.execute(text("UPDATE propostas SET numero = id + 1000 WHERE usuario_id = :u"), {"u": contas[0]})
    assert rn.indice_por_conta(engine)
    assert rn.renumerar(engine, contas[0]) == 3
    with engine.connect() as c:
        r = c.execute(text("SELECT data_proposta, numero FROM propostas WHERE usuario_id = :u ORDER BY numero"),
                      {"u": contas[0]}).all()
        outra = sorted(x[0] for x in c.execute(text("SELECT numero FROM propostas WHERE usuario_id = :u"),
                                                 {"u": contas[1]}).all())
    assert [x[1] for x in r] == [1, 2, 3]
    assert [str(x[0])[:10] for x in r] == ["2026-01-01", "2026-03-01", "2026-05-01"]
    assert outra == [1, 2, 3]
