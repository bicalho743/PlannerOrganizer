import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.pdf_generator import gerar_pdf_fechamento
from utils.importador import importar_cadastros, gerar_template_csv

def show():
    st.title("📝 Gestão de Propostas")

    # Usar radio para selecionar a aba
    aba_selecionada = st.radio(
        "Selecione a opção:",
        ["Nova Proposta", "Lista de Propostas", "Propostas em Execução", "Propostas Finalizadas"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.write("---")  # Divisor para separar o menu das abas do conteúdo

    # Exibir conteúdo com base na aba selecionada
    if aba_selecionada == "Nova Proposta":
        mostrar_nova_proposta()
    elif aba_selecionada == "Lista de Propostas":
        mostrar_lista_propostas()
    elif aba_selecionada == "Propostas em Execução":
        st.subheader("📋 PROPOSTAS EM EXECUÇÃO")
        mostrar_andamento()
    elif aba_selecionada == "Propostas Finalizadas":
        st.subheader("✅ PROPOSTAS FINALIZADAS")
        mostrar_propostas_finalizadas()
    # Opção de importação removida conforme solicitação do cliente

def mostrar_propostas_finalizadas():
    """
    Exibe as propostas que foram finalizadas (concluídas após a execução).
    Estas propostas servem apenas para histórico/controle.
    """
    try:
        # Carregar propostas finalizadas (status "Concluída")
        propostas = st.session_state.db.get_propostas()
        if not propostas.empty:
            # Filtrar apenas propostas finalizadas (com status "Concluída")
            propostas = propostas[propostas['status'] == 'Concluída']
        
        if propostas.empty:
            st.info("Nenhuma proposta finalizada encontrada no sistema.")
            return

        # Juntar dados de propostas com clientes
        clientes = st.session_state.db.get_clientes()
        propostas = propostas.merge(
            clientes[['id', 'nome']], 
            left_on='cliente_id', 
            right_on='id', 
            how='left',
            suffixes=('', '_cliente')
        )

        # Ordenar por data de proposta, mais recentes primeiro
        propostas = propostas.sort_values('data_proposta', ascending=False)
        
        # Criar DataFrame para exibição
        df_display = propostas[['numero', 'nome', 'descricao', 'valor', 'tipo_proposta', 'data_proposta']].copy()
        df_display.columns = ['Número', 'Cliente', 'Descrição', 'Valor (R$)', 'Tipo', 'Data']

        # Formatar valores
        df_display['Valor (R$)'] = df_display['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')
        # Formatação da data no formato brasileiro (DD/MM/YYYY)
        df_display['Data'] = pd.to_datetime(df_display['Data']).dt.strftime('%d/%m/%Y')
        
        # Exibir tabela com dados
        st.write("#### Lista de Propostas Finalizadas")
        st.dataframe(
            df_display, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Número": st.column_config.NumberColumn("Número", width="small"),
                "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                "Valor (R$)": st.column_config.TextColumn("Valor (R$)", width="small"),
                "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
                "Data": st.column_config.TextColumn("Data", width="small"),
            }
        )
        
        # Adicionar filtros para melhor visualização
        st.write("#### Filtrar Propostas Finalizadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtrar por cliente
            cliente_selecionado = st.selectbox(
                "Filtrar por Cliente",
                ["Todos"] + df_display['Cliente'].unique().tolist()
            )
        
        with col2:
            # Filtrar por tipo
            tipo_selecionado = st.selectbox(
                "Filtrar por Tipo",
                ["Todos"] + df_display['Tipo'].unique().tolist()
            )
            
        # Aplicar filtros se necessário
        df_filtrado = df_display.copy()
        
        if cliente_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Cliente'] == cliente_selecionado]
            
        if tipo_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_selecionado]
            
        # Exibir resultados filtrados se houver filtros aplicados
        if cliente_selecionado != "Todos" or tipo_selecionado != "Todos":
            st.write("#### Resultados Filtrados")
            
            if df_filtrado.empty:
                st.info("Nenhuma proposta encontrada com os filtros selecionados.")
            else:
                st.dataframe(
                    df_filtrado, 
                    hide_index=True, 
                    use_container_width=True
                )
                
                # Mostrar análise estatística
                valor_total = df_filtrado['Valor (R$)'].str.replace('R$', '').str.strip().str.replace('.', '').str.replace(',', '.').astype(float).sum()
                st.metric("Valor Total", f"R$ {valor_total:.2f}")
                
        # Adicionar opção para ver detalhes de uma proposta específica
        st.write("#### Visualizar Detalhes da Proposta")
        
        proposta_num = st.selectbox(
            "Selecione o número da proposta",
            df_display['Número'].tolist()
        )
        
        if st.button("📋 Ver Detalhes Completos", use_container_width=True):
            # Buscar proposta pelo número
            proposta = propostas[propostas['numero'] == proposta_num].iloc[0]
            cliente = clientes[clientes['id'] == proposta['cliente_id']].iloc[0]
            
            # Exibir detalhes completos
            st.write("---")
            st.write("### Detalhes da Proposta Finalizada")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Número:** #{proposta['numero']}")
                st.write(f"**Cliente:** {proposta['nome']}")
                st.write(f"**Tipo:** {proposta['tipo_proposta']}")
                st.write(f"**Data:** {pd.to_datetime(proposta['data_proposta']).strftime('%d/%m/%Y')}")
                
            with col2:
                st.write(f"**Valor Base:** R$ {float(proposta['valor']):.2f}")
                
                # Adicionar dados de acréscimos se existirem
                try:
                    acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                    if not acrescimos.empty:
                        valor_acrescimos = acrescimos['valor'].sum()
                        valor_total = float(proposta['valor']) + valor_acrescimos
                        st.write(f"**Valor Acréscimos:** R$ {valor_acrescimos:.2f}")
                        st.write(f"**Valor Total:** R$ {valor_total:.2f}")
                except Exception as e:
                    st.error(f"Erro ao buscar acréscimos: {str(e)}")
            
            st.write("**Descrição:**")
            st.info(proposta['descricao'])
            
            # Exibir acréscimos se existirem
            try:
                acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                if not acrescimos.empty:
                    st.write("### Acréscimos da Proposta")
                    
                    # Preparar dados
                    df_acrescimos = acrescimos[['tipo', 'fornecedor', 'valor', 'descricao']].copy()
                    df_acrescimos.columns = ['Tipo', 'Fornecedor/Assistente', 'Valor (R$)', 'Descrição']
                    df_acrescimos['Valor (R$)'] = df_acrescimos['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')
                    
                    # Exibir tabela de acréscimos
                    st.dataframe(df_acrescimos, hide_index=True, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao buscar acréscimos: {str(e)}")
            
            # Botão para baixar PDF se necessário
            if st.button("📄 Gerar PDF da Proposta Finalizada", type="primary"):
                try:
                    # Primeiro recuperar os acréscimos da proposta
                    acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                    
                    # Criar diretório se não existir
                    import os
                    os.makedirs("pdfs", exist_ok=True)
                    
                    # Gerar nome do arquivo
                    filename = f"pdfs/proposta_finalizada_{proposta['numero']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    # Gerar o PDF
                    gerar_pdf_fechamento(proposta, cliente, acrescimos, filename)
                    
                    # Exibir link para download
                    with open(filename, "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                        
                    st.success("PDF gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar PDF", 
                        data=PDFbyte,
                        file_name=f"proposta_finalizada_{proposta['numero']}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")
    
    except Exception as e:
        st.error(f"Erro ao carregar propostas finalizadas: {str(e)}")

def mostrar_nova_proposta():
    st.subheader("Cadastrar Nova Proposta")

    with st.form("nova_proposta", clear_on_submit=True):
        try:
            # Carregar lista de clientes para seleção
            clientes = st.session_state.db.get_clientes()
            if clientes.empty:
                st.warning("Não há clientes cadastrados. Por favor, cadastre um cliente primeiro.")
                st.form_submit_button("OK", disabled=True)
                return

            # Campos do formulário
            cliente_nome = st.selectbox("Cliente", clientes['nome'].tolist())
            cliente_row = clientes[clientes['nome'] == cliente_nome]
            if cliente_row.empty:
                st.error("Cliente não encontrado")
                return
            cliente_id = int(cliente_row['id'].iloc[0])

            descricao = st.text_area("Descrição do Serviço")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            tipo_proposta = st.selectbox(
                "Tipo de Proposta",
                ["Organização", "Organização Mudança", "Treinamento Funcionários", 
                 "Consultoria Online", "Consultoria Enxoval"]
            )

            col1, col2 = st.columns(2)
            with col1:
                # Configurar formato brasileiro de data (DD/MM/YYYY)
                data_inicio = st.date_input(
                    "Data de Início", 
                    format="DD/MM/YYYY"
                )
            with col2:
                # Configurar formato brasileiro de data (DD/MM/YYYY)
                data_fim = st.date_input(
                    "Data de Fim",
                    format="DD/MM/YYYY"
                )
                
            # Calcular e exibir previsão de dias entre início e fim
            if data_inicio and data_fim:
                dias_previstos = (data_fim - data_inicio).days
                if dias_previstos >= 0:
                    st.info(f"**Previsão de Dias:** {dias_previstos} dias")
                else:
                    st.warning("A data de fim deve ser posterior à data de início.")

            # Configurar formato brasileiro de data (DD/MM/YYYY) para prazo de entrega
            prazo_entrega = st.date_input(
                "Prazo de Entrega", 
                format="DD/MM/YYYY"
            ) if tipo_proposta in ["Organização", "Organização Mudança"] else None
            status = st.selectbox("Status", ["Aberta", "Recusada", "Fechada"])

            # Botão de submissão
            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if not descricao:
                    st.error("Por favor, preencha a descrição da proposta.")
                    return
                if valor <= 0:
                    st.error("Por favor, insira um valor válido maior que zero.")
                    return

                try:
                    # Adicionar proposta ao banco de dados
                    proposta_id = st.session_state.db.add_proposta(
                        cliente_id=cliente_id,
                        descricao=descricao,
                        valor=float(valor),
                        status=status,
                        tipo_proposta=tipo_proposta,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        prazo_entrega=prazo_entrega
                    )
                    st.success("Proposta cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar proposta: {str(e)}")

        except Exception as e:
            st.error(f"Erro ao carregar dados de clientes: {str(e)}")

def mostrar_lista_propostas():
    st.subheader("Propostas Cadastradas")
    try:
        propostas = st.session_state.db.get_propostas()
        if not propostas.empty:
            # Juntar propostas com informações dos clientes
            clientes = st.session_state.db.get_clientes()
            propostas = propostas.merge(
                clientes[['id', 'nome']],
                left_on='cliente_id',
                right_on='id',
                how='left',
                suffixes=('', '_cliente')
            )

            # Ordenar por data de proposta, mais recentes primeiro
            propostas = propostas.sort_values('data_proposta', ascending=False)
            
            # Guardar a referência original das propostas
            st.session_state.propostas_completas = propostas.copy()

            # Calcular a previsão de dias (utilizando data_inicio e data_fim - é a diferença entre elas)
            propostas['previsao_dias'] = None
            for idx, row in propostas.iterrows():
                try:
                    if pd.notna(row['data_inicio']) and pd.notna(row['data_fim']):
                        inicio = pd.to_datetime(row['data_inicio'])
                        fim = pd.to_datetime(row['data_fim'])
                        dias = (fim - inicio).days
                        propostas.at[idx, 'previsao_dias'] = dias if dias >= 0 else None
                        # Adicionar log para debug
                        print(f"Debug: Proposta {row['numero']}, Data início: {inicio}, Data fim: {fim}, Dias calculados: {dias}")
                except Exception as e:
                    print(f"Erro ao calcular dias para proposta {row.get('numero', 'desconhecida')}: {str(e)}")  # Log de erro para debug
                    
            # Criar DataFrame para exibição
            df_display = propostas[['id', 'numero', 'nome', 'descricao', 'valor', 'status', 'data_proposta', 'previsao_dias']].copy()
            df_display.columns = ['ID', 'Número', 'Cliente', 'Descrição', 'Valor (R$)', 'Status', 'Data', 'Previsão (Dias)']

            # Formatar valores
            df_display['Valor (R$)'] = df_display['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')
            # Formatação da data no formato brasileiro (DD/MM/YYYY)
            df_display['Data'] = pd.to_datetime(df_display['Data']).dt.strftime('%d/%m/%Y')
            
            # Criar uma cópia do DataFrame no state para edição
            if 'propostas_editaveis' not in st.session_state:
                st.session_state.propostas_editaveis = df_display.copy()
            
            # Exibir tabela editável
            st.write("**Edite os dados diretamente na tabela abaixo:**")
            edited_df = st.data_editor(
                df_display,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID", 
                        disabled=True,
                        required=True,
                        width="small"
                    ),
                    "Número": st.column_config.NumberColumn(
                        "Número", 
                        disabled=True,
                        required=True,
                        width="small"
                    ),
                    "Cliente": st.column_config.TextColumn(
                        "Cliente",
                        disabled=True,
                        width="medium"
                    ),
                    "Descrição": st.column_config.TextColumn(
                        "Descrição",
                        width="medium"
                    ),
                    "Valor (R$)": st.column_config.TextColumn(
                        "Valor (R$)",
                        width="small"
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Aberta", "Fechada", "Recusada"],
                        width="small"
                    ),
                    "Data": st.column_config.TextColumn(
                        "Data",
                        disabled=False,  # Agora permitimos editar a data
                        width="small"
                    ),
                    "Previsão (Dias)": st.column_config.NumberColumn(
                        "Previsão (Dias)",
                        min_value=0,
                        format="%d dias",
                        width="small"
                    ),
                },
                num_rows="dynamic",
                key="propostas_editor"
            )
            
            # Verificar se houve alterações e atualizar o banco de dados
            if st.button("Salvar Alterações", type="primary", use_container_width=True):
                contador_atualizacoes = 0
                
                # Verificar cada linha do DataFrame editado
                for i, row in edited_df.iterrows():
                    proposta_id = row['ID']
                    proposta_original = st.session_state.propostas_completas[st.session_state.propostas_completas['id'] == proposta_id].iloc[0]
                    alteracoes_realizadas = False
                    
                    # Verificar se houve alteração na descrição
                    if row['Descrição'] != proposta_original['descricao']:
                        st.session_state.db.atualizar_proposta(
                            proposta_id=proposta_id,
                            descricao=row['Descrição']
                        )
                        contador_atualizacoes += 1
                    
                    # Verificar se houve alteração no status
                    if row['Status'] != proposta_original['status']:
                        st.session_state.db.atualizar_proposta(
                            proposta_id=proposta_id,
                            status=row['Status']
                        )
                        contador_atualizacoes += 1
                    
                    # Verificar se houve alteração no valor
                    try:
                        # Extração mais cuidadosa do valor monetário
                        valor_str = row['Valor (R$)']
                        
                        # Remover símbolo monetário
                        valor_str = valor_str.replace('R$', '').strip()
                        
                        # Verificar qual formato o usuário está usando
                        if ',' in valor_str and '.' in valor_str:
                            # Formato brasileiro com separador de milhares (1.234,56)
                            valor_str = valor_str.replace('.', '').replace(',', '.')
                        elif ',' in valor_str:
                            # Formato com vírgula como decimal (1234,56)
                            valor_str = valor_str.replace(',', '.')
                        # Caso contrário, mantém o formato com ponto decimal (1234.56)
                            
                        valor_editado = float(valor_str)
                        
                        # Log para diagnóstico
                        print(f"Debug: Conversão de valor: original='{row['Valor (R$)']}', limpo='{valor_str}', float={valor_editado}")
                        
                        if abs(valor_editado - float(proposta_original['valor'])) > 0.01:  # Comparação com tolerância
                            st.session_state.db.atualizar_proposta(
                                proposta_id=proposta_id,
                                valor=valor_editado
                            )
                            contador_atualizacoes += 1
                    except Exception as e:
                        st.warning(f"Valor inválido para a proposta {row['Número']}: {row['Valor (R$)']}. Erro: {str(e)}")
                        
                    # Verificar se houve alteração na data
                    try:
                        data_original = pd.to_datetime(proposta_original['data_proposta']).strftime('%d/%m/%Y')
                        if row['Data'] != data_original:
                            # Log para diagnóstico
                            print(f"Debug: Conversão de data: original='{data_original}', nova='{row['Data']}'")
                            
                            # Converter a data para o formato do banco - com tratamento mais robusto
                            try:
                                # Primeira estratégia: usar parse do pandas diretamente (mais flexível)
                                nova_data = None
                                try:
                                    # Tentar converter sem especificar formato (pandas tenta inferir)
                                    nova_data = pd.to_datetime(row['Data']).date()
                                    print(f"Debug: Data convertida com sucesso usando inferência automática: {nova_data}")
                                except:
                                    # Se falhar, tentar com formatos específicos
                                    try:
                                        # Formato DD/MM/YYYY (brasileiro)
                                        nova_data = pd.to_datetime(row['Data'], format='%d/%m/%Y').date()
                                        print(f"Debug: Data convertida com formato DD/MM/YYYY: {nova_data}")
                                    except:
                                        try:
                                            # Formato MM/DD/YYYY (americano)
                                            nova_data = pd.to_datetime(row['Data'], format='%m/%d/%Y').date()
                                            print(f"Debug: Data convertida com formato MM/DD/YYYY: {nova_data}")
                                        except:
                                            try:
                                                # Formato YYYY-MM-DD (ISO)
                                                nova_data = pd.to_datetime(row['Data'], format='%Y-%m-%d').date()
                                                print(f"Debug: Data convertida com formato YYYY-MM-DD: {nova_data}")
                                            except Exception as e:
                                                print(f"Debug: Todos os formatos de data falharam: {str(e)}")
                                                
                                # Se conseguimos converter a data, atualizar no banco
                                if nova_data:
                                    # Atualizar não só a data_proposta, mas também data_inicio e data_fim
                                    # para que a visualização do PDF use as datas atualizadas
                                    st.session_state.db.atualizar_proposta(
                                        proposta_id=proposta_id,
                                        data_proposta=nova_data,
                                        data_inicio=nova_data,  # Atualizar também a data de início
                                    )
                                    
                                    # Se temos previsão de dias, calcular nova data de fim
                                    dias_previstos = proposta_original.get('previsao_dias', 0)
                                    if dias_previstos and dias_previstos > 0:
                                        data_fim_nova = nova_data + pd.Timedelta(days=dias_previstos)
                                        st.session_state.db.atualizar_proposta(
                                            proposta_id=proposta_id,
                                            data_fim=data_fim_nova
                                        )
                                        print(f"Debug: Data atualizada com sucesso. Início: {nova_data}, Fim: {data_fim_nova}")
                                    else:
                                        print(f"Debug: Data atualizada com sucesso para: {nova_data} (sem ajuste da data fim)")
                                    
                                    contador_atualizacoes += 1
                                else:
                                    st.warning(f"Não foi possível converter a data '{row['Data']}'. Use o formato DD/MM/YYYY.")
                            except Exception as e:
                                st.warning(f"Formato de data inválido para a proposta {row['Número']}: {row['Data']}. Erro: {str(e)}. Use o formato DD/MM/YYYY.")
                    except Exception as e:
                        st.warning(f"Erro ao processar data para a proposta {row['Número']}: {str(e)}")
                                
                    # Verificar se houve alteração na previsão de dias
                    previsao_dias_original = proposta_original.get('previsao_dias')
                    if pd.notna(row['Previsão (Dias)']) and row['Previsão (Dias)'] != previsao_dias_original:
                        try:
                            # Se temos a previsão de dias mas não as datas, vamos calculá-las
                            dias = int(row['Previsão (Dias)'])
                            inicio = None
                            fim = None
                            
                            # Se já temos data de início, calculamos a data de fim
                            if pd.notna(proposta_original['data_inicio']):
                                inicio = pd.to_datetime(proposta_original['data_inicio'])
                                fim = inicio + pd.Timedelta(days=dias)
                            # Se não temos data de início, usamos a data da proposta como início
                            elif pd.notna(proposta_original['data_proposta']):
                                inicio = pd.to_datetime(proposta_original['data_proposta'])
                                fim = inicio + pd.Timedelta(days=dias)
                                
                            if inicio and fim:
                                st.session_state.db.atualizar_proposta(
                                    proposta_id=proposta_id,
                                    data_inicio=inicio.date(),
                                    data_fim=fim.date()
                                )
                                contador_atualizacoes += 1
                        except Exception as e:
                            st.warning(f"Erro ao atualizar datas baseadas na previsão de dias: {str(e)}")
                
                if contador_atualizacoes > 0:
                    st.success(f"{contador_atualizacoes} atualizações realizadas com sucesso!")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração detectada.")
            
            st.markdown("---")
            
            # Seleção de proposta para ação
            st.subheader("Outras Ações")
            col1, col2 = st.columns(2)
            with col1:
                proposta_num = st.number_input("Número da proposta para ação:", 
                                             min_value=int(propostas['numero'].min()),
                                             max_value=int(propostas['numero'].max()),
                                             step=1)
            with col2:
                acao = st.selectbox("Ação:", ["Excluir", "Exportar PDF"])

            # Duas ações diferentes: Excluir precisa de formulário, mas Exportar PDF não
            if acao == "Excluir":
                # Formulário para exclusão
                with st.form("acao_proposta"):
                    if st.form_submit_button(f"Confirmar {acao}"):
                        proposta = propostas[propostas['numero'] == proposta_num].iloc[0]
                        
                        if st.session_state.get(f'confirm_delete_proposta_{proposta["id"]}', False):
                            sucesso, msg = st.session_state.db.excluir_proposta(proposta['id'])
                            if sucesso:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.session_state[f'confirm_delete_proposta_{proposta["id"]}'] = True
                            st.warning("Confirma a exclusão desta proposta?")
                            st.rerun()
            
            elif acao == "Exportar PDF":
                # Primeiro mostre a opção de template Canva
                usar_template_canva = st.checkbox("Usar Template Canva", help="Selecione esta opção para usar um template visual para o PDF")
                
                # Botão simples para confirmar a exportação
                if st.button(f"Confirmar {acao}"):
                    proposta = propostas[propostas['numero'] == proposta_num].iloc[0]
                    try:
                        with st.spinner("Gerando PDF..."):
                            # Criar diretório para PDFs se não existir
                            os.makedirs("pdfs", exist_ok=True)

                            # Nome do arquivo
                            filename = f"pdfs/proposta_{proposta['numero']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                            # Buscar acréscimos da proposta
                            acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                            
                            # Log para diagnóstico
                            print(f"Debug: Gerando PDF para proposta {proposta['numero']} - usando template: {usar_template_canva}")
                            
                            # Gerar PDF
                            pdf_path = gerar_pdf_fechamento(
                                proposta=proposta,
                                cliente={'nome': proposta['nome']},
                                acrescimos=acrescimos,
                                filename=filename,
                                usar_template=usar_template_canva
                            )

                            print(f"Debug: PDF gerado no caminho: {pdf_path}")
                            st.success("PDF gerado com sucesso!")
                            
                            # Criar link para download (agora fora do form)
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="📥 Baixar PDF",
                                    data=pdf_bytes,
                                    file_name=os.path.basename(filename),
                                    mime="application/pdf",
                                    key=f"download_button_{proposta['numero']}"
                                )
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {str(e)}")

        else:
            st.info("Nenhuma proposta encontrada.")

    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")

