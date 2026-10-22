import streamlit as st
import pandas as pd
import plotly.express as px
import html as html_module
from datetime import date, datetime, timedelta
from utils.currency_formatter import fmt_brl
from utils.ui import botao_excluir, botao_editar, input_moeda, cartao_clicavel
from utils.indicadores import (movimentos, entrou_gastou, retirado, previsto, por_categoria, mei, cor_categoria,
                               realizados_no_mes, das_do_ano, faturamento_ano, prazo_dasn,
                               CATEGORIA_IMPOSTO, CATEGORIA_RETIRADA, DAS_MEI, LIMITE_MEI)

LINK_PGMEI = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao"
LINK_DASN = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Identificacao"


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
MES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

CSS_PAINEL = """
<style>
.fp-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 4px 0 12px; }
.fp-kpi { background: #fff; border: 1px solid #E4E7EC; border-radius: 12px; padding: 14px 16px; }
.fp-kpi .rot { font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; }
.fp-kpi .val { font-size: 1.4rem; font-weight: 700; color: #101828; margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.fp-kpi .sub { font-size: .8rem; color: #667085; line-height: 1.4; display: block; }
.fp-kpi.entra .val { color: #067647; }
.fp-kpi.sai .val { color: #B42318; }
.fp-kpi.destaque { background: var(--navy); border-color: var(--navy); }
.fp-kpi.destaque .rot, .fp-kpi.destaque .sub { color: #C8D1DC; }
.fp-kpi.destaque .val { color: #fff; }
.fp-prev { background: #F8F9FB; border: 1px solid #E4E7EC; border-radius: 10px; padding: 10px 14px; font-size: .88rem; color: #344054; margin-bottom: 14px; }
.fp-prev b { font-variant-numeric: tabular-nums; }
.fp-alerta { background: #FFFAEB; border: 1px solid #FEC84B; border-radius: 10px; padding: 10px 14px; font-size: .88rem; color: #93370D; margin-bottom: 14px; }
.fp-secao { font-size: .78rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; margin: 2px 0 8px; }
.fp-cat { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 5px 0; font-size: .86rem; }
.fp-cat .nm { display: flex; align-items: center; gap: 8px; color: #344054; min-width: 0; }
.fp-cat .nm span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fp-dot { flex: none; width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.fp-cat .bar { height: 8px; background: #F2F4F7; border-radius: 999px; overflow: hidden; }
.fp-cat .bar i { display: block; height: 100%; border-radius: 999px; }
.fp-cat b { font-variant-numeric: tabular-nums; white-space: nowrap; }
.fp-vazio { color: #98A2B3; font-size: .86rem; }
.fp-mei .lin { display: flex; justify-content: space-between; gap: 10px; font-size: .88rem; color: #344054; }
.fp-mei .trilho { height: 12px; background: #F2F4F7; border-radius: 999px; overflow: hidden; margin: 8px 0 6px; position: relative; }
.fp-mei .trilho i { display: block; height: 100%; border-radius: 999px; }
.fp-mei .det { font-size: .8rem; color: #667085; line-height: 1.5; }
.fp-mei .ok { color: #067647; font-weight: 600; }
.fp-mei .pend { color: #B54708; font-weight: 600; }
.fp-das { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; margin: 4px 0 10px; }
.fp-das div { border: 1px solid #E4E7EC; border-radius: 10px; padding: 8px 10px; background: #fff; }
.fp-das b { display: block; font-size: .9rem; color: #101828; text-transform: capitalize; }
.fp-das span { font-size: .74rem; color: #667085; display: block; line-height: 1.35; }
.fp-das .pago { background: #ECFDF3; border-color: #ABEFC6; } .fp-das .pago span { color: #067647; }
.fp-das .atrasado { background: #FEF3F2; border-color: #FECDCA; } .fp-das .atrasado span { color: #B42318; font-weight: 600; }
.fp-das .avencer { background: #FFFAEB; border-color: #FEDF89; } .fp-das .avencer span { color: #B54708; font-weight: 600; }
.fp-das .futuro { background: #F9FAFB; } .fp-das .futuro b { color: #98A2B3; }
@media (max-width: 900px) { .fp-das { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 900px) { .fp-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
"""


def _kpi(rotulo, valor, sub, cls=""):
    return (f'<div class="fp-kpi {cls}"><span class="rot">{rotulo}</span>'
            f'<div class="val">{valor}</div><span class="sub">{sub}</span></div>')


def _barras_categoria(itens):
    if not itens:
        return '<div class="fp-vazio">Nada neste mês.</div>'
    topo = itens[0][1] or 1
    html = ""
    for nome, valor in itens[:7]:
        cor = cor_categoria(nome)
        nome_h = html_module.escape(str(nome))
        html += (f'<div class="fp-cat"><span class="nm"><i class="fp-dot" style="background:{cor}"></i>'
                 f'<span title="{nome_h}">{nome_h}</span></span>'
                 f'<span class="bar"><i style="width:{valor / topo * 100:.0f}%;background:{cor}"></i></span>'
                 f'<b>{fmt_brl(valor)}</b></div>')
    return html


