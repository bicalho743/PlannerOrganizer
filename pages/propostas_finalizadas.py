"""
Página dedicada para visualização e gerenciamento de propostas finalizadas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
from utils.database import Database
import os

# Importar funções para geração de PDF
from utils.propostas_helper import st_gerar_pdf_cliente, st_gerar_pdf_interno

def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Propostas Finalizadas</h1>', unsafe_allow_html=True)
    
    # Verificar se temos uma conexão com o banco de dados
    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return
    
    # Obter todas as propostas diretamente
    todas_propostas = st.session_state.db.get_propostas()
    
    # Adicionar informação de diagnóstico
    st.info(f"Total de propostas no banco: {len(todas_propostas) if not todas_propostas.empty else 0}")
    
    # Filtro para propostas finalizadas
    if not todas_propostas.empty:
        # Aplicar filtro
        from utils.proposta_status import STATUS_FINALIZADA, STATUS_RECUSADA, label_for as _label_status
        propostas_finalizadas = todas_propostas[
            ((todas_propostas['status'] == STATUS_FINALIZADA) & (todas_propostas['status_execucao'] == 'Finalizada')) |
            (todas_propostas['status'] == STATUS_RECUSADA)
        ]
        
        # Mostrar contagem para debug
        st.write(f"Total de propostas finalizadas encontradas: {len(propostas_finalizadas)}")
        
        if not propostas_finalizadas.empty:
            # Exibir cada proposta em um expander
            for idx, proposta in propostas_finalizadas.iterrows():
                with st.expander(f"{proposta['numero']} - {proposta['cliente_nome']} - {proposta['descricao']} (R$ {proposta['valor']:.2f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {proposta['id']}")
                        st.write(f"**Cliente:** {proposta['cliente_nome']}")
                        st.write(f"**Descrição:** {proposta['descricao']}")
                        st.write(f"**Valor:** R$ {proposta['valor']:.2f}")
                        
                    with col2:
                        st.write(f"**Tipo:** {proposta['tipo_proposta']}")
                        st.write(f"**Status:** {_label_status(proposta['status'])}")
                        st.write(f"**Status Execução:** {proposta['status_execucao']}")
                        data_inicio_str = proposta['data_inicio'].strftime('%d/%m/%Y') if pd.notna(proposta['data_inicio']) else 'N/D'
                        st.write(f"**Data Início:** {data_inicio_str}")
                        data_fim_str = proposta['data_fim'].strftime('%d/%m/%Y') if pd.notna(proposta['data_fim']) else 'N/D'
                        st.write(f"**Data Fim:** {data_fim_str}")
                    
                    # Adicionar botões de ação
                    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                    
                    with col_btn1:
                        if st.button("Relatório Cliente", key=f"rel_cliente_btn_{proposta['id']}"):
                            # Usar a função importada no início do arquivo
                            st_gerar_pdf_cliente(proposta['id'])
                    
                    with col_btn2:
                        if st.button("Relatório Interno", key=f"rel_interno_btn_{proposta['id']}"):
                            # Usar a função importada no início do arquivo
                            st_gerar_pdf_interno(proposta['id'])
                            
                    with col_btn3:
                        if st.button("Gerar Relatório", key=f"rel_btn_{proposta['id']}"):
                            st.session_state.proposta_selec_relatorio = proposta['id']
                            st.rerun()
                    
                    with col_btn4:
                        if st.button("Reabrir Proposta", key=f"reabrir_btn_{proposta['id']}"):
                            st.session_state.proposta_selec_reabrir = proposta['id']
                            st.rerun()
        else:
            st.info("Não há propostas finalizadas no momento.")
            
    else:
        st.warning("Não foram encontradas propostas no banco de dados.")
    
    # Mostrar seção para reabrir proposta se houver propostas finalizadas
    if not todas_propostas.empty and not propostas_finalizadas.empty:
        with st.expander("Reabrir Proposta Finalizada"):
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
                st.warning("Esta ação mudará o status da proposta para 'Em Execução'.")
                
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

if __name__ == "__main__":
    show()