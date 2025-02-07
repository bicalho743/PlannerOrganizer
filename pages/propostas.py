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
            try:
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
                            valor=float(valor),  # Garantir que é float
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
            except Exception as e:
                st.error(f"Erro ao carregar dados de clientes: {str(e)}")

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

            # Juntar dados de propostas com clientes para exibir o nome do cliente
            clientes = st.session_state.db.get_clientes()
            propostas = propostas.merge(clientes[['id', 'nome']], 
                                     left_on='cliente_id', 
                                     right_on='id', 
                                     suffixes=('', '_cliente'))

            # Selecionar proposta mostrando número e cliente
            proposta_display = propostas.apply(
                lambda x: f"Proposta #{x['numero']} - {x['nome']}", axis=1
            ).tolist()

            proposta_selecionada = st.selectbox(
                "Selecione a Proposta",
                proposta_display
            )

            if proposta_selecionada:
                # Extrair número da proposta do texto selecionado
                numero_proposta = int(proposta_selecionada.split('#')[1].split(' -')[0])
                proposta = propostas[propostas['numero'] == numero_proposta].iloc[0]

                # Exibir detalhes da proposta
                st.write(f"**Cliente:** {proposta['nome']}")
                st.write(f"**Descrição:** {proposta['descricao']}")
                valor_total = float(proposta['valor'])  # Garantir que é float
                st.write(f"**Valor Base:** R$ {valor_total:.2f}")

                # Adicionar acréscimos
                st.subheader("Adicionar Acréscimos")

                # Lista para armazenar os acréscimos
                if "acrescimos" not in st.session_state:
                    st.session_state.acrescimos = []

                # Formulário para adicionar acréscimo
                with st.form("adicionar_acrescimo"):
                    col1, col2 = st.columns(2)

                    with col1:
                        tipo_acrescimo = st.selectbox(
                            "Tipo de Acréscimo",
                            ["Organização", "Assistente", "Fornecedor", "Marcenaria", "Produto"]
                        )

                    with col2:
                        if tipo_acrescimo == "Fornecedor":
                            fornecedor = st.selectbox(
                                "Fornecedor",
                                ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                            )
                            fornecedor_nome = fornecedor
                        elif tipo_acrescimo == "Assistente":
                            # Carregar assistentes cadastrados
                            assistentes = st.session_state.db.get_assistentes()
                            if not assistentes.empty:
                                assistente = st.selectbox(
                                    "Assistente",
                                    assistentes['nome'].tolist()
                                )
                                fornecedor_nome = assistente
                            else:
                                st.warning("Nenhum assistente cadastrado. Por favor, cadastre um assistente primeiro.")
                                fornecedor_nome = None
                        else:
                            fornecedor_nome = None

                    descricao_acrescimo = st.text_input("Descrição")
                    valor_acrescimo = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

                    if st.form_submit_button("Adicionar"):
                        try:
                            if valor_acrescimo > 0 and (tipo_acrescimo != "Assistente" or fornecedor_nome):
                                # Adicionar acréscimo ao banco de dados
                                st.session_state.db.add_acrescimo_proposta(
                                    proposta_id=int(proposta['id']),  # Garantir que é int
                                    tipo=tipo_acrescimo,
                                    fornecedor=fornecedor_nome,
                                    descricao=descricao_acrescimo if descricao_acrescimo else None,
                                    valor=float(valor_acrescimo),  # Garantir que é float
                                    status_pagamento='Pendente'
                                )
                                st.success("Acréscimo adicionado com sucesso!")
                                st.rerun()
                            elif tipo_acrescimo == "Assistente" and not fornecedor_nome:
                                st.error("Por favor, selecione um assistente.")
                            else:
                                st.error("Por favor, insira um valor válido.")
                        except Exception as e:
                            st.error(f"Erro ao adicionar acréscimo: {str(e)}")

                # Exibir acréscimos
                try:
                    acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                    if not acrescimos.empty:
                        st.write("### Acréscimos Adicionados")
                        for _, acrescimo in acrescimos.iterrows():
                            if acrescimo['tipo'] == "Fornecedor":
                                st.write(f"- {acrescimo['tipo']} - {acrescimo['fornecedor']}: R$ {float(acrescimo['valor']):.2f}")
                            else:
                                st.write(f"- {acrescimo['tipo']}: R$ {float(acrescimo['valor']):.2f}")
                            if acrescimo['descricao']:
                                st.write(f"  *{acrescimo['descricao']}*")
                except Exception as e:
                    st.error(f"Erro ao carregar acréscimos: {str(e)}")

        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")