def _painel_mes(financeiro_df):
    """Entrou, gastou, sobrou e retiradas do mês escolhido; previsão; categorias; limite do MEI."""
    hoje = datetime.now().date()
    opcoes = []
    a, m = hoje.year, hoje.month
    for _ in range(12):
        opcoes.append((a, m))
        a, m = (a - 1, 12) if m == 1 else (a, m - 1)
    col_mes, _ = st.columns([1, 3])
    ano, mes = col_mes.selectbox("Mês", opcoes, format_func=lambda am: f"{MESES[am[1] - 1].capitalize()} de {am[0]}",
                            key="fin_mes_painel", label_visibility="collapsed")
    mov = movimentos(financeiro_df.assign(data=financeiro_df["data"].dt.date) if not financeiro_df.empty else financeiro_df)
    entrou, gastou = entrou_gastou(mov, ano, mes)
    sobrou = entrou - gastou
    retirou = retirado(mov, ano, mes)
    st.markdown(CSS_PAINEL + '<div class="fp-kpis">' +
                _kpi("Entrou", fmt_brl(entrou), "recebido no mês", "entra") +
                _kpi("Gastou", fmt_brl(gastou), "despesas pagas da empresa", "sai") +
                _kpi("Sobrou", fmt_brl(sobrou), "lucro do mês (entrou − gastou)", "destaque") +
                _kpi("Retirado para você", fmt_brl(retirou),
                     f"ficou no caixa da empresa: {fmt_brl(sobrou - retirou)}" if retirou
                     else f"lance como “{CATEGORIA_RETIRADA}”") +
                '</div>', unsafe_allow_html=True)

    if (ano, mes) == (hoje.year, hoje.month):
        a_entrar, a_sair = previsto(mov, ano, mes)
        if a_entrar or a_sair:
            st.markdown(f'<div class="fp-prev">Previsão até o fim de {MESES[mes - 1]}: ainda entram <b>{fmt_brl(a_entrar)}</b> '
                        f'e saem <b>{fmt_brl(a_sair)}</b>. Se tudo se confirmar, o mês fecha com '
                        f'<b>{fmt_brl(sobrou + a_entrar - a_sair)}</b>.</div>', unsafe_allow_html=True)
    if retirou > sobrou > -1 and retirou:
        st.markdown(f'<div class="fp-alerta">Você retirou {fmt_brl(retirou - sobrou)} a mais do que a empresa lucrou em '
                    f'{MESES[mes - 1]}. Separe o dinheiro da empresa do pessoal para o caixa não ficar no vermelho.</div>',
                    unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1], gap="medium")
    with c1:
        st.markdown('<div class="fp-secao">De onde veio</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(_barras_categoria(por_categoria(mov, ano, mes, "entra")), unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="fp-secao">Para onde foi</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(_barras_categoria(por_categoria(mov, ano, mes, "sai")), unsafe_allow_html=True)
    with c3:
        info = mei(mov, hoje)
        st.markdown(f'<div class="fp-secao">Limite do MEI · {info["ano"]}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            uso = info["uso"]
            cor = "#067647" if uso < 0.7 else ("#DC6803" if uso < 0.9 else "#D92D20")
            proj = info["projecao"]
            aviso = (f'No ritmo atual o ano fecha em <b>{fmt_brl(proj)}</b>, acima do limite: converse com sua contadora.'
                     if proj > info["limite"] else f'No ritmo atual o ano fecha em {fmt_brl(proj)}.')
            ant = date(hoje.year, hoje.month, 1) - timedelta(days=1)
            situ = das_do_ano(mov, ant.year, hoje)[ant.month - 1]
            das = (f'<span class="ok">DAS de {MES_ABREV[ant.month - 1]} pago</span>' if situ["situacao"] == "pago"
                   else f'<span class="pend">DAS de {MES_ABREV[ant.month - 1]} '
                        f'{"atrasado" if situ["situacao"] == "atrasado" else "vence dia 20"}</span>')
            st.markdown(f'<div class="fp-mei"><div class="lin"><span>Faturado</span>'
                        f'<b>{fmt_brl(info["faturado"])} de {fmt_brl(info["limite"])}</b></div>'
                        f'<div class="trilho"><i style="width:{min(uso, 1) * 100:.0f}%;background:{cor}"></i></div>'
                        f'<div class="det">{uso:.0%} do limite usado. {aviso}<br>{das} · detalhes na aba MEI.</div></div>',
                        unsafe_allow_html=True)


def _aba_mei(financeiro_df):
    """Aba MEI: limite do ano com projeção, DAS de cada mês e a declaração anual (DASN-SIMEI)."""
    hoje = datetime.now().date()
    mov = movimentos(financeiro_df.assign(data=financeiro_df["data"].dt.date) if not financeiro_df.empty else financeiro_df)
    col_ano, _ = st.columns([1, 3])
    ano = col_ano.selectbox("Ano", [hoje.year, hoje.year - 1], key="fin_mei_ano", label_visibility="collapsed")

    fat = faturamento_ano(mov, ano)
    uso = fat["total"] / LIMITE_MEI
    if ano == hoje.year:
        dia = hoje.timetuple().tm_yday
        proj = fat["total"] / dia * (366 if ano % 4 == 0 else 365) if fat["total"] else 0.0
    else:
        proj = fat["total"]
    das = das_do_ano(mov, ano, hoje)
    devidos = [m for m in das if m["situacao"] != "futuro"]
    pagos = sum(m["situacao"] == "pago" for m in devidos)
    atrasados = [m for m in devidos if m["situacao"] == "atrasado"]
    ano_decl, limite_decl, faltam = prazo_dasn(hoje)

    st.markdown(CSS_PAINEL + '<div class="fp-kpis">' +
                _kpi(f"Faturado em {ano}", fmt_brl(fat["total"]), f"{uso:.0%} do limite de {fmt_brl(LIMITE_MEI)}",
                     "destaque") +
                _kpi("Projeção do ano" if ano == hoje.year else "Fechou o ano", fmt_brl(proj),
                     "acima do limite: fale com sua contadora" if proj > LIMITE_MEI
                     else f"sobram {fmt_brl(LIMITE_MEI - proj)} até o limite") +
                _kpi("DAS pagos", f"{pagos} de {len(devidos)}",
                     f"{len(atrasados)} em atraso" if atrasados else "nenhum em atraso",
                     "sai" if atrasados else "entra") +
                _kpi("Declaração anual", limite_decl.strftime("%d/%m/%Y"),
                     f"DASN-SIMEI de {ano_decl} · faltam {faltam} dias") +
                '</div>', unsafe_allow_html=True)

    cor = "#067647" if uso < 0.7 else ("#DC6803" if uso < 0.9 else "#D92D20")
    st.markdown(f'<div class="fp-mei" style="margin-bottom:14px"><div class="trilho">'
                f'<i style="width:{min(uso, 1) * 100:.0f}%;background:{cor}"></i></div>'
                f'<div class="det">Conta só o que já foi recebido. Se o MEI foi aberto em {ano}, o limite é de '
                f'{fmt_brl(LIMITE_MEI / 12)} por mês de atividade. Passar até 20% do limite: paga a diferença e vira '
                f'microempresa no ano seguinte; acima disso, o desenquadramento volta ao início do ano.</div></div>',
                unsafe_allow_html=True)

    st.markdown(f'<div class="fp-secao">DAS mês a mês · {ano}</div>', unsafe_allow_html=True)
    classe = {"pago": "pago", "atrasado": "atrasado", "a vencer": "avencer", "futuro": "futuro"}
    cards = ""
    for m in das:
        if m["situacao"] == "pago":
            txt = f"pago em {m['pago_em'].strftime('%d/%m')}"
        elif m["situacao"] == "futuro":
            txt = f"vence {m['vencimento'].strftime('%d/%m')}"
        else:
            txt = f"{m['situacao']} · {m['vencimento'].strftime('%d/%m')}"
        cards += f'<div class="{classe[m["situacao"]]}"><b>{MESES[m["mes"] - 1]}</b><span>{txt}</span></div>'
    st.markdown(f'<div class="fp-das">{cards}</div>', unsafe_allow_html=True)
    st.caption(f"O DAS de cada mês vence no dia 20 do mês seguinte. Em 2026 o valor para serviços é "
               f"{fmt_brl(DAS_MEI)}. Pagou por fora? Lance aqui ou como “{CATEGORIA_IMPOSTO}” no Financeiro.")

    em_aberto = [m for m in devidos if m["situacao"] != "pago"]
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        if em_aberto:
            with st.form("fin_form_das", clear_on_submit=True):
                st.markdown("**Lançar DAS pago**")
                f1, f2, f3 = st.columns(3)
                comp = f1.selectbox("Mês do DAS", em_aberto, format_func=lambda m: f"{MESES[m['mes'] - 1].capitalize()}/{ano}")
                pago_em = f2.date_input("Pago em", value=hoje, format="DD/MM/YYYY")
                with f3:
                    valor = input_moeda("Valor (R$)", "fin_das_valor", value=DAS_MEI, step=1.0)
                if st.form_submit_button("Lançar pagamento", type="primary", use_container_width=True):
                    if valor <= 0:
                        st.warning("Informe o valor pago.")
                    elif st.session_state.db.lancar_das(ano, comp["mes"], valor, pago_em):
                        st.rerun()
                    else:
                        st.error("Não consegui lançar agora. Tente de novo.")
        else:
            st.success("Todos os DAS devidos até agora estão pagos.")
        st.link_button("Gerar a guia do DAS (PGMEI)", LINK_PGMEI, icon=":material/open_in_new:")
    with c2:
        st.markdown(f'<div class="fp-secao">Declaração anual · DASN-SIMEI {ano_decl}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            ant = faturamento_ano(mov, ano_decl)
            st.markdown(f'<div class="fp-mei"><div class="lin"><span>Receita bruta de {ano_decl}</span>'
                        f'<b>{fmt_brl(ant["total"])}</b></div>'
                        f'<div class="lin"><span>Serviços</span><b>{fmt_brl(ant["servicos"])}</b></div>'
                        f'<div class="lin"><span>Venda de produtos (comércio)</span><b>{fmt_brl(ant["comercio"])}</b></div>'
                        f'<div class="det" style="margin-top:8px">Prazo: até {limite_decl.strftime("%d/%m/%Y")}. '
                        f'São esses números que a declaração pede. Confira com seus extratos antes de enviar.</div></div>',
                        unsafe_allow_html=True)
            st.link_button("Fazer a declaração", LINK_DASN, icon=":material/open_in_new:", use_container_width=True)


def _safe_float(val, default=0.0):
    try:
        if pd.isna(val) or val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _fmt_date(d):
    if d is None:
        return ""
    if isinstance(d, str):
        try:
            return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return d
    try:
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(d)


def _formatar_tipo(tipo):
    if tipo in ['receita_a_receber', 'receita', 'Receita']:
        return 'Receita'
    elif tipo in ['despesa_a_pagar', 'despesa', 'Despesa']:
        return 'Despesa'
    return str(tipo).title() if tipo else '—'


def _is_receita(row):
    return row.get('tipo', '') in ['receita', 'receita_a_receber', 'Receita'] or row.get('classificacao', '') == 'contas_a_receber'


def _is_despesa(row):
    return row.get('tipo', '') in ['despesa', 'despesa_a_pagar', 'Despesa'] or row.get('classificacao', '') == 'contas_a_pagar'


def _render_nova_transacao_form():
    categorias_receita = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
    categorias_despesa = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais",
                          "Custos Administrativos", CATEGORIA_IMPOSTO, CATEGORIA_RETIRADA]

    tipo = st.selectbox("Tipo", ["receita", "despesa"], key="fin_tipo_transacao")

    if tipo == "receita":
        with st.form("registro_receita", clear_on_submit=True):
            descricao = st.text_input("Descrição")
            valor = input_moeda("Valor (R$)", "fin_valor_receita", value=0.0, step=10.0)

            tipo_receita = st.selectbox("Tipo de Receita", ["organização", "comissão", "venda"])

            origem_tipo = st.selectbox("Origem", ["cliente", "fornecedor"])

            origem_id = None
            if origem_tipo == "cliente":
                origens = st.session_state.db.get_clientes()
                if not origens.empty:
                    origem = st.selectbox("Selecione o Cliente", origens['nome'].tolist(),
                                          index=None, placeholder="Selecione um cliente")
                    if origem:
                        origem_id = origens[origens['nome'] == origem]['id'].iloc[0]
                else:
                    st.warning("Nenhum cliente cadastrado")
            else:
                fornecedores = st.session_state.db.get_fornecedores()
                if not fornecedores.empty:
                    origem = st.selectbox("Selecione o Fornecedor", fornecedores['descricao'].tolist(),
                                          index=None, placeholder="Selecione um fornecedor")
                    if origem:
                        origem_id = fornecedores[fornecedores['descricao'] == origem]['id'].iloc[0]
                else:
                    st.warning("Nenhum fornecedor cadastrado")

            categoria = st.selectbox("Categoria", categorias_receita)
            submitted = st.form_submit_button("Registrar Receita", type="primary", use_container_width=True)

            if submitted:
                origem_label = "um cliente" if origem_tipo == "cliente" else "um fornecedor"
                if not descricao or valor <= 0:
                    st.warning("Preencha a descrição e um valor maior que zero.")
                elif origem_id is None:
                    st.error(f"Selecione {origem_label} antes de registrar a receita.")
                else:
                    try:
                        st.session_state.db.add_transacao(
                            tipo="receita", descricao=descricao, valor=valor,
                            categoria=categoria, tipo_receita=tipo_receita,
                            origem_id=origem_id, origem_tipo=origem_tipo
                        )
                        st.success("Receita registrada com sucesso!")
                        st.session_state["fin_nova_transacao_open"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar receita: {str(e)}")
    else:
        with st.form("registro_despesa", clear_on_submit=True):
            descricao = st.text_input("Descrição")
            valor = input_moeda("Valor (R$)", "fin_valor_despesa", value=0.0, step=10.0)
            categoria = st.selectbox("Categoria", categorias_despesa)
            submitted = st.form_submit_button("Registrar Despesa", type="primary", use_container_width=True)

            if submitted:
                if descricao and valor > 0:
                    try:
                        st.session_state.db.add_transacao(
                            tipo="despesa", descricao=descricao, valor=valor,
                            categoria=categoria, tipo_receita=None,
                            origem_id=None, origem_tipo=None
                        )
                        st.success("Despesa registrada com sucesso!")
                        st.session_state["fin_nova_transacao_open"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar despesa: {str(e)}")
                else:
                    st.warning("Preencha todos os campos corretamente.")


def _render_detail_panel(transacao, financeiro_df):
    tid = transacao['id']
    descricao = html_module.escape(str(transacao.get('descricao', '—')))
    tipo_label = _formatar_tipo(transacao.get('tipo', ''))
    categoria = html_module.escape(str(transacao.get('categoria', '—')))
    status = str(transacao.get('status', '—'))
    data_str = _fmt_date(transacao.get('data'))
    valor = _safe_float(transacao.get('valor'))

    is_rec = _is_receita(transacao)
    border_color = "#C9A84C" if is_rec else "#E53E3E"
    badge_bg = "#C6F6D5" if is_rec else "#FED7D7"
    badge_fg = "#276749" if is_rec else "#9B2C2C"

    meta_parts = [tipo_label, categoria]
    if data_str:
        meta_parts.append(f"{data_str}")
    prop_id = transacao.get('proposta_id')
    if prop_id and not pd.isna(prop_id):
        meta_parts.append(f"Proposta #{int(prop_id)}")
    meta_str = " · ".join(meta_parts)

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e2e8f0;border-left:4px solid {border_color};
                border-radius:8px;padding:12px 16px;margin-bottom:4px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <p style="font-weight:700;font-size:1rem;color:#1a202c;margin:0 0 4px 0;">
                    {descricao}
                    <span style="display:inline-block;padding:2px 8px;border-radius:12px;
                                 font-size:0.7rem;font-weight:600;background:{badge_bg};color:{badge_fg};
                                 margin-left:6px;">{html_module.escape(status)}</span>
                </p>
                <p style="font-size:0.78rem;color:#64748b;margin:0;">{meta_str}</p>
            </div>
            <span style="font-weight:700;font-size:1.1rem;color:{border_color};white-space:nowrap;">
                {fmt_brl(valor)}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    is_pendente = status == 'Pendente'

    if is_pendente:
        acao_label = "Receber" if is_rec else "Pagar"
        acao_key = f"fin_receber_{tid}" if is_rec else f"fin_pagar_{tid}"
        confirm_key = f"fin_confirm_receber_{tid}" if is_rec else f"fin_confirm_pagar_{tid}"

        # receber/pagar é a ação principal; excluir fica menor, logo ao lado
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        col_act1, col_act2, col_act3 = st.columns([2, 2, 1.2])
        with col_act1:
            if st.button(acao_label, key=acao_key, type="primary", icon=":material/check:", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()
        with col_act2:
            if botao_editar("Editar", key=f"fin_edit_{tid}", use_container_width=True):
                st.session_state["fin_editando"] = tid
                st.rerun()
        with col_act3:
            if botao_excluir("Excluir", f"fin_del_{tid}"):
                st.session_state[f"fin_confirm_del_{tid}"] = True
                st.rerun()
    else:
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        col_del, _ = st.columns([1.2, 4])
        with col_del:
            if botao_excluir("Excluir", f"fin_del_{tid}"):
                st.session_state[f"fin_confirm_del_{tid}"] = True
                st.rerun()

    if st.session_state.get(f"fin_confirm_receber_{tid}", False):
        st.success(f"Confirmar recebimento de **{fmt_brl(valor)}** — {transacao['descricao']}?")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("Confirmar", key=f"conf_rec_{tid}", type="primary", use_container_width=True):
                try:
                    st.session_state.db.atualizar_status_transacao(tid, 'Recebido', datetime.now().date())
                    st.session_state.pop(f"fin_confirm_receber_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with c2:
            if st.button("Voltar", key=f"cancel_rec_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_receber_{tid}", None)
                st.rerun()

    if st.session_state.get(f"fin_confirm_pagar_{tid}", False):
        st.success(f"Confirmar pagamento de **{fmt_brl(valor)}** — {transacao['descricao']}?")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("Confirmar", key=f"conf_pag_{tid}", type="primary", use_container_width=True):
                try:
                    st.session_state.db.atualizar_status_transacao(tid, 'Pago', datetime.now().date())
                    st.session_state.pop(f"fin_confirm_pagar_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with c2:
            if st.button("Voltar", key=f"cancel_pag_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_pagar_{tid}", None)
                st.rerun()

    if st.session_state.get(f"fin_confirm_del_{tid}", False):
        st.warning(f"Excluir **{transacao['descricao']}** — {fmt_brl(valor)} permanentemente?")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if botao_excluir("Excluir de vez", f"conf_del_{tid}"):
                try:
                    st.session_state.db.delete_transacao(tid)
                    st.session_state.pop(f"fin_confirm_del_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with c2:
            if st.button("Voltar", key=f"cancel_del_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_del_{tid}", None)
                st.rerun()

    if st.session_state.get("fin_editando") == tid:
        _render_edit_form(transacao)


def _render_edit_form(transacao):
    tid = transacao['id']
    categorias_receita = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
    categorias_despesa = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais",
                          "Custos Administrativos", CATEGORIA_IMPOSTO, CATEGORIA_RETIRADA]

    st.markdown("---")
    with st.form(key=f"edit_form_{tid}"):
        tipo_exibido = "receita" if transacao['tipo'] in ["receita", "receita_a_receber", "Receita"] else "despesa"

        tipo = st.selectbox("Tipo", ["receita", "despesa"], index=0 if tipo_exibido == "receita" else 1)
        descricao = st.text_input("Descrição", value=transacao['descricao'])
        valor = input_moeda("Valor (R$)", f"fin_valor_edit_{tid}", value=_safe_float(transacao.get('valor')), step=10.0)

        tipo_receita = None
        if tipo == "receita":
            tr_val = transacao.get('tipo_receita') if pd.notna(transacao.get('tipo_receita')) else "organização"
            tr_options = ["organização", "comissão", "venda"]
            tr_idx = tr_options.index(tr_val) if tr_val in tr_options else 0
            tipo_receita = st.selectbox("Tipo de Receita", tr_options, index=tr_idx)

        if tipo == "receita":
            cats = categorias_receita
            cat_val = transacao.get('categoria', '')
            if cat_val == "Serviço":
                cat_idx = 0
            elif cat_val in ["Venda de Produtos", "Produto"]:
                cat_idx = 1
            elif cat_val in ["Fornecedor", "Comissão", "Comissão sobre Fornecedores"]:
                cat_idx = 2
            elif cat_val in cats:
                cat_idx = cats.index(cat_val)
            else:
                cat_idx = 3
        else:
            cats = categorias_despesa
            cat_val = transacao.get('categoria', '')
            if cat_val in ["Assistente", "Pagamento Equipe/Assistentes", "Pagamento de Assistente"]:
                cat_idx = 0
            elif cat_val in ["Fornecedor", "Pagamento Parceiros/Fornecedores"]:
                cat_idx = 1
            elif cat_val in cats:
                cat_idx = cats.index(cat_val)
            else:
                cat_idx = 3

        categoria = st.selectbox("Categoria", cats, index=min(cat_idx, len(cats) - 1))

        col1, col2 = st.columns(2)
        with col1:
            salvar = st.form_submit_button("Salvar", type="primary", use_container_width=True)
        with col2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if salvar:
        try:
            st.session_state.db.update_transacao(
                tid, tipo=tipo, descricao=descricao, valor=valor,
                categoria=categoria, tipo_receita=tipo_receita
            )
            st.success("Transação atualizada!")
            st.session_state.pop("fin_editando", None)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {str(e)}")

    if cancelar:
        st.session_state.pop("fin_editando", None)
        st.rerun()


def _dedup_transacoes(df):
    if df.empty:
        return df
    dedup_cols = ['descricao', 'valor', 'data', 'proposta_id', 'categoria', 'status']
    available = [c for c in dedup_cols if c in df.columns]
    if available:
        df = df.drop_duplicates(subset=available, keep='first')

    if 'categoria' not in df.columns:
        return df
    equipe = df[df['categoria'] == 'Pagamento Equipe/Assistentes']
    assistente = df[df['categoria'] == 'Pagamento de Assistente']
    if equipe.empty or assistente.empty:
        return df
    dup_ids = []
    for _, row in assistente.iterrows():
        if 'proposta_id' in row and pd.notna(row.get('proposta_id')):
            dups = equipe[
                (equipe['proposta_id'] == row['proposta_id']) &
                (equipe['valor'] == row['valor'])
            ]
            if not dups.empty:
                dup_ids.append(row['id'])
    if dup_ids:
        return df[~df['id'].isin(dup_ids)]
    return df


def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown("""
    <style>
    .fin-page .main h2 { font-size: 1.1rem !important; font-weight: 700 !important; }
    .fin-page .main h3 { font-size: 0.95rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
    .stTextInput input, .stSelectbox select,
    .stNumberInput input, .stDateInput input,
    .stTextArea textarea { font-size: 0.85rem !important; }
    label[data-testid="stWidgetLabel"] > div > p { font-size: 0.82rem !important; }

    .kanban-col-header {
        font-weight: 700; font-size: 0.82rem;
        padding: 6px 10px; border-radius: 8px 8px 0 0;
        margin-bottom: 6px; text-align: center;
        letter-spacing: 0.03em; text-transform: uppercase;
    }
    .kanban-card {
        border: 1px solid #dee2e6; border-radius: 8px;
        padding: 8px 10px; margin-bottom: 6px;
        background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kanban-card-title { font-weight: 600; font-size: 0.82rem; margin-bottom: 1px; color: #1a202c; overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
    .kanban-card-sub { font-size: 0.72rem; color: #6c757d; margin-bottom: 3px; overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
    /* VALORES (dinheiro): nunca quebrar número no meio nem reticenciar.
       word-break:keep-all + overflow-wrap:normal => quebra no máximo no
       espaço do "R$" (2 linhas), mantendo "18.616,00" inteiro. */
    .kanban-card-valor { font-size: 0.78rem; font-weight: 600; overflow-wrap: normal; word-break: keep-all; white-space: normal; overflow: visible; text-overflow: clip; }
    .kanban-metric-value { overflow-wrap: normal; word-break: keep-all; white-space: normal; overflow: visible; text-overflow: clip; }
    /* RÓTULOS: quebrar só entre palavras, nunca no meio da palavra. */
    .kanban-card { overflow-wrap: break-word; word-break: normal; }
    .kanban-card-title, .kanban-card-sub { overflow-wrap: break-word; word-break: normal; }
    .kanban-col-header { white-space: normal; overflow-wrap: break-word; word-break: normal; }
    .kanban-metric-label { overflow-wrap: break-word; word-break: normal; }
    @media screen and (max-width: 768px) { .kanban-card-title { font-size: 0.9rem; } .kanban-card-sub { font-size: 0.8rem; } .kanban-card-valor { font-size: 0.82rem; } .kanban-metric { padding: 8px 6px; } .kanban-metric-label { font-size: 0.62rem; } .kanban-metric-value { font-size: 0.8rem; } .kanban-col-header { font-size: 0.74rem; } }
    @media screen and (max-width: 400px) { .kanban-metric-value { font-size: 0.72rem; } }
    .kanban-metric {
        background: #fff; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 10px 14px; text-align: center;
    }
    .kanban-metric-label {
        font-size: 0.72rem; color: #64748b; margin: 0 0 4px 0;
        font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase;
    }
    .kanban-metric-value {
        font-size: 0.95rem; font-weight: 700; color: #1a202c; margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    if "db" not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown('<h1 class="page-title">Financeiro</h1>', unsafe_allow_html=True)

    if "fin_selecionada" not in st.session_state:
        st.session_state["fin_selecionada"] = None
    if "fin_nova_transacao_open" not in st.session_state:
        st.session_state["fin_nova_transacao_open"] = False

    # Recarrega do banco apenas ao entrar na página (navegação); reruns por
    # interação de widget usam o cache — as mutações invalidam o cache no Database.
    entrou_na_pagina = st.session_state.get("_last_page_rendered") != "Financeiro"
    if entrou_na_pagina:
        st.session_state["fin_selecionada"] = None
        st.session_state.pop("fin_editando", None)
        for k in [k for k in st.session_state if str(k).startswith("fin_confirm_")]:
            st.session_state.pop(k, None)

    try:
        financeiro_df = st.session_state.db.get_financeiro(force_reload=entrou_na_pagina)
    except Exception as e:
        st.warning(f"Erro ao carregar dados financeiros: {str(e)}")
        financeiro_df = pd.DataFrame()

    required_cols = ['id', 'tipo', 'descricao', 'valor', 'data', 'status', 'categoria']
    if not financeiro_df.empty:
        for c in required_cols:
            if c not in financeiro_df.columns:
                financeiro_df[c] = None
        financeiro_df['data'] = pd.to_datetime(financeiro_df['data'], errors='coerce')
        financeiro_df = _dedup_transacoes(financeiro_df)

    pendentes = financeiro_df[financeiro_df['status'] == 'Pendente'].copy() if not financeiro_df.empty else pd.DataFrame()

    a_receber = pd.DataFrame()
    a_pagar = pd.DataFrame()
    if not pendentes.empty:
        rec_mask = pendentes.apply(lambda r: _is_receita(r), axis=1)
        a_receber = pendentes[rec_mask].copy()
        a_pagar = pendentes[~rec_mask].copy()

    concluidas = pd.DataFrame()
    if not financeiro_df.empty:
        concluidas = financeiro_df[financeiro_df['status'].isin(['Aprovado', 'Recebido', 'Pago'])].copy()

    aba_lanc, aba_mei = st.tabs(["Lançamentos", "MEI"])
    with aba_mei:
        _aba_mei(financeiro_df)
    with aba_lanc:
        _conteudo_lancamentos(financeiro_df, a_receber, a_pagar, concluidas)


def _conteudo_lancamentos(financeiro_df, a_receber, a_pagar, concluidas):
    col_btn, _ = st.columns([1, 3])
    with col_btn, st.container(key="cta_novo_lancamento"):
        if st.button("Novo lançamento", type="primary", icon=":material/add:", use_container_width=True, key="btn_nova_transacao"):
            st.session_state["fin_nova_transacao_open"] = not st.session_state["fin_nova_transacao_open"]
    if st.session_state["fin_nova_transacao_open"]:
        with st.expander("Novo lançamento", expanded=True):
            _render_nova_transacao_form()

    _painel_mes(financeiro_df)


    st.markdown("---")

    CARDS_POR_COLUNA = 6

    col_receber, col_pagar, col_concluidas = st.columns(3)

    for col_idx, (col_widget, col_label, col_df, col_color, valor_cor) in enumerate([
        (col_receber, "A receber", a_receber, "#ECFDF3", "#067647"),
        (col_pagar, "A pagar", a_pagar, "#FEF3F2", "#B42318"),
        (col_concluidas, "Recebidas e pagas", concluidas, "#F2F4F7", "#475467"),
    ]):
        with col_widget:
            count = len(col_df)
            st.markdown(
                f'<div class="kanban-col-header" style="background-color:{col_color};">{col_label} ({count})</div>',
                unsafe_allow_html=True
            )

            if not col_df.empty:
                display_df = col_df.sort_values("data", ascending=False)
                mostrar_todas = st.session_state.get(f"fin_show_all_{col_idx}", False)
                if not mostrar_todas:
                    display_df = display_df.head(CARDS_POR_COLUNA)

                for _, row in display_df.iterrows():
                    rid = row['id']
                    desc = html_module.escape(str(row.get('descricao', '—')))
                    cat = html_module.escape(str(row.get('categoria', '')))
                    data_s = _fmt_date(row.get('data'))
                    val_f = fmt_brl(_safe_float(row.get('valor')))

                    if cartao_clicavel(
                        f'<div class="kanban-card">'
                        f'<div class="kanban-card-title">{desc}</div>'
                        f'<div class="kanban-card-sub"><i class="fp-dot" style="background:{cor_categoria(cat)};margin-right:6px"></i>{cat} · {data_s}</div>'
                        f'<div class="kanban-card-valor" style="color:{valor_cor};">{val_f}</div>'
                        f'</div>',
                        key=f"fin_card_{col_idx}_{rid}", rotulo=f"Abrir {desc}"):
                        st.session_state["fin_selecionada"] = rid
                        st.rerun()

                if count > CARDS_POR_COLUNA:
                    toggle_label = "▲ Mostrar menos" if mostrar_todas else f"▼ Mostrar todas ({count})"
                    if st.button(toggle_label, key=f"fin_more_{col_idx}", use_container_width=True):
                        st.session_state[f"fin_show_all_{col_idx}"] = not mostrar_todas
                        st.rerun()
            else:
                st.caption("Nenhuma transação.")

    selected_id = st.session_state.get("fin_selecionada")
    if selected_id is not None and not financeiro_df.empty:
        rows = financeiro_df[financeiro_df['id'] == selected_id]
        if not rows.empty:
            transacao_sel = rows.iloc[0]

            @st.dialog("Detalhes da Transação", width="large")
            def _modal_detalhes():
                _render_detail_panel(transacao_sel, financeiro_df)
                if st.button("Fechar", key=f"fin_fechar_modal_{selected_id}", type="tertiary"):
                    st.session_state["fin_selecionada"] = None
                    st.session_state.pop("fin_editando", None)
                    for k in [k for k in st.session_state if str(k).startswith("fin_confirm_")]:
                        st.session_state.pop(k, None)
                    st.rerun()

            _modal_detalhes()
        else:
            st.session_state["fin_selecionada"] = None

    st.markdown("---")

    with st.expander("Histórico Financeiro", expanded=False):
        historico = financeiro_df[~(financeiro_df['status'] == 'Pendente')].copy() if not financeiro_df.empty else pd.DataFrame()

        if not historico.empty:
            h1, h2, h3 = st.columns([2, 1.5, 1.5])
            with h1:
                busca = st.text_input("Buscar por descrição", key="fin_hist_busca")
            with h2:
                tipo_filtro = st.multiselect("Tipo", ["receita", "despesa"], key="fin_hist_tipo")
                tipo_map = {
                    "receita": ["receita", "receita_a_receber", "Receita"],
                    "despesa": ["despesa", "despesa_a_pagar", "Despesa"],
                }
            with h3:
                meses_disponiveis = sorted(historico['data'].dt.to_period('M').dropna().unique(), reverse=True)
                meses_str = [str(m) for m in meses_disponiveis]
                mes_filtro = st.selectbox("Período", ["Todos"] + meses_str, key="fin_hist_mes")

            if busca:
                historico = historico[historico['descricao'].str.contains(busca, case=False, na=False)]
            if tipo_filtro:
                all_types = []
                for t in tipo_filtro:
                    all_types.extend(tipo_map.get(t, [t]))
                historico = historico[historico['tipo'].isin(all_types)]
            if mes_filtro != "Todos":
                historico = historico[historico['data'].dt.to_period('M').astype(str) == mes_filtro]

            if not historico.empty:
                rec_total = historico[historico.apply(lambda r: _is_receita(r), axis=1)]['valor'].sum()
                desp_total = historico[historico.apply(lambda r: _is_despesa(r), axis=1)]['valor'].sum()
                saldo_hist = rec_total - desp_total

                hm1, hm2, hm3, hm4 = st.columns(4)
                hm1.metric("Receitas", fmt_brl(rec_total))
                hm2.metric("Despesas", fmt_brl(desp_total))
                hm3.metric("Saldo", fmt_brl(saldo_hist))
                hm4.metric("Transações", f"{len(historico):,}")

                df_disp = historico.copy()
                df_disp['Data'] = df_disp['data'].dt.strftime('%d/%m/%Y')
                df_disp['Tipo'] = df_disp['tipo'].apply(_formatar_tipo)
                df_disp['Valor'] = df_disp['valor'].apply(fmt_brl)
                df_disp['Descrição'] = df_disp['descricao']
                df_disp['Categoria'] = df_disp['categoria'].fillna('—')
                df_disp['Status'] = df_disp['status']

                st.dataframe(
                    df_disp[['Data', 'Tipo', 'Descrição', 'Valor', 'Categoria', 'Status']],
                    use_container_width=True, hide_index=True
                )

                transacoes_display = [
                    f"{row['data'].strftime('%d/%m/%Y')} · {row['descricao']} · {fmt_brl(row['valor'])} · {row['status']}"
                    for _, row in historico.iterrows()
                ]
                if transacoes_display:
                    col_sel, col_del = st.columns([5, 1])
                    with col_sel:
                        selected_idx = st.selectbox(
                            "Selecione para excluir:",
                            range(len(transacoes_display)),
                            format_func=lambda x: transacoes_display[x],
                            key="fin_hist_select", label_visibility="collapsed"
                        )
                    with col_del:
                        if botao_excluir("Excluir", "fin_hist_del"):
                            t_sel = historico.iloc[selected_idx]
                            st.session_state[f"fin_hist_confirm_del_{t_sel['id']}"] = True
                            st.rerun()

                    if selected_idx is not None:
                        t_sel = historico.iloc[selected_idx]
                        if st.session_state.get(f"fin_hist_confirm_del_{t_sel['id']}", False):
                            st.warning(f"Excluir **{t_sel['descricao']}** — {fmt_brl(t_sel['valor'])}?")
                            c1, c2, _ = st.columns([1, 1, 5])
                            with c1:
                                if botao_excluir("Excluir de vez", f"fin_hist_conf_{t_sel['id']}"):
                                    try:
                                        st.session_state.db.delete_transacao(t_sel['id'])
                                        st.session_state.pop(f"fin_hist_confirm_del_{t_sel['id']}", None)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {str(e)}")
                            with c2:
                                if st.button("Voltar", key=f"fin_hist_canc_{t_sel['id']}", use_container_width=True):
                                    st.session_state.pop(f"fin_hist_confirm_del_{t_sel['id']}", None)
                                    st.rerun()
            else:
                st.info("Nenhuma transação encontrada com os filtros.")
        else:
            st.info("Não há transações no histórico.")

    with st.expander("Últimos 6 meses", expanded=False):
        mov = movimentos(financeiro_df.assign(data=financeiro_df["data"].dt.date) if not financeiro_df.empty else financeiro_df)
        if mov.empty:
            st.info("Não há dados suficientes para gerar análise.")
            return
        hoje = datetime.now().date()
        linhas, cats = [], []
        a, m = hoje.year, hoje.month
        for _ in range(6):
            entrou, gastou = entrou_gastou(mov, a, m)
            rotulo = f"{MES_ABREV[m - 1]}/{str(a)[2:]}"
            linhas += [{"Mês": rotulo, "Tipo": "Entrou", "Valor": entrou}, {"Mês": rotulo, "Tipo": "Gastou", "Valor": gastou}]
            cats += [{"Mês": rotulo, "Categoria": c, "Valor": v} for c, v in por_categoria(mov, a, m, "sai")]
            a, m = (a - 1, 12) if m == 1 else (a, m - 1)
        df_mes = pd.DataFrame(linhas[::-1])
        fig1 = px.bar(df_mes, x="Mês", y="Valor", color="Tipo", barmode="group", height=320,
                      color_discrete_map={"Entrou": "#12B76A", "Gastou": "#F04438"},
                      category_orders={"Mês": list(dict.fromkeys(df_mes["Mês"]))})
        fig1.update_layout(title="Entrou x gastou", margin=dict(l=0, r=0, t=40, b=0), legend_title_text="",
                           legend=dict(orientation="h", yanchor="bottom", y=1.02),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig1, use_container_width=True)
        if cats:
            df_cat = pd.DataFrame(cats[::-1])
            fig2 = px.bar(df_cat, x="Mês", y="Valor", color="Categoria", height=340,
                          color_discrete_map={c: cor_categoria(c) for c in df_cat["Categoria"].unique()},
                          category_orders={"Mês": list(dict.fromkeys(df_mes["Mês"]))})
            fig2.update_layout(title="Gastos por categoria", margin=dict(l=0, r=0, t=40, b=0), legend_title_text="",
                               legend=dict(orientation="h", yanchor="top", y=-0.15),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
