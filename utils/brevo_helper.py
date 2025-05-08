import os
import json
import logging
from datetime import datetime
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do cliente Brevo
def get_brevo_api_client():
    """
    Configura e retorna o cliente da API do Brevo.
    """
    # Obter a chave da API do ambiente
    api_key = os.environ.get('BREVO_API_KEY')
    
    if not api_key:
        logger.warning("Chave da API Brevo não encontrada nas variáveis de ambiente.")
        return None
    
    # Configurar API key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key
    
    # Criar instância da API
    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    return api_instance

def adicionar_contato_brevo(email, nome_completo="", lista_id=None):
    """
    Adiciona um contato à lista do Brevo.
    
    Args:
        email (str): Email do contato
        nome_completo (str): Nome completo do contato
        lista_id (int, opcional): ID da lista para adicionar o contato
        
    Returns:
        dict: Resultado da operação com status e mensagens
    """
    # Verificar se o email é válido
    if not email or '@' not in email:
        return {
            "success": False,
            "message": "Email inválido."
        }
    
    # Dividir nome e sobrenome se fornecido
    partes_nome = nome_completo.split(' ', 1)
    primeiro_nome = partes_nome[0] if partes_nome else ""
    sobrenome = partes_nome[1] if len(partes_nome) > 1 else ""
    
    # Obter o cliente da API
    api_instance = get_brevo_api_client()
    
    # Se não conseguir configurar o cliente, salvar localmente
    if not api_instance:
        return salvar_email_localmente(email, primeiro_nome, sobrenome)
    
    # Criar objeto de contato
    create_contact = sib_api_v3_sdk.CreateContact(
        email=email,
        attributes={
            "NOME": primeiro_nome,
            "SOBRENOME": sobrenome,
            "ORIGEM": "planos_page_form"
        },
        list_ids=[lista_id] if lista_id else None
    )
    
    try:
        # Fazer a chamada à API para criar contato
        api_instance.create_contact(create_contact)
        return {
            "success": True,
            "message": f"Contato {email} adicionado com sucesso ao Brevo."
        }
    except ApiException as e:
        logger.error(f"Erro ao criar contato no Brevo: {e}")
        # Fallback: salvar localmente em caso de erro
        return salvar_email_localmente(email, primeiro_nome, sobrenome)

def obter_listas_brevo():
    """
    Obtém as listas disponíveis no Brevo.
    
    Returns:
        list: Lista de dicionários com id e nome das listas
    """
    api_instance = get_brevo_api_client()
    
    if not api_instance:
        logger.warning("Cliente Brevo não configurado. Não é possível obter listas.")
        return []
    
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

def salvar_email_localmente(email, primeiro_nome="", sobrenome=""):
    """
    Salva o email e detalhes do usuário localmente quando a API não está disponível.
    
    Args:
        email (str): Email do contato
        primeiro_nome (str): Nome do contato
        sobrenome (str): Sobrenome do contato
        
    Returns:
        dict: Resultado da operação
    """
    arquivo = os.path.join("data", "captured_emails.json")
    nome_completo = f"{primeiro_nome} {sobrenome}".strip()
    
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
    
    # Verificar se o cliente da API está disponível
    api_instance = get_brevo_api_client()
    if not api_instance:
        return {
            "success": False,
            "message": "Não foi possível conectar à API do Brevo. Verifique sua chave de API."
        }
    
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
            
            create_contact = sib_api_v3_sdk.CreateContact(
                email=email,
                attributes={
                    "NOME": primeiro_nome,
                    "SOBRENOME": sobrenome,
                    "ORIGEM": "planos_page_form"
                }
            )
            
            # Chamar API para criar contato
            api_instance.create_contact(create_contact)
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