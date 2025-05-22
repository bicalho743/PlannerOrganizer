import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import Database

def show():
    st.title("📊 Propostas")
    
    # Inicializar banco de dados
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    db = st.session_state.db
    
    # Menu de navegação com selectbox para garantir que todas as opções apareçam
    opcao_selecionada = st.selectbox(
        "Escolha uma seção:",
        [
            "📝 Nova Proposta",
            "⚙️ Em Execução", 
            "📋 Propostas Finalizadas",
            "🔍 Todas as Propostas"
        ],
        index=0
    )
    
    st.markdown("---")
    
    # SEÇÃO 1: Nova Proposta
    if opcao_selecionada == "📝 Nova Proposta":
        st.header("Nova Proposta")
        st.info("Conteúdo da primeira seção será implementado")
    
    # SEÇÃO 2: Em Execução
    elif opcao_selecionada == "⚙️ Em Execução":
        st.header("Em Execução")
        st.info("Conteúdo da segunda seção será implementado")
    
    # SEÇÃO 3: Propostas Finalizadas
    elif opcao_selecionada == "📋 Propostas Finalizadas":
        st.header("Propostas Finalizadas")
        st.info("Conteúdo da terceira seção será implementado")
    
    # SEÇÃO 4: TODAS AS PROPOSTAS
    elif opcao_selecionada == "🔍 Todas as Propostas":
        st.header("🔍 Todas as Propostas")
        st.success("🎉 SUCESSO! A 4ª aba está funcionando!")
        st.info("Esta aba mostra todas as propostas, independentemente do status - Abertas, Em execução, Finalizadas e Recusadas.")
        
        try:
            # Obter todas as propostas
            propostas = db.get_propostas()
            
            if not propostas.empty:
                st.write(f"**Total de propostas encontradas: {len(propostas)}**")
                
                # Mostrar tabela com todas as propostas
                colunas_exibir = ['numero', 'cliente_nome', 'descricao', 'valor', 'status', 'status_execucao', 'data_criacao']
                colunas_disponiveis = [col for col in colunas_exibir if col in propostas.columns]
                
                if colunas_disponiveis:
                    st.dataframe(propostas[colunas_disponiveis], use_container_width=True)
                else:
                    st.dataframe(propostas, use_container_width=True)
                
                # Mostrar estatísticas por status
                if 'status' in propostas.columns:
                    st.subheader("Estatísticas por Status")
                    status_counts = propostas['status'].value_counts()
                    st.bar_chart(status_counts)
                    
                    # Mostrar detalhes
                    for status, count in status_counts.items():
                        st.write(f"- **{status}**: {count} proposta(s)")
                        
            else:
                st.warning("Nenhuma proposta encontrada no sistema.")
                
        except Exception as e:
            st.error(f"Erro ao carregar propostas: {str(e)}")
            st.error("Verifique a conexão com o banco de dados.")

if __name__ == "__main__":
    show()