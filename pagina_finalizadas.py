# ABA 3: FINALIZADAS
with tab3:
    st.header("Propostas Finalizadas")
    
    if not propostas.empty:
        # Resetar o DataFrame para evitar problemas de referência
        propostas_finalizadas = None
        
        # Filtrar apenas propostas com status exatamente igual a "Finalizada" ou "Recusada"
        propostas_somente_finalizadas = propostas_com_clientes[
            (propostas_com_clientes['status'] == 'Finalizada') | 
            (propostas_com_clientes['status'] == 'Recusada')
        ].copy()
        
        # Mostrar o total de propostas finalizadas para diagnóstico
        st.write(f"Total de propostas finalizadas: {len(propostas_somente_finalizadas)}")
        
        # Se houver propostas finalizadas, exibir
        if not propostas_somente_finalizadas.empty:
            # Preparar um DataFrame limpo apenas com as colunas necessárias
            df_finalizadas = pd.DataFrame()
            df_finalizadas['ID'] = propostas_somente_finalizadas['id']
            df_finalizadas['Número'] = propostas_somente_finalizadas['numero']
            df_finalizadas['Cliente'] = propostas_somente_finalizadas['nome']
            df_finalizadas['Descrição'] = propostas_somente_finalizadas['descricao']
            df_finalizadas['Status'] = propostas_somente_finalizadas['status']
            
            # Formatar valor como moeda
            df_finalizadas['Valor (R$)'] = propostas_somente_finalizadas['valor'].apply(
                lambda x: f"R$ {float(x) if pd.notna(x) else 0.0:.2f}"
            )
            
            # Formatar datas
            df_finalizadas['Data Início'] = propostas_somente_finalizadas['data_inicio'].apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
            )
            
            df_finalizadas['Tipo'] = propostas_somente_finalizadas['tipo_proposta']
            
            # Adicionar debug para cada proposta (apenas durante solução de problemas)
            for idx, proposta in propostas_somente_finalizadas.iterrows():
                st.write(f"Proposta #{proposta['numero']} - Status: {proposta['status']}")
            
            # Exibir a tabela sem a coluna ID
            st.dataframe(df_finalizadas.drop(columns=['ID']), hide_index=True)
            
            # Guardar referência para uso nas seções abaixo
            propostas_finalizadas = propostas_somente_finalizadas
            
        else:
            st.info("Não há propostas finalizadas no sistema.")
            # Criar DataFrame vazio para evitar erros abaixo
            propostas_finalizadas = pd.DataFrame()
    else:
        st.info("Não há propostas cadastradas no sistema.")
        propostas_finalizadas = pd.DataFrame()
        
    # Verificar se temos propostas finalizadas antes de mostrar a interface para reabrir/excluir
    if not propostas_finalizadas.empty:
        with st.expander("Reabrir Proposta Finalizada"):
            # Obter lista de números de propostas finalizadas para o select box
            numeros_propostas = propostas_finalizadas['numero'].tolist()
            numeros_propostas.sort()  # Ordenar para facilitar a seleção
            
            proposta_numero = st.selectbox(
                "Selecione o número da proposta a reabrir:",
                numeros_propostas,
                key="numero_proposta_finalizada_reabrir"
            )
            
            proposta_reabrir = propostas_finalizadas[propostas_finalizadas['numero'] == proposta_numero]
            
            if not proposta_reabrir.empty:
                st.info(f"Você está prestes a reabrir a proposta #{proposta_numero} - {proposta_reabrir.iloc[0]['descricao']}")
                st.warning("Esta ação mudará o status da proposta para 'Em execução'.")
                
                if st.button("REABRIR PROPOSTA", key="confirmar_reabertura"):
                    try:
                        # Importar função de reabrir proposta
                        from reabrir_proposta import reabrir_proposta_finalizada
                        
                        # Obter ID da proposta
                        proposta_id = proposta_reabrir.iloc[0]['id']
                        
                        # Chamar função de reabertura
                        resultado = reabrir_proposta_finalizada(proposta_id)
                        
                        if resultado.get('status') == 'sucesso':
                            st.success(resultado.get('mensagem'))
                            time.sleep(1)
                            st.rerun()
                        elif resultado.get('status') == 'sucesso_com_alerta':
                            st.success(resultado.get('mensagem'))
                            st.warning(resultado.get('alerta'))
                            st.info(f"Encontrados {resultado.get('lancamentos_encontrados')} lançamentos financeiros.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Erro ao reabrir proposta: {resultado.get('mensagem')}")
                    except Exception as e:
                        st.error(f"Erro ao reabrir proposta: {str(e)}")
        
        # Adicionar área para exclusão de proposta
        with st.expander("Excluir Proposta Finalizada"):
            # Obter lista de números de propostas finalizadas para o select box
            numeros_propostas = propostas_finalizadas['numero'].tolist()
            numeros_propostas.sort()  # Ordenar para facilitar a seleção
            
            proposta_numero = st.selectbox(
                "Selecione o número da proposta a excluir:",
                numeros_propostas,
                key="numero_proposta_finalizada_excluir"
            )
            
            proposta_exc = propostas_finalizadas[propostas_finalizadas['numero'] == proposta_numero]
            
            if not proposta_exc.empty:
                st.warning(f"Você está prestes a excluir a proposta #{proposta_numero} - {proposta_exc.iloc[0]['descricao']}")
                if st.button("CONFIRMAR EXCLUSÃO", key="confirmar_exclusao_finalizada"):
                    try:
                        resultado_exclusao = st.session_state.db.excluir_proposta_por_numero(proposta_numero)
                        sucesso = resultado_exclusao.get("status", False)
                        mensagem = resultado_exclusao.get("message", "Erro desconhecido")
                        if sucesso:
                            st.success("Proposta excluída com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Erro ao excluir proposta: {mensagem}")
                    except Exception as e:
                        st.error(f"Erro ao excluir proposta: {str(e)}")
            else:
                st.info("Selecione uma proposta válida para excluir.")
        
        # Ações para propostas finalizadas
        st.subheader("Documentos")
        
        # Obter lista de números de propostas para o select box
        numeros_propostas_finalizadas = propostas_finalizadas['numero'].tolist()
        numeros_propostas_finalizadas.sort()  # Ordenar para facilitar a seleção
        
        proposta_numero = st.selectbox(
            "Selecione o número da proposta:",
            numeros_propostas_finalizadas,
            key="numero_proposta_finalizada_docs"
        )
        
        # Verificar se a proposta existe
        proposta_final = propostas_finalizadas[propostas_finalizadas['numero'] == proposta_numero]