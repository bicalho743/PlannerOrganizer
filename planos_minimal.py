import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planos Simples",
    page_icon="favicon.png",
    layout="wide"
)

# Título principal
st.title("Planos de Assinatura")

# Seção de planos super simples
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Plano Mensal")
    st.write("R$ 9,70 / mês")
    st.write("- Acesso a todos os recursos")
    st.write("- Cancelamento a qualquer momento")
    if st.button("Assinar Mensal", key="btn_mensal"):
        st.success("Plano mensal selecionado!")

with col2:
    st.subheader("Plano Anual")
    st.write("R$ 97 / ano")
    st.write("- Economize 17%")
    st.write("- Acesso a todos os recursos")
    if st.button("Assinar Anual", key="btn_anual"):
        st.success("Plano anual selecionado!")

with col3:
    st.subheader("Acesso Vitalício")
    st.write("R$ 247 (pagamento único)")
    st.write("- Sem mensalidades")
    st.write("- Acesso permanente")
    if st.button("Comprar Vitalício", key="btn_vitalicio"):
        st.success("Acesso vitalício selecionado!")