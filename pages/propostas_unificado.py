import streamlit as st
import logging
logging.basicConfig(level=logging.INFO)
from utils.finalizar_proposta_v2 import finalizar_proposta_v2
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import uuid
import plotly.graph_objects as go
import html as html_module
from utils.database import Fornecedor
from utils.propostas_helper import st_gerar_pdf_cliente, st_gerar_pdf_interno, st_gerar_pdf_fornecedores, gerar_pdf_proposta
from streamlit_extras.stylable_container import stylable_container


def _safe_float(val, default=0.0):
    try:
        if pd.isna(val) or val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


from utils.currency_formatter import fmt_brl as _fmt_brl


def _render_nova_proposta_form(clientes):
    tipo_cadastro = st.radio(
        "Tipo de cadastro:",
        ["Nova proposta", "Cadastro retroativo"],
        horizontal=True,
        key="tipo_cadastro_nova"
    )

    with st.form(key="nova_proposta_form"):
        clientes_lista = clientes['nome'].tolist()
        cliente = st.selectbox("Cliente:", clientes_lista)
        descricao = st.text_area("Descrição do serviço:", height=100)
        valor = st.number_input("Valor do serviço (R$):", min_value=0.0, format="%.2f")
        prazo = st.number_input("Prazo estimado (dias):", min_value=1, value=15)

        data_inicio = datetime.now().date()
        status_inicial = "Aguardando"
        gerar_financeiro = False

        if tipo_cadastro == "Nova proposta":
            data_inicio = st.date_input("Data de início prevista:", datetime.now().date(), format="DD/MM/YYYY")
            status_opcoes = ["Aguardando", "Aprovada", "Recusada"]
            status_inicial = st.selectbox("Status inicial da proposta:", status_opcoes, index=0)
        else:
            data_inicio = st.date_input("Data de início:", datetime.now().date() - timedelta(days=30), format="DD/MM/YYYY")
            status_opcoes = ["Aguardando", "Aprovada", "Recusada", "Em execução", "Finalizada"]
            status_inicial = st.selectbox("Status da proposta:", status_opcoes)

            data_aprovacao = data_inicio
            data_inicio_execucao = data_inicio
            data_fim_real = data_inicio + timedelta(days=prazo)
            status_pagamento = "Pendente"

            if status_inicial in ["Aprovada", "Em execução", "Finalizada"]:
                data_aprovacao = st.date_input("Data de aprovação:", data_inicio, format="DD/MM/YYYY")
            if status_inicial in ["Em execução", "Finalizada"]:
                st.info("A data de início de execução será igual à data de início da proposta.")
                data_inicio_execucao = data_inicio
            if status_inicial == "Finalizada":
                data_fim_real = st.date_input("Data de conclusão:", data_inicio + timedelta(days=prazo), format="DD/MM/YYYY")
            if status_inicial in ["Aprovada", "Finalizada"]:
                status_pagamento = st.selectbox("Status de pagamento:", ["Pendente", "Parcial", "Pago"])

            gerar_financeiro = st.checkbox("Gerar lançamentos financeiros", value=True)

        data_fim = data_inicio + timedelta(days=prazo)
        st.info(f"Data de término prevista: {data_fim.strftime('%d/%m/%Y')}")

        tipo_proposta = st.selectbox(
            "Tipo de Proposta:",
            ["Organização", "Consultoria", "Acompanhamento", "Projeto", "Outro"]
        )

        submitted = st.form_submit_button("SALVAR PROPOSTA", type="primary", use_container_width=True)

        if submitted:
            try:
                cliente_id = clientes[clientes['nome'] == cliente]['id'].iloc[0]

                status_proposta_mapeado = status_inicial
                if status_inicial == "Aguardando":
                    status_proposta_mapeado = "Em elaboração"
                elif status_inicial == "Recusada":
                    status_proposta_mapeado = "Finalizada"

                if tipo_cadastro == "Nova proposta":
                    gerar_transacoes = status_inicial == "Aprovada"
                else:
                    gerar_transacoes = gerar_financeiro

                novo_numero = st.session_state.db.add_proposta(
                    cliente_id=cliente_id,
                    descricao=descricao,
                    valor=valor,
                    status=status_proposta_mapeado,
                    tipo_proposta=tipo_proposta,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    previsao_dias=prazo,
                    prazo_entrega=data_inicio,
                    gerar_transacoes_automaticas=gerar_transacoes
                )

                if novo_numero:
                    proposta_atualizada = {}

                    if status_inicial in ["Aprovada", "Em execução", "Finalizada"]:
                        if tipo_cadastro == "Cadastro retroativo" and 'data_aprovacao' in locals():
                            proposta_atualizada['data_aprovacao'] = data_aprovacao
                            proposta_atualizada['data_proposta'] = data_aprovacao
                        else:
                            proposta_atualizada['data_aprovacao'] = data_inicio
                            proposta_atualizada['data_proposta'] = data_inicio

                    if status_inicial in ["Em execução", "Finalizada"]:
                        proposta_atualizada['data_inicio_execucao'] = data_inicio
                        proposta_atualizada['status_execucao'] = "Em execução"

                    if status_inicial == "Finalizada":
                        if tipo_cadastro == "Cadastro retroativo" and 'data_fim_real' in locals():
                            proposta_atualizada['data_fim'] = data_fim_real
                        else:
                            proposta_atualizada['data_fim'] = data_fim
                        proposta_atualizada['status_execucao'] = "Concluída"

                    if status_inicial in ["Aprovada", "Finalizada"] and tipo_cadastro == "Cadastro retroativo" and 'status_pagamento' in locals():
                        proposta_atualizada['status_pagamento_base'] = status_pagamento

                    if status_inicial == "Recusada":
                        proposta_atualizada['status_execucao'] = "Cancelada"
                        proposta_atualizada['data_fim'] = datetime.now().date()

                    if proposta_atualizada:
                        st.session_state.db.update_proposta(novo_numero, **proposta_atualizada)

                    st.success(f"Proposta #{novo_numero} criada com sucesso!")
                    st.session_state['kanban_nova_proposta_open'] = False
                    st.rerun()
                else:
                    st.error("Erro ao salvar proposta.")
            except Exception as e:
                st.error(f"Erro ao salvar proposta: {str(e)}")


def _render_detail_panel(proposta_id, proposta, propostas_com_clientes):
    """Renders the full detail panel for a selected proposal."""
    nome_cliente = proposta.get('nome', proposta.get('cliente_nome', 'Cliente'))
    numero = proposta.get('numero', proposta_id)
    status_atual = proposta.get('status', '')
    em_aberto = status_atual in ['Em elaboração', 'Aguardando aprovação', 'Aguardando']
    aprovada_parada = status_atual == 'Aprovada'

    st.markdown(f"### Proposta #{numero} — {nome_cliente}")
    st.caption(proposta.get('descricao', '')[:120])

    finalizada = status_atual in ['Finalizada', 'Recusada']

    if em_aberto or aprovada_parada:
        _render_open_proposal_actions(proposta_id, proposta)
    elif finalizada:
        _render_finalized_proposal_actions(proposta_id, proposta)
    else:
        _tab_itens(proposta_id, show_finalizar=True)


