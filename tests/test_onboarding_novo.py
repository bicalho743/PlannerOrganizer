"""Onboarding do site antes da conta: contas do orçamento e gravação do rascunho na conta nova."""
import os
import uuid

import pytest
import streamlit as st

from utils import onboarding_novo as ob
from utils import precificacao as pr

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa do Postgres de teste")


def _rascunho(**extra):
    o = ob._novo()
    o.update({"nome": "Ana", "empresa": "Ana Ribeiro Organização", "amb": {"Cozinha": 1, "Closet / guarda-roupa": 2},
              "assist": 1, "cliente": "Juliana Ferraz", "tel_cliente": "(11) 99999-0000", "whatsapp": "(11) 98765-4321",
              "cor": "Ameixa", "ok_whats": True})
    o.update(extra)
    return o


def test_hora_e_orcamento_usam_a_precificacao():
    o = _rascunho()
    p = ob.parametros(o)
    assert pr.hora_sugerida(p) > pr.hora_minima(p) > 0
    r = ob.orcamento(o)
    assert r["sugerido"] % 10 == 0 and r["sugerido"] >= r["preco_minimo"]
    assert r["pessoas"] == 2
    assert "Cozinha" in ob.descricao(o) and "Closet / guarda-roupa (2)" in ob.descricao(o)


def test_mudanca_conta_por_comodo():
    o = _rascunho(tipo="pre", amb={"Cozinha": 1, "Sala": 1})
    assert ob.horas_do_orcamento(o) == 2 * pr.AMBIENTES_PADRAO["Mudança (por cômodo)"]
    assert ob.descricao(o).startswith("Pré-mudança")


def test_sem_ambiente_nao_tem_preco():
    assert ob.orcamento(_rascunho(amb={})) is None


def test_rascunho_vira_conta_completa():
    from utils.database import Database
    uid = "onb-" + uuid.uuid4().hex[:10]
    db = Database(usuario_id=uid)
    db.create_perfil(uid, f"{uid}@teste.com", "Ana")
    st.session_state.db = db
    o = _rascunho(valor=2000.0, sinal_pct=40)
    tok = ob.salvar_rascunho(o)
    st.session_state.pop(ob.CHAVE, None)          # como na volta do Google: só o código sobrou
    st.session_state["_ob_token"] = tok
    resumo = ob.concluir(db)
    assert resumo and resumo["proposta_id"]
    props = db.get_propostas()
    assert len(props) == 1
    linha = props.iloc[0]
    assert float(linha["valor"]) == 2000.0 and float(linha.get("sinal") or 0) == 800.0
    assert "Juliana Ferraz" in db.get_clientes()["nome"].tolist()
    perfil = db.get_perfil_usuario() or {}
    assert perfil.get("empresa") == "Ana Ribeiro Organização"
    assert perfil.get("telefone") == "(11) 98765-4321"
    assert perfil.get("cor_principal") == ob.CORES["Ameixa"]
    assert float((db.get_precificacao() or {}).get("renda_desejada") or 0) == 5000.0
    assert ob.carregar_rascunho(tok) is None       # usado uma vez só
    assert ob.concluir(db) is None


def test_conta_que_ja_tem_proposta_nao_recebe_rascunho():
    from utils.database import Database
    uid = "onb-" + uuid.uuid4().hex[:10]
    db = Database(usuario_id=uid)
    db.create_perfil(uid, f"{uid}@teste.com", "Bia")
    st.session_state.db = db
    cli = db.add_cliente(nome="Cliente antiga")
    db.add_proposta(cliente_id=cli, descricao="x", valor=100, status="em_aberto", gerar_transacoes_automaticas=False)
    st.session_state["_ob_token"] = ob.salvar_rascunho(_rascunho())
    assert ob.concluir(db) is None
    assert len(db.get_propostas()) == 1


def test_numero_de_assistentes():
    o = _rascunho(assist=3)
    assert ob.orcamento(o)["pessoas"] == 4
    assert "com 3 assistentes" in ob.descricao(o)
    assert "atendimento individual" in ob.descricao(_rascunho(assist=0))


def test_numero_da_proposta_comeca_em_1_em_cada_conta():
    from utils.database import Database
    nums = []
    for nome in ("Ana", "Bia"):
        uid = "num-" + uuid.uuid4().hex[:10]
        db = Database(usuario_id=uid)
        db.create_perfil(uid, f"{uid}@teste.com", nome)
        cli = db.add_cliente(nome="Cliente")
        for _ in range(2):
            db.add_proposta(cliente_id=cli, descricao="x", valor=100, status="em_aberto",
                            gerar_transacoes_automaticas=False)
        nums.append(sorted(int(n) for n in db.get_propostas()["numero"]))
    assert nums == [[1, 2], [1, 2]]
