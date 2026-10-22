"""
Precificação: quanto vale a hora da organizer e quanto cobrar por um projeto.

Os cálculos ficam em utils/precificacao.py (com testes); aqui só os campos e o resultado.
Os números da organizer são guardados no perfil (Database.salvar_precificacao).
"""
import math

import pandas as pd
import streamlit as st

from utils import precificacao as pr
from utils.currency_formatter import fmt_brl
from utils.ui import input_moeda

CSS = """
<style>
.pc-intro { color: #667085; font-size: .92rem; margin: -6px 0 14px; }
.pc-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 6px 0 14px; }
.pc-kpi { background: #fff; border: 1px solid #E4E7EC; border-radius: 12px; padding: 14px 16px; }
.pc-kpi .rot { font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; }
.pc-kpi .val { font-size: 1.5rem; font-weight: 700; color: #101828; margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.pc-kpi .sub { font-size: .8rem; color: #667085; display: block; }
.pc-kpi.destaque { background: var(--navy); border-color: var(--navy); border-top: 3px solid var(--gold); }
.pc-kpi.destaque .rot { color: var(--gold); }
.pc-kpi.destaque .val { color: #fff; }
.pc-kpi.destaque .sub { color: #C8D1DC; }
.pc-nota { background: #FBF5E6; border: 1px solid #E3CF97; color: #5C4712; border-radius: 10px; padding: 10px 14px; font-size: .88rem; }
.pc-lin { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid #F2F4F7; font-size: .9rem; }
.pc-lin span { color: #475467; } .pc-lin b { font-variant-numeric: tabular-nums; }
@media (max-width: 900px) { .pc-kpis { grid-template-columns: 1fr; } }
</style>
"""


def _kpi(rot, val, sub, destaque=False):
    return (f'<div class="pc-kpi{" destaque" if destaque else ""}"><span class="rot">{rot}</span>'
            f'<div class="val">{val}</div><span class="sub">{sub}</span></div>')


def _parametros():
    """Números salvos da organizer (ou os padrões), carregados uma vez por sessão."""
    if "_pc_param" not in st.session_state:
        salvos = {}
        try:
            salvos = st.session_state.db.get_precificacao() or {}
        except Exception as e:
            print(f"[precificacao] {e}")
        st.session_state["_pc_param"] = {**pr.PADROES, **salvos}
    return st.session_state["_pc_param"]


def _aba_hora(p):
    st.markdown("Comece pelo mês: quanto você quer ganhar, quanto gasta para trabalhar e quantas horas consegue "
                "atender. Tempo de orçamento, compras e deslocamento não conta como hora vendida.")
    c1, c2 = st.columns(2)
    with c1:
        p["renda_desejada"] = input_moeda("Quanto você quer ganhar por mês (R$)", "pc_renda", p["renda_desejada"])
        p["dias_mes"] = st.number_input("Dias de atendimento no mês", 1, 31, int(p["dias_mes"]), key="pc_dias")
        p["horas_dia"] = st.number_input("Horas de trabalho por dia de atendimento", 1.0, 14.0,
                                         float(p["horas_dia"]), 0.5, key="pc_horas_dia")
        p["margem_pct"] = st.number_input("Margem de lucro (%)", 0.0, 200.0, float(p["margem_pct"]), 5.0, key="pc_margem",
                                          help="Sobra para reinvestir, imprevistos e meses mais fracos.")
    with c2:
        p["custo_impostos_fixos"] = input_moeda("Impostos fixos do mês, como o DAS do MEI (R$)", "pc_das",
                                                p["custo_impostos_fixos"], step=10.0)
        p["custo_transporte"] = input_moeda("Transporte (R$/mês)", "pc_transp", p["custo_transporte"], step=50.0)
        p["custo_ferramentas"] = input_moeda("Ferramentas, celular, marketing e cursos (R$/mês)", "pc_ferr",
                                             p["custo_ferramentas"], step=50.0)
        p["custo_outros"] = input_moeda("Outros custos do mês (R$)", "pc_outros", p["custo_outros"], step=50.0)
        p["imposto_pct"] = st.number_input("Imposto sobre cada venda (%)", 0.0, 30.0, float(p["imposto_pct"]), 0.5,
                                           key="pc_imp", help="MEI: 0 (o DAS já está nos custos fixos). Simples Nacional: a sua alíquota.")

    st.markdown('<div class="pc-kpis">'
                + _kpi("Hora sugerida", fmt_brl(pr.hora_sugerida(p)), f"com {p['margem_pct']:.0f}% de margem", True)
                + _kpi("Hora mínima", fmt_brl(pr.hora_minima(p)), "abaixo disso a conta do mês não fecha")
                + _kpi("Horas que você vende", f"{pr.horas_vendidas(p):.0f} h/mês",
                       f"custos fixos de {fmt_brl(pr.custos_fixos(p))}")
                + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="pc-nota">Referência: guias de preço de 2026 apontam de R$ 80 a R$ 350 por hora no Brasil, '
                'conforme cidade e experiência. Use a sua conta, não a média: ela mostra o que o seu negócio precisa.</div>',
                unsafe_allow_html=True)
    st.markdown("")
    if st.button("Salvar meus números", type="primary", key="pc_salvar"):
        if st.session_state.db.salvar_precificacao({k: p[k] for k in pr.PADROES}):
            st.success("Números salvos. Eles valem para o cálculo de projetos.")
        else:
            st.error("Não consegui salvar agora. Tente de novo.")


