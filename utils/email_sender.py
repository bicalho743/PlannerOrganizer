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

# Função para enviar e-mail de confirmação de assinatura
def enviar_confirmacao_assinatura(destinatario, nome, plano):
    """
    Envia um e-mail de confirmação de assinatura
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        plano: Nome do plano assinado
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = f"Bem-vindo ao Planner Organiza - Plano {plano} Ativado!"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #1E88E5; text-align: center;">Assinatura Confirmada!</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Estamos muito felizes em confirmar que sua assinatura do <strong>Plano {plano}</strong> foi realizada com sucesso.</p>
        
        <p>A partir de agora, você tem acesso a todas as funcionalidades incríveis do Planner Organiza:</p>
        
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Gerenciamento ilimitado de propostas
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Gerenciamento ilimitado de clientes
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Relatórios personalizados
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Exportação de dados
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Suporte prioritário
            </li>
        </ul>
        
        <p>Para acessar sua assinatura e verificar os detalhes, visite <a href="https://www.plannerorganiza.com.br/minha_assinatura" style="color: #1E88E5; text-decoration: none;">Minha Assinatura</a>.</p>
        
        <p>Se precisar de qualquer assistência, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você assinou o Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar e-mail de notificação de pagamento
def enviar_notificacao_pagamento(destinatario, nome, plano):
    """
    Envia um e-mail de notificação de pagamento
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        plano: Nome do plano
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = f"Pagamento Processado - Planner Organiza ({plano})"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #1E88E5; text-align: center;">Pagamento Processado</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Confirmamos que o pagamento do seu <strong>Plano {plano}</strong> foi processado com sucesso.</p>
        
        <p>Sua assinatura continua ativa e você pode usar todas as funcionalidades do Planner Organiza sem interrupções.</p>
        
        <p>Para verificar os detalhes da sua assinatura, visite <a href="https://www.plannerorganiza.com.br/minha_assinatura" style="color: #1E88E5; text-decoration: none;">Minha Assinatura</a>.</p>
        
        <p>Se precisar de qualquer assistência, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você é cliente do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar e-mail de lembrete de renovação
def enviar_lembrete_renovacao(destinatario, nome, plano, dias_restantes, data_expiracao):
    """
    Envia um e-mail de lembrete de renovação
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        plano: Nome do plano
        dias_restantes: Número de dias restantes
        data_expiracao: Data de expiração formatada
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = f"Sua Assinatura do Planner Organiza Vence em {dias_restantes} Dias"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #FF9800; text-align: center;">Lembrete de Renovação</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Gostaríamos de lembrá-lo que sua assinatura do <strong>Plano {plano}</strong> expirará em <strong>{dias_restantes} dias</strong> ({data_expiracao}).</p>
        
        <p>Para garantir que você continue tendo acesso a todas as funcionalidades do Planner Organiza sem interrupções, verifique se seu método de pagamento está atualizado.</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #333;">O que fazer agora?</h3>
            <p style="margin-bottom: 0;">Acesse <a href="https://www.plannerorganiza.com.br/minha_assinatura" style="color: #1E88E5; text-decoration: none;">Minha Assinatura</a> para verificar os detalhes da sua assinatura e garantir que seu método de pagamento esteja atualizado.</p>
        </div>
        
        <p>Se tiver alguma dúvida ou precisar de assistência, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você é cliente do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar e-mail de notificação de cancelamento
def enviar_notificacao_cancelamento(destinatario, nome):
    """
    Envia um e-mail de notificação de cancelamento
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = "Sua Assinatura do Planner Organiza Foi Cancelada"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #F44336; text-align: center;">Assinatura Cancelada</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Confirmamos que sua assinatura do Planner Organiza foi cancelada conforme solicitado.</p>
        
        <p>Você continuará tendo acesso às funcionalidades até o final do período pago atual. Após esse período, seu acesso será limitado.</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #333;">Sentimos sua falta!</h3>
            <p style="margin-bottom: 0;">Se mudar de ideia, você pode reativar sua assinatura a qualquer momento através da página <a href="https://www.plannerorganiza.com.br/planos" style="color: #1E88E5; text-decoration: none;">Planos</a>.</p>
        </div>
        
        <p>Gostaríamos de agradecer por ter sido nosso cliente e esperamos poder atendê-lo novamente no futuro.</p>
        
        <p>Se tiver alguma dúvida ou feedback sobre o serviço, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você cancelou sua assinatura do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar e-mail de confirmação de teste gratuito
