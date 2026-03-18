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


def _safe_float(val, default=0.0):
    try:
        if pd.isna(val) or val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _fmt_brl(val):
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


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
                    time.sleep(1)
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

    st.markdown(f"### Proposta #{numero} — {nome_cliente}")
    st.caption(proposta.get('descricao', '')[:120])

    detail_tabs = st.tabs([
        "📊 Detalhes", "📦 Produtos", "🏭 Fornecedores",
        "👥 Assistentes", "➕ Outros", "🏁 Finalizar / Ações"
    ])

    with detail_tabs[0]:
        _tab_detalhes(proposta_id, proposta)

    with detail_tabs[1]:
        _tab_produtos(proposta_id)

    with detail_tabs[2]:
        _tab_fornecedores(proposta_id)

    with detail_tabs[3]:
        _tab_assistentes(proposta_id)

    with detail_tabs[4]:
        _tab_outros(proposta_id)

    with detail_tabs[5]:
        _tab_acoes(proposta_id, proposta)


def _tab_detalhes(proposta_id, proposta):
    st.subheader("Detalhes")

    with st.form(key=f"form_andamento_{proposta_id}"):
        st.write("Registre uma nova atualização de detalhes:")
        descricao_andamento = st.text_area("Descrição:", height=100)
        submitted = st.form_submit_button("Registrar Andamento", type="primary")

        if submitted:
            if descricao_andamento:
                try:
                    resultado = st.session_state.db.add_andamento_proposta(
                        proposta_id=proposta_id,
                        status="Em andamento",
                        observacao=descricao_andamento
                    )
                    if resultado:
                        st.success("Andamento registrado com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Erro ao registrar andamento.")
                except Exception as e:
                    st.error(f"Erro ao registrar andamento: {str(e)}")
            else:
                st.warning("Por favor, insira uma descrição para o andamento.")

    try:
        andamentos = st.session_state.db.get_andamentos_proposta(proposta_id)
        if not andamentos.empty:
            st.write("### Histórico de Andamentos")
            for _, andamento in andamentos.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        texto = andamento.get('observacao', andamento.get('descricao', 'Andamento sem descrição'))
                        st.markdown(f"**{texto}**")
                        status = andamento.get('status', '')
                        if pd.notna(status) and status:
                            st.caption(f"📊 Status: {status}")
                    with col2:
                        data_and = andamento.get('data')
                        if pd.notna(data_and) and data_and:
                            data_formatada = data_and.strftime('%d/%m/%Y')
                        else:
                            data_formatada = 'N/A'
                        st.markdown(f"📅 {data_formatada}")
                    st.markdown("---")
    except Exception as e:
        st.error(f"Erro ao carregar andamentos: {str(e)}")

    hoje = datetime.now().date()
    data_inicio_exec = proposta.get('data_inicio_execucao') or proposta.get('data_inicio')
    if data_inicio_exec is None:
        data_inicio_exec = hoje - timedelta(days=1)
    data_fim_prevista = proposta.get('data_fim')
    if data_fim_prevista is None:
        data_fim_prevista = data_inicio_exec + timedelta(days=30)

    try:
        total_dias = (data_fim_prevista - data_inicio_exec).days
        dias_decorridos = (hoje - data_inicio_exec).days
        progresso = min(100, max(0, int(dias_decorridos / total_dias * 100))) if total_dias > 0 else 0
        st.write("**Progresso baseado no prazo:**")
        st.progress(progresso)
        st.caption(f"Progresso: {progresso}% ({dias_decorridos} de {total_dias} dias)")
        if hoje > data_fim_prevista:
            st.warning(f"⚠️ Proposta atrasada por {(hoje - data_fim_prevista).days} dias!")
        else:
            dias_restantes = (data_fim_prevista - hoje).days
            st.info(f"📅 Restam {dias_restantes} dias para a conclusão prevista")
    except (TypeError, AttributeError):
        pass


