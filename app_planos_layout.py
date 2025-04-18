"""
Arquivo de exemplo para incorporar a seção de planos diretamente na aplicação principal.
Copie e cole este código diretamente no app.py no local onde deseja exibir os planos.
"""

import os
import streamlit as st

def exemplo_integracao_app():
    """
    Exemplo de como integrar a seção de planos com o app principal.
    Copie o código relevante para seu app.py
    """
    
    # Defina o estilo CSS
    css_planos = """
    <style>
    .main {
        background: linear-gradient(135deg, #f9fafc, #eef5ff);
    }
    
    h1, h2, h3 {
        color: #1E366F;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2D8CFF, #1E366F);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1E66B5, #152A50);
        transform: translateY(-2px);
    }
    
    .featured-plan {
        border: 2px solid #2D8CFF;
        border-radius: 10px;
        padding: 20px;
        position: relative;
        background: linear-gradient(to bottom, #f9fdff, #eaf7ff);
    }
    
    .regular-plan {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        background-color: white;
    }
    
    .plan-price {
        font-size: 2rem;
        font-weight: bold;
        color: #2D8CFF;
    }
    
    .ribbon {
        position: absolute;
        top: -10px;
        right: 10px;
        background: #ff6b6b;
        color: white;
        padding: 5px 15px;
        font-size: 0.8rem;
        font-weight: bold;
        border-radius: 3px;
        transform: rotate(2deg);
    }
    
    .savings {
        background-color: #e6fff0;
        color: #00a651;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .feature-list li {
        margin-bottom: 8px;
    }
    
    .feature-check {
        color: #2D8CFF;
        font-weight: bold;
    }
    </style>
    """
    st.markdown(css_planos, unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>Comece agora e leve sua organização para o próximo nível</h1>", unsafe_allow_html=True)
    
    # Layout de 3 colunas
    col1, col2, col3 = st.columns(3)
    
    # Plano Mensal
    with col1:
        st.markdown("<div class='regular-plan'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>💡 Plano Mensal</h3>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><div class='plan-price'>R$9,70</div><div style='color: #666; margin-bottom: 20px;'>por mês</div></div>", unsafe_allow_html=True)
        
        st.markdown("<ul class='feature-list'>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Acesso a todos os recursos</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Suporte por e-mail</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Cancelamento a qualquer momento</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Ideal para testar o sistema</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        
        if st.button("ASSINAR MENSAL", key="monthly"):
            st.info("Redirecionando para o checkout...")
            # Aqui você pode adicionar a lógica para redirecionar para o checkout
            # Por exemplo, usando o utils.stripe_helper:
            # from utils.stripe_helper import create_checkout_session
            # success, session = create_checkout_session('price_id_mensal')
            # if success:
            #     st.markdown(f"<script>window.location.href = '{session['url']}';</script>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Plano Anual (Destacado)
    with col2:
        st.markdown("<div class='featured-plan'>", unsafe_allow_html=True)
        st.markdown("<div class='ribbon'>RECOMENDADO</div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🔥 Plano Anual</h3>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><div class='plan-price'>R$97,00</div><div style='color: #666; margin-bottom: 10px;'>por ano</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><div class='savings'>ECONOMIZE 17%</div></div>", unsafe_allow_html=True)
        
        st.markdown("<ul class='feature-list'>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Acesso a todos os recursos</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Suporte prioritário</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Atualizações gratuitas</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Treinamento personalizado</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Melhor custo-benefício</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        
        if st.button("ASSINAR ANUAL", key="yearly"):
            st.info("Redirecionando para o checkout...")
            # Lógica de redirecionamento para o plano anual
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Plano Vitalício
    with col3:
        st.markdown("<div class='regular-plan'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🏆 Acesso Vitalício</h3>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><div class='plan-price'>R$247,00</div><div style='color: #666; margin-bottom: 20px;'>pagamento único</div></div>", unsafe_allow_html=True)
        
        st.markdown("<ul class='feature-list'>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Acesso permanente ao sistema</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Suporte prioritário</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Sem mensalidades futuras</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Todas as atualizações inclusas</li>", unsafe_allow_html=True)
        st.markdown("<li><span class='feature-check'>✓</span> Melhor para longo prazo</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        
        if st.button("COMPRAR VITALÍCIO", key="lifetime"):
            st.info("Redirecionando para o checkout...")
            # Lógica de redirecionamento para o plano vitalício
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Planner Organizer | Planos",
        page_icon="favicon.png",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    exemplo_integracao_app()