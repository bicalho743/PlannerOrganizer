import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta

# Importação para gerenciar assinaturas
from utils.assinatura_db import registrar_assinatura, obter_assinatura_usuario
from utils.brevo_helper import obter_listas_brevo, exportar_contatos_para_brevo

def show():
    if not st.session_state.autenticado or st.session_state.usuario.tipo != 'admin':
        st.error("Acesso negado. Esta página é restrita para administradores.")
        return

    # Criar abas para diferentes seções de administração
    tab1, tab2, tab3 = st.tabs(["Gerenciar Usuários", "Gerenciar Assinaturas", "Capturas de Email"])
    
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
            
    with tab3:
        st.title("📧 Gerenciar Capturas de Email")
        
        # Define o caminho para o arquivo de capturas
        arquivo_capturas = os.path.join("data", "captured_emails.json")
        
        # Função para carregar os e-mails capturados
        def carregar_emails_capturados():
            """Carrega os e-mails capturados do arquivo local"""
            if not os.path.exists(arquivo_capturas):
                return []
            
            try:
                with open(arquivo_capturas, 'r') as f:
                    dados = json.load(f)
                return dados
            except Exception as e:
                st.error(f"Erro ao carregar e-mails capturados: {e}")
                return []
        
        # Função para salvar chave API
        def salvar_chave_api(chave):
            """Salva a chave API do Brevo nas variáveis de ambiente"""
            os.environ["BREVO_API_KEY"] = chave
            
            # Também salva em um arquivo para persistência entre sessões
            config_dir = os.path.join("data", "config")
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, "brevo_config.json")
            with open(config_file, 'w') as f:
                json.dump({"api_key": chave}, f)
            
            return True
        
        # Criando sub-abas para organizar a interface
        subtab1, subtab2, subtab3 = st.tabs(["Configuração API", "Visualizar Capturas", "Exportar para Brevo"])
        
        # Aba 1: Configuração da API
        with subtab1:
            st.subheader("Configuração da API Brevo")
            
            # Verifica se já existe uma chave salva
            chave_atual = os.environ.get("BREVO_API_KEY", "")
            tem_chave = bool(chave_atual)
            
            # Exibe status atual
            if tem_chave:
                st.success("✅ API Brevo configurada")
                chave_mascarada = chave_atual[:4] + "*" * (len(chave_atual) - 8) + chave_atual[-4:] if len(chave_atual) > 8 else "****"
                st.info(f"Chave atual: {chave_mascarada}")
            else:
                st.warning("⚠️ API Brevo não configurada")
            
            # Campo para inserir nova chave
            nova_chave = st.text_input("Chave da API Brevo", 
                                    value="", 
                                    type="password",
                                    help="Insira a chave da API do Brevo para integração direta")
            
            # Botão para salvar a chave
            if st.button("Salvar chave da API", key="salvar_chave_brevo", use_container_width=True):
                if not nova_chave:
                    st.error("Por favor, insira uma chave da API.")
                else:
                    sucesso = salvar_chave_api(nova_chave)
                    if sucesso:
                        st.success("✅ Chave da API salva com sucesso!")
                        st.rerun()  # Atualiza a página para refletir a nova configuração
            
            # Instruções para obter a chave
            with st.expander("Como obter sua chave de API Brevo"):
                st.markdown("""
                ### Passos para obter uma chave de API do Brevo:
                
                1. Acesse sua conta no [Brevo](https://app.brevo.com/)
                2. Vá para **Configurações** > **Integração**
                3. Clique em **API Keys**
                4. Gere uma nova chave de API ou use uma existente
                5. Copie a chave e cole no campo acima
                
                A chave de API permite que o sistema envie os e-mails capturados diretamente para sua lista de contatos no Brevo.
                """)
        
        # Aba 2: Visualizar e-mails capturados
        with subtab2:
            st.subheader("E-mails Capturados Localmente")
            
            # Carregar os e-mails capturados
            emails_capturados = carregar_emails_capturados()
            
            # Exibir contagem
            st.info(f"Total de e-mails capturados: {len(emails_capturados)}")
            
            # Verificar se há e-mails para exibir
            if not emails_capturados:
                st.warning("Nenhum e-mail capturado encontrado.")
            else:
                # Criar DataFrame para exibição mais amigável
                df = pd.DataFrame(emails_capturados)
                
                # Formatar as datas para exibição
                if 'captured_at' in df.columns:
                    df['data_captura'] = pd.to_datetime(df['captured_at']).dt.strftime('%d/%m/%Y %H:%M')
                
                # Ordenar por data de captura (mais recente primeiro)
                if 'captured_at' in df.columns:
                    df = df.sort_values('captured_at', ascending=False)
                
                # Selecionar colunas relevantes para exibição
                colunas_exibir = ['email', 'first_name', 'last_name', 'data_captura', 'source']
                colunas_exibir = [col for col in colunas_exibir if col in df.columns]
                
                # Renomear colunas para português
                mapeamento_colunas = {
                    'email': 'Email',
                    'first_name': 'Nome',
                    'last_name': 'Sobrenome',
                    'data_captura': 'Data de Captura',
                    'source': 'Origem'
                }
                
                # Aplicar renomeação nas colunas disponíveis
                rename_dict = {col: mapeamento_colunas.get(col, col) for col in colunas_exibir}
                df_exibir = df[colunas_exibir].rename(columns=rename_dict)
                
                # Exibir a tabela com possibilidade de filtro
                st.dataframe(df_exibir, use_container_width=True)
                
                # Opção para exportar como CSV
                csv = df_exibir.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Baixar como CSV",
                    data=csv,
                    file_name=f"emails_capturados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
        
        # Aba 3: Exportar para Brevo
        with subtab3:
            st.subheader("Exportar Contatos para Brevo")
            
            # Verificar se a API está configurada
            tem_api = bool(os.environ.get("BREVO_API_KEY", ""))
            
            if not tem_api:
                st.error("⚠️ Você precisa configurar a API do Brevo na aba Configuração antes de exportar contatos.")
            else:
                # Carregar os e-mails capturados
                emails_capturados = carregar_emails_capturados()
                
                if not emails_capturados:
                    st.warning("Não há e-mails capturados para exportar.")
                else:
                    st.info(f"Existem {len(emails_capturados)} e-mails capturados que podem ser exportados para o Brevo.")
                    
                    # Obter listas disponíveis no Brevo
                    listas = obter_listas_brevo()
                    
                    if not listas:
                        st.warning("Não foi possível obter as listas do Brevo. Verifique sua chave de API.")
                    else:
                        # Criar opções de seleção para as listas
                        lista_opcoes = [{"label": f"{lista['name']} (ID: {lista['id']})", "value": lista['id']} for lista in listas]
                        lista_opcoes.insert(0, {"label": "Nenhuma (apenas adicionar contatos)", "value": None})
                        
                        # Permitir seleção da lista
                        lista_selecionada = st.selectbox(
                            "Selecione a lista para adicionar os contatos:",
                            options=[opcao["value"] for opcao in lista_opcoes],
                            format_func=lambda x: next((opcao["label"] for opcao in lista_opcoes if opcao["value"] == x), str(x))
                        )
                        
                        # Botão para exportar
                        if st.button("Exportar contatos para Brevo", key="exportar_brevo", use_container_width=True):
                            with st.spinner("Exportando contatos..."):
                                resultado = exportar_contatos_para_brevo()
                                
                                if resultado["success"]:
                                    st.success(resultado["message"])
                                    
                                    # Se foi bem sucedido, oferecer recarregar a página
                                    if st.button("Atualizar página", key="atualizar_apos_exportacao", use_container_width=True):
                                        st.rerun()
                                else:
                                    st.error(resultado["message"])
