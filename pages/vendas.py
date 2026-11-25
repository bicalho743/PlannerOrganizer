"""
Vendas de produtos.

Regras (o banco garante, ver tests/test_vendas_integ.py):
- venda recebida na hora entra no Financeiro como recebida, na data da venda; venda a receber vira entrada +
  parcelas mensais pendentes. Assim as vendas aparecem no Início, no Financeiro e nos Relatórios;
- editar itens mantém o Financeiro igual ao total da venda e ajusta o estoque;
- o custo do produto fica gravado em cada item: a tela mostra o lucro e a margem de cada venda;
- cancelar mantém o histórico (devolve o estoque, cancela o que falta receber e lança a devolução do já recebido).

Tela (protótipo "vendas"): números do período (lucro, vendido, a receber, estoque baixo), vendas recentes com busca,
período e filtro por situação, Repor estoque (com lançamento de compra) e Mais vendidos, detalhes em janela, tabela de
todas as vendas e análise por período.
"""
import streamlit as st
import pandas as pd
import html as html_module
from datetime import datetime, date, timedelta
import os
import tempfile
from utils.custom_components import custom_info, custom_warning
from utils.ui import botao_excluir, botao_editar, botao_documento, cartao_clicavel
from utils.design_tokens import (
    NAVY, NAVY_HOVER, GOLD,
)


from utils.currency_formatter import fmt_brl as _fmt_brl
from utils.formatadores import valor_ou_traco
from utils import visual
from utils.visual import esc

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

    # Mesma busca da proposta: lista em ordem alfabética, começa vazia (digite para filtrar)
    cliente_id = st.selectbox(
        "Cliente",
        options=clientes_df["id"].tolist(),
        format_func=lambda x: clientes_df[clientes_df["id"] == x]["nome"].iloc[0],
        index=None,
        placeholder="Digite o nome do cliente",
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
                if botao_excluir("Remover", f"nv_rm_{i}", use_container_width=False, help="Remover da venda"):
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
            data_venda = st.date_input("Data da venda", value=visual.hoje(), format="DD/MM/YYYY", key="nv_data")

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
            finalizar = st.button("FINALIZAR VENDA", type="primary", use_container_width=True, key="nv_finalizar")
            if finalizar and cliente_id is None:
                st.error("Selecione um cliente antes de finalizar a venda.")
            elif finalizar:
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

    # editar e, ao lado, cancelar/excluir (vermelho) menor — mesmo arranjo do Financeiro
    col_edit, col_canc, _ = st.columns([2, 1.4, 2.6])
    with col_edit:
        if not cancelada and botao_editar("Editar itens", key=f"det_edit_{venda_id}", use_container_width=True):
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
        st.download_button(
            label="Baixar PDF da venda",
            data=pdf_bytes,
            file_name=f"Relatorio_Venda_{safe_nome}_{numero_exibir}.pdf",
            mime="application/pdf",
            key=f"dl_btn_venda_{venda_id}",
            icon=":material/download:",
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

                # quantidade e preço mudam só nos campos; "Salvar e fechar" grava tudo de uma vez.
                # Remover e Adicionar produto gravam na hora.
                _chaves_itens = [k for i in itens_atuais["id"] for k in (f"eq_{i}", f"ep_{i}")] if not itens_atuais.empty else []
                if not itens_atuais.empty:
                    ch1, ch2, ch3, _ = st.columns([3, 1, 1, 1])
                    ch2.caption("Qtd")
                    ch3.caption("Preço unit.")
                    for _, item in itens_atuais.iterrows():
                        ec1, ec2, ec3, ec5 = st.columns([3, 1, 1, 1], vertical_alignment="center")
                        ec1.write(f"**{item['produto_nome']}**")
                        with ec2:
                            nova_qtd = st.number_input("Qtd", min_value=1, value=int(item["quantidade"]),
                                                       key=f"eq_{item['id']}", label_visibility="collapsed")
                        with ec3:
                            novo_preco = st.number_input("R$", min_value=0.01, value=float(item["preco_unitario"]),
                                                         format="%.2f", key=f"ep_{item['id']}", label_visibility="collapsed")
                        with ec5:
                            if botao_excluir("Remover", f"erm_{item['id']}", help="Remove o item da venda agora"):
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
                            for _, item in itens_atuais.iterrows():
                                q = int(st.session_state.get(f"eq_{item['id']}", item["quantidade"]))
                                pr = float(st.session_state.get(f"ep_{item['id']}", item["preco_unitario"]))
                                if q != int(item["quantidade"]) or round(pr, 2) != round(float(item["preco_unitario"]), 2):
                                    st.session_state.db.update_item_venda(item["id"], q, pr)
                            st.session_state.db.recalcular_valor_total_venda(venda_id)
                            for k in _chaves_itens:
                                st.session_state.pop(k, None)
                            st.session_state[f"editando_venda_{venda_id}"] = False
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
                with fe2:
                    if st.button("Cancelar", use_container_width=True, key=f"canc_edit_{venda_id}"):
                        for k in _chaves_itens:  # descarta o que foi mudado nos campos
                            st.session_state.pop(k, None)
                        st.session_state[f"editando_venda_{venda_id}"] = False
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {str(e)}")
                if st.button("Fechar", key=f"canc_edit_err_{venda_id}", type="tertiary"):
                    st.session_state[f"editando_venda_{venda_id}"] = False
                    st.rerun()




def _delta(a, b):
    """Variação contra o período anterior de mesmo tamanho ('' se não há base)."""
    if not b:
        return ""
    v = (a - b) / abs(b)
    cor = "#2F6B4F" if v >= 0 else "#9B2C2C"
    return f'<span style="color:{cor};font-weight:600">{"▲" if v >= 0 else "▼"} {abs(v):.0%}</span> vs anterior'


def _metricas(vp, comp):
    """Números do período: (vendas, faturamento, ticket médio, lucro, margem) e as variações contra o anterior."""
    def soma(df, c):
        return float(df[c].apply(_safe_float).sum()) if not df.empty else 0.0

    fat, fat_c = soma(vp, "valor_total"), soma(comp, "valor_total")
    luc, luc_c = soma(vp, "lucro"), soma(comp, "lucro")
    n, n_c = len(vp), len(comp)
    tk = fat / n if n else 0.0
    tk_c = fat_c / n_c if n_c else 0.0
    return {"n": n, "fat": fat, "tk": tk, "luc": luc, "margem": (luc / fat) if fat else None,
            "d_fat": _delta(fat, fat_c), "d_luc": _delta(luc, luc_c), "d_tk": _delta(tk, tk_c), "d_n": _delta(n, n_c)}


# ícones de traço (mesma família do menu); sem emoji
_IC_SACOLA = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
              'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8h12l-1 13H7z"/>'
              '<path d="M9 8a3 3 0 0 1 6 0"/></svg>')
_IC_CANCEL = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
              'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="m9 9 6 6M15 9l-6 6"/></svg>')

