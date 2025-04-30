"""
Aplicação Streamlit para corrigir problemas de finalização de propostas
Esta app permite visualizar e corrigir propostas que não aparecem corretamente na interface
"""
import streamlit as st
import psycopg2
import os
from datetime import datetime
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Corrigir Propostas",
    page_icon="🛠️",
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

def verificar_estrutura_banco():
    """Verifica a estrutura das tabelas relevantes"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar tabela propostas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'propostas'
            ORDER BY ordinal_position;
        """)
        colunas_propostas = [row[0] for row in cursor.fetchall()]
        
        # Verificar tabela financeiro
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financeiro'
            ORDER BY ordinal_position;
        """)
        colunas_financeiro = [row[0] for row in cursor.fetchall()]
        
        return {
            'propostas': colunas_propostas,
            'financeiro': colunas_financeiro
        }
    except Exception as e:
        st.error(f"Erro ao verificar estrutura do banco: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def obter_propostas_problematicas():
    """Identifica propostas com problemas de exibição na interface"""
    conn = get_db_connection()
    if not conn:
        return None, None
    
    try:
        # Propostas com inconsistências em campos de data
        inconsistentes_query = """
            SELECT id, status, data_inicio, data_proposta, data_finalizacao, usuario_id, ativo
            FROM propostas
            WHERE 
                (status = 'Finalizada' AND data_finalizacao IS NULL)
                OR (status = 'Finalizada' AND data_proposta IS NULL)
                OR (status = 'Em execução' AND data_finalizacao IS NOT NULL)
            ORDER BY id DESC;
        """
        
        # Propostas finalizadas sem lançamentos financeiros
        sem_lancamentos_query = """
            SELECT 
                p.id, 
                p.status, 
                p.valor, 
                c.nome as cliente_nome,
                p.data_finalizacao,
                p.usuario_id
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN financeiro f ON p.id = f.proposta_id AND f.tipo = 'receita_a_receber'
            WHERE p.status = 'Finalizada' AND f.id IS NULL
            ORDER BY p.id DESC;
        """
        
        propostas_inconsistentes = pd.read_sql(inconsistentes_query, conn)
        propostas_sem_lancamentos = pd.read_sql(sem_lancamentos_query, conn)
        
        return propostas_inconsistentes, propostas_sem_lancamentos
    except Exception as e:
        st.error(f"Erro ao identificar propostas problemáticas: {e}")
        return None, None
    finally:
        conn.close()

def listar_todas_propostas():
    """Lista todas as propostas no banco de dados"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        query = """
            SELECT 
                p.id, 
                p.descricao, 
                p.valor, 
                p.status, 
                c.nome as cliente_nome,
                p.data_inicio,
                p.data_proposta,
                p.data_finalizacao
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.id DESC
            LIMIT 100;
        """
        
        propostas = pd.read_sql(query, conn)
        return propostas
    except Exception as e:
        st.error(f"Erro ao listar propostas: {e}")
        return None
    finally:
        conn.close()

def corrigir_proposta(proposta_id, finalizar=False):
    """Corrige uma proposta específica"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        conn.autocommit = False  # Iniciar transação
        cursor = conn.cursor()
        data_atual = datetime.now().date()
        
        # Verificar se a proposta existe
        cursor.execute("""
            SELECT id, status, data_inicio, data_proposta, data_finalizacao, usuario_id
            FROM propostas
            WHERE id = %s;
        """, (proposta_id,))
        
        proposta = cursor.fetchone()
        if not proposta:
            conn.rollback()
            return False, f"Proposta #{proposta_id} não encontrada"
        
        proposta_id, status, data_inicio, data_proposta, data_finalizacao, usuario_id = proposta
        
        # Se foi solicitado para finalizar ou já está finalizada
        if finalizar or status == 'Finalizada':
            # Atualizar status e datas
            cursor.execute("""
                UPDATE propostas 
                SET 
                    status = 'Finalizada',
                    data_finalizacao = COALESCE(%s, data_finalizacao, %s),
                    data_proposta = COALESCE(data_proposta, data_inicio, %s),
                    ativo = TRUE
                WHERE id = %s;
            """, (data_atual if not data_finalizacao else None, data_atual, data_atual, proposta_id))
            
            # Adicionar lançamento financeiro se não existir
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
                WHERE p.id = %s
                AND NOT EXISTS (
                    SELECT 1 FROM financeiro 
                    WHERE proposta_id = %s AND tipo = 'receita_a_receber'
                );
            """, (data_atual, proposta_id, proposta_id))
            
            mensagem = f"Proposta #{proposta_id} finalizada e corrigida com sucesso"
        else:
            # Se não deve finalizar mas tem data_finalizacao, remover
            if data_finalizacao is not None:
                cursor.execute("""
                    UPDATE propostas 
                    SET data_finalizacao = NULL
                    WHERE id = %s;
                """, (proposta_id,))
                
            mensagem = f"Proposta #{proposta_id} corrigida (mantida como {status})"
        
        conn.commit()
        return True, mensagem
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao corrigir proposta #{proposta_id}: {e}"
    finally:
        cursor.close()
        conn.close()

def corrigir_todas_propostas():
    """Corrige todas as propostas com problemas"""
    conn = get_db_connection()
    if not conn:
        return False, "Erro de conexão com o banco de dados"
    
    try:
        conn.autocommit = False  # Iniciar transação
        cursor = conn.cursor()
        data_atual = datetime.now().date()
        
        # 1. Garantir que todas as propostas finalizadas tenham data_finalizacao
        cursor.execute("""
            UPDATE propostas 
            SET data_finalizacao = %s
            WHERE status = 'Finalizada' AND data_finalizacao IS NULL
            RETURNING id;
        """, (data_atual,))
        
        propostas_atualizadas_1 = cursor.fetchall()
        
        # 2. Garantir que todas as propostas finalizadas tenham data_proposta
        cursor.execute("""
            UPDATE propostas 
            SET data_proposta = COALESCE(data_inicio, %s)
            WHERE status = 'Finalizada' AND data_proposta IS NULL
            RETURNING id;
        """, (data_atual,))
        
        propostas_atualizadas_2 = cursor.fetchall()
        
        # 3. Remover data_finalizacao de propostas não finalizadas
        cursor.execute("""
            UPDATE propostas 
            SET data_finalizacao = NULL
            WHERE status <> 'Finalizada' AND data_finalizacao IS NOT NULL
            RETURNING id;
        """)
        
        propostas_atualizadas_3 = cursor.fetchall()
        
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
        
        # 5. Corrigir propostas com status incorreto
        cursor.execute("""
            UPDATE propostas
            SET status = 'Finalizada'
            WHERE status = 'Em análise' AND data_finalizacao IS NOT NULL
            RETURNING id;
        """)
        
        propostas_atualizadas_4 = cursor.fetchall()
        
        conn.commit()
        
        mensagem = (
            f"Correção concluída com sucesso:\n"
            f"- {len(propostas_atualizadas_1)} propostas com data_finalizacao adicionada\n"
            f"- {len(propostas_atualizadas_2)} propostas com data_proposta adicionada\n"
            f"- {len(propostas_atualizadas_3)} propostas não finalizadas corrigidas\n"
            f"- {len(lancamentos_criados)} lançamentos financeiros criados\n"
            f"- {len(propostas_atualizadas_4)} propostas com status corrigido"
        )
        
        return True, mensagem
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao corrigir propostas: {e}"
    finally:
        cursor.close()
        conn.close()

# Interface Streamlit
def main():
    st.title("🛠️ Correção de Propostas")
    
    st.markdown("""
    Esta ferramenta ajuda a corrigir problemas com propostas que não aparecem corretamente na interface.
    
    ### Problemas comuns:
    - Propostas finalizadas, mas sem data de finalização
    - Propostas finalizadas, mas sem data da proposta
    - Propostas em execução, mas com data de finalização
    - Propostas finalizadas sem lançamentos financeiros
    """)
    
    # Verificar login
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        with st.expander("⚠️ Você não está autenticado", expanded=True):
            st.warning("Você não está logado no sistema. Para utilizar esta ferramenta, você precisa estar autenticado.")
            st.info("Se você estiver logado no Render, esta ferramenta funcionará corretamente.")
    
    # Abas
    tab1, tab2, tab3 = st.tabs(["Diagnóstico", "Correção Individual", "Correção em Massa"])
    
    # Tab 1: Diagnóstico
    with tab1:
        st.header("Diagnóstico de Propostas")
        
        if st.button("🔍 Verificar Propostas Problemáticas", key="btn_verificar"):
            with st.spinner("Analisando propostas..."):
                propostas_inconsistentes, propostas_sem_lancamentos = obter_propostas_problematicas()
                
                if propostas_inconsistentes is not None:
                    st.session_state.propostas_inconsistentes = propostas_inconsistentes
                    st.session_state.propostas_sem_lancamentos = propostas_sem_lancamentos
                    
                    # Mostrar resultados
                    st.subheader("Propostas com Inconsistências nas Datas")
                    if not propostas_inconsistentes.empty:
                        st.dataframe(propostas_inconsistentes, use_container_width=True)
                        st.info(f"Encontradas {len(propostas_inconsistentes)} propostas com inconsistências nas datas")
                    else:
                        st.success("Nenhuma proposta com inconsistências nas datas encontrada!")
                    
                    st.subheader("Propostas Finalizadas sem Lançamentos Financeiros")
                    if not propostas_sem_lancamentos.empty:
                        st.dataframe(propostas_sem_lancamentos, use_container_width=True)
                        st.info(f"Encontradas {len(propostas_sem_lancamentos)} propostas finalizadas sem lançamentos financeiros")
                    else:
                        st.success("Nenhuma proposta finalizada sem lançamentos financeiros encontrada!")
        
        # Listar todas as propostas
        st.header("Todas as Propostas")
        if st.button("📋 Listar Todas as Propostas", key="btn_listar"):
            with st.spinner("Carregando propostas..."):
                propostas = listar_todas_propostas()
                if propostas is not None:
                    st.dataframe(propostas, use_container_width=True)
    
    # Tab 2: Correção Individual
    with tab2:
        st.header("Corrigir Proposta Específica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            proposta_id = st.number_input("ID da Proposta", min_value=1, step=1)
            finalizar = st.checkbox("Finalizar Proposta", 
                                   help="Se marcado, a proposta será finalizada mesmo que não esteja atualmente")
        
        with col2:
            st.markdown("### Ações:")
            if st.button("🔧 Corrigir Proposta", key="btn_corrigir"):
                with st.spinner(f"Corrigindo proposta #{proposta_id}..."):
                    sucesso, mensagem = corrigir_proposta(proposta_id, finalizar)
                    
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)
    
    # Tab 3: Correção em Massa
    with tab3:
        st.header("Corrigir Todas as Propostas Problemáticas")
        
        st.warning("""
        ⚠️ **ATENÇÃO**: Esta opção irá corrigir TODAS as propostas com problemas no banco de dados.
        
        Isso inclui:
        - Adicionar data_finalizacao às propostas finalizadas sem esse campo
        - Adicionar data_proposta às propostas finalizadas sem esse campo
        - Remover data_finalizacao de propostas não finalizadas
        - Criar lançamentos financeiros para propostas finalizadas que não os têm
        - Corrigir status inconsistentes com data_finalizacao
        
        Recomenda-se fazer um backup do banco antes de prosseguir.
        """)
        
        confirma = st.checkbox("Confirmo que desejo corrigir todas as propostas problemáticas")
        
        if confirma:
            if st.button("🔧 CORRIGIR TODAS AS PROPOSTAS", key="btn_corrigir_todas"):
                with st.spinner("Corrigindo todas as propostas problemáticas..."):
                    sucesso, mensagem = corrigir_todas_propostas()
                    
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)
        else:
            st.info("Marque a caixa de confirmação para habilitar a correção em massa")
    
    # Informações técnicas
    with st.expander("ℹ️ Informações Técnicas"):
        st.subheader("Estrutura do Banco de Dados")
        if st.button("🔍 Verificar Estrutura", key="btn_estrutura"):
            with st.spinner("Analisando estrutura do banco..."):
                estrutura = verificar_estrutura_banco()
                if estrutura:
                    st.write("**Colunas da tabela propostas:**")
                    st.write(", ".join(estrutura['propostas']))
                    
                    st.write("**Colunas da tabela financeiro:**")
                    st.write(", ".join(estrutura['financeiro']))

if __name__ == "__main__":
    main()