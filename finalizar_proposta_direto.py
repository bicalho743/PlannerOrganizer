"""
Script independente para finalizar propostas diretamente no banco de dados,
sem depender do SQLAlchemy ou outras camadas de abstração.
Este script usa psycopg2 para comunicação direta com o PostgreSQL.
"""
import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging
import streamlit as st

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Conexão com o banco de dados
def get_db_connection():
    """Estabelece conexão direta com o banco de dados usando psycopg2"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        conn.autocommit = True
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        logger.error(f"Erro de conexão: {str(e)}")
        return None

# Função para obter detalhes da proposta
def get_proposta_detalhes(proposta_id, usuario_id):
    """Obtém detalhes da proposta diretamente do banco"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Consulta para obter detalhes da proposta
        query = """
            SELECT p.*, c.nome as cliente_nome 
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s AND p.usuario_id = %s
        """
        cursor.execute(query, (proposta_id, usuario_id))
        proposta = cursor.fetchone()
        
        cursor.close()
        return proposta
    except Exception as e:
        st.error(f"Erro ao obter detalhes da proposta: {str(e)}")
        logger.error(f"Erro ao obter proposta: {str(e)}")
        return None
    finally:
        conn.close()

# Função para obter produtos da proposta
def get_proposta_produtos(proposta_id, usuario_id):
    """Obtém produtos da proposta diretamente do banco"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Consulta para obter produtos da proposta
        query = """
            SELECT pp.* 
            FROM proposta_produtos pp
            JOIN propostas p ON pp.proposta_id = p.id
            WHERE pp.proposta_id = %s AND p.usuario_id = %s
        """
        cursor.execute(query, (proposta_id, usuario_id))
        produtos = cursor.fetchall()
        
        cursor.close()
        return produtos
    except Exception as e:
        st.error(f"Erro ao obter produtos da proposta: {str(e)}")
        logger.error(f"Erro ao obter produtos: {str(e)}")
        return []
    finally:
        conn.close()

# Função para obter fornecedores da proposta
def get_proposta_fornecedores(proposta_id, usuario_id):
    """Obtém fornecedores da proposta diretamente do banco"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Consulta para obter fornecedores da proposta
        query = """
            SELECT pf.* 
            FROM proposta_fornecedores pf
            JOIN propostas p ON pf.proposta_id = p.id
            WHERE pf.proposta_id = %s AND p.usuario_id = %s
        """
        cursor.execute(query, (proposta_id, usuario_id))
        fornecedores = cursor.fetchall()
        
        cursor.close()
        return fornecedores
    except Exception as e:
        st.error(f"Erro ao obter fornecedores da proposta: {str(e)}")
        logger.error(f"Erro ao obter fornecedores: {str(e)}")
        return []
    finally:
        conn.close()

# Função para obter acréscimos da proposta
def get_proposta_acrescimos(proposta_id, usuario_id):
    """Obtém acréscimos da proposta diretamente do banco"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Consulta para obter acréscimos da proposta
        query = """
            SELECT pa.* 
            FROM proposta_acrescimos pa
            JOIN propostas p ON pa.proposta_id = p.id
            WHERE pa.proposta_id = %s AND p.usuario_id = %s
        """
        cursor.execute(query, (proposta_id, usuario_id))
        acrescimos = cursor.fetchall()
        
        cursor.close()
        return acrescimos
    except Exception as e:
        st.error(f"Erro ao obter acréscimos da proposta: {str(e)}")
        logger.error(f"Erro ao obter acréscimos: {str(e)}")
        return []
    finally:
        conn.close()

# Função para obter assistentes da proposta
def get_proposta_assistentes(proposta_id, usuario_id):
    """Obtém assistentes da proposta diretamente do banco"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Consulta para obter assistentes da proposta
        query = """
            SELECT pa.* 
            FROM proposta_assistentes pa
            JOIN propostas p ON pa.proposta_id = p.id
            WHERE pa.proposta_id = %s AND p.usuario_id = %s
        """
        cursor.execute(query, (proposta_id, usuario_id))
        assistentes = cursor.fetchall()
        
        cursor.close()
        return assistentes
    except Exception as e:
        st.error(f"Erro ao obter assistentes da proposta: {str(e)}")
        logger.error(f"Erro ao obter assistentes: {str(e)}")
        return []
    finally:
        conn.close()

# Função para adicionar lançamento financeiro
def add_lancamento(descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id):
    """Adiciona um lançamento financeiro diretamente no banco"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar se a coluna usuario_id existe na tabela financeiro
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'financeiro' AND column_name = 'usuario_id'
            );
        """)
        usuario_id_exists = cursor.fetchone()[0]
        
        # Consulta para adicionar lançamento
        if usuario_id_exists:
            query = """
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id, usuario_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                descricao, valor, data, categoria, tipo, status, 
                forma_pagamento, proposta_id, usuario_id
            ))
        else:
            query = """
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, tipo, status, forma_pagamento, proposta_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                descricao, valor, data, categoria, tipo, status, 
                forma_pagamento, proposta_id
            ))
        
        cursor.close()
        logger.info(f"Lançamento financeiro adicionado com sucesso: {descricao}")
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar lançamento financeiro: {str(e)}")
        logger.error(f"Erro ao adicionar lançamento: {str(e)}")
        return False
    finally:
        conn.close()

