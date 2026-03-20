"""
Módulo de Pós-Organização
Gerencia ações de acompanhamento pós-serviço para propostas finalizadas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from html import escape as html_escape

# Templates de fallback caso o banco não retorne
TEMPLATES_FALLBACK = {
    'agradecimento':  {'nome': 'Agradecimento',  'dias_apos': 1,  'emoji': '🙏', 'texto': 'Foi um prazer enorme participar desse momento da sua casa, {nome}. Fico feliz que tudo tenha ficado exatamente como você merecia. Qualquer coisa que precisar, estou por aqui. 🤍', 'gratuito': False, 'hint': ''},
    'acompanhamento': {'nome': 'Acompanhamento', 'dias_apos': 7,  'emoji': '📞', 'texto': 'Oi, {nome}! Passando pra saber como você está se sentindo na sua casa depois da organização. Tudo funcionando bem pra você? 😊', 'gratuito': False, 'hint': ''},
    'ajuste_fino':    {'nome': 'Ajuste fino',    'dias_apos': 30, 'emoji': '🔧', 'texto': 'Oi, {nome}! Gosto de voltar depois de algumas semanas para garantir que tudo ainda está funcionando para você — sem custo, faz parte do meu acompanhamento. Posso passar na sua casa essa semana? 🏡', 'gratuito': True, 'hint': 'Esta visita é gratuita e faz parte do seu padrão de atendimento. Não mencione desconto — posicione como cuidado incluído no serviço. É o momento ideal para apresentar o acompanhamento periódico pago no D+60.'},
    'feedback':       {'nome': 'Feedback',        'dias_apos': 45, 'emoji': '💬', 'texto': 'Oi, {nome}! Sua opinião é muito importante pra mim. O que você sentiu de diferença no seu dia a dia depois da organização? Fico feliz em ouvir — mesmo o que ainda pode melhorar. 💬', 'gratuito': False, 'hint': ''},
    'continuidade':   {'nome': 'Continuidade',    'dias_apos': 60, 'emoji': '🤝', 'texto': 'Oi, {nome}! Muitas clientes gostam de manter esse cuidado com a casa de forma contínua — um acompanhamento periódico pra garantir que tudo siga funcionando bem. Se fizer sentido pra você, posso te contar como funciona. 🤝', 'gratuito': False, 'hint': ''},
    'retorno_tecnico':{'nome': 'Retorno Técnico', 'dias_apos': 0,  'emoji': '🔄', 'texto': 'Oi, {nome}! Conforme combinamos, estou passando para agendar nosso retorno técnico. Quando seria um bom momento para você? 🗓️', 'gratuito': False, 'hint': ''},
}


def formatar_data_br(data):
    try:
        if pd.isna(data):
            return "N/A"
        if isinstance(data, str):
            return data
        return pd.to_datetime(data).strftime('%d/%m/%Y')
    except:
        return str(data) if data else "N/A"


OBJETIVOS_ETAPA = {
    'agradecimento':   'Mensagem elegante de encerramento',
    'acompanhamento':  'Saber como a cliente está se sentindo na casa',
    'ajuste_fino':     'Propor pequenos ajustes após uso real',
    'feedback':        'Colher opinião genuína da experiência',
    'continuidade':    'Oferta elegante de serviço contínuo',
    'retorno_tecnico': 'Visita técnica agendada',
}


def get_template(templates, action_type):
    """Retorna info do template para o tipo de ação (case-insensitive)."""
    etapa = (action_type or '').lower().strip()
    t = templates.get(etapa) or TEMPLATES_FALLBACK.get(etapa, {})
    texto = t.get('texto') or ''
    dias_apos = t.get('dias_apos', 0)
    objetivo = OBJETIVOS_ETAPA.get(etapa, '')
    gratuito = t.get('gratuito', False)
    hint = t.get('hint', '')
    return (
        t.get('emoji', '📌'),
        t.get('nome', etapa.replace('_', ' ').title()),
        texto,
        dias_apos,
        objetivo,
        gratuito,
        hint,
    )


CSS = """
<style>
.po-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #1E2547;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.po-card-concluido { border-left-color: #38A169; opacity: 0.85; }
.po-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
}
.po-cliente { font-weight: 700; font-size: 0.95rem; color: #1a202c; margin: 0; }
.po-proposta { font-size: 0.78rem; color: #64748b; margin: 2px 0 0 0; }
.po-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
}
.po-badge-ativo     { background: #dcfce7; color: #166534; }
.po-badge-concluido { background: #e0e7ff; color: #3730a3; }
.po-proxima { font-size: 0.8rem; color: #475569; margin: 4px 0 0 0; }
.po-proxima strong  { color: #1E2547; }

/* Ação card */
.po-acao-wrap {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.po-acao-wrap-feito    { background: #f0fdf4; border-color: #bbf7d0; }
.po-acao-wrap-cancelado{ background: #fafafa; border-color: #e5e7eb; opacity: 0.6; }
.po-acao-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}
.po-acao-title { font-weight: 700; font-size: 0.9rem; color: #1a202c; margin: 0; }
.po-acao-date  { font-size: 0.75rem; color: #64748b; margin: 0 0 8px 0; }
.po-pill {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 12px;
    font-size: 0.68rem;
    font-weight: 700;
}
.po-pill-pendente  { background: #fef3c7; color: #92400e; }
.po-pill-feito     { background: #dcfce7; color: #166534; }
.po-pill-cancelado { background: #f3f4f6; color: #6b7280; }

.po-msg-box {
    background: #f1f5f9;
    border-left: 3px solid #94a3b8;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #334155;
    font-style: italic;
    margin: 8px 0 4px 0;
    line-height: 1.5;
}

/* Header detalhe */
.po-detalhe-header {
    background: linear-gradient(135deg, #1E2547 0%, #2E4A99 100%);
    color: white;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.po-detalhe-header h3 { margin: 0; font-size: 1.1rem; font-weight: 700; }
.po-detalhe-header p  { margin: 4px 0 0 0; font-size: 0.82rem; opacity: 0.85; }

/* Linha de progresso */
.po-progress-bar {
    background: #e2e8f0;
    border-radius: 99px;
    height: 6px;
    margin: 8px 0 4px 0;
    overflow: hidden;
}
.po-progress-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #1E2547, #2E4A99);
}
</style>
"""


def _init_state():
    if 'pos_view' not in st.session_state:
        st.session_state.pos_view = 'lista'
    if 'pos_org_selecionada_id' not in st.session_state:
        st.session_state.pos_org_selecionada_id = None


def _abrir_detalhes(row):
    st.session_state.pos_org_selecionada_id = row['id']
    st.session_state.pos_org_cliente_nome = row['cliente_nome']
    st.session_state.pos_org_proposta_numero = row['proposta_numero']
    st.session_state.pos_view = 'detalhes'


def _view_lista(templates):
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
    df = st.session_state.db.get_post_organizations(status_filter=status_filter)

    if df.empty:
        st.info("Nenhum acompanhamento encontrado. Quando uma proposta for finalizada, as ações de pós-organização serão criadas automaticamente.")
        return

    for _, row in df.iterrows():
        is_concluido = row['status'] == 'CONCLUIDO'
        extra = "po-card-concluido" if is_concluido else ""
        badge_cls = "po-badge-concluido" if is_concluido else "po-badge-ativo"
        badge_txt = "Concluído" if is_concluido else "Ativo"

        if row['proxima_acao']:
            emoji, nome_acao, _, _, _, _, _ = get_template(templates, row['proxima_acao'])
            proxima = f"{emoji} {nome_acao} &nbsp;·&nbsp; 📅 {formatar_data_br(row['proxima_acao_data'])}"
        else:
            proxima = "✅ Todas as ações concluídas"

        col_card, col_btn = st.columns([5, 1])
        with col_card:
            st.markdown(f"""
            <div class="po-card {extra}">
                <div class="po-card-header">
                    <div>
                        <p class="po-cliente">👤 {row['cliente_nome']}</p>
                        <p class="po-proposta">Proposta #{row['proposta_numero']}</p>
                    </div>
                    <span class="po-badge {badge_cls}">{badge_txt}</span>
                </div>
                <p class="po-proxima"><strong>Próxima ação:</strong> {proxima}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
            if st.button("🔍 Ver", key=f"btn_det_{row['id']}", use_container_width=True):
                _abrir_detalhes(row)
                st.rerun()


def _view_detalhes(templates):
    pos_org_id = st.session_state.pos_org_selecionada_id
    cliente_nome = st.session_state.get('pos_org_cliente_nome', 'N/A')
    proposta_numero = st.session_state.get('pos_org_proposta_numero', 'N/A')

    # Header
    st.markdown(f"""
    <div class="po-detalhe-header">
        <h3>👤 {cliente_nome}</h3>
        <p>Proposta #{proposta_numero} &nbsp;·&nbsp; Ações de Acompanhamento Pós-Serviço</p>
    </div>
    """, unsafe_allow_html=True)

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Voltar", key="btn_voltar_lista", use_container_width=True):
            st.session_state.pos_view = 'lista'
            st.session_state.pos_org_selecionada_id = None
            st.rerun()

    df_acoes = st.session_state.db.get_post_organization_actions(pos_org_id)

    if df_acoes.empty:
        st.warning("Nenhuma ação encontrada para este acompanhamento.")
        return

    # Barra de progresso
    total = len(df_acoes[df_acoes['action_type'] != 'retorno_tecnico'])
    feitas = len(df_acoes[(df_acoes['action_type'] != 'retorno_tecnico') & (df_acoes['status'] == 'FEITO')])
    pct = int((feitas / total * 100) if total > 0 else 0)
    st.markdown(f"""
    <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;font-size:0.78rem;color:#64748b;margin-bottom:4px">
            <span>Progresso</span><span>{feitas}/{total} concluídas</span>
        </div>
        <div class="po-progress-bar"><div class="po-progress-fill" style="width:{pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)

    for _, acao in df_acoes.iterrows():
        is_feito = acao['status'] == 'FEITO'
        is_cancelado = acao['status'] == 'CANCELADO'

        emoji, nome_acao, texto_template, dias_apos, objetivo, gratuito, hint = get_template(templates, acao['action_type'])
        nome_safe = html_escape(cliente_nome or 'cliente')
        msg_personalizada = (texto_template or '').replace('{nome}', nome_safe)

        wrap_cls = "po-acao-wrap-feito" if is_feito else ("po-acao-wrap-cancelado" if is_cancelado else "")
        pill_cls = "po-pill-feito" if is_feito else ("po-pill-cancelado" if is_cancelado else "po-pill-pendente")
        pill_txt = "✓ Feito" if is_feito else ("✕ Cancelado" if is_cancelado else "⏳ Pendente")

        dias_badge = f"<span style='background:#e2e8f0;color:#475569;padding:2px 8px;border-radius:10px;font-size:0.68rem;font-weight:700;margin-left:6px;'>D+{dias_apos}</span>" if dias_apos else ""
        objetivo_html = f"<p style='font-size:0.75rem;color:#94a3b8;margin:2px 0 0 0;font-style:italic;'>{objetivo}</p>" if objetivo else ""
        
        # Badge "Gratuito" para ajuste fino
        gratuito_badge = "<span style='background:#d4edda;color:#155724;padding:2px 8px;border-radius:10px;font-size:0.68rem;font-weight:700;margin-left:4px;'>💚 Gratuito</span>" if gratuito else ""

        st.markdown(f'<div class="po-acao-wrap {wrap_cls}"><div class="po-acao-header"><span style="font-size:1.2rem">{emoji}</span><p class="po-acao-title">{nome_acao}</p>{dias_badge}{gratuito_badge}<span class="po-pill {pill_cls}">{pill_txt}</span></div>{objetivo_html}<p class="po-acao-date">📅 Prevista para {formatar_data_br(acao["due_date"])}</p><div class="po-msg-box">{msg_personalizada}</div></div>', unsafe_allow_html=True)

        # Controles abaixo do card
        col_check, col_obs = st.columns([1, 3])

        with col_check:
            novo_status = st.checkbox(
                "Marcar como feito",
                value=is_feito,
                key=f"check_acao_{acao['id']}",
                disabled=is_cancelado
            )

        with col_obs:
            obs_atual = acao['notes'] if acao['notes'] else ""
            nova_obs = st.text_input(
                "Observação",
                value=obs_atual,
                key=f"obs_acao_{acao['id']}",
                label_visibility="collapsed",
                placeholder="Observação...",
                disabled=is_cancelado
            )
        
        # Exibir hint estratégico se disponível
        if hint and not is_cancelado:
            st.markdown(f'<div style="background:#f0f4ff;border-left:3px solid #6366f1;padding:10px 12px;margin:8px 0;border-radius:4px"><p style="margin:0;font-size:0.85rem;color:#4f46e5;font-weight:600">💡 Dica estratégica:</p><p style="margin:4px 0 0 0;font-size:0.8rem;color:#4338ca">{hint}</p></div>', unsafe_allow_html=True)

        # Salvar mudanças
        if novo_status != is_feito or nova_obs != obs_atual:
            new_status = 'FEITO' if novo_status else 'PENDENTE'
            result = st.session_state.db.update_post_organization_action(
                action_id=acao['id'],
                status=new_status,
                notes=nova_obs if nova_obs else None
            )
            if result:
                if acao['action_type'] == 'acompanhamento' and new_status == 'FEITO':
                    st.session_state.show_retorno_tecnico_modal = True
                    st.session_state.retorno_tecnico_pos_org_id = pos_org_id
                st.rerun()

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Modal Retorno Técnico
    if st.session_state.get('show_retorno_tecnico_modal', False):
        st.markdown("---")
        st.markdown("""
        <div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>
            <p style='font-weight:700;color:#1e40af;margin:0 0 4px 0;'>🔄 Retorno Técnico Necessário?</p>
            <p style='font-size:0.85rem;color:#1e3a8a;margin:0;'>O acompanhamento foi concluído. Há necessidade de ajuste ou visita técnica?</p>
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


def show():
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Pós-Organização</h1>', unsafe_allow_html=True)
    _init_state()

    # Carrega templates uma vez
    templates = st.session_state.db.get_post_org_templates()

    if st.session_state.pos_view == 'detalhes' and st.session_state.pos_org_selecionada_id:
        _view_detalhes(templates)
    else:
        _view_lista(templates)
