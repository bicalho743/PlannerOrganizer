import streamlit as st
import os
import json
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Título principal
st.title("Login - Planner Organizer")

# Configuração do Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", st.secrets.get("FIREBASE_API_KEY", "")),
    "authDomain": "planner-organizer-68a23.firebaseapp.com",
    "projectId": "planner-organizer-68a23",
    "storageBucket": "planner-organizer-68a23.appspot.com", 
    "messagingSenderId": "763383033284",
    "appId": "1:763383033284:web:5a5dc3b4d3f5bc63631ce7"
}

# Se não estiver autenticado, mostrar tela de login
if not st.session_state.authenticated:
    # Adicionar CSS para melhorar a aparência
    st.markdown("""
    <style>
        .login-box {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .login-button {
            background-color: #4285F4;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
            margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Adicionar script Firebase
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Inicializar Firebase
    st.markdown(f"""
    <script>
    // Inicializar Firebase
    if (typeof firebase === 'undefined') {{
        console.error("Firebase não está disponível");
    }} else {{
        // Configuração
        const firebaseConfig = {json.dumps(firebase_config)};
        
        // Inicializar
        if (firebase.apps.length === 0) {{
            firebase.initializeApp(firebaseConfig);
            console.log("Firebase inicializado com sucesso");
        }} else {{
            console.log("Firebase já inicializado");
        }}
        
        // Auth
        const auth = firebase.auth();
        
        // Recuperação de senha
        window.resetPassword = function(email) {{
            console.log("Enviando email de recuperação para:", email);
            
            // Configuração para o email de recuperação
            const actionCodeSettings = {{
                // URL de redirecionamento após recuperação
                url: window.location.origin + window.location.pathname,
                // Manipular código como código de recuperação de senha
                handleCodeInApp: false
            }};
            
            console.log("ActionCodeSettings:", actionCodeSettings);
            
            // Enviar email de recuperação
            auth.sendPasswordResetEmail(email, actionCodeSettings)
                .then(() => {{
                    console.log("Email de recuperação enviado com sucesso");
                    alert("Um email de recuperação de senha foi enviado para " + email + ". Por favor, verifique sua caixa de entrada e siga as instruções para redefinir sua senha.");
                }})
                .catch((error) => {{
                    console.error("Erro ao enviar email de recuperação:", error);
                    let mensagem = "Erro ao enviar email de recuperação: " + error.message;
                    
                    if (error.code === 'auth/user-not-found') {{
                        mensagem = "Email não encontrado. Verifique se o email está correto ou crie uma nova conta.";
                    }}
                    
                    alert(mensagem);
                }});
        }};
    }}
    </script>
    """, unsafe_allow_html=True)
    
    # Navegação em abas
    tab1, tab2 = st.tabs(["Login", "Recuperação de Senha"])
    
    with tab1:
        # Formulário de login padrão
        with st.form("login_form"):
            st.subheader("Login com email e senha")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Entrar", use_container_width=True)
            with col2:
                demo = st.form_submit_button("Modo Demo", use_container_width=True)
            
            if submit:
                # Modo simplificado: aceitar qualquer senha não vazia para qualquer email
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        "email": email,
                        "auth_method": "email",
                        "login_time": datetime.now().isoformat()
                    }
                    st.success(f"Login bem-sucedido com {email}")
                    st.rerun()
                else:
                    st.error("Por favor preencha email e senha")
            
            if demo:
                # Modo demo para testes
                st.session_state.authenticated = True
                st.session_state.user = {
                    "email": "demo@example.com",
                    "name": "Usuário Demo",
                    "auth_method": "demo",
                    "demo": True,
                    "login_time": datetime.now().isoformat()
                }
                st.success("Modo demonstração ativado!")
                st.rerun()
    
    with tab2:
        # Formulário de recuperação de senha
        st.subheader("Recuperação de Senha")
        st.write("Informe seu email para receber instruções de recuperação de senha")
        
        recovery_email = st.text_input("Email para recuperação")
        
        if st.button("Enviar Email de Recuperação", use_container_width=True):
            if recovery_email:
                # Chamar a função JavaScript de recuperação de senha
                st.markdown(f"""
                <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    if (typeof window.resetPassword === 'function') {{
                        window.resetPassword("{recovery_email}");
                    }} else {{
                        alert("Módulo de recuperação de senha não disponível. Verifique sua conexão e tente novamente.");
                    }}
                }});
                </script>
                """, unsafe_allow_html=True)
                
                st.info(f"Processando solicitação para {recovery_email}...")
            else:
                st.error("Por favor, informe seu email")

    # Separador
    st.markdown("<p style='text-align:center; margin: 20px 0;'>ou</p>", unsafe_allow_html=True)
    
    # Login com Google (funcionalidade simulada para teste)
    if st.button("Continuar com Google", key="google_btn", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user = {
            "email": "usuario@gmail.com",
            "name": "Usuário Google",
            "auth_method": "google",
            "profile_pic": "https://lh3.googleusercontent.com/a/default-user",
            "login_time": datetime.now().isoformat()
        }
        st.success("Login com Google bem-sucedido!")
        st.rerun()
    
    # Login com Facebook (funcionalidade simulada para teste)
    if st.button("Continuar com Facebook", key="facebook_btn", type="primary", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user = {
            "email": "usuario@facebook.com",
            "name": "Usuário Facebook",
            "auth_method": "facebook",
            "profile_pic": "https://graph.facebook.com/default-user/picture",
            "login_time": datetime.now().isoformat()
        }
        st.success("Login com Facebook bem-sucedido!")
        st.rerun()
    
    # Informação de uso
    st.markdown("""
    <div style="margin-top: 30px; text-align: center; color: #666;">
        <p>Este é um ambiente de demonstração para fins de desenvolvimento. Não utilize senhas reais.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown("""
    <div style="margin-top: 50px;">
        <h2 style="text-align: center; margin-bottom: 30px;">Planos e Preços</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; height: 100%;">
            <h3 style="text-align: center; color: #333;">Mensal</h3>
            <h2 style="text-align: center; color: #007bff; margin: 10px 0;">R$ 9,70</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">por mês</p>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte via email</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
            </ul>
            <div style="text-align: center; margin-top: 20px;">
                <button style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Assinar Plano</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; border: 2px solid #007bff; border-radius: 10px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background-color: #007bff; color: white; margin: -20px -20px 20px -20px; padding: 10px; text-align: center; border-radius: 8px 8px 0 0;">
                <span>Mais Popular</span>
            </div>
            <h3 style="text-align: center; color: #333;">Anual</h3>
            <h2 style="text-align: center; color: #007bff; margin: 10px 0;">R$ 97,00</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">por ano (economize 17%)</p>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte prioritário</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
                <li>Economia de 2 meses no ano</li>
            </ul>
            <div style="text-align: center; margin-top: 20px;">
                <button style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">Assinar Plano</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; height: 100%;">
            <h3 style="text-align: center; color: #333;">Vitalício</h3>
            <h2 style="text-align: center; color: #007bff; margin: 10px 0;">R$ 247,00</h2>
            <p style="text-align: center; color: #666; margin-bottom: 20px;">pagamento único</p>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte premium</li>
                <li>Acesso vitalício sem mensalidades</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Prioridade nas atualizações</li>
            </ul>
            <div style="text-align: center; margin-top: 20px;">
                <button style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Comprar Acesso</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="margin-top: 50px; text-align: center; color: #666; font-size: 0.8rem;">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
        <p>Dúvidas? Entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)

# Se estiver autenticado, mostrar área de usuário
else:
    # Exibir mensagem de boas-vindas
    st.success(f"Login realizado com sucesso como {st.session_state.user.get('email')}")
    
    # Exibir informações do usuário
    st.write("### Dados do usuário")
    st.json(st.session_state.user)
    
    # Botão para entrar no sistema
    if st.button("Acessar o Sistema", key="btn_access_system"):
        st.switch_page("app.py")
    
    # Botão para sair
    if st.button("Sair", key="btn_logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()