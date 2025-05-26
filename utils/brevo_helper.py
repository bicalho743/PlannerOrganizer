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
# A chave usada no exemplo Node.js
api_key = os.getenv("BREVO_API_KEY", "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")
# Forçar o uso da lista 7, independente do que estiver nas variáveis de ambiente
lista_brevo_id = "7"  # ID da lista do Brevo onde os e-mails serão armazenados
EMAIL_REMETENTE = "contato@plannerorganiza.com.br"
NOME_REMETENTE = "Equipe Planner Organizer"

# Imprimir configurações na inicialização para facilitar debug
logger.info(f"🔑 Brevo API configurada. Lista ID: {lista_brevo_id}")
logger.info(f"📧 E-mail remetente configurado: {EMAIL_REMETENTE}")

def adicionar_contato_brevo(email, nome_completo=""):
    """
    Adiciona um contato à lista do Brevo e garante que esteja na lista 7.
    Se o contato já existir, atualiza seus dados e o adiciona à lista.
    
    Args:
        email (str): Email do contato
        nome_completo (str): Nome completo do contato
        
    Returns:
        dict: Resultado da operação com status e mensagens
    """
    # Log detalhado para diagnóstico
    logger.info(f"⭐ INICIANDO ADIÇÃO DE CONTATO: {email}, nome: {nome_completo}")
    
    # Verificar se o email é válido
    if not email or '@' not in email:
        logger.error(f"❌ E-mail inválido: {email}")
        return {
            "success": False,
            "message": "Email inválido."
        }
    
    # Verificar se temos a API Key configurada
    if not api_key:
        logger.warning("❌ Chave da API Brevo não encontrada nas variáveis de ambiente.")
        return salvar_email_localmente(email, nome_completo)
    
    # Exibir versão parcial da chave para debug (sem mostrar a chave completa)
    masked_key = api_key[:8] + "..." + api_key[-4:]
    logger.info(f"🔑 Usando API KEY: {masked_key}")
    
    # Configuração da API
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # Fixa o ID da lista como 7 para a lista "Leads Planner Organizer"
    list_id = 7
    logger.info(f"📋 Lista alvo: ID {list_id}")
    
    # Dividir nome e sobrenome
    partes_nome = nome_completo.split(' ', 1) if nome_completo else ["", ""]
    primeiro_nome = partes_nome[0] if partes_nome else ""
    sobrenome = partes_nome[1] if len(partes_nome) > 1 else ""
    
    # Preparar atributos do contato - usando o formato do exemplo Node.js
    atributos = {
        "NOME": nome_completo,
        "FIRSTNAME": primeiro_nome,
        "LASTNAME": sobrenome,
        "SOURCE": "Planner Organizer",
        "ORIGEM": "Landing Page Planner Organizer"
    }
    
    logger.info(f"📝 Atributos configurados: {atributos}")
    
    # ABORDAGEM 1: USANDO OBJETO CreateContact
    try:
        # Criar objeto de contato do Brevo
        create_contact = sib_api_v3_sdk.CreateContact()
        
        # Configurar os dados do contato
        create_contact.email = email
        create_contact.attributes = atributos
        create_contact.list_ids = [list_id]  # Sempre adicionar à lista 7
        
        # Log dos dados que serão enviados
        logger.info(f"📤 Enviando dados para API Brevo: email={email}, list_ids=[{list_id}]")
        
        # Tenta criar o contato via método do SDK
        api_instance.create_contact(create_contact)
        logger.info(f"✅ Novo contato {email} adicionado com sucesso na lista {list_id} do Brevo.")
        
        # Verificar se o contato foi adicionado à lista correta
        try:
            # Busca o contato para confirmar
            contato_info = api_instance.get_contact_info(email)
            lista_ids = contato_info.list_ids if hasattr(contato_info, 'list_ids') else []
            
            if list_id in lista_ids:
                logger.info(f"✅ Confirmado: contato {email} está na lista {list_id}.")
            else:
                logger.warning(f"⚠️ Contato adicionado mas não está na lista {list_id}. Listas atuais: {lista_ids}")
                # Tenta adicionar explicitamente à lista 7
                api_instance.add_contact_to_list(list_id, {'emails': [email]})
                logger.info(f"🔄 Adicionado explicitamente o contato {email} à lista {list_id}.")
        except Exception as check_error:
            logger.error(f"❌ Erro ao verificar se contato foi adicionado à lista: {check_error}")
        
        return {
            "success": True,
            "message": f"Obrigado! Seu e-mail {email} foi registrado com sucesso.",
            "fallback": False
        }
    except ApiException as e:
        # Verificar se é erro de contato duplicado (já existe)
        erro_duplicado = False
        if hasattr(e, 'body'):
            body_str = str(e.body).lower()
            erro_duplicado = 'duplicate_parameter' in body_str or 'contact already exist' in body_str or 'already exists' in body_str
            
        if erro_duplicado:
            logger.info(f"⚠️ Contato {email} já existe no Brevo. Tentando atualizar...")
            
            try:
                # Busca o contato existente
                contato_existente = api_instance.get_contact_info(email)
                
                # Verificar se já está na lista 7
                lista_ids_atuais = contato_existente.list_ids if hasattr(contato_existente, 'list_ids') else []
                
                if list_id not in lista_ids_atuais:
                    # Adicionar à lista 7 se ainda não estiver
                    logger.info(f"📝 Adicionando contato existente {email} à lista {list_id}...")
                    
                    # Adicionar o contato à lista
                    try:
                        api_instance.add_contact_to_list(list_id, {'emails': [email]})
                        logger.info(f"✅ Contato {email} adicionado com sucesso à lista {list_id}.")
                    except ApiException as add_error:
                        logger.error(f"❌ Erro ao adicionar contato à lista: {add_error}")
                else:
                    logger.info(f"✓ Contato {email} já está na lista {list_id}.")
                
                # Atualiza os atributos do contato mesmo assim para manter os dados atualizados
                update_data = {
                    "attributes": atributos
                }
                logger.info(f"📝 Atualizando atributos do contato: {atributos}")
                api_instance.update_contact(email, update_data)
                logger.info(f"✅ Atributos do contato {email} atualizados com sucesso.")
                
                return {
                    "success": True,
                    "message": f"Seu e-mail {email} já estava registrado e foi atualizado com sucesso.",
                    "fallback": False
                }
                
            except ApiException as update_error:
                logger.error(f"❌ Erro ao atualizar contato existente: {update_error}")
                return salvar_email_localmente(email, nome_completo)
        else:
            # Outro tipo de erro
            logger.error(f"❌ Erro ao adicionar e-mail na lista do Brevo: {e}")
            # Fallback: salvar localmente em caso de erro
            return salvar_email_localmente(email, nome_completo)
    except Exception as e:
        logger.error(f"❌ Erro não tratado ao adicionar contato: {e}")
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
        "message": f"Obrigado! Seu e-mail {email} foi registrado e será adicionado à nossa lista de contatos do Brevo. Entraremos em contato assim que nossos planos estiverem disponíveis.",
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