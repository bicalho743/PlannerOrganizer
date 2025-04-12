import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.pdf_generator import gerar_pdf_fechamento
from utils.importador import importar_cadastros, gerar_template_csv

def show():
    st.title("📝 Gestão de Propostas")

    # Usar radio para selecionar a aba - Removida opção de importação
    aba_selecionada = st.radio(
        "Selecione a opção:",
        ["Nova Proposta", "Lista de Propostas", "Andamento do Trabalho"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.write("---")  # Divisor para separar o menu das abas do conteúdo

    # Exibir conteúdo com base na aba selecionada
    if aba_selecionada == "Nova Proposta":
        mostrar_nova_proposta()
    elif aba_selecionada == "Lista de Propostas":
        mostrar_lista_propostas()
    elif aba_selecionada == "Andamento do Trabalho":
        mostrar_andamento()
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
            cliente_id = int(clientes[clientes['nome'] == cliente_nome]['id'].iloc[0])

            descricao = st.text_area("Descrição do Serviço")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

            tipo_proposta = st.selectbox(
                "Tipo de Proposta",
                ["Organização", "Organização Mudança", "Treinamento Funcionários", 
                 "Consultoria Online", "Consultoria Enxoval"]
            )

            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data de Início")
            with col2:
                data_fim = st.date_input("Data de Fim")

            prazo_entrega = st.date_input("Prazo de Entrega") if tipo_proposta in ["Organização", "Organização Mudança"] else None
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

            # Criar DataFrame para exibição
            df_display = propostas[['numero', 'nome', 'descricao', 'valor', 'status', 'data_proposta']].copy()
            df_display.columns = ['Número', 'Cliente', 'Descrição', 'Valor (R$)', 'Status', 'Data']

            # Formatar valores
            df_display['Valor (R$)'] = df_display['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')
            df_display['Data'] = pd.to_datetime(df_display['Data']).dt.strftime('%d/%m/%Y')

            # Exibir tabela
            st.dataframe(df_display, hide_index=True)

            # Seleção de proposta para ação
            col1, col2 = st.columns(2)
            with col1:
                proposta_num = st.number_input("Número da proposta para ação:", 
                                             min_value=int(propostas['numero'].min()),
                                             max_value=int(propostas['numero'].max()),
                                             step=1)
            with col2:
                acao = st.selectbox("Ação:", ["Excluir", "Exportar PDF"])

            # Formulário de ação
            with st.form("acao_proposta"):
                if st.form_submit_button(f"Confirmar {acao}"):
                    proposta = propostas[propostas['numero'] == proposta_num].iloc[0]

                    if acao == "Excluir":
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
                        try:
                            # Criar diretório para PDFs se não existir
                            os.makedirs("pdfs", exist_ok=True)

                            # Nome do arquivo
                            filename = f"pdfs/proposta_{proposta['numero']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                            # Buscar acréscimos da proposta
                            acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])

                            # Gerar PDF
                            usar_template_canva = st.checkbox("Usar Template Canva")
                            pdf_path = gerar_pdf_fechamento(
                                proposta=proposta,
                                cliente={'nome': proposta['nome']},
                                acrescimos=acrescimos,
                                filename=filename,
                                usar_template=usar_template_canva
                            )

                            # Criar link para download
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="Baixar PDF",
                                    data=pdf_bytes,
                                    file_name=os.path.basename(filename),
                                    mime="application/pdf"
                                )

                            st.success("PDF gerado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao gerar PDF: {str(e)}")

        else:
            st.info("Nenhuma proposta encontrada.")

    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")

def mostrar_andamento():
    st.subheader("Andamento do Trabalho")
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

                with st.form("adicionar_acrescimo"):
                    col1, col2 = st.columns(2)

                    with col1:
                        tipo_acrescimo = st.selectbox(
                            "Tipo de Acréscimo",
                            ["Organização", "Assistente", "Fornecedor", "Marcenaria", "Produto"]
                        )

                    with col2:
                        fornecedor_nome = None
                        if tipo_acrescimo == "Fornecedor":
                            fornecedor = st.selectbox(
                                "Fornecedor",
                                ["La Luc", "Multicoisas", "Organizatta", "Outro"]
                            )
                            fornecedor_nome = fornecedor
                        elif tipo_acrescimo == "Assistente":
                            try:
                                assistentes = st.session_state.db.get_assistentes()
                                if not assistentes.empty:
                                    assistente = st.selectbox(
                                        "Assistente",
                                        assistentes['nome'].tolist()
                                    )
                                    fornecedor_nome = assistente
                                else:
                                    st.warning("Nenhum assistente cadastrado.")
                            except Exception as e:
                                st.error(f"Erro ao carregar assistentes: {str(e)}")

                    descricao_acrescimo = st.text_input("Descrição")
                    valor_acrescimo = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

                    if st.form_submit_button("Adicionar"):
                        if valor_acrescimo <= 0:
                            st.error("Por favor, insira um valor válido maior que zero.")
                            return

                        if tipo_acrescimo == "Assistente" and not fornecedor_nome:
                            st.error("Por favor, selecione um assistente.")
                            return

                        try:
                            st.session_state.db.add_acrescimo_proposta(
                                proposta_id=int(proposta['id']),
                                tipo=tipo_acrescimo,
                                fornecedor=fornecedor_nome,
                                descricao=descricao_acrescimo if descricao_acrescimo else None,
                                valor=float(valor_acrescimo)
                            )
                            st.success("Acréscimo adicionado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao adicionar acréscimo: {str(e)}")

                # Exibir acréscimos existentes
                try:
                    acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                    if not acrescimos.empty:
                        st.write("### Acréscimos Adicionados")

                        # Criar DataFrame para exibição
                        df_acrescimos = acrescimos[['tipo', 'fornecedor', 'valor', 'descricao']].copy()
                        df_acrescimos.columns = ['Tipo', 'Fornecedor', 'Valor (R$)', 'Descrição']

                        # Formatar valores
                        df_acrescimos['Valor (R$)'] = df_acrescimos['Valor (R$)'].apply(lambda x: f'R$ {float(x):.2f}')

                        # Exibir tabela
                        st.dataframe(df_acrescimos, hide_index=True)

                        # Status e valor total
                        valor_total = float(proposta['valor']) + acrescimos['valor'].sum()
                        st.write(f"**Valor Total da Proposta:** R$ {valor_total:.2f}")

                except Exception as e:
                    st.error(f"Erro ao carregar acréscimos: {str(e)}")

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
    if usar_template:
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
    else:
        #Example of how it might look:  Replace this with your actual original PDF generation code.
        #This is a placeholder,  you need to replace this with your existing code.
        with open(filename, "wb") as f:
            f.write(b"This is a placeholder PDF. Replace this with your actual PDF generation code.")
        return filename