def mostrar_andamento():
    # Nota: A subheader já é inserida na chamada da função agora
    try:
        # Carregar propostas em execução (status Fechada)
        propostas = st.session_state.db.get_propostas()
        if not propostas.empty:
            # Filtrar apenas propostas em execução (com status "Fechada")
            propostas = propostas[propostas['status'] == 'Fechada']
            
        if propostas.empty:
            st.warning("Nenhuma proposta em execução encontrada.")
            return

        # Juntar dados de propostas com clientes
        clientes = st.session_state.db.get_clientes()
        propostas = propostas.merge(
            clientes[['id', 'nome']], 
            left_on='cliente_id', 
            right_on='id', 
            how='left',
            suffixes=('', '_cliente')
        )

        # Selecionar proposta
        proposta_display = [
            f"Proposta #{p['numero']} - {p['nome']} - {p['descricao'][:30] + '...' if len(p['descricao']) > 30 else p['descricao']}" 
            for _, p in propostas.iterrows()
        ]

        # Usar colunas para melhorar o layout
        col_selecao1, col_selecao2 = st.columns([3, 1])
        
        with col_selecao1:
            proposta_selecionada = st.selectbox(
                "Selecione a Proposta em Execução",
                proposta_display,
                key="proposta_execucao"
            )
            
        with col_selecao2:
            btn_selecionar = st.button("Visualizar Detalhes", type="primary", use_container_width=True)

        if proposta_selecionada and btn_selecionar:
            try:
                # Extrair número da proposta
                numero_proposta = int(proposta_selecionada.split('#')[1].split(' -')[0])
                proposta = propostas[propostas['numero'] == numero_proposta].iloc[0]
                cliente = clientes[clientes['id'] == proposta['cliente_id']].iloc[0]

                # Criar 3 abas para organizar as informações
                tab_info, tab_acrescimos, tab_pagamentos = st.tabs([
                    "📋 Informações Gerais", 
                    "💰 Acréscimos e Fornecedores", 
                    "📊 Pagamentos"
                ])
                
                with tab_info:
                    # Exibir detalhes da proposta com melhor layout
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Dados da Proposta")
                        st.write(f"**Número:** #{proposta['numero']}")
                        st.write(f"**Data:** {pd.to_datetime(proposta['data_proposta']).strftime('%d/%m/%Y')}")
                        st.write(f"**Tipo:** {proposta['tipo_proposta']}")
                        st.write(f"**Status:** {proposta['status']}")
                        
                        # Exibir datas
                        if pd.notna(proposta['data_inicio']) and pd.notna(proposta['data_fim']):
                            data_inicio = pd.to_datetime(proposta['data_inicio']).strftime('%d/%m/%Y')
                            data_fim = pd.to_datetime(proposta['data_fim']).strftime('%d/%m/%Y')
                            st.write(f"**Período:** {data_inicio} a {data_fim}")
                            
                            # Calcular dias
                            dias = (pd.to_datetime(proposta['data_fim']) - pd.to_datetime(proposta['data_inicio'])).days
                            st.write(f"**Duração:** {dias} dias")
                    
                    with col2:
                        st.markdown("### Dados do Cliente")
                        st.write(f"**Nome:** {cliente['nome']}")
                        st.write(f"**Telefone:** {cliente.get('telefone', 'Não informado')}")
                        st.write(f"**Email:** {cliente.get('email', 'Não informado')}")
                        st.write(f"**Endereço:** {cliente.get('endereco', 'Não informado')}")
                    
                    st.markdown("### Descrição do Serviço")
                    st.write(proposta['descricao'])
                    
                    st.markdown("### Valores")
                    st.write(f"**Valor Base:** R$ {float(proposta['valor']):.2f}")
                    
                    # Calcular e exibir valor total com acréscimos
                    try:
                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                        if not acrescimos.empty:
                            valor_acrescimos = acrescimos['valor'].sum()
                            valor_total = float(proposta['valor']) + valor_acrescimos
                            st.write(f"**Valor Acréscimos:** R$ {valor_acrescimos:.2f}")
                            st.write(f"**Valor Total:** R$ {valor_total:.2f}")
                        else:
                            st.write(f"**Valor Total:** R$ {float(proposta['valor']):.2f} (sem acréscimos)")
                    except Exception as e:
                        st.error(f"Erro ao calcular valores totais: {str(e)}")
                
                with tab_acrescimos:
                    st.markdown("### Adicionar Acréscimo")
                    
                    # Layout com formulário mais organizado 
                    with st.form("adicionar_acrescimo", clear_on_submit=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            tipo_acrescimo = st.selectbox(
                                "Tipo de Acréscimo",
                                ["Organização", "Assistente", "Fornecedor", "Marcenaria", "Produto"],
                                key="tipo_acrescimo"
                            )

                        with col2:
                            fornecedor_nome = None
                            if tipo_acrescimo == "Fornecedor":
                                # Carregar lista de fornecedores do banco de dados
                                try:
                                    fornecedores = st.session_state.db.get_fornecedores()
                                    if not fornecedores.empty:
                                        fornecedor_opcoes = fornecedores['nome'].tolist()
                                    else:
                                        fornecedor_opcoes = ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                                except Exception as e:
                                    print(f"Erro ao carregar fornecedores: {str(e)}")
                                    fornecedor_opcoes = ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                                
                                fornecedor = st.selectbox(
                                    "Fornecedor",
                                    options=fornecedor_opcoes,
                                    key="fornecedor_select"
                                )
                                fornecedor_nome = fornecedor
                                
                            elif tipo_acrescimo == "Assistente":
                                try:
                                    assistentes = st.session_state.db.get_assistentes()
                                    if not assistentes.empty:
                                        assistente = st.selectbox(
                                            "Assistente",
                                            options=assistentes['nome'].tolist(),
                                            key="assistente_select"
                                        )
                                        fornecedor_nome = assistente
                                    else:
                                        st.warning("Nenhum assistente cadastrado. Por favor, cadastre assistentes na seção Cadastros.")
                                except Exception as e:
                                    st.error(f"Erro ao carregar assistentes: {str(e)}")

                        descricao_acrescimo = st.text_area("Descrição", height=80, key="descricao_acrescimo")
                        valor_acrescimo = st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="valor_acrescimo")

                        submitted = st.form_submit_button("Adicionar Acréscimo", use_container_width=True)
                        
                        if submitted:
                            if valor_acrescimo <= 0:
                                st.error("Por favor, insira um valor válido maior que zero.")
                            elif tipo_acrescimo == "Assistente" and not fornecedor_nome:
                                st.error("Por favor, selecione um assistente.")
                            elif tipo_acrescimo == "Fornecedor" and not fornecedor_nome:
                                st.error("Por favor, selecione um fornecedor.")
                            else:
                                try:
                                    # Salvando o ID da proposta em uma variável de sessão para manter após o rerun
                                    proposta_id_atual = int(proposta['id'])
                                    if 'proposta_selecionada_id' not in st.session_state:
                                        st.session_state.proposta_selecionada_id = proposta_id_atual
                                    else:
                                        st.session_state.proposta_selecionada_id = proposta_id_atual
                                    
                                    # Adicionando o acréscimo
                                    result = st.session_state.db.add_acrescimo_proposta(
                                        proposta_id=proposta_id_atual,
                                        tipo=tipo_acrescimo,
                                        fornecedor=fornecedor_nome,
                                        descricao=descricao_acrescimo if descricao_acrescimo else None,
                                        valor=float(valor_acrescimo)
                                    )
                                    
                                    # Verificar se o acréscimo foi adicionado com sucesso
                                    if result:
                                        st.success(f"Acréscimo de {tipo_acrescimo} adicionado com sucesso!")
                                        
                                        # Limpar campos após sucesso
                                        if 'valor_acrescimo' in st.session_state:
                                            st.session_state.valor_acrescimo = 0.0
                                        if 'descricao_acrescimo' in st.session_state:
                                            st.session_state.descricao_acrescimo = ""
                                    else:
                                        st.error("Não foi possível adicionar o acréscimo. Tente novamente.")
                                    
                                    # Não precisamos de rerun aqui porque vamos atualizar a exibição logo em seguida
                                except Exception as e:
                                    st.error(f"Erro ao adicionar acréscimo: {str(e)}")
                                    print(f"Erro detalhado: {str(e)}")
                                    
                            # Recarregar a mesma proposta
                            st.experimental_rerun()

                    # Exibir acréscimos existentes com melhor formatação
                    st.markdown("### Acréscimos Cadastrados")
                    try:
                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                        if not acrescimos.empty:
                            # Criar visual mais rico para acréscimos
                            # Separar acréscimos por tipo
                            assistentes = acrescimos[acrescimos['tipo'] == 'Assistente']
                            fornecedores = acrescimos[acrescimos['tipo'] == 'Fornecedor']
                            outros = acrescimos[~acrescimos['tipo'].isin(['Assistente', 'Fornecedor'])]
                            
                            # Display usando métrica para melhor visualização
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                total_assistentes = assistentes['valor'].sum() if not assistentes.empty else 0
                                st.metric("Total Assistentes", f"R$ {total_assistentes:.2f}")
                                
                            with col2:
                                total_fornecedores = fornecedores['valor'].sum() if not fornecedores.empty else 0
                                st.metric("Total Fornecedores", f"R$ {total_fornecedores:.2f}")
                                
                            with col3:
                                total_outros = outros['valor'].sum() if not outros.empty else 0
                                st.metric("Total Outros", f"R$ {total_outros:.2f}")
                            
                            # Criar DataFrame para exibição
                            df_acrescimos = acrescimos[['tipo', 'fornecedor', 'valor', 'descricao']].copy()
                            df_acrescimos.columns = ['Tipo', 'Fornecedor/Assistente', 'Valor (R$)', 'Descrição']

                            # Formatar valores
                            df_acrescimos['Valor (R$)'] = df_acrescimos['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')

                            # Exibir tabela com melhor design
                            st.dataframe(
                                df_acrescimos, 
                                hide_index=True,
                                use_container_width=True,
                                column_config={
                                    "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
                                    "Fornecedor/Assistente": st.column_config.TextColumn("Fornecedor/Assistente", width="medium"),
                                    "Valor (R$)": st.column_config.TextColumn("Valor (R$)", width="small"),
                                    "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                                }
                            )

                            # Calcular valor total 
                            valor_total = float(proposta['valor']) + acrescimos['valor'].sum()
                            st.metric("Valor Total da Proposta", f"R$ {valor_total:.2f}", 
                                      delta=f"R$ {acrescimos['valor'].sum():.2f} em acréscimos")
                        else:
                            st.info("Nenhum acréscimo cadastrado para esta proposta.")
                    except Exception as e:
                        st.error(f"Erro ao carregar acréscimos: {str(e)}")
                
                with tab_pagamentos:
                    st.markdown("### Resumo Financeiro")
                    
                    # 1. Exibir resumo de pagamentos ao cliente
                    st.subheader("Pagamentos do Cliente")
                    try:
                        # Aqui você pode conectar com o módulo financeiro
                        # Para demonstração, vamos mostrar valores fictícios baseados nos acréscimos
                        
                        # Valor base da proposta
                        valor_base = float(proposta['valor'])
                        
                        # Obter acréscimos se existirem
                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                        valor_acrescimos = acrescimos['valor'].sum() if not acrescimos.empty else 0
                        
                        # Valor total
                        valor_total = valor_base + valor_acrescimos
                        
                        # Criar tabela de pagamentos ao cliente
                        st.write(f"**Valor base:** R$ {valor_base:.2f}")
                        st.write(f"**Valor acréscimos:** R$ {valor_acrescimos:.2f}")
                        st.write(f"**Valor total a receber:** R$ {valor_total:.2f}")
                        
                        # Aqui poderia exibir um histórico de pagamentos já recebidos
                        # st.write("**Pagamentos recebidos:** R$ X.XX")
                        # st.write("**Saldo a receber:** R$ X.XX")
                        
                    except Exception as e:
                        st.error(f"Erro ao carregar resumo financeiro: {str(e)}")
                    
                    # 2. Exibir resumo de pagamentos a fornecedores/assistentes
                    st.subheader("Pagamentos a Fornecedores/Assistentes")
                    try:
                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                        if not acrescimos.empty:
                            # Agrupar por tipo e fornecedor
                            resumo = acrescimos.groupby(['tipo', 'fornecedor'])['valor'].sum().reset_index()
                            resumo.columns = ['Tipo', 'Fornecedor/Assistente', 'Valor a Pagar (R$)']
                            
                            # Formatar valores
                            resumo['Valor a Pagar (R$)'] = resumo['Valor a Pagar (R$)'].apply(lambda x: f'R$ {float(x):.2f}')
                            
                            # Exibir tabela de pagamentos
                            st.dataframe(resumo, hide_index=True, use_container_width=True)
                        else:
                            st.info("Nenhum pagamento pendente para fornecedores ou assistentes.")
                    except Exception as e:
                        st.error(f"Erro ao carregar pagamentos a fornecedores: {str(e)}")
                
                # Botões para ações na proposta
                st.write("---")
                col_botoes1, col_botoes2, col_botoes3 = st.columns(3)
                
                with col_botoes1:
                    # Botão para gerar PDF de fechamento
                    if st.button("📄 Gerar PDF de Fechamento", type="primary", use_container_width=True):
                        try:
                            # Primeiro recuperar os acréscimos da proposta
                            acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                            
                            # Gerar nome de arquivo temporário
                            import tempfile
                            import os
                            
                            # Criar diretório temporário se não existir
                            os.makedirs("pdfs", exist_ok=True)
                            
                            # Gerar nome do arquivo
                            filename = f"pdfs/proposta_{proposta['numero']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            
                            # Gerar o PDF
                            gerar_pdf_fechamento(proposta, cliente, acrescimos, filename)
                            
                            # Exibir link para download
                            with open(filename, "rb") as pdf_file:
                                PDFbyte = pdf_file.read()
                                
                            st.success("PDF gerado com sucesso!")
                            st.download_button(
                                label="📥 Baixar PDF", 
                                data=PDFbyte,
                                file_name=f"proposta_{proposta['numero']}_fechamento.pdf",
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"Erro ao gerar PDF: {str(e)}")
                
                with col_botoes2:
                    # Botão para marcar proposta como finalizada
                    if st.button("✅ Finalizar Proposta", use_container_width=True):
                        try:
                            # Aqui implementaríamos a lógica para marcar a proposta como finalizada
                            # Atualizando seu status para um novo valor como "Finalizada" ou "Concluída"
                            st.session_state.db.atualizar_proposta(
                                proposta_id=proposta['id'],
                                status="Concluída"  # Novo status para propostas finalizadas
                            )
                            st.success("Proposta marcada como finalizada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao finalizar proposta: {str(e)}")
                
                with col_botoes3:
                    # Botão para gerar transações financeiras
                    if st.button("💰 Gerar Transações Financeiras", use_container_width=True):
                        try:
                            # Aqui implementaríamos a lógica para gerar as transações financeiras
                            # similar à que existia no módulo de integração
                            resultado = st.session_state.db.gerar_transacoes_proposta(proposta['id'])
                            
                            if resultado.get("status") == "já existem transações":
                                st.info(f"⚠️ Já existem {resultado.get('count', 0)} transações para esta proposta.")
                            elif resultado.get("status") == "sucesso":
                                st.success(f"""
                                ✅ Transações geradas com sucesso!
                                - Receita ID: {resultado.get('receita_id')}
                                - Despesas geradas: {resultado.get('total_despesas')}
                                """)
                            else:
                                st.warning("⚠️ Não foi possível gerar as transações. Verifique os dados da proposta.")
                        except Exception as e:
                            st.error(f"Erro ao gerar transações financeiras: {str(e)}")

            except Exception as e:
                st.error(f"Erro ao processar proposta selecionada: {str(e)}")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")

def mostrar_importacao():
    st.subheader("Importar Propostas")

    # Instruções para o usuário
    st.write("""
    Para importar propostas, seu arquivo CSV deve ter o seguinte formato:
    - Arquivo CSV com separador ponto e vírgula (;)
    - Colunas necessárias:
        - cliente_nome (obrigatório): Nome do cliente existente no sistema
        - descricao (obrigatório): Descrição da proposta
        - valor (obrigatório): Valor em Reais (ex: 1500.00)
        - status: Status da proposta ("Aberta", "Fechada", "Recusada")
        - tipo_proposta: Tipo de proposta
        - data_inicio: Data de início (formato: DD/MM/YYYY)
        - data_fim: Data de fim (formato: DD/MM/YYYY)
    """)

    # Download de template para o usuário
    col1, col2 = st.columns([1, 2])
    with col1:
        template = gerar_template_csv("Proposta")
        st.download_button(
            "📝 Baixar Template CSV",
            template,
            "template_proposta.csv",
            "text/csv",
            help="Baixe este template, preencha com seus dados e faça upload para importar"
        )

    with col2:
        st.info("""
        O template contém todas as colunas necessárias para importar propostas.
        Preencha os dados e faça upload do arquivo abaixo.
        """)

    # Upload do arquivo
    st.subheader("Upload do arquivo")
    arquivo = st.file_uploader(
        "Selecione o arquivo CSV",
        type=['csv'],
        key="proposta_file_uploader"
    )

    if arquivo:
        if st.button("Importar Propostas", key="importar_propostas_button", type="primary"):
            try:
                # Adicionar o tipo "Proposta" no importador
                with st.spinner("Importando propostas..."):
                    sucesso, mensagem = importar_cadastros(arquivo, "Proposta", st.session_state.db)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)
            except Exception as e:
                st.error(f"Erro ao importar propostas: {str(e)}")

