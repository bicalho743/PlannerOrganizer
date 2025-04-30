"""
Script para corrigir problemas de finalização de propostas
Este script contorna os problemas do ORM e faz operações diretamente via SQL
"""
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import os
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Corrigir Finalização de Propostas",
    page_icon="🔧",
    layout="wide"
)

# Funções de banco de dados
def get_db_connection():
    """Obtém uma conexão direta com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def verificar_estrutura_tabelas(conn=None):
    """Verifica a estrutura das tabelas e retorna informações sobre elas"""
    fechar_conn = False
    if conn is None:
        conn = get_db_connection()
        fechar_conn = True
    
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar tabela propostas
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
            ORDER BY ordinal_position;
        """)
        colunas_propostas = cursor.fetchall()
        
        # Verificar tabela financeiro
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
            ORDER BY ordinal_position;
        """)
        colunas_financeiro = cursor.fetchall()
        
        # Formatar para melhor visualização
        estrutura = {
            'propostas': {col[0]: col[1] for col in colunas_propostas},
            'financeiro': {col[0]: col[1] for col in colunas_financeiro},
        }
        
        # Obter configurações adicionais
        has_forma_pagamento = 'forma_pagamento' in estrutura['financeiro']
        
        return {
            'estrutura': estrutura,
            'has_forma_pagamento': has_forma_pagamento
        }
    except Exception as e:
        st.error(f"Erro ao verificar estrutura das tabelas: {e}")
        return None
    finally:
        cursor.close()
        if fechar_conn and conn:
            conn.close()

def buscar_propostas_abertas(usuario_id=None, conn=None):
    """Busca propostas não finalizadas para o usuário especificado"""
    fechar_conn = False
    if conn is None:
        conn = get_db_connection()
        fechar_conn = True
    
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if usuario_id:
            # Filtrar por usuário
            query = """
                SELECT p.id, p.descricao, p.valor, p.status, c.nome as cliente_nome,
                       p.data_inicio, p.data_proposta, p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = %s AND p.status <> 'Finalizada'
                ORDER BY p.id DESC;
            """
            cursor.execute(query, (usuario_id,))
        else:
            # Buscar todas
            query = """
                SELECT p.id, p.descricao, p.valor, p.status, c.nome as cliente_nome,
                       p.data_inicio, p.data_proposta, p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.status <> 'Finalizada'
                ORDER BY p.id DESC;
            """
            cursor.execute(query)
        
        propostas = cursor.fetchall()
        return propostas
    except Exception as e:
        st.error(f"Erro ao buscar propostas: {e}")
        return None
    finally:
        cursor.close()
        if fechar_conn and conn:
            conn.close()

def buscar_todas_propostas(usuario_id=None, conn=None):
    """Busca todas as propostas, com opção de filtrar por usuário"""
    fechar_conn = False
    if conn is None:
        conn = get_db_connection()
        fechar_conn = True
    
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if usuario_id:
            # Filtrar por usuário
            query = """
                SELECT p.id, p.descricao, p.valor, p.status, c.nome as cliente_nome,
                       p.data_inicio, p.data_proposta, p.data_finalizacao, p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = %s
                ORDER BY p.id DESC;
            """
            cursor.execute(query, (usuario_id,))
        else:
            # Buscar todas
            query = """
                SELECT p.id, p.descricao, p.valor, p.status, c.nome as cliente_nome,
                       p.data_inicio, p.data_proposta, p.data_finalizacao, p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                ORDER BY p.id DESC;
            """
            cursor.execute(query)
        
        propostas = cursor.fetchall()
        return propostas
    except Exception as e:
        st.error(f"Erro ao buscar todas as propostas: {e}")
        return None
    finally:
        cursor.close()
        if fechar_conn and conn:
            conn.close()

def buscar_proposta_detalhes(proposta_id, conn=None):
    """Busca detalhes de uma proposta específica"""
    fechar_conn = False
    if conn is None:
        conn = get_db_connection()
        fechar_conn = True
    
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar detalhes da proposta
        query = """
            SELECT p.*, c.nome as cliente_nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s;
        """
        cursor.execute(query, (proposta_id,))
        proposta = cursor.fetchone()
        
        if not proposta:
            return None
        
        # Buscar lançamentos financeiros relacionados
        cursor.execute("""
            SELECT id, descricao, valor, data, categoria, tipo, status
            FROM financeiro
            WHERE proposta_id = %s
            ORDER BY id;
        """, (proposta_id,))
        
        proposta['lancamentos'] = cursor.fetchall()
        
        return proposta
    except Exception as e:
        st.error(f"Erro ao buscar detalhes da proposta: {e}")
        return None
    finally:
        cursor.close()
        if fechar_conn and conn:
            conn.close()

def finalizar_proposta_sql(proposta_id, usuario_id=None):
    """Finaliza uma proposta diretamente via SQL, evitando o ORM"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        # Verificar estrutura das tabelas
        estrutura = verificar_estrutura_tabelas(conn)
        if not estrutura:
            return False, "Erro ao verificar estrutura das tabelas"
        
        has_forma_pagamento = estrutura['has_forma_pagamento']
        
        # Começar transação
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar detalhes da proposta
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
        
        # Verificar se já está finalizada
        if proposta['status'] == 'Finalizada':
            # Verificar se tem data de finalização
            if proposta['data_finalizacao'] is None:
                data_atual = datetime.now().date()
                # Adicionar data de finalização
                cursor.execute("""
                    UPDATE propostas 
                    SET data_finalizacao = %s
                    WHERE id = %s;
                """, (data_atual, proposta_id))
            
            # Verificar se já existe lançamento financeiro
            cursor.execute("""
                SELECT id FROM financeiro 
                WHERE proposta_id = %s AND tipo = 'receita_a_receber'
            """, (proposta_id,))
            
            lancamento = cursor.fetchone()
            if not lancamento:
                # Criar lançamento financeiro
                data_atual = datetime.now().date()
                descricao = f"Proposta #{proposta_id} - {proposta['cliente_nome']}"
                
                if has_forma_pagamento:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        descricao, 
                        proposta['valor'], 
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
                        proposta['valor'], 
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
        data_atual = datetime.now().date()
        
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
            
            if has_forma_pagamento:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    descricao, 
                    proposta['valor'], 
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
                    proposta['valor'], 
                    data_atual, 
                    'Serviços de Organização',
                    'receita_a_receber',
                    'Pendente',
                    proposta_id,
                    proposta['usuario_id']
                ))
            
            lancamento_id = cursor.fetchone()['id']
        
        conn.commit()
        return True, f"Proposta #{proposta_id} finalizada com sucesso"
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao finalizar proposta: {e}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()

