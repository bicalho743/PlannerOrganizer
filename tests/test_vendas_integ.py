"""
Integração do módulo Vendas: dinheiro, estoque e custo sempre consistentes.

Regras cobertas:
- venda recebida na hora vira receita "Recebido" na data da venda (entra no Início, Financeiro e Relatórios);
- venda a receber vira entrada recebida + parcelas pendentes com vencimento mensal;
- editar itens (web ou app) mantém o Financeiro igual ao total da venda e ajusta o estoque;
- estoque só é devolvido se foi baixado (não infla ao cancelar venda sem estoque);
- o custo do produto fica gravado no item (lucro da venda não muda se o custo mudar depois);
- cancelar devolve o estoque, cancela o que falta receber e lança a devolução do que já foi recebido.

Bate no PostgreSQL de DATABASE_URL (como test_propostas_finalizadas_integ); cada execução usa um usuario_id
único e apaga tudo no fim.
"""
import os
import uuid
from datetime import date

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")

DIA = date(2026, 10, 10)


def _limpar(engine, uid):
    with engine.connect() as c:
        for sql in ["DELETE FROM itens_venda WHERE venda_id IN (SELECT id FROM vendas WHERE usuario_id = :u "
                    "OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u))",
                    "DELETE FROM financeiro WHERE usuario_id = :u OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM vendas WHERE usuario_id = :u OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM acrescimos_proposta WHERE proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM propostas WHERE usuario_id = :u",
                    "DELETE FROM produtos WHERE usuario_id = :u",
                    "DELETE FROM clientes WHERE usuario_id = :u"]:
            c.execute(text(sql), {"u": uid})


@pytest.fixture
def ctx():
    from utils.database import Database, engine
    uid = f"test-vendas-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=uid)
    _limpar(engine, uid)
    cliente = db.add_cliente(nome="Cliente Vendas")
    caixa = db.add_produto(nome="Caixa organizadora", preco_custo=20.0, preco_venda=50.0, estoque=5)
    cabide = db.add_produto(nome="Cabide", preco_custo=2.0, preco_venda=6.0, estoque=1)
    yield db, cliente, caixa, cabide
    _limpar(engine, uid)


def _fin(db, venda_id):
    db.session.expire_all()
    from utils.models import Transacao
    return (db.session.query(Transacao).filter_by(origem_id=venda_id, origem_tipo="venda", usuario_id=db.usuario_id)
            .order_by(Transacao.id).all())


def _estoque(db, pid):
    db.session.expire_all()
    from utils.models import Produto
    return db.session.query(Produto).get(pid).estoque


def _venda(db, vid):
    df = db.get_vendas()
    return df[df["id"] == vid].iloc[0]


def _ativos(ts):
    """Saldo do Financeiro ligado à venda: receitas − devoluções, sem cancelados."""
    return round(sum((t.valor if t.tipo.startswith("receita") else -t.valor) for t in ts if t.status != "Cancelado"), 2)


def test_venda_a_vista_entra_como_recebida_na_data_da_venda_com_custo(ctx):
    db, cli, caixa, _ = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": caixa, "quantidade": 2, "preco_unitario": 50.0}],
                       forma_pagamento="PIX", data_venda=DIA)
    ts = _fin(db, vid)
    assert len(ts) == 1
    t = ts[0]
    assert (t.tipo, t.status, t.valor, t.data, t.data_recebimento) == ("receita", "Recebido", 100.0, DIA, DIA)
    v = _venda(db, vid)
    assert (v["situacao"], v["recebido"], v["a_receber"]) == ("Paga", 100.0, 0.0)
    assert (v["custo"], v["lucro"]) == (40.0, 60.0)
    assert _estoque(db, caixa) == 3
    # o custo gravado não muda se o produto mudar de preço depois
    db.update_produto(caixa, preco_custo=35.0)
    assert _venda(db, vid)["custo"] == 40.0


def test_venda_a_receber_com_entrada_e_parcelas(ctx):
    db, cli, caixa, _ = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": caixa, "quantidade": 2, "preco_unitario": 50.0}],
                       forma_pagamento="Cartão de crédito", data_venda=DIA, recebido=False, entrada=10.0, parcelas=3,
                       primeiro_vencimento=date(2026, 11, 10))
    ts = _fin(db, vid)
    assert [(t.status, t.valor, t.data) for t in ts] == [
        ("Recebido", 10.0, DIA), ("Pendente", 30.0, date(2026, 11, 10)),
        ("Pendente", 30.0, date(2026, 12, 10)), ("Pendente", 30.0, date(2027, 1, 10))]
    v = _venda(db, vid)
    assert (v["situacao"], v["recebido"], v["a_receber"]) == ("A receber", 10.0, 90.0)


def test_editar_itens_mantem_financeiro_e_estoque(ctx):
    db, cli, caixa, cabide = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": caixa, "quantidade": 1, "preco_unitario": 50.0}],
                       forma_pagamento="PIX", data_venda=DIA, recebido=False, parcelas=1, primeiro_vencimento=DIA)
    item = int(db.get_itens_venda(vid).iloc[0]["id"])
    db.update_item_venda(item, 3, 50.0)                  # +2 caixas
    assert _estoque(db, caixa) == 2
    db.add_item_venda(vid, cabide, 1, 6.0)
    assert _estoque(db, cabide) == 0
    db.recalcular_valor_total_venda(vid)
    assert _ativos(_fin(db, vid)) == 156.0
    db.remove_item_venda(item)
    assert _estoque(db, caixa) == 5
    assert _ativos(_fin(db, vid)) == 6.0 == _venda(db, vid)["valor_total"]


