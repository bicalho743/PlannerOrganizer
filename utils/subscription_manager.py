"""
Gerenciador de assinaturas para integração Firebase-Stripe.
Este módulo verifica e gerencia o status de assinatura dos usuários.
"""
import logging
import time
from datetime import datetime
import streamlit as st
import pyrebase
from utils.firebase_config import firebase, db, auth

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Classe para gerenciar assinaturas e planos de usuários"""
    
    def __init__(self):
        self.db = db
        self.auth = auth
        
    def get_user_subscription(self, user_id):
        """
        Obtém os detalhes de assinatura de um usuário do Firebase
        
        Args:
            user_id (str): UID do usuário no Firebase
            
        Returns:
            dict: Dados da assinatura ou None se não encontrada
        """
        if not self.db:
            logger.warning("Firebase não inicializado - modo de demonstração")
            return {
                "status": "active",
                "plan": "demo",
                "demo_mode": True
            }
            
        try:
            # Obter documento do usuário
            user_ref = self.db.child("users").child(user_id)
            user_data = user_ref.get()
            
            if user_data and "subscription" in user_data.val():
                return user_data.val()["subscription"]
            
            # Usuário não tem assinatura
            return None
        except Exception as e:
            logger.error(f"Erro ao obter assinatura: {e}")
            return None
    
    def is_subscription_active(self, user_id):
        """
        Verifica se a assinatura do usuário está ativa
        
        Args:
            user_id (str): UID do usuário no Firebase
            
        Returns:
            bool: True se assinatura ativa, False caso contrário
        """
        # No modo de demonstração, considerar ativo
        if not self.db:
            return True
            
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return False
            
        # Para planos vitalícios, sempre ativo
        if subscription.get("tipo") == "lifetime":
            return True
            
        # Para assinaturas, verificar status atual
        status = subscription.get("status")
        if status == "active":
            # Verificar também a data de expiração
            current_period_end = subscription.get("current_period_end")
            if current_period_end:
                # Converter timestamp para data e comparar com agora
                now = int(time.time())
                return current_period_end > now
                
            # Se não tiver data de expiração, considerar ativo
            return True
        
        return False
    
    def get_trial_days_remaining(self, user_id):
        """
        Calcula dias restantes do período de teste
        
        Args:
            user_id (str): UID do usuário no Firebase
            
        Returns:
            int: Dias restantes ou 0 se não estiver em período de teste
        """
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return 0
            
        trial_end = subscription.get("trial_end")
        if not trial_end:
            return 0
            
        # Calcular dias restantes
        now = int(time.time())
        if trial_end > now:
            return (trial_end - now) // 86400  # Converter segundos para dias
            
        return 0
    
    def get_subscription_details(self, user_id):
        """
        Obtém detalhes formatados da assinatura para exibição
        
        Args:
            user_id (str): UID do usuário no Firebase
            
        Returns:
            dict: Detalhes da assinatura formatados
        """
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return {
                "status": "inactive",
                "plan_name": "Sem plano",
                "is_active": False,
                "expiry_date": None,
                "expiry_formatted": "N/A",
                "trial_days": 0
            }
            
        # Verificar status
        is_active = self.is_subscription_active(user_id)
        
        # Mapear plano para nome amigável
        plan_mapping = {
            "mensal": "Plano Mensal",
            "anual": "Plano Anual",
            "vitalicio": "Acesso Vitalício",
            "demo": "Demonstração"
        }
        
        plan_name = plan_mapping.get(subscription.get("plan"), "Plano Desconhecido")
        
        # Obter data de expiração
        current_period_end = subscription.get("current_period_end")
        expiry_date = None
        expiry_formatted = "N/A"
        
        if current_period_end:
            expiry_date = datetime.fromtimestamp(current_period_end)
            expiry_formatted = expiry_date.strftime("%d/%m/%Y")
            
        # Verificar se é vitalício
        if subscription.get("tipo") == "lifetime":
            expiry_formatted = "Sem expiração (vitalício)"
            
        # Calcular dias restantes de teste
        trial_days = self.get_trial_days_remaining(user_id)
        
        return {
            "status": subscription.get("status", "inactive"),
            "plan_name": plan_name,
            "is_active": is_active,
            "expiry_date": expiry_date,
            "expiry_formatted": expiry_formatted,
            "trial_days": trial_days
        }
    
    def show_subscription_status(self, user_id):
        """
        Exibe o status da assinatura do usuário na interface
        
        Args:
            user_id (str): UID do usuário no Firebase
        """
        details = self.get_subscription_details(user_id)
        
        # Criar UI para status da assinatura
        if details["is_active"]:
            st.sidebar.success(f"✓ {details['plan_name']} Ativo")
            
            # Mostrar informações adicionais
            with st.sidebar.expander("Detalhes da assinatura"):
                st.write(f"**Plano:** {details['plan_name']}")
                st.write(f"**Status:** {details['status'].capitalize()}")
                
                if details["trial_days"] > 0:
                    st.write(f"**Período de teste:** {details['trial_days']} dias restantes")
                
                if "Vitalício" not in details["plan_name"]:
                    st.write(f"**Validade:** {details['expiry_formatted']}")
                    
                    # Adicionar botão para gerenciar assinatura
                    if st.button("Gerenciar assinatura"):
                        # TODO: Implementar link para portal de gerenciamento do Stripe
                        st.info("O portal de gerenciamento será aberto em breve.")
        else:
            # Assinatura inativa
            st.sidebar.warning("Assinatura Inativa")
            
            # Mostrar botão para renovar
            if st.sidebar.button("Renovar assinatura"):
                st.session_state.show_plans = True
                st.rerun()
                
# Criar instância global para uso em várias partes do aplicativo
subscription_manager = SubscriptionManager()