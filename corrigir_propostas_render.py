"""
Script autônomo para corrigir propostas no Render
Este script corrige problemas de finalização e exibição de propostas no Render
É uma solução completa que não requer DBeaver ou SQL direto
"""
import os
import sys
import psycopg2
from datetime import datetime

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERRO: Variável de ambiente DATABASE_URL não encontrada")
            sys.exit(1)
            
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Auto-commit para simplificar
        print("✅ Conexão com o banco de dados estabelecida com sucesso")
        return conn
    except Exception as e:
        print(f"❌ ERRO ao conectar ao banco de dados: {e}")
        sys.exit(1)

def verificar_estrutura_banco(conn):
    """Verifica a estrutura das tabelas relevantes"""
    cursor = conn.cursor()
    try:
        # Verificar tabela propostas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
            ORDER BY ordinal_position;
        """)
        colunas_propostas = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tabela 'propostas' encontrada com {len(colunas_propostas)} colunas")
        
        # Verificar campos essenciais
        campos_essenciais = ['id', 'status', 'data_inicio', 'data_proposta', 'data_finalizacao', 'usuario_id']
        campos_faltantes = [campo for campo in campos_essenciais if campo not in colunas_propostas]
        
        if campos_faltantes:
            print(f"⚠️ ATENÇÃO: A tabela 'propostas' não tem os campos: {', '.join(campos_faltantes)}")
        else:
            print("✅ Todos os campos essenciais encontrados na tabela 'propostas'")
        
        # Verificar tabela financeiro
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
            ORDER BY ordinal_position;
        """)
        colunas_financeiro = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tabela 'financeiro' encontrada com {len(colunas_financeiro)} colunas")
        
        # Verificar campos essenciais para financeiro
        campos_financeiro = ['id', 'descricao', 'valor', 'data', 'categoria', 'tipo', 'status', 'proposta_id', 'usuario_id']
        campos_faltantes = [campo for campo in campos_financeiro if campo not in colunas_financeiro]
        
        if campos_faltantes:
            print(f"⚠️ ATENÇÃO: A tabela 'financeiro' não tem os campos: {', '.join(campos_faltantes)}")
        else:
            print("✅ Todos os campos essenciais encontrados na tabela 'financeiro'")
            
        return {
            'propostas': colunas_propostas,
            'financeiro': colunas_financeiro
        }
    except Exception as e:
        print(f"❌ ERRO ao verificar estrutura do banco: {e}")
        return None
    finally:
        cursor.close()

def identificar_propostas_problematicas(conn):
    """Identifica propostas com problemas de exibição na interface"""
    cursor = conn.cursor()
    try:
        # Propostas com inconsistências em campos de data
        cursor.execute("""
            SELECT id, status, data_inicio, data_proposta, data_finalizacao, usuario_id
            FROM propostas
            WHERE 
                (status = 'Finalizada' AND data_finalizacao IS NULL)
                OR (status = 'Finalizada' AND data_proposta IS NULL)
                OR (status = 'Em execução' AND data_finalizacao IS NOT NULL)
            ORDER BY id DESC;
        """)
        
        propostas_inconsistentes = cursor.fetchall()
        
        # Propostas finalizadas sem lançamentos financeiros
        cursor.execute("""
            SELECT p.id, p.status, p.valor, c.nome as cliente_nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
            WHERE p.status = 'Finalizada' AND f.id IS NULL
            ORDER BY p.id DESC;
        """)
        
        propostas_sem_lancamentos = cursor.fetchall()
        
        if propostas_inconsistentes:
            print(f"\n⚠️ Encontradas {len(propostas_inconsistentes)} propostas com inconsistências em datas:")
            for p in propostas_inconsistentes:
                print(f"  - Proposta #{p[0]}: status={p[1]}, inicio={p[2]}, proposta={p[3]}, finalização={p[4]}")
        else:
            print("\n✅ Nenhuma proposta com inconsistências em datas encontrada")
            
        if propostas_sem_lancamentos:
            print(f"\n⚠️ Encontradas {len(propostas_sem_lancamentos)} propostas finalizadas sem lançamentos financeiros:")
            for p in propostas_sem_lancamentos:
                print(f"  - Proposta #{p[0]}: valor={p[2]}, cliente={p[3]}")
        else:
            print("\n✅ Nenhuma proposta finalizada sem lançamentos financeiros")
            
        return propostas_inconsistentes, propostas_sem_lancamentos
    except Exception as e:
        print(f"❌ ERRO ao identificar propostas problemáticas: {e}")
        return [], []
    finally:
        cursor.close()

