"""
Integração: compromisso da Agenda com valor gera "A receber" no Financeiro e fica em sincronia.

Bate no PostgreSQL de DATABASE_URL; cada execução usa um usuario_id único e apaga tudo no fim.
"""
import os
import uuid
from datetime import date

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL não definido")


def _limpar(engine, uid):
    with engine.connect() as c:
        for sql in ["DELETE FROM compromissos WHERE usuario_id = :u", "DELETE FROM financeiro WHERE usuario_id = :u",
                    "DELETE FROM clientes WHERE usuario_id = :u"]:
            c.execute(text(sql), {"u": uid})
        c.commit()


@pytest.fixture
def ctx():
    from utils.database import Database, engine
    uid = f"test-agenda-{uuid.uuid4().hex[:12]}"
    db = Database(usuario_id=uid)
    _limpar(engine, uid)
    cliente = db.add_cliente(nome="Organizer Ana")
    yield db, cliente
    _limpar(engine, uid)


def _lanc(db, tid):
    df = db.get_financeiro(force_reload=True)
    if df.empty:
        return None
    linha = df[df["id"] == tid]
    return None if linha.empty else linha.iloc[0]


def test_compromisso_com_valor_vira_a_receber_e_acompanha_edicao(ctx):
    db, cliente = ctx
    cid = db.salvar_compromisso(data=date(2026, 11, 10), titulo="Diária", hora="09:00", cliente_id=cliente, valor=200)
    comp = db.get_compromissos().iloc[0]
    assert comp["id"] == cid and comp["cliente_nome"] == "Organizer Ana" and comp["status_receita"] == "Pendente"
    lanc = _lanc(db, comp["transacao_id"])
    assert lanc["valor"] == 200 and lanc["status"] == "Pendente" and str(lanc["data"])[:10] == "2026-11-10"
    assert lanc["descricao"] == "Diária - Organizer Ana"

    db.salvar_compromisso(cid, data=date(2026, 11, 12), titulo="Diária", cliente_id=cliente, valor=250)
    lanc = _lanc(db, comp["transacao_id"])
    assert lanc["valor"] == 250 and str(lanc["data"])[:10] == "2026-11-12"

    db.salvar_compromisso(cid, data=date(2026, 11, 12), titulo="Diária", cliente_id=cliente, valor=0)
    assert _lanc(db, comp["transacao_id"]) is None
    assert pd_isna(db.get_compromissos().iloc[0]["transacao_id"])


def pd_isna(v):
    import pandas as pd
    return v is None or pd.isna(v)


def test_receita_recebida_nao_muda_e_fica_ao_excluir(ctx):
    db, cliente = ctx
    cid = db.salvar_compromisso(data=date(2026, 11, 10), titulo="Diária", cliente_id=cliente, valor=200)
    tid = int(db.get_compromissos().iloc[0]["transacao_id"])
    db.atualizar_status_transacao(tid, "Recebido", date(2026, 11, 10))
    db.salvar_compromisso(cid, data=date(2026, 11, 10), titulo="Diária", cliente_id=cliente, valor=999)
    assert _lanc(db, tid)["valor"] == 200
    assert db.excluir_compromisso(cid)
    assert db.get_compromissos().empty and _lanc(db, tid) is not None


def test_excluir_compromisso_apaga_receita_pendente(ctx):
    db, _ = ctx
    cid = db.salvar_compromisso(data=date(2026, 11, 10), titulo="Visita de orçamento", valor=150)
    tid = int(db.get_compromissos().iloc[0]["transacao_id"])
    assert db.excluir_compromisso(cid)
    assert _lanc(db, tid) is None


def test_lancar_das(ctx):
    db, _ = ctx
    tid = db.lancar_das(2026, 3, 86.05, date(2026, 4, 2))
    lanc = _lanc(db, tid)
    assert lanc["descricao"] == "DAS MEI competência 03/2026" and lanc["status"] == "Pago"


