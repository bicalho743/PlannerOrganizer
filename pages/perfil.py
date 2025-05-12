import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

def carregar_perfil(user_id):
    """
    Carrega os dados do perfil do usuário a partir do arquivo JSON
    
    Args:
        user_id: ID ou email do usuário
        
    Returns:
        dict: Dados do perfil ou dicionário vazio se não existir
    """
    # Normalizar o ID do usuário para uso em nome de arquivo
    user_id_normalizado = user_id.replace('@', '_at_').replace('.', '_dot_')
    
    # Caminho do arquivo de perfil
    perfil_path = f"data/perfis/{user_id_normalizado}.json"
    
    # Verificar se o arquivo existe
    if os.path.exists(perfil_path):
        try:
            with open(perfil_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar perfil: {str(e)}")
            return {}
    else:
        return {}

def salvar_perfil(user_id, dados_perfil):
    """
    Salva os dados do perfil do usuário em um arquivo JSON
    
    Args:
        user_id: ID ou email do usuário
        dados_perfil: Dicionário com os dados do perfil
        
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    # Normalizar o ID do usuário para uso em nome de arquivo
    user_id_normalizado = user_id.replace('@', '_at_').replace('.', '_dot_')
    
    # Garantir que o diretório existe
    os.makedirs("data/perfis", exist_ok=True)
    
    # Caminho do arquivo de perfil
    perfil_path = f"data/perfis/{user_id_normalizado}.json"
    
    # Adicionar timestamp de atualização
    dados_perfil['ultima_atualizacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    try:
        with open(perfil_path, 'w', encoding='utf-8') as f:
            json.dump(dados_perfil, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar perfil: {str(e)}")
        return False

def show():
    """
    Exibe a página de perfil do usuário
    """
    st.title("Perfil do Usuário")
    
    # Verificar se o usuário está logado
    print(f"Verificando estado da autenticação no perfil: {st.session_state.keys()}")
    if "authenticated" in st.session_state:
        print(f"Estado de autenticação: {st.session_state.authenticated}")
    
    if "usuario" in st.session_state:
        print(f"Dados do usuário na sessão: {st.session_state.usuario}")
    else:
        print("Dados do usuário na sessão: Não encontrado")
        
    if "user" in st.session_state:
        print(f"Objeto 'user' na sessão: {type(st.session_state.user)}")
    
    # Verificar se o usuário está autenticado
    if "authenticated" in st.session_state and st.session_state.authenticated:
        # Se apenas o objeto 'user' existe mas não 'usuario'
        if "user" in st.session_state and "usuario" not in st.session_state:
            # Criar objeto 'usuario' com dados mínimos
            if isinstance(st.session_state.user, dict) and 'email' in st.session_state.user:
                email = st.session_state.user.get('email')
                st.session_state.usuario = {
                    'email': email,
                    'nome': email.split('@')[0].title(),
                    'role': 'user'
                }
                print(f"Criado objeto 'usuario' a partir de 'user': {st.session_state.usuario}")
    
    # Verificação principal
    if "usuario" not in st.session_state or not st.session_state.usuario:
        st.warning("Você precisa estar logado para acessar seu perfil.")
        # Verificar login admin como fallback
        if "authenticated" in st.session_state and st.session_state.authenticated:
            st.info("Você está autenticado, mas seus dados de usuário não estão disponíveis. Tente fazer login novamente.")
        return
    
    # Obter dados do usuário atual
    usuario = st.session_state.usuario
    user_id = usuario.get('email', 'usuario_desconhecido')
    
    # Carregar perfil existente
    perfil = carregar_perfil(user_id)
    
    # Exibir formulário de perfil
    with st.form("form_perfil", clear_on_submit=False):
        st.subheader("Dados Pessoais")
        
        # Seção de dados pessoais
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo", 
                                value=perfil.get('nome', usuario.get('nome', '')))
            
            telefone = st.text_input("Telefone", 
                                    value=perfil.get('telefone', usuario.get('telefone', '')),
                                    help="Formato: (XX) XXXXX-XXXX")
        
        with col2:
            email = st.text_input("Email", 
                                value=perfil.get('email', usuario.get('email', '')), 
                                disabled=True,
                                help="O email não pode ser alterado pois é usado para autenticação")
            
            instagram = st.text_input("Instagram", 
                                    value=perfil.get('instagram', ''),
                                    help="Seu perfil do Instagram (sem @)")
        
        st.subheader("Dados Profissionais")
        
        # Seção de dados da empresa
        col1, col2 = st.columns(2)
        
        with col1:
            empresa = st.text_input("Nome da Empresa/Negócio", 
                                   value=perfil.get('empresa', usuario.get('empresa', '')))
            
            website = st.text_input("Website", 
                                   value=perfil.get('website', 'www.plannerorganizer.com.br'),
                                   help="Seu site ou landing page")
        
        with col2:
            cargo = st.text_input("Cargo/Função", 
                                 value=perfil.get('cargo', 'Personal Organizer'))
            
            cnpj = st.text_input("CNPJ (se houver)", 
                                value=perfil.get('cnpj', ''),
                                help="Formato: XX.XXX.XXX/XXXX-XX")
        
        # Endereço
        st.subheader("Endereço Profissional")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            endereco = st.text_input("Endereço", 
                                    value=perfil.get('endereco', ''))
        
        with col2:
            numero = st.text_input("Número", 
                                 value=perfil.get('numero', ''))
        
        with col3:
            complemento = st.text_input("Complemento", 
                                      value=perfil.get('complemento', ''))
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            bairro = st.text_input("Bairro", 
                                  value=perfil.get('bairro', ''))
        
        with col2:
            cidade = st.text_input("Cidade", 
                                  value=perfil.get('cidade', ''))
        
        with col3:
            estado = st.text_input("Estado", 
                                  value=perfil.get('estado', ''),
                                  max_chars=2)
            
        cep = st.text_input("CEP", 
                          value=perfil.get('cep', ''),
                          help="Formato: XXXXX-XXX")
        
        # Informações adicionais para relatórios
        st.subheader("Personalização de Relatórios")
        
        mensagem_padrao = st.text_area(
            "Mensagem de Agradecimento (para incluir nos relatórios)", 
            value=perfil.get('mensagem_padrao', 'Agradecemos a confiança em nossos serviços.'),
            help="Esta mensagem aparecerá nos relatórios enviados para clientes"
        )
        
        botao_salvar = st.form_submit_button("💾 Salvar Perfil")
        
        if botao_salvar:
            # Preparar dados para salvar
            dados_perfil = {
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'instagram': instagram,
                'empresa': empresa,
                'website': website,
                'cargo': cargo,
                'cnpj': cnpj,
                'endereco': endereco,
                'numero': numero,
                'complemento': complemento,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'cep': cep,
                'mensagem_padrao': mensagem_padrao
            }
            
            # Salvar perfil
            if salvar_perfil(user_id, dados_perfil):
                st.success("✅ Perfil salvo com sucesso!")
                
                # Atualizar dados do usuário na sessão 
                # (apenas os campos relevantes para outras partes do sistema)
                if 'usuario' in st.session_state:
                    st.session_state.usuario['nome'] = nome
                    st.session_state.usuario['telefone'] = telefone
                    st.session_state.usuario['empresa'] = empresa
                
                # Atualizar também o objeto 'user'
                if 'user' in st.session_state:
                    if isinstance(st.session_state.user, dict):
                        st.session_state.user['nome'] = nome
                        st.session_state.user['telefone'] = telefone
                        st.session_state.user['empresa'] = empresa
            else:
                st.error("❌ Erro ao salvar perfil. Tente novamente.")
    
    # Exibir informações de última atualização
    if 'ultima_atualizacao' in perfil:
        st.info(f"📅 Última atualização: {perfil['ultima_atualizacao']}")
    
    # Seção de faturamento e assinatura
    st.subheader("💳 Faturamento e Assinatura")
    
    # Link para o portal do cliente Stripe
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #026937;">
        <h4 style="margin-top: 0; color: #026937;">Portal do Cliente Stripe</h4>
        <p>Gerencie sua assinatura, atualize seus dados de pagamento e visualize suas faturas.</p>
        <a href="https://dashboard.stripe.com/billing/portal" target="_blank">
            <button style="background-color: #026937; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Acessar Portal do Cliente
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Exibir dicas de uso
    with st.expander("📘 Sobre o Perfil", expanded=False):
        st.markdown("""
        ### Por que preencher seu perfil?
        
        As informações do seu perfil serão utilizadas nos relatórios e documentos gerados pelo sistema, como:
        
        - **Propostas para clientes**: Seu nome e contatos aparecerão como dados do profissional
        - **Relatórios financeiros**: O nome da empresa será utilizado nos cabeçalhos
        - **Documentos PDF**: Todas as informações de contato aparecerão no rodapé dos documentos
        
        Mantenha seus dados sempre atualizados para uma experiência profissional completa!
        """)

if __name__ == "__main__":
    show()