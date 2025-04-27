import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def show():
    # Título com estilo personalizado para ficar mais próximo do topo
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">💰 Gestão Financeira</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Registrar Transação",
        "Extrato",
        "Contas a Receber", 
        "Contas a Pagar",
        "Dashboard Financeiro"
    ])

    with tab1:
        st.subheader("Nova Transação")

        with st.form("registro_transacao", clear_on_submit=True):
            tipo = st.selectbox(
                "Tipo",
                ["receita", "despesa", "receita_a_receber"]
            )

            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            if tipo in ["receita", "receita_a_receber"]:
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
            else:
                tipo_receita = None
                origem_tipo = None
                origem_id = None

            categoria = st.selectbox(
                "Categoria",
                ["Serviço", "Produto", "Fornecedor", "Outros"]
            )

            submitted = st.form_submit_button("Registrar")

            if submitted:
                if descricao and valor > 0:
                    try:
                        st.session_state.db.add_transacao(
                            tipo=tipo,
                            descricao=descricao,
                            valor=valor,
                            categoria=categoria,
                            tipo_receita=tipo_receita,
                            origem_id=origem_id,
                            origem_tipo=origem_tipo
                        )
                        st.success("Transação registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar transação: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos corretamente.")

    with tab2:
        st.subheader("Extrato Financeiro")

        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_filtro = st.multiselect(
                "Tipo",
                ["receita", "despesa", "receita_a_receber"]
            )
        with col2:
            categoria_filtro = st.multiselect(
                "Categoria",
                ["Serviço", "Produto", "Fornecedor", "Outros"]
            )
        with col3:
            data_filtro = st.date_input("Data")

        # Carregar e filtrar dados
        financeiro = st.session_state.db.get_financeiro()

        if not financeiro.empty:
            # Converter a coluna 'data' para datetime
            financeiro['data'] = pd.to_datetime(financeiro['data'])

            # Aplicar filtros
            if tipo_filtro:
                financeiro = financeiro[financeiro['tipo'].isin(tipo_filtro)]
            if categoria_filtro:
                financeiro = financeiro[financeiro['categoria'].isin(categoria_filtro)]

            # Preparar dados para exibição
            df_display = financeiro.copy()
            df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:.2f}")
            df_display['tipo'] = df_display['tipo'].apply(lambda x: x.title())

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

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Editar Selecionado"):
                        st.session_state.transacao_em_edicao = financeiro.iloc[selected_idx]
                        st.rerun()
                with col2:
                    if st.button("🗑️ Excluir Selecionado"):
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
                tipo = st.selectbox(
                    "Tipo",
                    ["receita", "despesa", "receita_a_receber"],
                    index=["receita", "despesa", "receita_a_receber"].index(transacao['tipo'])
                )

                descricao = st.text_input("Descrição", value=transacao['descricao'])
                valor = st.number_input("Valor (R$)", value=float(transacao['valor']), min_value=0.0, step=0.01)

                if tipo in ["receita", "receita_a_receber"]:
                    tipo_receita = st.selectbox(
                        "Tipo de Receita",
                        ["organização", "comissão", "venda"],
                        index=["organização", "comissão", "venda"].index(
                            transacao['tipo_receita'] if pd.notna(transacao.get('tipo_receita')) else "organização"
                        )
                    )
                else:
                    tipo_receita = None

                categoria = st.selectbox(
                    "Categoria",
                    ["Serviço", "Produto", "Fornecedor", "Assistente", "Outros"],
                    index=["Serviço", "Produto", "Fornecedor", "Assistente", "Outros"].index(
                        transacao['categoria'] if transacao['categoria'] in ["Serviço", "Produto", "Fornecedor", "Assistente", "Outros"] else "Outros"
                    )
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

        # Resumo financeiro
        receitas = financeiro[financeiro['tipo'].isin(['receita', 'receita_a_receber'])]['valor'].sum() if not financeiro.empty else 0
        despesas = financeiro[financeiro['tipo'] == 'despesa']['valor'].sum() if not financeiro.empty else 0
        saldo = receitas - despesas

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Receitas", f"R$ {receitas:.2f}")
        col2.metric("Total Despesas", f"R$ {despesas:.2f}")
        col3.metric("Saldo", f"R$ {saldo:.2f}")
        if financeiro.empty:
            st.info("Nenhuma transação encontrada.")


    with tab3:
        st.subheader("Contas a Receber")

        contas_receber = st.session_state.db.get_contas_receber()

        if not contas_receber.empty:
            # Adicionar coluna de ações
            for idx, conta in contas_receber.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{conta['descricao']}**")
                    st.write(f"Valor: R$ {conta['valor']:.2f}")
                    st.write(f"Origem: {conta['origem_tipo']}")
                    st.write(f"Status: {conta['status']}")

                with col2:
                    if conta['status'] == 'Pendente':
                        if st.button("✅ Receber", key=f"receber_{conta['id']}"):
                            st.session_state.db.atualizar_status_transacao(
                                conta['id'],
                                'Recebido',
                                datetime.now().date()
                            )
                            st.rerun()

                with col3:
                    if conta['status'] == 'Pendente':
                        if st.button("❌ Cancelar", key=f"cancelar_{conta['id']}"):
                            st.session_state.db.atualizar_status_transacao(
                                conta['id'],
                                'Cancelado'
                            )
                            st.rerun()

                st.divider()

            # Resumo de contas a receber
            total_pendente = contas_receber[contas_receber['status'] == 'Pendente']['valor'].sum()
            total_recebido = contas_receber[contas_receber['status'] == 'Recebido']['valor'].sum()

            col1, col2 = st.columns(2)
            col1.metric("Total Pendente", f"R$ {total_pendente:.2f}")
            col2.metric("Total Recebido", f"R$ {total_recebido:.2f}")
        else:
            st.info("Nenhuma conta a receber cadastrada.")

    with tab4:
        st.subheader("Contas a Pagar")
        
        # Função para obter contas a pagar (despesas pendentes)
        contas_pagar = st.session_state.db.get_financeiro()
        if not contas_pagar.empty:
            # Filtrar por classificação contas_a_pagar ou tipo despesa com status pendente
            contas_pagar = contas_pagar[(
                (contas_pagar['classificacao'] == 'contas_a_pagar') | 
                ((contas_pagar['tipo'] == 'despesa') & (contas_pagar['status'] == 'Pendente'))
            )]
            
            if not contas_pagar.empty:
                # Adicionar filtro específico para assistentes
                filtro_tipo = st.radio(
                    "Filtrar por tipo:",
                    ["Todos", "Assistentes", "Outros"],
                    horizontal=True
                )
                
                # Aplicar filtro
                if filtro_tipo == "Assistentes":
                    contas_pagar = contas_pagar[(contas_pagar['categoria'] == 'Assistente') | 
                                               (contas_pagar['subcategoria'] == 'Assistentes') |
                                               (contas_pagar['descricao'].str.contains('Assistente:', na=False))]
                elif filtro_tipo == "Outros":
                    contas_pagar = contas_pagar[(contas_pagar['categoria'] != 'Assistente') & 
                                               (contas_pagar['subcategoria'] != 'Assistentes') &
                                               (~contas_pagar['descricao'].str.contains('Assistente:', na=False))]
                
                # Exibir contas a pagar
                if not contas_pagar.empty:
                    for idx, conta in contas_pagar.iterrows():
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.write(f"**{conta['descricao']}**")
                                st.write(f"Valor: R$ {conta['valor']:.2f}")
                                st.write(f"Categoria: {conta['categoria']}")
                                if 'subcategoria' in conta and pd.notna(conta['subcategoria']):
                                    st.write(f"Subcategoria: {conta['subcategoria']}")
                                if 'proposta_id' in conta and pd.notna(conta['proposta_id']):
                                    st.write(f"Proposta: #{conta['proposta_id']}")
                                st.write(f"Data: {pd.to_datetime(conta['data']).strftime('%d/%m/%Y')}")
                            
                            with col2:
                                if st.button("✅ Pagar", key=f"pagar_{conta['id']}"):
                                    st.session_state.db.atualizar_status_transacao(
                                        conta['id'],
                                        'Pago',
                                        datetime.now().date()
                                    )
                                    st.success(f"Pagamento de {conta['descricao']} registrado!")
                                    st.rerun()
                            
                            with col3:
                                if st.button("❌ Cancelar", key=f"cancelar_pagar_{conta['id']}"):
                                    st.session_state.db.atualizar_status_transacao(
                                        conta['id'],
                                        'Cancelado'
                                    )
                                    st.success(f"Pagamento de {conta['descricao']} cancelado!")
                                    st.rerun()
                            
                            st.divider()
                    
                    # Resumo de contas a pagar
                    total_pendente = contas_pagar['valor'].sum()
                    
                    # Considerar todas as formas de identificar assistentes
                    assistentes_mask = (
                        (contas_pagar['categoria'] == 'Assistente') | 
                        (contas_pagar['subcategoria'] == 'Assistentes') |
                        (contas_pagar['descricao'].str.contains('Assistente:', na=False))
                    )
                    
                    total_assistentes = contas_pagar[assistentes_mask]['valor'].sum()
                    total_outros = total_pendente - total_assistentes
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Pendente", f"R$ {total_pendente:.2f}")
                    col2.metric("Pagamentos a Assistentes", f"R$ {total_assistentes:.2f}")
                    col3.metric("Outros Pagamentos", f"R$ {total_outros:.2f}")
                else:
                    st.info(f"Nenhuma conta a pagar encontrada do tipo {filtro_tipo.lower()}.")
            else:
                st.info("Nenhuma conta a pagar pendente.")
                
                # Adicionar botão para ver histórico de pagamentos
                if st.button("Ver Histórico de Pagamentos"):
                    st.session_state.mostrar_historico_pagamentos = True
                
                # Exibir histórico se solicitado
                if 'mostrar_historico_pagamentos' in st.session_state and st.session_state.mostrar_historico_pagamentos:
                    historico = st.session_state.db.get_financeiro()
                    if not historico.empty:
                        historico = historico[(
                            (historico['tipo'] == 'despesa') | 
                            (historico['tipo'] == 'despesa_a_pagar') |
                            (historico['classificacao'] == 'contas_a_pagar')
                        ) & (historico['status'].isin(['Pago', 'Cancelado']))]
                        
                        if not historico.empty:
                            st.subheader("Histórico de Pagamentos")
                            # Converter coluna data para exibição
                            historico['data_formatada'] = pd.to_datetime(historico['data']).dt.strftime('%d/%m/%Y')
                            
                            # Criar tabela para visualização
                            st.dataframe(
                                historico[['data_formatada', 'descricao', 'valor', 'categoria', 'status']].rename(
                                    columns={'data_formatada': 'Data', 'descricao': 'Descrição', 
                                            'valor': 'Valor (R$)', 'categoria': 'Categoria', 'status': 'Status'}
                                ),
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("Nenhum registro de pagamento encontrado.")
        else:
            st.info("Nenhuma transação financeira encontrada.")
            
        # Adicionar assistentes diretamente
        with st.expander("💼 Cadastrar Pagamento para Assistente"):
            assistentes = st.session_state.db.get_assistentes()
            
            if not assistentes.empty:
                with st.form("cadastrar_pagamento_assistente"):
                    assistente_selecionado = st.selectbox(
                        "Selecione o Assistente",
                        assistentes['nome'].tolist()
                    )
                    
                    assistente_id = assistentes[assistentes['nome'] == assistente_selecionado]['id'].iloc[0]
                    
                    descricao = st.text_input(
                        "Descrição do Serviço", 
                        value=f"Pagamento para {assistente_selecionado}"
                    )
                    
                    valor = st.number_input("Valor a Pagar (R$)", min_value=0.0, step=10.0)
                    
                    proposta_id = st.number_input("ID da Proposta (opcional)", value=0, min_value=0, step=1)
                    
                    if st.form_submit_button("Cadastrar Pagamento"):
                        if valor > 0:
                            try:
                                st.session_state.db.add_transacao(
                                    tipo="despesa_a_pagar",
                                    descricao=descricao,
                                    valor=valor,
                                    categoria="Assistente",
                                    subcategoria="Pagamento de Serviço",
                                    origem_id=assistente_id,
                                    origem_tipo="assistente",
                                    proposta_id=proposta_id if proposta_id > 0 else None,
                                    classificacao="contas_a_pagar"
                                )
                                st.success(f"Pagamento para {assistente_selecionado} cadastrado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao cadastrar pagamento: {str(e)}")
                        else:
                            st.warning("Por favor, informe um valor válido para o pagamento.")
            else:
                st.warning("Nenhum assistente cadastrado. Adicione assistentes no menu Cadastros primeiro.")

    with tab5:
        st.subheader("Dashboard Financeiro")

        if not financeiro.empty:
            # Resumo de Contas a Receber
            contas_receber = st.session_state.db.get_contas_receber()
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

            # Gráfico de Receitas vs Despesas por Categoria
            fig1 = px.bar(
                financeiro,
                x='categoria',
                y='valor',
                color='tipo',
                title='Transações por Categoria',
                labels={'valor': 'Valor (R$)', 'categoria': 'Categoria'}
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Evolução Temporal
            financeiro['data'] = pd.to_datetime(financeiro['data'])
            dados_temporais = financeiro.groupby(
                [pd.Grouper(key='data', freq='ME'), 'tipo']
            )['valor'].sum().reset_index()

            fig2 = px.line(
                dados_temporais,
                x='data',
                y='valor',
                color='tipo',
                title='Evolução Temporal',
                labels={'valor': 'Valor (R$)', 'data': 'Data'}
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Distribuição por Tipo de Receita
            receitas = financeiro[financeiro['tipo'].isin(['receita', 'receita_a_receber'])]
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