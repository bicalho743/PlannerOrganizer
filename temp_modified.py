# Fornecedores - Estrutura modificada
with exec_tab3:
    st.subheader("Fornecedores")
    
    try:
        # 1. Formulário para adicionar novo fornecedor
        st.markdown("### Adicionar Novo Fornecedor")
        
        # Obter lista de fornecedores cadastrados
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
                # Buscar percentual de comissão do fornecedor selecionado
                percentual_comissao = 0.0
                try:
                    fornecedor_selecionado = fornecedores[fornecedores['id']==fornecedor_id]
                    if 'percentual_comissao' in fornecedor_selecionado.columns:
                        percentual_comissao = fornecedor_selecionado['percentual_comissao'].iloc[0] or 0.0
                except:
                    percentual_comissao = 0.0
                
                valor_fornecimento = st.number_input(
                    "Valor do Fornecimento R$:",
                    min_value=0.01,
                    step=10.0,
                    format="%.2f",
                    key=f"valor_fornecimento_{proposta_exec_id}"
                )
                
                if percentual_comissao > 0:
                    st.info(f"Este fornecedor possui {percentual_comissao:.1f}% de comissão configurada.")
                
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
                            if resultado.get("comissao_gerada"):
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
        
        # 2. Se estiver editando, mostrar formulário de edição
        if hasattr(st.session_state, 'editing_fornecedor_id') and st.session_state.editing_fornecedor_id:
            st.markdown("### Editar Fornecedor")
            
            with st.form(key=f"edit_fornecedor_form_{st.session_state.editing_fornecedor_id}"):
                valor_edit = st.number_input(
                    "Valor:", 
                    min_value=0.01, 
                    value=st.session_state.editing_fornecedor_valor,
                    format="%.2f"
                )
                
                descricao_edit = st.text_area(
                    "Descrição:", 
                    value=st.session_state.editing_fornecedor_descricao,
                    height=70
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("Salvar Alterações"):
                        if st.session_state.db.atualizar_acrescimo(
                            st.session_state.editing_fornecedor_id,
                            valor=valor_edit,
                            descricao=descricao_edit
                        ):
                            st.success("Fornecedor atualizado com sucesso!")
                            # Limpar estado de edição
                            st.session_state.editing_fornecedor_id = None
                            st.session_state.editing_fornecedor_valor = None
                            st.session_state.editing_fornecedor_descricao = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar fornecedor.")
                
                with col2:
                    if st.form_submit_button("Cancelar"):
                        # Limpar estado de edição
                        st.session_state.editing_fornecedor_id = None
                        st.session_state.editing_fornecedor_valor = None
                        st.session_state.editing_fornecedor_descricao = None
                        st.rerun()
        
        # 3. Exibir fornecedores já adicionados à proposta
        fornecedores_atuais = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "FORNECEDOR")
        
        if not fornecedores_atuais.empty:
            st.markdown("### Fornecedores Adicionados")
            
            # Criar tabela para exibição dos fornecedores
            for idx, row in fornecedores_atuais.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{row['fornecedor']}**")
                        st.caption(row['descricao'])
                    
                    with col2:
                        st.markdown(f"**R$ {row['valor']:.2f}**")
                    
                    with col3:
                        # Botão para editar
                        if st.button("Editar", key=f"edit_fornecedor_{row['id']}"):
                            st.session_state.editing_fornecedor_id = row['id']
                            st.session_state.editing_fornecedor_valor = row['valor']
                            st.session_state.editing_fornecedor_descricao = row['descricao']
                            st.rerun()
                    
                    with col4:
                        # Botão para excluir
                        if st.button("Excluir", key=f"del_fornecedor_{row['id']}"):
                            if st.session_state.db.excluir_acrescimo(row['id']):
                                st.success("Fornecedor removido com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Erro ao remover fornecedor.")
            
            # Exibir total
            st.info(f"Total de fornecedores: R$ {fornecedores_atuais['valor'].sum():.2f}")
        else:
            st.info("Nenhum fornecedor adicionado a esta proposta.")
    except Exception as e:
        st.error(f"Erro ao carregar informações: {str(e)}")
        st.write("Detalhes do erro:", str(e))

