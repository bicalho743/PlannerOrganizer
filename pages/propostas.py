import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import uuid

def show():
    st.title("PROPOSTAS")
    
    # Verificar se temos uma conexão com o banco de dados
    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return
    
    # Criar abas para organizar o conteúdo
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Nova Proposta", 
        "Propostas em Aberto", 
        "Em Execução", 
        "Finalizadas", 
        "Todas as Propostas"
    ])
    
    # ABA 1: NOVA PROPOSTA
    with tab1:
        st.header("Nova Proposta")
        
        # Obter a lista de clientes do banco de dados
        try:
            clientes = st.session_state.db.get_clientes()
            if clientes.empty:
                st.warning("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
            else:
                # Formulário para cadastro de nova proposta
                with st.form(key="nova_proposta_form"):
                    # Cliente (seleção a partir do módulo de cadastro)
                    clientes_lista = clientes['nome'].tolist()
                    cliente = st.selectbox("Cliente:", clientes_lista)
                    
                    # Descrição do serviço
                    descricao = st.text_area("Descrição do serviço:", height=100)
                    
                    # Valor do serviço
                    valor = st.number_input("Valor do serviço (R$):", min_value=0.0, format="%.2f")
                    
                    # Prazo estimado (em dias)
                    prazo = st.number_input("Prazo estimado (dias):", min_value=1, value=15)
                    
                    # Data de início prevista
                    data_inicio = st.date_input("Data de início prevista:", datetime.now().date())
                    
                    # Calcular data de término com base no prazo
                    data_fim = data_inicio + timedelta(days=prazo)
                    st.info(f"Data de término prevista: {data_fim.strftime('%d/%m/%Y')}")
                    
                    # Tipo de proposta
                    tipo_proposta = st.selectbox(
                        "Tipo de Proposta:",
                        ["Organização", "Consultoria", "Acompanhamento", "Projeto", "Outro"]
                    )
                    
                    # Botão para salvar
                    submitted = st.form_submit_button("Salvar Proposta")
                    
                    if submitted:
                        try:
                            # Obter o ID do cliente selecionado
                            cliente_id = clientes[clientes['nome'] == cliente]['id'].iloc[0]
                            
                            # Criar nova proposta
                            novo_numero = st.session_state.db.add_proposta(
                                cliente_id=cliente_id,
                                descricao=descricao,
                                valor=valor,
                                status="Em elaboração",  # Status inicial
                                tipo_proposta=tipo_proposta,
                                data_inicio=data_inicio,
                                data_fim=data_fim,
                                previsao_dias=prazo,  # Prazo em dias (número)
                                prazo_entrega=data_inicio  # Usamos data_inicio como base
                            )
                            
                            if novo_numero:
                                st.success(f"Proposta #{novo_numero} criada com sucesso!")
                                
                                # Aguardar um momento para a mensagem ser exibida
                                time.sleep(1)
                                st.rerun()  # Recarregar a página para limpar o formulário
                            else:
                                st.error("Erro ao salvar proposta.")
                        except Exception as e:
                            st.error(f"Erro ao salvar proposta: {str(e)}")
        except Exception as e:
            st.error(f"Erro ao carregar clientes: {str(e)}")
    
    # Carregar todas as propostas uma única vez para usar em várias abas
    try:
        propostas = st.session_state.db.get_propostas()
        # Garantir que clientes esteja definido, mesmo se o primeiro bloco falhar
        if not 'clientes' in locals() or clientes is None or clientes.empty:
            clientes = st.session_state.db.get_clientes()
        
        # Mesclar propostas com clientes para exibir nome do cliente
        if not propostas.empty and not clientes.empty:
            propostas_com_clientes = propostas.merge(
                clientes[['id', 'nome']],
                left_on='cliente_id',
                right_on='id',
                suffixes=('', '_cliente'),
                how='left'
            )
        else:
            propostas_com_clientes = propostas
            
        # ABA 2: PROPOSTAS EM ABERTO
        with tab2:
            st.header("Propostas em Aberto")
            
            if not propostas.empty:
                # Filtrar propostas em elaboração ou aprovadas
                propostas_em_aberto = propostas_com_clientes[
                    propostas_com_clientes['status'].isin(['Em elaboração', 'Aprovada'])
                ]
                
                if not propostas_em_aberto.empty:
                    # Preparar DataFrame para exibição
                    df_em_aberto = pd.DataFrame()
                    # Removido o ID da tabela para mostrar apenas o número da proposta
                    df_em_aberto['Número'] = propostas_em_aberto['numero']
                    df_em_aberto['Cliente'] = propostas_em_aberto['nome']
                    df_em_aberto['Descrição'] = propostas_em_aberto['descricao']
                    df_em_aberto['Valor (R$)'] = propostas_em_aberto['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    df_em_aberto['Status'] = propostas_em_aberto['status']
                    df_em_aberto['Tipo'] = propostas_em_aberto['tipo_proposta']
                    
                    # Formatar datas para exibição
                    df_em_aberto['Início'] = propostas_em_aberto['data_inicio'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    df_em_aberto['Prazo (dias)'] = propostas_em_aberto['previsao_dias']
                    
                    # Exibir tabela
                    st.dataframe(df_em_aberto)
                    
                    # Ações para propostas em aberto
                    st.subheader("Ações")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        proposta_id = st.number_input("ID da Proposta", min_value=1, step=1, key="id_proposta_em_aberto")
                    
                    with col2:
                        # Filtrar a proposta selecionada para verificar o status
                        proposta_selecionada = propostas_em_aberto[propostas_em_aberto['id'] == proposta_id]
                        if not proposta_selecionada.empty:
                            status_atual = proposta_selecionada.iloc[0]['status']
                            st.write(f"Status atual: {status_atual}")
                            
                            # Botões de ação baseados no status
                            if status_atual == "Em elaboração":
                                col_aprove, col_reject = st.columns(2)
                                
                                with col_aprove:
                                    if st.button("Aprovar Proposta", key="aprovar_proposta_em_aberto"):
                                        # Atualizar o status da proposta para "Aprovada"
                                        data_aprovacao = datetime.now().date()
                                        sucesso = st.session_state.db.update_proposta_status(
                                            proposta_id=proposta_id,
                                            novo_status="Aprovada",
                                            data_aprovacao=data_aprovacao
                                        )
                                        
                                        if sucesso:
                                            st.success(f"Proposta {proposta_id} aprovada com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Erro ao aprovar proposta {proposta_id}")
                                
                                with col_reject:
                                    if st.button("Recusar Proposta", key="recusar_proposta_em_aberto"):
                                        # Atualizar o status da proposta para "Recusada"
                                        data_recusa = datetime.now().date()
                                        sucesso = st.session_state.db.update_proposta_status(
                                            proposta_id=proposta_id,
                                            novo_status="Recusada",
                                            data_recusa=data_recusa
                                        )
                                        
                                        if sucesso:
                                            st.success(f"Proposta {proposta_id} recusada.")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Erro ao recusar proposta {proposta_id}")
                            
                            elif status_atual == "Aprovada":
                                if st.button("Iniciar Execução", key="iniciar_execucao"):
                                    # Atualizar o status da proposta para "Em execução"
                                    data_inicio_execucao = datetime.now().date()
                                    sucesso = st.session_state.db.atualizar_proposta(
                                        proposta_id=proposta_id,
                                        status="Em execução",
                                        data_inicio_execucao=data_inicio_execucao,
                                        status_execucao="Iniciada"
                                    )
                                    
                                    if sucesso:
                                        st.success(f"Proposta {proposta_id} iniciada com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"Erro ao iniciar execução da proposta {proposta_id}")
                            
                            # Botões presentes independente do status
                            col_edit, col_delete = st.columns(2)
                            
                            with col_edit:
                                if st.button("Editar Proposta", key="editar_proposta_em_aberto"):
                                    st.session_state.proposta_para_editar = proposta_id
                                    st.session_state.modo_edicao_proposta = True
                                    st.rerun()
                            
                            with col_delete:
                                if st.button("Excluir Proposta", key="excluir_proposta_em_aberto"):
                                    if 'confirmar_exclusao' not in st.session_state:
                                        st.session_state.confirmar_exclusao = False
                                        st.session_state.proposta_para_excluir = proposta_id
                                    
                                    st.session_state.confirmar_exclusao = True
                                    st.session_state.proposta_para_excluir = proposta_id
                                    st.warning(f"Tem certeza que deseja excluir a proposta #{proposta_selecionada.iloc[0]['numero']}?")
                                    
                                    confirm_col1, confirm_col2 = st.columns(2)
                                    with confirm_col1:
                                        if st.button("Sim, excluir", key="confirmar_exclusao"):
                                            # Excluir proposta
                                            sucesso = st.session_state.db.excluir_proposta(proposta_id)
                                            
                                            if sucesso:
                                                st.success(f"Proposta excluída com sucesso!")
                                                # Limpar estado
                                                if 'confirmar_exclusao' in st.session_state:
                                                    del st.session_state.confirmar_exclusao
                                                if 'proposta_para_excluir' in st.session_state:
                                                    del st.session_state.proposta_para_excluir
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(f"Erro ao excluir proposta {proposta_id}")
                                    
                                    with confirm_col2:
                                        if st.button("Cancelar", key="cancelar_exclusao"):
                                            # Limpar estado
                                            if 'confirmar_exclusao' in st.session_state:
                                                del st.session_state.confirmar_exclusao
                                            if 'proposta_para_excluir' in st.session_state:
                                                del st.session_state.proposta_para_excluir
                                            st.rerun()
                        else:
                            st.warning("Selecione uma proposta válida.")
                    
                    # Formulário de edição condicional
                    if 'modo_edicao_proposta' in st.session_state and st.session_state.modo_edicao_proposta:
                        if 'proposta_para_editar' in st.session_state:
                            proposta_edit_id = st.session_state.proposta_para_editar
                            proposta_edit = propostas_com_clientes[propostas_com_clientes['id'] == proposta_edit_id]
                            
                            if not proposta_edit.empty:
                                st.subheader(f"Editar Proposta #{proposta_edit.iloc[0]['numero']}")
                                
                                with st.form(key="editar_proposta_form"):
                                    # Cliente (não editável)
                                    st.text_input("Cliente:", value=proposta_edit.iloc[0]['nome'], disabled=True)
                                    
                                    # Campos editáveis
                                    descricao_edit = st.text_area(
                                        "Descrição:", 
                                        value=proposta_edit.iloc[0]['descricao'], 
                                        height=100
                                    )
                                    
                                    valor_edit = st.number_input(
                                        "Valor (R$):",
                                        value=float(proposta_edit.iloc[0]['valor']),
                                        format="%.2f"
                                    )
                                    
                                    tipo_proposta_edit = st.selectbox(
                                        "Tipo de Proposta:",
                                        ["Organização", "Consultoria", "Acompanhamento", "Projeto", "Outro"],
                                        index=["Organização", "Consultoria", "Acompanhamento", "Projeto", "Outro"].index(
                                            proposta_edit.iloc[0]['tipo_proposta']) if pd.notna(proposta_edit.iloc[0]['tipo_proposta']) else 0
                                    )
                                    
                                    # Data de início e prazo
                                    data_inicio_edit = st.date_input(
                                        "Data de início:",
                                        proposta_edit.iloc[0]['data_inicio'] if pd.notna(proposta_edit.iloc[0]['data_inicio']) else datetime.now().date()
                                    )
                                    
                                    prazo_edit = st.number_input(
                                        "Prazo (dias):",
                                        value=int(proposta_edit.iloc[0]['previsao_dias']) if pd.notna(proposta_edit.iloc[0]['previsao_dias']) else 15,
                                        min_value=1
                                    )
                                    
                                    # Calcular nova data de fim
                                    data_fim_edit = data_inicio_edit + timedelta(days=prazo_edit)
                                    
                                    # Botões de ação
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        cancelar = st.form_submit_button("Cancelar")
                                    with col2:
                                        salvar = st.form_submit_button("Salvar Alterações")
                                    
                                    if cancelar:
                                        st.session_state.modo_edicao_proposta = False
                                        st.rerun()
                                    
                                    if salvar:
                                        try:
                                            sucesso = st.session_state.db.atualizar_proposta(
                                                proposta_id=proposta_edit_id,
                                                descricao=descricao_edit,
                                                valor=valor_edit,
                                                tipo_proposta=tipo_proposta_edit,
                                                data_inicio=data_inicio_edit,
                                                data_fim=data_fim_edit,
                                                previsao_dias=prazo_edit
                                            )
                                            
                                            if sucesso:
                                                st.success("Proposta atualizada com sucesso!")
                                                st.session_state.modo_edicao_proposta = False
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("Erro ao atualizar proposta.")
                                        except Exception as e:
                                            st.error(f"Erro ao atualizar proposta: {str(e)}")
                else:
                    st.info("Não há propostas em aberto no momento.")
            else:
                st.info("Não há propostas cadastradas no sistema.")
        
        # ABA 3: EM EXECUÇÃO
        with tab3:
            st.header("Propostas em Execução")
            
            if not propostas.empty:
                # Filtrar propostas em execução
                propostas_em_execucao = propostas_com_clientes[
                    propostas_com_clientes['status'] == 'Em execução'
                ]
                
                if not propostas_em_execucao.empty:
                    # Preparar DataFrame para exibição
                    df_execucao = pd.DataFrame()
                    # Removido o ID da tabela para mostrar apenas o número da proposta
                    df_execucao['Número'] = propostas_em_execucao['numero']
                    df_execucao['Cliente'] = propostas_em_execucao['nome']
                    df_execucao['Descrição'] = propostas_em_execucao['descricao']
                    df_execucao['Valor (R$)'] = propostas_em_execucao['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    df_execucao['Status Execução'] = propostas_em_execucao['status_execucao']
                    df_execucao['Início Execução'] = propostas_em_execucao['data_inicio_execucao'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Exibir tabela
                    st.dataframe(df_execucao)
                    
                    # Ações para propostas em execução
                    st.subheader("Gerenciar Execução")
                    
                    proposta_exec_id = st.number_input("ID da Proposta", min_value=1, step=1, key="id_proposta_execucao")
                    
                    # Verificar se a proposta existe
                    proposta_exec = propostas_em_execucao[propostas_em_execucao['id'] == proposta_exec_id]
                    
                    if not proposta_exec.empty:
                        st.write(f"Proposta #{proposta_exec.iloc[0]['numero']} - {proposta_exec.iloc[0]['descricao']}")
                        
                        # Criar abas para gerenciar diferentes aspectos da execução
                        exec_tab1, exec_tab2, exec_tab3, exec_tab4, exec_tab5 = st.tabs([
                            "Andamento", "Produtos", "Fornecedores", "Assistentes", "Finalizar"
                        ])
                        
                        with exec_tab1:
                            st.subheader("Andamento")
                            
                            # Formulário para registrar andamento
                            with st.form(key=f"andamento_form_{proposta_exec_id}"):
                                status_andamento = st.selectbox(
                                    "Status:",
                                    ["Em andamento", "Aguardando cliente", "Aguardando material", "Pausa", "Etapa concluída"]
                                )
                                
                                comodo = st.text_input("Cômodo/Área:", placeholder="Ex: Cozinha, Escritório, etc.")
                                
                                observacao = st.text_area("Observações:", height=100)
                                
                                if st.form_submit_button("Registrar Andamento"):
                                    try:
                                        andamento_id = st.session_state.db.add_andamento_proposta(
                                            proposta_id=proposta_exec_id,
                                            status=status_andamento,
                                            observacao=observacao,
                                            comodo=comodo
                                        )
                                        
                                        if andamento_id:
                                            st.success("Andamento registrado com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("Erro ao registrar andamento.")
                                    except Exception as e:
                                        st.error(f"Erro ao registrar andamento: {str(e)}")
                            
                            # Mostrar histórico de andamentos
                            try:
                                andamentos = st.session_state.db.get_andamentos_proposta(proposta_exec_id)
                                
                                if not andamentos.empty:
                                    st.write("Histórico de Andamento:")
                                    
                                    # Formatar para exibição
                                    andamentos['Data'] = andamentos['data'].apply(
                                        lambda x: x.strftime('%d/%m/%Y %H:%M') if pd.notna(x) else ''
                                    )
                                    
                                    st.dataframe(
                                        andamentos[['Data', 'status', 'comodo', 'observacao']].rename(
                                            columns={
                                                'status': 'Status',
                                                'comodo': 'Cômodo/Área',
                                                'observacao': 'Observações'
                                            }
                                        )
                                    )
                                else:
                                    st.info("Nenhum registro de andamento para esta proposta.")
                            except Exception as e:
                                st.error(f"Erro ao carregar andamentos: {str(e)}")
                        
                        with exec_tab2:
                            st.subheader("Produtos")
                            
                            # Formulário para adicionar produtos
                            with st.form(key=f"produto_form_{proposta_exec_id}"):
                                nome_produto = st.text_input("Nome do produto:")
                                descricao_produto = st.text_area("Descrição:", height=70)
                                valor_produto = st.number_input("Valor unitário (R$):", min_value=0.0, format="%.2f")
                                quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                                comodo_produto = st.text_input("Cômodo/Área:")
                                
                                if st.form_submit_button("Adicionar Produto"):
                                    try:
                                        produto_id = st.session_state.db.add_produto_organizador(
                                            proposta_id=proposta_exec_id,
                                            nome=nome_produto,
                                            descricao=descricao_produto,
                                            valor=valor_produto,
                                            quantidade=quantidade,
                                            comodo=comodo_produto
                                        )
                                        
                                        if produto_id:
                                            st.success("Produto adicionado com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("Erro ao adicionar produto.")
                                    except Exception as e:
                                        st.error(f"Erro ao adicionar produto: {str(e)}")
                            
                            # Mostrar produtos adicionados
                            try:
                                produtos = st.session_state.db.get_produtos_organizadores(proposta_exec_id)
                                
                                if not produtos.empty:
                                    st.write("Produtos da Proposta:")
                                    
                                    # Calcular valor total
                                    produtos['valor_total'] = produtos['valor'] * produtos['quantidade']
                                    
                                    # Formatar para exibição
                                    df_produtos = pd.DataFrame()
                                    df_produtos['Nome'] = produtos['nome']
                                    df_produtos['Descrição'] = produtos['descricao']
                                    df_produtos['Valor Unit.'] = produtos['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                    df_produtos['Quantidade'] = produtos['quantidade']
                                    df_produtos['Valor Total'] = produtos['valor_total'].apply(lambda x: f"R$ {float(x):.2f}")
                                    df_produtos['Cômodo'] = produtos['comodo']
                                    
                                    st.dataframe(df_produtos)
                                    
                                    # Mostrar valor total da proposta
                                    valor_total_produtos = produtos['valor_total'].sum()
                                    st.info(f"Valor Total dos Produtos: R$ {valor_total_produtos:.2f}")
                                else:
                                    st.info("Nenhum produto adicionado a esta proposta.")
                            except Exception as e:
                                st.error(f"Erro ao carregar produtos: {str(e)}")
                                
                        with exec_tab3:
                            st.subheader("Fornecedores")
                            
                            # 1. Formulário para adicionar novo fornecedor
                            st.markdown("### Adicionar Novo Fornecedor")
                            
                            # Obter lista de fornecedores cadastrados
                            try:
                                fornecedores = st.session_state.db.get_fornecedores()
                                
                                if not fornecedores.empty:
                                    # Formulário para adicionar fornecedor à proposta
                                    with st.form(key=f"fornecedor_form_{proposta_exec_id}"):
                                        fornecedor_id = st.selectbox(
                                            "Selecione o fornecedor:",
                                            fornecedores['id'].tolist(),
                                            format_func=lambda x: fornecedores[fornecedores['id']==x]['descricao'].iloc[0]
                                        )
                                        
                                        # Obter o percentual de comissão padrão do fornecedor selecionado (se houver)
                                        percentual_comissao = 0.0
                                        try:
                                            fornecedor_selecionado = fornecedores[fornecedores['id'] == fornecedor_id]
                                            if not fornecedor_selecionado.empty and 'percentual_comissao' in fornecedor_selecionado.columns:
                                                percentual_comissao = fornecedor_selecionado['percentual_comissao'].iloc[0] or 0.0
                                        except (KeyError, IndexError):
                                            pass
                                        
                                        valor_fornecimento = st.number_input("Valor do fornecimento (R$):", min_value=0.0, format="%.2f")
                                        
                                        # Exibir o percentual de comissão configurado no cadastro do fornecedor
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.info(f"Percentual de comissão configurado para este fornecedor: {percentual_comissao:.2f}%")
                                            st.caption("O percentual de comissão é definido no cadastro do fornecedor")
                                        
                                        with col2:
                                            if percentual_comissao > 0:
                                                valor_comissao = valor_fornecimento * (percentual_comissao / 100)
                                                st.info(f"Comissão: R$ {valor_comissao:.2f}")
                                        
                                        observacao_fornecimento = st.text_area("Observações:", height=70)
                                        
                                        if st.form_submit_button("Adicionar Fornecedor"):
                                            try:
                                                # Adicionar fornecedor à proposta usando a nova função
                                                resultado = st.session_state.db.add_fornecedor_proposta(
                                                    proposta_id=proposta_exec_id,
                                                    fornecedor_id=fornecedor_id,
                                                    valor=valor_fornecimento,
                                                    observacoes=observacao_fornecimento,
                                                    percentual_comissao=percentual_comissao if percentual_comissao > 0 else None
                                                )
                                                
                                                if resultado and resultado.get("acrescimo_id"):
                                                    mensagem = f"Fornecedor adicionado com sucesso à proposta!"
                                                    
                                                    # Se gerou comissão, adicionar essa informação à mensagem
                                                    if resultado.get("comissao_gerada", False):
                                                        valor_comissao = resultado.get("valor_comissao", 0)
                                                        mensagem += f"\nComissão de R$ {valor_comissao:.2f} registrada automaticamente."
                                                    
                                                    st.success(mensagem)
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao adicionar fornecedor.")
                                            except Exception as e:
                                                st.error(f"Erro ao adicionar fornecedor: {str(e)}")
                                else:
                                    st.warning("Nenhum fornecedor cadastrado no sistema.")
                                    st.write("Vá para a seção de Cadastros para adicionar fornecedores.")
                                    
                                # 2. Exibir fornecedores já adicionados à proposta
                                st.markdown("---")
                                st.markdown("### Fornecedores Adicionados")
                                
                                fornecedores_atuais = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "FORNECEDOR")
                                
                                if not fornecedores_atuais.empty:
                                    # Criar tabela para exibição dos fornecedores
                                    for idx, row in fornecedores_atuais.iterrows():
                                        with st.container():
                                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                                            
                                            with col1:
                                                st.markdown(f"**{row['fornecedor']}**")
                                                st.caption(row['descricao'])
                                            
                                            with col2:
                                                st.markdown(f"**R$ {float(row['valor']):.2f}**")
                                            
                                            with col3:
                                                if st.button("Editar", key=f"edit_forn_{row['id']}"):
                                                    # Armazenar ID do acréscimo sendo editado
                                                    st.session_state[f"edit_forn_id_{proposta_exec_id}"] = row['id']
                                                    st.rerun()
                                            
                                            with col4:
                                                if st.button("Excluir", key=f"del_forn_{row['id']}"):
                                                    try:
                                                        # Excluir acréscimo
                                                        sucesso = st.session_state.db.excluir_acrescimo(row['id'])
                                                        if sucesso:
                                                            st.success("Fornecedor removido com sucesso!")
                                                            time.sleep(1)
                                                            st.rerun()
                                                        else:
                                                            st.error("Erro ao remover fornecedor.")
                                                    except Exception as e:
                                                        st.error(f"Erro ao remover fornecedor: {str(e)}")
                                            
                                            st.divider()
                                else:
                                    st.info("Nenhum fornecedor adicionado a esta proposta.")
                                    
                                # 3. Formulário de edição se algum item foi selecionado
                                edit_forn_id = st.session_state.get(f"edit_forn_id_{proposta_exec_id}", None)
                                if edit_forn_id:
                                    st.markdown("### Editar Fornecedor")
                                    
                                    # Buscar dados do acréscimo
                                    acrescimo = st.session_state.db.get_acrescimo_by_id(edit_forn_id)
                                    if not acrescimo.empty:
                                        with st.form(key=f"edit_forn_form_{edit_forn_id}"):
                                            # Preparar valores atuais para edição
                                            fornecedor_nome = acrescimo.iloc[0]['fornecedor']
                                            acrescimo_valor = acrescimo.iloc[0]['valor']
                                            acrescimo_descricao = acrescimo.iloc[0]['descricao']
                                            
                                            st.write(f"Fornecedor: **{fornecedor_nome}**")
                                            
                                            valor_edit = st.number_input(
                                                "Valor (R$):", 
                                                min_value=0.0, 
                                                value=float(acrescimo_valor), 
                                                format="%.2f"
                                            )
                                            
                                            descricao_edit = st.text_area(
                                                "Descrição/Observações:", 
                                                value=acrescimo_descricao, 
                                                height=70
                                            )
                                            
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                if st.form_submit_button("Salvar Alterações"):
                                                    try:
                                                        # Atualizar acréscimo
                                                        sucesso = st.session_state.db.atualizar_acrescimo(
                                                            acrescimo_id=edit_forn_id,
                                                            valor=valor_edit,
                                                            descricao=descricao_edit
                                                        )
                                                        
                                                        if sucesso:
                                                            st.success("Fornecedor atualizado com sucesso!")
                                                            # Limpar estado de edição
                                                            del st.session_state[f"edit_forn_id_{proposta_exec_id}"]
                                                            time.sleep(1)
                                                            st.rerun()
                                                        else:
                                                            st.error("Erro ao atualizar fornecedor.")
                                                    except Exception as e:
                                                        st.error(f"Erro ao atualizar fornecedor: {str(e)}")
                                            
                                            with col2:
                                                if st.form_submit_button("Cancelar"):
                                                    # Limpar estado de edição
                                                    del st.session_state[f"edit_forn_id_{proposta_exec_id}"]
                                                    st.rerun()
                                            st.success("Fornecedor adicionado com sucesso!")
                                            st.info("Esta funcionalidade será implementada em breve.")
                                else:
                                    st.warning("Nenhum fornecedor cadastrado no sistema.")
                                    st.write("Vá para a seção de Cadastros para adicionar fornecedores.")
                            except Exception as e:
                                st.error(f"Erro ao carregar fornecedores: {str(e)}")
                                
                        with exec_tab4:
                            st.subheader("Assistentes")
                            
                            # 1. Formulário para adicionar novo assistente
                            st.markdown("### Adicionar Novo Assistente")
                            
                            # Obter lista de assistentes cadastrados
                            try:
                                assistentes = st.session_state.db.get_assistentes()
                                
                                if not assistentes.empty:
                                    # Formulário para adicionar assistente à proposta
                                    with st.form(key=f"assistente_form_{proposta_exec_id}"):
                                        assistente_id = st.selectbox(
                                            "Selecione o assistente:",
                                            assistentes['id'].tolist(),
                                            format_func=lambda x: assistentes[assistentes['id']==x]['nome'].iloc[0]
                                        )
                                        
                                        valor_assistente = st.number_input("Valor do serviço (R$):", min_value=0.0, format="%.2f")
                                        observacao_assistente = st.text_area("Observações:", height=70)
                                        
                                        if st.form_submit_button("Adicionar Assistente"):
                                            try:
                                                # Adicionar assistente à proposta
                                                acrescimo_id = st.session_state.db.add_acrescimo_proposta(
                                                    proposta_id=proposta_exec_id,
                                                    tipo="ASSISTENTE",
                                                    assistente_id=assistente_id,
                                                    valor=valor_assistente,
                                                    descricao=observacao_assistente
                                                )
                                                
                                                if acrescimo_id:
                                                    st.success("Assistente adicionado com sucesso à proposta!")
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao adicionar assistente.")
                                            except Exception as e:
                                                st.error(f"Erro ao adicionar assistente: {str(e)}")
                                else:
                                    st.warning("Nenhum assistente cadastrado no sistema.")
                                    st.write("Vá para a seção de Cadastros para adicionar assistentes.")
                                
                                # 2. Exibir assistentes já adicionados à proposta
                                st.markdown("---")
                                st.markdown("### Assistentes Adicionados")
                                
                                assistentes_atuais = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "ASSISTENTE")
                                
                                if not assistentes_atuais.empty:
                                    # Criar tabela para exibição dos assistentes
                                    for idx, row in assistentes_atuais.iterrows():
                                        with st.container():
                                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                                            
                                            with col1:
                                                st.markdown(f"**{row['assistente']}**")
                                                st.caption(row['descricao'])
                                            
                                            with col2:
                                                st.markdown(f"**R$ {float(row['valor']):.2f}**")
                                            
                                            with col3:
                                                if st.button("Editar", key=f"edit_asst_{row['id']}"):
                                                    # Armazenar ID do acréscimo sendo editado
                                                    st.session_state[f"edit_asst_id_{proposta_exec_id}"] = row['id']
                                                    st.rerun()
                                            
                                            with col4:
                                                if st.button("Excluir", key=f"del_asst_{row['id']}"):
                                                    try:
                                                        # Excluir acréscimo
                                                        sucesso = st.session_state.db.excluir_acrescimo(row['id'])
                                                        if sucesso:
                                                            st.success("Assistente removido com sucesso!")
                                                            time.sleep(1)
                                                            st.rerun()
                                                        else:
                                                            st.error("Erro ao remover assistente.")
                                                    except Exception as e:
                                                        st.error(f"Erro ao remover assistente: {str(e)}")
                                            
                                            st.divider()
                                else:
                                    st.info("Nenhum assistente adicionado a esta proposta.")
                                    
                                # 3. Formulário de edição se algum item foi selecionado
                                edit_asst_id = st.session_state.get(f"edit_asst_id_{proposta_exec_id}", None)
                                if edit_asst_id:
                                    st.markdown("### Editar Assistente")
                                    
                                    # Buscar dados do acréscimo
                                    acrescimo = st.session_state.db.get_acrescimo_by_id(edit_asst_id)
                                    if not acrescimo.empty:
                                        with st.form(key=f"edit_asst_form_{edit_asst_id}"):
                                            # Preparar valores atuais para edição
                                            assistente_nome = acrescimo.iloc[0]['assistente']
                                            acrescimo_valor = acrescimo.iloc[0]['valor']
                                            acrescimo_descricao = acrescimo.iloc[0]['descricao']
                                            
                                            st.write(f"Assistente: **{assistente_nome}**")
                                            
                                            valor_edit = st.number_input(
                                                "Valor (R$):", 
                                                min_value=0.0, 
                                                value=float(acrescimo_valor), 
                                                format="%.2f"
                                            )
                                            
                                            descricao_edit = st.text_area(
                                                "Descrição/Observações:", 
                                                value=acrescimo_descricao, 
                                                height=70
                                            )
                                            
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                if st.form_submit_button("Salvar Alterações"):
                                                    try:
                                                        # Atualizar acréscimo
                                                        sucesso = st.session_state.db.atualizar_acrescimo(
                                                            acrescimo_id=edit_asst_id,
                                                            valor=valor_edit,
                                                            descricao=descricao_edit
                                                        )
                                                        
                                                        if sucesso:
                                                            st.success("Assistente atualizado com sucesso!")
                                                            # Limpar estado de edição
                                                            del st.session_state[f"edit_asst_id_{proposta_exec_id}"]
                                                            time.sleep(1)
                                                            st.rerun()
                                                        else:
                                                            st.error("Erro ao atualizar assistente.")
                                                    except Exception as e:
                                                        st.error(f"Erro ao atualizar assistente: {str(e)}")
                                            
                                            with col2:
                                                if st.form_submit_button("Cancelar"):
                                                    # Limpar estado de edição
                                                    del st.session_state[f"edit_asst_id_{proposta_exec_id}"]
                                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao carregar assistentes: {str(e)}")
                                
                        with exec_tab5:
                            st.subheader("Finalizar Proposta")
                            
                            if st.button("Marcar como Concluída", key=f"finalizar_{proposta_exec_id}"):
                                try:
                                    data_conclusao = datetime.now().date()
                                    
                                    sucesso = st.session_state.db.atualizar_proposta(
                                        proposta_id=proposta_exec_id,
                                        status="Concluída",
                                        status_execucao="Finalizada"
                                    )
                                    
                                    if sucesso:
                                        st.success(f"Proposta {proposta_exec_id} marcada como concluída!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Erro ao finalizar proposta.")
                                except Exception as e:
                                    st.error(f"Erro ao finalizar proposta: {str(e)}")
                    else:
                        st.warning("Selecione uma proposta válida em execução.")
                else:
                    st.info("Não há propostas em execução no momento.")
            else:
                st.info("Não há propostas cadastradas no sistema.")
        
        # ABA 4: FINALIZADAS
        with tab4:
            st.header("Propostas Finalizadas")
            
            if not propostas.empty:
                # Filtrar propostas concluídas
                propostas_finalizadas = propostas_com_clientes[
                    propostas_com_clientes['status'] == 'Concluída'
                ]
                
                if not propostas_finalizadas.empty:
                    # Preparar DataFrame para exibição
                    df_finalizadas = pd.DataFrame()
                    # Removido o ID da tabela para mostrar apenas o número da proposta
                    df_finalizadas['Número'] = propostas_finalizadas['numero']
                    df_finalizadas['Cliente'] = propostas_finalizadas['nome']
                    df_finalizadas['Descrição'] = propostas_finalizadas['descricao']
                    df_finalizadas['Valor (R$)'] = propostas_finalizadas['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    
                    # Formatar datas para exibição
                    df_finalizadas['Início'] = propostas_finalizadas['data_inicio'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    df_finalizadas['Início Execução'] = propostas_finalizadas['data_inicio_execucao'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Exibir tabela
                    st.dataframe(df_finalizadas)
                    
                    # Ações para propostas finalizadas
                    st.subheader("Documentos")
                    
                    proposta_final_id = st.number_input("ID da Proposta", min_value=1, step=1, key="id_proposta_finalizada")
                    
                    # Verificar se a proposta existe
                    proposta_final = propostas_finalizadas[propostas_finalizadas['id'] == proposta_final_id]
                    
                    if not proposta_final.empty:
                        st.write(f"Proposta #{proposta_final.iloc[0]['numero']} - {proposta_final.iloc[0]['descricao']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Gerar Relatório para Cliente", key=f"relatorio_cliente_{proposta_final_id}"):
                                st.info("Gerando relatório para cliente... Esta funcionalidade será implementada em breve.")
                        
                        with col2:
                            if st.button("Gerar Relatório Interno", key=f"relatorio_interno_{proposta_final_id}"):
                                st.info("Gerando relatório interno... Esta funcionalidade será implementada em breve.")
                    else:
                        st.warning("Selecione uma proposta válida finalizada.")
                else:
                    st.info("Não há propostas finalizadas no momento.")
            else:
                st.info("Não há propostas cadastradas no sistema.")
        
        # ABA 5: TODAS AS PROPOSTAS
        with tab5:
            st.header("Todas as Propostas")
            
            if not propostas.empty:
                # Adicionar filtros
                st.subheader("Filtros")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_filter = st.multiselect(
                        "Status:",
                        sorted(propostas['status'].unique().tolist()),
                        default=sorted(propostas['status'].unique().tolist())
                    )
                
                with col2:
                    clientes_filter = st.multiselect(
                        "Cliente:",
                        sorted(propostas_com_clientes['nome'].unique().tolist()),
                        default=sorted(propostas_com_clientes['nome'].unique().tolist())
                    )
                
                with col3:
                    data_filter = st.date_input(
                        "Data a partir de:",
                        datetime.now().date() - timedelta(days=365)
                    )
                
                # Aplicar filtros
                # Convertendo data_filter para timestamp para comparação correta
                data_timestamp = pd.Timestamp(data_filter)
                
                propostas_filtradas = propostas_com_clientes[
                    (propostas_com_clientes['status'].isin(status_filter)) &
                    (propostas_com_clientes['nome'].isin(clientes_filter)) &
                    # Usando .dt.date para comparar apenas a parte da data
                    (propostas_com_clientes['data_proposta'].apply(lambda x: pd.Timestamp(x).date() if pd.notna(x) else pd.NaT) >= data_filter)
                ]
                
                # Preparar DataFrame para exibição
                if not propostas_filtradas.empty:
                    df_todas = pd.DataFrame()
                    # Removido o ID da tabela para mostrar apenas o número da proposta
                    df_todas['Número'] = propostas_filtradas['numero']
                    df_todas['Cliente'] = propostas_filtradas['nome']
                    df_todas['Descrição'] = propostas_filtradas['descricao']
                    df_todas['Valor (R$)'] = propostas_filtradas['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    df_todas['Status'] = propostas_filtradas['status']
                    df_todas['Tipo'] = propostas_filtradas['tipo_proposta']
                    
                    # Formatar datas para exibição
                    df_todas['Data Proposta'] = propostas_filtradas['data_proposta'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Verificar se o campo data_aprovacao existe no dataframe
                    if 'data_aprovacao' in propostas_filtradas.columns:
                        df_todas['Data Aprovação'] = propostas_filtradas['data_aprovacao'].apply(
                            lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                        )
                    else:
                        df_todas['Data Aprovação'] = ''
                        
                    df_todas['Início'] = propostas_filtradas['data_inicio'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Exibir tabela
                    st.dataframe(df_todas)
                    
                    # Mostrar resumo
                    st.subheader("Resumo")
                    
                    # Resumo por status
                    resumo_status = propostas_filtradas.groupby('status').size().reset_index(name='Quantidade')
                    resumo_valor = propostas_filtradas.groupby('status')['valor'].sum().reset_index(name='Valor Total')
                    resumo = resumo_status.merge(resumo_valor, on='status')
                    resumo['Valor Total'] = resumo['Valor Total'].apply(lambda x: f"R$ {float(x):.2f}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("Resumo por Status:")
                        st.dataframe(resumo.rename(columns={'status': 'Status'}))
                    
                    with col2:
                        st.write("Total:")
                        st.metric(
                            "Total de Propostas", 
                            len(propostas_filtradas),
                            delta=f"R$ {float(propostas_filtradas['valor'].sum()):.2f}"
                        )
                else:
                    st.warning("Nenhuma proposta corresponde aos filtros selecionados.")
            else:
                st.info("Não há propostas cadastradas no sistema.")
    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")