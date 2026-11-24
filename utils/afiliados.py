"""
Programa de afiliadas: quem indica o Planner ganha 25% de cada pagamento da conta indicada, por 12 meses,
e a indicada ganha 10% de desconto no plano anual (R$ 429,90 em vez de R$ 479,90).

Fluxo
- A afiliada se inscreve no site (com a conta dela) e fica `pendente` até a dona aprovar.
- Aprovada, ganha um código (ex.: TAMARA) e o link plannerorganiza.com.br/?ref=TAMARA.
- A conta nova fica ligada à afiliada quando entra pelo link (o site guarda o `ref` da visita) ou digita o
  código em "Tenho um convite" (app e site). O teste grátis continua o padrão (7 dias). Cada conta tem uma afiliada só, e
  ninguém indica a si mesma.
- Cada pagamento da conta indicada (Stripe, App Store ou Google Play) gera uma comissão de 25% do valor
  líquido (sem a taxa da loja ou do cartão), durante 12 meses a partir do 1º pagamento.
- A comissão fica liberada 30 dias depois do pagamento (prazo de reembolso). Reembolso cancela a comissão.
- Todo mês a dona paga por Pix quem tem R$ 50 ou mais liberados e marca como pago.
- Contra fraude: cada CPF e cada chave Pix só podem ter uma inscrição (que não tenha sido recusada).

As tabelas são criadas aqui (CREATE IF NOT EXISTS) e funcionam no Postgres e no SQLite dos testes.
"""
import re
from datetime import date, datetime, timedelta
from sqlalchemy import text

PERCENTUAL = 0.25  # até 24/11/2026 era 30% (sem desconto para a indicada)
DESCONTO_INDICADA = 0.10  # no plano anual: R$ 429,90 em vez de R$ 479,90 (site e, no app, a partir da 1.0.20)
PRECO_ANUAL_INDICADA = 429.90
MESES_COMISSAO = 12
DIAS_LIBERAR = 30
MINIMO_PAGAMENTO = 50.0
DIAS_TESTE_INDICADA = 7  # igual ao padrão: indicação não estende o teste (evita uso só para não pagar)
# taxa que a loja ou o cartão ficam (fração do valor e valor fixo em R$); comissão é sobre o que sobra
TAXAS = {"stripe": (0.0399, 0.39), "apple": (0.15, 0.0), "google": (0.15, 0.0)}
CANAIS = {"stripe": "Site (cartão)", "apple": "App Store", "google": "Google Play"}


class AfiliadoInvalido(ValueError):
    """Mensagem pronta para mostrar."""


def criar_tabelas(engine) -> None:
    with engine.begin() as c:
        c.execute(text(
            "CREATE TABLE IF NOT EXISTS afiliados ("
            "codigo TEXT PRIMARY KEY, usuario_id TEXT UNIQUE, nome TEXT NOT NULL, email TEXT, cpf TEXT, "
            "pix TEXT, instagram TEXT, status TEXT NOT NULL DEFAULT 'pendente', "
            "criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, aprovado_em TIMESTAMP)"))
        c.execute(text(
            "CREATE TABLE IF NOT EXISTS indicacoes ("
            "usuario_id TEXT PRIMARY KEY, codigo TEXT NOT NULL, origem TEXT, "
            "criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        c.execute(text(
            "CREATE TABLE IF NOT EXISTS comissoes ("
            "ref TEXT PRIMARY KEY, codigo TEXT NOT NULL, usuario_id TEXT NOT NULL, canal TEXT NOT NULL, "
            "valor_pago NUMERIC NOT NULL, valor_liquido NUMERIC NOT NULL, comissao NUMERIC NOT NULL, "
            "pago_em DATE NOT NULL, liberada_em DATE NOT NULL, status TEXT NOT NULL DEFAULT 'pendente', "
            "paga_em DATE)"))


