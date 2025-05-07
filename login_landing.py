import streamlit as st
import logging
import os
from datetime import datetime, timedelta
import utils.firebase_auth as firebase_auth

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_termos():
    """Mostra a página de termos de uso"""
    st.markdown("""
    # Termos de Uso
    
    ## 1. Aceite dos Termos
    
    Ao acessar este aplicativo, você concorda em cumprir estes Termos de Serviço, todas as leis e regulamentos aplicáveis e concorda que é responsável pelo cumprimento de todas as leis locais aplicáveis.
    
    ## 2. Licença de Uso
    
    É concedida permissão para uso temporário deste aplicativo para uso pessoal e comercial, não para redistribuição ou revenda. Esta é a concessão de uma licença, não uma transferência de título.
    
    ## 3. Uso Adequado
    
    Você concorda em utilizar o aplicativo apenas para fins legítimos e de maneira que não infrinja os direitos de terceiros, não restrinja ou iniba o uso e aproveitamento do aplicativo por qualquer terceiro.
    
    ## 4. Limitação de Responsabilidade
    
    Em nenhum caso a empresa será responsável por quaisquer danos decorrentes do uso deste aplicativo.
    
    ## 5. Alterações dos Termos
    
    Reservamo-nos o direito, a nosso critério, de alterar ou modificar estes termos a qualquer momento. Se uma revisão for material, tentaremos fornecer um aviso com pelo menos 30 dias de antecedência.
    """)

def show_politica():
    """Mostra a página de política de privacidade"""
    st.markdown("""
    # Política de Privacidade
    
    ## 1. Coleta de Dados
    
    Coletamos informações que você nos fornece diretamente, como nome, e-mail, dados de propostas, clientes, e outras informações que você decide compartilhar.
    
    ## 2. Uso de Dados
    
    Utilizamos suas informações para fornecer, manter e melhorar nossos serviços, bem como para entender como você usa nosso aplicativo.
    
    ## 3. Compartilhamento de Dados
    
    Não compartilhamos suas informações pessoais com terceiros, exceto em circunstâncias específicas, como quando exigido por lei ou com seu consentimento.
    
    ## 4. Segurança
    
    Implementamos medidas de segurança apropriadas para proteger contra acesso não autorizado, alteração, divulgação ou destruição de seus dados pessoais.
    
    ## 5. Seus Direitos
    
    Você tem o direito de acessar, corrigir ou excluir seus dados pessoais. Para exercer esses direitos, entre em contato conosco através das informações fornecidas.
    """)