CSS = """
<style>
.vd-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.vd-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.vd-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.vd-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 4px; }
.st-key-vd_acoes { padding-top: 44px; }
.st-key-vd_acoes [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; align-items: center; justify-content: flex-end; gap: 10px !important; }
.st-key-vd_acoes [data-testid="stColumn"] { width: auto !important; min-width: 0 !important; flex: 0 1 auto !important; }
.st-key-vd_produtos button, .st-key-vd_produtos button p { color: #9C7A22 !important; font-weight: 700 !important; white-space: nowrap; }
.st-key-cta_vd_nova .stButton > button { min-height: 46px; padding: 0 20px; border-radius: 10px; white-space: nowrap; }
.vd-kpis { display: grid; grid-template-columns: 1.2fr 1fr 1fr 1fr; gap: 12px; margin: 18px 0 22px; }
.vd-kpi { background: #fff; border: 1px solid #E7E2D6; border-radius: 16px; padding: 18px 20px; min-width: 0; }
.vd-kpi .rot { font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #5B6B80; }
.vd-kpi .val { font-size: 1.6rem; font-weight: 700; color: var(--navy); margin: 8px 0 4px; font-variant-numeric: tabular-nums;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.vd-kpi .val.verde { color: #2F6B4F; }
.vd-kpi .val.verm { color: #9B2C2C; }
.vd-kpi .sub { font-size: .8rem; color: #5B6B80; line-height: 1.4; display: block; }
.vd-kpi.destaque { background: var(--navy); border-color: var(--navy); }
.vd-kpi.destaque .rot { color: var(--gold); }
.vd-kpi.destaque .val { color: #fff; }
.vd-kpi.destaque .sub { color: #C8D1DC; }
.vd-secao { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #4A5B73; margin: 4px 0 10px; }
.vd-row { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #E7E2D6 !important; border-radius: 12px !important;
          padding: 12px 14px !important; margin-bottom: 0 !important; box-shadow: none !important; min-width: 0; }
.vd-row .ic { flex: none; width: 34px; height: 34px; border-radius: 10px; background: #F6EDD3; color: #7A5F0B;
              display: flex; align-items: center; justify-content: center; }
.vd-row .ic.canc { background: #F2F4F7; color: #667085; }
.vd-row .tx { min-width: 0; flex: 1; }
.vd-row .tx b { display: block; color: var(--navy); font-size: .9rem; overflow-wrap: anywhere; }
.vd-row .tx .d { display: block; font-size: .8rem; color: #5B6B80; overflow-wrap: anywhere; }
.vd-row .dir { display: flex; align-items: center; gap: 12px; flex: none; }
.vd-row .v { font-weight: 700; font-size: .9rem; color: var(--navy); white-space: nowrap; font-variant-numeric: tabular-nums; }
.vd-row.cancelada .tx b, .vd-row.cancelada .v { color: #98A2B3; text-decoration: line-through; }
[class*="st-key-kcard_vdr_"] { margin-bottom: 8px; }
.vd-kpi.destaque .sub span { color: #A8D5BA !important; }
.st-key-vd_cab_lista [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; align-items: center; row-gap: 6px; }
.st-key-vd_cab_lista [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; width: auto !important; min-width: 0 !important; }
.st-key-vd_cab_lista [data-testid="stColumn"]:last-child { flex: 0 1 auto !important; width: auto !important; min-width: 0 !important; }
.st-key-vd_cab_lista .vd-secao { margin: 0; }
.st-key-vd_cab_lista [data-testid="stColumn"] { height: auto !important; }
.st-key-vd_situacao [data-testid="stButtonGroup"] > div { gap: 6px; flex-wrap: wrap; }
.st-key-vd_situacao button { border-radius: 999px !important; border: 1px solid #E7E2D6 !important; background: #fff !important;
                             min-height: 30px !important; padding: 2px 12px !important; }
.st-key-vd_situacao button p { font-size: .82rem !important; font-weight: 600 !important; color: #5B6B80 !important; }
.st-key-vd_situacao button[aria-checked="true"] { background: var(--navy) !important; border-color: var(--navy) !important; }
.st-key-vd_situacao button[aria-checked="true"] p { color: #fff !important; }
.vd-pil { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; font-size: .74rem;
          font-weight: 700; white-space: nowrap; line-height: 1.3; }
.vd-pil.ok { background: #E3F1E8; color: #2F6B4F; }
.vd-pil.ab { border: 1.5px solid #C9A84C; color: #7A5F0B; background: #fff; }
.vd-pil.cc { background: #F2F4F7; color: #667085; }
[class*="st-key-vdc_"] { background: #fff; border-radius: 16px !important; border-color: #E7E2D6 !important; padding: 18px !important; }
.vd-h4 { font-size: 1rem; font-weight: 700; color: var(--navy); margin: 0 0 6px; }
.vd-li { display: flex; justify-content: space-between; gap: 10px; font-size: .9rem; padding: 9px 0; border-top: 1px solid #F0ECE3; }
.vd-li span { color: #5B6B80; overflow-wrap: anywhere; }
.vd-li b { color: var(--navy); white-space: nowrap; }
.vd-li b.verm { color: #9B2C2C; }
.vd-nota { font-size: .8rem; color: #5B6B80; margin-top: 6px; }
.vd-vazio { color: #5B6B80; font-size: .9rem; padding: 6px 0 2px; }
.st-key-vd_compra_btn .stButton > button { background: #fff !important; color: var(--navy) !important; border: 1px solid #E7E2D6 !important;
                                           min-height: 46px; font-weight: 700 !important; border-radius: 10px; }
.st-key-vd_compra_btn .stButton > button p { font-weight: 700 !important; }
.st-key-vd_compra_btn .stButton > button:hover { border-color: var(--gold) !important; }
.st-key-vd_filtros [data-testid="stHorizontalBlock"] { align-items: flex-end; }
.st-key-vd_mais button, .st-key-vd_mais button p { color: #9C7A22 !important; font-weight: 700 !important; }
.st-key-vd_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { align-items: flex-start; }
.vd-aviso { color: #5B6B80; font-size: .8rem; margin-top: 4px; }
[class*="st-key-kcard_vdr_"] { container-type: inline-size; }
@container (max-width: 520px) {
  .vd-row { flex-wrap: wrap; }
  .vd-row .dir { width: 100%; padding-left: 46px; justify-content: space-between; }
}
@media (max-width: 1280px) {
  .st-key-vd_cab > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-vd_cab > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
  .st-key-vd_acoes { padding-top: 0; }
}
@media (max-width: 1180px) {
  .vd-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .st-key-vd_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-vd_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
}
@media (max-width: 640px) {
  h1.vd-titulo { font-size: 2.1rem !important; }
  .st-key-vd_acoes { padding-top: 0; }
  .st-key-vd_acoes [data-testid="stHorizontalBlock"] { justify-content: space-between; flex-direction: row-reverse !important; }
  .vd-kpi { padding: 14px 16px; }
  .st-key-vd_cab_lista [data-testid="stColumn"]:first-child { flex: 1 1 100% !important; width: 100% !important; min-height: 24px; }
  .vd-kpi .val { font-size: 1.25rem; }
  .st-key-vd_filtros [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-vd_filtros [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
}
</style>
"""