def enviar_confirmacao_teste(destinatario, nome, data_fim):
    """
    Envia um e-mail de confirmação do início do período de teste gratuito
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        data_fim: Data de término do período de teste
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = "Seu período de teste gratuito começou!"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #4CAF50; text-align: center;">Seu teste gratuito foi ativado!</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Estamos muito felizes em confirmar que seu <strong>período de teste gratuito</strong> foi ativado com sucesso!</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #333;">Detalhes do seu teste:</h3>
            <p>Início: <strong>Hoje</strong></p>
            <p>Término: <strong>{data_fim}</strong></p>
            <p>Durante este período, você tem acesso completo a todas as funcionalidades do Planner Organiza.</p>
        </div>
        
        <p>A partir de agora, você pode explorar todas as funcionalidades incríveis do Planner Organiza:</p>
        
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Gerenciamento ilimitado de propostas
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Gerenciamento ilimitado de clientes
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Relatórios personalizados
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Exportação de dados
            </li>
            <li style="margin-bottom: 10px; padding-left: 25px; position: relative;">
                <span style="position: absolute; left: 0; color: #4CAF50;">✓</span> 
                Suporte prioritário
            </li>
        </ul>
        
        <p>Quando seu período de teste terminar, você será convidado a escolher um de nossos planos para continuar usando o sistema.</p>
        
        <p>Para verificar o status do seu teste e ver os planos disponíveis, visite <a href="https://www.plannerorganiza.com.br/minha_assinatura" style="color: #1E88E5; text-decoration: none;">Minha Assinatura</a>.</p>
        
        <p>Se precisar de qualquer assistência, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você iniciou um teste gratuito do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar e-mail de lembrete de fim de teste
def enviar_lembrete_fim_teste(destinatario, nome, data_fim):
    """
    Envia um e-mail lembrando o usuário que o período de teste está prestes a terminar
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        data_fim: Data de término do período de teste
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = "Seu teste gratuito termina amanhã - Escolha seu plano agora!"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #FF9800; text-align: center;">Seu teste gratuito está terminando!</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Gostaríamos de lembrá-lo que seu <strong>período de teste gratuito</strong> do Planner Organiza termina <strong>amanhã</strong> ({data_fim}).</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #333;">Não perca o acesso às funcionalidades!</h3>
            <p>Para continuar usando o Planner Organiza sem interrupções, escolha um de nossos planos:</p>
            <ul>
                <li><strong>Plano Mensal</strong> - Flexibilidade para cancelar a qualquer momento</li>
                <li><strong>Plano Anual</strong> - Economia de 20% em relação ao plano mensal</li>
                <li><strong>Plano Vitalício</strong> - Pagamento único, acesso para sempre</li>
            </ul>
        </div>
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="https://www.plannerorganiza.com.br/planos" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">ESCOLHER MEU PLANO</a>
        </p>
        
        <p>Se você estiver gostando da sua experiência e quiser continuar usando todas as funcionalidades, este é o momento perfeito para escolher o plano que melhor atende às suas necessidades.</p>
        
        <p>Se tiver alguma dúvida ou precisar de assistência para escolher o plano ideal, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você está usando o período de teste gratuito do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar notificação de falha no pagamento
