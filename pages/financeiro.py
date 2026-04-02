import streamlit as st
import pandas as pd
import plotly.express as px
import html as html_module
from datetime import datetime, timedelta
from utils.currency_formatter import fmt_brl
from utils.design_tokens import (
    NAVY, GOLD, GOLD_DARK, GOLD_GRADIENT, GOLD_BUTTON_CSS,
    TEXT_PRIMARY, TEXT_SECONDARY,
)
from streamlit_extras.stylable_container import stylable_container


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
    categorias_despesa = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais", "Custos Administrativos"]

    tipo = st.selectbox("Tipo", ["receita", "despesa"], key="fin_tipo_transacao")

    if tipo == "receita":
        with st.form("registro_receita", clear_on_submit=True):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            tipo_receita = st.selectbox("Tipo de Receita", ["organização", "comissão", "venda"])

            origem_tipo = st.selectbox("Origem", ["cliente", "fornecedor"])

            origem_id = None
            if origem_tipo == "cliente":
                origens = st.session_state.db.get_clientes()
                if not origens.empty:
                    origem = st.selectbox("Selecione o Cliente", origens['nome'].tolist())
                    origem_id = origens[origens['nome'] == origem]['id'].iloc[0]
                else:
                    st.warning("Nenhum cliente cadastrado")
            else:
                fornecedores = st.session_state.db.get_fornecedores()
                if not fornecedores.empty:
                    origem = st.selectbox("Selecione o Fornecedor", fornecedores['descricao'].tolist())
                    origem_id = fornecedores[fornecedores['descricao'] == origem]['id'].iloc[0]
                else:
                    st.warning("Nenhum fornecedor cadastrado")

            categoria = st.selectbox("Categoria", categorias_receita)
            submitted = st.form_submit_button("Registrar Receita", type="primary", use_container_width=True)

            if submitted:
                if descricao and valor > 0:
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
                    st.warning("Preencha todos os campos corretamente.")
    else:
        with st.form("registro_despesa", clear_on_submit=True):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
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
        meta_parts.append(f"📅 {data_str}")
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
        if is_rec:
            col_act1, col_act2, col_act3, col_space = st.columns([1, 1, 1, 3])
            with col_act1:
                if st.button("✅ Receber", key=f"fin_receber_{tid}", use_container_width=True):
                    st.session_state[f"fin_confirm_receber_{tid}"] = True
                    st.rerun()
            with col_act2:
                if st.button("✏️ Editar", key=f"fin_edit_{tid}", use_container_width=True):
                    st.session_state["fin_editando"] = tid
                    st.rerun()
            with col_act3:
                if st.button("🗑️ Excluir", key=f"fin_del_{tid}", use_container_width=True):
                    st.session_state[f"fin_confirm_del_{tid}"] = True
                    st.rerun()
        else:
            col_act1, col_act2, col_act3, col_space = st.columns([1, 1, 1, 3])
            with col_act1:
                if st.button("✅ Pagar", key=f"fin_pagar_{tid}", use_container_width=True):
                    st.session_state[f"fin_confirm_pagar_{tid}"] = True
                    st.rerun()
            with col_act2:
                if st.button("✏️ Editar", key=f"fin_edit_{tid}", use_container_width=True):
                    st.session_state["fin_editando"] = tid
                    st.rerun()
            with col_act3:
                if st.button("🗑️ Excluir", key=f"fin_del_{tid}", use_container_width=True):
                    st.session_state[f"fin_confirm_del_{tid}"] = True
                    st.rerun()
    else:
        col_del, col_space = st.columns([1, 5])
        with col_del:
            if st.button("🗑️ Excluir", key=f"fin_del_{tid}", use_container_width=True):
                st.session_state[f"fin_confirm_del_{tid}"] = True
                st.rerun()

    if st.session_state.get(f"fin_confirm_receber_{tid}", False):
        st.success(f"Confirmar recebimento de **{fmt_brl(valor)}** — {transacao['descricao']}?")
        c1, c2, _ = st.columns([1, 1, 5])
        with c1:
            if st.button("✓ Confirmar", key=f"conf_rec_{tid}", use_container_width=True):
                try:
                    st.session_state.db.atualizar_status_transacao(tid, 'Recebido', datetime.now().date())
                    st.session_state.pop(f"fin_confirm_receber_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with c2:
            if st.button("✗ Voltar", key=f"cancel_rec_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_receber_{tid}", None)
                st.rerun()

    if st.session_state.get(f"fin_confirm_pagar_{tid}", False):
        st.success(f"Confirmar pagamento de **{fmt_brl(valor)}** — {transacao['descricao']}?")
        c1, c2, _ = st.columns([1, 1, 5])
        with c1:
            if st.button("✓ Confirmar", key=f"conf_pag_{tid}", use_container_width=True):
                try:
                    st.session_state.db.atualizar_status_transacao(tid, 'Pago', datetime.now().date())
                    st.session_state.pop(f"fin_confirm_pagar_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with c2:
            if st.button("✗ Voltar", key=f"cancel_pag_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_pagar_{tid}", None)
                st.rerun()

    if st.session_state.get(f"fin_confirm_del_{tid}", False):
        st.warning(f"Excluir **{transacao['descricao']}** — {fmt_brl(valor)} permanentemente?")
        c1, c2, _ = st.columns([1, 1, 5])
        with c1:
            if st.button("✓ Confirmar", key=f"conf_del_{tid}", use_container_width=True):
                try:
                    st.session_state.db.delete_transacao(tid)
                    st.session_state.pop(f"fin_confirm_del_{tid}", None)
                    st.session_state["fin_selecionada"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with c2:
            if st.button("✗ Voltar", key=f"cancel_del_{tid}", use_container_width=True):
                st.session_state.pop(f"fin_confirm_del_{tid}", None)
                st.rerun()

    if st.session_state.get("fin_editando") == tid:
        _render_edit_form(transacao)


def _render_edit_form(transacao):
    tid = transacao['id']
    categorias_receita = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
    categorias_despesa = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais", "Custos Administrativos"]

    st.markdown("---")
    with st.form(key=f"edit_form_{tid}"):
        tipo_exibido = "receita" if transacao['tipo'] in ["receita", "receita_a_receber", "Receita"] else "despesa"

        tipo = st.selectbox("Tipo", ["receita", "despesa"], index=0 if tipo_exibido == "receita" else 1)
        descricao = st.text_input("Descrição", value=transacao['descricao'])
        valor = st.number_input("Valor (R$)", value=_safe_float(transacao.get('valor')), min_value=0.0, step=0.01)

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
            salvar = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

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
    .kanban-card-title { font-weight: 600; font-size: 0.82rem; margin-bottom: 1px; color: #1a202c; }
    .kanban-card-sub { font-size: 0.72rem; color: #6c757d; margin-bottom: 3px; }
    .kanban-card-valor { font-size: 0.78rem; font-weight: 600; }
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

    st.markdown('<div class="fin-page">', unsafe_allow_html=True)

    if "db" not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Gestão Financeira</h1>', unsafe_allow_html=True)

    if "fin_selecionada" not in st.session_state:
        st.session_state["fin_selecionada"] = None
    if "fin_nova_transacao_open" not in st.session_state:
        st.session_state["fin_nova_transacao_open"] = False

    try:
        financeiro_df = st.session_state.db.get_financeiro(force_reload=True)
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

    total_receber = a_receber['valor'].apply(_safe_float).sum() if not a_receber.empty else 0.0
    total_pagar = a_pagar['valor'].apply(_safe_float).sum() if not a_pagar.empty else 0.0
    saldo = total_receber - total_pagar

    mc1, mc2, mc3 = st.columns(3)
    for col, label, valor, cor in [
        (mc1, "💰 A RECEBER", total_receber, "#C9A84C"),
        (mc2, "💸 A PAGAR", total_pagar, "#E53E3E"),
        (mc3, "📊 SALDO", saldo, "#C9A84C" if saldo >= 0 else "#E53E3E"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kanban-metric">
                <p class="kanban-metric-label">{label}</p>
                <p class="kanban-metric-value" style="color:{cor};">{fmt_brl(valor)}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    col_esp1, col_btn, col_esp2 = st.columns([1, 3, 1])
    with col_btn:
        with stylable_container(key="gold_nova_transacao", css_styles=GOLD_BUTTON_CSS):
            if st.button("✚  Nova Transação", type="primary", use_container_width=True, key="btn_nova_transacao"):
                st.session_state["fin_nova_transacao_open"] = not st.session_state["fin_nova_transacao_open"]

    if st.session_state["fin_nova_transacao_open"]:
        with st.expander("💰 Nova Transação", expanded=True):
            _render_nova_transacao_form()

    st.markdown("---")

    MAX_CONCLUIDAS = 5

    col_receber, col_pagar, col_concluidas = st.columns(3)

    for col_idx, (col_widget, col_label, col_df, col_color, valor_cor) in enumerate([
        (col_receber, "💰 A Receber", a_receber, "#f5f0e0", "#C9A84C"),
        (col_pagar, "💸 A Pagar", a_pagar, "#f8d7da", "#E53E3E"),
        (col_concluidas, "✅ Aprovadas/Pagas", concluidas, "#e2e3e5", "#4A5568"),
    ]):
        with col_widget:
            count = len(col_df)
            st.markdown(
                f'<div class="kanban-col-header" style="background-color:{col_color};">{col_label} ({count})</div>',
                unsafe_allow_html=True
            )

            if not col_df.empty:
                display_df = col_df.sort_values("data", ascending=False)
                if col_idx == 2:
                    display_df = display_df.head(MAX_CONCLUIDAS)

                for _, row in display_df.iterrows():
                    rid = row['id']
                    desc = html_module.escape(str(row.get('descricao', '—'))[:50])
                    cat = html_module.escape(str(row.get('categoria', '')))
                    data_s = _fmt_date(row.get('data'))
                    val_f = fmt_brl(_safe_float(row.get('valor')))

                    st.markdown(
                        f'<div class="kanban-card">'
                        f'<div class="kanban-card-title">{desc}</div>'
                        f'<div class="kanban-card-sub">{cat} · {data_s}</div>'
                        f'<div class="kanban-card-valor" style="color:{valor_cor};">{val_f}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    is_selected = st.session_state.get("fin_selecionada") == rid
                    btn_label = "▲ Fechar" if is_selected else "▼ Ver Detalhes"
                    if st.button(btn_label, key=f"fin_card_{col_idx}_{rid}", use_container_width=True):
                        if is_selected:
                            st.session_state["fin_selecionada"] = None
                        else:
                            st.session_state["fin_selecionada"] = rid
                        st.rerun()

                if col_idx == 2 and count > MAX_CONCLUIDAS:
                    st.caption(f"Exibindo {MAX_CONCLUIDAS} de {count}")
            else:
                st.caption("Nenhuma transação.")

    selected_id = st.session_state.get("fin_selecionada")
    if selected_id is not None and not financeiro_df.empty:
        st.markdown("---")
        rows = financeiro_df[financeiro_df['id'] == selected_id]
        if not rows.empty:
            _render_detail_panel(rows.iloc[0], financeiro_df)
        else:
            st.info("Transação não encontrada.")
            st.session_state["fin_selecionada"] = None

    st.markdown("---")

    with st.expander("📜 Histórico Financeiro", expanded=False):
        historico = financeiro_df[~(financeiro_df['status'] == 'Pendente')].copy() if not financeiro_df.empty else pd.DataFrame()

        if not historico.empty:
            h1, h2, h3 = st.columns([2, 1.5, 1.5])
            with h1:
                busca = st.text_input("🔍 Buscar por descrição", key="fin_hist_busca")
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
                        if st.button("🗑️ Excluir", key="fin_hist_del", use_container_width=True):
                            t_sel = historico.iloc[selected_idx]
                            st.session_state[f"fin_hist_confirm_del_{t_sel['id']}"] = True
                            st.rerun()

                    if selected_idx is not None:
                        t_sel = historico.iloc[selected_idx]
                        if st.session_state.get(f"fin_hist_confirm_del_{t_sel['id']}", False):
                            st.warning(f"Excluir **{t_sel['descricao']}** — {fmt_brl(t_sel['valor'])}?")
                            c1, c2, _ = st.columns([1, 1, 5])
                            with c1:
                                if st.button("✓ Confirmar", key=f"fin_hist_conf_{t_sel['id']}", use_container_width=True):
                                    try:
                                        st.session_state.db.delete_transacao(t_sel['id'])
                                        st.session_state.pop(f"fin_hist_confirm_del_{t_sel['id']}", None)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {str(e)}")
                            with c2:
                                if st.button("✗ Voltar", key=f"fin_hist_canc_{t_sel['id']}", use_container_width=True):
                                    st.session_state.pop(f"fin_hist_confirm_del_{t_sel['id']}", None)
                                    st.rerun()
            else:
                st.info("Nenhuma transação encontrada com os filtros.")
        else:
            st.info("Não há transações no histórico.")

    with st.expander("📈 Análise Financeira", expanded=False):
        if not financeiro_df.empty:
            fin_copy = financeiro_df.copy()
            fin_copy['mes'] = fin_copy['data'].dt.to_period('M').astype(str)

            dados_mensais = fin_copy.groupby(['mes', 'tipo'])['valor'].sum().reset_index()
            if not dados_mensais.empty:
                fig1 = px.bar(
                    dados_mensais, x='mes', y='valor', color='tipo',
                    color_discrete_map={
                        'receita': '#38A169', 'despesa': '#E53E3E',
                        'receita_a_receber': '#68D391', 'despesa_a_pagar': '#FC8181',
                        'Receita': '#38A169', 'Despesa': '#E53E3E'
                    },
                    labels={'valor': 'Valor (R$)', 'mes': 'Mês', 'tipo': 'Tipo'},
                    barmode='group', height=350
                )
                fig1.update_layout(
                    title="Receitas vs Despesas por Mês",
                    margin=dict(l=0, r=0, t=40, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig1, use_container_width=True)

            dados_cat = fin_copy.groupby(['categoria', 'tipo'])['valor'].sum().reset_index()
            if not dados_cat.empty:
                fig2 = px.bar(
                    dados_cat, x='categoria', y='valor', color='tipo',
                    color_discrete_map={
                        'receita': '#38A169', 'despesa': '#E53E3E',
                        'receita_a_receber': '#68D391', 'despesa_a_pagar': '#FC8181',
                        'Receita': '#38A169', 'Despesa': '#E53E3E'
                    },
                    labels={'valor': 'Valor (R$)', 'categoria': 'Categoria', 'tipo': 'Tipo'},
                    height=350
                )
                fig2.update_layout(
                    title="Distribuição por Categoria",
                    margin=dict(l=0, r=0, t=40, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Não há dados suficientes para gerar análise.")

    st.markdown('</div>', unsafe_allow_html=True)
