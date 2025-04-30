"""
Módulo para finalizar propostas de forma robusta, evitando problemas de conversão de tipos
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pandas as pd
import streamlit as st

def get_db_connection():
    """Obtém uma conexão direta com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def get_proposta(proposta_id, usuario_id=None):
    """Obtém detalhes de uma proposta específica"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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
        
        return proposta
    except Exception as e:
        st.error(f"Erro ao obter proposta: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_lancamentos_by_proposta(proposta_id):
    """Obtém lançamentos financeiros associados a uma proposta"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        query = """
            SELECT id, descricao, valor, data, categoria, tipo, status
            FROM financeiro
            WHERE proposta_id = %s
            ORDER BY id;
        """
        
        lancamentos = pd.read_sql(query, conn, params=(proposta_id,))
        return lancamentos
    except Exception as e:
        st.error(f"Erro ao obter lançamentos: {e}")
        return []
    finally:
        conn.close()

def add_lancamento(descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id):
    """Adiciona um lançamento financeiro ao banco de dados"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar campos da tabela financeiro
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
        """)
        colunas = [row[0] for row in cursor.fetchall()]
        
        # Garantir que valor seja float
        try:
            valor = float(valor)
        except (ValueError, TypeError):
            st.error(f"Erro ao converter valor '{valor}' para float")
            return None
        
        # Construir query com base nas colunas disponíveis
        if 'forma_pagamento' in colunas:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                descricao, 
                valor, 
                data, 
                categoria,
                tipo,
                status,
                '',
                proposta_id,
                usuario_id
            ))
        else:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                descricao, 
                valor, 
                data, 
                categoria,
                tipo,
                status,
                proposta_id,
                usuario_id
            ))
        
        lancamento_id = cursor.fetchone()[0]
        conn.commit()
        
        return lancamento_id
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar lançamento: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_proposta_fornecedores(proposta_id):
    """Obtém fornecedores associados a uma proposta"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, nome, valor
            FROM proposta_fornecedores
            WHERE proposta_id = %s;
        """, (proposta_id,))
        
        fornecedores = cursor.fetchall()
        return fornecedores
    except Exception as e:
        st.error(f"Erro ao obter fornecedores: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def processar_fornecedores(proposta_id, usuario_id, data):
    """Processa fornecedores criando lançamentos financeiros"""
    fornecedores = get_proposta_fornecedores(proposta_id)
    
    for fornecedor in fornecedores:
        descricao = f"Fornecedor: {fornecedor['nome']} - Proposta #{proposta_id}"
        add_lancamento(
            descricao,
            float(fornecedor['valor']),
            data,
            'Fornecedores',
            'despesa_a_pagar',
            'Pendente',
            proposta_id,
            usuario_id
        )

def get_proposta_acrescimos(proposta_id):
    """Obtém acréscimos associados a uma proposta"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, descricao, valor, tipo
            FROM proposta_acrescimos
            WHERE proposta_id = %s;
        """, (proposta_id,))
        
        acrescimos = cursor.fetchall()
        return acrescimos
    except Exception as e:
        st.error(f"Erro ao obter acréscimos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def processar_acrescimos(proposta_id, usuario_id, data):
    """Processa acréscimos criando lançamentos financeiros"""
    acrescimos = get_proposta_acrescimos(proposta_id)
    
    for acrescimo in acrescimos:
        if acrescimo['tipo'] == 'OUTRO':
            descricao = f"Custo: {acrescimo['descricao']} - Proposta #{proposta_id}"
            add_lancamento(
                descricao,
                float(acrescimo['valor']),
                data,
                'Outros Custos',
                'despesa_a_pagar',
                'Pendente',
                proposta_id,
                usuario_id
            )

def get_proposta_assistentes(proposta_id):
    """Obtém assistentes associados a uma proposta"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, nome, valor
            FROM proposta_assistentes
            WHERE proposta_id = %s;
        """, (proposta_id,))
        
        assistentes = cursor.fetchall()
        return assistentes
    except Exception as e:
        st.error(f"Erro ao obter assistentes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def processar_assistentes(proposta_id, usuario_id, data):
    """Processa assistentes criando lançamentos financeiros"""
    assistentes = get_proposta_assistentes(proposta_id)
    
    for assistente in assistentes:
        descricao = f"Assistente: {assistente['nome']} - Proposta #{proposta_id}"
        add_lancamento(
            descricao,
            float(assistente['valor']),
            data,
            'Assistentes',
            'despesa_a_pagar',
            'Pendente',
            proposta_id,
            usuario_id
        )

def get_proposta_produtos(proposta_id):
    """Obtém produtos associados a uma proposta"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT pp.id, pp.quantidade, pp.valor_unitario, pr.nome
            FROM proposta_produtos pp
            JOIN produtos pr ON pp.produto_id = pr.id
            WHERE pp.proposta_id = %s;
        """, (proposta_id,))
        
        produtos = cursor.fetchall()
        return produtos
    except Exception as e:
        st.error(f"Erro ao obter produtos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def processar_produtos(proposta_id, usuario_id, data):
    """Processa produtos criando lançamentos financeiros"""
    produtos = get_proposta_produtos(proposta_id)
    
    if produtos:
        total_produtos = sum(float(p['quantidade']) * float(p['valor_unitario']) for p in produtos)
        nome_produtos = ", ".join(p['nome'] for p in produtos)
        
        descricao = f"Produtos: {nome_produtos} - Proposta #{proposta_id}"
        add_lancamento(
            descricao,
            total_produtos,
            data,
            'Produtos',
            'despesa_a_pagar',
            'Pendente',
            proposta_id,
            usuario_id
        )

def finalizar_proposta_sql(proposta_id, usuario_id=None):
    """Finaliza uma proposta diretamente via SQL, com verificações de tipos"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        # Começar transação
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar se a proposta existe e pertence ao usuário
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
        
        # Definir data atual
        data_atual = datetime.now().date()
        
        # Verificar se já está finalizada
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
                
                # Verificar campos da tabela financeiro
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'financeiro'
                """)
                colunas = [row[0] for row in cursor.fetchall()]
                
                # Garantir que valor seja float
                try:
                    valor = float(proposta['valor'])
                except (ValueError, TypeError):
                    valor = 0.0
                    st.warning(f"Valor da proposta ({proposta['valor']}) não pôde ser convertido para float, usando 0.0")
                
                # Construir query com base nas colunas disponíveis
                if 'forma_pagamento' in colunas:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        descricao, 
                        valor, 
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
                        valor, 
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
        
        # Se não está finalizada, finalizar agora
        try:
            # Atualizar proposta
            cursor.execute("""
                UPDATE propostas 
                SET 
                    status = 'Finalizada',
                    data_finalizacao = %s,
                    data_proposta = COALESCE(data_proposta, data_inicio, %s)
                WHERE id = %s
                RETURNING id;
            """, (data_atual, data_atual, proposta_id))
            
            if cursor.fetchone() is None:
                conn.rollback()
                return False, f"Erro ao atualizar proposta #{proposta_id}"
            
            # Verificar se já existe lançamento
            cursor.execute("""
                SELECT id FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber'
            """, (proposta_id,))
            
            lancamento = cursor.fetchone()
            if not lancamento:
                # Criar lançamento financeiro
                descricao = f"Proposta #{proposta_id} - {proposta['cliente_nome']}"
                
                # Verificar campos da tabela financeiro
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'financeiro'
                """)
                colunas = [row[0] for row in cursor.fetchall()]
                
                # Garantir que valor seja float
                try:
                    valor = float(proposta['valor'])
                except (ValueError, TypeError):
                    valor = 0.0
                    st.warning(f"Valor da proposta ({proposta['valor']}) não pôde ser convertido para float, usando 0.0")
                
                # Construir query com base nas colunas disponíveis
                if 'forma_pagamento' in colunas:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        descricao, 
                        valor, 
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
                        valor, 
                        data_atual, 
                        'Serviços de Organização',
                        'receita_a_receber',
                        'Pendente',
                        proposta_id,
                        proposta['usuario_id']
                    ))
            
            # Processar fornecedores, acréscimos, assistentes e produtos
            processar_fornecedores(proposta_id, proposta['usuario_id'], data_atual)
            processar_acrescimos(proposta_id, proposta['usuario_id'], data_atual)
            processar_assistentes(proposta_id, proposta['usuario_id'], data_atual)
            processar_produtos(proposta_id, proposta['usuario_id'], data_atual)
            
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