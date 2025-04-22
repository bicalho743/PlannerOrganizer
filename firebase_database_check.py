"""
Ferramenta simples para verificar a conexão entre Firebase e PostgreSQL
"""
import os
import sys
import json
import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Verificação Firebase-PostgreSQL",
    page_icon="🔄",
    layout="wide"
)

st.title("Verificação de Conexão Firebase-PostgreSQL")

# Seção de diagnóstico
st.header("Diagnóstico")

# Verificar variáveis de ambiente
st.subheader("Variáveis de Ambiente")
env_vars = {
    "DATABASE_URL": os.environ.get("DATABASE_URL") is not None,
    "FIREBASE_API_KEY": os.environ.get("FIREBASE_API_KEY") is not None,
    "FIREBASE_DATABASE_URL": os.environ.get("FIREBASE_DATABASE_URL") is not None,
    "STRIPE_API_KEY": os.environ.get("STRIPE_API_KEY") is not None,
    "STRIPE_PUBLISHABLE_KEY": os.environ.get("STRIPE_PUBLISHABLE_KEY") is not None,
}

for var, exists in env_vars.items():
    if exists:
        st.success(f"✅ {var}: Disponível")
    else:
        st.error(f"❌ {var}: Não encontrado")

# Verificar arquivo de credenciais do Firebase
st.subheader("Arquivo de Credenciais do Firebase")
firebase_cred_paths = [
    "api/firebase_credentials.json",
    "attached_assets/planner-organizer-68a23-firebase-adminsdk-fbsvc-035c993cd8.json"
]

found_credentials = False
for path in firebase_cred_paths:
    if os.path.exists(path):
        st.success(f"✅ Arquivo encontrado: {path}")
        
        # Mostrar informações do arquivo
        try:
            with open(path, 'r') as f:
                cred_data = json.load(f)
                
            # Exibir informações não sensíveis
            st.write("Informações do arquivo:")
            st.write(f"- **Project ID:** {cred_data.get('project_id')}")
            st.write(f"- **Client Email:** {cred_data.get('client_email')}")
            st.write(f"- **Type:** {cred_data.get('type')}")
            
            found_credentials = True
            break
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo {path}: {str(e)}")
            
if not found_credentials:
    st.error("❌ Nenhum arquivo de credenciais encontrado")

# Testar conexão com PostgreSQL
st.subheader("Teste de Conexão com PostgreSQL")

try:
    # Tentar importar módulos necessários
    st.info("Importando módulos SQLAlchemy...")
    import sqlalchemy
    from sqlalchemy import create_engine, text
    st.success("✅ SQLAlchemy importado com sucesso")
    
    # Tentar conectar ao banco de dados
    if "DATABASE_URL" in os.environ:
        st.info("Conectando ao PostgreSQL...")
        engine = create_engine(os.environ["DATABASE_URL"])
        
        with engine.connect() as conn:
            st.success("✅ Conexão com PostgreSQL estabelecida")
            
            # Contar registros nas tabelas principais
            tables = ["clientes", "propostas", "vendas", "usuarios"]
            table_counts = {}
            
            for table in tables:
                try:
                    query = f"SELECT COUNT(*) FROM {table}"
                    result = conn.execute(text(query)).scalar()
                    table_counts[table] = result
                except Exception as e:
                    table_counts[table] = f"Erro: {str(e)}"
            
            # Exibir contagem
            st.write("Contagem de registros:")
            for table, count in table_counts.items():
                st.write(f"- **{table}:** {count}")
    else:
        st.error("❌ Variável DATABASE_URL não encontrada")
except Exception as e:
    st.error(f"❌ Erro ao conectar ao PostgreSQL: {str(e)}")

# Testar conexão com Firebase
st.subheader("Teste de Conexão com Firebase")

try:
    # Tentar importar módulos do Firebase
    st.info("Importando módulos Firebase...")
    import firebase_admin
    from firebase_admin import credentials, firestore
    st.success("✅ Módulos Firebase importados com sucesso")
    
    # Verificar se já existe uma instância do Firebase
    if not firebase_admin._apps:
        st.info("Inicializando Firebase...")
        
        # Tentar usar o arquivo de credenciais
        if found_credentials:
            cred_path = firebase_cred_paths[0] if os.path.exists(firebase_cred_paths[0]) else firebase_cred_paths[1]
            cred = credentials.Certificate(cred_path)
            firebase_app = firebase_admin.initialize_app(cred)
            st.success(f"✅ Firebase inicializado com credenciais de {cred_path}")
        else:
            st.error("❌ Não foi possível inicializar Firebase (credenciais não encontradas)")
    else:
        st.success("✅ Firebase já está inicializado")
    
    # Tentar acessar o Firestore
    try:
        db = firestore.client()
        st.success("✅ Conexão com Firestore estabelecida")
        
        # Listar coleções
        collections = db.collections()
        collection_list = [c.id for c in collections]
        
        if collection_list:
            st.write("Coleções disponíveis:")
            for coll in collection_list:
                st.write(f"- **{coll}**")
        else:
            st.warning("⚠️ Nenhuma coleção encontrada no Firestore")
    except Exception as e:
        st.error(f"❌ Erro ao acessar Firestore: {str(e)}")
except Exception as e:
    st.error(f"❌ Erro ao inicializar Firebase: {str(e)}")

# Exibir caminhos do sistema
st.subheader("Caminhos do Sistema")
st.write(f"- **Diretório atual:** {os.getcwd()}")
st.write(f"- **sys.path:** {sys.path}")