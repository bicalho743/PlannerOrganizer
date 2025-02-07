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

            # Extrair número da proposta do texto selecionado
            numero_proposta = int(proposta_selecionada.split('#')[1].split(' -')[0])
            proposta = propostas[propostas['numero'] == numero_proposta].iloc[0]

            # Exibir detalhes da proposta
            st.write(f"**Cliente:** {proposta['nome']}")
            st.write(f"**Descrição:** {proposta['descricao']}")
            valor_total = proposta['valor']
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
                        ["Organização", "Fornecedor", "Marcenaria", "Produto"]
                    )

                with col2:
                    if tipo_acrescimo == "Fornecedor":
                        fornecedor = st.selectbox(
                            "Fornecedor",
                            ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                        )
                    else:
                        fornecedor = None

                descricao_acrescimo = st.text_input("Descrição")
                valor_acrescimo = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
                status_pagamento = st.selectbox(
                    "Status do Pagamento",
                    ["Pendente", "Pago"],
                    key=f"status_pagamento_novo"
                )

                if st.form_submit_button("Adicionar"):
                    if valor_acrescimo > 0:
                        acrescimo = {
                            'tipo': tipo_acrescimo,
                            'fornecedor': fornecedor,
                            'descricao': descricao_acrescimo,
                            'valor': valor_acrescimo,
                            'status_pagamento': status_pagamento
                        }
                        st.session_state.acrescimos.append(acrescimo)
                        st.success("Acréscimo adicionado!")
                        st.rerun()

            # Exibir acréscimos
            if st.session_state.acrescimos:
                st.write("### Acréscimos Adicionados")
                for i, acrescimo in enumerate(st.session_state.acrescimos):
                    valor_total += acrescimo['valor']
                    if acrescimo['tipo'] == "Fornecedor":
                        st.write(f"- {acrescimo['tipo']} - {acrescimo['fornecedor']}: R$ {acrescimo['valor']:.2f} ({acrescimo['status_pagamento']})")
                    else:
                        st.write(f"- {acrescimo['tipo']}: R$ {acrescimo['valor']:.2f} ({acrescimo['status_pagamento']})")
                    if acrescimo['descricao']:
                        st.write(f"  *{acrescimo['descricao']}*")

            # Botão para fechar e mostrar total
            if st.button("Fechar Proposta"):
                st.write("### Resumo Final")
                st.write(f"**Cliente:** {proposta['nome']}")
                st.write(f"**Valor Base:** R$ {proposta['valor']:.2f}")

                valor_pendente = 0.0
                for i, acrescimo in enumerate(st.session_state.acrescimos):
                    status = st.selectbox(
                        "Status do Pagamento",
                        ["Pendente", "Pago"],
                        key=f"status_pagamento_{i}",
                        index=0 if acrescimo['status_pagamento'] == "Pendente" else 1
                    )
                    acrescimo['status_pagamento'] = status

                    if status == "Pendente":
                        valor_pendente += acrescimo['valor']

                    if acrescimo['tipo'] == "Fornecedor":
                        st.write(f"**{acrescimo['tipo']} - {acrescimo['fornecedor']}:** R$ {acrescimo['valor']:.2f} - {status}")
                    else:
                        st.write(f"**{acrescimo['tipo']}:** R$ {acrescimo['valor']:.2f} - {status}")

                st.write(f"**Valor Total:** R$ {valor_total:.2f}")
                st.write(f"**Valor Pendente:** R$ {valor_pendente:.2f}")

                # Botão para confirmar e salvar alterações
                if st.button("Confirmar Alterações", key="confirmar_alteracoes"):
                    st.success("Alterações salvas com sucesso!")
                    st.session_state.acrescimos = []  # Limpar acréscimos após confirmar

        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")