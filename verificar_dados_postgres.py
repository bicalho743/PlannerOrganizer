import psycopg2
import os
from psycopg2.extras import RealDictCursor
import sys

def verificar_dados_banco():
    """Verifica dados no banco PostgreSQL"""
    try:
        # Obter conexão do ambiente
        db_url = os.environ.get("DATABASE_URL")
        print(f"Tentando conectar ao banco PostgreSQL...")
        
        conn = psycopg2.connect(db_url)
        print("Conexão estabelecida com sucesso!")
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Listar tabelas no banco
        print("\n==== TABELAS NO BANCO DE DADOS ====")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f"Total de tabelas: {len(tabelas)}")
        for i, tabela in enumerate(tabelas):
            print(f"{i+1}. {tabela['table_name']}")
        
        # 2. Verificar usuários
        print("\n==== USUÁRIOS CADASTRADOS ====")
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        print(f"Total de usuários: {len(usuarios)}")
        for usuario in usuarios:
            print(f"- ID: {usuario['id']}, Email: {usuario['email']}, Nome: {usuario.get('nome', 'N/A')}")
            print(f"  Empresa: {usuario.get('empresa', 'N/A')}, Firebase ID: {usuario.get('firebase_id', 'N/A')}")
            print("------")
        
        # 3. Verificar clientes
        print("\n==== CLIENTES NO SISTEMA ====")
        cursor.execute("SELECT id, nome, email, usuario_id FROM clientes LIMIT 10")
        clientes = cursor.fetchall()
        print(f"Total de clientes (primeiros 10): {len(clientes)}")
        for cliente in clientes:
            print(f"- ID: {cliente['id']}, Nome: {cliente['nome']}, Usuario ID: {cliente['usuario_id']}")
        
        # 4. Verificar se há um usuário específico
        email_buscado = "solanobicalho@yahoo.com.br"
        print(f"\n==== BUSCANDO USUÁRIO COM EMAIL: {email_buscado} ====")
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email_buscado,))
        usuario_encontrado = cursor.fetchone()
        
        if usuario_encontrado:
            print(f"✅ Usuário encontrado!")
            print(f"- ID: {usuario_encontrado['id']}")
            print(f"- Email: {usuario_encontrado['email']}")
            print(f"- Nome: {usuario_encontrado.get('nome', 'N/A')}")
            print(f"- Firebase ID: {usuario_encontrado.get('firebase_id', 'N/A')}")
            
            # 5. Buscar clientes deste usuário
            usuario_id = usuario_encontrado['id']
            print(f"\n==== CLIENTES DO USUÁRIO ID: {usuario_id} ====")
            cursor.execute("SELECT * FROM clientes WHERE usuario_id = %s", (usuario_id,))
            clientes_usuario = cursor.fetchall()
            print(f"Total de clientes: {len(clientes_usuario)}")
            
            for cliente in clientes_usuario:
                print(f"- ID: {cliente['id']}, Nome: {cliente['nome']}")
                print(f"  Email: {cliente.get('email', 'N/A')}, Telefone: {cliente.get('telefone', 'N/A')}")
                print("------")
        else:
            print(f"❌ Usuário {email_buscado} não encontrado!")
            print("\n==== AMOSTRA DE USUÁRIOS DISPONÍVEIS ====")
            cursor.execute("SELECT email FROM usuarios LIMIT 5")
            emails = cursor.fetchall()
            if emails:
                print("Alguns emails disponíveis:")
                for email in emails:
                    print(f"- {email['email']}")
            else:
                print("Nenhum usuário encontrado no banco.")
        
        # 6. Verificar estrutura de tabelas principais
        print("\n==== ESTRUTURA DA TABELA DE CLIENTES ====")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'clientes'
            ORDER BY ordinal_position
        """)
        colunas = cursor.fetchall()
        for col in colunas:
            print(f"- {col['column_name']} ({col['data_type']})")
        
        # 7. Verificar conexão com o Render
        print("\n==== INFORMAÇÕES DO SERVIDOR ====")
        cursor.execute("SELECT current_database(), current_user")
        db_info = cursor.fetchone()
        print(f"Banco de dados: {db_info['current_database']}")
        print(f"Usuário conectado: {db_info['current_user']}")
        
        # 8. Verificar índices na tabela de clientes
        print("\n==== ÍNDICES NA TABELA DE CLIENTES ====")
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'clientes'
        """)
        indices = cursor.fetchall()
        for idx in indices:
            print(f"- {idx['indexname']}: {idx['indexdef']}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        print("\nVerificação concluída com sucesso!")
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_dados_banco()