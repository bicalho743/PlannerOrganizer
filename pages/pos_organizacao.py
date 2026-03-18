"""
Módulo de Pós-Organização
Gerencia ações de acompanhamento pós-serviço para propostas finalizadas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def formatar_data_br(data):
    """Formata data para padrão brasileiro DD/MM/YYYY"""
    try:
        if pd.isna(data):
            return "N/A"
        if isinstance(data, str):
            return data
        return pd.to_datetime(data).strftime('%d/%m/%Y')
    except:
        return str(data) if data else "N/A"


def traduzir_tipo_acao(action_type):
    """Traduz o tipo de ação para português amigável"""
    traducoes = {
        'AGRADECIMENTO': '🙏 Agradecimento',
        'MANUTENCAO': '🔧 Manutenção',
        'FOLLOW_UP': '📞 Follow-up',
        'FEEDBACK': '⭐ Feedback',
        'OPORTUNIDADE': '💡 Oportunidade',
        'RETORNO_TECNICO': '🔄 Retorno Técnico'
    }
    return traducoes.get(action_type, action_type)


def traduzir_status(status):
    """Traduz o status para português com emoji"""
    traducoes = {
        'PENDENTE': '⏳ Pendente',
        'FEITO': '✅ Feito',
        'CANCELADO': '❌ Cancelado',
        'ATIVO': '🟢 Ativo',
        'CONCLUIDO': '✔️ Concluído'
    }
    return traducoes.get(status, status)


def show():
    """Função principal do módulo Pós-Organização"""
    
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return
    
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">📋 Pós-Organização</h1>', unsafe_allow_html=True)
    
    # Tabs para Lista e Detalhes
    tab_lista, tab_detalhes = st.tabs(["📑 Lista de Acompanhamentos", "🔍 Detalhes"])
    
    # ===== TAB 1: Lista de Acompanhamentos =====
    with tab_lista:
        st.subheader("Acompanhamentos Pós-Serviço")
        
        # Filtro de status
        col_filtro, col_refresh = st.columns([3, 1])
        with col_filtro:
            filtro_status = st.selectbox(
                "Filtrar por status:",
                options=["Todos", "ATIVO", "CONCLUIDO"],
                index=0,
                key="filtro_status_pos"
            )
        with col_refresh:
            st.write("")  # Espaçamento
            if st.button("🔄 Atualizar", key="btn_refresh_pos"):
                st.rerun()
        
        # Buscar dados
        status_filter = None if filtro_status == "Todos" else filtro_status
        df_pos_orgs = st.session_state.db.get_post_organizations(status_filter=status_filter)
        
        if df_pos_orgs.empty:
            st.info("Nenhum acompanhamento de pós-organização encontrado.")
            st.markdown("""
            **Como funciona:**
            - Quando uma proposta é marcada como **Finalizada**, o sistema cria automaticamente um registro de pós-organização.
            - São criadas ações automáticas de acompanhamento (agradecimento, manutenção, follow-up, etc.)
            - Você pode gerenciar essas ações aqui.
            """)
        else:
            # Exibir tabela de pós-organizações
            for idx, row in df_pos_orgs.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**Cliente:** {row['cliente_nome']}")
                        st.markdown(f"**Proposta:** #{row['proposta_numero']}")
                    
                    with col2:
                        st.markdown(f"**Status:** {traduzir_status(row['status'])}")
                        if row['proxima_acao']:
                            data_acao = formatar_data_br(row['proxima_acao_data'])
                            st.markdown(f"**Próxima ação:** {traduzir_tipo_acao(row['proxima_acao'])} ({data_acao})")
                        else:
                            st.markdown("**Próxima ação:** Todas concluídas")
                    
                    with col3:
                        if st.button("Ver Detalhes", key=f"btn_detalhes_{row['id']}", use_container_width=True):
                            st.session_state.pos_org_selecionada_id = row['id']
                            st.session_state.pos_org_cliente_nome = row['cliente_nome']
                            st.session_state.pos_org_proposta_numero = row['proposta_numero']
                    
                    st.divider()
    
    # ===== TAB 2: Detalhes =====
    with tab_detalhes:
        # Verificar se há uma pós-organização selecionada
        if 'pos_org_selecionada_id' not in st.session_state or st.session_state.pos_org_selecionada_id is None:
            st.info("Selecione um acompanhamento na aba 'Lista de Acompanhamentos' para ver os detalhes.")
            
            # Permitir seleção direta
            df_pos_orgs = st.session_state.db.get_post_organizations()
            if not df_pos_orgs.empty:
                opcoes = ["-- Selecione --"] + [
                    f"{row['cliente_nome']} - Proposta #{row['proposta_numero']}" 
                    for _, row in df_pos_orgs.iterrows()
                ]
                selecao = st.selectbox("Ou selecione aqui:", options=opcoes, key="sel_pos_org_direto")
                
                if selecao != "-- Selecione --":
                    idx = opcoes.index(selecao) - 1
                    row = df_pos_orgs.iloc[idx]
                    st.session_state.pos_org_selecionada_id = row['id']
                    st.session_state.pos_org_cliente_nome = row['cliente_nome']
                    st.session_state.pos_org_proposta_numero = row['proposta_numero']
                    st.rerun()
        else:
            # Exibir detalhes da pós-organização selecionada
            pos_org_id = st.session_state.pos_org_selecionada_id
            cliente_nome = st.session_state.get('pos_org_cliente_nome', 'N/A')
            proposta_numero = st.session_state.get('pos_org_proposta_numero', 'N/A')
            
            st.subheader(f"Ações de {cliente_nome} - Proposta #{proposta_numero}")
            
            # Botão para voltar
            if st.button("⬅️ Voltar para Lista", key="btn_voltar_lista"):
                st.session_state.pos_org_selecionada_id = None
                st.rerun()
            
            st.divider()
            
            # Buscar ações
            df_acoes = st.session_state.db.get_post_organization_actions(pos_org_id)
            
            if df_acoes.empty:
                st.warning("Nenhuma ação encontrada para este acompanhamento.")
            else:
                # Exibir cada ação
                for idx, acao in df_acoes.iterrows():
                    with st.container():
                        col_check, col_info, col_obs = st.columns([1, 2, 2])
                        
                        with col_check:
                            # Checkbox para marcar como FEITO
                            is_feito = acao['status'] == 'FEITO'
                            novo_status = st.checkbox(
                                "Feito",
                                value=is_feito,
                                key=f"check_acao_{acao['id']}",
                                disabled=acao['status'] == 'CANCELADO'
                            )
                        
                        with col_info:
                            st.markdown(f"**{traduzir_tipo_acao(acao['action_type'])}**")
                            st.markdown(f"📅 Data prevista: {formatar_data_br(acao['due_date'])}")
                            st.markdown(f"Status: {traduzir_status(acao['status'])}")
                        
                        with col_obs:
                            # Campo de observação
                            obs_atual = acao['notes'] if acao['notes'] else ""
                            nova_obs = st.text_input(
                                "Observação",
                                value=obs_atual,
                                key=f"obs_acao_{acao['id']}",
                                label_visibility="collapsed",
                                placeholder="Adicione uma observação..."
                            )
                        
                        # Atualizar ação se houve mudança
                        if novo_status != is_feito or nova_obs != obs_atual:
                            new_status = 'FEITO' if novo_status else 'PENDENTE'
                            result = st.session_state.db.update_post_organization_action(
                                action_id=acao['id'],
                                status=new_status,
                                notes=nova_obs if nova_obs else None
                            )
                            
                            if result:
                                # Verificar se é FOLLOW_UP sendo marcado como FEITO
                                if acao['action_type'] == 'FOLLOW_UP' and new_status == 'FEITO':
                                    st.session_state.show_retorno_tecnico_modal = True
                                    st.session_state.retorno_tecnico_pos_org_id = pos_org_id
                                
                                st.rerun()
                        
                        st.divider()
                
                # Modal para Retorno Técnico
                if st.session_state.get('show_retorno_tecnico_modal', False):
                    st.subheader("🔄 Retorno Técnico Necessário?")
                    st.info("O Follow-up foi marcado como concluído. Há necessidade de ajuste ou retorno técnico?")
                    
                    col_sim, col_nao = st.columns(2)
                    
                    with col_sim:
                        if st.button("✅ Sim, agendar retorno", key="btn_sim_retorno", use_container_width=True):
                            st.session_state.agendar_retorno = True
                    
                    with col_nao:
                        if st.button("❌ Não, não precisa", key="btn_nao_retorno", use_container_width=True):
                            st.session_state.show_retorno_tecnico_modal = False
                            st.rerun()
                    
                    # Formulário para agendar retorno
                    if st.session_state.get('agendar_retorno', False):
                        st.markdown("---")
                        st.subheader("Agendar Retorno Técnico")
                        
                        # Data do retorno (entre 15 e 30 dias)
                        data_min = datetime.now().date() + timedelta(days=15)
                        data_max = datetime.now().date() + timedelta(days=30)
                        
                        data_retorno = st.date_input(
                            "Data do retorno técnico",
                            value=data_min,
                            min_value=data_min,
                            max_value=data_max,
                            format="DD/MM/YYYY",
                            key="data_retorno_tecnico"
                        )
                        
                        if st.button("💾 Confirmar Agendamento", key="btn_confirmar_retorno", type="primary"):
                            pos_org_id = st.session_state.retorno_tecnico_pos_org_id
                            result = st.session_state.db.add_retorno_tecnico_action(
                                post_organization_id=pos_org_id,
                                due_date=data_retorno
                            )
                            
                            if result:
                                st.success(f"✅ Retorno técnico agendado para {formatar_data_br(data_retorno)}")
                                st.session_state.show_retorno_tecnico_modal = False
                                st.session_state.agendar_retorno = False
                                st.rerun()
                            else:
                                st.error("Erro ao agendar retorno técnico.")