def _render_open_proposal_actions(proposta_id, proposta):
    """Compact action bar for open/approved proposals not yet in execution."""
    valor = _safe_float(proposta.get('valor'))
    status_atual = proposta.get('status', '')
    data_str = ""
    d = proposta.get('data_inicio')
    if d:
        try:
            data_str = d.strftime("%d/%m/%Y") if hasattr(d, 'strftime') else str(d)[:10]
        except Exception:
            data_str = str(d)[:10]

    if status_atual == 'Aprovada':
        badge_label, badge_bg = "Aprovada", "#1D6A4A"
    else:
        badge_label, badge_bg = "Em Aberto", "#B7860D"

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;padding:12px 16px;
                background:#faf9f7;border-radius:10px;border:1px solid #e8e5df;margin-bottom:14px;">
      <span style="background:{badge_bg};color:#fff;font-size:11px;font-weight:700;
                   padding:3px 10px;border-radius:12px;white-space:nowrap;">{badge_label}</span>
      <span style="font-size:13px;color:#0D1B2A;font-weight:600;">{_fmt_brl(valor)}</span>
      {"<span style='font-size:12px;color:#8B8680;'>" + data_str + "</span>" if data_str else ""}
    </div>""", unsafe_allow_html=True)

    if status_atual == 'Aprovada':
        if st.button("▶️ Iniciar Execução", key=f"btn_iniciar_{proposta_id}", use_container_width=True, type="primary"):
            try:
                res = st.session_state.db.update_proposta_status(proposta_id=proposta_id,
                      novo_status="Em execução", data_aprovacao=proposta.get('data_aprovacao') or datetime.now().date())
                if res.get('status', False):
                    st.session_state['kanban_selected_proposta'] = None
                    st.rerun()
                else:
                    st.error(res.get('message', 'Erro ao iniciar.'))
            except Exception as e:
                st.error(str(e))
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Aprovar", key=f"btn_aprovar_{proposta_id}", use_container_width=True, type="primary"):
                try:
                    res = st.session_state.db.update_proposta_status(proposta_id=proposta_id,
                          novo_status="Aprovada", data_aprovacao=datetime.now().date())
                    if res.get('status', False):
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state.db.invalidar_cache()
                        st.rerun()
                    else:
                        st.error(res.get('message', 'Erro ao aprovar.'))
                except Exception as e:
                    st.error(str(e))
        with c2:
            if st.button("❌ Recusar", key=f"btn_recusar_{proposta_id}", use_container_width=True):
                try:
                    from sqlalchemy import text as sa_text
                    from utils.database import engine
                    with engine.connect() as conn:
                        conn.execute(sa_text(
                            "UPDATE propostas SET status = 'Recusada', status_execucao = 'Cancelada' WHERE id = :pid"
                        ), {"pid": proposta_id})
                        conn.commit()
                    st.session_state['kanban_selected_proposta'] = None
                    st.session_state.db.invalidar_cache()
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        c3, c4 = st.columns(2)
        with c3:
            if st.button("📄 Gerar Proposta", key=f"btn_pdf_proposta_{proposta_id}", use_container_width=True):
                try:
                    sucesso, mensagem, arquivo = gerar_pdf_proposta(db=st.session_state.db, proposta_id=proposta_id)
                    if sucesso and arquivo:
                        with open(arquivo, "rb") as f:
                            st.success("PDF gerado!")
                            st.download_button("📥 Baixar", f.read(), f"Proposta_{proposta_id}.pdf",
                                               "application/pdf", key=f"dl_proposta_{proposta_id}", use_container_width=True)
                    else:
                        st.error(f"Erro: {mensagem}")
                except Exception as e:
                    st.error(str(e))
        with c4:
            if st.button("🗑️ Excluir", key=f"btn_excluir_open_{proposta_id}", use_container_width=True):
                st.session_state[f"confirm_delete_{proposta_id}"] = True

        if st.session_state.get(f"confirm_delete_{proposta_id}", False):
            st.warning("Esta ação é permanente e removerá todos os dados relacionados.")
            dc1, dc2, dc3 = st.columns([2, 1, 1])
            with dc2:
                if st.button("Cancelar", key=f"btn_cancel_del_{proposta_id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{proposta_id}"] = False
                    st.rerun()
            with dc3:
                if st.button("Confirmar", key=f"btn_confirm_del_{proposta_id}", use_container_width=True, type="primary"):
                    try:
                        from sqlalchemy import text
                        from utils.database import engine
                        with engine.connect() as conn:
                            po_ids = conn.execute(text(f"SELECT id FROM post_organizations WHERE proposta_id = {proposta_id}")).fetchall()
                            if po_ids:
                                po_id_list = ",".join(str(r[0]) for r in po_ids)
                                conn.execute(text(f"DELETE FROM post_organization_actions WHERE post_organization_id IN ({po_id_list})"))
                            for tbl in ["post_organizations", "vendas", "financeiro", "acrescimos_proposta", "produtos_organizadores", "andamento_propostas"]:
                                conn.execute(text(f"DELETE FROM {tbl} WHERE proposta_id = {proposta_id}"))
                            conn.execute(text(f"DELETE FROM propostas WHERE id = {proposta_id}"))
                            conn.commit()
                        st.success(f"Proposta #{proposta_id} excluída.")
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state[f"confirm_delete_{proposta_id}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


def _render_finalized_proposal_actions(proposta_id, proposta):
    """Compact view for finalized proposals: report buttons + reopen/delete."""
    nome_cliente = proposta.get('nome', proposta.get('cliente_nome', 'Cliente'))
    numero = proposta.get('numero', proposta_id)
    valor = _safe_float(proposta.get('valor'))
    status_atual = proposta.get('status', '')

    if status_atual == 'Recusada':
        badge_label, badge_bg = "Recusada", "#C0392B"
    else:
        badge_label, badge_bg = "Finalizada", "#4A4A4A"

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;padding:12px 16px;
                background:#faf9f7;border-radius:10px;border:1px solid #e8e5df;margin-bottom:14px;">
      <span style="background:{badge_bg};color:#fff;font-size:11px;font-weight:700;
                   padding:3px 10px;border-radius:12px;white-space:nowrap;">{badge_label}</span>
      <span style="font-size:13px;color:#0D1B2A;font-weight:600;">{_fmt_brl(valor)}</span>
    </div>""", unsafe_allow_html=True)

    rc1, rc2 = st.columns(2)
    with rc1:
        _report_card_download("📋", "RELATÓRIO CLIENTE", "Proposta de serviço", proposta_id, "cliente", nome_cliente, numero)
    with rc2:
        _report_card_download("📊", "RELATÓRIO INTERNO", "Margens e custos", proposta_id, "interno", nome_cliente, numero)

    rc3, rc4 = st.columns(2)
    with rc3:
        _report_card_download("🏢", "RELATÓRIO FORNECEDORES", "Lista de terceiros", proposta_id, "fornecedores", nome_cliente, numero)
    with rc4:
        _report_card_download("📦", "VENDAS DO PRODUTO", "Produtos organizados", proposta_id, "vendas", nome_cliente, numero)

    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button("🔄 Reabrir", key=f"btn_reabrir_fin_{proposta_id}", use_container_width=True):
            st.session_state[f"confirm_reopen_{proposta_id}"] = True
    with ac2:
        if st.button("🗑️ Excluir", key=f"btn_excluir_fin_{proposta_id}", use_container_width=True):
            st.session_state[f"confirm_delete_{proposta_id}"] = True

    if st.session_state.get(f"confirm_reopen_{proposta_id}", False):
        st.warning("A proposta voltará para o status 'Em execução'.")
        ro1, ro2, ro3 = st.columns([2, 1, 1])
        with ro2:
            if st.button("Cancelar", key=f"btn_cancel_reopen_{proposta_id}", use_container_width=True):
                st.session_state[f"confirm_reopen_{proposta_id}"] = False
                st.rerun()
        with ro3:
            if st.button("Confirmar", key=f"btn_confirm_reopen_{proposta_id}", use_container_width=True, type="primary"):
                try:
                    from reabrir_proposta import reabrir_proposta_finalizada
                    res = reabrir_proposta_finalizada(proposta_id)
                    if res.get('status') in ['sucesso', 'sucesso_com_alerta']:
                        st.success(res.get('mensagem'))
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state[f"confirm_reopen_{proposta_id}"] = False
                        st.rerun()
                    else:
                        st.error(res.get('mensagem'))
                except Exception as e:
                    st.error(str(e))

    if st.session_state.get(f"confirm_delete_{proposta_id}", False):
        st.warning("Esta ação é permanente e removerá todos os dados relacionados.")
        dc1, dc2, dc3 = st.columns([2, 1, 1])
        with dc2:
            if st.button("Cancelar", key=f"btn_cancel_del_fin_{proposta_id}", use_container_width=True):
                st.session_state[f"confirm_delete_{proposta_id}"] = False
                st.rerun()
        with dc3:
            if st.button("Confirmar", key=f"btn_confirm_del_fin_{proposta_id}", use_container_width=True, type="primary"):
                try:
                    from sqlalchemy import text
                    from utils.database import engine
                    with engine.connect() as conn:
                        po_ids = conn.execute(text(f"SELECT id FROM post_organizations WHERE proposta_id = {proposta_id}")).fetchall()
                        if po_ids:
                            po_id_list = ",".join(str(r[0]) for r in po_ids)
                            conn.execute(text(f"DELETE FROM post_organization_actions WHERE post_organization_id IN ({po_id_list})"))
                        for tbl in ["post_organizations", "vendas", "financeiro", "acrescimos_proposta", "produtos_organizadores", "andamento_propostas"]:
                            conn.execute(text(f"DELETE FROM {tbl} WHERE proposta_id = {proposta_id}"))
                        conn.execute(text(f"DELETE FROM propostas WHERE id = {proposta_id}"))
                        conn.commit()
                    st.success(f"Proposta #{proposta_id} excluída.")
                    st.session_state['kanban_selected_proposta'] = None
                    st.session_state[f"confirm_delete_{proposta_id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


def _report_card_download(icon, title, subtitle, proposta_id, report_type, nome_cliente="Cliente", numero_proposta=None):
    """Render a navy card-styled download button that generates and downloads PDF on click."""
    pdf_bytes = None
    file_name = f"Relatorio_{report_type}_{proposta_id}.pdf"
    error_msg = None

    try:
        if report_type == "cliente":
            from utils.propostas_helper import gerar_pdf_cliente_proposta
            sucesso, mensagem, filename = gerar_pdf_cliente_proposta(st.session_state.db, proposta_id)
            if sucesso and filename:
                with open(filename, "rb") as f:
                    pdf_bytes = f.read()
                file_name = os.path.basename(filename)
            else:
                error_msg = mensagem
        elif report_type == "interno":
            from utils.propostas_helper import gerar_pdf_interno_proposta
            sucesso, mensagem, filename = gerar_pdf_interno_proposta(st.session_state.db, proposta_id)
            if sucesso and filename:
                with open(filename, "rb") as f:
                    pdf_bytes = f.read()
                file_name = os.path.basename(filename)
            else:
                error_msg = mensagem
        elif report_type == "fornecedores":
            from utils.propostas_helper import gerar_pdf_fornecedores_proposta
            sucesso, mensagem, filename = gerar_pdf_fornecedores_proposta(st.session_state.db, proposta_id)
            if sucesso and filename:
                with open(filename, "rb") as f:
                    pdf_bytes = f.read()
                file_name = os.path.basename(filename)
            else:
                error_msg = mensagem
        elif report_type == "vendas":
            import time as _t
            from utils.pdf_generator_v2 import gerar_pdf_venda_v2
            produtos = st.session_state.db.get_produtos_organizadores(proposta_id)
            if produtos is None or (hasattr(produtos, 'empty') and produtos.empty):
                error_msg = "Nenhum produto cadastrado."
            else:
                val_col = 'valor_unit' if 'valor_unit' in produtos.columns else 'valor'
                valor_total = float(produtos[val_col].astype(float).mul(produtos['quantidade'].astype(float)).sum())
                num_exibir = numero_proposta or proposta_id
                venda_dados = {'id': num_exibir, 'status': 'Proposta', 'forma_pagamento': 'N/A',
                               'valor_total': round(valor_total, 2),
                               'data_venda': datetime.now().strftime('%d/%m/%Y'),
                               'observacoes': f"Produtos Proposta #{num_exibir} - {nome_cliente}"}
                rename_map = {'nome': 'produto_nome', val_col: 'preco_unitario'}
                itens_pdf = produtos.rename(columns=rename_map)[['produto_nome', 'quantidade', 'preco_unitario']].copy()
                ts = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(int(_t.time()))
                fname = f"pdfs/Venda_Proposta_{num_exibir}_{ts}.pdf"
                os.makedirs("pdfs", exist_ok=True)
                pdf_path = gerar_pdf_venda_v2(venda_dados, {'nome': nome_cliente}, itens_pdf, fname)
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    file_name = f"Produtos_Proposta_{num_exibir}.pdf"
                else:
                    error_msg = "Erro ao gerar PDF de vendas."
    except Exception as e:
        error_msg = str(e)

    if pdf_bytes:
        import base64
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f"""
        <a href="data:application/pdf;base64,{b64}" download="{file_name}"
           style="text-decoration:none;display:block;">
          <div style="background:#0D1B2A;border-radius:10px;padding:16px;text-align:center;min-height:80px;
                      display:flex;flex-direction:column;align-items:center;justify-content:center;
                      cursor:pointer;transition:all 0.2s;border:1px solid transparent;"
               onmouseover="this.style.background='#162840';this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)'"
               onmouseout="this.style.background='#0D1B2A';this.style.transform='none';this.style.boxShadow='none'">
            <div style="font-size:22px;">{icon}</div>
            <div style="color:#C9A84C;font-weight:700;font-size:12px;margin-top:4px;">{title}</div>
            <div style="color:#aaa;font-size:10px;">{subtitle}</div>
          </div>
        </a>""", unsafe_allow_html=True)
    elif error_msg:
        st.markdown(f"""
        <div style="background:#0D1B2A;border-radius:10px;padding:16px;text-align:center;min-height:80px;
                    display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0.6;">
          <div style="font-size:22px;">{icon}</div>
          <div style="color:#C9A84C;font-weight:700;font-size:12px;margin-top:4px;">{title}</div>
          <div style="color:#ff6b6b;font-size:10px;">{error_msg}</div>
        </div>""", unsafe_allow_html=True)


