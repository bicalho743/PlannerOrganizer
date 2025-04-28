"""
Aplicação Streamlit para finalizar propostas diretamente
Esta aplicação garante que o processo de finalização e geração de lançamentos financeiros funcione corretamente
"""
import streamlit as st
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
import pandas as pd
import json

# Configuração da página
st.set_page_config(
    page_title="Finalizar Propostas",
    page_icon="✅",
    layout="wide"
)

# Funções para conexão com o banco de dados
def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def obter_propostas_nao_finalizadas(usuario_id=None):
    """Obtém lista de propostas não finalizadas"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if usuario_id:
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
        st.error(f"Erro ao obter propostas: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def obter_proposta_detalhes(proposta_id):
    """Obtém detalhes de uma proposta específica"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
            
        # Obter produtos da proposta
        cursor.execute("""
            SELECT * FROM proposta_produtos WHERE proposta_id = %s;
        """, (proposta_id,))
        proposta['produtos'] = cursor.fetchall()
        
        # Obter acréscimos da proposta
        cursor.execute("""
            SELECT * FROM proposta_acrescimos WHERE proposta_id = %s;
        """, (proposta_id,))
        proposta['acrescimos'] = cursor.fetchall()
        
        # Obter assistentes da proposta
        cursor.execute("""
            SELECT * FROM proposta_assistentes WHERE proposta_id = %s;
        """, (proposta_id,))
        proposta['assistentes'] = cursor.fetchall()
        
        # Obter fornecedores da proposta
        cursor.execute("""
            SELECT * FROM proposta_fornecedores WHERE proposta_id = %s;
        """, (proposta_id,))
        proposta['fornecedores'] = cursor.fetchall()
        
        return proposta
    except Exception as e:
        st.error(f"Erro ao obter detalhes da proposta: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def adicionar_lancamento_financeiro(descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id):
    """Adiciona um lançamento financeiro no banco de dados"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        cursor = conn.cursor()
        
        # Verificar campos da tabela financeiro
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
        """)
        colunas = [row[0] for row in cursor.fetchall()]
        
        # Construir query com base nas colunas disponíveis
        colunas_inserir = ['descricao', 'valor', 'data', 'categoria', 'tipo', 'status', 'proposta_id', 'usuario_id']
        valores = [descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id]
        
        # Adicionar forma_pagamento se existir
        if 'forma_pagamento' in colunas:
            colunas_inserir.append('forma_pagamento')
            valores.append('')
        
        # Construir query
        placeholders = ', '.join(['%s'] * len(valores))
        query = f"""
            INSERT INTO financeiro ({', '.join(colunas_inserir)})
            VALUES ({placeholders})
            RETURNING id;
        """
        
        cursor.execute(query, valores)
        lancamento_id = cursor.fetchone()[0]
        
        conn.commit()
        return True, lancamento_id
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao adicionar lançamento: {e}"
    finally:
        cursor.close()
        conn.close()

