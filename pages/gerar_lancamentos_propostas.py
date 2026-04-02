import streamlit as st
import pandas as pd
from datetime import datetime
from utils.currency_formatter import fmt_brl
import time

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Gerar Lançamentos para Propostas",
    page_icon="📊",
    layout="wide"
)

# Verificar autenticação
from utils.auth_guard import require_auth
require_auth()

# Título da página
st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Gerar Lançamentos Financeiros para Propostas</h1>', unsafe_allow_html=True)

# Descrição
st.write("""
Esta ferramenta permite gerar ou regenerar lançamentos financeiros para propostas que já estão 
aprovadas ou em execução, mas que não tiveram seus lançamentos financeiros gerados corretamente.
""")

# Obter propostas
@st.cache_data(ttl=60)
def carregar_propostas():
    try:
        # Buscar todas as propostas
        propostas_df = st.session_state.db.get_propostas()
        
        # Filtrar apenas Aprovadas e Em Execução
        propostas_df = propostas_df[propostas_df['status'].isin(['Aprovada', 'Em execução'])]
        
        if propostas_df.empty:
            return pd.DataFrame()
            
        # Formatar valores
        propostas_df['valor_formatado'] = propostas_df['valor'].apply(fmt_brl)
        
        # Ordenar por data de modificação (mais recentes primeiro)
        if 'data_modificacao' in propostas_df.columns:
            propostas_df = propostas_df.sort_values(by='data_modificacao', ascending=False)
            
        return propostas_df
    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")
        return pd.DataFrame()

# Verificar se há lançamentos financeiros para a proposta
def verificar_lancamentos(proposta_id):
    try:
        # Buscar transações relacionadas à proposta
        query = f"""
        SELECT COUNT(*) as total 
        FROM transacoes 
        WHERE proposta_id = {proposta_id} 
        AND (tipo = 'receita_a_receber_aprovacao' OR tipo = 'contas_a_receber')
        """
        
        resultado = st.session_state.db.executar_query_sql_direto(query)
        if resultado.empty:
            return 0
        
        return resultado.iloc[0]['total']
    except Exception as e:
        st.error(f"Erro ao verificar lançamentos: {str(e)}")
        return 0

# Carregar propostas
propostas_df = carregar_propostas()

if propostas_df.empty:
    st.warning("Não há propostas aprovadas ou em execução.")
else:
    # Exibir propostas
    st.subheader("Propostas Disponíveis")
    
    # Adicionar coluna com número de lançamentos existentes
    propostas_df['lancamentos'] = propostas_df['id'].apply(verificar_lancamentos)
    
    # Formatar para exibição
    propostas_display = propostas_df.copy()
    propostas_display['status_lancamentos'] = propostas_display['lancamentos'].apply(
        lambda x: "✅ Lançamentos existentes" if x > 0 else "❌ Sem lançamentos"
    )
    
    # Exibir tabela de propostas
    st.dataframe(
        propostas_display[['id', 'numero', 'nome', 'descricao', 'status', 'valor_formatado', 'status_lancamentos']],
        use_container_width=True,
        column_config={
            "id": "ID",
            "numero": "Número",
            "nome": "Cliente",
            "descricao": "Descrição",
            "status": "Status",
            "valor_formatado": "Valor",
            "status_lancamentos": "Situação dos Lançamentos"
        }
    )
    
    # Seleção da proposta
    proposta_ids = propostas_df['id'].tolist()
    proposta_numeros = propostas_df['numero'].tolist()
    proposta_clientes = propostas_df['nome'].tolist()
    
    # Criar opções de seleção combinando número + cliente para melhor identificação
    opcoes_selecao = [f"#{num} - {cliente}" for num, cliente in zip(proposta_numeros, proposta_clientes)]
    
    # Seleção da proposta
    with st.form(key='gerar_lancamentos_form'):
        st.subheader("Selecione a Proposta para Gerar/Regenerar Lançamentos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selecao_index = st.selectbox(
                "Proposta:",
                range(len(opcoes_selecao)),
                format_func=lambda x: opcoes_selecao[x]
            )
        
        with col2:
            forcar_regeneracao = st.checkbox(
                "Forçar regeneração (apaga lançamentos existentes)", 
                value=True,
                help="Se marcado, removerá quaisquer lançamentos financeiros existentes antes de criar novos."
            )
        
        proposta_id = proposta_ids[selecao_index]
        proposta_info = propostas_df[propostas_df['id'] == proposta_id].iloc[0]
        
        # Exibir informações da proposta selecionada
        st.info(f"""
        **Proposta Selecionada:** #{proposta_info['numero']} - {proposta_info['nome']}  
        **Descrição:** {proposta_info['descricao']}  
        **Status:** {proposta_info['status']}  
        **Valor:** {proposta_info['valor_formatado']}  
        **Lançamentos existentes:** {proposta_info['lancamentos']}
        """)
        
        submit_button = st.form_submit_button(label="Gerar Lançamentos Financeiros")
    
    if submit_button:
        with st.spinner("Gerando lançamentos financeiros..."):
            try:
                # Chamar função para gerar lançamentos
                resultado = st.session_state.db.gerar_lancamentos_proposta_aprovada(
                    proposta_id=proposta_id,
                    forcar_geracao=forcar_regeneracao
                )
                
                # Verificar resultado
                if resultado:
                    if 'status' in resultado and resultado['status'] == 'já existe' and not forcar_regeneracao:
                        st.warning(f"Lançamentos já existem para esta proposta. Marque 'Forçar regeneração' para substituí-los.")
                    else:
                        valor_base = resultado.get('valor_base', 0)
                        lancamentos = resultado.get('lancamentos_gerados', 0)
                        st.success(f"Lançamentos gerados com sucesso! Valor base: R$ {valor_base:.2f}, Total de lançamentos: {lancamentos}")
                        
                        # Recarregar dados após alguns segundos
                        st.rerun()
                else:
                    st.error("Falha ao gerar lançamentos. Nenhum resultado retornado.")
            except Exception as e:
                st.error(f"Erro ao gerar lançamentos: {str(e)}")

# Instruções adicionais
with st.expander("Mais informações"):
    st.markdown("""
    ### Como funciona?
    
    Quando uma proposta é aprovada ou entra em execução, o sistema deve automaticamente gerar:
    
    1. Um lançamento de receita a receber no extrato financeiro
    2. Um lançamento nas contas a receber
    
    Ambos são categorizados como "Receita - serviços de organização".
    
    ### Quando usar esta ferramenta?
    
    Utilize esta ferramenta quando:
    
    - Uma proposta foi aprovada, mas não teve seus lançamentos financeiros gerados
    - Você precisa corrigir ou regenerar lançamentos de uma proposta específica
    - Após migrar dados de um sistema anterior
    
    ### Observações
    
    - A regeneração de lançamentos remove qualquer lançamento financeiro existente associado à proposta
    - O valor base para os lançamentos é o valor total da proposta
    - As categorias e descrições são padronizadas conforme as regras do sistema
    """)

# Botão para retornar à página principal
if st.button("Voltar para Propostas"):
    from streamlit.components.v1 import html
    html("""
    <script>
    window.parent.location.href = '/';
    </script>
    """)