import psycopg2
import os
from psycopg2.extras import RealDictCursor

def verificar_usuario_firebase(firebase_id):
    """Verifica detalhes de um usuário específico do Firebase"""
    try:
        print(f"===== VERIFICAÇÃO DO USUÁRIO FIREBASE {firebase_id} =====")
        # Obter conexão do ambiente
        db_url = os.environ.get("DATABASE_URL")
        print(f"Conectando ao banco PostgreSQL...")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Verificar na tabela usuarios_firebase
        cursor.execute("""
            SELECT * FROM usuarios_firebase
            WHERE uid = %s
        """, (firebase_id,))
        
        firebase_user = cursor.fetchone()
        
        if firebase_user:
            print("✅ Usuário encontrado na tabela usuarios_firebase")
            print(f"- ID: {firebase_user.get('id', 'N/A')}")
            print(f"- UID: {firebase_user.get('uid', 'N/A')}")
            print(f"- Nome: {firebase_user.get('nome', 'N/A')}")
            print(f"- Email: {firebase_user.get('email', 'N/A')}")
            print(f"- Provedor: {firebase_user.get('provedor', 'N/A')}")
            print(f"- Criado em: {firebase_user.get('criado_em', 'N/A')}")
            print(f"- Último login: {firebase_user.get('ultimo_login', 'N/A')}")
            
            # Tentar encontrar na tabela usuarios
            firebase_email = firebase_user.get('email')
            if firebase_email:
                cursor.execute("""
                    SELECT * FROM usuarios
                    WHERE email = %s
                """, (firebase_email,))
                
                usuario_db = cursor.fetchone()
                
                if usuario_db:
                    print("\n✅ Usuário encontrado na tabela usuarios")
                    print(f"- ID: {usuario_db.get('id', 'N/A')}")
                    print(f"- Email: {usuario_db.get('email', 'N/A')}")
                    print(f"- Nome: {usuario_db.get('nome', 'N/A')}")
                    print(f"- Empresa: {usuario_db.get('empresa', 'N/A')}")
                else:
                    print("\n❌ Usuário não encontrado na tabela usuarios com o mesmo email")
        else:
            print(f"❌ Usuário com Firebase ID {firebase_id} não encontrado")
        
        # 2. Verificar clientes deste usuário
        print("\n==== CLIENTES DO USUÁRIO ====")
        cursor.execute("""
            SELECT * FROM clientes
            WHERE usuario_id = %s
            LIMIT 10
        """, (firebase_id,))
        
        clientes = cursor.fetchall()
        
        if clientes:
            print(f"✅ Encontrados {len(clientes)} clientes para este usuário")
            for cliente in clientes:
                print(f"- ID: {cliente.get('id', 'N/A')}, Nome: {cliente.get('nome', 'N/A')}")
                print(f"  Email: {cliente.get('email', 'N/A')}, Telefone: {cliente.get('telefone', 'N/A')}")
                print("  ---")
        else:
            print("❌ Nenhum cliente encontrado para este usuário")
        
        # 3. Verificar propostas deste usuário
        print("\n==== PROPOSTAS DO USUÁRIO ====")
        cursor.execute("""
            SELECT p.*, c.nome as cliente_nome
            FROM propostas p
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE p.usuario_id = %s
            LIMIT 10
        """, (firebase_id,))
        
        propostas = cursor.fetchall()
        
        if propostas:
            print(f"✅ Encontradas {len(propostas)} propostas para este usuário")
            for proposta in propostas:
                print(f"- ID: {proposta.get('id', 'N/A')}")
                print(f"  Cliente: {proposta.get('cliente_nome', 'N/A')}")
                print(f"  Descrição: {proposta.get('descricao', 'N/A')}")
                print(f"  Valor: {proposta.get('valor', 'N/A')}")
                print(f"  Status: {proposta.get('status', 'N/A')}")
                print("  ---")
        else:
            print("❌ Nenhuma proposta encontrada para este usuário")
            
        # 4. Verificar produtos deste usuário
        print("\n==== PRODUTOS DO USUÁRIO ====")
        cursor.execute("""
            SELECT *
            FROM produtos
            WHERE usuario_id = %s
            LIMIT 10
        """, (firebase_id,))
        
        produtos = cursor.fetchall()
        
        if produtos:
            print(f"✅ Encontrados {len(produtos)} produtos para este usuário")
            for produto in produtos:
                print(f"- ID: {produto.get('id', 'N/A')}")
                print(f"  Nome: {produto.get('nome', 'N/A')}")
                print(f"  Preço: {produto.get('preco_venda', 'N/A')}")
                print("  ---")
        else:
            print("❌ Nenhum produto encontrado para este usuário")
        
        # 5. Verificar uso geral deste ID em outras tabelas
        print("\n==== USO GERAL DO ID NAS TABELAS ====")
        
        other_tables = ['financeiro', 'vendas']
        
        for table in other_tables:
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM {table}
                WHERE usuario_id = %s
            """, (firebase_id,))
            
            total = cursor.fetchone()['total']
            
            print(f"Tabela {table}: {total} registros")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Usar o ID encontrado anteriormente
    verificar_usuario_firebase("2EaTVmLFJ5ReOjxQ3gaBzGqebsv1")