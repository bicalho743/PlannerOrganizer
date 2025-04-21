"""
Página de login simplificada com recuperação de senha
Implementação minimalista sem dependências JS complexas
"""
import streamlit as st
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered"
)

# Inicializar variáveis de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "mode" not in st.session_state:
    st.session_state.mode = "login"  # login, reset, signup

# Estilo CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2557D6;
        margin-bottom: 1rem;
    }
    
    .login-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .info-text {
        color: #666;
        font-size: 0.9rem;
        margin-top: 1rem;
    }
    
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<h1 class='main-title'>Planner Organizer</h1>", unsafe_allow_html=True)

# Função para mostrar login
def mostrar_login():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    
    # Campos de login
    email = st.text_input("Email", key="login_email", 
                         help="Digite seu email cadastrado")
    senha = st.text_input("Senha", type="password", key="login_password", 
                         help="Digite sua senha")
    
    # Botões de login
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar", key="login_button", use_container_width=True):
            with st.spinner("Verificando credenciais..."):
                # Simulação de login (substitua pelo Firebase)
                if email == "demo@example.com" and senha == "senha123":
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        "email": email,
                        "login_time": datetime.now().isoformat()
                    }
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Tente novamente.")
    
    with col2:
        if st.button("Modo Demo", key="demo_button", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user = {
                "email": "demo@example.com",
                "name": "Usuário Demo",
                "demo": True,
                "login_time": datetime.now().isoformat()
            }
            st.rerun()
    
    # Links para outras opções
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Criar Conta", key="go_to_signup"):
            st.session_state.mode = "signup"
            st.rerun()
    
    with col2:
        if st.button("Esqueci a Senha", key="go_to_reset"):
            st.session_state.mode = "reset"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Função para mostrar criar conta
def mostrar_criar_conta():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.subheader("Criar Nova Conta")
    
    # Campos de registro
    email = st.text_input("Email", key="signup_email",
                         help="Digite um email válido")
    senha = st.text_input("Senha", type="password", key="signup_password",
                         help="Mínimo 6 caracteres")
    confirmar_senha = st.text_input("Confirmar Senha", type="password", 
                                   key="signup_confirm_password")
    
    # Botão de criação de conta
    if st.button("Criar Conta", key="signup_button", use_container_width=True):
        with st.spinner("Criando conta..."):
            # Verificações básicas
            if not email or not senha:
                st.error("Email e senha são obrigatórios")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres")
            else:
                # Simulação de criação de conta (substitua pelo Firebase)
                st.success("Conta criada com sucesso! Um email de verificação foi enviado para " + email)
                st.info("Por favor, verifique seu email e confirme sua conta antes de fazer login.")
                
                # Voltar para login após 3 segundos
                import time
                time.sleep(3)
                st.session_state.mode = "login"
                st.rerun()
    
    # Botão para voltar ao login
    if st.button("Voltar ao Login", key="back_to_login_from_signup"):
        st.session_state.mode = "login"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Função para mostrar recuperação de senha
def mostrar_recuperar_senha():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.subheader("Recuperação de Senha")
    
    # Campo de email
    email = st.text_input("Email", key="reset_email",
                         help="Digite o email cadastrado para receber o link de recuperação")
    
    # Botão de recuperação
    if st.button("Enviar Email de Recuperação", key="reset_button", use_container_width=True):
        with st.spinner("Enviando email de recuperação..."):
            # Simulação de envio de email (substitua pelo Firebase)
            st.success("Um email de recuperação foi enviado para " + email + " se esta conta existir.")
            st.info("Por favor, verifique sua caixa de entrada e siga as instruções no email.")
            
            # Voltar para login após 3 segundos
            import time
            time.sleep(3)
            st.session_state.mode = "login"
            st.rerun()
    
    # Botão para voltar ao login
    if st.button("Voltar ao Login", key="back_to_login_from_reset"):
        st.session_state.mode = "login"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Função para mostrar área logada
def mostrar_area_logada():
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}")
    
    # Informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        # Acesso ao sistema
        if st.button("Acessar o Sistema", key="access_button", use_container_width=True):
            st.info("Redirecionando para o sistema principal...")
            # Simulação de redirecionamento (substitua pelo código real)
    
    with col2:
        # Botão para sair
        if st.button("Sair", key="logout_button", use_container_width=True):
            # Limpar dados da sessão
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

# Mostrar a interface apropriada
if st.session_state.authenticated:
    mostrar_area_logada()
else:
    if st.session_state.mode == "login":
        mostrar_login()
    elif st.session_state.mode == "signup":
        mostrar_criar_conta()
    elif st.session_state.mode == "reset":
        mostrar_recuperar_senha()

# Informação de uso
st.markdown("""
<div class="footer">
    <p>Esta é uma demonstração do sistema de login com recuperação de senha.</p>
    <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)