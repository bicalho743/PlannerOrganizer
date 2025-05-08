import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path para poder importar os módulos de utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.render_fix import inject_render_compatibility_fix

def show():
    # Injetar script de compatibilidade para o Render (se necessário)
    inject_render_compatibility_fix()
    
    # Configuração da página
    st.title("Planos de Assinatura")
    
    # CSS para a mensagem de página em construção
    st.markdown("""
    <style>
    .construction-container {
        background: linear-gradient(135deg, #f5f7fa, #e9eff6);
        padding: 3rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin: 2rem auto;
        max-width: 800px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }
    
    .construction-icon {
        font-size: 5rem;
        margin-bottom: 1.5rem;
        color: #4F4F52;
    }
    
    .construction-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4F4F52;
        margin-bottom: 1rem;
    }
    
    .construction-message {
        font-size: 1.2rem;
        color: #5A6A85;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    .construction-info {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 4px solid #4CAF50;
        text-align: left;
    }
    
    .construction-info-title {
        font-weight: 600;
        color: #4F4F52;
        margin-bottom: 0.5rem;
        font-size: 1.2rem;
    }
    
    .construction-info-text {
        color: #5A6A85;
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .contact-button {
        display: inline-block;
        background-color: #4F4F52;
        color: white;
        padding: 0.8rem 2rem;
        border-radius: 5px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        margin-top: 1rem;
    }
    
    .contact-button:hover {
        background-color: #3A3A3D;
        transform: translateY(-2px);
    }
    
    /* Animação do ícone em construção */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .animated-icon {
        animation: pulse 2s infinite ease-in-out;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mensagem de página em construção
    st.markdown("""
    <div class="construction-container">
        <div class="construction-icon animated-icon">🏗️</div>
        <div class="construction-title">Página em Construção</div>
        <div class="construction-message">
            Estamos trabalhando para trazer os melhores planos e preços para sua experiência com o Planner Organizer.
            Em breve, você poderá escolher o plano que melhor atende às necessidades do seu negócio.
        </div>
        
        <div class="construction-info">
            <div class="construction-info-title">Enquanto isso...</div>
            <div class="construction-info-text">
                Você pode utilizar nossa versão de demonstração gratuitamente para conhecer todas as funcionalidades do sistema. 
                Basta fazer login com as credenciais de demonstração disponíveis na página inicial.
            </div>
        </div>
        
        <div class="construction-info">
            <div class="construction-info-title">Quer ser notificado quando os planos estiverem disponíveis?</div>
            <div class="construction-info-text">
                Deixe seu e-mail conosco e informaremos assim que nossos planos de assinatura estiverem disponíveis,
                com condições especiais para os primeiros assinantes.
            </div>
        </div>
        
        <a href="mailto:contato@plannerorganizer.com.br" class="contact-button">
            Quero ser notificado
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de informações adicionais
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #5A6A85; font-size: 0.9rem;">
        <p>Para mais informações ou para solicitar um orçamento personalizado, entre em contato com nossa equipe.</p>
        <p>E-mail: contato@plannerorganizer.com.br | Telefone: (11) 4321-1234</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão para voltar à página inicial
    if st.button("Voltar para a página inicial"):
        st.switch_page("app.py")

# Permitir que este arquivo seja executado diretamente
if __name__ == "__main__":
    show()