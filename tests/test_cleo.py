"""Cléo: a resposta do Claude vira ações simples para o app (sem chamar a rede)."""
from datetime import date

from utils.cleo import interpretar


def _resposta(*blocos):
    return lambda corpo: {"content": list(blocos)}


def test_compromisso_preenchido():
    r = interpretar("marca a Ana sexta às 14h", clientes=["Ana Souza"], hoje=date(2026, 11, 16),
                    chamar=_resposta(
                        {"type": "text", "text": "Abri o compromisso com a Ana."},
                        {"type": "tool_use", "name": "preencher_compromisso",
                         "input": {"titulo": "Visita", "data": "2026-11-20", "hora": "14:00",
                                   "cliente": "Ana Souza", "local": ""}}))
    assert r["fala"] == "Abri o compromisso com a Ana."
    assert r["acoes"] == [{"tipo": "formulario", "formulario": "compromisso",
                           "campos": {"titulo": "Visita", "data": "2026-11-20", "hora": "14:00", "cliente": "Ana Souza"}}]


def test_salvar_e_fechar():
    r = interpretar("pode salvar", chamar=_resposta({"type": "tool_use", "name": "salvar_formulario", "input": {}}))
    assert r["acoes"] == [{"tipo": "salvar"}] and r["fala"] == "Pronto."
    r = interpretar("cancela", chamar=_resposta({"type": "tool_use", "name": "fechar_formulario", "input": {}}))
    assert r["acoes"] == [{"tipo": "fechar"}]


def test_tela_invalida_e_ignorada():
    r = interpretar("abre", chamar=_resposta({"type": "tool_use", "name": "abrir_tela", "input": {"tela": "hackear"}}))
    assert r["acoes"] == []


def test_texto_vazio_nao_chama_o_claude():
    def nao_deve_chamar(corpo):
        raise AssertionError("não devia chamar")
    assert interpretar("   ", chamar=nao_deve_chamar)["acoes"] == []


def test_prompt_traz_data_e_clientes():
    visto = {}
    def espia(corpo):
        visto.update(corpo); return {"content": []}
    interpretar("oi", tela="agenda", clientes=["Bia"], hoje=date(2026, 11, 16), chamar=espia)
    assert "2026-11-16" in visto["system"] and "segunda-feira" in visto["system"] and "Bia" in visto["system"]


def test_valores_do_formulario_vao_no_prompt():
    visto = {}
    def espia(corpo):
        visto.update(corpo); return {"content": []}
    interpretar("sexta", formulario="compromisso", valores={"titulo": "Visita", "hora": ""}, chamar=espia)
    assert '"titulo": "Visita"' in visto["system"] and "hora" not in visto["system"].split("Valores já preenchidos")[1].split("\n")[0]


def test_data_de_hoje_usa_horario_de_brasilia():
    from utils.cleo import FUSO
    from datetime import datetime
    # 01:00 UTC de 17/11 ainda é 16/11 em Brasília
    assert datetime(2026, 11, 17, 1, 0, tzinfo=__import__("zoneinfo").ZoneInfo("UTC")).astimezone(FUSO).date().isoformat() == "2026-11-16"


def test_limite_diario(monkeypatch):
    import utils.cleo as c
    monkeypatch.setattr(c, "LIMITE_DIARIO", 2)
    c._usos.clear()
    assert c.dentro_do_limite("u") and c.dentro_do_limite("u") and not c.dentro_do_limite("u")
    assert c.dentro_do_limite("outra")


def test_dados_sensiveis_nao_vao_no_prompt():
    visto = {}
    def espia(corpo):
        visto.update(corpo); return {"content": []}
    interpretar("ok", formulario="cliente", valores={"nome": "Ana", "cpf": "123.456.789-00", "telefone": "31999990000",
                                                      "email": "a@b.com", "endereco": "Rua X"}, chamar=espia)
    assert "Ana" in visto["system"]
    for segredo in ("123.456.789-00", "31999990000", "a@b.com", "Rua X"):
        assert segredo not in visto["system"]


def test_cleo_so_no_plano_pro(monkeypatch):
    from utils.trial import cleo_liberada
    monkeypatch.setenv("TRIAL_ISENTOS", "dono@exemplo.com")
    assert cleo_liberada({"plano": "pro"})
    assert cleo_liberada({"plano": "ativo"})
    assert cleo_liberada({"plano": "gratuito", "email": "Dono@Exemplo.com"})
    assert not cleo_liberada({"plano": "gratuito", "email": "outra@exemplo.com"})
    assert not cleo_liberada({"plano": "cancelado"})
    assert not cleo_liberada(None)


def test_so_agenda_ignora_outros_formularios():
    """Desde 28/11/2026 a Cléo é só da Agenda: pedido de proposta ou lançamento não vira ação."""
    r = interpretar("proposta pra Carla de 3 mil", chamar=_resposta(
        {"type": "text", "text": "Por voz eu só cuido da Agenda."},
        {"type": "tool_use", "name": "preencher_proposta", "input": {"cliente": "Carla", "valor": 3000}},
        {"type": "tool_use", "name": "abrir_tela", "input": {"tela": "financeiro"}}))
    assert r["acoes"] == [] and "Agenda" in r["fala"]


def test_nao_salva_formulario_de_outra_tela():
    """Versões antigas mostram a Cléo na proposta: lá 'salvar' não pode valer."""
    r = interpretar("pode salvar", formulario="proposta",
                    chamar=_resposta({"type": "tool_use", "name": "salvar_formulario", "input": {}}))
    assert r["acoes"] == []
    r = interpretar("pode salvar", formulario="compromisso",
                    chamar=_resposta({"type": "tool_use", "name": "salvar_formulario", "input": {}}))
    assert r["acoes"] == [{"tipo": "salvar"}]
