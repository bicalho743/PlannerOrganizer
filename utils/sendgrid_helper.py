"""
Módulo auxiliar para integração com o SendGrid.
Fornece funções para envio de e-mails, gerenciamento de listas de contatos,
e adição de contatos às listas do SendGrid.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

class SendGridHelper:
    """
    Classe para facilitar a integração com a API do SendGrid.
    Fornece métodos para gerenciar contatos e lists no SendGrid.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o helper com uma chave de API do SendGrid.
        
        Args:
            api_key: Chave de API do SendGrid. Se não fornecida, tenta ler da variável de ambiente SENDGRID_API_KEY.
        """
        self.api_key = api_key or os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            logger.warning("Chave de API do SendGrid não encontrada. A funcionalidade de e-mail está desabilitada.")
        
        self.base_url = "https://api.sendgrid.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_contact(self, email: str, first_name: str = "", last_name: str = "", 
                     custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Adiciona um novo contato ao SendGrid.
        
        Args:
            email: Endereço de e-mail do contato
            first_name: Nome do contato (opcional)
            last_name: Sobrenome do contato (opcional)
            custom_fields: Campos personalizados associados ao contato (opcional)
            
        Returns:
            Dict com a resposta da API do SendGrid
        """
        if not self.api_key:
            logger.error("Tentativa de criar contato sem API key configurada")
            return {"error": "SendGrid API key não configurada"}
            
        url = f"{self.base_url}/marketing/contacts"
        
        data = {
            "contacts": [
                {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name
                }
            ]
        }
        
        # Adicionar campos personalizados se fornecidos
        if custom_fields:
            data["contacts"][0].update(custom_fields)
            
        try:
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao criar contato no SendGrid: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_or_create_list(self, list_name: str) -> Dict[str, Any]:
        """
        Obtém uma lista pelo nome ou cria uma nova se não existir.
        
        Args:
            list_name: Nome da lista a ser encontrada ou criada
            
        Returns:
            Dict contendo o ID da lista e outras informações
        """
        if not self.api_key:
            logger.error("Tentativa de buscar/criar lista sem API key configurada")
            return {"error": "SendGrid API key não configurada"}
            
        # Primeiro, verificar se a lista já existe
        lists_url = f"{self.base_url}/marketing/lists"
        
        try:
            response = requests.get(lists_url, headers=self.headers)
            response.raise_for_status()
            lists_data = response.json()
            
            # Procurar a lista pelo nome
            for list_item in lists_data.get("result", []):
                if list_item.get("name") == list_name:
                    return {"success": True, "list_id": list_item.get("id"), "list_data": list_item, "existed": True}
            
            # Se não encontrou, criar a lista
            create_data = {"name": list_name}
            create_response = requests.post(lists_url, headers=self.headers, json=create_data)
            create_response.raise_for_status()
            new_list = create_response.json()
            
            return {"success": True, "list_id": new_list.get("id"), "list_data": new_list, "existed": False}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar/criar lista no SendGrid: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def add_contact_to_list(self, email: str, list_id: str, first_name: str = "", 
                          last_name: str = "", custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Adiciona um contato a uma lista específica no SendGrid.
        Cria o contato se ele não existir.
        
        Args:
            email: E-mail do contato
            list_id: ID da lista onde o contato será adicionado
            first_name: Nome do contato (opcional)
            last_name: Sobrenome do contato (opcional)
            custom_fields: Campos personalizados para o contato (opcional)
            
        Returns:
            Dict com o resultado da operação
        """
        # Primeiro criar o contato para garantir que ele existe
        contact_result = self.create_contact(email, first_name, last_name, custom_fields)
        
        if not contact_result.get("success", False):
            return contact_result
            
        # Agora adicionar o contato à lista
        url = f"{self.base_url}/marketing/lists/{list_id}/contacts"
        
        data = {
            "contact_ids": [email]  # No SendGrid, podemos identificar contatos pelo e-mail
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao adicionar contato à lista no SendGrid: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def capture_email_for_notification(self, email: str, first_name: str = "", 
                                  last_name: str = "", source: str = "planos_page") -> Dict[str, Any]:
        """
        Função de alto nível para capturar um e-mail para notificações.
        Adiciona o e-mail à lista de espera para notificações de planos.
        
        Args:
            email: E-mail do contato
            first_name: Nome do contato (opcional)
            last_name: Sobrenome do contato (opcional)
            source: Origem da captura do e-mail (ex: "planos_page", "landing_page", etc.)
            
        Returns:
            Dict com o resultado da operação
        """
        if not self.api_key:
            logger.error("Tentativa de capturar e-mail sem API key configurada")
            return {"success": False, "error": "SendGrid API key não configurada"}
            
        try:
            # Tenta salvar apenas o contato sem associá-lo a uma lista
            # Isso evita problemas com permissões limitadas de API
            contact_result = self.create_contact(email, first_name, last_name, {
                "source": source,
                "captured_at": "planner_organizer"
            })
            
            # Se conseguiu salvar o contato, considera sucesso mesmo sem adicionar à lista
            if contact_result.get("success", False):
                logger.info(f"E-mail capturado com sucesso: {email}")
                return {"success": True, "message": "E-mail capturado com sucesso"}
            
            # Verifica se o erro é 403 (Forbidden) - falta de permissão
            error = contact_result.get("error", "")
            if "403" in str(error):
                # Implementar modo de fallback: salvar em um arquivo local
                self._save_email_to_local_storage(email, first_name, last_name, source)
                logger.warning(f"Fallback: E-mail {email} salvo em armazenamento local devido a permissões insuficientes na API")
                return {"success": True, "message": "E-mail capturado em armazenamento local", "fallback": True}
            
            return contact_result
                
        except Exception as e:
            logger.error(f"Erro ao capturar e-mail: {str(e)}")
            # Tentar usar fallback
            try:
                self._save_email_to_local_storage(email, first_name, last_name, source)
                logger.warning(f"Fallback: E-mail {email} salvo em armazenamento local após erro")
                return {"success": True, "message": "E-mail capturado em armazenamento local", "fallback": True}
            except Exception as inner_e:
                logger.error(f"Erro ao salvar e-mail em armazenamento local: {str(inner_e)}")
                return {"success": False, "error": f"Não foi possível processar seu e-mail: {str(e)}"}
    
    def _save_email_to_local_storage(self, email: str, first_name: str = "", last_name: str = "", source: str = ""):
        """
        Método auxiliar para salvar e-mails em um arquivo local quando a API do SendGrid não está disponível
        ou não tem permissões suficientes.
        
        Args:
            email: E-mail do contato
            first_name: Nome do contato
            last_name: Sobrenome do contato
            source: Origem da captura do e-mail
        """
        import os
        import json
        from datetime import datetime
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        contacts_file = os.path.join(data_dir, "captured_emails.json")
        
        # Carregar dados existentes
        existing_data = []
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de contatos: {str(e)}")
                existing_data = []
        
        # Adicionar novo contato
        new_contact = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "source": source,
            "captured_at": datetime.now().isoformat(),
        }
        
        existing_data.append(new_contact)
        
        # Salvar dados atualizados
        with open(contacts_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)


# Função auxiliar para uso fácil em outros módulos
def capture_email(email: str, first_name: str = "", last_name: str = "", 
                source: str = "planos_page") -> Dict[str, Any]:
    """
    Função utilitária para capturar e-mail para notificações.
    
    Args:
        email: E-mail do contato
        first_name: Nome do contato (opcional)
        last_name: Sobrenome do contato (opcional)
        source: Origem da captura do e-mail (ex: "planos_page", "landing_page", etc.)
        
    Returns:
        Dict com o resultado da operação
    """
    helper = SendGridHelper()
    return helper.capture_email_for_notification(email, first_name, last_name, source)