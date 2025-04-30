import streamlit as st
from utils.finalizar_proposta_fix import finalizar_proposta_sql
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import uuid
import plotly.graph_objects as go
from utils.database import Fornecedor

def show():
    # Título com estilo personalizado para ficar mais próximo do topo
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">📝 Propostas</h1>', unsafe_allow_html=True)
    
    # Verificar se temos uma conexão com o banco de dados
    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return
    
    # Adicionar classes CSS para melhorar a aparência das abas
    st.markdown("""
    <style>
    div[data-testid="stTabs"] > div:first-child {
        background-color: #f8f9fa;
        border-radius: 4px;
        padding: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Criar abas para organizar o conteúdo com ícones para cada uma
    st.markdown('<div class="main-tabs">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Nova Proposta", 
        "📁 Propostas em Aberto", 
        "⚙️ Em Execução", 
        "✅ Finalizadas", 
        "📋 Todas as Propostas"
    ])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ABA 1: NOVA PROPOSTA
    with tab1:
        st.header("Nova Proposta")
        
        # Obter a lista de clientes do banco de dados
        try:
            clientes = st.session_state.db.get_clientes()
            if clientes.empty:
                st.warning("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
            else:
                # Opção para escolher entre nova proposta padrão ou proposta retroativa
                tipo_cadastro = st.radio(
                    "Tipo de cadastro:", 
                    ["Nova proposta", "Cadastro retroativo"],
                    horizontal=True
                )
                
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
                    
                    # Data de início prevista - ajustada conforme tipo de cadastro
                    if tipo_cadastro == "Nova proposta":
                        data_inicio = st.date_input("Data de início prevista:", datetime.now().date())
                    else:
                        data_inicio = st.date_input("Data de início:", datetime.now().date() - timedelta(days=90))
                        
                        # Para cadastros retroativos, oferecer opcões de status mais avançados
                        status_opcoes = [
                            "Em elaboração", 
                            "Aguardando aprovação", 
                            "Aprovada", 
                            "Em execução", 
                            "Finalizada"
                        ]
                        status_inicial = st.selectbox("Status da proposta:", status_opcoes)
                        
                        # Datas relacionadas ao status selecionado
                        if status_inicial in ["Aprovada", "Em execução", "Finalizada"]:
                            data_aprovacao = st.date_input("Data de aprovação:", data_inicio)
                        
                        if status_inicial in ["Em execução", "Finalizada"]:
                            # A data de início de execução é sempre igual à data de início da proposta
                            # Não permitimos mais que o usuário selecione uma data diferente
                            st.info("A data de início de execução será igual à data de início da proposta.")
                            data_inicio_execucao = data_inicio  # Usar sempre a data de início da proposta
                        
                        if status_inicial == "Finalizada":
                            data_fim_real = st.date_input("Data de conclusão:", data_inicio + timedelta(days=prazo))
                            
                        # Status de pagamento para propostas finalizadas ou aprovadas
                        if status_inicial in ["Aprovada", "Finalizada"]:
                            status_pagamento = st.selectbox(
                                "Status de pagamento:",
                                ["Pendente", "Parcial", "Pago"]
                            )
                    
                    # Calcular data de término com base no prazo
                    data_fim = data_inicio + timedelta(days=prazo)
                    st.info(f"Data de término prevista: {data_fim.strftime('%d/%m/%Y')}")
                    
                    # Tipo de proposta
                    tipo_proposta = st.selectbox(
                        "Tipo de Proposta:",
                        ["Organização", "Consultoria", "Acompanhamento", "Projeto", "Outro"]
                    )
                    
                    # Opção para gerar lançamentos financeiros automaticamente
                    if tipo_cadastro == "Cadastro retroativo":
                        gerar_financeiro = st.checkbox("Gerar lançamentos financeiros", value=True)
                    
                    # Botão para salvar
                    submitted = st.form_submit_button("Salvar Proposta")
                    
                    if submitted:
                        try:
                            # Obter o ID do cliente selecionado
                            cliente_id = clientes[clientes['nome'] == cliente]['id'].iloc[0]
                            
                            # Status e configurações baseadas no tipo de cadastro
                            if tipo_cadastro == "Nova proposta":
                                status_proposta = "Em elaboração"  # Status inicial padrão
                                gerar_transacoes = False
                            else:
                                status_proposta = status_inicial
                                gerar_transacoes = gerar_financeiro if 'gerar_financeiro' in locals() else False
                            
                            # Criar nova proposta
                            novo_numero = st.session_state.db.add_proposta(
                                cliente_id=cliente_id,
                                descricao=descricao,
                                valor=valor,
                                status=status_proposta,
                                tipo_proposta=tipo_proposta,
                                data_inicio=data_inicio,
                                data_fim=data_fim,
                                previsao_dias=prazo,  # Prazo em dias (número)
                                prazo_entrega=data_inicio,  # Usamos data_inicio como base
                                gerar_transacoes_automaticas=gerar_transacoes
                            )
                            
                            # Para propostas retroativas com status avançados, atualizar campos adicionais
                            if tipo_cadastro == "Cadastro retroativo" and novo_numero:
                                proposta_atualizada = {}
                                
                                # Adicionar datas relacionadas ao status
                                if status_inicial in ["Aprovada", "Em execução", "Finalizada"]:
                                    proposta_atualizada['data_aprovacao'] = data_aprovacao
                                    # Para propostas aprovadas, a data de proposta deve ser a mesma
                                    proposta_atualizada['data_proposta'] = data_aprovacao
                                
                                if status_inicial in ["Em execução", "Finalizada"]:
                                    # A data de início de execução é sempre a data de início da proposta
                                    proposta_atualizada['data_inicio_execucao'] = data_inicio
                                    proposta_atualizada['status_execucao'] = "Em execução"
                                
                                if status_inicial == "Finalizada":
                                    proposta_atualizada['data_fim'] = data_fim_real
                                    proposta_atualizada['status_execucao'] = "Concluída"
                                
                                # Status de pagamento para propostas
                                if status_inicial in ["Aprovada", "Finalizada"]:
                                    proposta_atualizada['status_pagamento_base'] = status_pagamento
                                
                                # Atualizar proposta com os campos adicionais
                                if proposta_atualizada:
                                    st.session_state.db.update_proposta(novo_numero, **proposta_atualizada)
                            
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
        
        # Garantir que todas as colunas numéricas sejam do tipo correto
        # Isso evita o erro '<' not supported between instances of 'float' and 'str'
        for col in ['valor', 'previsao_dias', 'id', 'numero', 'cliente_id']:
            if col in propostas.columns:
                propostas[col] = pd.to_numeric(propostas[col], errors='coerce')
        
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
                # Filtrar apenas propostas em elaboração ou aguardando aprovação
                propostas_em_aberto = propostas_com_clientes[
                    propostas_com_clientes['status'].isin(['Em elaboração', 'Aguardando aprovação'])
                ]
                
                if not propostas_em_aberto.empty:
                    # Criar uma cópia das propostas para manipulação
                    propostas_display = propostas_em_aberto.copy()
                    
                    # Converter valores para exibição
                    propostas_display['valor_formatado'] = propostas_display['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    propostas_display['data_inicio_formatada'] = propostas_display['data_inicio'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Processar alterações de status pendentes
                    for idx, proposta in propostas_display.iterrows():
                        proposta_id = proposta['id']
                        alterar_status_key = f"alterar_status_{proposta_id}"
                        
                        if alterar_status_key in st.session_state and st.session_state[alterar_status_key]:
                            novo_status = st.session_state[alterar_status_key]
                            
                            if novo_status == "Excluir":
                                # Processar exclusão
                                sucesso, mensagem = st.session_state.db.excluir_proposta(proposta_id)
                                if sucesso:
                                    st.success(f"Proposta {proposta_id} excluída com sucesso!")
                                    # Remover da sessão e recarregar
                                    del st.session_state[alterar_status_key]
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao excluir proposta: {mensagem}")
                                    del st.session_state[alterar_status_key]
                            
                            elif novo_status != proposta['status']:
                                # Processar mudança de status
                                data_aprovacao = None
                                data_inicio_execucao = None
                                status_execucao = None
                                
                                # Definir parâmetros com base no novo status
                                gerar_transacoes = False
                                if novo_status == "Aprovada":
                                    data_aprovacao = datetime.now().date()
                                    # Automaticamente mudar para "Em execução" quando aprovada
                                    novo_status = "Em execução"
                                    # Usar a data de início da proposta como data de início de execução
                                    data_inicio_execucao = proposta['data_inicio'] if pd.notna(proposta['data_inicio']) else datetime.now().date()
                                    status_execucao = "Iniciada"
                                    gerar_transacoes = True
                                
                                elif novo_status == "Em execução":
                                    # Usar a data de início da proposta como data de início de execução
                                    data_inicio_execucao = proposta['data_inicio'] if pd.notna(proposta['data_inicio']) else datetime.now().date()
                                    status_execucao = "Iniciada"
                                    
                                    # Se a proposta não foi aprovada, aprovar primeiro
                                    if proposta['status'] != "Aprovada" and data_aprovacao is None:
                                        data_aprovacao = datetime.now().date()
                                        gerar_transacoes = True
                                
                                # Atualizar o status
                                if data_aprovacao:
                                    resultado = st.session_state.db.update_proposta_status(
                                        proposta_id=proposta_id,
                                        novo_status=novo_status,
                                        data_aprovacao=data_aprovacao
                                    )
                                    
                                    # Verificar se a atualização teve sucesso
                                    sucesso = resultado.get('status', False)
                                    
                                    # Após atualizar o status, se necessário gerar transações
                                    if sucesso and gerar_transacoes:
                                        try:
                                            # Gerar transações financeiras (receita e despesas)
                                            resultado = st.session_state.db.gerar_transacoes_proposta(proposta_id)
                                            print(f"DEBUG: Transações geradas para proposta {proposta_id}: {resultado}")
                                        except Exception as e:
                                            st.error(f"Erro ao gerar transações financeiras: {str(e)}")
                                else:
                                    resultado = st.session_state.db.atualizar_proposta(
                                        proposta_id=proposta_id,
                                        status=novo_status,
                                        data_inicio_execucao=data_inicio_execucao,
                                        status_execucao=status_execucao
                                    )
                                    
                                    # Verificar se a atualização teve sucesso
                                    sucesso = resultado.get('status', False)
                                
                                if sucesso:
                                    st.success(f"Proposta {proposta_id} atualizada para '{novo_status}'!")
                                    # Remover da sessão e recarregar
                                    del st.session_state[alterar_status_key]
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao atualizar proposta {proposta_id}")
                                    del st.session_state[alterar_status_key]
                    
                    # Construir interface com seletores de status direto na tabela
                    
                    # Cabeçalho e descrição
                    st.write("Selecione uma proposta abaixo para editar ou alterar o status:")
                    
                    # Layout com 5 colunas. A última vai conter o botão de exclusão
                    col_num, col_info, col_status, col_export, col_excluir = st.columns([1, 4, 3, 1, 1])
                    
                    with col_num:
                        st.markdown("**Número**")
                    with col_info:
                        st.markdown("**Informações da Proposta**")
                    with col_status:
                        st.markdown("**Alterar Status**")
                    with col_export:
                        st.markdown("**PDF**")
                    with col_excluir:
                        st.markdown("**Ações**")
                    
                    # Exibir cada proposta com seus controles
                    for idx, proposta in propostas_display.iterrows():
                        proposta_id = proposta['id']
                        status_atual = proposta['status']
                        
                        # Criar container para a linha da proposta
                        with st.container():
                            # 5 colunas: Número, Info, Status Selector, Export, Excluir
                            col_num, col_info, col_status, col_export, col_excluir = st.columns([1, 4, 3, 1, 1])
                            
                            # Coluna 1: Número da proposta (não mais o ID)
                            with col_num:
                                st.write(f"**{proposta['numero']}**")
                            
                            # Coluna 2: Informações da proposta (sem incluir o número no título)
                            with col_info:
                                st.markdown(f"""
                                **{proposta['nome']}**  
                                {proposta['descricao']}  
                                **Valor:** {proposta['valor_formatado']} | **Tipo:** {proposta['tipo_proposta']}  
                                **Início Execução:** {proposta['data_inicio_formatada']} | **Prazo:** {proposta['previsao_dias']} dias
                                """)
                            
                            # Coluna 3: Seletor de status com botão para salvar
                            with col_status:
                                # Definir opções de status com base no fluxo de trabalho
                                opcoes_status = []
                                if status_atual == "Em elaboração":
                                    opcoes_status = [
                                        "Em elaboração",
                                        "Aguardando aprovação", 
                                        "Aprovada", 
                                        "Recusada"
                                    ]
                                elif status_atual == "Aguardando aprovação":
                                    opcoes_status = [
                                        "Aguardando aprovação", 
                                        "Em elaboração", 
                                        "Aprovada", 
                                        "Recusada"
                                    ]
                                elif status_atual == "Aprovada":
                                    opcoes_status = [
                                        "Aprovada", 
                                        "Em execução", 
                                        "Recusada"
                                    ]
                                elif status_atual == "Recusada":
                                    opcoes_status = [
                                        "Recusada", 
                                        "Em elaboração", 
                                        "Aprovada"
                                    ]
                                
                                # Adicionar opção de exclusão
                                opcoes_status.append("Excluir")
                                
                                # Índice padrão para o seletor
                                try:
                                    status_index = opcoes_status.index(status_atual)
                                except ValueError:
                                    status_index = 0
                                
                                # Criar duas colunas para o seletor e o botão
                                status_col, btn_col = st.columns([3, 1])
                                
                                with status_col:
                                    # Seletor de status
                                    novo_status = st.selectbox(
                                        f"Status atual: {status_atual}",
                                        opcoes_status,
                                        index=status_index,
                                        format_func=lambda x: f"❌ Excluir proposta" if x == "Excluir" else x,
                                        key=f"status_sel_{proposta_id}",
                                        label_visibility="collapsed"
                                    )
                                
                                with btn_col:
                                    # Botão de salvar alteração
                                    if st.button("Salvar", key=f"btn_save_{proposta_id}"):
                                        if novo_status == status_atual:
                                            st.success("✓")
                                        elif novo_status == "Excluir":
                                            st.warning("⚠️")
                                            confirmar_key = f"confirm_del_{proposta_id}"
                                            if st.button("Confirmar", key=confirmar_key):
                                                st.session_state[f"alterar_status_{proposta_id}"] = "Excluir"
                                                st.rerun()
                                        else:
                                            st.session_state[f"alterar_status_{proposta_id}"] = novo_status
                                            st.rerun()
                            
                            # Coluna 4: Botão para exportar PDF
                            with col_export:
                                if st.button("PDF", key=f"pdf_{proposta_id}"):
                                    from utils.propostas_helper import gerar_pdf_proposta
                                    
                                    # Gerar o PDF
                                    sucesso, mensagem, arquivo = gerar_pdf_proposta(
                                        db=st.session_state.db,
                                        proposta_id=proposta_id
                                    )
                                    
                                    if sucesso and arquivo:
                                        # Ler o arquivo para download
                                        with open(arquivo, "rb") as file:
                                            pdf_bytes = file.read()
                                        
                                        # Oferecer o download
                                        proposta_id = proposta['id']
                                        # Obter nome do cliente da proposta para usar no nome do arquivo
                                        cliente_id = proposta['cliente_id']
                                        cliente_df = st.session_state.db.get_cliente_by_id(cliente_id)
                                        cliente_nome = "sem_nome"
                                        if not cliente_df.empty:
                                            # Obter o nome da primeira linha do DataFrame
                                            nome_str = str(cliente_df.iloc[0]['nome']) if 'nome' in cliente_df.columns else "sem_nome"
                                            cliente_nome = nome_str.replace(' ', '_').lower()
                                        
                                        # Mostrar mensagem de sucesso padronizada
                                        st.success(f"Proposta gerada com sucesso!")
                                        
                                        # Criar botão de download com formato padronizado
                                        download_key = f"download_proposta_{proposta['numero']}_{datetime.now().strftime('%H%M%S')}"
                                        st.download_button(
                                            label="Download da Proposta",
                                            data=pdf_bytes,
                                            file_name=f"Proposta_{proposta_id}_{cliente_nome}.pdf",
                                            mime="application/pdf",
                                            key=download_key
                                        )
                                    else:
                                        st.error(f"Erro: {mensagem}")
                            
                            # Coluna 5: Botão de exclusão
                            with col_excluir:
                                # Usar um identificador único para cada proposta
                                exclusao_key = f"exclusao_{proposta_id}"
                                
                                # Criar ou redefinir estado de exclusão para esta proposta
                                if exclusao_key not in st.session_state:
                                    st.session_state[exclusao_key] = {
                                        "confirmar_visivel": False,
                                        "excluindo": False
                                    }
                                
                                # Botão para iniciar o processo de exclusão
                                if not st.session_state[exclusao_key]["confirmar_visivel"] and not st.session_state[exclusao_key]["excluindo"]:
                                    if st.button("EXCLUIR", key=f"excluir_btn_{proposta_id}"):
                                        st.session_state[exclusao_key]["confirmar_visivel"] = True
                                        st.rerun()
                                
                                # Mostrar confirmação e botões
                                if st.session_state[exclusao_key]["confirmar_visivel"]:
                                    st.warning(f"Confirmar exclusão da proposta #{proposta['numero']}?")
                                    
                                    # Criar linha para os botões de confirmação
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        if st.button("CANCELAR", key=f"cancelar_excluir_{proposta_id}"):
                                            st.session_state[exclusao_key]["confirmar_visivel"] = False
                                            st.rerun()
                                    
                                    with col2:
                                        if st.button("CONFIRMAR", key=f"confirmar_excluir_{proposta_id}"):
                                            st.session_state[exclusao_key]["excluindo"] = True
                                            st.session_state[exclusao_key]["confirmar_visivel"] = False
                                            st.rerun()
                                
                                # Executar a exclusão
                                if st.session_state[exclusao_key]["excluindo"]:
                                    try:
                                        st.info(f"Excluindo proposta ID: {proposta_id}...")
                                        # Converter para int explicitamente para garantir
                                        proposta_id_int = int(proposta_id)
                                        sucesso, mensagem = st.session_state.db.excluir_proposta(proposta_id_int)
                                        
                                        if sucesso:
                                            st.success("Proposta excluída com sucesso!")
                                            # Dar tempo para visualizar a mensagem
                                            time.sleep(1)
                                            # Resetar o estado e recarregar
                                            st.session_state[exclusao_key] = {
                                                "confirmar_visivel": False,
                                                "excluindo": False
                                            }
                                            st.rerun()
                                        else:
                                            st.error(f"Erro ao excluir proposta: {mensagem}")
                                            if st.button("Tentar novamente", key=f"retry_excluir_{proposta_id}"):
                                                st.session_state[exclusao_key]["excluindo"] = False
                                                st.session_state[exclusao_key]["confirmar_visivel"] = False
                                                st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao excluir proposta: {str(e)}")
                                        if st.button("Tentar novamente", key=f"retry_error_{proposta_id}"):
                                            st.session_state[exclusao_key]["excluindo"] = False
                                            st.session_state[exclusao_key]["confirmar_visivel"] = False
                                            st.rerun()
                            
                            # Separador entre propostas
                            st.markdown("---")
                    
                    # Barra separadora para separar da área de edição de proposta
                    st.divider()
                    
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
                    df_execucao['Número'] = propostas_em_execucao['numero']  # Mostrar número em vez do ID
                    df_execucao['Cliente'] = propostas_em_execucao['nome']
                    df_execucao['Descrição'] = propostas_em_execucao['descricao']
                    df_execucao['Valor (R$)'] = propostas_em_execucao['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    df_execucao['Status Execução'] = propostas_em_execucao['status_execucao']
                    df_execucao['Início Execução'] = propostas_em_execucao['data_inicio_execucao'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Adicionar coluna para o botão de exclusão
                    df_execucao['ID'] = propostas_em_execucao['id']  # Manter o ID como coluna oculta para referência
                    
                    # Exibir tabela sem o índice automático do pandas
                    st.dataframe(df_execucao.drop(columns=['ID']), hide_index=True)
                    
                    # Adicionar área para exclusão de proposta
                    with st.expander("Excluir Proposta em Execução"):
                        # Obter lista de números de propostas em execução para o select box
                        numeros_propostas = propostas_em_execucao['numero'].tolist()
                        numeros_propostas.sort()  # Ordenar para facilitar a seleção
                        
                        proposta_numero = st.selectbox(
                            "Selecione o número da proposta a excluir:",
                            numeros_propostas,
                            key="numero_proposta_execucao_excluir"
                        )
                        
                        proposta_exc = propostas_em_execucao[propostas_em_execucao['numero'] == proposta_numero]
                        
                        if not proposta_exc.empty:
                            st.warning(f"Você está prestes a excluir a proposta #{proposta_numero} - {proposta_exc.iloc[0]['descricao']}")
                            if st.button("CONFIRMAR EXCLUSÃO", key="confirmar_exclusao_execucao"):
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
                    
                    # Ações para propostas em execução
                    st.subheader("Gerenciar Execução")
                    
                    # Obter lista de números de propostas para o select box
                    numeros_propostas_execucao = propostas_em_execucao['numero'].tolist()
                    numeros_propostas_execucao.sort()  # Ordenar para facilitar a seleção
                    
                    # Usar selectbox em vez de number_input para escolher pelo número da proposta
                    proposta_exec_numero = st.selectbox(
                        "Número da Proposta",
                        numeros_propostas_execucao,
                        key="numero_proposta_execucao_gerenciar"
                    )
                    
                    # Buscar o ID correspondente ao número selecionado
                    proposta_exec_selecionada = propostas_em_execucao[propostas_em_execucao['numero'] == proposta_exec_numero]
                    proposta_exec_id = proposta_exec_selecionada.iloc[0]['id'] if not proposta_exec_selecionada.empty else 0
                    
                    # Verificar se a proposta existe
                    proposta_exec = propostas_em_execucao[propostas_em_execucao['id'] == proposta_exec_id]
                    
                    if not proposta_exec.empty:
                        # Adicionar breadcrumbs para navegação
                        st.markdown(
                            f"""
                            <div class="breadcrumb">
                                <span>Propostas</span> > 
                                <span>Em Execução</span> > 
                                <span>Proposta #{proposta_exec.iloc[0]['numero']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Mostrar informações da proposta com melhor formatação
                        st.markdown(
                            f"""
                            <div class="section-container">
                                <h2 style="margin-top:0">Proposta #{proposta_exec.iloc[0]['numero']}</h2>
                                <p style="font-size: 1.1rem; color: #555;">{proposta_exec.iloc[0]['descricao']}</p>
                                <div style="display: flex; gap: 2rem; margin-top: 0.5rem; margin-bottom: 1rem;">
                                    <div>
                                        <strong>Cliente:</strong> {proposta_exec.iloc[0]['nome']}
                                    </div>
                                    <div>
                                        <strong>Valor:</strong> R$ {float(proposta_exec.iloc[0]['valor']):.2f}
                                    </div>
                                    <div>
                                        <strong>Status:</strong> {proposta_exec.iloc[0]['status']}
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Adicionar barra de progresso visual
                        progresso = 50  # Valor exemplo, pode ser calculado com base em andamentos registrados
                        st.markdown(
                            f"""
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {progresso}%;"></div>
                            </div>
                            <div style="text-align: center; font-size: 0.85rem; margin-bottom: 1rem;">
                                Progresso da proposta: {progresso}%
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Adicionar estilos específicos para as abas de execução
                        st.markdown("""
                        <style>
                        div[data-testid="stTabs"] > div:nth-child(2) {
                            background-color: white;
                            border-radius: 6px;
                            padding: 1rem;
                            box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Criar abas para gerenciar diferentes aspectos da execução com ícones e cores
                        st.markdown('<div class="execution-tabs">', unsafe_allow_html=True)
                        exec_tab1, exec_tab2, exec_tab3, exec_tab4, exec_tab5, exec_tab6 = st.tabs([
                            "📊 Andamento", "📦 Produtos", "➕ Outros", "🏭 Fornecedores", "👥 Assistentes", "🏁 Finalizar"
                        ])
                        st.markdown('</div>', unsafe_allow_html=True)
                        
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
                            
                            # Mostrar histórico de andamentos no formato de cartões
                            try:
                                andamentos = st.session_state.db.get_andamentos_proposta(proposta_exec_id)
                                
                                if not andamentos.empty:
                                    st.markdown("""
                                    <h3 style="margin-top: 2rem; border-bottom: 1px solid #e6e6e6; padding-bottom: 0.5rem;">
                                        📋 Histórico de Andamento
                                    </h3>
                                    """, unsafe_allow_html=True)
                                    
                                    # Ordenar do mais recente para o mais antigo
                                    andamentos = andamentos.sort_values(by='data', ascending=False)
                                    
                                    # Status e cores
                                    status_colors = {
                                        "Em andamento": "#4285F4", # Azul
                                        "Aguardando cliente": "#FBBC05", # Amarelo
                                        "Aguardando material": "#F4B400", # Laranja
                                        "Pausa": "#EA4335", # Vermelho
                                        "Etapa concluída": "#34A853" # Verde
                                    }
                                    
                                    # Formatação avançada para mostrar dados como cartões
                                    for idx, andamento in andamentos.iterrows():
                                        status = andamento['status']
                                        data = andamento['data'].strftime('%d/%m/%Y %H:%M') if pd.notna(andamento['data']) else ''
                                        comodo = andamento['comodo'] if pd.notna(andamento['comodo']) else ''
                                        observacao = andamento['observacao'] if pd.notna(andamento['observacao']) else ''
                                        
                                        # Cor para o status
                                        cor_status = status_colors.get(status, "#1E366F")
                                        
                                        st.markdown(f"""
                                        <div class="item-card" style="border-left: 4px solid {cor_status}; margin-bottom: 1rem;">
                                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                                <strong style="color: {cor_status};">{status}</strong>
                                                <span style="color: #666; font-size: 0.9rem;">{data}</span>
                                            </div>
                                            <div style="margin-bottom: 0.5rem;">
                                                <strong>Cômodo/Área:</strong> {comodo if comodo else "N/A"}
                                            </div>
                                            <p style="margin: 0; font-style: italic; color: #555;">{observacao}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.info("Nenhum registro de andamento para esta proposta.")
                            except Exception as e:
                                st.error(f"Erro ao carregar andamentos: {str(e)}")
                        
                        with exec_tab2:
                            st.subheader("Adição à Proposta")
                            
                            # Produtos do catálogo
                            try:
                                # Buscar produtos cadastrados
                                produtos_cadastrados = st.session_state.db.get_produtos()
                                
                                # Filtrar produtos de serviço (UBER, CABIDE, etc.)
                                if not produtos_cadastrados.empty:
                                    # Definir termos que identificam produtos de serviço
                                    termos_servico = ['uber', 'transporte', 'serviço', 'servico', 'frete', 'delivery', 'entrega', 'cabide']
                                    
                                    # Converter nomes para minúsculo para comparação
                                    produtos_cadastrados['nome_lower'] = produtos_cadastrados['nome'].str.lower()
                                    
                                    # Criar máscara para filtrar produtos de serviço
                                    mask_servicos = produtos_cadastrados['nome_lower'].apply(
                                        lambda x: any(termo in x for termo in termos_servico) if isinstance(x, str) else False
                                    )
                                    
                                    # Filtrar para manter apenas produtos que NÃO são de serviço
                                    produtos_cadastrados = produtos_cadastrados[~mask_servicos].copy()
                                    
                                    # Remover coluna temporária
                                    if 'nome_lower' in produtos_cadastrados.columns:
                                        produtos_cadastrados = produtos_cadastrados.drop('nome_lower', axis=1)
                                
                                if not produtos_cadastrados.empty:
                                    with st.form(key=f"produto_catalogo_form_{proposta_exec_id}"):
                                        # Seleção de produto do catálogo
                                        produto_id = st.selectbox(
                                            "Selecione o produto:",
                                            produtos_cadastrados['id'].tolist(),
                                            format_func=lambda x: f"{produtos_cadastrados[produtos_cadastrados['id']==x]['nome'].iloc[0]} - R$ {float(produtos_cadastrados[produtos_cadastrados['id']==x]['preco_venda'].iloc[0]):.2f}"
                                        )
                                        
                                        # Obter dados do produto selecionado
                                        produto_info = produtos_cadastrados[produtos_cadastrados['id'] == produto_id].iloc[0]
                                        
                                        # Exibir informações do produto
                                        st.write(f"**Descrição:** {produto_info['descricao']}")
                                        st.write(f"**Categoria:** {produto_info['categoria']}")
                                        
                                        # Campos para configurar a adição
                                        quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                                        comodo_produto = st.text_input("Cômodo/Área:")
                                        
                                        # Opção para ajustar o preço (padrão é o preço de venda)
                                        usar_preco_padrao = st.checkbox("Usar preço padrão", value=True)
                                        preco_personalizado = st.number_input(
                                            "Preço personalizado (R$):", 
                                            min_value=0.0, 
                                            value=float(produto_info['preco_venda']),
                                            format="%.2f",
                                            disabled=usar_preco_padrao
                                        )
                                            
                                        # Determinar qual preço usar
                                        preco_final = float(produto_info['preco_venda']) if usar_preco_padrao else preco_personalizado
                                        
                                        if st.form_submit_button("Adicionar à Proposta"):
                                            try:
                                                # Log de depuração
                                                # Removido logs de debug que apareciam na interface
                                                # st.info(f"DEBUG: Adicionando produto do catálogo '{produto_info['nome']}' à proposta ID={proposta_exec_id}")
                                                # st.info(f"DEBUG: Valor: {preco_final}, Quantidade: {quantidade}")
                                                
                                                # Adicionar o produto à proposta
                                                try:
                                                    # Garantir que comodo_produto não seja None
                                                    comodo_final = comodo_produto if comodo_produto else "Geral"
                                                    
                                                    # Fazer validações explícitas dos tipos de dados
                                                    try:
                                                        proposta_id_validado = int(proposta_exec_id)
                                                        nome_validado = str(produto_info['nome'])
                                                        descricao_validada = str(produto_info['descricao']) if produto_info.get('descricao') else ""
                                                        preco_validado = float(preco_final)
                                                        quantidade_validada = int(quantidade)
                                                        comodo_validado = str(comodo_final)
                                                            
                                                        # Removido logs de debug que apareciam na interface
                                                    except (ValueError, TypeError) as e_val:
                                                        # st.error(f"DEBUG: Erro na validação de dados: {str(e_val)}")
                                                        raise ValueError(f"Erro na preparação dos dados: {str(e_val)}")
                                                    
                                                    # st.info(f"DEBUG: Chamando add_produto_organizador")
                                                    produto_org_id = None  # Inicializa a variável
                                                    try:
                                                        produto_org_id = st.session_state.db.add_produto_organizador(
                                                            proposta_id=proposta_id_validado,
                                                            nome=nome_validado,
                                                            descricao=descricao_validada,
                                                            valor=preco_validado,
                                                            quantidade=quantidade_validada,
                                                            comodo=comodo_validado
                                                        )
                                                            
                                                        # Removido logs de debug e verificação direta no banco
                                                        # A verificação direta no banco não é mais necessária, pois o sistema está mais estável
                                                            
                                                        # Se chegou aqui, a operação foi bem-sucedida
                                                        st.success(f"Produto '{produto_info['nome']}' adicionado com sucesso!")
                                                        time.sleep(2)  # Aumentar tempo para garantir que transação seja concluída
                                                        st.rerun()
                                                    except Exception as e_inner:
                                                        # Removido logs de debug
                                                        # import traceback
                                                        # st.error(traceback.format_exc())
                                                        st.error("Erro ao adicionar produto à proposta.")
                                                except Exception as e_outer:
                                                    # Removido logs de debug
                                                    # import traceback
                                                    # st.error(traceback.format_exc())
                                                    st.error("Erro no processamento do produto.")
                                            except Exception as e:
                                                st.error(f"Erro ao adicionar produto: {str(e)}")
                                                import traceback
                                                st.error(traceback.format_exc())
                                else:
                                    st.warning("Não há produtos cadastrados no sistema.")
                                    st.write("Vá para o módulo de Vendas > Produtos para cadastrar produtos.")
                            except Exception as e:
                                st.error(f"Erro ao carregar produtos: {str(e)}")
                            
                            # Conteúdo de "prod_tab2" foi movido para a aba "Outros" (exec_tab3)

                            
                            # Mostrar produtos adicionados
                            try:
                                produtos = st.session_state.db.get_produtos_organizadores(proposta_exec_id)
                                
                                # Filtrar produtos de serviço (UBER, CABIDE, etc.)
                                if not produtos.empty:
                                    # Definir termos que identificam produtos de serviço
                                    termos_servico = ['uber', 'transporte', 'serviço', 'servico', 'frete', 'delivery', 'entrega', 'cabide']
                                    
                                    # Converter nomes para minúsculo para comparação
                                    produtos['nome_lower'] = produtos['nome'].str.lower()
                                    
                                    # Criar máscara para filtrar produtos de serviço
                                    mask_servicos = produtos['nome_lower'].apply(
                                        lambda x: any(termo in x for termo in termos_servico) if isinstance(x, str) else False
                                    )
                                    
                                    # Filtrar para manter apenas produtos que NÃO são de serviço
                                    produtos = produtos[~mask_servicos].copy()
                                    
                                    # Remover coluna temporária
                                    if 'nome_lower' in produtos.columns:
                                        produtos = produtos.drop('nome_lower', axis=1)
                                
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
                            st.subheader("Outros Itens")
                            
                            # Formulário para adicionar itens personalizados
                            with st.form(key=f"produto_outros_form_{proposta_exec_id}"):
                                # Campos para item personalizado
                                st.write("### Adicionar Item Personalizado")
                                nome_produto = st.text_input("Nome do item:")
                                descricao_produto = st.text_area("Descrição:", height=70)
                                valor_produto = st.number_input("Valor unitário (R$):", min_value=0.0, format="%.2f")
                                quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                                comodo_produto = st.text_input("Cômodo/Área:")
                                
                                # Visualização do valor total
                                valor_total = valor_produto * quantidade
                                st.write(f"**Valor Total: R$ {valor_total:.2f}**")
                                
                                # Botão para adicionar
                                if st.form_submit_button("Adicionar Item"):
                                    if not nome_produto:
                                        st.error("O nome do item é obrigatório.")
                                    else:
                                        try:
                                            # Removido logs de debug que apareciam na interface
                                            # st.info(f"DEBUG: Adicionando item personalizado '{nome_produto}' à proposta ID={proposta_exec_id}")
                                            # st.info(f"DEBUG: Valor: {valor_produto}, Quantidade: {quantidade}")
                                            
                                            # Garantir que comodo_produto não seja None
                                            comodo_final = comodo_produto if comodo_produto else "Geral"
                                            
                                            # Validação de tipos
                                            try:
                                                proposta_id_validado = int(proposta_exec_id)
                                                nome_validado = str(nome_produto)
                                                descricao_validada = str(descricao_produto) if descricao_produto else ""
                                                valor_validado = float(valor_produto)
                                                quantidade_validada = int(quantidade)
                                                comodo_validado = str(comodo_final)
                                                
                                                # Removido logs de debug que apareciam na interface
                                            except (ValueError, TypeError) as e_val:
                                                # st.error(f"DEBUG: Erro na validação de dados: {str(e_val)}")
                                                raise ValueError(f"Erro na preparação dos dados: {str(e_val)}")
                                            
                                            # Salvar o item como acréscimo tipo OUTRO
                                            # em vez de como produto organizador
                                            item_id = None
                                            try:
                                                # Usar a função add_acrescimo_proposta para adicionar como tipo OUTRO
                                                resultado = st.session_state.db.add_acrescimo_proposta(
                                                    proposta_id=proposta_id_validado,
                                                    tipo="OUTRO",  # Tipo OUTRO para garantir que seja processado corretamente
                                                    fornecedor=nome_validado,  # Nome do item vai como fornecedor
                                                    descricao=descricao_validada,  # Descrição
                                                    valor=valor_validado * quantidade_validada  # Valor total (preço unitário x quantidade)
                                                )
                                                
                                                if resultado and "acrescimo_id" in resultado:
                                                    item_id = resultado["acrescimo_id"]
                                                    
                                                if item_id:
                                                    st.success(f"Item '{nome_produto}' adicionado com sucesso!")
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao adicionar item à proposta.")
                                            except Exception as e_add:
                                                st.error(f"Erro ao adicionar à base de dados: {str(e_add)}")
                                                # Removido logs de debug detalhados
                                        except Exception as e:
                                            st.error(f"Erro ao adicionar item: {str(e)}")
                                            # Removido logs de debug detalhados
                            
                            # Exibir itens do tipo OUTRO já adicionados
                            try:
                                # Buscar acréscimos do tipo OUTRO da proposta
                                outros_itens = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id=proposta_exec_id, tipo="OUTRO")
                                
                                if not outros_itens.empty:
                                    st.write("### Itens Adicionais")
                                    
                                    for idx, item in outros_itens.iterrows():
                                        with st.container():
                                            col1, col2, col3 = st.columns([3, 1, 1])
                                            
                                            with col1:
                                                # fornecedor é o nome do item
                                                st.write(f"**{item['fornecedor']}**")
                                                st.write(f"_{item['descricao'] if pd.notna(item['descricao']) else ''}_")
                                            
                                            with col2:
                                                # No acréscimo só temos o valor total, não tem quantidade
                                                st.write(f"R$ {float(item['valor']):.2f}")
                                                st.write(f"Status: {item['status_pagamento']}")
                                            
                                            with col3:
                                                # Botão para remover
                                                if st.button(f"Remover", key=f"remove_outro_{item['id']}"):
                                                    try:
                                                        # Usar função apropriada para remover acréscimo
                                                        st.session_state.db.remover_acrescimo(item['id'])
                                                        st.success(f"Item removido com sucesso!")
                                                        time.sleep(1)
                                                        st.rerun()
                                                    except Exception as e:
                                                        st.error(f"Erro ao remover item: {str(e)}")
                                            
                                            st.divider()
                                else:
                                    st.info("Nenhum item adicional foi cadastrado nesta proposta.")
                            except Exception as e:
                                st.error(f"Erro ao carregar itens personalizados: {str(e)}")
                                
                        with exec_tab4:
                            st.subheader("Fornecedores")
                            
                            # Obter lista de fornecedores cadastrados
                            try:
                                fornecedores = st.session_state.db.get_fornecedores()
                                
                                if not fornecedores.empty:
                                    # Formulário para adicionar fornecedor à proposta
                                    with st.form(key=f"fornecedor_form_{proposta_exec_id}"):
                                        # Dentro de um form não podemos usar on_change, então temos que fazer de outra forma
                                        # Seleção do fornecedor (sem callback)
                                        fornecedor_id = st.selectbox(
                                            "Selecione o fornecedor:",
                                            fornecedores['id'].tolist(),
                                            format_func=lambda x: fornecedores[fornecedores['id']==x]['descricao'].iloc[0]
                                        )
                                        
                                        # Buscar o percentual de comissão diretamente após a seleção
                                        percentual_comissao = 0.0
                                        try:
                                            # Buscar do DataFrame primeiro (mais rápido)
                                            fornecedor_df = fornecedores[fornecedores['id'] == fornecedor_id]
                                            if not fornecedor_df.empty and 'percentual_comissao' in fornecedor_df.columns:
                                                percentual_comissao = fornecedor_df['percentual_comissao'].iloc[0] or 0.0
                                                # Removido log de debug
                                            
                                            # Se não encontrou no DataFrame, buscar direto do banco
                                            if percentual_comissao == 0.0:
                                                # Buscar do banco diretamente (fallback)
                                                forn_query = f"SELECT percentual_comissao FROM fornecedores WHERE id = {fornecedor_id}"
                                                result = st.session_state.db.session.execute(forn_query).fetchone()
                                                if result and result[0]:
                                                    percentual_comissao = float(result[0])
                                                    # Removido log de debug
                                        except Exception as e:
                                            # Removido log de debug
                                            pass
                                        
                                        valor_fornecimento = st.number_input("Valor do fornecimento (R$):", min_value=0.0, format="%.2f")
                                        
                                        # Exibir o percentual de comissão que está configurado no cadastro do fornecedor (somente leitura)
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
                            except Exception as e:
                                st.error(f"Erro ao carregar fornecedores: {str(e)}")
                                
                        with exec_tab5:
                            st.subheader("Assistentes")
                            
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
                                                # Adicionar assistente à proposta usando a nova função
                                                acrescimo_id = st.session_state.db.add_assistente_proposta(
                                                    proposta_id=proposta_exec_id,
                                                    assistente_id=assistente_id,
                                                    valor=valor_assistente,
                                                    observacoes=observacao_assistente
                                                )
                                                
                                                if acrescimo_id:
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
                            except Exception as e:
                                st.error(f"Erro ao carregar assistentes: {str(e)}")
                                
                        with exec_tab6:
                            st.subheader("Finalizar Proposta")
                            
                            # Exibir resumo completo da proposta antes de finalizar
                            try:
                                # 1. Dados básicos da proposta
                                st.write("### Dados Básicos")
                                dados_basicos = pd.DataFrame({
                                    "Item": ["Número", "Cliente", "Descrição", "Data de Início", "Data de Aprovação", "Valor Base", "Status"],
                                    "Valor": [
                                        proposta_exec.iloc[0]['numero'],
                                        proposta_exec.iloc[0]['nome'],
                                        proposta_exec.iloc[0]['descricao'],
                                        proposta_exec.iloc[0]['data_inicio'].strftime('%d/%m/%Y') if pd.notna(proposta_exec.iloc[0]['data_inicio']) else 'N/A',
                                        proposta_exec.iloc[0]['data_aprovacao'].strftime('%d/%m/%Y') if pd.notna(proposta_exec.iloc[0]['data_aprovacao']) else 'N/A',
                                        f"R$ {float(proposta_exec.iloc[0]['valor']):.2f}",
                                        proposta_exec.iloc[0]['status']
                                    ]
                                })
                                st.dataframe(dados_basicos, hide_index=True, use_container_width=True)
                                
                                # 2. Produtos adicionados
                                st.write("### Produtos")
                                produtos = st.session_state.db.get_produtos_organizadores(proposta_exec_id)
                                
                                # Filtrar produtos de catálogo (não itens "Outros")
                                if not produtos.empty:
                                    # Verificar se tem produtos de UBER ou outros serviços que não são produtos físicos
                                    # Geralmente esses itens contêm palavras-chave como "serviço", "uber", "transporte", etc.
                                    # Adicionar o termo 'cabide' conforme solicitado
                                    termos_outros = ['uber', 'transporte', 'serviço', 'servico', 'frete', 'delivery', 'entrega', 'cabide']
                                    
                                    # Filtragem para separar itens que parecem ser "Outros"
                                    produtos_filtrados = produtos.copy()
                                    produtos_servicos = None
                                    
                                    if 'nome' in produtos_filtrados.columns:
                                        # Converter nomes para minúsculo para comparação
                                        produtos_filtrados['nome_lower'] = produtos_filtrados['nome'].str.lower()
                                        
                                        # Criar máscara para itens que parecem ser outros serviços
                                        mask_outros = produtos_filtrados['nome_lower'].apply(
                                            lambda x: any(termo in x for termo in termos_outros) if isinstance(x, str) else False
                                        )
                                        
                                        # Separar produtos e serviços
                                        produtos_servicos = produtos_filtrados[mask_outros].copy()
                                        produtos_filtrados = produtos_filtrados[~mask_outros].copy()
                                        
                                        # Remover coluna temporária
                                        if 'nome_lower' in produtos_filtrados.columns:
                                            produtos_filtrados = produtos_filtrados.drop('nome_lower', axis=1)
                                        if not produtos_servicos.empty and 'nome_lower' in produtos_servicos.columns:
                                            produtos_servicos = produtos_servicos.drop('nome_lower', axis=1)
                                    
                                    # Guardar para uso posterior na seção "Outros Itens"
                                    if produtos_servicos is not None and not produtos_servicos.empty:
                                        st.session_state['produtos_servicos_filtrados'] = produtos_servicos
                                    
                                    # Se ainda temos produtos depois da filtragem
                                    if not produtos_filtrados.empty:
                                        # Calcular valor total
                                        produtos_filtrados['valor_total'] = produtos_filtrados['valor'] * produtos_filtrados['quantidade']
                                        total_produtos = produtos_filtrados['valor_total'].sum()
                                        
                                        # Formatar para exibição
                                        df_produtos = pd.DataFrame()
                                        df_produtos['Nome'] = produtos_filtrados['nome']
                                        df_produtos['Valor Unit.'] = produtos_filtrados['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                        df_produtos['Quantidade'] = produtos_filtrados['quantidade']
                                        df_produtos['Valor Total'] = produtos_filtrados['valor_total'].apply(lambda x: f"R$ {float(x):.2f}")
                                        df_produtos['Cômodo'] = produtos_filtrados['comodo']
                                        
                                        st.dataframe(df_produtos, hide_index=True, use_container_width=True)
                                        st.info(f"Total Produtos: R$ {total_produtos:.2f}")
                                    else:
                                        st.info("Nenhum produto físico adicionado a esta proposta.")
                                else:
                                    st.info("Nenhum produto adicionado a esta proposta.")
                                
                                # 3. Fornecedores
                                st.write("### Fornecedores")
                                fornecedores = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "FORNECEDOR")
                                if not fornecedores.empty:
                                    total_fornecedores = fornecedores['valor'].sum()
                                    
                                    # Formatar para exibição
                                    df_fornecedores = pd.DataFrame()
                                    df_fornecedores['Fornecedor'] = fornecedores['fornecedor']
                                    df_fornecedores['Descrição'] = fornecedores['descricao']
                                    df_fornecedores['Valor'] = fornecedores['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                    
                                    st.dataframe(df_fornecedores, hide_index=True, use_container_width=True)
                                    st.info(f"Total Fornecedores: R$ {total_fornecedores:.2f}")
                                else:
                                    st.info("Nenhum fornecedor adicionado a esta proposta.")
                                
                                # 4. Assistentes
                                st.write("### Assistentes")
                                assistentes = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "ASSISTENTE")
                                if not assistentes.empty:
                                    total_assistentes = assistentes['valor'].sum()
                                    
                                    # Formatar para exibição
                                    df_assistentes = pd.DataFrame()
                                    df_assistentes['Assistente'] = assistentes['fornecedor']
                                    df_assistentes['Descrição'] = assistentes['descricao']
                                    df_assistentes['Valor'] = assistentes['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                    
                                    st.dataframe(df_assistentes, hide_index=True, use_container_width=True)
                                    st.info(f"Total Assistentes: R$ {total_assistentes:.2f}")
                                else:
                                    st.info("Nenhum assistente adicionado a esta proposta.")
                                
                                # 5. Outros itens
                                st.write("### Outros Itens")
                                # Buscar itens do tipo OUTRO (singular) e OUTROS (plural) para garantir compatibilidade
                                outros_itens_singular = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "OUTRO")
                                outros_itens_plural = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_exec_id, "OUTROS")
                                
                                # Unir os dois conjuntos de dados
                                if not outros_itens_singular.empty and not outros_itens_plural.empty:
                                    outros_itens = pd.concat([outros_itens_singular, outros_itens_plural])
                                elif not outros_itens_singular.empty:
                                    outros_itens = outros_itens_singular
                                else:
                                    outros_itens = outros_itens_plural
                                
                                # Verificar se há produtos de serviço (UBER etc.) filtrados anteriormente
                                tem_produtos_servico = 'produtos_servicos_filtrados' in st.session_state and not st.session_state['produtos_servicos_filtrados'].empty
                                
                                # DEBUG - Verificar produtos do tipo "caixa" diretamente no banco
                                try:
                                    # Buscar produtos com caixa no nome
                                    # Buscar produtos usando a função segura já existente
                                    produtos_df = st.session_state.db.get_produtos_organizadores_sql_direto(proposta_id=proposta_exec_id)
                                    
                                    produtos_caixa = []
                                    if not produtos_df.empty:
                                        # Filtrar produtos que contêm "caixa" no nome (case insensitive)
                                        caixas_df = produtos_df[produtos_df['nome'].str.lower().str.contains('caixa', na=False)]
                                        
                                        if not caixas_df.empty:
                                            for _, row in caixas_df.iterrows():
                                                produtos_caixa.append({
                                                    "id": row['id'],
                                                    "nome": row['nome'],
                                                    "valor": float(row['valor']) if pd.notna(row['valor']) else 0,
                                                    "quantidade": int(row['quantidade']) if pd.notna(row['quantidade']) else 1
                                                })
                                    
                                    # Se encontramos produtos do tipo caixa, adicionar à tabela
                                    if produtos_caixa:
                                        # Criar DataFrame para os produtos caixa
                                        df_caixa = pd.DataFrame(produtos_caixa)
                                        
                                        # Se não temos outros itens, criar DataFrame vazio
                                        if outros_itens.empty:
                                            outros_itens = pd.DataFrame(columns=['id', 'tipo', 'fornecedor', 'descricao', 'valor', 'status_pagamento', 'data_cadastro'])
                                            
                                        # Para cada produto caixa, adicionar como um "Outro item"
                                        for _, produto in df_caixa.iterrows():
                                            # Verificar se este item já está nos outros_itens
                                            if 'descricao' in outros_itens.columns and 'valor' in outros_itens.columns:
                                                # Verificar se já existe um item com o mesmo nome e valor
                                                ja_existe = outros_itens[
                                                    (outros_itens['descricao'] == produto['nome']) & 
                                                    (outros_itens['valor'] == produto['valor'])
                                                ].shape[0] > 0
                                                
                                                if not ja_existe:
                                                    # Criar um novo registro para o DataFrame
                                                    novo_item = pd.DataFrame({
                                                        'id': [None],
                                                        'tipo': ['OUTRO'],
                                                        'fornecedor': [''],
                                                        'descricao': [produto['nome']],
                                                        'valor': [produto['valor']],
                                                        'status_pagamento': ['Pendente'],
                                                        'data_cadastro': [None]
                                                    })
                                                    
                                                    # Adicionar ao DataFrame principal
                                                    outros_itens = pd.concat([outros_itens, novo_item])
                                except Exception as e:
                                    st.warning(f"Erro ao buscar produtos tipo caixa: {str(e)}")
                                
                                if not outros_itens.empty or tem_produtos_servico:
                                    # Inicializar o DataFrame para exibição
                                    df_outros = pd.DataFrame()
                                    
                                    # Adicionar os acréscimos do tipo OUTROS
                                    # Agora usando o nome em vez da descrição conforme solicitado
                                    if not outros_itens.empty:
                                        df_temp = pd.DataFrame()
                                        # Verificar se a coluna 'fornecedor' tem valor, se não usar a descricao
                                        df_temp['Nome do Item'] = outros_itens.apply(
                                            lambda row: row['fornecedor'] if pd.notna(row['fornecedor']) and row['fornecedor'].strip() != '' 
                                            else row['descricao'], 
                                            axis=1
                                        )
                                        df_temp['Valor'] = outros_itens['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                        df_temp['Tipo'] = "Acréscimo"
                                        df_outros = pd.concat([df_outros, df_temp])
                                    
                                    # Adicionar os produtos de serviço (UBER etc.)
                                    if tem_produtos_servico:
                                        try:
                                            produtos_servicos = st.session_state['produtos_servicos_filtrados'].copy()
                                            # Garantir que campos numéricos sejam números
                                            if 'valor' in produtos_servicos.columns:
                                                produtos_servicos['valor'] = produtos_servicos['valor'].astype(float)
                                            if 'quantidade' in produtos_servicos.columns:
                                                produtos_servicos['quantidade'] = produtos_servicos['quantidade'].astype(float)
                                            # Calcular total com valores numéricos corrigidos
                                            produtos_servicos['valor_total'] = produtos_servicos['valor'] * produtos_servicos['quantidade']
                                            
                                            df_temp = pd.DataFrame()
                                            if 'nome' in produtos_servicos.columns:
                                                df_temp['Nome do Item'] = produtos_servicos['nome']
                                            else:
                                                df_temp['Nome do Item'] = ["Item sem nome"] * len(produtos_servicos)
                                                
                                            df_temp['Valor'] = produtos_servicos['valor_total'].apply(lambda x: f"R$ {float(x):.2f}")
                                            df_temp['Tipo'] = "Serviço"
                                            df_outros = pd.concat([df_outros, df_temp])
                                        except Exception as e:
                                            st.warning(f"Não foi possível exibir produtos de serviço: {str(e)}")
                                    
                                    # Calcular valor total
                                    total_outros = 0
                                    if not outros_itens.empty:
                                        total_outros += outros_itens['valor'].sum()
                                    
                                    if tem_produtos_servico:
                                        try:
                                            produtos_servicos = st.session_state['produtos_servicos_filtrados'].copy()
                                            # Garantir que campos numéricos sejam números
                                            if 'valor' in produtos_servicos.columns:
                                                produtos_servicos['valor'] = produtos_servicos['valor'].astype(float)
                                            if 'quantidade' in produtos_servicos.columns:
                                                produtos_servicos['quantidade'] = produtos_servicos['quantidade'].astype(float)
                                            # Calcular total com valores numéricos corrigidos
                                            produtos_servicos['valor_total'] = produtos_servicos['valor'] * produtos_servicos['quantidade']
                                            total_outros += produtos_servicos['valor_total'].sum()
                                        except Exception as e:
                                            st.warning(f"Erro ao calcular o total de produtos de serviço: {str(e)}")
                                    
                                    # Exibir dados e totais
                                    st.dataframe(df_outros, hide_index=True, use_container_width=True)
                                    st.info(f"Total Outros Itens: R$ {total_outros:.2f}")
                                else:
                                    st.info("Nenhum item adicional nesta proposta.")
                                
                                # 6. Resumo financeiro
                                st.write("### Resumo Financeiro")
                                
                                # Calcular totais
                                valor_personal_organizer = float(proposta_exec.iloc[0]['valor'])
                                valor_produtos = total_produtos if 'total_produtos' in locals() else 0
                                valor_fornecedores = total_fornecedores if 'total_fornecedores' in locals() else 0
                                valor_assistentes = total_assistentes if 'total_assistentes' in locals() else 0
                                valor_outros = total_outros if 'total_outros' in locals() else 0
                                
                                # Os assistentes são despesas, então devem ser subtraídos do total
                                valor_total = valor_personal_organizer + valor_produtos + valor_fornecedores - valor_assistentes + valor_outros
                                
                                # Mensagem de debug para acompanhar os valores
                                print(f"DEBUG FINANCEIRO: base={valor_personal_organizer}, produtos={valor_produtos}, fornecedores={valor_fornecedores}, assistentes={valor_assistentes} (subtraído), outros={valor_outros}, total={valor_total}")
                                
                                resumo = pd.DataFrame({
                                    "Item": ["Valor Personal Organizer", "Produtos", "Fornecedores", "Assistentes", "Outros", "Total Geral"],
                                    "Valor": [
                                        f"R$ {valor_personal_organizer:.2f}",
                                        f"R$ {valor_produtos:.2f}",
                                        f"R$ {valor_fornecedores:.2f}",
                                        f"R$ {valor_assistentes:.2f}",
                                        f"R$ {valor_outros:.2f}",
                                        f"R$ {valor_total:.2f}"
                                    ]
                                })
                                
                                st.dataframe(resumo, hide_index=True, use_container_width=True)
                                
                                # Gráfico de distribuição de valores
                                st.write("### Distribuição de Valores")
                                valores = {
                                    'Valor Personal Organizer': valor_personal_organizer,
                                    'Produtos': valor_produtos,
                                    'Fornecedores': valor_fornecedores,
                                    'Assistentes (Custos)': -valor_assistentes if valor_assistentes > 0 else 0,  # Negativo para representar custos
                                    'Outros': valor_outros
                                }
                                
                                # Filtrar apenas valores diferentes de zero (valor absoluto)
                                valores_filtrados = {k: abs(v) for k, v in valores.items() if v != 0}
                                
                                # Criar versão alternativa do gráfico usando plotly para maior compatibilidade
                                
                                if valores_filtrados:
                                    labels = list(valores_filtrados.keys())
                                    values = list(valores_filtrados.values())
                                    
                                    fig = go.Figure(data=[go.Pie(
                                        labels=labels,
                                        values=values,
                                        hole=.3,
                                        hoverinfo='label+percent',
                                        textinfo='label+value'
                                    )])
                                    
                                    fig.update_layout(
                                        title="Distribuição de Valores da Proposta",
                                        height=500
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                
                            except Exception as e:
                                st.error(f"Erro ao gerar resumo da proposta: {str(e)}")
                            
                            # Botão para finalizar a proposta
                            st.markdown("---")
                            if st.button("Marcar como Concluída", key=f"finalizar_{proposta_exec_id}"):
                                try:
                                    # Usar a nova função de finalização robusta
                                    from utils.finalizar_proposta_fix import finalizar_proposta_sql
                                    
                                    with st.spinner("Finalizando proposta..."):
                                        # Chamar a função segura que usa uma sessão isolada para evitar problemas de concorrência
                                        resultado = finalizar_proposta_segura(proposta_exec_id)
                                        
                                        # Verificar se a operação foi bem-sucedida
                                        if resultado.get("status", False):
                                            # Mostrar mensagem de sucesso
                                            st.success(f"Proposta #{proposta_exec_numero} marcada como concluída!")
                                            
                                            # Mostrar detalhes dos lançamentos gerados
                                            lancamentos = resultado.get("lancamentos", {})
                                            lancamentos_count = lancamentos.get("gerados", 0)
                                            
                                            if lancamentos_count > 0:
                                                st.success(f"{lancamentos_count} lançamentos financeiros gerados com sucesso!")
                                                
                                                # Mostrar detalhes dos valores em um expander
                                                with st.expander("Detalhes dos lançamentos"):
                                                    valores = lancamentos.get("valores", {})
                                                    st.write(f"- Valor Personal Organizer: R$ {valores.get('base', 0):.2f}")
                                                    st.write(f"- Produtos: R$ {valores.get('produtos', 0):.2f}")
                                                    st.write(f"- Fornecedores: R$ {valores.get('fornecedores', 0) if 'fornecedores' in valores else 0:.2f}")
                                                    st.write(f"- Assistentes a Pagar: R$ {valores.get('assistentes', 0) if 'assistentes' in valores else 0:.2f}")
                                                    st.write(f"- Outros: R$ {valores.get('outros', 0) if 'outros' in valores else 0:.2f}")
                                            
                                            # Mostrar detalhes de vendas registradas, se houver        
                                            if "venda_id" in resultado:
                                                venda_id = resultado.get("venda_id")
                                                produtos_vendidos = resultado.get("produtos_vendidos", 0)
                                                st.success(f"Venda #{venda_id} registrada com {produtos_vendidos} produtos!")
                                            
                                            # Atualizar a interface após completar a operação
                                            time.sleep(2)  # Dar tempo para o usuário ver as mensagens
                                            st.rerun()
                                        else:
                                            # Mostrar mensagem de erro
                                            st.error(f"Falha ao marcar proposta como concluída: {resultado.get('mensagem', 'Erro desconhecido')}")
                                
                                except Exception as e:
                                    # Capturar e mostrar qualquer erro que ocorra durante o processo
                                    st.error(f"Erro ao finalizar proposta: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
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
                    # Manter o ID como coluna oculta para referência
                    df_finalizadas['ID'] = propostas_finalizadas['id']
                    df_finalizadas['Número'] = propostas_finalizadas['numero']
                    df_finalizadas['Cliente'] = propostas_finalizadas['nome']
                    df_finalizadas['Descrição'] = propostas_finalizadas['descricao']
                    df_finalizadas['Valor (R$)'] = propostas_finalizadas['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                    
                    # Formatar datas para exibição - removida coluna Início duplicada
                    df_finalizadas['Início Execução'] = propostas_finalizadas['data_inicio_execucao'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Adicionar coluna de Fim Execução (usando a data_fim)
                    # Deixar em branco para propostas recusadas
                    df_finalizadas['Fim Execução'] = propostas_finalizadas.apply(
                        lambda row: '' if row['status'] == 'Recusada' else row['data_fim'].strftime('%d/%m/%Y') if pd.notna(row['data_fim']) else '',
                        axis=1
                    )
                    
                    # Exibir tabela sem mostrar a coluna ID
                    st.dataframe(df_finalizadas.drop(columns=['ID']), hide_index=True)
                    
                    # Adicionar área para reabrir proposta finalizada
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
                    
                    if not proposta_final.empty:
                        st.write(f"Proposta #{proposta_final.iloc[0]['numero']} - {proposta_final.iloc[0]['descricao']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Gerar Relatório para Cliente", key=f"relatorio_cliente_{proposta_numero}"):
                                with st.spinner("Gerando relatório para cliente..."):
                                    try:
                                        # Obter dados da proposta
                                        proposta_dict = proposta_final.iloc[0].to_dict()
                                        
                                        # Obter dados do cliente
                                        cliente = st.session_state.db.get_cliente_by_id(proposta_dict['cliente_id'])
                                        cliente_dict = cliente.iloc[0].to_dict() if not cliente.empty else {'nome': 'Cliente não encontrado'}
                                        
                                        # Obter acréscimos da proposta
                                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta_dict['id'])
                                        
                                        # Definir caminho do arquivo com o formato solicitado (relatório + número da proposta + nome do cliente)
                                        nome_cliente_formatado = cliente_dict['nome'].replace(' ', '_').replace('/', '_').replace('\\', '_')
                                        relatorio_path = f"pdfs/relatorio_{proposta_dict['numero']}_{nome_cliente_formatado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                        
                                        # Gerar o PDF
                                        from utils.pdf_generator import gerar_pdf_cliente
                                        pdf_path = gerar_pdf_cliente(proposta_dict, cliente_dict, acrescimos, relatorio_path)
                                        
                                        # Criar link para download
                                        with open(pdf_path, "rb") as pdf_file:
                                            pdf_bytes = pdf_file.read()
                                        
                                        # Mostrar mensagem de sucesso
                                        st.success(f"Relatório para cliente gerado com sucesso!")
                                        
                                        # Criar botão de download com key única
                                        download_key = f"download_cliente_{proposta_dict['numero']}_{datetime.now().strftime('%H%M%S')}"
                                        st.download_button(
                                            label="Download do Relatório",
                                            data=pdf_bytes,
                                            file_name=f"relatório_{proposta_dict['numero']}_{cliente_dict['nome']}.pdf",
                                            mime="application/pdf",
                                            key=download_key
                                        )
                                    except Exception as e:
                                        st.error(f"Erro ao gerar relatório para cliente: {str(e)}")
                        
                        with col2:
                            if st.button("Gerar Relatório Interno", key=f"relatorio_interno_{proposta_numero}"):
                                with st.spinner("Gerando relatório interno..."):
                                    try:
                                        # Obter dados da proposta
                                        proposta_dict = proposta_final.iloc[0].to_dict()
                                        
                                        # Obter dados do cliente
                                        cliente = st.session_state.db.get_cliente_by_id(proposta_dict['cliente_id'])
                                        cliente_dict = cliente.iloc[0].to_dict() if not cliente.empty else {'nome': 'Cliente não encontrado'}
                                        
                                        # Obter acréscimos da proposta
                                        acrescimos = st.session_state.db.get_acrescimos_proposta(proposta_dict['id'])
                                        
                                        # Obter transações financeiras relacionadas à proposta
                                        # Filtrar para obter as comissões
                                        financeiro = st.session_state.db.get_financeiro(include_all=True)
                                        print(f"DEBUG: Total de transações financeiras: {len(financeiro)}")
                                        
                                        if not financeiro.empty:
                                            print(f"DEBUG: Procurando comissões para proposta ID={proposta_dict['id']}")
                                            print(f"DEBUG: Colunas disponíveis: {financeiro.columns.tolist()}")
                                            
                                            # Verificar se proposta_id existe nas colunas
                                            if 'proposta_id' in financeiro.columns:
                                                # Mostrar alguns valores de proposta_id para debug
                                                proposta_ids = financeiro['proposta_id'].dropna().unique()
                                                print(f"DEBUG: Valores únicos de proposta_id: {proposta_ids}")
                                                
                                                # Filtrar por proposta_id
                                                transacoes_proposta = financeiro[financeiro['proposta_id'] == proposta_dict['id']]
                                                print(f"DEBUG: Transações desta proposta: {len(transacoes_proposta)}")
                                                
                                                # Mostrar todas as transações para esta proposta para debug
                                                if not transacoes_proposta.empty:
                                                    print("DEBUG: Transações encontradas para esta proposta:")
                                                    for idx, tx in transacoes_proposta.iterrows():
                                                        print(f"DEBUG: Transação {idx}: {tx['descricao']}, tipo={tx.get('tipo', 'N/A')}, categoria={tx.get('categoria', 'N/A')}, subcategoria={tx.get('subcategoria', 'N/A')}, valor={tx.get('valor', 0)}")
                                            else:
                                                print("DEBUG: Coluna 'proposta_id' não encontrada no DataFrame financeiro")
                                            
                                            # Filtrar as comissões - analisar valores categorizados como "Comissão de Fornecedor"
                                            comissoes = financeiro[
                                                (financeiro['proposta_id'] == proposta_dict['id']) & 
                                                (
                                                    (financeiro['categoria'].str.lower().str.contains('comissão')) | 
                                                    (financeiro['categoria'].str.lower().str.contains('comissao')) | 
                                                    (financeiro['subcategoria'].str.lower().str.contains('comissão')) |
                                                    (financeiro['subcategoria'].str.lower().str.contains('comissao')) |
                                                    (financeiro['tipo_receita'].str.lower().str.contains('comissão')) |
                                                    (financeiro['tipo_receita'].str.lower().str.contains('comissao'))
                                                )
                                            ]
                                            
                                            # Converter comissões para o mesmo formato dos acréscimos
                                            if not comissoes.empty:
                                                print(f"DEBUG: Encontradas {len(comissoes)} comissões para a proposta {proposta_dict['id']}")
                                                # Adicionar coluna 'comissao' para indicar que são registros de comissão
                                                for _, comissao in comissoes.iterrows():
                                                    print(f"DEBUG: Comissão encontrada: {comissao['descricao']} - R$ {comissao['valor']}")
                                                    
                                                    # Adicionar ao DataFrame de acréscimos
                                                    novo_acrescimo = {
                                                        'id': comissao['id'], 
                                                        'tipo': 'COMISSÃO',
                                                        'fornecedor': comissao.get('origem_tipo', ''),
                                                        'descricao': comissao['descricao'],
                                                        'valor': comissao['valor'],
                                                        'status_pagamento': comissao['status'],
                                                        'data_cadastro': comissao['data'],
                                                        'categoria': comissao['categoria'],
                                                        'subcategoria': comissao['subcategoria'],
                                                        'tipo_receita': comissao.get('tipo_receita', '')
                                                    }
                                                    
                                                    # Adicionar ao DataFrame de acréscimos
                                                    acrescimos = pd.concat([acrescimos, pd.DataFrame([novo_acrescimo])], ignore_index=True)
                                        
                                        # Definir caminho do arquivo
                                        # Nome do arquivo inclui o nome do cliente para fácil identificação
                                        cliente_nome_simplificado = proposta_dict['cliente_nome'].replace(" ", "_")[:20] # Limitar tamanho
                                        relatorio_path = f"pdfs/relatorio_interno_{proposta_dict['numero']}_{cliente_nome_simplificado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                        
                                        # Gerar o PDF
                                        from utils.pdf_generator import gerar_pdf_interno
                                        pdf_path = gerar_pdf_interno(proposta_dict, cliente_dict, acrescimos, relatorio_path)
                                        
                                        # Criar link para download
                                        with open(pdf_path, "rb") as pdf_file:
                                            pdf_bytes = pdf_file.read()
                                        
                                        # Mostrar mensagem de sucesso
                                        st.success(f"Relatório interno gerado com sucesso!")
                                        
                                        # Criar botão de download com key única
                                        download_key = f"download_interno_{proposta_dict['numero']}_{datetime.now().strftime('%H%M%S')}"
                                        st.download_button(
                                            label="Download do Relatório Interno",
                                            data=pdf_bytes,
                                            file_name=f"relatorio_interno_{proposta_dict['numero']}_{cliente_nome_simplificado}.pdf",
                                            mime="application/pdf",
                                            key=download_key
                                        )
                                    except Exception as e:
                                        st.error(f"Erro ao gerar relatório interno: {str(e)}")
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
                    # Garantir que os valores sejam do tipo string para evitar erro de comparação entre tipos
                    try:
                        status_values = [str(x) for x in propostas['status'].unique() if pd.notna(x)]
                        status_filter = st.multiselect(
                            "Status:",
                            sorted(status_values),
                            default=sorted(status_values)
                        )
                    except Exception as e:
                        st.error(f"Erro ao carregar filtros de status: {str(e)}")
                        status_filter = []
                
                with col2:
                    # Garantir que os valores sejam do tipo string para evitar erro de comparação entre tipos
                    try:
                        clientes_values = [str(x) for x in propostas_com_clientes['nome'].unique() if pd.notna(x)]
                        clientes_filter = st.multiselect(
                            "Cliente:",
                            sorted(clientes_values),
                            default=sorted(clientes_values)
                        )
                    except Exception as e:
                        st.error(f"Erro ao carregar filtros de clientes: {str(e)}")
                        clientes_filter = []
                
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
                    df_todas['ID'] = propostas_filtradas['id']
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
                        
                    # Colunas de início e fim de execução - Removida coluna Início duplicada
                    df_todas['Início Execução'] = propostas_filtradas['data_inicio_execucao'].apply(
                        lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                    )
                    
                    # Deixar Fim Execução em branco para propostas recusadas
                    df_todas['Fim Execução'] = propostas_filtradas.apply(
                        lambda row: '' if row['status'] == 'Recusada' else row['data_fim'].strftime('%d/%m/%Y') if pd.notna(row['data_fim']) else '', 
                        axis=1
                    )
                    
                    # Exibir tabela sem a coluna ID
                    st.dataframe(df_todas.drop(columns=['ID']), hide_index=True)
                    
                    # Adicionar área para exclusão de proposta
                    with st.expander("Excluir Proposta"):
                        # Obter lista de números de propostas para o select box
                        numeros_propostas = propostas_filtradas['numero'].tolist()
                        numeros_propostas.sort()  # Ordenar para facilitar a seleção
                        
                        proposta_numero = st.selectbox(
                            "Selecione o número da proposta a excluir:",
                            numeros_propostas,
                            key="numero_proposta_todas_excluir"
                        )
                        
                        proposta_exc = propostas_filtradas[propostas_filtradas['numero'] == proposta_numero]
                        
                        if not proposta_exc.empty:
                            st.warning(f"Você está prestes a excluir a proposta #{proposta_numero} - {proposta_exc.iloc[0]['descricao']}")
                            if st.button("CONFIRMAR EXCLUSÃO", key="confirmar_exclusao_todas"):
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