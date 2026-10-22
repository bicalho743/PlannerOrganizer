"""
Integração: retornos de pós-organização só para serviço finalizado.

Regras cobertas:
- proposta finalizada mostra os retornos no Início e na tela Pós-organização;
- proposta reaberta (voltou a "Em execução") não mostra retorno, mesmo com ações pendentes no banco;
- finalizada de novo com outra data, os retornos pendentes passam a contar da nova data.

Bate no PostgreSQL de DATABASE_URL (como test_vendas_integ); cada execução usa um usuario_id único e apaga
tudo no fim.
"""
import os
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _limpar(engine, uid):
    with engine.connect() as c:
        for sql in ["DELETE FROM post_organization_actions WHERE post_organization_id IN "
                    "(SELECT id FROM post_organizations WHERE usuario_id = :u)",
                    "DELETE FROM post_organizations WHERE usuario_id = :u",
                    "DELETE FROM financeiro WHERE usuario_id = :u OR proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
                    "DELETE FROM propostas WHERE usuario_id = :u",
                    "DELETE FROM clientes WHERE usuario_id = :u"]:
            c.execute(text(sql), {"u": uid})
        c.commit()


@pytest.fixture
def ctx():
    from utils.database import Database, engine
    uid = f"test-posorg-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=uid)
    _limpar(engine, uid)
    cliente = db.add_cliente(nome="Cliente Pós")
    yield db, cliente
    _limpar(engine, uid)


def _proposta_finalizada(db, cliente, fim):
    from utils.proposta_status import STATUS_FINALIZADA
    pid = db.add_proposta(cliente_id=cliente, descricao="Organização", valor=1000.0,
                          status=STATUS_FINALIZADA, gerar_transacoes_automaticas=False)
    db.create_post_organization(proposta_id=pid, cliente_id=cliente, data_final_projeto=fim)
    return pid


def _acoes(db, pid):
    db.session.expire_all()
    from utils.models import PostOrganization, PostOrganizationAction
    po = db.session.query(PostOrganization).filter_by(proposta_id=pid).first()
    return po, db.session.query(PostOrganizationAction).filter_by(post_organization_id=po.id, status="PENDENTE").all()


def test_finalizada_mostra_e_reaberta_esconde_retornos(ctx):
    db, cli = ctx
    pid = _proposta_finalizada(db, cli, date.today() - timedelta(days=60))  # retornos já vencidos
    assert not db.get_pending_post_actions_for_dashboard().empty
    assert not db.get_post_organizations().empty

    db.update_proposta(pid, status="em_execucao")
    db.session.expire_all()
    assert db.get_pending_post_actions_for_dashboard().empty
    assert db.get_post_organizations().empty
    assert _acoes(db, pid)[1], "as ações continuam no banco; só não aparecem"


def test_finalizar_de_novo_remarca_os_retornos_pendentes(ctx):
    db, cli = ctx
    fim_antigo = date.today() - timedelta(days=60)
    pid = _proposta_finalizada(db, cli, fim_antigo)
    _, antes = _acoes(db, pid)
    prazos = {a.id: a.due_date for a in antes}

    novo_fim = date.today()
    db.create_post_organization(proposta_id=pid, cliente_id=cli, data_final_projeto=novo_fim)
    po, depois = _acoes(db, pid)
    assert po.data_final_projeto == novo_fim
    for a in depois:
        assert a.due_date == prazos[a.id] + (novo_fim - fim_antigo)
