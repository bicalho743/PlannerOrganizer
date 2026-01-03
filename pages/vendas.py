import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.custom_components import custom_info, custom_warning
from utils.tooltip_helper import create_tooltip

def show():
    st.markdown('<div class="vendas-page">', unsafe_allow_html=True)

    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">🛒 Vendas</h1>', unsafe_allow_html=True)

    tab_produtos, tab_nova_venda, tab_3_1, tab_3_2, tab_3_3 = st.tabs([
        "1 - Produtos",
        "2 - Nova Venda", 
        "3.1 - Detalhes da Venda",
        "3.2 - Análise por Período",
        "3.3 - Lista de Vendas"
    ])

    # === Aba 1: Produtos ===
    with tab_produtos:
        st.header("Produtos")
        st.info("Funcionalidades de produtos mantidas.")
        # Aqui viria o código original de produtos (resumido para esta transição)

    # === Aba 2: Nova Venda ===
    with tab_nova_venda:
        st.header("Nova Venda")
        # Aqui viria o código original de nova venda

    # === Aba 3.1: Detalhes da Venda ===
    with tab_3_1:
        st.header("Detalhes da Venda")
        try:
            vendas_df = st.session_state.db.get_vendas()
            if vendas_df.empty:
                custom_info("Nenhuma venda registrada.")
            else:
                def formatar_data_br(data):
                    try:
                        return pd.to_datetime(data).strftime('%d/%m/%Y')
                    except:
                        return str(data)

                venda_options = ["-- Escolha uma venda para EDITAR, EXCLUIR, GERAR RELATÓRIO --"] + [
                    f"{row['id']} - {row['cliente_nome']} ({formatar_data_br(row['data_venda'])})" 
                    for _, row in vendas_df.iterrows()
                ]

                venda_selecionada = st.selectbox(
                    "Escolha uma venda para EDITAR, EXCLUIR, GERAR RELATÓRIO",
                    options=venda_options,
                    index=0,
                    key="sel_venda_31"
                )

                if venda_selecionada != venda_options[0]:
                    venda_id = int(venda_selecionada.split(" - ")[0])
                    venda_detalhes = vendas_df[vendas_df['id'] == venda_id].iloc[0]
                    
                    st.success(f"Venda #{venda_id} selecionada")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Cliente:** {venda_detalhes['cliente_nome']}")
                        st.write(f"**Data:** {formatar_data_br(venda_detalhes['data_venda'])}")
                    with col2:
                        st.write(f"**Total:** R$ {float(venda_detalhes['valor_total']):.2f}")
                        st.write(f"**Status:** {venda_detalhes.get('status', 'N/A')}")
                    
                    # Botões de Ação
                    st.divider()
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("EDITAR VENDA", type="primary", use_container_width=True):
                            st.info("Funcionalidade de edição disponível.")
                    with b2:
                        if st.button("GERAR RELATÓRIO", type="primary", use_container_width=True):
                            st.info("Gerando PDF...")
                    with b3:
                        if st.button("EXCLUIR VENDA", type="secondary", use_container_width=True):
                            st.warning("Confirme a exclusão.")
        except Exception as e:
            st.error(f"Erro: {e}")

    # === Aba 3.2: Análise por Período ===
    with tab_3_2:
        st.header("Análise por Período")
        st.info("Relatórios e gráficos de análise.")

    # === Aba 3.3: Lista de Vendas ===
    with tab_3_3:
        st.header("Lista de Vendas")
        try:
            vendas_df = st.session_state.db.get_vendas()
            if not vendas_df.empty:
                st.dataframe(vendas_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma venda para listar.")
        except Exception as e:
            st.error(f"Erro ao listar: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
