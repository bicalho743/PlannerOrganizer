import streamlit as st
import os
import sys
import base64
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Adicionar o diretório principal ao path para encontrar módulos
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Configurações do Brevo
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_LIST_ID = os.getenv("BREVO_LIST_ID", "7")
EMAIL_REMETENTE = "contato@plannerorganizer.com.br" 
NOME_REMETENTE = "Equipe Planner Organizer"
ASSUNTO_EMAIL = "Manual Planner Organizer"
CAMINHO_ANEXO = os.path.join(root_dir, "pdfs", "manual_sistema.pdf")

def adicionar_email_lista_brevo(email_usuario, nome_usuario="Novo Cliente"):
    """Adiciona um contato à lista do Brevo"""
    try:
        # Configuração da API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # Preparar dados do contato
        contato = {
            "email": email_usuario, 
            "attributes": {"NOME": nome_usuario}
        }
        
        # Adicionar à lista específica se configurada
        try:
            list_id = int(BREVO_LIST_ID)
            contato["listIds"] = [list_id]
        except ValueError:
            # Se o ID não for um número válido, continuamos sem a lista
            st.warning(f"ID da lista inválido: {BREVO_LIST_ID}")
            
        # Enviar para API
        api_instance.create_contact(contato)
        st.success(f"E-mail {email_usuario} adicionado com sucesso à lista.")
        return True
    except ApiException as e:
        st.error(f"Erro na API do Brevo: {e}")
        return False
    except Exception as e:
        st.error(f"Erro ao adicionar e-mail: {e}")
        return False

def enviar_email_manual(destinatario_email, destinatario_nome):
    """Envia o e-mail com o manual em anexo"""
    try:
        # Verificar se o arquivo do manual existe
        if not os.path.exists(CAMINHO_ANEXO):
            st.error(f"Arquivo do manual não encontrado em: {CAMINHO_ANEXO}")
            return False
            
        # Configuração da API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # Conteúdo HTML do e-mail
        mensagem_html = f"""
        <h3>Obrigado por se cadastrar!</h3>
        <p>Olá <strong>{destinatario_nome}</strong>,</p>
        <p>Estamos felizes em tê-lo conosco! Como prometido, aqui está o seu manual em anexo.</p>
        <p>Caso tenha dúvidas, estamos à disposição.</p>
        <p>Atenciosamente,<br>Equipe Planner Organizer</p>
        """
        
        # Preparar e-mail
        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": destinatario_email, "name": destinatario_nome}],
            sender={"email": EMAIL_REMETENTE, "name": NOME_REMETENTE},
            subject=ASSUNTO_EMAIL,
            html_content=mensagem_html
        )
        
        # Anexar o manual
        with open(CAMINHO_ANEXO, "rb") as file:
            content = base64.b64encode(file.read()).decode('utf-8')
            email.attachment = [
                {"content": content, "name": os.path.basename(CAMINHO_ANEXO)}
            ]
        
        # Enviar e-mail
        api_instance.send_transac_email(email)
        st.success(f"E-mail enviado com sucesso para {destinatario_email}!")
        return True
    except ApiException as e:
        st.error(f"Erro na API do Brevo ao enviar e-mail: {e}")
        return False
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

def main():
    """Função principal da aplicação"""
    st.set_page_config(
        page_title="Enviar Manual - Planner Organizer",
        page_icon="favicon.png",
        layout="centered"
    )

    st.title("Cadastre-se e Receba seu Manual")
    
    # Formulário simples de cadastro
    email_usuario = st.text_input("Digite seu e-mail:")
    nome_usuario = st.text_input("Digite seu nome:", value="Novo Cliente")

    if st.button("Cadastrar e Receber Manual"):
        if "@" in email_usuario:
            with st.spinner("Processando sua solicitação..."):
                # 1. Adicionar à lista do Brevo
                if adicionar_email_lista_brevo(email_usuario, nome_usuario):
                    # 2. Enviar e-mail com o manual
                    if enviar_email_manual(email_usuario, nome_usuario):
                        st.success(f"Cadastro realizado e e-mail enviado com sucesso para {email_usuario}!")
                    else:
                        st.warning("E-mail cadastrado, mas houve um problema ao enviar o manual.")
        else:
            st.error("E-mail inválido. Por favor, verifique e tente novamente.")

if __name__ == "__main__":
    main()