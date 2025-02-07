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

            prazo_entrega = None
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
                            'prazo_entrega': prazo_entrega
                        }

                        proposta_id = st.session_state.db.add_proposta(**dados_proposta)
                        st.success(f"Proposta cadastrada com sucesso! Número: {proposta_id}")
                        st.rerun()
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

            if not propostas.empty:
                # Converter data_proposta para datetime
                propostas['data_proposta'] = pd.to_datetime(propostas['data_proposta'])

                # Aplicar filtros
                if status_filtro:
                    propostas = propostas[propostas['status'].isin(status_filtro)]

                # Ordenar por data mais recente
                propostas = propostas.sort_values('data_proposta', ascending=False)

                # Exibir tabela de propostas
                st.dataframe(
                    propostas[[
                        'numero', 'descricao', 'valor', 'status',
                        'tipo_proposta', 'data_inicio', 'data_fim', 'data_proposta'
                    ]],
                    use_container_width=True
                )
            else:
                st.info("Nenhuma proposta encontrada.")

        except Exception as e:
            st.error(f"Erro ao carregar propostas: {str(e)}")

    with tab3:
        st.subheader("Andamento do Trabalho")

        try:
            # Selecionar proposta
            propostas = st.session_state.db.get_propostas()
            if not propostas.empty:
                proposta_numero = st.selectbox(
                    "Número da Proposta",
                    propostas['numero'].tolist()
                )

                # Obter dados da proposta selecionada
                proposta = propostas[propostas['numero'] == proposta_numero].iloc[0]
                proposta_id = int(proposta['id'])

                # Informações principais
                st.write(f"**Descrição:** {proposta['descricao']}")
                st.write(f"**Valor Total:** R$ {proposta['valor']:.2f}")
                st.write(f"**Status:** {proposta['status']}")

                # Produtos e fornecedores
                st.write("---")
                st.subheader("Produtos")

                with st.form("cadastro_produto"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome_produto = st.text_input("Nome do Produto")
                        comodo = st.text_input("Cômodo")
                        quantidade = st.number_input("Quantidade", min_value=1, step=1)
                    with col2:
                        descricao_produto = st.text_area("Descrição")

                    if st.form_submit_button("Adicionar Produto"):
                        if nome_produto and comodo:
                            try:
                                produto_id = st.session_state.db.add_produto_organizador(
                                    proposta_id=proposta_id,
                                    nome=nome_produto,
                                    descricao=descricao_produto,
                                    valor=0,
                                    quantidade=quantidade,
                                    comodo=comodo
                                )
                                st.success("Produto cadastrado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao cadastrar produto: {str(e)}")
                        else:
                            st.warning("Por favor, preencha todos os campos obrigatórios.")

                # Lista de produtos
                produtos = st.session_state.db.get_produtos_organizadores(proposta_id)
                if not produtos.empty:
                    for _, produto in produtos.iterrows():
                        with st.expander(f"{produto['nome']} - {produto['comodo']}"):
                            st.write(f"**Descrição:** {produto['descricao']}")
                            st.write(f"**Quantidade:** {produto['quantidade']}")
                            if produto['valor'] > 0:
                                st.write(f"**Valor:** R$ {produto['valor']:.2f}")

                            # Adicionar fornecedor
                            with st.form(f"fornecedor_{produto['id']}"):
                                fornecedores = st.session_state.db.get_fornecedores()
                                if not fornecedores.empty:
                                    fornecedor = st.selectbox(
                                        "Fornecedor",
                                        fornecedores['nome'].tolist(),
                                        key=f"fornecedor_{produto['id']}"
                                    )
                                    valor = st.number_input(
                                        "Valor (R$)",
                                        min_value=0.0,
                                        step=0.01,
                                        key=f"valor_{produto['id']}"
                                    )
                                    observacoes = st.text_input(
                                        "Observações",
                                        key=f"obs_{produto['id']}"
                                    )

                                    if st.form_submit_button("Adicionar Fornecedor"):
                                        if valor > 0:
                                            try:
                                                fornecedor_id = fornecedores[
                                                    fornecedores['nome'] == fornecedor
                                                ]['id'].iloc[0]

                                                st.session_state.db.add_produto_fornecedor(
                                                    produto_id=produto['id'],
                                                    fornecedor_id=fornecedor_id,
                                                    valor=valor,
                                                    observacoes=observacoes
                                                )
                                                st.success("Fornecedor adicionado com sucesso!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao adicionar fornecedor: {str(e)}")
                                        else:
                                            st.warning("Por favor, informe um valor válido.")
                                else:
                                    st.warning("Nenhum fornecedor cadastrado.")

                            # Mostrar fornecedores existentes
                            cotacoes = st.session_state.db.get_produto_fornecedores(produto['id'])
                            if not cotacoes.empty:
                                st.write("**Fornecedores cadastrados:**")
                                for _, cotacao in cotacoes.iterrows():
                                    st.write(
                                        f"• {cotacao['fornecedor_nome']}: "
                                        f"R$ {cotacao['valor']:.2f} "
                                        f"({cotacao['data_cotacao'].strftime('%d/%m/%Y')})"
                                    )
                else:
                    st.info("Nenhum produto cadastrado para esta proposta.")
            else:
                st.warning("Nenhuma proposta cadastrada.")

        except Exception as e:
            st.error(f"Erro ao carregar dados do andamento: {str(e)}")