ROTULO_PERIODO = {"Este mês": None, "Últimos 30 dias": "nos últimos 30 dias", "Últimos 90 dias": "nos últimos 90 dias",
                  "Últimos 12 meses": "nos últimos 12 meses", "Tudo": "desde o início"}
FILTROS_SITUACAO = ["Todas", "Paga", "A receber", "Cancelada"]
POR_PAGINA = 8


def _ir(pagina):
    st.session_state.current_page = pagina
    st.rerun()


def _fechar_venda():
    st.session_state["venda_selecionada"] = None
    for k in ("vd_lista", "vd_lista_ultima"):  # a mesma linha pode ser aberta de novo
        st.session_state.pop(k, None)


def _fechar_compra():
    st.session_state["vd_compra_open"] = False


def _pilula(situacao, parcelas):
    if situacao == "Cancelada":
        return '<span class="vd-pil cc">Cancelada</span>'
    if situacao == "Paga":
        return '<span class="vd-pil ok">✓ Recebido</span>'
    n, r = parcelas or (0, 0)
    if n > 1:
        return f'<span class="vd-pil ab">○ {r} de {n} recebida{"s" if r != 1 else ""}</span>'
    return '<span class="vd-pil ab">○ A receber</span>'


def _linha_venda(v, resumo, parcelas):
    cliente = esc(valor_ou_traco(v.get("cliente_nome"), "Cliente"))
    titulo = f"{cliente} · {esc(resumo)}" if resumo else cliente
    d = v.get("data_venda")
    partes = [d.strftime("%d/%m") if hasattr(d, "strftime") and not pd.isna(d) else ""]
    num = v.get("proposta_numero")
    if num and not pd.isna(num):
        partes.append(f"junto com a proposta nº {esc(num)}")
    forma = valor_ou_traco(v.get("forma_pagamento"), "")
    if forma:
        partes.append(esc(forma))
    falta = _safe_float(v.get("a_receber"))
    if falta > 0.004:
        partes.append(f"falta {esc(_fmt_brl(falta))}")
    canc = v.get("situacao") == "Cancelada"
    return (f'<div class="kanban-card vd-row{" cancelada" if canc else ""}">'
            f'<span class="ic{" canc" if canc else ""}">{_IC_CANCEL if canc else _IC_SACOLA}</span>'
            f'<div class="tx"><b>{titulo}</b><span class="d">{" · ".join(p for p in partes if p)}</span></div>'
            f'<div class="dir">{_pilula(v.get("situacao"), parcelas)}<span class="v">{esc(_fmt_brl(v.get("valor_total", 0)))}</span></div></div>')