def identificar_propostas_problematicas():
    """Identifica propostas com problemas de finalização ou exibição"""
    conn = get_db_connection()
    if not conn:
        return None, None, None
    
    try:
        cursor = conn.cursor()
        
        # 1. Propostas finalizadas sem data_finalizacao
        cursor.execute("""
            SELECT p.id, p.descricao, c.nome as cliente_nome, p.valor, p.status
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.status = 'Finalizada' AND p.data_finalizacao IS NULL
            ORDER BY p.id DESC;
        """)
        sem_data_finalizacao = cursor.fetchall()
        
        # 2. Propostas finalizadas sem data_proposta
        cursor.execute("""
            SELECT p.id, p.descricao, c.nome as cliente_nome, p.valor, p.status
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.status = 'Finalizada' AND p.data_proposta IS NULL
            ORDER BY p.id DESC;
        """)
        sem_data_proposta = cursor.fetchall()
        
        # 3. Propostas finalizadas sem lançamentos financeiros
        cursor.execute("""
            SELECT p.id, p.descricao, c.nome as cliente_nome, p.valor, p.status
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
            WHERE p.status = 'Finalizada' AND f.id IS NULL
            ORDER BY p.id DESC;
        """)
        sem_lancamentos = cursor.fetchall()
        
        return sem_data_finalizacao, sem_data_proposta, sem_lancamentos
    except Exception as e:
        st.error(f"Erro ao identificar propostas problemáticas: {e}")
        return None, None, None
    finally:
        cursor.close()
        conn.close()

