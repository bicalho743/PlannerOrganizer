"""
Sincronização de clientes entre PostgreSQL e Firebase
Este módulo gerencia a sincronização bidirecional de dados de clientes
entre o banco de dados PostgreSQL e o Firebase Firestore.
"""
import os
import json
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from utils.firebase_config import get_firestore_db, initialize_firebase
import firebase_admin
from firebase_admin import firestore

# Variáveis para conexão com o banco de dados
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = None

def get_engine():
    """
    Retorna uma conexão com o banco de dados PostgreSQL
    
    Returns:
        engine: Objeto de conexão com o banco de dados
    """
    global engine
    if engine is None:
        engine = create_engine(DATABASE_URL)
    return engine

def get_all_clients_from_postgres():
    """
    Obtém todos os clientes do PostgreSQL
    
    Returns:
        DataFrame: Dataframe com todos os clientes
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            query = "SELECT * FROM clientes ORDER BY id"
            clients_df = pd.read_sql(query, conn)
            return clients_df
    except Exception as e:
        print(f"Erro ao obter clientes do PostgreSQL: {e}")
        return pd.DataFrame()

def get_client_by_id(client_id):
    """
    Obtém um cliente específico do PostgreSQL pelo ID
    
    Args:
        client_id: ID do cliente no PostgreSQL
        
    Returns:
        dict: Dados do cliente ou None se não encontrado
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            query = f"SELECT * FROM clientes WHERE id = {client_id}"
            result = conn.execute(text(query)).fetchone()
            if result:
                # Converter para dicionário
                columns = result.keys()
                client_data = {col: result[col] for col in columns}
                return client_data
            return None
    except Exception as e:
        print(f"Erro ao obter cliente {client_id} do PostgreSQL: {e}")
        return None

def get_all_clients_from_firebase():
    """
    Obtém todos os clientes do Firestore
    
    Returns:
        list: Lista de dicionários com dados dos clientes
    """
    try:
        db = get_firestore_db()
        if not db:
            print("Firestore não inicializado")
            return []
            
        clients_ref = db.collection('clients')
        clients = clients_ref.get()
        
        clients_data = []
        for client in clients:
            client_data = client.to_dict()
            client_data['firebase_id'] = client.id  # Adicionar ID do documento
            clients_data.append(client_data)
            
        return clients_data
    except Exception as e:
        print(f"Erro ao obter clientes do Firebase: {e}")
        return []

def get_client_from_firebase_by_postgres_id(postgres_id):
    """
    Busca um cliente no Firebase pelo ID do PostgreSQL
    
    Args:
        postgres_id: ID do cliente no PostgreSQL
        
    Returns:
        dict: Dados do cliente no Firebase ou None se não encontrado
    """
    try:
        db = get_firestore_db()
        if not db:
            return None
            
        # Buscar por postgres_id
        query = db.collection('clients').where('postgres_id', '==', postgres_id)
        results = query.get()
        
        if len(results) > 0:
            client_data = results[0].to_dict()
            client_data['firebase_id'] = results[0].id
            return client_data
        return None
    except Exception as e:
        print(f"Erro ao buscar cliente {postgres_id} no Firebase: {e}")
        return None

