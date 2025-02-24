import streamlit as st
from utils.pagamentos import GerenciadorPagamentos
from datetime import datetime

def show():
    st.title("💳 Pagamentos")

    if 'STRIPE_SECRET_KEY' not in st.secrets:
        st.error("Configure as chaves do Stripe nas secrets do Replit")
        return

    # Inicializar gerenciador de pagamentos
    gerenciador = GerenciadorPagamentos(st.session_state.db)

    # Adicionar script do Stripe
    st.markdown("""
        <script src="https://js.stripe.com/v3/"></script>
    """, unsafe_allow_html=True)

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

                # Botão para processar pagamento
                if st.button("Processar Pagamento", key=f"pay_{pagamento['proposta']}_{pagamento['tipo']}"):
                    try:
                        # Criar intenção de pagamento
                        payment_info = gerenciador.criar_pagamento(
                            proposta_id=pagamento['proposta'],
                            valor=pagamento['valor'],
                            descricao=f"Pagamento {pagamento['tipo']} - Proposta #{pagamento['proposta']}"
                        )

                        # Configurar Stripe Elements
                        st.markdown(f"""
                        <div id="payment-form">
                            <div id="payment-element"></div>
                            <button id="submit">Pagar R$ {pagamento['valor']:.2f}</button>
                        </div>

                        <script>
                            const stripe = Stripe('{payment_info['publishableKey']}');
                            const elements = stripe.elements({{
                                clientSecret: '{payment_info['clientSecret']}'
                            }});

                            const paymentElement = elements.create('payment');
                            paymentElement.mount('#payment-element');

                            const form = document.getElementById('payment-form');
                            form.addEventListener('submit', async (event) => {{
                                event.preventDefault();

                                const {{error}} = await stripe.confirmPayment({{
                                    elements,
                                    confirmParams: {{
                                        return_url: window.location.origin + '/pagamento_concluido',
                                    }}
                                }});

                                if (error) {{
                                    const messageDiv = document.createElement('div');
                                    messageDiv.textContent = error.message;
                                    form.appendChild(messageDiv);
                                }}
                            }});
                        </script>
                        """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Erro ao processar pagamento: {str(e)}")
    else:
        st.info("Não há pagamentos pendentes.")

    # Histórico de Pagamentos
    st.subheader("Histórico de Pagamentos")
    with st.expander("Ver histórico"):
        # TODO: Implementar visualização do histórico de pagamentos
        st.info("Em desenvolvimento")