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
        ["Nova Proposta", "Lista de Propostas", "Propostas em Execução"],
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
        propostas_fechadas = st.session_state.db.get_propostas(status="Fechada")
        
        if not propostas_fechadas.empty:
            for _, proposta in propostas_fechadas.iterrows():
                with st.expander(f"Proposta #{proposta['numero']} - {proposta['cliente_nome']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Valor Base:** R$ {proposta['valor']:.2f}")
                        st.write(f"**Data Início:** {proposta['data_inicio'].strftime('%d/%m/%Y')}")
                    
                    with col2:
                        st.write(f"**Status Execução:** {proposta['status_execucao']}")
                        if proposta['data_fim']:
                            st.write(f"**Data Fim:** {proposta['data_fim'].strftime('%d/%m/%Y')}")
                    
                    # Adicionar fornecedor
                    st.subheader("Adicionar Fornecedor")
                    with st.form(f"form_fornecedor_{proposta['id']}"):
                        fornecedores = st.session_state.db.get_fornecedores()
                        fornecedor = st.selectbox("Fornecedor", fornecedores['descricao'].tolist())
                        valor_fornecedor = st.number_input("Valor", min_value=0.0, step=0.01)
                        
                        if st.form_submit_button("Registrar Fornecedor"):
                            # Registrar comissão a receber
                            st.session_state.db.add_transacao(
                                tipo="receita_a_receber",
                                descricao=f"Comissão - Proposta #{proposta['numero']}",
                                valor=valor_fornecedor,
                                categoria="Comissão",
                                origem_tipo="fornecedor"
                            )
                            st.success("Fornecedor registrado e comissão gerada!")
                    
                    # Adicionar assistente
                    st.subheader("Adicionar Assistente")
                    with st.form(f"form_assistente_{proposta['id']}"):
                        assistentes = st.session_state.db.get_assistentes()
                        assistente = st.selectbox("Assistente", assistentes['nome'].tolist())
                        valor_assistente = st.number_input("Valor", min_value=0.0, step=0.01, key=f"valor_assist_{proposta['id']}")
                        
                        if st.form_submit_button("Registrar Assistente"):
                            # Registrar pagamento a assistente
                            st.session_state.db.add_transacao(
                                tipo="despesa",
                                descricao=f"Pagamento Assistente - Proposta #{proposta['numero']}",
                                valor=valor_assistente,
                                categoria="Assistente"
                            )
                            st.success("Assistente registrado e pagamento gerado!")
                    
                    # Adicionar produtos
                    st.subheader("Adicionar Produtos")
                    with st.form(f"form_produtos_{proposta['id']}"):
                        produtos = st.session_state.db.get_produtos()
                        produto = st.selectbox("Produto", produtos['nome'].tolist())
                        quantidade = st.number_input("Quantidade", min_value=1, step=1)
                        produto_info = produtos[produtos['nome'] == produto].iloc[0]
                        valor_total = quantidade * float(produto_info['preco_venda'].replace('R$ ', '').replace(',', '.'))
                        
                        if st.form_submit_button("Adicionar Produto"):
                            # Registrar venda
                            st.session_state.db.add_venda(
                                cliente_id=proposta['cliente_id'],
                                produtos=[{
                                    'produto_id': produto_info['id'],
                                    'quantidade': quantidade,
                                    'valor': valor_total
                                }],
                                proposta_id=proposta['id']
                            )
                            st.success("Produto adicionado com sucesso!")
                    
                    # Gerar fatura de fechamento
                    if st.button("Gerar Fatura de Fechamento", key=f"fatura_{proposta['id']}"):
                        total_fornecedores = 0  # Somar valores dos fornecedores
                        total_assistentes = 0   # Somar valores dos assistentes
                        total_produtos = 0      # Somar valores dos produtos
                        valor_final = float(proposta['valor']) + total_fornecedores + total_assistentes + total_produtos
                        
                        # Gerar PDF com fatura
                        try:
                            # Garantir que o diretório pdfs existe
                            import os
                            if not os.path.exists("pdfs"):
                                os.makedirs("pdfs")
                            
                            filename = f"pdfs/fatura_proposta_{proposta['numero']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            
                            # Buscar cliente
                            cliente = clientes[clientes['id'] == proposta['cliente_id']].iloc[0]
                            
                            # Buscar acréscimos
                            acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                            
                            # Gerar PDF com parâmetros corretos
                            gerar_pdf_fechamento(proposta, cliente, acrescimos, filename)
                            
                            st.success("Fatura gerada com sucesso!")
                            
                            # Disponibilizar o download do PDF gerado
                            with open(filename, "rb") as file:
                                st.download_button(
                                    label="Baixar Fatura em PDF",
                                    data=file,
                                    file_name=f"fatura_proposta_{proposta['numero']}.pdf",
                                    mime="application/pdf",
                                    key="download_pdf_fatura"
                                )
                        except Exception as e:
                            st.error(f"Erro ao gerar PDF: {str(e)}")
                            print(f"Erro detalhado ao gerar PDF: {str(e)}")
        else:
            st.info("Não há propostas em execução.")
        st.write("""
        A integração entre módulos agora acontece de forma automática.
        """)
    # Opção de importação removida conforme solicitação do cliente

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

        # Selecionar proposta
        proposta_display = [
            f"Proposta #{p['numero']} - {p['nome']}" 
            for _, p in propostas.iterrows()
        ]

        with st.form("selecionar_proposta"):
            proposta_selecionada = st.selectbox(
                "Selecione a Proposta",
                proposta_display
            )
            submited = st.form_submit_button("Selecionar")

        if proposta_selecionada and submited:
            try:
                # Extrair número da proposta
                numero_proposta = int(proposta_selecionada.split('#')[1].split(' -')[0])
                proposta = propostas[propostas['numero'] == numero_proposta].iloc[0]

                # Exibir detalhes da proposta
                st.write(f"**Cliente:** {proposta['nome']}")
                st.write(f"**Descrição:** {proposta['descricao']}")
                st.write(f"**Valor Base:** R$ {float(proposta['valor']):.2f}")

                # Seção de acréscimos
                st.subheader("Adicionar Acréscimos")

                # Verificar se a proposta está fechada e mostrar alerta
                if proposta['status'] == 'Fechada':
                    st.warning("Esta proposta está fechada, mas você ainda pode adicionar acréscimos se necessário.")
                
                with st.form("adicionar_acrescimo", clear_on_submit=True):
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
                            # Carregar lista de fornecedores do banco de dados ou usar valores padrão
                            try:
                                fornecedores = st.session_state.db.get_fornecedores()
                                if not fornecedores.empty:
                                    fornecedor_opcoes = fornecedores['nome'].tolist()
                                else:
                                    st.info("Lista de fornecedores não encontrada, usando valores padrão.")
                                    fornecedor_opcoes = ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                            except Exception as e:
                                st.info("Erro ao carregar fornecedores, usando valores padrão.")
                                print(f"Erro ao carregar fornecedores: {str(e)}")
                                fornecedor_opcoes = ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                            
                            fornecedor = st.selectbox(
                                "Fornecedor",
                                options=fornecedor_opcoes,
                                key="fornecedor_select"
                            )
                            fornecedor_nome = fornecedor
                            
                        elif tipo_acrescimo == "Assistente":
                            # Carregar lista de assistentes ou usar valores padrão
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
                                    # Usar valores padrão se não houver assistentes cadastrados
                                    st.info("Nenhum assistente cadastrado, usando valores padrão.")
                                    assistente = st.selectbox(
                                        "Assistente",
                                        options=["Assistente Padrão", "Outro Assistente"],
                                        key="assistente_select_padrao"
                                    )
                                    fornecedor_nome = assistente
                            except Exception as e:
                                st.info("Erro ao carregar assistentes, usando valores padrão.")
                                print(f"Erro ao carregar assistentes: {str(e)}")
                                assistente = st.selectbox(
                                    "Assistente",
                                    options=["Assistente Padrão", "Outro Assistente"],
                                    key="assistente_select_padrao"
                                )
                                fornecedor_nome = assistente

                    # Garantir que sempre tenhamos um fornecedor ou assistente
                    if not fornecedor_nome and tipo_acrescimo in ["Organização", "Marcenaria", "Produto"]:
                        fornecedor_nome = f"{tipo_acrescimo} Padrão"

                    descricao_acrescimo = st.text_area("Descrição", height=80, key="descricao_acrescimo")
                    valor_acrescimo = st.number_input("Valor (R$)", min_value=0.0, step=0.01, value=100.0, key="valor_acrescimo")

                    # Salvar ID da proposta em session_state para uso após POST
                    proposta_id_atual = int(proposta['id'])
                    st.session_state.proposta_atual_id = proposta_id_atual
                    
                    # Botão para adicionar acréscimo
                    submitted = st.form_submit_button("Adicionar Acréscimo", use_container_width=True, type="primary")
                    
                    if submitted:
                        if valor_acrescimo <= 0:
                            st.error("Por favor, insira um valor válido maior que zero.")
                        else:
                            # Sempre temos um fornecedor_nome, então podemos prosseguir
                            proposta_id_atual = int(proposta['id'])
                            
                            try:
                                # Logs para depuração
                                print(f"DEBUG PROPOSTAS UI: Iniciando adição de acréscimo para proposta ID={proposta_id_atual}")
                                print(f"DEBUG PROPOSTAS UI: Parâmetros - tipo={tipo_acrescimo}, fornecedor={fornecedor_nome}, valor={valor_acrescimo}")
                                
                                # Usar o helper para adicionar acréscimo
                                from utils.propostas_helper import st_adicionar_acrescimo
                                
                                # Chamar função simplificada
                                sucesso, acrescimo_id = st_adicionar_acrescimo(
                                    proposta_id_atual,
                                    tipo_acrescimo,
                                    fornecedor_nome,
                                    descricao_acrescimo,
                                    valor_acrescimo
                                )
                                
                                # Se bem-sucedido, o helper já faz rerun, então não precisamos fazer mais nada
                                if sucesso:
                                    # Limpar campos após sucesso
                                    if 'valor_acrescimo' in st.session_state:
                                        st.session_state.valor_acrescimo = 0.0
                                    if 'descricao_acrescimo' in st.session_state:
                                        st.session_state.descricao_acrescimo = ""
                                    
                                    # Salvar dados para manter a mesma proposta selecionada após o rerun
                                    st.session_state.proposta_atual_id = proposta_id_atual
                                    st.session_state.ultimo_acrescimo_id = acrescimo_id
                            except Exception as e:
                                print(f"DEBUG PROPOSTAS UI CRITICAL ERROR: {str(e)}")
                                import traceback
                                traceback.print_exc()
                                st.error(f"Erro ao adicionar acréscimo: {str(e)}")
                                print(f"Erro detalhado ao adicionar acréscimo: {str(e)}")

                # Exibir acréscimos existentes
                try:
                    print(f"DEBUG PROPOSTAS UI: Buscando acréscimos para proposta ID={proposta['id']}")
                    # Adicionar timestamp para evitar caching
                    import time
                    timestamp = time.time()
                    acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                    print(f"DEBUG PROPOSTAS UI: Query acréscimos executada em {time.time() - timestamp:.2f}s")
                    
                    # Sempre exibir o cabeçalho da seção e separador
                    st.markdown("---")
                    st.subheader("Acréscimos Adicionados")
                    
                    # Botão para atualizar/recarregar os acréscimos
                    if st.button("🔄 Atualizar Lista de Acréscimos", key="refresh_acrescimos", type="secondary", use_container_width=True):
                        st.experimental_rerun()
                    
                    if acrescimos.empty:
                        # Exibir mensagem quando não houver acréscimos
                        st.info("Nenhum acréscimo cadastrado para esta proposta.")
                        
                        # Exibir apenas o valor base da proposta
                        valor_total = float(proposta['valor'])
                        st.write(f"**Valor Base da Proposta:** R$ {valor_total:.2f}")
                    else:
                        print(f"DEBUG PROPOSTAS UI: Encontrados {len(acrescimos)} acréscimos")
                        
                        # Criar DataFrame para exibição
                        df_acrescimos = acrescimos[['id', 'tipo', 'fornecedor', 'valor', 'descricao', 'status_pagamento', 'data_cadastro']].copy()
                        
                        # Renomear colunas para exibição
                        df_acrescimos.columns = ['ID', 'Tipo', 'Fornecedor', 'Valor (R$)', 'Descrição', 'Status Pgto', 'Data']
                        
                        # Formatar valores e data
                        df_acrescimos['Valor (R$)'] = df_acrescimos['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')
                        df_acrescimos['Data'] = df_acrescimos['Data'].apply(lambda x: x.strftime('%d/%m/%Y') if x else '')

                        # Exibir tabela com os acréscimos
                        st.dataframe(df_acrescimos, hide_index=True)

                        # Calcular e exibir valor total com acréscimos
                        try:
                            valor_acrescimos = acrescimos['valor'].sum()
                            valor_base = float(proposta['valor'])
                            valor_total = valor_base + valor_acrescimos
                            
                            # Exibir valores detalhados em um container destacado
                            st.markdown("---")
                            st.subheader("Resumo Financeiro")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.info(f"**Valor Base**\nR$ {valor_base:.2f}")
                            with col2:
                                st.info(f"**Total Acréscimos**\nR$ {valor_acrescimos:.2f}")
                            with col3:
                                st.success(f"**Valor Total**\nR$ {valor_total:.2f}")
                        except Exception as calc_error:
                            print(f"DEBUG PROPOSTAS UI ERROR: Erro ao calcular valores: {str(calc_error)}")
                            st.error(f"Erro ao calcular valores: {str(calc_error)}")

                except Exception as e:
                    print(f"DEBUG PROPOSTAS UI ERROR: Erro ao carregar acréscimos: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    st.error(f"Erro ao carregar acréscimos: {str(e)}")
                    
                # Adicionar botão para gerar PDF de fechamento sempre disponível para propostas fechadas
                st.markdown("---")
                if proposta['status'] == 'Fechada':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📄 Gerar PDF de Fechamento", 
                                    key="gerar_pdf_fechamento", 
                                    type="primary", 
                                    use_container_width=True):
                            try:
                                st.info("Gerando PDF de fechamento... Por favor, aguarde.")
                                # Buscar dados do cliente
                                cliente = st.session_state.db.get_cliente_by_id(proposta['cliente_id'])
                                
                                # Obter acréscimos da proposta 
                                acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                                
                                # Nome do arquivo
                                filename = f"pdfs/proposta_{proposta['numero']}_{proposta['cliente_id']}_fechamento.pdf"
                                
                                # Gerar PDF com parâmetros corretos
                                import os
                                from utils.pdf_generator import gerar_pdf_fechamento
                                
                                # Garantir que o diretório existe
                                if not os.path.exists('pdfs'):
                                    os.makedirs('pdfs')
                                
                                # Converter cliente de dataframe para dicionário se necessário
                                cliente_dict = cliente
                                if hasattr(cliente, 'to_dict'):
                                    cliente_dict = cliente.to_dict()
                                elif not isinstance(cliente, dict):
                                    # Caso seja um objeto SQLAlchemy, extrair atributos
                                    cliente_dict = {'nome': cliente.nome if hasattr(cliente, 'nome') else "Cliente"}
                                
                                # Debugging
                                st.write("⏳ Gerando PDF... Por favor, aguarde.")
                                st.write(f"📄 Nome do arquivo: {filename}")
                                st.write(f"👤 Cliente: {cliente_dict.get('nome', 'N/A')}")
                                st.write(f"💰 Valor base: R$ {float(proposta.get('valor', 0)):.2f}")
                                
                                # Usar o helper para gerar PDF
                                from utils.propostas_helper import st_gerar_pdf_proposta
                                
                                # Chamar função simplificada
                                st_gerar_pdf_proposta(proposta['id'], filename)
                            except Exception as pdf_error:
                                st.error(f"Erro ao gerar PDF: {str(pdf_error)}")
                                import traceback
                                traceback.print_exc()
                    
                    with col2:
                        if st.button("💰 Marcar como Paga", 
                                   key="marcar_como_paga", 
                                   type="secondary", 
                                   use_container_width=True):
                            try:
                                # Usar o helper para marcar como paga
                                from utils.propostas_helper import st_marcar_proposta_como_paga
                                st_marcar_proposta_como_paga(proposta['id'])
                            except Exception as pay_error:
                                st.error(f"Erro ao atualizar status de pagamento: {str(pay_error)}")
                                import traceback
                                traceback.print_exc()

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

# Função auxiliar para gerar PDF com template
def gerar_pdf_com_template(proposta, cliente, acrescimos, filename):
    """
    Função auxiliar que usa template Canva para gerar PDF
    """
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
        st.warning(f"Não foi possível usar o template Canva: {str(e)}")
        # Usar a função padrão se falhar
        return gerar_pdf_fechamento(proposta, cliente, acrescimos, filename)