def _dialogo_compra(produtos_df):
    """Lançar compra de estoque: soma a quantidade comprada ao estoque do produto (o valor pago vai pelo Financeiro)."""
    @st.dialog("Lançar compra de estoque", on_dismiss=_fechar_compra)
    def _d():
        if produtos_df.empty:
            st.info("Cadastre seus produtos primeiro em Cadastros › Produtos.")
            return
        df = produtos_df.sort_values("nome")
        pid = st.selectbox("Produto", df["id"].tolist(), index=None, placeholder="Escolha o produto",
                           format_func=lambda x: f'{df[df["id"] == x]["nome"].iloc[0]} · em estoque: '
                                                 f'{int(_safe_float(df[df["id"] == x]["estoque"].iloc[0]))}',
                           key="vd_compra_prod")
        qtd = st.number_input("Quantidade comprada", min_value=1, value=1, step=1, key="vd_compra_qtd")
        st.caption("Soma ao estoque do produto. O valor pago você lança no Financeiro, como despesa.")
        c1, c2 = st.columns(2)
        if c1.button("Lançar no estoque", type="primary", use_container_width=True, key="vd_compra_ok"):
            if pid is None:
                st.error("Escolha o produto.")
                return
            novo = st.session_state.db.atualizar_estoque(int(pid), int(qtd))
            if novo is None:
                st.error("Não foi possível atualizar o estoque agora.")
                return
            nome = df[df["id"] == pid]["nome"].iloc[0]
            st.session_state["vd_compra_open"] = False
            st.session_state["vd_msg"] = f"Estoque de {nome} atualizado: {int(novo)} unidade{'s' if novo != 1 else ''}."
            st.rerun()
        if c2.button("Cancelar", use_container_width=True, key="vd_compra_canc"):
            st.session_state["vd_compra_open"] = False
            st.rerun()
    _d()


