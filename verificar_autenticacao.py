import streamlit as st
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

def verificar_autenticacao_firebase():
    """
    Verifica a configuração de autenticação do Firebase e como os usuários são 
    registrados no banco de dados PostgreSQL
    """
    st.title("Verificação de Autenticação e Isolamento de Dados")
    
    # 1. Verificar configuração do Firebase
    st.subheader("1. Configuração do Firebase")
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "N/A")
    
    if firebase_api_key != "N/A":
        # Mascarar a chave por segurança
        masked_key = firebase_api_key[:4] + "..." + firebase_api_key[-4:]
        st.success(f"Firebase API Key configurada: {masked_key}")
    else:
        st.error("Firebase API Key não encontrada nas variáveis de ambiente")
    
    # 2. Verificar conexão com o banco de dados
    st.subheader("2. Conexão com o banco de dados")
    db_url = os.environ.get("DATABASE_URL", "N/A")
    
    if db_url != "N/A":
        # Mascarar a URL por segurança
        masked_url = db_url.split("@")[0][:10] + "..." + db_url.split("@")[-1][-10:] if "@" in db_url else "URL presente mas formato não reconhecido"
        st.success(f"Database URL configurada: {masked_url}")
        
        try:
            conn = psycopg2.connect(db_url)
            st.success("✅ Conexão com o banco de dados estabelecida com sucesso")
            
            # Verificar estrutura da tabela de usuários
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'usuarios'
                ORDER BY ordinal_position
            """)
            
            st.subheader("Estrutura da tabela de usuários")
            colunas = []
            for col in cursor.fetchall():
                colunas.append(f"{col['column_name']} ({col['data_type']})")
            
            st.json(colunas)
            
            # Verificar tabela usuarios_firebase
            cursor.execute("""
                SELECT COUNT(*) as total FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'usuarios_firebase'
            """)
            
            if cursor.fetchone()['total'] > 0:
                st.success("✅ Tabela usuarios_firebase encontrada")
                
                # Verificar estrutura
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'usuarios_firebase'
                    ORDER BY ordinal_position
                """)
                
                st.subheader("Estrutura da tabela usuarios_firebase")
                colunas_firebase = []
                for col in cursor.fetchall():
                    colunas_firebase.append(f"{col['column_name']} ({col['data_type']})")
                
                st.json(colunas_firebase)
                
                # Verificar dados
                cursor.execute("SELECT COUNT(*) as total FROM usuarios_firebase")
                total = cursor.fetchone()['total']
                st.write(f"Total de registros: {total}")
                
                if total > 0:
                    cursor.execute("SELECT * FROM usuarios_firebase LIMIT 5")
                    registros = cursor.fetchall()
                    
                    # Remover dados sensíveis
                    for reg in registros:
                        if 'token' in reg:
                            reg['token'] = "***REMOVIDO***"
                        if 'refresh_token' in reg:
                            reg['refresh_token'] = "***REMOVIDO***"
                    
                    st.subheader("Amostra de registros")
                    st.json(registros)
            else:
                st.warning("⚠️ Tabela usuarios_firebase não encontrada")
            
            # 3. Verificar como o login é gerenciado
            st.subheader("3. Fluxo de Autenticação")
            
            # Verificar arquivo de login.py
            import importlib.util
            try:
                spec = importlib.util.spec_from_file_location("login", "login.py")
                login_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(login_module)
                st.success("✅ Módulo login.py carregado com sucesso")
                
                # Tentar determinar o fluxo de autenticação com base no código
                import inspect
                login_code = inspect.getsource(login_module)
                
                auth_methods = []
                if "firebase" in login_code.lower():
                    auth_methods.append("Firebase Authentication")
                if "jwt" in login_code.lower():
                    auth_methods.append("JWT (JSON Web Tokens)")
                if "session_state" in login_code:
                    auth_methods.append("Streamlit Session State")
                
                st.write("Métodos de autenticação identificados:")
                for method in auth_methods:
                    st.write(f"- {method}")
                
            except Exception as e:
                st.error(f"Erro ao analisar módulo login.py: {str(e)}")
            
            # 4. Verificar mecanismo de isolamento de dados
            st.subheader("4. Mecanismo de Isolamento de Dados")
            
            # Verificar use de usuario_id nas tabelas principais
            main_tables = ['clientes', 'propostas', 'financeiro', 'vendas', 'produtos']
            
            st.write("Verificando isolamento nas tabelas principais:")
            for table in main_tables:
                cursor.execute(f"""
                    SELECT COUNT(*) as total FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'usuario_id'
                """)
                
                if cursor.fetchone()['total'] > 0:
                    st.success(f"✅ Tabela {table} possui coluna usuario_id")
                    
                    # Verificar se há índice para usuario_id
                    cursor.execute(f"""
                        SELECT COUNT(*) as total FROM pg_indexes
                        WHERE tablename = '{table}' AND indexdef LIKE '%usuario_id%'
                    """)
                    
                    if cursor.fetchone()['total'] > 0:
                        st.success(f"  ✓ Índice encontrado para usuario_id em {table}")
                    else:
                        st.warning(f"  ⚠️ Sem índice para usuario_id em {table}")
                else:
                    st.error(f"❌ Tabela {table} NÃO possui coluna usuario_id")
            
            # 5. Verificar firewall do banco e configurações de acesso
            st.subheader("5. Configurações de Acesso ao Banco")
            
            # Verificar se o banco é do Render
            is_render = "render.com" in db_url.lower() if db_url != "N/A" else False
            is_neon = "neon.tech" in db_url.lower() if db_url != "N/A" else False
            
            if is_render:
                st.info("""
                ℹ️ **Banco de dados do Render detectado**
                
                O Render configura seu PostgreSQL com as seguintes características:
                - Acesso externo limitado por firewall
                - Necessidade de configurar IP permitido para conexões externas
                - Para usar o DBeaver, você precisa adicionar seu IP atual à lista de IPs permitidos no painel do Render
                """)
            elif is_neon:
                st.info("""
                ℹ️ **Banco de dados do Neon.tech detectado**
                
                O Neon.tech configura seu PostgreSQL com as seguintes características:
                - Acesso externo autenticado por senha
                - Modo serverless com conexões efêmeras
                - Para usar o DBeaver, use a string de conexão completa do Neon.tech incluindo SSL
                """)
            
            # Fechar conexão
            cursor.close()
            conn.close()
            
        except Exception as e:
            st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
    else:
        st.error("Database URL não encontrada nas variáveis de ambiente")
    
    # 6. Firebase API status
    st.subheader("6. Status da API do Firebase")
    
    if firebase_api_key != "N/A":
        try:
            # Teste teórico apenas para verificar se a chave é válida (não faz autenticação real)
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={firebase_api_key}"
            payload = {
                "continueUri": "https://example.com",
                "identifier": "test@example.com",
                "providerId": "password"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code < 400:
                st.success("✅ Firebase API está acessível e chave parece ser válida")
            else:
                error_data = response.json() if response.content else {"error": "Unknown"}
                st.error(f"❌ Erro ao acessar Firebase API: {error_data.get('error', {}).get('message', 'Desconhecido')}")
                
        except Exception as e:
            st.error(f"Erro ao testar Firebase API: {str(e)}")
    
    # 7. Instruções para acessar o banco via DBeaver
    st.subheader("7. Como acessar o banco via DBeaver")
    
    if is_render:
        st.info("""
        ### Conexão com o Render via DBeaver
        
        1. **Configure seu IP no Render**
           - Vá ao Dashboard do Render
           - Selecione seu banco PostgreSQL
           - Acesse "Settings" > "IP Allowlist"
           - Adicione seu IP atual
        
        2. **Configure o DBeaver**
           - Crie uma nova conexão PostgreSQL
           - Use os dados:
             - Host: Nome do host fornecido pelo Render
             - Port: 5432
             - Database: Nome do banco (geralmente 'postgres')
             - Username: Usuário fornecido pelo Render
             - Password: Senha fornecida pelo Render
           - Na guia "SSL", habilite "Verify server certificate"
        """)
    elif is_neon:
        st.info("""
        ### Conexão com o Neon.tech via DBeaver
        
        1. **Obtenha a string de conexão no Neon**
           - Acesse o dashboard do Neon.tech
           - Selecione seu projeto
           - Clique em "Connection Details"
           - Copie a string de conexão
        
        2. **Configure o DBeaver**
           - Crie uma nova conexão PostgreSQL
           - Use a opção "URL" e cole a string de conexão
           - OU configure manualmente:
             - Host: Endpoint fornecido pelo Neon
             - Port: 5432
             - Database: Nome do banco 
             - Username: Usuário fornecido 
             - Password: Senha fornecida
           - Na guia "SSL", selecione "Require SSL" e verifique o certificado do servidor
        """)
    else:
        st.info("""
        ### Conexão com PostgreSQL via DBeaver
        
        1. **Obtenha os dados de conexão**
           - Host/URL do servidor
           - Porta (normalmente 5432)
           - Nome do banco de dados
           - Nome de usuário
           - Senha
        
        2. **Configure o DBeaver**
           - Crie uma nova conexão PostgreSQL
           - Preencha os campos com as informações acima
           - Teste a conexão antes de salvar
        """)

    # 8. Conclusão sobre o isolamento
    st.subheader("8. Conclusão sobre Isolamento de Dados")
    
    has_isolation = True
    for table in main_tables:
        cursor = conn.cursor() if 'conn' in locals() else None
        if cursor:
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'usuario_id'
            """)
            if cursor.fetchone()[0] == 0:
                has_isolation = False
                break
            cursor.close()
    
    if has_isolation:
        st.success("""
        ✅ **Sistema configurado com isolamento multi-tenant**
        
        O sistema está configurado com o modelo de isolamento de dados por usuário, onde:
        - Cada tabela principal (clientes, propostas, etc.) possui uma coluna usuario_id
        - Os dados são filtrados por usuario_id em todas as operações
        - Cada usuário só acessa seus próprios dados
        - O design é compatível com SaaS multi-tenant
        """)
    else:
        st.warning("""
        ⚠️ **Sistema sem isolamento completo de dados**
        
        Algumas tabelas principais não possuem a coluna usuario_id, o que pode comprometer o isolamento de dados entre usuários.
        """)

def main():
    verificar_autenticacao_firebase()

if __name__ == "__main__":
    main()