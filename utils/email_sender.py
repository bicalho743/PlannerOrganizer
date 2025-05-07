"""
Módulo para envio de e-mails usando SendGrid
"""
import os
from datetime import datetime
import time
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

# Configuração do SendGrid
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'contato@plannerorganiza.com.br')
FROM_NAME = os.environ.get('FROM_NAME', 'Planner Organiza')

# Cliente do SendGrid
if SENDGRID_API_KEY:
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
else:
    sg = None

# Função genérica para enviar e-mails
def enviar_email(destinatario, assunto, conteudo_html, conteudo_texto=None, 
                 remetente=FROM_EMAIL, nome_remetente=FROM_NAME):
    """
    Envia um e-mail usando SendGrid
    
    Args:
        destinatario: E-mail do destinatário
        assunto: Assunto do e-mail
        conteudo_html: Conteúdo HTML do e-mail
        conteudo_texto: Conteúdo em texto plano (opcional)
        remetente: E-mail do remetente (opcional)
        nome_remetente: Nome do remetente (opcional)
        
    Returns:
        dict: Resultado da operação
    """
    try:
        if not sg:
            print(f"API Key do SendGrid não configurada. E-mail não enviado para {destinatario}")
            return {
                'success': False,
                'message': 'API Key do SendGrid não configurada'
            }
            
        # Criar e-mail
        from_email = Email(remetente, nome_remetente)
        to_email = To(destinatario)
        
        # Definir conteúdo
        if conteudo_html:
            content = HtmlContent(conteudo_html)
        else:
            content = Content("text/plain", conteudo_texto or "")
            
        # Criar mensagem
        mail = Mail(from_email, to_email, assunto, content)
        
        # Enviar e-mail
        response = sg.send(mail)
        
        return {
            'success': True,
            'status_code': response.status_code,
            'message': 'E-mail enviado com sucesso'
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'message': f'Erro ao enviar e-mail: {str(e)}'
        }

# As funções relacionadas a assinaturas e Stripe foram removidas
# para preparar para a nova implementação