def add_client_to_firebase(client_data):
    """
    Adiciona um cliente ao Firebase Firestore
    
    Args:
        client_data: Dicionário com dados do cliente
        
    Returns:
        str: ID do documento criado no Firebase ou None em caso de erro
    """
    try:
        db = get_firestore_db()
        if not db:
            return None
        
        # Converter objetos date para string
        for key, value in client_data.items():
            if isinstance(value, datetime):
                client_data[key] = value.isoformat()
        
        # Adicionar timestamp de criação
        client_data['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Criar documento na coleção clients
        doc_ref = db.collection('clients').document()
        doc_ref.set(client_data)
        
        return doc_ref.id
    except Exception as e:
        print(f"Erro ao adicionar cliente ao Firebase: {e}")
        return None

def update_client_in_firebase(firebase_id, client_data):
    """
    Atualiza um cliente existente no Firebase
    
    Args:
        firebase_id: ID do documento no Firestore
        client_data: Dados atualizados do cliente
        
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    try:
        db = get_firestore_db()
        if not db:
            return False
        
        # Converter objetos date para string
        for key, value in client_data.items():
            if isinstance(value, datetime):
                client_data[key] = value.isoformat()
        
        # Adicionar timestamp de atualização
        client_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Atualizar documento
        doc_ref = db.collection('clients').document(firebase_id)
        doc_ref.update(client_data)
        
        return True
    except Exception as e:
        print(f"Erro ao atualizar cliente {firebase_id} no Firebase: {e}")
        return False

def sync_client_to_firebase(postgres_id):
    """
    Sincroniza um cliente específico do PostgreSQL para o Firebase
    
    Args:
        postgres_id: ID do cliente no PostgreSQL
        
    Returns:
        dict: Resultado da sincronização com status e mensagens
    """
    try:
        # Obter dados do cliente no PostgreSQL
        client_data = get_client_by_id(postgres_id)
        if not client_data:
            return {"success": False, "message": f"Cliente {postgres_id} não encontrado no PostgreSQL"}
        
        # Verificar se o cliente já existe no Firebase
        firebase_client = get_client_from_firebase_by_postgres_id(postgres_id)
        
        if firebase_client:
            # Cliente já existe, atualizar
            firebase_id = firebase_client['firebase_id']
            
            # Preparar dados para atualização
            update_data = {
                'nome': client_data['nome'],
                'email': client_data['email'],
                'telefone': client_data['telefone'],
                'endereco': client_data['endereco'],
                'cpf': client_data['cpf'],
                'data_aniversario': client_data['data_aniversario'],
                'origem_cliente': client_data['origem_cliente'],
                'data_cadastro': client_data['data_cadastro'].isoformat() if client_data['data_cadastro'] else None,
                'estado': client_data['estado'],
                'cidade': client_data['cidade'],
                'bairro': client_data['bairro'],
                'observacoes': client_data['observacoes'],
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            success = update_client_in_firebase(firebase_id, update_data)
            if success:
                return {"success": True, "message": f"Cliente {postgres_id} atualizado no Firebase", "action": "update"}
            else:
                return {"success": False, "message": f"Erro ao atualizar cliente {postgres_id} no Firebase"}
        else:
            # Cliente não existe, criar novo
            firebase_data = {
                'postgres_id': postgres_id,
                'nome': client_data['nome'],
                'email': client_data['email'],
                'telefone': client_data['telefone'],
                'endereco': client_data['endereco'],
                'cpf': client_data['cpf'],
                'data_aniversario': client_data['data_aniversario'],
                'origem_cliente': client_data['origem_cliente'],
                'data_cadastro': client_data['data_cadastro'].isoformat() if client_data['data_cadastro'] else None,
                'estado': client_data['estado'],
                'cidade': client_data['cidade'],
                'bairro': client_data['bairro'],
                'observacoes': client_data['observacoes']
            }
            
            firebase_id = add_client_to_firebase(firebase_data)
            if firebase_id:
                return {
                    "success": True, 
                    "message": f"Cliente {postgres_id} adicionado ao Firebase", 
                    "action": "create",
                    "firebase_id": firebase_id
                }
            else:
                return {"success": False, "message": f"Erro ao adicionar cliente {postgres_id} ao Firebase"}
    except Exception as e:
        return {"success": False, "message": f"Erro ao sincronizar cliente {postgres_id}: {e}"}

def sync_all_clients_to_firebase():
    """
    Sincroniza todos os clientes do PostgreSQL para o Firebase
    
    Returns:
        dict: Estatísticas da sincronização
    """
    try:
        # Obter todos os clientes do PostgreSQL
        clients_df = get_all_clients_from_postgres()
        if clients_df.empty:
            return {"success": False, "message": "Nenhum cliente encontrado no PostgreSQL"}
        
        # Estatísticas de sincronização
        stats = {
            "total": len(clients_df),
            "created": 0,
            "updated": 0,
            "errors": 0,
            "details": []
        }
        
        # Sincronizar cada cliente
        for _, row in clients_df.iterrows():
            result = sync_client_to_firebase(row['id'])
            
            if result['success']:
                if result['action'] == 'create':
                    stats['created'] += 1
                elif result['action'] == 'update':
                    stats['updated'] += 1
            else:
                stats['errors'] += 1
            
            stats['details'].append({
                'client_id': row['id'],
                'name': row['nome'],
                'result': result
            })
        
        return {
            "success": True,
            "message": f"Sincronização concluída: {stats['created']} criados, {stats['updated']} atualizados, {stats['errors']} erros",
            "stats": stats
        }
    except Exception as e:
        return {"success": False, "message": f"Erro na sincronização: {e}"}

def add_client_to_both(client_data):
    """
    Adiciona um novo cliente tanto ao PostgreSQL quanto ao Firebase
    
    Args:
        client_data: Dicionário com dados do cliente
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Adicionar ao PostgreSQL primeiro
        columns = ", ".join(client_data.keys())
        placeholders = ", ".join([f":{key}" for key in client_data.keys()])
        
        engine = get_engine()
        with engine.connect() as conn:
            # Inserir cliente
            query = f"""
            INSERT INTO clientes ({columns})
            VALUES ({placeholders})
            RETURNING id
            """
            
            result = conn.execute(text(query), client_data)
            conn.commit()
            
            # Obter ID gerado
            postgres_id = result.fetchone()[0]
            
        # Adicionar o ID do PostgreSQL aos dados
        firebase_data = client_data.copy()
        firebase_data['postgres_id'] = postgres_id
        
        # Adicionar ao Firebase
        firebase_id = add_client_to_firebase(firebase_data)
        
        if firebase_id:
            return {
                "success": True,
                "message": "Cliente adicionado com sucesso ao PostgreSQL e Firebase",
                "postgres_id": postgres_id,
                "firebase_id": firebase_id
            }
        else:
            return {
                "success": True,
                "warning": "Cliente adicionado apenas ao PostgreSQL, falha ao adicionar ao Firebase",
                "postgres_id": postgres_id
            }
    except Exception as e:
        return {"success": False, "message": f"Erro ao adicionar cliente: {e}"}

def link_client_to_firebase_user(postgres_id, firebase_user_id):
    """
    Vincula um cliente do PostgreSQL a um usuário do Firebase
    
    Args:
        postgres_id: ID do cliente no PostgreSQL
        firebase_user_id: ID do usuário no Firebase Auth
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Verificar se o cliente existe no PostgreSQL
        client_data = get_client_by_id(postgres_id)
        if not client_data:
            return {"success": False, "message": f"Cliente {postgres_id} não encontrado no PostgreSQL"}
        
        # Obter o cliente no Firebase
        firebase_client = get_client_from_firebase_by_postgres_id(postgres_id)
        
        db = get_firestore_db()
        if not db:
            return {"success": False, "message": "Firestore não inicializado"}
        
        # Atualizar usuário no Firebase com vínculo ao cliente
        user_ref = db.collection('users').document(firebase_user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return {"success": False, "message": f"Usuário {firebase_user_id} não encontrado no Firebase"}
        
        # Vincular usuário ao cliente
        user_ref.update({
            'linked_client': {
                'postgres_id': postgres_id,
                'firebase_client_id': firebase_client['firebase_id'] if firebase_client else None,
                'name': client_data['nome'],
                'email': client_data['email'],
                'linked_at': firestore.SERVER_TIMESTAMP
            }
        })
        
        # Se o cliente existir no Firebase, vinculá-lo ao usuário
        if firebase_client:
            client_ref = db.collection('clients').document(firebase_client['firebase_id'])
            client_ref.update({
                'firebase_user_id': firebase_user_id,
                'linked_at': firestore.SERVER_TIMESTAMP
            })
        
        return {
            "success": True,
            "message": f"Cliente {postgres_id} vinculado ao usuário {firebase_user_id}",
            "client_name": client_data['nome'],
            "user_id": firebase_user_id
        }
    except Exception as e:
        return {"success": False, "message": f"Erro ao vincular cliente ao usuário: {e}"}

# Inicializar Firebase ao importar o módulo
initialize_firebase()