def corrigir_todas_propostas(conn):
    """Corrige todas as propostas com problemas de exibição na interface"""
    cursor = conn.cursor()
    data_atual = datetime.now().date()
    
    try:
        # 1. Garantir que todas as propostas finalizadas tenham data_finalizacao
        cursor.execute("""
            UPDATE propostas 
            SET data_finalizacao = %s
            WHERE status = 'Finalizada' AND data_finalizacao IS NULL
            RETURNING id;
        """, (data_atual,))
        
        propostas_atualizadas = cursor.fetchall()
        if propostas_atualizadas:
            print(f"✅ Adicionada data_finalizacao para {len(propostas_atualizadas)} propostas")
            for p in propostas_atualizadas:
                print(f"  - Proposta #{p[0]}")
        
        # 2. Garantir que todas as propostas finalizadas tenham data_proposta
        cursor.execute("""
            UPDATE propostas 
            SET data_proposta = COALESCE(data_inicio, %s)
            WHERE status = 'Finalizada' AND data_proposta IS NULL
            RETURNING id;
        """, (data_atual,))
        
        propostas_atualizadas = cursor.fetchall()
        if propostas_atualizadas:
            print(f"✅ Adicionada data_proposta para {len(propostas_atualizadas)} propostas")
            for p in propostas_atualizadas:
                print(f"  - Proposta #{p[0]}")
        
        # 3. Remover data_finalizacao de propostas não finalizadas
        cursor.execute("""
            UPDATE propostas 
            SET data_finalizacao = NULL
            WHERE status <> 'Finalizada' AND data_finalizacao IS NOT NULL
            RETURNING id;
        """)
        
        propostas_atualizadas = cursor.fetchall()
        if propostas_atualizadas:
            print(f"✅ Removida data_finalizacao de {len(propostas_atualizadas)} propostas não finalizadas")
            for p in propostas_atualizadas:
                print(f"  - Proposta #{p[0]}")
        
        # 4. Criar lançamentos financeiros para propostas finalizadas que não os têm
        cursor.execute("""
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
            SELECT 
                'Proposta #' || p.id || ' - ' || c.nome,
                p.valor,
                COALESCE(p.data_finalizacao, %s),
                'Serviços de Organização',
                'receita_a_receber',
                'Pendente',
                p.id,
                p.usuario_id
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
            WHERE p.status = 'Finalizada' AND f.id IS NULL
            RETURNING proposta_id;
        """, (data_atual,))
        
        lancamentos_criados = cursor.fetchall()
        if lancamentos_criados:
            print(f"✅ Criados lançamentos financeiros para {len(lancamentos_criados)} propostas")
            for p in lancamentos_criados:
                print(f"  - Proposta #{p[0]}")
        
        # 5. Corrigir propostas com status incorreto baseado na data_finalizacao
        cursor.execute("""
            UPDATE propostas
            SET status = 'Finalizada'
            WHERE status = 'Em análise' AND data_finalizacao IS NOT NULL
            RETURNING id;
        """)
        
        propostas_atualizadas = cursor.fetchall()
        if propostas_atualizadas:
            print(f"✅ Corrigido status para 'Finalizada' em {len(propostas_atualizadas)} propostas")
            for p in propostas_atualizadas:
                print(f"  - Proposta #{p[0]}")
        
        print("\n✅ Correção de todas as propostas concluída com sucesso")
        return True
    except Exception as e:
        print(f"❌ ERRO ao corrigir propostas: {e}")
        return False
    finally:
        cursor.close()