def show():
    from utils.auth_guard import require_auth
    from utils import vendas_dados
    require_auth()
    st.markdown(CSS, unsafe_allow_html=True)

    if "db" not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return
    db = st.session_state.db
    ss = st.session_state
    ss.setdefault("venda_selecionada", None)
    ss.setdefault("vendas_nova_venda_open", False)
    ss.setdefault("vd_compra_open", False)

    # ---------- cabeçalho ----------
    c_tit, c_btn = st.container(key="vd_cab").columns([2.8, 1.5], vertical_alignment="top")
    c_tit.markdown('<div class="vd-eyebrow">Produtos para as suas clientes</div><h1 class="vd-titulo">Vendas</h1>'
                   '<div class="vd-sub">Colmeias, cestos e organizadores que você vende junto com o serviço, '
                   'com lucro e estoque.</div>', unsafe_allow_html=True)
    with c_btn, st.container(key="vd_acoes"):
        b1, b2 = st.columns(2)
        with b1, st.container(key="vd_produtos"):
            if st.button("Meus produtos e estoque", type="tertiary", key="vd_ir_produtos"):
                _ir("Cadastros")
        with b2, st.container(key="cta_vd_nova"):
            if st.button("Nova venda", icon=":material/add:", key="btn_nova_venda_top"):
                ss["vendas_nova_venda_open"] = not ss["vendas_nova_venda_open"]
                if not ss["vendas_nova_venda_open"]:
                    ss.produtos_venda = []

    if ss.get("vd_msg"):
        st.success(ss.pop("vd_msg"))

    try:
        vendas_df = db.get_vendas()
    except Exception as e:
        st.warning(f"Erro ao carregar vendas: {str(e)}")
        vendas_df = pd.DataFrame()
    if vendas_df is None:
        vendas_df = pd.DataFrame()
    if not vendas_df.empty:
        vendas_df["data_venda"] = pd.to_datetime(vendas_df["data_venda"], errors="coerce")
        if "situacao" not in vendas_df:
            vendas_df["situacao"] = vendas_df["status"]
    try:
        produtos_df = db.get_produtos()
    except Exception:
        produtos_df = pd.DataFrame()
    if produtos_df is None:
        produtos_df = pd.DataFrame()

    # vendas registradas antes da correção ficaram como "Pendente" no Financeiro, mesmo pagas na hora
    try:
        n_antigas = db.contar_vendas_antigas_pendentes()
    except Exception:
        n_antigas = 0
    if n_antigas:
        with st.container(border=True):
            st.markdown(f"**{n_antigas} venda{'s' if n_antigas != 1 else ''} antiga{'s' if n_antigas != 1 else ''} "
                        f"aparece{'m' if n_antigas != 1 else ''} como “a receber” no Financeiro.** Até agora toda venda feita "
                        "nesta tela entrava como pendente, mesmo paga na hora, e por isso não contava no faturamento. "
                        "Se elas já foram pagas, marque como recebidas (na data de cada venda).")
            if st.button("Marcar vendas antigas como recebidas", key="vd_marcar_antigas"):
                n = db.marcar_vendas_antigas_recebidas()
                st.success(f"{n} venda{'s' if n != 1 else ''} marcada{'s' if n != 1 else ''} como recebida{'s' if n != 1 else ''}.")
                st.rerun()

    # ---------- números (o período e a busca ficam junto da lista, abaixo; aqui vale o que está escolhido) ----------
    hoje = visual.hoje()
    nome_periodo = ss.get("vd_periodo") or "Este mês"
    if nome_periodo not in PERIODOS_VENDA:
        nome_periodo = "Este mês"
    busca = (ss.get("vd_busca") or "").strip()
    ini, fim = _periodo(nome_periodo, hoje)

    def _no_periodo(df, i, f):
        if df.empty:
            return df
        d = df["data_venda"].dt.date
        return df[(d >= i) & (d <= f)] if i else df[d <= f]

    def _filtra_busca(df):
        if not busca or df.empty:
            return df
        b = busca.lower()
        return df[df["cliente_nome"].astype(str).str.lower().str.contains(b, regex=False)
                  | df["observacoes"].astype(str).str.lower().str.contains(b, regex=False)]

    vp = _filtra_busca(_no_periodo(vendas_df, ini, fim))
    ativas = vp[vp["situacao"] != "Cancelada"] if not vp.empty else vp
    comp = pd.DataFrame()
    if ini and not vendas_df.empty:
        dur = (fim - ini).days + 1
        comp = _filtra_busca(_no_periodo(vendas_df, ini - timedelta(days=dur), ini - timedelta(days=1)))
        comp = comp[comp["situacao"] != "Cancelada"] if not comp.empty else comp
    m = _metricas(ativas, comp if ini else ativas.iloc[0:0])
    rot = ROTULO_PERIODO.get(nome_periodo) or f"em {visual.MESES[hoje.month - 1]}"

    abertas_ids = vendas_df[vendas_df["a_receber"].apply(_safe_float) > 0.004]["id"].tolist() \
        if "a_receber" in vendas_df else []
    a_receber = float(vendas_df["a_receber"].apply(_safe_float).sum()) if "a_receber" in vendas_df else 0.0
    parc_abertas = vendas_dados.parcelas_por_venda(db, abertas_ids)
    n_parc = sum(n - r for n, r in parc_abertas.values()) or len(abertas_ids)
    baixo = vendas_dados.estoque_baixo(produtos_df)

    sub_lucro = " · ".join(x for x in [rot, f"margem {m['margem']:.0%}" if m["margem"] is not None else "", m["d_luc"]] if x)
    sub_vend = " · ".join(x for x in [f"{m['n']} venda{'s' if m['n'] != 1 else ''}",
                                      f"ticket médio {_fmt_brl(m['tk'])}" if m["n"] else "", m["d_fat"]] if x)
    st.markdown(
        '<div class="vd-kpis">'
        f'<div class="vd-kpi destaque"><span class="rot">Lucro com produtos</span><div class="val">{_fmt_brl(m["luc"])}</div>'
        f'<span class="sub">{sub_lucro}</span></div>'
        f'<div class="vd-kpi"><span class="rot">Vendido</span><div class="val">{_fmt_brl(m["fat"])}</div>'
        f'<span class="sub">{sub_vend}</span></div>'
        f'<div class="vd-kpi"><span class="rot">A receber</span><div class="val verde">{_fmt_brl(a_receber)}</div>'
        f'<span class="sub">{n_parc} parcela{"s" if n_parc != 1 else ""} · de qualquer data</span></div>'
        f'<div class="vd-kpi"><span class="rot">Estoque baixo</span><div class="val{" verm" if len(baixo) else ""}">{len(baixo)}</div>'
        f'<span class="sub">produto{"s" if len(baixo) != 1 else ""} para repor</span></div>'
        '</div>', unsafe_allow_html=True)

    # ---------- nova venda ----------
    if ss["vendas_nova_venda_open"]:
        with st.expander("Nova venda", expanded=True):
            try:
                _render_nova_venda_form(db.get_clientes(), produtos_df)
            except Exception as e:
                st.error(f"Erro ao carregar formulário: {str(e)}")

    # Relatório pós-finalização
    if ss.get("mostrar_gerar_relatorio", False) and ss.get("venda_recente_id"):
        with st.container(border=True, key="vdc_pos_venda"):
            st.success("Venda finalizada! Gere o relatório abaixo.")
            rc1, rc2 = st.columns(2)
            with rc1:
                if botao_documento("Gerar relatório", use_container_width=True, key="btn_rel_pos"):
                    try:
                        vid = ss.venda_recente_id
                        vrow = vendas_df[vendas_df["id"] == vid].iloc[0]
                        itens_tmp = db.get_itens_venda(vid)
                        nome = str(vrow.get("cliente_nome") or "Cliente")
                        proposta_dados = {
                            "id": vrow.get("proposta_numero") or vrow["id"],
                            "tipo_proposta": "Venda",
                            "status": vrow.get("situacao", "Paga"),
                            "forma_pagamento": ss.venda_recente_forma_pagamento,
                            "valor_total": ss.venda_recente_valor_total,
                            "data_venda": vrow["data_venda"],
                            "observacoes": ss.venda_recente_observacoes or ""
                        }
                        pdf_bytes = _pdf_venda(proposta_dados, {"nome": nome}, itens_tmp)
                        safe = nome.replace(" ", "_").replace("/", "_").lower()
                        st.success("PDF gerado!")
                        st.download_button("Baixar PDF", data=pdf_bytes, file_name=f"Venda_{vid}_{safe}.pdf",
                                           mime="application/pdf", key="dl_rel_pos")
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
            with rc2:
                if st.button("Fechar", type="secondary", use_container_width=True, key="btn_nova_pos"):
                    ss.mostrar_gerar_relatorio = False
                    for k in list(ss.keys()):
                        if k.startswith("venda_recente_"):
                            del ss[k]
                    st.rerun()

    # ---------- corpo: vendas recentes | repor estoque e mais vendidos ----------
    corpo = st.container(key="vd_corpo")
    esq, dir_ = corpo.columns([1.9, 1], gap="medium")
    with esq:
        with st.container(key="vd_cab_lista"):
            h1_, h2_ = st.columns([1, 1])
            h1_.markdown('<div class="vd-secao">Vendas recentes</div>', unsafe_allow_html=True)
            with h2_:
                filtro = st.segmented_control("Situação", FILTROS_SITUACAO, default="Todas", key="vd_situacao",
                                              label_visibility="collapsed") or "Todas"
        with st.container(key="vd_filtros"):
            f1, f2 = st.columns([2, 1])
            f1.text_input("Buscar", key="vd_busca", placeholder="Buscar cliente ou observação",
                          label_visibility="collapsed")
            f2.selectbox("Período dos números", list(PERIODOS_VENDA), index=list(PERIODOS_VENDA).index("Este mês"),
                         key="vd_periodo", label_visibility="collapsed",
                         help="Vale para os números do topo e para Mais vendidos. A lista mostra todas as datas.")
        lista = _filtra_busca(vendas_df)
        if filtro != "Todas" and not lista.empty:
            lista = lista[lista["situacao"] == filtro]
        if lista.empty:
            st.markdown('<div class="vd-vazio">' + ("Nenhuma venda encontrada." if (busca or filtro != "Todas")
                        else "Nenhuma venda registrada ainda. Clique em Nova venda para começar.") + '</div>',
                        unsafe_allow_html=True)
        else:
            lista = lista.sort_values(["data_venda", "id"], ascending=False)
            limite = ss.get("vd_limite", POR_PAGINA)
            mostrar = lista.head(limite)
            ids = mostrar["id"].tolist()
            resumos = vendas_dados.itens_resumo(db, ids)
            parcelas = vendas_dados.parcelas_por_venda(db, ids)
            for _, v in mostrar.iterrows():
                vid = int(v["id"])
                if cartao_clicavel(_linha_venda(v, resumos.get(vid, ""), parcelas.get(vid)), key=f"vdr_{vid}",
                                   rotulo=f"Abrir venda de {valor_ou_traco(v.get('cliente_nome'), 'Cliente')}"):
                    ss["venda_selecionada"] = vid
                    ss["vd_compra_open"] = False
                    st.rerun()
            if len(lista) > limite:
                with st.container(key="vd_mais"):
                    if st.button(f"Mostrar mais ({len(lista) - limite})", type="tertiary", key="vd_mais_btn"):
                        ss["vd_limite"] = limite + POR_PAGINA * 2
                        st.rerun()
            st.markdown(f'<div class="vd-aviso">Todas as datas, das mais novas para as mais antigas. Os números do topo '
                        f'seguem o período escolhido ({esc(nome_periodo.lower())}).</div>', unsafe_allow_html=True)
        with st.expander("Todas as vendas em tabela", expanded=False):
            _lista_vendas(vendas_df, busca)

    with dir_:
        with st.container(border=True, key="vdc_repor"):
            st.markdown('<div class="vd-h4">Repor estoque</div>', unsafe_allow_html=True)
            if baixo.empty:
                st.markdown('<div class="vd-li"><span>' + ("Nenhum produto com estoque baixo." if not produtos_df.empty
                            else "Nenhum produto cadastrado.") + '</span></div>', unsafe_allow_html=True)
            else:
                st.markdown("".join(f'<div class="vd-li"><span>{esc(r["nome"])}</span><b class="verm">{int(r["estoque"])} un.</b></div>'
                                    for _, r in baixo.head(6).iterrows()), unsafe_allow_html=True)
                if len(baixo) > 6:
                    st.markdown(f'<div class="vd-nota">e mais {len(baixo) - 6}.</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vd-nota">Entram aqui os produtos com até {vendas_dados.ESTOQUE_BAIXO} unidades.</div>',
                        unsafe_allow_html=True)
            with st.container(key="vd_compra_btn"):
                if st.button("Lançar compra de estoque", use_container_width=True, key="vd_compra"):
                    from utils import somente_leitura
                    if somente_leitura.ativo():   # modo consulta: abre o convite para assinar, não a janela
                        somente_leitura.tentou()
                    else:
                        ss["vd_compra_open"] = True
                        ss["venda_selecionada"] = None
                        st.rerun()
        with st.container(border=True, key="vdc_top"):
            st.markdown('<div class="vd-h4">Mais vendidos</div>', unsafe_allow_html=True)
            top = vendas_dados.mais_vendidos(db, ativas["id"].tolist() if not ativas.empty else [])
            if top:
                st.markdown("".join(f'<div class="vd-li"><span>{esc(n)}</span><b>{esc(_fmt_brl(r))}</b></div>'
                                    for n, r, _ in top), unsafe_allow_html=True)
            else:
                st.markdown('<div class="vd-li"><span>Nenhuma venda no período.</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vd-nota">Pelo valor vendido {esc(rot)}.</div>', unsafe_allow_html=True)

    # ---------- janelas (uma por vez) ----------
    selected_id = ss.get("venda_selecionada")
    if selected_id is not None and not vendas_df.empty:
        rows = vendas_df[vendas_df["id"] == selected_id]
        if not rows.empty:
            venda_sel = rows.iloc[0]

            @st.dialog("Detalhes da venda", width="large", on_dismiss=_fechar_venda)
            def _modal_venda():
                _render_detail_panel(selected_id, venda_sel)
                st.markdown("---")
                if st.button("Fechar", key=f"venda_fechar_modal_{selected_id}", type="tertiary"):
                    _fechar_venda()
                    st.rerun()

            _modal_venda()
        else:
            ss["venda_selecionada"] = None
    elif ss.get("vd_compra_open"):
        _dialogo_compra(produtos_df)

    # Análise por período (seção colapsável)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    with st.expander("Análise por período", expanded=False):
        _analise(vendas_df[vendas_df["situacao"] != "Cancelada"] if not vendas_df.empty else vendas_df)


