"""
Finalização segura de propostas com geração de lançamentos financeiros.
Chamado automaticamente pelo router quando status muda para 'finalizada'.
"""
import os
import psycopg2
from datetime import datetime, date, timedelta

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL não encontrada")
    return psycopg2.connect(db_url)

def _invalidar_cache_app(usuario_id):
    """Invalida o cache por sessão de get_propostas() (e afins) após a
    finalização gravada por ESTA conexão direta.

    Sem isso, a tela poderia continuar lendo o estado antigo em cache na mesma
    sessão até um rerun do Streamlit, fazendo a proposta finalizada "sumir"
    momentaneamente do filtro de finalizadas (#35)."""
    if not usuario_id:
        return
    try:
        from utils.database import remove_cache
        for key in ("cache_clientes", "cache_propostas", "cache_financeiro"):
            remove_cache(f"{key}_{usuario_id}")
    except Exception as e:
        print(f"[finalizar_v2] aviso: falha ao invalidar cache: {e}")

def finalizar_proposta_v2(proposta_id: int) -> dict:
    print(f"[finalizar_v2] iniciando proposta #{proposta_id}")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Buscar dados da proposta
        cur.execute("""
            SELECT p.id, p.numero, p.descricao, p.valor, p.status_execucao,
                   p.cliente_id, p.usuario_id, c.nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
        """, (proposta_id,))
        row = cur.fetchone()
        if not row:
            return {"status": False, "mensagem": "Proposta não encontrada"}

        pid, numero, descricao, valor, status_exec, cliente_id, usuario_id, nome_cliente = row

        # Marcar a proposta como finalizada (status canônico + campo de execução
        # usado pelo kanban). Feito sempre, mesmo que os lançamentos já existam,
        # para garantir que a proposta saia da coluna "Em Execução".
        cur.execute("""
            UPDATE propostas
            SET status = 'finalizada',
                status_execucao = 'Finalizada',
                data_fim = COALESCE(data_fim, CURRENT_DATE)
            WHERE id = %s
        """, (proposta_id,))
        print(f"[finalizar_v2] proposta #{numero} marcada como finalizada")

        # Verificar se lançamentos já foram gerados (evitar duplicidade)
        cur.execute(
            "SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s AND origem_tipo IN ('venda_produtos','servicos_adicionais','comissao_fornecedor','pagamento_assistente')",
            (proposta_id,)
        )
        if cur.fetchone()[0] > 0:
            conn.commit()
            _invalidar_cache_app(usuario_id)
            print(f"[finalizar_v2] proposta #{numero} já tem lançamentos, status finalizado")
            return {"status": True, "mensagem": "Lançamentos já existem"}

        lancamentos = 0

        # ── Produtos (produtos_organizadores) ────────────────────────────
        cur.execute("""
            SELECT nome, valor * quantidade AS total
            FROM produtos_organizadores
            WHERE proposta_id = %s
        """, (proposta_id,))
        produtos = cur.fetchall()
        valor_produtos = sum(float(r[1] or 0) for r in produtos)

        if valor_produtos > 0:
            cur.execute("""
                INSERT INTO financeiro
                (descricao, valor, data, categoria, subcategoria, tipo,
                 origem_id, origem_tipo, proposta_id, status, classificacao, usuario_id)
                VALUES (%s,%s,CURRENT_DATE,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                f"Venda de produtos — Proposta #{numero} — {nome_cliente}",
                valor_produtos, "Venda de Produtos", "Produtos", "Receita",
                proposta_id, "venda_produtos", proposta_id,
                "Pendente", "contas_a_receber", usuario_id
            ))
            lancamentos += 1
            print(f"[finalizar_v2] produtos R${valor_produtos:.2f}")

        # ── Acréscimos OUTROS ─────────────────────────────────────────────
        cur.execute("""
            SELECT descricao, valor FROM acrescimos_proposta
            WHERE proposta_id = %s AND tipo = 'OUTROS'
        """, (proposta_id,))
        outros = cur.fetchall()
        valor_outros = sum(float(r[1] or 0) for r in outros)

        if valor_outros > 0:
            cur.execute("""
                INSERT INTO financeiro
                (descricao, valor, data, categoria, subcategoria, tipo,
                 origem_id, origem_tipo, proposta_id, status, classificacao, usuario_id)
                VALUES (%s,%s,CURRENT_DATE,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                f"Serviços adicionais — Proposta #{numero} — {nome_cliente}",
                valor_outros, "Serviços adicionais", "Outros", "Receita",
                proposta_id, "servicos_adicionais", proposta_id,
                "Pendente", "contas_a_receber", usuario_id
            ))
            lancamentos += 1

        # ── Comissões de fornecedores (só se percentual > 0) ─────────────
        cur.execute("""
            SELECT a.fornecedor, a.valor,
                   COALESCE(f.percentual_comissao, 0) as pct
            FROM acrescimos_proposta a
            LEFT JOIN fornecedores f ON LOWER(a.fornecedor) = LOWER(f.descricao)
            WHERE a.proposta_id = %s AND a.tipo = 'FORNECEDOR'
        """, (proposta_id,))
        fornecedores = cur.fetchall()

        for forn_nome, forn_valor, pct in fornecedores:
            forn_valor = float(forn_valor or 0)
            pct = float(pct or 0)
            if forn_valor > 0 and pct > 0:
                comissao = forn_valor * pct / 100
                cur.execute("""
                    INSERT INTO financeiro
                    (descricao, valor, data, categoria, subcategoria, tipo,
                     origem_id, origem_tipo, proposta_id, status, classificacao, usuario_id)
                    VALUES (%s,%s,CURRENT_DATE,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    f"Comissão {pct}% — {forn_nome} — Proposta #{numero}",
                    comissao, "Comissão sobre fornecedores", "Comissão", "Receita",
                    proposta_id, "comissao_fornecedor", proposta_id,
                    "Pendente", "contas_a_receber", usuario_id
                ))
                lancamentos += 1

        # ── Assistentes (despesa) ─────────────────────────────────────────
        cur.execute("""
            SELECT fornecedor, valor FROM acrescimos_proposta
            WHERE proposta_id = %s AND tipo = 'ASSISTENTE'
        """, (proposta_id,))
        assistentes = cur.fetchall()

        for assist_nome, assist_valor in assistentes:
            assist_valor = float(assist_valor or 0)
            if assist_valor > 0:
                cur.execute("""
                    INSERT INTO financeiro
                    (descricao, valor, data, categoria, subcategoria, tipo,
                     origem_id, origem_tipo, proposta_id, status, classificacao, usuario_id)
                    VALUES (%s,%s,CURRENT_DATE,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    f"Assistente: {assist_nome} — Proposta #{numero}",
                    assist_valor, "Pagamento Equipe/Assistentes", "Assistentes", "Despesa",
                    proposta_id, "pagamento_assistente", proposta_id,
                    "Pendente", "contas_a_pagar", usuario_id
                ))
                lancamentos += 1

        # ── Pós-organização ───────────────────────────────────────────────
        cur.execute("""
            SELECT id FROM post_organizations
            WHERE proposta_id = %s AND usuario_id = %s
        """, (proposta_id, usuario_id))

        if not cur.fetchone():
            hoje = date.today()
            cur.execute("""
                INSERT INTO post_organizations
                (proposta_id, cliente_id, data_final_projeto, status, usuario_id)
                VALUES (%s,%s,%s,'ATIVO',%s) RETURNING id
            """, (proposta_id, cliente_id, hoje, usuario_id))
            pos_id = cur.fetchone()[0]

            acoes = [
                ('agradecimento',  hoje + timedelta(days=1)),
                ('acompanhamento', hoje + timedelta(days=7)),
                ('ajuste_fino',    hoje + timedelta(days=30)),
                ('feedback',       hoje + timedelta(days=45)),
                ('continuidade',   hoje + timedelta(days=60)),
            ]
            for action_type, due_date in acoes:
                cur.execute("""
                    INSERT INTO post_organization_actions
                    (post_organization_id, action_type, due_date, status, usuario_id)
                    VALUES (%s,%s,%s,'PENDENTE',%s)
                """, (pos_id, action_type, due_date, usuario_id))

            print(f"[finalizar_v2] pós-organização criada id={pos_id}")

        conn.commit()
        _invalidar_cache_app(usuario_id)
        print(f"[finalizar_v2] concluído — {lancamentos} lançamentos gerados")
        return {"status": True, "lancamentos": lancamentos}

    except Exception as e:
        conn.rollback()
        print(f"[finalizar_v2] ERRO: {e}")
        raise
    finally:
        cur.close()
        conn.close()
