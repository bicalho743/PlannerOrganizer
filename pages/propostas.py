import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import time

# Dependências para exportação e manipulação de PDFs
try:
    from utils.propostas_helper import fechar_proposta, gerar_pdf_fechamento
except Exception as e:
    print(f"Erro ao importar funções auxiliares: {str(e)}")
    
    # Funções mock para o caso de erros de importação
    def fechar_proposta(db, proposta_id):
        st.warning("Função de fechamento de proposta não disponível")
        return False, "Função não disponível"
        
    def gerar_pdf_fechamento(proposta, cliente, acrescimos, filename):
        st.warning("Função de geração de PDF não disponível")
        return None


def show():
    """Função principal do módulo de Propostas"""
    st.title("PROPOSTAS")
    
    # Verificar se a sessão de banco de dados está disponível
    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        st.stop()
    
    # Definir abas na interface
    tabs = st.tabs([
        "Nova Proposta", 
        "Lista de Propostas", 
        "Propostas em Execução",
        "Importação"
    ])
    
    # Tab 1: Nova Proposta
    with tabs[0]:
        mostrar_nova_proposta()
    
    # Tab 2: Lista de Propostas
    with tabs[1]:
        mostrar_lista_propostas()
    
    # Tab 3: Propostas em Execução
    with tabs[2]:
        mostrar_andamento()
    
    # Tab 4: Importação
    with tabs[3]:
        mostrar_importacao()


def mostrar_nova_proposta():
    """Interface para criar uma nova proposta"""
    st.subheader("NOVA PROPOSTA")
    
    # Verificar se temos clientes
    try:
        clientes = st.session_state.db.get_clientes()
        if clientes.empty:
            st.error("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {str(e)}")
        return
    
    # Formulário para nova proposta
    with st.form("nova_proposta"):
        # Informações básicas
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção de cliente
            clientes_lista = clientes['nome'].tolist()
            cliente = st.selectbox("Cliente:", clientes_lista)
            
            # Descrição
            descricao = st.text_area("Descrição:", height=100)
            
            # Status
            status_options = ["Aberta", "Fechada", "Recusada"]
            status = st.selectbox("Status:", status_options)
        
        with col2:
            # Valor
            valor = st.number_input("Valor (R$):", min_value=0.0, format='%0.2f')
            
            # Tipo de proposta
            tipo_proposta = st.selectbox(
                "Tipo de Proposta:",
                ["Serviço", "Produto", "Misto"]
            )
            
            # Datas
            data_inicio = st.date_input("Data de Início:", datetime.now().date())
            
            # Calcular prazo previsto
            prazo_dias = st.number_input("Prazo de Entrega (dias):", min_value=1, value=15)
            data_fim_prevista = data_inicio + timedelta(days=prazo_dias)
            
            # Exibir data de término calculada (não editável)
            st.markdown(f"**Data de Término Prevista:** {data_fim_prevista.strftime('%d/%m/%Y')}")
            
        # Botão de salvar
        submitted = st.form_submit_button("Salvar Proposta")
        
        if submitted:
            try:
                # Buscar o ID do cliente
                cliente_id = clientes[clientes['nome'] == cliente]['id'].iloc[0]
                
                # Salvar proposta
                novo_numero = st.session_state.db.add_proposta(
                    cliente_id=cliente_id,
                    descricao=descricao,
                    valor=valor,
                    status=status,
                    tipo_proposta=tipo_proposta,
                    data_inicio=data_inicio,
                    data_fim=data_fim_prevista,
                    previsao_dias=prazo_dias
                )
                
                if novo_numero:
                    st.success(f"Proposta #{novo_numero} salva com sucesso!")
                    
                    # Se o status já for fechado, fechar a proposta
                    if status == "Fechada":
                        proposta_id = st.session_state.db.get_proposta_by_numero(novo_numero)['id'].iloc[0]
                        fechar_proposta(st.session_state.db, proposta_id)
                    
                    # Recarregar a página
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erro ao salvar proposta.")
            except Exception as e:
                st.error(f"Erro ao salvar proposta: {str(e)}")