def corrigir_proposta_especifica(conn, proposta_id):
    """Corrige uma proposta específica"""
    cursor = conn.cursor()
    data_atual = datetime.now().date()
    
    try:
        # Verificar se a proposta existe
        cursor.execute("""
            SELECT id, status, data_inicio, data_proposta, data_finalizacao, usuario_id
            FROM propostas
            WHERE id = %s;
        """, (proposta_id,))
        
        proposta = cursor.fetchone()
        if not proposta:
            print(f"❌ Proposta #{proposta_id} não encontrada")
            return False
        
        proposta_id, status, data_inicio, data_proposta, data_finalizacao, usuario_id = proposta
        
        print(f"\n🔍 Proposta #{proposta_id}:")
        print(f"  - Status: {status}")
        print(f"  - Data início: {data_inicio}")
        print(f"  - Data proposta: {data_proposta}")
        print(f"  - Data finalização: {data_finalizacao}")
        
        # Verificar se já está finalizada
        if status == 'Finalizada':
            # Garantir data_finalizacao
            if data_finalizacao is None:
                cursor.execute("""
                    UPDATE propostas 
                    SET data_finalizacao = %s
                    WHERE id = %s;
                """, (data_atual, proposta_id))
                print(f"✅ Adicionada data_finalizacao: {data_atual}")
            
            # Garantir data_proposta
            if data_proposta is None:
                nova_data = data_inicio if data_inicio else data_atual
                cursor.execute("""
                    UPDATE propostas 
                    SET data_proposta = %s
                    WHERE id = %s;
                """, (nova_data, proposta_id))
                print(f"✅ Adicionada data_proposta: {nova_data}")
        else:
            # Se não está finalizada, perguntar se deseja finalizar
            finalizar = input(f"Proposta #{proposta_id} não está finalizada. Deseja finalizá-la? (s/n): ")
            if finalizar.lower() == 's':
                cursor.execute("""
                    UPDATE propostas 
                    SET status = 'Finalizada',
                        data_finalizacao = %s,
                        data_proposta = COALESCE(data_proposta, data_inicio, %s)
                    WHERE id = %s;
                """, (data_atual, data_atual, proposta_id))
                print(f"✅ Proposta #{proposta_id} finalizada com sucesso")
                status = 'Finalizada'  # Atualizar para usar nas próximas verificações
            else:
                # Se não finalizar, apenas remover data_finalizacao se existir
                if data_finalizacao is not None:
                    cursor.execute("""
                        UPDATE propostas 
                        SET data_finalizacao = NULL
                        WHERE id = %s;
                    """, (proposta_id,))
                    print(f"✅ Removida data_finalizacao da proposta #{proposta_id}")
        
        # Verificar/criar lançamento financeiro se a proposta estiver finalizada
        if status == 'Finalizada':
            cursor.execute("""
                SELECT id FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber';
            """, (proposta_id,))
            
            lancamento = cursor.fetchone()
            if not lancamento:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    SELECT 
                        'Proposta #' || p.id || ' - ' || c.nome,
                        p.valor,
                        COALESCE(p.data_finalizacao, %s),
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        p.id,
                        p.usuario_id
                    FROM propostas p
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.id = %s;
                """, (data_atual, proposta_id))
                print(f"✅ Criado lançamento financeiro para proposta #{proposta_id}")
            else:
                print(f"✅ Proposta já possui lançamento financeiro")
        
        print(f"\n✅ Proposta #{proposta_id} corrigida com sucesso")
        return True
    except Exception as e:
        print(f"❌ ERRO ao corrigir proposta #{proposta_id}: {e}")
        return False
    finally:
        cursor.close()
        
def forcar_proposta_finalizada(conn, proposta_id):
    """Força uma proposta a aparecer como finalizada (último recurso)"""
    cursor = conn.cursor()
    data_atual = datetime.now().date()
    
    try:
        # Verificar se a proposta existe
        cursor.execute("""
            SELECT id FROM propostas WHERE id = %s;
        """, (proposta_id,))
        
        if not cursor.fetchone():
            print(f"❌ Proposta #{proposta_id} não encontrada")
            return False
        
        # Forçar finalização completa
        cursor.execute("""
            UPDATE propostas 
            SET 
                status = 'Finalizada',
                data_finalizacao = %s,
                data_proposta = COALESCE(data_proposta, data_inicio, %s),
                ativo = TRUE
            WHERE id = %s;
        """, (data_atual, data_atual, proposta_id))
        
        # Garantir lançamento financeiro
        cursor.execute("""
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
            SELECT 
                'Proposta #' || p.id || ' - ' || c.nome,
                p.valor,
                %s,
                'Serviços de Organização',
                'receita_a_receber',
                'Pendente',
                p.id,
                p.usuario_id
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
            AND NOT EXISTS (
                SELECT 1 FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber'
            );
        """, (data_atual, proposta_id, proposta_id))
        
        print(f"✅ Proposta #{proposta_id} FORÇADA como finalizada com sucesso")
        return True
    except Exception as e:
        print(f"❌ ERRO ao forçar proposta #{proposta_id}: {e}")
        return False
    finally:
        cursor.close()

def mostrar_menu():
    """Exibe o menu de opções"""
    print("\n==== MENU DE CORREÇÃO DE PROPOSTAS ====")
    print("1. Verificar estrutura do banco de dados")
    print("2. Identificar propostas com problemas")
    print("3. Corrigir TODAS as propostas problemáticas")
    print("4. Corrigir uma proposta específica")
    print("5. FORÇAR uma proposta como finalizada (último recurso)")
    print("6. Sair")
    return input("\nEscolha uma opção (1-6): ")

def main():
    """Função principal"""
    print("\n========================================")
    print("   CORREÇÃO DE PROPOSTAS NO RENDER")
    print("========================================")
    print("Este script corrige problemas de finalização e exibição de propostas.")
    
    # Conectar ao banco de dados
    conn = get_db_connection()
    
    while True:
        opcao = mostrar_menu()
        
        if opcao == '1':
            verificar_estrutura_banco(conn)
        
        elif opcao == '2':
            identificar_propostas_problematicas(conn)
        
        elif opcao == '3':
            confirmacao = input("\n⚠️ AVISO: Isso corrigirá TODAS as propostas. Continuar? (s/n): ")
            if confirmacao.lower() == 's':
                corrigir_todas_propostas(conn)
            else:
                print("Operação cancelada")
        
        elif opcao == '4':
            try:
                proposta_id = int(input("\nDigite o ID da proposta a corrigir: "))
                corrigir_proposta_especifica(conn, proposta_id)
            except ValueError:
                print("❌ Por favor, digite um número válido")
        
        elif opcao == '5':
            try:
                proposta_id = int(input("\n⚠️ AVISO: Esta é uma operação de ÚLTIMO RECURSO.\nDigite o ID da proposta a forçar como finalizada: "))
                confirmacao = input(f"Tem certeza que deseja FORÇAR a proposta #{proposta_id} como finalizada? (s/n): ")
                if confirmacao.lower() == 's':
                    forcar_proposta_finalizada(conn, proposta_id)
                else:
                    print("Operação cancelada")
            except ValueError:
                print("❌ Por favor, digite um número válido")
        
        elif opcao == '6':
            print("\nEncerrando script...")
            break
        
        else:
            print("\n❌ Opção inválida. Por favor, escolha uma opção de 1 a 6.")
    
    # Fechar conexão
    conn.close()
    print("\n✅ Finalizado com sucesso!")

if __name__ == "__main__":
    main()