def _tab_produtos(proposta_id):
    st.subheader("Produtos")
    st.write("Adição à Proposta")

    with st.form(key=f"form_produto_{proposta_id}"):
        produtos_cadastrados = st.session_state.db.get_produtos()

        if not produtos_cadastrados.empty:
            opcoes_produtos = produtos_cadastrados['id'].tolist()

            def format_produto_option(produto_id):
                produto = produtos_cadastrados.loc[produtos_cadastrados['id'] == produto_id]
                if not produto.empty:
                    nome = produto['nome'].iloc[0]
                    preco = float(produto['preco_venda'].iloc[0])
                    return f"{nome} - R$ {preco:.2f}"
                return "Produto não encontrado"

            st.write("Selecione o produto:")
            produto_selecionado_id = st.selectbox(
                "Selecione o produto:",
                options=opcoes_produtos,
                format_func=format_produto_option,
                key=f"select_produto_{proposta_id}",
                label_visibility="collapsed"
            )

            produto = produtos_cadastrados.loc[produtos_cadastrados['id'] == produto_selecionado_id].iloc[0]
            st.write(f"Descrição: {produto['descricao']}")
            st.write(f"Categoria: {produto['categoria']}")

            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
            comodo = st.text_input("Cômodo/Área:")
            usar_preco_padrao = st.checkbox("Usar preço padrão", value=True)
            preco_padrao = float(produto['preco_venda'])

            if not usar_preco_padrao:
                valor_unitario = st.number_input("Preço personalizado (R$):", min_value=0.0, value=preco_padrao, format="%.2f")
            else:
                valor_unitario = preco_padrao

            produto_salvar = st.form_submit_button("ADICIONAR À PROPOSTA", type="primary", use_container_width=True)

            if produto_salvar:
                try:
                    valor_total = valor_unitario * quantidade
                    nome_produto = produto['nome']
                    descricao_produto = produto['descricao']
                    comodo_final = comodo if comodo else "Geral"

                    produto_id = st.session_state.db.add_produto_organizador(
                        proposta_id=proposta_id,
                        nome=nome_produto,
                        descricao=descricao_produto,
                        valor=valor_unitario,
                        quantidade=quantidade,
                        comodo=comodo_final
                    )

                    st.success(f"Produto '{nome_produto}' adicionado com sucesso! Valor Total: R$ {valor_total:.2f}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar produto: {str(e)}")
        else:
            st.warning("Não há produtos cadastrados no sistema. Adicione produtos no módulo de vendas.")
            st.form_submit_button("ADICIONAR À PROPOSTA", disabled=True)

    st.write("Produtos da Proposta:")
    try:
        produtos_proposta_raw = st.session_state.db.get_produtos_organizadores(proposta_id=proposta_id)

        if not produtos_proposta_raw.empty:
            produtos_proposta = produtos_proposta_raw.rename(columns={'valor': 'valor_unit'})
            produtos_proposta['valor_total'] = produtos_proposta['valor_unit'] * produtos_proposta['quantidade']

            st.dataframe(
                produtos_proposta[['nome', 'descricao', 'valor_unit', 'quantidade', 'valor_total', 'comodo']],
                column_config={
                    'nome': 'Nome',
                    'descricao': 'Descrição',
                    'valor_unit': st.column_config.NumberColumn('Valor Unit.', format="R$ %.2f"),
                    'quantidade': 'Quantidade',
                    'valor_total': st.column_config.NumberColumn('Valor Total', format="R$ %.2f"),
                    'comodo': 'Cômodo'
                },
                use_container_width=True,
                hide_index=True
            )

            with st.form(key=f"form_remover_produto_{proposta_id}"):
                st.write("Selecione um produto para remover:")
                produto_remover_id = st.selectbox(
                    "Selecione um produto para remover:",
                    options=produtos_proposta['id'].tolist(),
                    format_func=lambda x: f"{x} - {produtos_proposta.loc[produtos_proposta['id'] == x, 'nome'].iloc[0]}",
                    key=f"select_remover_produto_{proposta_id}"
                )

                remover_produto = st.form_submit_button("REMOVER PRODUTO", type="primary", use_container_width=True)

                if remover_produto:
                    try:
                        resultado = st.session_state.db.remove_produto_organizador(produto_remover_id)
                        if resultado:
                            st.success("Produto removido com sucesso!")
                        else:
                            st.error("Falha ao remover o produto.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao remover produto: {str(e)}")

            valor_total_produtos = produtos_proposta['valor_total'].sum()
            st.info(f"Valor Total dos Produtos: R$ {valor_total_produtos:.2f}")

            st.markdown("---")
            if st.button("📄 GERAR RELATÓRIO DE VENDA DOS PRODUTOS", type="primary", use_container_width=True, key=f"btn_pdf_produtos_proposta_{proposta_id}"):
                try:
                    from utils.pdf_generator_venda_fixed import gerar_pdf_venda

                    venda_dados = {
                        'id': proposta_id,
                        'status': 'Proposta',
                        'forma_pagamento': 'N/A',
                        'valor_total': round(float(valor_total_produtos), 2),
                        'data_venda': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'observacoes': f"Produtos da Proposta #{proposta_id}"
                    }
                    cliente_dados = {'nome': 'Cliente'}

                    itens_pdf = produtos_proposta.rename(columns={
                        'nome': 'produto_nome',
                        'valor_unit': 'preco_unitario'
                    })[['produto_nome', 'quantidade', 'preco_unitario']].copy()

                    import time as _t
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ts_unique = str(int(_t.time()))
                    filename = f"pdfs/Venda_Proposta_{proposta_id}_{timestamp}_{ts_unique}.pdf"
                    os.makedirs("pdfs", exist_ok=True)

                    pdf_path = gerar_pdf_venda(venda_dados, cliente_dados, itens_pdf, filename)

                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_data = pdf_file.read()
                        st.success("Relatório de venda dos produtos gerado com sucesso!")
                        st.download_button(
                            label="📥 Baixar Relatório de Venda",
                            data=pdf_data,
                            file_name=f"Relatorio_Venda_Proposta_{proposta_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"download_pdf_venda_proposta_{proposta_id}"
                        )
                    else:
                        st.error("Erro ao gerar arquivo PDF")
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {str(e)}")
        else:
            st.info("Nenhum produto adicionado a esta proposta ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar produtos da proposta: {str(e)}")