def mostrar_lista_propostas():
    """Interface para exibir e gerenciar a lista de propostas"""
    st.subheader("📋 LISTA DE PROPOSTAS")
    
    try:
        # Carregar propostas
        propostas = st.session_state.db.get_propostas()
        if propostas.empty:
            st.warning("Nenhuma proposta cadastrada.")
            return

        # Juntar dados de propostas com clientes
        clientes = st.session_state.db.get_clientes()
        
        # Verificar se temos clientes
        if clientes.empty:
            st.error("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
            return
            
        propostas = propostas.merge(
            clientes[['id', 'nome']], 
            left_on='cliente_id', 
            right_on='id', 
            suffixes=('', '_cliente')
        )
        
        # Salvar propostas completas na session_state para uso posterior
        st.session_state.propostas_completas = propostas.copy()
        
        # Preparar dados para exibição em tabela editável
        df_exibicao = pd.DataFrame()
        df_exibicao['ID'] = propostas['id']
        df_exibicao['Número'] = propostas['numero']
        df_exibicao['Cliente'] = propostas['nome']
        df_exibicao['Descrição'] = propostas['descricao']
        df_exibicao['Valor (R$)'] = propostas['valor'].apply(lambda x: f'R$ {float(x):.2f}')
        df_exibicao['Status'] = propostas['status']
        
        # Formatar datas para exibição
        df_exibicao['Data'] = propostas['data_proposta'].apply(
            lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
        )
        
        # Adicionar coluna de previsão de dias
        df_exibicao['Previsão (Dias)'] = propostas['previsao_dias']
        
        # Permitir edição diretamente na tabela
        edited_df = st.data_editor(
            df_exibicao,
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
                    disabled=False,  # Permitimos editar a data
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
        
        # Botões de ações principais em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            # Botão para salvar alterações
            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                contador_atualizacoes = 0
                
                # Verificar cada linha do DataFrame editado
                for i, row in edited_df.iterrows():
                    proposta_id = row['ID']
                    proposta_original = st.session_state.propostas_completas[st.session_state.propostas_completas['id'] == proposta_id].iloc[0]
                    
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
                        # Extração do valor monetário
                        valor_str = row['Valor (R$)']
                        
                        # Remover símbolo monetário
                        valor_str = valor_str.replace('R$', '').strip()
                        
                        # Lidar com diferentes formatos
                        if ',' in valor_str and '.' in valor_str:
                            # Formato brasileiro com separador de milhares (1.234,56)
                            valor_str = valor_str.replace('.', '').replace(',', '.')
                        elif ',' in valor_str:
                            # Formato com vírgula como decimal (1234,56)
                            valor_str = valor_str.replace(',', '.')
                        # Caso contrário, mantém o formato com ponto decimal (1234.56)
                            
                        valor_editado = float(valor_str)
                        
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
                        data_original = pd.to_datetime(proposta_original['data_proposta']).strftime('%d/%m/%Y') if pd.notna(proposta_original['data_proposta']) else ""
                        if row['Data'] != data_original:
                            # Converter a data para o formato do banco
                            try:
                                # Tentar diferentes formatos de data
                                nova_data = None
                                try:
                                    # Primeiro tenta inferir automaticamente
                                    nova_data = pd.to_datetime(row['Data']).date()
                                except:
                                    try:
                                        # Formato DD/MM/YYYY (brasileiro)
                                        nova_data = pd.to_datetime(row['Data'], format='%d/%m/%Y').date()
                                    except:
                                        try:
                                            # Formato MM/DD/YYYY (americano)
                                            nova_data = pd.to_datetime(row['Data'], format='%m/%d/%Y').date()
                                        except:
                                            # Formato YYYY-MM-DD (ISO)
                                            nova_data = pd.to_datetime(row['Data'], format='%Y-%m-%d').date()
                                
                                # Atualizar não só a data_proposta, mas também data_inicio
                                st.session_state.db.atualizar_proposta(
                                    proposta_id=proposta_id,
                                    data_proposta=nova_data,
                                    data_inicio=nova_data
                                )
                                
                                # Se temos previsão de dias, calcular nova data de fim
                                dias_previstos = proposta_original.get('previsao_dias', 0)
                                if dias_previstos and dias_previstos > 0:
                                    data_fim_nova = nova_data + pd.Timedelta(days=dias_previstos)
                                    st.session_state.db.atualizar_proposta(
                                        proposta_id=proposta_id,
                                        data_fim=data_fim_nova
                                    )
                                
                                contador_atualizacoes += 1
                            except Exception as e:
                                st.warning(f"Formato de data inválido para a proposta {row['Número']}: {row['Data']}. Erro: {str(e)}. Use o formato DD/MM/YYYY.")
                    except Exception as e:
                        st.warning(f"Erro ao processar data para a proposta {row['Número']}: {str(e)}")
                                
                    # Verificar se houve alteração na previsão de dias
                    previsao_dias_original = proposta_original.get('previsao_dias')
                    if pd.notna(row['Previsão (Dias)']) and pd.notna(previsao_dias_original) and row['Previsão (Dias)'] != previsao_dias_original:
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
                                    data_fim=fim.date(),
                                    previsao_dias=dias
                                )
                                contador_atualizacoes += 1
                        except Exception as e:
                            st.warning(f"Erro ao atualizar datas baseadas na previsão de dias: {str(e)}")
                
                if contador_atualizacoes > 0:
                    st.success(f"{contador_atualizacoes} atualizações realizadas com sucesso!")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração detectada.")
        
        with col2:
            # Botão para fechar propostas selecionadas
            if st.button("🔒 Fechar Propostas Selecionadas", type="secondary", use_container_width=True):
                # Fechar propostas que foram marcadas como "Fechada" no Status
                propostas_para_fechar = edited_df[edited_df['Status'] == 'Fechada']
                
                if propostas_para_fechar.empty:
                    st.warning("Nenhuma proposta foi marcada como 'Fechada'. Selecione o status 'Fechada' nas propostas que deseja fechar.")
                else:
                    contador_fechamentos = 0
                    for _, row in propostas_para_fechar.iterrows():
                        # Verificar se a proposta já estava fechada
                        proposta_id = row['ID']
                        proposta_original = st.session_state.propostas_completas[st.session_state.propostas_completas['id'] == proposta_id].iloc[0]
                        
                        if proposta_original['status'] != 'Fechada':
                            sucesso, mensagem = fechar_proposta(st.session_state.db, proposta_id)
                            if sucesso:
                                contador_fechamentos += 1
                    
                    if contador_fechamentos > 0:
                        st.success(f"{contador_fechamentos} proposta(s) fechada(s) com sucesso!")
                        st.rerun()
                    else:
                        st.info("Nenhuma proposta foi fechada. Talvez já estivessem com status 'Fechada'.")
        
        # Linha horizontal para separar
        st.markdown("---")
        
        # Seleção de proposta para ação
        st.subheader("Outras Ações")
        col1, col2 = st.columns(2)
        with col1:
            proposta_num = st.number_input("Número da proposta para ação:", 
                                         min_value=int(propostas['numero'].min()) if not propostas.empty else 1,
                                         max_value=int(propostas['numero'].max()) if not propostas.empty else 1,
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
            # Primeiro mostre a opção de template
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
                        
                        # Gerar PDF
                        if usar_template_canva:
                            # Usar função que suporta template
                            pdf_path = gerar_pdf_com_template(
                                proposta=proposta,
                                cliente={'nome': proposta['nome']},
                                acrescimos=acrescimos,
                                filename=filename
                            )
                        else:
                            # Usar função padrão
                            pdf_path = gerar_pdf_fechamento(
                                proposta=proposta,
                                cliente={'nome': proposta['nome']},
                                acrescimos=acrescimos,
                                filename=filename
                            )

                        if pdf_path:
                            st.success("PDF gerado com sucesso!")
                            
                            # Criar link para download
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="📥 Baixar PDF",
                                    data=pdf_bytes,
                                    file_name=os.path.basename(filename),
                                    mime="application/pdf",
                                    key=f"download_button_{proposta['numero']}"
                                )
                        else:
                            st.error("Não foi possível gerar o PDF.")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")

    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")


def mostrar_andamento():
    """Exibe propostas em execução e permite adicionar acréscimos"""
    st.subheader("PROPOSTAS EM EXECUÇÃO")
    try:
        propostas = st.session_state.db.get_propostas()
        if propostas.empty:
            st.warning("Nenhuma proposta cadastrada.")
            return

        # Juntar dados de propostas com clientes
        clientes = st.session_state.db.get_clientes()
        propostas = propostas.merge(
            clientes[['id', 'nome']], 
            left_on='cliente_id', 
            right_on='id', 
            suffixes=('', '_cliente')
        )

        # Filtrar apenas propostas em execução (status Fechada)
        propostas_execucao = propostas[propostas['status'] == 'Fechada'].copy()
        
        if propostas_execucao.empty:
            st.info("Nenhuma proposta em execução. Para mover uma proposta para execução, altere seu status para 'Fechada'.")
            
            # Mostrar opção para ver todas as propostas
            if st.checkbox("Mostrar todas as propostas"):
                proposta_display = [
                    f"Proposta #{p['numero']} - {p['nome']} ({p['status']})" 
                    for _, p in propostas.iterrows()
                ]
            else:
                return
        else:
            # Se temos propostas em execução, mostrar apenas essas
            proposta_display = [
                f"Proposta #{p['numero']} - {p['nome']}" 
                for _, p in propostas_execucao.iterrows()
            ]

        with st.form("selecionar_proposta_execucao"):
            proposta_selecionada = st.selectbox(
                "Selecione a Proposta",
                proposta_display
            )
            submited = st.form_submit_button("Selecionar")

        if proposta_selecionada and submited:
            try:
                # Extrair número da proposta
                numero_proposta = int(proposta_selecionada.split("#")[1].split(" ")[0])
                # Buscar proposta completa
                proposta = propostas[propostas['numero'] == numero_proposta].iloc[0]
                
                # Exibir detalhes da proposta
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Cliente:** {proposta['nome']}")
                    st.markdown(f"**Descrição:** {proposta['descricao']}")
                    st.markdown(f"**Status:** {proposta['status']}")
                
                with col2:
                    st.markdown(f"**Valor:** R$ {float(proposta['valor']):.2f}")
                    if pd.notna(proposta['data_inicio']):
                        st.markdown(f"**Data Início:** {proposta['data_inicio'].strftime('%d/%m/%Y')}")
                    if pd.notna(proposta['data_fim']):
                        st.markdown(f"**Data Término:** {proposta['data_fim'].strftime('%d/%m/%Y')}")
                
                # Verificar se a proposta tem acréscimos
                acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                
                # Exibir acréscimos existentes
                if not acrescimos.empty:
                    st.markdown("### Acréscimos da Proposta")
                    
                    df_acrescimos = pd.DataFrame()
                    df_acrescimos['ID'] = acrescimos['id']
                    df_acrescimos['Descrição'] = acrescimos['descricao']
                    df_acrescimos['Valor (R$)'] = acrescimos['valor'].apply(lambda x: f'R$ {float(x):.2f}')
                    df_acrescimos['Data'] = acrescimos['data_acrescimo'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    df_acrescimos['Tipo'] = acrescimos['tipo']
                    
                    st.dataframe(df_acrescimos)
                    
                    # Mostrar valor total (proposta + acréscimos)
                    valor_total = float(proposta['valor']) + acrescimos['valor'].sum()
                    st.markdown(f"**Valor Total (Proposta + Acréscimos):** R$ {valor_total:.2f}")
                else:
                    st.info("Esta proposta não tem acréscimos registrados.")
                
                # Formulário para adicionar acréscimo
                st.markdown("### Adicionar Acréscimo")
                
                with st.form("adicionar_acrescimo"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        descricao_acrescimo = st.text_area("Descrição do Acréscimo:", height=100)
                        tipo_acrescimo = st.selectbox(
                            "Tipo:",
                            ["Padrão", "Fornecedor", "Assistente"]
                        )
                    
                    with col2:
                        valor_acrescimo = st.number_input("Valor (R$):", min_value=0.0, format='%0.2f')
                        data_acrescimo = st.date_input("Data:", datetime.now().date())
                        
                        # Se tipo for Fornecedor, selecione fornecedor
                        fornecedor_id = None
                        if tipo_acrescimo == "Fornecedor":
                            fornecedores = st.session_state.db.get_fornecedores()
                            if not fornecedores.empty:
                                fornecedor_nome = st.selectbox(
                                    "Fornecedor:",
                                    fornecedores['nome'].tolist()
                                )
                                # Buscar ID do fornecedor
                                fornecedor_id = fornecedores[fornecedores['nome'] == fornecedor_nome]['id'].iloc[0]
                            else:
                                st.warning("Nenhum fornecedor cadastrado. Cadastre fornecedores primeiro.")
                        
                        # Se tipo for Assistente, selecione assistente
                        assistente_id = None
                        if tipo_acrescimo == "Assistente":
                            assistentes = st.session_state.db.get_assistentes()
                            if not assistentes.empty:
                                assistente_nome = st.selectbox(
                                    "Assistente:",
                                    assistentes['nome'].tolist()
                                )
                                # Buscar ID do assistente
                                assistente_id = assistentes[assistentes['nome'] == assistente_nome]['id'].iloc[0]
                            else:
                                st.warning("Nenhum assistente cadastrado. Cadastre assistentes primeiro.")
                    
                    # Botão para adicionar acréscimo
                    submited_acrescimo = st.form_submit_button("Adicionar Acréscimo")
                    
                    if submited_acrescimo:
                        try:
                            # Parâmetros para adicionar acréscimo
                            parametros = {
                                'proposta_id': proposta['id'],
                                'descricao': descricao_acrescimo,
                                'valor': valor_acrescimo,
                                'data_acrescimo': data_acrescimo,
                                'tipo': tipo_acrescimo
                            }
                            
                            # Adicionar ID do fornecedor ou assistente, se aplicável
                            if tipo_acrescimo == "Fornecedor" and fornecedor_id is not None:
                                parametros['fornecedor_id'] = fornecedor_id
                            
                            if tipo_acrescimo == "Assistente" and assistente_id is not None:
                                parametros['assistente_id'] = assistente_id
                            
                            # Adicionar acréscimo
                            sucesso = st.session_state.db.add_acrescimo(**parametros)
                            
                            if sucesso:
                                st.success("Acréscimo adicionado com sucesso!")
                                
                                # Se for um fornecedor, criar registro financeiro
                                if tipo_acrescimo == "Fornecedor" and fornecedor_id is not None:
                                    try:
                                        # Criar transação financeira de pagamento ao fornecedor
                                        st.session_state.db.add_transacao_financeira(
                                            descricao=f"Pagamento para fornecedor - {descricao_acrescimo}",
                                            valor=valor_acrescimo,
                                            tipo="Saída",
                                            data_vencimento=data_acrescimo,
                                            fornecedor_id=fornecedor_id,
                                            proposta_id=proposta['id'],
                                            status="Em Aberto"
                                        )
                                        st.info("Registro financeiro para pagamento do fornecedor criado automaticamente.")
                                    except Exception as e:
                                        st.warning(f"Não foi possível criar o registro financeiro: {str(e)}")
                                
                                # Se for um assistente, criar registro financeiro
                                if tipo_acrescimo == "Assistente" and assistente_id is not None:
                                    try:
                                        # Criar transação financeira de pagamento ao assistente
                                        st.session_state.db.add_transacao_financeira(
                                            descricao=f"Pagamento para assistente - {descricao_acrescimo}",
                                            valor=valor_acrescimo,
                                            tipo="Saída",
                                            data_vencimento=data_acrescimo,
                                            assistente_id=assistente_id,
                                            proposta_id=proposta['id'],
                                            status="Em Aberto"
                                        )
                                        st.info("Registro financeiro para pagamento do assistente criado automaticamente.")
                                    except Exception as e:
                                        st.warning(f"Não foi possível criar o registro financeiro: {str(e)}")
                                
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar acréscimo.")
                        except Exception as e:
                            st.error(f"Erro ao adicionar acréscimo: {str(e)}")
                
                # Opção para marcar proposta como paga
                st.markdown("### Marcar Proposta como Paga")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    ja_paga = st.session_state.db.verificar_proposta_paga(proposta['id'])
                    
                    if ja_paga:
                        st.success("Esta proposta já está marcada como PAGA.")
                    else:
                        if st.button("✅ Marcar como PAGA", use_container_width=True):
                            with st.spinner("Processando..."):
                                try:
                                    # Marcar proposta como paga
                                    sucesso = st.session_state.db.marcar_proposta_paga(proposta['id'])
                                    if sucesso:
                                        st.success("Proposta marcada como PAGA com sucesso!")
                                        
                                        # Criar registro financeiro de recebimento
                                        try:
                                            valor_total = float(proposta['valor'])
                                            if not acrescimos.empty:
                                                valor_total += acrescimos['valor'].sum()
                                                
                                            st.session_state.db.add_transacao_financeira(
                                                descricao=f"Recebimento - Proposta #{proposta['numero']}",
                                                valor=valor_total,
                                                tipo="Entrada",
                                                data_vencimento=datetime.now().date(),
                                                cliente_id=proposta['cliente_id'],
                                                proposta_id=proposta['id'],
                                                status="Pago"
                                            )
                                            st.info("Registro financeiro de recebimento criado automaticamente.")
                                        except Exception as e:
                                            st.warning(f"Não foi possível criar o registro financeiro: {str(e)}")
                                            
                                        st.rerun()
                                    else:
                                        st.error("Erro ao marcar proposta como paga.")
                                except Exception as e:
                                    st.error(f"Erro ao marcar proposta como paga: {str(e)}")
                
                with col2:
                    # Gerar nota fiscal/recibo
                    if st.button("🧾 Gerar Nota de Fechamento", use_container_width=True):
                        with st.spinner("Gerando documentação de fechamento..."):
                            try:
                                # Criar diretório para PDFs se não existir
                                os.makedirs("pdfs", exist_ok=True)
                                
                                # Nome do arquivo
                                filename = f"pdfs/fechamento_proposta_{proposta['numero']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                
                                # Gerar PDF de fechamento
                                pdf_path = gerar_pdf_fechamento(
                                    proposta=proposta,
                                    cliente={'nome': proposta['nome']},
                                    acrescimos=acrescimos,
                                    filename=filename
                                )
                                
                                if pdf_path:
                                    st.success("Nota de fechamento gerada com sucesso!")
                                    
                                    # Criar link para download
                                    with open(pdf_path, "rb") as pdf_file:
                                        pdf_bytes = pdf_file.read()
                                        st.download_button(
                                            label="📥 Baixar Nota de Fechamento",
                                            data=pdf_bytes,
                                            file_name=os.path.basename(filename),
                                            mime="application/pdf",
                                            key=f"download_fechamento_{proposta['numero']}"
                                        )
                                else:
                                    st.error("Não foi possível gerar a nota de fechamento.")
                            except Exception as e:
                                st.error(f"Erro ao gerar nota de fechamento: {str(e)}")
            
            except Exception as e:
                st.error(f"Erro ao processar proposta: {str(e)}")

    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")


def mostrar_importacao():
    """Interface para importação de propostas"""
    st.subheader("IMPORTAÇÃO DE PROPOSTAS")
    
    # Criar modelo CSV para download
    criar_modelo_csv()
    
    # Importação de propostas
    uploaded_file = st.file_uploader("Selecione um arquivo CSV ou Excel", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Mostrar opções avançadas
        with st.expander("Opções Avançadas"):
            col1, col2 = st.columns(2)
            with col1:
                usar_cliente_id = st.checkbox("Usar ID do Cliente", help="Selecione se o arquivo contém IDs de clientes em vez de nomes")
            with col2:
                modo_debug = st.checkbox("Modo Debug", help="Mostra informações detalhadas de diagnóstico")
        
        # Botão para importar
        if st.button("Importar Propostas"):
            try:
                # Tentar importar diretamente
                from importar_propostas_v2 import importar_propostas_v2
                
                resultados = importar_propostas_v2(
                    arquivo=uploaded_file,
                    debug_mode=modo_debug,
                    usar_cliente_id=usar_cliente_id
                )
                
                st.success(f"Importação concluída: {resultados.get('sucesso', 0)} registros importados com sucesso")
                
                if resultados.get('erros', 0) > 0:
                    st.warning(f"Erros encontrados: {resultados.get('erros', 0)}")
                    
                    # Se houver detalhes de erros, exibir
                    if 'detalhes_erros' in resultados:
                        for erro in resultados['detalhes_erros']:
                            st.error(erro)
                
                # Mostrar detalhes adicionais em modo debug
                if modo_debug and 'detalhes_debug' in resultados:
                    with st.expander("Detalhes de Debug"):
                        for debug in resultados['detalhes_debug']:
                            st.text(debug)
            
            except Exception as e:
                st.error(f"Erro ao importar propostas: {str(e)}")
                
                # Se falhar, tentar método alternativo
                st.warning("Tentando método alternativo de importação...")
                
                try:
                    # Tentar usar outro módulo de importação
                    from importacao_direta import importar_propostas_direto
                    
                    # Redefinir o ponteiro do arquivo
                    uploaded_file.seek(0)
                    
                    # Importar com método alternativo
                    resultados = importar_propostas_direto()
                    
                    if resultados.get('sucesso', 0) > 0:
                        st.success(f"Importação concluída: {resultados.get('sucesso', 0)} registros importados com sucesso")
                    else:
                        st.error("Não foi possível importar as propostas. Verifique o formato do arquivo.")
                
                except Exception as alt_e:
                    st.error(f"Ambos os métodos de importação falharam. Erro: {str(alt_e)}")


def criar_modelo_csv():
    """Cria um modelo CSV para download"""
    # Criar dataframe de exemplo
    exemplo = pd.DataFrame([
        {
            'cliente': 'Nome do Cliente 1',
            'descricao': 'Descrição da proposta 1',
            'valor': 1000.00,
            'status': 'Aberta',
            'tipo_proposta': 'Serviço',
            'data_inicio': '01/01/2025',
            'data_fim': '15/01/2025',
            'prazo_entrega': 15
        },
        {
            'cliente': 'Nome do Cliente 2',
            'descricao': 'Descrição da proposta 2',
            'valor': 2500.00,
            'status': 'Aberta',
            'tipo_proposta': 'Produto',
            'data_inicio': '15/01/2025',
            'data_fim': '30/01/2025',
            'prazo_entrega': 15
        }
    ])
    
    # Converter para CSV
    csv = exemplo.to_csv(index=False)
    
    # Criar botão de download
    st.download_button(
        label="⬇️ Baixar Modelo CSV",
        data=csv,
        file_name="modelo_propostas_para_importacao.csv",
        mime="text/csv",
    )


def gerar_pdf_com_template(proposta, cliente, acrescimos, filename):
    """
    Função auxiliar que usa template para gerar PDF
    """
    try:
        from utils.pdf_generator import gerar_pdf_proposta_fechada
        
        # Calcular valor total
        valor_total = float(proposta['valor'])
        if not acrescimos.empty:
            valor_total += acrescimos['valor'].sum()
            
        # Preparar dados para PDF
        dados_pdf = {
            'numero_proposta': proposta['numero'],
            'cliente': cliente['nome'],
            'descricao': proposta['descricao'],
            'valor': float(proposta['valor']),
            'valor_total': valor_total,
            'data_inicio': proposta['data_inicio'].strftime('%d/%m/%Y') if pd.notna(proposta['data_inicio']) else '',
            'data_fim': proposta['data_fim'].strftime('%d/%m/%Y') if pd.notna(proposta['data_fim']) else '',
            'acrescimos': [
                {
                    'descricao': row['descricao'],
                    'valor': float(row['valor']),
                    'data': row['data_acrescimo'].strftime('%d/%m/%Y') if pd.notna(row['data_acrescimo']) else '',
                    'tipo': row['tipo']
                }
                for _, row in acrescimos.iterrows()
            ] if not acrescimos.empty else []
        }
        
        # Gerar PDF
        pdf_path = gerar_pdf_proposta_fechada(dados_pdf, filename)
        return pdf_path
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF com template: {str(e)}")
        
        # Tentar método alternativo
        try:
            from utils.propostas_helper import gerar_pdf_fechamento
            return gerar_pdf_fechamento(proposta, cliente, acrescimos, filename)
        except Exception as alt_e:
            st.error(f"Também não foi possível usar o método alternativo: {str(alt_e)}")
            return None