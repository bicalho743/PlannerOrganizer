import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    st.title("📝 Gestão de Propostas")

    tab1, tab2, tab3 = st.tabs([
        "Nova Proposta",
        "Lista de Propostas",
        "Andamento do Trabalho"
    ])

    with tab1:
        st.subheader("Cadastrar Nova Proposta")

        with st.form("cadastro_proposta"):
            # Carregar lista de clientes para seleção
            clientes = st.session_state.db.get_clientes()

            if clientes.empty:
                st.warning("Não há clientes cadastrados. Por favor, cadastre um cliente primeiro.")
                cliente_nome = None
            else:
                cliente_opcoes = clientes['nome'].tolist()
                cliente_nome = st.selectbox("Cliente", cliente_opcoes)

            descricao = st.text_area("Descrição do Serviço")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            tipo_proposta = st.selectbox(
                "Tipo de Proposta",
                [
                    "Organização",
                    "Organização Mudança",
                    "Treinamento Funcionários",
                    "Consultoria Online",
                    "Consultoria Enxoval"
                ]
            )

            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data de Início")
            with col2:
                data_fim = st.date_input("Data de Fim")

            if tipo_proposta in ["Organização", "Organização Mudança"]:
                prazo_entrega = st.date_input("Prazo de Entrega")

            status = st.selectbox("Status", ["Aberta", "Recusada", "Fechada"])

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if not cliente_nome:
                    st.error("É necessário ter pelo menos um cliente cadastrado para criar uma proposta.")
                elif descricao and valor > 0:
                    try:
                        cliente_id = int(clientes[clientes['nome'] == cliente_nome]['id'].iloc[0])
                        dados_proposta = {
                            'cliente_id': cliente_id,
                            'descricao': descricao,
                            'valor': valor,
                            'status': status,
                            'tipo_proposta': tipo_proposta,
                            'data_inicio': data_inicio,
                            'data_fim': data_fim,
                            'prazo_entrega': prazo_entrega if tipo_proposta in ["Organização", "Organização Mudança"] else None
                        }

                        proposta_id = st.session_state.db.add_proposta(**dados_proposta)
                        st.success(f"Proposta cadastrada com sucesso! Número: {proposta_id}")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar proposta: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos corretamente.")

    with tab2:
        st.subheader("Propostas Cadastradas")

        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            status_filtro = st.multiselect(
                "Filtrar por Status",
                ["Aberta", "Recusada", "Fechada"]
            )
        with col2:
            data_filtro = st.date_input("Filtrar por Data")

        try:
            # Carregar e processar dados
            propostas = st.session_state.db.get_propostas()
            clientes = st.session_state.db.get_clientes()

            if not propostas.empty and not clientes.empty:
                # Merge para obter nome do cliente
                propostas = propostas.merge(
                    clientes[['id', 'nome']],
                    left_on='cliente_id',
                    right_on='id',
                    suffixes=('', '_cliente')
                )

                # Aplicar filtros
                if status_filtro:
                    propostas = propostas[propostas['status'].isin(status_filtro)]

                # Exibir tabela de propostas
                if not propostas.empty:
                    colunas_exibir = [
                        'numero', 'nome', 'descricao', 'valor', 'status',
                        'tipo_proposta', 'data_inicio', 'data_fim', 'data_proposta'
                    ]
                    # Garantir que todas as colunas existem
                    colunas_exibir = [col for col in colunas_exibir if col in propostas.columns]
                    st.dataframe(propostas[colunas_exibir], use_container_width=True)
                else:
                    st.info("Nenhuma proposta encontrada.")
            else:
                st.info("Nenhuma proposta encontrada.")

        except Exception as e:
            st.error(f"Erro ao carregar propostas: {str(e)}")

    with tab3:
        st.subheader("Andamento do Trabalho")

        try:
            # Selecionar proposta
            propostas = st.session_state.db.get_propostas()
            clientes = st.session_state.db.get_clientes()

            if not propostas.empty and not clientes.empty:
                # Merge com dados do cliente
                propostas = propostas.merge(
                    clientes[['id', 'nome']],
                    left_on='cliente_id',
                    right_on='id',
                    suffixes=('', '_cliente')
                )

                # Seleção da proposta
                proposta_numero = st.selectbox(
                    "Número da Proposta",
                    propostas['numero'].tolist()
                )

                # Obter dados da proposta selecionada
                proposta = propostas[propostas['numero'] == proposta_numero].iloc[0]
                proposta_id = int(proposta['id'])

                # Informações principais
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Cliente:** {proposta['nome']}")
                with col2:
                    st.write(f"**Valor Total:** R$ {proposta['valor']:.2f}")

                # Descrição e Vale Acrescendo
                st.write("---")
                col1, col2 = st.columns(2)
                with col1:
                    vale_acrescendo = st.number_input(
                        "Vale Acrescendo (R$)",
                        min_value=0.0,
                        step=0.01,
                        value=0.0
                    )
                with col2:
                    st.text_area(
                        "Descrição do Serviço",
                        value=proposta['descricao'],
                        disabled=True
                    )

                # Produtos
                st.write("---")
                st.subheader("Produtos")

                with st.form("cadastro_produto"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        nome_produto = st.text_input("Nome do Produto")
                        comodo = st.text_input("Cômodo")
                    with col2:
                        descricao_produto = st.text_area("Descrição")
                        quantidade = st.number_input("Quantidade", min_value=1, step=1)
                    with col3:
                        # Comparativo de preços entre lojas
                        st.write("Valores por Loja")
                        loja1_valor = st.number_input("Loja 1 (R$)", min_value=0.0, step=0.01)
                        loja2_valor = st.number_input("Loja 2 (R$)", min_value=0.0, step=0.01)
                        loja3_valor = st.number_input("Loja 3 (R$)", min_value=0.0, step=0.01)

                    # Determinar o menor valor
                    valores_lojas = [
                        (loja1_valor, "Loja 1"),
                        (loja2_valor, "Loja 2"),
                        (loja3_valor, "Loja 3")
                    ]
                    menor_valor = min((v for v, _ in valores_lojas if v > 0), default=0)
                    loja_escolhida = next((loja for valor, loja in valores_lojas if valor == menor_valor), None)

                    if st.form_submit_button("Adicionar Produto"):
                        if nome_produto and menor_valor > 0 and comodo:
                            try:
                                st.session_state.db.add_produto_organizador(
                                    proposta_id=proposta_id,
                                    nome=nome_produto,
                                    descricao=descricao_produto,
                                    valor=menor_valor,
                                    quantidade=quantidade,
                                    comodo=comodo,
                                    fornecedor_id=None  # Será atualizado posteriormente
                                )
                                st.success(f"Produto cadastrado com sucesso! Melhor valor: {loja_escolhida} - R$ {menor_valor:.2f}")
                            except Exception as e:
                                st.error(f"Erro ao cadastrar produto: {str(e)}")
                        else:
                            st.warning("Por favor, preencha todos os campos obrigatórios e informe pelo menos um valor de loja.")

                # Lista de Produtos
                st.write("---")
                st.subheader("Produtos Cadastrados")
                produtos = st.session_state.db.get_produtos_organizadores(proposta_id)
                if not produtos.empty:
                    for idx, produto in produtos.iterrows():
                        with st.expander(f"{produto['nome']} - {produto['comodo']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Descrição:** {produto['descricao']}")
                                st.write(f"**Quantidade:** {produto['quantidade']}")
                            with col2:
                                st.write(f"**Valor:** R$ {produto['valor']:.2f}")
                                st.write(f"**Total:** R$ {(produto['valor'] * produto['quantidade']):.2f}")
                else:
                    st.info("Nenhum produto cadastrado.")

            else:
                st.warning("Nenhuma proposta cadastrada ou nenhum cliente encontrado.")

        except Exception as e:
            st.error(f"Erro ao carregar dados do andamento: {str(e)}")