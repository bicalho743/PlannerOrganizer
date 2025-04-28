# Solução para Problemas de Finalização de Propostas no Render

Este documento contém a solução para os problemas de finalização de propostas no ambiente Render. A solução é um script Python que pode ser executado diretamente no console do Render.

## O Problema

Algumas propostas marcadas como "Finalizadas" não estão aparecendo corretamente na interface ou não estão gerando os lançamentos financeiros esperados. Isso ocorre por algumas inconsistências no banco de dados:

1. Propostas finalizadas sem data de finalização (data_finalizacao)
2. Propostas finalizadas sem data da proposta (data_proposta)
3. Propostas finalizadas sem lançamentos financeiros associados

## A Solução

O script abaixo faz uma verificação completa da estrutura do banco de dados e corrige todos esses problemas automaticamente. Ele é adaptativo e funciona mesmo que a estrutura do banco seja diferente entre ambientes.

```python
"""
Script de correção para o problema de finalização de propostas no Render.
Este script é uma versão simplificada que pode ser executada diretamente no console do Render
"""
import os
import psycopg2
from datetime import datetime

def executar_correcao():
    """Executa a correção para o problema de finalização de propostas"""
    # Verificar DATABASE_URL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("ERRO: DATABASE_URL não encontrada nas variáveis de ambiente")
        return
    
    print("Conectando ao banco de dados...")
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Verificando estrutura da tabela financeiro...")
        
        # Verificar campos da tabela financeiro
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
        """)
        colunas_financeiro = [row[0] for row in cursor.fetchall()]
        
        print(f"Colunas encontradas: {', '.join(colunas_financeiro)}")
        
        # Primeiro, verificar se a coluna data_finalizacao existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
        """)
        colunas_propostas = [row[0] for row in cursor.fetchall()]
        
        print(f"Colunas encontradas na tabela propostas: {', '.join(colunas_propostas)}")
        
        # Verificar propostas com problemas usando consultas adequadas à estrutura
        print("Identificando propostas com problemas...")
        if 'data_finalizacao' in colunas_propostas:
            cursor.execute("""
                SELECT p.id, p.descricao, p.status, c.nome as cliente_nome
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE (p.status = 'Finalizada' AND p.data_finalizacao IS NULL)
                   OR (p.status = 'Finalizada' AND (
                       NOT EXISTS (
                           SELECT 1 FROM financeiro f 
                           WHERE f.proposta_id = p.id AND f.tipo = 'receita_a_receber'
                       )
                   ))
                ORDER BY p.id DESC;
            """)
        else:
            cursor.execute("""
                SELECT p.id, p.descricao, p.status, c.nome as cliente_nome
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.status = 'Finalizada' AND (
                       NOT EXISTS (
                           SELECT 1 FROM financeiro f 
                           WHERE f.proposta_id = p.id AND f.tipo = 'receita_a_receber'
                       )
                   )
                ORDER BY p.id DESC;
            """)
        
        propostas_problematicas = cursor.fetchall()
        
        if propostas_problematicas:
            print(f"\nEncontradas {len(propostas_problematicas)} propostas com problemas:")
            for p in propostas_problematicas:
                print(f"  Proposta #{p[0]} - {p[3]} - Status: {p[2]}")
                
            print("\nCorrigindo propostas com problemas...")
            data_atual = datetime.now().date()
            
            # Atualizar data_finalizacao para propostas finalizadas sem data
            if 'data_finalizacao' in colunas_propostas:
                cursor.execute("""
                    UPDATE propostas 
                    SET data_finalizacao = %s
                    WHERE status = 'Finalizada' AND data_finalizacao IS NULL
                    RETURNING id;
                """, (data_atual,))
                
                atualizadas = cursor.fetchall()
                if atualizadas:
                    print(f"  Adicionada data_finalizacao para {len(atualizadas)} propostas")
            
            # Atualizar data_proposta para propostas finalizadas sem data
            if 'data_proposta' in colunas_propostas:
                cursor.execute("""
                    UPDATE propostas 
                    SET data_proposta = COALESCE(data_inicio, %s)
                    WHERE status = 'Finalizada' AND data_proposta IS NULL
                    RETURNING id;
                """, (data_atual,))
                
                atualizadas = cursor.fetchall()
                if atualizadas:
                    print(f"  Adicionada data_proposta para {len(atualizadas)} propostas")
            
            # Criar lançamentos financeiros para propostas finalizadas que não os têm
            has_forma_pagamento = 'forma_pagamento' in colunas_financeiro
            
            # Construir a consulta SQL com base nas colunas existentes
            if has_forma_pagamento:
                sql_insert = """
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                    SELECT 
                        'Proposta #' || p.id || ' - ' || c.nome,
                        p.valor,
                        %s,
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        '',
                        p.id,
                        p.usuario_id
                    FROM propostas p
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE p.status = 'Finalizada' 
                    AND NOT EXISTS (
                        SELECT 1 FROM financeiro f 
                        WHERE f.proposta_id = p.id AND f.tipo = 'receita_a_receber'
                    )
                    RETURNING proposta_id;
                """
            else:
                sql_insert = """
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
                    WHERE p.status = 'Finalizada' 
                    AND NOT EXISTS (
                        SELECT 1 FROM financeiro f 
                        WHERE f.proposta_id = p.id AND f.tipo = 'receita_a_receber'
                    )
                    RETURNING proposta_id;
                """
            
            cursor.execute(sql_insert, (data_atual,))
            
            lancamentos_criados = cursor.fetchall()
            if lancamentos_criados:
                print(f"  Criados lançamentos financeiros para {len(lancamentos_criados)} propostas")
                
            print("\nVerificação final...")
            # Verificar se ainda existem propostas com problemas
            cursor.execute("""
                SELECT COUNT(*)
                FROM propostas p
                LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
                WHERE p.status = 'Finalizada' AND f.id IS NULL;
            """)
            
            ainda_problematicas = cursor.fetchone()[0]
            
            if ainda_problematicas > 0:
                print(f"⚠️ Ainda existem {ainda_problematicas} propostas finalizadas sem lançamentos financeiros")
            else:
                print("✅ Todas as propostas finalizadas agora têm lançamentos financeiros")
                
            # Verificar propostas com data_finalizacao nula
            if 'data_finalizacao' in colunas_propostas:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM propostas
                    WHERE status = 'Finalizada' AND data_finalizacao IS NULL;
                """)
                
                sem_data = cursor.fetchone()[0]
                
                if sem_data > 0:
                    print(f"⚠️ Ainda existem {sem_data} propostas finalizadas sem data_finalizacao")
                else:
                    print("✅ Todas as propostas finalizadas agora têm data_finalizacao")
        else:
            print("✅ Nenhuma proposta com problemas encontrada")
        
        # Verificar trigger para manter consistência
        print("\nVerificando/criando trigger para manter consistência...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION set_usuario_id_from_proposta()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.usuario_id IS NULL AND NEW.proposta_id IS NOT NULL THEN
                    NEW.usuario_id := (SELECT usuario_id FROM propostas WHERE id = NEW.proposta_id);
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS financeiro_usuario_id_trigger ON financeiro;
            
            CREATE TRIGGER financeiro_usuario_id_trigger
            BEFORE INSERT OR UPDATE ON financeiro
            FOR EACH ROW
            EXECUTE FUNCTION set_usuario_id_from_proposta();
        """)
        
        print("✅ Trigger criado/atualizado com sucesso")
        
        print("\nScript de correção concluído com sucesso!")
        
    except Exception as e:
        print(f"ERRO durante a execução: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    executar_correcao()
```

## Como Usar

1. Copie o código acima
2. Acesse o console do seu projeto no Render
3. Crie um novo arquivo chamado `fix_proposta.py` (você pode usar `vi fix_proposta.py` ou outro editor de linha de comando)
4. Cole o código no arquivo
5. Salve o arquivo
6. Execute o script com `python3 fix_proposta.py`
7. O script vai mostrar no console o que está sendo feito e quais correções foram aplicadas

## O que o Script Faz

1. Conecta ao banco de dados usando a variável de ambiente DATABASE_URL
2. Verifica a estrutura das tabelas para ser adaptável a diferentes ambientes
3. Identifica propostas com problemas (finalizadas sem data ou sem lançamentos)
4. Corrige as datas faltantes nas propostas
5. Cria lançamentos financeiros para propostas finalizadas que não os têm
6. Cria um trigger para garantir que o campo usuario_id seja corretamente propagado

## Resultados Esperados

Após executar o script, todas as propostas finalizadas devem:
- Ter uma data de finalização válida
- Ter uma data de proposta válida
- Ter um lançamento financeiro associado

Além disso, um trigger é criado para manter a consistência entre propostas e lançamentos financeiros no futuro.