def _tab_fornecedores(proposta_id):
    st.subheader("Fornecedores")

    try:
        fornecedores = st.session_state.db.get_fornecedores()

        if not fornecedores.empty:
            with st.form(key=f"form_fornecedor_{proposta_id}"):
                opcoes_fornecedores = fornecedores['id'].tolist()

                def format_fornecedor_option(fornecedor_id):
                    forn = fornecedores.loc[fornecedores['id'] == fornecedor_id]
                    if not forn.empty:
                        return forn['descricao'].iloc[0]
                    return "Fornecedor não encontrado"

                st.write("Selecione o fornecedor:")
                fornecedor_selecionado = st.selectbox(
                    "Selecione o fornecedor:",
                    options=opcoes_fornecedores,
                    format_func=format_fornecedor_option,
                    key=f"select_fornecedor_{proposta_id}",
                    label_visibility="collapsed"
                )

                valor_servico = st.number_input("Valor do serviço (R$):", min_value=0.0, value=0.0, format="%.2f", key=f"valor_forn_{proposta_id}")
                observacoes = st.text_area("Observações:", height=80, key=f"obs_forn_{proposta_id}")

                fornecedor_salvar = st.form_submit_button("Adicionar Fornecedor")

                if fornecedor_salvar:
                    if valor_servico <= 0:
                        st.error("O valor do serviço deve ser maior que zero.")
                    else:
                        try:
                            nome_fornecedor = format_fornecedor_option(fornecedor_selecionado)
                            resultado = st.session_state.db.add_fornecedor_proposta(
                                proposta_id=proposta_id,
                                fornecedor_id=fornecedor_selecionado,
                                valor=valor_servico,
                                observacoes=observacoes
                            )

                            if resultado and "acrescimo_id" in resultado:
                                st.success("Fornecedor adicionado à proposta com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar fornecedor. Verifique os dados e tente novamente.")
                        except Exception as e:
                            st.error(f"Erro ao adicionar fornecedor: {str(e)}")
        else:
            st.info("Não há fornecedores cadastrados. Adicione fornecedores no menu Cadastros > Fornecedores.")

        try:
            acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")

            if not acrescimos.empty:
                st.write("### Fornecedores Adicionados")
                df_display = acrescimos[['id', 'fornecedor', 'descricao', 'valor']].copy()
                df_display.columns = ['ID', 'Fornecedor', 'Descrição', 'Valor']
                df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                st.dataframe(df_display[['Fornecedor', 'Descrição', 'Valor']], hide_index=True)

                valor_total_forn = acrescimos['valor'].sum()
                st.info(f"Valor Total dos Fornecedores: R$ {valor_total_forn:.2f}")

                with st.form(key=f"form_editar_fornecedor_{proposta_id}"):
                    st.write("Selecione um fornecedor para editar:")
                    acrescimo_editar_id = st.selectbox(
                        "Selecione um fornecedor:",
                        options=acrescimos['id'].tolist(),
                        format_func=lambda x: f"{acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]}",
                        key=f"select_editar_fornecedor_{proposta_id}"
                    )

                    fornecedor_atual = acrescimos.loc[acrescimos['id'] == acrescimo_editar_id].iloc[0]
                    novo_valor = st.number_input("Novo valor (R$):", min_value=0.0, value=float(fornecedor_atual['valor']), format="%.2f", key=f"novo_valor_fornecedor_{proposta_id}")
                    nova_descricao = st.text_area("Novas observações:", value=fornecedor_atual['descricao'] if fornecedor_atual['descricao'] else "", key=f"nova_descricao_fornecedor_{proposta_id}")

                    editar_fornecedor = st.form_submit_button("Editar")

                    if editar_fornecedor:
                        try:
                            resultado = st.session_state.db.update_acrescimo_proposta(acrescimo_editar_id, valor=novo_valor, descricao=nova_descricao)
                            if resultado:
                                st.success("Fornecedor atualizado com sucesso!")
                            else:
                                st.error("Falha ao atualizar o fornecedor.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao editar fornecedor: {str(e)}")

                with st.form(key=f"form_remover_fornecedor_{proposta_id}"):
                    st.write("Selecione um fornecedor para remover:")
                    acrescimo_remover_id = st.selectbox(
                        "Selecione um fornecedor:",
                        options=acrescimos['id'].tolist(),
                        format_func=lambda x: f"{acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]}",
                        key=f"select_remover_fornecedor_{proposta_id}"
                    )
                    remover_fornecedor = st.form_submit_button("Remover")

                    if remover_fornecedor:
                        try:
                            resultado = st.session_state.db.remove_acrescimo_proposta(acrescimo_remover_id)
                            if resultado:
                                st.success("Fornecedor removido com sucesso!")
                            else:
                                st.error("Falha ao remover o fornecedor.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover fornecedor: {str(e)}")
            else:
                st.info("Nenhum fornecedor adicionado a esta proposta ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar fornecedores da proposta: {str(e)}")

    except Exception as e:
        st.error(f"Erro ao carregar fornecedores: {str(e)}")


