"""Textos da tela Propostas (utils/propostas_dados.py): descrição que vai para o PDF, cartões do quadro."""
from datetime import date, timedelta

from utils import propostas_dados as d
from utils.pdf_proposta import ambientes_da_descricao


def test_descricao_simples_vira_lista_no_pdf():
    txt = d.montar_descricao("organizacao", [("Cozinha", 1), ("Closet / guarda-roupa", 2)], dias=2, assistentes=1)
    assert txt.startswith("Organização de Cozinha, Closet / guarda-roupa (2).")
    assert ambientes_da_descricao(txt) == [("Cozinha", "1 ambiente"), ("Closet / guarda-roupa", "2 ambientes")]
    assert "com 1 assistente" in txt


def test_mudanca_por_comodo_lista_os_comodos_sem_as_caixas():
    txt = d.montar_descricao("pre", [("Cozinha", 12), ("Sala", 8)], caixas=20, dias=2)
    assert [n for n, _ in ambientes_da_descricao(txt)] == ["Cozinha", "Sala"]
    assert "Volume estimado: 20 caixas." in txt


def test_observacoes_e_materiais_saem_como_texto_corrido():
    txt = d.montar_descricao("pre", [("Cozinha", 12)], caixas=12, materiais=["Caixas de papelão", "Fita adesiva"],
                             observacoes="Louças frágeis.", mostrar_obs=True)
    assert ambientes_da_descricao(txt) == []          # o PDF mostra a descrição inteira
    assert "Materiais inclusos: caixas de papelão e fita adesiva." in txt
    assert txt.endswith("Observações da visita: Louças frágeis.")


def test_observacoes_escondidas_nao_vao_para_a_descricao():
    txt = d.montar_descricao("organizacao", [("Cozinha", 1)], observacoes="Segredo", mostrar_obs=False)
    assert "Segredo" not in txt


def test_mudanca_sem_comodos():
    txt = d.montar_descricao("pos", [], caixas=40, dias=3)
    assert txt.startswith("Pós-mudança. Volume estimado: 40 caixas.")
    assert ambientes_da_descricao(txt) == []


def test_servico_curto():
    assert d.servico_curto({"descricao": "Organização de Área de serviço. Prazo"}) == "Área de serviço"
    assert d.servico_curto({"descricao": "Organização de Cozinha, Despensa. P"}) == "Cozinha e Despensa"
    assert d.servico_curto({"descricao": "Pós-mudança. Volume", "tipo_proposta": "Pós-mudança"}) == "Pós-mudança"


def test_envio_rascunho_e_proposta_antiga():
    hoje = date.today()
    marcas = [{"data": hoje, "status": "Rascunho", "observacao": ""}]
    assert d.envio({}, marcas) == ("rascunho", hoje)
    marcas.append({"data": hoje, "status": "Enviada", "observacao": ""})
    assert d.envio({}, marcas)[0] == "enviada"
    # sem marca (feita antes da Nova proposta): enviada na data da proposta
    assert d.envio({"data_proposta": hoje - timedelta(days=4)}, []) == ("enviada", hoje - timedelta(days=4))


def test_dia_do_servico():
    hoje = date(2026, 11, 25)
    p = {"data_inicio_execucao": hoje, "data_fim": hoje + timedelta(days=1)}
    assert d.dia_do_servico(p, hoje) == (1, 2)
    assert d.dia_do_servico({"data_inicio": hoje, "previsao_dias": 3}, hoje + timedelta(days=1)) == (2, 3)
