"""
Ferramenta simples para verificar a conexão entre Firebase e PostgreSQL
"""
import streamlit as st
import psycopg2
import os
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(
    page_title="Verificar Firebase-PostgreSQL",
    page_icon="🔄",
    layout="wide"
)

# Configuração de estilo
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e9ecef;
        padding: 10px 20px;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #cce5ff;
        color: #004085;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #b8daff;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ffeeba;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.title("🔄 Verificar Integração Firebase-PostgreSQL")
st.markdown("Esta ferramenta verifica a sincronização entre o Firebase Auth e o banco de dados PostgreSQL")

# Conexão com o banco de dados
def get_connection():
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para exibir mensagens em caixas estilizadas
def success_box(message):
    st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)

def error_box(message):
    st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)

def info_box(message):
    st.markdown(f'<div class="info-box">{message}</div>', unsafe_allow_html=True)

def warning_box(message):
    st.markdown(f'<div class="warning-box">{message}</div>', unsafe_allow_html=True)

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs(["📊 Status", "👥 Usuários Firebase", "🗄️ Banco de Dados", "🔧 Ferramentas"])

with tab1:
    st.header("Status da Integração")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        api_status = st.container()
        st.subheader("Status da API")
        
        if st.button("Verificar API", key="check_api"):
            try:
                response = requests.get("http://localhost:8000/status")
                if response.status_code == 200:
                    data = response.json()
                    success_box(f"✅ API está online! Última atualização: {data.get('timestamp')}")
                else:
                    error_box(f"❌ API está offline. Código: {response.status_code}")
            except Exception as e:
                error_box(f"❌ Erro ao conectar com a API: {e}")
    
    with col2:
        db_status = st.container()
        st.subheader("Status do Banco de Dados")
        
        if st.button("Verificar Banco", key="check_db"):
            conn = get_connection()
            if conn:
                success_box("✅ Banco de dados está acessível")
                
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM usuarios_firebase")
                    count = cursor.fetchone()[0]
                    info_box(f"ℹ️ Total de usuários Firebase: {count}")
                    conn.close()
                except Exception as e:
                    warning_box(f"⚠️ Tabela 'usuarios_firebase' não encontrada ou erro: {e}")
            else:
                error_box("❌ Não foi possível conectar ao banco de dados")

