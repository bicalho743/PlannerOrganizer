import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
import json
import logging
import base64
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURAÇÕES GERAIS DO BREVO
api_key = os.getenv("BREVO_API_KEY", "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")
lista_brevo_id = os.getenv("BREVO_LIST_ID", "7")  # ID da lista do Brevo onde os e-mails serão armazenados
EMAIL_REMETENTE = "contato@plannerorganizer.com.br"
NOME_REMETENTE = "Equipe Planner Organizer"

def adicionar_contato_brevo(email, nome_completo=""):
    """
    Adiciona um contato à lista do Brevo.
    
    Args:
        email (str): Email do contato
        nome_completo (str): Nome completo do contato
        
    Returns:
        dict: Resultado da operação com status e mensagens
    """
    # Verificar se o email é válido
    if not email or '@' not in email:
        return {
            "success": False,
            "message": "Email inválido."
        }
    
    # Verificar se temos a API Key configurada
    if not api_key:
        logger.warning("Chave da API Brevo não encontrada nas variáveis de ambiente.")
        return salvar_email_localmente(email, nome_completo)
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # Dados do contato a ser adicionado
    contato = {
        "email": email,
        "attributes": {"NOME": nome_completo},
    }
    
    # Adicionar à lista específica se configurada
    if lista_brevo_id:
        try:
            # Tentar extrair o número do ID (remover caracteres como '#')
            cleaned_id = ''.join(c for c in lista_brevo_id if c.isdigit())
            if cleaned_id:
                list_id = int(cleaned_id)
                contato["listIds"] = [list_id]
                logger.info(f"Usando ID da lista Brevo: {list_id} (original: '{lista_brevo_id}')")
            else:
                logger.warning(f"BREVO_LIST_ID não contém números: '{lista_brevo_id}'. Não usando lista específica.")
        except (ValueError, TypeError):
            # Se não for possível converter, registrar um erro mas continuar
            logger.error(f"BREVO_LIST_ID inválido após limpeza: '{lista_brevo_id}'. Deve ser possível extrair um número.")
            # Não usar listIds neste caso, apenas adicionar o contato
    
    try:
        api_instance.create_contact(contato)
        logger.info(f"✅ E-mail {email} adicionado com sucesso na lista do Brevo.")
        return {
            "success": True,
            "message": f"Obrigado! Seu e-mail {email} foi registrado com sucesso.",
            "fallback": False
        }
    except ApiException as e:
        logger.error(f"❌ Erro ao adicionar e-mail na lista do Brevo: {e}")
        # Fallback: salvar localmente em caso de erro
        return salvar_email_localmente(email, nome_completo)

# Função simplificada para enviar o manual por email
def enviar_manual_email(destinatario_email, destinatario_nome="Novo Cliente"):
    """
    Envia o Manual do Sistema via email usando o Brevo.
    Função simplificada que usa valores padrão para assunto e mensagem.
    
    Args:
        destinatario_email (str): Email do destinatário
        destinatario_nome (str): Nome do destinatário
        
    Returns:
        dict: Resultado da operação
    """
    # Localizar o arquivo do manual
    manual_path = None
    possibilidades = [
        os.path.join(os.getcwd(), "pdfs", "manual_sistema.pdf"),
        os.path.join(os.getcwd(), "pdfs", "Manual_Planner_Organizer.pdf"),
        os.path.join(os.getcwd(), "Manual_Planner_Organizer.pdf"),
        os.path.join(os.getcwd(), "manual_sistema.pdf")
    ]
    
    for caminho in possibilidades:
        if os.path.exists(caminho):
            manual_path = caminho
            break
    
    if not manual_path:
        return {
            "success": False,
            "message": "Manual do sistema não encontrado."
        }
    
    mensagem_html = f"""
    <h2>Obrigado por se cadastrar!</h2>
    <p>Olá <strong>{destinatario_nome}</strong>,</p>
    <p>Estamos felizes em tê-lo conosco! Como prometido, aqui está o seu manual em anexo.</p>
    <p>Caso tenha dúvidas, estamos à disposição.</p>
    <p>Atenciosamente,<br>Equipe Planner Organizer</p>
    """
    
    # Chamar a função principal para enviar o email
    return enviar_email_brevo(
        destinatario_email=destinatario_email,
        destinatario_nome=destinatario_nome,
        assunto="Manual do Sistema Planner Organizer",
        mensagem_html=mensagem_html,
        anexo=manual_path
    )

def enviar_email_brevo(destinatario_email, destinatario_nome, assunto, mensagem_html, anexo=None):
    """
    Envia um e-mail transacional via Brevo.
    
    Args:
        destinatario_email (str): E-mail do destinatário
        destinatario_nome (str): Nome do destinatário
        assunto (str): Assunto do e-mail
        mensagem_html (str): Conteúdo HTML do e-mail
        anexo (str, opcional): Caminho para o arquivo anexo
        
    Returns:
        dict: Resultado da operação
    """
    if not api_key:
        return {
            "success": False,
            "message": "Chave da API Brevo não configurada."
        }
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": destinatario_email, "name": destinatario_nome}],
        sender={"email": EMAIL_REMETENTE, "name": NOME_REMETENTE},
        subject=assunto,
        html_content=mensagem_html
    )
    
    # Adicionar anexo se fornecido
    if anexo and os.path.exists(anexo):
        try:
            with open(anexo, "rb") as f:
                content = base64.b64encode(f.read()).decode('utf-8')
                email.attachment = [
                    {
                        "content": content,
                        "name": os.path.basename(anexo)
                    }
                ]
        except Exception as e:
            logger.error(f"Erro ao ler o anexo {anexo}: {e}")
    
    try:
        api_response = api_instance.send_transac_email(email)
        logger.info(f"✅ E-mail enviado com sucesso para {destinatario_email}!")
        return {
            "success": True,
            "message": "E-mail enviado com sucesso!"
        }
    except ApiException as e:
        logger.error(f"❌ Erro ao enviar o e-mail para {destinatario_email}: {e}")
        return {
            "success": False,
            "message": f"Erro ao enviar e-mail: {str(e)}"
        }

