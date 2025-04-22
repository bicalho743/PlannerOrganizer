"""
Sistema de auditoria de autenticação

Este módulo registra eventos relacionados à autenticação para fins de segurança,
como tentativas de login, logins bem-sucedidos, logouts, e outras atividades relacionadas.
"""
import os
import json
import logging
from datetime import datetime, timedelta
import streamlit as st
import sqlite3
import threading
import queue

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
AUDIT_DB_PATH = "data/auth_audit.db"
DB_SETUP_QUERY = """
CREATE TABLE IF NOT EXISTS auth_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    user_email TEXT,
    user_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    success INTEGER NOT NULL,
    details TEXT,
    session_id TEXT
);
"""

# Garantir que o diretório data existe
os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)

# Thread-safe queue para eventos
event_queue = queue.Queue()
db_lock = threading.Lock()


def setup_db():
    """Configura o banco de dados de auditoria se não existir"""
    try:
        with db_lock:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(DB_SETUP_QUERY)
            conn.commit()
            conn.close()
            logger.info("Banco de dados de auditoria configurado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao configurar banco de dados de auditoria: {str(e)}")


def log_auth_event(event_type, user_email=None, user_id=None, success=True, details=None):
    """
    Registra um evento de autenticação
    
    Args:
        event_type: Tipo de evento (login, logout, password_reset, etc)
        user_email: Email do usuário (opcional)
        user_id: ID do usuário (opcional)
        success: Se a operação foi bem-sucedida
        details: Detalhes adicionais do evento (opcional)
    """
    # Preparar dados do evento
    timestamp = datetime.now().isoformat()
    ip_address = os.environ.get("REMOTE_ADDR", "unknown")
    user_agent = os.environ.get("HTTP_USER_AGENT", "unknown")
    session_id = st.session_state.get("_session_id", "unknown")
    
    # Adicionar evento à fila
    event_data = {
        "timestamp": timestamp,
        "event_type": event_type,
        "user_email": user_email,
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": 1 if success else 0,
        "details": json.dumps(details) if details else None,
        "session_id": session_id
    }
    
    event_queue.put(event_data)
    
    # Registrar no log também
    if success:
        logger.info(f"Auth event: {event_type} for {user_email or 'unknown'}")
    else:
        logger.warning(f"Auth failure: {event_type} for {user_email or 'unknown'}")
    
    # Processar fila de eventos
    process_event_queue()


def process_event_queue():
    """Processa a fila de eventos de auditoria e salva no banco de dados"""
    processed = 0
    try:
        # Inicializar conexão com o banco
        with db_lock:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            cursor = conn.cursor()
            
            # Processar itens da fila
            while not event_queue.empty() and processed < 10:  # Limite por batch
                event = event_queue.get()
                
                # Inserir no banco
                cursor.execute(
                    """
                    INSERT INTO auth_events (
                        timestamp, event_type, user_email, user_id, 
                        ip_address, user_agent, success, details, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["timestamp"], event["event_type"], event["user_email"], 
                        event["user_id"], event["ip_address"], event["user_agent"], 
                        event["success"], event["details"], event["session_id"]
                    )
                )
                
                processed += 1
            
            # Commit e fechar
            conn.commit()
            conn.close()
    except Exception as e:
        logger.error(f"Erro ao processar fila de eventos de auditoria: {str(e)}")


def get_recent_events(limit=100, user_email=None):
    """
    Retorna eventos recentes de autenticação
    
    Args:
        limit: Número máximo de eventos a retornar
        user_email: Filtrar por usuário específico (opcional)
        
    Returns:
        list: Lista de eventos
    """
    try:
        events = []
        with db_lock:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_email:
                cursor.execute(
                    "SELECT * FROM auth_events WHERE user_email = ? ORDER BY timestamp DESC LIMIT ?",
                    (user_email, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM auth_events ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            
            for row in cursor.fetchall():
                event = dict(row)
                # Converter details de JSON para dict se não for None
                if event["details"]:
                    try:
                        event["details"] = json.loads(event["details"])
                    except:
                        pass
                events.append(event)
            
            conn.close()
        return events
    except Exception as e:
        logger.error(f"Erro ao buscar eventos de auditoria: {str(e)}")
        return []


def get_failed_login_count(user_email, minutes=30):
    """
    Retorna o número de tentativas de login falhas em um período
    
    Args:
        user_email: Email do usuário
        minutes: Período de tempo em minutos para verificar
        
    Returns:
        int: Número de tentativas falhas
    """
    try:
        with db_lock:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            cursor = conn.cursor()
            
            # Calcular timestamp de corte
            cutoff_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            
            cursor.execute(
                """
                SELECT COUNT(*) FROM auth_events 
                WHERE user_email = ? AND event_type = 'login' AND success = 0 AND timestamp > ?
                """,
                (user_email, cutoff_time)
            )
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
    except Exception as e:
        logger.error(f"Erro ao buscar contagem de logins falhos: {str(e)}")
        return 0


# Inicialização do módulo
setup_db()