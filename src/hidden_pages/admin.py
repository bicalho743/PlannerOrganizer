import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Importação para gerenciar assinaturas
from utils.assinatura_db import registrar_assinatura, obter_assinatura_usuario

def show():
    if not st.session_state.autenticado or st.session_state.usuario.tipo != 'admin':
        st.error("Acesso negado. Esta página é restrita para administradores.")
        return

    # Criar abas para diferentes seções de administração
    tab1, tab2 = st.tabs(["Gerenciar Usuários", "Gerenciar Assinaturas"])
    
    with tab1:
        st.title("👤 Administração de Usuários")
        
        # Carregar lista de usuários
        usuarios = st.session_state.db.get_usuarios()
        
        if not usuarios.empty:
            # Converter tipos de dados
            usuarios['data_cadastro'] = pd.to_datetime(usuarios['data_cadastro'])
            
            # Exibir estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Usuários", len(usuarios))
            with col2:
                usuarios_ativos = len(usuarios[usuarios['ativo']])
                st.metric("Usuários Ativos", usuarios_ativos)
            with col3:
                usuarios_inativos = len(usuarios[~usuarios['ativo']])
                st.metric("Usuários Inativos", usuarios_inativos)
            
            # Tabela de usuários com ações
            st.subheader("Gerenciar Usuários")
            
            for idx, usuario in usuarios.iterrows():
                with st.expander(f"📧 {usuario['email']} - {usuario['nome']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Nome:** {usuario['nome']}")
                        st.write(f"**Email:** {usuario['email']}")
                        st.write(f"**Empresa:** {usuario['empresa'] or 'Não informada'}")
                        st.write(f"**Data de Cadastro:** {usuario['data_cadastro'].strftime('%d/%m/%Y')}")
                    
                    with col2:
                        # Alterar status (ativo/inativo)
                        novo_status = st.toggle(
                            "Usuário Ativo",
                            value=usuario['ativo'],
                            key=f"status_{usuario['id']}"
                        )
                        
                        if novo_status != usuario['ativo']:
                            sucesso = st.session_state.db.atualizar_status_usuario(
                                usuario['id'],
                                novo_status
                            )
                            if sucesso:
                                st.success(f"Status atualizado para {'ativo' if novo_status else 'inativo'}")
                                st.rerun()
                        
                        # Alterar tipo de usuário
                        novo_tipo = st.selectbox(
                            "Tipo de Usuário",
                            options=['usuario', 'admin'],
                            index=0 if usuario['tipo'] == 'usuario' else 1,
                            key=f"tipo_{usuario['id']}"
                        )
                        
                        if novo_tipo != usuario['tipo']:
                            sucesso = st.session_state.db.atualizar_tipo_usuario(
                                usuario['id'],
                                novo_tipo
                            )
                            if sucesso:
                                st.success(f"Tipo de usuário atualizado para {novo_tipo}")
                                st.rerun()
        else:
            st.info("Nenhum usuário cadastrado ainda.")

    with tab2:
        st.title("💳 Administração de Assinaturas")
        
        # Área para criar ou modificar assinaturas manualmente
        st.header("Criar/Modificar Assinatura")
        
        # Seleção de usuário
        usuarios = st.session_state.db.get_usuarios()
        
        if not usuarios.empty:
            # Preparar lista de usuários para o dropdown
            opcoes_usuarios = [(row['id'], f"{row['nome']} ({row['email']})") for _, row in usuarios.iterrows()]
            opcoes_dict = {f"{id}": nome for id, nome in opcoes_usuarios}
            
            # Dropdown para selecionar usuário
            usuario_selecionado = st.selectbox(
                "Selecionar Usuário",
                options=list(opcoes_dict.keys()),
                format_func=lambda x: opcoes_dict[x]
            )
            
            if usuario_selecionado:
                # Obter email e id do usuário selecionado
                usuario_row = usuarios[usuarios['id'] == int(usuario_selecionado)].iloc[0]
                usuario_id = usuario_row['usuario_id']
                email_usuario = usuario_row['email']
                
                # Verificar se o usuário já tem assinatura
                resultado_assinatura = obter_assinatura_usuario(usuario_id)
                
                # Mostrar status atual da assinatura
                if resultado_assinatura.get('sucesso'):
                    assinatura = resultado_assinatura.get('assinatura', {})
                    st.success(f"Usuário já possui assinatura: {assinatura.get('plano')} ({assinatura.get('status')})")
                    
                    # Adicionar opção para modificar
                    st.subheader("Modificar Assinatura")
                else:
                    st.info("Usuário não possui assinatura ativa.")
                    st.subheader("Criar Nova Assinatura")
                
                # Formulário para criar/atualizar assinatura
                with st.form("form_assinatura"):
                    # Selecionar tipo de plano (dropdown)
                    plano = st.selectbox(
                        "Plano",
                        options=["Mensal", "Anual", "Vitalicio"],
                        index=0
                    )
                    
                    # Status da assinatura
                    status = st.selectbox(
                        "Status",
                        options=["ativo", "cancelado", "expirado", "pendente"],
                        index=0
                    )
                    
                    # Campos de data
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        data_inicio = st.date_input("Data de Início", value=datetime.now())
                    
                    with col2:
                        # Data fim será calculada automaticamente, mas também pode ser definida manualmente
                        data_fim_auto = None
                        
                        if plano == "Mensal":
                            data_fim_auto = data_inicio + timedelta(days=30)
                        elif plano == "Anual":
                            data_fim_auto = data_inicio + timedelta(days=365)
                        
                        # Para plano vitalício, não há data de fim
                        data_fim_disabled = plano == "Vitalicio"
                        
                        if data_fim_auto and not data_fim_disabled:
                            data_fim = st.date_input("Data de Término", value=data_fim_auto, disabled=data_fim_disabled)
                        else:
                            data_fim = st.date_input("Data de Término", disabled=data_fim_disabled)
                    
                    # IDs opcionais do Stripe
                    st.subheader("Dados do Stripe (opcional)")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        customer_id = st.text_input("Customer ID", placeholder="cus_...")
                    
                    with col2:
                        subscription_id = st.text_input("Subscription ID", placeholder="sub_...")
                    
                    # Botão de submissão
                    botao_salvar = st.form_submit_button("Salvar Assinatura")
                    
                    if botao_salvar:
                        # Preparar datas
                        data_inicio_dt = datetime.combine(data_inicio, datetime.min.time())
                        data_fim_dt = None
                        
                        if not data_fim_disabled and data_fim:
                            data_fim_dt = datetime.combine(data_fim, datetime.min.time())
                        
                        # Criar/atualizar assinatura
                        resultado = registrar_assinatura(
                            usuario_id=usuario_id,
                            plano=plano,
                            customer_id=customer_id if customer_id else None,
                            subscription_id=subscription_id if subscription_id else None,
                            status=status,
                            data_inicio=data_inicio_dt,
                            data_fim=data_fim_dt
                        )
                        
                        if resultado.get('sucesso'):
                            st.success(resultado.get('mensagem'))
                            st.rerun()
                        else:
                            st.error(resultado.get('mensagem'))
        else:
            st.info("Nenhum usuário cadastrado para gerenciar assinaturas.")
