import streamlit as st
import time

def exibir_aba_fornecedores(proposta_exec_id):
    """
    Exibe a aba de fornecedores para a proposta especificada.
    
    Args:
        proposta_exec_id: ID da proposta em execução
    """
    st.subheader("Fornecedores")
    
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
    
    st.markdown("---")
    
    # 2. Exibir fornecedores já adicionados à proposta
    try:
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
    except Exception as e:
        st.error(f"Erro ao carregar fornecedores: {str(e)}")