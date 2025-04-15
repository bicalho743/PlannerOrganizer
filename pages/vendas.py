import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import time

def show():
    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    st.title("🛒 Vendas")

    # Abas para diferentes funcionalidades
    tab_produtos, tab_nova_venda, tab_historico = st.tabs([
        "📦 Produtos",
        "🛍️ Nova Venda",
        "📊 Histórico de Vendas"
    ])

    # === Aba de Produtos ===
    with tab_produtos:
        st.subheader("Cadastro de Produtos")
        
        # Adicionar abas para incluir a importação
        cadastro_tab, importacao_tab = st.tabs(["Cadastro Individual", "Importação em Massa"])
        
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
            col1, col2 = st.columns([1, 2])
            
            # Formulário de cadastro de produto
            with col1:
                with st.form("cadastro_produto", clear_on_submit=True):
                    nome = st.text_input("Nome do Produto")
                    descricao = st.text_area("Descrição", height=100)
                    preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f")
                    preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.01, format="%.2f")
                    categoria = st.text_input("Categoria")
                    estoque = st.number_input("Estoque Inicial", min_value=0, step=1)
                    
                    submitted = st.form_submit_button("Cadastrar Produto")
                    
                    if submitted:
                        try:
                            # Verificar se os preços são válidos
                            if preco_venda <= 0:
                                st.error("O preço de venda deve ser maior que zero.")
                            else:
                                produto_id = st.session_state.db.add_produto(
                                    nome=nome,
                                    descricao=descricao,
                                    preco_custo=preco_custo,
                                    preco_venda=preco_venda,
                                    categoria=categoria,
                                    estoque=estoque
                                )
                                st.success(f"Produto '{nome}' cadastrado com sucesso!")
                                # Recarregar a lista de produtos
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar produto: {str(e)}")
            
            # Lista de produtos
            with col2:
                st.subheader("Produtos Cadastrados")
            
                try:
                    produtos_df = st.session_state.db.get_produtos()
                    if produtos_df.empty:
                        st.info("Nenhum produto cadastrado.")
                    else:
                        # Configurar colunas para exibição
                        produtos_df['lucro'] = produtos_df['preco_venda'] - produtos_df['preco_custo']
                        produtos_df['margem'] = (produtos_df['lucro'] / produtos_df['preco_venda'] * 100).round(2)
                        
                        # Formatar colunas monetárias
                        for col in ['preco_custo', 'preco_venda', 'lucro']:
                            produtos_df[col] = produtos_df[col].map('R$ {:.2f}'.format)
                        
                        produtos_df['margem'] = produtos_df['margem'].map('{:.2f}%'.format)
                        
                        # Colunas a exibir
                        colunas_exibir = ['id', 'nome', 'categoria', 'preco_custo', 'preco_venda', 'lucro', 'margem', 'estoque']
                        
                        # Exibir tabela com opções de edição/exclusão
                        st.dataframe(produtos_df[colunas_exibir], hide_index=True)
                        
                        # Área para editar/excluir produtos
                        with st.expander("Gerenciar Produtos"):
                            col_edit1, col_edit2 = st.columns(2)
                            
                            with col_edit1:
                                # Editar produto
                                st.subheader("Editar Produto")
                                produto_id = st.selectbox("Selecione o produto", 
                                                        options=produtos_df['id'].tolist(),
                                                        format_func=lambda x: f"{x} - {produtos_df[produtos_df['id'] == x]['nome'].iloc[0]}")
                                
                                if produto_id:
                                    produto_selecionado = produtos_df[produtos_df['id'] == produto_id].iloc[0]
                                    
                                    with st.form("editar_produto"):
                                        # Remover formatação de moeda para edição
                                        preco_custo_str = produto_selecionado['preco_custo'].replace('R$ ', '').replace(',', '.')
                                        preco_venda_str = produto_selecionado['preco_venda'].replace('R$ ', '').replace(',', '.')
                                        
                                        nome_edit = st.text_input("Nome", value=produto_selecionado['nome'])
                                        descricao_edit = st.text_area("Descrição", value=produto_selecionado.get('descricao', ''), height=100)
                                        preco_custo_edit = st.number_input("Preço de Custo", 
                                                                        value=float(preco_custo_str), 
                                                                        min_value=0.0, 
                                                                        step=0.01, 
                                                                        format="%.2f")
                                        preco_venda_edit = st.number_input("Preço de Venda", 
                                                                        value=float(preco_venda_str), 
                                                                        min_value=0.0, 
                                                                        step=0.01, 
                                                                        format="%.2f")
                                        categoria_edit = st.text_input("Categoria", value=produto_selecionado.get('categoria', ''))
                                        estoque_edit = st.number_input("Estoque", value=int(produto_selecionado['estoque']), min_value=0)
                                        
                                        submit_edit = st.form_submit_button("Atualizar Produto")
                                        
                                        if submit_edit:
                                            try:
                                                result = st.session_state.db.update_produto(
                                                    produto_id=produto_id,
                                                    nome=nome_edit,
                                                    descricao=descricao_edit,
                                                    preco_custo=preco_custo_edit,
                                                    preco_venda=preco_venda_edit,
                                                    categoria=categoria_edit,
                                                    estoque=estoque_edit
                                                )
                                                
                                                if result:
                                                    st.success("Produto atualizado com sucesso!")
                                                    st.rerun()
                                                else:
                                                    st.error("Falha ao atualizar o produto.")
                                            except Exception as e:
                                                st.error(f"Erro ao atualizar produto: {str(e)}")
                            
                            with col_edit2:
                                # Excluir produto
                                st.subheader("Excluir Produto")
                                produto_remover_id = st.selectbox("Selecione o produto para excluir", 
                                                                options=produtos_df['id'].tolist(),
                                                                format_func=lambda x: f"{x} - {produtos_df[produtos_df['id'] == x]['nome'].iloc[0]}", 
                                                                key="remover_produto")
                                
                                if st.button("Excluir Produto", type="primary", use_container_width=True):
                                    if produto_remover_id:
                                        produto_nome = produtos_df[produtos_df['id'] == produto_remover_id]['nome'].iloc[0]
                                        
                                        # Confirmação
                                        confirmacao = st.checkbox(f"Confirmo a exclusão do produto: {produto_nome}")
                                        
                                        if confirmacao and st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                                            try:
                                                result = st.session_state.db.delete_produto(produto_remover_id)
                                                if result:
                                                    st.success(f"Produto '{produto_nome}' excluído com sucesso!")
                                                    st.rerun()
                                                else:
                                                    st.error("Falha ao excluir o produto.")
                                            except Exception as e:
                                                st.error(f"Erro ao excluir produto: {str(e)}")
                except Exception as e:
                    st.error(f"Erro ao carregar produtos: {str(e)}")

    # === Aba de Nova Venda ===
    with tab_nova_venda:
        st.subheader("Registrar Nova Venda")
        
        # Carrega dados necessários
        clientes_df = st.session_state.db.get_clientes()
        produtos_df = st.session_state.db.get_produtos()
        
        if clientes_df.empty:
            st.warning("É necessário cadastrar clientes para registrar vendas.")
        elif produtos_df.empty:
            st.warning("É necessário cadastrar produtos para registrar vendas.")
        else:
            # Inicializar sessão state para produtos da venda
            if 'produtos_venda' not in st.session_state:
                st.session_state.produtos_venda = []
            
            # Selecionar cliente
            cliente_id = st.selectbox(
                "Selecione o Cliente", 
                options=clientes_df['id'].tolist(),
                format_func=lambda x: f"{x} - {clientes_df[clientes_df['id'] == x]['nome'].iloc[0]}"
            )
            
            # Adicionar produtos à venda
            with st.expander("Adicionar Produto", expanded=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # Filtrar apenas produtos com estoque
                    produtos_disponiveis = produtos_df[produtos_df['estoque'] > 0]
                    
                    if produtos_disponiveis.empty:
                        st.warning("Não há produtos em estoque disponíveis para venda.")
                        produto_id = None
                    else:
                        produto_id = st.selectbox(
                            "Selecione o Produto",
                            options=produtos_disponiveis['id'].tolist(),
                            format_func=lambda x: f"{x} - {produtos_disponiveis[produtos_disponiveis['id'] == x]['nome'].iloc[0]}"
                        )
                
                with col2:
                    if produto_id:
                        produto = produtos_df[produtos_df['id'] == produto_id].iloc[0]
                        max_quantidade = int(produto['estoque'])
                        quantidade = st.number_input("Quantidade", min_value=1, max_value=max_quantidade, value=1)
                    else:
                        quantidade = st.number_input("Quantidade", min_value=1, value=1, disabled=True)
                
                with col3:
                    if produto_id:
                        preco_venda_str = produto['preco_venda'].replace('R$ ', '').replace(',', '.') if isinstance(produto['preco_venda'], str) else produto['preco_venda']
                        preco_venda = float(preco_venda_str)
                        preco_unitario = st.number_input("Preço Unitário (R$)", min_value=0.01, value=preco_venda, format="%.2f")
                    else:
                        preco_unitario = st.number_input("Preço Unitário (R$)", min_value=0.01, value=0.01, format="%.2f", disabled=True)
            
                if produto_id and st.button("Adicionar ao Carrinho", use_container_width=True):
                    produto = produtos_df[produtos_df['id'] == produto_id].iloc[0]
                    
                    # Adicionar ao carrinho
                    st.session_state.produtos_venda.append({
                        'produto_id': produto_id,
                        'nome': produto['nome'],
                        'quantidade': quantidade,
                        'preco_unitario': preco_unitario,
                        'subtotal': quantidade * preco_unitario
                    })
                    
                    st.success(f"Produto '{produto['nome']}' adicionado ao carrinho!")
                    st.rerun()
            
            # Exibir produtos no carrinho
            if st.session_state.produtos_venda:
                st.subheader("Produtos no Carrinho")
                
                carrinho_df = pd.DataFrame(st.session_state.produtos_venda)
                valor_total = carrinho_df['subtotal'].sum()
                
                # Formatar para exibição
                carrinho_df['preco_unitario'] = carrinho_df['preco_unitario'].map('R$ {:.2f}'.format)
                carrinho_df['subtotal'] = carrinho_df['subtotal'].map('R$ {:.2f}'.format)
                
                st.dataframe(carrinho_df[['nome', 'quantidade', 'preco_unitario', 'subtotal']], hide_index=True)
                
                # Totais e finalização
                st.info(f"Valor Total da Venda: **R$ {valor_total:.2f}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    forma_pagamento = st.selectbox(
                        "Forma de Pagamento",
                        options=["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Transferência", "Outro"]
                    )
                
                with col2:
                    observacoes = st.text_area("Observações", height=100)
                
                # Botões de ação
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Limpar Carrinho", use_container_width=True):
                        st.session_state.produtos_venda = []
                        st.rerun()
                
                with col2:
                    if st.button("Finalizar Venda", type="primary", use_container_width=True):
                        try:
                            # Preparar itens para API
                            itens = []
                            for item in st.session_state.produtos_venda:
                                itens.append({
                                    'produto_id': item['produto_id'],
                                    'quantidade': item['quantidade'],
                                    'preco_unitario': item['preco_unitario'] if isinstance(item['preco_unitario'], float) else float(item['preco_unitario'].replace('R$ ', '').replace(',', '.'))
                                })
                            
                            # Registrar venda
                            venda_id = st.session_state.db.add_venda(
                                cliente_id=cliente_id,
                                itens=itens,
                                forma_pagamento=forma_pagamento,
                                observacoes=observacoes
                            )
                            
                            # Limpar carrinho e mostrar sucesso
                            st.session_state.produtos_venda = []
                            st.success(f"Venda registrada com sucesso! Código da venda: {venda_id}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar venda: {str(e)}")
            else:
                st.info("Nenhum produto adicionado ao carrinho.")

    # === Aba de Histórico de Vendas ===
    with tab_historico:
        st.subheader("Histórico de Vendas")
        
        try:
            vendas_df = st.session_state.db.get_vendas()
            
            if vendas_df.empty:
                st.info("Nenhuma venda registrada.")
            else:
                # Formatar dados para exibição
                vendas_df['valor_total'] = vendas_df['valor_total'].map('R$ {:.2f}'.format)
                
                # Exibir tabela de vendas
                st.dataframe(vendas_df, hide_index=True)
                
                # Detalhes da venda selecionada
                st.subheader("Detalhes da Venda")
                venda_id = st.selectbox(
                    "Selecione uma venda para ver detalhes",
                    options=vendas_df['id'].tolist(),
                    format_func=lambda x: f"Venda {x} - {vendas_df[vendas_df['id'] == x]['cliente_nome'].iloc[0]} ({vendas_df[vendas_df['id'] == x]['data_venda'].iloc[0]})"
                )
                
                if venda_id:
                    venda = vendas_df[vendas_df['id'] == venda_id].iloc[0]
                    
                    # Informações da venda
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Cliente:** {venda['cliente_nome']}")
                        st.write(f"**Data:** {venda['data_venda']}")
                        st.write(f"**Status:** {venda['status']}")
                    
                    with col2:
                        st.write(f"**Valor Total:** {venda['valor_total']}")
                        st.write(f"**Forma de Pagamento:** {venda['forma_pagamento']}")
                        st.write(f"**Observações:** {venda['observacoes'] or '-'}")
                    
                    # Exibir itens da venda
                    itens_df = st.session_state.db.get_itens_venda(venda_id)
                    
                    if not itens_df.empty:
                        st.subheader("Itens da Venda")
                        
                        # Formatar valores
                        itens_df['preco_unitario'] = itens_df['preco_unitario'].map('R$ {:.2f}'.format)
                        itens_df['subtotal'] = itens_df['subtotal'].map('R$ {:.2f}'.format)
                        
                        st.dataframe(itens_df[['produto_nome', 'quantidade', 'preco_unitario', 'subtotal']], hide_index=True)
                    
                    # Opções para cancelar ou excluir venda
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Opção para cancelar venda (muda o status)
                        if venda['status'] != 'Cancelada':
                            if st.button("Cancelar Venda", type="primary", key="btn_cancelar_venda"):
                                with st.form(key="form_cancelar_venda"):
                                    st.warning("Confirmar cancelamento da venda? Esta ação não pode ser desfeita.")
                                    confirmar_cancelamento = st.form_submit_button("Confirmar Cancelamento", type="primary")
                                
                                    if confirmar_cancelamento:
                                        try:
                                            result = st.session_state.db.cancelar_venda(venda_id)
                                            if result:
                                                st.success("Venda cancelada com sucesso!")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("Falha ao cancelar a venda.")
                                        except Exception as e:
                                            st.error(f"Erro ao cancelar venda: {str(e)}")
                    
                    with col2:
                        # Opção para excluir completamente a venda
                        if st.button("Excluir Venda", type="primary", key="btn_excluir_venda"):
                            with st.form(key="form_excluir_venda"):
                                st.warning("⚠️ ATENÇÃO! Esta ação irá EXCLUIR PERMANENTEMENTE a venda e todos seus itens do sistema.")
                                confirmar_exclusao = st.form_submit_button("Confirmar Exclusão", type="primary")
                                
                                if confirmar_exclusao:
                                    try:
                                        # Função nova para excluir venda
                                        result = st.session_state.db.excluir_venda(venda_id)
                                        if result:
                                            st.success("Venda excluída com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("Falha ao excluir a venda.")
                                    except Exception as e:
                                        st.error(f"Erro ao excluir venda: {str(e)}")
        except Exception as e:
            st.error(f"Erro ao carregar vendas: {str(e)}")