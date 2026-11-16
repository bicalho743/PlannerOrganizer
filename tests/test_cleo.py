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