def corrigir_todas_propostas_problematicas():
    """Corrige todas as propostas com problemas identificados"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        # Verificar estrutura das tabelas
        estrutura = verificar_estrutura_tabelas(conn)
        if not estrutura:
            return False, "Erro ao verificar estrutura das tabelas"
        
        has_forma_pagamento = estrutura['has_forma_pagamento']
        
        # Começar transação
        conn.autocommit = False
        cursor = conn.cursor()
        data_atual = datetime.now().date()
        
        # 1. Adicionar data_finalizacao para propostas finalizadas sem data
        cursor.execute("""
            UPDATE propostas 
            SET data_finalizacao = %s
            WHERE status = 'Finalizada' AND data_finalizacao IS NULL
            RETURNING id;
        """, (data_atual,))
        
        propostas_atualizadas_1 = cursor.fetchall()
        
        # 2. Adicionar data_proposta para propostas finalizadas sem data
        cursor.execute("""
            UPDATE propostas 
            SET data_proposta = COALESCE(data_inicio, %s)
            WHERE status = 'Finalizada' AND data_proposta IS NULL
            RETURNING id;
        """, (data_atual,))
        
        propostas_atualizadas_2 = cursor.fetchall()
        
        # 3. Criar lançamentos financeiros para propostas finalizadas sem lançamentos
        if has_forma_pagamento:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id)
                SELECT 
                    'Proposta #' || p.id || ' - ' || c.nome,
                    p.valor,
                    COALESCE(p.data_finalizacao, %s),
                    'Serviços de Organização',
                    'receita_a_receber',
                    'Pendente',
                    '',
                    p.id,
                    p.usuario_id
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
                WHERE p.status = 'Finalizada' AND f.id IS NULL
                RETURNING proposta_id;
            """, (data_atual,))
        else:
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
        
        # Criar um trigger para manter a consistência
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
        
        conn.commit()
        
        mensagem = (
            f"Correção concluída com sucesso:\n"
            f"- {len(propostas_atualizadas_1)} propostas com data_finalizacao adicionada\n"
            f"- {len(propostas_atualizadas_2)} propostas com data_proposta adicionada\n"
            f"- {len(lancamentos_criados)} lançamentos financeiros criados\n"
            f"- Trigger de consistência atualizado/criado"
        )
        
        return True, mensagem
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao corrigir propostas: {e}"
    finally:
        cursor.close()
        conn.close()

