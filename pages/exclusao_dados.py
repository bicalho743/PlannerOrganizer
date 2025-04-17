
import streamlit as st

def show():
    st.title("Exclusão de Dados do Usuário")
    
    st.markdown("""
    ## Solicitação de Exclusão de Dados

    Para solicitar a exclusão dos seus dados pessoais do sistema Planner Organizer, 
    preencha o formulário abaixo:
    """)

    with st.form("formulario_exclusao"):
        email = st.text_input("Seu e-mail")
        motivo = st.text_area("Motivo da solicitação (opcional)")
        confirmar = st.checkbox("Confirmo que desejo a exclusão dos meus dados")
        
        if st.form_submit_button("Enviar Solicitação"):
            if email and confirmar:
                st.success("Solicitação recebida com sucesso! Entraremos em contato em até 48 horas.")
            else:
                st.error("Por favor, preencha o e-mail e confirme a solicitação.")

if __name__ == "__main__":
    show()
