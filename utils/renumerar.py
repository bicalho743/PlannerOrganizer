"""
Renumerar as propostas de uma conta: 1, 2, 3... na ordem da data da proposta (e do id, no empate).

Para contas antigas, criadas quando o número seguia a contagem do banco todo (ex.: 77, 104, 351).
Só funciona com o índice novo (número único por conta, idx_proposta_usuario_numero). O id não muda:
lançamentos, itens e PDFs continuam ligados à proposta; só o número mostrado é trocado.
"""
from sqlalchemy import text


def indice_por_conta(engine) -> bool:
    with engine.connect() as c:
        return c.execute(text("SELECT 1 FROM pg_indexes WHERE tablename = 'propostas' "
                              "AND indexname = 'idx_proposta_usuario_numero'")).first() is not None and \
            c.execute(text("SELECT 1 FROM pg_indexes WHERE tablename = 'propostas' "
                           "AND indexname = 'idx_proposta_numero'")).first() is None


def previa(engine, usuario_id):
    """[(id, número atual, número novo, data)] na ordem nova."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT id, numero, data_proposta, row_number() OVER (ORDER BY data_proposta NULLS LAST, id) AS novo "
            "FROM propostas WHERE usuario_id = :u ORDER BY novo"), {"u": usuario_id}).all()
    return [(r.id, r.numero, int(r.novo), r.data_proposta) for r in rows]


def renumerar(engine, usuario_id) -> int:
    """Aplica a numeração nova. Devolve quantas propostas mudaram de número."""
    if not indice_por_conta(engine):
        raise RuntimeError("O banco ainda está com o número único no banco todo; abra o site uma vez e tente de novo.")
    with engine.begin() as c:
        mudam = c.execute(text(
            "SELECT count(*) FROM (SELECT numero, row_number() OVER (ORDER BY data_proposta NULLS LAST, id) n "
            "FROM propostas WHERE usuario_id = :u) t WHERE numero <> n"), {"u": usuario_id}).scalar()
        c.execute(text("UPDATE propostas SET numero = -id WHERE usuario_id = :u"), {"u": usuario_id})
        c.execute(text(
            "UPDATE propostas p SET numero = r.n FROM (SELECT id, row_number() OVER "
            "(ORDER BY data_proposta NULLS LAST, id) n FROM propostas WHERE usuario_id = :u) r "
            "WHERE p.id = r.id"), {"u": usuario_id})
    return int(mudam or 0)