def _aba_projeto(p):
    st.markdown("Marque os ambientes do projeto e ajuste as horas pela sua experiência. "
                "As horas iniciais são só um ponto de partida.")
    base = pd.DataFrame([{"Ambiente": a, "Quantidade": 0, "Horas cada": h} for a, h in pr.AMBIENTES_PADRAO.items()])
    tabela = st.data_editor(
        base, key="pc_ambientes", hide_index=True, use_container_width=True, num_rows="dynamic",
        column_config={
            "Ambiente": st.column_config.TextColumn(required=True),
            "Quantidade": st.column_config.NumberColumn(min_value=0, step=1),
            "Horas cada": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.1f h"),
        })
    tabela = tabela.fillna({"Quantidade": 0, "Horas cada": 0})
    escolhidos = tabela[tabela["Quantidade"] > 0]
    horas_ambientes = float((escolhidos["Quantidade"] * escolhidos["Horas cada"]).sum())

    c1, c2, c3 = st.columns(3)
    with c1:
        nivel = st.radio("Complexidade", list(pr.COMPLEXIDADE), index=1, key="pc_compl", horizontal=False)
        assistentes = st.number_input("Assistentes no projeto", 0, 10, 0, key="pc_assist")
    with c2:
        p["valor_hora_assistente"] = input_moeda("Valor da hora de cada assistente (R$)", "pc_v_assist",
                                                 p["valor_hora_assistente"], step=5.0)
        deslocamento = input_moeda("Deslocamento e estacionamento (R$)", "pc_desloc", 0.0, step=10.0)
    with c3:
        outros = input_moeda("Outros custos do projeto (R$)", "pc_outros_proj", 0.0, step=10.0,
                             help="Etiquetas, materiais de consumo. Produtos para a cliente ficam em Vendas.")
        sinal_pct = st.number_input("Sinal na aprovação (%)", 0, 100, 50, 5, key="pc_sinal")

    if horas_ambientes <= 0:
        st.info("Informe a quantidade de pelo menos um ambiente para ver o preço.")
        return
    r = pr.preco_projeto(p, horas_ambientes, pr.COMPLEXIDADE[nivel], assistentes, deslocamento, outros)
    arredondado = math.ceil(r["preco_sugerido"] / 10) * 10
    st.markdown('<div class="pc-kpis">'
                + _kpi("Preço sugerido", fmt_brl(arredondado), f"sinal de {fmt_brl(arredondado * sinal_pct / 100)} "
                       f"({sinal_pct}%)", True)
                + _kpi("Preço mínimo", fmt_brl(r["preco_minimo"]), "cobre sua hora mínima e os custos, sem margem")
                + _kpi("Fica para você", fmt_brl(r["lucro"]),
                       f"{fmt_brl(r['hora_efetiva'])} por hora sua no local")
                + '</div>', unsafe_allow_html=True)
    linhas = [("Horas de trabalho (com a complexidade)", f"{r['horas_trabalho']:.1f} h"),
              ("Equipe", f"{r['pessoas']} pessoa(s) · {r['suas_horas']:.1f} h suas no local"),
              ("Dias de atendimento", f"{r['dias_no_local']:.1f} dia(s) de {p['horas_dia']:.0f} h"),
              ("Custo das assistentes", fmt_brl(r["custo_equipe"])),
              ("Custos do projeto (equipe, deslocamento, outros)", fmt_brl(r["custos_diretos"])),
              ("Imposto sobre a venda", fmt_brl(r["imposto"]))]
    st.markdown("".join(f'<div class="pc-lin"><span>{a}</span><b>{b}</b></div>' for a, b in linhas),
                unsafe_allow_html=True)
    st.markdown("")



def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Precificação</h1>', unsafe_allow_html=True)
    st.markdown('<div class="pc-intro">Quanto vale a sua hora e quanto cobrar por cada projeto, com os seus números.</div>',
                unsafe_allow_html=True)
    p = _parametros()
    aba_hora, aba_projeto = st.tabs([":material/schedule: Sua hora", ":material/home_work: Preço de um projeto"])
    with aba_hora:
        _aba_hora(p)
    with aba_projeto:
        _aba_projeto(p)
