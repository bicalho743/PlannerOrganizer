import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show():
    st.title("💰 Contas a Pagar")

    tab1, tab2 = st.tabs(["Nova Conta", "Lista de Contas"])

    with tab1:
        st.subheader("Registrar Nova Conta")

        with st.form("cadastro_conta"):
            tipo_conta = st.selectbox(
                "Tipo de Conta",
                ["PF", "PJ"],
                format_func=lambda x: "Pessoa Física" if x == "PF" else "Pessoa Jurídica"
            )

            # Carregar categorias do tipo selecionado
            categorias = st.session_state.db.get_categorias_despesa()
            if not categorias.empty:
                categorias = categorias[categorias['tipo_conta'] == tipo_conta]
                categoria = st.selectbox(
                    "Categoria",
                    categorias['nome'].tolist()
                )
                categoria_id = categorias[categorias['nome'] == categoria]['id'].iloc[0]
            else:
                st.warning("Nenhuma categoria cadastrada. Adicione categorias primeiro.")
                categoria_id = None

            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            data_vencimento = st.date_input("Data de Vencimento")
            fornecedor = st.text_input("Fornecedor (opcional)")
            recorrente = st.checkbox("Conta Recorrente")
            observacoes = st.text_area("Observações (opcional)")

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if descricao and valor > 0 and categoria_id:
                    try:
                        st.session_state.db.add_conta_pagar(
                            descricao=descricao,
                            valor=valor,
                            data_vencimento=data_vencimento,
                            categoria_id=categoria_id,
                            tipo_conta=tipo_conta,
                            fornecedor=fornecedor,
                            recorrente=recorrente,
                            observacoes=observacoes
                        )
                        st.success("Conta cadastrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar conta: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

    with tab2:
        st.subheader("Contas Cadastradas")

        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filtro = st.multiselect(
                "Status",
                ["Pendente", "Pago", "Atrasado"],
                default=["Pendente"]
            )
        with col2:
            tipo_filtro = st.multiselect(
                "Tipo de Conta",
                ["PF", "PJ"],
                default=["PF", "PJ"]
            )
        with col3:
            data_filtro = st.date_input("Vencimento até")

        try:
            # Carregar dados
            contas = st.session_state.db.get_contas_pagar()
            categorias = st.session_state.db.get_categorias_despesa()

            if not contas.empty and not categorias.empty:
                # Converter datas para datetime
                contas['data_vencimento'] = pd.to_datetime(contas['data_vencimento'])

                # Merge com categorias
                contas = pd.merge(
                    contas,
                    categorias[['id', 'nome']],
                    left_on='categoria_id',
                    right_on='id',
                    how='left'
                )

                # Aplicar filtros
                if status_filtro:
                    contas = contas[contas['status'].isin(status_filtro)]
                if tipo_filtro:
                    contas = contas[contas['tipo_conta'].isin(tipo_filtro)]
                if data_filtro:
                    contas = contas[contas['data_vencimento'].dt.date <= data_filtro]

                # Formatar data para exibição
                contas['data_vencimento'] = contas['data_vencimento'].dt.strftime('%d/%m/%Y')

                # Exibir tabela
                st.dataframe(
                    contas[[
                        'descricao', 'valor', 'data_vencimento', 'status',
                        'nome', 'tipo_conta', 'fornecedor', 'recorrente'
                    ]],
                    use_container_width=True
                )

                # Resumo financeiro
                col1, col2, col3 = st.columns(3)

                # Calcular totais
                total_pendente = contas[contas['status'] == 'Pendente']['valor'].sum()
                total_pago = contas[contas['status'] == 'Pago']['valor'].sum()
                total_atrasado = contas[contas['status'] == 'Atrasado']['valor'].sum()

                col1.metric("Total Pendente", f"R$ {total_pendente:.2f}")
                col2.metric("Total Pago", f"R$ {total_pago:.2f}")
                col3.metric("Total Atrasado", f"R$ {total_atrasado:.2f}")
            else:
                st.info("Nenhuma conta cadastrada.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")