def enviar_notificacao_falha_pagamento(destinatario, nome, plano):
    """
    Envia um e-mail de notificação de falha no pagamento
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        plano: Nome do plano
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = "Ação Necessária: Problema com o Pagamento da sua Assinatura"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #F44336; text-align: center;">Problema com seu Pagamento</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Identificamos um problema com o processamento do pagamento da sua assinatura do <strong>Plano {plano}</strong>.</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #333;">O que fazer agora?</h3>
            <p>Para garantir que você continue tendo acesso a todas as funcionalidades do Planner Organiza sem interrupções, siga os passos abaixo:</p>
            <ol style="margin-bottom: 0;">
                <li>Acesse <a href="https://www.plannerorganiza.com.br/minha_assinatura" style="color: #1E88E5; text-decoration: none;">Minha Assinatura</a></li>
                <li>Clique em "Gerenciar Método de Pagamento"</li>
                <li>Verifique se os dados do seu cartão estão corretos ou adicione um novo método de pagamento</li>
            </ol>
        </div>
        
        <p>Tentaremos processar o pagamento novamente nos próximos dias. Se não conseguirmos processar o pagamento, sua assinatura poderá ser suspensa.</p>
        
        <p>Se precisar de qualquer assistência, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você é cliente do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Função para enviar boas-vindas após período de teste
def enviar_boas_vindas_apos_teste(destinatario, nome):
    """
    Envia um e-mail de boas-vindas após o período de teste
    
    Args:
        destinatario: E-mail do destinatário
        nome: Nome do destinatário
        
    Returns:
        dict: Resultado da operação
    """
    # Definir assunto
    assunto = "Aproveite ao Máximo o Planner Organiza!"
    
    # Definir conteúdo HTML
    conteudo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://www.plannerorganiza.com.br/static/logo.png" alt="Planner Organiza" style="max-width: 200px;">
        </div>
        
        <h1 style="color: #1E88E5; text-align: center;">Bem-vindo ao Planner Organiza!</h1>
        
        <p>Olá, <strong>{nome}</strong>!</p>
        
        <p>Você já está usando o Planner Organiza há alguns dias e esperamos que esteja aproveitando a experiência. Aqui estão algumas dicas para tirar o máximo proveito do sistema:</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #333;">Recursos Imperdíveis:</h3>
            <ul style="margin-bottom: 0; padding-left: 20px;">
                <li><strong>Gerenciamento de Propostas:</strong> Crie e acompanhe propostas de serviços de forma organizada.</li>
                <li><strong>Relatórios Detalhados:</strong> Gere relatórios profissionais para seus clientes.</li>
                <li><strong>Acompanhamento Financeiro:</strong> Monitore receitas e despesas relacionadas aos seus projetos.</li>
                <li><strong>Painel de Controle:</strong> Visualize métricas importantes para seu negócio.</li>
            </ul>
        </div>
        
        <p>Se tiver alguma dúvida ou precisar de assistência, não hesite em entrar em contato conosco respondendo a este e-mail ou através do nosso suporte em <a href="mailto:contato@plannerorganiza.com.br" style="color: #1E88E5; text-decoration: none;">contato@plannerorganiza.com.br</a>.</p>
        
        <p>Atenciosamente,<br>
        Equipe Planner Organiza</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #666;">
            <p>Este e-mail foi enviado para {destinatario} porque você é cliente do Planner Organiza.</p>
            <p>© {datetime.now().year} Planner Organiza - Todos os direitos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Enviar e-mail
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        conteudo_html=conteudo_html
    )

# Testar o envio de e-mail se executado diretamente
if __name__ == "__main__":
    # Testar se a API Key está configurada
    if not SENDGRID_API_KEY:
        print("API Key do SendGrid não configurada. Configure a variável de ambiente SENDGRID_API_KEY.")
    else:
        # Testar o envio de e-mail
        destinatario = input("Digite o e-mail de teste: ")
        
        if destinatario:
            resultado = enviar_confirmacao_assinatura(
                destinatario=destinatario,
                nome="Usuário de Teste",
                plano="Mensal"
            )
            
            print(f"Resultado: {resultado}")