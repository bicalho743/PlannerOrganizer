# Solução para Problemas de Finalização de Propostas no Render

Este documento contém duas soluções complementares para resolver os problemas de finalização de propostas no ambiente Render.

## O Problema

A funcionalidade de finalizar propostas está inoperante após o deploy no ambiente Render, embora funcione corretamente no ambiente de desenvolvimento. Os logs mostram erros de conversão de tipos de dados, especificamente:

```
pyarrow.lib.ArrowInvalid: ("Could not convert 'teste 1' with type str: tried to convert to int64", 'Conversion failed for column Valor with type object')
```

Este erro indica que há incompatibilidades na conversão de tipos de dados entre os ambientes, especialmente ao lidar com valores monetários.

## Solução 1: Script de Correção de Banco de Dados

O primeiro script corrige as inconsistências no banco de dados, garantindo que todas as propostas tenham as datas e lançamentos financeiros necessários.

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

## Solução 2: Substituir Arquivo de Finalização de Propostas

Este segundo script resolve o problema de conversão de tipos de dados nas funções de finalização. Deve ser salvo como `utils/finalizar_proposta_fix.py` no ambiente Render:

```python
"""
Módulo para finalizar propostas de forma robusta, evitando problemas de conversão de tipos
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_db_connection():
    """Obtém uma conexão direta com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def finalizar_proposta_direto(proposta_id, usuario_id=None):
    """Finaliza uma proposta diretamente, sem usar ORM, evitando problemas de conversão de tipos"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        # Iniciar transação
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        data_atual = datetime.now().date()
        
        # Verificar se a proposta existe e se pertence ao usuário
        query = """
            SELECT p.*, c.nome as cliente_nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
        """
        params = [proposta_id]
        
        if usuario_id:
            query += " AND p.usuario_id = %s"
            params.append(usuario_id)
        
        cursor.execute(query, params)
        proposta = cursor.fetchone()
        
        if not proposta:
            conn.rollback()
            return False, f"Proposta #{proposta_id} não encontrada ou você não tem permissão para finalizá-la"
        
        # Já está finalizada?
        if proposta['status'] == 'Finalizada':
            # Verificar se tem lançamento financeiro
            cursor.execute("""
                SELECT id FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber'
            """, (proposta_id,))
            
            lancamento = cursor.fetchone()
            if not lancamento:
                # Criar lançamento financeiro
                descricao = f"Proposta #{proposta_id} - {proposta['cliente_nome']}"
                
                # Verificar estrutura financeiro
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'financeiro'
                """)
                colunas = [row[0] for row in cursor.fetchall()]
                
                if 'forma_pagamento' in colunas:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        descricao, 
                        float(proposta['valor']), 
                        data_atual, 
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        '',
                        proposta_id,
                        proposta['usuario_id']
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        descricao, 
                        float(proposta['valor']), 
                        data_atual, 
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        proposta_id,
                        proposta['usuario_id']
                    ))
                
                lancamento_id = cursor.fetchone()['id']
                conn.commit()
                return True, f"Proposta já estava finalizada, mas lançamento financeiro foi criado com ID: {lancamento_id}"
            else:
                conn.commit()
                return True, "Proposta já está finalizada e tem lançamento financeiro"
            
        # Finalizar proposta
        try:
            # Atualizar status para finalizada
            cursor.execute("""
                UPDATE propostas 
                SET 
                    status = 'Finalizada',
                    data_finalizacao = %s
                WHERE id = %s
                RETURNING id;
            """, (data_atual, proposta_id))
            
            if cursor.fetchone() is None:
                conn.rollback()
                return False, f"Erro ao atualizar proposta #{proposta_id}"
            
            # Criar lançamento financeiro
            descricao = f"Proposta #{proposta_id} - {proposta['cliente_nome']}"
            
            # Verificar estrutura financeiro
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financeiro'
            """)
            colunas = [row[0] for row in cursor.fetchall()]
            
            if 'forma_pagamento' in colunas:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    descricao, 
                    float(proposta['valor']), 
                    data_atual, 
                    'Serviços de Organização',
                    'receita_a_receber',
                    'Pendente',
                    '',
                    proposta_id,
                    proposta['usuario_id']
                ))
            else:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    descricao, 
                    float(proposta['valor']), 
                    data_atual, 
                    'Serviços de Organização',
                    'receita_a_receber',
                    'Pendente',
                    proposta_id,
                    proposta['usuario_id']
                ))
            
            # Processar fornecedores
            cursor.execute("""
                SELECT id, nome, valor
                FROM proposta_fornecedores
                WHERE proposta_id = %s;
            """, (proposta_id,))
            
            fornecedores = cursor.fetchall()
            for fornecedor in fornecedores:
                descricao_fornecedor = f"Fornecedor: {fornecedor['nome']} - Proposta #{proposta_id}"
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    descricao_fornecedor,
                    float(fornecedor['valor']),
                    data_atual,
                    'Fornecedores',
                    'despesa_a_pagar',
                    'Pendente',
                    proposta_id,
                    proposta['usuario_id']
                ))
            
            # Processar outros custos (acréscimos)
            cursor.execute("""
                SELECT id, descricao, valor, tipo
                FROM proposta_acrescimos
                WHERE proposta_id = %s;
            """, (proposta_id,))
            
            acrescimos = cursor.fetchall()
            for acrescimo in acrescimos:
                if acrescimo['tipo'] == 'OUTRO':
                    descricao_acrescimo = f"Custo: {acrescimo['descricao']} - Proposta #{proposta_id}"
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        descricao_acrescimo,
                        float(acrescimo['valor']),
                        data_atual,
                        'Outros Custos',
                        'despesa_a_pagar',
                        'Pendente',
                        proposta_id,
                        proposta['usuario_id']
                    ))
            
            # Processar assistentes
            cursor.execute("""
                SELECT id, nome, valor
                FROM proposta_assistentes
                WHERE proposta_id = %s;
            """, (proposta_id,))
            
            assistentes = cursor.fetchall()
            for assistente in assistentes:
                descricao_assistente = f"Assistente: {assistente['nome']} - Proposta #{proposta_id}"
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    descricao_assistente,
                    float(assistente['valor']),
                    data_atual,
                    'Assistentes',
                    'despesa_a_pagar',
                    'Pendente',
                    proposta_id,
                    proposta['usuario_id']
                ))
            
            # Processar produtos
            cursor.execute("""
                SELECT pp.id, pp.quantidade, pp.valor_unitario, pr.nome
                FROM proposta_produtos pp
                JOIN produtos pr ON pp.produto_id = pr.id
                WHERE pp.proposta_id = %s;
            """, (proposta_id,))
            
            produtos = cursor.fetchall()
            if produtos:
                total_produtos = sum(float(p['quantidade']) * float(p['valor_unitario']) for p in produtos)
                nome_produtos = ", ".join(p['nome'] for p in produtos)
                
                descricao_produtos = f"Produtos: {nome_produtos} - Proposta #{proposta_id}"
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    descricao_produtos,
                    float(total_produtos),
                    data_atual,
                    'Produtos',
                    'despesa_a_pagar',
                    'Pendente',
                    proposta_id,
                    proposta['usuario_id']
                ))
            
            conn.commit()
            return True, f"Proposta #{proposta_id} finalizada com sucesso"
            
        except Exception as e:
            conn.rollback()
            return False, f"Erro específico ao finalizar proposta: {str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Erro geral ao finalizar proposta: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()
```