# Interface principal
def main():
    st.title("🔧 Corrija e Finalize Propostas")
    
    st.markdown("""
    ### Esta ferramenta visa resolver problemas comuns de finalização de propostas no sistema
    
    Em aplicações com banco PostgreSQL no Render, às vezes ocorrem problemas no ORM que podem causar:
    
    1. Propostas finalizadas sem data de finalização
    2. Propostas finalizadas sem data da proposta
    3. Propostas finalizadas sem lançamentos financeiros
    
    Selecione uma das opções abaixo para resolver esses problemas:
    """)
    
    tab1, tab2, tab3 = st.tabs([
        "🔎 Diagnóstico", 
        "🔧 Corrija Propostas Específicas", 
        "🧹 Corrija Todas as Propostas"
    ])
    
    # Tab 1: Diagnóstico
    with tab1:
        st.header("Diagnóstico de Propostas Problemáticas")
        
        if st.button("🔎 Verificar Problemas nas Propostas", key="btn_verificar"):
            with st.spinner("Analisando banco de dados..."):
                sem_data_finalizacao, sem_data_proposta, sem_lancamentos = identificar_propostas_problematicas()
                
                if sem_data_finalizacao is not None:
                    # Mostrar resultados
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.subheader("Sem Data de Finalização")
                        if sem_data_finalizacao:
                            df = pd.DataFrame(sem_data_finalizacao, columns=["ID", "Descrição", "Cliente", "Valor", "Status"])
                            st.dataframe(df, use_container_width=True)
                            st.info(f"{len(sem_data_finalizacao)} propostas sem data_finalizacao")
                        else:
                            st.success("✅ Nenhuma proposta sem data_finalizacao")
                    
                    with col2:
                        st.subheader("Sem Data da Proposta")
                        if sem_data_proposta:
                            df = pd.DataFrame(sem_data_proposta, columns=["ID", "Descrição", "Cliente", "Valor", "Status"])
                            st.dataframe(df, use_container_width=True)
                            st.info(f"{len(sem_data_proposta)} propostas sem data_proposta")
                        else:
                            st.success("✅ Nenhuma proposta sem data_proposta")
                    
                    with col3:
                        st.subheader("Sem Lançamentos")
                        if sem_lancamentos:
                            df = pd.DataFrame(sem_lancamentos, columns=["ID", "Descrição", "Cliente", "Valor", "Status"])
                            st.dataframe(df, use_container_width=True)
                            st.info(f"{len(sem_lancamentos)} propostas sem lançamentos")
                        else:
                            st.success("✅ Nenhuma proposta sem lançamento")
                    
                    # Resumo geral
                    total_problemas = len(sem_data_finalizacao) + len(sem_data_proposta) + len(sem_lancamentos)
                    if total_problemas > 0:
                        st.warning(f"Encontramos {total_problemas} problemas para corrigir")
                        if st.button("🧹 Corrigir Todos os Problemas", key="btn_fix_all_problems"):
                            with st.spinner("Corrigindo todos os problemas..."):
                                sucesso, mensagem = corrigir_todas_propostas_problematicas()
                                if sucesso:
                                    st.success(mensagem)
                                else:
                                    st.error(mensagem)
                    else:
                        st.success("✅ Nenhum problema encontrado nas propostas!")
                        
        # Verificar estrutura do banco
        st.subheader("Estrutura do Banco de Dados")
        if st.button("🔎 Verificar Estrutura", key="btn_estrutura"):
            with st.spinner("Analisando estrutura..."):
                estrutura = verificar_estrutura_tabelas()
                if estrutura:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Tabela propostas:**")
                        st.json(estrutura['estrutura']['propostas'])
                    
                    with col2:
                        st.write("**Tabela financeiro:**")
                        st.json(estrutura['estrutura']['financeiro'])
                    
                    st.write(f"**Coluna forma_pagamento em financeiro:** {'✅ Presente' if estrutura['has_forma_pagamento'] else '❌ Ausente'}")
                    
    # Tab 2: Corrigir propostas específicas
    with tab2:
        st.header("Corrigir uma Proposta Específica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            proposta_id = st.number_input("ID da Proposta a Corrigir", min_value=1, step=1)
            
            if st.button("🔍 Buscar Proposta", key="btn_buscar"):
                with st.spinner(f"Buscando proposta #{proposta_id}..."):
                    proposta = buscar_proposta_detalhes(proposta_id)
                    if proposta:
                        st.session_state.proposta_atual = proposta
                        st.success(f"Proposta #{proposta_id} encontrada!")
                    else:
                        st.error(f"Proposta #{proposta_id} não encontrada")
        
        with col2:
            if st.button("🔧 Finalizar Esta Proposta", key="btn_finalizar", 
                         help="Finaliza a proposta e cria os lançamentos financeiros necessários"):
                if 'proposta_atual' in st.session_state:
                    with st.spinner(f"Finalizando proposta #{st.session_state.proposta_atual['id']}..."):
                        sucesso, mensagem = finalizar_proposta_sql(st.session_state.proposta_atual['id'])
                        
                        if sucesso:
                            st.success(mensagem)
                            # Atualizar proposta
                            proposta = buscar_proposta_detalhes(st.session_state.proposta_atual['id'])
                            if proposta:
                                st.session_state.proposta_atual = proposta
                        else:
                            st.error(mensagem)
                else:
                    st.warning("Por favor, busque uma proposta primeiro")
        
        # Mostrar detalhes da proposta selecionada
        if 'proposta_atual' in st.session_state:
            proposta = st.session_state.proposta_atual
            
            st.subheader(f"Proposta #{proposta['id']} - {proposta['cliente_nome']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Descrição:** {proposta['descricao']}")
                st.write(f"**Valor:** R$ {proposta['valor']:.2f}")
                st.write(f"**Status:** {proposta['status']}")
            
            with col2:
                st.write(f"**Data Início:** {proposta['data_inicio'].strftime('%d/%m/%Y') if proposta['data_inicio'] else 'Não definida'}")
                st.write(f"**Data Proposta:** {proposta['data_proposta'].strftime('%d/%m/%Y') if proposta['data_proposta'] else 'Não definida'}")
                st.write(f"**Data Finalização:** {proposta['data_finalizacao'].strftime('%d/%m/%Y') if proposta.get('data_finalizacao') else 'Não finalizada'}")
            
            with col3:
                st.write(f"**ID do Usuário:** {proposta['usuario_id']}")
                st.write(f"**ID do Cliente:** {proposta['cliente_id']}")
                st.write(f"**Cliente:** {proposta['cliente_nome']}")
            
            # Mostrar lançamentos
            if 'lancamentos' in proposta and proposta['lancamentos']:
                st.subheader("Lançamentos Financeiros")
                
                # Converter para DataFrame para melhor visualização
                lancamentos_data = []
                for l in proposta['lancamentos']:
                    lancamentos_data.append({
                        "ID": l['id'],
                        "Descrição": l['descricao'],
                        "Valor": f"R$ {l['valor']:.2f}",
                        "Data": l['data'].strftime('%d/%m/%Y') if l['data'] else '',
                        "Categoria": l['categoria'],
                        "Tipo": l['tipo'],
                        "Status": l['status']
                    })
                
                if lancamentos_data:
                    st.dataframe(pd.DataFrame(lancamentos_data), use_container_width=True)
            else:
                st.warning("Não há lançamentos financeiros para esta proposta")
                
                if proposta['status'] == 'Finalizada':
                    st.error("Esta proposta está finalizada mas não tem lançamentos financeiros!")
                    st.info("Use o botão 'Finalizar Esta Proposta' para criar os lançamentos necessários")
    
    # Tab 3: Corrigir todas as propostas
    with tab3:
        st.header("Corrigir Todas as Propostas")
        
        st.warning("""
        ⚠️ **ATENÇÃO**: Esta opção irá corrigir TODAS as propostas com problemas no banco de dados.
        
        Isso inclui:
        - Adicionar data_finalizacao às propostas finalizadas sem esse campo
        - Adicionar data_proposta às propostas finalizadas sem esse campo
        - Criar lançamentos financeiros para propostas finalizadas que não os têm
        - Criar um trigger para manter a consistência entre propostas e lançamentos
        
        Você pode verificar os problemas na aba 'Diagnóstico' antes de prosseguir.
        """)
        
        if st.button("🧹 CORRIGIR TODAS AS PROPOSTAS", key="btn_fix_all"):
            confirma = st.checkbox("Confirmo que desejo corrigir todas as propostas com problemas")
            
            if confirma:
                with st.spinner("Corrigindo todas as propostas com problemas..."):
                    sucesso, mensagem = corrigir_todas_propostas_problematicas()
                    
                    if sucesso:
                        st.success(mensagem)
                        st.balloons()
                    else:
                        st.error(mensagem)
            else:
                st.info("Por favor, confirme que deseja prosseguir com a correção")
        
        # Listar propostas abertas
        st.subheader("Propostas não Finalizadas")
        
        if st.button("📋 Listar Propostas não Finalizadas", key="btn_list_open"):
            with st.spinner("Buscando propostas não finalizadas..."):
                propostas = buscar_propostas_abertas()
                
                if propostas:
                    # Converter para DataFrame para melhor visualização
                    data = []
                    for p in propostas:
                        data.append({
                            "ID": p['id'],
                            "Cliente": p['cliente_nome'],
                            "Descrição": p['descricao'],
                            "Valor": f"R$ {p['valor']:.2f}",
                            "Status": p['status'],
                            "Data Início": p['data_inicio'].strftime('%d/%m/%Y') if p['data_inicio'] else "",
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    st.info(f"Encontradas {len(propostas)} propostas não finalizadas")
                    
                    # Opção para finalizar todas
                    if st.button("✅ Finalizar Todas Estas Propostas", key="btn_finalizar_todas"):
                        st.warning("⚠️ Tem certeza que deseja finalizar TODAS estas propostas?")
                        confirma = st.checkbox("Sim, desejo finalizar todas as propostas não finalizadas")
                        
                        if confirma:
                            sucessos = 0
                            falhas = 0
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, proposta in enumerate(propostas):
                                status_text.text(f"Finalizando proposta #{proposta['id']}...")
                                sucesso, _ = finalizar_proposta_sql(proposta['id'])
                                
                                if sucesso:
                                    sucessos += 1
                                else:
                                    falhas += 1
                                
                                # Atualizar progresso
                                progress = (i + 1) / len(propostas)
                                progress_bar.progress(progress)
                            
                            status_text.empty()
                            if falhas == 0:
                                st.success(f"✅ Todas as {sucessos} propostas foram finalizadas com sucesso!")
                                st.balloons()
                            else:
                                st.warning(f"Processo concluído com {sucessos} sucessos e {falhas} falhas")
                else:
                    st.success("✅ Não há propostas não finalizadas no sistema")

if __name__ == "__main__":
    main()