import streamlit as st
import os
import sys
import time
import logging
from utils.planos import mostrar_planos

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Login",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remover o menu hamburguer e rodapé
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Verificar se o usuário já está autenticado
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Simulação da autenticação para demonstração
if "admin_login_attempt" not in st.session_state:
    st.session_state.admin_login_attempt = False

def main():
    # Se o usuário já estiver autenticado, redirecionar para o app principal
    if st.session_state.authenticated:
        # Redirecionar para o app principal
        st.success("Login realizado com sucesso! Redirecionando...")
        st.session_state.authenticated = True
        time.sleep(1)
        st.switch_page("app.py")
        return
    
    # Cabeçalho principal com logo e slogan
    st.markdown("""
    <div style="text-align: center; background: linear-gradient(135deg, #1E366F, #2D8CFF); padding: 2rem 1rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">Planner Organizer</h1>
        <p style="font-size: 1.5rem; font-weight: 300;">Transforme sua organização em resultados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Aba de navegação principal
    tab_principal, tab_planos, tab_sobre = st.tabs(["Acesso ao Sistema", "Planos e Preços", "Sobre o Sistema"])
    
    # Aba de Acesso ao Sistema
    with tab_principal:
        # Criar um layout com duas colunas
        col1, col2 = st.columns([6, 4])
        
        with col1:
            st.markdown("""
            <div style="padding: 2rem; background-color: #f8f9fa; border-radius: 10px;">
                <h1 style="color: #1E366F; font-size: 2rem;">Sistema Profissional</h1>
                <h3 style="color: #5A6A85; margin-bottom: 2rem;">Gestão para Personal Organizers</h3>
                
                <p style="margin-bottom: 1.5rem; color: #495057;">
                    Acesse o sistema para gerenciar suas propostas, clientes, 
                    produtos e finanças de maneira simples e eficiente.
                </p>
                
                <ul style="list-style-type: none; padding-left: 0; margin-bottom: 2rem;">
                    <li style="margin-bottom: 0.5rem; color: #495057;">✅ Controle de propostas</li>
                    <li style="margin-bottom: 0.5rem; color: #495057;">✅ Gestão de clientes</li>
                    <li style="margin-bottom: 0.5rem; color: #495057;">✅ Finanças e receitas</li>
                    <li style="margin-bottom: 0.5rem; color: #495057;">✅ Relatórios detalhados</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            tab1, tab2 = st.tabs(["Login", "Registrar"])
            
            with tab1:
                # Login tradicional com email/senha
                with st.form("login_form"):
                    username = st.text_input("Usuário ou E-mail")
                    password = st.text_input("Senha", type="password")
                    submit = st.form_submit_button("Entrar", use_container_width=True)
                    
                    if submit:
                        if username.lower() == "admin" and password == "admin":
                            st.session_state.authenticated = True
                            st.session_state.admin_login_attempt = True
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos")
                
                # Divisor com "ou"
                st.markdown("""
                <div style="text-align: center; margin: 1.5rem 0; position: relative;">
                    <hr style="margin: 0; border: none; height: 1px; background-color: #E0E0E0;">
                    <span style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); 
                           background-color: white; padding: 0 10px; color: #5A6A85; font-size: 0.9rem;">
                        ou continuar com
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Botão de login com Google (centralizado)
                st.markdown("""
                <div style="display: flex; justify-content: center; margin-bottom: 1rem;">
                    <button onclick="window.open('login_social.html', '_blank')" 
                            style="width: 100%; background-color: white; border: 1px solid #E0E0E0; 
                            border-radius: 4px; padding: 10px 0; display: flex; align-items: center; 
                            justify-content: center; cursor: pointer; transition: all 0.2s ease;">
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                            style="width: 18px; height: 18px; margin-right: 8px;">
                        Continuar com Google
                    </button>
                </div>
                """, unsafe_allow_html=True)
                
                # Adicionar links para recuperação de senha
                st.markdown("""
                <div style="text-align: center; margin-top: 1rem;">
                    <a href="#" style="color: #1E88E5; text-decoration: none; font-size: 0.9rem;">
                        Esqueceu sua senha?
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                # Nota informativa sobre o login social
                st.success("Login social ativado. Clique no botão 'Continuar com Google' para entrar com sua conta Google.")
                
                # Informações de acesso para demonstração
                st.markdown("""
                <div style="margin-top: 1rem; padding: 0.75rem; background-color: #E3F2FD; border-radius: 4px; border-left: 4px solid #1976D2;">
                    <p style="margin: 0; color: #1E366F; font-size: 0.9rem;">
                        <strong>Acesso para demonstração:</strong><br>
                        Usuário: admin<br>
                        Senha: admin
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with tab2:
                with st.form("registro_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nome = st.text_input("Nome completo")
                        email = st.text_input("E-mail")
                    
                    with col2:
                        senha = st.text_input("Senha", type="password")
                        confirmar_senha = st.text_input("Confirmar senha", type="password")
                    
                    aceito_termos = st.checkbox("Eu aceito os termos de uso")
                    
                    submit_button = st.form_submit_button("Criar conta", use_container_width=True)
                    
                    if submit_button:
                        if not (nome and email and senha and confirmar_senha):
                            st.error("Por favor, preencha todos os campos")
                        elif senha != confirmar_senha:
                            st.error("As senhas não coincidem")
                        elif not aceito_termos:
                            st.error("Você precisa aceitar os termos de uso")
                        else:
                            st.success(f"Conta simulada criada com sucesso para {email}")
                            st.info("Você pode fazer login agora")
    
    # Aba de Planos e Preços
    with tab_planos:
        # Usar o componente de planos e preços
        mostrar_planos()
    
    # Aba Sobre o Sistema
    with tab_sobre:
        st.markdown("## 🚀 Sobre o Planner Organizer")
        
        # Criar colunas para organizar o conteúdo
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### Transforme sua carreira com tecnologia
            
            O **Planner Organizer** é um sistema profissional desenvolvido por e para Personal Organizers. 
            Nossa missão é transformar a forma como os profissionais gerenciam seus projetos, propostas e clientes.
            
            ### Principais diferenciais:
            
            * **Automatização inteligente** - Gere propostas e relatórios com apenas alguns cliques
            * **Controle financeiro** - Saiba exatamente seu faturamento e despesas
            * **Interface intuitiva** - Fácil de usar mesmo para quem não tem familiaridade com tecnologia
            * **Fluxo de trabalho otimizado** - Acompanhe propostas do início ao fim
            * **Suporte ao cliente dedicado** - Estamos sempre prontos para ajudar
            
            ### Criado por quem entende o mercado
            
            Desenvolvido por profissionais que conhecem as dores e necessidades do dia a dia
            de quem trabalha com organização profissional.
            """)
            
            st.markdown("---")
            
            st.markdown("""
            ### Como funciona:
            
            1. **Cadastre seus clientes** - Mantenha suas informações organizadas
            2. **Crie propostas profissionais** - Com valores, prazos e detalhes do serviço
            3. **Acompanhe a execução** - Gerencie o andamento de cada projeto
            4. **Registre vendas e produtos** - Tenha controle sobre produtos vendidos
            5. **Monitore suas finanças** - Visualize receitas, despesas e lucros
            """)
        
        with col2:
            # Exibir imagem ilustrativa
            st.image("favicon.png", width=150)
            
            st.markdown("""
            ### Versão atual:
            
            **Planner Organizer 1.0.4**
            
            Última atualização: Abril 2025
            """)
            
            st.markdown("---")
            
            st.markdown("""
            ### Requisitos técnicos:
            
            * Funciona em qualquer navegador moderno
            * Compatível com computador, tablet e celular
            * Conexão com internet para acesso ao sistema
            """)
            
            st.markdown("---")
            
            st.markdown("""
            ### Segurança:
            
            * Dados protegidos e encriptados
            * Backups automáticos diários
            * Proteção contra acesso não autorizado
            """)
            
            # Botão para contato
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                <a href="mailto:contato@plannerorganiza.com.br" style="display: inline-block; background-color: #1E366F; color: white; padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; font-weight: 500;">
                    📧 Entrar em contato
                </a>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()