def _tab_assistentes(proposta_id):
    st.subheader("Assistentes")

    try:
        assistentes = st.session_state.db.get_assistentes()

        if not assistentes.empty:
            with st.form(key=f"form_assistente_{proposta_id}"):
                assistente_selecionado = st.selectbox(
                    "Selecione o assistente:",
                    options=assistentes['id'].tolist(),
                    format_func=lambda x: assistentes.loc[assistentes['id'] == x, 'nome'].iloc[0]
                )
                valor_servico = st.number_input("Valor do serviço (R$):", min_value=0.0, value=0.0, format="%.2f")
                observacoes = st.text_area("Observações:", height=100)
                assistente_salvar = st.form_submit_button("Adicionar Assistente")

                if assistente_salvar:
                    if valor_servico <= 0:
                        st.error("O valor do serviço deve ser maior que zero.")
                    else:
                        try:
                            resultado = st.session_state.db.add_assistente_proposta(
                                proposta_id=proposta_id,
                                assistente_id=assistente_selecionado,
                                valor=valor_servico,
                                observacoes=observacoes
                            )

                            if resultado and "acrescimo_id" in resultado:
                                st.success("Assistente adicionado à proposta com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar assistente. Verifique os dados e tente novamente.")
                        except Exception as e:
                            st.error(f"Erro ao adicionar assistente: {str(e)}")

            try:
                acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")

                if not acrescimos.empty:
                    st.write("### Assistentes Adicionados")
                    df_display = acrescimos[['id', 'fornecedor', 'descricao', 'valor']].copy()
                    df_display.columns = ['ID', 'Assistente', 'Descrição', 'Valor']
                    df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    st.dataframe(df_display[['Assistente', 'Descrição', 'Valor']], hide_index=True)

                    valor_total_assistentes = acrescimos['valor'].sum()
                    st.info(f"Valor Total dos Assistentes: R$ {valor_total_assistentes:.2f}")

                    with st.form(key=f"form_editar_assistente_{proposta_id}"):
                        st.write("Selecione um assistente para editar:")
                        acrescimo_editar_id = st.selectbox(
                            "Selecione um assistente:",
                            options=acrescimos['id'].tolist(),
                            format_func=lambda x: f"{acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]}",
                            key=f"select_editar_assistente_{proposta_id}"
                        )
                        assistente_atual = acrescimos.loc[acrescimos['id'] == acrescimo_editar_id].iloc[0]
                        novo_valor = st.number_input("Novo valor (R$):", min_value=0.0, value=float(assistente_atual['valor']), format="%.2f", key=f"novo_valor_assistente_{proposta_id}")
                        nova_descricao = st.text_area("Nova descrição:", value=assistente_atual['descricao'] if assistente_atual['descricao'] else "", key=f"nova_descricao_assistente_{proposta_id}")
                        editar_assistente = st.form_submit_button("Editar")

                        if editar_assistente:
                            try:
                                resultado = st.session_state.db.update_acrescimo_proposta(acrescimo_editar_id, valor=novo_valor, descricao=nova_descricao)
                                if resultado:
                                    st.success("Assistente atualizado com sucesso!")
                                else:
                                    st.error("Falha ao atualizar o assistente.")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao editar assistente: {str(e)}")

                    with st.form(key=f"form_remover_assistente_{proposta_id}"):
                        st.write("Selecione um assistente para remover:")
                        acrescimo_remover_id = st.selectbox(
                            "Selecione um assistente:",
                            options=acrescimos['id'].tolist(),
                            format_func=lambda x: f"{acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]}",
                            key=f"select_remover_assistente_{proposta_id}"
                        )
                        remover_assistente = st.form_submit_button("Remover")

                        if remover_assistente:
                            try:
                                resultado = st.session_state.db.remove_acrescimo_proposta(acrescimo_remover_id)
                                if resultado:
                                    st.success("Assistente removido com sucesso!")
                                else:
                                    st.error("Falha ao remover o assistente.")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao remover assistente: {str(e)}")
                else:
                    st.info("Nenhum assistente adicionado a esta proposta ainda.")
            except Exception as e:
                st.error(f"Erro ao carregar assistentes da proposta: {str(e)}")
        else:
            st.info("Não há assistentes cadastrados. Adicione assistentes no menu Cadastros > Assistentes.")

    except Exception as e:
        st.error(f"Erro ao carregar assistentes: {str(e)}")