def _codigo(txt: str) -> str:
    import unicodedata
    sem_acento = unicodedata.normalize("NFKD", txt or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", sem_acento.upper())[:20]


def _data(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


# ── afiliadas ────────────────────────────────────────────────────────────────

def afiliada_da_conta(engine, uid):
    criar_tabelas(engine)
    with engine.connect() as c:
        r = c.execute(text("SELECT * FROM afiliados WHERE usuario_id = :u"), {"u": uid}).mappings().first()
    return dict(r) if r else None


def inscrever(engine, uid, nome, email, cpf, pix, instagram="", codigo_desejado="") -> str:
    """Cria a inscrição (pendente). Devolve o código reservado."""
    criar_tabelas(engine)
    nome, pix, cpf = (nome or "").strip(), (pix or "").strip(), re.sub(r"\D", "", cpf or "")
    if not nome or not pix:
        raise AfiliadoInvalido("Preencha o nome e a chave Pix.")
    if len(cpf) != 11:
        raise AfiliadoInvalido("Digite um CPF com 11 números.")
    if afiliada_da_conta(engine, uid):
        raise AfiliadoInvalido("Esta conta já tem uma inscrição no programa.")
    with engine.connect() as c:  # um CPF e uma chave Pix por afiliada (contra contas duplicadas)
        if c.execute(text("SELECT 1 FROM afiliados WHERE cpf = :c AND status <> 'recusada'"), {"c": cpf}).first():
            raise AfiliadoInvalido("Este CPF já tem uma inscrição no programa.")
        if c.execute(text("SELECT 1 FROM afiliados WHERE lower(pix) = :p AND status <> 'recusada'"),
                     {"p": pix.lower()}).first():
            raise AfiliadoInvalido("Esta chave Pix já está cadastrada no programa.")
    base = _codigo(codigo_desejado) or _codigo(nome.split()[0])
    if len(base) < 3:
        raise AfiliadoInvalido("O código precisa de pelo menos 3 letras ou números.")
    with engine.begin() as c:
        codigo, n = base, 1
        while c.execute(text("SELECT 1 FROM afiliados WHERE codigo = :c"), {"c": codigo}).first() or \
                _e_convite(c, codigo):
            n += 1
            codigo = f"{base}{n}"
        c.execute(text(
            "INSERT INTO afiliados (codigo, usuario_id, nome, email, cpf, pix, instagram) "
            "VALUES (:c, :u, :n, :e, :cpf, :p, :i)"),
            {"c": codigo, "u": uid, "n": nome, "e": (email or "").strip().lower(), "cpf": cpf, "p": pix,
             "i": (instagram or "").strip()})
    return codigo


def _e_convite(conn, codigo) -> bool:
    try:
        return bool(conn.execute(text("SELECT 1 FROM convites WHERE codigo = :c"), {"c": codigo}).first())
    except Exception:
        return False


def mudar_status(engine, codigo, status) -> None:
    assert status in ("aprovada", "recusada", "pendente")
    criar_tabelas(engine)
    with engine.begin() as c:
        c.execute(text("UPDATE afiliados SET status = :s, aprovado_em = CASE WHEN :s = 'aprovada' "
                       "THEN CURRENT_TIMESTAMP ELSE aprovado_em END WHERE codigo = :c"),
                  {"s": status, "c": _codigo(codigo)})


def excluir(engine, codigo) -> dict:
    """Apaga a afiliada (ex.: inscrição de teste), as indicações ligadas ao código e as comissões não pagas.

    Recusa se já houver comissão paga, para não perder o histórico do que saiu por Pix.
    As contas indicadas continuam existindo; só deixam de estar ligadas a esse código (e perdem o desconto).
    """
    codigo = _codigo(codigo)
    with engine.begin() as c:
        if not c.execute(text("SELECT 1 FROM afiliados WHERE codigo = :c"), {"c": codigo}).first():
            raise AfiliadoInvalido("Afiliada não encontrada.")
        if c.execute(text("SELECT 1 FROM comissoes WHERE codigo = :c AND status = 'paga'"), {"c": codigo}).first():
            raise AfiliadoInvalido("Essa afiliada já recebeu comissão: não dá para excluir. Recuse ou deixe como está.")
        com = c.execute(text("DELETE FROM comissoes WHERE codigo = :c"), {"c": codigo}).rowcount
        ind = c.execute(text("DELETE FROM indicacoes WHERE codigo = :c"), {"c": codigo}).rowcount
        c.execute(text("DELETE FROM afiliados WHERE codigo = :c"), {"c": codigo})
    return {"indicacoes": ind, "comissoes": com}


def listar_afiliadas(engine, status=None):
    criar_tabelas(engine)
    sql = "SELECT * FROM afiliados" + (" WHERE status = :s" if status else "") + " ORDER BY criado_em"
    with engine.connect() as c:
        return [dict(r) for r in c.execute(text(sql), {"s": status}).mappings()]


# ── indicações ───────────────────────────────────────────────────────────────

def afiliada_aprovada(engine, codigo):
    criar_tabelas(engine)
    with engine.connect() as c:
        r = c.execute(text("SELECT * FROM afiliados WHERE codigo = :c AND status = 'aprovada'"),
                      {"c": _codigo(codigo)}).mappings().first()
    return dict(r) if r else None


def vincular(engine, uid, codigo, origem="codigo", email_conta="") -> dict:
    """Liga a conta à afiliada. Levanta AfiliadoInvalido se não der."""
    criar_tabelas(engine)
    af = afiliada_aprovada(engine, codigo)
    if not af:
        raise AfiliadoInvalido("Código não encontrado. Confira o código.")
    if af["usuario_id"] == uid or (email_conta and af.get("email") and af["email"] == email_conta.strip().lower()):
        raise AfiliadoInvalido("Não é possível usar o próprio código.")
    with engine.begin() as c:
        if c.execute(text("SELECT 1 FROM indicacoes WHERE usuario_id = :u"), {"u": uid}).first():
            raise AfiliadoInvalido("Esta conta já foi indicada por alguém.")
        c.execute(text("INSERT INTO indicacoes (usuario_id, codigo, origem) VALUES (:u, :c, :o)"),
                  {"u": uid, "c": af["codigo"], "o": origem})
    _ligar_oferta_no_app(uid)
    return af


def _ligar_oferta_no_app(uid):
    """No app, a indicada passa a ver o anual com 10% (oferta 'indicacao' do RevenueCat), em segundo plano."""
    import os
    import threading
    if not os.environ.get("REVENUECAT_SECRET_KEY"):
        return  # testes e ambiente sem RevenueCat
    try:
        from utils.assinatura import aplicar_oferta_indicacao
        threading.Thread(target=aplicar_oferta_indicacao, args=(uid,), daemon=True).start()
    except Exception as e:
        print(f"[afiliados] oferta do app para {uid}: {e}")


def tem_desconto_indicada(engine, uid) -> bool:
    """A conta foi indicada por uma afiliada: vê o anual com 10% de desconto."""
    try:
        return bool(uid and codigo_da_indicacao(engine, uid))
    except Exception:
        return False


def codigo_da_indicacao(engine, uid):
    criar_tabelas(engine)
    with engine.connect() as c:
        r = c.execute(text("SELECT codigo FROM indicacoes WHERE usuario_id = :u"), {"u": uid}).first()
    return r[0] if r else None


# ── comissões ────────────────────────────────────────────────────────────────

def valor_liquido(canal, valor_pago, takehome=None) -> float:
    if takehome is not None and canal in ("apple", "google"):
        return round(float(valor_pago) * float(takehome), 2)
    pct, fixo = TAXAS.get(canal, (0.0, 0.0))
    return round(max(0.0, float(valor_pago) * (1 - pct) - fixo), 2)


def registrar_pagamento(engine, uid, canal, ref, valor_pago, pago_em=None, takehome=None):
    """Chamado a cada pagamento confirmado. Devolve a comissão criada (dict) ou None.
    Repetir o mesmo `ref` (evento reenviado) não duplica."""
    criar_tabelas(engine)
    if not uid or not ref or float(valor_pago or 0) <= 0:
        return None
    codigo = codigo_da_indicacao(engine, uid)
    if not codigo:
        return None
    pago_em = _data(pago_em or date.today())
    with engine.begin() as c:
        if c.execute(text("SELECT 1 FROM comissoes WHERE ref = :r"), {"r": ref}).first():
            return None
        primeiro = c.execute(text("SELECT MIN(pago_em) FROM comissoes WHERE usuario_id = :u AND codigo = :c"),
                             {"u": uid, "c": codigo}).scalar()
        if primeiro and pago_em >= _somar_meses(_data(primeiro), MESES_COMISSAO):
            return None  # passou dos 12 meses de comissão
        liquido = valor_liquido(canal, valor_pago, takehome)
        com = {"ref": ref, "codigo": codigo, "usuario_id": uid, "canal": canal, "valor_pago": round(float(valor_pago), 2),
               "valor_liquido": liquido, "comissao": round(liquido * PERCENTUAL, 2), "pago_em": pago_em,
               "liberada_em": pago_em + timedelta(days=DIAS_LIBERAR)}
        c.execute(text(
            "INSERT INTO comissoes (ref, codigo, usuario_id, canal, valor_pago, valor_liquido, comissao, pago_em, liberada_em) "
            "VALUES (:ref, :codigo, :usuario_id, :canal, :valor_pago, :valor_liquido, :comissao, :pago_em, :liberada_em)"), com)
    return com


def estornar(engine, ref) -> bool:
    """Reembolso: cancela a comissão ainda não paga desse pagamento."""
    criar_tabelas(engine)
    with engine.begin() as c:
        n = c.execute(text("UPDATE comissoes SET status = 'cancelada' WHERE ref = :r AND status = 'pendente'"),
                      {"r": ref}).rowcount
    return n > 0


def _somar_meses(d: date, meses: int) -> date:
    m = d.month - 1 + meses
    ano, mes = d.year + m // 12, m % 12 + 1
    from calendar import monthrange
    return date(ano, mes, min(d.day, monthrange(ano, mes)[1]))


# ── painéis ──────────────────────────────────────────────────────────────────

def painel(engine, codigo, hoje=None) -> dict:
    """Números da afiliada: indicações, assinantes e comissões."""
    criar_tabelas(engine)
    hoje = _data(hoje or date.today())
    with engine.connect() as c:
        indicadas = c.execute(text("SELECT COUNT(*) FROM indicacoes WHERE codigo = :c"), {"c": codigo}).scalar() or 0
        coms = [dict(r) for r in c.execute(text(
            "SELECT * FROM comissoes WHERE codigo = :c ORDER BY pago_em DESC"), {"c": codigo}).mappings()]
    validas = [x for x in coms if x["status"] != "cancelada"]
    soma = lambda f: round(sum(float(x["comissao"]) for x in validas if f(x)), 2)
    return {
        "indicadas": int(indicadas),
        "assinantes": len({x["usuario_id"] for x in validas}),
        "a_liberar": soma(lambda x: x["status"] == "pendente" and _data(x["liberada_em"]) > hoje),
        "liberado": soma(lambda x: x["status"] == "pendente" and _data(x["liberada_em"]) <= hoje),
        "recebido": soma(lambda x: x["status"] == "paga"),
        "comissoes": coms,
    }


def a_pagar(engine, hoje=None):
    """Afiliadas com R$ 50 ou mais liberados, para o Pix do mês."""
    criar_tabelas(engine)
    hoje = _data(hoje or date.today())
    lista = []
    for af in listar_afiliadas(engine, "aprovada"):
        p = painel(engine, af["codigo"], hoje)
        if p["liberado"] >= MINIMO_PAGAMENTO:
            lista.append({**af, "valor": p["liberado"]})
    return lista


def marcar_pago(engine, codigo, hoje=None) -> float:
    """Marca como pagas as comissões liberadas da afiliada. Devolve o total marcado."""
    criar_tabelas(engine)
    hoje = _data(hoje or date.today())
    with engine.begin() as c:
        total = c.execute(text(
            "SELECT COALESCE(SUM(comissao), 0) FROM comissoes WHERE codigo = :c AND status = 'pendente' "
            "AND liberada_em <= :h"), {"c": codigo, "h": hoje}).scalar() or 0
        c.execute(text("UPDATE comissoes SET status = 'paga', paga_em = :h WHERE codigo = :c "
                       "AND status = 'pendente' AND liberada_em <= :h"), {"c": codigo, "h": hoje})
    return round(float(total), 2)
