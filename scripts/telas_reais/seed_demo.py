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


def _logo_demo():
    """Monograma "AR" dourado sobre creme, em data URL (como o Perfil grava o logotipo)."""
    import base64
    import io
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (240, 240), "#F6EDD3")
    dr = ImageDraw.Draw(img)
    dr.ellipse((14, 14, 226, 226), outline="#B8943D", width=6)
    fonte = None
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"):
        if os.path.exists(f):
            fonte = ImageFont.truetype(f, 92)
            break
    dr.text((120, 122), "AR", fill="#8A6A1C", font=fonte or ImageFont.load_default(), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


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
    # retornos que já passaram foram feitos (uma conta real não fica com mensagens atrasadas há semanas)
    with engine.begin() as c:
        c.execute(text("UPDATE post_organization_actions SET status = 'FEITO', completed_at = due_date "
                       "WHERE usuario_id = :u AND due_date < :lim"), {"u": UID, "lim": d(-1)})
    # logotipo (monograma) e cor da marca: as telas e os PDFs saem como os de uma organizer que já configurou tudo
    with engine.begin() as c:
        c.execute(text("UPDATE perfis SET logo = :l WHERE usuario_id = :u"), {"l": _logo_demo(), "u": UID})

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
    # DAS dos meses anteriores pagos em dia (senão o Financeiro mostra guias "vencidas" desde o começo do ano)
    from datetime import date as _date
    for ano, mes in [(H.year - 1, 12)] + [(H.year, m) for m in range(1, H.month)]:
        venc = _date(ano + (mes == 12), mes % 12 + 1, 20)
        if venc < H:
            lanc("despesa", f"DAS do MEI · competência {mes:02d}/{ano}", 86.05, "Impostos (DAS)", venc, True, "contas_a_pagar")

    prods = {}
    for nome, custo, venda, est, minimo in [("Colmeia 30x30", 18, 30, 14, 6), ("Cabide de veludo", 4.5, 9, 60, 20),
                                            ("Cesto de palha", 35, 70, 3, 4), ("Caixa organizadora", 22, 42, 12, None)]:
        prods[nome] = db.add_produto(nome=nome, preco_custo=custo, preco_venda=venda, estoque=est, estoque_minimo=minimo,
                                     categoria="Organização")
    # vendas de produtos junto com os serviços (a tela de Vendas não fica vazia)
    for cli, itens, quando, recebido in [
            ("Clara Mendes", [("Colmeia 30x30", 6), ("Caixa organizadora", 3)], d(-11), True),
            ("Luana Prado", [("Cabide de veludo", 30)], d(-7), True),
            ("Mariana Lopes", [("Cesto de palha", 2), ("Colmeia 30x30", 4)], d(-2), False)]:
        try:
            db.add_venda(clientes[cli], [{"produto_id": prods[n], "quantidade": q} for n, q in itens],
                         forma_pagamento="Pix", data_venda=quando, recebido=recebido,
                         **({} if recebido else {"parcelas": 1, "primeiro_vencimento": d(5)}))
        except Exception as e:
            print("  venda não criada:", e)
    print("Conta demo_landing pronta:", len(clientes), "clientes.")


if __name__ == "__main__":
    main()