def obter_listas_brevo():
    """
    Obtém as listas disponíveis no Brevo.
    
    Returns:
        list: Lista de dicionários com id e nome das listas
    """
    if not api_key:
        logger.warning("Chave da API Brevo não configurada.")
        return []
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    try:
        # Fazer chamada à API para obter listas
        result = api_instance.get_lists(limit=50)
        
        # Formatar resultado
        listas = []
        for lista in result.lists:
            listas.append({
                "id": lista.id,
                "name": lista.name
            })
        return listas
    except ApiException as e:
        logger.error(f"Erro ao obter listas do Brevo: {e}")
        return []

def salvar_email_localmente(email, nome_completo=""):
    """
    Salva o email e detalhes do usuário localmente quando a API não está disponível.
    
    Args:
        email (str): Email do contato
        nome_completo (str): Nome completo do contato
        
    Returns:
        dict: Resultado da operação
    """
    arquivo = os.path.join("data", "captured_emails.json")
    
    # Dividir nome e sobrenome se fornecido
    partes_nome = nome_completo.split(' ', 1) if nome_completo else ["", ""]
    primeiro_nome = partes_nome[0] if partes_nome else ""
    sobrenome = partes_nome[1] if len(partes_nome) > 1 else ""
    
    # Garante que o diretório existe
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    
    # Ler dados existentes se o arquivo existir
    dados = []
    if os.path.exists(arquivo):
        with open(arquivo, 'r') as f:
            try:
                dados = json.load(f)
            except json.JSONDecodeError:
                dados = []
    
    # Adicionar novo registro
    novo_registro = {
        "email": email.lower(),
        "first_name": primeiro_nome,
        "last_name": sobrenome,
        "source": "planos_page_form",
        "captured_at": datetime.now().isoformat()
    }
    
    dados.append(novo_registro)
    
    # Salvar de volta no arquivo
    with open(arquivo, 'w') as f:
        json.dump(dados, f, indent=4)
    
    logger.warning(f"Fallback: E-mail {email} salvo em armazenamento local devido a permissões insuficientes na API")
    
    return {
        "success": True,
        "message": f"Obrigado! Seu e-mail {email} foi salvo em nossa lista local. Entraremos em contato assim que nossos planos estiverem disponíveis.",
        "fallback": True
    }

def exportar_contatos_para_brevo():
    """
    Exporta contatos armazenados localmente para o Brevo quando a API estiver disponível.
    
    Returns:
        dict: Resultado da operação
    """
    arquivo = os.path.join("data", "captured_emails.json")
    
    if not os.path.exists(arquivo):
        return {
            "success": False,
            "message": "Não há contatos locais para exportar."
        }
    
    # Verificar se a API key está configurada
    if not api_key:
        return {
            "success": False,
            "message": "Não foi possível conectar à API do Brevo. Verifique sua chave de API."
        }
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # Ler contatos locais
    with open(arquivo, 'r') as f:
        contatos = json.load(f)
    
    # Estatísticas de exportação
    stats = {
        "total": len(contatos),
        "success": 0,
        "failed": 0
    }
    
    # Processar cada contato
    for contato in contatos:
        try:
            email = contato["email"]
            primeiro_nome = contato.get("first_name", "")
            sobrenome = contato.get("last_name", "")
            nome_completo = f"{primeiro_nome} {sobrenome}".strip()
            
            # Dados do contato para a API
            dados_contato = {
                "email": email,
                "attributes": {"NOME": nome_completo}
            }
            
            # Adicionar à lista específica se configurada
            if lista_brevo_id:
                try:
                    # Tentar extrair o número do ID (remover caracteres como '#')
                    cleaned_id = ''.join(c for c in lista_brevo_id if c.isdigit())
                    if cleaned_id:
                        list_id = int(cleaned_id)
                        dados_contato["listIds"] = [list_id]
                        logger.info(f"Usando ID da lista Brevo: {list_id} (original: '{lista_brevo_id}')")
                    else:
                        logger.warning(f"BREVO_LIST_ID não contém números: '{lista_brevo_id}'. Não usando lista específica.")
                except (ValueError, TypeError):
                    # Se não for possível converter, registrar um erro mas continuar
                    logger.error(f"BREVO_LIST_ID inválido após limpeza: '{lista_brevo_id}'. Deve ser possível extrair um número.")
                    # Não usar listIds neste caso, apenas adicionar o contato
            
            # Enviar para a API
            api_instance.create_contact(dados_contato)
            stats["success"] += 1
            
        except ApiException as e:
            logger.error(f"Erro ao exportar contato {contato.get('email')}: {e}")
            stats["failed"] += 1
    
    # Se todos os contatos foram exportados com sucesso, podemos
    # renomear o arquivo original para backup
    if stats["success"] == stats["total"]:
        backup_file = f"{arquivo}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        os.rename(arquivo, backup_file)
        logger.info(f"Arquivo original renomeado para {backup_file}")
    
    return {
        "success": True,
        "message": f"Exportação concluída. Total: {stats['total']}, Sucesso: {stats['success']}, Falhas: {stats['failed']}",
        "stats": stats
    }