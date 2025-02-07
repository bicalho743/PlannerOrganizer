import streamlit as st

def cadastrar_fornecedor(nome, cnpj, telefone, email, endereco, categoria, pix, contato):
    #Aqui você colocaria a lógica para inserir os dados no banco de dados
    print(f"Fornecedor cadastrado: Nome={nome}, CNPJ={cnpj}, Telefone={telefone}, Email={email}, Endereco={endereco}, Categoria={categoria}, PIX={pix}, Contato={contato}")
    st.success("Fornecedor cadastrado com sucesso!")


st.title("Cadastro de Fornecedor")

with st.form("cadastro_form"):
    nome = st.text_input("Nome")
    cnpj = st.text_input("CNPJ")
    telefone = st.text_input("Telefone")
    email = st.text_input("Email")
    endereco = st.text_input("Endereço")
    categoria = st.selectbox(
                "Categoria",
                ["Marcenaria", "Materiais", "Consignado", "Outros"]
            )
    pix = st.text_input("Chave PIX")
    contato = st.text_input("Nome do Contato")

    submitted = st.form_submit_button("Cadastrar")

if submitted:
    cadastrar_fornecedor(nome=nome,
                        cnpj=cnpj,
                        telefone=telefone,
                        email=email,
                        endereco=endereco,
                        categoria=categoria,
                        pix=pix,
                        contato=contato
                        )