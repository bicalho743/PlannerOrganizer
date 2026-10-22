"""
Vendas de produtos.

Regras (o banco garante, ver tests/test_vendas_integ.py):
- venda recebida na hora entra no Financeiro como recebida, na data da venda; venda a receber vira entrada +
  parcelas mensais pendentes. Assim as vendas aparecem no Início, no Financeiro e nos Relatórios;
- editar itens mantém o Financeiro igual ao total da venda e ajusta o estoque;
- o custo do produto fica gravado em cada item: a tela mostra o lucro e a margem de cada venda;
- cancelar mantém o histórico (devolve o estoque, cancela o que falta receber e lança a devolução do já recebido).

Tela: números do período (com comparação), quadro por situação do pagamento (Paga, A receber, Cancelada) com busca,
detalhes em janela e análise por período.
"""
import streamlit as st
import pandas as pd
import html as html_module
from datetime import datetime, date, timedelta
import os
import tempfile
from utils.custom_components import custom_info, custom_warning
from streamlit_extras.stylable_container import stylable_container
from utils.ui import botao_excluir, cartao_clicavel
from utils.design_tokens import (
    NAVY, NAVY_HOVER, GOLD, GOLD_BUTTON_CSS,
)


from utils.currency_formatter import fmt_brl as _fmt_brl
from utils.formatadores import valor_ou_traco

FORMAS_PAGAMENTO = ["PIX", "Cartão de crédito", "Cartão de débito", "Dinheiro", "Transferência", "Boleto"]
SITUACOES = [("Paga", "#d4edda"), ("A receber", "#fff3cd"), ("Cancelada", "#e2e3e5")]
PERIODOS_VENDA = {"Este mês": None, "Últimos 30 dias": 30, "Últimos 90 dias": 90, "Últimos 12 meses": 365, "Tudo": 0}


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


def _pct(v):
    return "—" if v is None or pd.isna(v) else f"{v * 100:.0f}%"


def _pdf_venda(venda_dados, cliente_dados, itens_df):
    """PDF da venda em bytes. Gera numa pasta temporária só desta chamada (antes ia para uma pasta comum do
    servidor com o nome da cliente: duas contas com cliente e número iguais podiam receber o arquivo uma da outra)."""
    from utils.pdf_generator_v2 import gerar_pdf_venda_v2
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, "venda.pdf")
        gerar_pdf_venda_v2(venda_dados, cliente_dados, itens_df, caminho)
        with open(caminho, "rb") as f:
            return f.read()


