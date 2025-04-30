"""
Script para corrigir problemas de finalização de propostas no Render
Este script deve ser copiado para o ambiente Render e executado lá
"""
import os
import psycopg2
import sys
from datetime import datetime

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        conn.autocommit = True
        print("Conexão com o banco de dados estabelecida com sucesso")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)

def check_proposta_status(conn, proposta_id):
    """Verifica o status atual de uma proposta"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, status, data_inicio, data_proposta, data_finalizacao
        FROM propostas
        WHERE id = %s
    """, (proposta_id,))
    
    proposta = cursor.fetchone()
    if proposta:
        print(f"Proposta #{proposta[0]}:")
        print(f"  Status: {proposta[1]}")
        print(f"  Data início: {proposta[2]}")
        print(f"  Data proposta: {proposta[3]}")
        print(f"  Data finalização: {proposta[4]}")
    else:
        print(f"Proposta #{proposta_id} não encontrada")
    
    cursor.close()
    return proposta

def completar_finalizacao_proposta(conn, proposta_id):
    """
    Finaliza completamente uma proposta, garantindo que todos os campos e registros
    relacionados sejam atualizados corretamente.
    """
    cursor = conn.cursor()
    
    # Verificar se a proposta existe
    cursor.execute("SELECT id, status, usuario_id FROM propostas WHERE id = %s", (proposta_id,))
    proposta = cursor.fetchone()
    
    if not proposta:
        print(f"Proposta #{proposta_id} não encontrada")
        cursor.close()
        return False
    
    proposta_id, status, usuario_id = proposta
    
    print(f"Processando proposta #{proposta_id} (status atual: {status})")
    
    # Se já estiver finalizada, verifica se tem todos os campos necessários
    if status == 'Finalizada':
        print(f"Proposta #{proposta_id} já está marcada como finalizada")
        
        # Verificar data_finalizacao
        cursor.execute("""
            SELECT data_finalizacao FROM propostas WHERE id = %s
        """, (proposta_id,))
        data_finalizacao = cursor.fetchone()[0]
        
        if not data_finalizacao:
            data_atual = datetime.now().date()
            cursor.execute("""
                UPDATE propostas 
                SET data_finalizacao = %s
                WHERE id = %s
            """, (data_atual, proposta_id))
            print(f"  Adicionada data de finalização: {data_atual}")
        
        # Verificar se existe lançamento financeiro
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro 
            WHERE proposta_id = %s AND tipo = 'receita_a_receber'
        """, (proposta_id,))
        
        tem_lancamento = cursor.fetchone()[0] > 0
        
        if not tem_lancamento:
            # Criar lançamento financeiro
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                SELECT 
                    'Proposta #' || p.id || ' - ' || c.nome,
                    p.valor,
                    CURRENT_DATE,
                    'Serviços de Organização',
                    'receita_a_receber',
                    'Pendente',
                    p.id,
                    p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = %s
            """, (proposta_id,))
            print("  Adicionado lançamento financeiro")
    else:
        # Não está finalizada, fazer o processo completo
        
        # 1. Criar lançamento financeiro se não existir
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro 
            WHERE proposta_id = %s AND tipo = 'receita_a_receber'
        """, (proposta_id,))
        
        tem_lancamento = cursor.fetchone()[0] > 0
        
        if not tem_lancamento:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                SELECT 
                    'Proposta #' || p.id || ' - ' || c.nome,
                    p.valor,
                    CURRENT_DATE,
                    'Serviços de Organização',
                    'receita_a_receber',
                    'Pendente',
                    p.id,
                    p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = %s
            """, (proposta_id,))
            print("  Criado lançamento financeiro")
        
        # 2. Atualizar status e data de finalização
        data_atual = datetime.now().date()
        cursor.execute("""
            UPDATE propostas 
            SET status = 'Finalizada',
                data_finalizacao = %s
            WHERE id = %s
        """, (data_atual, proposta_id))
        print(f"  Atualizado status para 'Finalizada' e data_finalizacao para {data_atual}")
    
    # Garantir que a data_proposta esteja preenchida
    cursor.execute("""
        SELECT data_proposta, data_inicio FROM propostas WHERE id = %s
    """, (proposta_id,))
    dados = cursor.fetchone()
    data_proposta, data_inicio = dados
    
    if not data_proposta and data_inicio:
        cursor.execute("""
            UPDATE propostas SET data_proposta = %s WHERE id = %s
        """, (data_inicio, proposta_id))
        print(f"  Atualizada data_proposta para {data_inicio}")
    
    cursor.close()
    print(f"Proposta #{proposta_id} finalizada com sucesso")
    return True

def finalizar_todas_propostas(conn):
    """Finaliza todas as propostas em execução ou análise"""
    cursor = conn.cursor()
    
    # Buscar propostas não finalizadas
    cursor.execute("""
        SELECT id, status FROM propostas 
        WHERE status IN ('Em execução', 'Em análise')
        ORDER BY id
    """)
    
    propostas = cursor.fetchall()
    cursor.close()
    
    if not propostas:
        print("Não há propostas para finalizar")
        return
    
    print(f"Encontradas {len(propostas)} propostas não finalizadas")
    
    sucessos = 0
    falhas = 0
    
    for proposta in propostas:
        proposta_id = proposta[0]
        if completar_finalizacao_proposta(conn, proposta_id):
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
    print("1. Verificar status de uma proposta")
    print("2. Finalizar uma proposta específica")
    print("3. Finalizar todas as propostas pendentes")
    print("4. Sair")
    return input("Escolha uma opção: ")

def main():
    """Função principal"""
    print("\n==== Script de Correção de Propostas no Render ====")
    print("Este script corrige problemas de finalização de propostas")
    
    # Obter conexão com o banco
    conn = get_db_connection()
    
    while True:
        opcao = mostrar_menu()
        
        if opcao == '1':
            proposta_id = input("Digite o ID da proposta para verificar: ")
            try:
                proposta_id = int(proposta_id)
                check_proposta_status(conn, proposta_id)
            except ValueError:
                print("ID inválido. Digite um número inteiro.")
        
        elif opcao == '2':
            proposta_id = input("Digite o ID da proposta a finalizar: ")
            try:
                proposta_id = int(proposta_id)
                completar_finalizacao_proposta(conn, proposta_id)
            except ValueError:
                print("ID inválido. Digite um número inteiro.")
        
        elif opcao == '3':
            confirma = input("Tem certeza que deseja finalizar TODAS as propostas pendentes? (s/n): ")
            if confirma.lower() == 's':
                finalizar_todas_propostas(conn)
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