"""
Módulo de Pós-Organização
Gerencia ações de acompanhamento pós-serviço para propostas finalizadas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def formatar_data_br(data):
    try:
        if pd.isna(data):
            return "N/A"
        if isinstance(data, str):
            return data
        return pd.to_datetime(data).strftime('%d/%m/%Y')
    except:
        return str(data) if data else "N/A"


def traduzir_tipo_acao(action_type):
    traducoes = {
        'AGRADECIMENTO': '🙏 Agradecimento',
        'MANUTENCAO': '🔧 Manutenção',
        'FOLLOW_UP': '📞 Follow-up',
        'FEEDBACK': '⭐ Feedback',
        'OPORTUNIDADE': '💡 Oportunidade',
        'RETORNO_TECNICO': '🔄 Retorno Técnico'
    }
    return traducoes.get(action_type, action_type)


def traduzir_status(status):
    traducoes = {
        'PENDENTE': '⏳ Pendente',
        'FEITO': '✅ Feito',
        'CANCELADO': '❌ Cancelado',
        'ATIVO': '🟢 Ativo',
        'CONCLUIDO': '✔️ Concluído'
    }
    return traducoes.get(status, status)


CSS = """
<style>
/* Cards de acompanhamento */
.po-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #1E2547;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.po-card-concluido {
    border-left-color: #38A169;
    opacity: 0.85;
}
.po-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
}
.po-cliente {
    font-weight: 700;
    font-size: 0.95rem;
    color: #1a202c;
    margin: 0;
}
.po-proposta {
    font-size: 0.78rem;
    color: #64748b;
    margin: 2px 0 0 0;
}
.po-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.po-badge-ativo { background: #dcfce7; color: #166534; }
.po-badge-concluido { background: #e0e7ff; color: #3730a3; }
.po-proxima {
    font-size: 0.8rem;
    color: #475569;
    margin: 4px 0 0 0;
}
.po-proxima strong { color: #1E2547; }

/* Cards de ação nos detalhes */
.po-acao-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.po-acao-card-feito {
    background: #f0fdf4;
    border-color: #bbf7d0;
}
.po-acao-card-cancelado {
    background: #fafafa;
    border-color: #e5e7eb;
    opacity: 0.65;
}
.po-acao-title {
    font-weight: 700;
    font-size: 0.88rem;
    color: #1a202c;
    margin: 0 0 3px 0;
}
.po-acao-meta {
    font-size: 0.75rem;
    color: #64748b;
    margin: 0;
}
.po-status-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.68rem;
    font-weight: 700;
}
.po-pill-pendente { background: #fef3c7; color: #92400e; }
.po-pill-feito    { background: #dcfce7; color: #166534; }
.po-pill-cancelado{ background: #f3f4f6; color: #6b7280; }

/* Header de detalhes */
.po-detalhe-header {
    background: linear-gradient(135deg, #1E2547 0%, #2E4A99 100%);
    color: white;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.po-detalhe-header h3 { margin: 0; font-size: 1.1rem; font-weight: 700; }
.po-detalhe-header p  { margin: 4px 0 0 0; font-size: 0.82rem; opacity: 0.85; }
</style>
"""


def show():
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<h1 style="font-size:1.8rem;font-weight:700;margin:0 0 1rem 0;">📋 Pós-Organização</h1>', unsafe_allow_html=True)

    tab_lista, tab_detalhes = st.tabs(["📑 Lista de Acompanhamentos", "🔍 Detalhes"])

    # ===== TAB 1: Lista =====
    with tab_lista:
        # Filtro inline compacto
        f1, f2 = st.columns([4, 1])
        with f1:
            filtro_status = st.selectbox(
                "Status:",
                options=["Todos", "ATIVO", "CONCLUIDO"],
                index=0,
                key="filtro_status_pos",
                label_visibility="collapsed"
            )
        with f2:
            if st.button("🔄 Atualizar", key="btn_refresh_pos", use_container_width=True):
                st.rerun()

        status_filter = None if filtro_status == "Todos" else filtro_status
        df_pos_orgs = st.session_state.db.get_post_organizations(status_filter=status_filter)

        if df_pos_orgs.empty:
            st.info("Nenhum acompanhamento encontrado. Quando uma proposta for finalizada, as ações de pós-organização serão criadas automaticamente.")
        else:
            for idx, row in df_pos_orgs.iterrows():
                status = row['status']
                is_concluido = status == 'CONCLUIDO'
                extra_class = "po-card-concluido" if is_concluido else ""
                badge_class = "po-badge-concluido" if is_concluido else "po-badge-ativo"
                badge_text = "Concluído" if is_concluido else "Ativo"

                if row['proxima_acao']:
                    data_acao = formatar_data_br(row['proxima_acao_data'])
                    proxima = f"{traduzir_tipo_acao(row['proxima_acao'])} &nbsp;·&nbsp; 📅 {data_acao}"
                else:
                    proxima = "✅ Todas as ações concluídas"

                col_card, col_btn = st.columns([5, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="po-card {extra_class}">
                        <div class="po-card-header">
                            <div>
                                <p class="po-cliente">👤 {row['cliente_nome']}</p>
                                <p class="po-proposta">Proposta #{row['proposta_numero']}</p>
                            </div>
                            <span class="po-badge {badge_class}">{badge_text}</span>
                        </div>
                        <p class="po-proxima"><strong>Próxima ação:</strong> {proxima}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
                    if st.button("🔍 Detalhes", key=f"btn_detalhes_{row['id']}", use_container_width=True):
                        st.session_state.pos_org_selecionada_id = row['id']
                        st.session_state.pos_org_cliente_nome = row['cliente_nome']
                        st.session_state.pos_org_proposta_numero = row['proposta_numero']
                        st.rerun()

    # ===== TAB 2: Detalhes =====
    with tab_detalhes:
        if 'pos_org_selecionada_id' not in st.session_state or st.session_state.pos_org_selecionada_id is None:
            st.info("Selecione um acompanhamento na aba 'Lista de Acompanhamentos' para ver os detalhes.")
            df_pos_orgs = st.session_state.db.get_post_organizations()
            if not df_pos_orgs.empty:
                opcoes = ["-- Selecione --"] + [
                    f"{row['cliente_nome']} — Proposta #{row['proposta_numero']}"
                    for _, row in df_pos_orgs.iterrows()
                ]
                selecao = st.selectbox("Ou selecione diretamente:", options=opcoes, key="sel_pos_org_direto")
                if selecao != "-- Selecione --":
                    idx = opcoes.index(selecao) - 1
                    row = df_pos_orgs.iloc[idx]
                    st.session_state.pos_org_selecionada_id = row['id']
                    st.session_state.pos_org_cliente_nome = row['cliente_nome']
                    st.session_state.pos_org_proposta_numero = row['proposta_numero']
                    st.rerun()
        else:
            pos_org_id = st.session_state.pos_org_selecionada_id
            cliente_nome = st.session_state.get('pos_org_cliente_nome', 'N/A')
            proposta_numero = st.session_state.get('pos_org_proposta_numero', 'N/A')

            # Header elegante
            st.markdown(f"""
            <div class="po-detalhe-header">
                <h3>👤 {cliente_nome}</h3>
                <p>Proposta #{proposta_numero} &nbsp;·&nbsp; Ações de Acompanhamento Pós-Serviço</p>
            </div>
            """, unsafe_allow_html=True)

            col_back, _ = st.columns([1, 4])
            with col_back:
                if st.button("⬅️ Voltar", key="btn_voltar_lista", use_container_width=True):
                    st.session_state.pos_org_selecionada_id = None
                    st.rerun()

            df_acoes = st.session_state.db.get_post_organization_actions(pos_org_id)

            if df_acoes.empty:
                st.warning("Nenhuma ação encontrada para este acompanhamento.")
            else:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                for idx, acao in df_acoes.iterrows():
                    is_feito = acao['status'] == 'FEITO'
                    is_cancelado = acao['status'] == 'CANCELADO'

                    card_class = "po-acao-card-feito" if is_feito else ("po-acao-card-cancelado" if is_cancelado else "")
                    pill_class = "po-pill-feito" if is_feito else ("po-pill-cancelado" if is_cancelado else "po-pill-pendente")
                    pill_text = "Feito" if is_feito else ("Cancelado" if is_cancelado else "Pendente")

                    col_info, col_check, col_obs = st.columns([3, 1, 3])

                    with col_info:
                        st.markdown(f"""
                        <div class="po-acao-card {card_class}">
                            <p class="po-acao-title">{traduzir_tipo_acao(acao['action_type'])}</p>
                            <p class="po-acao-meta">📅 {formatar_data_br(acao['due_date'])}</p>
                            <span class="po-status-pill {pill_class}">{pill_text}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_check:
                        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
                        novo_status = st.checkbox(
                            "Marcar feito",
                            value=is_feito,
                            key=f"check_acao_{acao['id']}",
                            disabled=is_cancelado
                        )

                    with col_obs:
                        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
                        obs_atual = acao['notes'] if acao['notes'] else ""
                        nova_obs = st.text_input(
                            "Observação",
                            value=obs_atual,
                            key=f"obs_acao_{acao['id']}",
                            label_visibility="collapsed",
                            placeholder="Adicione uma observação...",
                            disabled=is_cancelado
                        )

                    if novo_status != is_feito or nova_obs != obs_atual:
                        new_status = 'FEITO' if novo_status else 'PENDENTE'
                        result = st.session_state.db.update_post_organization_action(
                            action_id=acao['id'],
                            status=new_status,
                            notes=nova_obs if nova_obs else None
                        )
                        if result:
                            if acao['action_type'] == 'FOLLOW_UP' and new_status == 'FEITO':
                                st.session_state.show_retorno_tecnico_modal = True
                                st.session_state.retorno_tecnico_pos_org_id = pos_org_id
                            st.rerun()

                # Modal Retorno Técnico
                if st.session_state.get('show_retorno_tecnico_modal', False):
                    st.markdown("---")
                    st.markdown("""
                    <div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>
                        <p style='font-weight:700;color:#1e40af;margin:0 0 4px 0;'>🔄 Retorno Técnico Necessário?</p>
                        <p style='font-size:0.85rem;color:#1e3a8a;margin:0;'>O Follow-up foi concluído. Há necessidade de ajuste ou visita técnica?</p>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2, _ = st.columns([1.5, 1.5, 4])
                    with c1:
                        if st.button("✅ Sim, agendar", key="btn_sim_retorno", use_container_width=True):
                            st.session_state.agendar_retorno = True
                    with c2:
                        if st.button("❌ Não precisa", key="btn_nao_retorno", use_container_width=True):
                            st.session_state.show_retorno_tecnico_modal = False
                            st.rerun()

                    if st.session_state.get('agendar_retorno', False):
                        data_min = datetime.now().date() + timedelta(days=15)
                        data_max = datetime.now().date() + timedelta(days=30)
                        col_d, col_b = st.columns([2, 1])
                        with col_d:
                            data_retorno = st.date_input(
                                "Data do retorno técnico (entre 15 e 30 dias):",
                                value=data_min,
                                min_value=data_min,
                                max_value=data_max,
                                format="DD/MM/YYYY",
                                key="data_retorno_tecnico"
                            )
                        with col_b:
                            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                            if st.button("💾 Confirmar", key="btn_confirmar_retorno", use_container_width=True, type="primary"):
                                result = st.session_state.db.add_retorno_tecnico_action(
                                    post_organization_id=pos_org_id,
                                    due_date=data_retorno
                                )
                                if result:
                                    st.success(f"Retorno técnico agendado para {formatar_data_br(data_retorno)}")
                                    st.session_state.show_retorno_tecnico_modal = False
                                    st.session_state.agendar_retorno = False
                                    st.rerun()
                                else:
                                    st.error("Erro ao agendar retorno técnico.")
