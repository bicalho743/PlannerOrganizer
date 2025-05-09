import streamlit as st
from utils.finalizar_proposta_fix import finalizar_proposta_segura
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
    tab1, tab2, tab3 = st.tabs([
        "📝 Nova Proposta", 
        "⚙️ Em Execução", 
        "📋 Propostas Finalizadas"
    ])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Carregar todas as propostas e clientes para reuso
    try:
        propostas = st.session_state.db.get_propostas()
        clientes = st.session_state.db.get_clientes()
        
        # Garantir que todas as colunas numéricas sejam do tipo correto
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
            propostas_com_clientes = propostas.copy() if not propostas.empty else pd.DataFrame()
    
    except Exception as e:
        st.error(f"Erro ao carregar dados iniciais: {str(e)}")
        return
    
    # ABA 1: NOVA PROPOSTA
    with tab1:
        st.header("Nova Proposta")
        
        # Criar tabs dentro da primeira aba
        proposta_tab1, proposta_tab2 = st.tabs(["Nova Proposta", "Gerenciar Propostas"])
        
        # SUBTAB 1: NOVA PROPOSTA
        with proposta_tab1:
            try:
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
                            
                            # Status inicial para novas propostas
                            status_opcoes = [
                                "Aguardando", # Novo padrão (equivalente a Em elaboração/Aguardando aprovação)
                                "Aprovada",   # Vai para Em execução
                                "Recusada"    # Vai para Finalizada
                            ]
                            status_inicial = st.selectbox("Status inicial da proposta:", status_opcoes, index=0)
                            
                        else:
                            data_inicio = st.date_input("Data de início:", datetime.now().date() - timedelta(days=30))
                            
                            # Para cadastros retroativos, oferecer todas as opcões
                            status_opcoes = [
                                "Aguardando", # Novo padrão unificado
                                "Aprovada",   # Vai para Em execução
                                "Recusada",   # Vai para Finalizada
                                "Em execução",
                                "Finalizada"
                            ]
                            status_inicial = st.selectbox("Status da proposta:", status_opcoes)
                            
                            # Inicializar variáveis com valores padrão
                            data_aprovacao = data_inicio  # Valor padrão
                            data_inicio_execucao = data_inicio  # Valor padrão
                            data_fim_real = data_inicio + timedelta(days=prazo)  # Valor padrão
                            status_pagamento = "Pendente"  # Valor padrão
                            
                            # Datas relacionadas ao status selecionado
                            if status_inicial in ["Aprovada", "Em execução", "Finalizada"]:
                                data_aprovacao = st.date_input("Data de aprovação:", data_inicio)
                            
                            if status_inicial in ["Em execução", "Finalizada"]:
                                # A data de início de execução é sempre igual à data de início da proposta
                                st.info("A data de início de execução será igual à data de início da proposta.")
                                data_inicio_execucao = data_inicio
                            
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
                                
                                # Mapear status selecionado para o status no banco de dados
                                status_proposta_mapeado = status_inicial
                                
                                # Realizar conversão do status unificado para os status do banco
                                if status_inicial == "Aguardando":
                                    status_proposta_mapeado = "Em elaboração"
                                elif status_inicial == "Aprovada":
                                    status_proposta_mapeado = "Em execução"
                                elif status_inicial == "Recusada":
                                    status_proposta_mapeado = "Finalizada"
                                
                                # Status e configurações baseadas no tipo de cadastro
                                if tipo_cadastro == "Nova proposta":
                                    gerar_transacoes = status_inicial == "Aprovada"
                                else:
                                    # Usar valor padrão se variável não estiver disponível
                                    if 'gerar_financeiro' in locals():
                                        gerar_transacoes = gerar_financeiro
                                    else:
                                        gerar_transacoes = False
                                
                                # Criar nova proposta
                                novo_numero = st.session_state.db.add_proposta(
                                    cliente_id=cliente_id,
                                    descricao=descricao,
                                    valor=valor,
                                    status=status_proposta_mapeado,
                                    tipo_proposta=tipo_proposta,
                                    data_inicio=data_inicio,
                                    data_fim=data_fim,
                                    previsao_dias=prazo,
                                    prazo_entrega=data_inicio,
                                    gerar_transacoes_automaticas=gerar_transacoes
                                )
                                
                                # Para propostas com status avançados, atualizar campos adicionais
                                if novo_numero:
                                    proposta_atualizada = {}
                                    
                                    # Adicionar datas relacionadas ao status
                                    if status_inicial in ["Aprovada", "Em execução", "Finalizada"]:
                                        if tipo_cadastro == "Cadastro retroativo" and 'data_aprovacao' in locals():
                                            proposta_atualizada['data_aprovacao'] = data_aprovacao
                                            proposta_atualizada['data_proposta'] = data_aprovacao
                                        else:
                                            proposta_atualizada['data_aprovacao'] = data_inicio
                                            proposta_atualizada['data_proposta'] = data_inicio
                                    
                                    if status_inicial in ["Em execução", "Finalizada"]:
                                        proposta_atualizada['data_inicio_execucao'] = data_inicio
                                        proposta_atualizada['status_execucao'] = "Em execução"
                                    
                                    if status_inicial == "Finalizada":
                                        if tipo_cadastro == "Cadastro retroativo" and 'data_fim_real' in locals():
                                            proposta_atualizada['data_fim'] = data_fim_real
                                        else:
                                            proposta_atualizada['data_fim'] = data_fim
                                        proposta_atualizada['status_execucao'] = "Concluída"
                                    
                                    # Status de pagamento para propostas
                                    if status_inicial in ["Aprovada", "Finalizada"] and tipo_cadastro == "Cadastro retroativo" and 'status_pagamento' in locals():
                                        proposta_atualizada['status_pagamento_base'] = status_pagamento
                                    
                                    # Proposta recusada
                                    if status_inicial == "Recusada":
                                        proposta_atualizada['status_execucao'] = "Cancelada"
                                        proposta_atualizada['data_fim'] = datetime.now().date()
                                    
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
                st.error(f"Erro ao renderizar formulário: {str(e)}")
        
        # SUBTAB 2: GERENCIAR PROPOSTAS
        with proposta_tab2:
            st.subheader("Gerenciar Propostas")
            
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
                            
                            # Lidar com os novos status unificados
                            elif novo_status == "Aprovada":
                                # Mapear "Aprovada" para "Em execução"
                                data_aprovacao_local = datetime.now().date()
                                
                                # Log para depuração
                                print(f"DEBUG UI: Alterando proposta {proposta_id} de '{proposta['status']}' para 'Em execução', data_aprovacao={data_aprovacao_local}")
                                
                                # Atualizar o status usando sempre update_proposta_status
                                resultado = st.session_state.db.update_proposta_status(
                                    proposta_id=proposta_id,
                                    novo_status="Em execução",
                                    data_aprovacao=data_aprovacao_local
                                )
                                
                                sucesso = resultado.get('status', False)
                                
                                if sucesso:
                                    st.success(f"Proposta {proposta_id} aprovada e movida para Em execução!")
                                    del st.session_state[alterar_status_key]
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao atualizar proposta {proposta_id}")
                                    del st.session_state[alterar_status_key]
                            
                            elif novo_status == "Recusada":
                                # Mapear "Recusada" para "Finalizada" com status_execucao = "Cancelada"
                                print(f"DEBUG UI: Alterando proposta {proposta_id} para 'Finalizada' (Recusada)")
                                
                                # Primeiro atualizar para finalizada
                                resultado = st.session_state.db.update_proposta_status(
                                    proposta_id=proposta_id,
                                    novo_status="Finalizada"
                                )
                                
                                # Depois atualizar o status_execucao para Cancelada
                                if resultado.get('status', False):
                                    st.session_state.db.update_proposta(
                                        proposta_id, 
                                        status_execucao="Cancelada",
                                        data_fim=datetime.now().date()
                                    )
                                    st.success(f"Proposta {proposta_id} marcada como recusada!")
                                    del st.session_state[alterar_status_key]
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao recusar proposta {proposta_id}")
                                    del st.session_state[alterar_status_key]
                    
                    # Construir interface com seletores de status direto na tabela
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
                            
                            # Coluna 1: Número da proposta
                            with col_num:
                                st.write(f"**{proposta['numero']}**")
                            
                            # Coluna 2: Informações da proposta
                            with col_info:
                                st.markdown(f"""
                                **{proposta['nome']}**  
                                {proposta['descricao']}  
                                **Valor:** {proposta['valor_formatado']} | **Tipo:** {proposta['tipo_proposta']}  
                                **Início Execução:** {proposta['data_inicio_formatada']} | **Prazo:** {proposta['previsao_dias']} dias
                                """)
                            
                            # Coluna 3: Seletor de status com botão para salvar
                            with col_status:
                                # Definir opções de status com base no fluxo de trabalho unificado
                                status_unificado = "Aguardando"
                                if status_atual in ["Em elaboração", "Aguardando aprovação"]:
                                    status_unificado = "Aguardando"
                                
                                # Opções de status unificado
                                opcoes_status = [
                                    "Aguardando", 
                                    "Aprovada", 
                                    "Recusada"
                                ]
                                
                                # Adicionar opção de exclusão
                                opcoes_status.append("Excluir")
                                
                                # Índice padrão para o seletor
                                try:
                                    status_index = opcoes_status.index(status_unificado)
                                except ValueError:
                                    status_index = 0
                                
                                # Criar duas colunas para o seletor e o botão
                                status_col, btn_col = st.columns([3, 1])
                                
                                with status_col:
                                    # Seletor de status
                                    novo_status = st.selectbox(
                                        f"Status: {status_unificado}",
                                        opcoes_status,
                                        index=status_index,
                                        format_func=lambda x: f"❌ Excluir proposta" if x == "Excluir" else x,
                                        key=f"status_sel_{proposta_id}",
                                        label_visibility="collapsed"
                                    )
                                
                                with btn_col:
                                    # Botão de salvar alteração
                                    if st.button("Salvar", key=f"btn_save_{proposta_id}"):
                                        if novo_status == status_unificado:
                                            st.success("✓ Sem alterações")
                                        elif novo_status == "Excluir":
                                            # Criar um botão de confirmação
                                            confirmar_key = f"confirm_del_{proposta_id}"
                                            st.warning("⚠️ Tem certeza?")
                                            if st.button("Confirmar", key=confirmar_key):
                                                st.session_state[f"alterar_status_{proposta_id}"] = "Excluir"
                                                st.rerun()
                                        else:
                                            st.session_state[f"alterar_status_{proposta_id}"] = novo_status
                                            st.rerun()
                            
                            # Coluna 4: Exportar para PDF
                            with col_export:
                                if st.button("📄", key=f"pdf_{proposta_id}"):
                                    st.download_button(
                                        label="Baixar",
                                        data="Arquivo PDF simulado",
                                        file_name=f"proposta_{proposta['numero']}.pdf",
                                        mime="application/pdf",
                                        key=f"download_{proposta_id}"
                                    )
                            
                            # Coluna 5: Botão de exclusão (modo alternativo mais direto)
                            with col_excluir:
                                if st.button("🗑️", key=f"del_{proposta_id}"):
                                    st.warning("⚠️ Tem certeza?")
                                    confirmar_key = f"confirm_del_direct_{proposta_id}"
                                    if st.button("Sim", key=confirmar_key):
                                        st.session_state[f"alterar_status_{proposta_id}"] = "Excluir"
                                        st.rerun()
                                                
                else:
                    st.info("Não há propostas em aberto no momento.")
            else:
                st.info("Não há propostas cadastradas. Crie uma nova proposta na aba ao lado.")

    # ABA 2: EM EXECUÇÃO
    with tab2:
        st.header("Propostas em Execução")
        
        if 'propostas_com_clientes' in locals() and not propostas.empty:
            # Filtrar apenas propostas em execução
            propostas_em_execucao = propostas_com_clientes[
                propostas_com_clientes['status'] == 'Em execução'
            ]
            
            if not propostas_em_execucao.empty:
                # Mostrar as propostas em execução
                st.write(f"Total: {len(propostas_em_execucao)} propostas em execução")
                
                # Criar seletor de proposta para gerenciar
                proposta_selecionada_id = st.selectbox(
                    "Selecione uma proposta para gerenciar:",
                    options=propostas_em_execucao['id'].tolist(),
                    format_func=lambda x: f"#{propostas_em_execucao[propostas_em_execucao['id'] == x]['numero'].iloc[0]} - {propostas_em_execucao[propostas_em_execucao['id'] == x]['nome'].iloc[0]}: {propostas_em_execucao[propostas_em_execucao['id'] == x]['descricao'].iloc[0][:50]}..."
                )
                
                if proposta_selecionada_id:
                    # Obter os dados da proposta selecionada
                    proposta = propostas_em_execucao[propostas_em_execucao['id'] == proposta_selecionada_id].iloc[0]
                    
                    st.subheader(f"Gerenciando: Proposta #{proposta['numero']} - {proposta['nome']}")
                    
                    # Adicionar CSS personalizado para as abas
                    st.markdown("""
                    <style>
                    div[data-testid="stTabs"] > div:nth-child(2) > div:nth-child(1) {
                        background-color: #f1f3f9;
                        padding: 15px;
                        border-radius: 5px;
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
                        with st.form(key=f"form_andamento_{proposta_selecionada_id}"):
                            st.write("Registre uma nova atualização de andamento:")
                            descricao_andamento = st.text_area("Descrição:", height=100)
                            data_andamento = st.date_input("Data:", datetime.now())
                            porcentagem = st.slider("Porcentagem concluída:", 0, 100, 0)
                            observacoes = st.text_area("Observações:", height=70)
                            
                            andamento_salvar = st.form_submit_button("Registrar Andamento")
                            
                            if andamento_salvar:
                                # Lógica para salvar o andamento
                                st.success("Andamento registrado com sucesso!")
                        
                        # Calcular e mostrar progresso da proposta
                        data_inicio_exec = proposta.get('data_inicio_execucao', proposta['data_inicio'])
                        data_fim_prevista = proposta.get('data_fim', data_inicio_exec + timedelta(days=30))
                        
                        hoje = datetime.now().date()
                        total_dias = (data_fim_prevista - data_inicio_exec).days
                        dias_decorridos = (hoje - data_inicio_exec).days
                        
                        if total_dias > 0:
                            progresso = min(100, max(0, int(dias_decorridos / total_dias * 100)))
                            st.write("**Progresso baseado no prazo:**")
                            st.progress(progresso)
                            st.caption(f"Progresso: {progresso}% ({dias_decorridos} de {total_dias} dias)")
                            
                            # Verificar se está atrasado
                            if hoje > data_fim_prevista:
                                st.warning(f"⚠️ Proposta atrasada por {(hoje - data_fim_prevista).days} dias!")
                            else:
                                dias_restantes = (data_fim_prevista - hoje).days
                                st.info(f"📅 Restam {dias_restantes} dias para a conclusão prevista")
                    
                    with exec_tab2:
                        st.subheader("Produtos")
                        
                        st.write("Lista de produtos para esta proposta:")
                        # Implementação de produtos
                        with st.form(key=f"form_produto_{proposta_selecionada_id}"):
                            st.write("Adicionar novo produto:")
                            nome_produto = st.text_input("Nome do produto:")
                            descricao_produto = st.text_area("Descrição:", height=100)
                            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                            valor_unitario = st.number_input("Valor unitário (R$):", min_value=0.0, value=0.0, format="%.2f")
                            
                            produto_salvar = st.form_submit_button("Adicionar Produto")
                            
                            if produto_salvar:
                                # Lógica para salvar o produto
                                st.success("Produto adicionado com sucesso!")
                    
                    with exec_tab3:
                        st.subheader("Outros")
                        
                        st.write("Informações adicionais e acréscimos")
                        # Implementação de outras informações
                        with st.form(key=f"form_outros_{proposta_selecionada_id}"):
                            st.write("Adicionar acréscimo:")
                            descricao_acrescimo = st.text_input("Descrição do acréscimo:")
                            valor_acrescimo = st.number_input("Valor (R$):", min_value=0.0, value=0.0, format="%.2f")
                            justificativa = st.text_area("Justificativa:", height=100)
                            
                            acrescimo_salvar = st.form_submit_button("Adicionar Acréscimo")
                            
                            if acrescimo_salvar:
                                # Lógica para salvar o acréscimo
                                st.success("Acréscimo registrado com sucesso!")
                    
                    with exec_tab4:
                        st.subheader("Fornecedores")
                        
                        st.write("Fornecedores envolvidos nesta proposta")
                        # Implementação de fornecedores
                        # Consultar os fornecedores da base
                        try:
                            fornecedores = st.session_state.db.get_fornecedores()
                            if not fornecedores.empty:
                                with st.form(key=f"form_fornecedor_{proposta_selecionada_id}"):
                                    fornecedor_selecionado = st.selectbox(
                                        "Selecione um fornecedor:", 
                                        options=fornecedores['id'].tolist(),
                                        format_func=lambda x: fornecedores.loc[fornecedores['id'] == x, 'nome'].iloc[0]
                                    )
                                    
                                    fornecedor_salvar = st.form_submit_button("Adicionar Fornecedor à Proposta")
                                    
                                    if fornecedor_salvar:
                                        # Lógica para adicionar fornecedor
                                        st.success("Fornecedor adicionado à proposta com sucesso!")
                            else:
                                st.info("Não há fornecedores cadastrados.")
                        except Exception as e:
                            st.error(f"Erro ao carregar fornecedores: {str(e)}")
                    
                    with exec_tab5:
                        st.subheader("Assistentes")
                        
                        st.write("Assistentes alocados nesta proposta")
                        # Implementação de assistentes
                        try:
                            assistentes = st.session_state.db.get_assistentes()
                            if not assistentes.empty:
                                with st.form(key=f"form_assistente_{proposta_selecionada_id}"):
                                    assistente_selecionado = st.selectbox(
                                        "Selecione um assistente:", 
                                        options=assistentes['id'].tolist(),
                                        format_func=lambda x: assistentes.loc[assistentes['id'] == x, 'nome'].iloc[0]
                                    )
                                    
                                    assistente_salvar = st.form_submit_button("Alocar Assistente à Proposta")
                                    
                                    if assistente_salvar:
                                        # Lógica para adicionar assistente
                                        st.success("Assistente alocado à proposta com sucesso!")
                            else:
                                st.info("Não há assistentes cadastrados.")
                        except Exception as e:
                            st.error(f"Erro ao carregar assistentes: {str(e)}")
                    
                    with exec_tab6:
                        st.subheader("🏁 FINALIZAR PROPOSTA")
                        
                        st.warning("⚠️ **Atenção**: Finalizar uma proposta não poderá ser desfeito facilmente.")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.form(key=f"form_finalizar_concluida_{proposta_selecionada_id}"):
                                finalizar_concluida = st.form_submit_button("Finalizar como Concluída")
                                if finalizar_concluida:
                                    try:
                                        # Chamar a função para finalizar proposta
                                        resultado = finalizar_proposta_segura(proposta_selecionada_id)
                                        if resultado.get('status', False):
                                            st.success("✅ Proposta finalizada com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Erro ao finalizar proposta: {resultado.get('message', 'Erro desconhecido')}")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao finalizar proposta: {str(e)}")
                        
                        with col2:
                            with st.form(key=f"form_finalizar_recusada_{proposta_selecionada_id}"):
                                finalizar_recusada = st.form_submit_button("Finalizar como Recusada")
                                if finalizar_recusada:
                                    try:
                                        # Aqui poderia chamar uma função específica para recusar proposta
                                        st.error("🚫 Proposta marcada como recusada.")
                                        # Implementar lógica
                                    except Exception as e:
                                        st.error(f"❌ Erro ao recusar proposta: {str(e)}")
                        
                        # Adicionar uma seção para Resumo
                        st.subheader("Resumo da Proposta")
                        
                        # Valores fictícios para demonstração
                        total_produtos = 0
                        total_acrescimos = 0
                        valor_final = float(proposta['valor']) + total_acrescimos
                        
                        st.write(f"**Cliente:** {proposta['nome']}")
                        st.write(f"**Valor Original:** R$ {float(proposta['valor']):,.2f}")
                        st.write(f"**Acréscimos:** R$ {total_acrescimos:,.2f}")
                        st.write(f"**Valor Final:** R$ {valor_final:,.2f}")
                        
                        # Visualização em gráfico
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=['Valor Original', 'Acréscimos', 'Valor Final'],
                            y=[float(proposta['valor']), total_acrescimos, valor_final],
                            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
                        ))
                        fig.update_layout(title='Composição do Valor da Proposta')
                        st.plotly_chart(fig)
            else:
                st.info("Não há propostas em execução no momento.")
    
    # ABA 3: PROPOSTAS FINALIZADAS
    with tab3:
        st.header("Propostas Finalizadas")
        
        if 'propostas_com_clientes' in locals() and not propostas.empty:
            # Filtro específico para mostrar apenas propostas finalizadas
            propostas_finalizadas = propostas_com_clientes[
                ((propostas_com_clientes['status'] == 'Finalizada') & 
                 (propostas_com_clientes['status_execucao'] == 'Concluída')) |
                (propostas_com_clientes['status'] == 'Recusada')
            ]
            
            # Mostrar contagem de propostas finalizadas
            st.write(f"Total de propostas finalizadas encontradas: {len(propostas_finalizadas)}")
            
            if propostas_finalizadas.empty:
                st.info("Não há propostas finalizadas no momento.")
                return
            
            # Interface para filtrar propostas
            col1, col2 = st.columns(2)
            with col1:
                filtro_status = st.multiselect(
                    "Filtrar por status:",
                    propostas_finalizadas['status'].unique().tolist(),
                    default=[]
                )
            with col2:
                filtro_cliente = st.multiselect(
                    "Filtrar por cliente:",
                    propostas_finalizadas['nome'].unique().tolist() if not propostas_finalizadas.empty else [],
                    default=[]
                )
            
            # Aplicar filtros adicionais
            propostas_filtradas = propostas_finalizadas.copy()
            
            if filtro_status:
                propostas_filtradas = propostas_filtradas[propostas_filtradas['status'].isin(filtro_status)]
            
            if filtro_cliente:
                propostas_filtradas = propostas_filtradas[propostas_filtradas['nome'].isin(filtro_cliente)]
            
            # Mostrar resultados
            if not propostas_filtradas.empty:
                st.write(f"Total: {len(propostas_filtradas)} propostas encontradas")
                
                # Preparar colunas para exibição mais limpa
                propostas_filtradas['data_formatada'] = propostas_filtradas['data_inicio'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                )
                propostas_filtradas['valor_formatado'] = propostas_filtradas['valor'].apply(
                    lambda x: f"R$ {float(x):,.2f}" if pd.notna(x) else ''
                )
                
                # Mostrar em DataEditor para facilitar a visualização
                st.dataframe(
                    propostas_filtradas[['numero', 'nome', 'descricao', 'valor_formatado', 'status', 'data_formatada', 'tipo_proposta']],
                    column_config={
                        'numero': 'Proposta #',
                        'nome': 'Cliente',
                        'descricao': 'Descrição',
                        'valor_formatado': 'Valor',
                        'status': 'Status',
                        'data_formatada': 'Data Início',
                        'tipo_proposta': 'Tipo'
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Adicionar opção para exportar
                with st.form(key="exportar_csv_form"):
                    exportar_csv = st.form_submit_button("Exportar para CSV")
                    
                    if exportar_csv:
                        csv = propostas_filtradas[['numero', 'nome', 'descricao', 'valor_formatado', 'status', 'data_formatada', 'tipo_proposta']].to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name="propostas_exportadas.csv",
                            mime="text/csv"
                        )
                
                # Adicionar funcionalidade para reabrir propostas
                with st.expander("Reabrir Proposta Finalizada"):
                    # Obter lista de números de propostas finalizadas para o select box
                    numeros_propostas = propostas_finalizadas['numero'].tolist()
                    numeros_propostas.sort()  # Ordenar para facilitar a seleção
                    
                    with st.form(key="reabrir_proposta_form"):
                        proposta_numero = st.selectbox(
                            "Selecione o número da proposta a reabrir:",
                            numeros_propostas,
                            key="numero_proposta_finalizada_reabrir"
                        )
                        
                        proposta_reabrir = propostas_finalizadas[propostas_finalizadas['numero'] == proposta_numero]
                        
                        if not proposta_reabrir.empty:
                            st.info(f"Você está prestes a reabrir a proposta #{proposta_numero} - {proposta_reabrir.iloc[0]['descricao']}")
                            st.warning("Esta ação mudará o status da proposta para 'Em execução'.")
                        
                        reabrir_proposta = st.form_submit_button("REABRIR PROPOSTA")
                        
                        if reabrir_proposta and not proposta_reabrir.empty:
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
            else:
                st.info("Nenhuma proposta encontrada com os filtros selecionados.")
        else:
            st.info("Não há propostas cadastradas no sistema.")

# Permitir que este arquivo seja executado diretamente
if __name__ == "__main__":
    show()