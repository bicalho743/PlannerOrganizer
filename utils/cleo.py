"""
Cléo, a assistente de voz do app.

O app transcreve a fala no próprio celular e manda o TEXTO para cá. Este módulo pede ao Claude
(Haiku, o mais barato) para entender o pedido e devolver ações simples que o app executa:
abrir uma tela, abrir um formulário já preenchido, salvar ou fechar. Nada é gravado aqui:
quem grava é o app, depois que a usuária confere e confirma.
"""
import json
import os
import threading
from datetime import date, datetime
from zoneinfo import ZoneInfo

import anthropic

MODELO = os.getenv("CLEO_MODELO", "claude-haiku-5-5")
FUSO = ZoneInfo("America/Sao_Paulo")   # o servidor roda em UTC: depois das 21h "amanhã" cairia um dia adiante
LIMITE_DIARIO = int(os.getenv("CLEO_LIMITE_DIARIO", "150"))   # pedidos por conta por dia (protege o gasto com a API)
MAX_TEXTO = 600
# dados pessoais das clientes que nunca vão ao modelo (o app também os retira antes de enviar)
CAMPOS_SENSIVEIS = {"cpf", "telefone", "email", "endereco", "pix", "data_nascimento"}
MAX_CLIENTES = 300

TELAS = ["inicio", "propostas", "agenda", "financeiro", "clientes", "vendas",
         "pos_organizacao", "relatorios", "pdf", "precificacao", "perfil", "menu"]

SISTEMA = """Você é a Cléo, assistente de voz do app Planner Organiza, usado por personal organizers no Brasil.
Fale sempre em português do Brasil, em frases curtas e simpáticas, como quem conversa. Sem jargão.

O que você faz: SÓ a Agenda. Você abre o formulário de compromisso da Agenda JÁ PREENCHIDO com o que a usuária disse
(serviço, visita, retorno, reunião, lembrete com data e hora). Você nunca grava
nada sozinha: a usuária confere o formulário na tela e diz "salvar" (ou toca em salvar).

Regras:
- Hoje é {hoje} ({dia_semana}). Converta datas faladas ("amanhã", "sexta", "dia 20") para AAAA-MM-DD e horas para HH:MM (24h).
- Valores em reais viram número (ex.: "mil e duzentos" = 1200).
- Pedidos de proposta, financeiro, cadastro de cliente ou outra tela: diga com gentileza que por voz você só cuida da
  Agenda e que o resto é pelo app. Não use ferramenta nesses casos.
- Cliente: use exatamente um nome da lista de clientes quando a usuária citar uma. Se não achar, passe o nome falado
  mesmo assim e avise que não encontrou. Nunca invente cliente, valor, data ou telefone: se faltar algo importante,
  preencha o que sabe e pergunte o resto em uma frase.
- "Salvar", "confirma", "pode salvar" -> use salvar_formulario. "Fecha", "cancela", "deixa pra lá" -> use fechar_formulario.
- Se o pedido não tiver relação com o app, diga com gentileza que você ajuda a marcar compromissos na Agenda.
- Sempre responda com uma frase curta de fala (o app lê e mostra). Use as ferramentas para as ações.

Tela atual da usuária: {tela}. Formulário aberto agora: {formulario}.
Valores já preenchidos nesse formulário: {valores}
Se já há formulário aberto do mesmo tipo e a usuária só complementa ou corrige ("sexta", "muda o valor para 500", "põe o
telefone"), use a ferramenta de preencher apenas com o que MUDA: o app junta com o que já estava. Nunca repita tudo.
Clientes cadastradas (nomes): {clientes}"""

