import streamlit as st
import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker

# Título da página
st.title("Examinador de Estrutura da Tabela Propostas")

# Conectar ao banco usando SQLAlchemy
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    st.error("Variável de ambiente DATABASE_URL não definida.")
    st.stop()

# Conectar diretamente com psycopg2 para verificar a estrutura
st.subheader("Estrutura da Tabela (psycopg2)")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar se a tabela existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'proposta'
        );
    """)
    tabela_existe = cursor.fetchone()[0]
    
    if not tabela_existe:
        st.error("Tabela 'proposta' não existe no banco de dados!")
    else:
        st.success("Tabela 'proposta' encontrada no banco de dados.")
        
        # Obter estrutura da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'proposta'
            ORDER BY ordinal_position;
        """)
        
        colunas = cursor.fetchall()
        df_colunas = pd.DataFrame(colunas, columns=['coluna', 'tipo', 'nulavel', 'default'])
        st.write("### Estrutura da tabela:")
        st.dataframe(df_colunas)
        
        # Verificar valores na tabela
        cursor.execute("SELECT COUNT(*) FROM proposta;")
        count = cursor.fetchone()[0]
        st.write(f"Número de registros na tabela: {count}")
        
        if count > 0:
            st.write("### Amostra de dados:")
            cursor.execute("SELECT * FROM proposta LIMIT 5;")
            amostra = cursor.fetchall()
            
            # Obter nomes das colunas
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'proposta'
                ORDER BY ordinal_position;
            """)
            nomes_colunas = [col[0] for col in cursor.fetchall()]
            
            df_amostra = pd.DataFrame(amostra, columns=nomes_colunas)
            st.dataframe(df_amostra)
    
    # Verificar constraints/foreign keys
    st.subheader("Constraints e Foreign Keys")
    cursor.execute("""
        SELECT tc.constraint_name, tc.constraint_type, 
               kcu.column_name, 
               ccu.table_name AS foreign_table_name,
               ccu.column_name AS foreign_column_name 
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.table_name = 'proposta';
    """)
    
    constraints = cursor.fetchall()
    if constraints:
        df_constraints = pd.DataFrame(constraints, 
                                     columns=['nome_constraint', 'tipo_constraint', 
                                             'coluna', 'tabela_referencia', 'coluna_referencia'])
        st.dataframe(df_constraints)
    else:
        st.info("Nenhuma constraint encontrada para a tabela 'proposta'.")
    
    # Testes de inserção com dados específicos
    st.subheader("Teste de Inserção")
    
    if st.button("Realizar teste de inserção"):
        try:
            # Obter valor máximo atual da coluna número
            cursor.execute("SELECT MAX(numero) FROM proposta;")
            max_numero = cursor.fetchone()[0]
            proximo_numero = 1 if max_numero is None else max_numero + 1
            
            # Teste com dados explícitos
            cursor.execute("""
                INSERT INTO proposta (
                    numero, cliente_id, descricao, valor, status, 
                    tipo_proposta, data_inicio, data_fim, prazo_entrega
                ) VALUES (
                    %s, 1, 'Teste de Inserção Direto', 1000.00, 'Em andamento',
                    'Organização', CURRENT_DATE, CURRENT_DATE + INTERVAL '7 day', 
                    CURRENT_DATE + INTERVAL '14 day'
                ) RETURNING id;
            """, (proximo_numero,))
            
            novo_id = cursor.fetchone()[0]
            conn.commit()
            
            st.success(f"Inserção bem-sucedida! Novo ID: {novo_id}")
        except Exception as e:
            conn.rollback()
            st.error(f"Erro ao inserir registro de teste: {str(e)}")
    
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn:
        conn.close()

# Conexão usando SQLAlchemy
st.subheader("Estrutura da Tabela (SQLAlchemy)")

try:
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    if 'proposta' in metadata.tables:
        proposta_table = metadata.tables['proposta']
        
        # Obter detalhes da tabela
        insp = inspect(engine)
        columns = insp.get_columns('proposta')
        
        df_columns = pd.DataFrame([
            {
                'nome': col['name'],
                'tipo': str(col['type']),
                'nulavel': col['nullable'],
                'default': col.get('default', None)
            } for col in columns
        ])
        
        st.write("### Estrutura da tabela (SQLAlchemy):")
        st.dataframe(df_columns)
        
        # Criar sessão e testar inserção
        Session = sessionmaker(bind=engine)
        session = Session()
        
        if st.button("Realizar teste de inserção com SQLAlchemy"):
            try:
                # Obter valor máximo atual da coluna número
                max_numero = session.query(proposta_table.c.numero).order_by(
                    proposta_table.c.numero.desc()
                ).limit(1).scalar()
                
                proximo_numero = 1 if max_numero is None else max_numero + 1
                
                # Inserir usando SQLAlchemy core
                from datetime import datetime, timedelta
                hoje = datetime.now().date()
                
                insert_stmt = proposta_table.insert().values(
                    numero=proximo_numero,
                    cliente_id=1,
                    descricao="Teste de Inserção via SQLAlchemy",
                    valor=1200.00,
                    status="Em andamento",
                    tipo_proposta="Organização",
                    data_inicio=hoje,
                    data_fim=hoje + timedelta(days=7),
                    prazo_entrega=hoje + timedelta(days=14)
                )
                
                result = session.execute(insert_stmt)
                session.commit()
                
                st.success(f"Inserção via SQLAlchemy bem-sucedida!")
            except Exception as e:
                session.rollback()
                st.error(f"Erro ao inserir via SQLAlchemy: {str(e)}")
            finally:
                session.close()
        
    else:
        st.error("Tabela 'proposta' não encontrada via SQLAlchemy!")
        
except Exception as e:
    st.error(f"Erro ao conectar via SQLAlchemy: {str(e)}")