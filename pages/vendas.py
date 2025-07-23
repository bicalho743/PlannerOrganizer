import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import time
import os
from utils.custom_components import custom_info, custom_warning

def show():
    # Verificar se o db está na sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return

    # CSS removido - usando componentes globais custom_info() agora

    # Removido função local - usando componente global custom_info

    # Título com estilo personalizado para ficar mais próximo do topo
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">🛒 Vendas</h1>', unsafe_allow_html=True)

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
                        custom_info("Nenhum produto cadastrado.")
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

                        # CSS para colorir a barra do expander com cor sólida idêntica aos botões primary
                        st.markdown("""
                        <style>
                        /* Estilizar o expander "Gerenciar Produtos" */
                        div[data-testid="stExpander"] details summary {
                            background: #3a75c4 !important;
                            background-color: #3a75c4 !important;
                            background-image: none !important;
                            color: white !important;
                            border-radius: 0.375rem !important;
                            padding: 0.375rem 0.75rem !important;
                            font-weight: 400 !important;
                            border: 1px solid #3a75c4 !important;
                            font-size: 1rem !important;
                            line-height: 1.5 !important;
                        }

                        div[data-testid="stExpander"] details summary:hover {
                            background: #0056b3 !important;
                            background-color: #0056b3 !important;
                            background-image: none !important;
                            border-color: #0056b3 !important;
                            color: white !important;
                        }

                        /* Ícone do expander */
                        div[data-testid="stExpander"] details summary svg {
                            color: white !important;
                        }

                        /* Corrigir visibilidade do texto nos selectbox */
                        .stSelectbox > div > div > div {
                            color: #1e1e1e !important;
                            background-color: #f8f9fa !important;
                        }

                        .stSelectbox select {
                            color: #1e1e1e !important;
                            background-color: #f8f9fa !important;
                        }

                        /* Dropdown options */
                        .stSelectbox [data-baseweb="select"] > div {
                            color: #1e1e1e !important;
                            background-color: #ffffff !important;
                        }

                        /* Text in selectbox */
                        .stSelectbox [data-testid="stSelectbox"] > div > div {
                            color: #1e1e1e !important;
                        }

                        /* Input fields visibility */
                        .stTextInput input, .stTextArea textarea, .stNumberInput input {
                            color: #1e1e1e !important;
                            background-color: #f8f9fa !important;
                        }

                        /* Labels visibility */
                        label, .stSelectbox > label, .stTextInput > label, .stTextArea > label, .stNumberInput > label {
                            color: #1e1e1e !important;
                            font-weight: 600 !important;
                        }

                        /* Botões com texto branco - CSS mais específico */
                        div[data-testid="column"] button[data-testid="baseButton-primary"],
                        div[data-testid="column"] button[data-testid="baseButton-secondary"],
                        div.stButton > button,
                        button[kind="primary"],
                        button[kind="secondary"],
                        .stButton button,
                        .stForm button {
                            color: #ffffff !important;
                            background-color: #3a75c4 !important;
                            border: 1px solid #3a75c4 !important;
                            font-weight: 600 !important;
                        }

                        div[data-testid="column"] button[data-testid="baseButton-primary"]:hover,
                        div[data-testid="column"] button[data-testid="baseButton-secondary"]:hover,
                        div.stButton > button:hover,
                        button[kind="primary"]:hover,
                        button[kind="secondary"]:hover,
                        .stButton button:hover,
                        .stForm button:hover {
                            color: #ffffff !important;
                            background-color: #2B547E !important;
                            border: 1px solid #2B547E !important;
                        }

                        /* Forçar cor branca em todos os botões */
                        button {
                            color: #ffffff !important;
                        }

                        /* Tabs também */
                        .stTabs button {
                            color: #ffffff !important;
                            background-color: #3a75c4 !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)

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

                                        submit_edit = st.form_submit_button("Atualizar Produto", type="primary")

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

                                # Variável de estado para controlar o fluxo de exclusão
                                if 'exclusao_confirmada' not in st.session_state:
                                    st.session_state.exclusao_confirmada = False

                                # Botão inicial de exclusão
                                if st.button("Excluir Produto", type="primary", use_container_width=True, key="btn_excluir_produto"):
                                    # Ativamos o modo de confirmação
                                    st.session_state.exclusao_confirmada = True
                                    st.rerun()

                                # Exibir confirmação se o modo de confirmação estiver ativo
                                if st.session_state.exclusao_confirmada:
                                    if produto_remover_id:
                                        produto_nome = produtos_df[produtos_df['id'] == produto_remover_id]['nome'].iloc[0]

                                        # Saindo do bloco de colunas aninhadas para evitar erro
                                        st.warning(f"Tem certeza que deseja excluir o produto: **{produto_nome}**?")

                    # Movendo os botões de confirmação para fora do aninhamento excessivo de colunas
                    # Somente mostrará se o modo de confirmação estiver ativo
                    if 'exclusao_confirmada' in st.session_state and st.session_state.exclusao_confirmada and produtos_df is not None and not produtos_df.empty:
                        produto_remover_id = st.session_state.get('remover_produto')
                        if produto_remover_id is not None:
                            produto_nome = produtos_df[produtos_df['id'] == produto_remover_id]['nome'].iloc[0]

                            confirm_col1, confirm_col2 = st.columns(2)
                            with confirm_col1:
                                if st.button("✓ Confirmar Exclusão", type="primary", use_container_width=True, key="btn_confirmar_exclusao"):
                                    try:
                                        print(f"Tentando excluir produto ID: {produto_remover_id}")
                                        result = st.session_state.db.delete_produto(produto_remover_id)

                                        if result:
                                            st.success(f"Produto '{produto_nome}' excluído com sucesso!")
                                            # Resetar estado de confirmação
                                            st.session_state.exclusao_confirmada = False
                                            # Recarregar a página
                                            time.sleep(1)  # Pequena pausa para mostrar a mensagem
                                            st.rerun()
                                        else:
                                            st.error("Falha ao excluir o produto. Tente novamente.")
                                    except Exception as e:
                                        st.error(f"Erro ao excluir produto: {str(e)}")
                                        import traceback
                                        print(traceback.format_exc())

                            with confirm_col2:
                                if st.button("✗ Cancelar", use_container_width=True, key="btn_cancelar_exclusao"):
                                    # Resetar estado de confirmação
                                    st.session_state.exclusao_confirmada = False
                                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao carregar produtos: {str(e)}")

    # === Aba de Nova Venda ===
    with tab_nova_venda:
        st.subheader("Registrar Nova Venda")

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
                        custom_info("Não há produtos em estoque disponíveis para venda.")
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

                if produto_id and st.button("Adicionar ao Carrinho", type="primary", use_container_width=True):
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

                # Cabeçalhos da tabela
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1.5, 1.5, 1, 1])
                with col1:
                    st.write("**Produto**")
                with col2:
                    st.write("**Qtd**")
                with col3:
                    st.write("**Preço Unit.**")
                with col4:
                    st.write("**Subtotal**")
                with col5:
                    st.write("**Editar**")
                with col6:
                    st.write("**Remover**")

                st.markdown("---")

                # Lista editável de produtos no carrinho
                for i, item in enumerate(st.session_state.produtos_venda):
                    col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1.5, 1.5, 1, 1])

                    with col1:
                        st.write(f"{item['nome']}")

                    with col2:
                        # Campo editável de quantidade
                        nova_quantidade = st.number_input(
                            "Qtd", 
                            min_value=1, 
                            value=item['quantidade'],
                            key=f"qty_{i}",
                            label_visibility="collapsed"
                        )

                    with col3:
                        # Campo editável de preço unitário
                        novo_preco = st.number_input(
                            "Preço Unit.",
                            min_value=0.01, 
                            value=item['preco_unitario'],
                            format="%.2f",
                            key=f"price_{i}",
                            label_visibility="collapsed"
                        )

                    with col4:
                        # Subtotal calculado automaticamente
                        novo_subtotal = nova_quantidade * novo_preco
                        st.write(f"R$ {novo_subtotal:.2f}")

                    with col5:
                        # Botão para atualizar o item
                        if st.button("✏️", key=f"edit_{i}", help="Atualizar item", use_container_width=True):
                            st.session_state.produtos_venda[i]['quantidade'] = nova_quantidade
                            st.session_state.produtos_venda[i]['preco_unitario'] = novo_preco
                            st.session_state.produtos_venda[i]['subtotal'] = novo_subtotal
                            st.success(f"Item '{item['nome']}' atualizado!")
                            st.rerun()

                    with col6:
                        # Botão para remover o item
                        if st.button("🗑️", key=f"remove_{i}", help="Remover item", use_container_width=True):
                            st.session_state.produtos_venda.pop(i)
                            st.success(f"Item '{item['nome']}' removido do carrinho!")
                            st.rerun()

                # Calcular valor total
                valor_total = sum([item['quantidade'] * item['preco_unitario'] for item in st.session_state.produtos_venda])

                # Totais e finalização
                st.markdown("---")
                custom_info(f"Valor Total da Venda: **R$ {valor_total:.2f}**")

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
                    if st.button("Limpar Carrinho", type="secondary", use_container_width=True):
                        st.session_state.produtos_venda = []
                        st.rerun()

                with col2:
                    # JavaScript para corrigir botões invisíveis
                    st.markdown("""
                    <script>
                    setTimeout(function() {
                        // Encontrar todos os botões
                        const buttons = document.querySelectorAll('button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"]');

                        buttons.forEach(button => {
                            // Aplicar estilos diretamente
                            if (button.textContent.includes('Limpar') || button.textContent.includes('Finalizar')) {
                                button.style.backgroundColor = '#f8f9fa';
                                button.style.color = '#212529';
                                button.style.border = '1px solid #dee2e6';
                                button.style.fontWeight = '500';
                                button.style.minHeight = '38px';

                                // Se for botão primário (Finalizar)
                                if (button.textContent.includes('Finalizar')) {
                                    button.style.backgroundColor = '#3a75c4';
                                    button.style.color = 'white';
                                    button.style.border = '1px solid #3a75c4';
                                }

                                // Garantir que o texto seja visível
                                const textElements = button.querySelectorAll('p, span, div');
                                textElements.forEach(el => {
                                    el.style.color = 'inherit';
                                    el.style.opacity = '1';
                                    el.style.visibility = 'visible';
                                });
                            }
                        });
                    }, 500);
                    </script>
                    """, unsafe_allow_html=True)

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
                custom_info("Nenhum produto adicionado ao carrinho.")

    # === Aba de Histórico de Vendas ===
    with tab_historico:
        st.subheader("Histórico de Vendas")

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
                        itens_df['lucro'] = itens_df['lucro'].map('R$ {:.2f}'.format)

                        st.dataframe(itens_df[['produto_nome', 'quantidade', 'preco_unitario', 'subtotal', 'lucro']], hide_index=True)

                        # Botões de ação em três colunas
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            # Botão para editar venda
                            if st.button("EDITAR VENDAS", type="primary", key=f"editar_venda_{venda_id}", use_container_width=True):
                                st.session_state[f'editando_venda_{venda_id}'] = True
                                st.rerun()

                        with col2:
                            # Botão para gerar PDF
                            gerar_pdf_btn = st.button("GERAR RELATÓRIO DE VENDAS", type="primary", key=f"gerar_pdf_venda_{venda_id}", use_container_width=True)

                        with col3:
                            # Botão para excluir venda
                            if st.button("EXCLUIR VENDAS", type="primary", key=f"excluir_venda_{venda_id}", use_container_width=True):
                                # Marcar venda para exclusão
                                st.session_state[f'confirmar_exclusao_venda_{venda_id}'] = True
                                st.rerun()

                        # Confirmação de exclusão da venda
                        if st.session_state.get(f'confirmar_exclusao_venda_{venda_id}', False):
                            st.warning(f"⚠️ **Tem certeza que deseja excluir a Venda #{venda_id}?**")
                            custom_info(f"**Cliente:** {venda['cliente_nome']} | **Valor:** {venda['valor_total']} | **Data:** {venda['data_venda']}")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✓ CONFIRMAR EXCLUSÃO", type="primary", key=f"confirmar_exclusao_{venda_id}", use_container_width=True):
                                    with st.spinner("Excluindo venda..."):
                                        try:
                                            # Primeira tentativa: usando SQL direto
                                            result = st.session_state.db.excluir_venda_com_sql(venda_id)
                                            if result:
                                                st.success(f"✅ Venda #{venda_id} excluída com sucesso!")
                                                # Reset estado de confirmação
                                                st.session_state[f'confirmar_exclusao_venda_{venda_id}'] = False
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                # Segunda tentativa: usando ORM
                                                result = st.session_state.db.excluir_venda(venda_id)
                                                if result:
                                                    st.success(f"✅ Venda #{venda_id} excluída com sucesso!")
                                                    st.session_state[f'confirmar_exclusao_venda_{venda_id}'] = False
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Falha ao excluir a venda.")
                                        except Exception as e:
                                            st.error(f"Erro ao excluir venda: {str(e)}")

                            with col2:
                                if st.button("✗ CANCELAR", type="secondary", key=f"cancelar_exclusao_{venda_id}", use_container_width=True):
                                    st.session_state[f'confirmar_exclusao_venda_{venda_id}'] = False
                                    st.rerun()

                        # Modo de edição da venda
                        if st.session_state.get(f'editando_venda_{venda_id}', False):
                            st.subheader("Editando Itens da Venda")
                            st.warning("Modo de edição ativo. Faça as alterações nos itens abaixo:")

                            # Preparar dados originais para edição (sem formatação)
                            itens_originais = st.session_state.db.get_itens_venda(venda_id)

                            # Lista editável dos itens
                            for i, item in itens_originais.iterrows():
                                # Função para salvar quantidade alterada
                                def salvar_quantidade():
                                    key_qty = f"edit_qty_{venda_id}_{i}"
                                    key_price = f"edit_price_{venda_id}_{i}"
                                    if key_qty in st.session_state and key_price in st.session_state:
                                        try:
                                            st.session_state.db.update_item_venda(
                                                item['id'], 
                                                st.session_state[key_qty], 
                                                st.session_state[key_price]
                                            )
                                            st.success(f"Item '{item['produto_nome']}' atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao atualizar item: {str(e)}")

                                # Função para salvar preço alterado
                                def salvar_preco():
                                    key_qty = f"edit_qty_{venda_id}_{i}"
                                    key_price = f"edit_price_{venda_id}_{i}"
                                    if key_qty in st.session_state and key_price in st.session_state:
                                        try:
                                            st.session_state.db.update_item_venda(
                                                item['id'], 
                                                st.session_state[key_qty], 
                                                st.session_state[key_price]
                                            )
                                            st.success(f"Item '{item['produto_nome']}' atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao atualizar item: {str(e)}")

                                col1, col2, col3, col4, col5 = st.columns([3, 1, 1.5, 1.5, 1])

                                with col1:
                                    st.write(f"**{item['produto_nome']}**")

                                with col2:
                                    st.markdown("**Qtd**")
                                    nova_quantidade = st.number_input(
                                        "Quantidade", 
                                        min_value=1, 
                                        value=int(item['quantidade']),
                                        key=f"edit_qty_{venda_id}_{i}",
                                        on_change=salvar_quantidade,
                                        label_visibility="collapsed"
                                    )

                                with col3:
                                    st.markdown("**Preço Unit.**")
                                    novo_preco = st.number_input(
                                        "Preço Unitário",
                                        min_value=0.01, 
                                        value=float(item['preco_unitario']),
                                        format="%.2f",
                                        key=f"edit_price_{venda_id}_{i}",
                                        on_change=salvar_preco,
                                        label_visibility="collapsed"
                                    )

                                with col4:
                                    novo_subtotal = nova_quantidade * novo_preco
                                    st.markdown("**R$ {:.2f}**".format(novo_subtotal))

                                with col5:
                                    # Botão para remover item
                                    if st.button("🗑️", key=f"remove_item_{venda_id}_{i}", help="Remover item da venda", use_container_width=True):
                                        try:
                                            st.session_state.db.remove_item_venda(item['id'])
                                            st.success(f"Item '{item['produto_nome']}' removido!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao remover item: {str(e)}")

                            # Botões de controle da edição
                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("Cancelar Edição", type="secondary", key=f"cancelar_edicao_{venda_id}"):
                                    st.session_state[f'editando_venda_{venda_id}'] = False
                                    st.rerun()

                            with col2:
                                if st.button("Finalizar Edição", type="primary", key=f"finalizar_edicao_{venda_id}"):
                                    st.session_state[f'editando_venda_{venda_id}'] = False
                                    st.success("Edição finalizada!")
                                    st.rerun()

                        # Processar geração de PDF se o botão foi clicado
                        if gerar_pdf_btn:
                            with st.spinner("Gerando relatório de venda..."):
                                try:
                                    # Obter dados do cliente
                                    from datetime import datetime
                                    cliente_id = venda.get('cliente_id', None)
                                    if cliente_id:
                                        cliente_df = st.session_state.db.get_cliente_by_id(cliente_id)
                                        cliente_dict = cliente_df.iloc[0].to_dict() if not cliente_df.empty else {'nome': venda['cliente_nome']}
                                    else:
                                        cliente_dict = {'nome': venda['cliente_nome']}

                                    # Definir caminho do arquivo
                                    cliente_nome_formatado = cliente_dict['nome'].replace(' ', '_').replace('/', '_').replace('\\', '_')
                                    pdf_filename = f"pdfs/venda_{venda_id}_{cliente_nome_formatado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                                    # Gerar o PDF
                                    from utils.pdf_generator_venda_fixed import gerar_pdf_venda
                                    pdf_path = gerar_pdf_venda(venda, cliente_dict, itens_df, pdf_filename)

                                    # Criar link para download
                                    with open(pdf_path, "rb") as pdf_file:
                                        pdf_bytes = pdf_file.read()

                                    # Mostrar mensagem de sucesso
                                    st.success(f"Relatório de venda gerado com sucesso!")

                                    # Botão de download
                                    download_key = f"download_venda_{venda_id}_{datetime.now().strftime('%H%M%S')}"
                                    st.download_button(
                                        label="📥 Baixar Relatório de Venda",
                                        data=pdf_bytes,
                                        file_name=os.path.basename(pdf_path),
                                        mime="application/pdf",
                                        key=download_key
                                    )
                                except Exception as e:
                                    st.error(f"Erro ao gerar relatório: {str(e)}")


        except Exception as e:
            st.error(f"Erro ao carregar vendas: {str(e)}")

    # CSS e JavaScript para eliminar qualquer fundo azul restante
    st.markdown("""
    <style>
    /* MÁXIMA PRIORIDADE - Forçar fundo branco em TODOS os elementos de informação */
    .stAlert, 
    div[data-testid="stAlert"],
    .stInfo,
    div[data-testid="stInfo"],
    .element-container .stAlert,
    .element-container div[data-testid="stAlert"],
    div[data-baseweb="notification"],
    .css-1x8cf1d,
    .css-12w0qpk,
    [data-baseweb="notification"],
    [role="alert"],
    .streamlit-alert {
        background-color: rgba(255, 255, 255, 0.9) !important;
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        color: #1e1e1e !important;
        border-left: 4px solid #6c757d !important;
    }

    /* Forçar texto escuro em alertas */
    .stAlert *,
    div[data-testid="stAlert"] *,
    .stInfo *,
    div[data-testid="stInfo"] *,
    div[data-baseweb="notification"] *,
    [data-baseweb="notification"] *,
    [role="alert"] * {
        color: #1e1e1e !important;
    }

    /* Remover qualquer background azul de containers */
    .main .block-container,
    div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"] {
        background: transparent !important;
    }

    /* Específico para alertas de informação - REMOVER AZUL */
    .stAlert[data-baseweb="notification"],
    div[data-testid="stAlert"][data-baseweb="notification"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        background: rgba(255, 255, 255, 0.9) !important;
        border-left: 4px solid #6c757d !important;
    }

    /* Forçar override de estilos inline azuis */
    div[style*="background-color: rgb(13, 110, 253)"],
    div[style*="background-color: blue"],
    div[style*="background: blue"],
    div[style*="background: rgb(13, 110, 253)"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        background: rgba(255, 255, 255, 0.9) !important;
    }
    </style>

    <script>
    // JavaScript para forçar remoção de fundos azuis
    function removeBlueBackgrounds() {
        // Buscar todos os elementos com fundo azul
        const blueElements = document.querySelectorAll('*');

        blueElements.forEach(element => {
            const computedStyle = window.getComputedStyle(element);
            const bgColor = computedStyle.backgroundColor;

            // Verificar se o fundo é azul
            if (bgColor.includes('rgb(13, 110, 253)') || 
                bgColor.includes('rgb(32, 146, 236)') ||
                bgColor.includes('blue') ||
                element.style.backgroundColor.includes('blue') ||
                element.style.backgroundColor.includes('rgb(13, 110, 253)')) {

                element.style.setProperty('background-color', 'rgba(255, 255, 255, 0.9)', 'important');
                element.style.setProperty('background', 'rgba(255, 255, 255, 0.9)', 'important');
                element.style.setProperty('border', '1px solid rgba(0, 0, 0, 0.1)', 'important');
                element.style.setProperty('color', '#1e1e1e', 'important');
            }
        });

        // Buscar especificamente alertas do Streamlit
        const alerts = document.querySelectorAll('[data-testid="stAlert"], .stAlert, [data-baseweb="notification"], [role="alert"]');
        alerts.forEach(alert => {
            alert.style.setProperty('background-color', 'rgba(255, 255, 255, 0.9)', 'important');
            alert.style.setProperty('background', 'rgba(255, 255, 255, 0.9)', 'important');
            alert.style.setProperty('border', '1px solid rgba(0, 0, 0, 0.1)', 'important');
            alert.style.setProperty('border-left', '4px solid #6c757d', 'important');

            // Forçar cor do texto
            const textElements = alert.querySelectorAll('*');
            textElements.forEach(text => {
                text.style.setProperty('color', '#1e1e1e', 'important');
            });
        });
    }

    // Executar imediatamente
    removeBlueBackgrounds();

    // Observar mudanças no DOM
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                setTimeout(removeBlueBackgrounds, 100);
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Executar periodicamente
    setInterval(removeBlueBackgrounds, 1000);
    </script>
    """, unsafe_allow_html=True)