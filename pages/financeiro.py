import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import time
from datetime import datetime, timedelta
from utils.currency_formatter import format_currency_br
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
            data_filtro = st.date_input("Data")

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

        contas_receber = st.session_state.db.get_contas_receber()

        # Filtrar apenas as contas com status pendente
        if not contas_receber.empty:
            contas_receber = contas_receber[contas_receber['status'] == 'Pendente']

        # Exibir título da seção
        st.write("Lista de Contas a Receber Pendentes:")

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

        # Inicializar flag para recarga forçada
        if 'reload_contas_pagar' not in st.session_state:
            st.session_state.reload_contas_pagar = False

        # Exibir título da seção
        st.write("Lista de Contas a Pagar Pendentes:")

        # Definir se precisamos forçar o recarregamento
        force_reload = True

        # Se o flag de recarregamento estiver ativo, garantir que estamos recarregando
        if st.session_state.reload_contas_pagar:
            force_reload = True
            # Resetar o flag para o próximo carregamento
            st.session_state.reload_contas_pagar = False

        # Carregar as contas a pagar (despesas pendentes)
        # Forçar recarregamento para evitar dados desatualizados
        contas_pagar = st.session_state.db.get_financeiro(force_reload=force_reload)
        if not contas_pagar.empty:
            # Filtrar por classificação contas_a_pagar OU tipo despesa, sempre com status pendente
            contas_pagar = contas_pagar[
                (
                    (contas_pagar['classificacao'] == 'contas_a_pagar') | 
                    (contas_pagar['tipo'] == 'despesa') |
                    (contas_pagar['tipo'] == 'despesa_a_pagar')
                ) & 
                (contas_pagar['status'] == 'Pendente')  # Garantir que status seja Pendente para todos os tipos
            ]

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
                                               (contas_pagar['categoria'] == 'Pagamento Equipe/Assistentes') |
                                               (contas_pagar['categoria'] == 'Pagamento de Assistente') |
                                               (contas_pagar['subcategoria'] == 'Assistentes') |
                                               (contas_pagar['descricao'].str.contains('Assistente:', na=False))]
                elif filtro_tipo == "Outros":
                    contas_pagar = contas_pagar[
                        (contas_pagar['categoria'] != 'Assistente') & 
                        (contas_pagar['categoria'] != 'Pagamento Equipe/Assistentes') &
                        (contas_pagar['categoria'] != 'Pagamento de Assistente') &
                        (contas_pagar['subcategoria'] != 'Assistentes') &
                        (~contas_pagar['descricao'].str.contains('Assistente:', na=False))
                    ]

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
                                # Chave única para cada botão de pagamento
                                pagar_key = f"pagar_{conta['id']}"

                                # Usar variáveis de sessão simples para gerenciar estado
                                if pagar_key not in st.session_state:
                                    st.session_state[pagar_key] = False

                                # Botão de pagamento
                                if st.button("✅ Pagar", key=f"btn_{pagar_key}"):
                                    # Alternar estado de confirmação
                                    st.session_state[pagar_key] = True
                                    st.rerun()

                                # Se o botão foi clicado, mostrar confirmação
                                if st.session_state.get(pagar_key, False):
                                    st.info(f"Confirmando pagamento de R$ {conta['valor']:.2f}")

                                    col_conf1, col_conf2 = st.columns(2)
                                    with col_conf1:
                                        if st.button("✓ Confirmar", key=f"confirm_{pagar_key}"):
                                            try:
                                                # Usar o método da classe Database para atualizar transação mais seguramente
                                                data_pagamento = datetime.now().date()

                                                # Atualizar status da transação usando método adequado do DB
                                                result = st.session_state.db.atualizar_status_transacao(
                                                    transacao_id=conta['id'],
                                                    status='Pago',
                                                    data_recebimento=data_pagamento
                                                )

                                                if result:
                                                    st.success(f"✅ Pagamento de {conta['descricao']} registrado com sucesso!")

                                                    # Forçar recarregamento dos dados na próxima exibição
                                                    st.session_state.reload_contas_pagar = True

                                                    # Limpar estado via session state
                                                    st.session_state[pagar_key] = False

                                                    # Aguardar um pouco para exibir a mensagem de sucesso
                                                    time.sleep(1)

                                                    # Recarregar a página para mostrar dados atualizados
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao registrar pagamento. A transação não foi encontrada.")
                                            except Exception as e:
                                                st.error(f"Erro ao registrar pagamento: {str(e)}")

                                    with col_conf2:
                                        if st.button("✗ Cancelar", key=f"cancel_{pagar_key}"):
                                            # Limpar estado via session state
                                            st.session_state[pagar_key] = False
                                            st.rerun()

                            with col3:
                                # Chave única para cada botão de cancelamento
                                cancelar_key = f"cancelar_pagar_{conta['id']}"

                                # Usar variáveis de sessão simples para gerenciar estado
                                if cancelar_key not in st.session_state:
                                    st.session_state[cancelar_key] = False

                                # Botão de cancelamento
                                if st.button("❌ Cancelar", key=f"btn_{cancelar_key}"):
                                    # Alternar estado de confirmação
                                    st.session_state[cancelar_key] = True
                                    st.rerun()

                                # Se o botão foi clicado, mostrar confirmação
                                if st.session_state.get(cancelar_key, False):
                                    st.warning(f"Confirmar cancelamento da conta: {conta['descricao']}")

                                    col_canc1, col_canc2 = st.columns(2)
                                    with col_canc1:
                                        if st.button("✓ Confirmar", key=f"confirm_{cancelar_key}"):
                                            try:
                                                # Usar o método da classe Database para atualizar transação mais seguramente
                                                result = st.session_state.db.atualizar_status_transacao(
                                                    transacao_id=conta['id'],
                                                    status='Cancelado'
                                                )

                                                if result:
                                                    st.success(f"Pagamento de {conta['descricao']} cancelado com sucesso!")

                                                    # Forçar recarregamento dos dados na próxima exibição
                                                    st.session_state.reload_contas_pagar = True

                                                    # Limpar estado via session state
                                                    st.session_state[cancelar_key] = False

                                                    # Aguardar um pouco para exibir a mensagem de sucesso
                                                    time.sleep(1)

                                                    # Recarregar a página para mostrar dados atualizados
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao cancelar pagamento. A transação não foi encontrada.")
                                            except Exception as e:
                                                st.error(f"Erro ao cancelar pagamento: {str(e)}")

                                    with col_canc2:
                                        if st.button("✗ Voltar", key=f"voltar_{cancelar_key}"):
                                            # Limpar estado via session state
                                            st.session_state[cancelar_key] = False
                                            st.rerun()

                            st.divider()

                    # Resumo de contas a pagar
                    total_pendente = contas_pagar['valor'].sum()

                    # Considerar todas as formas de identificar assistentes
                    assistentes_mask = (
                        (contas_pagar['categoria'] == 'Assistente') | 
                        (contas_pagar['categoria'] == 'Pagamento Equipe/Assistentes') |
                        (contas_pagar['categoria'] == 'Pagamento de Assistente') |
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
                st.info("Nenhuma conta a pagar pendente. Para visualizar contas pagas ou canceladas, consulte a aba Histórico.")
        else:
            st.info("Nenhuma transação financeira encontrada.")

    with tab5:
        st.subheader("Histórico Financeiro")

        # Inicializar filtros em sessão para manter estado quando redirecionado
        if 'filtro_historico' not in st.session_state:
            st.session_state.filtro_historico = {
                "tipo": [],
                "status": ["Aprovado", "Recebido", "Pago", "Cancelado"]
            }

        # Recuperar dados para histórico, forçando recarregamento do banco
        historico = st.session_state.db.get_financeiro(force_reload=True)

        if not historico.empty:
            # Converter a coluna 'data' para datetime para manipulação
            historico['data'] = pd.to_datetime(historico['data'])

            # Filtrar apenas transações com status não-pendente
            historico = historico[~(historico['status'] == 'Pendente')]

            # Controles de filtro
            st.write("#### Filtros")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Filtro por tipo de transação
                tipos_disponiveis = ["receita", "despesa"]
                tipo_selecionado = st.multiselect(
                    "Tipo de Transação", 
                    tipos_disponiveis,
                    default=st.session_state.filtro_historico["tipo"] if st.session_state.filtro_historico["tipo"] else []
                )

            with col2:
                # Filtro por status
                status_disponiveis = ["Aprovado", "Recebido", "Pago", "Cancelado"]
                status_selecionado = st.multiselect(
                    "Status", 
                    status_disponiveis,
                    default=st.session_state.filtro_historico["status"]
                )

            with col3:
                # Filtro por período
                hoje = datetime.now().date()
                primeiro_dia_mes = hoje.replace(day=1)
                data_inicio = st.date_input(
                    "Data Inicial", 
                    value=primeiro_dia_mes,
                    key="historico_data_inicio"
                )
                data_fim = st.date_input(
                    "Data Final", 
                    value=hoje,
                    key="historico_data_fim"
                )

            # Aplicar filtros
            if tipo_selecionado:
                historico = historico[historico['tipo'].isin(tipo_selecionado)]

            if status_selecionado:
                historico = historico[historico['status'].isin(status_selecionado)]

            # Filtro de data
            historico = historico[
                (historico['data'].dt.date >= data_inicio) & 
                (historico['data'].dt.date <= data_fim)
            ]

            # Mostrar os resultados
            if not historico.empty:
                # Formatar para exibição
                df_display = historico.copy()
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

                # Mostrar os dados
                st.write(f"#### Resultados ({len(df_display)} transações)")
                st.dataframe(
                    df_display[['data', 'tipo', 'descricao', 'valor', 'categoria', 'status']],
                    use_container_width=True,
                    hide_index=True
                )

                # Botão para exportar para CSV (removido para evitar IDs duplicados)
                # if st.button("📊 Exportar para CSV"):
                #     csv = df_display.to_csv(index=False)
                #     # Criar um botão de download
                #     b64 = base64.b64encode(csv.encode()).decode()
                #     href = f'<a href="data:file/csv;base64,{b64}" download="historico_financeiro.csv">Download CSV</a>'
                #     st.markdown(href, unsafe_allow_html=True)

                # Mostrar resumos
                st.write("#### Resumo Financeiro")
                col1, col2, col3 = st.columns(3)

                # Valores por tipo
                receitas = historico[historico['tipo'] == 'receita']['valor'].sum()
                despesas = historico[historico['tipo'] == 'despesa']['valor'].sum()
                saldo = receitas - despesas

                col1.metric("Total Receitas", f"R$ {receitas:.2f}")
                col2.metric("Total Despesas", f"R$ {despesas:.2f}")
                col3.metric("Saldo Período", f"R$ {saldo:.2f}")

                # Gráfico de barras por categoria
                st.write("#### Distribuição por Categoria")
                fig = px.bar(
                    historico, 
                    x='categoria', 
                    y='valor', 
                    color='tipo',
                    title="Valores por Categoria",
                    labels={'valor': 'Valor (R$)', 'categoria': 'Categoria'}
                )
                st.plotly_chart(fig, use_container_width=True)
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
            col1.metric("💰 Total Receitas", f"R$ {resumo['total_receitas']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            col2.metric("💸 Total Despesas", f"R$ {resumo['total_despesas']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            saldo_cor = "normal"
            if resumo['saldo_mes'] > 0:
                saldo_cor = "inverse" 
            col3.metric("📈 Saldo do Mês", f"R$ {resumo['saldo_mes']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            # Status das transações
            st.markdown("#### 📊 Status das Transações")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("✅ Receitas Pagas", f"R$ {resumo['receitas_pagas']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            col2.metric("⏳ Receitas Pendentes", f"R$ {resumo['receitas_pendentes']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            col3.metric("✅ Despesas Pagas", f"R$ {resumo['despesas_pagas']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            col4.metric("⏳ Despesas Pendentes", f"R$ {resumo['despesas_pendentes']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        with tab_transacoes:
            # Lista de transações do mês
            transacoes = st.session_state.fluxo_caixa_simple.get_transacoes_mes(ano_selecionado, mes_selecionado)
            
            if not transacoes.empty:
                # Formatação para exibição
                df_display = transacoes.copy()
                df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
                df_display['valor_formatado'] = df_display['valor'].apply(
                    lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                )
                
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
                    df_categorias[col + '_formatado'] = df_categorias[col].apply(
                        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    )
                
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