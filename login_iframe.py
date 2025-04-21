import streamlit as st
import os
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Login - Planner Organizer",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos personalizados
st.markdown("""
<style>
    .login-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .login-header {
        text-align: center;
        margin-bottom: 20px;
    }
    .login-header h1 {
        color: #2d8cff;
        font-weight: bold;
    }
    .firebase-iframe {
        width: 100%;
        min-height: 400px;
        border: none;
        overflow: hidden;
    }
    .demo-button {
        background-color: #28a745;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        margin-top: 20px;
        display: block;
        width: 100%;
        text-align: center;
    }
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 20px 0;
    }
    .divider::before,
    .divider::after {
        content: "";
        flex: 1;
        border-bottom: 1px solid #ddd;
    }
    .divider span {
        padding: 0 10px;
        color: #999;
    }
    .pricing-container {
        margin-top: 30px;
    }
    .pricing-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        height: 100%;
    }
    .pricing-card.highlight {
        border: 2px solid #2d8cff;
    }
    .pricing-header {
        background-color: #2d8cff;
        color: white;
        padding: 10px;
        margin: -20px -20px 20px -20px;
        border-radius: 10px 10px 0 0;
        text-align: center;
    }
    .pricing-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .pricing-price {
        font-size: 28px;
        font-weight: bold;
        color: #2d8cff;
        text-align: center;
        margin-bottom: 5px;
    }
    .pricing-period {
        color: #777;
        font-size: 14px;
        text-align: center;
        margin-bottom: 20px;
    }
    .pricing-button {
        background-color: #2d8cff;
        color: white;
        padding: 10px;
        border: none;
        border-radius: 5px;
        width: 100%;
        cursor: pointer;
        font-weight: bold;
        margin-top: 15px;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        color: #777;
        font-size: 14px;
    }
    /* Esconder elementos desnecessários */
    header {
        visibility: hidden;
    }
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    /* Adicione seu CSS personalizado aqui */
</style>
""", unsafe_allow_html=True)

# Inicializar sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# Verificar parâmetros de URL para autenticação com Firebase
try:
    params = dict(st.query_params)
    if "auth_success" in params and params["auth_success"] == "true":
        if "uid" in params and "email" in params:
            # Login via Firebase bem-sucedido
            uid = params["uid"]
            email = params["email"]
            
            # Salvar na sessão
            st.session_state.authenticated = True
            st.session_state.user = {
                "uid": uid,
                "email": email,
                "auth_method": "firebase",
                "login_time": datetime.now().isoformat()
            }
            
            # Limpar parâmetros de URL
            st.query_params.clear()
            st.rerun()
except Exception as e:
    st.error(f"Erro ao processar parâmetros de URL: {e}")
    # Evitar que erros nos parâmetros de URL quebrem a página

# Script para receber mensagem do iframe
js_code = """
<script>
window.addEventListener('message', function(event) {
    // Verificar origem da mensagem (a fazer: tornar mais seguro)
    
    // Processar mensagem de autenticação bem-sucedida
    if (event.data.type === 'FIREBASE_AUTH_SUCCESS') {
        console.log('Autenticação Firebase bem-sucedida:', event.data.payload);
        
        // Redirecionar para a mesma página com parâmetros de autenticação
        const url = new URL(window.location.href);
        url.searchParams.set('auth_success', 'true');
        url.searchParams.set('uid', event.data.payload.uid);
        url.searchParams.set('email', event.data.payload.email);
        
        // Redirecionar
        window.location.href = url.toString();
    }
});
</script>
"""

# Adicionar script à página
st.markdown(js_code, unsafe_allow_html=True)

# Título principal
st.markdown('<div class="login-header"><h1>Planner Organizer</h1><p>Sistema de Gestão Profissional para o seu Negócio</p></div>', unsafe_allow_html=True)

# Mostrar área de login ou dashboard conforme o estado de autenticação
if not st.session_state.authenticated:
    # Área de login
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Incorporar iframe com a página de login do Firebase
    iframe_url = "public/firebase_login.html"
    st.markdown(f'<iframe src="{iframe_url}" class="firebase-iframe"></iframe>', unsafe_allow_html=True)
    
    # Separador
    st.markdown('<div class="divider"><span>OU</span></div>', unsafe_allow_html=True)
    
    # Botão de login de demonstração
    if st.button("Login no Modo de Demonstração", key="demo_login", use_container_width=True, type="primary"):
        st.session_state.authenticated = True
        st.session_state.user = {
            "uid": "demo-user",
            "email": "demo@example.com",
            "name": "Usuário Demonstração",
            "auth_method": "demo",
            "demo": True,
            "login_time": datetime.now().isoformat()
        }
        st.success("Login de demonstração realizado com sucesso!")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown('<h2 style="text-align: center; margin-top: 40px; margin-bottom: 20px;">Escolha o Plano Ideal para o Seu Negócio</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-title">Mensal</h3>
            <div class="pricing-price">R$ 9,70</div>
            <div class="pricing-period">por mês</div>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte via email</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
            </ul>
            <button class="pricing-button">Assinar Plano</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="pricing-card highlight">
            <div class="pricing-header">Mais Popular</div>
            <h3 class="pricing-title">Anual</h3>
            <div class="pricing-price">R$ 97,00</div>
            <div class="pricing-period">por ano (economize 17%)</div>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte prioritário</li>
                <li>7 dias de teste grátis</li>
                <li>Cancele quando quiser</li>
                <li>Economia de 2 meses no ano</li>
            </ul>
            <button class="pricing-button">Assinar Plano</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3 class="pricing-title">Vitalício</h3>
            <div class="pricing-price">R$ 247,00</div>
            <div class="pricing-period">pagamento único</div>
            <ul>
                <li>Acesso a todas as funcionalidades</li>
                <li>Suporte premium</li>
                <li>Acesso vitalício sem mensalidades</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Prioridade nas atualizações</li>
            </ul>
            <button class="pricing-button">Comprar Acesso</button>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div class="footer">
        <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
        <p>Dúvidas? Entre em contato: contato@plannerorganizer.com.br</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Área de usuário autenticado
    if st.session_state.user:
        st.success(f"Login realizado com sucesso como {st.session_state.user.get('email', 'usuário')}")
        
        # Exibir informações do usuário
        st.write("### Dados do usuário")
        st.json(st.session_state.user)
    else:
        # Caso raro em que authenticated é True mas user não está disponível
        st.warning("Sessão autenticada, mas dados do usuário não estão disponíveis")
        st.session_state.authenticated = False  # Força reconexão
        st.rerun()
    
    # Botão para acessar o sistema
    if st.button("Acessar o Sistema", key="btn_access_system", type="primary", use_container_width=True):
        st.switch_page("app.py")
    
    # Botão para sair
    if st.button("Sair", key="btn_logout", use_container_width=True):
        # Limpar sessão
        st.session_state.authenticated = False
        st.session_state.user = None
        
        # Adicionar código JavaScript para limpar localStorage
        st.markdown("""
        <script>
        localStorage.removeItem('firebase_user');
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun()