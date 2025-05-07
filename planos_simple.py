import streamlit as st
import logging
from utils.stripe_handler import verificar_configuracao_stripe
from utils.planos import mostrar_secao_planos
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock de autenticação para permitir assinatura antes do login
class DummyAuth:
    def is_authenticated(self):
        return False
    
    def get_current_user(self):
        return None
    
    def logout(self):
        pass

def check_login():
    """Verifica se o usuário está logado e retorna suas informações"""
    # Nesta versão simplificada, não há login real
    return {"autenticado": False, "usuario": None}

def logout():
    """Realiza logout do usuário"""
    pass

def get_firebase_token():
    """Recupera o token do Firebase da sessão"""
    return None

def iniciar_periodo_teste(usuario_id, dias=7):
    """
    Inicia um período de teste para o usuário
    
    Args:
        usuario_id: ID do usuário
        dias: Número de dias do período de teste
        
    Returns:
        dict: Resultado da operação
    """
    logger.info(f"Iniciando período de teste para usuário {usuario_id} por {dias} dias")
    return {"sucesso": True, "mensagem": "Período de teste iniciado com sucesso"}

def mostrar_pagina_planos():
    """
    Mostra a página de planos para assinatura
    Esta função é usada como parte da página principal
    """
    # Configuração da página
    st.set_page_config(
        page_title="Planner Organiza | Planos",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # CSS para estilo da página
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .header-text {
        text-align: center;
        padding: 2rem 0;
    }
    .header-text h1 {
        color: #1E366F;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .header-text p {
        color: #666;
        font-size: 1.2rem;
        max-width: 800px;
        margin: 0 auto;
    }
    .divider {
        margin: 2rem 0;
        border-top: 1px solid #eee;
    }
    .testimonial {
        padding: 1.5rem;
        background-color: #f9f9f9;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #666;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho da página
    st.markdown("""
    <div class="header-text">
        <h1>Escolha o plano ideal para o seu negócio</h1>
        <p>Tenha acesso a todas as funcionalidades para gerenciar suas propostas, clientes e finanças de forma eficiente.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar configuração do Stripe e exibir aviso se necessário
    config = verificar_configuracao_stripe()
    if not all(config.values()):
        st.warning("⚠️ Sistema de pagamento em manutenção. Alguns planos podem estar indisponíveis temporariamente.")
    
    # Exibir planos com preços e botões de assinatura
    mostrar_secao_planos(layout_colunas=True)
    
    # Seção de depoimentos
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("## O que nossos clientes estão dizendo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="testimonial">
            <p>"Este sistema me ajudou a organizar meu negócio de forma profissional. Consigo gerenciar todas as propostas e acompanhar o financeiro com facilidade."</p>
            <p><strong>- Maria Silva, Consultora de Organização</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="testimonial">
            <p>"Desde que comecei a usar o Planner Organiza, meu faturamento aumentou em 30%. A visão clara de todos os projetos fez toda a diferença."</p>
            <p><strong>- João Santos, Personal Organizer</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Perguntas frequentes
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("## Perguntas Frequentes")
    
    with st.expander("Posso cancelar minha assinatura a qualquer momento?"):
        st.write("Sim, você pode cancelar sua assinatura a qualquer momento. No plano mensal, o acesso continua até o final do período já pago. No plano anual, você mantém o acesso até o final do ano contratado.")
    
    with st.expander("O que acontece após eu assinar?"):
        st.write("Após a confirmação do pagamento, você terá acesso imediato a todas as funcionalidades do sistema. Você receberá um email com os detalhes da sua assinatura e instruções de acesso.")
    
    with st.expander("Existe algum período de teste?"):
        st.write("Sim, oferecemos um período de teste gratuito de 7 dias para que você possa conhecer todas as funcionalidades antes de assinar. Durante este período, você terá acesso a todas as funcionalidades sem restrições.")
    
    with st.expander("Quais métodos de pagamento são aceitos?"):
        st.write("Aceitamos cartões de crédito das principais bandeiras (Visa, Mastercard, American Express, Elo). Os pagamentos são processados de forma segura através da plataforma Stripe.")
    
    # Botão para iniciar período de teste
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("### Ainda não está pronto para assinar?")
    
    if st.button("Iniciar Período de Teste Gratuito", type="secondary", use_container_width=True):
        st.info("Para iniciar o período de teste gratuito, você precisa criar uma conta ou fazer login.")
        if st.button("Criar Conta/Login"):
            st.session_state["redirect"] = "login"
    
    # Rodapé
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="footer">
        <p>&copy; 2025 Planner Organiza. Todos os direitos reservados.</p>
        <p>Ao assinar, você concorda com nossos <a href="#">Termos de Serviço</a> e <a href="#">Política de Privacidade</a>.</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    mostrar_pagina_planos()

def show():
    main()

if __name__ == "__main__":
    main()