def _tab_outros(proposta_id):
    st.subheader("Outros")
    st.write("Adicionar itens adicionais que não estão no catálogo de produtos")

    with st.form(key=f"form_outros_{proposta_id}"):
        col1, col2 = st.columns(2)
        with col1:
            nome_item = st.text_input("Nome do Item:")
            descricao_item = st.text_input("Descrição:")
            comodo_area = st.text_input("Cômodo/Área:")
        with col2:
            valor_unitario = st.number_input("Valor unitário (R$):", min_value=0.0, value=0.0, format="%.2f")
            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
            valor_total = valor_unitario * quantidade
            st.write(f"Valor total: R$ {valor_total:.2f}")

        item_salvar = st.form_submit_button("Adicionar Item")

        if item_salvar:
            if not nome_item or valor_unitario <= 0:
                st.error("Preencha o nome do item e um valor válido.")
            else:
                try:
                    resultado = st.session_state.db.add_acrescimo_proposta(
                        proposta_id=proposta_id,
                        tipo="OUTROS",
                        valor=valor_total,
                        descricao=f"{nome_item} - {descricao_item}" if descricao_item else nome_item,
                        fornecedor=comodo_area if comodo_area else "Geral"
                    )

                    if resultado and "acrescimo_id" in resultado:
                        st.success(f"Item '{nome_item}' adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao adicionar item. Verifique os dados e tente novamente.")
                except Exception as e:
                    st.error(f"Erro ao adicionar item: {str(e)}")

    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")

        if not acrescimos.empty:
            st.write("### Itens adicionados")
            df_display = acrescimos.copy()
            df_display['nome_item'] = df_display['descricao'].apply(lambda x: x.split(' - ')[0] if ' - ' in x else x)
            df_display['descricao_item'] = df_display['descricao'].apply(lambda x: x.split(' - ')[1] if ' - ' in x else '')
            df_display = df_display[['id', 'nome_item', 'descricao_item', 'valor', 'fornecedor']]
            df_display.columns = ['ID', 'Nome', 'Descrição', 'Valor Total', 'Cômodo/Área']
            df_display['Valor Total'] = df_display['Valor Total'].apply(lambda x: f"R$ {float(x):.2f}")
            st.dataframe(df_display)

            with st.form(key=f"form_remover_outros_{proposta_id}"):
                acrescimo_remover_id = st.selectbox(
                    "Selecione um item para remover:",
                    options=acrescimos['id'].tolist(),
                    format_func=lambda x: acrescimos.loc[acrescimos['id'] == x, 'descricao'].iloc[0]
                )
                remover_item = st.form_submit_button("Remover Item")

                if remover_item:
                    try:
                        resultado = st.session_state.db.remove_acrescimo_proposta(acrescimo_remover_id)
                        if resultado:
                            st.success("Item removido com sucesso!")
                        else:
                            st.error("Falha ao remover o item.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao remover item: {str(e)}")
        else:
            st.info("Nenhum item adicional adicionado a esta proposta ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar itens adicionais da proposta: {str(e)}")


