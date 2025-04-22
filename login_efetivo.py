"""
Página de login com integração efetiva com Firebase Auth
"""
import streamlit as st
import os
import json
import time
from datetime import datetime

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Login | Planner Organizer",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Ocultar menu e rodapé
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #f9fafc, #eef5ff);
        color: #333;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #2d8cff;
    }
    
    /* Container principal*/
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    /* Cabeçalho */
    .main-header {
        color: #2d8cff;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .subheader {
        color: #5A6A85;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Formulários */
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    .form-title {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        color: #2d8cff;
        text-align: center;
    }
    
    .form-input {
        margin-bottom: 1.5rem;
    }
    
    .form-input label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #4a5568;
    }
    
    .form-input input {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-size: 1rem;
        transition: all 0.3s;
    }
    
    .form-input input:focus {
        border-color: #2d8cff;
        box-shadow: 0 0 0 3px rgba(45,140,255,0.2);
        outline: none;
    }
    
    .form-button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, #2d8cff, #0063cc);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        margin-top: 1rem;
    }
    
    .form-button:hover {
        background: linear-gradient(135deg, #0063cc, #004a99);
        transform: translateY(-2px);
    }
    
    .form-footer {
        text-align: center;
        margin-top: 1.5rem;
        color: #718096;
        font-size: 0.9rem;
    }
    
    .form-footer a {
        color: #2d8cff;
        text-decoration: none;
        font-weight: 500;
    }
    
    .form-divider {
        display: flex;
        align-items: center;
        margin: 1.5rem 0;
        color: #718096;
    }
    
    .form-divider:before,
    .form-divider:after {
        content: "";
        flex: 1;
        height: 1px;
        background: #e2e8f0;
    }
    
    .form-divider span {
        padding: 0 1rem;
        font-size: 0.9rem;
    }
    
    /* Mensagens */
    .success-message {
        padding: 1rem;
        background: #c6f6d5;
        color: #276749;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .error-message {
        padding: 1rem;
        background: #fed7d7;
        color: #9b2c2c;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    /* Planos */
    .plans-section {
        margin-top: 3rem;
    }
    
    .plans-title {
        font-size: 1.8rem;
        text-align: center;
        margin-bottom: 2rem;
        color: #2d8cff;
    }
    
    .plan-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        transition: all 0.3s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .plan-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.15);
    }
    
    .plan-header {
        padding: 1.5rem;
        background: linear-gradient(135deg, #2d8cff, #0063cc);
        color: white;
        text-align: center;
    }
    
    .plan-name {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .plan-price {
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .plan-price-period {
        font-size: 1rem;
        opacity: 0.8;
    }
    
    .plan-body {
        padding: 1.5rem;
        flex-grow: 1;
    }
    
    .plan-features {
        list-style: none;
        padding: 0;
        margin: 0 0 1.5rem 0;
    }
    
    .plan-features li {
        padding: 0.5rem 0;
        display: flex;
        align-items: center;
    }
    
    .plan-features li:before {
        content: "✓";
        color: #48bb78;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    .plan-footer {
        padding: 1.5rem;
        background: #f7fafc;
        text-align: center;
    }
    
    .plan-button {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, #2d8cff, #0063cc);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        text-decoration: none;
    }
    
    .plan-button:hover {
        background: linear-gradient(135deg, #0063cc, #004a99);
        transform: translateY(-2px);
    }
    
    /* Popular plan */
    .popular-plan {
        transform: scale(1.05);
        border: 2px solid #2d8cff;
    }
    
    .popular-plan .plan-header {
        background: linear-gradient(135deg, #0063cc, #004a99);
    }
    
    .popular-badge {
        background: #ed8936;
        color: white;
        padding: 0.25rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .plan-card {
            margin-bottom: 2rem;
        }
        .popular-plan {
            transform: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Adicionar Firebase SDK
    st.markdown("""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-firestore.js"></script>
    <script src="/public/js/firebase-auth.js"></script>
    """, unsafe_allow_html=True)
    
    # Definir configuração do Firebase
    firebase_config = {
        "apiKey": st.secrets.get("FIREBASE_API_KEY", "AIzaSyA8xzYgZXCkZ-97RWQZXtMpvLVf1Jx8wjk"),
        "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", "planner-organizer.firebaseapp.com"),
        "projectId": st.secrets.get("FIREBASE_PROJECT_ID", "planner-organizer"),
        "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", "planner-organizer.appspot.com"),
        "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", "695046724018"),
        "appId": st.secrets.get("FIREBASE_APP_ID", "1:695046724018:web:98d8feec0c6b6c937d57fd"),
        "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", "https://planner-organizer-default-rtdb.firebaseio.com")
    }
    
    # Inicializar Firebase via JavaScript
    st.markdown(f"""
    <script>
        // Configuração do Firebase
        const firebaseConfig = {json.dumps(firebase_config)};
        
        // Inicializar Firebase quando a página carregar
        document.addEventListener('DOMContentLoaded', function() {{
            // Inicializar Firebase
            if (window.firebaseAuth) {{
                window.firebaseAuth.init(firebaseConfig);
                console.log("Firebase inicializado na página de login");
            }}
        }});
        
        // Funções para autenticação
        function loginUser(email, password) {{
            if (window.firebaseAuth) {{
                window.firebaseAuth.login(email, password)
                    .then((userCredential) => {{
                        // Login bem-sucedido
                        const user = userCredential.user;
                        console.log("Login bem-sucedido:", user.email);
                        
                        // Redirecionar para dashboard
                        window.location.href = "/dashboard";
                    }})
                    .catch((error) => {{
                        // Tratar erros de login
                        console.error("Erro no login:", error);
                        document.getElementById('login-error').textContent = getErrorMessage(error.code);
                        document.getElementById('login-error').style.display = 'block';
                    }});
            }}
        }}
        
        function registerUser(email, password, name) {{
            if (window.firebaseAuth) {{
                window.firebaseAuth.register(email, password, name)
                    .then((userCredential) => {{
                        // Registro bem-sucedido
                        const user = userCredential.user;
                        console.log("Registro bem-sucedido:", user.email);
                        
                        // Verificar se há um plano selecionado
                        const selectedPlan = localStorage.getItem('selected_plan');
                        if (selectedPlan) {{
                            // Redirecionar para checkout
                            window.firebaseAuth.createCheckoutSession(selectedPlan)
                                .then(data => {{
                                    console.log("Checkout criado:", data);
                                    localStorage.removeItem('selected_plan');
                                }})
                                .catch(error => {{
                                    console.error("Erro ao criar checkout:", error);
                                    // Redirecionar para dashboard mesmo com erro
                                    window.location.href = "/dashboard";
                                }});
                        }} else {{
                            // Redirecionar para dashboard
                            window.location.href = "/dashboard";
                        }}
                    }})
                    .catch((error) => {{
                        // Tratar erros de registro
                        console.error("Erro no registro:", error);
                        document.getElementById('register-error').textContent = getErrorMessage(error.code);
                        document.getElementById('register-error').style.display = 'block';
                    }});
            }}
        }}
        
        function resetPassword(email) {{
            if (window.firebaseAuth) {{
                window.firebaseAuth.resetPassword(email)
                    .then(() => {{
                        // E-mail enviado com sucesso
                        console.log("E-mail de redefinição enviado para:", email);
                        document.getElementById('reset-success').textContent = 
                            "E-mail de redefinição enviado. Verifique sua caixa de entrada.";
                        document.getElementById('reset-success').style.display = 'block';
                    }})
                    .catch((error) => {{
                        // Tratar erros de redefinição
                        console.error("Erro na redefinição de senha:", error);
                        document.getElementById('reset-error').textContent = getErrorMessage(error.code);
                        document.getElementById('reset-error').style.display = 'block';
                    }});
            }}
        }}
        
        function getErrorMessage(errorCode) {{
            switch (errorCode) {{
                case 'auth/invalid-email':
                    return 'E-mail inválido.';
                case 'auth/user-disabled':
                    return 'Este usuário foi desativado.';
                case 'auth/user-not-found':
                    return 'Usuário não encontrado.';
                case 'auth/wrong-password':
                    return 'Senha incorreta.';
                case 'auth/email-already-in-use':
                    return 'Este e-mail já está sendo usado por outra conta.';
                case 'auth/weak-password':
                    return 'A senha é muito fraca. Use pelo menos 6 caracteres.';
                default:
                    return 'Ocorreu um erro. Por favor, tente novamente.';
            }}
        }}
    </script>
    """, unsafe_allow_html=True)
    
    # Container principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">Planner Organizer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Sistema Profissional para Personal Organizers</p>', unsafe_allow_html=True)
    
    # Abas para Login/Registro/Recuperação
    tab1, tab2, tab3 = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])
    
    with tab1:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="form-title">Faça Login</h2>', unsafe_allow_html=True)
        
        # Mensagem de erro (oculta por padrão)
        st.markdown('<div id="login-error" class="error-message" style="display: none;"></div>', unsafe_allow_html=True)
        
        # Formulário de login
        email_login = st.text_input("E-mail", key="email_login")
        password_login = st.text_input("Senha", type="password", key="password_login")
        
        # Botão de login
        login_button = st.button("Entrar", key="login_button")
        
        if login_button:
            # JavaScript para executar login
            st.markdown(f"""
            <script>
                loginUser("{email_login}", "{password_login}");
            </script>
            """, unsafe_allow_html=True)
        
        # Links para outras abas
        st.markdown("""
        <div class="form-footer">
            Não tem uma conta? <a href="#" onclick="document.querySelector('.stTabs [role=tablist] button:nth-child(2)').click(); return false;">Registre-se</a>
            <br>
            Esqueceu sua senha? <a href="#" onclick="document.querySelector('.stTabs [role=tablist] button:nth-child(3)').click(); return false;">Recupere aqui</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Divisor
        st.markdown('<div class="form-divider"><span>ou</span></div>', unsafe_allow_html=True)
        
        # Botão para modo de demonstração
        st.markdown("""
        <div style="text-align: center;">
            <a href="/dashboard?demo=true" class="form-button" style="background: #718096; display: inline-block; width: auto; padding: 0.5rem 2rem;">
                Acessar em Modo de Demonstração
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="form-title">Criar Nova Conta</h2>', unsafe_allow_html=True)
        
        # Mensagem de erro (oculta por padrão)
        st.markdown('<div id="register-error" class="error-message" style="display: none;"></div>', unsafe_allow_html=True)
        
        # Formulário de registro
        name_register = st.text_input("Nome", key="name_register")
        email_register = st.text_input("E-mail", key="email_register")
        password_register = st.text_input("Senha", type="password", key="password_register")
        password_confirm = st.text_input("Confirmar Senha", type="password", key="password_confirm")
        
        # Botão de registro
        register_button = st.button("Criar Conta", key="register_button")
        
        if register_button:
            # Verificar se as senhas conferem
            if password_register != password_confirm:
                st.error("As senhas não conferem.")
            else:
                # JavaScript para executar registro
                st.markdown(f"""
                <script>
                    registerUser("{email_register}", "{password_register}", "{name_register}");
                </script>
                """, unsafe_allow_html=True)
        
        # Links para outras abas
        st.markdown("""
        <div class="form-footer">
            Já tem uma conta? <a href="#" onclick="document.querySelector('.stTabs [role=tablist] button:nth-child(1)').click(); return false;">Faça login</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="form-title">Recuperar Senha</h2>', unsafe_allow_html=True)
        
        # Mensagens (ocultas por padrão)
        st.markdown('<div id="reset-success" class="success-message" style="display: none;"></div>', unsafe_allow_html=True)
        st.markdown('<div id="reset-error" class="error-message" style="display: none;"></div>', unsafe_allow_html=True)
        
        # Formulário de recuperação
        email_reset = st.text_input("E-mail", key="email_reset")
        
        # Botão de recuperação
        reset_button = st.button("Enviar E-mail de Recuperação", key="reset_button")
        
        if reset_button:
            # JavaScript para executar recuperação
            st.markdown(f"""
            <script>
                resetPassword("{email_reset}");
            </script>
            """, unsafe_allow_html=True)
        
        # Informações adicionais
        st.markdown("""
        <div class="form-footer">
            <p>Um e-mail com instruções para redefinir sua senha será enviado para o endereço fornecido, se ele estiver associado a uma conta.</p>
            <p>Verifique também sua caixa de spam.</p>
            <a href="#" onclick="document.querySelector('.stTabs [role=tablist] button:nth-child(1)').click(); return false;">Voltar para o login</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown('<div class="plans-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="plans-title">Escolha o plano que melhor se adapta a você</h2>', unsafe_allow_html=True)
    
    # Layout de planos em 3 colunas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="plan-card">
            <div class="plan-header">
                <div class="plan-name">Mensal</div>
                <div class="plan-price">R$ 9,70<span class="plan-price-period">/mês</span></div>
            </div>
            <div class="plan-body">
                <ul class="plan-features">
                    <li>Acesso completo ao sistema</li>
                    <li>Suporte via email</li>
                    <li>Atualizações gratuitas</li>
                    <li>Exportação de relatórios</li>
                    <li>7 dias de teste grátis</li>
                </ul>
            </div>
            <div class="plan-footer">
                <button onclick="selectPlan('monthly')" class="plan-button">Assinar Agora</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="plan-card popular-plan">
            <div class="plan-header">
                <div class="popular-badge">Mais Popular</div>
                <div class="plan-name">Anual</div>
                <div class="plan-price">R$ 97,00<span class="plan-price-period">/ano</span></div>
            </div>
            <div class="plan-body">
                <ul class="plan-features">
                    <li>Acesso completo ao sistema</li>
                    <li>Suporte via email</li>
                    <li>Atualizações gratuitas</li>
                    <li>Exportação de relatórios</li>
                    <li>7 dias de teste grátis</li>
                    <li>Economia de 17% em relação ao plano mensal</li>
                </ul>
            </div>
            <div class="plan-footer">
                <button onclick="selectPlan('yearly')" class="plan-button">Assinar Agora</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="plan-card">
            <div class="plan-header">
                <div class="plan-name">Vitalício</div>
                <div class="plan-price">R$ 247,00<span class="plan-price-period">/único</span></div>
            </div>
            <div class="plan-body">
                <ul class="plan-features">
                    <li>Acesso completo ao sistema</li>
                    <li>Suporte via email</li>
                    <li>Atualizações gratuitas</li>
                    <li>Exportação de relatórios</li>
                    <li>Pagamento único sem mensalidades</li>
                    <li>Economia a longo prazo</li>
                </ul>
            </div>
            <div class="plan-footer">
                <button onclick="selectPlan('lifetime')" class="plan-button">Comprar Agora</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Script para selecionar plano
    st.markdown("""
    <script>
        function selectPlan(planId) {
            // Verificar se o usuário está logado
            const user = firebase.auth().currentUser;
            
            if (user) {
                // Usuário logado, criar checkout diretamente
                window.firebaseAuth.createCheckoutSession(planId)
                    .then(data => {
                        console.log("Checkout criado:", data);
                    })
                    .catch(error => {
                        console.error("Erro ao criar checkout:", error);
                        alert("Erro ao processar pagamento. Por favor, tente novamente.");
                    });
            } else {
                // Usuário não logado, salvar plano e redirecionar para registro
                localStorage.setItem('selected_plan', planId);
                // Mudar para a aba de registro
                document.querySelector('.stTabs [role=tablist] button:nth-child(2)').click();
                // Mostrar mensagem
                alert("Você precisa criar uma conta para assinar este plano.");
            }
        }
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; color: #718096; font-size: 0.9rem;">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
        <p>Atendendo com excelência Personal Organizers em todo Brasil.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()