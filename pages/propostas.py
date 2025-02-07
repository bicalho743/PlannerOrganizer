import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.pdf_generator import gerar_pdf_fechamento

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
            try:
                # Carregar lista de clientes para seleção
                clientes = st.session_state.db.get_clientes()
                if clientes.empty:
                    st.warning("Não há clientes cadastrados. Por favor, cadastre um cliente primeiro.")
                    st.stop()

                # Campos do formulário
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

                # Botão de submissão
                submitted = st.form_submit_button("Cadastrar")

                if submitted:
                    if not descricao:
                        st.error("Por favor, preencha a descrição da proposta.")
                        return
                    if valor <= 0:
                        st.error("Por favor, insira um valor válido maior que zero.")
                        return

                    try:
                        # Adicionar proposta ao banco de dados
                        proposta_id = st.session_state.db.add_proposta(
                            cliente_id=cliente_id,
                            descricao=descricao,
                            valor=float(valor),
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
                propostas_display = propostas[[
                    'numero', 'descricao', 'valor', 'status',
                    'tipo_proposta', 'data_inicio', 'data_fim',
                    'data_proposta'
                ]].sort_values('data_proposta', ascending=False)

                # Converter valor para float e formatar
                propostas_display['valor'] = propostas_display['valor'].astype(float).round(2)

                st.dataframe(propostas_display, use_container_width=True)
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
                return

            # Juntar dados de propostas com clientes
            clientes = st.session_state.db.get_clientes()
            propostas = propostas.merge(
                clientes[['id', 'nome']], 
                left_on='cliente_id', 
                right_on='id', 
                suffixes=('', '_cliente')
            )

            # Selecionar proposta
            proposta_display = [
                f"Proposta #{p['numero']} - {p['nome']}" 
                for _, p in propostas.iterrows()
            ]

            proposta_selecionada = st.selectbox(
                "Selecione a Proposta",
                proposta_display
            )

            if proposta_selecionada:
                try:
                    # Extrair número da proposta
                    numero_proposta = int(proposta_selecionada.split('#')[1].split(' -')[0])
                    proposta = propostas[propostas['numero'] == numero_proposta].iloc[0]

                    # Exibir detalhes da proposta
                    st.write(f"**Cliente:** {proposta['nome']}")
                    st.write(f"**Descrição:** {proposta['descricao']}")
                    st.write(f"**Valor Base:** R$ {float(proposta['valor']):.2f}")

                    # Seção de acréscimos
                    st.subheader("Adicionar Acréscimos")

                    with st.form("adicionar_acrescimo"):
                        col1, col2 = st.columns(2)

                        with col1:
                            tipo_acrescimo = st.selectbox(
                                "Tipo de Acréscimo",
                                ["Organização", "Assistente", "Fornecedor", "Marcenaria", "Produto"]
                            )

                        with col2:
                            fornecedor_nome = None
                            if tipo_acrescimo == "Fornecedor":
                                fornecedor = st.selectbox(
                                    "Fornecedor",
                                    ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                                )
                                fornecedor_nome = fornecedor
                            elif tipo_acrescimo == "Assistente":
                                try:
                                    assistentes = st.session_state.db.get_assistentes()
                                    if not assistentes.empty:
                                        assistente = st.selectbox(
                                            "Assistente",
                                            assistentes['nome'].tolist()
                                        )
                                        fornecedor_nome = assistente
                                    else:
                                        st.warning("Nenhum assistente cadastrado.")
                                except Exception as e:
                                    st.error(f"Erro ao carregar assistentes: {str(e)}")

                        descricao_acrescimo = st.text_input("Descrição")
                        valor_acrescimo = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

                        if st.form_submit_button("Adicionar"):
                            if valor_acrescimo <= 0:
                                st.error("Por favor, insira um valor válido maior que zero.")
                                return

                            if tipo_acrescimo == "Assistente" and not fornecedor_nome:
                                st.error("Por favor, selecione um assistente.")
                                return

                            try:
                                # Adicionar acréscimo
                                st.session_state.db.add_acrescimo_proposta(
                                    proposta_id=int(proposta['id']),
                                    tipo=tipo_acrescimo,
                                    fornecedor=fornecedor_nome,
                                    descricao=descricao_acrescimo if descricao_acrescimo else None,
                                    valor=float(valor_acrescimo)
                                )
                                st.success("Acréscimo adicionado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao adicionar acréscimo: {str(e)}")

                    # Exibir acréscimos existentes
                    try:
                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                        if not acrescimos.empty:
                            st.write("### Acréscimos Adicionados")
                            for _, acrescimo in acrescimos.iterrows():
                                valor = float(acrescimo['valor'])
                                if acrescimo['tipo'] == "Fornecedor":
                                    st.write(f"- {acrescimo['tipo']} - {acrescimo['fornecedor']}: R$ {valor:.2f}")
                                else:
                                    st.write(f"- {acrescimo['tipo']}: R$ {valor:.2f}")

                                if acrescimo['descricao']:
                                    st.write(f"  *{acrescimo['descricao']}*")

                        # Botão e seção de Fechar Proposta
                        st.write("---")
                        col1, col2, col3 = st.columns([2,1,1])
                        with col3:
                            st.write("**Valor Base**")
                            valor_base = st.number_input(
                                "Valor Base",
                                value=float(proposta['valor']),
                                step=0.01,
                                key="valor_base"
                            )
                            status_base = st.selectbox(
                                "Status",
                                ["Pendente", "Pago"],
                                key="status_base"
                            )
                            st.write("---")

                            # Exibir acréscimos para atualização
                            valor_pendente = valor_base if status_base == "Pendente" else 0.0

                            if not acrescimos.empty:
                                for index, acrescimo in acrescimos.iterrows():
                                    col1, col2, col3 = st.columns([2, 1, 1])

                                    with col1:
                                        if acrescimo['tipo'] == "Fornecedor":
                                            st.write(f"**{acrescimo['tipo']} - {acrescimo['fornecedor']}**")
                                        else:
                                            st.write(f"**{acrescimo['tipo']}**")
                                        if acrescimo['descricao']:
                                            st.write(f"*{acrescimo['descricao']}*")

                                    with col2:
                                        novo_valor = st.number_input(
                                            "Valor",
                                            value=float(acrescimo['valor']),
                                            step=0.01,
                                            key=f"valor_{index}"
                                        )

                                    with col3:
                                        status = st.selectbox(
                                            "Status",
                                            ["Pendente", "Pago"],
                                            key=f"status_{index}"
                                        )

                                    if status == "Pendente":
                                        valor_pendente += novo_valor

                                    st.write("---")

                            # Atualizar status de pagamento da proposta base
                            try:
                                # Converter explicitamente para tipos nativos do Python
                                proposta_id = int(proposta['id'])
                                valor_base = float(valor_base)

                                st.session_state.db.atualizar_status_pagamento_proposta(
                                    proposta_id=proposta_id,
                                    status_pagamento_base=status_base,
                                    valor_base=valor_base
                                )

                                # Atualizar totais
                                valor_total = valor_base
                                if not acrescimos.empty:
                                    # Converter valores para float antes de somar
                                    valor_total += float(acrescimos['valor'].astype(float).sum())

                                st.write(f"**Valor Total:** R$ {valor_total:.2f}")
                                st.write(f"**Valor Pendente:** R$ {valor_pendente:.2f}")

                            except Exception as e:
                                st.error(f"Erro ao atualizar status de pagamento: {str(e)}")

                            # Botão para confirmar e salvar alterações
                            if st.button("Confirmar Alterações"):
                                st.success("Alterações salvas com sucesso!")
                                st.rerun()

                        # Botão para exportar PDF movido para fora do bloco de atualização
                        st.write("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Exportar Resumo Final (PDF)"):
                                try:
                                    # Criar diretório para PDFs se não existir
                                    os.makedirs("pdfs", exist_ok=True)

                                    # Nome do arquivo
                                    filename = f"pdfs/proposta_{proposta['numero']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                                    # Gerar PDF
                                    pdf_path = gerar_pdf_fechamento(
                                        proposta=proposta,
                                        cliente={'nome': proposta['nome']},
                                        acrescimos=acrescimos,
                                        filename=filename
                                    )

                                    # Criar link para download
                                    with open(pdf_path, "rb") as pdf_file:
                                        pdf_bytes = pdf_file.read()
                                        st.download_button(
                                            label="Baixar PDF",
                                            data=pdf_bytes,
                                            file_name=os.path.basename(filename),
                                            mime="application/pdf"
                                        )

                                    st.success("PDF gerado com sucesso!")
                                except Exception as e:
                                    st.error(f"Erro ao gerar PDF: {str(e)}")

                    except Exception as e:
                        st.error(f"Erro ao carregar acréscimos: {str(e)}")

                except Exception as e:
                    st.error(f"Erro ao processar proposta selecionada: {str(e)}")

        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")