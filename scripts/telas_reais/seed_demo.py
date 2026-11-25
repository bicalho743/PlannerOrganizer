"""
Conta de demonstração para gerar as telas reais (landing, lojas, redes sociais).

Cria (ou recria do zero) a conta `demo_landing` com dados de exemplo de uma personal organizer:
clientes, propostas em todas as situações, agenda do mês, retornos de pós-organização,
financeiro do mês e produtos. As datas acompanham o dia em que o script roda.

Uso (banco de TESTE, nunca o de produção):
  DATABASE_URL=postgresql://postgres@127.0.0.1:5499/sinal_teste python scripts/telas_reais/seed_demo.py
"""
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

if "render.com" in os.environ.get("DATABASE_URL", "") or "dpg-" in os.environ.get("DATABASE_URL", ""):
    sys.exit("Este script só roda no banco de teste.")

from sqlalchemy import text  # noqa: E402

from utils.database import Database, engine  # noqa: E402
from utils.visual import hoje  # noqa: E402

UID = "demo_landing"
H = hoje()
d = lambda n: H + timedelta(days=n)  # noqa: E731


def limpar():
    passos = [
        "DELETE FROM post_organization_actions WHERE post_organization_id IN (SELECT id FROM post_organizations WHERE usuario_id = :u)",
        "DELETE FROM post_organizations WHERE usuario_id = :u",
        "DELETE FROM financeiro WHERE usuario_id = :u",
        "DELETE FROM compromissos WHERE usuario_id = :u",
        "DELETE FROM itens_venda WHERE venda_id IN (SELECT id FROM vendas WHERE usuario_id = :u)",
        "DELETE FROM vendas WHERE usuario_id = :u",
        "DELETE FROM andamento_propostas WHERE proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
        "DELETE FROM produtos_organizadores WHERE proposta_id IN (SELECT id FROM propostas WHERE usuario_id = :u)",
        "DELETE FROM propostas WHERE usuario_id = :u",
        "DELETE FROM produtos WHERE usuario_id = :u",
        "DELETE FROM clientes WHERE usuario_id = :u",
        "DELETE FROM perfis WHERE usuario_id = :u",
    ]
    for sql in passos:
        try:
            with engine.begin() as c:
                c.execute(text(sql), {"u": UID})
        except Exception as e:  # tabela que não existe nesta versão do banco
            print("  (pulado)", sql.split(" WHERE")[0], "-", str(e).splitlines()[0][:80])


