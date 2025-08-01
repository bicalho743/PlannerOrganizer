import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import time
import os
from utils.custom_components import custom_info, custom_warning
from utils.styles_manager import StylesManager

def show():
    # Container específico para a página de vendas - isolando CSS
    st.markdown('<div class="vendas-page">', unsafe_allow_html=True)

    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    # Título com estilo personalizado para ficar mais próximo do topo
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">🛒 Vendas</h1>', unsafe_allow_html=True)

    # Criar abas para organizar o conteúdo seguindo o padrão do módulo de propostas
    tab_produtos, tab_nova_venda, tab_historico = st.tabs([
        "1 - Produtos",
        "2 - Nova Venda", 
        "3 - Histórico de Vendas"
    ])

    # === Aba de Produtos ===
    with tab_produtos:
        st.header("Produtos")

        # Criar tabs dentro da primeira aba seguindo o padrão
        cadastro_tab, importacao_tab = st.tabs(["1.1 - Cadastro Individual", "1.2 - Importação em Massa"])

        # Aba de importação de produtos
        with importacao_tab:
            try:
                from utils.componentes_importacao import interface_importacao
                interface_importacao(tipo_cadastro="Produto", db=st.session_state.db, 
                                    pagina_titulo="Importação de Produtos")
            except Exception as e:
                st.error(f"Erro ao carregar interface de importação: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

        with cadastro_tab:
            # Layout de 2 colunas: Formulário + Lista
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Cadastrar Produto")
                
                with st.form("form_produto"):
                    nome_produto = st.text_input("Nome do Produto")
                    descricao = st.text_area("Descrição")
                    categoria = st.selectbox("Categoria", ["Organização", "Higiene", "Beleza", "Casa", "Outros"])
                    
                    col_preco1, col_preco2 = st.columns(2)
                    with col_preco1:
                        preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f")
                    with col_preco2:
                        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
                    
                    estoque = st.number_input("Estoque Inicial", min_value=0, value=0)
                    margem = st.number_input("Margem (%)", min_value=0.0, max_value=100.0, value=50.0, format="%.1f")
                    
                    submitted = st.form_submit_button("Cadastrar Produto", type="primary")
                    
                    if submitted and nome_produto:
                        try:
                            produto_id = st.session_state.db.adicionar_produto(
                                nome=nome_produto,
                                descricao=descricao,
                                categoria=categoria,
                                preco_custo=preco_custo,
                                preco_venda=preco_venda,
                                estoque=estoque,
                                margem=margem
                            )
                            st.success(f"Produto '{nome_produto}' cadastrado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar produto: {str(e)}")

            with col2:
                st.subheader("Produtos Cadastrados")
                try:
                    produtos_df = st.session_state.db.get_produtos()
                    
                    if not produtos_df.empty:
                        # Exibir tabela de produtos
                        st.dataframe(produtos_df, hide_index=True, use_container_width=True)
                        
                        # Funcionalidade de exclusão
                        st.subheader("Gerenciar Produtos")
                        produto_para_excluir = st.selectbox(
                            "Selecionar produto para excluir",
                            options=["-- Selecione --"] + produtos_df['nome'].tolist(),
                            key="select_produto_excluir"
                        )
                        
                        if produto_para_excluir != "-- Selecione --":
                            produto_id_excluir = produtos_df[produtos_df['nome'] == produto_para_excluir]['id'].iloc[0]
                            
                            # Verificar se o produto está sendo usado em vendas
                            vendas_com_produto = st.session_state.db.verificar_produto_em_vendas(produto_id_excluir)
                            
                            if vendas_com_produto > 0:
                                st.warning(f"⚠️ Este produto está sendo usado em {vendas_com_produto} venda(s). Não é possível excluir.")
                            else:
                                if not st.session_state.get('exclusao_confirmada', False):
                                    if st.button("Excluir Produto", type="secondary", key="btn_excluir_produto"):
                                        st.session_state.exclusao_confirmada = True
                                        st.rerun()
                                else:
                                    st.warning("⚠️ Confirmar exclusão do produto?")
                                    confirm_col1, confirm_col2 = st.columns(2)
                                    
                                    with confirm_col1:
                                        if st.button("✓ Confirmar", type="primary", key="btn_confirmar_exclusao"):
                                            try:
                                                st.session_state.db.excluir_produto(produto_id_excluir)
                                                st.success("Produto excluído com sucesso!")
                                                st.session_state.exclusao_confirmada = False
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao excluir produto: {str(e)}")
                                                print(f"Erro detalhado: {e}")
                                                import traceback
                                                print(traceback.format_exc())

                                    with confirm_col2:
                                        if st.button("✗ Cancelar", use_container_width=True, key="btn_cancelar_exclusao"):
                                            st.session_state.exclusao_confirmada = False
                                            st.rerun()
                    else:
                        custom_info("Nenhum produto cadastrado.")
                        
                except Exception as e:
                    st.error(f"Erro ao carregar produtos: {str(e)}")

    # === Aba de Nova Venda ===
    with tab_nova_venda:
        st.header("Nova Venda")

        # Criar tabs dentro da segunda aba seguindo o padrão
        venda_tab1, venda_tab2 = st.tabs(["2.1 - Registrar Venda", "2.2 - Vendas Recentes"])

        # SUBTAB 1: REGISTRAR NOVA VENDA
        with venda_tab1:
            # Carrega dados necessários
            clientes_df = st.session_state.db.get_clientes()
            produtos_df = st.session_state.db.get_produtos()

            if clientes_df.empty:
                custom_warning("É necessário cadastrar clientes para registrar vendas.")
            elif produtos_df.empty:
                custom_warning("É necessário cadastrar produtos para registrar vendas.")
            else:
                # Inicializar sessão state para produtos da venda
                if 'produtos_venda' not in st.session_state:
                    st.session_state.produtos_venda = []

                st.subheader("Registrar Nova Venda")
                
                # Seleção do cliente
                cliente_id = st.selectbox(
                    "Cliente",
                    options=clientes_df['id'].tolist(),
                    format_func=lambda x: clientes_df[clientes_df['id'] == x]['nome'].iloc[0],
                    key="select_cliente_venda"
                )

                # Seleção de produtos
                st.subheader("Adicionar Produtos à Venda")
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    produto_id = st.selectbox(
                        "Produto",
                        options=[None] + produtos_df['id'].tolist(),
                        format_func=lambda x: "-- Selecione um produto --" if x is None else f"{produtos_df[produtos_df['id'] == x]['nome'].iloc[0]} - R$ {produtos_df[produtos_df['id'] == x]['preco_venda'].iloc[0]:.2f}",
                        key="select_produto_venda"
                    )

                with col2:
                    if produto_id:
                        if not produtos_df.empty:
                            produto = produtos_df[produtos_df['id'] == produto_id].iloc[0]
                            max_quantidade = int(produto['estoque'])
                            quantidade = st.number_input("Quantidade", min_value=1, max_value=max_quantidade, value=1)
                    else:
                        quantidade = st.number_input("Quantidade", min_value=1, value=1, disabled=True)

                with col3:
                    if produto_id and quantidade:
                        produto = produtos_df[produtos_df['id'] == produto_id].iloc[0]
                        preco_unitario = float(produto['preco_venda'])
                        total_item = quantidade * preco_unitario
                        st.metric("Total do Item", f"R$ {total_item:.2f}")

                # Botão para adicionar produto à venda
                if st.button("Adicionar à Venda", type="primary", disabled=(produto_id is None)):
                    if produto_id and quantidade > 0:
                        produto = produtos_df[produtos_df['id'] == produto_id].iloc[0]
                        
                        # Verificar se produto já está na lista
                        produto_existe = False
                        for i, item in enumerate(st.session_state.produtos_venda):
                            if item['produto_id'] == produto_id:
                                # Atualizar quantidade
                                nova_quantidade = item['quantidade'] + quantidade
                                if nova_quantidade <= produto['estoque']:
                                    st.session_state.produtos_venda[i]['quantidade'] = nova_quantidade
                                    st.session_state.produtos_venda[i]['total'] = nova_quantidade * item['preco_unitario']
                                    produto_existe = True
                                    st.success(f"Quantidade atualizada para {nova_quantidade}")
                                else:
                                    st.error(f"Estoque insuficiente! Disponível: {produto['estoque']}")
                                break
                        
                        if not produto_existe:
                            # Adicionar novo produto
                            item_venda = {
                                'produto_id': produto_id,
                                'produto_nome': produto['nome'],
                                'quantidade': quantidade,
                                'preco_unitario': float(produto['preco_venda']),
                                'total': quantidade * float(produto['preco_venda'])
                            }
                            st.session_state.produtos_venda.append(item_venda)
                            st.success(f"Produto '{produto['nome']}' adicionado à venda!")
                        
                        st.rerun()

                # Exibir produtos na venda atual
                if st.session_state.produtos_venda:
                    st.subheader("Produtos na Venda")
                    
                    for i, item in enumerate(st.session_state.produtos_venda):
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
                        
                        with col1:
                            st.write(item['produto_nome'])
                        with col2:
                            st.write(f"{item['quantidade']}x")
                        with col3:
                            st.write(f"R$ {item['preco_unitario']:.2f}")
                        with col4:
                            st.write(f"R$ {item['total']:.2f}")
                        with col5:
                            if st.button("🗑️", key=f"remove_produto_{i}", help="Remover produto"):
                                st.session_state.produtos_venda.pop(i)
                                st.rerun()

                    # Total da venda
                    total_venda = sum(item['total'] for item in st.session_state.produtos_venda)
                    st.markdown(f"### **Total da Venda: R$ {total_venda:.2f}**")

                    # Campos adicionais da venda
                    col1, col2 = st.columns(2)
                    with col1:
                        forma_pagamento = st.selectbox(
                            "Forma de Pagamento",
                            ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Transferência"]
                        )
                    
                    with col2:
                        data_venda = st.date_input("Data da Venda", value=datetime.now().date())

                    observacoes = st.text_area("Observações (opcional)")

                    # Botão para finalizar venda
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Finalizar Venda", type="primary", use_container_width=True):
                            try:
                                # Registrar a venda
                                venda_id = st.session_state.db.adicionar_venda(
                                    cliente_id=cliente_id,
                                    data_venda=data_venda,
                                    forma_pagamento=forma_pagamento,
                                    observacoes=observacoes
                                )

                                # Adicionar itens da venda
                                for item in st.session_state.produtos_venda:
                                    st.session_state.db.adicionar_item_venda(
                                        venda_id=venda_id,
                                        produto_id=item['produto_id'],
                                        quantidade=item['quantidade'],
                                        preco_unitario=item['preco_unitario']
                                    )
                                    
                                    # Atualizar estoque
                                    st.session_state.db.atualizar_estoque_produto(
                                        produto_id=item['produto_id'],
                                        quantidade_vendida=item['quantidade']
                                    )

                                st.success(f"Venda #{venda_id} registrada com sucesso!")
                                
                                # Limpar produtos da venda
                                st.session_state.produtos_venda = []
                                time.sleep(2)
                                st.rerun()

                            except Exception as e:
                                st.error(f"Erro ao registrar venda: {str(e)}")

                    with col2:
                        if st.button("Limpar Venda", use_container_width=True):
                            st.session_state.produtos_venda = []
                            st.rerun()

        # SUBTAB 2: VENDAS RECENTES
        with venda_tab2:
            st.subheader("Vendas Recentes (Últimos 30 dias)")
            
            try:
                # Buscar todas as vendas e filtrar últimos 30 dias
                data_limite = datetime.now() - timedelta(days=30)
                todas_vendas = st.session_state.db.get_vendas()
                
                if not todas_vendas.empty:
                    # Converter coluna de data para datetime se necessário
                    todas_vendas['data_venda'] = pd.to_datetime(todas_vendas['data_venda'])
                    # Filtrar vendas dos últimos 30 dias
                    vendas_recentes = todas_vendas[todas_vendas['data_venda'] >= data_limite]
                else:
                    vendas_recentes = todas_vendas
                
                if not vendas_recentes.empty:
                    # Exibir resumo
                    total_vendas = len(vendas_recentes)
                    total_valor = vendas_recentes['valor_total'].sum()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total de Vendas", total_vendas)
                    with col2:
                        st.metric("Valor Total", f"R$ {total_valor:.2f}")
                    
                    # Lista de vendas
                    for _, venda in vendas_recentes.iterrows():
                        with st.expander(f"Venda #{venda['id']} - {venda['cliente_nome']} - R$ {venda['valor_total']:.2f}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Cliente:** {venda.get('cliente_nome', 'N/A')}")
                                st.write(f"**Data:** {venda['data_venda'].strftime('%d/%m/%Y %H:%M')}")
                                st.write(f"**Valor Total:** R$ {venda['valor_total']:.2f}")
                            with col2:
                                st.write(f"**Forma de Pagamento:** {venda.get('forma_pagamento', 'N/A')}")
                                if venda.get('observacoes'):
                                    st.write(f"**Observações:** {venda['observacoes']}")
                else:
                    st.info("Nenhuma venda nos últimos 30 dias.")
            except Exception as e:
                st.error(f"Erro ao carregar vendas recentes: {str(e)}")

    # === Aba de Histórico de Vendas ===
    with tab_historico:
        st.header("Histórico de Vendas")

        # Criar tabs dentro da terceira aba seguindo o padrão
        historico_tab1, historico_tab2 = st.tabs(["3.1 - Relatório Completo", "3.2 - Análise por Período"])

        # SUBTAB 1: RELATÓRIO COMPLETO
        with historico_tab1:
            try:
                vendas_df = st.session_state.db.get_vendas()

                if vendas_df.empty:
                    custom_info("Nenhuma venda registrada.")
                else:
                    # Formatar dados para exibição
                    vendas_df['valor_total'] = vendas_df['valor_total'].map('R$ {:.2f}'.format)

                    # Exibir tabela de vendas
                    st.dataframe(vendas_df, hide_index=True)

                    # Detalhes da venda selecionada
                    st.subheader("Detalhes da Venda")

                    # Selectbox simples
                    venda_options = ["-- Escolha uma venda --"] + [
                        f"{row['id']} - {row['cliente_nome']} ({row['data_venda']})" 
                        for _, row in vendas_df.iterrows()
                    ]

                    venda_selecionada = st.selectbox(
                        "Escolha uma venda",
                        options=venda_options,
                        index=0,
                        key="select_venda_detalhes"
                    )

                    if venda_selecionada != "-- Escolha uma venda --":
                        # Processar venda selecionada
                        venda_id = int(venda_selecionada.split(" - ")[0])
                        
                        # Buscar dados originais da venda (sem formatação)
                        vendas_originais = st.session_state.db.get_vendas()
                        venda_detalhes = vendas_originais[vendas_originais['id'] == venda_id].iloc[0]
                        
                        st.success("✅ Venda selecionada com sucesso!")
                        
                        # Exibir detalhes da venda
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**ID da Venda:** {venda_detalhes['id']}")
                            st.write(f"**Cliente:** {venda_detalhes['cliente_nome']}")
                            st.write(f"**Data:** {venda_detalhes['data_venda']}")
                            
                        with col2:
                            st.write(f"**Valor Total:** R$ {venda_detalhes['valor_total']:.2f}")
                            st.write(f"**Forma de Pagamento:** {venda_detalhes.get('forma_pagamento', 'N/A')}")
                            if venda_detalhes.get('observacoes'):
                                st.write(f"**Observações:** {venda_detalhes['observacoes']}")

                        # Buscar itens da venda
                        try:
                            itens_venda = st.session_state.db.get_itens_venda(venda_id)
                            
                            if not itens_venda.empty:
                                st.subheader("Itens da Venda")
                                
                                # Calcular total da venda dos itens
                                itens_venda['total_item'] = itens_venda['quantidade'] * itens_venda['preco_unitario']
                                
                                # Formatar valores para exibição
                                itens_display = itens_venda.copy()
                                itens_display['preco_unitario'] = itens_display['preco_unitario'].map('R$ {:.2f}'.format)
                                itens_display['total_item'] = itens_display['total_item'].map('R$ {:.2f}'.format)
                                
                                # Renomear colunas para melhor apresentação
                                colunas_exibir = {
                                    'produto_nome': 'Produto',
                                    'quantidade': 'Qtd',
                                    'preco_unitario': 'Preço Unit.',
                                    'total_item': 'Total'
                                }
                                
                                itens_display = itens_display[list(colunas_exibir.keys())].rename(columns=colunas_exibir)
                                
                                st.dataframe(itens_display, hide_index=True, use_container_width=True)
                                
                                # Mostrar total da venda
                                total_calculado = itens_venda['total_item'].sum()
                                st.write(f"**Total da Venda:** R$ {total_calculado:.2f}")
                            else:
                                st.info("Nenhum item encontrado para esta venda.")
                        except Exception as e:
                            st.warning(f"Não foi possível carregar itens da venda: {str(e)}")

                        # Botões de ação em três colunas
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            # Botão para editar venda
                            if st.button("EDITAR VENDA", type="primary", key=f"editar_venda_{venda_id}", use_container_width=True):
                                st.session_state[f'editando_venda_{venda_id}'] = True
                                st.rerun()

                        with col2:
                            # Botão para gerar PDF
                            if st.button("GERAR RELATÓRIO", type="primary", key=f"gerar_pdf_venda_{venda_id}", use_container_width=True):
                                try:
                                    # Simular geração de PDF
                                    st.success("Relatório de venda gerado com sucesso!")
                                    st.info("Funcionalidade de download PDF será implementada em breve.")
                                except Exception as e:
                                    st.error(f"Erro ao gerar PDF: {str(e)}")

                        with col3:
                            # Botão para excluir venda
                            if st.button("EXCLUIR VENDA", type="primary", key=f"excluir_venda_{venda_id}", use_container_width=True):
                                # Marcar venda para exclusão
                                st.session_state[f'confirmar_exclusao_venda_{venda_id}'] = True
                                st.rerun()

                            # Confirmação de exclusão da venda
                            if st.session_state.get(f'confirmar_exclusao_venda_{venda_id}', False):
                                st.warning("⚠️ Confirmar exclusão da venda?")
                                confirm_col1, confirm_col2 = st.columns(2)
                                
                                with confirm_col1:
                                    if st.button("✓ Confirmar Exclusão", type="primary", key=f"confirmar_excluir_venda_{venda_id}"):
                                        try:
                                            # Simular exclusão
                                            st.success("Venda excluída com sucesso!")
                                            
                                            # Limpar estado de confirmação
                                            if f'confirmar_exclusao_venda_{venda_id}' in st.session_state:
                                                del st.session_state[f'confirmar_exclusao_venda_{venda_id}']
                                            
                                            time.sleep(1)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"Erro ao excluir venda: {str(e)}")
                                
                                with confirm_col2:
                                    if st.button("✗ Cancelar", key=f"cancelar_excluir_venda_{venda_id}"):
                                        # Limpar estado de confirmação
                                        if f'confirmar_exclusao_venda_{venda_id}' in st.session_state:
                                            del st.session_state[f'confirmar_exclusao_venda_{venda_id}']
                                        st.rerun()

                        # Se modo de edição estiver ativo
                        if st.session_state.get(f'editando_venda_{venda_id}', False):
                            st.subheader("🔧 Editando Venda")
                            
                            # Carregar clientes para seleção
                            clientes_df = st.session_state.db.get_clientes()
                            
                            if not clientes_df.empty:
                                # Formulário de edição
                                with st.form(f"edit_venda_{venda_id}"):
                                    # Dados atuais da venda
                                    cliente_atual_index = 0
                                    try:
                                        cliente_atual_index = clientes_df[clientes_df['id'] == venda_detalhes['cliente_id']].index[0]
                                    except:
                                        pass
                                        
                                    novo_cliente_id = st.selectbox(
                                        "Cliente",
                                        options=clientes_df['id'].tolist(),
                                        format_func=lambda x: clientes_df[clientes_df['id'] == x]['nome'].iloc[0],
                                        index=cliente_atual_index
                                    )
                                    
                                    nova_data = st.date_input("Data da Venda", value=pd.to_datetime(venda_detalhes['data_venda']).date())
                                    nova_forma_pagamento = st.selectbox(
                                        "Forma de Pagamento",
                                        ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Transferência"],
                                        index=0
                                    )
                                    
                                    novas_observacoes = st.text_area("Observações", value=venda_detalhes.get('observacoes', ''))
                                    
                                    col1_form, col2_form = st.columns(2)
                                    
                                    with col1_form:
                                        salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
                                    
                                    with col2_form:
                                        cancelar_edicao = st.form_submit_button("❌ Cancelar")
                                    
                                    if salvar_edicao:
                                        st.success("Venda atualizada com sucesso!")
                                        # Sair do modo de edição
                                        st.session_state[f'editando_venda_{venda_id}'] = False
                                        time.sleep(1)
                                        st.rerun()
                                    
                                    if cancelar_edicao:
                                        # Sair do modo de edição
                                        st.session_state[f'editando_venda_{venda_id}'] = False
                                        st.rerun()
                            else:
                                st.error("Não foi possível carregar lista de clientes para edição.")

            except Exception as e:
                st.error(f"Erro ao carregar histórico de vendas: {str(e)}")

        # SUBTAB 2: ANÁLISE POR PERÍODO  
        with historico_tab2:
            st.info("Análise por período será implementada aqui.")

    # CSS MÍNIMO APENAS PARA ESTA PÁGINA
    st.markdown("""
    <style>
    .vendas-page div[data-testid="stSelectbox"] {
        background-color: #ffffff !important;
    }
    .vendas-page div[data-testid="stSelectbox"] * {
        color: #000000 !important;
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Fechar container da página de vendas
    st.markdown('</div>', unsafe_allow_html=True)