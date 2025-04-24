"""
Módulo de autenticação com Firebase
"""
import streamlit as st
import pyrebase
import json
from datetime import datetime, timedelta
from utils.firebase_config import FIREBASE_CONFIG, AUTH_COOKIE_NAME, TOKEN_EXPIRY

class FirebaseAuth:
    """
    Classe para gerenciar autenticação com Firebase
    """
    def __init__(self):
        self.firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        self.auth = self.firebase.auth()
        self.db = self.firebase.database()
    
    def login(self, email, password):
        """
        Realiza login no Firebase
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            dict: Informações do usuário autenticado ou erro
        """
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            # Obter informações adicionais do usuário
            user_info = self.auth.get_account_info(user['idToken'])
            
            # Criar objeto de usuário para armazenar na sessão
            session_user = {
                'localId': user['localId'],
                'email': user['email'],
                'idToken': user['idToken'],
                'refreshToken': user['refreshToken'],
                'expiresIn': user['expiresIn'],
                'registered': user.get('registered', True),
                'last_login': datetime.now().isoformat(),
                'expiry': (datetime.now() + timedelta(seconds=TOKEN_EXPIRY)).isoformat()
            }
            
            # Armazenar na sessão
            st.session_state.user = session_user
            st.session_state.authenticated = True
            
            # Tentar carregar o perfil completo do usuário do Realtime Database
            user_profile = None
            try:
                # Buscar dados do perfil no banco de dados do Firebase
                user_profile = self.db.child("users").child(user['localId']).get().val()
                print(f"Perfil encontrado no Firebase: {user_profile}")
            except Exception as profile_error:
                print(f"Erro ao carregar perfil do Firebase: {str(profile_error)}")
            
            # Inicializar dados do usuário com valores padrão
            usuario_data = {
                'email': user['email'],
                'nome': user['email'].split('@')[0].title(),  # Fallback para nome a partir do email
                'telefone': '',  # Valor padrão
                'empresa': 'Planner Organizer',  # Valor padrão
                'role': 'user'  # Papel padrão
            }
            
            # Se encontrou perfil no Firebase, atualizar com dados reais
            if user_profile and isinstance(user_profile, dict):
                # Atualizar nome se disponível no perfil
                if 'name' in user_profile and user_profile['name']:
                    usuario_data['nome'] = user_profile['name']
                
                # Atualizar outros campos que possam existir no perfil
                for field in ['telefone', 'empresa', 'instagram', 'website']:
                    if field in user_profile and user_profile[field]:
                        usuario_data[field] = user_profile[field]
                
                # Verificar se há dados adicionais
                if 'profile' in user_profile and isinstance(user_profile['profile'], dict):
                    for field, value in user_profile['profile'].items():
                        if value:  # Adicionar apenas se tiver valor
                            usuario_data[field] = value
            
            # Verificar também se há displayName nos dados da conta
            if 'users' in user_info and len(user_info['users']) > 0:
                user_data = user_info['users'][0]
                if 'displayName' in user_data and user_data['displayName']:
                    usuario_data['nome'] = user_data['displayName']
            
            # Atualizar a sessão com os dados enriquecidos do usuário
            st.session_state.usuario = usuario_data
            
            # Tentar carregar perfil do banco de dados PostgreSQL se existir
            try:
                from utils.database import Database
                if 'db' in st.session_state:
                    db = st.session_state.db
                    # Verificar se existe método para carregar perfil
                    if hasattr(db, 'get_perfil_by_email'):
                        db_profile = db.get_perfil_by_email(email)
                        if db_profile:
                            print(f"Perfil encontrado no PostgreSQL: {db_profile}")
                            # Atualizar dados com o perfil do PostgreSQL
                            for field, value in db_profile.items():
                                if value:  # Adicionar apenas se tiver valor
                                    usuario_data[field] = value
                            # Atualizar sessão novamente
                            st.session_state.usuario = usuario_data
            except Exception as db_error:
                print(f"Erro ao carregar perfil do PostgreSQL: {str(db_error)}")
            
            print(f"Login realizado com sucesso. Dados do usuário na sessão: {st.session_state.usuario}")
            
            return {'success': True, 'user': session_user}
        
        except Exception as e:
            error_msg = str(e)
            # Verificar tipo de erro para mensagem mais amigável
            if "INVALID_PASSWORD" in error_msg:
                error_msg = "Senha incorreta."
            elif "EMAIL_NOT_FOUND" in error_msg:
                error_msg = "Email não cadastrado."
            elif "INVALID_EMAIL" in error_msg:
                error_msg = "Formato de email inválido."
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_msg:
                error_msg = "Muitas tentativas. Tente novamente mais tarde."
            
            return {'success': False, 'error': error_msg}
    
    def register(self, email, password, name=""):
        """
        Registra um novo usuário no Firebase
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            name: Nome do usuário (opcional)
            
        Returns:
            dict: Informações do usuário registrado ou erro
        """
        try:
            # Criar usuário no Firebase Auth
            user = self.auth.create_user_with_email_and_password(email, password)
            
            # Criar perfil no Realtime Database
            user_profile = {
                'email': email,
                'name': name,
                'created_at': datetime.now().isoformat(),
                'role': 'user'  # Papel padrão
            }
            
            # Salvar perfil no banco
            self.db.child("users").child(user['localId']).set(user_profile)
            
            # Já fazer login após registro bem-sucedido
            return self.login(email, password)
        
        except Exception as e:
            error_msg = str(e)
            # Verificar tipo de erro para mensagem mais amigável
            if "EMAIL_EXISTS" in error_msg:
                error_msg = "Este email já está cadastrado."
            elif "WEAK_PASSWORD" in error_msg:
                error_msg = "A senha deve ter pelo menos 6 caracteres."
            elif "INVALID_EMAIL" in error_msg:
                error_msg = "Formato de email inválido."
            
            return {'success': False, 'error': error_msg}
    
    def logout(self):
        """
        Realiza logout do usuário atual
        
        Returns:
            dict: Status da operação
        """
        try:
            # Limpar dados de sessão
            if 'user' in st.session_state:
                del st.session_state.user
                
            if 'usuario' in st.session_state:
                del st.session_state.usuario
            
            st.session_state.authenticated = False
            print("Logout realizado. Sessão limpa.")
            
            return {'success': True}
        except Exception as e:
            print(f"Erro ao realizar logout: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def reset_password(self, email):
        """
        Envia email para redefinição de senha
        
        Args:
            email: Email do usuário
            
        Returns:
            dict: Status da operação
        """
        try:
            print(f"Tentando enviar email de redefinição para: {email}")
            
            # Verificar se o email existe no Firebase
            try:
                # Esta operação vai falhar se o email não existir
                user_methods = self.auth.get_user_by_email(email)
                print(f"Usuário encontrado: {user_methods}")
            except Exception as user_error:
                print(f"Erro ao buscar usuário: {user_error}")
                # Se não encontrar o usuário, retornar erro apropriado
                if "EMAIL_NOT_FOUND" in str(user_error) or "INVALID_EMAIL" in str(user_error):
                    return {'success': False, 'error': "Email não cadastrado."}
                    
            # Tentar enviar o email de redefinição
            result = self.auth.send_password_reset_email(email)
            print(f"Resultado do envio: {result}")
            
            # Verificar se houve algum erro no envio
            if result is not None and isinstance(result, dict) and 'error' in result:
                print(f"Erro no envio: {result['error']}")
                return {'success': False, 'error': f"Erro ao enviar email: {result['error']}"}
                
            # Se chegou aqui, o email foi enviado com sucesso
            print(f"Email enviado com sucesso para {email}")
            return {'success': True, 'message': 'Email de redefinição enviado. Verifique sua caixa de entrada e pasta de spam.'}
        except Exception as e:
            error_msg = str(e)
            print(f"Exceção ao enviar email de redefinição: {error_msg}")
            
            # Verificar tipo de erro para mensagem mais amigável
            if "EMAIL_NOT_FOUND" in error_msg:
                error_msg = "Email não cadastrado."
            elif "INVALID_EMAIL" in error_msg:
                error_msg = "Formato de email inválido."
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_msg:
                error_msg = "Muitas tentativas. Tente novamente mais tarde."
            elif "USER_DISABLED" in error_msg:
                error_msg = "Esta conta foi desativada. Entre em contato com o suporte."
                
            return {'success': False, 'error': error_msg}
    
    def is_authenticated(self):
        """
        Verifica se o usuário atual está autenticado
        
        Returns:
            bool: True se autenticado, False caso contrário
        """
        # Implementação básica baseada na sessão
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """
        Retorna o usuário atualmente autenticado
        
        Returns:
            dict: Informações do usuário ou None se não autenticado
        """
        if not self.is_authenticated():
            return None
        
        return st.session_state.get('user', None)

# Inicializar o objeto de autenticação
firebase_auth = FirebaseAuth()