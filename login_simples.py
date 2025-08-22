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

# Verificar estado para mostrar política de privacidade
if "show_politica" not in st.session_state:
    st.session_state.show_politica = False

# Estado para controlar modo de criação de conta
if "creating_account" not in st.session_state:
    st.session_state.creating_account = False

# Mostrar termos de uso se solicitado ou se estiver criando conta pela primeira vez
if st.session_state.show_termos or (st.session_state.creating_account and "termos_viewed" not in st.session_state):
    st.session_state.termos_viewed = True
    from pages.termos_de_uso import show
    show()
    st.stop()

# Mostrar política de privacidade se solicitado
if st.session_state.show_politica:
    from pages.politica_privacidade import show
    show()
    st.stop()

# Adicionar o cabeçalho personalizado
header_html = """
<div style="background: linear-gradient(120deg, #2E4057 0%, #4A6670 100%); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center; position: relative; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <h2 style="color: white; margin: 0; padding: 0; font-family: 'Poppins', sans-serif;">Planner Organizer</h2>
    <a href="/planos_novo" style="position: absolute; top: 50%; right: 1rem; transform: translateY(-50%); background-color: #FF7043; color: white; padding: 0.5rem 1rem; border-radius: 2rem; text-decoration: none; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: all 0.3s ease;">
        💰 Planos e Assinaturas
    </a>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)


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

def show_politica():
    """Mostra a página de política de privacidade"""
    st.session_state.show_politica = True
    st.rerun()

def main():
    # Se o usuário já estiver autenticado, redirecionar para o app principal
    if st.session_state.authenticated:
        # Redirecionar para o app principal
        st.success("Login realizado com sucesso! Redirecionando...")
        st.session_state.authenticated = True
        st.switch_page("app.py")
        return
    
    # Componentes para capturar cliques nos links do formulário
    if st.checkbox("", key="termos_form_link", label_visibility="collapsed"):
        show_termos()
    
    if st.checkbox("", key="politica_form_link", label_visibility="collapsed"):
        show_politica()
    
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
            
            # Links para termos e política
            terms_html = """
            <div style="font-size: 0.9rem; margin: 15px 0;">
                Ao criar uma conta, você concorda com nossos 
                <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_termos_form')); return false;">Termos de Uso</a> e 
                <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_politica_form')); return false;">Política de Privacidade</a>
            </div>
            """
            st.markdown(terms_html, unsafe_allow_html=True)
            
            # Interceptar cliques nos termos e política
            js_code = """
            <script>
                document.addEventListener('show_termos_form', function() {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: true,
                        dataType: 'bool',
                        componentId: 'termos_form_link'
                    }, '*');
                });
                
                document.addEventListener('show_politica_form', function() {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: true,
                        dataType: 'bool',
                        componentId: 'politica_form_link'
                    }, '*');
                });
            </script>
            """
            st.components.v1.html(js_code, height=0)
            
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
        
        # CSS para otimização mobile - LOGIN PRIORITÁRIO
        mobile_css = """
        <style>
        /* MOBILE OPTIMIZATION - LOGIN FIRST */
        @media (max-width: 768px) {
            /* LOGIN FORMULÁRIO NO TOPO NO MOBILE */
            .login-form-container {
                order: -1 !important; /* Move form para o topo */
                margin-bottom: 1.5rem !important;
                background: #f8f9fa !important;
                border-radius: 10px !important;
                padding: 1rem !important;
                border: 2px solid #4A6670 !important;
            }
            
            /* Títulos menores no mobile */
            h1[data-testid="stTitle"] {
                font-size: 1.3rem !important;
                margin-bottom: 0.3rem !important;
                text-align: center !important;
            }
            
            /* Subtitle centralizado e menor */
            .element-container h3 {
                font-size: 0.9rem !important;
                margin-bottom: 0.8rem !important;
                text-align: center !important;
            }
            
            /* Colunas em stack vertical no mobile */
            div[data-testid="column"] {
                width: 100% !important;
                flex: none !important;
                margin-bottom: 1rem !important;
            }
            
            /* Imagem promocional menor no mobile */
            div[data-testid="column"]:first-child {
                max-width: 150px !important;
                margin: 0 auto !important;
            }
            
            /* Conteúdo promocional compacto */
            .login-promo {
                padding: 8px !important;
                margin: 5px 0 !important;
                font-size: 0.8rem !important;
            }
            
            .login-promo h3 {
                font-size: 0.9rem !important;
                margin-bottom: 0.3rem !important;
            }
            
            .login-promo ul {
                padding-left: 12px !important;
                margin-bottom: 0.3rem !important;
            }
            
            .login-promo li {
                margin-bottom: 0.2rem !important;
                font-size: 0.75rem !important;
            }
            
            /* Inputs de login maiores no mobile */
            .stTextInput > div > div > input {
                font-size: 1rem !important;
                padding: 0.7rem !important;
            }
            
            /* Botão de login destacado */
            div.stButton > button[kind="formSubmit"] {
                font-size: 1.1rem !important;
                padding: 0.8rem 1.5rem !important;
                margin-top: 1rem !important;
            }
        }
        </style>
        """
        st.markdown(mobile_css, unsafe_allow_html=True)
        
        # FORMULÁRIO DE LOGIN PRIMEIRO NO MOBILE
        login_container = st.container()
        with login_container:
            st.markdown('<div class="login-form-container">', unsafe_allow_html=True)
            
            # Login tradicional com email/senha
            with st.form("login_form"):
                username = st.text_input("Usuário ou E-mail", placeholder="Digite seu email")
                password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                
                # Checkbox para aceitar os termos
                terms_html = """
                <div style="font-size: 0.8rem; margin: 0.5rem 0; text-align: center;">
                    Ao continuar, você concorda com os <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_termos')); return false;">Termos de Uso</a>
                </div>
                """
                st.markdown(terms_html, unsafe_allow_html=True)
                
                # Botão de login
                submitted = st.form_submit_button("🔐 ENTRAR", use_container_width=True)
                
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
                
                if submitted:
                    # Credenciais de demonstração para testes
                    if username.lower() == "admin" and password == "admin":
                        st.session_state.authenticated = True
                        st.session_state.user_id = "admin-demo-user-123"
                        st.session_state.usuario_id = "admin-demo-user-123"
                        
                        # Dados do usuário demo
                        user_data = {
                            'localId': 'admin-demo-user-123',
                            'email': 'admin@plannerorganizer.com',
                            'role': 'admin'
                        }
                        
                        usuario_data = {
                            'email': 'admin@plannerorganizer.com',
                            'nome': 'Administrador',
                            'telefone': '',
                            'empresa': 'Planner Organizer',
                            'role': 'admin'
                        }
                        
                        st.session_state.user = user_data
                        st.session_state.usuario = usuario_data
                        
                        # Salvar sessão persistente
                        try:
                            from utils.session_persistence import save_session_to_storage
                            save_session_to_storage(user_data, usuario_data, "admin-demo-user-123")
                        except Exception as e:
                            print(f"Erro ao salvar sessão demo: {str(e)}")
                        
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        # Autenticação Firebase
                        try:
                            # Fazer login usando Firebase
                            result = firebase_auth.login(username, password)
                            
                            if result["success"]:
                                st.session_state.authenticated = True
                                
                                # Definir ID do usuário
                                if 'user' in result and 'localId' in result['user']:
                                    usuario_id = result['user']['localId']
                                    st.session_state.usuario_id = usuario_id
                                    st.session_state.user_id = usuario_id
                                
                                st.success("Login realizado com sucesso!")
                                st.rerun()
                            else:
                                # Mensagens de erro personalizadas
                                error_message = result.get("error", "")
                                if "INVALID_PASSWORD" in error_message or "INVALID_LOGIN_CREDENTIALS" in error_message:
                                    st.error("Senha incorreta. Verifique suas credenciais.")
                                elif "EMAIL_NOT_FOUND" in error_message:
                                    st.error("Email não encontrado. Crie uma nova conta.")
                                elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_message:
                                    st.error("Muitas tentativas. Tente novamente mais tarde.")
                                else:
                                    st.error("Erro de autenticação. Verifique suas credenciais.")
                        except Exception as e:
                            st.error("Sistema de autenticação indisponível. Tente novamente.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Layout com duas colunas: imagem promocional e texto
        col1, col2 = st.columns([3, 4])
        
        with col1:
            # Adicionar a imagem promocional
            st.image("professional_business_woman.png", use_column_width=True)
        
        with col2:
            # Conteúdo promocional destacando benefícios do sistema
            promo_html = """
            <div class="login-promo" style="background: linear-gradient(120deg, #FFF8E1 0%, #FFECB3 100%); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #FF7043;">
                <h3 style="color: #5D4037; margin-top: 0; font-size: 20px;">Cansada de planilhas e papéis?</h3>
                <ul style="color: #5D4037; padding-left: 20px; margin-bottom: 5px;">
                    <li><b>Organize</b> - Diga adeus às planilhas desorganizadas</li>
                    <li><b>Centralize</b> - Todos os seus clientes em um só lugar</li>
                    <li><b>Economize</b> - Reduza tempo com tarefas administrativas</li>
                    <li><b>Profissionalize</b> - Impressione seus clientes com relatórios</li>
                </ul>
                <p style="font-style: italic; color: #795548; margin: 5px 0 0 0; font-size: 14px;">Planner Organizer: sua gestão profissional a um clique de distância.</p>
            </div>
            """
            st.markdown(promo_html, unsafe_allow_html=True)
    
        # CONTEÚDO PROMOCIONAL (aparece depois do login no mobile)
        
        # Botão de submissão estilizado para usar cor diferente do azul padrão
        submit_button_style = """
        <style>
        div.stButton > button[kind="formSubmit"] {
            background-color: #4A6670;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="formSubmit"]:hover {
            background-color: #5D4037;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        </style>
        """
        st.markdown(submit_button_style, unsafe_allow_html=True)
        
        # Botão de submissão
        submit = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit:
            # Credenciais de demonstração para testes
            if username.lower() == "admin" and password == "admin":
                st.session_state.authenticated = True
                
                # Configurar usuario_id para o admin
                demo_usuario_id = "admin-demo-user-123"
                st.session_state.usuario_id = demo_usuario_id
                
                st.session_state.usuario = {
                    'id': demo_usuario_id,  # Adicionar ID também no objeto usuario
                    'email': 'admin@plannerorganizer.com',
                    'nome': 'Administrador',
                    'role': 'admin',
                    'telefone': '',
                    'empresa': 'Planner Organizer'
                }
                
                # Importante: Reinicializar o Database com o ID do usuário
                try:
                    from utils.database import Database
                    if 'db' in st.session_state:
                        # Remover a instância antiga do Database
                        del st.session_state.db
                    
                    print(f"DEBUG MULTI-TENANT: Reinicializando Database com usuario_id={demo_usuario_id} para usuário demo")
                    # Criar nova instância com o ID do usuário
                    st.session_state.db = Database(usuario_id=demo_usuario_id)
                except Exception as db_error:
                    print(f"DEBUG MULTI-TENANT: Erro ao reinicializar Database para demo: {str(db_error)}")
                
                st.rerun()
            else:
                # Autenticação Firebase com tratamento de erros
                try:
                    from utils.firebase_auth import firebase_auth
                    
                    # Fazer login usando Firebase
                    result = firebase_auth.login(username, password)
                    
                    if result["success"]:
                        st.session_state.authenticated = True
                        
                        # Garantir que o usuário_id esteja definido corretamente
                        if 'user' in result and 'localId' in result['user']:
                            usuario_id = result['user']['localId']
                            
                            # Importante: Reinicializar o Database com o ID do usuário
                            try:
                                from utils.database import Database
                                if 'db' in st.session_state:
                                    # Remover a instância antiga do Database
                                    del st.session_state.db
                                
                                print(f"DEBUG MULTI-TENANT: Reinicializando Database com usuario_id={usuario_id} após login bem-sucedido")
                                # Criar nova instância com o ID do usuário
                                st.session_state.db = Database(usuario_id=usuario_id)
                            except Exception as db_error:
                                print(f"DEBUG MULTI-TENANT: Erro ao reinicializar Database: {str(db_error)}")
                        
                        st.rerun()
                    else:
                        # Mostrar mensagem de erro amigável
                        error_message = result.get("error", "")
                        # Mensagens personalizadas para cada tipo de erro
                        if "INVALID_PASSWORD" in error_message or "INVALID_LOGIN_CREDENTIALS" in error_message:
                            st.error("Senha incorreta. Por favor, verifique suas credenciais.")
                        elif "EMAIL_NOT_FOUND" in error_message or "USER_NOT_FOUND" in error_message:
                            st.error("Usuário não encontrado. Verifique o email ou crie uma nova conta.")
                        elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_message:
                            st.error("Muitas tentativas incorretas. Por favor, tente novamente mais tarde.")
                        elif "USER_DISABLED" in error_message:
                            st.error("Esta conta foi desativada. Entre em contato com o suporte.")
                        else:
                            # Mensagem genérica para outros erros
                            st.error("Erro de autenticação. Verifique suas credenciais.")
                except Exception as e:
                    # Em caso de erro no próprio sistema de autenticação
                    st.error("Sistema de autenticação indisponível no momento. Tente novamente mais tarde.")
    
    # Usando componente para capturar clique nos termos
    if st.checkbox("", key="termos_link", label_visibility="collapsed"):
        show_termos()
    
    # Informações de acesso para demonstração
    st.info("""
    **Acesso para demonstração:**
    - Usuário: admin
    - Senha: admin
    """)
    
    # Estilizar os outros botões
    alt_buttons_style = """
    <style>
    /* Estilo para o botão Criar Nova Conta */
    div.stButton:nth-of-type(1) > button {
        background-color: #0066FF;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton:nth-of-type(1) > button:hover {
        background-color: #0052CC;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Estilo para o botão Pular Login */
    div.stButton:nth-of-type(2) > button {
        background-color: #0066FF;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton:nth-of-type(2) > button:hover {
        background-color: #0052CC;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    </style>
    """
    st.markdown(alt_buttons_style, unsafe_allow_html=True)
    
    # Botões para esqueceu sua senha e criar conta
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Esqueceu sua senha?", use_container_width=True):
            # Aqui poderia ir a lógica para recuperação de senha
            st.info("Funcionalidade de recuperação de senha em implementação.")
    
    with col2:
        if st.button("Criar uma conta", use_container_width=True):
            st.session_state.creating_account = True
            # Mostrará os termos de uso automaticamente no próximo rerun
            st.rerun()
            
    # Opção alternativa para pular o login durante testes (oculta em uma nova linha)
    if st.button("Pular login (apenas para testes)", use_container_width=False, key="pular_login"):
        st.session_state.authenticated = True
            
            # Configurar usuario_id para o modo de teste
            test_usuario_id = "test-user-bypass-123"
            st.session_state.usuario_id = test_usuario_id
            
            # Configurar dados básicos de usuário
            st.session_state.usuario = {
                'id': test_usuario_id,
                'email': 'test@plannerorganizer.com',
                'nome': 'Usuário de Teste',
                'role': 'user',
                'telefone': '',
                'empresa': 'Planner Organizer'
            }
            
            # Reinicializar o Database com o ID do usuário de teste
            try:
                from utils.database import Database
                if 'db' in st.session_state:
                    # Remover a instância antiga do Database
                    del st.session_state.db
                
                print(f"DEBUG MULTI-TENANT: Reinicializando Database com usuario_id={test_usuario_id} para modo de teste")
                # Criar nova instância com o ID do usuário
                st.session_state.db = Database(usuario_id=test_usuario_id)
            except Exception as db_error:
                print(f"DEBUG MULTI-TENANT: Erro ao reinicializar Database para modo de teste: {str(db_error)}")
            
            st.rerun()
    
    # Adicionar rodapé com links
    # Importar e usar o rodapé padronizado
    try:
        from utils.page_config import apply_page_footer
        apply_page_footer()
    except ImportError:
        # Fallback para o caso de erro na importação
        footer_html = """
        <div class="footer-custom">
            &copy; 2025 Planner Organizer | 
            <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_termos')); return false;">Termos de Uso</a> | 
            <a href="#" onclick="document.dispatchEvent(new CustomEvent('show_politica')); return false;">Política de Privacidade</a> | 
            <a href="mailto:contato@plannerorganizer.com.br">Contato</a>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)
    
    # Detector para política de privacidade no rodapé
    if st.checkbox("", key="politica_link", label_visibility="collapsed"):
        show_politica()

if __name__ == "__main__":
    main()