def test_regime_padrao_mei_e_troca(ctx):
    from utils.models import Perfil
    db, _ = ctx
    db.session.add(Perfil(usuario_id=db.usuario_id, email=f"{db.usuario_id}@teste.local", nome="Teste"))
    db.session.flush()
    try:
        assert db.get_regime() == {"regime": "MEI", "aliquota": None}
        assert db.salvar_regime("Simples Nacional", 7.5)
        assert db.get_regime() == {"regime": "Simples Nacional", "aliquota": 7.5}
        assert not db.salvar_regime("Inventado")
    finally:
        db.session.query(Perfil).filter_by(usuario_id=db.usuario_id).delete()
        db.session.flush()


def test_tutorial_aparece_ate_ser_visto(ctx):
    from utils.models import Perfil
    db, _ = ctx
    assert db.get_tutorial_visto() == "sem perfil"  # conta sem perfil não vê o tutorial (nada para mostrar)
    db.session.add(Perfil(usuario_id=db.usuario_id, email=f"{db.usuario_id}@teste.local", nome="Teste"))
    db.session.flush()
    try:
        assert db.get_tutorial_visto() is None
        assert db.marcar_tutorial_visto()
        assert db.get_tutorial_visto()
    finally:
        db.session.query(Perfil).filter_by(usuario_id=db.usuario_id).delete()
        db.session.flush()


def test_origem_do_cadastro_guarda_a_primeira(ctx):
    import json
    from utils.models import Perfil
    db, _ = ctx
    db.session.add(Perfil(usuario_id=db.usuario_id, email=f"{db.usuario_id}@teste.local", nome="Teste"))
    db.session.flush()
    try:
        assert db.salvar_origem_cadastro({"tema": "retorno", "utm_source": "instagram"})
        assert not db.salvar_origem_cadastro({"tema": "mei"})
        p = db.session.query(Perfil).filter_by(usuario_id=db.usuario_id).first()
        db.session.refresh(p)
        assert json.loads(p.origem_cadastro)["tema"] == "retorno"
    finally:
        db.session.query(Perfil).filter_by(usuario_id=db.usuario_id).delete()
        db.session.flush()


def test_modo_consulta_nao_grava_nada_mas_le(ctx, monkeypatch):
    """Teste grátis encerrado: leitura normal, toda gravação recusada (ORM e psycopg2 direto)."""
    import psycopg2
    from utils import somente_leitura
    db, cliente = ctx
    db.salvar_compromisso(data=date(2026, 11, 10), titulo="Antes do bloqueio", valor=100)
    monkeypatch.setattr(somente_leitura, "ativo", lambda: True)
    monkeypatch.setattr(somente_leitura, "tentou", lambda: None)
    assert len(db.get_compromissos()) == 1                       # lê
    for gravar in (lambda: db.salvar_compromisso(data=date(2026, 11, 11), titulo="Depois", valor=50),
                   lambda: db.lancar_das(2026, 3, 86.05, date(2026, 4, 2))):
        with pytest.raises(Exception, match="teste grátis terminou"):
            gravar()
    with pytest.raises(somente_leitura.ContaSomenteLeitura):
        with psycopg2.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
            cur.execute("UPDATE clientes SET nome = 'x' WHERE id = %s", (cliente,))
    monkeypatch.setattr(somente_leitura, "ativo", lambda: False)
    db.session.rollback()
    assert list(db.get_compromissos()["titulo"]) == ["Antes do bloqueio"]


def test_modo_consulta_nao_gera_pdf(monkeypatch, tmp_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from utils import somente_leitura
    monkeypatch.setattr(somente_leitura, "ativo", lambda: True)
    monkeypatch.setattr(somente_leitura, "tentou", lambda: None)
    doc = lambda: SimpleDocTemplate(str(tmp_path / "x.pdf"), pagesize=A4).build(
        [Paragraph("oi", getSampleStyleSheet()["Normal"])])
    with pytest.raises(somente_leitura.ContaSomenteLeitura):
        doc()
    with somente_leitura.liberar_pdf():  # manual do sistema
        doc()
    assert (tmp_path / "x.pdf").exists()
