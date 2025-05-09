import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from utils.database import Database

# Configuração da página
st.set_page_config(
    page_title="Planner Organiza - Propostas Finalizadas",
    page_icon="📝",
    layout="wide"
)

# Verificar login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Inicializar banco de dados
db = Database()

# Título da página
st.title("📝 Propostas Finalizadas")

# Função para carregar propostas finalizadas
def carregar_propostas_finalizadas():
    # Obter todas as propostas
    propostas = db.get_propostas()
    
    # Filtrar apenas as propostas finalizadas
    if not propostas.empty:
        propostas_finalizadas = propostas[
            ((propostas['status'] == 'Finalizada') & (propostas['status_execucao'] == 'Finalizada')) |
            (propostas['status'] == 'Recusada')
        ]
        return propostas_finalizadas
    return pd.DataFrame()

# Carregar propostas finalizadas
propostas_finalizadas = carregar_propostas_finalizadas()

# Exibir contagem de propostas finalizadas
st.write(f"Total de propostas finalizadas encontradas: {len(propostas_finalizadas)}")

# Verificar se temos propostas finalizadas
if not propostas_finalizadas.empty:
    # Exibir propostas no formato expandível
    for idx, proposta in propostas_finalizadas.iterrows():
        # Criar um expander para cada proposta
        with st.expander(f"{proposta['numero']} - {proposta['cliente_nome']} - {proposta['descricao']} (R$ {proposta['valor']:.2f})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {proposta['id']}")
                st.write(f"**Cliente:** {proposta['cliente_nome']}")
                st.write(f"**Descrição:** {proposta['descricao']}")
                st.write(f"**Valor:** R$ {proposta['valor']:.2f}")
                
            with col2:
                st.write(f"**Tipo:** {proposta['tipo_proposta']}")
                st.write(f"**Status:** {proposta['status']}")
                st.write(f"**Status Execução:** {proposta['status_execucao']}")
                data_inicio_str = proposta['data_inicio'].strftime('%d/%m/%Y') if pd.notna(proposta['data_inicio']) else 'N/D'
                st.write(f"**Data Início:** {data_inicio_str}")
                data_fim_str = proposta['data_fim'].strftime('%d/%m/%Y') if pd.notna(proposta['data_fim']) else 'N/D'
                st.write(f"**Data Fim:** {data_fim_str}")
            
            # Adicionar botões de ação
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Gerar Relatório", key=f"rel_btn_{proposta['id']}"):
                    st.session_state.proposta_selec_relatorio = proposta['id']
                    st.rerun()
            
            with col_btn2:
                if st.button("Reabrir Proposta", key=f"reabrir_btn_{proposta['id']}"):
                    st.session_state.proposta_selec_reabrir = proposta['id']
                    st.rerun()
else:
    st.info("Não há propostas finalizadas no momento.")

# Seção para reabrir proposta finalizada
if not propostas_finalizadas.empty:
    st.subheader("Reabrir Proposta Finalizada")
    
    # Obter lista de números de propostas finalizadas para o select box
    numeros_propostas = propostas_finalizadas['numero'].tolist()
    numeros_propostas.sort()  # Ordenar para facilitar a seleção
    
    proposta_numero = st.selectbox(
        "Selecione o número da proposta a reabrir:",
        numeros_propostas,
        key="numero_proposta_finalizada_reabrir"
    )
    
    proposta_reabrir = propostas_finalizadas[propostas_finalizadas['numero'] == proposta_numero]
    
    if not proposta_reabrir.empty:
        st.info(f"Você está prestes a reabrir a proposta #{proposta_numero} - {proposta_reabrir.iloc[0]['descricao']}")
        st.warning("Esta ação mudará o status da proposta para 'Em execução'.")
        
        if st.button("REABRIR PROPOSTA", key="confirmar_reabertura"):
            try:
                # Importar função de reabrir proposta
                from reabrir_proposta import reabrir_proposta_finalizada
                
                # Obter ID da proposta
                proposta_id = proposta_reabrir.iloc[0]['id']
                
                # Chamar função de reabertura
                resultado = reabrir_proposta_finalizada(proposta_id)
                
                if resultado.get('status') == 'sucesso':
                    st.success(resultado.get('mensagem'))
                    st.rerun()
                elif resultado.get('status') == 'sucesso_com_alerta':
                    st.success(resultado.get('mensagem'))
                    st.warning(resultado.get('alerta'))
                    st.info(f"Encontrados {resultado.get('lancamentos_encontrados')} lançamentos financeiros.")
                    st.rerun()
                else:
                    st.error(f"Erro ao reabrir proposta: {resultado.get('mensagem')}")
            except Exception as e:
                st.error(f"Erro ao reabrir proposta: {str(e)}")