def test_editar_venda_ja_recebida_gera_complemento_ou_devolucao(ctx):
    db, cli, caixa, _ = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": caixa, "quantidade": 2, "preco_unitario": 50.0}],
                       forma_pagamento="PIX", data_venda=DIA)
    item = int(db.get_itens_venda(vid).iloc[0]["id"])
    db.update_item_venda(item, 3, 50.0)
    ts = _fin(db, vid)
    assert _ativos(ts) == 150.0 and ts[-1].status == "Pendente" and ts[-1].valor == 50.0   # falta receber 50
    db.update_item_venda(item, 1, 50.0)
    ts = _fin(db, vid)
    assert _ativos(ts) == 50.0
    dev = [t for t in ts if t.tipo == "despesa"]
    assert len(dev) == 1 and dev[0].valor == 50.0 and dev[0].status == "Pendente"            # devolver 50 à cliente


def test_estoque_nao_infla_quando_venda_passou_do_estoque(ctx):
    db, cli, _, cabide = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": cabide, "quantidade": 3, "preco_unitario": 6.0}],
                       forma_pagamento="Dinheiro", data_venda=DIA)
    assert _estoque(db, cabide) == 1                     # tinha 1: não baixou
    db.cancelar_venda(vid)
    assert _estoque(db, cabide) == 1                     # antes voltava para 4


def test_cancelar_devolve_estoque_e_lanca_devolucao(ctx):
    db, cli, caixa, _ = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": caixa, "quantidade": 2, "preco_unitario": 50.0}],
                       forma_pagamento="PIX", data_venda=DIA, recebido=False, entrada=40.0, parcelas=2,
                       primeiro_vencimento=date(2026, 11, 10))
    assert db.cancelar_venda(vid, devolver_recebido=True)
    assert _estoque(db, caixa) == 5
    ts = _fin(db, vid)
    assert all(t.status == "Cancelado" for t in ts if t.tipo == "receita" and t.status != "Recebido")
    dev = [t for t in ts if t.tipo == "despesa"]
    assert len(dev) == 1 and dev[0].valor == 40.0
    assert _venda(db, vid)["situacao"] == "Cancelada"
    assert db.cancelar_venda(vid) is False               # cancelar de novo não faz nada


def test_app_status_cancelada_e_substituir_itens(ctx):
    db, cli, caixa, cabide = ctx
    vid = db.add_venda(cliente_id=cli, itens=[{"produto_id": caixa, "quantidade": 1, "preco_unitario": 50.0}],
                       forma_pagamento="PIX", data_venda=DIA)
    db.substituir_itens_venda(vid, [{"produto_id": caixa, "quantidade": 2, "preco_unitario": 50.0},
                                    {"produto_id": cabide, "quantidade": 1, "preco_unitario": 6.0}])
    assert (_estoque(db, caixa), _estoque(db, cabide)) == (3, 0)
    assert _ativos(_fin(db, vid)) == 106.0
    db.atualizar_venda(vid, status="Cancelada")
    assert (_estoque(db, caixa), _estoque(db, cabide)) == (5, 1)


def test_vendas_antigas_pendentes_podem_ser_marcadas_como_recebidas(ctx):
    db, cli, caixa, _ = ctx
    from utils.models import Venda, Transacao
    v = Venda(cliente_id=cli, valor_total=50.0, data_venda=DIA, status="Concluída", forma_pagamento="PIX", usuario_id=db.usuario_id)
    db.session.add(v); db.session.flush()
    db.session.add(Transacao(tipo="receita", descricao="Venda para Cliente Vendas", valor=50.0, categoria="Vendas",
                             origem_id=v.id, origem_tipo="venda", status="Pendente", usuario_id=db.usuario_id,
                             data=date(2026, 10, 21)))
    db.session.commit()
    assert db.contar_vendas_antigas_pendentes() == 1
    assert db.marcar_vendas_antigas_recebidas() == 1
    t = _fin(db, v.id)[0]
    assert (t.status, t.data, t.data_recebimento) == ("Recebido", DIA, DIA)
    assert db.contar_vendas_antigas_pendentes() == 0


def test_venda_de_proposta_com_comissao_pertence_a_conta(ctx):
    """A venda gerada de uma proposta (e a comissão do fornecedor) precisa ter dona: sem usuario_id ela
    some das telas, que só mostram registros da conta. A comissão usava um campo inexistente e dava erro."""
    db, cli, _, _ = ctx
    from utils.proposta_status import STATUS_EM_ABERTO
    pid = db.add_proposta(cliente_id=cli, descricao="Closet", valor=1000.0, status=STATUS_EM_ABERTO,
                          gerar_transacoes_automaticas=False)
    db.add_acrescimo_proposta(proposta_id=pid, tipo="FORNECEDOR", valor=500.0, fornecedor="Marcenaria",
                              percentual_comissao=10.0)
    from utils.database import engine
    with engine.connect() as c:   # add_acrescimo_proposta não grava o percentual: grava direto
        c.execute(text("UPDATE acrescimos_proposta SET percentual_comissao = 10 WHERE proposta_id = :p"), {"p": pid})
    r = db.criar_venda_de_proposta(pid)
    vid = r["venda_id"]
    assert vid in set(db.get_vendas()["id"])
    ts = _fin(db, vid)
    assert any(t.categoria == "Vendas" and t.status == "Recebido" and t.valor == 1000.0 for t in ts)
    assert any(t.categoria == "Comissões" and t.valor == 50.0 for t in ts)
    assert all(t.usuario_id == db.usuario_id for t in ts)