# Função para verificar se já existem lançamentos para a proposta
def get_lancamentos_by_proposta(proposta_id, usuario_id):
    """Obtém lançamentos relacionados à proposta diretamente do banco"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Consulta para obter lançamentos da proposta
        query = """
            SELECT f.* 
            FROM financeiro f
            WHERE f.proposta_id = %s
        """
        cursor.execute(query, (proposta_id,))
        lancamentos = cursor.fetchall()
        
        cursor.close()
        return lancamentos
    except Exception as e:
        st.error(f"Erro ao obter lançamentos da proposta: {str(e)}")
        logger.error(f"Erro ao obter lançamentos: {str(e)}")
        return []
    finally:
        conn.close()

# Função para atualizar o status da proposta
def update_proposta_status(proposta_id, status, usuario_id):
    """Atualiza o status da proposta diretamente no banco"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Consulta para atualizar status da proposta
        query = """
            UPDATE propostas 
            SET status = %s 
            WHERE id = %s AND usuario_id = %s
        """
        cursor.execute(query, (status, proposta_id, usuario_id))
        
        cursor.close()
        logger.info(f"Status da proposta #{proposta_id} atualizado para {status}")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status da proposta: {str(e)}")
        logger.error(f"Erro ao atualizar status: {str(e)}")
        return False
    finally:
        conn.close()

# Função principal para finalizar proposta
def finalizar_proposta_direto(proposta_id, usuario_id):
    """Finaliza uma proposta diretamente no banco de dados"""
    try:
        # Obter detalhes da proposta
        proposta = get_proposta_detalhes(proposta_id, usuario_id)
        if not proposta:
            return {
                'status': 'error',
                'message': f'Proposta ID {proposta_id} não encontrada'
            }
        
        # Verificar se já está finalizada
        if proposta['status'] == 'Finalizada':
            return {
                'status': 'error',
                'message': f'Proposta já está finalizada'
            }
        
        # Verificar se existem lançamentos já associados
        lancamentos = get_lancamentos_by_proposta(proposta_id, usuario_id)
        logger.info(f"Existem {len(lancamentos)} lançamentos para a proposta {proposta_id}")
        
        # Verificar se já existe lançamento de receita
        lancamento_principal = False
        for l in lancamentos:
            if l['categoria'] == 'Serviços de Organização' and l['tipo'] == 'receita_a_receber':
                lancamento_principal = True
                break
        
        # Se não existe lançamento principal, criar
        valor_proposta = float(proposta['valor']) if proposta['valor'] is not None else 0.0
        
        if not lancamento_principal:
            # Criar lançamento de receita
            logger.info(f"Criando lançamento principal para proposta {proposta_id}")
            add_lancamento(
                f"Proposta #{proposta['id']} - {proposta['cliente_nome']}",
                valor_proposta,
                datetime.now().date(),
                "Serviços de Organização",
                "receita_a_receber",
                "Pendente",
                "",
                proposta_id,
                usuario_id
            )
        else:
            logger.info(f"Já existe lançamento principal para proposta {proposta_id}")
        
        # Tratar fornecedores
        fornecedores = get_proposta_fornecedores(proposta_id, usuario_id)
        logger.info(f"Encontrados {len(fornecedores)} fornecedores para a proposta {proposta_id}")
        
        for fornecedor in fornecedores:
            # Processar comissão de parceiros se percentual > 0
            percentual = float(fornecedor['percentual']) if fornecedor['percentual'] is not None else 0.0
            
            if percentual > 0:
                valor_comissao = (percentual / 100) * valor_proposta
                logger.info(f"Criando lançamento de comissão de {percentual}% para fornecedor {fornecedor['nome']}")
                
                add_lancamento(
                    f"Comissão {fornecedor['nome']} - Proposta #{proposta['id']}",
                    valor_comissao,
                    datetime.now().date(),
                    "Comissões",
                    "despesa_a_pagar",
                    "Pendente",
                    "",
                    proposta_id,
                    usuario_id
                )
        
        # Tratar acréscimos (outros custos)
        acrescimos = get_proposta_acrescimos(proposta_id, usuario_id)
        outros_acrescimos = [a for a in acrescimos if a['tipo'] == 'OUTRO']
        logger.info(f"Encontrados {len(outros_acrescimos)} acréscimos do tipo OUTRO para a proposta {proposta_id}")
        
        for acrescimo in outros_acrescimos:
            valor_acrescimo = float(acrescimo['valor']) if acrescimo['valor'] is not None else 0.0
            
            if valor_acrescimo > 0:
                logger.info(f"Criando lançamento para acréscimo {acrescimo['descricao']} - R$ {valor_acrescimo}")
                
                add_lancamento(
                    f"Acréscimo de {acrescimo['tipo']} - Proposta #{proposta['id']}",
                    valor_acrescimo,
                    datetime.now().date(),
                    "Custos de Projetos",
                    "despesa_a_pagar",
                    "Pendente",
                    "",
                    proposta_id,
                    usuario_id
                )
        
        # Tratar assistentes
        assistentes = get_proposta_assistentes(proposta_id, usuario_id)
        logger.info(f"Encontrados {len(assistentes)} assistentes para a proposta {proposta_id}")
        
        for assistente in assistentes:
            valor_assistente = float(assistente['valor']) if assistente['valor'] is not None else 0.0
            
            if valor_assistente > 0:
                logger.info(f"Criando lançamento para assistente {assistente['descricao']} - R$ {valor_assistente}")
                
                add_lancamento(
                    f"Serviço de {assistente['descricao']} - Proposta #{proposta['id']}",
                    valor_assistente,
                    datetime.now().date(),
                    "Assistentes",
                    "despesa_a_pagar",
                    "Pendente",
                    "",
                    proposta_id,
                    usuario_id
                )
        
        # Tratar produtos
        produtos = get_proposta_produtos(proposta_id, usuario_id)
        produtos_total = 0
        
        for produto in produtos:
            quantidade = float(produto['quantidade']) if produto['quantidade'] is not None else 0.0
            valor_unitario = float(produto['valor_unitario']) if produto['valor_unitario'] is not None else 0.0
            
            produtos_total += quantidade * valor_unitario
        
        if produtos_total > 0:
            logger.info(f"Criando lançamento para produtos da proposta {proposta_id} - R$ {produtos_total}")
            
            add_lancamento(
                f"Produtos para proposta #{proposta['id']}",
                produtos_total,
                datetime.now().date(),
                "Produtos",
                "despesa_a_pagar",
                "Pendente",
                "",
                proposta_id,
                usuario_id
            )
        
        # Atualizar status da proposta
        update_proposta_status(proposta_id, 'Finalizada', usuario_id)
        
        logger.info(f"Proposta #{proposta_id} finalizada com sucesso!")
        
        return {
            'status': 'success',
            'message': f'Proposta #{proposta_id} finalizada com sucesso! Lançamentos financeiros gerados.',
            'proposta_id': proposta_id
        }
    
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta: {str(e)}")
        return {
            'status': 'error',
            'message': f'Erro ao finalizar proposta: {str(e)}'
        }

