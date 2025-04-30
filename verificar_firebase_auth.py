import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def verificar_firebase_integracao():
    """Verifica a integração do Firebase com o sistema"""
    print("====== VERIFICAÇÃO DE AUTENTICAÇÃO FIREBASE ======")
    
    # 1. Verificar variáveis de ambiente
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "N/A")
    
    if firebase_api_key != "N/A":
        print("✅ Firebase API Key configurada")
    else:
        print("❌ Firebase API Key não encontrada nas variáveis de ambiente")
    
    # 2. Verificar tabela usuarios_firebase no banco de dados
    try:
        db_url = os.environ.get("DATABASE_URL", "N/A")
        if db_url == "N/A":
            print("❌ DATABASE_URL não encontrada nas variáveis de ambiente")
            return
        
        print("Conectando ao banco de dados...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar tabela usuarios_firebase
        cursor.execute("""
            SELECT COUNT(*) as total FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'usuarios_firebase'
        """)
        
        if cursor.fetchone()['total'] > 0:
            print("✅ Tabela usuarios_firebase encontrada")
            
            # Verificar estrutura
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'usuarios_firebase'
                ORDER BY ordinal_position
            """)
            
            print("\nEstrutura da tabela usuarios_firebase:")
            for col in cursor.fetchall():
                print(f"- {col['column_name']} ({col['data_type']})")
            
            # Verificar dados
            cursor.execute("SELECT COUNT(*) as total FROM usuarios_firebase")
            total = cursor.fetchone()['total']
            print(f"\nTotal de registros em usuarios_firebase: {total}")
            
            if total > 0:
                cursor.execute("SELECT uid, email FROM usuarios_firebase LIMIT 5")
                registros = cursor.fetchall()
                
                print("\nAmostra de registros (sem tokens):")
                for reg in registros:
                    print(f"- Firebase UID: {reg.get('uid', 'N/A')}")
                    print(f"  Email: {reg.get('email', 'N/A')}")
                    print("  ------")
        else:
            print("❌ Tabela usuarios_firebase não encontrada")
        
        # 3. Verificar tabela usuarios
        print("\n==== TABELA USUARIOS ====")
        cursor.execute("""
            SELECT COUNT(*) as total FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'usuarios'
        """)
        
        if cursor.fetchone()['total'] > 0:
            print("✅ Tabela usuarios encontrada")
            
            # Verificar estrutura
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'usuarios'
                ORDER BY ordinal_position
            """)
            
            print("\nEstrutura da tabela usuarios:")
            for col in cursor.fetchall():
                print(f"- {col['column_name']} ({col['data_type']})")
            
            # Verificar relação com firebase_id
            cursor.execute("""
                SELECT COUNT(*) as total FROM information_schema.columns 
                WHERE table_name = 'usuarios' AND column_name = 'firebase_id'
            """)
            
            if cursor.fetchone()['total'] > 0:
                print("✅ Coluna firebase_id encontrada na tabela usuarios")
                
                # Verificar se há correspondência entre as tabelas
                cursor.execute("""
                    SELECT u.id, u.email, u.firebase_id, COUNT(uf.firebase_id) as firebase_count
                    FROM usuarios u
                    LEFT JOIN usuarios_firebase uf ON u.firebase_id = uf.firebase_id
                    GROUP BY u.id, u.email, u.firebase_id
                    LIMIT 5
                """)
                
                correspondencias = cursor.fetchall()
                print("\nCorrespondência entre usuarios e usuarios_firebase:")
                for corr in correspondencias:
                    print(f"- Usuário: {corr.get('email', 'N/A')}")
                    print(f"  Firebase ID: {corr.get('firebase_id', 'N/A')}")
                    print(f"  Correspondências: {corr.get('firebase_count', 0)}")
                    print("  ------")
            else:
                print("❌ Coluna firebase_id NÃO encontrada na tabela usuarios")
                
                # Verificar se há outro mecanismo de vinculação
                print("\nVerificando mecanismos alternativos de vinculação:")
                cursor.execute("SELECT * FROM usuarios LIMIT 1")
                sample_user = cursor.fetchone()
                
                potential_links = []
                for col, val in sample_user.items():
                    if col not in ('id', 'nome', 'email', 'telefone', 'empresa', 'role'):
                        potential_links.append(col)
                
                if potential_links:
                    print(f"Possíveis colunas de vinculação: {', '.join(potential_links)}")
                else:
                    print("Não foram encontradas colunas adicionais para vinculação com Firebase")
        else:
            print("❌ Tabela usuarios não encontrada")
        
        # 4. Verificar login.py
        print("\n==== CÓDIGO DE AUTENTICAÇÃO ====")
        try:
            with open("login.py", "r") as f:
                login_code = f.read()
                
            auth_methods = []
            if "firebase" in login_code.lower():
                auth_methods.append("Firebase Authentication")
            if "jwt" in login_code.lower():
                auth_methods.append("JWT (JSON Web Tokens)")
            if "session_state" in login_code:
                auth_methods.append("Streamlit Session State")
            
            if auth_methods:
                print("Métodos de autenticação identificados:")
                for method in auth_methods:
                    print(f"- {method}")
            else:
                print("Não foi possível identificar métodos de autenticação no código")
                
            # Verificar como os dados do usuário são armazenados na sessão
            if "session_state" in login_code and "usuario" in login_code:
                print("\nArmazenamento de sessão identificado:")
                
                if "st.session_state['usuario']" in login_code or "st.session_state.usuario" in login_code:
                    print("- Dados armazenados em st.session_state.usuario")
                
                if "st.session_state['user']" in login_code or "st.session_state.user" in login_code:
                    print("- Dados armazenados em st.session_state.user")
                    
                if "st.session_state['auth']" in login_code or "st.session_state.auth" in login_code:
                    print("- Dados armazenados em st.session_state.auth")
                    
            # Verificar firebase_auth.py se existir
            if os.path.exists("utils/firebase_auth.py"):
                print("\nMódulo firebase_auth.py encontrado!")
                
                with open("utils/firebase_auth.py", "r") as f:
                    firebase_code = f.read()
                
                if "login_firebase" in firebase_code:
                    print("- Função login_firebase identificada")
                if "verify_token" in firebase_code:
                    print("- Função verify_token identificada")
                if "get_user_info" in firebase_code:
                    print("- Função get_user_info identificada")
                    
        except Exception as e:
            print(f"Erro ao analisar código de autenticação: {str(e)}")
        
        # 5. Verificar como o usuario_id é usado nas tabelas
        print("\n==== ISOLAMENTO DE DADOS POR USUARIO_ID ====")
        main_tables = ['clientes', 'propostas', 'financeiro', 'vendas', 'produtos']
        
        for table in main_tables:
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = '{table}'
            """)
            
            if cursor.fetchone()['total'] > 0:
                cursor.execute(f"""
                    SELECT COUNT(*) as total FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'usuario_id'
                """)
                
                if cursor.fetchone()['total'] > 0:
                    print(f"✅ Tabela {table} possui coluna usuario_id")
                    
                    # Verificar tipos de dados da coluna usuario_id
                    cursor.execute(f"""
                        SELECT data_type FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'usuario_id'
                    """)
                    
                    data_type = cursor.fetchone()['data_type']
                    print(f"  - Tipo de dados: {data_type}")
                    
                    # Verificar valores distintos
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT usuario_id) as distinct_count
                        FROM {table}
                    """)
                    
                    distinct_count = cursor.fetchone()['distinct_count']
                    print(f"  - Valores distintos: {distinct_count}")
                    
                    # Verificar amostra dos primeiros 2 valores
                    cursor.execute(f"""
                        SELECT DISTINCT usuario_id
                        FROM {table}
                        LIMIT 2
                    """)
                    
                    distinct_values = cursor.fetchall()
                    values_str = ', '.join([str(val['usuario_id']) for val in distinct_values if val['usuario_id'] is not None])
                    print(f"  - Exemplos: {values_str if values_str else 'Nenhum valor não-nulo encontrado'}")
                    
                else:
                    print(f"❌ Tabela {table} NÃO possui coluna usuario_id")
            else:
                print(f"⚠️ Tabela {table} não encontrada no banco")
        
        # 6. Verificar configurações de acesso ao banco
        print("\n==== CONFIGURAÇÕES DO BANCO DE DADOS ====")
        
        # Verificar se o banco é do Render ou Neon
        is_render = "render.com" in db_url.lower() if db_url != "N/A" else False
        is_neon = "neon.tech" in db_url.lower() if db_url != "N/A" else False
        
        if is_render:
            print("🔍 Banco de dados detectado: Render PostgreSQL")
            print("- Acesso externo limitado por firewall")
            print("- É necessário adicionar IPs permitidos no painel do Render")
        elif is_neon:
            print("🔍 Banco de dados detectado: Neon.tech PostgreSQL")
            print("- Modo serverless com conexões efêmeras")
            print("- Acesso externo autenticado com SSL obrigatório")
        else:
            print("🔍 Banco de dados PostgreSQL genérico")
        
        # Verificar informações do servidor
        cursor.execute("SELECT current_database(), current_user, version()")
        db_info = cursor.fetchone()
        print(f"\nInformações do servidor:")
        print(f"- Banco de dados: {db_info['current_database']}")
        print(f"- Usuário: {db_info['current_user']}")
        print(f"- Versão: {db_info['version']}")
        
        # Verificar conexão com solanobicalho@yahoo.com.br
        email_buscado = "solanobicalho@yahoo.com.br"
        print(f"\n==== BUSCANDO USUÁRIO {email_buscado} ====")
        
        # Verificar na tabela usuarios
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email_buscado,))
        usuario_encontrado = cursor.fetchone()
        
        if usuario_encontrado:
            print(f"✅ Usuário encontrado na tabela usuarios!")
            print(f"- ID: {usuario_encontrado['id']}")
            print(f"- Email: {usuario_encontrado['email']}")
            print(f"- Nome: {usuario_encontrado.get('nome', 'N/A')}")
            print(f"- Firebase ID: {usuario_encontrado.get('firebase_id', 'N/A')}")
            
            # Verificar na tabela firebase
            if 'firebase_id' in usuario_encontrado and usuario_encontrado['firebase_id']:
                cursor.execute("SELECT * FROM usuarios_firebase WHERE firebase_id = %s", 
                              (usuario_encontrado['firebase_id'],))
                firebase_record = cursor.fetchone()
                
                if firebase_record:
                    print("✅ Registro correspondente encontrado na tabela usuarios_firebase")
                else:
                    print("❌ Não há registro correspondente na tabela usuarios_firebase")
            
            # Verificar clientes deste usuário
            usuario_id = usuario_encontrado['id']
            cursor.execute("SELECT COUNT(*) as total FROM clientes WHERE usuario_id = %s", (usuario_id,))
            total_clientes = cursor.fetchone()['total']
            
            print(f"\nClientes associados: {total_clientes}")
            if total_clientes > 0:
                cursor.execute("SELECT id, nome FROM clientes WHERE usuario_id = %s LIMIT 5", (usuario_id,))
                clientes = cursor.fetchall()
                
                print("Exemplos de clientes:")
                for cliente in clientes:
                    print(f"- ID: {cliente['id']}, Nome: {cliente['nome']}")
            
        else:
            print(f"❌ Usuário {email_buscado} não encontrado na tabela usuarios")
            
            # Verificar na tabela firebase
            cursor.execute("SELECT * FROM usuarios_firebase WHERE email = %s", (email_buscado,))
            firebase_record = cursor.fetchone()
            
            if firebase_record:
                print(f"✅ Usuário encontrado na tabela usuarios_firebase!")
                print(f"- Firebase ID: {firebase_record.get('firebase_id', 'N/A')}")
                print(f"- Usuario ID: {firebase_record.get('usuario_id', 'N/A')}")
                
                # Verificar se há usuário com este ID
                if 'usuario_id' in firebase_record and firebase_record['usuario_id']:
                    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (firebase_record['usuario_id'],))
                    linked_user = cursor.fetchone()
                    
                    if linked_user:
                        print(f"✅ Usuário vinculado encontrado: {linked_user.get('email', 'N/A')}")
                    else:
                        print("❌ Não há usuário com o ID vinculado")
            else:
                print(f"❌ Usuário {email_buscado} não encontrado na tabela usuarios_firebase")
                
                # Mostrar alguns usuários de exemplo
                print("\nAmostra de usuários disponíveis:")
                cursor.execute("SELECT id, email FROM usuarios LIMIT 3")
                users_sample = cursor.fetchall()
                
                for user in users_sample:
                    print(f"- ID: {user['id']}, Email: {user['email']}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao verificar banco de dados: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n====== VERIFICAÇÃO CONCLUÍDA ======")

if __name__ == "__main__":
    verificar_firebase_integracao()