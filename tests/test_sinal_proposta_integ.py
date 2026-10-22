"""
Integração: o sinal (entrada) da proposta chega ao Financeiro.

Regras cobertas:
- ao aprovar, o sinal vira receita "Recebido" na data da aprovação e a receita pendente fica com o saldo;
- mudar o sinal depois (Editar serviço) ajusta os dois lançamentos; sinal zerado apaga o do sinal;
- sinal igual ao valor deixa nada a receber; se o sinal diminuir, o saldo volta a ficar pendente;
- proposta em aberto não ganha lançamento; receita já recebida não é mexida (o sinal contaria duas vezes).

Bate no PostgreSQL de DATABASE_URL (como test_vendas_integ); cada execução usa um usuario_id único e apaga
tudo no fim.
"""
import os
import uuid
from datetime import date

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _limpar(engine, uid):
    with engine.connect() as c:
        for sql in ["DELETE FROM financeiro WHERE usuario_id = :u OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM propostas WHERE usuario_id = :u",
                    "DELETE FROM clientes WHERE usuario_id = :u"]:
            c.execute(text(sql), {"u": uid})
        c.commit()


@pytest.fixture
def ctx():
    from utils.database import Database, engine
    uid = f"test-sinal-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=uid)
    _limpar(engine, uid)
    cliente = db.add_cliente(nome="Cliente Sinal")
    yield db, cliente
    _limpar(engine, uid)


def _proposta(db, cliente, valor=3000.0, sinal=0.0):
    from utils.proposta_status import STATUS_EM_ABERTO
    pid = db.add_proposta(cliente_id=cliente, descricao="Organização da cozinha", valor=valor,
                          status=STATUS_EM_ABERTO, gerar_transacoes_automaticas=False)
    if sinal:
        db.update_proposta(pid, sinal=sinal)
    return pid


def _aprovar(db, pid):
    """Mesmo caminho da tela: muda o status (gera a receita) e sincroniza o sinal."""
    from utils.proposta_status import STATUS_APROVADA
    assert db.update_proposta_status(proposta_id=pid, novo_status=STATUS_APROVADA,
                                     data_aprovacao=date.today()).get("status")
    db.sincronizar_sinal_proposta(pid)


def _fin(db, pid):
    db.session.expire_all()
    from utils.models import Transacao
    ts = db.session.query(Transacao).filter_by(proposta_id=pid).order_by(Transacao.id).all()
    sinal = [t for t in ts if db.SINAL_TAG in (t.descricao or "")]
    resto = [t for t in ts if db.SINAL_TAG not in (t.descricao or "")]
    return sinal, resto


def test_aprovar_com_sinal_lanca_sinal_recebido_e_saldo_pendente(ctx):
    db, cli = ctx
    pid = _proposta(db, cli, valor=3000.0, sinal=1000.0)
    _aprovar(db, pid)
    sinal, resto = _fin(db, pid)
    assert len(sinal) == 1 and sinal[0].valor == 1000.0 and sinal[0].status == "Recebido"
    assert sinal[0].data_recebimento == date.today()
    assert len(resto) == 1 and resto[0].valor == 2000.0 and resto[0].status == "Pendente"


def test_aprovar_sem_sinal_lanca_so_o_valor_pendente(ctx):
    db, cli = ctx
    pid = _proposta(db, cli, valor=3000.0)
    _aprovar(db, pid)
    sinal, resto = _fin(db, pid)
    assert sinal == [] and len(resto) == 1 and resto[0].valor == 3000.0 and resto[0].status == "Pendente"


def test_editar_sinal_depois_ajusta_e_zerar_apaga(ctx):
    db, cli = ctx
    pid = _proposta(db, cli, valor=3000.0, sinal=1000.0)
    _aprovar(db, pid)
    db.update_proposta(pid, sinal=1500.0)
    db.sincronizar_sinal_proposta(pid)
    sinal, resto = _fin(db, pid)
    assert len(sinal) == 1 and sinal[0].valor == 1500.0 and resto[0].valor == 1500.0
    db.update_proposta(pid, sinal=0.0)
    db.sincronizar_sinal_proposta(pid)
    sinal, resto = _fin(db, pid)
    assert sinal == [] and resto[0].valor == 3000.0 and resto[0].status == "Pendente"


def test_sinal_igual_ao_valor_nada_a_receber_e_volta_se_diminuir(ctx):
    db, cli = ctx
    pid = _proposta(db, cli, valor=3000.0, sinal=3000.0)
    _aprovar(db, pid)
    sinal, resto = _fin(db, pid)
    assert sinal[0].valor == 3000.0 and resto[0].valor == 0 and resto[0].status == "Recebido"
    db.update_proposta(pid, sinal=2000.0)
    db.sincronizar_sinal_proposta(pid)
    sinal, resto = _fin(db, pid)
    assert sinal[0].valor == 2000.0 and resto[0].valor == 1000.0 and resto[0].status == "Pendente"


def test_proposta_em_aberto_nao_ganha_lancamento(ctx):
    db, cli = ctx
    pid = _proposta(db, cli, valor=3000.0, sinal=1000.0)
    assert not db.sincronizar_sinal_proposta(pid)
    assert _fin(db, pid) == ([], [])


def test_receita_ja_recebida_nao_e_mexida(ctx):
    db, cli = ctx
    pid = _proposta(db, cli, valor=3000.0)
    _aprovar(db, pid)
    _, resto = _fin(db, pid)
    db.atualizar_status_transacao(resto[0].id, "Recebido", date.today())
    db.update_proposta(pid, sinal=1000.0)
    db.sincronizar_sinal_proposta(pid)
    sinal, resto = _fin(db, pid)
    assert sinal == [] and resto[0].valor == 3000.0 and resto[0].status == "Recebido"
