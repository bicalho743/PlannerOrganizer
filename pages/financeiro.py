import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import time
from datetime import datetime, timedelta
from utils.currency_formatter import format_currency_br
from utils.fluxo_caixa_module import CashFlowModule, MonthCashFlow, REVENUE_CATEGORIES, EXPENSE_CATEGORIES

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

        # Primeiro, fora do form, para que a mudança seja imediata
        tipo = st.selectbox(
            "Tipo",
            ["receita", "despesa"],
            key="tipo_transacao"
        )

        with st.form("registro_transacao", clear_on_submit=True):
            # Replicar o valor do selectbox dentro do form
            tipo_form = st.selectbox(
                "Tipo (confirmação)",
                ["receita", "despesa"],
                index=0 if tipo == "receita" else 1,
                disabled=True,
                key="tipo_form"
            )

            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            # Campos condicionais baseados no tipo selecionado
            if tipo == "receita":
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
            else:
                # Para despesas, definir valores None
                tipo_receita = None
                origem_tipo = None
                origem_id = None
                
                categoria = st.selectbox(
                    "Categoria",
                    categorias_despesa
                )

            submitted = st.form_submit_button("Registrar")

            if submitted:
                if descricao and valor > 0:
                    try:
                        st.session_state.db.add_transacao(
                            tipo=tipo,  # Usar o tipo selecionado fora do form
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
                    financeiro = financeiro[~financeiro['id'].isin(duplicados_assistentes)]

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
                    if st.button("✏️ Editar Selecionado"):
                        st.session_state.transacao_em_edicao = financeiro.iloc[selected_idx]
                        st.rerun()
                with col3:
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

                # Botão para exportar para CSV
                if st.button("📊 Exportar para CSV"):
                    csv = df_display.to_csv(index=False)
                    # Criar um botão de download
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="historico_financeiro.csv">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)

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

        # Inicializar o módulo de fluxo de caixa no session_state
        if 'fluxo_caixa_module' not in st.session_state:
            st.session_state.fluxo_caixa_module = CashFlowModule(
                saldo_inicial=0.0, 
                db_connection=st.session_state.db
            )
        
        # Inicializar categorias personalizadas
        if 'categorias_receitas_personalizadas' not in st.session_state:
            st.session_state.categorias_receitas_personalizadas = REVENUE_CATEGORIES.copy()
        if 'categorias_despesas_personalizadas' not in st.session_state:
            st.session_state.categorias_despesas_personalizadas = EXPENSE_CATEGORIES.copy()

        # Barra lateral para configurações
        with st.expander("⚙️ Configurações", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.saldo_inicial = st.number_input(
                    "Saldo Inicial (R$)", 
                    value=st.session_state.fluxo_caixa_module.saldo_inicial,
                    step=100.0
                )
            with col2:
                if st.button("Atualizar Saldo Inicial", use_container_width=True):
                    st.session_state.fluxo_caixa_module.saldo_inicial = st.session_state.saldo_inicial
                    st.session_state.fluxo_caixa_module.recalcular_saldos()
                    st.success("Saldo inicial atualizado!")
                    
        # Seção de sincronização com banco de dados
        with st.expander("🔄 Sincronizar com Banco de Dados", expanded=False):
            st.markdown("""
            **Integração Automática**: Esta seção permite sincronizar o fluxo de caixa com as transações 
            registradas na aba "Registrar Transação". As transações pagas/recebidas serão automaticamente 
            importadas para os valores realizados.
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Sincronizar Todos os Meses", use_container_width=True):
                    if st.session_state.fluxo_caixa_module.months:
                        sucesso_total = 0
                        for mes in st.session_state.fluxo_caixa_module.months:
                            if st.session_state.fluxo_caixa_module.sincronizar_mes_com_banco(mes.name):
                                sucesso_total += 1
                        
                        st.success(f"✅ {sucesso_total} meses sincronizados com sucesso!")
                        st.rerun()
                    else:
                        st.warning("Nenhum mês cadastrado para sincronizar.")
            
            with col2:
                if st.session_state.fluxo_caixa_module.months:
                    mes_para_sync = st.selectbox(
                        "Sincronizar mês específico:",
                        [m.name for m in st.session_state.fluxo_caixa_module.months],
                        key="sync_mes_especifico"
                    )
                    
                    if st.button("🔄 Sincronizar Mês Selecionado", use_container_width=True):
                        if st.session_state.fluxo_caixa_module.sincronizar_mes_com_banco(mes_para_sync):
                            st.success(f"✅ Mês {mes_para_sync} sincronizado!")
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao sincronizar {mes_para_sync}")
            
            # Informações sobre o mapeamento de categorias
            st.markdown("#### 📋 Mapeamento de Categorias")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Receitas do Banco → Fluxo de Caixa:**")
                st.markdown("• Serviços de Organização → Contas a receber-vendas realizadas")
                st.markdown("• Venda de Produtos → Contas a receber-vendas realizadas")
                st.markdown("• Vendas → Contas a receber-vendas realizadas")
                st.markdown("• Comissão sobre Fornecedores → Outros recebimentos")
                st.markdown("• Serviços Adicionais → Outros recebimentos")
            
            with col2:
                st.markdown("**Despesas do Banco → Fluxo de Caixa:**")
                st.markdown("• Pagamento Equipe/Assistentes → Pró Labore")
                st.markdown("• Pagamento Parceiros/Fornecedores → Fornecedores")
                st.markdown("• Custos Operacionais → Fornecedores")
                st.markdown("• Custos Administrativos → MEI")
                st.markdown("• Assistente → Pró Labore")

        # Seção para personalizar categorias
        with st.expander("🏷️ Personalizar Categorias", expanded=False):
            tab_receitas, tab_despesas = st.tabs(["💰 Receitas", "💸 Despesas"])
            
            with tab_receitas:
                st.markdown("**Categorias de Receitas:**")
                
                # Mostrar categorias atuais
                for i, categoria in enumerate(st.session_state.categorias_receitas_personalizadas):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {categoria}")
                    with col2:
                        if st.button("🗑️", key=f"del_receita_{i}", help="Excluir categoria"):
                            st.session_state.categorias_receitas_personalizadas.remove(categoria)
                            st.rerun()
                
                # Adicionar nova categoria
                st.markdown("**Adicionar Nova Categoria:**")
                nova_receita = st.text_input("Nome da nova categoria de receita", key="nova_categoria_receita")
                if st.button("➕ Adicionar Receita", use_container_width=True):
                    if nova_receita and nova_receita not in st.session_state.categorias_receitas_personalizadas:
                        st.session_state.categorias_receitas_personalizadas.append(nova_receita)
                        st.success(f"Categoria '{nova_receita}' adicionada!")
                        st.rerun()
                    elif nova_receita in st.session_state.categorias_receitas_personalizadas:
                        st.warning("Esta categoria já existe!")
            
            with tab_despesas:
                st.markdown("**Categorias de Despesas:**")
                
                # Mostrar categorias atuais
                for i, categoria in enumerate(st.session_state.categorias_despesas_personalizadas):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {categoria}")
                    with col2:
                        if st.button("🗑️", key=f"del_despesa_{i}", help="Excluir categoria"):
                            st.session_state.categorias_despesas_personalizadas.remove(categoria)
                            st.rerun()
                
                # Adicionar nova categoria
                st.markdown("**Adicionar Nova Categoria:**")
                nova_despesa = st.text_input("Nome da nova categoria de despesa", key="nova_categoria_despesa")
                if st.button("➕ Adicionar Despesa", use_container_width=True):
                    if nova_despesa and nova_despesa not in st.session_state.categorias_despesas_personalizadas:
                        st.session_state.categorias_despesas_personalizadas.append(nova_despesa)
                        st.success(f"Categoria '{nova_despesa}' adicionada!")
                        st.rerun()
                    elif nova_despesa in st.session_state.categorias_despesas_personalizadas:
                        st.warning("Esta categoria já existe!")
                
                # Botão para resetar para padrão
                st.markdown("---")
                if st.button("🔄 Restaurar Categorias Padrão", use_container_width=True):
                    st.session_state.categorias_receitas_personalizadas = REVENUE_CATEGORIES.copy()
                    st.session_state.categorias_despesas_personalizadas = EXPENSE_CATEGORIES.copy()
                    st.success("Categorias restauradas para o padrão!")
                    st.rerun()

        # Seção para adicionar/editar meses
        st.markdown("### 📅 Gestão de Meses")

        # Lista de meses padrão
        meses_padrao = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]

        # Adicionar novo mês
        with st.expander("➕ Adicionar Novo Mês", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                nome_mes = st.selectbox("Selecione o Mês", meses_padrao)
            with col2:
                ano_mes = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year, step=1)

            if st.button("Adicionar Mês", use_container_width=True):
                # Criar nome completo com mês e ano
                nome_completo = f"{nome_mes} {ano_mes}"
                
                # Verificar se o mês já existe
                nomes_existentes = [m.name for m in st.session_state.fluxo_caixa_module.months]
                if nome_completo not in nomes_existentes:
                    novo_mes = MonthCashFlow(name=nome_completo)
                    st.session_state.fluxo_caixa_module.adicionar_mes(novo_mes)
                    st.success(f"Mês {nome_completo} adicionado com sucesso!")
                else:
                    st.warning(f"O mês {nome_completo} já existe!")

        # Exibir meses existentes
        if st.session_state.fluxo_caixa_module.months:
            st.markdown("### 📊 Meses Cadastrados")

            # Seletor de mês para edição
            nomes_meses = [m.name for m in st.session_state.fluxo_caixa_module.months]
            mes_selecionado = st.selectbox("Selecione um mês para editar", nomes_meses)

            # Encontrar o mês selecionado
            mes_obj = None
            for m in st.session_state.fluxo_caixa_module.months:
                if m.name == mes_selecionado:
                    mes_obj = m
                    break

            if mes_obj:
                col1, col2 = st.columns(2)

                # Seção de Receitas
                with col1:
                    st.markdown("#### 💰 Receitas")
                    
                    # Subseção Previstas
                    with st.expander("📅 Receitas Previstas", expanded=True):
                        for categoria in st.session_state.categorias_receitas_personalizadas:
                            valor_atual = mes_obj.previsao_receitas.get(categoria, 0.0)
                            novo_valor = st.number_input(
                                categoria, 
                                value=valor_atual, 
                                step=100.0,
                                key=f"receita_prev_{mes_selecionado}_{categoria}"
                            )

                            if novo_valor != valor_atual:
                                mes_obj.editar_receita(categoria, novo_valor, previsao=True)
                    
                    # Subseção Realizadas (importadas do banco)
                    if mes_obj.realizado_receitas:
                        with st.expander("✅ Receitas Realizadas (Banco)", expanded=False):
                            for categoria, valor in mes_obj.realizado_receitas.items():
                                st.metric(categoria, f"R$ {valor:,.2f}")
                    else:
                        st.info("💡 Use 'Sincronizar com Banco' para importar receitas realizadas")

                # Seção de Despesas
                with col2:
                    st.markdown("#### 💸 Despesas")
                    
                    # Subseção Previstas
                    with st.expander("📅 Despesas Previstas", expanded=True):
                        for categoria in st.session_state.categorias_despesas_personalizadas:
                            valor_atual = mes_obj.previsao_despesas.get(categoria, 0.0)
                            novo_valor = st.number_input(
                                categoria, 
                                value=valor_atual, 
                                step=50.0,
                                key=f"despesa_prev_{mes_selecionado}_{categoria}"
                            )

                            if novo_valor != valor_atual:
                                mes_obj.editar_despesa(categoria, novo_valor, previsao=True)
                    
                    # Subseção Realizadas (importadas do banco)
                    if mes_obj.realizado_despesas:
                        with st.expander("✅ Despesas Realizadas (Banco)", expanded=False):
                            for categoria, valor in mes_obj.realizado_despesas.items():
                                st.metric(categoria, f"R$ {valor:,.2f}")
                    else:
                        st.info("💡 Use 'Sincronizar com Banco' para importar despesas realizadas")

                # Botão para recalcular
                if st.button("🔄 Recalcular Saldos", use_container_width=True):
                    st.session_state.fluxo_caixa_module.recalcular_saldos()
                    st.success("Saldos recalculados!")

                # Resumo do mês selecionado
                st.markdown("#### 📈 Resumo do Mês")
                
                # Resumo Previsto
                st.markdown("**📅 Valores Previstos:**")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Receitas Previstas", format_currency_br(mes_obj.total_receitas_previsao))
                with col2:
                    st.metric("Despesas Previstas", format_currency_br(mes_obj.total_despesas_previsao))
                with col3:
                    st.metric("Saldo Mensal Previsto", format_currency_br(mes_obj.saldo_mensal_previsao))
                with col4:
                    st.metric("Saldo Final Previsto", format_currency_br(mes_obj.saldo_final_previsao))
                
                # Resumo Realizado (se disponível)
                if mes_obj.total_receitas_realizado is not None or mes_obj.total_despesas_realizado is not None:
                    st.markdown("**✅ Valores Realizados (Banco):**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        receitas_real = mes_obj.total_receitas_realizado or 0.0
                        st.metric("Receitas Realizadas", format_currency_br(receitas_real))
                    with col2:
                        despesas_real = mes_obj.total_despesas_realizado or 0.0
                        st.metric("Despesas Realizadas", format_currency_br(despesas_real))
                    with col3:
                        saldo_real = mes_obj.saldo_mensal_realizado or 0.0
                        st.metric("Saldo Mensal Real", format_currency_br(saldo_real))
                    with col4:
                        saldo_final_real = mes_obj.saldo_final_realizado or 0.0
                        st.metric("Saldo Final Real", format_currency_br(saldo_final_real))

        # Visualização consolidada
        if st.session_state.fluxo_caixa_module.months:
            st.markdown("### 📊 Visão Consolidada")

            # Obter resumo de todos os meses
            resumo = st.session_state.fluxo_caixa_module.obter_resumo()

            # Criar DataFrame para visualização
            dados_resumo = []
            for nome_mes, dados in resumo.items():
                dados_resumo.append({
                    'Mês': nome_mes,
                    'Receitas Previstas': dados['total_receitas_previsao'],
                    'Despesas Previstas': dados['total_despesas_previsao'],
                    'Saldo Mensal': dados['saldo_mensal_previsao'],
                    'Saldo Acumulado': dados['saldo_acumulado_previsao'],
                    'Saldo Final': dados['saldo_final_previsao']
                })

            df_resumo = pd.DataFrame(dados_resumo)

            # Tabela resumo
            st.markdown("#### 📋 Tabela Resumo")

            # Formatar valores para exibição
            df_display = df_resumo.copy()
            for col in ['Receitas Previstas', 'Despesas Previstas', 'Saldo Mensal', 'Saldo Acumulado', 'Saldo Final']:
                df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Gráfico de evolução do saldo
            st.markdown("#### 📈 Evolução do Saldo Final")
            fig_saldo = px.line(
                df_resumo, 
                x='Mês', 
                y='Saldo Final',
                title='Evolução do Saldo Final por Mês',
                labels={'Saldo Final': 'Saldo Final (R$)', 'Mês': 'Mês'},
                markers=True
            )
            fig_saldo.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_saldo, use_container_width=True)

            # Gráfico de receitas vs despesas
            st.markdown("#### 💰 Receitas vs Despesas")
            fig_comp = px.bar(
                df_resumo, 
                x='Mês', 
                y=['Receitas Previstas', 'Despesas Previstas'],
                title='Comparativo de Receitas e Despesas por Mês',
                labels={'value': 'Valor (R$)', 'Mês': 'Mês', 'variable': 'Tipo'},
                barmode='group'
            )
            fig_comp.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_comp, use_container_width=True)

            # Botões de ação
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Limpar Todos os Dados", use_container_width=True):
                    st.session_state.fluxo_caixa_module = CashFlowModule(
                        saldo_inicial=0.0, 
                        db_connection=st.session_state.db
                    )
                    st.success("Todos os dados foram limpos!")
            
            with col2:
                if st.button("📊 Exportar Fluxo de Caixa (CSV)", use_container_width=True):
                    # Criar DataFrame para exportação
                    resumo = st.session_state.fluxo_caixa_module.obter_resumo()
                    
                    dados_export = []
                    for nome_mes, dados in resumo.items():
                        dados_export.append({
                            'Mês': nome_mes,
                            'Receitas Previstas': dados['total_receitas_previsao'],
                            'Despesas Previstas': dados['total_despesas_previsao'],
                            'Saldo Mensal Previsto': dados['saldo_mensal_previsao'],
                            'Saldo Final Previsto': dados['saldo_final_previsao']
                        })
                    
                    if dados_export:
                        df_export = pd.DataFrame(dados_export)
                        csv = df_export.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Baixar CSV",
                            data=csv,
                            file_name=f"fluxo_caixa_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("Nenhum dado para exportar.")

        else:
            st.info("Nenhum mês cadastrado. Use a seção 'Adicionar Novo Mês' para começar.")

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