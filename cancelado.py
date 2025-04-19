"""
Página de cancelamento após o checkout do Stripe
"""
import streamlit as st
import os

def main():
    """
    Página exibida após o cancelamento do checkout
    """
    # Configuração da página
    st.set_page_config(
        page_title="Pagamento Cancelado | Planner Organizer",
        page_icon="❌",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Ocultar o menu hamburger e o rodapé do Streamlit
    hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    
    # CSS para a página
    st.markdown("""
    <style>
    .cancel-container {
        padding: 2rem;
        border-radius: 10px;
        background-color: #fff5f5;
        border: 1px solid #feb2b2;
        text-align: center;
        margin: 2rem auto;
        max-width: 600px;
    }
    .cancel-icon {
        font-size: 5rem;
        color: #e53e3e;
        margin-bottom: 1rem;
    }
    .cancel-title {
        font-size: 1.8rem;
        color: #822727;
        margin-bottom: 1rem;
    }
    .cancel-message {
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 2rem;
    }
    .action-button {
        background-color: #3182ce;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        transition: background-color 0.3s;
        margin: 0 10px;
    }
    .action-button:hover {
        background-color: #2b6cb0;
    }
    .secondary-button {
        background-color: #718096;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        transition: background-color 0.3s;
        margin: 0 10px;
    }
    .secondary-button:hover {
        background-color: #4a5568;
    }
    .button-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container principal
    st.markdown("""
    <div class="cancel-container">
        <div class="cancel-icon">❌</div>
        <h1 class="cancel-title">Pagamento Cancelado</h1>
        <p class="cancel-message">
            Você cancelou o processo de pagamento. Não se preocupe, nenhum valor foi cobrado.
            Quando estiver pronto, você pode tentar novamente ou escolher outro plano.
        </p>
        <div class="button-container">
            <a href="/" class="secondary-button">Voltar ao Início</a>
            <a href="/?show_plans=true" class="action-button">Ver Planos Novamente</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # JavaScript para definir parâmetro na URL
    st.markdown("""
    <script>
        // Função para redirecionar com parâmetro
        function viewPlansAgain() {
            window.location.href = '/?show_plans=true';
            return false;
        }
        
        // Adicionar handler para o botão
        document.addEventListener('DOMContentLoaded', function() {
            const planButton = document.querySelector('a[href="/?show_plans=true"]');
            if (planButton) {
                planButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    viewPlansAgain();
                });
            }
        });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()