with tab2:
    st.header("Usuários do Firebase")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("Listar Usuários Firebase", key="list_firebase_users"):
            try:
                response = requests.get("http://localhost:8000/api/usuarios")
                if response.status_code == 200:
                    data = response.json()
                    users = data.get('usuarios', [])
                    
                    if users:
                        # Convertendo em DataFrame para exibição
                        df = pd.DataFrame(users)
                        # Formatando as datas
                        if 'ultimo_login' in df.columns:
                            df['ultimo_login'] = pd.to_datetime(df['ultimo_login']).dt.strftime('%d/%m/%Y %H:%M')
                        if 'criado_em' in df.columns:
                            df['criado_em'] = pd.to_datetime(df['criado_em']).dt.strftime('%d/%m/%Y %H:%M')
                            
                        st.dataframe(df, use_container_width=True)
                        success_box(f"✅ {len(users)} usuários encontrados")
                    else:
                        info_box("Nenhum usuário encontrado no Firebase")
                else:
                    error_box(f"Erro ao obter usuários: {response.status_code}")
            except Exception as e:
                error_box(f"Erro ao conectar com a API: {e}")
    
    with col2:
        st.subheader("Adicionar Usuário")
        with st.form("add_user_form"):
            uid = st.text_input("UID", value="teste_" + datetime.now().strftime("%H%M%S"))
            nome = st.text_input("Nome", value="Usuário Teste")
            email = st.text_input("Email", value=f"teste_{datetime.now().strftime('%H%M%S')}@example.com")
            provedor = st.selectbox("Provedor", ["firebase", "google.com", "facebook.com", "github.com"])
            foto_url = st.text_input("URL da Foto", value="https://example.com/foto.jpg")
            
            submitted = st.form_submit_button("Adicionar")
            if submitted:
                try:
                    response = requests.post(
                        "http://localhost:8000/api/salvar-usuario",
                        json={
                            "uid": uid,
                            "nome": nome,
                            "email": email,
                            "provedor": provedor,
                            "foto_url": foto_url
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        success_box(f"✅ {data.get('mensagem')}")
                    else:
                        error_box(f"❌ Erro: {response.status_code} - {response.text}")
                except Exception as e:
                    error_box(f"❌ Erro ao conectar com a API: {e}")

with tab3:
    st.header("Dados do PostgreSQL")
    
    if st.button("Exibir Dados do Banco", key="show_db_data"):
        conn = get_connection()
        if conn:
            try:
                # Verificar tabela usuarios_firebase
                query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'usuarios_firebase'
                """
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    success_box("✅ Tabela 'usuarios_firebase' encontrada")
                    
                    # Obter estrutura da tabela
                    query = """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'usuarios_firebase'
                    """
                    structure_df = pd.read_sql_query(query, conn)
                    st.subheader("Estrutura da Tabela")
                    st.dataframe(structure_df, use_container_width=True)
                    
                    # Obter dados
                    query = "SELECT * FROM usuarios_firebase ORDER BY criado_em DESC"
                    users_df = pd.read_sql_query(query, conn)
                    
                    if not users_df.empty:
                        # Formatando as datas
                        for col in users_df.columns:
                            if users_df[col].dtype == 'datetime64[ns]':
                                users_df[col] = users_df[col].dt.strftime('%d/%m/%Y %H:%M')
                        
                        st.subheader("Dados dos Usuários")
                        st.dataframe(users_df, use_container_width=True)
                        info_box(f"ℹ️ Total de {len(users_df)} usuários no banco de dados")
                    else:
                        warning_box("⚠️ Nenhum usuário encontrado na tabela")
                else:
                    error_box("❌ Tabela 'usuarios_firebase' não existe no banco de dados")
                
                conn.close()
            except Exception as e:
                error_box(f"❌ Erro ao consultar o banco de dados: {e}")
        else:
            error_box("❌ Não foi possível conectar ao banco de dados")

with tab4:
    st.header("Ferramentas de Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Teste de API")
        
        with st.form("api_test_form"):
            endpoint = st.text_input("Endpoint", value="/status")
            method = st.selectbox("Método", ["GET", "POST"])
            payload = st.text_area("Dados (JSON para POST)", value='{"test": "value"}')
            
            submitted = st.form_submit_button("Executar")
            if submitted:
                try:
                    url = f"http://localhost:8000{endpoint}"
                    
                    if method == "GET":
                        response = requests.get(url)
                    else:
                        try:
                            json_data = json.loads(payload)
                            response = requests.post(url, json=json_data)
                        except json.JSONDecodeError:
                            error_box("❌ JSON inválido nos dados")
                            st.stop()
                    
                    st.subheader("Resposta")
                    st.code(f"Status: {response.status_code}")
                    
                    try:
                        st.json(response.json())
                    except:
                        st.text(response.text)
                except Exception as e:
                    error_box(f"❌ Erro na requisição: {e}")
    
    with col2:
        st.subheader("Banco de Dados")
        
        with st.form("db_query_form"):
            sql_query = st.text_area("Consulta SQL (somente SELECT)", 
                                     value="SELECT * FROM usuarios_firebase LIMIT 10")
            
            submitted = st.form_submit_button("Executar")
            if submitted:
                if "SELECT" in sql_query.upper() and not any(word in sql_query.upper() 
                                                           for word in ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE"]):
                    conn = get_connection()
                    if conn:
                        try:
                            df = pd.read_sql_query(sql_query, conn)
                            conn.close()
                            
                            st.subheader("Resultado")
                            st.dataframe(df, use_container_width=True)
                            success_box(f"✅ Consulta executada com sucesso. {len(df)} registros encontrados.")
                        except Exception as e:
                            error_box(f"❌ Erro ao executar consulta: {e}")
                    else:
                        error_box("❌ Não foi possível conectar ao banco de dados")
                else:
                    error_box("❌ Apenas consultas SELECT são permitidas")

    # Limpar tabela
    st.subheader("Manutenção de Dados")
    if st.button("Limpar Todos os Usuários", type="primary", help="⚠️ Esta ação não pode ser desfeita!"):
        warning = st.warning("Tem certeza que deseja excluir todos os usuários? Esta ação não pode ser desfeita!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim, limpar todos os dados", key="confirm_delete"):
                conn = get_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM usuarios_firebase")
                        conn.commit()
                        
                        # Verificar se a exclusão funcionou
                        cursor.execute("SELECT COUNT(*) FROM usuarios_firebase")
                        count = cursor.fetchone()[0]
                        
                        if count == 0:
                            success_box("✅ Todos os usuários foram excluídos com sucesso!")
                        else:
                            warning_box(f"⚠️ Alguns registros podem não ter sido excluídos. Restaram {count} registros.")
                        
                        conn.close()
                    except Exception as e:
                        error_box(f"❌ Erro ao limpar tabela: {e}")
                else:
                    error_box("❌ Não foi possível conectar ao banco de dados")
        with col2:
            if st.button("Não, cancelar", key="cancel_delete"):
                st.rerun()

# Informações de uso
st.divider()
st.markdown("""
### Como usar esta ferramenta
- Use a aba **Status** para verificar se a API e o banco de dados estão funcionando corretamente.
- Na aba **Usuários Firebase** você pode listar e adicionar usuários para testar a integração.
- A aba **Banco de Dados** permite visualizar a estrutura e dados diretamente do PostgreSQL.
- Use a aba **Ferramentas** para testes avançados e manutenção do sistema.

Esta ferramenta é apenas para fins administrativos e de teste.
""")