# Interface Streamlit para finalizar proposta
def main():
    st.set_page_config(page_title="Finalizar Proposta", page_icon="📝")
    
    st.title("Finalizar Proposta Diretamente")
    st.write("Esta ferramenta finaliza uma proposta diretamente no banco de dados, ignorando o SQLAlchemy e seus problemas de cache.")
    
    # Verificar login
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()
    
    # Obter ID do usuário
    usuario_id = st.session_state.user_info.get('localId')
    
    # Conectar ao banco
    conn = get_db_connection()
    if not conn:
        st.error("Não foi possível conectar ao banco de dados.")
        st.stop()
    
    # Obter propostas não finalizadas
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT p.id, p.descricao, p.valor, p.status, c.nome as cliente_nome 
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.usuario_id = %s AND p.status != 'Finalizada'
            ORDER BY p.id DESC
        """
        cursor.execute(query, (usuario_id,))
        propostas = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao obter propostas: {str(e)}")
        st.stop()
    
    if not propostas:
        st.info("Não há propostas para finalizar.")
        st.stop()
    
    # Criar lista de propostas para seleção
    proposta_options = [f"#{p['id']} - {p['cliente_nome']} - {p['descricao']} - R${p['valor']}" for p in propostas]
    
    selected_proposta = st.selectbox("Selecione a proposta a finalizar:", proposta_options)
    
    if selected_proposta:
        proposta_id = int(selected_proposta.split('-')[0].replace('#', '').strip())
        
        st.write(f"**Proposta selecionada:** ID {proposta_id}")
        
        # Mostrar detalhes da proposta
        proposta = get_proposta_detalhes(proposta_id, usuario_id)
        if proposta:
            st.write(f"**Cliente:** {proposta['cliente_nome']}")
            st.write(f"**Descrição:** {proposta['descricao']}")
            st.write(f"**Valor:** R$ {proposta['valor']}")
            st.write(f"**Status atual:** {proposta['status']}")
        
        # Botão para finalizar proposta
        if st.button("Finalizar Esta Proposta"):
            with st.spinner("Finalizando proposta..."):
                result = finalizar_proposta_direto(proposta_id, usuario_id)
                
                if result['status'] == 'success':
                    st.success(result['message'])
                else:
                    st.error(result['message'])

# Executar a função principal
if __name__ == "__main__":
    main()