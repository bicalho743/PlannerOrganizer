"""
Configuração do Firebase para autenticação de usuários e armazenamento de dados
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin.exceptions import FirebaseError

# Configuração do Firebase
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com",
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7",
    "measurementId": "G-XQP8M2ZKHZ",
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "https://planner-organizer-68a23.firebaseio.com")
}

# Variável global para o app Firebase Admin
firebase_app = None
db = None

def initialize_firebase():
    """
    Inicializa o Firebase Admin SDK
    """
    global firebase_app, db
    
    if firebase_app:
        return firebase_app, db
        
    try:
        # Tentar inicializar o Firebase Admin SDK
        cred_path = "api/firebase_credentials.json"
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin inicializado com sucesso (credenciais de arquivo)")
        else:
            # Usar variáveis de ambiente como alternativa
            firebase_app = firebase_admin.initialize_app()
            print("Firebase Admin inicializado com sucesso (credenciais padrão)")
            
        # Inicializar Firestore
        db = firestore.client()
        return firebase_app, db
    except Exception as e:
        print(f"Erro ao inicializar Firebase Admin: {e}")
        return None, None

def get_firestore_db():
    """
    Retorna a instância do banco de dados Firestore
    """
    global firebase_app, db
    
    if not firebase_app or not db:
        _, db = initialize_firebase()
    
    return db

def create_user(email, password, display_name=None):
    """
    Cria um novo usuário no Firebase Authentication
    
    Args:
        email: Email do usuário
        password: Senha do usuário
        display_name: Nome de exibição (opcional)
        
    Returns:
        dict: Informações do usuário criado ou erro
    """
    try:
        # Inicializar Firebase se necessário
        _, _ = initialize_firebase()
        
        # Criar usuário
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name or email.split('@')[0],
            email_verified=False
        )
        
        # Criar documento do usuário no Firestore
        if db:
            user_ref = db.collection('users').document(user.uid)
            user_ref.set({
                'email': email,
                'name': display_name or email.split('@')[0],
                'created_at': firestore.SERVER_TIMESTAMP
            })
        
        return {
            "success": True,
            "user_id": user.uid,
            "email": user.email,
            "display_name": user.display_name
        }
    except FirebaseError as e:
        return {
            "success": False,
            "error": str(e),
            "code": e.code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_user_by_id(user_id):
    """
    Obtém informações de um usuário pelo ID
    
    Args:
        user_id: ID do usuário no Firebase
        
    Returns:
        dict: Informações do usuário ou erro
    """
    try:
        # Inicializar Firebase se necessário
        _, _ = initialize_firebase()
        
        # Buscar usuário
        user = auth.get_user(user_id)
        
        # Buscar dados adicionais no Firestore
        user_data = {}
        if db:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
        
        return {
            "success": True,
            "user_id": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "user_data": user_data
        }
    except FirebaseError as e:
        return {
            "success": False,
            "error": str(e),
            "code": e.code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def update_user_data(user_id, data):
    """
    Atualiza dados do usuário no Firestore
    
    Args:
        user_id: ID do usuário no Firebase
        data: Dicionário com os dados a serem atualizados
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Inicializar Firebase se necessário
        _, db = initialize_firebase()
        
        if not db:
            return {"success": False, "error": "Firestore não inicializado"}
        
        # Atualizar dados
        user_ref = db.collection('users').document(user_id)
        user_ref.update(data)
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Inicializar Firebase ao importar o módulo
initialize_firebase()