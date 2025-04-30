import streamlit as st
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
import traceback

def atualizar_categorias_financeiro():
    """Atualiza as categorias dos lançamentos financeiros de 'Propostas' para 'Serviços de Organização'"""
    st.title("Atualizar Categorias do Financeiro")
    
    st.write("Essa ferramenta atualiza todas as categorias incorretas no módulo financeiro:")
    st.write("- Muda categorias 'Propostas' para 'Serviços de Organização'")
    st.write("- Muda categorias 'Serviço' para 'Serviços de Organização'")
    
    # Obter conexão com o banco
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        st.error("DATABASE_URL não encontrada no ambiente")
        return
    
    try:
        # Criar conexão e engine
        engine = create_engine(db_url)
        
        # Contar os registros que serão atualizados
        with engine.connect() as conn:
            # Contar registros com categoria "Propostas"
            result_propostas = conn.execute(text("SELECT COUNT(*) FROM transacoes WHERE categoria = 'Propostas'"))
            count_propostas = result_propostas.scalar()
            
            # Contar registros com categoria "Serviço"
            result_servico = conn.execute(text("SELECT COUNT(*) FROM transacoes WHERE categoria = 'Serviço'"))
            count_servico = result_servico.scalar()
            
            total_atualizar = count_propostas + count_servico
        
        st.info(f"Total de registros a serem atualizados: {total_atualizar}")
        st.info(f"- {count_propostas} registros com categoria 'Propostas'")
        st.info(f"- {count_servico} registros com categoria 'Serviço'")
        
        if st.button("Atualizar Categorias", type="primary"):
            with st.spinner("Atualizando registros..."):
                try:
                    with engine.connect() as conn:
                        # Atualizar registros com categoria "Propostas"
                        query_propostas = text("UPDATE transacoes SET categoria = 'Serviços de Organização' WHERE categoria = 'Propostas'")
                        result_propostas = conn.execute(query_propostas)
                        
                        # Atualizar registros com categoria "Serviço"
                        query_servico = text("UPDATE transacoes SET categoria = 'Serviços de Organização' WHERE categoria = 'Serviço'")
                        result_servico = conn.execute(query_servico)
                        
                        # Realizar commit
                        conn.commit()
                    
                    st.success(f"Atualização concluída! {total_atualizar} registros foram atualizados.")
                    st.info("Agora todos os registros estão usando a categoria 'Serviços de Organização'.")
                except Exception as e:
                    st.error(f"Erro ao atualizar registros: {str(e)}")
                    st.error(traceback.format_exc())
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    atualizar_categorias_financeiro()