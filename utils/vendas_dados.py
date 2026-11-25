"""
Consultas de apoio da tela Vendas (pages/vendas.py), só leitura.

- parcelas_por_venda: quantas parcelas cada venda tem no Financeiro e quantas já foram recebidas
  (mesmos filtros de Database.get_vendas: origem 'venda', categoria Vendas, receitas Recebido/Pendente);
- itens_resumo: "12 Colmeia 30x30 + 4 Cesto" de cada venda;
- mais_vendidos: produtos com mais receita num conjunto de vendas;
- estoque_baixo: produtos com estoque até o mínimo de cada um (o que a organizer definiu no produto, ou 5).
"""
import pandas as pd

ESTOQUE_BAIXO = 5   # mínimo usado quando a organizer não definiu o estoque mínimo do produto


def _uid(db):
    return getattr(db, "usuario_id", None)


def parcelas_por_venda(db, ids):
    """{venda_id: (parcelas, recebidas)} das receitas da venda no Financeiro."""
    from utils.models import Transacao
    ids = [int(i) for i in ids]
    if not ids:
        return {}
    try:
        q = db.session.query(Transacao).filter(Transacao.origem_tipo == "venda", Transacao.origem_id.in_(ids))
        if _uid(db):
            q = q.filter(Transacao.usuario_id == _uid(db))
        cat = getattr(db, "CATEGORIA_VENDA", "Vendas")
        out = {}
        for t in q.all():
            if t.categoria != cat or not str(t.tipo).startswith("receita") or t.status not in ("Recebido", "Pendente"):
                continue
            n, r = out.get(t.origem_id, (0, 0))
            out[t.origem_id] = (n + 1, r + (t.status == "Recebido"))
        return out
    except Exception as e:
        print(f"[vendas_dados] parcelas: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return {}


def _itens(db, ids):
    from utils.models import ItemVenda, Produto
    q = (db.session.query(ItemVenda, Produto).join(Produto, ItemVenda.produto_id == Produto.id, isouter=True)
         .filter(ItemVenda.venda_id.in_([int(i) for i in ids])).order_by(ItemVenda.id))
    for iv, p in q.all():
        nome = (p.nome if p is not None and p.nome else None) or (iv.descricao or "").strip() or "Produto"
        custo = iv.custo_unitario if iv.custo_unitario is not None else (p.preco_custo if p is not None else None)
        yield iv, nome, custo


def itens_resumo(db, ids):
    """{venda_id: '12 Colmeia 30x30 + 4 Cesto de palha'} (até 3 produtos; o resto vira '+ N')."""
    if not len(ids):
        return {}
    try:
        por = {}
        for iv, nome, _ in _itens(db, ids):
            por.setdefault(iv.venda_id, []).append(f"{int(iv.quantidade or 0)} {nome}")
        return {v: " + ".join(l[:3]) + (f" + {len(l) - 3} itens" if len(l) > 3 else "") for v, l in por.items()}
    except Exception as e:
        print(f"[vendas_dados] itens: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return {}


def mais_vendidos(db, ids, n=3):
    """[(produto, receita, quantidade)] dos produtos que mais faturaram nessas vendas."""
    if not len(ids):
        return []
    try:
        tot = {}
        for iv, nome, _ in _itens(db, ids):
            r, q = tot.get(nome, (0.0, 0))
            tot[nome] = (r + float(iv.quantidade or 0) * float(iv.preco_unitario or 0), q + int(iv.quantidade or 0))
        return sorted(((k, r, q) for k, (r, q) in tot.items()), key=lambda x: -x[1])[:n]
    except Exception as e:
        print(f"[vendas_dados] mais vendidos: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return []


def estoque_baixo(produtos_df, limite=ESTOQUE_BAIXO):
    """Produtos com estoque até o mínimo de cada um (estoque_minimo do produto, ou `limite` se vazio),
    do menor para o maior. A coluna "minimo" diz qual mínimo valeu."""
    if produtos_df is None or produtos_df.empty or "estoque" not in produtos_df:
        return pd.DataFrame(columns=["id", "nome", "estoque", "minimo"])
    df = produtos_df.copy()
    df["estoque"] = pd.to_numeric(df["estoque"], errors="coerce").fillna(0).astype(int)
    minimo = pd.to_numeric(df["estoque_minimo"], errors="coerce") if "estoque_minimo" in df else pd.Series(index=df.index, dtype=float)
    df["minimo"] = minimo.fillna(limite).astype(int)
    return df[df["estoque"] <= df["minimo"]].sort_values(["estoque", "nome"])
