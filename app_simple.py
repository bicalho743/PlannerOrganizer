import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📅",
    layout="wide"
)

st.title("🚀 Planner Organizer - Sistema Funcionando!")
st.success("Aplicação carregada com sucesso!")

if st.button("Teste de Botão"):
    st.balloons()
    st.write("✅ Botão funcionando perfeitamente!")

st.markdown("---")
st.info("Sistema operacional e pronto para uso.")