import streamlit as st
import logging
# Configurar logging básico
logging.basicConfig(level=logging.INFO)
from utils.finalizar_proposta_v2 import finalizar_proposta_v2
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import uuid
import plotly.graph_objects as go
from utils.database import Fornecedor
from utils.propostas_helper import st_gerar_pdf_cliente, st_gerar_pdf_interno

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
                                # Adicionar logs para debug
                                print(f"DEBUG UI: Excluindo proposta ID: {proposta_id} (tipo: {type(proposta_id)})")
                                st.info(f"Excluindo proposta {proposta_id}...")
                                
                                # Processar exclusão
                                sucesso, mensagem = st.session_state.db.excluir_proposta(proposta_id)
                                print(f"DEBUG UI: Resultado exclusão: sucesso={sucesso}, mensagem={mensagem}")
                                
                                if sucesso:
                                    st.success(f"Proposta {proposta_id} excluída com sucesso!")
                                    # Remover da sessão e recarregar
                                    del st.session_state[alterar_status_key]
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao excluir proposta: {mensagem}")
                                    # Manter o estado para debug (comentar esta linha se necessário)
                                    # del st.session_state[alterar_status_key]
                            
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
                    
                    # Layout com 5 colunas. Aumentando espaço para PDF e Ações
                    col_num, col_info, col_status, col_export, col_excluir = st.columns([1, 3, 2.5, 1.5, 1.5])
                    
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
                            col_num, col_info, col_status, col_export, col_excluir = st.columns([1, 3, 2.5, 1.5, 1.5])
                            
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
                                            st.warning("⚠️ Tem certeza que deseja excluir esta proposta?")
                                            col1_conf, col2_conf = st.columns(2)
                                            
                                            with col1_conf:
                                                if st.button("✓ Sim, excluir", key=confirmar_key):
                                                    # Executar a exclusão diretamente com SQL
                                                    try:
                                                        from sqlalchemy import text
                                                        from utils.database import engine
                                                        
                                                        with engine.connect() as conn:
                                                            # 1. Excluir transações financeiras
                                                            conn.execute(text(f"DELETE FROM financeiro WHERE proposta_id = {proposta_id}"))
                                                            
                                                            # 2. Excluir acréscimos
                                                            conn.execute(text(f"DELETE FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                                                            
                                                            # 3. Excluir produtos da proposta
                                                            conn.execute(text(f"DELETE FROM produtos_organizadores WHERE proposta_id = {proposta_id}"))
                                                            
                                                            # 4. Excluir andamento
                                                            conn.execute(text(f"DELETE FROM andamento_propostas WHERE proposta_id = {proposta_id}"))
                                                            
                                                            # 5. Excluir a proposta
                                                            conn.execute(text(f"DELETE FROM propostas WHERE id = {proposta_id}"))
                                                            
                                                            # Confirmar alterações
                                                            conn.commit()
                                                        
                                                        st.success(f"✅ Proposta #{proposta_id} excluída com sucesso!")
                                                        time.sleep(1.5)
                                                        st.rerun()
                                                    except Exception as e:
                                                        st.error(f"Erro ao excluir proposta: {str(e)}")
                                                        time.sleep(2)
                                            
                                            with col2_conf:
                                                if st.button("✗ Cancelar", key=f"cancel_{confirmar_key}"):
                                                    st.rerun()
                                        else:
                                            st.session_state[f"alterar_status_{proposta_id}"] = novo_status
                                            st.rerun()
                            
                            # Coluna 4: Exportar para PDF
                            with col_export:
                                # CSS específico para botão verde
                                st.markdown("""
                                <style>
                                .green-button button {
                                    background: linear-gradient(135deg, #4CAF50, #45a049) !important;
                                    color: white !important;
                                    border: none !important;
                                    border-radius: 6px !important;
                                    font-weight: 500 !important;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                with st.container():
                                    if st.button("Gerar Proposta", key=f"pdf_{proposta_id}", help="Gerar PDF da proposta"):
                                        try:
                                            # Importar a função de geração de PDF
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
                                                
                                                # Obter nome do cliente para usar no nome do arquivo
                                                cliente_id = proposta['cliente_id']
                                                cliente_df = st.session_state.db.get_cliente_by_id(cliente_id)
                                                cliente_nome = "sem_nome"
                                                if not cliente_df.empty:
                                                    nome_str = str(cliente_df.iloc[0]['nome']) if 'nome' in cliente_df.columns else "sem_nome"
                                                    cliente_nome = nome_str.replace(' ', '_').lower()
                                                
                                                # Mostrar mensagem de sucesso
                                                st.success("PDF gerado com sucesso!")
                                                
                                                # Criar botão de download
                                                st.download_button(
                                                    label="Baixar",
                                                    data=pdf_bytes,
                                                    file_name=f"Proposta_{proposta_id}_{cliente_nome}.pdf",
                                                    mime="application/pdf",
                                                    key=f"download_{proposta_id}"
                                                )
                                            else:
                                                st.error(f"Erro ao gerar PDF: {mensagem}")
                                        except Exception as e:
                                            st.error(f"Erro ao gerar PDF: {str(e)}")
                            
                            # Coluna 5: Botão de exclusão (modo alternativo mais direto)
                            with col_excluir:
                                
                                # Chave exclusiva para cada botão de exclusão
                                excluir_key = f"del_{proposta_id}"
                                confirmar_key = f"confirm_del_direct_{proposta_id}"
                                
                                # CSS específico para botão vermelho
                                st.markdown("""
                                <style>
                                .red-button button {
                                    background: linear-gradient(135deg, #f44336, #d32f2f) !important;
                                    color: white !important;
                                    border: none !important;
                                    border-radius: 6px !important;
                                    font-weight: 500 !important;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                # Usar variáveis de sessão simples para gerenciar estado
                                if excluir_key not in st.session_state:
                                    st.session_state[excluir_key] = False
                                
                                # Botão de exclusão
                                if st.button("🗑️ Excluir", key=f"btn_{excluir_key}", help="Excluir proposta"):
                                    # Alternar estado de confirmação
                                    st.session_state[excluir_key] = True
                                    st.rerun()
                                
                                # Mostrar confirmação se o botão foi clicado
                                if st.session_state.get(excluir_key, False):
                                    st.warning("⚠️ Tem certeza que deseja excluir esta proposta?")
                                    col_confirm1, col_confirm2 = st.columns(2)
                                    
                                    with col_confirm1:
                                        # CSS para botão de confirmação (vermelho)
                                        st.markdown("""
                                        <style>
                                        div[data-testid="column"] button[kind="secondary"] {
                                            width: 100% !important;
                                            font-size: 0.75rem !important;
                                            padding: 0.3rem 0.5rem !important;
                                            background: linear-gradient(135deg, #f44336, #d32f2f) !important;
                                            color: white !important;
                                            border: none !important;
                                            border-radius: 4px !important;
                                            font-weight: 500 !important;
                                            transition: all 0.3s ease !important;
                                        }
                                        div[data-testid="column"] button[kind="secondary"]:hover {
                                            background: linear-gradient(135deg, #d32f2f, #c62828) !important;
                                            transform: translateY(-1px) !important;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
                                        }
                                        </style>
                                        """, unsafe_allow_html=True)
                                        if st.button("✓ Sim, excluir", key=f"sim_{confirmar_key}"):
                                            # Chamar função excluir direto
                                            try:
                                                # Criar conexão SQL Alchemy direta para garantir
                                                from sqlalchemy import text
                                                from utils.database import engine
                                                
                                                with engine.connect() as conn:
                                                    # 1. Excluir transações financeiras
                                                    conn.execute(text(f"DELETE FROM financeiro WHERE proposta_id = {proposta_id}"))
                                                    
                                                    # 2. Excluir acréscimos
                                                    conn.execute(text(f"DELETE FROM acrescimos_proposta WHERE proposta_id = {proposta_id}"))
                                                    
                                                    # 3. Excluir produtos da proposta
                                                    conn.execute(text(f"DELETE FROM produtos_organizadores WHERE proposta_id = {proposta_id}"))
                                                    
                                                    # 4. Excluir andamento
                                                    conn.execute(text(f"DELETE FROM andamento_propostas WHERE proposta_id = {proposta_id}"))
                                                    
                                                    # 5. Excluir a proposta
                                                    conn.execute(text(f"DELETE FROM propostas WHERE id = {proposta_id}"))
                                                    
                                                    # Confirmar alterações
                                                    conn.commit()
                                                
                                                st.success(f"✅ Proposta #{proposta_id} excluída com sucesso!")
                                                # Limpar estado
                                                st.session_state[excluir_key] = False
                                                time.sleep(1.5)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao excluir proposta: {str(e)}")
                                    
                                    with col_confirm2:
                                        # CSS para botão de cancelar (cinza)
                                        st.markdown("""
                                        <style>
                                        div[data-testid="column"] button[kind="secondary"] {
                                            width: 100% !important;
                                            font-size: 0.75rem !important;
                                            padding: 0.3rem 0.5rem !important;
                                            background: linear-gradient(135deg, #757575, #616161) !important;
                                            color: white !important;
                                            border: none !important;
                                            border-radius: 4px !important;
                                            font-weight: 500 !important;
                                            transition: all 0.3s ease !important;
                                        }
                                        div[data-testid="column"] button[kind="secondary"]:hover {
                                            background: linear-gradient(135deg, #616161, #424242) !important;
                                            transform: translateY(-1px) !important;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
                                        }
                                        </style>
                                        """, unsafe_allow_html=True)
                                        if st.button("✗ Cancelar", key=f"cancelar_{confirmar_key}"):
                                            # Limpar estado de sessão
                                            st.session_state[excluir_key] = False
                                            st.rerun()
                                                
                else:
                    st.info("Não há propostas em aberto no momento.")
            else:
                st.info("Não há propostas cadastradas. Crie uma nova proposta na aba ao lado.")

    # ABA 2: EM EXECUÇÃO
    with tab2:
        st.header("Propostas em Execução")
        
        if not propostas.empty:
            # Filtrar apenas propostas em execução - usar status_execucao correto
            propostas_em_execucao = propostas_com_clientes[
                propostas_com_clientes['status_execucao'] == 'Em execução'
            ]
        else:
            propostas_em_execucao = pd.DataFrame()
            
        if not propostas_em_execucao.empty:
            # Mostrar as propostas em execução
            st.write(f"Total: {len(propostas_em_execucao)} propostas em execução")
            
            # Criar seletor de proposta para gerenciar
            def format_proposta(x):
                p = propostas_em_execucao[propostas_em_execucao['id'] == x].iloc[0]
                numero = p.get('numero', 'N/A')
                nome = p.get('nome', 'Sem nome')
                # Usar tanto 'descricao' quanto 'observacao' para compatibilidade
                descricao = p.get('descricao', p.get('observacao', 'Sem descrição'))
                return f"#{numero} - {nome}: {str(descricao)[:50]}..."
            
            proposta_selecionada_id = st.selectbox(
                "Selecione uma proposta para gerenciar:",
                options=propostas_em_execucao['id'].tolist(),
                format_func=format_proposta
            )
            
            if proposta_selecionada_id:
                # Obter os dados da proposta selecionada
                proposta = propostas_em_execucao[propostas_em_execucao['id'] == proposta_selecionada_id].iloc[0]
                
                # Adicionar título da proposta
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
                    "📊 Detalhes", "📦 Produtos", "➕ Outros", "🏭 Fornecedores", "👥 Assistentes", "🏁 Finalizar"
                ])
                st.markdown('</div>', unsafe_allow_html=True)
                
                with exec_tab1:
                    st.subheader("Detalhes")
                    
                    # Formulário para registrar detalhes
                    with st.form(key=f"form_andamento_{proposta_selecionada_id}"):
                        st.write("Registre uma nova atualização de detalhes:")
                        descricao_andamento = st.text_area("Descrição:", height=100)
                        data_andamento = st.date_input("Data:", datetime.now())
                        # Usar o mesmo valor da barra superior como padrão para manter consistência
                        try:
                            slider_value = st.session_state[f"slider_progresso_topo_{proposta_selecionada_id}"]
                        except:
                            slider_value = 0
                        # Ocultar o slider aqui, já que temos um equivalente no topo
                        observacoes = st.text_area("Observações:", height=70)
                        
                        andamento_salvar = st.form_submit_button("Registrar Andamento")
                        
                        if andamento_salvar:
                            # Usar o valor do slider de progresso superior
                            porcentagem = st.session_state.get(f"slider_progresso_topo_{proposta_selecionada_id}", 0)
                            
                            # Lógica para salvar o andamento
                            try:
                                st.session_state.db.add_andamento(
                                    proposta_id=proposta_selecionada_id,
                                    descricao=descricao_andamento,
                                    data=data_andamento,
                                    porcentagem=porcentagem,
                                    observacoes=observacoes
                                )
                                st.success(f"Andamento registrado com sucesso! Progresso: {porcentagem}%")
                                
                                # Recarregar a página para mostrar a atualização
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao registrar andamento: {str(e)}")
                        
                        # EXIBIR ANDAMENTOS REGISTRADOS
                        st.markdown("---")
                        st.subheader("📋 Andamentos Registrados")
                        
                        try:
                            # Buscar andamentos desta proposta usando o novo método
                            andamentos_df_raw = st.session_state.db.get_andamentos(proposta_id=proposta_selecionada_id)
                            
                            # Verificar se há andamentos válidos
                            tem_andamentos = False
                            if andamentos_df_raw is not None and not andamentos_df_raw.empty:
                                tem_andamentos = len(andamentos_df_raw) > 0
                            
                            # Exibir apenas tabela resumida dos andamentos (apenas colunas relevantes)
                            if tem_andamentos:
                                # Verificar se as colunas necessárias existem
                                colunas_necessarias = ['data', 'status', 'observacao']
                                colunas_existentes = [col for col in colunas_necessarias if col in andamentos_df_raw.columns]
                                
                                if len(colunas_existentes) >= 2:  # Pelo menos data e status
                                    # Criar tabela resumida com apenas as colunas importantes
                                    andamentos_resumo = andamentos_df_raw[colunas_existentes].copy()
                                    # Renomear colunas para português
                                    column_mapping = {'data': 'Data', 'status': 'Status', 'observacao': 'Observação'}
                                    andamentos_resumo.columns = [column_mapping.get(col, col) for col in colunas_existentes]
                                    
                                    # Verificar se há dados reais para exibir
                                    if len(andamentos_resumo) > 0:
                                        st.dataframe(andamentos_resumo, hide_index=True, use_container_width=True)
                                else:
                                    # Fallback: mostrar tabela completa se as colunas esperadas não existirem
                                    if len(andamentos_df_raw) > 0:
                                        st.dataframe(andamentos_df_raw, hide_index=True, use_container_width=True)
                            else:
                                # Quando não há andamentos, mostrar uma mensagem discreta e limpa
                                st.caption("💭 Ainda não há registros de andamento para esta proposta.")
                            
                            if False:  # Desabilitando a seção duplicada
                                # Ordenar por data (mais recente primeiro)
                                andamentos_df = andamentos_df.sort_values('data', ascending=False)
                                
                                # Exibir cada andamento em um container estilizado
                                for idx, andamento in andamentos_df.iterrows():
                                    with st.container():
                                        col1, col2, col3 = st.columns([2, 1, 1])
                                        
                                        with col1:
                                            # Tratar tanto 'observacao' quanto 'descricao' para compatibilidade
                                            texto = andamento.get('observacao', andamento.get('descricao', 'Andamento sem descrição'))
                                            
                                            st.markdown(f"**{texto}**")
                                            # Se houver status, mostrar também
                                            status = andamento.get('status', '')
                                            if pd.notna(status) and status:
                                                st.caption(f"📊 Status: {status}")
                                        
                                        with col2:
                                            data_andamento = andamento.get('data')
                                            if pd.notna(data_andamento) and data_andamento:
                                                data_formatada = data_andamento.strftime('%d/%m/%Y')
                                            else:
                                                data_formatada = 'N/A'
                                            st.markdown(f"📅 {data_formatada}")
                                        
                                        with col3:
                                            progresso = andamento.get('porcentagem', 0) if pd.notna(andamento.get('porcentagem')) else 0
                                            st.markdown(f"📊 {progresso}%")
                                    
                                    st.markdown("---")
                                
                        except Exception as e:
                            st.error(f"Erro ao carregar andamentos: {str(e)}")
                            import traceback
                            st.text(traceback.format_exc())
                        
                        # Calcular e mostrar progresso da proposta com tratamento seguro para datas
                        hoje = datetime.now().date()
                        
                        # Obter data de início com valor padrão seguro
                        data_inicio_exec = proposta.get('data_inicio_execucao')
                        if data_inicio_exec is None:
                            data_inicio_exec = proposta.get('data_inicio')
                        # Garantir que temos uma data válida para o início
                        if data_inicio_exec is None:
                            data_inicio_exec = hoje - timedelta(days=1)  # Valor padrão seguro
                            
                        # Obter data de fim com valor padrão seguro  
                        data_fim_prevista = proposta.get('data_fim')
                        if data_fim_prevista is None:
                            # Agora é seguro adicionar timedelta pois data_inicio_exec é garantido
                            data_fim_prevista = data_inicio_exec + timedelta(days=30)
                        
                        # Calcular dias com verificações seguras
                        try:
                            total_dias = (data_fim_prevista - data_inicio_exec).days
                            dias_decorridos = (hoje - data_inicio_exec).days
                            
                            if total_dias > 0:
                                progresso = min(100, max(0, int(dias_decorridos / total_dias * 100)))
                            else:
                                progresso = 0
                        except (TypeError, AttributeError):
                            # Fallback seguro em caso de erro com datas
                            total_dias = 30
                            dias_decorridos = 0
                            progresso = 0
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
                        
                        st.write("Adição à Proposta")
                        # Implementação de produtos
                        with st.form(key=f"form_produto_{proposta_selecionada_id}"):
                            # Obter lista de produtos cadastrados no módulo de vendas
                            produtos_cadastrados = st.session_state.db.get_produtos()
                            
                            if not produtos_cadastrados.empty:
                                # Lista de opções para o selectbox com produto e preço
                                opcoes_produtos = produtos_cadastrados['id'].tolist()
                                
                                # Função para formatar o nome do produto com preço
                                def format_produto_option(produto_id):
                                    produto = produtos_cadastrados.loc[produtos_cadastrados['id'] == produto_id]
                                    if not produto.empty:
                                        nome = produto['nome'].iloc[0]
                                        preco = float(produto['preco_venda'].iloc[0])
                                        return f"{nome} - R$ {preco:.2f}"
                                    return "Produto não encontrado"
                                
                                # Crie o selectbox para selecionar produtos
                                st.write("Selecione o produto:")
                                produto_selecionado_id = st.selectbox(
                                    "Selecione o produto:", 
                                    options=opcoes_produtos,
                                    format_func=format_produto_option,
                                    key=f"select_produto_{proposta_selecionada_id}",
                                    label_visibility="collapsed"
                                )
                                
                                # Obter dados do produto selecionado
                                produto = produtos_cadastrados.loc[produtos_cadastrados['id'] == produto_selecionado_id].iloc[0]
                                
                                # Mostrar descrição e categoria do produto selecionado
                                st.write(f"Descrição: {produto['descricao']}")
                                st.write(f"Categoria: {produto['categoria']}")
                                
                                # Campo de quantidade
                                quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                                
                                # Campo de cômodo/área
                                comodo = st.text_input("Cômodo/Área:")
                                
                                # Checkbox para usar preço padrão
                                usar_preco_padrao = st.checkbox("Usar preço padrão", value=True)
                                
                                # Campo de preço personalizado (habilitado apenas se não usar preço padrão)
                                preco_padrao = float(produto['preco_venda'])
                                
                                if not usar_preco_padrao:
                                    valor_unitario = st.number_input(
                                        "Preço personalizado (R$):", 
                                        min_value=0.0, 
                                        value=preco_padrao, 
                                        format="%.2f"
                                    )
                                else:
                                    valor_unitario = preco_padrao
                                
                                produto_salvar = st.form_submit_button("Adicionar à Proposta")
                                
                                if produto_salvar:
                                    try:
                                        # Calcular valor total para exibição
                                        valor_total = valor_unitario * quantidade
                                        
                                        # Obter os dados do produto selecionado
                                        nome_produto = produto['nome']
                                        descricao_produto = produto['descricao']
                                        
                                        # Definir cômodo padrão se vazio
                                        comodo_final = comodo if comodo else "Geral"
                                        
                                        # Salvar o produto na tabela produtos_organizadores
                                        produto_id = st.session_state.db.add_produto_organizador(
                                            proposta_id=proposta_selecionada_id,
                                            nome=nome_produto,
                                            descricao=descricao_produto,
                                            valor=valor_unitario,
                                            quantidade=quantidade,
                                            comodo=comodo_final
                                        )
                                        
                                        st.success(f"Produto '{nome_produto}' adicionado com sucesso! Valor Total: R$ {valor_total:.2f}")
                                        
                                        # Recarregar a página após adicionar
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao adicionar produto: {str(e)}")
                            else:
                                st.warning("Não há produtos cadastrados no sistema. Adicione produtos no módulo de vendas.")
                        
                        # Exibir tabela de produtos da proposta
                        st.write("Produtos da Proposta:")
                        
                        try:
                            # Obter produtos da proposta do banco de dados
                            produtos_proposta_raw = st.session_state.db.get_produtos_organizadores(proposta_id=proposta_selecionada_id)
                            
                            # Se existem produtos, preparar o DataFrame para exibição
                            if not produtos_proposta_raw.empty:
                                # Renomear colunas para corresponder ao que precisamos exibir
                                produtos_proposta = produtos_proposta_raw.rename(columns={
                                    'valor': 'valor_unit'
                                })
                                
                                # Calcular valor total para cada produto
                                produtos_proposta['valor_total'] = produtos_proposta['valor_unit'] * produtos_proposta['quantidade']
                            else:
                                # Se não houver produtos, criar DataFrame vazio com as colunas necessárias
                                produtos_proposta = pd.DataFrame(columns=[
                                    'id', 'nome', 'descricao', 'valor_unit', 'quantidade', 'valor_total', 'comodo'
                                ])
                            
                            if not produtos_proposta.empty:
                                # Mostrar tabela de produtos
                                st.dataframe(
                                    produtos_proposta[['nome', 'descricao', 'valor_unit', 'quantidade', 'valor_total', 'comodo']],
                                    column_config={
                                        'nome': 'Nome',
                                        'descricao': 'Descrição',
                                        'valor_unit': st.column_config.NumberColumn('Valor Unit.', format="R$ %.2f"),
                                        'quantidade': 'Quantidade',
                                        'valor_total': st.column_config.NumberColumn('Valor Total', format="R$ %.2f"),
                                        'comodo': 'Cômodo'
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Opção para remover produtos
                                with st.form(key=f"form_remover_produto_{proposta_selecionada_id}"):
                                    st.write("Selecione um produto para remover:")
                                    produto_remover_id = st.selectbox(
                                        "Selecione um produto para remover:",
                                        options=produtos_proposta['id'].tolist(),
                                        format_func=lambda x: f"{x} - {produtos_proposta.loc[produtos_proposta['id'] == x, 'nome'].iloc[0]}",
                                        key=f"select_remover_produto_{proposta_selecionada_id}"
                                    )
                                    
                                    remover_produto = st.form_submit_button("Remover")
                                    
                                    if remover_produto:
                                        try:
                                            # Chamar a função para remover o produto do banco de dados
                                            resultado = st.session_state.db.remove_produto_organizador(produto_remover_id)
                                            
                                            if resultado:
                                                st.success(f"Produto removido com sucesso!")
                                            else:
                                                st.error("Falha ao remover o produto. Ele pode não existir mais no banco de dados.")
                                                
                                            # Recarregar a página
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao remover produto: {str(e)}")
                                
                                # Mostrar valor total dos produtos
                                valor_total_produtos = produtos_proposta['valor_total'].sum()
                                st.info(f"Valor Total dos Produtos: R$ {valor_total_produtos:.2f}")
                            else:
                                st.info("Nenhum produto adicionado a esta proposta ainda.")
                        except Exception as e:
                            st.error(f"Erro ao carregar produtos da proposta: {str(e)}")
                    
                    with exec_tab3:
                        st.subheader("Outros")
                        
                        st.write("Adicionar itens adicionais que não estão no catálogo de produtos")
                        
                        # Formulário para adicionar outros itens
                        with st.form(key=f"form_outros_{proposta_selecionada_id}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                nome_item = st.text_input("Nome do Item:")
                                descricao_item = st.text_input("Descrição:")
                                comodo_area = st.text_input("Cômodo/Área:")
                            
                            with col2:
                                valor_unitario = st.number_input("Valor unitário (R$):", min_value=0.0, value=0.0, format="%.2f")
                                quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                                valor_total = valor_unitario * quantidade
                                st.write(f"Valor total: R$ {valor_total:.2f}")
                            
                            item_salvar = st.form_submit_button("Adicionar Item")
                            
                            if item_salvar:
                                if not nome_item or valor_unitario <= 0:
                                    st.error("Preencha o nome do item e um valor válido.")
                                else:
                                    try:
                                        # Adicionar o item como um acréscimo do tipo OUTROS
                                        resultado = st.session_state.db.add_acrescimo_proposta(
                                            proposta_id=proposta_selecionada_id,
                                            tipo="OUTROS",
                                            valor=valor_total,
                                            descricao=f"{nome_item} - {descricao_item}" if descricao_item else nome_item,
                                            fornecedor=comodo_area if comodo_area else "Geral"
                                        )
                                        
                                        if resultado and "acrescimo_id" in resultado:
                                            st.success(f"Item '{nome_item}' adicionado com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("Erro ao adicionar item. Verifique os dados e tente novamente.")
                                    except Exception as e:
                                        st.error(f"Erro ao adicionar item: {str(e)}")
                        
                        # Exibir itens adicionados
                        try:
                            # Obter todos os acréscimos do tipo OUTROS para esta proposta
                            acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_selecionada_id, "OUTROS")
                            
                            if not acrescimos.empty:
                                st.write("### Itens adicionados")
                                
                                # Preparar os dados para exibição em uma tabela
                                df_display = acrescimos.copy()
                                
                                # Extrair o nome do item da descrição (assumindo formato "Nome - Descrição")
                                df_display['nome_item'] = df_display['descricao'].apply(
                                    lambda x: x.split(' - ')[0] if ' - ' in x else x
                                )
                                df_display['descricao_item'] = df_display['descricao'].apply(
                                    lambda x: x.split(' - ')[1] if ' - ' in x else ''
                                )
                                
                                # Renomear colunas para exibição
                                df_display = df_display[['id', 'nome_item', 'descricao_item', 'valor', 'fornecedor']]
                                df_display.columns = ['ID', 'Nome', 'Descrição', 'Valor Total', 'Cômodo/Área']
                                
                                # Formatar valores monetários
                                df_display['Valor Total'] = df_display['Valor Total'].apply(lambda x: f"R$ {float(x):.2f}")
                                
                                # Exibir a tabela
                                st.dataframe(df_display)
                                
                                # Formulário para remover itens
                                with st.form(key=f"form_remover_outros_{proposta_selecionada_id}"):
                                    acrescimo_remover_id = st.selectbox(
                                        "Selecione um item para remover:",
                                        options=acrescimos['id'].tolist(),
                                        format_func=lambda x: acrescimos.loc[acrescimos['id'] == x, 'descricao'].iloc[0]
                                    )
                                    
                                    remover_item = st.form_submit_button("Remover Item")
                                    
                                    if remover_item:
                                        try:
                                            # Chamar a função para remover o acréscimo
                                            resultado = st.session_state.db.remove_acrescimo_proposta(acrescimo_remover_id)
                                            
                                            if resultado:
                                                st.success("Item removido com sucesso!")
                                            else:
                                                st.error("Falha ao remover o item. Ele pode não existir mais no banco de dados.")
                                                
                                            # Recarregar a página
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao remover item: {str(e)}")
                                
                                # Mostrar valor total
                                valor_total_outros = acrescimos['valor'].sum()
                                st.info(f"Valor Total dos Itens Adicionais: R$ {valor_total_outros:.2f}")
                            else:
                                st.info("Nenhum item adicional foi incluído nesta proposta.")
                        except Exception as e:
                            st.error(f"Erro ao carregar itens adicionais: {str(e)}")
                    
                    with exec_tab4:
                        st.subheader("Fornecedores")
                        
                        st.write("Fornecedores envolvidos nesta proposta")
                        # Implementação de fornecedores
                        # Consultar os fornecedores da base
                        try:
                            # Obter todos os fornecedores
                            fornecedores = st.session_state.db.get_fornecedores()
                            
                            # Verificar se temos algum fornecedor
                            if not fornecedores.empty:
                                with st.form(key=f"form_fornecedor_{proposta_selecionada_id}"):
                                    # Ordenar fornecedores por categoria e nome
                                    fornecedores_ordenados = fornecedores.sort_values(by=['categoria', 'nome'])
                                    
                                    fornecedor_selecionado = st.selectbox(
                                        "Selecione o fornecedor:", 
                                        options=fornecedores_ordenados['id'].tolist(),
                                        format_func=lambda x: f"{fornecedores_ordenados.loc[fornecedores_ordenados['id'] == x, 'nome'].iloc[0]} ({fornecedores_ordenados.loc[fornecedores_ordenados['id'] == x, 'categoria'].iloc[0]})"
                                    )
                                    
                                    # Obter o percentual de comissão do fornecedor selecionado
                                    fornecedor_percentual = fornecedores_ordenados.loc[fornecedores_ordenados['id'] == fornecedor_selecionado, 'percentual_comissao'].iloc[0]
                                    fornecedor_percentual = float(fornecedor_percentual) if fornecedor_percentual is not None else 0.0
                                    
                                    # Campo para o valor do fornecimento
                                    valor_fornecimento = st.number_input("Valor do fornecimento (R$):", min_value=0.0, value=0.0, format="%.2f")
                                    
                                    # Calcular comissão
                                    valor_comissao = valor_fornecimento * (fornecedor_percentual / 100) if valor_fornecimento > 0 else 0
                                    
                                    # Exibir informações sobre percentual e comissão
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.info(f"Percentual de comissão configurado para este fornecedor: {fornecedor_percentual:.2f}%")
                                    with col2:
                                        st.info(f"Comissão: R$ {valor_comissao:.2f}")
                                    
                                    # Mensagem sobre o percentual
                                    st.caption("O percentual de comissão é definido no cadastro do fornecedor")
                                    
                                    # Campo para observações
                                    observacoes = st.text_area("Observações:", height=100)
                                    
                                    fornecedor_salvar = st.form_submit_button("Adicionar Fornecedor")
                                    
                                    if fornecedor_salvar:
                                        if valor_fornecimento <= 0:
                                            st.error("O valor do fornecimento deve ser maior que zero.")
                                        else:
                                            try:
                                                # Adicionar fornecedor à proposta
                                                resultado = st.session_state.db.add_fornecedor_proposta(
                                                    proposta_id=proposta_selecionada_id,
                                                    fornecedor_id=fornecedor_selecionado,
                                                    valor=valor_fornecimento,
                                                    observacoes=observacoes
                                                )
                                                
                                                if resultado and "acrescimo_id" in resultado:
                                                    st.success("Fornecedor adicionado à proposta com sucesso!")
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao adicionar fornecedor. Verifique os dados e tente novamente.")
                                            except Exception as e:
                                                st.error(f"Erro ao adicionar fornecedor: {str(e)}")
                                
                                # Exibir fornecedores já adicionados
                                try:
                                    # Obter todos os acréscimos do tipo FORNECEDOR para esta proposta
                                    acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_selecionada_id, "FORNECEDOR")
                                    
                                    if not acrescimos.empty:
                                        st.write("### Fornecedores adicionados")
                                        
                                        # Preparar os dados para exibição em uma tabela
                                        df_display = acrescimos.copy()
                                        
                                        # Renomear colunas para exibição
                                        df_display = df_display[['id', 'fornecedor', 'descricao', 'valor']]
                                        df_display.columns = ['ID', 'Fornecedor', 'Observações', 'Valor']
                                        
                                        # Formatar valores monetários
                                        df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                        
                                        # Exibir a tabela
                                        st.dataframe(df_display)
                                        
                                        # Calcular e mostrar valor total
                                        valor_total_fornecedores = acrescimos['valor'].sum()
                                        st.info(f"Valor Total dos Fornecedores: R$ {valor_total_fornecedores:.2f}")
                                        
                                        # Formulário para remover fornecedores
                                        with st.form(key=f"form_remover_fornecedor_{proposta_selecionada_id}"):
                                            acrescimo_remover_id = st.selectbox(
                                                "Selecione um fornecedor para remover:",
                                                options=acrescimos['id'].tolist(),
                                                format_func=lambda x: f"{acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]}"
                                            )
                                            
                                            remover_fornecedor = st.form_submit_button("Remover Fornecedor")
                                            
                                            if remover_fornecedor:
                                                try:
                                                    # Chamar a função para remover o acréscimo
                                                    resultado = st.session_state.db.remove_acrescimo_proposta(acrescimo_remover_id)
                                                    
                                                    if resultado:
                                                        st.success("Fornecedor removido com sucesso!")
                                                    else:
                                                        st.error("Falha ao remover o fornecedor. Ele pode não existir mais no banco de dados.")
                                                        
                                                    # Recarregar a página
                                                    time.sleep(1)
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro ao remover fornecedor: {str(e)}")
                                        
                                        # Já mostramos o valor total acima, remover esta duplicidade
                                    else:
                                        st.info("Nenhum fornecedor adicionado a esta proposta ainda.")
                                except Exception as e:
                                    st.error(f"Erro ao carregar fornecedores da proposta: {str(e)}")
                            else:
                                st.info("Não há fornecedores cadastrados. Adicione fornecedores no menu Cadastros > Fornecedores.")
                        except Exception as e:
                            st.error(f"Erro ao carregar fornecedores: {str(e)}")
                    
                    with exec_tab5:
                        st.subheader("Assistentes")
                        
                        # Implementação de assistentes
                        try:
                            assistentes = st.session_state.db.get_assistentes()
                            
                            if not assistentes.empty:
                                # Formulário para adicionar assistente
                                with st.form(key=f"form_assistente_{proposta_selecionada_id}"):
                                    # Campo para selecionar assistente
                                    assistente_selecionado = st.selectbox(
                                        "Selecione o assistente:", 
                                        options=assistentes['id'].tolist(),
                                        format_func=lambda x: assistentes.loc[assistentes['id'] == x, 'nome'].iloc[0]
                                    )
                                    
                                    # Campo para valor do serviço
                                    valor_servico = st.number_input("Valor do serviço (R$):", min_value=0.0, value=0.0, format="%.2f")
                                    
                                    # Campo para observações
                                    observacoes = st.text_area("Observações:", height=100)
                                    
                                    # Botão para adicionar assistente
                                    assistente_salvar = st.form_submit_button("Adicionar Assistente")
                                    
                                    # Processar o envio do formulário
                                    if assistente_salvar:
                                        if valor_servico <= 0:
                                            st.error("O valor do serviço deve ser maior que zero.")
                                        else:
                                            try:
                                                # Adicionar assistente à proposta
                                                resultado = st.session_state.db.add_assistente_proposta(
                                                    proposta_id=proposta_selecionada_id,
                                                    assistente_id=assistente_selecionado,
                                                    valor=valor_servico,
                                                    observacoes=observacoes
                                                )
                                                
                                                if resultado and "acrescimo_id" in resultado:
                                                    st.success("Assistente adicionado à proposta com sucesso!")
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("Erro ao adicionar assistente. Verifique os dados e tente novamente.")
                                            except Exception as e:
                                                st.error(f"Erro ao adicionar assistente: {str(e)}")
                                
                                # Exibir assistentes já adicionados
                                try:
                                    # Obter todos os acréscimos do tipo ASSISTENTE para esta proposta
                                    acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_selecionada_id, "ASSISTENTE")
                                    
                                    if not acrescimos.empty:
                                        st.write("### Assistentes Adicionados")
                                        
                                        # Preparar os dados para exibição em uma tabela
                                        df_display = acrescimos.copy()
                                        
                                        # Renomear colunas para exibição
                                        df_display = df_display[['id', 'fornecedor', 'descricao', 'valor']]
                                        df_display.columns = ['ID', 'Assistente', 'Descrição', 'Valor']
                                        
                                        # Formatar valores monetários
                                        df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                        
                                        # Exibir a tabela
                                        st.dataframe(df_display[['Assistente', 'Descrição', 'Valor']], hide_index=True)
                                        
                                        # Calcular e mostrar valor total
                                        valor_total_assistentes = acrescimos['valor'].sum()
                                        st.info(f"Valor Total dos Assistentes: R$ {valor_total_assistentes:.2f}")
                                        
                                        # Formulário para remover assistente
                                        with st.form(key=f"form_remover_assistente_{proposta_selecionada_id}"):
                                            st.write("Selecione um assistente para remover:")
                                            
                                            # Usar ID para identificação única
                                            acrescimo_remover_id = st.selectbox(
                                                "Selecione um assistente:",
                                                options=acrescimos['id'].tolist(),
                                                format_func=lambda x: f"{acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]}"
                                            )
                                            
                                            remover_assistente = st.form_submit_button("Remover")
                                            
                                            if remover_assistente:
                                                try:
                                                    # Chamar a função para remover o acréscimo
                                                    resultado = st.session_state.db.remove_acrescimo_proposta(acrescimo_remover_id)
                                                    
                                                    if resultado:
                                                        st.success("Assistente removido com sucesso!")
                                                    else:
                                                        st.error("Falha ao remover o assistente. Ele pode não existir mais no banco de dados.")
                                                        
                                                    # Recarregar a página
                                                    time.sleep(1)
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro ao remover assistente: {str(e)}")
                                    else:
                                        st.info("Nenhum assistente adicionado a esta proposta ainda.")
                                except Exception as e:
                                    st.error(f"Erro ao carregar assistentes da proposta: {str(e)}")
                            else:
                                st.info("Não há assistentes cadastrados. Adicione assistentes no menu Cadastros > Assistentes.")
                        except Exception as e:
                            st.error(f"Erro ao carregar assistentes: {str(e)}")
                    
                    with exec_tab6:
                        st.subheader("Finalizar Proposta")
                        
                        # Obter dados para apresentação
                        try:
                            # Dados básicos da proposta
                            valor_base = float(proposta['valor']) if proposta['valor'] else 0
                            data_inicio = proposta['data_inicio'] if 'data_inicio' in proposta else None
                            data_aprovacao = proposta['data_aprovacao'] if 'data_aprovacao' in proposta else None
                            
                            # Obter produtos
                            produtos_df = st.session_state.db.get_produtos_organizadores(proposta_selecionada_id)
                            
                            # Obter fornecedores
                            fornecedores_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_selecionada_id, "FORNECEDOR")
                            
                            # Obter assistentes
                            assistentes_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_selecionada_id, "ASSISTENTE")
                            
                            # Obter outros itens
                            outros_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_selecionada_id, "OUTROS")
                            
                            # Calcular valores totais
                            total_produtos = produtos_df['valor'].sum() * produtos_df['quantidade'].sum() if not produtos_df.empty else 0
                            total_fornecedores = fornecedores_df['valor'].sum() if not fornecedores_df.empty else 0
                            total_assistentes = assistentes_df['valor'].sum() if not assistentes_df.empty else 0
                            total_outros = outros_df['valor'].sum() if not outros_df.empty else 0
                            
                            # Valor final
                            total_geral = valor_base + total_produtos + total_fornecedores + total_assistentes + total_outros
                            
                            # SEÇÃO 1: DADOS BÁSICOS
                            st.write("### Dados Básicos")
                            
                            # Criar tabela de dados básicos
                            dados_basicos = {
                                "Item": ["Número", "Cliente", "Descrição", "Data de Início", "Data de Aprovação", "Valor Base", "Status"],
                                "Valor": [
                                    proposta['numero'],
                                    proposta['nome'],
                                    proposta['descricao'],
                                    data_inicio.strftime('%d/%m/%Y') if data_inicio else '-',
                                    data_aprovacao.strftime('%d/%m/%Y') if data_aprovacao else '-',
                                    f"R$ {valor_base:.2f}",
                                    proposta['status_execucao'] if 'status_execucao' in proposta else proposta['status']
                                ]
                            }
                            
                            # Exibir tabela de dados básicos
                            st.dataframe(pd.DataFrame(dados_basicos), hide_index=True, use_container_width=True)
                            
                            # SEÇÃO 2: PRODUTOS
                            st.write("### Produtos")
                            
                            if not produtos_df.empty:
                                # Preparar DataFrame para exibição
                                produtos_display = produtos_df.copy()
                                produtos_display['Valor Total'] = produtos_display['valor'] * produtos_display['quantidade']
                                
                                # Renomear colunas para exibição
                                produtos_display = produtos_display[['id', 'nome', 'valor', 'quantidade', 'Valor Total', 'comodo']]
                                produtos_display.columns = ['ID', 'Nome', 'Valor Unit.', 'Quantidade', 'Valor Total', 'Cômodo']
                                
                                # Formatar valores monetários
                                produtos_display['Valor Unit.'] = produtos_display['Valor Unit.'].apply(lambda x: f"R$ {float(x):.2f}")
                                produtos_display['Valor Total'] = produtos_display['Valor Total'].apply(lambda x: f"R$ {float(x):.2f}")
                                
                                # Exibir a tabela sem a coluna ID
                                st.dataframe(produtos_display[['Nome', 'Valor Unit.', 'Quantidade', 'Valor Total', 'Cômodo']], hide_index=True, use_container_width=True)
                                
                                # Exibir total
                                st.info(f"Total Produtos: R$ {total_produtos:.2f}")
                            else:
                                st.info("Nenhum produto adicionado a esta proposta.")
                            
                            # SEÇÃO 3: FORNECEDORES
                            st.write("### Fornecedores")
                            
                            if not fornecedores_df.empty:
                                # Preparar DataFrame para exibição
                                fornecedores_display = fornecedores_df.copy()
                                
                                # Renomear colunas para exibição
                                fornecedores_display = fornecedores_display[['id', 'fornecedor', 'descricao', 'valor']]
                                fornecedores_display.columns = ['ID', 'Fornecedor', 'Descrição', 'Valor']
                                
                                # Formatar valores monetários
                                fornecedores_display['Valor'] = fornecedores_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                
                                # Exibir a tabela sem a coluna ID
                                st.dataframe(fornecedores_display[['Fornecedor', 'Descrição', 'Valor']], hide_index=True, use_container_width=True)
                                
                                # Exibir total
                                st.info(f"Total Fornecedores: R$ {total_fornecedores:.2f}")
                            else:
                                st.info("Nenhum fornecedor adicionado a esta proposta.")
                            
                            # SEÇÃO 4: ASSISTENTES
                            st.write("### Assistentes")
                            
                            if not assistentes_df.empty:
                                # Preparar DataFrame para exibição
                                assistentes_display = assistentes_df.copy()
                                
                                # Renomear colunas para exibição
                                assistentes_display = assistentes_display[['id', 'fornecedor', 'descricao', 'valor']]
                                assistentes_display.columns = ['ID', 'Assistente', 'Descrição', 'Valor']
                                
                                # Formatar valores monetários
                                assistentes_display['Valor'] = assistentes_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                
                                # Exibir a tabela sem a coluna ID
                                st.dataframe(assistentes_display[['Assistente', 'Descrição', 'Valor']], hide_index=True, use_container_width=True)
                                
                                # Exibir total
                                st.info(f"Total Assistentes: R$ {total_assistentes:.2f}")
                            else:
                                st.info("Nenhum assistente adicionado a esta proposta.")
                            
                            # SEÇÃO 5: OUTROS ITENS
                            st.write("### Outros Itens")
                            
                            if not outros_df.empty:
                                # Preparar DataFrame para exibição
                                outros_display = outros_df.copy()
                                
                                # Renomear colunas para exibição
                                outros_display = outros_display[['id', 'fornecedor', 'descricao', 'valor']]
                                outros_display.columns = ['ID', 'Item', 'Descrição', 'Valor']
                                
                                # Formatar valores monetários
                                outros_display['Valor'] = outros_display['Valor'].apply(lambda x: f"R$ {float(x):.2f}")
                                
                                # Exibir a tabela sem a coluna ID
                                st.dataframe(outros_display[['Item', 'Descrição', 'Valor']], hide_index=True, use_container_width=True)
                                
                                # Exibir total
                                st.info(f"Total Outros Itens: R$ {total_outros:.2f}")
                            else:
                                st.info("Nenhum item adicional adicionado a esta proposta.")
                            
                            # SEÇÃO 6: RESUMO FINANCEIRO
                            st.write("### Resumo Financeiro")
                            
                            resumo_financeiro = {
                                "Item": ["Valor Personal Organizer", "Produtos", "Fornecedores", "Assistentes", "Outros", "Total Geral"],
                                "Valor": [
                                    f"R$ {valor_base:.2f}",
                                    f"R$ {total_produtos:.2f}",
                                    f"R$ {total_fornecedores:.2f}",
                                    f"R$ {total_assistentes:.2f}",
                                    f"R$ {total_outros:.2f}",
                                    f"R$ {total_geral:.2f}"
                                ]
                            }
                            
                            st.dataframe(pd.DataFrame(resumo_financeiro), hide_index=True, use_container_width=True)
                            
                            # SEÇÃO 7: DISTRIBUIÇÃO DE VALORES (GRÁFICO DE PIZZA)
                            st.write("### Distribuição de Valores")
                            
                            # Preparar dados para o gráfico
                            labels = ['Valor Personal Organizer', 'Fornecedores', 'Assistentes (Custos)', 'Produtos']
                            values = [valor_base, total_fornecedores, total_assistentes, total_produtos]
                            
                            # Criar o gráfico de pizza
                            fig = go.Figure(data=[go.Pie(
                                labels=labels,
                                values=values,
                                hole=.3,  # Criar gráfico tipo donut
                                textinfo='label+value'
                            )])
                            
                            fig.update_layout(
                                title_text="Distribuição de Valores da Proposta",
                                legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                            )
                            
                            # Exibir o gráfico
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # SEÇÃO 8: BOTÃO PARA FINALIZAR
                            st.warning("⚠️ **Atenção**: Finalizar uma proposta não poderá ser desfeito facilmente.")
                            
                            with st.form(key=f"form_finalizar_concluida_{proposta_selecionada_id}"):
                                finalizar_concluida = st.form_submit_button("Marcar como Concluída", use_container_width=True)
                                if finalizar_concluida:
                                    try:
                                        # Chamar a função para finalizar proposta (versão V2)
                                        # Garantir que o ID seja convertido para inteiro
                                        proposta_id_int = int(proposta_selecionada_id)
                                        print(f"===== CHAMANDO FINALIZAR PROPOSTA COM ID={proposta_id_int} =====")
                                        resultado = finalizar_proposta_v2(proposta_id_int)
                                        if resultado.get('status', False):
                                            st.success("✅ Proposta finalizada com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Erro ao finalizar proposta: {resultado.get('message', 'Erro desconhecido')}")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao finalizar proposta: {str(e)}")
                        
                        except Exception as e:
                            st.error(f"Erro ao carregar dados para finalização: {str(e)}")
            else:
                st.info("Não há propostas em execução no momento.")
    
    # ABA 3: PROPOSTAS FINALIZADAS
    with tab3:
        st.header("Propostas Finalizadas")
        
        if 'propostas_com_clientes' in locals() and not propostas.empty:
            # Filtro específico para mostrar apenas propostas finalizadas
            propostas_finalizadas = propostas_com_clientes[
                ((propostas_com_clientes['status'] == 'Finalizada') & 
                 (propostas_com_clientes['status_execucao'] == 'Finalizada')) |
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
                
                # Adicionar funcionalidade para gerar relatórios de propostas finalizadas
                
                with st.expander("Gerar Relatórios"):
                    # Obter lista de números de propostas finalizadas para o select box
                    numeros_propostas = propostas_filtradas['numero'].tolist()
                    numeros_propostas.sort()  # Ordenar para facilitar a seleção
                    
                    proposta_numero = st.selectbox(
                        "Selecione o número da proposta para gerar relatório:",
                        numeros_propostas,
                        key="numero_proposta_relatorio"
                    )
                    
                    proposta_relatorio = propostas_filtradas[propostas_filtradas['numero'] == proposta_numero]
                    
                    if not proposta_relatorio.empty:
                        st.info(f"Proposta selecionada: #{proposta_numero} - {proposta_relatorio.iloc[0]['descricao']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Relatório Cliente", key="gerar_relatorio_cliente"):
                                try:
                                    proposta_id = propostas_filtradas[propostas_filtradas['numero'] == proposta_numero].iloc[0]['id']
                                    st_gerar_pdf_cliente(proposta_id)
                                except Exception as e:
                                    st.error(f"Erro ao gerar relatório para cliente: {str(e)}")
                        
                        with col2:
                            if st.button("Relatório Interno", key="gerar_relatorio_interno"):
                                try:
                                    proposta_id = propostas_filtradas[propostas_filtradas['numero'] == proposta_numero].iloc[0]['id']
                                    st_gerar_pdf_interno(proposta_id)
                                except Exception as e:
                                    st.error(f"Erro ao gerar relatório interno: {str(e)}")
                
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