def _tab_detalhes(proposta_id, proposta):
    # ── Barra de progresso ────────────────────────────────────────────────
    hoje = datetime.now().date()
    data_inicio_exec = proposta.get('data_inicio_execucao') or proposta.get('data_inicio')
    if data_inicio_exec is None:
        data_inicio_exec = hoje - timedelta(days=1)
    data_fim_prevista = proposta.get('data_fim')
    if data_fim_prevista is None:
        data_fim_prevista = data_inicio_exec + timedelta(days=30)

    try:
        total_dias = max(1, (data_fim_prevista - data_inicio_exec).days)
        dias_decorridos = (hoje - data_inicio_exec).days
        progresso = min(100, max(0, int(dias_decorridos / total_dias * 100)))
        dias_restantes = max(0, (data_fim_prevista - hoje).days)
        atrasado = hoje > data_fim_prevista
        cor_prog = "#C0392B" if atrasado else "#1D6A4A"
        label_prog = (f"⚠️ Atrasado em {(hoje - data_fim_prevista).days} dias"
                      if atrasado else f"📅 {dias_restantes} dias restantes")
        st.markdown(f"""
        <div style="background:#f7f7f5;border-radius:10px;padding:14px 18px;margin-bottom:18px;border:1px solid #e8e6e0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-weight:600;color:#0D1B2A;font-size:13px;">Progresso do Prazo</span>
            <span style="font-size:13px;color:{cor_prog};font-weight:600;">{label_prog}</span>
          </div>
          <div style="background:#e8e6e0;border-radius:6px;height:10px;overflow:hidden;">
            <div style="background:{cor_prog};width:{progresso}%;height:100%;border-radius:6px;transition:width .3s;"></div>
          </div>
          <div style="margin-top:6px;font-size:12px;color:#9a9890;">{progresso}% — {dias_decorridos} de {total_dias} dias</div>
        </div>""", unsafe_allow_html=True)
    except (TypeError, AttributeError):
        pass

    # ── Formulário novo andamento ─────────────────────────────────────────
    st.markdown('<p style="font-weight:600;color:#0D1B2A;font-size:14px;margin-bottom:4px;">📝 Novo Andamento</p>', unsafe_allow_html=True)
    with st.form(key=f"form_andamento_{proposta_id}"):
        descricao_andamento = st.text_area("Descrição:", height=90, placeholder="Descreva o que aconteceu nesta etapa…", label_visibility="collapsed")
        submitted = st.form_submit_button("✔ Registrar Andamento", type="primary", use_container_width=True)
        if submitted:
            if descricao_andamento:
                try:
                    resultado = st.session_state.db.add_andamento_proposta(
                        proposta_id=proposta_id, status="Em andamento", observacao=descricao_andamento)
                    if resultado:
                        st.success("Andamento registrado!")
                        st.rerun()
                    else:
                        st.error("Erro ao registrar andamento.")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
            else:
                st.warning("Insira uma descrição.")

    # ── Histórico de andamentos ───────────────────────────────────────────
    try:
        andamentos = st.session_state.db.get_andamentos_proposta(proposta_id)
        if not andamentos.empty:
            st.markdown('<p style="font-weight:600;color:#0D1B2A;font-size:14px;margin:16px 0 8px;">🕐 Histórico</p>', unsafe_allow_html=True)
            cards = ""
            for _, a in andamentos.iterrows():
                texto = html_module.escape(str(a.get('observacao') or a.get('descricao') or 'Sem descrição'))
                data_and = a.get('data')
                data_str = data_and.strftime('%d/%m/%Y') if pd.notna(data_and) and data_and else '—'
                cards += f"""
                <div style="border-left:3px solid #C9A84C;background:#fff;border-radius:0 8px 8px 0;
                            padding:10px 14px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.06);">
                  <div style="font-size:13px;color:#1C1C1A;">{texto}</div>
                  <div style="font-size:11px;color:#9a9890;margin-top:4px;">📅 {data_str}</div>
                </div>"""
            st.markdown(cards, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar andamentos: {str(e)}")


def _tab_produtos(proposta_id):
    # ── Lista atual de produtos ───────────────────────────────────────────
    try:
        produtos_proposta_raw = st.session_state.db.get_produtos_organizadores(proposta_id=proposta_id)
        if not produtos_proposta_raw.empty:
            produtos_proposta = produtos_proposta_raw.rename(columns={'valor': 'valor_unit'})
            produtos_proposta['valor_total'] = produtos_proposta['valor_unit'] * produtos_proposta['quantidade']
            valor_total_produtos = produtos_proposta['valor_total'].sum()

            # Métricas resumo
            c1, c2 = st.columns(2)
            c1.metric("Itens adicionados", len(produtos_proposta))
            c2.metric("Total produtos", _fmt_brl(valor_total_produtos))

            # Cards dos itens
            cards = ""
            for _, p in produtos_proposta.iterrows():
                nome = html_module.escape(str(p.get('nome', '')))
                comodo = html_module.escape(str(p.get('comodo') or 'Geral'))
                qty = int(p.get('quantidade', 1))
                vunit = float(p.get('valor_unit', 0))
                vtot = float(p.get('valor_total', 0))
                vunit_str = _fmt_brl(vunit)
                vtot_str  = _fmt_brl(vtot)
                cards += f"""
                <div style="border-left:3px solid #C9A84C;background:#fff;border-radius:0 8px 8px 0;
                            padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);
                            display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <span style="font-weight:600;color:#0D1B2A;font-size:13px;">{nome}</span>
                    <span style="font-size:11px;color:#9a9890;margin-left:8px;">📦 {comodo}</span>
                  </div>
                  <div style="text-align:right;white-space:nowrap;">
                    <span style="font-size:11px;color:#9a9890;">{qty}× {vunit_str}</span><br>
                    <span style="font-weight:700;color:#1D6A4A;font-size:13px;">{vtot_str}</span>
                  </div>
                </div>"""
            st.markdown(cards, unsafe_allow_html=True)

            # Remover produto
            with st.expander("🗑️ Remover produto"):
                with st.form(key=f"form_remover_produto_{proposta_id}"):
                    produto_remover_id = st.selectbox(
                        "Selecione:",
                        options=produtos_proposta['id'].tolist(),
                        format_func=lambda x: produtos_proposta.loc[produtos_proposta['id'] == x, 'nome'].iloc[0],
                        key=f"select_remover_produto_{proposta_id}"
                    )
                    if st.form_submit_button("Remover", type="primary", use_container_width=True):
                        try:
                            if st.session_state.db.remove_produto_organizador(produto_remover_id):
                                st.success("Produto removido!")
                            else:
                                st.error("Falha ao remover.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

            # PDF dos produtos
            st.markdown("---")
            if st.button("📄 Gerar Relatório de Venda dos Produtos", use_container_width=True, key=f"btn_pdf_produtos_proposta_{proposta_id}"):
                try:
                    from utils.pdf_generator_v2 import gerar_pdf_venda_v2
                    from sqlalchemy import text as _text
                    import time as _t
                    _prop_row = st.session_state.db.session.execute(
                        _text("SELECT p.numero, c.nome FROM propostas p LEFT JOIN clientes c ON p.cliente_id = c.id WHERE p.id = :pid"),
                        {"pid": proposta_id}
                    ).fetchone()
                    _num_prop = _prop_row[0] if _prop_row else proposta_id
                    _nome_cl = _prop_row[1] if _prop_row and _prop_row[1] else "Cliente"
                    venda_dados = {'id': _num_prop, 'status': 'Proposta', 'forma_pagamento': 'N/A',
                                   'valor_total': round(float(valor_total_produtos), 2),
                                   'data_venda': datetime.now().strftime('%d/%m/%Y'), 'observacoes': f"Produtos Proposta #{_num_prop} - {_nome_cl}"}
                    itens_pdf = produtos_proposta.rename(columns={'nome': 'produto_nome', 'valor_unit': 'preco_unitario'})[['produto_nome', 'quantidade', 'preco_unitario']].copy()
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(int(_t.time()))
                    filename = f"pdfs/Venda_Proposta_{_num_prop}_{ts}.pdf"
                    os.makedirs("pdfs", exist_ok=True)
                    pdf_path = gerar_pdf_venda_v2(venda_dados, {'nome': _nome_cl}, itens_pdf, filename)
                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            st.success("PDF gerado!")
                            st.download_button("📥 Baixar PDF", f.read(), f"Produtos_Proposta_{proposta_id}.pdf",
                                               "application/pdf", use_container_width=True,
                                               key=f"dl_pdf_venda_proposta_{proposta_id}")
                    else:
                        st.error("Erro ao gerar PDF.")
                except Exception as e:
                    st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon">📦</div>
              <div class="itens-empty-title">Nenhum produto ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir produtos</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {str(e)}")

    st.markdown('<p style="font-weight:600;color:#0D1B2A;font-size:14px;margin-bottom:4px;">➕ Adicionar Produto</p>', unsafe_allow_html=True)
    with st.form(key=f"form_produto_{proposta_id}"):
        produtos_cadastrados = st.session_state.db.get_produtos()
        if not produtos_cadastrados.empty:
            opcoes_produtos = produtos_cadastrados['id'].tolist()
            def format_produto_option(pid):
                p = produtos_cadastrados.loc[produtos_cadastrados['id'] == pid]
                if not p.empty:
                    return f"{p['nome'].iloc[0]} — R$ {float(p['preco_venda'].iloc[0]):.2f}"
                return "?"
            produto_selecionado_id = st.selectbox("Produto:", options=opcoes_produtos,
                                                   format_func=format_produto_option,
                                                   key=f"select_produto_{proposta_id}")
            produto = produtos_cadastrados.loc[produtos_cadastrados['id'] == produto_selecionado_id].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                comodo = st.text_input("Cômodo/Área:")
            with col2:
                preco_padrao = float(produto['preco_venda'])
                usar_preco_padrao = st.checkbox("Usar preço padrão", value=True)
                if not usar_preco_padrao:
                    valor_unitario = st.number_input("Preço (R$):", min_value=0.0, value=preco_padrao, format="%.2f")
                else:
                    valor_unitario = preco_padrao
                    st.write(f"Preço: R$ {preco_padrao:.2f}")
            if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
                try:
                    st.session_state.db.add_produto_organizador(proposta_id=proposta_id, nome=produto['nome'],
                        descricao=produto['descricao'], valor=valor_unitario, quantidade=quantidade,
                        comodo=comodo if comodo else "Geral")
                    st.success(f"'{produto['nome']}' adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.warning("Nenhum produto cadastrado. Adicione em Cadastros > Produtos.")
            st.form_submit_button("ADICIONAR", disabled=True)


def _tab_itens(proposta_id, show_finalizar=False):
    """Itens & Custos com navegação lateral por categoria."""

    try:
        produtos_df     = st.session_state.db.get_produtos_organizadores(proposta_id)
        fornecedores_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
        assistentes_df  = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
        outros_df       = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")
    except Exception as e:
        st.error(f"Erro ao carregar itens: {e}"); return

    t_prod  = (produtos_df['valor'] * produtos_df['quantidade']).sum() if not produtos_df.empty else 0
    t_forn  = fornecedores_df['valor'].sum() if not fornecedores_df.empty else 0
    t_asst  = assistentes_df['valor'].sum() if not assistentes_df.empty else 0
    t_outr  = outros_df['valor'].sum() if not outros_df.empty else 0
    t_total = t_prod + t_forn + t_asst + t_outr

    cats = [
        ("Produtos",     "📦", len(produtos_df),     t_prod,  "#C9A84C"),
        ("Fornecedores", "🏢", len(fornecedores_df),  t_forn,  "#0F5E6E"),
        ("Assistentes",  "👥", len(assistentes_df),   t_asst,  "#6B4EAA"),
        ("Outros",       "➕", len(outros_df),        t_outr,  "#E07B39"),
    ]

    key_cat = f"itens_cat_{proposta_id}"
    if key_cat not in st.session_state:
        st.session_state[key_cat] = "Produtos"
    old_to_new = {"📦 Produtos": "Produtos", "🏢 Fornecedores": "Fornecedores",
                  "👥 Assistentes": "Assistentes", "➕ Outros": "Outros"}
    if st.session_state[key_cat] in old_to_new:
        st.session_state[key_cat] = old_to_new[st.session_state[key_cat]]

    cat_ativa = st.session_state[key_cat]

    st.markdown("""
    <style>
    .itens-sidebar-title {
        font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: #8B8680; padding: 0 0 10px 2px;
        border-bottom: 1px solid #eee; margin-bottom: 6px;
    }
    .itens-total-box {
        background: #faf9f7; border: 1px solid #e8e5df; border-radius: 10px;
        padding: 14px 12px; margin-top: 12px;
    }
    .itens-total-label {
        font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; color: #8B8680; margin-bottom: 4px;
    }
    .itens-total-value {
        font-size: 18px; font-weight: 700; color: #0D1B2A;
    }
    .itens-content-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 18px; background: #faf9f7; border-radius: 10px;
        margin-bottom: 16px; border: 1px solid #e8e5df;
    }
    .itens-content-title {
        font-size: 16px; font-weight: 700; color: #0D1B2A;
        display: flex; align-items: center; gap: 8px;
    }
    .itens-content-subtitle {
        font-size: 12px; color: #8B8680; margin-top: 2px;
    }
    .itens-empty-state {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 48px 20px;
        background: #faf9f7; border-radius: 12px; border: 1px dashed #ddd;
        margin: 8px 0 16px 0; text-align: center;
    }
    .itens-empty-icon { font-size: 40px; margin-bottom: 12px; opacity: 0.6; }
    .itens-empty-title {
        font-size: 15px; font-weight: 600; color: #4a4a4a; margin-bottom: 6px;
    }
    .itens-empty-hint { font-size: 12px; color: #9a9890; }
    </style>
    """, unsafe_allow_html=True)

    col_nav, col_main = st.columns([1, 2.8])

    with col_nav:
        st.markdown('<div class="itens-sidebar-title">ITENS & CUSTOS</div>', unsafe_allow_html=True)

        labels = []
        label_map = {}
        for cat_name, cat_icon, cat_qtd, cat_total, cat_cor in cats:
            sub = _fmt_brl(cat_total) if cat_total > 0 else ""
            display = f"{cat_icon} {cat_name}  {cat_qtd}" + (f" · {sub}" if sub else "")
            labels.append(display)
            label_map[display] = cat_name

        labels_base = [name for name, _, _, _, _ in cats]
        idx_atual = labels_base.index(cat_ativa) if cat_ativa in labels_base else 0

        escolha = st.radio(
            "Categoria",
            options=labels,
            index=idx_atual,
            key=f"radio_cat_{proposta_id}",
            label_visibility="collapsed"
        )

        cat_ativa = label_map.get(escolha, "Produtos")
        st.session_state[key_cat] = cat_ativa

        st.markdown(f"""
        <div class="itens-total-box">
          <div class="itens-total-label">Total geral</div>
          <div class="itens-total-value">{_fmt_brl(t_total)}</div>
        </div>""", unsafe_allow_html=True)

        if show_finalizar:
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            if st.button("🏁 FINALIZAR PROJETO", key=f"btn_finalizar_exec_{proposta_id}", use_container_width=True, type="primary"):
                try:
                    res = finalizar_proposta_v2(int(proposta_id))
                    if res.get('status', False):
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state['proposta_finalizada_sucesso'] = True
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(res.get('message', 'Erro ao finalizar.'))
                except Exception as e:
                    st.error(str(e))

    with col_main:
        for cat_name, cat_icon, cat_qtd, cat_total, cat_cor in cats:
            if cat_name == cat_ativa:
                sub_text = f"{cat_qtd} {'item' if cat_qtd == 1 else 'itens'} · {_fmt_brl(cat_total)}"
                st.markdown(f"""
                <div class="itens-content-header">
                  <div>
                    <div class="itens-content-title">{cat_icon} {cat_name}</div>
                    <div class="itens-content-subtitle">{sub_text}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                break

        if cat_ativa == "Produtos":
            _tab_produtos(proposta_id)
        elif cat_ativa == "Fornecedores":
            _tab_fornecedores(proposta_id)
        elif cat_ativa == "Assistentes":
            _tab_assistentes(proposta_id)
        elif cat_ativa == "Outros":
            _tab_outros(proposta_id)



def _acrescimos_cards(acrescimos, cor_borda="#C9A84C"):
    """Renderiza acréscimos como cards com borda colorida e valor à direita."""
    cards = ""
    for _, a in acrescimos.iterrows():
        nome = html_module.escape(str(a.get('fornecedor') or a.get('descricao') or '—'))
        desc = html_module.escape(str(a.get('descricao') or ''))
        val  = float(a.get('valor', 0))
        val_str = _fmt_brl(val)
        cards += f"""
        <div style="border-left:3px solid {cor_borda};background:#fff;border-radius:0 8px 8px 0;
                    padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);
                    display:flex;justify-content:space-between;align-items:center;">
          <div>
            <span style="font-weight:600;color:#0D1B2A;font-size:13px;">{nome}</span>
            {"<br><span style='font-size:11px;color:#9a9890;'>" + desc + "</span>" if desc and desc != nome else ""}
          </div>
          <span style="font-weight:700;color:#1D6A4A;font-size:13px;white-space:nowrap;">{val_str}</span>
        </div>"""
    return cards


def _tab_fornecedores(proposta_id):
    # ── Lista atual ───────────────────────────────────────────────────────
    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
        if not acrescimos.empty:
            total_forn = acrescimos['valor'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Fornecedores", len(acrescimos))
            c2.metric("Total", _fmt_brl(total_forn))
            st.markdown(_acrescimos_cards(acrescimos, "#0F5E6E"), unsafe_allow_html=True)

            with st.expander("✏️ Editar / 🗑️ Remover"):
                ids = acrescimos['id'].tolist()
                fmt_forn = lambda x: acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]
                col_e, col_r = st.columns(2)
                with col_e:
                    with st.form(key=f"form_editar_fornecedor_{proposta_id}"):
                        aid = st.selectbox("Editar:", options=ids, format_func=fmt_forn, key=f"sel_edit_forn_{proposta_id}")
                        atual = acrescimos.loc[acrescimos['id'] == aid].iloc[0]
                        nv = st.number_input("Novo valor (R$):", min_value=0.0, value=float(atual['valor']), format="%.2f", key=f"nv_forn_{proposta_id}")
                        nd = st.text_area("Observações:", value=str(atual['descricao'] or ""), height=70, key=f"nd_forn_{proposta_id}")
                        if st.form_submit_button("Salvar", use_container_width=True):
                            try:
                                if st.session_state.db.update_acrescimo_proposta(aid, valor=nv, descricao=nd):
                                    st.success("Atualizado!"); st.rerun()
                                else:
                                    st.error("Falha ao atualizar.")
                            except Exception as e:
                                st.error(str(e))
                with col_r:
                    with st.form(key=f"form_remover_fornecedor_{proposta_id}"):
                        rid = st.selectbox("Remover:", options=ids, format_func=fmt_forn, key=f"sel_rem_forn_{proposta_id}")
                        if st.form_submit_button("🗑️ Remover", use_container_width=True):
                            try:
                                if st.session_state.db.remove_acrescimo_proposta(rid):
                                    st.success("Removido!"); st.rerun()
                                else:
                                    st.error("Falha ao remover.")
                            except Exception as e:
                                st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon">🏢</div>
              <div class="itens-empty-title">Nenhum fornecedor ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir fornecedores</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar fornecedores: {str(e)}")

    st.markdown('<p style="font-weight:600;color:#0D1B2A;font-size:14px;margin-bottom:4px;">➕ Adicionar Fornecedor</p>', unsafe_allow_html=True)
    try:
        fornecedores = st.session_state.db.get_fornecedores()
        if not fornecedores.empty:
            with st.form(key=f"form_fornecedor_{proposta_id}"):
                def fmt_forn_opt(fid):
                    r = fornecedores.loc[fornecedores['id'] == fid]
                    return r['descricao'].iloc[0] if not r.empty else "?"
                forn_sel = st.selectbox("Fornecedor:", options=fornecedores['id'].tolist(),
                                        format_func=fmt_forn_opt, key=f"select_fornecedor_{proposta_id}")
                col1, col2 = st.columns(2)
                with col1:
                    valor_servico = st.number_input("Valor (R$):", min_value=0.0, value=0.0, format="%.2f", key=f"valor_forn_{proposta_id}")
                with col2:
                    observacoes = st.text_area("Observações:", height=70, key=f"obs_forn_{proposta_id}")
                if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
                    if valor_servico <= 0:
                        st.error("Valor deve ser maior que zero.")
                    else:
                        try:
                            res = st.session_state.db.add_fornecedor_proposta(proposta_id=proposta_id,
                                  fornecedor_id=forn_sel, valor=valor_servico, observacoes=observacoes)
                            if res and "acrescimo_id" in res:
                                st.success("Fornecedor adicionado!"); st.rerun()
                            else:
                                st.error("Erro ao adicionar.")
                        except Exception as e:
                            st.error(str(e))
        else:
            st.info("Nenhum fornecedor cadastrado. Adicione em Cadastros > Fornecedores.")
    except Exception as e:
        st.error(str(e))


def _tab_assistentes(proposta_id):
    # ── Lista atual ───────────────────────────────────────────────────────
    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
        if not acrescimos.empty:
            total_asst = acrescimos['valor'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Assistentes", len(acrescimos))
            c2.metric("Total", _fmt_brl(total_asst))
            st.markdown(_acrescimos_cards(acrescimos, "#6B4EAA"), unsafe_allow_html=True)

            with st.expander("✏️ Editar / 🗑️ Remover"):
                ids = acrescimos['id'].tolist()
                fmt_a = lambda x: acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]
                col_e, col_r = st.columns(2)
                with col_e:
                    with st.form(key=f"form_editar_assistente_{proposta_id}"):
                        aid = st.selectbox("Editar:", options=ids, format_func=fmt_a, key=f"sel_edit_asst_{proposta_id}")
                        atual = acrescimos.loc[acrescimos['id'] == aid].iloc[0]
                        nv = st.number_input("Novo valor (R$):", min_value=0.0, value=float(atual['valor']), format="%.2f", key=f"nv_asst_{proposta_id}")
                        nd = st.text_area("Descrição:", value=str(atual['descricao'] or ""), height=70, key=f"nd_asst_{proposta_id}")
                        if st.form_submit_button("Salvar", use_container_width=True):
                            try:
                                if st.session_state.db.update_acrescimo_proposta(aid, valor=nv, descricao=nd):
                                    st.success("Atualizado!"); st.rerun()
                                else:
                                    st.error("Falha ao atualizar.")
                            except Exception as e:
                                st.error(str(e))
                with col_r:
                    with st.form(key=f"form_remover_assistente_{proposta_id}"):
                        rid = st.selectbox("Remover:", options=ids, format_func=fmt_a, key=f"sel_rem_asst_{proposta_id}")
                        if st.form_submit_button("🗑️ Remover", use_container_width=True):
                            try:
                                if st.session_state.db.remove_acrescimo_proposta(rid):
                                    st.success("Removido!"); st.rerun()
                                else:
                                    st.error("Falha ao remover.")
                            except Exception as e:
                                st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon">👥</div>
              <div class="itens-empty-title">Nenhum assistente ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir assistentes</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar assistentes: {str(e)}")

    st.markdown('<p style="font-weight:600;color:#0D1B2A;font-size:14px;margin-bottom:4px;">➕ Adicionar Assistente</p>', unsafe_allow_html=True)
    try:
        assistentes = st.session_state.db.get_assistentes()
        if not assistentes.empty:
            with st.form(key=f"form_assistente_{proposta_id}"):
                asst_sel = st.selectbox("Assistente:", options=assistentes['id'].tolist(),
                                        format_func=lambda x: assistentes.loc[assistentes['id'] == x, 'nome'].iloc[0])
                col1, col2 = st.columns(2)
                with col1:
                    valor_servico = st.number_input("Valor (R$):", min_value=0.0, value=0.0, format="%.2f")
                with col2:
                    observacoes = st.text_area("Observações:", height=70)
                if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
                    if valor_servico <= 0:
                        st.error("Valor deve ser maior que zero.")
                    else:
                        try:
                            res = st.session_state.db.add_assistente_proposta(proposta_id=proposta_id,
                                  assistente_id=asst_sel, valor=valor_servico, observacoes=observacoes)
                            if res and "acrescimo_id" in res:
                                st.success("Assistente adicionado!"); st.rerun()
                            else:
                                st.error("Erro ao adicionar.")
                        except Exception as e:
                            st.error(str(e))
        else:
            st.info("Nenhum assistente cadastrado. Adicione em Cadastros > Assistentes.")
    except Exception as e:
        st.error(str(e))


def _tab_outros(proposta_id):
    # ── Lista atual ───────────────────────────────────────────────────────
    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")
        if not acrescimos.empty:
            total_outros = acrescimos['valor'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Itens extras", len(acrescimos))
            c2.metric("Total", _fmt_brl(total_outros))
            # Montar cards com nome extraído da descrição
            cards = ""
            for _, a in acrescimos.iterrows():
                desc_raw = str(a.get('descricao') or '—')
                nome = html_module.escape(desc_raw.split(' - ')[0] if ' - ' in desc_raw else desc_raw)
                sub  = html_module.escape(desc_raw.split(' - ')[1] if ' - ' in desc_raw else '')
                comodo = html_module.escape(str(a.get('fornecedor') or 'Geral'))
                val = float(a.get('valor', 0))
                val_str = _fmt_brl(val)
                cards += f"""
                <div style="border-left:3px solid #E07B39;background:#fff;border-radius:0 8px 8px 0;
                            padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);
                            display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <span style="font-weight:600;color:#0D1B2A;font-size:13px;">{nome}</span>
                    {'<br><span style="font-size:11px;color:#9a9890;">' + sub + '</span>' if sub else ''}
                    <span style="font-size:11px;color:#9a9890;margin-left:6px;">📍 {comodo}</span>
                  </div>
                  <span style="font-weight:700;color:#1D6A4A;font-size:13px;white-space:nowrap;">{val_str}</span>
                </div>"""
            st.markdown(cards, unsafe_allow_html=True)

            with st.expander("🗑️ Remover item"):
                with st.form(key=f"form_remover_outros_{proposta_id}"):
                    rid = st.selectbox("Selecione:", options=acrescimos['id'].tolist(),
                                       format_func=lambda x: acrescimos.loc[acrescimos['id'] == x, 'descricao'].iloc[0])
                    if st.form_submit_button("Remover", use_container_width=True):
                        try:
                            if st.session_state.db.remove_acrescimo_proposta(rid):
                                st.success("Item removido!"); st.rerun()
                            else:
                                st.error("Falha ao remover.")
                        except Exception as e:
                            st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon">➕</div>
              <div class="itens-empty-title">Nenhum item extra ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir itens extras</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar itens: {str(e)}")

    st.markdown('<p style="font-weight:600;color:#0D1B2A;font-size:14px;margin-bottom:4px;">➕ Adicionar Item Extra</p>', unsafe_allow_html=True)
    with st.form(key=f"form_outros_{proposta_id}"):
        col1, col2 = st.columns(2)
        with col1:
            nome_item = st.text_input("Nome do Item:")
            descricao_item = st.text_input("Descrição:")
            comodo_area = st.text_input("Cômodo/Área:")
        with col2:
            valor_unitario = st.number_input("Valor unitário (R$):", min_value=0.0, value=0.0, format="%.2f")
            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
            valor_total_calc = valor_unitario * quantidade
            st.markdown(f'<p style="color:#1D6A4A;font-weight:600;margin-top:22px;">Total: R$ {valor_total_calc:.2f}</p>', unsafe_allow_html=True)
        if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
            if not nome_item or valor_unitario <= 0:
                st.error("Preencha o nome e um valor válido.")
            else:
                try:
                    res = st.session_state.db.add_acrescimo_proposta(
                        proposta_id=proposta_id, tipo="OUTROS",
                        valor=valor_unitario * quantidade,
                        descricao=f"{nome_item} - {descricao_item}" if descricao_item else nome_item,
                        fornecedor=comodo_area if comodo_area else "Geral"
                    )
                    if res and "acrescimo_id" in res:
                        st.success(f"'{nome_item}' adicionado!"); st.rerun()
                    else:
                        st.error("Erro ao adicionar.")
                except Exception as e:
                    st.error(str(e))


def _status_badge(label, cor_fundo, cor_texto="#fff"):
    st.markdown(f"""
    <div style="display:inline-block;background:{cor_fundo};color:{cor_texto};
                border-radius:20px;padding:5px 16px;font-size:13px;font-weight:600;
                margin-bottom:16px;">{label}</div>""", unsafe_allow_html=True)


def _tab_acoes(proposta_id, proposta):
    status_atual   = proposta.get('status', '')
    status_execucao = proposta.get('status_execucao', '')

    em_aberto    = status_atual in ['Em elaboração', 'Aguardando aprovação', 'Aguardando']
    esta_aprovada = status_atual == 'Aprovada'
    em_execucao  = status_execucao == 'Em execução'
    finalizada   = status_atual in ['Finalizada', 'Recusada']

    # ── Badge de status ───────────────────────────────────────────────────
    if em_aberto:
        _status_badge("🟡 Em Aberto", "#B7860D")
    elif esta_aprovada and not em_execucao and not finalizada:
        _status_badge("✅ Aprovada — aguardando início", "#1D6A4A")
    elif em_execucao and not finalizada:
        _status_badge("🔵 Em Execução", "#1565C0")
    elif finalizada:
        cor_fin = "#4A4A4A" if status_atual == 'Finalizada' else "#C0392B"
        _status_badge(f"🏁 {status_atual}", cor_fin)
    else:
        _status_badge(f"● {status_atual}", "#555")

    # ── EM ABERTO ─────────────────────────────────────────────────────────
    if em_aberto:
        st.markdown('<p style="color:#555;font-size:13px;margin-bottom:12px;">Escolha a próxima ação para esta proposta.</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Aprovar Proposta", type="primary", use_container_width=True, key=f"btn_aprovar_{proposta_id}"):
                try:
                    res = st.session_state.db.update_proposta_status(proposta_id=proposta_id,
                          novo_status="Aprovada", data_aprovacao=datetime.now().date())
                    if res.get('status', False):
                        st.success("Proposta aprovada!")
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error(res.get('message', 'Erro ao aprovar.'))
                except Exception as e:
                    st.error(str(e))
        with col2:
            if st.button("❌ Recusar Proposta", use_container_width=True, key=f"btn_recusar_{proposta_id}"):
                try:
                    res = st.session_state.db.update_proposta_status(proposta_id=proposta_id, novo_status="Finalizada")
                    if res.get('status', False):
                        st.session_state.db.update_proposta(proposta_id, status_execucao="Cancelada", data_fim=datetime.now().date())
                        st.success("Proposta recusada.")
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error("Erro ao recusar.")
                except Exception as e:
                    st.error(str(e))

    # ── APROVADA ──────────────────────────────────────────────────────────
    elif esta_aprovada and not em_execucao and not finalizada:
        st.markdown('<p style="color:#555;font-size:13px;margin-bottom:12px;">Inicie a execução quando o trabalho começar.</p>', unsafe_allow_html=True)
        if st.button("▶ Iniciar Execução", type="primary", use_container_width=True, key=f"btn_iniciar_exec_{proposta_id}"):
            try:
                res = st.session_state.db.update_proposta_status(proposta_id=proposta_id,
                      novo_status="Em execução", data_aprovacao=proposta.get('data_aprovacao'))
                if res.get('status', False):
                    st.success("Execução iniciada!")
                    st.session_state['kanban_selected_proposta'] = None
                    st.rerun()
                else:
                    st.error(res.get('message', 'Erro.'))
            except Exception as e:
                st.error(str(e))

    # ── EM EXECUÇÃO ───────────────────────────────────────────────────────
    elif em_execucao and not finalizada:
        try:
            valor_base      = _safe_float(proposta.get('valor'))
            produtos_df     = st.session_state.db.get_produtos_organizadores(proposta_id)
            fornecedores_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
            assistentes_df  = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
            outros_df       = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")

            total_prod = (produtos_df['valor'] * produtos_df['quantidade']).sum() if not produtos_df.empty else 0
            total_forn = fornecedores_df['valor'].sum() if not fornecedores_df.empty else 0
            total_asst = assistentes_df['valor'].sum() if not assistentes_df.empty else 0
            total_outr = outros_df['valor'].sum() if not outros_df.empty else 0
            total_geral = valor_base + total_prod + total_forn + total_asst + total_outr

            # Métricas compactas
            c1, c2, c3 = st.columns(3)
            c1.metric("Serviço (PO)", _fmt_brl(valor_base))
            c2.metric("Custos totais", _fmt_brl(total_forn + total_asst + total_outr + total_prod))
            c3.metric("Total geral", _fmt_brl(total_geral))

            # Breakdown em cards
            breakdown = [
                ("🏷️ Personal Organizer", valor_base, "#C9A84C"),
                ("📦 Produtos",           total_prod, "#0F5E6E"),
                ("🏢 Fornecedores",       total_forn, "#0F5E6E"),
                ("👥 Assistentes",        total_asst, "#6B4EAA"),
                ("➕ Outros",             total_outr, "#E07B39"),
            ]
            rows_html = ""
            for label, val, cor in breakdown:
                if val > 0:
                    rows_html += f"""
                    <div style="display:flex;justify-content:space-between;padding:7px 12px;
                                border-left:3px solid {cor};background:#fff;border-radius:0 6px 6px 0;
                                margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.05);">
                      <span style="font-size:13px;color:#333;">{label}</span>
                      <span style="font-size:13px;font-weight:600;color:#1D6A4A;">{_fmt_brl(val)}</span>
                    </div>"""
            rows_html += f"""
                    <div style="display:flex;justify-content:space-between;padding:9px 12px;
                                background:#0D1B2A;border-radius:6px;margin-top:6px;">
                      <span style="font-size:13px;color:#C9A84C;font-weight:700;">TOTAL GERAL</span>
                      <span style="font-size:14px;font-weight:700;color:#fff;">{_fmt_brl(total_geral)}</span>
                    </div>"""
            st.markdown(rows_html, unsafe_allow_html=True)

            # Gráfico de pizza
            if any(v > 0 for _, v, _ in breakdown):
                labels = [l for l, v, _ in breakdown if v > 0]
                values = [v for _, v, _ in breakdown if v > 0]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.35,
                                              textinfo='percent', hoverinfo='label+value')])
                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250,
                                  showlegend=True,
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.3))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar resumo: {str(e)}")

        st.markdown("---")
        with st.form(key=f"form_finalizar_concluida_{proposta_id}"):
            if st.form_submit_button("🏁 MARCAR COMO CONCLUÍDA", type="primary", use_container_width=True):
                try:
                    res = finalizar_proposta_v2(int(proposta_id))
                    if res.get('status', False):
                        st.success("Proposta finalizada com sucesso!")
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error(f"Erro: {res.get('message', 'Desconhecido')}")
                except Exception as e:
                    st.error(str(e))

    # ── FINALIZADA ────────────────────────────────────────────────────────
    elif finalizada:
        st.markdown('<p style="color:#555;font-size:13px;margin-bottom:12px;">Gere os relatórios para esta proposta concluída.</p>', unsafe_allow_html=True)

        # Cards de relatório
        st.markdown("""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;">
          <div style="background:#0D1B2A;border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:22px;">📋</div>
            <div style="color:#C9A84C;font-weight:700;font-size:12px;margin-top:4px;">RELATÓRIO CLIENTE</div>
            <div style="color:#aaa;font-size:10px;">Proposta de serviço</div>
          </div>
          <div style="background:#0D1B2A;border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:22px;">📊</div>
            <div style="color:#C9A84C;font-weight:700;font-size:12px;margin-top:4px;">RELATÓRIO INTERNO</div>
            <div style="color:#aaa;font-size:10px;">Margens e custos</div>
          </div>
          <div style="background:#0D1B2A;border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:22px;">🏢</div>
            <div style="color:#C9A84C;font-weight:700;font-size:12px;margin-top:4px;">RELATÓRIO FORNECEDORES</div>
            <div style="color:#aaa;font-size:10px;">Lista de terceiros</div>
          </div>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Gerar para Cliente", use_container_width=True, key=f"btn_rel_cliente_{proposta_id}"):
                try:
                    st_gerar_pdf_cliente(proposta_id)
                except Exception as e:
                    st.error(str(e))
        with col2:
            if st.button("📊 Gerar Interno", use_container_width=True, key=f"btn_rel_interno_{proposta_id}"):
                try:
                    st_gerar_pdf_interno(proposta_id)
                except Exception as e:
                    st.error(str(e))
        with col3:
            if st.button("🏢 Gerar Fornecedores", use_container_width=True, key=f"btn_rel_forn_{proposta_id}"):
                try:
                    st_gerar_pdf_fornecedores(proposta_id)
                except Exception as e:
                    st.error(str(e))

        with st.expander("🔄 Reabrir Proposta Finalizada"):
            st.warning("Esta ação retornará a proposta para o status 'Em execução'.")
            if st.button("REABRIR PROPOSTA", key=f"btn_reabrir_{proposta_id}", type="primary", use_container_width=True):
                try:
                    from reabrir_proposta import reabrir_proposta_finalizada
                    res = reabrir_proposta_finalizada(proposta_id)
                    if res.get('status') in ['sucesso', 'sucesso_com_alerta']:
                        st.success(res.get('mensagem'))
                        if res.get('status') == 'sucesso_com_alerta':
                            st.warning(res.get('alerta'))
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error(res.get('mensagem'))
                except Exception as e:
                    st.error(str(e))

    else:
        st.info(f"Status: {status_atual} / {status_execucao}")

    # ── Gerar PDF da proposta (sempre disponível) ─────────────────────────
    st.markdown("---")
    if st.button("📄 Gerar PDF da Proposta (cliente)", key=f"btn_pdf_proposta_{proposta_id}", use_container_width=True):
        try:
            sucesso, mensagem, arquivo = gerar_pdf_proposta(db=st.session_state.db, proposta_id=proposta_id)
            if sucesso and arquivo:
                with open(arquivo, "rb") as f:
                    st.success("PDF gerado!")
                    st.download_button("📥 Baixar Proposta", f.read(), f"Proposta_{proposta_id}.pdf",
                                       "application/pdf", key=f"dl_proposta_{proposta_id}", use_container_width=True)
            else:
                st.error(f"Erro: {mensagem}")
        except Exception as e:
            st.error(str(e))

    # ── Excluir proposta ──────────────────────────────────────────────────
    with st.expander("🗑️ Excluir Proposta", expanded=False):
        st.warning("⚠️ Esta ação é **permanente** e removerá todos os dados relacionados.")
        confirmar_exclusao = st.checkbox("Entendo que esta ação não pode ser desfeita", key=f"confirmar_exclusao_{proposta_id}")
        if confirmar_exclusao:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ EXCLUIR PROPOSTA", key=f"btn_excluir_kanban_{proposta_id}", type="secondary", use_container_width=True):
                    try:
                        from sqlalchemy import text
                        from utils.database import engine
                        with engine.connect() as conn:
                            for tbl in ["post_organizations", "vendas", "financeiro", "acrescimos_proposta", "produtos_organizadores", "andamento_propostas"]:
                                conn.execute(text(f"DELETE FROM {tbl} WHERE proposta_id = {proposta_id}"))
                            conn.execute(text(f"DELETE FROM propostas WHERE id = {proposta_id}"))
                            conn.commit()
                        st.success(f"Proposta #{proposta_id} excluída.")
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with col2:
                if st.button("🔙 Cancelar", key=f"btn_cancel_excl_{proposta_id}", type="primary", use_container_width=True):
                    st.rerun()


def show():
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">📝 Propostas</h1>', unsafe_allow_html=True)

    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return

    if 'kanban_selected_proposta' not in st.session_state:
        st.session_state['kanban_selected_proposta'] = None
    if 'kanban_nova_proposta_open' not in st.session_state:
        st.session_state['kanban_nova_proposta_open'] = False

    if st.session_state.pop('proposta_finalizada_sucesso', False):
        st.success("✅ Proposta finalizada com sucesso!")

    try:
        propostas = st.session_state.db.get_propostas()
        clientes = st.session_state.db.get_clientes()

        for col in ['valor', 'previsao_dias', 'id', 'numero', 'cliente_id']:
            if col in propostas.columns:
                propostas[col] = pd.to_numeric(propostas[col], errors='coerce')

        if not propostas.empty and not clientes.empty:
            propostas_com_clientes = propostas.merge(
                clientes[['id', 'nome']],
                left_on='cliente_id',
                right_on='id',
                suffixes=('', '_cliente'),
                how='left'
            )
        else:
            propostas_com_clientes = propostas.copy() if not propostas.empty else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao carregar dados iniciais: {str(e)}")
        return

    col_esp1, col_btn, col_esp2 = st.columns([1, 3, 1])
    with col_btn:
        with stylable_container(key="gold_nova_proposta", css_styles="""
            button {
                background: linear-gradient(135deg, #C9A84C, #B8943D) !important;
                color: #fff !important;
                font-weight: 700 !important;
                font-size: 15px !important;
                padding: 12px 32px !important;
                border-radius: 10px !important;
                border: none !important;
                letter-spacing: 0.02em !important;
                box-shadow: 0 3px 12px rgba(201,168,76,0.35) !important;
            }
        """):
            nova_btn = st.button("✚  Nova Proposta", type="primary", use_container_width=True, key="btn_nova_proposta_top")
            if nova_btn:
                st.session_state['kanban_nova_proposta_open'] = not st.session_state['kanban_nova_proposta_open']

    if st.session_state['kanban_nova_proposta_open']:
        with st.expander("📝 Nova Proposta", expanded=True):
            if clientes.empty:
                st.warning("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
            else:
                _render_nova_proposta_form(clientes)

    st.markdown("---")

    def _col_propostas(label, status_list, exec_status_list=None, exclude_exec=None):
        if propostas_com_clientes.empty:
            return pd.DataFrame()
        mask = propostas_com_clientes['status'].isin(status_list)
        if exec_status_list is not None:
            mask = mask | propostas_com_clientes['status_execucao'].isin(exec_status_list)
        if exclude_exec is not None:
            mask = mask & ~propostas_com_clientes['status_execucao'].isin(exclude_exec)
        return propostas_com_clientes[mask].copy()

    propostas_em_aberto = _col_propostas(
        "Em aberto",
        ['Em elaboração', 'Aguardando aprovação', 'Aguardando']
    )

    propostas_aprovadas = _col_propostas(
        "Aprovada",
        ['Aprovada'],
        exclude_exec=['Em execução']
    )

    if not propostas_com_clientes.empty:
        propostas_em_exec = propostas_com_clientes[
            propostas_com_clientes['status_execucao'] == 'Em execução'
        ].copy()
    else:
        propostas_em_exec = pd.DataFrame()

    if not propostas_com_clientes.empty:
        propostas_finalizadas = propostas_com_clientes[
            (propostas_com_clientes['status'] == 'Finalizada') |
            (propostas_com_clientes['status'] == 'Recusada')
        ].copy()
    else:
        propostas_finalizadas = pd.DataFrame()

    col_aberto, col_aprovada, col_execucao, col_finalizada = st.columns(4)

    COLS_CONFIG = [
        (col_aberto, "🟡 Em Aberto", propostas_em_aberto, "#fff3cd"),
        (col_aprovada, "🟢 Aprovada", propostas_aprovadas, "#d4edda"),
        (col_execucao, "🔵 Em Execução", propostas_em_exec, "#cce5ff"),
        (col_finalizada, "✅ Finalizada", propostas_finalizadas, "#e2e3e5"),
    ]

    kanban_css = """
    <style>
    .kanban-col-header {
        font-weight: 700;
        font-size: 0.82rem;
        padding: 6px 10px;
        border-radius: 8px 8px 0 0;
        margin-bottom: 6px;
        text-align: center;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .kanban-card {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        background: #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kanban-card-cliente {
        font-weight: 600;
        font-size: 0.82rem;
        margin-bottom: 1px;
        color: #1a202c;
    }
    .kanban-card-desc {
        font-size: 0.72rem;
        color: #6c757d;
        margin-bottom: 3px;
    }
    .kanban-card-valor {
        font-size: 0.78rem;
        color: #1a5276;
        font-weight: 600;
    }
    /* Botões "Ver Detalhes" compactos */
    .stButton > button[kind="secondary"] {
        font-size: 0.75rem !important;
        padding: 4px 8px !important;
        min-height: 0 !important;
        height: auto !important;
        line-height: 1.4 !important;
    }
    /* Cards de métricas do rodapé */
    .kanban-metric {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
    }
    .kanban-metric-label {
        font-size: 0.72rem;
        color: #64748b;
        margin: 0 0 4px 0;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .kanban-metric-value {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1a202c;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    """
    st.markdown(kanban_css, unsafe_allow_html=True)

    for col_idx, (col_widget, col_label, col_df, col_color) in enumerate(COLS_CONFIG):
        with col_widget:
            st.markdown(
                f'<div class="kanban-col-header" style="background-color:{col_color};">{col_label} ({len(col_df)})</div>',
                unsafe_allow_html=True
            )
            if not col_df.empty:
                for _, proposta in col_df.iterrows():
                    pid = proposta['id']
                    cliente_nome = html_module.escape(str(proposta.get('nome', proposta.get('cliente_nome', 'Cliente'))))
                    desc = html_module.escape(str(proposta.get('descricao', ''))[:60])
                    valor_f = html_module.escape(_fmt_brl(_safe_float(proposta.get('valor'))))

                    st.markdown(
                        f'<div class="kanban-card">'
                        f'<div class="kanban-card-cliente">{cliente_nome}</div>'
                        f'<div class="kanban-card-desc">{desc}</div>'
                        f'<div class="kanban-card-valor">{valor_f}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    is_selected = st.session_state.get('kanban_selected_proposta') == pid
                    btn_label = "▲ Fechar" if is_selected else "▼ Ver Detalhes"
                    if st.button(btn_label, key=f"card_btn_c{col_idx}_{pid}", use_container_width=True):
                        if is_selected:
                            st.session_state['kanban_selected_proposta'] = None
                        else:
                            st.session_state['kanban_selected_proposta'] = pid
                        st.rerun()
            else:
                st.caption("Nenhuma proposta nesta etapa.")

    total_aberto = propostas_em_aberto['valor'].apply(_safe_float).sum() if not propostas_em_aberto.empty else 0.0
    total_aprovada = propostas_aprovadas['valor'].apply(_safe_float).sum() if not propostas_aprovadas.empty else 0.0
    total_execucao = propostas_em_exec['valor'].apply(_safe_float).sum() if not propostas_em_exec.empty else 0.0
    total_finalizada = propostas_finalizadas['valor'].apply(_safe_float).sum() if not propostas_finalizadas.empty else 0.0

    st.markdown("---")
    footer_c1, footer_c2, footer_c3, footer_c4 = st.columns(4)
    for col, label, valor in [
        (footer_c1, "🟡 Em Aberto",   total_aberto),
        (footer_c2, "🟢 Aprovada",    total_aprovada),
        (footer_c3, "🔵 Em Execução", total_execucao),
        (footer_c4, "✅ Finalizada",  total_finalizada),
    ]:
        with col:
            st.markdown(f"""
            <div class="kanban-metric">
                <p class="kanban-metric-label">{label}</p>
                <p class="kanban-metric-value">{_fmt_brl(valor)}</p>
            </div>
            """, unsafe_allow_html=True)

    selected_id = st.session_state.get('kanban_selected_proposta')
    if selected_id is not None:
        st.markdown("---")
        if not propostas_com_clientes.empty:
            proposta_rows = propostas_com_clientes[propostas_com_clientes['id'] == selected_id]
            if not proposta_rows.empty:
                proposta_row = proposta_rows.iloc[0]
                _render_detail_panel(selected_id, proposta_row, propostas_com_clientes)
            else:
                st.warning("Proposta não encontrada. Pode ter sido excluída ou alterada.")
                st.session_state['kanban_selected_proposta'] = None


if __name__ == "__main__":
    show()