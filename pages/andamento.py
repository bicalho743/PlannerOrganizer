import streamlit as st
from datetime import datetime

def show():
    st.title("📋 Andamento do Trabalho")

    # CSS para garantir alinhamento à esquerda e consistência visual
    st.markdown("""
        <style>
        .element-container {
            width: 100% !important;
        }
        /* Força alinhamento à esquerda para todos os elementos de texto */
        .stMarkdown, .stText, div[data-testid="stText"], p {
            text-align: left !important;
            width: 100% !important;
            display: block !important;
            margin-left: 0 !important;
            padding-left: 0 !important;
        }
        /* Remove margens e padding indesejados */
        .stColumn, div[data-testid="column"] {
            padding-left: 0 !important;
            margin-left: 0 !important;
        }
        /* Ajusta containers para manter alinhamento */
        .stContainer, div[class^="stContainer"] {
            margin-left: 0 !important;
            padding-left: 0 !important;
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Buscar dados da proposta selecionada
    proposta = st.session_state.get('proposta_selecionada')
    if not proposta:
        st.warning("Selecione uma proposta primeiro")
        return

    # Container principal com informações da proposta
    with st.container():
        st.markdown(f"### Proposta #{proposta['numero']} - {proposta['cliente_nome']}")

        # Informações básicas em um único container
        with st.container():
            st.markdown(f"**Cliente:** {proposta['cliente_nome']}")
            st.markdown(f"**Descrição:** {proposta.get('descricao', 'Não especificada')}")
            st.markdown(f"**Valor Base:** R$ {proposta['valor_base']:.2f}")

    # Seção de Acréscimos
    st.markdown("### Adicionar Acréscimos")

    with st.form("novo_acrescimo"):
        st.markdown("**Tipo de Acréscimo**")
        tipo = st.selectbox("", ["Organização", "Assistente", "Fornecedor"], label_visibility="collapsed")

        st.markdown("**Descrição**")
        descricao = st.text_input("", label_visibility="collapsed")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Valor (R$)**")
            valor = st.number_input("", value=0.0, format="%.2f", label_visibility="collapsed")

        st.form_submit_button("Adicionar")

    # Acréscimos Adicionados
    st.markdown("### Acréscimos Adicionados")

    acrescimos = proposta.get('acrescimos', [])
    valor_total = proposta['valor_base']
    valor_pendente = 0.0

    for acrescimo in acrescimos:
        with st.container():
            st.markdown(f"**{acrescimo['tipo']}:** R$ {acrescimo['valor']:.2f}")
            st.markdown(f"{acrescimo['descricao']}")
            valor_total += acrescimo['valor']
            if acrescimo['status'] == 'Pendente':
                valor_pendente += acrescimo['valor']

    # Resumo financeiro
    with st.container():
        st.markdown("### Resumo Financeiro")
        st.markdown(f"**Valor Base:** R$ {proposta['valor_base']:.2f}")
        st.markdown(f"**Status:** {proposta.get('status_pagamento_base', 'Pendente')}")

        for acrescimo in acrescimos:
            st.markdown(f"**{acrescimo['tipo']}:** {acrescimo['descricao']}")
            st.markdown(f"**Valor:** R$ {acrescimo['valor']:.2f}")
            st.markdown(f"**Status:** {acrescimo['status']}")

        st.markdown("---")
        st.markdown(f"**Valor Total:** R$ {valor_total:.2f}")
        st.markdown(f"**Valor Pendente:** R$ {valor_pendente:.2f}")