# Assistentes - Estrutura modificada
with exec_tab4:
    st.subheader("Assistentes")
    
    try:
        # 1. Formulário para adicionar novo assistente
        st.markdown("### Adicionar Novo Assistente")
        
        # Obter lista de assistentes cadastrados
        assistentes = st.session_state.db.get_assistentes()
        
        if not assistentes.empty:
            # Formulário para adicionar assistente à proposta
            with st.form(key=f"assistente_form_{proposta_exec_id}"):
                assistente_id = st.selectbox(
                    "Selecione o assistente:",
                    assistentes['id'].tolist(),
                    format_func=lambda x: assistentes[assistentes['id']==x]['nome'].iloc[0]
                )
                
                # Obter o percentual de comissão padrão do assistente selecionado
                percentual_comissao = 0.0
                try:
                    assistente_selecionado = assistentes[assistentes['id']==assistente_id]
                    if 'percentual_comissao' in assistente_selecionado.columns:
                        percentual_comissao = assistente_selecionado['percentual_comissao'].iloc[0] or 0.0
                except:
                    percentual_comissao = 0.0
                
                valor_assistente = st.number_input(
                    "Valor R$:",
                    min_value=0.01,
                    step=10.0,
                    format="%.2f",
                    key=f"valor_assistente_{proposta_exec_id}"
                )
                
                observacao_assistente = st.text_area("Observações:", height=70)
                
                if st.form_submit_button("Adicionar Assistente"):
                    try:
                        resultado = st.session_state.db.add_assistente_proposta(
                            proposta_id=proposta_exec_id,
                            assistente_id=assistente_id,
                            valor=valor_assistente,
                            observacoes=observacao_assistente
                        )
                        
                        if resultado and resultado.get("acrescimo_id"):
                            st.success(f"Assistente adicionado com sucesso à proposta!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Erro ao adicionar assistente.")
                    except Exception as e:
                        st.error(f"Erro ao adicionar assistente: {str(e)}")
        else:
            st.warning("Nenhum assistente cadastrado no sistema.")
            st.write("Vá para a seção de Cadastros para adicionar assistentes.")
        
        # 2. Se estiver editando, mostrar formulário de edição
        if hasattr(st.session_state, 'editing_assistente_id') and st.session_state.editing_assistente_id:
            st.markdown("### Editar Assistente")
            
            with st.form(key=f"edit_assistente_form_{st.session_state.editing_assistente_id}"):
                valor_edit = st.number_input(
                    "Valor:", 
                    min_value=0.01, 
                    value=st.session_state.editing_assistente_valor,
                    format="%.2f"
                )
                
                descricao_edit = st.text_area(
                    "Descrição:", 
                    value=st.session_state.editing_assistente_descricao,
                    height=70
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("Salvar Alterações"):
                        if st.session_state.db.atualizar_acrescimo(
                            st.session_state.editing_assistente_id,
                            valor=valor_edit,
                            descricao=descricao_edit
                        ):
                            st.success("Assistente atualizado com sucesso!")
                            # Limpar estado de edição
                            st.session_state.editing_assistente_id = None
                            st.session_state.editing_assistente_valor = None
                            st.session_state.editing_assistente_descricao = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar assistente.")
                
                with col2:
                    if st.form_submit_button("Cancelar"):
                        # Limpar estado de edição
                        st.session_state.editing_assistente_id = None
                        st.session_state.editing_assistente_valor = None
                        st.session_state.editing_assistente_descricao = None
                        st.rerun()
        
        # 3. Exibir assistentes já adicionados à proposta
        assistentes_atuais = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "ASSISTENTE")
        
        if not assistentes_atuais.empty:
            st.markdown("### Assistentes Adicionados")
            
            # Criar tabela para exibição dos assistentes
            for idx, row in assistentes_atuais.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{row['fornecedor']}**")  # Usando o campo fornecedor que contém o nome
                        st.caption(row['descricao'])
                    
                    with col2:
                        st.markdown(f"**R$ {row['valor']:.2f}**")
                    
                    with col3:
                        # Botão para editar
                        if st.button("Editar", key=f"edit_assistente_{row['id']}"):
                            st.session_state.editing_assistente_id = row['id']
                            st.session_state.editing_assistente_valor = row['valor']
                            st.session_state.editing_assistente_descricao = row['descricao']
                            st.rerun()
                    
                    with col4:
                        # Botão para excluir
                        if st.button("Excluir", key=f"del_assistente_{row['id']}"):
                            if st.session_state.db.excluir_acrescimo(row['id']):
                                st.success("Assistente removido com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Erro ao remover assistente.")
            
            # Exibir total
            st.info(f"Total de assistentes: R$ {assistentes_atuais['valor'].sum():.2f}")
        else:
            st.info("Nenhum assistente adicionado a esta proposta.")
    except Exception as e:
        st.error(f"Erro ao carregar informações: {str(e)}")
        st.write("Detalhes do erro:", str(e))")