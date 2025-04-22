import streamlit as st

st.set_page_config(page_title="Teste Básico", page_icon="🔄")

st.title("Aplicativo de Teste Básico")
st.write("Este é um aplicativo de teste simples para verificar se o Streamlit está funcionando corretamente.")

# Adicionar um slider interativo
value = st.slider("Selecione um valor", 0, 100, 50)
st.write(f"Valor selecionado: {value}")

# Adicionar um botão
if st.button("Clique Aqui"):
    st.success("Botão clicado com sucesso!")

# Mostrar informações sobre o ambiente
st.subheader("Informações do Ambiente")
st.info("Se você está vendo esta mensagem, o aplicativo Streamlit está funcionando corretamente!")