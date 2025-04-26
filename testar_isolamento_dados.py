import psycopg2
import os
from psycopg2.extras import RealDictCursor
import sys

def testar_isolamento():
    """Testa o isolamento de dados entre usuários no sistema"""
    try:
        print("===== VERIFICAÇÃO DE ISOLAMENTO MULTI-TENANT =====")
        # Obter conexão do ambiente
        db_url = os.environ.get("DATABASE_URL")
        print(f"Conectando ao banco PostgreSQL...")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Verificar como a coluna usuario_id é usada nas tabelas principais
        main_tables = ['clientes', 'propostas', 'financeiro', 'vendas', 'produtos']
        
        for table in main_tables:
            # Verificar se a tabela existe
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = '{table}'
                )
            """)
            
            if cursor.fetchone()['exists']:
                # Verificar se a tabela tem a coluna usuario_id
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'usuario_id'
                    )
                """)
                
                if cursor.fetchone()['exists']:
                    print(f"✅ Tabela {table} possui coluna usuario_id")
                    
                    # Verificar tipo de dados da coluna usuario_id
                    cursor.execute(f"""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'usuario_id'
                    """)
                    
                    data_type = cursor.fetchone()['data_type']
                    print(f"  - Tipo: {data_type}")
                    
                    # Verificar se há valores NULL na coluna usuario_id
                    cursor.execute(f"""
                        SELECT COUNT(*) as total_null
                        FROM {table}
                        WHERE usuario_id IS NULL
                    """)
                    
                    total_null = cursor.fetchone()['total_null']
                    print(f"  - Registros com usuario_id NULL: {total_null}")
                    
                    # Verificar distribuição de valores
                    cursor.execute(f"""
                        SELECT usuario_id, COUNT(*) as total
                        FROM {table}
                        WHERE usuario_id IS NOT NULL
                        GROUP BY usuario_id
                        ORDER BY total DESC
                        LIMIT 5
                    """)
                    
                    distribuicao = cursor.fetchall()
                    if distribuicao:
                        print(f"  - Distribuição de valores:")
                        for dist in distribuicao:
                            print(f"    * usuario_id {dist['usuario_id']}: {dist['total']} registros")
                else:
                    print(f"❌ Tabela {table} NÃO possui coluna usuario_id")
            else:
                print(f"⚠️ Tabela {table} não encontrada no banco")
        
        # 2. Verificar as políticas de acesso nas consultas SQL
        print("\n==== VERIFICANDO CONTROLE DE ACESSO EM CONSULTAS ====")
        
        # Olhar o código nas funções principais
        try:
            # Verificar utils/database.py para ver como as consultas são construídas
            with open("utils/database.py", "r") as f:
                db_code = f.read()
                
            # Verificar se as consultas em database.py usam a cláusula WHERE usuario_id
            where_usuario_id_count = db_code.count("WHERE usuario_id")
            and_usuario_id_count = db_code.count("AND usuario_id")
            
            print(f"Cláusulas WHERE usuario_id em database.py: {where_usuario_id_count}")
            print(f"Cláusulas AND usuario_id em database.py: {and_usuario_id_count}")
            
            # Verificar como o usuario_id é passado para as consultas
            # Verificar se o sistema usa session_state para armazenar o ID do usuário
            session_usuario_count = db_code.count("session_state['usuario']") + db_code.count("session_state.usuario") 
            
            print(f"Referências a session_state['usuario']: {session_usuario_count}")
            
            # Verificar como o sistema obtém o usuario_id para filtrar consultas
            if "get_usuario_id" in db_code:
                print("✅ Função get_usuario_id encontrada para obter ID do usuário")
            
            # Verificar login.py para entender como os dados do usuário são armazenados
            with open("login.py", "r") as f:
                login_code = f.read()
                
            # Verificar se o login.py define o session_state
            if "session_state['usuario']" in login_code or "session_state.usuario" in login_code:
                print("✅ Login.py configura st.session_state.usuario")
            
            if "st.session_state['user']" in login_code or "st.session_state.user" in login_code:
                print("✅ Login.py configura st.session_state.user")
                
        except Exception as e:
            print(f"Erro ao analisar código: {str(e)}")
        
        # 3. Verificar o código de inicialização do banco de dados
        print("\n==== VERIFICANDO INICIALIZAÇÃO DO BANCO DE DADOS ====")
        
        # Verificar como o banco de dados é inicializado
        try:
            with open("app.py", "r") as f:
                app_code = f.read()
                
            # Verificar se app.py inicializa o banco com context de usuário
            if "init_db" in app_code and "usuario_id" in app_code:
                print("✅ App.py inicializa banco com contexto de usuário")
            
            # Verificar como o sistema obtém o ID do usuário atual
            if "get_current_user_id" in app_code:
                print("✅ Função get_current_user_id encontrada")
            
            if "firebase_user_id" in app_code:
                print("✅ Referência a firebase_user_id encontrada")
        
        except Exception as e:
            print(f"Erro ao analisar app.py: {str(e)}")
        
        # 4. Teste prático: verificar conteúdo de 2 usuários
        print("\n==== TESTANDO ISOLAMENTO ENTRE USUÁRIOS ====")
        
        # Buscar IDs de 2 usuários diferentes
        cursor.execute("SELECT id, email FROM usuarios LIMIT 2")
        usuarios = cursor.fetchall()
        
        if len(usuarios) >= 2:
            usuario1 = usuarios[0]
            usuario2 = usuarios[1]
            
            print(f"Usuário 1: {usuario1['email']} (ID: {usuario1['id']})")
            print(f"Usuário 2: {usuario2['email']} (ID: {usuario2['id']})")
            
            # Verificar clientes para cada usuário
            cursor.execute(f"SELECT COUNT(*) as total FROM clientes WHERE usuario_id = '{usuario1['id']}'")
            clientes_usuario1 = cursor.fetchone()['total']
            
            cursor.execute(f"SELECT COUNT(*) as total FROM clientes WHERE usuario_id = '{usuario2['id']}'")
            clientes_usuario2 = cursor.fetchone()['total']
            
            print(f"Clientes do usuário 1: {clientes_usuario1}")
            print(f"Clientes do usuário 2: {clientes_usuario2}")
            
            # Verificar propostas para cada usuário
            cursor.execute(f"SELECT COUNT(*) as total FROM propostas WHERE usuario_id = '{usuario1['id']}'")
            propostas_usuario1 = cursor.fetchone()['total']
            
            cursor.execute(f"SELECT COUNT(*) as total FROM propostas WHERE usuario_id = '{usuario2['id']}'")
            propostas_usuario2 = cursor.fetchone()['total']
            
            print(f"Propostas do usuário 1: {propostas_usuario1}")
            print(f"Propostas do usuário 2: {propostas_usuario2}")
            
            # Verificar consistência entre clientes e propostas
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM propostas p 
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = '{usuario1['id']}' AND c.usuario_id != '{usuario1['id']}'
            """)
            
            inconsistencias_usuario1 = cursor.fetchone()['total']
            
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM propostas p 
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = '{usuario2['id']}' AND c.usuario_id != '{usuario2['id']}'
            """)
            
            inconsistencias_usuario2 = cursor.fetchone()['total']
            
            print(f"Inconsistências do usuário 1 (propostas ligadas a clientes de outros usuários): {inconsistencias_usuario1}")
            print(f"Inconsistências do usuário 2 (propostas ligadas a clientes de outros usuários): {inconsistencias_usuario2}")
            
            if inconsistencias_usuario1 == 0 and inconsistencias_usuario2 == 0:
                print("✅ Não foram encontradas inconsistências entre usuários")
            else:
                print("❌ Foram encontradas inconsistências no isolamento de dados")
        else:
            print("Não foi possível encontrar 2 usuários para testar")
        
        # 5. Verificar registros do Firebase
        print("\n==== VERIFICANDO VÍNCULOS COM FIREBASE ====")
        
        cursor.execute("SELECT * FROM usuarios_firebase LIMIT 1")
        firebase_record = cursor.fetchone()
        
        if firebase_record:
            print("Colunas na tabela usuarios_firebase:")
            for col in firebase_record.keys():
                print(f"- {col}")
            
            # Verificar como os IDs do Firebase são vinculados aos usuários
            if 'uid' in firebase_record:
                print(f"ID do Firebase encontrado na coluna 'uid'")
                
                # Verificar se há coluna correspondente em usuarios
                cursor.execute("""
                    SELECT COUNT(*) as total FROM information_schema.columns 
                    WHERE table_name = 'usuarios' AND column_name = 'firebase_id'
                """)
                
                if cursor.fetchone()['total'] > 0:
                    print("✅ Coluna firebase_id encontrada na tabela usuarios")
                else:
                    print("❌ Não há coluna firebase_id na tabela usuarios")
        else:
            print("Não foram encontrados registros na tabela usuarios_firebase")
        
        # 6. Verificar valores nulos em usuario_id
        print("\n==== VERIFICANDO VALORES NULOS EM USUARIO_ID ====")
        
        for table in main_tables:
            if table == 'clientes':
                # Verificar apenas clientes com valores nulos
                cursor.execute(f"""
                    SELECT id, nome, usuario_id FROM {table}
                    WHERE usuario_id IS NULL
                    LIMIT 5
                """)
                
                null_records = cursor.fetchall()
                
                if null_records:
                    print(f"Clientes com usuario_id NULL:")
                    for rec in null_records:
                        print(f"- ID: {rec['id']}, Nome: {rec['nome']}")
                else:
                    print(f"Não foram encontrados clientes com usuario_id NULL")
        
        # 7. Verificar consistência dos dados do usuário
        print("\n==== VERIFICANDO CADASTRO DO FIREBASE ====")
        
        email_buscado = "solanobicalho@yahoo.com.br"
        print(f"Verificando dados do usuário {email_buscado}")
        
        cursor.execute("""
            SELECT * FROM usuarios_firebase
            WHERE email = %s
        """, (email_buscado,))
        
        firebase_user = cursor.fetchone()
        
        if firebase_user:
            print(f"✅ Usuário encontrado na tabela usuarios_firebase")
            print(f"- UID: {firebase_user.get('uid', 'N/A')}")
            print(f"- Email: {firebase_user.get('email', 'N/A')}")
            print(f"- Provedor: {firebase_user.get('provedor', 'N/A')}")
            print(f"- Criado em: {firebase_user.get('criado_em', 'N/A')}")
            
            # Verificar se há registro correspondente em usuarios
            cursor.execute("""
                SELECT * FROM usuarios
                WHERE email = %s
            """, (email_buscado,))
            
            db_user = cursor.fetchone()
            
            if db_user:
                print(f"✅ Usuário também encontrado na tabela usuarios")
                print(f"- ID: {db_user.get('id', 'N/A')}")
                
                # Verificar se há vinculação entre as tabelas
                print("\nVerificando vinculação entre tabelas:")
                if 'firebase_id' in db_user and db_user['firebase_id'] == firebase_user.get('uid'):
                    print("✅ ID do Firebase corretamente vinculado ao usuário")
                else:
                    print("❌ Não há vinculação correta entre Firebase e usuário")
            else:
                print(f"❌ Usuário não encontrado na tabela usuarios")
        else:
            print(f"❌ Usuário {email_buscado} não encontrado no Firebase")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_isolamento()