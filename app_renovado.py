import streamlit as st
import time
import pandas as pd
import os
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar banco de dados e configurações
import utils.database as db
import utils.page_config as page_config
from utils.firebase_auth import (
    login_with_email_password,
    register_with_email_password,
    reset_password,
    verify_firebase_token
)

# Inicializar variáveis de sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

if "token" not in st.session_state:
    st.session_state["token"] = None

if "mostrar_termos" not in st.session_state:
    st.session_state["mostrar_termos"] = False

if "mostrar_politica" not in st.session_state:
    st.session_state["mostrar_politica"] = False

# Funções para páginas de termos e política
def show_termos():
    """Mostra a página de termos de uso"""
    st.session_state["mostrar_termos"] = True
    st.rerun()

def show_politica():
    """Mostra a página de política de privacidade"""
    st.session_state["mostrar_politica"] = True
    st.rerun()

# Função para verificar login
def verificar_login():
    if st.session_state["autenticado"] and st.session_state["usuario"]:
        return (
            st.session_state["usuario"].get("localId"),
            st.session_state["usuario"].get("displayName", "Usuário"),
            st.session_state["usuario"].get("email")
        )
    return None, None, None

# Função para mostrar a landing page
def mostrar_landing_page():
    # Configuração da página
    st.set_page_config(
        page_title="Planner Organiza | Sistema Profissional",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
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
        try:
            from pages.termos_de_uso import show
            show()
        except ImportError:
            st.markdown("""
            # Termos de Uso
            
            ## 1. Aceite dos Termos
            
            Ao acessar este aplicativo, você concorda em cumprir estes Termos de Serviço, todas as leis e regulamentos aplicáveis e concorda que é responsável pelo cumprimento de todas as leis locais aplicáveis.
            
            ## 2. Licença de Uso
            
            É concedida permissão para uso temporário deste aplicativo para uso pessoal e comercial, não para redistribuição ou revenda. Esta é a concessão de uma licença, não uma transferência de título.
            """)
    elif "politica" in query_params:
        try:
            from pages.politica_privacidade import show
            show()
        except ImportError:
            st.markdown("""
            # Política de Privacidade
            
            ## 1. Coleta de Dados
            
            Coletamos informações que você nos fornece diretamente, como nome, e-mail, dados de propostas, clientes, e outras informações que você decide compartilhar.
            
            ## 2. Uso de Dados
            
            Utilizamos suas informações para fornecer, manter e melhorar nossos serviços, bem como para entender como você usa nosso aplicativo.
            """)
    elif "planos" in query_params:
        try:
            from utils.planos import mostrar_secao_planos
            
            # Título da página
            st.markdown("""
            <div style="text-align: center; max-width: 800px; margin: 0 auto;">
                <h1 style="margin-bottom: 1rem;">Escolha o Plano Ideal para o Seu Negócio</h1>
                <p style="font-size: 1.1rem; margin-bottom: 2rem; color: #666;">
                    Gerencie suas propostas, clientes e finanças com a plataforma mais completa do mercado.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar os planos
            mostrar_secao_planos(layout_colunas=True)
            
            # Seção de depoimentos
            st.markdown("<div style='margin: 2rem 0; border-top: 1px solid #eee;'></div>", unsafe_allow_html=True)
            st.markdown("## O que nossos clientes estão dizendo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div style="padding: 1.5rem; background-color: #f9f9f9; border-radius: 10px; margin: 1rem 0;">
                    <p>"Este sistema me ajudou a organizar meu negócio de forma profissional. Consigo gerenciar todas as propostas e acompanhar o financeiro com facilidade."</p>
                    <p><strong>- Maria Silva, Consultora de Organização</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="padding: 1.5rem; background-color: #f9f9f9; border-radius: 10px; margin: 1rem 0;">
                    <p>"Desde que comecei a usar o Planner Organiza, meu faturamento aumentou em 30%. A visão clara de todos os projetos fez toda a diferença."</p>
                    <p><strong>- João Santos, Personal Organizer</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            # Botão para iniciar período de teste
            st.markdown("<div style='margin: 2rem 0; border-top: 1px solid #eee;'></div>", unsafe_allow_html=True)
            st.markdown("### Ainda não está pronto para assinar?")
            
            if st.button("Iniciar Período de Teste Gratuito", type="secondary", use_container_width=True):
                if st.session_state.get("autenticado", False):
                    # Iniciar período de teste
                    usuario_id = st.session_state["usuario"].get("localId")
                    if usuario_id:
                        try:
                            from utils.assinatura_db import iniciar_periodo_teste
                            resultado = iniciar_periodo_teste(usuario_id, dias=7)
                            if resultado.get("sucesso"):
                                st.success("Período de teste iniciado com sucesso!")
                                st.balloons()
                                time.sleep(2)
                                st.experimental_rerun()
                            else:
                                st.error(f"Falha ao iniciar período de teste: {resultado.get('mensagem')}")
                        except Exception as e:
                            st.error(f"Erro ao iniciar período de teste: {str(e)}")
                else:
                    st.info("Para iniciar o período de teste gratuito, você precisa criar uma conta ou fazer login.")
                    if st.button("Fazer Login ou Cadastrar"):
                        # Redirecionar para página de login
                        st.markdown("""
                        <script>
                            window.location.href = "/?login=1";
                        </script>
                        """, unsafe_allow_html=True)
                        st.info("Redirecionando para página de login...")
        except Exception as e:
            st.error(f"Erro ao carregar a página de planos: {str(e)}")
    elif "login" in query_params or st.session_state.get("mostrar_login", False):
        # Formulário de login
        st.subheader("Acesse sua conta")
        
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_password")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("Entrar", type="primary", use_container_width=True):
                if email and senha:
                    with st.spinner("Autenticando..."):
                        try:
                            resultado = login_with_email_password(email, senha)
                            if resultado.get("autenticado"):
                                st.session_state["autenticado"] = True
                                st.session_state["usuario"] = resultado.get("usuario")
                                st.session_state["token"] = resultado.get("token")
                                st.success("Login realizado com sucesso!")
                                time.sleep(1)
                                # Redirecionar para o dashboard
                                st.markdown("""
                                <script>
                                    window.location.href = "/dashboard";
                                </script>
                                """, unsafe_allow_html=True)
                                st.info("Redirecionando para o dashboard...")
                            else:
                                st.error(f"Falha na autenticação: {resultado.get('mensagem')}")
                        except Exception as e:
                            st.error(f"Erro ao fazer login: {str(e)}")
                else:
                    st.warning("Preencha todos os campos.")
        
        with col2:
            if st.button("Esqueci a senha", use_container_width=True):
                if email:
                    try:
                        reset_password(email)
                        st.success(f"Email de redefinição de senha enviado para {email}")
                    except Exception as e:
                        st.error(f"Erro ao enviar email de redefinição: {str(e)}")
                else:
                    st.warning("Digite seu email para redefinir a senha.")
        
        with col3:
            if st.button("Criar conta", use_container_width=True):
                st.session_state["mostrar_cadastro"] = True
                st.session_state["mostrar_login"] = False
                st.rerun()
        
        # Opção para voltar à página inicial
        if st.button("← Voltar para a página inicial"):
            st.session_state["mostrar_login"] = False
            st.rerun()
    elif "cadastro" in query_params or st.session_state.get("mostrar_cadastro", False):
        # Formulário de cadastro
        st.subheader("Crie sua conta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome completo", key="cadastro_nome")
            email = st.text_input("Email", key="cadastro_email")
        
        with col2:
            senha = st.text_input("Senha", type="password", help="Mínimo 6 caracteres", key="cadastro_senha")
            confirmar_senha = st.text_input("Confirmar senha", type="password", key="cadastro_confirmar")
        
        aceito_termos = st.checkbox("Li e concordo com os [Termos de Uso](/?termos=1) e a [Política de Privacidade](/?politica=1)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Cadastrar", type="primary", use_container_width=True):
                if not nome or not email or not senha or not confirmar_senha:
                    st.error("Todos os campos são obrigatórios.")
                elif senha != confirmar_senha:
                    st.error("As senhas não coincidem.")
                elif len(senha) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                elif not aceito_termos:
                    st.error("Você precisa aceitar os termos de uso e política de privacidade.")
                else:
                    with st.spinner("Cadastrando..."):
                        try:
                            resultado = register_with_email_password(email, senha, nome)
                            if resultado.get("registrado"):
                                st.success("Cadastro realizado com sucesso!")
                                st.session_state["autenticado"] = True
                                st.session_state["usuario"] = resultado.get("usuario")
                                st.session_state["token"] = resultado.get("token")
                                time.sleep(1)
                                # Redirecionar para o dashboard
                                st.markdown("""
                                <script>
                                    window.location.href = "/dashboard";
                                </script>
                                """, unsafe_allow_html=True)
                                st.info("Redirecionando para o dashboard...")
                            else:
                                st.error(f"Falha no cadastro: {resultado.get('mensagem')}")
                        except Exception as e:
                            st.error(f"Erro ao cadastrar: {str(e)}")
        
        with col2:
            if st.button("Já tenho uma conta", use_container_width=True):
                st.session_state["mostrar_cadastro"] = False
                st.session_state["mostrar_login"] = True
                st.rerun()
        
        # Opção para voltar à página inicial
        if st.button("← Voltar para a página inicial"):
            st.session_state["mostrar_cadastro"] = False
            st.rerun()
    else:
        # Página inicial
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
            
            # Botões de ação
            col_login, col_planos = st.columns(2)
            
            with col_login:
                if st.button("Faça Login", type="primary", use_container_width=True):
                    st.session_state["mostrar_login"] = True
                    st.rerun()
            
            with col_planos:
                if st.button("Ver planos disponíveis", use_container_width=True):
                    # Redirecionar para página de planos
                    st.markdown("""
                    <script>
                        window.location.href = "/?planos=1";
                    </script>
                    """, unsafe_allow_html=True)
                    st.success("Redirecionando para a página de planos...")
        
        with cols[1]:
            # Imagem ilustrativa
            try:
                st.image("app-icon.svg", width=300)
            except:
                st.image("app-icon-192.png", width=300)
    
    # Rodapé
    st.markdown("""
    <div class="footer">
        <p>&copy; 2025 Planner Organiza. Todos os direitos reservados.</p>
        <p>
            <a href="/?termos=1">Termos de Uso</a> | 
            <a href="/?politica=1">Política de Privacidade</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Função principal
def main():
    # Verificar parâmetros da URL
    query_params = st.query_params
    
    # Se estiver na página inicial, mostrar a landing page
    if not query_params or "home" in query_params or "login" in query_params or "cadastro" in query_params or "termos" in query_params or "politica" in query_params or "planos" in query_params:
        mostrar_landing_page()
    else:
        # Configuração da página para o aplicativo principal
        st.set_page_config(
            page_title="Planner Organiza | Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Verificar autenticação
        if not st.session_state.get("autenticado", False):
            st.warning("Você precisa fazer login para acessar esta página.")
            
            if st.button("Fazer Login"):
                # Redirecionar para página de login
                st.markdown("""
                <script>
                    window.location.href = "/?login=1";
                </script>
                """, unsafe_allow_html=True)
                st.info("Redirecionando para página de login...")
            
            return
        
        # Carregar a página principal do sistema
        try:
            from utils.page_config import show_main_page
            show_main_page()
        except Exception as e:
            st.error(f"Erro ao carregar a página principal: {str(e)}")

if __name__ == "__main__":
    main()