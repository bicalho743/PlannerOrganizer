import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def mostrar_integracao_modulos():
    st.subheader("🔄 Integração entre Módulos")
    
    st.write("""
    Esta seção permite realizar integrações entre os módulos de Propostas, Financeiro e Vendas.
    Você pode gerar transações financeiras e registros de vendas a partir de propostas aprovadas.
    """)
    
    # Carregar propostas disponíveis
    propostas = st.session_state.db.get_propostas()
    
    if propostas.empty:
        st.warning("🔎 Não há propostas cadastradas para realizar a integração.")
        return
    
    # Juntar propostas com informações dos clientes para exibição
    clientes = st.session_state.db.get_clientes()
    propostas = propostas.merge(
        clientes[['id', 'nome']],
        left_on='cliente_id',
        right_on='id',
        how='left',
        suffixes=('', '_cliente')
    )
    
    # Criar duas colunas para exibir as opções
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Gerar Transações Financeiras")
        st.write("Crie transações financeiras a partir de uma proposta.")
        
        # Seleção de proposta
        proposta_ids = propostas[['id', 'numero', 'nome', 'descricao', 'valor']].copy()
        proposta_ids['display'] = proposta_ids.apply(
            lambda x: f"#{x['numero']} - {x['nome']} - R$ {float(x['valor']):.2f}", axis=1
        )
        proposta_selecionada = st.selectbox(
            "Selecione a proposta:",
            proposta_ids['display'].tolist(),
            key="proposta_transacao"
        )
        
        # Obter o ID da proposta selecionada
        proposta_idx = proposta_ids[proposta_ids['display'] == proposta_selecionada].index[0]
        proposta_id = proposta_ids.iloc[proposta_idx]['id']
        
        # Botão para gerar transações
        if st.button("💰 Gerar Transações Financeiras", type="primary"):
            with st.spinner("Processando..."):
                try:
                    resultado = st.session_state.db.gerar_transacoes_proposta(proposta_id)
                    
                    if resultado.get("status") == "já existem transações":
                        st.info(f"⚠️ Já existem {resultado.get('count', 0)} transações para esta proposta.")
                    elif resultado.get("status") == "sucesso":
                        st.success(f"""
                        ✅ Transações geradas com sucesso!
                        - Receita ID: {resultado.get('receita_id')}
                        - Despesas geradas: {resultado.get('total_despesas')}
                        """)
                    else:
                        st.warning("⚠️ Não foi possível gerar as transações. Verifique os dados da proposta.")
                        
                except Exception as e:
                    st.error(f"Erro ao gerar transações: {str(e)}")
    
    with col2:
        st.markdown("### Criar Venda a partir de Proposta")
        st.write("Transforme uma proposta em uma venda no módulo de Vendas.")
        
        # Seleção de proposta
        proposta_selecionada_venda = st.selectbox(
            "Selecione a proposta:",
            proposta_ids['display'].tolist(),
            key="proposta_venda"
        )
        
        # Obter o ID da proposta selecionada
        proposta_idx_venda = proposta_ids[proposta_ids['display'] == proposta_selecionada_venda].index[0]
        proposta_id_venda = proposta_ids.iloc[proposta_idx_venda]['id']
        
        # Opção de forma de pagamento
        forma_pagamento = st.selectbox(
            "Forma de pagamento:",
            ["À vista", "Cartão de Crédito", "Boleto", "Transferência", "PIX"]
        )
        
        # Botão para criar venda
        if st.button("🛒 Criar Venda", type="primary"):
            with st.spinner("Processando..."):
                try:
                    resultado = st.session_state.db.criar_venda_de_proposta(
                        proposta_id=proposta_id_venda,
                        forma_pagamento=forma_pagamento
                    )
                    
                    if resultado.get("status") == "venda_existente":
                        st.info(f"⚠️ Já existe uma venda (ID: {resultado.get('venda_id')}) para esta proposta.")
                    elif resultado.get("status") == "sucesso":
                        st.success(f"""
                        ✅ Venda criada com sucesso!
                        - Venda ID: {resultado.get('venda_id')}
                        - Valor: R$ {float(resultado.get('valor', 0)):.2f}
                        - Tipo: {resultado.get('tipo', '')}
                        - {resultado.get('message', '')}
                        """)
                    else:
                        st.warning("⚠️ Não foi possível criar a venda. Verifique os dados da proposta.")
                        
                except Exception as e:
                    st.error(f"Erro ao criar venda: {str(e)}")

def show():
    # Verificar se existe um link para a página de propostas
    if hasattr(st.session_state, 'voltar_para_propostas') and st.session_state.voltar_para_propostas:
        if st.button("← Voltar para Propostas", key="btn_voltar"):
            st.session_state.voltar_para_propostas = False
            st.experimental_rerun()
    
    st.title("🔄 Integração entre Módulos")
    
    # Conteúdo principal
    mostrar_integracao_modulos()