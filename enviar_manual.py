"""
Módulo para envio de manual do sistema
"""
import streamlit as st
import os
import sys

# Adicionar o diretório principal ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def main():
    """Função principal da página de envio de manual"""
    st.title("Envio de Manual do Sistema")
    st.write("Esta página permite enviar o manual do sistema por email.")
    
    with st.form("enviar_manual"):
        email = st.text_input("Email do destinatário:")
        nome = st.text_input("Nome do destinatário:")
        
        submitted = st.form_submit_button("Enviar Manual")
        
        if submitted:
            if email and nome:
                try:
                    # Importar as funções quando necessário para evitar erros de inicialização
                    from enviar_manual_simples import adicionar_email_lista_brevo, enviar_email_manual
                    
                    # Adicionar à lista do Brevo
                    adicionar_email_lista_brevo(email, nome)
                    
                    # Enviar email com manual
                    resultado = enviar_email_manual(email, nome)
                    
                    if resultado:
                        st.success("Manual enviado com sucesso!")
                    else:
                        st.error("Erro ao enviar manual.")
                        
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
            else:
                st.error("Por favor, preencha todos os campos.")

if __name__ == "__main__":
    main()