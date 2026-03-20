import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import time
from datetime import datetime, timedelta
from utils.currency_formatter import format_currency_br, fmt_brl
from utils.fluxo_caixa_simple import FluxoCaixaSimple

def show():
    # Título com estilo personalizado para ficar mais próximo do topo
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">💰 Gestão Financeira</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Registrar Transação",
        "Pendências",
        "Contas a Receber", 
        "Contas a Pagar",
        "Histórico",
        "Dashboard Financeiro",
        "Fluxo de Caixa"
    ])

    with tab1:
        st.subheader("Nova Transação")

        # Definir categorias
        categorias_receita = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
        categorias_despesa = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais", "Custos Administrativos"]

        # Selectbox para tipo fora do form para atualização dinâmica
        tipo = st.selectbox(
            "Tipo",
            ["receita", "despesa"],
            key="tipo_transacao_main"
        )

        # Mostrar formulário baseado no tipo selecionado
        if tipo == "receita":
            st.markdown("#### 💰 Registrar Receita")
            with st.form("registro_receita", clear_on_submit=True):
                descricao = st.text_input("Descrição")
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
                
                tipo_receita = st.selectbox(
                    "Tipo de Receita",
                    ["organização", "comissão", "venda"]
                )

                origem_tipo = st.selectbox(
                    "Origem",
                    ["cliente", "fornecedor"]
                )

                # Carregar origens
                if origem_tipo == "cliente":
                    origens = st.session_state.db.get_clientes()
                    if not origens.empty:
                        origem = st.selectbox("Selecione o Cliente", origens['nome'].tolist())
                        origem_id = origens[origens['nome'] == origem]['id'].iloc[0]
                    else:
                        st.warning("Nenhum cliente cadastrado")
                        origem_id = None
                else:  # fornecedor
                    fornecedores = st.session_state.db.get_fornecedores()
                    if not fornecedores.empty:
                        origem = st.selectbox("Selecione o Fornecedor", fornecedores['descricao'].tolist())
                        origem_id = fornecedores[fornecedores['descricao'] == origem]['id'].iloc[0]
                    else:
                        st.warning("Nenhum fornecedor cadastrado")
                        origem_id = None

                categoria = st.selectbox(
                    "Categoria",
                    categorias_receita
                )

                submitted = st.form_submit_button("Registrar Receita")

                if submitted:
                    if descricao and valor > 0:
                        try:
                            st.session_state.db.add_transacao(
                                tipo="receita",
                                descricao=descricao,
                                valor=valor,
                                categoria=categoria,
                                tipo_receita=tipo_receita,
                                origem_id=origem_id,
                                origem_tipo=origem_tipo
                            )
                            st.success("Receita registrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar receita: {str(e)}")
                    else:
                        st.warning("Por favor, preencha todos os campos corretamente.")

        else:  # despesa
            st.markdown("#### 💸 Registrar Despesa") 
            with st.form("registro_despesa", clear_on_submit=True):
                descricao = st.text_input("Descrição")
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
                
                categoria = st.selectbox(
                    "Categoria",
                    categorias_despesa
                )

                submitted = st.form_submit_button("Registrar Despesa")

                if submitted:
                    if descricao and valor > 0:
                        try:
                            st.session_state.db.add_transacao(
                                tipo="despesa",
                                descricao=descricao,
                                valor=valor,
                                categoria=categoria,
                                tipo_receita=None,
                                origem_id=None,
                                origem_tipo=None
                            )
                            st.success("Despesa registrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar despesa: {str(e)}")
                    else:
                        st.warning("Por favor, preencha todos os campos corretamente.")



    with tab2:
        st.subheader("Pendências Financeiras")

        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_filtro = st.multiselect(
                "Tipo",
                ["receita", "despesa"]
            )
        with col2:
            # Lista completa de categorias para filtro
            categorias_receita = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
            categorias_despesa = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais", "Custos Administrativos"]
            todas_categorias = categorias_receita + categorias_despesa

            categoria_filtro = st.multiselect(
                "Categoria",
                todas_categorias
            )
        with col3:
            data_filtro = st.date_input("Data", format="DD/MM/YYYY")

        # Carregar e filtrar dados
        financeiro = st.session_state.db.get_financeiro()

        if not financeiro.empty:
            # Converter a coluna 'data' para datetime
            financeiro['data'] = pd.to_datetime(financeiro['data'])

            # Filtrar apenas transações pendentes
            financeiro = financeiro[financeiro['status'] == 'Pendente']

            # Filtrar para evitar duplicação de pagamentos de assistentes
            # Primeiro identificamos todos os assistentes que têm transações tanto com categoria antiga quanto nova
            if 'categoria' in financeiro.columns:
                # Caso 1: Identificar duplicações de pagamentos de assistentes
                duplicados_assistentes = []

                # Separar transações com diferentes categorias de assistentes
                assistentes_pagamento_equipe = financeiro[financeiro['categoria'] == 'Pagamento Equipe/Assistentes']
                assistentes_pagamento = financeiro[financeiro['categoria'] == 'Pagamento de Assistente']

                # Se existem registros em ambas categorias
                if not assistentes_pagamento_equipe.empty and not assistentes_pagamento.empty:
                    # Para cada transação com categoria 'Pagamento de Assistente'
                    for _, row in assistentes_pagamento.iterrows():
                        # Verificar se há uma transação correspondente com 'Pagamento Equipe/Assistentes'
                        if 'proposta_id' in row and pd.notna(row['proposta_id']):
                            # Buscar por proposta_id
                            duplicados = assistentes_pagamento_equipe[
                                (assistentes_pagamento_equipe['proposta_id'] == row['proposta_id']) &
                                (assistentes_pagamento_equipe['valor'] == row['valor'])
                            ]
                            if not duplicados.empty:
                                duplicados_assistentes.append(row['id'])

                # Remover as transações duplicadas (manter apenas a versão padronizada)
                if duplicados_assistentes:
                    financeiro = financeiro[~financeiro['id'].isin(list(duplicados_assistentes))]

            # Aplicar filtros adicionais
            if tipo_filtro:
                financeiro = financeiro[financeiro['tipo'].isin(tipo_filtro)]
            if categoria_filtro:
                financeiro = financeiro[financeiro['categoria'].isin(categoria_filtro)]

            # Preparar dados para exibição
            df_display = financeiro.copy()
            df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:.2f}")
            # Formatar o tipo para exibição (simplificar tipos)
            def formatar_tipo(tipo):
                # Referências a 'receita_a_receber' mantidas apenas para compatibilidade
                # com dados históricos no banco que possam conter este valor
                if tipo == 'receita_a_receber':
                    return 'Receita'
                elif tipo == 'receita':
                    return 'Receita'
                elif tipo == 'despesa_a_pagar':
                    return 'Despesa'
                elif tipo == 'despesa':
                    return 'Despesa'
                else:
                    return tipo.title()

            df_display['tipo'] = df_display['tipo'].apply(formatar_tipo)

            # Exibir tabela
            st.dataframe(
                df_display[['data', 'tipo', 'descricao', 'valor', 'categoria', 'status']],
                use_container_width=True,
                hide_index=True
            )

            # Seleção e ações para transação
            if len(financeiro) > 0:
                transacoes_display = [f"{row['descricao']} - R$ {row['valor']:.2f} ({row['data'].strftime('%d/%m/%Y')})" 
                                    for idx, row in financeiro.iterrows()]
                selected_idx = st.selectbox("Selecione uma transação", 
                                          range(len(transacoes_display)),
                                          format_func=lambda x: transacoes_display[x])

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Aprovar", key=f"aprovar_pendencia"):
                        transacao_id = financeiro.iloc[selected_idx]['id']
                        try:
                            st.session_state.db.atualizar_status_transacao(
                                transacao_id,
                                'Aprovado',
                                datetime.now().date()
                            )
                            st.success("Transação aprovada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao aprovar transação: {str(e)}")
                with col2:
                    if st.button("✏️ Editar Selecionado", key="btn_editar_pendencia"):
                        st.session_state.transacao_em_edicao = financeiro.iloc[selected_idx]
                        st.rerun()
                with col3:
                    if st.button("🗑️ Excluir Selecionado", key="btn_excluir_pendencia"):
                        try:
                            if st.session_state.db.delete_transacao(financeiro.iloc[selected_idx]['id']):
                                st.success("Transação excluída com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir transação.")
                        except Exception as e:
                            st.error(f"Erro ao excluir transação: {str(e)}")

        # Modal de edição
        if 'transacao_em_edicao' in st.session_state:
            transacao = st.session_state.transacao_em_edicao
            st.write("---")
            st.subheader("Editar Transação")

            with st.form(key="edicao_transacao_form"):
                # Mapeamento de tipo de transação para simplificar
                # Mantida a referência a "receita_a_receber" apenas para compatibilidade com 
                # dados históricos no banco que possam conter este valor
                tipo_exibido = "receita" if transacao['tipo'] in ["receita", "receita_a_receber"] else "despesa"

                tipo = st.selectbox(
                    "Tipo",
                    ["receita", "despesa"],
                    index=0 if tipo_exibido == "receita" else 1
                )

                descricao = st.text_input("Descrição", value=transacao['descricao'])
                valor = st.number_input("Valor (R$)", value=float(transacao['valor']), min_value=0.0, step=0.01)

                # Simplificado para usar apenas a opção disponível no selectbox
                if tipo == "receita":
                    tipo_receita = st.selectbox(
                        "Tipo de Receita",
                        ["organização", "comissão", "venda"],
                        index=["organização", "comissão", "venda"].index(
                            transacao['tipo_receita'] if pd.notna(transacao.get('tipo_receita')) else "organização"
                        )
                    )
                else:
                    tipo_receita = None

                # Categorias baseadas no tipo da transação (receita ou despesa)
                # Simplificado para usar apenas a opção disponível no selectbox
                if tipo == "receita":
                    categorias_disponíveis = ["Serviços de Organização", "Venda de Produtos", "Comissão sobre Fornecedores", "Serviços Adicionais"]
                    # Tentar encontrar a categoria atual nas novas categorias
                    if transacao['categoria'] == "Serviço":
                        categoria_index = 0  # Serviços de Organização
                    elif transacao['categoria'] in ["Venda de Produtos", "Produto"]:
                        categoria_index = 1  # Venda de Produtos
                    elif transacao['categoria'] in ["Fornecedor", "Comissão"]:
                        categoria_index = 2  # Comissão sobre Fornecedores
                    else:
                        categoria_index = 3  # Serviços Adicionais
                else:
                    categorias_disponíveis = ["Pagamento Equipe/Assistentes", "Pagamento Parceiros/Fornecedores", "Custos Operacionais", "Custos Administrativos"]
                    # Tentar encontrar a categoria atual nas novas categorias
                    if transacao['categoria'] == "Assistente" or transacao['categoria'] == "Pagamento Equipe/Assistentes":
                        categoria_index = 0  # Pagamento Equipe/Assistentes
                    elif transacao['categoria'] == "Fornecedor" or transacao['categoria'] == "Pagamento Parceiros/Fornecedores":
                        categoria_index = 1  # Pagamento Parceiros/Fornecedores
                    else:
                        categoria_index = 3  # Custos Administrativos

                categoria = st.selectbox(
                    "Categoria",
                    categorias_disponíveis,
                    index=categoria_index
                )

                # Criar uma única linha de botões para o form
                col1, col2 = st.columns(2)
                with col1:
                    salvar_button = st.form_submit_button("💾 Salvar")
                with col2:
                    cancelar_button = st.form_submit_button("❌ Cancelar")

            # Lógica de ações após o form
            if salvar_button:
                try:
                    st.session_state.db.update_transacao(
                        transacao['id'],
                        tipo=tipo,
                        descricao=descricao,
                        valor=valor,
                        categoria=categoria,
                        tipo_receita=tipo_receita
                    )
                    st.success("Transação atualizada com sucesso!")
                    del st.session_state.transacao_em_edicao
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar transação: {str(e)}")

            if cancelar_button:
                del st.session_state.transacao_em_edicao
                st.rerun()

        # Resumo financeiro - usar os tipos corretos do banco (maiúscula)
        if not financeiro.empty:
            # Valores a Receber - usar tipos exatos do banco
            receitas = financeiro[
                (((financeiro['tipo'] == 'Receita') | (financeiro['tipo'] == 'receita_a_receber') | 
                  (financeiro['tipo'] == 'receita')) | 
                 (financeiro['classificacao'] == 'contas_a_receber')) & 
                (financeiro['status'] == 'Pendente')
            ]['valor'].sum()

            # Valores a Pagar - usar tipos exatos do banco
            despesas = financeiro[
                (((financeiro['tipo'] == 'Despesa') | (financeiro['tipo'] == 'despesa_a_pagar') |
                  (financeiro['tipo'] == 'despesa')) |
                 (financeiro['classificacao'] == 'contas_a_pagar')) & 
                (financeiro['status'] == 'Pendente')
            ]['valor'].sum()
        else:
            receitas = 0
            despesas = 0

        saldo = receitas - despesas

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Receitas", format_currency_br(receitas))
        col2.metric("Total Despesas", format_currency_br(despesas))
        col3.metric("Saldo", format_currency_br(saldo))
        if financeiro.empty:
            st.info("Nenhuma transação encontrada.")


    with tab3:
        st.subheader("Contas a Receber")

        # CSS compacto para cards de contas a receber (borda verde)
        st.markdown("""
        <style>
        .cr-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #38A169;
            border-radius: 8px;
            padding: 10px 16px;
            margin-bottom: 6px;
        }
        .cr-title {
            font-weight: 700;
            font-size: 0.92rem;
            color: #1a202c;
            margin: 0 0 3px 0;
        }
        .cr-meta {
            font-size: 0.78rem;
            color: #64748b;
            margin: 0;
        }
        .cr-valor {
            font-weight: 700;
            color: #38A169;
            font-size: 1.05rem;
            white-space: nowrap;
        }
        .cr-resumo {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 12px;
            display: flex;
            gap: 24px;
        }
        .cr-resumo-item { flex: 1; text-align: center; }
        .cr-resumo-label { font-size: 0.75rem; color: #64748b; margin: 0; }
        .cr-resumo-valor { font-size: 1rem; font-weight: 700; color: #1a202c; margin: 0; }
        </style>
        """, unsafe_allow_html=True)

        if 'reload_contas_receber' not in st.session_state:
            st.session_state.reload_contas_receber = False

        contas_receber = st.session_state.db.get_contas_receber(
            force_reload=st.session_state.reload_contas_receber or True
        )
        st.session_state.reload_contas_receber = False

        if not contas_receber.empty:
            contas_receber = contas_receber[contas_receber['status'] == 'Pendente']

        if not contas_receber.empty:
            for idx, conta in contas_receber.iterrows():
                receber_key = f"cr_receber_{conta['id']}"
                cancelar_key = f"cr_cancelar_{conta['id']}"

                if receber_key not in st.session_state:
                    st.session_state[receber_key] = False
                if cancelar_key not in st.session_state:
                    st.session_state[cancelar_key] = False

                # Montar linha de metadados
                partes_meta = []
                if 'origem_tipo' in conta and pd.notna(conta.get('origem_tipo')) and conta['origem_tipo']:
                    partes_meta.append(str(conta['origem_tipo']))
                if 'categoria' in conta and pd.notna(conta.get('categoria')) and conta['categoria']:
                    partes_meta.append(str(conta['categoria']))
                if 'proposta_id' in conta and pd.notna(conta.get('proposta_id')):
                    partes_meta.append(f"Proposta #{int(conta['proposta_id'])}")
                if 'data' in conta and pd.notna(conta.get('data')):
                    partes_meta.append(f"📅 {pd.to_datetime(conta['data']).strftime('%d/%m/%Y')}")
                meta_str = " · ".join(partes_meta) if partes_meta else "—"

                # Card + botões na mesma linha
                col_card, col_receber, col_cancelar = st.columns([5, 1, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="cr-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <p class="cr-title">{conta['descricao']}</p>
                                <p class="cr-meta">{meta_str}</p>
                            </div>
                            <span class="cr-valor">R$ {conta['valor']:.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_receber:
                    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                    if not st.session_state.get(receber_key) and not st.session_state.get(cancelar_key):
                        if st.button("✅ Receber", key=f"btn_{receber_key}", use_container_width=True):
                            st.session_state[receber_key] = True
                            st.rerun()

                with col_cancelar:
                    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                    if not st.session_state.get(receber_key) and not st.session_state.get(cancelar_key):
                        if st.button("❌ Excluir", key=f"btn_{cancelar_key}", use_container_width=True):
                            st.session_state[cancelar_key] = True
                            st.rerun()

                # Confirmação de recebimento
                if st.session_state.get(receber_key):
                    with st.container():
                        st.success(f"Confirmar recebimento de **R$ {conta['valor']:.2f}** — {conta['descricao']}?")
                        c1, c2, _ = st.columns([1, 1, 5])
                        with c1:
                            if st.button("✓ Confirmar", key=f"confirm_{receber_key}", use_container_width=True):
                                try:
                                    result = st.session_state.db.atualizar_status_transacao(
                                        transacao_id=conta['id'],
                                        status='Recebido',
                                        data_recebimento=datetime.now().date()
                                    )
                                    if result:
                                        st.session_state.reload_contas_receber = True
                                        st.session_state[receber_key] = False
                                        st.rerun()
                                    else:
                                        st.error("Erro ao registrar recebimento.")
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                        with c2:
                            if st.button("✗ Voltar", key=f"cancel_{receber_key}", use_container_width=True):
                                st.session_state[receber_key] = False
                                st.rerun()

                # Confirmação de cancelamento
                if st.session_state.get(cancelar_key):
                    with st.container():
                        st.warning(f"Excluir a conta **{conta['descricao']}** permanentemente?")
                        c1, c2, _ = st.columns([1, 1, 5])
                        with c1:
                            if st.button("✓ Confirmar", key=f"confirm_{cancelar_key}", use_container_width=True):
                                try:
                                    result = st.session_state.db.atualizar_status_transacao(
                                        transacao_id=conta['id'],
                                        status='Cancelado'
                                    )
                                    if result:
                                        st.session_state.reload_contas_receber = True
                                        st.session_state[cancelar_key] = False
                                        st.rerun()
                                    else:
                                        st.error("Erro ao excluir.")
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                        with c2:
                            if st.button("✗ Voltar", key=f"voltar_{cancelar_key}", use_container_width=True):
                                st.session_state[cancelar_key] = False
                                st.rerun()

            # Resumo compacto
            total_pendente = contas_receber['valor'].sum()
            st.markdown(f"""
            <div class="cr-resumo">
                <div class="cr-resumo-item">
                    <p class="cr-resumo-label">Total Pendente</p>
                    <p class="cr-resumo-valor" style="color:#38A169;">R$ {total_pendente:.2f}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma conta a receber cadastrada.")

    with tab4:
        st.subheader("Contas a Pagar")

        # CSS compacto para cards de contas a pagar
        st.markdown("""
        <style>
        .cp-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #E53E3E;
            border-radius: 8px;
            padding: 10px 16px;
            margin-bottom: 6px;
        }
        .cp-title {
            font-weight: 700;
            font-size: 0.92rem;
            color: #1a202c;
            margin: 0 0 3px 0;
        }
        .cp-meta {
            font-size: 0.78rem;
            color: #64748b;
            margin: 0;
        }
        .cp-valor {
            font-weight: 700;
            color: #E53E3E;
            font-size: 1.05rem;
            white-space: nowrap;
        }
        .cp-resumo {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 12px;
            display: flex;
            gap: 24px;
        }
        .cp-resumo-item { flex: 1; text-align: center; }
        .cp-resumo-label { font-size: 0.75rem; color: #64748b; margin: 0; }
        .cp-resumo-valor { font-size: 1rem; font-weight: 700; color: #1a202c; margin: 0; }
        </style>
        """, unsafe_allow_html=True)

        if 'reload_contas_pagar' not in st.session_state:
            st.session_state.reload_contas_pagar = False

        force_reload = True
        if st.session_state.reload_contas_pagar:
            st.session_state.reload_contas_pagar = False

        contas_pagar = st.session_state.db.get_financeiro(force_reload=force_reload)
        if not contas_pagar.empty:
            contas_pagar = contas_pagar[
                (
                    (contas_pagar['classificacao'] == 'contas_a_pagar') |
                    (contas_pagar['tipo'] == 'despesa') |
                    (contas_pagar['tipo'] == 'despesa_a_pagar')
                ) &
                (contas_pagar['status'] == 'Pendente')
            ]

            if not contas_pagar.empty:
                filtro_tipo = st.radio(
                    "Filtrar por tipo:",
                    ["Todos", "Assistentes", "Outros"],
                    horizontal=True
                )

                if filtro_tipo == "Assistentes":
                    contas_pagar = contas_pagar[
                        (contas_pagar['categoria'] == 'Assistente') |
                        (contas_pagar['categoria'] == 'Pagamento Equipe/Assistentes') |
                        (contas_pagar['categoria'] == 'Pagamento de Assistente') |
                        (contas_pagar['subcategoria'] == 'Assistentes') |
                        (contas_pagar['descricao'].str.contains('Assistente:', na=False))
                    ]
                elif filtro_tipo == "Outros":
                    contas_pagar = contas_pagar[
                        (contas_pagar['categoria'] != 'Assistente') &
                        (contas_pagar['categoria'] != 'Pagamento Equipe/Assistentes') &
                        (contas_pagar['categoria'] != 'Pagamento de Assistente') &
                        (contas_pagar['subcategoria'] != 'Assistentes') &
                        (~contas_pagar['descricao'].str.contains('Assistente:', na=False))
                    ]

                if not contas_pagar.empty:
                    for idx, conta in contas_pagar.iterrows():
                        pagar_key = f"pagar_{conta['id']}"
                        cancelar_key = f"cancelar_pagar_{conta['id']}"

                        if pagar_key not in st.session_state:
                            st.session_state[pagar_key] = False
                        if cancelar_key not in st.session_state:
                            st.session_state[cancelar_key] = False

                        # Montar linha de metadados
                        partes_meta = [conta['categoria']]
                        if 'subcategoria' in conta and pd.notna(conta.get('subcategoria')) and conta['subcategoria']:
                            partes_meta.append(str(conta['subcategoria']))
                        if 'proposta_id' in conta and pd.notna(conta.get('proposta_id')):
                            partes_meta.append(f"Proposta #{int(conta['proposta_id'])}")
                        partes_meta.append(f"📅 {pd.to_datetime(conta['data']).strftime('%d/%m/%Y')}")
                        meta_str = " · ".join(partes_meta)

                        # Card compacto com info e valor lado a lado
                        col_card, col_pagar, col_excluir = st.columns([5, 1, 1])
                        with col_card:
                            st.markdown(f"""
                            <div class="cp-card">
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <div>
                                        <p class="cp-title">{conta['descricao']}</p>
                                        <p class="cp-meta">{meta_str}</p>
                                    </div>
                                    <span class="cp-valor">R$ {conta['valor']:.2f}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col_pagar:
                            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                            if not st.session_state.get(pagar_key) and not st.session_state.get(cancelar_key):
                                if st.button("✅ Pagar", key=f"btn_{pagar_key}", use_container_width=True):
                                    st.session_state[pagar_key] = True
                                    st.rerun()

                        with col_excluir:
                            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                            if not st.session_state.get(pagar_key) and not st.session_state.get(cancelar_key):
                                if st.button("❌ Excluir", key=f"btn_{cancelar_key}", use_container_width=True):
                                    st.session_state[cancelar_key] = True
                                    st.rerun()

                        # Confirmação de pagamento (inline, abaixo do card)
                        if st.session_state.get(pagar_key):
                            with st.container():
                                st.success(f"Confirmar pagamento de **R$ {conta['valor']:.2f}** — {conta['descricao']}?")
                                c1, c2, _ = st.columns([1, 1, 5])
                                with c1:
                                    if st.button("✓ Confirmar", key=f"confirm_{pagar_key}", use_container_width=True):
                                        try:
                                            result = st.session_state.db.atualizar_status_transacao(
                                                transacao_id=conta['id'],
                                                status='Pago',
                                                data_recebimento=datetime.now().date()
                                            )
                                            if result:
                                                st.session_state.reload_contas_pagar = True
                                                st.session_state[pagar_key] = False
                                                st.rerun()
                                            else:
                                                st.error("Erro ao registrar pagamento.")
                                        except Exception as e:
                                            st.error(f"Erro: {str(e)}")
                                with c2:
                                    if st.button("✗ Voltar", key=f"cancel_{pagar_key}", use_container_width=True):
                                        st.session_state[pagar_key] = False
                                        st.rerun()

                        # Confirmação de cancelamento
                        if st.session_state.get(cancelar_key):
                            with st.container():
                                st.warning(f"Excluir a conta **{conta['descricao']}** permanentemente?")
                                c1, c2, _ = st.columns([1, 1, 5])
                                with c1:
                                    if st.button("✓ Confirmar", key=f"confirm_{cancelar_key}", use_container_width=True):
                                        try:
                                            result = st.session_state.db.atualizar_status_transacao(
                                                transacao_id=conta['id'],
                                                status='Cancelado'
                                            )
                                            if result:
                                                st.session_state.reload_contas_pagar = True
                                                st.session_state[cancelar_key] = False
                                                st.rerun()
                                            else:
                                                st.error("Erro ao cancelar.")
                                        except Exception as e:
                                            st.error(f"Erro: {str(e)}")
                                with c2:
                                    if st.button("✗ Voltar", key=f"voltar_{cancelar_key}", use_container_width=True):
                                        st.session_state[cancelar_key] = False
                                        st.rerun()

                    # Resumo compacto
                    total_pendente = contas_pagar['valor'].sum()
                    assistentes_mask = (
                        (contas_pagar['categoria'] == 'Assistente') |
                        (contas_pagar['categoria'] == 'Pagamento Equipe/Assistentes') |
                        (contas_pagar['categoria'] == 'Pagamento de Assistente') |
                        (contas_pagar['subcategoria'] == 'Assistentes') |
                        (contas_pagar['descricao'].str.contains('Assistente:', na=False))
                    )
                    total_assistentes = contas_pagar[assistentes_mask]['valor'].sum()
                    total_outros = total_pendente - total_assistentes

                    st.markdown(f"""
                    <div class="cp-resumo">
                        <div class="cp-resumo-item">
                            <p class="cp-resumo-label">Total Pendente</p>
                            <p class="cp-resumo-valor" style="color:#E53E3E;">R$ {total_pendente:.2f}</p>
                        </div>
                        <div class="cp-resumo-item">
                            <p class="cp-resumo-label">Assistentes</p>
                            <p class="cp-resumo-valor">R$ {total_assistentes:.2f}</p>
                        </div>
                        <div class="cp-resumo-item">
                            <p class="cp-resumo-label">Outros</p>
                            <p class="cp-resumo-valor">R$ {total_outros:.2f}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"Nenhuma conta a pagar encontrada do tipo {filtro_tipo.lower()}.")
            else:
                st.info("Nenhuma conta a pagar pendente. Para visualizar contas pagas ou canceladas, consulte a aba Histórico.")
        else:
            st.info("Nenhuma transação financeira encontrada.")

    with tab5:
        st.subheader("Histórico Financeiro")

        # CSS para o histórico
        st.markdown("""
        <style>
        .hf-filtros {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 18px 6px 18px;
            margin-bottom: 16px;
        }
        .hf-filtros-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 8px 0;
        }
        .hf-metric-row {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        .hf-metric {
            flex: 1;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px 16px;
            text-align: center;
        }
        .hf-metric-label { font-size: 0.72rem; color: #64748b; margin: 0 0 4px 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
        .hf-metric-value { font-size: 1.25rem; font-weight: 800; margin: 0; }
        .hf-row-receita { border-left: 3px solid #38A169; }
        .hf-row-despesa { border-left: 3px solid #E53E3E; }
        .hf-section-title {
            font-size: 0.78rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 16px 0 8px 0;
        }
        </style>
        """, unsafe_allow_html=True)

        if 'filtro_historico' not in st.session_state:
            st.session_state.filtro_historico = {
                "tipo": [],
                "status": ["Aprovado", "Recebido", "Pago", "Cancelado"]
            }

        historico = st.session_state.db.get_financeiro(force_reload=True)

        if not historico.empty:
            historico['data'] = pd.to_datetime(historico['data'])
            historico = historico[~(historico['status'] == 'Pendente')]

            # Painel de filtros compacto
            st.markdown('<div class="hf-filtros"><p class="hf-filtros-label">🔍 Filtros</p>', unsafe_allow_html=True)
            f1, f2, f3, f4 = st.columns([2, 2, 1.5, 1.5])
            with f1:
                tipo_selecionado = st.multiselect(
                    "Tipo", ["receita", "despesa"],
                    default=st.session_state.filtro_historico["tipo"],
                    key="hist_tipo"
                )
            with f2:
                status_selecionado = st.multiselect(
                    "Status", ["Aprovado", "Recebido", "Pago", "Cancelado"],
                    default=st.session_state.filtro_historico["status"],
                    key="hist_status"
                )
            with f3:
                hoje = datetime.now().date()
                data_inicio = st.date_input("De", value=hoje.replace(day=1), key="historico_data_inicio", format="DD/MM/YYYY")
            with f4:
                data_fim = st.date_input("Até", value=hoje, key="historico_data_fim", format="DD/MM/YYYY")
            st.markdown('</div>', unsafe_allow_html=True)

            # Aplicar filtros
            if tipo_selecionado:
                historico = historico[historico['tipo'].isin(tipo_selecionado)]
            if status_selecionado:
                historico = historico[historico['status'].isin(status_selecionado)]
            historico = historico[
                (historico['data'].dt.date >= data_inicio) &
                (historico['data'].dt.date <= data_fim)
            ]

            if not historico.empty:
                # Métricas em destaque
                receitas = historico[historico['tipo'].isin(['receita', 'receita_a_receber'])]['valor'].sum()
                despesas = historico[historico['tipo'].isin(['despesa', 'despesa_a_pagar'])]['valor'].sum()
                saldo = receitas - despesas
                saldo_cor = "#38A169" if saldo >= 0 else "#E53E3E"

                st.markdown(f"""
                <div class="hf-metric-row">
                    <div class="hf-metric">
                        <p class="hf-metric-label">Receitas</p>
                        <p class="hf-metric-value" style="color:#38A169;">R$ {receitas:,.2f}</p>
                    </div>
                    <div class="hf-metric">
                        <p class="hf-metric-label">Despesas</p>
                        <p class="hf-metric-value" style="color:#E53E3E;">R$ {despesas:,.2f}</p>
                    </div>
                    <div class="hf-metric">
                        <p class="hf-metric-label">Saldo</p>
                        <p class="hf-metric-value" style="color:{saldo_cor};">R$ {saldo:,.2f}</p>
                    </div>
                    <div class="hf-metric">
                        <p class="hf-metric-label">Transações</p>
                        <p class="hf-metric-value" style="color:#1E2547;">{len(historico)}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tabela de resultados
                def formatar_tipo(tipo):
                    if tipo in ['receita_a_receber', 'receita', 'Receita']:
                        return 'Receita'
                    elif tipo in ['despesa_a_pagar', 'despesa', 'Despesa']:
                        return 'Despesa'
                    return tipo.title()

                df_display = historico.copy()
                df_display['Tipo'] = df_display['tipo'].apply(formatar_tipo)
                df_display['Data'] = df_display['data'].dt.strftime('%d/%m/%Y')
                df_display['Valor (R$)'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
                df_display['Descrição'] = df_display['descricao']
                df_display['Categoria'] = df_display['categoria'].fillna('—')
                df_display['Status'] = df_display['status']

                st.markdown('<p class="hf-section-title">Transações</p>', unsafe_allow_html=True)
                st.dataframe(
                    df_display[['Data', 'Tipo', 'Descrição', 'Valor (R$)', 'Categoria', 'Status']],
                    use_container_width=True,
                    hide_index=True
                )

                # Gráfico de distribuição por categoria
                if not historico.empty:
                    st.markdown('<p class="hf-section-title">Distribuição por Categoria</p>', unsafe_allow_html=True)
                    fig = px.bar(
                        historico,
                        x='categoria',
                        y='valor',
                        color='tipo',
                        color_discrete_map={'receita': '#38A169', 'despesa': '#E53E3E'},
                        labels={'valor': 'Valor (R$)', 'categoria': 'Categoria', 'tipo': 'Tipo'},
                        height=300
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=10, b=0),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Gerenciar transação (excluir)
                st.markdown('<p class="hf-section-title">Excluir Transação</p>', unsafe_allow_html=True)
                transacoes_display = [
                    f"{row['data'].strftime('%d/%m/%Y')} · {row['descricao']} · R$ {row['valor']:,.2f} · {row['status']}"
                    for idx, row in historico.iterrows()
                ]
                col_sel, col_del = st.columns([5, 1])
                with col_sel:
                    selected_idx = st.selectbox(
                        "Selecione:",
                        range(len(transacoes_display)),
                        format_func=lambda x: transacoes_display[x],
                        key="select_transacao_historico",
                        label_visibility="collapsed"
                    )
                with col_del:
                    if st.button("🗑️ Excluir", key="btn_excluir_historico", use_container_width=True):
                        transacao_sel = historico.iloc[selected_idx]
                        st.session_state[f"confirmar_exclusao_{transacao_sel['id']}"] = True
                        st.rerun()

                if selected_idx is not None:
                    transacao_sel = historico.iloc[selected_idx]
                    if st.session_state.get(f"confirmar_exclusao_{transacao_sel['id']}", False):
                        st.warning(f"Excluir **{transacao_sel['descricao']}** — R$ {transacao_sel['valor']:,.2f}?")
                        c1, c2, _ = st.columns([1, 1, 5])
                        with c1:
                            if st.button("✓ Confirmar", key=f"confirmar_exclusao_final_{transacao_sel['id']}", use_container_width=True):
                                try:
                                    if st.session_state.db.delete_transacao(transacao_sel['id']):
                                        st.success("Transação excluída!")
                                        del st.session_state[f"confirmar_exclusao_{transacao_sel['id']}"]
                                        st.rerun()
                                    else:
                                        st.error("Erro ao excluir transação.")
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                        with c2:
                            if st.button("✗ Voltar", key=f"cancelar_exclusao_{transacao_sel['id']}", use_container_width=True):
                                del st.session_state[f"confirmar_exclusao_{transacao_sel['id']}"]
                                st.rerun()
            else:
                st.info("Nenhuma transação encontrada com os filtros selecionados.")
        else:
            st.info("Não há transações no histórico.")

    with tab6:
        st.subheader("Dashboard Financeiro")

        # Obter dados financeiros com force_reload para evitar cache
        financeiro_completo = st.session_state.db.get_financeiro(force_reload=True)

        if not financeiro_completo.empty:
            # Remover função de simplificação - usar diretamente os tipos do banco

            # Card com resumo geral (métricas)
            st.subheader("Resumo Geral")

            # Calcular totais usando os tipos exatos do banco (com maiúscula)
            total_receitas = financeiro_completo[
                (((financeiro_completo['tipo'] == 'Receita') | (financeiro_completo['tipo'] == 'receita_a_receber') | 
                  (financeiro_completo['tipo'] == 'receita')) | 
                 (financeiro_completo['classificacao'] == 'contas_a_receber')) & 
                (financeiro_completo['status'] == 'Pendente')
            ]['valor'].sum()

            total_despesas = financeiro_completo[
                (((financeiro_completo['tipo'] == 'Despesa') | (financeiro_completo['tipo'] == 'despesa_a_pagar') |
                  (financeiro_completo['tipo'] == 'despesa')) |
                 (financeiro_completo['classificacao'] == 'contas_a_pagar')) & 
                (financeiro_completo['status'] == 'Pendente')
            ]['valor'].sum()

            saldo = total_receitas - total_despesas

            # Exibir as métricas
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Receitas", format_currency_br(total_receitas))
            col2.metric("Total Despesas", format_currency_br(total_despesas))
            col3.metric("Saldo", format_currency_br(saldo))

            # Resumo de Contas a Receber, com force_reload
            contas_receber = st.session_state.db.get_contas_receber(force_reload=True)
            if not contas_receber.empty:
                st.subheader("Resumo de Contas a Receber")

                # Agrupar por origem e status
                resumo_receber = contas_receber.groupby(['origem_tipo', 'status'])['valor'].sum().reset_index()

                # Gráfico de barras empilhadas
                fig_receber = px.bar(
                    resumo_receber,
                    x='origem_tipo',
                    y='valor',
                    color='status',
                    title='Contas a Receber por Origem',
                    labels={'valor': 'Valor (R$)', 'origem_tipo': 'Origem', 'status': 'Status'}
                )
                st.plotly_chart(fig_receber, use_container_width=True)

            # Gráfico de Receitas vs Despesas por Categoria (usando dados originais)
            fig1 = px.bar(
                financeiro_completo,
                x='categoria',
                y='valor',
                color='tipo',
                title='Transações por Categoria',
                labels={'valor': 'Valor (R$)', 'categoria': 'Categoria', 'tipo': 'Tipo'}
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Evolução Temporal
            financeiro_completo['data'] = pd.to_datetime(financeiro_completo['data'])
            dados_temporais = financeiro_completo.groupby(
                [pd.Grouper(key='data', freq='ME'), 'tipo']
            )['valor'].sum().reset_index()

            fig2 = px.line(
                dados_temporais,
                x='data',
                y='valor',
                color='tipo',
                title='Evolução Temporal',
                labels={'valor': 'Valor (R$)', 'data': 'Data', 'tipo': 'Tipo'}
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Distribuição por Tipo de Receita
            receitas = financeiro_completo[financeiro_completo['tipo'] == 'Receita']
            if not receitas.empty and 'tipo_receita' in receitas.columns:
                fig3 = px.pie(
                    receitas,
                    values='valor',
                    names='tipo_receita',
                    title='Distribuição por Tipo de Receita'
                )
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Não há dados suficientes para gerar o dashboard.")

    with tab7:
        st.subheader("💰 Fluxo de Caixa")
        
        # Inicializar módulo simplificado
        if 'fluxo_caixa_simple' not in st.session_state:
            st.session_state.fluxo_caixa_simple = FluxoCaixaSimple(st.session_state.db)
        
        # Seleção do período
        col1, col2 = st.columns(2)
        with col1:
            ano_selecionado = st.selectbox(
                "Ano",
                options=list(range(2023, 2027)),
                index=list(range(2023, 2027)).index(datetime.now().year),
                key="fluxo_ano"
            )
        with col2:
            mes_selecionado = st.selectbox(
                "Mês",
                options=list(range(1, 13)),
                format_func=lambda x: datetime(2024, x, 1).strftime('%B'),
                index=datetime.now().month - 1,
                key="fluxo_mes"
            )
        
        # Tabs para diferentes visualizações
        tab_visao_geral, tab_transacoes, tab_categorias, tab_filtros = st.tabs([
            "📊 Visão Geral", 
            "📋 Transações", 
            "🏷️ Por Categoria",
            "🔍 Categorias Usadas"
        ])
        
        with tab_visao_geral:
            # Resumo mensal
            resumo = st.session_state.fluxo_caixa_simple.get_resumo_mensal(ano_selecionado, mes_selecionado)
            
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total Receitas", fmt_brl(resumo['total_receitas']))
            col2.metric("💸 Total Despesas", fmt_brl(resumo['total_despesas']))
            
            saldo_cor = "normal"
            if resumo['saldo_mes'] > 0:
                saldo_cor = "inverse" 
            col3.metric("📈 Saldo do Mês", fmt_brl(resumo['saldo_mes']))
            
            # Status das transações
            st.markdown("#### 📊 Status das Transações")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("✅ Receitas Pagas", fmt_brl(resumo['receitas_pagas']))
            col2.metric("⏳ Receitas Pendentes", fmt_brl(resumo['receitas_pendentes']))
            col3.metric("✅ Despesas Pagas", fmt_brl(resumo['despesas_pagas']))
            col4.metric("⏳ Despesas Pendentes", fmt_brl(resumo['despesas_pendentes']))
        
        with tab_transacoes:
            # Lista de transações do mês
            transacoes = st.session_state.fluxo_caixa_simple.get_transacoes_mes(ano_selecionado, mes_selecionado)
            
            if not transacoes.empty:
                # Formatação para exibição
                df_display = transacoes.copy()
                df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
                df_display['valor_formatado'] = df_display['valor'].apply(fmt_brl)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    tipos_filtro = st.multiselect(
                        "Filtrar por Tipo",
                        options=df_display['tipo'].unique(),
                        default=df_display['tipo'].unique(),
                        key="filtro_tipo_transacoes"
                    )
                with col2:
                    status_filtro = st.multiselect(
                        "Filtrar por Status", 
                        options=df_display['status'].unique(),
                        default=df_display['status'].unique(),
                        key="filtro_status_transacoes"
                    )
                
                # Aplicar filtros
                if tipos_filtro:
                    transacoes_filtradas = df_display[df_display['tipo'].isin(list(tipos_filtro))]
                else:
                    transacoes_filtradas = df_display
                    
                if status_filtro:
                    transacoes_filtradas = transacoes_filtradas[transacoes_filtradas['status'].isin(list(status_filtro))]
                
                # Exibir tabela
                st.dataframe(
                    transacoes_filtradas[['data', 'tipo', 'descricao', 'categoria', 'valor_formatado', 'status']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "data": "Data",
                        "tipo": "Tipo", 
                        "descricao": "Descrição",
                        "categoria": "Categoria",
                        "valor_formatado": "Valor",
                        "status": "Status"
                    }
                )
                
                # Botão de exportação
                if st.button("📊 Exportar para CSV"):
                    csv_data = st.session_state.fluxo_caixa_simple.export_to_dataframe(ano_selecionado, mes_selecionado)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data.to_csv(index=False),
                        file_name=f"fluxo_caixa_{ano_selecionado}_{mes_selecionado:02d}.csv",
                        mime="text/csv"
                    )
            else:
                st.info(f"Nenhuma transação encontrada para {datetime(2024, mes_selecionado, 1).strftime('%B')} de {ano_selecionado}")
        
        with tab_categorias:
            # Análise por categoria
            resumo_categorias = st.session_state.fluxo_caixa_simple.get_resumo_por_categoria(ano_selecionado, mes_selecionado)
            
            if resumo_categorias:
                # Converter para DataFrame para visualização
                dados_categorias = []
                for categoria, dados in resumo_categorias.items():
                    dados_categorias.append({
                        'Categoria': categoria,
                        'Receitas': dados['receitas'],
                        'Despesas': dados['despesas'], 
                        'Saldo': dados['saldo'],
                        'Transações': dados['transacoes']
                    })
                
                df_categorias = pd.DataFrame(dados_categorias)
                
                # Formatar valores monetários
                for col in ['Receitas', 'Despesas', 'Saldo']:
                    df_categorias[col + '_formatado'] = df_categorias[col].apply(fmt_brl)
                
                # Exibir tabela
                st.dataframe(
                    df_categorias[['Categoria', 'Receitas_formatado', 'Despesas_formatado', 'Saldo_formatado', 'Transações']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Receitas_formatado": "Receitas",
                        "Despesas_formatado": "Despesas", 
                        "Saldo_formatado": "Saldo"
                    }
                )
                
                # Gráfico de categorias
                if len(df_categorias) > 0:
                    fig = px.bar(
                        df_categorias, 
                        x='Categoria',
                        y=['Receitas', 'Despesas'],
                        title=f"Receitas vs Despesas por Categoria - {datetime(2024, mes_selecionado, 1).strftime('%B')} {ano_selecionado}",
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma transação para análise por categoria neste período")
        
        with tab_filtros:
            # Mostrar categorias utilizadas
            st.markdown("#### 📋 Categorias Registradas no Sistema")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**💰 Categorias de Receitas:**")
                categorias_receitas = st.session_state.fluxo_caixa_simple.get_categorias_usadas("receita")
                if categorias_receitas:
                    for categoria in categorias_receitas:
                        st.write(f"• {categoria}")
                else:
                    st.info("Nenhuma categoria de receita registrada")
            
            with col2:
                st.markdown("**💸 Categorias de Despesas:**")
                categorias_despesas = st.session_state.fluxo_caixa_simple.get_categorias_usadas("despesa")
                if categorias_despesas:
                    for categoria in categorias_despesas:
                        st.write(f"• {categoria}")
                else:
                    st.info("Nenhuma categoria de despesa registrada")

    # CSS e JavaScript para eliminar qualquer fundo azul restante e corrigir selectbox
    st.markdown("""
    <style>
    /* Correção específica para selectbox desta página */
    div[data-testid="stSelectbox"] * {
        color: #1e1e1e !important;
        font-weight: 500 !important;
    }

    div[data-testid="stSelectbox"] [data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }

    /* Estilos gerais para consistência */
    .stSelectbox>label {
        color: #1e1e1e !important;
    }

    /* Eliminar fundo azul */
    div[data-testid="stSelectbox"] div[data-baseweb="select"]>div {
        background-color: white !important;
    }

    /* Corrigir cor do texto */
    div[data-testid="stSelectbox"] div[data-baseweb="select"]>div>span {
        color: #1e1e1e !important;
    }

    /* Definitivamente garantir que o texto seja legível */
    div[data-testid="stSelectbox"] div[data-baseweb="select"]>div>span {
        opacity: 1 !important;
    }
    </style>

    <script>
    function removeBlueBackgrounds() {
        // Selecionar todos os elementos que podem ter o fundo azul
        var elements = document.querySelectorAll('div[data-testid="stSelectbox"] *');

        // Remover a cor de fundo azul de todos os elementos
        elements.forEach(function(element) {
            element.style.backgroundColor = 'white !important';
        });
    }

    // Executar periodicamente
    setInterval(removeBlueBackgrounds, 1000);

    // Corrigir selectbox - FORÇAR TEXTO VISÍVEL
    function fixSelectboxes() {
        const selectboxes = document.querySelectorAll('[data-testid="stSelectbox"]');
        selectboxes.forEach(selectbox => {
            const textElements = selectbox.querySelectorAll('*');
            textElements.forEach(el => {
                if (el.textContent && el.textContent.trim() !== '') {
                    el.style.setProperty('color', '#1e1e1e', 'important');
                    el.style.fontWeight = '500';
                    el.style.opacity = '1';
                    el.style.visibility = 'visible';
                }
            });
        });
    }

    // Executar correção de selectbox
    fixSelectboxes();
    setInterval(fixSelectboxes, 1000);
    </script>
    """, unsafe_allow_html=True)