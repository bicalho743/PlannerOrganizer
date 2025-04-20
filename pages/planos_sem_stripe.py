import streamlit as st
import os
from datetime import datetime, timedelta

# Configuração inicial da página - DEVE ser o primeiro comando Streamlit
st.set_page_config(
    page_title="Planos - Planner Organizer",
    page_icon="📊",
    layout="wide"
)

def exibir_planos_simples():
    """
    Exibe os planos sem integração com o Stripe, apenas para demonstração
    """
    # Verificar se há plano pré-selecionado do app principal
    plano_selecionado = None
    if "plano_selecionado" in st.session_state:
        plano_selecionado = st.session_state.plano_selecionado
        # Limpar o plano selecionado depois de usá-lo
        del st.session_state.plano_selecionado
    
    st.title("Planos - Planner Organizer")
    
    # Mostrar mensagem personalizada se o plano foi pré-selecionado
    if plano_selecionado:
        if plano_selecionado == "mensal":
            st.success("Você selecionou o Plano Mensal! Confira os detalhes abaixo.")
        elif plano_selecionado == "anual":
            st.success("Você selecionou o Plano Anual! Esta é nossa opção mais popular.")
        elif plano_selecionado == "vitalicio":
            st.success("Você selecionou o Plano Vitalício! Esta é a melhor opção para longo prazo.")
    
    st.markdown("""
    ## Comece agora e leve sua organização para o próximo nível!
    
    Escolha o plano ideal para seu negócio. Todas as opções incluem acesso a todos os recursos.
    """)
    
    # CSS para estilizar os cards
    st.markdown("""
    <style>
    .pricing-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        transition: transform 0.3s, box-shadow 0.3s;
        background: white;
    }
    
    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    .pricing-card h3 {
        color: #1E88E5;
        font-size: 1.5rem;
        margin-bottom: 10px;
    }
    
    .pricing-card .price {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 15px 0;
    }
    
    .pricing-card .features {
        margin: 20px 0;
    }
    
    .pricing-card .feature-item {
        margin: 8px 0;
    }
    
    .pricing-button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 15px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        transition: background-color 0.3s;
    }
    
    .pricing-button:hover {
        background-color: #1565C0;
    }
    
    .highlight-card {
        border: 3px solid #ffd700;
        transform: scale(1.03);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Criar os cards de preços
    col1, col2, col3 = st.columns(3)
    
    # Plano Mensal
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3>Plano Mensal</h3>
            <div class="price">R$ 9,70 / mês</div>
            <div class="features">
                <p class="feature-item">✅ 7 dias de teste gratuito</p>
                <p class="feature-item">✅ Acesso a todos os recursos</p>
                <p class="feature-item">✅ Suporte por email</p>
                <p class="feature-item">✅ Armazenamento ilimitado</p>
                <p class="feature-item">✅ Exportação de relatórios</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão nativo do Streamlit em vez de HTML/JavaScript
        if st.button("Assinar Plano Mensal", key="mensal_btn", type="primary", use_container_width=True):
            st.success("Funcionalidade em implementação. Entre em contato para assinar.")
            st.balloons()  # Efeito de balões para melhorar a experiência
    
    # Plano Anual (destacado)
    with col2:
        st.markdown("""
        <div class="pricing-card highlight-card">
            <div style="position: absolute; top: -12px; right: 20px; background: #ffd700; padding: 5px 10px; border-radius: 15px; font-weight: bold;">Mais Popular</div>
            <h3>Plano Anual</h3>
            <div class="price">R$ 97,00 / ano</div>
            <div style="color: green; font-weight: bold;">Economize 17%</div>
            <div class="features">
                <p class="feature-item">✅ 7 dias de teste gratuito</p>
                <p class="feature-item">✅ Acesso a todos os recursos</p>
                <p class="feature-item">✅ Suporte prioritário</p>
                <p class="feature-item">✅ Armazenamento ilimitado</p>
                <p class="feature-item">✅ Exportação de relatórios</p>
                <p class="feature-item">✅ Sem preocupação mensal</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão nativo do Streamlit destacado
        st.markdown('<style>div[data-testid="stButton"] button {background-color: #FFA500;}</style>', unsafe_allow_html=True)
        if st.button("Melhor Valor! Assinar Plano Anual", key="anual_btn", type="primary", use_container_width=True):
            st.success("Funcionalidade em implementação. Entre em contato para assinar.")
            st.balloons()
    
    # Plano Vitalício
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3>Plano Vitalício</h3>
            <div class="price">R$ 247,00</div>
            <div style="color: green; font-weight: bold;">Pagamento único</div>
            <div class="features">
                <p class="feature-item">✅ Acesso vitalício</p>
                <p class="feature-item">✅ Sem mensalidades</p>
                <p class="feature-item">✅ Acesso a todos os recursos</p>
                <p class="feature-item">✅ Suporte prioritário vitalício</p>
                <p class="feature-item">✅ Atualizações gratuitas</p>
                <p class="feature-item">✅ 100% sem recorrência</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão nativo do Streamlit para o plano vitalício
        if st.button("Adquirir Acesso Vitalício", key="vitalicio_btn", type="primary", use_container_width=True):
            st.success("Funcionalidade em implementação. Entre em contato para adquirir.")
            st.balloons()
    
    # Informações de contato e FAQ
    st.markdown("""
    ## Informações Adicionais
    
    Para adquirir um dos planos ou para mais informações, entre em contato conosco pelo email: **contato@plannerorganizer.com.br**
    
    ### Perguntas Frequentes
    
    **Como funciona o período de teste gratuito?**  
    Os planos mensais e anuais incluem 7 dias de teste gratuito. Durante esse período, você terá acesso a todas as funcionalidades do sistema sem custo.
    
    **Posso mudar de plano depois?**  
    Sim, você pode atualizar seu plano a qualquer momento. Se estiver em um plano mensal, pode mudar para o anual ou vitalício com facilidade.
    
    **Como funciona o pagamento?**  
    No momento estamos implementando nossa solução de pagamentos. Por enquanto, entre em contato diretamente para processar seu pagamento.
    
    **O que acontece quando expira meu período?**  
    Após o término do seu período de assinatura, você terá acesso limitado ao sistema. Para continuar utilizando todas as funcionalidades, será necessário renovar sua assinatura.
    """)

# Chamada principal
exibir_planos_simples()