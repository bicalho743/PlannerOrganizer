import streamlit as st
from datetime import datetime

def show():
    st.title("💳 Pagamentos")

    # Mostrar pagamentos pendentes
    st.subheader("Pagamentos Pendentes")
    pagamentos_pendentes = st.session_state.db.get_pagamentos_pendentes()

    if not pagamentos_pendentes.empty:
        for _, pagamento in pagamentos_pendentes.iterrows():
            with st.expander(f"Proposta #{pagamento['proposta']} - {pagamento['cliente']}"):
                st.write(f"**Tipo:** {pagamento['tipo']}")
                st.write(f"**Valor:** R$ {pagamento['valor']:.2f}")
                if pagamento['fornecedor']:
                    st.write(f"**Fornecedor:** {pagamento['fornecedor']}")

                # Botões de ação
                col1, col2 = st.columns([3, 1])
                with col1:
                    data_recebimento = st.date_input(
                        "Data de Recebimento",
                        value=datetime.now().date(),
                        key=f"date_{pagamento['proposta']}_{pagamento['tipo']}"
                    )
                with col2:
                    if st.button("✅ Marcar como Recebido", key=f"rec_{pagamento['proposta']}_{pagamento['tipo']}"):
                        try:
                            if pagamento['tipo'] == 'Valor Base':
                                # Atualizar status de pagamento da proposta
                                st.session_state.db.atualizar_status_pagamento_proposta(
                                    proposta_id=pagamento['proposta'],
                                    status_pagamento_base='Recebido',
                                    valor_base=pagamento['valor']
                                )
                            else:
                                # Atualizar status do acréscimo
                                st.session_state.db.atualizar_status_pagamento_acrescimo(
                                    proposta_id=pagamento['proposta'],
                                    tipo=pagamento['tipo'],
                                    status='Recebido'
                                )

                            # Registrar transação
                            st.session_state.db.add_transacao(
                                tipo='receita',
                                descricao=f"Recebimento {pagamento['tipo']} - Proposta #{pagamento['proposta']}",
                                valor=pagamento['valor'],
                                categoria='Recebimento Proposta',
                                origem_id=pagamento['proposta'],
                                origem_tipo='proposta',
                                status='Recebido',
                                data_recebimento=data_recebimento
                            )
                            st.success("Pagamento registrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar pagamento: {str(e)}")
    else:
        st.info("Não há pagamentos pendentes.")

    # Histórico de Pagamentos
    st.subheader("Histórico de Pagamentos")
    with st.expander("Ver histórico"):
        try:
            historico = st.session_state.db.get_historico_pagamentos()
            if not historico.empty:
                for _, pagamento in historico.iterrows():
                    st.write(f"**Proposta #{pagamento['proposta']} - {pagamento['cliente']}**")
                    st.write(f"**Tipo:** {pagamento['tipo']}")
                    st.write(f"**Valor:** R$ {pagamento['valor']:.2f}")
                    st.write(f"**Data de Recebimento:** {pagamento['data_recebimento'].strftime('%d/%m/%Y')}")
                    st.write("---")
            else:
                st.info("Nenhum pagamento registrado no histórico.")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {str(e)}")