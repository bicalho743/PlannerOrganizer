"""Estoque mínimo por produto, compra de estoque com despesa e mensagens de pós-organização por conta."""
import os
import uuid

import pandas as pd
import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa do Postgres de teste")


def _conta():
    from utils.database import Database
    uid = "est-" + uuid.uuid4().hex[:10]
    db = Database(usuario_id=uid)
    db.create_perfil(uid, f"{uid}@t.com", "X")
    return uid, db


def test_estoque_baixo_usa_o_minimo_de_cada_produto():
    from utils.vendas_dados import estoque_baixo
    df = pd.DataFrame([{"id": 1, "nome": "A", "estoque": 8, "estoque_minimo": 10},
                       {"id": 2, "nome": "B", "estoque": 4, "estoque_minimo": None},
                       {"id": 3, "nome": "C", "estoque": 4, "estoque_minimo": 2}])
    r = estoque_baixo(df)
    assert list(r["nome"]) == ["B", "A"] and list(r["minimo"]) == [5, 10]


def test_minimo_gravado_no_produto():
    _, db = _conta()
    pid = db.add_produto(nome="Colmeia", preco_custo=10, preco_venda=20, estoque=3, estoque_minimo=8)
    p = db.get_produtos().set_index("id").loc[pid]
    assert int(p["estoque_minimo"]) == 8
    db.update_produto(pid, estoque=4)                     # sem mexer no mínimo
    assert int(db.get_produtos().set_index("id").loc[pid]["estoque_minimo"]) == 8
    db.update_produto(pid, estoque_minimo=None)           # vazio volta ao padrão
    assert pd.isna(db.get_produtos().set_index("id").loc[pid]["estoque_minimo"])


def test_add_transacao_devolve_o_id_e_marca_pago():
    _, db = _conta()
    tid = db.add_transacao(tipo="despesa", descricao="Compra de estoque: 3 × Colmeia", valor=30.0,
                           categoria="Pagamento Parceiros/Fornecedores", classificacao="contas_a_pagar")
    assert isinstance(tid, int) and tid > 0
    from utils.visual import hoje
    db.atualizar_status_transacao(tid, "Pago", hoje())
    fin = db.get_financeiro()
    assert fin[fin["id"] == tid]["status"].iloc[0] == "Pago"


def test_mensagem_de_pos_personalizada_so_na_conta():
    from utils.database import engine
    from sqlalchemy import text
    with engine.begin() as c:   # garante um modelo padrão para a etapa
        c.execute(text("INSERT INTO post_org_templates (etapa, nome, dias_apos, texto, gratuito) "
                       "VALUES ('agradecimento', 'Agradecimento', 1, 'Obrigada, {nome}!', false) "
                       "ON CONFLICT (etapa) DO NOTHING"))
    _, a = _conta()
    _, b = _conta()
    padrao = a.get_post_org_templates()["agradecimento"]["texto"]
    assert a.salvar_modelo_pos("agradecimento", "Oi {nome}, foi ótimo!")
    ta, tb = a.get_post_org_templates()["agradecimento"], b.get_post_org_templates()["agradecimento"]
    assert ta["texto"] == "Oi {nome}, foi ótimo!" and ta["personalizado"] and ta["padrao"] == padrao
    assert tb["texto"] == padrao and not tb["personalizado"]
    a.salvar_modelo_pos("agradecimento", None)
    assert a.get_post_org_templates()["agradecimento"]["texto"] == padrao
