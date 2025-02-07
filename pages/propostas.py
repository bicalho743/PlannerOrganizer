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

            if tipo_proposta in ["Organização", "Organização Mudança"]:
                prazo_entrega = st.date_input("Prazo de Entrega")

            status = st.selectbox("Status", ["Aberta", "Fechada", "Cancelada"])

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if not cliente_nome:
                    st.error("É necessário ter pelo menos um cliente cadastrado para criar uma proposta.")
                elif descricao and valor > 0:
                    try:
                        # Converter cliente_id para int padrão do Python
                        cliente_id = int(clientes[clientes['nome'] == cliente_nome]['id'].iloc[0])
                        dados_proposta = {
                            'cliente_id': cliente_id,
                            'descricao': descricao,
                            'valor': valor,
                            'status': status,
                            'tipo_proposta': tipo_proposta
                        }

                        if tipo_proposta in ["Organização", "Organização Mudança"]:
                            dados_proposta['prazo_entrega'] = prazo_entrega if 'prazo_entrega' in locals() else None

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
                ["Aberta", "Fechada", "Cancelada"]
            )
        with col2:
            data_filtro = st.date_input("Filtrar por Data")

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
            st.dataframe(
                propostas[['numero', 'nome', 'descricao', 'valor', 'status', 'tipo_proposta', 'data_proposta']],
                use_container_width=True
            )
        else:
            st.info("Nenhuma proposta encontrada.")

    with tab3:
        st.subheader("Andamento do Trabalho")

        # Selecionar proposta
        propostas = st.session_state.db.get_propostas()
        if not propostas.empty:
            proposta_numero = st.selectbox(
                "Selecione o Número da Proposta",
                propostas['numero'].tolist()
            )
            proposta = propostas[propostas['numero'] == proposta_numero].iloc[0]

            # Tabs para organizar o andamento
            andamento_tab1, andamento_tab2 = st.tabs(["Registrar Andamento", "Produtos Organizadores"])

            with andamento_tab1:
                with st.form("registro_andamento"):
                    status = st.selectbox(
                        "Status do Andamento",
                        ["Em Análise", "Em Execução", "Parado", "Concluído"]
                    )
                    comodo = st.text_input("Cômodo (opcional)")
                    observacao = st.text_area("Observações")

                    if st.form_submit_button("Registrar Andamento"):
                        try:
                            st.session_state.db.add_andamento_proposta(
                                proposta_id=proposta['id'],
                                status=status,
                                observacao=observacao,
                                comodo=comodo
                            )
                            st.success("Andamento registrado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao registrar andamento: {str(e)}")

                # Exibir histórico de andamentos
                andamentos = st.session_state.db.get_andamentos_proposta(proposta['id'])
                if not andamentos.empty:
                    st.dataframe(andamentos, use_container_width=True)
                else:
                    st.info("Nenhum andamento registrado.")

            with andamento_tab2:
                with st.form("cadastro_produto"):
                    nome_produto = st.text_input("Nome do Produto")
                    descricao_produto = st.text_area("Descrição do Produto")
                    valor_produto = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
                    quantidade = st.number_input("Quantidade", min_value=1, step=1)
                    comodo = st.text_input("Cômodo")

                    # Carregar fornecedores
                    fornecedores = st.session_state.db.get_fornecedores()
                    if not fornecedores.empty:
                        fornecedor = st.selectbox(
                            "Fornecedor",
                            fornecedores['nome'].tolist()
                        )
                        fornecedor_id = fornecedores[fornecedores['nome'] == fornecedor]['id'].iloc[0]
                    else:
                        st.warning("Nenhum fornecedor cadastrado.")
                        fornecedor_id = None

                    if st.form_submit_button("Cadastrar Produto"):
                        if nome_produto and valor_produto > 0 and comodo and fornecedor_id:
                            try:
                                st.session_state.db.add_produto_organizador(
                                    proposta_id=proposta['id'],
                                    nome=nome_produto,
                                    descricao=descricao_produto,
                                    valor=valor_produto,
                                    quantidade=quantidade,
                                    comodo=comodo,
                                    fornecedor_id=fornecedor_id
                                )
                                st.success("Produto cadastrado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao cadastrar produto: {str(e)}")
                        else:
                            st.warning("Por favor, preencha todos os campos obrigatórios.")

                # Exibir produtos cadastrados
                produtos = st.session_state.db.get_produtos_organizadores(proposta['id'])
                if not produtos.empty:
                    st.dataframe(produtos, use_container_width=True)
                else:
                    st.info("Nenhum produto cadastrado.")
        else:
            st.warning("Nenhuma proposta cadastrada.")