def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename, usar_template=False):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    
    # IMPORTANTE: Carregar dados atualizados da proposta diretamente do banco
    # para garantir que estamos usando as informações mais recentes
    import pandas as pd
    print(f"DEBUG PDF: Recarregando dados atualizados da proposta #{proposta.get('numero')}")
    
    # Usar duas abordagens para garantir redundância e segurança
    
    # 1. Consulta SQL direta para pegar os dados mais recentes
    try:
        if 'id' in proposta:
            from sqlalchemy.sql import text
            from utils.database import Session
            
            session = Session()
            try:
                # Consulta SQL direta para garantir dados mais atualizados
                result = session.execute(
                    text("""
                    SELECT id, numero, cliente_id, descricao, valor, status, 
                           tipo_proposta, data_inicio, data_fim, prazo_entrega, 
                           data_proposta, status_pagamento_base, previsao_dias 
                    FROM propostas 
                    WHERE id = :id
                    """),
                    {"id": proposta['id']}
                ).fetchone()
                
                if result:
                    # Atualizar dados da proposta com os valores do banco
                    proposta_dict = {
                        'id': result[0],
                        'numero': result[1],
                        'cliente_id': result[2],
                        'descricao': result[3],
                        'valor': result[4],
                        'status': result[5],
                        'tipo_proposta': result[6],
                        'data_inicio': result[7],
                        'data_fim': result[8],
                        'prazo_entrega': result[9],
                        'data_proposta': result[10],
                        'status_pagamento_base': result[11],
                        'previsao_dias': result[12]
                    }
                    
                    # Atualizar a proposta com os dados novos
                    for key, value in proposta_dict.items():
                        proposta[key] = value
                    
                    print(f"DEBUG PDF: Proposta recarregada com SQL direto! ID={proposta['id']}")
                    print(f"DEBUG PDF: Data da proposta: {proposta['data_proposta']}")
                    print(f"DEBUG PDF: Data início: {proposta['data_inicio']}")
                    print(f"DEBUG PDF: Data fim: {proposta['data_fim']}")
                    print(f"DEBUG PDF: Previsão dias: {proposta['previsao_dias']}")
            except Exception as e:
                print(f"DEBUG PDF: Erro na consulta SQL direta: {str(e)}")
            finally:
                session.close()
    except Exception as e:
        print(f"DEBUG PDF: Erro ao tentar acesso direto ao banco: {str(e)}")
        
    # 2. Método secundário usando a API normal do banco de dados (como backup)
    try:
        if 'db' in st.session_state and 'id' in proposta:
            propostas_atualizadas = st.session_state.db.get_propostas()
            if not propostas_atualizadas.empty:
                proposta_atualizada = propostas_atualizadas[propostas_atualizadas['id'] == proposta['id']]
                if not proposta_atualizada.empty:
                    proposta_backup = proposta_atualizada.iloc[0]
                    print(f"DEBUG PDF: Proposta também recarregada via API normal! ID={proposta_backup['id']}")
    except Exception as e:
        print(f"DEBUG PDF: Erro ao recarregar proposta via API: {str(e)}")
    
    if usar_template:
        try:
            from utils.pdf_merger import preencher_template_canva
            dados = {
                'cliente': cliente['nome'],
                'valor': float(proposta['valor']),
                'data': datetime.now().strftime('%d/%m/%Y'),
                'descricao': proposta['descricao']
            }
            template_path = "templates/proposta_template.pdf"
            preencher_template_canva(template_path, dados, filename)
            return filename
        except Exception as e:
            st.warning(f"Não foi possível usar o template Canva. Usando geração padrão: {str(e)}")
            # Se falhar, continua com a geração padrão
    
    # Criação do documento com ReportLab
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    styles = getSampleStyleSheet()
    
    # Criar estilo personalizado para o cabeçalho
    styles.add(ParagraphStyle(
        name='TituloAzul',
        parent=styles['Heading1'],
        textColor=colors.blue,
        spaceAfter=12
    ))
    
    elements = []
    
    # Adicionar título
    elements.append(Paragraph("PROPOSTA DE SERVIÇO", styles['TituloAzul']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Adicionar informações básicas da proposta
    elements.append(Paragraph(f"<b>Número:</b> {proposta.get('numero', '')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Cliente:</b> {cliente.get('nome', '')}", styles['Normal']))
    
    # Usar a data da proposta se disponível, senão usar a data atual
    data_proposta = proposta.get('data_proposta')
    if pd.notna(data_proposta):
        data_str = pd.to_datetime(data_proposta).strftime('%d/%m/%Y')
    else:
        data_str = datetime.now().strftime('%d/%m/%Y')
    
    elements.append(Paragraph(f"<b>Data:</b> {data_str}", styles['Normal']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Descrição:</b> {proposta.get('descricao', '')}", styles['Normal']))
    
    # Adicionar informações de prazo (se disponíveis)
    if pd.notna(proposta.get('data_inicio')) and pd.notna(proposta.get('data_fim')):
        data_inicio = pd.to_datetime(proposta['data_inicio']).strftime('%d/%m/%Y')
        data_fim = pd.to_datetime(proposta['data_fim']).strftime('%d/%m/%Y')
        elements.append(Paragraph(f"<b>Período:</b> {data_inicio} a {data_fim}", styles['Normal']))
        
        dias = (pd.to_datetime(proposta['data_fim']) - pd.to_datetime(proposta['data_inicio'])).days
        elements.append(Paragraph(f"<b>Previsão:</b> {dias} dias", styles['Normal']))
    
    elements.append(Spacer(1, 0.25*inch))
    
    # Adicionar detalhes de valor
    valor_base = float(proposta.get('valor', 0))
    elements.append(Paragraph(f"<b>Valor Base:</b> R$ {valor_base:.2f}", styles['Normal']))
    
    # Adicionar tabela de acréscimos se existirem
    if acrescimos is not None and not acrescimos.empty:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>Acréscimos:</b>", styles['Normal']))
        
        # Criar dados da tabela
        data = [['Tipo', 'Fornecedor', 'Descrição', 'Valor (R$)']]
        valor_total_acrescimos = 0
        
        for _, a in acrescimos.iterrows():
            valor = float(a.get('valor', 0))
            valor_total_acrescimos += valor
            data.append([
                a.get('tipo', ''),
                a.get('fornecedor', ''),
                a.get('descricao', ''),
                f'R$ {valor:.2f}'
            ])
        
        # Criar a tabela
        table = Table(data, colWidths=[1.2*inch, 1.5*inch, 2.5*inch, 1*inch])
        
        # Estilo da tabela
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Valor total com acréscimos
        valor_total = valor_base + valor_total_acrescimos
        elements.append(Paragraph(f"<b>Acréscimos:</b> R$ {valor_total_acrescimos:.2f}", styles['Normal']))
        elements.append(Paragraph(f"<b>Valor Total:</b> R$ {valor_total:.2f}", styles['Normal']))
    
    # Adicionar condições e termos
    elements.append(Spacer(1, 0.4*inch))
    elements.append(Paragraph("<b>CONDIÇÕES E TERMOS:</b>", styles['Heading3']))
    elements.append(Paragraph("1. Esta proposta é válida por 30 dias a partir da data de emissão.", styles['Normal']))
    elements.append(Paragraph("2. O pagamento deve ser realizado conforme condições acordadas.", styles['Normal']))
    elements.append(Paragraph("3. Alterações no escopo podem resultar em ajustes de prazo e valor.", styles['Normal']))
    
    # Adicionar assinaturas
    elements.append(Spacer(1, inch))
    elements.append(Paragraph("____________________________                    ____________________________", styles['Normal']))
    elements.append(Paragraph("         Planner Organizer                                             Cliente", styles['Normal']))
    
    # Gerar o PDF
    doc.build(elements)
    return filename