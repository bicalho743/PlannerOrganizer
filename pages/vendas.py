import streamlit as st
import pandas as pd
import html as html_module
from datetime import datetime
import os
from utils.custom_components import custom_info, custom_warning
from streamlit_extras.stylable_container import stylable_container


def _fmt_brl(val):
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


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


def _render_nova_venda_form(clientes_df, produtos_df):
    if clientes_df.empty:
        custom_warning("É necessário cadastrar clientes para registrar vendas.")
        return
    if produtos_df.empty:
        custom_warning("É necessário cadastrar produtos (em Cadastros → Produtos) para registrar vendas.")
        return

    clientes_df = clientes_df.sort_values("nome").reset_index(drop=True)
    produtos_df = produtos_df.sort_values("nome").reset_index(drop=True)

    if "produtos_venda" not in st.session_state:
        st.session_state.produtos_venda = []

    cliente_id = st.selectbox(
        "Cliente",
        options=clientes_df["id"].tolist(),
        format_func=lambda x: clientes_df[clientes_df["id"] == x]["nome"].iloc[0],
        key="nv_cliente_id"
    )

    st.markdown("**Adicionar produtos:**")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        produto_id = st.selectbox(
            "Produto",
            options=[None] + produtos_df["id"].tolist(),
            format_func=lambda x: "-- Selecione --" if x is None
                else f"{produtos_df[produtos_df['id']==x]['nome'].iloc[0]} — R$ {produtos_df[produtos_df['id']==x]['preco_venda'].iloc[0]:.2f}",
            key="nv_produto_id"
        )
    with col2:
        if produto_id:
            prod = produtos_df[produtos_df["id"] == produto_id].iloc[0]
            estoque_atual = int(prod["estoque"])
            quantidade = st.number_input("Qtd", min_value=1, max_value=max(1, estoque_atual), value=1, key="nv_qtd")
            if estoque_atual == 0:
                st.warning("Sem estoque")
        else:
            quantidade = st.number_input("Qtd", min_value=1, value=1, disabled=True, key="nv_qtd_dis")
    with col3:
        if produto_id:
            prod = produtos_df[produtos_df["id"] == produto_id].iloc[0]
            total_item = quantidade * float(prod["preco_venda"])
            st.metric("Total", _fmt_brl(total_item))

    if st.button("Adicionar à venda", type="primary", disabled=(produto_id is None), key="nv_add_produto"):
        if produto_id:
            prod = produtos_df[produtos_df["id"] == produto_id].iloc[0]
            produto_existe = False
            for i, item in enumerate(st.session_state.produtos_venda):
                if item["produto_id"] == produto_id:
                    nova_qtd = item["quantidade"] + quantidade
                    if nova_qtd <= prod["estoque"]:
                        st.session_state.produtos_venda[i]["quantidade"] = nova_qtd
                        st.session_state.produtos_venda[i]["total"] = nova_qtd * item["preco_unitario"]
                        produto_existe = True
                    else:
                        st.error(f"Estoque insuficiente! Disponível: {prod['estoque']}")
                    break
            if not produto_existe:
                st.session_state.produtos_venda.append({
                    "produto_id": produto_id,
                    "produto_nome": prod["nome"],
                    "quantidade": quantidade,
                    "preco_unitario": float(prod["preco_venda"]),
                    "total": quantidade * float(prod["preco_venda"])
                })
            st.rerun()

    if st.session_state.produtos_venda:
        st.markdown("**Produtos na venda:**")
        for i, item in enumerate(st.session_state.produtos_venda):
            c1, c2, c3, c4, c5 = st.columns([3, 1, 2, 2, 1])
            c1.write(item["produto_nome"])
            c2.write(f"{item['quantidade']}x")
            c3.write(_fmt_brl(item["preco_unitario"]))
            c4.write(_fmt_brl(item["total"]))
            with c5:
                if st.button("🗑️", key=f"nv_rm_{i}", help="Remover"):
                    st.session_state.produtos_venda.pop(i)
                    st.rerun()

        total_venda = sum(item["total"] for item in st.session_state.produtos_venda)
        st.markdown(f"**Total: {_fmt_brl(total_venda)}**")

        col1, col2 = st.columns(2)
        with col1:
            forma_pagamento = st.selectbox("Forma de pagamento", ["Cartão", "PIX"], key="nv_pagamento")
        with col2:
            data_venda = st.date_input("Data da venda", value=datetime.now().date(), format="DD/MM/YYYY", key="nv_data")

        observacoes = st.text_area("Observações (opcional)", key="nv_obs")

        col_fin, col_lim = st.columns(2)
        with col_fin:
            if st.button("FINALIZAR VENDA", type="primary", use_container_width=True, key="nv_finalizar"):
                try:
                    itens = [{"produto_id": it["produto_id"], "quantidade": it["quantidade"], "preco_unitario": it["preco_unitario"]}
                             for it in st.session_state.produtos_venda]
                    venda_id = st.session_state.db.add_venda(
                        cliente_id=cliente_id,
                        itens=itens,
                        forma_pagamento=forma_pagamento,
                        observacoes=observacoes,
                        data_venda=data_venda
                    )
                    st.success(f"✅ Venda #{venda_id} registrada com sucesso!")
                    st.session_state.produtos_venda = []
                    st.session_state.vendas_nova_venda_open = False
                    st.session_state.venda_recente_id = venda_id
                    st.session_state.venda_recente_cliente_id = cliente_id
                    st.session_state.venda_recente_forma_pagamento = forma_pagamento
                    st.session_state.venda_recente_observacoes = observacoes
                    st.session_state.venda_recente_valor_total = total_venda
                    st.session_state.mostrar_gerar_relatorio = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar venda: {str(e)}")
        with col_lim:
            if st.button("Limpar", use_container_width=True, key="nv_limpar"):
                st.session_state.produtos_venda = []
                st.rerun()