def show_login_section():
    """Exibe o formulário de login"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Acesse sua conta")
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_password")
        
        col_login, col_button = st.columns([2, 1])
        with col_login:
            if st.button("Entrar", type="primary", use_container_width=True):
                # Tentativa de login
                if email and senha:
                    with st.spinner("Autenticando..."):
                        try:
                            resultado = firebase_auth.login_with_email_password(email, senha)
                            if resultado["autenticado"]:
                                st.success("Login realizado com sucesso!")
                                st.session_state["usuario"] = resultado["usuario"]
                                st.session_state["autenticado"] = True
                                st.session_state["token"] = resultado["token"]
                                st.rerun()
                            else:
                                st.error(f"Falha na autenticação: {resultado['mensagem']}")
                        except Exception as e:
                            st.error(f"Erro no login: {str(e)}")
                else:
                    st.warning("Por favor, preencha email e senha.")

        # Links para redefinir senha ou criar nova conta
        st.markdown("---")
        col_reset, col_signup = st.columns(2)
        with col_reset:
            if st.button("Esqueci minha senha", type="secondary", use_container_width=True):
                if email:
                    try:
                        firebase_auth.reset_password(email)
                        st.success(f"Email para redefinição de senha enviado para {email}")
                    except Exception as e:
                        st.error(f"Erro ao solicitar redefinição de senha: {str(e)}")
                else:
                    st.warning("Digite seu email antes de solicitar redefinição de senha.")
        
        with col_signup:
            if st.button("Criar nova conta", type="secondary", use_container_width=True):
                st.session_state["mostrar_cadastro"] = True
                st.rerun()
    
    with col2:
        # Seção de destaque para os planos
        st.markdown("### Planos disponíveis")
        st.markdown("**Plano Mensal** - R$ 9,70/mês")
        st.markdown("**Plano Anual** - R$ 97,00/ano")
        st.markdown("**Acesso Vitalício** - R$ 247,00")
        
        if st.button("Ver detalhes dos planos", use_container_width=True):
            # Redirecionar para a página de planos
            st.markdown("""
            <script>
                window.location.href = "/planos";
            </script>
            """, unsafe_allow_html=True)

def show_signup_section():
    """Exibe o formulário de cadastro"""
    st.markdown("### Crie sua conta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome completo", key="signup_nome")
        email = st.text_input("Email", key="signup_email")
    
    with col2:
        senha = st.text_input("Senha", type="password", help="Mínimo 6 caracteres", key="signup_senha")
        confirmar_senha = st.text_input("Confirmar senha", type="password", key="signup_confirmar")
    
    col_terms, col_signup, col_back = st.columns([2, 1, 1])
    
    with col_terms:
        aceite_termos = st.checkbox("Aceito os [Termos de Uso](/termos) e a [Política de Privacidade](/politica)")
    
    with col_signup:
        signup_button = st.button("Cadastrar", type="primary", use_container_width=True)
        if signup_button:
            if not nome or not email or not senha or not confirmar_senha:
                st.error("Todos os campos são obrigatórios.")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            elif not aceite_termos:
                st.error("Você precisa aceitar os termos de uso e política de privacidade.")
            else:
                # Tentativa de cadastro
                with st.spinner("Cadastrando..."):
                    try:
                        resultado = firebase_auth.register_with_email_password(email, senha, nome)
                        if resultado["registrado"]:
                            st.success("Cadastro realizado com sucesso! Você pode fazer login agora.")
                            st.session_state["mostrar_cadastro"] = False
                            st.rerun()
                        else:
                            st.error(f"Falha no cadastro: {resultado['mensagem']}")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {str(e)}")
    
    with col_back:
        if st.button("Voltar", use_container_width=True):
            st.session_state["mostrar_cadastro"] = False
            st.rerun()

def main():
    # Configurações iniciais da página
    st.set_page_config(
        page_title="Planner Organiza | Login",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializar variáveis de sessão se não existirem
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None
        
    if "mostrar_cadastro" not in st.session_state:
        st.session_state["mostrar_cadastro"] = False
        
    if "token" not in st.session_state:
        st.session_state["token"] = None
    
    # CSS para a página
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .logo-text {
        color: #1E366F;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .tagline {
        color: #666;
        font-size: 1.2rem;
        margin-top: 0;
    }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 2rem;
    }
    .header-links {
        display: flex;
        gap: 1.5rem;
    }
    .header-link {
        color: #1E366F;
        text-decoration: none;
        font-weight: 500;
    }
    .header-link:hover {
        text-decoration: underline;
    }
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #666;
        font-size: 0.9rem;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }
    .main-content {
        padding: 2rem 0;
    }
    .cta-button {
        background-color: #1E366F;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        font-weight: 600;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho
    st.markdown("""
    <div class="header">
        <div>
            <h1 class="logo-text">Planner Organiza</h1>
            <p class="tagline">Gerencie seus projetos com eficiência</p>
        </div>
        <div class="header-links">
            <a href="/" class="header-link">Início</a>
            <a href="/planos" class="header-link">Planos</a>
            <a href="/sobre" class="header-link">Sobre</a>
            <a href="/contato" class="header-link">Contato</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar qual página mostrar
    query_params = st.query_params
    
    if "termos" in query_params:
        show_termos()
    elif "politica" in query_params:
        show_politica()
    elif st.session_state["autenticado"]:
        # O usuário está logado, redirecionar para o dashboard
        st.markdown(f"## Bem-vindo(a), {st.session_state['usuario']['displayName']}!")
        
        if st.button("Acessar o sistema", type="primary"):
            # Redirecionar para o dashboard
            st.markdown("""
            <script>
                window.location.href = "/dashboard";
            </script>
            """, unsafe_allow_html=True)
            
        if st.button("Sair"):
            # Fazer logout
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = None
            st.session_state["token"] = None
            st.rerun()
    else:
        # Página inicial com hero section
        cols = st.columns([2, 1])
        
        with cols[0]:
            st.markdown("""
            # Simplifique a gestão dos seus projetos
            
            Organize propostas, clientes e finanças de forma integrada e eficiente. 
            Com o Planner Organiza você terá:
            
            * ✅ **Controle de Propostas** - Acompanhe todo o ciclo de vida de suas propostas
            * ✅ **Gestão de Clientes** - Mantenha todos os dados de seus clientes organizados
            * ✅ **Controle Financeiro** - Tenha uma visão clara da parte financeira do seu negócio
            * ✅ **Relatórios Personalizados** - Gere relatórios profissionais para seus clientes
            """)
            
            col_login, col_planos = st.columns(2)
            with col_login:
                if st.button("Faça Login", type="primary", use_container_width=True):
                    st.session_state["mostrar_login"] = True
                    st.rerun()
            
            with col_planos:
                if st.button("Ver planos disponíveis", use_container_width=True):
                    st.markdown("""
                    <script>
                        window.location.href = "/planos";
                    </script>
                    """, unsafe_allow_html=True)
                    
                    # Alternativa caso o JavaScript não funcione
                    st.success("Redirecionando para a página de planos...")
        
        with cols[1]:
            # Imagem ilustrativa
            st.image("app-icon.svg", width=300)
        
        # Mostrar formulário de login/cadastro se necessário
        if st.session_state.get("mostrar_cadastro", False):
            show_signup_section()
        elif st.session_state.get("mostrar_login", False):
            show_login_section()
    
    # Rodapé
    st.markdown("""
    <div class="footer">
        <p>&copy; 2025 Planner Organiza. Todos os direitos reservados.</p>
        <p>
            <a href="?termos=1">Termos de Uso</a> | 
            <a href="?politica=1">Política de Privacidade</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()