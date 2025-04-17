
import streamlit as st

def show():
    st.title("Política de Privacidade")
    
    st.markdown("""
    ## Política de Privacidade do Planner Organizer

    ### 1. Informações coletadas
    Coletamos apenas as informações necessárias para o funcionamento do sistema:
    - Nome
    - E-mail
    - Informações de propostas e serviços
    
    ### 2. Uso das informações
    As informações são utilizadas exclusivamente para:
    - Gerenciamento de propostas
    - Comunicação com clientes
    - Geração de relatórios
    
    ### 3. Proteção de dados
    Seus dados são armazenados de forma segura e protegida.
    
    ### 4. Seus direitos
    Você tem direito a:
    - Acessar seus dados
    - Solicitar correções
    - Solicitar exclusão
    """)

if __name__ == "__main__":
    show()
