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

        with st.form("cadastro_proposta", clear_on_submit=True):
            # Carregar lista de clientes para seleção
            clientes = st.session_state.db.get_clientes()

            if clientes.empty:
                st.warning("Não há clientes cadastrados. Por favor, cadastre um cliente primeiro.")
                st.stop()

            cliente_nome = st.selectbox("Cliente", clientes['nome'].tolist())
            cliente_id = int(clientes[clientes['nome'] == cliente_nome]['id'].iloc[0])

            descricao = st.text_area("Descrição do Serviço")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            tipo_proposta = st.selectbox(
                "Tipo de Proposta",
                ["Organização", "Organização Mudança", "Treinamento Funcionários", 
                 "Consultoria Online", "Consultoria Enxoval"]
            )

            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data de Início")
            with col2:
                data_fim = st.date_input("Data de Fim")

            prazo_entrega = st.date_input("Prazo de Entrega") if tipo_proposta in ["Organização", "Organização Mudança"] else None
            status = st.selectbox("Status", ["Aberta", "Recusada", "Fechada"])

            submitted = st.form_submit_button("Cadastrar")

            if submitted and descricao and valor > 0:
                try:
                    proposta_id = st.session_state.db.add_proposta(
                        cliente_id=cliente_id,
                        descricao=descricao,
                        valor=valor,
                        status=status,
                        tipo_proposta=tipo_proposta,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        prazo_entrega=prazo_entrega
                    )
                    st.success("Proposta cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar proposta: {str(e)}")

    with tab2:
        st.subheader("Propostas Cadastradas")

        try:
            propostas = st.session_state.db.get_propostas()
            if not propostas.empty:
                st.dataframe(
                    propostas[[
                        'numero', 'descricao', 'valor', 'status',
                        'tipo_proposta', 'data_inicio', 'data_fim',
                        'data_proposta'
                    ]].sort_values('data_proposta', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("Nenhuma proposta encontrada.")
        except Exception as e:
            st.error(f"Erro ao carregar propostas: {str(e)}")

    with tab3:
        st.subheader("Andamento do Trabalho")

        try:
            propostas = st.session_state.db.get_propostas()
            if propostas.empty:
                st.warning("Nenhuma proposta cadastrada.")
                st.stop()

            # Selecionar proposta
            proposta_numero = st.selectbox(
                "Número da Proposta",
                propostas['numero'].tolist()
            )

            proposta = propostas[propostas['numero'] == proposta_numero].iloc[0]
            proposta_id = int(proposta['id'])

            # Mostrar detalhes da proposta
            st.write(f"**Descrição:** {proposta['descricao']}")
            st.write(f"**Valor Total:** R$ {proposta['valor']:.2f}")
            st.write(f"**Status:** {proposta['status']}")

            # Adicionar produto
            st.subheader("Adicionar Produto")
            with st.form("cadastro_produto", clear_on_submit=True):
                nome_produto = st.text_input("Nome do Produto")
                descricao_produto = st.text_area("Descrição")
                quantidade = st.number_input("Quantidade", min_value=1, value=1)
                comodo = st.text_input("Cômodo")

                if st.form_submit_button("Adicionar") and nome_produto and comodo:
                    try:
                        st.session_state.db.add_produto_organizador(
                            proposta_id=proposta_id,
                            nome=nome_produto,
                            descricao=descricao_produto,
                            valor=0,
                            quantidade=quantidade,
                            comodo=comodo
                        )
                        st.success("Produto adicionado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao adicionar produto: {str(e)}")

            # Listar produtos
            produtos = st.session_state.db.get_produtos_organizadores(proposta_id)
            if not produtos.empty:
                st.subheader("Produtos da Proposta")
                for _, produto in produtos.iterrows():
                    with st.expander(f"{produto['nome']} - {produto['comodo']}"):
                        st.write(f"**Descrição:** {produto['descricao']}")
                        st.write(f"**Quantidade:** {produto['quantidade']}")
                        st.write(f"**Valor Atual:** R$ {produto['valor']:.2f}")

                        # Adicionar fornecedor
                        fornecedores = st.session_state.db.get_fornecedores()
                        if not fornecedores.empty:
                            with st.form(f"add_fornecedor_{produto['id']}", clear_on_submit=True):
                                fornecedor = st.selectbox(
                                    "Fornecedor",
                                    fornecedores['nome'].tolist(),
                                    key=f"fornecedor_{produto['id']}"
                                )
                                fornecedor_id = int(fornecedores[fornecedores['nome'] == fornecedor]['id'].iloc[0])
                                valor = st.number_input(
                                    "Valor (R$)",
                                    min_value=0.01,
                                    step=0.01,
                                    key=f"valor_{produto['id']}"
                                )

                                if st.form_submit_button("Adicionar Fornecedor"):
                                    try:
                                        st.session_state.db.add_produto_fornecedor(
                                            produto_id=produto['id'],
                                            fornecedor_id=fornecedor_id,
                                            valor=valor
                                        )
                                        st.success("Fornecedor adicionado com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao adicionar fornecedor: {str(e)}")
            else:
                st.info("Nenhum produto cadastrado para esta proposta.")

        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")