def main():
    limpar()
    db = Database(usuario_id=UID)
    db.create_perfil(UID, "ana@exemplo.com.br", "Ana Ribeiro", telefone="(11) 99876-5432",
                     empresa="Ana Ribeiro Organização", instagram="anaribeiro.organiza", cor_principal="#B8943D")
    db.salvar_regime("mei")

    mes = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    clientes = {}
    for nome, tel, bairro, origem, niver in [
        ("Clara Mendes", "11987654321", "Pinheiros", "Instagram", None),
        ("Mariana Lopes", "11954321098", "Perdizes", "Indicação", f"{H.day:02d}/{mes[H.month - 1]}"),
        ("Fernanda Rocha", "11987654300", "Moema", "Instagram", None),
        ("Paula Nunes", "11976543210", "Vila Madalena", "Google", None),
        ("Beatriz Faria", "11943210987", "Itaim Bibi", "Indicação", None),
        ("Luana Prado", "11932109876", "Santana", "Instagram", None),
        ("Renata Dias", "11909876543", "Mooca", "Google", None),
        ("Juliana Ferraz", "11998761234", "Pinheiros", "Instagram", None),
    ]:
        clientes[nome] = db.add_cliente(nome=nome, telefone=tel, bairro=bairro, cidade="São Paulo", estado="SP",
                                        origem_cliente=origem, data_aniversario=niver)

    def prop(cli, tipo, desc, valor, status, criada, inicio=None, fim=None, dias=None, sinal=0):
        pid = db.add_proposta(clientes[cli], desc, valor, status, tipo, data_inicio=inicio, data_fim=fim,
                              previsao_dias=dias, gerar_transacoes_automaticas=False)
        db.update_proposta(pid, data_proposta=criada, **({"sinal": sinal} if sinal else {}))
        return pid

    prop("Fernanda Rocha", "Organização", "Organização de Closet / guarda-roupa (2).", 1850, "em_aberto", d(-4))
    prop("Juliana Ferraz", "Pré-mudança", "Pré-mudança: embalagem e inventário (34 caixas).", 2480, "em_aberto", d(-1))
    prop("Mariana Lopes", "Organização", "Organização de Cozinha, Despensa.", 2400, "aprovada", d(-6), inicio=d(3), dias=1, sinal=1200)
    p_clara = prop("Clara Mendes", "Pós-mudança", "Pós-mudança: desembalagem e organização (40 caixas).", 6900,
                   "em_execucao", d(-12), inicio=H, fim=d(1), dias=2, sinal=3450)
    for cli, tipo, desc, valor, dias_atras in [("Beatriz Faria", "Organização", "Organização de Quarto infantil.", 980, 30),
                                               ("Luana Prado", "Organização", "Organização de Closet / guarda-roupa.", 1400, 7),
                                               ("Renata Dias", "Organização", "Organização de Cozinha, Área de serviço.", 1650, 2)]:
        pid = prop(cli, tipo, desc, valor, "finalizada", d(-dias_atras - 10), inicio=d(-dias_atras), fim=d(-dias_atras), dias=1)
        db.create_post_organization(pid, clientes[cli], d(-dias_atras))

    db.salvar_compromisso(None, data=H, titulo="Visita técnica", hora="16:00", cliente_id=clientes["Paula Nunes"],
                          local="", valor=0, observacoes="Lavanderia")
    db.salvar_compromisso(None, data=d(2), titulo="Visita de orçamento", hora="10:00", cliente_id=clientes["Juliana Ferraz"],
                          local="", valor=150, observacoes="")

    def lanc(tipo, desc, valor, cat, quando, pago, classif):
        tid = db.add_transacao(tipo=tipo, descricao=desc, valor=valor, categoria=cat, classificacao=classif,
                               proposta_id=p_clara if "Clara" in desc else None)
        if pago and tid:
            db.atualizar_status_transacao(int(tid), "Recebido" if tipo == "receita" else "Pago", quando)
        if tid:
            with engine.begin() as c:
                c.execute(text("UPDATE financeiro SET data = :d WHERE id = :i"), {"d": quando, "i": int(tid)})

    lanc("receita", "Sinal · Clara Mendes", 3450, "Serviços de Organização", d(-12), True, "contas_a_receber")
    lanc("receita", "Saldo · Clara Mendes", 3450, "Serviços de Organização", d(1), False, "contas_a_receber")
    lanc("receita", "Sinal · Mariana Lopes", 1200, "Serviços de Organização", d(-5), True, "contas_a_receber")
    lanc("receita", "Luana Prado · closet", 1400, "Serviços de Organização", d(-7), True, "contas_a_receber")
    lanc("despesa", "Assistente Júlia", 360, "Pagamento Equipe/Assistentes", d(-7), True, "contas_a_pagar")
    lanc("despesa", "Caixas e fitas", 180, "Custos Operacionais", d(-9), True, "contas_a_pagar")
    lanc("despesa", "DAS do MEI", 86.05, "Impostos (DAS)", d(5), False, "contas_a_pagar")

    for nome, custo, venda, est, minimo in [("Colmeia 30x30", 18, 30, 2, 6), ("Cabide de veludo", 4.5, 9, 40, 20),
                                            ("Cesto de palha", 35, 70, 3, 4), ("Caixa organizadora", 22, 42, 12, None)]:
        db.add_produto(nome=nome, preco_custo=custo, preco_venda=venda, estoque=est, estoque_minimo=minimo,
                       categoria="Organização")
    print("Conta demo_landing pronta:", len(clientes), "clientes.")


if __name__ == "__main__":
    main()
