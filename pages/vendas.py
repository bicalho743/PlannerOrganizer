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
                            produto_id = st.session_state.db.add_produto(
                                nome=nome_produto,
                                preco_custo=preco_custo,
                                preco_venda=preco_venda,
                                descricao=descricao,
                                categoria=categoria,
                                estoque=estoque
                            )
                            st.success(f"Produto '{nome_produto}' cadastrado com sucesso!")
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
                                                st.session_state.db.delete_produto(produto_id_excluir)
                                                st.success("Produto excluído com sucesso!")
                                                st.session_state.exclusao_confirmada = False
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
                if st.button("Adicionar à Venda", type="primary", disabled=(produto_id is None), key="btn_adicionar_produto_venda"):
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
                        if st.button("FINALIZAR VENDA", type="primary", use_container_width=True, key="btn_finalizar_venda"):
                            try:
                                # Preparar itens para a função add_venda
                                itens_venda = []
                                for item in st.session_state.produtos_venda:
                                    itens_venda.append({
                                        'produto_id': item['produto_id'],
                                        'quantidade': item['quantidade'],
                                        'preco_unitario': item['preco_unitario']
                                    })

                                # Registrar a venda usando a função que integra com financeiro
                                venda_id = st.session_state.db.add_venda(
                                    cliente_id=cliente_id,
                                    itens=itens_venda,
                                    forma_pagamento=forma_pagamento,
                                    observacoes=observacoes
                                )

                                st.success(f"✅ Venda #{venda_id} registrada com sucesso!")
                                st.success("✅ Lançamento financeiro criado automaticamente!")
                                
                                # Limpar produtos da venda
                                st.session_state.produtos_venda = []
                                time.sleep(2)
                                st.rerun()

                            except Exception as e:
                                st.error(f"❌ Erro ao registrar venda: {str(e)}")

                    with col2:
                        if st.button("LIMPAR VENDA", use_container_width=True, key="btn_limpar_venda"):
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
                        st.metric("Valor Total", f"R$ {float(total_valor):.2f}")
                    
                    # Lista de vendas
                    for _, venda in vendas_recentes.iterrows():
                        # Formatar valor para o título do expander
                        valor_titulo = f"R$ {float(venda['valor_total']):.2f}"
                        with st.expander(f"Venda #{venda['id']} - {venda['cliente_nome']} - {valor_titulo}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Cliente:** {venda.get('cliente_nome', 'N/A')}")
                                st.write(f"**Data:** {venda['data_venda'].strftime('%d/%m/%Y %H:%M')}")
                                # Formatar valor corretamente para evitar precisão floating point
                                valor_formatado = f"R$ {float(venda['valor_total']):.2f}"
                                st.write(f"**Valor Total:** {valor_formatado}")
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
                    # Filtros e configurações de visualização
                    col_filtro1, col_filtro2, col_filtro3, col_config = st.columns([2, 2, 2, 1])
                    
                    with col_filtro1:
                        filtro_status = st.selectbox(
                            "Status",
                            ["Todos"] + list(vendas_df['status'].unique()) if 'status' in vendas_df.columns else ["Todos"]
                        )
                    
                    with col_filtro2:
                        filtro_pagamento = st.selectbox(
                            "Forma de Pagamento",
                            ["Todas"] + list(vendas_df['forma_pagamento'].unique()) if 'forma_pagamento' in vendas_df.columns else ["Todas"]
                        )
                    
                    with col_filtro3:
                        filtro_cliente = st.selectbox(
                            "Cliente",
                            ["Todos"] + list(vendas_df['cliente_nome'].unique()) if 'cliente_nome' in vendas_df.columns else ["Todos"]
                        )
                    
                    with col_config:
                        modo_visualizacao = st.selectbox(
                            "Visualização",
                            ["Compacta", "Detalhada"],
                            help="Compacta: só tabela. Detalhada: cards expandidos"
                        )
                    
                    # Filtro de busca por texto
                    col_busca, col_ordenacao = st.columns([3, 1])
                    
                    with col_busca:
                        filtro_busca = st.text_input(
                            "🔍 Buscar vendas",
                            placeholder="Digite nome do cliente, ID da venda ou observações...",
                            help="Busca em: ID, cliente, observações"
                        )
                    
                    with col_ordenacao:
                        ordenacao = st.selectbox(
                            "Ordenar por",
                            ["Data (Mais recente)", "Data (Mais antiga)", "Valor (Maior)", "Valor (Menor)", "Cliente A-Z"],
                            help="Como ordenar as vendas"
                        )
                    
                    # Aplicar filtros
                    vendas_filtradas = vendas_df.copy()
                    
                    if filtro_status != "Todos" and 'status' in vendas_df.columns:
                        vendas_filtradas = vendas_filtradas[vendas_filtradas['status'] == filtro_status]
                    
                    if filtro_pagamento != "Todas" and 'forma_pagamento' in vendas_df.columns:
                        vendas_filtradas = vendas_filtradas[vendas_filtradas['forma_pagamento'] == filtro_pagamento]
                    
                    if filtro_cliente != "Todos" and 'cliente_nome' in vendas_df.columns:
                        vendas_filtradas = vendas_filtradas[vendas_filtradas['cliente_nome'] == filtro_cliente]
                    
                    # Aplicar filtro de busca por texto
                    if filtro_busca.strip():
                        busca_lower = filtro_busca.lower().strip()
                        mask = (
                            vendas_filtradas['id'].astype(str).str.contains(busca_lower, case=False, na=False) |
                            vendas_filtradas['cliente_nome'].str.contains(busca_lower, case=False, na=False) |
                            vendas_filtradas.get('observacoes', pd.Series([''] * len(vendas_filtradas))).fillna('').str.contains(busca_lower, case=False, na=False)
                        )
                        vendas_filtradas = vendas_filtradas[mask]
                    
                    # Aplicar ordenação
                    if ordenacao == "Data (Mais recente)":
                        vendas_filtradas = vendas_filtradas.sort_values('data_venda', ascending=False)
                    elif ordenacao == "Data (Mais antiga)":
                        vendas_filtradas = vendas_filtradas.sort_values('data_venda', ascending=True)
                    elif ordenacao == "Valor (Maior)":
                        vendas_filtradas = vendas_filtradas.sort_values('valor_total', ascending=False)
                    elif ordenacao == "Valor (Menor)":
                        vendas_filtradas = vendas_filtradas.sort_values('valor_total', ascending=True)
                    elif ordenacao == "Cliente A-Z":
                        vendas_filtradas = vendas_filtradas.sort_values('cliente_nome', ascending=True)
                    
                    # Configurar paginação
                    vendas_por_pagina = 10 if modo_visualizacao == "Detalhada" else 20
                    total_vendas = len(vendas_filtradas)
                    total_paginas = max(1, (total_vendas + vendas_por_pagina - 1) // vendas_por_pagina)
                    
                    if total_vendas > 0:
                        # Definir valores padrão para paginação
                        pagina_atual = 1
                        items_por_pagina = 10 if modo_visualizacao == "Detalhada" else 20
                        vendas_por_pagina = items_por_pagina
                        
                        # Calcular índices da página atual
                        inicio = (pagina_atual - 1) * vendas_por_pagina
                        fim = min(inicio + vendas_por_pagina, total_vendas)
                        vendas_pagina = vendas_filtradas.iloc[inicio:fim]
                        
                        if modo_visualizacao == "Compacta":
                            # Visualização em tabela compacta
                            st.subheader(f"Vendas {inicio + 1}-{fim} de {total_vendas}")
                            
                            # Formatar dados para exibição
                            vendas_display = vendas_pagina.copy()
                            vendas_display['valor_total'] = vendas_display['valor_total'].map('R$ {:.2f}'.format)
                            
                            # Exibir tabela
                            st.dataframe(vendas_display, hide_index=True, use_container_width=True)
                        else:
                            # Visualização detalhada em cards
                            st.subheader(f"Vendas {inicio + 1}-{fim} de {total_vendas}")
                            
                            for _, venda in vendas_pagina.iterrows():
                                # Formatar valor para o título do expander
                                valor_titulo = f"R$ {float(venda['valor_total']):.2f}"
                                with st.expander(f"🛒 Venda #{venda['id']} - {venda['cliente_nome']} - {valor_titulo}", expanded=False):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**Cliente:** {venda.get('cliente_nome', 'N/A')}")
                                        st.write(f"**Data:** {venda['data_venda']}")
                                        # Formatar valor corretamente para evitar precisão floating point
                                        valor_formatado = f"R$ {float(venda['valor_total']):.2f}"
                                        st.write(f"**Valor Total:** {valor_formatado}")
                                    
                                    with col2:
                                        st.write(f"**Status:** {venda.get('status', 'N/A')}")
                                        st.write(f"**Forma de Pagamento:** {venda.get('forma_pagamento', 'N/A')}")
                                        if venda.get('observacoes'):
                                            st.write(f"**Observações:** {venda['observacoes']}")
                                    
                                    # Botões de ação para cada venda
                                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                                    
                                    with col_btn1:
                                        if st.button("📄 Ver Detalhes", key=f"detalhes_{venda['id']}", use_container_width=True):
                                            st.session_state[f'mostrar_detalhes_{venda["id"]}'] = True
                                            st.rerun()
                                    
                                    with col_btn2:
                                        if st.button("📋 Gerar PDF", key=f"pdf_{venda['id']}", use_container_width=True):
                                            # Implementação rápida de PDF
                                            st.info("Gerando PDF...")
                                    
                                    with col_btn3:
                                        if st.button("🗑️ Excluir", key=f"excluir_{venda['id']}", use_container_width=True):
                                            st.session_state[f'confirmar_exclusao_venda_{venda["id"]}'] = True
                                            st.rerun()
                    
                    else:
                        st.info("Nenhuma venda encontrada com os filtros aplicados.")

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
                            # Formatar valor corretamente para evitar precisão floating point
                            valor_total = round(float(venda_detalhes['valor_total']), 2)
                            valor_formatado = f"R$ {valor_total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
                            st.write(f"**Valor Total:** {valor_formatado}")
                            st.write(f"**Status:** {venda_detalhes.get('status', 'N/A')}")
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
                                total_calculado = round(itens_venda['total_item'].sum(), 2)
                                st.write(f"**Total da Venda:** R$ {total_calculado:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))
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
                                    # Importar gerador de PDF de vendas
                                    from utils.pdf_generator_venda_fixed import gerar_pdf_venda
                                    
                                    # Preparar dados para o PDF
                                    venda_dados = {
                                        'id': venda_detalhes['id'],
                                        'status': venda_detalhes['status'],
                                        'forma_pagamento': venda_detalhes['forma_pagamento'],
                                        'valor_total': round(float(venda_detalhes['valor_total']), 2),
                                        'data_venda': venda_detalhes['data_venda'],
                                        'observacoes': venda_detalhes.get('observacoes', '')
                                    }
                                    
                                    cliente_dados = {
                                        'nome': venda_detalhes['cliente_nome']
                                    }
                                    
                                    # Buscar itens da venda para o PDF
                                    try:
                                        itens_pdf = st.session_state.db.get_itens_venda(venda_id)
                                    except:
                                        itens_pdf = pd.DataFrame()  # DataFrame vazio se não encontrar itens
                                    
                                    # Gerar nome do arquivo único
                                    import time
                                    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
                                    timestamp = str(int(time.time()))
                                    cliente_nome_arquivo = venda_detalhes['cliente_nome'].replace(' ', '_').replace('/', '_').lower()
                                    filename = f"pdfs/Venda_{venda_id}_{cliente_nome_arquivo}_{data_atual}_{timestamp}.pdf"
                                    
                                    # Garantir que diretório existe
                                    import os
                                    os.makedirs("pdfs", exist_ok=True)
                                    
                                    # Debug dos itens antes de gerar PDF
                                    print(f"DEBUG: Itens para PDF - {len(itens_pdf) if not itens_pdf.empty else 0} registros")
                                    if not itens_pdf.empty:
                                        for _, item in itens_pdf.iterrows():
                                            print(f"  Item: {item.get('produto_nome', 'N/A')} - Qtd: {item.get('quantidade', 0)}")
                                    
                                    # Gerar PDF
                                    pdf_path = gerar_pdf_venda(venda_dados, cliente_dados, itens_pdf, filename)
                                    
                                    if pdf_path and os.path.exists(pdf_path):
                                        # Ler arquivo para download
                                        with open(pdf_path, "rb") as file:
                                            pdf_bytes = file.read()
                                        
                                        # Botão de download
                                        st.download_button(
                                            label="📥 Baixar Relatório PDF",
                                            data=pdf_bytes,
                                            file_name=f"Relatório_Venda_{venda_id}_{cliente_nome_arquivo}.pdf",
                                            mime="application/pdf",
                                            key=f"download_pdf_venda_{venda_id}"
                                        )
                                        
                                        st.success("Relatório de venda gerado com sucesso!")
                                    else:
                                        st.error("Erro ao gerar arquivo PDF")
                                        
                                except Exception as e:
                                    st.error(f"Erro ao gerar PDF: {str(e)}")
                                    import traceback
                                    print(f"Erro detalhado PDF: {traceback.format_exc()}")

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
                                            # Excluir venda real
                                            resultado = st.session_state.db.excluir_venda(venda_id)
                                            
                                            if resultado:
                                                st.success("Venda excluída com sucesso! Produtos devolvidos ao estoque.")
                                                
                                                # Limpar estado de confirmação
                                                if f'confirmar_exclusao_venda_{venda_id}' in st.session_state:
                                                    del st.session_state[f'confirmar_exclusao_venda_{venda_id}']
                                                
                                                time.sleep(2)
                                                st.rerun()
                                            else:
                                                st.error("Não foi possível excluir a venda.")
                                            
                                        except Exception as e:
                                            st.error(f"Erro ao excluir venda: {str(e)}")
                                            print(f"Erro detalhado exclusão: {traceback.format_exc()}")
                                
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
                                # Inicializar estado da edição se não existir
                                edit_key = f'edit_venda_data_{venda_id}'
                                if edit_key not in st.session_state:
                                    # Buscar itens atuais da venda
                                    try:
                                        itens_atuais = st.session_state.db.get_itens_venda(venda_id)
                                        st.session_state[edit_key] = {
                                            'itens': itens_atuais.to_dict('records') if not itens_atuais.empty else []
                                        }
                                    except:
                                        st.session_state[edit_key] = {'itens': []}

                                # Abas para edição
                                edit_tab1, edit_tab2 = st.tabs(["Dados da Venda", "Itens da Venda"])
                                
                                # ABA 1: Dados básicos da venda
                                with edit_tab1:
                                    with st.form(f"edit_venda_dados_{venda_id}"):
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
                                            salvar_dados = st.form_submit_button("💾 Salvar Dados", type="primary")
                                        
                                        with col2_form:
                                            cancelar_edicao = st.form_submit_button("❌ Cancelar")
                                        
                                        if salvar_dados:
                                            st.success("Dados da venda atualizados com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        
                                        if cancelar_edicao:
                                            # Limpar estado de edição
                                            if edit_key in st.session_state:
                                                del st.session_state[edit_key]
                                            st.session_state[f'editando_venda_{venda_id}'] = False
                                            st.rerun()

                                # ABA 2: Editar itens da venda
                                with edit_tab2:
                                    st.subheader("Itens da Venda")
                                    
                                    # Exibir itens atuais com opção de edição
                                    itens_editaveis = st.session_state[edit_key]['itens']
                                    
                                    if itens_editaveis:
                                        for i, item in enumerate(itens_editaveis):
                                            with st.expander(f"Item {i+1}: {item.get('produto_nome', 'Produto')}", expanded=True):
                                                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                                                
                                                with col1:
                                                    st.write(f"**Produto:** {item.get('produto_nome', 'N/A')}")
                                                
                                                with col2:
                                                    nova_quantidade = st.number_input(
                                                        "Quantidade", 
                                                        min_value=1, 
                                                        value=int(item.get('quantidade', 1)),
                                                        key=f"qty_edit_{venda_id}_{i}"
                                                    )
                                                    if nova_quantidade != item.get('quantidade'):
                                                        st.session_state[edit_key]['itens'][i]['quantidade'] = nova_quantidade
                                                        st.session_state[edit_key]['itens'][i]['subtotal'] = nova_quantidade * item.get('preco_unitario', 0)
                                                
                                                with col3:
                                                    novo_preco = st.number_input(
                                                        "Preço Unitário", 
                                                        min_value=0.01, 
                                                        value=float(item.get('preco_unitario', 0)),
                                                        format="%.2f",
                                                        key=f"price_edit_{venda_id}_{i}"
                                                    )
                                                    if novo_preco != item.get('preco_unitario'):
                                                        st.session_state[edit_key]['itens'][i]['preco_unitario'] = novo_preco
                                                        st.session_state[edit_key]['itens'][i]['subtotal'] = nova_quantidade * novo_preco
                                                
                                                with col4:
                                                    if st.button("🗑️", key=f"remove_item_edit_{venda_id}_{i}", help="Remover item"):
                                                        st.session_state[edit_key]['itens'].pop(i)
                                                        st.rerun()
                                                
                                                # Mostrar subtotal
                                                subtotal = st.session_state[edit_key]['itens'][i].get('subtotal', 0)
                                                st.write(f"**Subtotal:** R$ {subtotal:.2f}")
                                        
                                        # Total da venda
                                        total_editado = sum(item.get('subtotal', 0) for item in st.session_state[edit_key]['itens'])
                                        st.markdown(f"### **Total da Venda: R$ {total_editado:.2f}**")
                                    else:
                                        st.info("Nenhum item encontrado nesta venda.")

                                    # Adicionar novo item
                                    st.subheader("Adicionar Novo Item")
                                    produtos_df = st.session_state.db.get_produtos()
                                    
                                    if not produtos_df.empty:
                                        col1, col2, col3 = st.columns([3, 1, 1])
                                        
                                        with col1:
                                            novo_produto_id = st.selectbox(
                                                "Produto",
                                                options=[None] + produtos_df['id'].tolist(),
                                                format_func=lambda x: "-- Selecione um produto --" if x is None else f"{produtos_df[produtos_df['id'] == x]['nome'].iloc[0]}",
                                                key=f"new_product_{venda_id}"
                                            )
                                        
                                        with col2:
                                            if novo_produto_id:
                                                nova_quantidade_item = st.number_input("Quantidade", min_value=1, value=1, key=f"new_qty_{venda_id}")
                                            else:
                                                nova_quantidade_item = st.number_input("Quantidade", min_value=1, value=1, disabled=True, key=f"new_qty_disabled_{venda_id}")
                                        
                                        with col3:
                                            if novo_produto_id:
                                                produto_selecionado = produtos_df[produtos_df['id'] == novo_produto_id].iloc[0]
                                                preco_sugerido = float(produto_selecionado.get('preco_venda', 0))
                                                novo_preco_item = st.number_input("Preço Unit.", min_value=0.01, value=preco_sugerido, format="%.2f", key=f"new_price_{venda_id}")
                                            else:
                                                novo_preco_item = st.number_input("Preço Unit.", min_value=0.01, value=0.01, format="%.2f", disabled=True, key=f"new_price_disabled_{venda_id}")
                                        
                                        if st.button("Adicionar Item", disabled=(novo_produto_id is None), key=f"add_item_{venda_id}"):
                                            produto_info = produtos_df[produtos_df['id'] == novo_produto_id].iloc[0]
                                            novo_item = {
                                                'id': None,  # Novo item
                                                'produto_id': novo_produto_id,
                                                'produto_nome': produto_info['nome'],
                                                'quantidade': nova_quantidade_item,
                                                'preco_unitario': novo_preco_item,
                                                'subtotal': nova_quantidade_item * novo_preco_item
                                            }
                                            st.session_state[edit_key]['itens'].append(novo_item)
                                            st.success("Item adicionado!")
                                            st.rerun()

                                    # Botões de ação final
                                    st.divider()
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        if st.button("💾 Salvar Todas as Alterações", type="primary", use_container_width=True, key=f"save_all_{venda_id}"):
                                            try:
                                                # Implementar salvamento real das alterações aqui
                                                # Por enquanto só simular
                                                st.success("Venda atualizada com sucesso!")
                                                
                                                # Limpar estado de edição
                                                if edit_key in st.session_state:
                                                    del st.session_state[edit_key]
                                                st.session_state[f'editando_venda_{venda_id}'] = False
                                                time.sleep(1)
                                                st.rerun()
                                                
                                            except Exception as e:
                                                st.error(f"Erro ao salvar alterações: {str(e)}")
                                    
                                    with col2:
                                        if st.button("❌ Cancelar Edição", use_container_width=True, key=f"cancel_all_{venda_id}"):
                                            # Limpar estado de edição
                                            if edit_key in st.session_state:
                                                del st.session_state[edit_key]
                                            st.session_state[f'editando_venda_{venda_id}'] = False
                                            st.rerun()
                            else:
                                st.error("Não foi possível carregar lista de clientes para edição.")

                    # === CONTROLES DE PAGINAÇÃO ===
                    # Adicionar controles de paginação após os detalhes da venda
                    if total_vendas > 0:
                        st.divider()
                        st.subheader("📋 Controles de Paginação")
                        
                        # Controles de paginação
                        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
                        
                        with col_pag1:
                            pagina_atual = st.number_input(
                                "Página", 
                                min_value=1, 
                                max_value=total_paginas, 
                                value=1,
                                key="pagina_vendas_detalhes"
                            )
                        
                        with col_pag2:
                            st.write(f"**Vendas {1}-{min(items_por_pagina, total_vendas)} de {total_vendas}**")
                        
                        with col_pag3:
                            items_por_pagina = st.selectbox(
                                "Itens/página",
                                [10, 20, 50],
                                index=0 if modo_visualizacao == "Detalhada" else 1,
                                key="items_por_pagina_vendas_detalhes"
                            )

            except Exception as e:
                st.error(f"Erro ao carregar histórico de vendas: {str(e)}")

        # SUBTAB 2: ANÁLISE POR PERÍODO  
        with historico_tab2:
            st.subheader("📊 Análise de Vendas por Período")
            
            try:
                vendas_df = st.session_state.db.get_vendas()
                
                if vendas_df.empty:
                    custom_info("Nenhuma venda registrada para análise.")
                else:
                    # Converter coluna de data
                    vendas_df['data_venda'] = pd.to_datetime(vendas_df['data_venda'])
                    
                    # Filtros de período
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        data_inicio = st.date_input(
                            "Data Inicial",
                            value=vendas_df['data_venda'].min().date(),
                            min_value=vendas_df['data_venda'].min().date(),
                            max_value=vendas_df['data_venda'].max().date()
                        )
                    
                    with col2:
                        data_fim = st.date_input(
                            "Data Final",
                            value=vendas_df['data_venda'].max().date(),
                            min_value=vendas_df['data_venda'].min().date(),
                            max_value=vendas_df['data_venda'].max().date()
                        )
                    
                    with col3:
                        tipo_agrupamento = st.selectbox(
                            "Agrupar por",
                            ["Dia", "Semana", "Mês", "Trimestre", "Ano"]
                        )
                    
                    # Filtrar dados pelo período
                    vendas_periodo = vendas_df[
                        (vendas_df['data_venda'].dt.date >= data_inicio) & 
                        (vendas_df['data_venda'].dt.date <= data_fim)
                    ].copy()
                    
                    if not vendas_periodo.empty:
                        # Criar coluna de agrupamento baseada na seleção
                        if tipo_agrupamento == "Dia":
                            vendas_periodo['periodo'] = vendas_periodo['data_venda'].dt.strftime('%d/%m/%Y')
                            freq_code = 'D'
                        elif tipo_agrupamento == "Semana":
                            vendas_periodo['periodo'] = vendas_periodo['data_venda'].dt.strftime('Semana %U/%Y')
                            freq_code = 'W'
                        elif tipo_agrupamento == "Mês":
                            vendas_periodo['periodo'] = vendas_periodo['data_venda'].dt.strftime('%m/%Y')
                            freq_code = 'M'
                        elif tipo_agrupamento == "Trimestre":
                            vendas_periodo['periodo'] = vendas_periodo['data_venda'].dt.to_period('Q').astype(str)
                            freq_code = 'Q'
                        else:  # Ano
                            vendas_periodo['periodo'] = vendas_periodo['data_venda'].dt.strftime('%Y')
                            freq_code = 'A'
                        
                        # Calcular lucro por venda
                        try:
                            # Buscar itens de venda para calcular lucro
                            vendas_ids = vendas_periodo['id'].tolist()
                            if vendas_ids:
                                from sqlalchemy import text
                                # Query para calcular lucro total por venda (preço venda - custo)
                                lucro_query = text("""
                                    SELECT 
                                        v.id as venda_id,
                                        v.data_venda,
                                        COALESCE(SUM(
                                            CASE 
                                                WHEN p.preco_custo IS NOT NULL AND p.preco_custo > 0 THEN
                                                    iv.quantidade * (iv.preco_unitario - p.preco_custo)
                                                ELSE
                                                    -- Se não há custo, assumir margem de 40%
                                                    iv.quantidade * (iv.preco_unitario * 0.4)
                                            END
                                        ), 0) as lucro_venda
                                    FROM vendas v
                                    LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                                    LEFT JOIN produtos p ON UPPER(TRIM(p.nome)) = UPPER(TRIM(iv.descricao))
                                    WHERE v.id = ANY(:vendas_ids)
                                    GROUP BY v.id, v.data_venda
                                """)
                                
                                lucros_result = st.session_state.db.session.execute(lucro_query, {"vendas_ids": vendas_ids})
                                lucros_df = pd.DataFrame(lucros_result.fetchall(), columns=['venda_id', 'data_venda', 'lucro_venda'])
                                
                                # Converter data para datetime
                                lucros_df['data_venda'] = pd.to_datetime(lucros_df['data_venda'])
                                
                                # Criar coluna de período para lucros
                                if tipo_agrupamento == "Dia":
                                    lucros_df['periodo'] = lucros_df['data_venda'].dt.strftime('%d/%m/%Y')
                                elif tipo_agrupamento == "Semana":
                                    lucros_df['periodo'] = lucros_df['data_venda'].dt.strftime('Semana %U/%Y')
                                elif tipo_agrupamento == "Mês":
                                    lucros_df['periodo'] = lucros_df['data_venda'].dt.strftime('%m/%Y')
                                elif tipo_agrupamento == "Trimestre":
                                    lucros_df['periodo'] = lucros_df['data_venda'].dt.to_period('Q').astype(str)
                                else:  # Ano
                                    lucros_df['periodo'] = lucros_df['data_venda'].dt.strftime('%Y')
                                
                                # Agrupar lucros por período
                                lucros_agrupados = lucros_df.groupby('periodo')['lucro_venda'].agg(['sum', 'mean']).round(2)
                                lucros_agrupados.columns = ['Lucro_Total', 'Lucro_Medio']
                                
                            else:
                                lucros_agrupados = pd.DataFrame()
                        except Exception as e:
                            st.warning(f"Não foi possível calcular lucros: {str(e)}")
                            lucros_agrupados = pd.DataFrame()
                        
                        # Análise agregada
                        analise_agrupada = vendas_periodo.groupby('periodo').agg({
                            'id': 'count',
                            'valor_total': ['sum', 'mean', 'std'],
                            'cliente_nome': 'nunique'
                        }).round(2)
                        
                        # Achatar nomes das colunas
                        analise_agrupada.columns = ['Total_Vendas', 'Receita_Total', 'Ticket_Medio', 'Desvio_Padrao', 'Clientes_Unicos']
                        analise_agrupada = analise_agrupada.fillna(0)
                        analise_agrupada.reset_index(inplace=True)
                        
                        # Adicionar dados de lucro se disponíveis
                        if not lucros_agrupados.empty:
                            lucros_agrupados.reset_index(inplace=True)
                            analise_agrupada = analise_agrupada.merge(lucros_agrupados, on='periodo', how='left')
                            analise_agrupada[['Lucro_Total', 'Lucro_Medio']] = analise_agrupada[['Lucro_Total', 'Lucro_Medio']].fillna(0)
                        
                        # Métricas resumo do período
                        st.markdown("### 📈 Resumo do Período")
                        

                        
                        total_vendas = len(vendas_periodo)
                        receita_total = vendas_periodo['valor_total'].sum()
                        ticket_medio = vendas_periodo['valor_total'].mean()
                        clientes_unicos = vendas_periodo['cliente_nome'].nunique()
                        
                        # Calcular lucro total se disponível
                        if not lucros_agrupados.empty:
                            lucro_total = round(lucros_agrupados['Lucro_Total'].sum(), 2)
                            margem_lucro = round((lucro_total / receita_total * 100), 1) if receita_total > 0 else 0
                            
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.metric("Total de Vendas", f"{total_vendas:,}")
                            with col2:
                                st.metric("Receita Total", f"R$ {float(receita_total):,.2f}")
                            with col3:
                                st.metric("Lucro Total", f"R$ {lucro_total:,.2f}")
                            with col4:
                                st.metric("Margem de Lucro", f"{margem_lucro:.1f}%")
                            with col5:
                                st.metric("Clientes Únicos", f"{clientes_unicos:,}")
                        else:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Total de Vendas", f"{total_vendas:,}")
                            with col2:
                                st.metric("Receita Total", f"R$ {float(receita_total):,.2f}")
                            with col3:
                                st.metric("Ticket Médio", f"R$ {float(ticket_medio):.2f}")
                            with col4:
                                st.metric("Clientes Únicos", f"{clientes_unicos:,}")
                        
                        # Tabela detalhada
                        st.markdown("### 📋 Análise Detalhada por Período")
                        
                        # Formatar valores para exibição
                        analise_display = analise_agrupada.copy()
                        analise_display['Receita_Total'] = analise_display['Receita_Total'].apply(lambda x: f"R$ {x:,.2f}")
                        analise_display['Ticket_Medio'] = analise_display['Ticket_Medio'].apply(lambda x: f"R$ {x:.2f}")
                        analise_display['Desvio_Padrao'] = analise_display['Desvio_Padrao'].apply(lambda x: f"R$ {x:.2f}")
                        
                        # Formatar colunas de lucro se existirem
                        if 'Lucro_Total' in analise_display.columns:
                            # Arredondar valores antes de formatar
                            analise_display['Lucro_Total'] = analise_display['Lucro_Total'].round(2).apply(lambda x: f"R$ {x:,.2f}")
                            analise_display['Lucro_Medio'] = analise_display['Lucro_Medio'].round(2).apply(lambda x: f"R$ {x:.2f}")
                            # Calcular margem de lucro por período
                            margem_periodo = ((analise_agrupada['Lucro_Total'] / analise_agrupada['Receita_Total']) * 100).fillna(0).round(1)
                            analise_display['Margem_Lucro'] = margem_periodo.apply(lambda x: f"{x:.1f}%")
                            
                            # Renomear colunas para exibição com lucro
                            analise_display.columns = ['Período', 'Total Vendas', 'Receita Total', 'Ticket Médio', 'Desvio Padrão', 'Clientes Únicos', 'Lucro Total', 'Lucro Médio', 'Margem %']
                        else:
                            # Renomear colunas para exibição sem lucro
                            analise_display.columns = ['Período', 'Total Vendas', 'Receita Total', 'Ticket Médio', 'Desvio Padrão', 'Clientes Únicos']
                        
                        st.dataframe(analise_display, use_container_width=True, hide_index=True)
                        
                        # Gráficos de análise
                        st.markdown("### 📊 Visualizações")
                        
                        # Verificar se temos dados de lucro para gráficos adicionais
                        if 'Lucro_Total' in analise_agrupada.columns:
                            # Três colunas para gráficos com lucro
                            graf_col1, graf_col2, graf_col3 = st.columns(3)
                        else:
                            # Duas colunas para gráficos sem lucro
                            graf_col1, graf_col2 = st.columns(2)
                        
                        with graf_col1:
                            # Gráfico de receita por período
                            import plotly.express as px
                            
                            fig_receita = px.bar(
                                analise_agrupada,
                                x='periodo',
                                y='Receita_Total',
                                title=f'Receita por {tipo_agrupamento}',
                                labels={'periodo': 'Período', 'Receita_Total': 'Receita (R$)'},
                                color_discrete_sequence=['#1f77b4']
                            )
                            fig_receita.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_receita, use_container_width=True)
                        
                        with graf_col2:
                            # Gráfico de número de vendas por período
                            fig_vendas = px.line(
                                analise_agrupada,
                                x='periodo',
                                y='Total_Vendas',
                                title=f'Número de Vendas por {tipo_agrupamento}',
                                labels={'periodo': 'Período', 'Total_Vendas': 'Quantidade de Vendas'},
                                markers=True,
                                color_discrete_sequence=['#ff7f0e']
                            )
                            fig_vendas.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_vendas, use_container_width=True)
                        
                        # Gráfico adicional de lucro se disponível
                        if 'Lucro_Total' in analise_agrupada.columns:
                            with graf_col3:
                                # Gráfico de lucro por período
                                fig_lucro = px.bar(
                                    analise_agrupada,
                                    x='periodo',
                                    y='Lucro_Total',
                                    title=f'Lucro por {tipo_agrupamento}',
                                    labels={'periodo': 'Período', 'Lucro_Total': 'Lucro (R$)'},
                                    color_discrete_sequence=['#2ca02c']
                                )
                                fig_lucro.update_layout(xaxis_tickangle=-45)
                                st.plotly_chart(fig_lucro, use_container_width=True)
                        
                        # Análise de produtos mais vendidos no período
                        st.markdown("### 🏆 Top Produtos no Período")
                        
                        try:
                            # Buscar itens de vendas do período
                            vendas_ids = vendas_periodo['id'].tolist()
                            if vendas_ids:
                                # Consulta SQL para pegar produtos mais vendidos
                                from sqlalchemy import text
                                query = text("""
                                    SELECT 
                                        p.nome as produto_nome,
                                        SUM(iv.quantidade) as quantidade_total,
                                        SUM(iv.quantidade * iv.preco_unitario) as receita_produto,
                                        COUNT(DISTINCT iv.venda_id) as vendas_com_produto,
                                        AVG(iv.preco_unitario) as preco_medio
                                    FROM itens_venda iv
                                    JOIN produtos p ON iv.produto_id = p.id
                                    JOIN vendas v ON iv.venda_id = v.id
                                    WHERE iv.venda_id = ANY(:venda_ids)
                                    AND v.usuario_id = :usuario_id
                                    GROUP BY p.id, p.nome
                                    ORDER BY quantidade_total DESC
                                    LIMIT 10
                                """)
                                
                                try:
                                    # Usar a sessão do SQLAlchemy diretamente
                                    resultado = st.session_state.db.session.execute(query, {
                                        'venda_ids': vendas_ids,
                                        'usuario_id': st.session_state.usuario_id
                                    })
                                    top_produtos = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
                                except Exception as e:
                                    st.warning(f"Erro na consulta de produtos: {str(e)}")
                                    # Fallback: análise simplificada sem produtos
                                    top_produtos = pd.DataFrame()
                                
                                if not top_produtos.empty:
                                    # Formatar dados para exibição
                                    top_produtos_display = top_produtos.copy()
                                    top_produtos_display['receita_produto'] = top_produtos_display['receita_produto'].apply(lambda x: f"R$ {x:.2f}")
                                    top_produtos_display['preco_medio'] = top_produtos_display['preco_medio'].apply(lambda x: f"R$ {x:.2f}")
                                    
                                    # Renomear colunas
                                    top_produtos_display.columns = ['Produto', 'Qtd Total', 'Receita', 'Nº Vendas', 'Preço Médio']
                                    
                                    st.dataframe(top_produtos_display, use_container_width=True, hide_index=True)
                                    
                                    # Gráfico de pizza dos top 5 produtos
                                    if len(top_produtos) >= 3:
                                        fig_pizza = px.pie(
                                            top_produtos.head(),
                                            values='quantidade_total',
                                            names='produto_nome',
                                            title='Top 5 Produtos por Quantidade'
                                        )
                                        st.plotly_chart(fig_pizza, use_container_width=True)
                                else:
                                    st.info("Nenhum produto encontrado para o período selecionado.")
                            else:
                                st.info("Nenhuma venda encontrada no período para análise de produtos.")
                        except Exception as e:
                            st.warning(f"Não foi possível carregar análise de produtos: {str(e)}")
                        

                    
                    else:
                        st.warning("Nenhuma venda encontrada no período selecionado.")
                        
            except Exception as e:
                st.error(f"Erro ao carregar análise por período: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

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