"""
Funil de conversão: do cadastro à assinatura, por canal (app ou site) e por origem (anúncio, Instagram...).

O que já existe no banco é lido direto (perfis, clientes, propostas, plano). Só o que não fica guardado em
lugar nenhum vira evento em `eventos_funil`, gravado uma única vez por conta (vale a primeira vez):
- conta_criada   (canal: app ou site)
- primeiro_pdf   (gerou o primeiro PDF de proposta)
- planos_vistos  (abriu a tela de planos / Plano e cobrança)

Etapas do funil (cada uma é um subconjunto da anterior só na leitura; a conta pode pular etapas):
cadastro → questionário respondido → 1º cliente → 1ª proposta → 1º PDF → viu os planos → assinou.
"""
import json
from datetime import date, datetime, timedelta

from sqlalchemy import text

EVENTOS = ("conta_criada", "primeiro_pdf", "planos_vistos")

ETAPAS = [
    ("cadastro", "Criou a conta"),
    ("onboarding", "Respondeu o questionário"),
    ("cliente", "Cadastrou o 1º cliente"),
    ("proposta", "Criou a 1ª proposta"),
    ("pdf", "Gerou o 1º PDF"),
    ("planos", "Viu a tela de planos"),
    ("assinou", "Assinou"),
]

_PRONTAS = set()


def criar_tabela(engine) -> None:
    if id(engine) in _PRONTAS:
        return
    with engine.begin() as c:
        c.execute(text(
            "CREATE TABLE IF NOT EXISTS eventos_funil ("
            "usuario_id TEXT NOT NULL, nome TEXT NOT NULL, canal TEXT, "
            "criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (usuario_id, nome))"))
    _PRONTAS.add(id(engine))


def registrar(engine, uid, nome, canal="") -> bool:
    """Grava o evento na primeira vez. Nunca levanta erro (medição não pode atrapalhar o uso)."""
    if not uid or nome not in EVENTOS:
        return False
    try:
        criar_tabela(engine)
        with engine.begin() as c:
            n = c.execute(text(
                "INSERT INTO eventos_funil (usuario_id, nome, canal) VALUES (:u, :n, :c) "
                "ON CONFLICT DO NOTHING"), {"u": uid, "n": nome, "c": (canal or "")[:20]}).rowcount
        return n > 0
    except Exception as e:
        print(f"[funil] {nome} {uid}: {e}")
        return False


def _origem(txt):
    try:
        o = json.loads(txt) if txt else {}
    except (TypeError, ValueError):
        o = {}
    fonte = (o.get("utm_source") or "").lower()
    if o.get("ref"):
        return "afiliada"
    if fonte in ("facebook", "fb", "ig", "instagram", "meta"):
        return "anúncio Meta" if (o.get("utm_medium") or "").lower() in ("paid", "cpc", "ads") else "Instagram/Facebook"
    return fonte or "sem origem"


def contas(engine, desde: date, ate: date = None) -> list:
    """Uma linha por conta criada no período, com cada etapa marcada (True/False)."""
    criar_tabela(engine)
    ate = ate or date.today()
    with engine.connect() as c:
        linhas = c.execute(text(
            "SELECT p.usuario_id, p.email, p.data_cadastro, p.plano, p.onboarding, p.origem_cadastro, "
            " (SELECT canal FROM eventos_funil e WHERE e.usuario_id = p.usuario_id AND e.nome = 'conta_criada') AS canal, "
            " EXISTS (SELECT 1 FROM clientes x WHERE x.usuario_id = p.usuario_id) AS cliente, "
            " EXISTS (SELECT 1 FROM propostas x WHERE x.usuario_id = p.usuario_id) AS proposta, "
            " EXISTS (SELECT 1 FROM eventos_funil e WHERE e.usuario_id = p.usuario_id AND e.nome = 'primeiro_pdf') AS pdf, "
            " EXISTS (SELECT 1 FROM eventos_funil e WHERE e.usuario_id = p.usuario_id AND e.nome = 'planos_vistos') AS planos "
            "FROM perfis p WHERE p.data_cadastro >= :d AND p.data_cadastro <= :a ORDER BY p.data_cadastro DESC"),
            {"d": desde, "a": ate}).mappings().all()
    saida = []
    for r in linhas:
        try:
            onb = json.loads(r["onboarding"]) if r["onboarding"] else {}
        except (TypeError, ValueError):
            onb = {}
        saida.append({
            "usuario_id": r["usuario_id"], "email": r["email"], "data_cadastro": r["data_cadastro"],
            "canal": r["canal"] or "?", "origem": _origem(r["origem_cadastro"]),
            "cadastro": True,
            "onboarding": bool(onb.get("respondido") or onb.get("tempo") or onb.get("dores") or onb.get("formal")),
            "cliente": bool(r["cliente"]), "proposta": bool(r["proposta"]), "pdf": bool(r["pdf"]),
            "planos": bool(r["planos"]), "assinou": (r["plano"] or "") in ("pro", "ativo"),
        })
    return saida


def resumo(lista: list) -> list:
    """[(chave, rótulo, quantidade, % do total, % da etapa anterior)]."""
    total = len(lista)
    saida, anterior = [], total
    for chave, rotulo in ETAPAS:
        n = sum(1 for x in lista if x[chave])
        saida.append((chave, rotulo, n, (n / total * 100) if total else 0.0, (n / anterior * 100) if anterior else 0.0))
        anterior = n
    return saida


def por_grupo(lista: list, campo: str) -> dict:
    grupos = {}
    for x in lista:
        grupos.setdefault(x[campo], []).append(x)
    return grupos


def periodo(dias: int):
    hoje = date.today()
    return hoje - timedelta(days=dias - 1), hoje
