"""
Leitura dos retornos de pós-organização para as telas Pós-organização e Clientes do site.

Uma consulta só (ações + pós-organização + cliente + proposta), em vez de várias consultas por linha
como em Database.get_post_organizations / get_post_organization_actions. Usa uma conexão própria do
engine (como utils/funil.py): se a leitura falhar, a sessão do banco da tela não fica quebrada.

Regras iguais às do Início e da Agenda: só a conta logada e só serviço finalizado (proposta reaberta
não mostra retorno até ser finalizada de novo).
"""
import pandas as pd
from sqlalchemy import text

COLUNAS = ["action_id", "post_organization_id", "action_type", "due_date", "status", "notes", "completed_at",
           "cliente_id", "cliente_nome", "cliente_telefone", "proposta_id", "proposta_numero", "proposta_tipo",
           "proposta_descricao", "proposta_valor", "data_final_projeto"]

_SQL = text("""
SELECT a.id AS action_id, a.post_organization_id, a.action_type, a.due_date, a.status, a.notes, a.completed_at,
       po.cliente_id, c.nome AS cliente_nome, c.telefone AS cliente_telefone,
       po.proposta_id, p.numero AS proposta_numero, p.tipo_proposta AS proposta_tipo,
       p.descricao AS proposta_descricao, p.valor AS proposta_valor, po.data_final_projeto,
       p.status AS proposta_status
  FROM post_organization_actions a
  JOIN post_organizations po ON po.id = a.post_organization_id
  LEFT JOIN clientes c ON c.id = po.cliente_id
  LEFT JOIN propostas p ON p.id = po.proposta_id
 WHERE po.usuario_id = :u
 ORDER BY a.due_date, a.id
""")


def _engine():
    from utils.database import engine
    return engine


def acoes_pos(usuario_id, engine=None):
    """Todas as ações de pós-organização da conta (pendentes e enviadas), de serviços finalizados."""
    if not usuario_id:
        return pd.DataFrame(columns=COLUNAS)
    from utils.proposta_status import normalize, STATUS_FINALIZADA
    try:
        with (engine or _engine()).connect() as c:
            linhas = [dict(r._mapping) for r in c.execute(_SQL, {"u": usuario_id})]
    except Exception as e:
        print(f"[pos_dados] {usuario_id}: {e}")
        return pd.DataFrame(columns=COLUNAS)
    linhas = [r for r in linhas if normalize(r.get("proposta_status") or "") == STATUS_FINALIZADA]
    df = pd.DataFrame(linhas, columns=COLUNAS + ["proposta_status"])
    return df.drop(columns=["proposta_status"])


def pendentes(df):
    """Só as ações que ainda não foram enviadas (status PENDENTE)."""
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUNAS)
    return df[df["status"].astype(str).str.upper() == "PENDENTE"]


def salvar_nota(usuario_id, action_id, nota, engine=None):
    """Grava só a anotação de um retorno da conta (sem mudar a situação nem a data de envio)."""
    if not usuario_id:
        return False
    try:
        with (engine or _engine()).begin() as c:
            n = c.execute(text(
                "UPDATE post_organization_actions SET notes = :n WHERE id = :a AND post_organization_id IN "
                "(SELECT id FROM post_organizations WHERE usuario_id = :u)"),
                {"n": (nota or "").strip() or None, "a": int(action_id), "u": usuario_id}).rowcount
        return n > 0
    except Exception as e:
        print(f"[pos_dados] nota {action_id}: {e}")
        return False