def _lista_vendas(vendas_df, busca):
    """Todas as vendas, de qualquer data, com o nome da cliente: clicar na linha abre a venda."""
    if vendas_df.empty:
        st.caption("Nenhuma venda registrada.")
        return
    df = vendas_df
    if busca:
        b = busca.strip().lower()
        df = df[df["cliente_nome"].astype(str).str.lower().str.contains(b, regex=False)
                | df["observacoes"].astype(str).str.lower().str.contains(b, regex=False)]
    df = df.sort_values("data_venda", ascending=False).reset_index(drop=True)
    tabela = pd.DataFrame({
        "Data": df["data_venda"].dt.strftime("%d/%m/%Y"),
        "Cliente": df["cliente_nome"].apply(lambda v: valor_ou_traco(v, "—")),
        "Valor": df["valor_total"].apply(_fmt_brl),
        "Situação": df["situacao"],
        "Pagamento": df["forma_pagamento"].apply(lambda v: valor_ou_traco(v, "—")),
        "Venda": df["id"].apply(lambda v: f"#{v}"),
    })
    sel = st.dataframe(tabela, hide_index=True, use_container_width=True, height=min(38 + 35 * len(tabela), 420),
                       on_select="rerun", selection_mode="single-cell", key="vd_lista")
    st.caption(f"{len(tabela)} venda(s){' na busca' if busca else ''} · clique numa linha para abrir")
    # qualquer célula da linha abre a venda (no modo de linha só o quadradinho à esquerda selecionava)
    celulas = sel.selection.cells if sel and sel.selection else []
    escolhida = int(df.iloc[celulas[0][0]]["id"]) if celulas else None
    # abre só quando a escolha muda (depois de fechar, a linha continua marcada e não deve reabrir)
    if escolhida != st.session_state.get("vd_lista_ultima"):
        st.session_state["vd_lista_ultima"] = escolhida
        if escolhida is not None:
            st.session_state["venda_selecionada"] = escolhida
            st.rerun()


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