def _tab_acoes(proposta_id, proposta):
    st.subheader("Finalizar / Ações")

    status_atual = proposta.get('status', '')
    status_execucao = proposta.get('status_execucao', '')

    em_aberto = status_atual in ['Em elaboração', 'Aguardando aprovação', 'Aguardando']
    esta_aprovada = status_atual == 'Aprovada'
    em_execucao = status_execucao == 'Em execução'
    finalizada = status_atual in ['Finalizada', 'Recusada']

    st.markdown("#### Transições de Estágio")

    if em_aberto:
        st.info("Esta proposta está **Em Aberto**. Você pode aprová-la ou recusá-la.")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Aprovar Proposta", type="primary", use_container_width=True, key=f"btn_aprovar_{proposta_id}"):
                try:
                    data_aprovacao_local = datetime.now().date()
                    resultado = st.session_state.db.update_proposta_status(
                        proposta_id=proposta_id,
                        novo_status="Aprovada",
                        data_aprovacao=data_aprovacao_local
                    )
                    sucesso = resultado.get('status', False)
                    if sucesso:
                        st.success("Proposta aprovada! Agora está na coluna **Aprovada**.")
                        st.session_state['kanban_selected_proposta'] = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Erro ao aprovar proposta: {resultado.get('message', '')}")
                except Exception as e:
                    st.error(f"Erro ao aprovar proposta: {str(e)}")

        with col2:
            if st.button("❌ Recusar Proposta", type="secondary", use_container_width=True, key=f"btn_recusar_{proposta_id}"):
                try:
                    resultado = st.session_state.db.update_proposta_status(
                        proposta_id=proposta_id,
                        novo_status="Finalizada"
                    )
                    if resultado.get('status', False):
                        st.session_state.db.update_proposta(
                            proposta_id,
                            status_execucao="Cancelada",
                            data_fim=datetime.now().date()
                        )
                        st.success("Proposta marcada como recusada!")
                        st.session_state['kanban_selected_proposta'] = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao recusar proposta.")
                except Exception as e:
                    st.error(f"Erro ao recusar proposta: {str(e)}")

    elif esta_aprovada and not em_execucao and not finalizada:
        st.info("Esta proposta está **Aprovada**. Você pode iniciar a execução.")
        if st.button("▶ Iniciar Execução", type="primary", use_container_width=True, key=f"btn_iniciar_exec_{proposta_id}"):
            try:
                resultado = st.session_state.db.update_proposta_status(
                    proposta_id=proposta_id,
                    novo_status="Em execução",
                    data_aprovacao=proposta.get('data_aprovacao')
                )
                sucesso = resultado.get('status', False)
                if sucesso:
                    st.success("Execução iniciada! Proposta movida para **Em Execução**.")
                    st.session_state['kanban_selected_proposta'] = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Erro ao iniciar execução: {resultado.get('message', '')}")
            except Exception as e:
                st.error(f"Erro ao iniciar execução: {str(e)}")

    elif em_execucao and not finalizada:
        st.info("Esta proposta está **Em Execução**. Você pode finalizá-la.")

        try:
            valor_base = _safe_float(proposta.get('valor'))
            data_inicio = proposta.get('data_inicio')
            data_aprovacao = proposta.get('data_aprovacao')

            produtos_df = st.session_state.db.get_produtos_organizadores(proposta_id)
            fornecedores_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
            assistentes_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
            outros_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")

            total_produtos = (produtos_df['valor'] * produtos_df['quantidade']).sum() if not produtos_df.empty else 0
            total_fornecedores = fornecedores_df['valor'].sum() if not fornecedores_df.empty else 0
            total_assistentes = assistentes_df['valor'].sum() if not assistentes_df.empty else 0
            total_outros = outros_df['valor'].sum() if not outros_df.empty else 0
            total_geral = valor_base + total_produtos + total_fornecedores + total_assistentes + total_outros

            st.write("### Resumo Financeiro")
            resumo_financeiro = {
                "Item": ["Valor Personal Organizer", "Produtos", "Fornecedores", "Assistentes", "Outros", "Total Geral"],
                "Valor": [
                    f"R$ {valor_base:.2f}",
                    f"R$ {total_produtos:.2f}",
                    f"R$ {total_fornecedores:.2f}",
                    f"R$ {total_assistentes:.2f}",
                    f"R$ {total_outros:.2f}",
                    f"R$ {total_geral:.2f}"
                ]
            }
            st.dataframe(pd.DataFrame(resumo_financeiro), hide_index=True, use_container_width=True)

            labels = ['Valor Personal Organizer', 'Fornecedores', 'Assistentes (Custos)', 'Produtos']
            values = [valor_base, total_fornecedores, total_assistentes, total_produtos]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3, textinfo='label+value')])
            fig.update_layout(title_text="Distribuição de Valores da Proposta", legend=dict(orientation="h", yanchor="bottom", y=-0.3))
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao carregar resumo financeiro: {str(e)}")

        st.warning("⚠️ **Atenção**: Finalizar uma proposta não poderá ser desfeito facilmente.")

        with st.form(key=f"form_finalizar_concluida_{proposta_id}"):
            finalizar_concluida = st.form_submit_button("🏁 MARCAR COMO CONCLUÍDA", type="primary", use_container_width=True)
            if finalizar_concluida:
                try:
                    proposta_id_int = int(proposta_id)
                    resultado = finalizar_proposta_v2(proposta_id_int)
                    if resultado.get('status', False):
                        st.success("✅ Proposta finalizada com sucesso!")
                        st.session_state['kanban_selected_proposta'] = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao finalizar proposta: {resultado.get('message', 'Erro desconhecido')}")
                except Exception as e:
                    st.error(f"❌ Erro ao finalizar proposta: {str(e)}")

    elif finalizada:
        st.info("Esta proposta está **Finalizada**.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 RELATÓRIO CLIENTE", type="primary", use_container_width=True, key=f"btn_rel_cliente_{proposta_id}"):
                try:
                    st_gerar_pdf_cliente(proposta_id)
                except Exception as e:
                    st.error(f"Erro ao gerar relatório para cliente: {str(e)}")

        with col2:
            if st.button("📄 RELATÓRIO INTERNO", type="primary", use_container_width=True, key=f"btn_rel_interno_{proposta_id}"):
                try:
                    st_gerar_pdf_interno(proposta_id)
                except Exception as e:
                    st.error(f"Erro ao gerar relatório interno: {str(e)}")

        with col3:
            if st.button("📄 RELATÓRIO FORNECEDORES", type="primary", use_container_width=True, key=f"btn_rel_forn_{proposta_id}"):
                try:
                    st_gerar_pdf_fornecedores(proposta_id)
                except Exception as e:
                    st.error(f"Erro ao gerar relatório de fornecedores: {str(e)}")

        st.markdown("---")
        with st.expander("🔄 Reabrir Proposta Finalizada"):
            st.warning("Esta ação mudará o status da proposta para 'Em execução'.")
            if st.button("REABRIR PROPOSTA", key=f"btn_reabrir_{proposta_id}", type="primary", use_container_width=True):
                try:
                    from reabrir_proposta import reabrir_proposta_finalizada
                    resultado = reabrir_proposta_finalizada(proposta_id)
                    if resultado.get('status') in ['sucesso', 'sucesso_com_alerta']:
                        st.success(resultado.get('mensagem'))
                        if resultado.get('status') == 'sucesso_com_alerta':
                            st.warning(resultado.get('alerta'))
                        st.session_state['kanban_selected_proposta'] = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Erro ao reabrir proposta: {resultado.get('mensagem')}")
                except Exception as e:
                    st.error(f"Erro ao reabrir proposta: {str(e)}")

    else:
        st.info(f"Status atual: {status_atual} / {status_execucao}")

    st.markdown("---")
    with st.expander("🗑️ Excluir Proposta", expanded=False):
        st.warning("⚠️ **ATENÇÃO**: Esta ação irá excluir permanentemente a proposta e todos os seus dados relacionados!")
        confirmar_exclusao = st.checkbox("Eu entendo que esta ação não pode ser desfeita", key=f"confirmar_exclusao_{proposta_id}")

        if confirmar_exclusao:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ EXCLUIR PROPOSTA", key=f"btn_excluir_kanban_{proposta_id}", type="secondary", use_container_width=True):
                    try:
                        from sqlalchemy import text
                        from utils.database import engine

                        with engine.connect() as conn:
                            conn.execute(text(f"DELETE FROM financeiro WHERE proposta_id = {proposta_id}"))
                            conn.execute(text(f"DELETE FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                            conn.execute(text(f"DELETE FROM produtos_organizadores WHERE proposta_id = {proposta_id}"))
                            conn.execute(text(f"DELETE FROM andamento_propostas WHERE proposta_id = {proposta_id}"))
                            conn.execute(text(f"DELETE FROM propostas WHERE id = {proposta_id}"))
                            conn.commit()

                        st.success(f"✅ Proposta #{proposta_id} excluída com sucesso!")
                        st.session_state['kanban_selected_proposta'] = None
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir proposta: {str(e)}")
            with col2:
                if st.button("🔙 Cancelar", key=f"btn_cancelar_exclusao_kanban_{proposta_id}", type="primary", use_container_width=True):
                    st.rerun()

    st.markdown("---")
    if st.button("↩ Gerar PDF da Proposta", key=f"btn_pdf_proposta_{proposta_id}", type="secondary"):
        try:
            sucesso, mensagem, arquivo = gerar_pdf_proposta(db=st.session_state.db, proposta_id=proposta_id)
            if sucesso and arquivo:
                with open(arquivo, "rb") as file:
                    pdf_bytes = file.read()
                st.success("Proposta do cliente gerada com sucesso!")
                st.download_button(
                    label="📥 Baixar Proposta",
                    data=pdf_bytes,
                    file_name=f"Proposta_{proposta_id}.pdf",
                    mime="application/pdf",
                    key=f"download_proposta_{proposta_id}"
                )
            else:
                st.error(f"Erro ao gerar PDF: {mensagem}")
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {str(e)}")


def show():
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">📝 Propostas</h1>', unsafe_allow_html=True)

    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return

    if 'kanban_selected_proposta' not in st.session_state:
        st.session_state['kanban_selected_proposta'] = None
    if 'kanban_nova_proposta_open' not in st.session_state:
        st.session_state['kanban_nova_proposta_open'] = False

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

    hdr_col1, hdr_col2 = st.columns([6, 2])
    with hdr_col1:
        pass
    with hdr_col2:
        nova_btn = st.button("+ Nova Proposta", type="primary", use_container_width=True, key="btn_nova_proposta_top")
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
        ['Aprovada']
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
        font-size: 1rem;
        padding: 8px 12px;
        border-radius: 8px 8px 0 0;
        margin-bottom: 8px;
        text-align: center;
    }
    .kanban-card {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        background: #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .kanban-card-cliente {
        font-weight: 600;
        font-size: 0.93rem;
        margin-bottom: 2px;
    }
    .kanban-card-desc {
        font-size: 0.8rem;
        color: #6c757d;
        margin-bottom: 4px;
    }
    .kanban-card-valor {
        font-size: 0.88rem;
        color: #1a5276;
        font-weight: 600;
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
    with footer_c1:
        st.metric("🟡 Em Aberto", _fmt_brl(total_aberto))
    with footer_c2:
        st.metric("🟢 Aprovada", _fmt_brl(total_aprovada))
    with footer_c3:
        st.metric("🔵 Em Execução", _fmt_brl(total_execucao))
    with footer_c4:
        st.metric("✅ Finalizada", _fmt_brl(total_finalizada))

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
