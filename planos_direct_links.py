import streamlit as st

def exibir_planos_diretos():
    """
    Exibe os planos com links diretos para o checkout do Stripe
    """
    st.title("Escolha seu plano")
    
    st.markdown("""
    Este é um sistema de integração direta com o Stripe. 
    Selecione um dos planos abaixo para ser redirecionado ao checkout seguro.
    """)
    
    # Criar três colunas para os planos
    col1, col2, col3 = st.columns(3)
    
    # Plano Mensal
    with col1:
        st.subheader("Plano Mensal")
        st.write("R$ 9,70 / mês")
        st.write("✓ 7 dias de teste grátis")
        st.write("✓ Acesso a todos os recursos")
        st.write("✓ Suporte por email")
        
        url_mensal = "https://buy.stripe.com/test_14k3dG3pL3rI6KQ000"
        st.markdown(f"[Assinar Plano Mensal]({url_mensal})")
    
    # Plano Anual
    with col2:
        st.subheader("Plano Anual")
        st.write("R$ 97,00 / ano")
        st.write("✓ 7 dias de teste grátis")
        st.write("✓ Economize 17%")
        st.write("✓ Suporte prioritário")
        
        url_anual = "https://buy.stripe.com/test_5kA9F26BP1jA4CI004"
        st.markdown(f"[Assinar Plano Anual]({url_anual})")
    
    # Plano Vitalício
    with col3:
        st.subheader("Acesso Vitalício")
        st.write("R$ 247,00 (único)")
        st.write("✓ Sem mensalidades")
        st.write("✓ Todas as atualizações futuras")
        st.write("✓ Suporte prioritário vitalício")
        
        url_vitalicio = "https://buy.stripe.com/test_aEU9F26BPeSEbZ6005"
        st.markdown(f"[Adquirir Acesso Vitalício]({url_vitalicio})")
    
    # Botões alternativos que abrem em uma nova aba
    st.markdown("### Ou use os botões abaixo (abrem em nova aba)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <a href="https://buy.stripe.com/test_14k3dG3pL3rI6KQ000" target="_blank">
            <button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                Assinar Plano Mensal
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <a href="https://buy.stripe.com/test_5kA9F26BP1jA4CI004" target="_blank">
            <button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                Assinar Plano Anual
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <a href="https://buy.stripe.com/test_aEU9F26BPeSEbZ6005" target="_blank">
            <button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                Adquirir Acesso Vitalício
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    # Informações sobre a página checkout do Stripe
    st.info("""
    Ao clicar em qualquer um dos botões acima, você será redirecionado para a página segura de checkout do Stripe,
    onde poderá inserir seus dados de pagamento com total segurança. Após o pagamento bem-sucedido, você será 
    redirecionado de volta para nossa plataforma.
    """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Planos - Planner Organizer",
        page_icon="📊",
        layout="wide"
    )
    exibir_planos_diretos()