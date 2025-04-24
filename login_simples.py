import streamlit as st
import os
import sys
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Login",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Importar e aplicar correção para problemas de carregamento de módulos JavaScript
try:
    from utils.render_fix import inject_render_compatibility_fix
    inject_render_compatibility_fix()
    logger.info("Injetado script de compatibilidade para Render no login")
except Exception as e:
    logger.error(f"Erro ao injetar script de compatibilidade no login: {e}")

# Verificar estado para mostrar termos de uso
if "show_termos" not in st.session_state:
    st.session_state.show_termos = False

# Estado para controlar modo de criação de conta
if "creating_account" not in st.session_state:
    st.session_state.creating_account = False

# Mostrar termos de uso se solicitado ou se estiver criando conta pela primeira vez
if st.session_state.show_termos or (st.session_state.creating_account and "termos_viewed" not in st.session_state):
    st.session_state.termos_viewed = True  # Marcar que os termos já foram vistos
    from pages.termos_de_uso import show
    show()
    st.stop()

# Remover o menu hamburguer e rodapé
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Adicionar novo rodapé personalizado */
    .footer-custom {
        position: fixed;
        bottom: 0;
        width: 100%;
        text-align: center;
        padding: 10px;
        background-color: #f5f7fa;
        font-size: 0.8rem;
        color: #555;
        border-top: 1px solid #eaeaea;
    }
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Verificar se o usuário já está autenticado
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def show_termos():
    """Mostra a página de termos de uso"""
    st.session_state.show_termos = True
    st.rerun()

def main():
    # Se o usuário já estiver autenticado, redirecionar para o app principal
    if st.session_state.authenticated:
        # Redirecionar para o app principal
        st.success("Login realizado com sucesso! Redirecionando...")
        st.session_state.authenticated = True
        st.switch_page("app.py")
        return
    
    # Se o usuário está no processo de criação de conta e já aceitou os termos
    if st.session_state.get("creating_account", False) and st.session_state.get("termos_aceitos", False):
        # Mostrar formulário de cadastro
        st.title("Planner Organizer - Criar Nova Conta")
        st.subheader("Preencha seus dados para criar uma conta no sistema")
        
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome completo")
                email = st.text_input("Email")
                telefone = st.text_input("Telefone")
            
            with col2:
                username = st.text_input("Nome de usuário")
                password = st.text_input("Senha", type="password")
                confirm_password = st.text_input("Confirmar senha", type="password")
            
            # Checkbox de confirmação
            aceite_marketing = st.checkbox("Desejo receber atualizações e novidades por email")
            
            # Botão de submissão
            submit = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if submit:
                # Em um sistema real, aqui seria feito o registro no banco de dados
                # Por enquanto, apenas simulamos um registro bem-sucedido
                if password != confirm_password:
                    st.error("As senhas não coincidem. Por favor, verifique.")
                elif not nome or not email or not username or not password:
                    st.error("Por favor, preencha todos os campos obrigatórios.")
                else:
                    # Simular criação de conta com sucesso
                    st.success("Conta criada com sucesso! Você já pode fazer login.")
                    # Voltar ao modo de login normal
                    st.session_state.creating_account = False
                    st.session_state.termos_aceitos = False
                    st.rerun()
        
        # Botão para voltar ao login
        if st.button("Voltar ao login"):
            st.session_state.creating_account = False
            st.session_state.termos_aceitos = False
            st.rerun()
    else:
        # Tela normal de login
        st.title("Planner Organizer - Login")
        st.subheader("Sistema de Gestão para Personal Organizers")
    
    # Login tradicional com email/senha
    with st.form("login_form"):
        username = st.text_input("Usuário ou E-mail")
        password = st.text_input("Senha", type="password")
        
        # Checkbox para aceitar os termos
        terms_html = """
        <div style="font-size: 0.85rem; margin-top: 10px;">
            Ao continuar, você concorda com os <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_termos')); return false;">Termos de Uso</a>
        </div>
        """
        st.markdown(terms_html, unsafe_allow_html=True)
        
        # Interceptar cliques nos termos de uso
        termos_js = """
        <script>
            document.addEventListener('show_termos', function() {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: true,
                    dataType: 'bool',
                    componentId: 'termos_link'
                }, '*');
            });
        </script>
        """
        st.components.v1.html(termos_js, height=0)
        
        # Botão de submissão
        submit = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit:
            if username.lower() == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    
    # Usando componente para capturar clique nos termos
    if st.checkbox("", key="termos_link", label_visibility="collapsed"):
        show_termos()
    
    # Informações de acesso para demonstração
    st.info("""
    **Acesso para demonstração:**
    - Usuário: admin
    - Senha: admin
    """)
    
    # Botões para criar conta ou pular login
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Criar Nova Conta", use_container_width=True):
            st.session_state.creating_account = True
            # Mostrará os termos de uso automaticamente no próximo rerun
            st.rerun()
    
    with col2:
        # Opção alternativa para pular o login durante testes
        if st.button("Pular login (apenas para testes)", use_container_width=True):
            st.session_state.authenticated = True
            st.rerun()
    
    # Adicionar rodapé com links
    footer_html = """
    <div class="footer-custom">
        &copy; 2025 Planner Organizer | 
        <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_termos')); return false;">Termos de Uso</a> | 
        <a href="mailto:contato@plannerorganizer.com.br">Contato</a>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()