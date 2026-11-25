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


def renumerar_na_conexao(c, usuario_id):
    """Os dois passos da troca, numa conexão já em transação (usado também pela tarefa única do banco)."""
    c.execute(text("UPDATE propostas SET numero = -id WHERE usuario_id = :u"), {"u": usuario_id})
    c.execute(text(
        "UPDATE propostas p SET numero = r.n FROM (SELECT id, row_number() OVER "
        "(ORDER BY data_proposta NULLS LAST, id) n FROM propostas WHERE usuario_id = :u) r "
        "WHERE p.id = r.id"), {"u": usuario_id})


def renumerar(engine, usuario_id) -> int:
    """Aplica a numeração nova. Devolve quantas propostas mudaram de número."""
    if not indice_por_conta(engine):
        raise RuntimeError("O banco ainda está com o número único no banco todo; abra o site uma vez e tente de novo.")
    with engine.begin() as c:
        mudam = c.execute(text(
            "SELECT count(*) FROM (SELECT numero, row_number() OVER (ORDER BY data_proposta NULLS LAST, id) n "
            "FROM propostas WHERE usuario_id = :u) t WHERE numero <> n"), {"u": usuario_id}).scalar()
        renumerar_na_conexao(c, usuario_id)
    return int(mudam or 0)


# contas antigas renumeradas uma única vez, direto no banco (a dona da conta não mexe nisso)
CONTAS_A_RENUMERAR = {"renumerar_conta_tamara_2026_11": "tamarascavalcante@yahoo.com.br"}


def tarefas_unicas(engine):
    """Roda cada renumeração da lista uma vez só no banco todo: a primeira instância que gravar a marca em
    tarefas_unicas faz a troca na mesma transação; as outras encontram a marca e não fazem nada."""
    with engine.begin() as c:
        c.execute(text("CREATE TABLE IF NOT EXISTS tarefas_unicas (nome TEXT PRIMARY KEY, "
                       "feita_em TIMESTAMP DEFAULT now())"))
    for nome, email in CONTAS_A_RENUMERAR.items():
        with engine.begin() as c:
            if c.execute(text("INSERT INTO tarefas_unicas (nome) VALUES (:n) ON CONFLICT DO NOTHING RETURNING nome"),
                         {"n": nome}).first() is None:
                continue
            for (uid,) in c.execute(text("SELECT DISTINCT usuario_id FROM perfis WHERE lower(email) = :e "
                                         "AND usuario_id IS NOT NULL"), {"e": email}).all():
                renumerar_na_conexao(c, uid)
            print(f"[migração] {nome}: feito", flush=True)