FERRAMENTAS = [
    {"name": "preencher_compromisso",
     "description": "Abre o formulário de novo compromisso da Agenda, preenchido.",
     "input_schema": {"type": "object", "properties": {
         "titulo": {"type": "string"}, "data": {"type": "string", "description": "AAAA-MM-DD"},
         "hora": {"type": "string", "description": "HH:MM"}, "cliente": {"type": "string"},
         "local": {"type": "string"}, "valor": {"type": "number"}, "observacoes": {"type": "string"}}}},
    {"name": "salvar_formulario", "description": "Confirma e salva o formulário que está aberto.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "fechar_formulario", "description": "Fecha o formulário aberto sem salvar.",
     "input_schema": {"type": "object", "properties": {}}},
]

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

# nome da ferramenta -> tipo de ação que o app entende
_FORMULARIOS = {"preencher_compromisso": "compromisso"}   # desde 28/11/2026 a Cléo é só da Agenda


_cliente = None


def _chamar_claude(corpo: dict) -> dict:
    """Chama o Claude pelo SDK oficial e devolve a resposta como dicionário."""
    global _cliente
    if _cliente is None:
        _cliente = anthropic.Anthropic(timeout=25.0, max_retries=1)   # lê ANTHROPIC_API_KEY do ambiente
    return _cliente.messages.create(**corpo).model_dump()


_usos: dict = {}
_trava = threading.Lock()


def dentro_do_limite(uid: str, agora: datetime | None = None) -> bool:
    """Conta um pedido da conta hoje (horário de Brasília). False quando passou do limite diário."""
    dia = (agora or datetime.now(FUSO)).date().isoformat()
    with _trava:
        for chave in [k for k in _usos if k[1] != dia]:
            del _usos[chave]
        _usos[(uid, dia)] = _usos.get((uid, dia), 0) + 1
        return _usos[(uid, dia)] <= LIMITE_DIARIO


def _valores_texto(valores) -> str:
    if not isinstance(valores, dict) or not valores:
        return "(nenhum)"
    limpo = {str(k)[:30]: str(v)[:120] for k, v in list(valores.items())[:12]
             if v not in (None, "") and str(k).lower() not in CAMPOS_SENSIVEIS}
    return json.dumps(limpo, ensure_ascii=False) if limpo else "(nenhum)"


def interpretar(texto: str, tela: str = "", formulario: str = "", clientes=None, valores=None,
                hoje: date | None = None, chamar=_chamar_claude) -> dict:
    """Devolve {"fala": str, "acoes": [ {tipo, ...} ]}. `chamar` existe para os testes."""
    texto = (texto or "").strip()[:MAX_TEXTO]
    if not texto:
        return {"fala": "Não ouvi nada. Pode repetir?", "acoes": []}
    hoje = hoje or datetime.now(FUSO).date()
    nomes = [str(n)[:80] for n in (clientes or [])][:MAX_CLIENTES]
    sistema = SISTEMA.format(
        hoje=hoje.isoformat(), dia_semana=DIAS[hoje.weekday()], tela=tela or "desconhecida",
        formulario=formulario or "nenhum", valores=_valores_texto(valores), clientes="; ".join(nomes) if nomes else "(nenhuma)")
    resp = chamar({"model": MODELO, "max_tokens": 500, "system": sistema,
                   "tools": FERRAMENTAS, "messages": [{"role": "user", "content": texto}]})
    fala, acoes = [], []
    for bloco in resp.get("content", []):
        if bloco.get("type") == "text" and bloco.get("text", "").strip():
            fala.append(bloco["text"].strip())
        elif bloco.get("type") == "tool_use":
            nome, dados = bloco.get("name"), bloco.get("input") or {}
            if nome in _FORMULARIOS:
                campos = {k: v for k, v in dados.items() if v not in (None, "")}
                acoes.append({"tipo": "formulario", "formulario": _FORMULARIOS[nome], "campos": campos})
            elif nome in ("salvar_formulario", "fechar_formulario") and formulario in ("", "compromisso"):
                # versões antigas do app ainda mostram a Cléo em outros formulários: lá ela não salva nem fecha
                acoes.append({"tipo": nome.split("_")[0]})
    return {"fala": " ".join(fala) or ("Pronto." if acoes else "Não entendi. Pode falar de outro jeito?"),
            "acoes": acoes}