def finalizar_proposta(proposta_id, usuario_id=None):
    """Finaliza uma proposta e cria os lançamentos financeiros necessários"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        conn.autocommit = False  # Iniciar transação
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        data_atual = datetime.now().date()
        
        # Obter detalhes da proposta
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
            conn.rollback()
            return False, f"Proposta #{proposta_id} já está finalizada"
        
        # Verificar se já existe lançamento principal
        cursor.execute("""
            SELECT id FROM financeiro 
            WHERE proposta_id = %s AND tipo = 'receita_a_receber'
        """, (proposta_id,))
        
        lancamento_existente = cursor.fetchone()
        lancamento_id = None
        
        if not lancamento_existente:
            # Criar lançamento financeiro principal
            descricao = f"Proposta #{proposta_id} - {proposta['cliente_nome']}"
            sucesso, resultado = adicionar_lancamento_financeiro(
                descricao,
                proposta['valor'],
                data_atual,
                'Serviços de Organização',
                'receita_a_receber',
                'Pendente',
                proposta_id,
                proposta['usuario_id']
            )
            
            if not sucesso:
                conn.rollback()
                return False, resultado
                
            lancamento_id = resultado
        
        # Atualizar status e datas da proposta
        cursor.execute("""
            UPDATE propostas 
            SET 
                status = 'Finalizada',
                data_finalizacao = %s,
                data_proposta = COALESCE(data_proposta, data_inicio, %s)
            WHERE id = %s
            RETURNING id;
        """, (data_atual, data_atual, proposta_id))
        
        atualizado = cursor.fetchone()
        if not atualizado:
            conn.rollback()
            return False, f"Erro ao atualizar proposta #{proposta_id}"
        
        conn.commit()
        return True, f"Proposta #{proposta_id} finalizada com sucesso"
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao finalizar proposta: {e}"
    finally:
        cursor.close()
        conn.close()

def listar_lancamentos_da_proposta(proposta_id):
    """Lista todos os lançamentos financeiros de uma proposta"""
    conn = get_db_connection()
    if not conn:
        return None
    
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
        st.error(f"Erro ao listar lançamentos: {e}")
        return None
    finally:
        conn.close()

# Interface Streamlit
def main():
    st.title("✅ Finalizar Propostas")
    
    st.markdown("""
    Esta ferramenta permite finalizar propostas e garantir que os lançamentos financeiros sejam criados corretamente.
    O processo inclui:
    1. Marcar a proposta como 'Finalizada'
    2. Definir a data de finalização
    3. Criar um lançamento financeiro para a proposta
    """)
    
    # Verificar login
    if "user_info" in st.session_state:
        usuario_id = st.session_state.user_info.get('localId')
        st.success(f"Usuário autenticado: {st.session_state.user_info.get('email')}")
    else:
        usuario_id = None
        st.warning("Você não está logado. Algumas funcionalidades podem ser limitadas.")
    
    # Abas
    tab1, tab2 = st.tabs(["Lista de Propostas", "Finalizar Proposta Específica"])
    
    # Tab 1: Lista de Propostas
    with tab1:
        st.header("Propostas não Finalizadas")
        
        if st.button("🔄 Atualizar Lista", key="btn_atualizar"):
            with st.spinner("Carregando propostas..."):
                propostas = obter_propostas_nao_finalizadas(usuario_id)
                if propostas:
                    st.session_state.propostas = propostas
                    
                    # Criar tabela de dados
                    dados = []
                    for p in propostas:
                        dados.append({
                            "ID": p['id'],
                            "Cliente": p['cliente_nome'],
                            "Descrição": p['descricao'],
                            "Valor": f"R$ {p['valor']:.2f}",
                            "Status": p['status'],
                            "Data Início": p['data_inicio'].strftime('%d/%m/%Y') if p['data_inicio'] else "",
                        })
                    
                    df = pd.DataFrame(dados)
                    st.dataframe(df, use_container_width=True)
                    
                    # Seleção de proposta para finalizar
                    st.subheader("Selecionar Proposta para Finalizar")
                    
                    # Criar lista de IDs para seleção
                    proposta_options = [f"#{p['id']} - {p['cliente_nome']} (R$ {p['valor']:.2f})" for p in propostas]
                    
                    if proposta_options:
                        proposta_selecionada = st.selectbox(
                            "Selecione a proposta para finalizar:",
                            options=proposta_options,
                            key="proposta_select"
                        )
                        
                        # Extrair ID da proposta selecionada
                        proposta_id = int(proposta_selecionada.split('#')[1].split(' ')[0])
                        
                        if st.button("✅ Finalizar Proposta Selecionada", key="btn_finalizar_selecionada"):
                            with st.spinner(f"Finalizando proposta #{proposta_id}..."):
                                sucesso, mensagem = finalizar_proposta(proposta_id, usuario_id)
                                
                                if sucesso:
                                    st.success(mensagem)
                                    
                                    # Mostrar lançamentos criados
                                    st.subheader("Lançamentos Financeiros")
                                    lancamentos = listar_lancamentos_da_proposta(proposta_id)
                                    if lancamentos is not None and not lancamentos.empty:
                                        st.dataframe(lancamentos, use_container_width=True)
                                    else:
                                        st.info("Nenhum lançamento financeiro encontrado para esta proposta.")
                                else:
                                    st.error(mensagem)
                    else:
                        st.info("Nenhuma proposta disponível para finalizar.")
                else:
                    st.info("Nenhuma proposta não finalizada encontrada.")
    
    # Tab 2: Finalizar Proposta Específica
    with tab2:
        st.header("Finalizar por ID da Proposta")
        
        proposta_id = st.number_input("ID da Proposta", min_value=1, step=1)
        
        if st.button("🔍 Buscar Proposta", key="btn_buscar"):
            with st.spinner(f"Buscando proposta #{proposta_id}..."):
                proposta = obter_proposta_detalhes(proposta_id)
                
                if proposta:
                    st.session_state.proposta_detalhes = proposta
                    
                    # Mostrar detalhes da proposta
                    st.subheader(f"Proposta #{proposta['id']} - {proposta['cliente_nome']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Descrição:** {proposta['descricao']}")
                        st.write(f"**Valor:** R$ {proposta['valor']:.2f}")
                        st.write(f"**Status:** {proposta['status']}")
                    
                    with col2:
                        st.write(f"**Data Início:** {proposta['data_inicio'].strftime('%d/%m/%Y') if proposta['data_inicio'] else 'Não definida'}")
                        st.write(f"**Data Proposta:** {proposta['data_proposta'].strftime('%d/%m/%Y') if proposta['data_proposta'] else 'Não definida'}")
                        st.write(f"**Data Finalização:** {proposta['data_finalizacao'].strftime('%d/%m/%Y') if proposta.get('data_finalizacao') else 'Não finalizada'}")
                    
                    # Verificar se já está finalizada
                    if proposta['status'] == 'Finalizada':
                        st.warning(f"Esta proposta já está finalizada desde {proposta['data_finalizacao'].strftime('%d/%m/%Y') if proposta.get('data_finalizacao') else 'data desconhecida'}")
                        
                        # Mostrar lançamentos existentes
                        st.subheader("Lançamentos Financeiros")
                        lancamentos = listar_lancamentos_da_proposta(proposta_id)
                        if lancamentos is not None and not lancamentos.empty:
                            st.dataframe(lancamentos, use_container_width=True)
                        else:
                            st.warning("Esta proposta está marcada como finalizada, mas não possui lançamentos financeiros!")
                            
                            if st.button("🔧 Criar Lançamento Financeiro", key="btn_criar_lancamento"):
                                with st.spinner("Criando lançamento financeiro..."):
                                    data_atual = datetime.now().date()
                                    descricao = f"Proposta #{proposta_id} - {proposta['cliente_nome']}"
                                    sucesso, resultado = adicionar_lancamento_financeiro(
                                        descricao,
                                        proposta['valor'],
                                        data_atual,
                                        'Serviços de Organização',
                                        'receita_a_receber',
                                        'Pendente',
                                        proposta_id,
                                        proposta['usuario_id']
                                    )
                                    
                                    if sucesso:
                                        st.success(f"Lançamento financeiro criado com sucesso (ID: {resultado})")
                                    else:
                                        st.error(f"Erro ao criar lançamento: {resultado}")
                    else:
                        # Opção para finalizar
                        if st.button("✅ Finalizar Esta Proposta", key="btn_finalizar_especifica"):
                            with st.spinner(f"Finalizando proposta #{proposta_id}..."):
                                sucesso, mensagem = finalizar_proposta(proposta_id, usuario_id)
                                
                                if sucesso:
                                    st.success(mensagem)
                                    
                                    # Mostrar lançamentos criados
                                    st.subheader("Lançamentos Financeiros Criados")
                                    lancamentos = listar_lancamentos_da_proposta(proposta_id)
                                    if lancamentos is not None and not lancamentos.empty:
                                        st.dataframe(lancamentos, use_container_width=True)
                                    else:
                                        st.warning("Nenhum lançamento financeiro encontrado para esta proposta.")
                                else:
                                    st.error(mensagem)
                else:
                    st.error(f"Proposta #{proposta_id} não encontrada")
    
    # Depuração - visível apenas se st.secrets["debug"] estiver definido como True
    if "debug" in st.secrets and st.secrets["debug"]:
        with st.expander("🔧 Depuração"):
            st.subheader("Estrutura do Banco de Dados")
            if st.button("Verificar Tabelas", key="btn_verificar_tabelas"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Listar tabelas
                    cursor.execute("""
                        SELECT tablename FROM pg_catalog.pg_tables
                        WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
                    """)
                    tabelas = [row[0] for row in cursor.fetchall()]
                    st.write("Tabelas no banco de dados:")
                    st.write(tabelas)
                    
                    # Verificar tabela financeiro
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'financeiro'
                        ORDER BY ordinal_position;
                    """)
                    colunas = cursor.fetchall()
                    st.write("Estrutura da tabela financeiro:")
                    st.json(json.dumps(dict(colunas)))
                    
                    # Verificar tabela propostas
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'propostas'
                        ORDER BY ordinal_position;
                    """)
                    colunas = cursor.fetchall()
                    st.write("Estrutura da tabela propostas:")
                    st.json(json.dumps(dict(colunas)))
                    
                    cursor.close()
                    conn.close()

if __name__ == "__main__":
    main()