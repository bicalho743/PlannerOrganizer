"""
Script para corrigir problemas de finalização de propostas
Este script contorna os problemas do ORM e faz operações diretamente via SQL
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Função para obter conexão com o banco de dados
def get_db_connection():
    """Obtém uma conexão direta com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        conn.autocommit = True
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        logger.error(f"Erro de conexão: {e}")
        return None

# Função para verificar a estrutura das tabelas
def verificar_estrutura_tabelas(conn=None):
    """Verifica a estrutura das tabelas e retorna informações sobre elas"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    if not conn:
        return {}
    
    result = {}
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Tabela financeiro
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
            ORDER BY ordinal_position;
        """)
        result['financeiro_colunas'] = [row['column_name'] for row in cursor.fetchall()]
        
        # Tabela propostas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
            ORDER BY ordinal_position;
        """)
        result['propostas_colunas'] = [row['column_name'] for row in cursor.fetchall()]
        
        cursor.close()
    except Exception as e:
        st.error(f"Erro ao verificar estrutura das tabelas: {e}")
        logger.error(f"Erro na verificação de estrutura: {e}")
    finally:
        if should_close and conn:
            conn.close()
    
    return result

# Função para buscar propostas não finalizadas
def buscar_propostas_abertas(usuario_id=None, conn=None):
    """Busca propostas não finalizadas para o usuário especificado"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    if not conn:
        return []
    
    propostas = []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if usuario_id:
            query = """
                SELECT p.*, c.nome as cliente_nome
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.usuario_id = %s AND p.status <> 'Finalizada'
                ORDER BY p.id DESC;
            """
            cursor.execute(query, (usuario_id,))
        else:
            query = """
                SELECT p.*, c.nome as cliente_nome
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.status <> 'Finalizada'
                ORDER BY p.id DESC;
            """
            cursor.execute(query)
        
        propostas = cursor.fetchall()
        cursor.close()
    except Exception as e:
        st.error(f"Erro ao buscar propostas: {e}")
        logger.error(f"Erro na busca de propostas: {e}")
    finally:
        if should_close and conn:
            conn.close()
    
    return propostas

# Função para finalizar uma proposta
def finalizar_proposta_sql(proposta_id, usuario_id=None):
    """Finaliza uma proposta diretamente via SQL, evitando o ORM"""
    conn = get_db_connection()
    if not conn:
        return {
            'status': 'error',
            'message': 'Não foi possível conectar ao banco de dados'
        }
    
    try:
        # Verificar estrutura das tabelas
        estrutura = verificar_estrutura_tabelas(conn)
        financeiro_colunas = estrutura.get('financeiro_colunas', [])
        
        # Obter detalhes da proposta
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
        
        if not proposta:
            cursor.close()
            conn.close()
            return {
                'status': 'error',
                'message': f'Proposta #{proposta_id} não encontrada'
            }
        
        # Verificar se já está finalizada
        if proposta['status'] == 'Finalizada':
            cursor.close()
            conn.close()
            return {
                'status': 'error',
                'message': f'Proposta #{proposta_id} já está finalizada'
            }
        
        # Buscar lançamentos existentes
        cursor.execute("""
            SELECT * FROM financeiro WHERE proposta_id = %s
        """, (proposta_id,))
        
        lancamentos = cursor.fetchall()
        
        # Verificar se já existe lançamento de receita
        lancamento_principal_existe = False
        for l in lancamentos:
            if l.get('tipo') == 'receita_a_receber' and l.get('categoria') == 'Serviços de Organização':
                lancamento_principal_existe = True
                break
        
        # Inserir lançamento principal se não existir
        if not lancamento_principal_existe:
            # Construir a query baseada nas colunas disponíveis
            colunas = ['descricao', 'valor', 'data', 'categoria', 'tipo', 'status', 'proposta_id']
            valores = [
                f"Proposta #{proposta_id} - {proposta['cliente_nome']}",
                proposta['valor'],
                datetime.now().date(),
                'Serviços de Organização',
                'receita_a_receber',
                'Pendente',
                proposta_id
            ]
            
            # Adicionar usuario_id se a coluna existir
            if 'usuario_id' in financeiro_colunas:
                colunas.append('usuario_id')
                valores.append(proposta['usuario_id'])
            
            # Adicionar forma_pagamento se a coluna existir
            if 'forma_pagamento' in financeiro_colunas:
                colunas.append('forma_pagamento')
                valores.append('')
            
            # Construir query dinâmica
            placeholders = ','.join(['%s'] * len(valores))
            query = f"""
                INSERT INTO financeiro ({','.join(colunas)})
                VALUES ({placeholders})
            """
            
            cursor.execute(query, valores)
            logger.info(f"Lançamento principal criado para proposta #{proposta_id}")
        
        # Marcar proposta como finalizada
        cursor.execute("""
            UPDATE propostas SET status = 'Finalizada' WHERE id = %s
        """, (proposta_id,))
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'message': f'Proposta #{proposta_id} finalizada com sucesso'
        }
    
    except Exception as e:
        if conn:
            conn.close()
        st.error(f"Erro ao finalizar proposta: {e}")
        logger.error(f"Erro na finalização: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao finalizar proposta: {e}'
        }

# Interface Streamlit
def main():
    st.set_page_config(
        page_title="Corrigir Finalização de Propostas",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Corrigir Finalização de Propostas")
    st.write("""
    Esta ferramenta resolve problemas na finalização de propostas, 
    contornando o ORM e fazendo operações diretamente via SQL.
    """)
    
    # Verificar login
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Você precisa estar logado para acessar esta ferramenta.")
        st.stop()
    
    # Obter ID do usuário
    usuario_id = st.session_state.user_info.get('localId')
    
    # Verificar estrutura do banco
    with st.expander("Informações de diagnóstico"):
        if st.button("Verificar estrutura do banco"):
            estrutura = verificar_estrutura_tabelas()
            if estrutura:
                st.write("**Colunas da tabela financeiro:**")
                st.write(estrutura.get('financeiro_colunas', []))
                st.write("**Colunas da tabela propostas:**")
                st.write(estrutura.get('propostas_colunas', []))
            else:
                st.error("Não foi possível verificar a estrutura das tabelas.")
    
    # Buscar propostas em aberto
    propostas = buscar_propostas_abertas(usuario_id)
    
    if not propostas:
        st.info("Não há propostas em aberto para finalizar.")
        st.stop()
    
    # Exibir propostas em formato de cards
    st.subheader("Propostas em Aberto")
    
    for i, proposta in enumerate(propostas):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### #{proposta['id']} - {proposta['cliente_nome']}")
            st.write(f"**Descrição:** {proposta['descricao']}")
            st.write(f"**Valor:** R$ {proposta['valor']}")
            st.write(f"**Status:** {proposta['status']}")
        
        with col2:
            if st.button(f"Finalizar", key=f"btn_{proposta['id']}"):
                confirma = st.checkbox(f"Confirmar finalização da proposta #{proposta['id']}?", key=f"confirm_{proposta['id']}")
                
                if confirma:
                    with st.spinner("Finalizando proposta..."):
                        resultado = finalizar_proposta_sql(proposta['id'], usuario_id)
                        
                        if resultado['status'] == 'success':
                            st.success(resultado['message'])
                            st.rerun()
                        else:
                            st.error(resultado['message'])
        
        st.markdown("---")

if __name__ == "__main__":
    main()