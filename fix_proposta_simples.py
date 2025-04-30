"""
Script simplificado para finalizar propostas diretamente via psycopg2
Este script é uma versão minimalista que deve funcionar mesmo em ambientes
com problemas de configuração do SQLAlchemy ou outros ORMs
"""
import os
import sys
import psycopg2
from datetime import datetime

def get_db_connection():
    """Estabelece conexão direta com o banco de dados"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Erro: Variável de ambiente DATABASE_URL não encontrada")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        print("Conexão com o banco de dados estabelecida com sucesso")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)

def detectar_estrutura_financeiro(conn):
    """Detecta a estrutura atual da tabela financeiro"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
            ORDER BY ordinal_position;
        """)
        colunas = [row[0] for row in cursor.fetchall()]
        print(f"Colunas da tabela financeiro: {', '.join(colunas)}")
        tem_forma_pagamento = 'forma_pagamento' in colunas
        tem_usuario_id = 'usuario_id' in colunas
        return tem_forma_pagamento, tem_usuario_id
    except Exception as e:
        print(f"Erro ao detectar estrutura da tabela financeiro: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def listar_propostas_nao_finalizadas(conn):
    """Lista propostas não finalizadas"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.id, p.descricao, p.valor, p.status, c.nome as cliente_nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.status <> 'Finalizada'
            ORDER BY p.id DESC;
        """)
        propostas = cursor.fetchall()
        
        if not propostas:
            print("Não há propostas pendentes para finalizar")
            return []
        
        print(f"Encontradas {len(propostas)} propostas não finalizadas:")
        for p in propostas:
            print(f"  #{p[0]} - {p[4]} - R$ {p[2]} - Status: {p[3]}")
        
        return propostas
    except Exception as e:
        print(f"Erro ao listar propostas: {e}")
        return []
    finally:
        cursor.close()

def finalizar_proposta(conn, proposta_id, tem_forma_pagamento, tem_usuario_id):
    """Finaliza uma proposta específica"""
    cursor = conn.cursor()
    try:
        # Verificar se a proposta existe e não está finalizada
        cursor.execute("""
            SELECT p.id, p.valor, p.usuario_id, c.nome as cliente_nome, p.status
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s;
        """, (proposta_id,))
        
        proposta = cursor.fetchone()
        if not proposta:
            print(f"Proposta #{proposta_id} não encontrada")
            return False
        
        print(f"Dados da proposta #{proposta_id}:")
        print(f"  Cliente: {proposta[3]}")
        print(f"  Valor: R$ {proposta[1]}")
        print(f"  Status atual: {proposta[4]}")
        
        if proposta[4] == 'Finalizada':
            print(f"Proposta #{proposta_id} já está finalizada")
            return True
        
        # Verificar se já existe lançamento financeiro para esta proposta
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro
            WHERE proposta_id = %s AND tipo = 'receita_a_receber';
        """, (proposta_id,))
        
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Proposta #{proposta_id} já possui lançamento financeiro")
        else:
            # Construir a consulta de acordo com a estrutura da tabela
            colunas = ['descricao', 'valor', 'data', 'categoria', 'tipo', 'status', 'proposta_id']
            valores = [
                f"Proposta #{proposta_id} - {proposta[3]}",
                proposta[1],
                datetime.now().date(),
                'Serviços de Organização',
                'receita_a_receber',
                'Pendente',
                proposta_id
            ]
            
            if tem_usuario_id:
                colunas.append('usuario_id')
                valores.append(proposta[2])
            
            if tem_forma_pagamento:
                colunas.append('forma_pagamento')
                valores.append('')
            
            colunas_str = ', '.join(colunas)
            placeholders = ', '.join(['%s'] * len(valores))
            
            query = f"INSERT INTO financeiro ({colunas_str}) VALUES ({placeholders})"
            cursor.execute(query, valores)
            print(f"Lançamento financeiro criado para proposta #{proposta_id}")
        
        # Atualizar status da proposta
        cursor.execute("""
            UPDATE propostas SET status = 'Finalizada' WHERE id = %s
        """, (proposta_id,))
        print(f"Proposta #{proposta_id} finalizada com sucesso")
        
        return True
    except Exception as e:
        print(f"Erro ao finalizar proposta #{proposta_id}: {e}")
        return False
    finally:
        cursor.close()

def finalizar_todas_propostas(conn, tem_forma_pagamento, tem_usuario_id):
    """Finaliza todas as propostas não finalizadas"""
    propostas = listar_propostas_nao_finalizadas(conn)
    if not propostas:
        return
    
    sucessos = 0
    falhas = 0
    
    for p in propostas:
        proposta_id = p[0]
        print(f"\nProcessando proposta #{proposta_id}...")
        
        if finalizar_proposta(conn, proposta_id, tem_forma_pagamento, tem_usuario_id):
            sucessos += 1
        else:
            falhas += 1
    
    print(f"\nResumo da operação:")
    print(f"  Propostas processadas: {len(propostas)}")
    print(f"  Sucessos: {sucessos}")
    print(f"  Falhas: {falhas}")

def mostrar_menu():
    """Mostra o menu de opções"""
    print("\n==== Menu de Operações ====")
    print("1. Listar propostas não finalizadas")
    print("2. Finalizar uma proposta específica")
    print("3. Finalizar todas as propostas pendentes")
    print("4. Sair")
    return input("Escolha uma opção: ")

def main():
    """Função principal"""
    print("\n==== Script de Finalização de Propostas ====")
    print("Este script contorna problemas do SQLAlchemy e finaliza propostas diretamente via SQL")
    
    # Obter conexão com o banco
    conn = get_db_connection()
    
    # Detectar estrutura da tabela financeiro
    tem_forma_pagamento, tem_usuario_id = detectar_estrutura_financeiro(conn)
    
    while True:
        opcao = mostrar_menu()
        
        if opcao == '1':
            listar_propostas_nao_finalizadas(conn)
        
        elif opcao == '2':
            proposta_id = input("Digite o ID da proposta a finalizar: ")
            try:
                proposta_id = int(proposta_id)
                finalizar_proposta(conn, proposta_id, tem_forma_pagamento, tem_usuario_id)
            except ValueError:
                print("ID inválido. Digite um número inteiro.")
        
        elif opcao == '3':
            confirma = input("Tem certeza que deseja finalizar TODAS as propostas pendentes? (s/n): ")
            if confirma.lower() == 's':
                finalizar_todas_propostas(conn, tem_forma_pagamento, tem_usuario_id)
            else:
                print("Operação cancelada.")
        
        elif opcao == '4':
            print("Encerrando script...")
            break
        
        else:
            print("Opção inválida. Tente novamente.")
    
    conn.close()

if __name__ == "__main__":
    main()