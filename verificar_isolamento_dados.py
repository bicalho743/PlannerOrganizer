import streamlit as st
import psycopg2
import os
from psycopg2.extras import RealDictCursor

def conectar_db():
    """Conecta diretamente ao banco de dados usando psycopg2"""
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
        return None

def verificar_usuario_dados():
    """Verifica como os dados do usuário estão armazenados e isolados no banco"""
    conn = conectar_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar usuários no banco
        st.subheader("Verificação de Usuários")
        cursor.execute("SELECT id, email, role FROM usuarios")
        usuarios = cursor.fetchall()
        
        if not usuarios:
            st.warning("Nenhum usuário encontrado no banco de dados")
        else:
            st.success(f"Encontrados {len(usuarios)} usuários no banco")
            
            # Mostrar usuários encontrados
            st.write("##### Usuários cadastrados:")
            for u in usuarios:
                st.write(f"- ID: {u['id']}, Email: {u['email']}, Role: {u['role']}")
            
            # Para o usuário atual, mostrar mais detalhes
            email_atual = 'solanobicalho@yahoo.com.br'
            st.write("##### Informações do usuário atual:")
            cursor.execute("SELECT id, email, role, nome, empresa FROM usuarios WHERE email = %s", (email_atual,))
            usuario_atual = cursor.fetchone()
            
            if usuario_atual:
                st.write(f"ID: {usuario_atual['id']}")
                st.write(f"Email: {usuario_atual['email']}")
                st.write(f"Nome: {usuario_atual['nome']}")
                st.write(f"Empresa: {usuario_atual['empresa']}")
                st.write(f"Role: {usuario_atual['role']}")
                
                # Verificar cliente para este usuário
                usuario_id = usuario_atual['id']
                
                # Verificar quantos clientes este usuário tem
                cursor.execute("SELECT COUNT(*) as total FROM clientes WHERE usuario_id = %s", (usuario_id,))
                total_clientes = cursor.fetchone()['total']
                
                st.subheader(f"Clientes do usuário ({total_clientes} registros)")
                if total_clientes > 0:
                    # Listar os clientes deste usuário
                    cursor.execute("SELECT id, nome, email, telefone FROM clientes WHERE usuario_id = %s LIMIT 10", (usuario_id,))
                    clientes = cursor.fetchall()
                    
                    for cliente in clientes:
                        st.write(f"- Cliente ID: {cliente['id']}, Nome: {cliente['nome']}")
                        st.write(f"  Email: {cliente['email']}, Telefone: {cliente['telefone']}")
                        st.write("---")
                    
                    # Verificar se há clientes de outros usuários com mesmo nome
                    for cliente in clientes[:2]:  # Verificar apenas os 2 primeiros para não sobrecarregar
                        cursor.execute("""
                            SELECT c.id, c.nome, c.email, u.email as usuario_email 
                            FROM clientes c
                            JOIN usuarios u ON c.usuario_id = u.id
                            WHERE c.nome = %s AND c.usuario_id != %s
                        """, (cliente['nome'], usuario_id))
                        
                        clientes_outros = cursor.fetchall()
                        if clientes_outros:
                            st.warning(f"⚠️ Encontrados clientes de mesmo nome em outros usuários!")
                            for c in clientes_outros:
                                st.write(f"- Cliente: {c['nome']}, Usuário: {c['usuario_email']}")
                        else:
                            st.success(f"✓ Cliente '{cliente['nome']}' isolado corretamente")
                
                # Verificar propostas para este usuário
                cursor.execute("SELECT COUNT(*) as total FROM propostas WHERE usuario_id = %s", (usuario_id,))
                total_propostas = cursor.fetchone()['total']
                
                st.subheader(f"Propostas do usuário ({total_propostas} registros)")
                if total_propostas > 0:
                    cursor.execute("""
                        SELECT p.id, p.descricao, c.nome as cliente_nome, p.status
                        FROM propostas p
                        JOIN clientes c ON p.cliente_id = c.id
                        WHERE p.usuario_id = %s
                        LIMIT 5
                    """, (usuario_id,))
                    
                    propostas = cursor.fetchall()
                    for proposta in propostas:
                        st.write(f"- Proposta #{proposta['id']}, Cliente: {proposta['cliente_nome']}")
                        st.write(f"  Status: {proposta['status']}, Descrição: {proposta['descricao']}")
                        st.write("---")
                
                # Verificar se há propostas vinculadas a clientes de outros usuários (isso seria um problema)
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM propostas p
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.usuario_id = %s AND c.usuario_id != %s
                """, (usuario_id, usuario_id))
                
                propostas_problema = cursor.fetchone()['total']
                if propostas_problema > 0:
                    st.error(f"⚠️ ALERTA: Encontradas {propostas_problema} propostas vinculadas a clientes de outros usuários!")
                else:
                    st.success("✓ Todas as propostas estão vinculadas corretamente a clientes do mesmo usuário")
                    
                # Verificar schema do banco
                st.subheader("Estrutura do banco de dados")
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'clientes'
                """)
                
                st.write("##### Estrutura da tabela clientes:")
                for col in cursor.fetchall():
                    st.write(f"- {col['column_name']} ({col['data_type']})")
                
                # Verificar se há coluna usuario_id nas tabelas principais
                cursor.execute("""
                    SELECT table_name, column_name
                    FROM information_schema.columns 
                    WHERE column_name = 'usuario_id'
                    AND table_name IN ('clientes', 'propostas', 'financeiro', 'vendas', 'produtos')
                """)
                
                tabelas_com_usuario_id = cursor.fetchall()
                st.write("##### Tabelas com coluna usuario_id:")
                for tabela in tabelas_com_usuario_id:
                    st.write(f"- {tabela['table_name']}")
                
                if len(tabelas_com_usuario_id) >= 5:  # As 5 tabelas principais devem ter usuario_id
                    st.success("✓ Todas as tabelas principais contêm a coluna usuario_id para isolamento de dados")
                else:
                    st.warning("⚠️ Algumas tabelas importantes parecem não ter coluna usuario_id")
                
            else:
                st.error(f"Usuário com email {email_atual} não encontrado no banco")
    
    except Exception as e:
        st.error(f"Erro ao verificar dados: {e}")
    finally:
        if conn:
            conn.close()

def main():
    st.set_page_config(
        page_title="Verificação de Isolamento de Dados",
        page_icon="🔒",
        layout="wide"
    )
    
    st.title("Verificação de Isolamento de Dados no PostgreSQL")
    st.write("""
    Esta ferramenta verifica se os dados estão corretamente isolados por usuário no banco PostgreSQL,
    garantindo que cada cliente tenha acesso apenas aos seus próprios dados.
    """)
    
    if st.button("Verificar Isolamento de Dados", type="primary"):
        verificar_usuario_dados()
    
    st.write("---")
    st.info("""
    **Como funciona o isolamento de dados?**
    
    O sistema utiliza a coluna `usuario_id` em todas as tabelas principais para garantir que 
    cada usuário só veja e acesse seus próprios dados. Isso é conhecido como 
    "Tenant Isolation" ou "Multi-Tenancy" no modelo SaaS.
    
    Quando você faz login, o sistema registra seu ID de usuário na sessão e 
    filtra todas as consultas ao banco usando este ID.
    """)

if __name__ == "__main__":
    main()