def _periodo(nome, hoje):
    """(início, fim) do filtro de período; início None = desde sempre."""
    if nome == "Este mês":
        return hoje.replace(day=1), hoje
    dias = PERIODOS_VENDA.get(nome, 0)
    return (hoje - timedelta(days=dias - 1), hoje) if dias else (None, hoje)


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
                else f"{produtos_df[produtos_df['id']==x]['nome'].iloc[0]} — {_fmt_brl(produtos_df[produtos_df['id']==x]['preco_venda'].iloc[0])}",
            key="nv_produto_id"
        )
    prod = produtos_df[produtos_df["id"] == produto_id].iloc[0] if produto_id else None
    with col2:
        quantidade = st.number_input("Qtd", min_value=1, value=1, key="nv_qtd", disabled=prod is None)
        if prod is not None:
            st.caption(f"Em estoque: {int(_safe_float(prod['estoque']))}")
    with col3:
        if prod is not None:
            st.metric("Total", _fmt_brl(quantidade * float(prod["preco_venda"])))

    if st.button("Adicionar à venda", type="primary", disabled=(prod is None), key="nv_add_produto"):
        for item in st.session_state.produtos_venda:
            if item["produto_id"] == produto_id:
                item["quantidade"] += quantidade
                item["total"] = item["quantidade"] * item["preco_unitario"]
                break
        else:
            st.session_state.produtos_venda.append({
                "produto_id": produto_id,
                "produto_nome": prod["nome"],
                "quantidade": quantidade,
                "preco_unitario": float(prod["preco_venda"]),
                "custo_unitario": _safe_float(prod.get("preco_custo")),
                "estoque": int(_safe_float(prod["estoque"])),
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
                if botao_excluir("🗑️", f"nv_rm_{i}", use_container_width=False, help="Remover"):
                    st.session_state.produtos_venda.pop(i)
                    st.rerun()

        total_venda = sum(item["total"] for item in st.session_state.produtos_venda)
        custo_venda = sum(item.get("custo_unitario", 0) * item["quantidade"] for item in st.session_state.produtos_venda)
        lucro = total_venda - custo_venda
        st.markdown(f"**Total: {_fmt_brl(total_venda)}** · lucro estimado {_fmt_brl(lucro)}"
                    + (f" ({lucro / total_venda:.0%})" if total_venda else ""))
        sem_estoque = [it["produto_nome"] for it in st.session_state.produtos_venda if it["quantidade"] > it.get("estoque", 0)]
        if sem_estoque:
            st.warning("Estoque insuficiente para: " + ", ".join(sem_estoque) +
                       ". A venda é registrada, mas o estoque desses produtos não baixa. Atualize o estoque em Cadastros → Produtos.")

        col1, col2 = st.columns(2)
        with col1:
            forma_pagamento = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO, key="nv_pagamento")
        with col2:
            data_venda = st.date_input("Data da venda", value=datetime.now().date(), format="DD/MM/YYYY", key="nv_data")

        recebimento = st.radio("Pagamento", ["Recebido na hora", "A receber"], horizontal=True, key="nv_receb",
                               help="A receber: o valor entra no Financeiro como pendente, com vencimento, e aparece em "
                                    "Relatórios › Próximos meses até ser marcado como recebido.")
        entrada, parcelas, primeiro_venc = 0.0, 1, None
        if recebimento == "A receber":
            r1, r2, r3 = st.columns(3)
            entrada = r1.number_input("Entrada recebida hoje (R$)", min_value=0.0, max_value=float(total_venda),
                                      value=0.0, step=10.0, format="%.2f", key="nv_entrada")
            parcelas = int(r2.number_input("Parcelas", min_value=1, max_value=24, value=1, key="nv_parcelas"))
            primeiro_venc = r3.date_input("1º vencimento", value=data_venda + timedelta(days=30), format="DD/MM/YYYY",
                                          key="nv_venc")
            resto = total_venda - entrada
            if resto > 0:
                st.caption(f"{parcelas}× de {_fmt_brl(resto / parcelas)}" if parcelas > 1 else f"{_fmt_brl(resto)} a receber")

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
                        data_venda=data_venda,
                        recebido=recebimento == "Recebido na hora",
                        entrada=entrada,
                        parcelas=parcelas,
                        primeiro_vencimento=primeiro_venc,
                    )
                    st.success(f"Venda #{venda_id} registrada com sucesso!")
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
    cliente_nome = html_module.escape(valor_ou_traco(venda_row.get("cliente_nome"), "Cliente"))
    situacao     = valor_ou_traco(venda_row.get("situacao") or venda_row.get("status"))
    data_str     = html_module.escape(_fmt_date(venda_row.get("data_venda")))
    pagamento    = valor_ou_traco(venda_row.get("forma_pagamento"))
    valor_str    = html_module.escape(_fmt_brl(venda_row.get("valor_total", 0)))
    obs_raw      = valor_ou_traco(venda_row.get("observacoes"), "")
    proposta_desc = valor_ou_traco(venda_row.get("proposta_descricao"), "")
    cancelada    = venda_row.get("status") == "Cancelada"

    meta_parts = [p for p in [data_str] if p and p != "—"]
    if pagamento and pagamento != "—":
        meta_parts.append(html_module.escape(pagamento))
    if proposta_desc:
        meta_parts.append(html_module.escape(proposta_desc))
    elif obs_raw:
        meta_parts.append(html_module.escape(obs_raw[:80]))
    meta_str = " · ".join(meta_parts)

    cores = {"Paga": ("#38A169", "#C6F6D5", "#276749"), "A receber": ("#D69E2E", "#FEFCBF", "#744210")}
    border_color, badge_bg, badge_fg = cores.get(situacao, ("#718096", "#EDF2F7", "#2D3748"))

    receb, a_receber = _safe_float(venda_row.get("recebido")), _safe_float(venda_row.get("a_receber"))
    lucro, margem = _safe_float(venda_row.get("lucro")), venda_row.get("margem")
    resumo = (f"Recebido {_fmt_brl(receb)}" + (f" · <b>falta receber {_fmt_brl(a_receber)}</b>" if a_receber else "")
              + ("" if cancelada else f" · lucro {_fmt_brl(lucro)} ({_pct(margem)})"
                 + (" — custo estimado pelo cadastro atual" if venda_row.get("custo_estimado") else "")))

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
                    <span class="det-badge">{html_module.escape(situacao)}</span>
                </p>
                <p class="det-meta">{cliente_nome} &nbsp;·&nbsp; {meta_str}</p>
                <p class="det-meta" style="margin-top:4px">{resumo}</p>
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
        except Exception as e:
            print(f"Erro: {e}")
        pid = venda_row.get("proposta_id")
        if pid and not pd.isna(pid):
            try:
                po = st.session_state.db.get_produtos_organizadores(proposta_id=int(pid))
                if not po.empty:
                    po = po.rename(columns={"nome": "produto_nome", "valor": "preco_unitario"})
                    po["subtotal"] = po["preco_unitario"] * po["quantidade"]
                    cols = ["produto_nome", "quantidade", "preco_unitario", "subtotal"]
                    if "comodo" in po.columns:
                        cols.append("comodo")
                    return po[cols]
            except Exception as e:
                print(f"Erro: {e}")
        return pd.DataFrame()

    itens_det = _get_itens_completo()

    if not itens_det.empty:
        try:
            disp = itens_det.copy()
            disp["Total"] = (disp["quantidade"] * disp["preco_unitario"]).map(_fmt_brl)
            disp["preco_unitario"] = disp["preco_unitario"].map(_fmt_brl)
            cols = {"produto_nome": "Produto", "quantidade": "Qtd", "preco_unitario": "Unit.", "Total": "Total"}
            if "lucro" in disp.columns:
                disp["lucro"] = disp["lucro"].apply(lambda v: "—" if v is None or pd.isna(v) else _fmt_brl(v))
                cols["lucro"] = "Lucro"
            st.dataframe(disp[list(cols)].rename(columns=cols), hide_index=True, use_container_width=True)
        except Exception as e:
            st.caption(f"Itens: {str(e)}")

    col_edit, col_canc, col_space = st.columns([1, 1, 3])
    with col_edit:
        if not cancelada and st.button("Editar", key=f"det_edit_{venda_id}", use_container_width=True):
            st.session_state[f"editando_venda_{venda_id}"] = not st.session_state.get(f"editando_venda_{venda_id}", False)
            st.rerun()
    with col_canc:
        if not cancelada:
            if botao_excluir("Cancelar venda", f"det_canc_{venda_id}"):
                st.session_state[f"confirmar_cancelar_{venda_id}"] = True
                st.rerun()
        elif botao_excluir("Excluir", f"det_del_{venda_id}", help="Apaga a venda cancelada de vez"):
            st.session_state[f"confirmar_excluir_{venda_id}"] = True
            st.rerun()

    try:
        nome_raw = str(venda_row.get("cliente_nome", "") or "")
        if not nome_raw or nome_raw in ("Cliente", "cliente", "Cliente não encontrado", "nan", "None"):
            nome_raw = "Cliente"
        safe_nome = nome_raw.replace(" ", "_").replace("/", "_").lower()
        numero_exibir = venda_row.get("proposta_numero") or venda_row.get("id", "")
        proposta_dados = {
            "id": numero_exibir,
            "tipo_proposta": "Venda",
            "status": situacao,
            "forma_pagamento": venda_row.get("forma_pagamento", ""),
            "valor_total": round(_safe_float(venda_row.get("valor_total", 0)), 2),
            "data_venda": venda_row.get("data_venda"),
            "observacoes": venda_row.get("observacoes", "")
        }
        pdf_bytes = _pdf_venda(proposta_dados, {"nome": nome_raw}, itens_det)
        # uma regra por item: o stylable_container só prefixa o começo de cada item
        _venda_css = [
            "button {"
            f"background:{NAVY} !important;border-radius:10px !important;"
            "padding:14px 24px !important;width:100% !important;"
            "border:1px solid transparent !important;transition:all 0.2s !important;}",
            "button:hover {"
            f"background:{NAVY_HOVER} !important;transform:translateY(-2px) !important;"
            "box-shadow:0 4px 12px rgba(0,0,0,0.3) !important;}",
            "button :is(p, div) {"
            f"color:{GOLD} !important;font-weight:700 !important;font-size:13px !important;}}",
        ]
        with stylable_container(key=f"dl_venda_{venda_id}", css_styles=_venda_css):
            st.download_button(
                label="Baixar PDF da Venda",
                data=pdf_bytes,
                file_name=f"Relatorio_Venda_{safe_nome}_{numero_exibir}.pdf",
                mime="application/pdf",
                key=f"dl_btn_venda_{venda_id}",
                use_container_width=True,
            )
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")

    # Confirmação de cancelamento: mantém o histórico
    if st.session_state.get(f"confirmar_cancelar_{venda_id}", False):
        st.warning(f"Cancelar a Venda #{venda_id} — {venda_row.get('cliente_nome','')}? Os produtos baixados voltam ao "
                   "estoque e o que falta receber sai do Financeiro.")
        devolver = False
        if receb > 0:
            devolver = st.checkbox(f"Vou devolver à cliente o que ela já pagou ({_fmt_brl(receb)})", value=True,
                                   key=f"canc_dev_{venda_id}",
                                   help="Lança a devolução como conta a pagar no Financeiro.")
        cc1, cc2, _ = st.columns([1, 1, 3])
        with cc1:
            if st.button("Confirmar cancelamento", type="primary", key=f"conf_canc_{venda_id}", use_container_width=True):
                try:
                    st.session_state.db.cancelar_venda(venda_id, devolver_recebido=devolver)
                    st.session_state.pop(f"confirmar_cancelar_{venda_id}", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with cc2:
            if st.button("Voltar", key=f"canc_canc_{venda_id}", use_container_width=True):
                st.session_state.pop(f"confirmar_cancelar_{venda_id}", None)
                st.rerun()

    # Confirmação de exclusão (só para vendas canceladas)
    if st.session_state.get(f"confirmar_excluir_{venda_id}", False):
        st.warning(f"Excluir de vez a Venda #{venda_id} — {venda_row.get('cliente_nome','')}? O histórico dela some.")
        cc1, cc2, _ = st.columns([1, 1, 4])
        with cc1:
            if st.button("Confirmar", type="primary", key=f"conf_del_{venda_id}", use_container_width=True):
                try:
                    st.session_state.db.excluir_venda(venda_id)
                    st.session_state["venda_selecionada"] = None
                    for k in [f"confirmar_excluir_{venda_id}", f"editando_venda_{venda_id}"]:
                        st.session_state.pop(k, None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with cc2:
            if st.button("Cancelar", key=f"canc_del_{venda_id}", use_container_width=True):
                st.session_state.pop(f"confirmar_excluir_{venda_id}", None)
                st.rerun()

    # Painel de edição de itens
    if st.session_state.get(f"editando_venda_{venda_id}", False):
        with st.expander("Editar itens", expanded=True):
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
                            if botao_excluir("🗑️", f"erm_{item['id']}", help="Remover"):
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
                        if st.form_submit_button("Adicionar produto", type="primary", use_container_width=True):
                            if novo_prod != "-- Selecione --":
                                try:
                                    pid_add = produtos_df[produtos_df["nome"] == novo_prod]["id"].iloc[0]
                                    st.session_state.db.add_item_venda(venda_id, pid_add, nova_qtd_add, novo_preco_add)
                                    st.rerun()
                                except Exception as ex:
                                    st.error(str(ex))

                fe1, fe2 = st.columns(2)
                with fe1:
                    if st.button("Salvar e fechar", type="primary", use_container_width=True, key=f"fin_edit_{venda_id}"):
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




def _metricas(vp, comp):
    """Números do período com a variação contra o período anterior de mesmo tamanho."""
    def soma(df, c):
        return float(df[c].apply(_safe_float).sum()) if not df.empty else 0.0

    def delta(a, b):
        if not b:
            return ""
        v = (a - b) / abs(b)
        cor = "#067647" if v >= 0 else "#B42318"
        return f'<span style="color:{cor};font-weight:600">{"▲" if v >= 0 else "▼"} {abs(v):.0%}</span> vs anterior'

    fat, fat_c = soma(vp, "valor_total"), soma(comp, "valor_total")
    luc, luc_c = soma(vp, "lucro"), soma(comp, "lucro")
    n, n_c = len(vp), len(comp)
    tk = fat / n if n else 0.0
    tk_c = fat_c / n_c if n_c else 0.0
    return [("Vendas", f"{n}", delta(n, n_c)), ("Faturamento", _fmt_brl(fat), delta(fat, fat_c)),
            ("Ticket médio", _fmt_brl(tk), delta(tk, tk_c)),
            ("Lucro", _fmt_brl(luc), " · ".join(x for x in [f"margem {luc / fat:.0%}" if fat else "", delta(luc, luc_c)] if x))]


def show():
    from utils.auth_guard import require_auth
    require_auth()
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
    .kanban-card-falta { font-size: 0.72rem; color: #B54708; font-weight: 600; }
    .vd-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; margin: 4px 0 12px; }
    .vd-kpi { background: #fff; border: 1px solid #E4E7EC; border-radius: 12px; padding: 12px 14px; }
    .vd-kpi .rot { font-size: .7rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; }
    .vd-kpi .val { font-size: 1.2rem; font-weight: 700; color: #101828; margin: 3px 0 2px; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .vd-kpi .sub { font-size: .76rem; color: #667085; display: block; line-height: 1.4; }
    .vd-kpi.alerta { border-color: #FEC84B; background: #FFFAEB; }
    @media (max-width: 900px) { .vd-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="vendas-page">', unsafe_allow_html=True)

    if "db" not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown('<h1 class="page-title">Vendas</h1>', unsafe_allow_html=True)

    if "venda_selecionada" not in st.session_state:
        st.session_state["venda_selecionada"] = None
    if "vendas_nova_venda_open" not in st.session_state:
        st.session_state["vendas_nova_venda_open"] = False

    try:
        vendas_df = st.session_state.db.get_vendas()
    except Exception as e:
        st.warning(f"Erro ao carregar vendas: {str(e)}")
        vendas_df = pd.DataFrame()
    if vendas_df is None:
        vendas_df = pd.DataFrame()
    if not vendas_df.empty:
        vendas_df["data_venda"] = pd.to_datetime(vendas_df["data_venda"], errors="coerce")
        if "situacao" not in vendas_df:
            vendas_df["situacao"] = vendas_df["status"]

    # vendas registradas antes da correção ficaram como "Pendente" no Financeiro, mesmo pagas na hora
    try:
        n_antigas = st.session_state.db.contar_vendas_antigas_pendentes()
    except Exception:
        n_antigas = 0
    if n_antigas:
        with st.container(border=True):
            st.markdown(f"**{n_antigas} venda{'s' if n_antigas != 1 else ''} antiga{'s' if n_antigas != 1 else ''} "
                        f"aparece{'m' if n_antigas != 1 else ''} como “a receber” no Financeiro.** Até agora toda venda feita "
                        "nesta tela entrava como pendente, mesmo paga na hora, e por isso não contava no faturamento. "
                        "Se elas já foram pagas, marque como recebidas (na data de cada venda).")
            if st.button("Marcar vendas antigas como recebidas", key="vd_marcar_antigas"):
                n = st.session_state.db.marcar_vendas_antigas_recebidas()
                st.success(f"{n} venda{'s' if n != 1 else ''} marcada{'s' if n != 1 else ''} como recebida{'s' if n != 1 else ''}.")
                st.rerun()

    hoje = datetime.now().date()
    f1, f2 = st.columns([1, 2])
    nome_periodo = f1.selectbox("Período", list(PERIODOS_VENDA), index=2, key="vd_periodo")
    busca = f2.text_input("Buscar cliente ou observação", key="vd_busca", placeholder="Nome da cliente…")
    ini, fim = _periodo(nome_periodo, hoje)

    def _no_periodo(df, i, f):
        if df.empty:
            return df
        d = df["data_venda"].dt.date
        return df[(d >= i) & (d <= f)] if i else df[d <= f]

    vp = _no_periodo(vendas_df, ini, fim)
    if busca and not vp.empty:
        b = busca.strip().lower()
        vp = vp[vp["cliente_nome"].astype(str).str.lower().str.contains(b, regex=False)
                | vp["observacoes"].astype(str).str.lower().str.contains(b, regex=False)]
    ativas = vp[vp["situacao"] != "Cancelada"] if not vp.empty else vp
    comp = pd.DataFrame()
    if ini and not vendas_df.empty:
        dur = (fim - ini).days + 1
        comp = _no_periodo(vendas_df, ini - timedelta(days=dur), ini - timedelta(days=1))
        comp = comp[comp["situacao"] != "Cancelada"]
    a_receber = float(vendas_df["a_receber"].apply(_safe_float).sum()) if "a_receber" in vendas_df else 0.0
    n_abertas = int((vendas_df["a_receber"].apply(_safe_float) > 0.004).sum()) if "a_receber" in vendas_df else 0
    cards = "".join(f'<div class="vd-kpi"><span class="rot">{r}</span><div class="val">{v}</div><span class="sub">{s or "&nbsp;"}</span></div>'
                    for r, v, s in _metricas(ativas, comp if ini else ativas.iloc[0:0]))
    cards += (f'<div class="vd-kpi{" alerta" if a_receber else ""}"><span class="rot">A receber</span>'
              f'<div class="val">{_fmt_brl(a_receber)}</div><span class="sub">{n_abertas} venda{"s" if n_abertas != 1 else ""} '
              'em aberto, de qualquer data</span></div>')
    st.markdown(f'<div class="vd-kpis">{cards}</div>', unsafe_allow_html=True)

    col_esp1, col_btn, col_esp2 = st.columns([1, 3, 1])
    with col_btn:
        with stylable_container(key="gold_nova_venda", css_styles=list(GOLD_BUTTON_CSS)):
            if st.button("Nova venda", type="primary", icon=":material/add:", use_container_width=True, key="btn_nova_venda_top"):
                st.session_state["vendas_nova_venda_open"] = not st.session_state["vendas_nova_venda_open"]
                if not st.session_state["vendas_nova_venda_open"]:
                    st.session_state.produtos_venda = []

    if st.session_state["vendas_nova_venda_open"]:
        with st.expander("Nova Venda", expanded=True):
            try:
                clientes_df = st.session_state.db.get_clientes()
                produtos_df = st.session_state.db.get_produtos()
                _render_nova_venda_form(clientes_df, produtos_df)
            except Exception as e:
                st.error(f"Erro ao carregar formulário: {str(e)}")

    # Relatório pós-finalização
    if st.session_state.get("mostrar_gerar_relatorio", False) and st.session_state.get("venda_recente_id"):
        st.markdown("---")
        st.success("Venda finalizada! Gere o relatório abaixo.")
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("GERAR RELATÓRIO", type="primary", use_container_width=True, key="btn_rel_pos"):
                try:
                    vid = st.session_state.venda_recente_id
                    vrow = vendas_df[vendas_df["id"] == vid].iloc[0]
                    itens_tmp = st.session_state.db.get_itens_venda(vid)
                    nome = str(vrow.get("cliente_nome") or "Cliente")
                    proposta_dados = {
                        "id": vrow.get("proposta_numero") or vrow["id"],
                        "tipo_proposta": "Venda",
                        "status": vrow.get("situacao", "Paga"),
                        "forma_pagamento": st.session_state.venda_recente_forma_pagamento,
                        "valor_total": st.session_state.venda_recente_valor_total,
                        "data_venda": vrow["data_venda"],
                        "observacoes": st.session_state.venda_recente_observacoes or ""
                    }
                    pdf_bytes = _pdf_venda(proposta_dados, {"nome": nome}, itens_tmp)
                    safe = nome.replace(" ", "_").replace("/", "_").lower()
                    st.success("PDF gerado!")
                    st.download_button("Baixar PDF", data=pdf_bytes, file_name=f"Venda_{vid}_{safe}.pdf",
                                       mime="application/pdf", key="dl_rel_pos")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        with rc2:
            if st.button("Nova venda", type="secondary", use_container_width=True, key="btn_nova_pos"):
                st.session_state.mostrar_gerar_relatorio = False
                for k in list(st.session_state.keys()):
                    if k.startswith("venda_recente_"):
                        del st.session_state[k]
                st.rerun()

    st.markdown("---")

    # quadro por situação do pagamento; "A receber" mostra todas as vendas em aberto, de qualquer data
    abertas = vendas_df[(vendas_df["situacao"] == "A receber")] if not vendas_df.empty else vendas_df
    if busca and not abertas.empty:
        b = busca.strip().lower()
        abertas = abertas[abertas["cliente_nome"].astype(str).str.lower().str.contains(b, regex=False)]
    colunas = st.columns(3)
    for col_idx, ((rotulo, cor), col_widget) in enumerate(zip(SITUACOES, colunas)):
        col_df = abertas if rotulo == "A receber" else (vp[vp["situacao"] == rotulo] if not vp.empty else vp)
        with col_widget:
            st.markdown(f'<div class="kanban-col-header" style="background-color:{cor};">{rotulo} ({len(col_df)})</div>',
                        unsafe_allow_html=True)
            if col_df.empty:
                st.caption("Nenhuma venda nesta situação." if rotulo == "A receber" else "Nenhuma venda neste período.")
                continue
            col_df = col_df.sort_values("data_venda", ascending=False)
            limite = 30
            for _, venda in col_df.head(limite).iterrows():
                vid = venda["id"]
                cliente = html_module.escape(valor_ou_traco(venda.get("cliente_nome"), "Cliente"))
                pagamento = html_module.escape(valor_ou_traco(venda.get("forma_pagamento"), ""))
                data_str = html_module.escape(_fmt_date(venda.get("data_venda")))
                valor_f = html_module.escape(_fmt_brl(venda.get("valor_total", 0)))
                sub_html = " · ".join(p for p in [pagamento, data_str] if p)
                falta = _safe_float(venda.get("a_receber"))
                extra = f'<div class="kanban-card-falta">falta {html_module.escape(_fmt_brl(falta))}</div>' if falta else ""
                if cartao_clicavel(
                    f'<div class="kanban-card">'
                    f'<div class="kanban-card-cliente">{cliente}</div>'
                    f'<div class="kanban-card-sub">{sub_html}</div>'
                    f'<div class="kanban-card-valor">{valor_f}</div>{extra}'
                    f'</div>',
                    key=f"card_btn_{col_idx}_{vid}", rotulo=f"Abrir venda de {cliente}"):
                    st.session_state["venda_selecionada"] = vid
                    st.rerun()
            if len(col_df) > limite:
                st.caption(f"e mais {len(col_df) - limite}. Use a busca ou um período menor.")

    # Detalhes em modal centralizado (mesmo padrão do Financeiro e das Propostas)
    selected_id = st.session_state.get("venda_selecionada")
    if selected_id is not None and not vendas_df.empty:
        rows = vendas_df[vendas_df["id"] == selected_id]
        if not rows.empty:
            venda_sel = rows.iloc[0]

            @st.dialog("Detalhes da Venda", width="large")
            def _modal_venda():
                _render_detail_panel(selected_id, venda_sel)
                st.markdown("---")
                if st.button("Fechar", key=f"venda_fechar_modal_{selected_id}", use_container_width=True):
                    st.session_state["venda_selecionada"] = None
                    st.rerun()

            _modal_venda()
        else:
            st.session_state["venda_selecionada"] = None

    # Análise por período (seção colapsável)
    st.markdown("---")
    with st.expander("Análise por período", expanded=False):
        _analise(vendas_df[vendas_df["situacao"] != "Cancelada"] if not vendas_df.empty else vendas_df)


def _analise(vendas_df):
    try:
        if vendas_df.empty:
            custom_info("Nenhuma venda registrada para análise.")
            return
        import plotly.express as px
        col1, col2, col3 = st.columns(3)
        dmin, dmax = vendas_df["data_venda"].min().date(), vendas_df["data_venda"].max().date()
        with col1:
            data_inicio = st.date_input("Data Inicial", value=dmin, min_value=dmin, max_value=dmax,
                                        format="DD/MM/YYYY", key="analise_di")
        with col2:
            data_fim = st.date_input("Data Final", value=dmax, min_value=dmin, max_value=dmax,
                                     format="DD/MM/YYYY", key="analise_df")
        with col3:
            tipo_agrupamento = st.selectbox("Agrupar por", ["Dia", "Semana", "Mês", "Trimestre", "Ano"], index=2,
                                            key="analise_grupo")
        vp = vendas_df[(vendas_df["data_venda"].dt.date >= data_inicio) & (vendas_df["data_venda"].dt.date <= data_fim)].copy()
        if vp.empty:
            st.warning("Nenhuma venda no período.")
            return
        fmt = {"Dia": "%d/%m/%Y", "Semana": "Semana %U/%Y", "Mês": "%m/%Y", "Ano": "%Y"}
        vp["periodo"] = (vp["data_venda"].dt.to_period("Q").astype(str) if tipo_agrupamento == "Trimestre"
                         else vp["data_venda"].dt.strftime(fmt[tipo_agrupamento]))
        vp["ordem"] = vp["data_venda"]
        for c in ("valor_total", "lucro"):
            vp[c] = vp[c].apply(_safe_float)
        analise = vp.groupby("periodo").agg(
            ordem=("ordem", "min"), Total_Vendas=("id", "count"), Receita_Total=("valor_total", "sum"),
            Lucro=("lucro", "sum"), Ticket_Medio=("valor_total", "mean"), Clientes_Unicos=("cliente_nome", "nunique")
        ).sort_values("ordem").drop(columns="ordem").round(2).reset_index()
        analise["Margem"] = (analise["Lucro"] / analise["Receita_Total"]).where(analise["Receita_Total"] > 0)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Vendas", f"{len(vp):,}")
        m2.metric("Receita Total", _fmt_brl(vp["valor_total"].sum()))
        m3.metric("Lucro", _fmt_brl(vp["lucro"].sum()))
        m4.metric("Clientes Únicos", f"{vp['cliente_nome'].nunique():,}")

        disp = analise.copy()
        for c in ("Receita_Total", "Lucro", "Ticket_Medio"):
            disp[c] = disp[c].apply(_fmt_brl)
        disp["Margem"] = disp["Margem"].apply(_pct)
        disp = disp[["periodo", "Total_Vendas", "Receita_Total", "Lucro", "Margem", "Ticket_Medio", "Clientes_Unicos"]]
        disp.columns = ["Período", "Vendas", "Receita", "Lucro", "Margem", "Ticket médio", "Clientes"]
        st.dataframe(disp, use_container_width=True, hide_index=True)

        fig = px.bar(analise, x="periodo", y=["Receita_Total", "Lucro"], barmode="group",
                     title=f"Receita e lucro por {tipo_agrupamento.lower()}",
                     labels={"periodo": "Período", "value": "R$", "variable": ""},
                     color_discrete_sequence=[NAVY, GOLD])
        fig.for_each_trace(lambda t: t.update(name={"Receita_Total": "Receita", "Lucro": "Lucro"}[t.name]))
        fig.update_layout(xaxis_tickangle=-45, separators=",.")
        st.plotly_chart(fig, use_container_width=True)

        # produtos que mais vendem e que mais dão lucro (custo gravado na venda; itens antigos usam o custo atual)
        st.markdown("**Produtos no período**")
        from sqlalchemy import text
        vids = [int(v) for v in vp["id"].tolist()]
        if vids:
            q = text("""
                SELECT COALESCE(p.nome, iv.descricao, 'Produto') AS nome,
                       SUM(iv.quantidade) AS qtd,
                       SUM(iv.quantidade * iv.preco_unitario) AS receita,
                       SUM(iv.quantidade * (iv.preco_unitario - COALESCE(iv.custo_unitario, p.preco_custo, 0))) AS lucro
                FROM itens_venda iv
                LEFT JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = ANY(:ids)
                GROUP BY COALESCE(p.nome, iv.descricao, 'Produto')
                ORDER BY receita DESC
                LIMIT 15
            """)
            res = st.session_state.db.session.execute(q, {"ids": vids})
            top = pd.DataFrame(res.fetchall(), columns=["Produto", "Qtd", "Receita", "Lucro"])
            if not top.empty:
                top["Margem"] = (top["Lucro"].astype(float) / top["Receita"].astype(float)).where(top["Receita"].astype(float) > 0)
                top["Qtd"] = top["Qtd"].astype(int)
                for c in ("Receita", "Lucro"):
                    top[c] = top[c].astype(float).apply(_fmt_brl)
                top["Margem"] = top["Margem"].apply(_pct)
                st.dataframe(top, use_container_width=True, hide_index=True)
            else:
                st.info("Estas vendas não possuem itens detalhados cadastrados.")
    except Exception as e:
        st.error(f"Erro na análise: {str(e)}")