def _render_detail_panel(venda_id, venda_row):
    cliente_nome = html_module.escape(str(venda_row.get("cliente_nome", "Cliente")))
    status       = str(venda_row.get("status") or "—")
    data_str     = html_module.escape(_fmt_date(venda_row.get("data_venda")))
    pagamento    = str(venda_row.get("forma_pagamento") or "—")
    valor_str    = html_module.escape(_fmt_brl(venda_row.get("valor_total", 0)))
    obs_raw      = str(venda_row.get("observacoes") or "")
    proposta_desc = str(venda_row.get("proposta_descricao") or "")

    # linha de metadados compacta
    meta_parts = [status, data_str]
    if pagamento and pagamento != "—":
        meta_parts.append(pagamento)
    if proposta_desc:
        meta_parts.append(html_module.escape(proposta_desc))
    elif obs_raw:
        meta_parts.append(html_module.escape(obs_raw[:80]))
    meta_str = " · ".join(meta_parts)

    # badge de cor por status
    status_lower = status.lower()
    if "conclu" in status_lower or "confirm" in status_lower:
        border_color = "#38A169"
        badge_bg = "#C6F6D5"; badge_fg = "#276749"
    elif "pendent" in status_lower or "aberto" in status_lower:
        border_color = "#D69E2E"
        badge_bg = "#FEFCBF"; badge_fg = "#744210"
    else:
        border_color = "#718096"
        badge_bg = "#EDF2F7"; badge_fg = "#2D3748"

    st.markdown(f"""
    <style>
    .det-card {{
        background:#fff; border:1px solid #e2e8f0;
        border-left:4px solid {border_color};
        border-radius:8px; padding:12px 16px; margin-bottom:4px;
    }}
    .det-title {{ font-weight:700; font-size:1rem; color:#1a202c; margin:0 0 4px 0; }}
    .det-meta  {{ font-size:0.78rem; color:#64748b; margin:0; }}
    .det-valor {{ font-weight:700; font-size:1.1rem; color:{border_color}; white-space:nowrap; }}
    .det-badge {{
        display:inline-block; padding:2px 8px; border-radius:12px;
        font-size:0.7rem; font-weight:600;
        background:{badge_bg}; color:{badge_fg}; margin-left:6px;
    }}
    </style>
    <div class="det-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <p class="det-title">
                    Venda #{venda_id}
                    <span class="det-badge">{html_module.escape(status)}</span>
                </p>
                <p class="det-meta">👤 {cliente_nome} &nbsp;·&nbsp; {meta_str}</p>
            </div>
            <span class="det-valor">{valor_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Helper: busca itens de itens_venda; cai para produtos_organizadores se vazio ──
    def _get_itens_completo():
        try:
            iv = st.session_state.db.get_itens_venda(venda_id)
            if not iv.empty:
                return iv
        except Exception:
            pass
        pid = venda_row.get("proposta_id")
        if pid and not pd.isna(pid):
            try:
                po = st.session_state.db.get_produtos_organizadores(proposta_id=int(pid))
                if not po.empty:
                    po = po.rename(columns={"nome": "produto_nome", "valor": "preco_unitario"})
                    po["subtotal"] = po["preco_unitario"] * po["quantidade"]
                    return po[["produto_nome", "quantidade", "preco_unitario", "subtotal"]]
            except Exception:
                pass
        return pd.DataFrame()

    itens_det = _get_itens_completo()

    # Itens da venda (compacto, sem título separado)
    if not itens_det.empty:
        try:
            disp = itens_det.copy()
            disp["Total"] = (disp["quantidade"] * disp["preco_unitario"]).map(
                lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            )
            disp["preco_unitario"] = disp["preco_unitario"].map(
                lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            )
            disp = disp[["produto_nome","quantidade","preco_unitario","Total"]].rename(columns={
                "produto_nome":"Produto","quantidade":"Qtd","preco_unitario":"Unit."
            })
            st.dataframe(disp, hide_index=True, use_container_width=True)
        except Exception as e:
            st.caption(f"Itens: {str(e)}")

    # Botões de ação compactos
    col_edit, col_pdf, col_del, col_space = st.columns([1, 1, 1, 3])
    with col_edit:
        if st.button("✏️ Editar", key=f"det_edit_{venda_id}", use_container_width=True):
            st.session_state[f"editando_venda_{venda_id}"] = not st.session_state.get(f"editando_venda_{venda_id}", False)
            st.rerun()
    with col_pdf:
        if st.button("📄 PDF", key=f"det_pdf_{venda_id}", use_container_width=True):
            st.session_state[f"gerar_pdf_{venda_id}"] = True
            st.rerun()
    with col_del:
        if st.button("🗑️ Excluir", key=f"det_del_{venda_id}", use_container_width=True):
            st.session_state[f"confirmar_excluir_{venda_id}"] = True
            st.rerun()

    # Geração de PDF (após clicar no botão)
    if st.session_state.get(f"gerar_pdf_{venda_id}", False):
        st.session_state.pop(f"gerar_pdf_{venda_id}", None)
        try:
            from utils.pdf_generator_venda_fixed import gerar_pdf_venda
            import time as _time
            venda_dados = {
                "id": venda_row["id"],
                "status": venda_row.get("status", "Concluída"),
                "forma_pagamento": venda_row.get("forma_pagamento", ""),
                "valor_total": round(_safe_float(venda_row.get("valor_total", 0)), 2),
                "data_venda": venda_row.get("data_venda"),
                "observacoes": venda_row.get("observacoes", "")
            }
            prop_desc = venda_row.get("proposta_descricao") or None
            nome_raw = str(venda_row.get("cliente_nome", "cliente"))
            itens_pdf = itens_det  # usa os itens já carregados (com fallback proposta)
            os.makedirs("pdfs", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(int(_time.time()))
            safe_nome = nome_raw.replace(" ", "_").replace("/", "_").lower()
            pdf_path = gerar_pdf_venda(venda_dados, {"nome": nome_raw}, itens_pdf,
                                       f"pdfs/Venda_{venda_id}_{safe_nome}_{ts}.pdf",
                                       proposta_descricao=prop_desc)
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.success("PDF gerado!")
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"Venda_{venda_id}_{safe_nome}.pdf",
                    mime="application/pdf",
                    key=f"dl_pdf_{venda_id}"
                )
            else:
                st.error("Erro ao gerar PDF.")
        except Exception as e:
            st.error(f"Erro: {str(e)}")

    # Confirmação de exclusão
    if st.session_state.get(f"confirmar_excluir_{venda_id}", False):
        st.warning(f"⚠️ Excluir Venda #{venda_id} — {venda_row.get('cliente_nome','')}?")
        cc1, cc2, _ = st.columns([1, 1, 4])
        with cc1:
            if st.button("✓ Confirmar", type="primary", key=f"conf_del_{venda_id}", use_container_width=True):
                try:
                    st.session_state.db.excluir_venda(venda_id)
                    st.session_state["venda_selecionada"] = None
                    for k in [f"confirmar_excluir_{venda_id}", f"editando_venda_{venda_id}"]:
                        st.session_state.pop(k, None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with cc2:
            if st.button("✗ Cancelar", key=f"canc_del_{venda_id}", use_container_width=True):
                st.session_state.pop(f"confirmar_excluir_{venda_id}", None)
                st.rerun()

    # Painel de edição de itens
    if st.session_state.get(f"editando_venda_{venda_id}", False):
        with st.expander("✏️ Editar itens", expanded=True):
            try:
                itens_atuais = st.session_state.db.get_itens_venda(venda_id)
                produtos_df  = st.session_state.db.get_produtos()

                if not itens_atuais.empty:
                    for _, item in itens_atuais.iterrows():
                        ec1, ec2, ec3, ec4, ec5 = st.columns([3, 1, 1, 1, 1])
                        ec1.write(f"**{item['produto_nome']}**")
                        with ec2:
                            nova_qtd = st.number_input("Qtd", min_value=1, value=int(item["quantidade"]),
                                                       key=f"eq_{item['id']}", label_visibility="collapsed")
                        with ec3:
                            novo_preco = st.number_input("R$", min_value=0.01, value=float(item["preco_unitario"]),
                                                         format="%.2f", key=f"ep_{item['id']}", label_visibility="collapsed")
                        with ec4:
                            if st.button("💾", key=f"esv_{item['id']}", help="Salvar", use_container_width=True):
                                try:
                                    st.session_state.db.update_item_venda(item["id"], nova_qtd, novo_preco)
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))
                        with ec5:
                            if st.button("🗑️", key=f"erm_{item['id']}", help="Remover", use_container_width=True):
                                try:
                                    st.session_state.db.remove_item_venda(item["id"])
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))
                    st.markdown("---")

                if not produtos_df.empty:
                    with st.form(f"form_add_item_{venda_id}"):
                        ap1, ap2, ap3 = st.columns([3, 1, 1])
                        with ap1:
                            prods_lista = ["-- Selecione --"] + sorted(produtos_df["nome"].tolist())
                            novo_prod = st.selectbox("Produto", prods_lista, key=f"ap_prod_{venda_id}")
                        with ap2:
                            nova_qtd_add = st.number_input("Qtd", min_value=1, value=1, key=f"ap_qtd_{venda_id}")
                        with ap3:
                            preco_default = 0.01
                            if novo_prod != "-- Selecione --":
                                prow = produtos_df[produtos_df["nome"] == novo_prod].iloc[0]
                                preco_default = max(0.01, float(prow["preco_venda"]))
                            novo_preco_add = st.number_input("Preço", min_value=0.01, value=preco_default,
                                                             format="%.2f", key=f"ap_preco_{venda_id}")
                        if st.form_submit_button("➕ Adicionar produto", type="primary", use_container_width=True):
                            if novo_prod != "-- Selecione --":
                                try:
                                    pid_add = produtos_df[produtos_df["nome"] == novo_prod]["id"].iloc[0]
                                    st.session_state.db.add_item_venda(venda_id, pid_add, nova_qtd_add, novo_preco_add)
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))

                fe1, fe2 = st.columns(2)
                with fe1:
                    if st.button("✅ Salvar e fechar", type="primary", use_container_width=True, key=f"fin_edit_{venda_id}"):
                        try:
                            st.session_state.db.recalcular_valor_total_venda(venda_id)
                            st.session_state[f"editando_venda_{venda_id}"] = False
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
                with fe2:
                    if st.button("Cancelar", use_container_width=True, key=f"canc_edit_{venda_id}"):
                        st.session_state[f"editando_venda_{venda_id}"] = False
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {str(e)}")
                if st.button("Fechar", key=f"canc_edit_err_{venda_id}"):
                    st.session_state[f"editando_venda_{venda_id}"] = False
                    st.rerun()


def show():
    st.markdown("""
    <style>
    .vendas-page .main h2 { font-size: 1.1rem !important; font-weight: 700 !important; }
    .vendas-page .main h3 { font-size: 0.95rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
    .stTextInput input, .stSelectbox select,
    .stNumberInput input, .stDateInput input,
    .stTextArea textarea { font-size: 0.85rem !important; }
    label[data-testid="stWidgetLabel"] > div > p { font-size: 0.82rem !important; }
    .stButton > button:not([kind="primary"]) { font-size: 0.8rem !important; padding: 5px 12px !important; }
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
    .kanban-card-cliente { font-weight: 600; font-size: 0.82rem; margin-bottom: 1px; color: #1a202c; }
    .kanban-card-sub { font-size: 0.72rem; color: #6c757d; margin-bottom: 3px; }
    .kanban-card-valor { font-size: 0.78rem; color: #1a5276; font-weight: 600; }
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

    st.markdown('<div class="vendas-page">', unsafe_allow_html=True)

    if "db" not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown('<h1 style="font-size: 1.8rem; font-weight: 700; margin-top: 0; padding-top: 0; margin-bottom: 0.8rem;">🛒 Vendas</h1>', unsafe_allow_html=True)

    if "venda_selecionada" not in st.session_state:
        st.session_state["venda_selecionada"] = None
    if "vendas_nova_venda_open" not in st.session_state:
        st.session_state["vendas_nova_venda_open"] = False

    col_esp1, col_btn, col_esp2 = st.columns([1, 3, 1])
    with col_btn:
        with stylable_container(key="gold_nova_venda", css_styles="""
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
            if st.button("✚  Nova Venda", type="primary", use_container_width=True, key="btn_nova_venda_top"):
                st.session_state["vendas_nova_venda_open"] = not st.session_state["vendas_nova_venda_open"]
                if not st.session_state["vendas_nova_venda_open"]:
                    st.session_state.produtos_venda = []

    if st.session_state["vendas_nova_venda_open"]:
        with st.expander("🛒 Nova Venda", expanded=True):
            try:
                clientes_df = st.session_state.db.get_clientes()
                produtos_df = st.session_state.db.get_produtos()
                _render_nova_venda_form(clientes_df, produtos_df)
            except Exception as e:
                st.error(f"Erro ao carregar formulário: {str(e)}")

    # Relatório pós-finalização
    if st.session_state.get("mostrar_gerar_relatorio", False) and st.session_state.get("venda_recente_id"):
        st.markdown("---")
        st.success("🎉 Venda finalizada! Gere o relatório abaixo.")
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("📄 GERAR RELATÓRIO", type="primary", use_container_width=True, key="btn_rel_pos"):
                try:
                    from utils.pdf_generator_venda_fixed import gerar_pdf_venda
                    import time as _time
                    vid = st.session_state.venda_recente_id
                    vendas_tmp = st.session_state.db.get_vendas()
                    vrow = vendas_tmp[vendas_tmp["id"] == vid].iloc[0]
                    clientes_tmp = st.session_state.db.get_clientes()
                    crow = clientes_tmp[clientes_tmp["id"] == st.session_state.venda_recente_cliente_id].iloc[0]
                    itens_tmp = st.session_state.db.get_itens_venda(vid)
                    venda_dados = {
                        "id": vrow["id"], "status": vrow.get("status", "Concluída"),
                        "forma_pagamento": st.session_state.venda_recente_forma_pagamento,
                        "valor_total": st.session_state.venda_recente_valor_total,
                        "data_venda": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "observacoes": st.session_state.venda_recente_observacoes or ""
                    }
                    proposta_desc_pos = vrow.get("proposta_descricao") or None
                    safe = crow["nome"].replace(" ", "_").replace("/", "_").lower()
                    os.makedirs("pdfs", exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_path = gerar_pdf_venda(venda_dados, {"nome": crow["nome"]}, itens_tmp,
                                               f"pdfs/Venda_{vid}_{safe}_{ts}.pdf",
                                               proposta_descricao=proposta_desc_pos)
                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.success("PDF gerado!")
                        st.download_button("📥 Baixar PDF", data=pdf_bytes,
                                           file_name=f"Venda_{vid}_{safe}.pdf", mime="application/pdf",
                                           key="dl_rel_pos")
                    else:
                        st.error("Erro ao gerar PDF.")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with rc2:
            if st.button("✅ Nova venda", type="secondary", use_container_width=True, key="btn_nova_pos"):
                st.session_state.mostrar_gerar_relatorio = False
                for k in list(st.session_state.keys()):
                    if k.startswith("venda_recente_"):
                        del st.session_state[k]
                st.rerun()

    st.markdown("---")

    # Carregar dados
    try:
        vendas_df = st.session_state.db.get_vendas()
    except Exception as e:
        st.error(f"Erro ao carregar vendas: {str(e)}")
        return

    # Separar por status
    # "Confirmada" é equivalente a "Concluída" (status legado de versões anteriores)
    def _col_vendas(status_vals):
        if vendas_df.empty:
            return pd.DataFrame()
        if isinstance(status_vals, str):
            status_vals = [status_vals]
        return vendas_df[vendas_df["status"].isin(status_vals)].copy()

    vendas_concluidas = _col_vendas(["Concluída", "Confirmada"])
    vendas_pendentes  = _col_vendas(["Pendente", "Em aberto"])
    vendas_canceladas = _col_vendas(["Cancelada"])

    col_concluida, col_pendente, col_cancelada = st.columns(3)

    COLS_CONFIG = [
        (col_concluida, "✅ Concluída",  vendas_concluidas, "#d4edda"),
        (col_pendente,  "🟡 Pendente",   vendas_pendentes,  "#fff3cd"),
        (col_cancelada, "⛔ Cancelada",  vendas_canceladas, "#e2e3e5"),
    ]

    for col_idx, (col_widget, col_label, col_df, col_color) in enumerate(COLS_CONFIG):
        with col_widget:
            st.markdown(
                f'<div class="kanban-col-header" style="background-color:{col_color};">{col_label} ({len(col_df)})</div>',
                unsafe_allow_html=True
            )
            if not col_df.empty:
                # Ordenar por data mais recente
                col_df = col_df.sort_values("data_venda", ascending=False)
                for _, venda in col_df.iterrows():
                    vid = venda["id"]
                    cliente = html_module.escape(str(venda.get("cliente_nome", "Cliente")))
                    pagamento = html_module.escape(str(venda.get("forma_pagamento", "")))
                    data_str = html_module.escape(_fmt_date(venda.get("data_venda")))
                    valor_f = html_module.escape(_fmt_brl(venda.get("valor_total", 0)))

                    st.markdown(
                        f'<div class="kanban-card">'
                        f'<div class="kanban-card-cliente">{cliente}</div>'
                        f'<div class="kanban-card-sub">{pagamento} · {data_str}</div>'
                        f'<div class="kanban-card-valor">{valor_f}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    is_selected = st.session_state.get("venda_selecionada") == vid
                    btn_label = "▲ Fechar" if is_selected else "▼ Ver Detalhes"
                    if st.button(btn_label, key=f"card_btn_{col_idx}_{vid}", use_container_width=True):
                        if is_selected:
                            st.session_state["venda_selecionada"] = None
                        else:
                            st.session_state["venda_selecionada"] = vid
                        st.rerun()
            else:
                st.caption("Nenhuma venda nesta etapa.")

    # Rodapé com totais
    total_concluidas = vendas_concluidas["valor_total"].apply(_safe_float).sum() if not vendas_concluidas.empty else 0.0
    total_pendentes  = vendas_pendentes["valor_total"].apply(_safe_float).sum()  if not vendas_pendentes.empty  else 0.0
    total_canceladas = vendas_canceladas["valor_total"].apply(_safe_float).sum() if not vendas_canceladas.empty else 0.0

    st.markdown("---")
    fc1, fc2, fc3 = st.columns(3)
    for col, label, valor in [
        (fc1, "✅ Concluída",  total_concluidas),
        (fc2, "🟡 Pendente",   total_pendentes),
        (fc3, "⛔ Cancelada",  total_canceladas),
    ]:
        with col:
            st.markdown(f"""
            <div class="kanban-metric">
                <p class="kanban-metric-label">{label}</p>
                <p class="kanban-metric-value">{_fmt_brl(valor)}</p>
            </div>""", unsafe_allow_html=True)

    # Painel de detalhes
    selected_id = st.session_state.get("venda_selecionada")
    if selected_id is not None:
        st.markdown("---")
        if not vendas_df.empty:
            rows = vendas_df[vendas_df["id"] == selected_id]
            if not rows.empty:
                _render_detail_panel(selected_id, rows.iloc[0])
            else:
                st.warning("Venda não encontrada.")
                st.session_state["venda_selecionada"] = None

    # Análise por período (seção colapsável)
    st.markdown("---")
    with st.expander("📊 Análise por Período", expanded=False):
        try:
            if vendas_df.empty:
                custom_info("Nenhuma venda registrada para análise.")
            else:
                import numpy as np
                import plotly.express as px

                vendas_df["data_venda"] = pd.to_datetime(vendas_df["data_venda"])

                col1, col2, col3 = st.columns(3)
                with col1:
                    data_inicio = st.date_input("Data Inicial",
                        value=vendas_df["data_venda"].min().date(),
                        min_value=vendas_df["data_venda"].min().date(),
                        max_value=vendas_df["data_venda"].max().date(),
                        format="DD/MM/YYYY", key="analise_di")
                with col2:
                    data_fim = st.date_input("Data Final",
                        value=vendas_df["data_venda"].max().date(),
                        min_value=vendas_df["data_venda"].min().date(),
                        max_value=vendas_df["data_venda"].max().date(),
                        format="DD/MM/YYYY", key="analise_df")
                with col3:
                    tipo_agrupamento = st.selectbox("Agrupar por",
                        ["Dia", "Semana", "Mês", "Trimestre", "Ano"], key="analise_grupo")

                vp = vendas_df[
                    (vendas_df["data_venda"].dt.date >= data_inicio) &
                    (vendas_df["data_venda"].dt.date <= data_fim)
                ].copy()

                if vp.empty:
                    st.warning("Nenhuma venda no período.")
                else:
                    if tipo_agrupamento == "Dia":
                        vp["periodo"] = vp["data_venda"].dt.strftime("%d/%m/%Y")
                    elif tipo_agrupamento == "Semana":
                        vp["periodo"] = vp["data_venda"].dt.strftime("Semana %U/%Y")
                    elif tipo_agrupamento == "Mês":
                        vp["periodo"] = vp["data_venda"].dt.strftime("%m/%Y")
                    elif tipo_agrupamento == "Trimestre":
                        vp["periodo"] = vp["data_venda"].dt.to_period("Q").astype(str)
                    else:
                        vp["periodo"] = vp["data_venda"].dt.strftime("%Y")

                    analise = vp.groupby("periodo").agg(
                        Total_Vendas=("id", "count"),
                        Receita_Total=("valor_total", "sum"),
                        Ticket_Medio=("valor_total", "mean"),
                        Clientes_Unicos=("cliente_nome", "nunique")
                    ).round(2).reset_index()

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Vendas", f"{len(vp):,}")
                    m2.metric("Receita Total", _fmt_brl(vp["valor_total"].sum()))
                    m3.metric("Ticket Médio", _fmt_brl(vp["valor_total"].mean()))
                    m4.metric("Clientes Únicos", f"{vp['cliente_nome'].nunique():,}")

                    disp = analise.copy()
                    disp["Receita_Total"] = disp["Receita_Total"].apply(lambda x: f"R$ {x:,.2f}")
                    disp["Ticket_Medio"] = disp["Ticket_Medio"].apply(lambda x: f"R$ {x:.2f}")
                    disp.columns = ["Período", "Total Vendas", "Receita Total", "Ticket Médio", "Clientes Únicos"]
                    st.dataframe(disp, use_container_width=True, hide_index=True)

                    gc1, gc2 = st.columns(2)
                    with gc1:
                        fig = px.bar(analise, x="periodo", y="Receita_Total",
                                     title=f"Receita por {tipo_agrupamento}",
                                     labels={"periodo": "Período", "Receita_Total": "R$"},
                                     color_discrete_sequence=["#1f77b4"])
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    with gc2:
                        fig2 = px.line(analise, x="periodo", y="Total_Vendas",
                                       title=f"Nº Vendas por {tipo_agrupamento}",
                                       labels={"periodo": "Período", "Total_Vendas": "Qtd"},
                                       markers=True, color_discrete_sequence=["#ff7f0e"])
                        fig2.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig2, use_container_width=True)

                    # Top produtos
                    st.markdown("**🏆 Top Produtos no Período**")
                    try:
                        from sqlalchemy import text
                        vids = vp["id"].tolist()
                        if vids:
                            placeholders = ",".join(str(v) for v in vids)
                            q = text(f"""
                                SELECT
                                    COALESCE(p.nome, iv.descricao, 'Produto') AS nome,
                                    SUM(iv.quantidade)                        AS qtd,
                                    SUM(iv.quantidade * iv.preco_unitario)    AS receita,
                                    AVG(iv.preco_unitario)                    AS preco_medio
                                FROM itens_venda iv
                                LEFT JOIN produtos p ON iv.produto_id = p.id
                                WHERE iv.venda_id IN ({placeholders})
                                GROUP BY COALESCE(p.nome, iv.descricao, 'Produto')
                                ORDER BY qtd DESC
                                LIMIT 15
                            """)
                            res = st.session_state.db.session.execute(q)
                            top = pd.DataFrame(res.fetchall(), columns=["Produto", "Qtd", "Receita", "Preço Médio"])
                            if not top.empty:
                                top["Qtd"] = top["Qtd"].astype(int)
                                top["Receita"] = top["Receita"].apply(lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X","."))
                                top["Preço Médio"] = top["Preço Médio"].apply(lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X","."))
                                st.dataframe(top, use_container_width=True, hide_index=True)
                            else:
                                st.info("Estas vendas não possuem itens detalhados cadastrados. "
                                        "Novas vendas criadas pelo sistema já registram os produtos automaticamente.")
                    except Exception as e:
                        st.warning(f"Não foi possível carregar top produtos: {str(e)}")
        except Exception as e:
            st.error(f"Erro na análise: {str(e)}")