## Como Usar Esta Solução

### Passo 1: Corrigir o banco de dados

1. Copie o primeiro script (o da Solução 1)
2. Acesse o console do seu projeto no Render
3. Crie um novo arquivo chamado `fix_proposta.py` (você pode usar `vi fix_proposta.py` ou outro editor de linha de comando)
4. Cole o código do primeiro script
5. Salve o arquivo e execute-o com `python3 fix_proposta.py`
6. O script vai mostrar no console o que está sendo feito e quais correções foram aplicadas

### Passo 2: Implementar a função robusta de finalização

1. Copie o segundo script (o da Solução 2)
2. No console do Render, crie o diretório utils se ainda não existir: `mkdir -p utils`
3. Crie um novo arquivo `utils/finalizar_proposta_fix.py`
4. Cole o código do segundo script
5. Salve o arquivo

### Passo 3: Modificar o arquivo pages/propostas.py para usar a nova função

No arquivo `pages/propostas.py`, encontre a função que finaliza as propostas e substitua-a pela chamada à nova função:

```python
# Antes do código, adicione a importação
from utils.finalizar_proposta_fix import finalizar_proposta_direto

# Substitua a função de finalização atual por esta:
if st.button("✅ Finalizar Proposta", key=f"finalizar_{proposta_id}"):
    with st.spinner("Finalizando proposta..."):
        sucesso, mensagem = finalizar_proposta_direto(proposta_id, st.session_state.user_info.get('localId'))
        if sucesso:
            st.success(mensagem)
            time.sleep(1)
            st.experimental_rerun()  # Recarregar a página para mostrar as mudanças
        else:
            st.error(mensagem)
```

## Resultados Esperados

Após implementar esta solução:

1. O banco de dados estará totalmente correto e consistente para propostas existentes
2. O botão de finalizar proposta funcionará corretamente no ambiente Render
3. As conversões de tipos de dados serão tratadas adequadamente, evitando os erros mostrados nos logs
4. Novos lançamentos financeiros serão criados corretamente

Esta solução é robusta e flexível, adaptando-se a diferentes estruturas de banco de dados e evitando problemas de conversão de tipos comuns no ambiente Render.