"""
Página de planos minimalista para o Planner Organizer
"""
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planos - Planner Organizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-color: #1E366F;
        --secondary-color: #2E7DE6;
        --accent-color: #4FADE0;
        --bg-color: #F8F9FA;
        --text-color: #333;
        --light-text-color: #6c757d;
        --border-color: #e0e0e0;
    }
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    h1 {
        color: var(--primary-color);
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: var(--primary-color);
        font-size: 1.8rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    p {
        color: var(--text-color);
        font-size: 1rem;
        line-height: 1.6;
    }
    
    .subtitle {
        color: var(--light-text-color);
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    .plans-container {
        display: flex;
        gap: 24px;
        margin-top: 2rem;
        flex-wrap: wrap;
    }
    
    .plan-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.05);
        padding: 1.8rem;
        flex: 1;
        min-width: 300px;
        border-top: 5px solid var(--secondary-color);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .plan-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.08);
    }
    
    .plan-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .plan-price {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--secondary-color);
        margin-bottom: 0.5rem;
    }
    
    .plan-period {
        font-size: 0.9rem;
        color: var(--light-text-color);
        margin-bottom: 1.5rem;
    }
    
    .plan-features {
        margin: 1.5rem 0;
    }
    
    .feature-item {
        display: flex;
        align-items: center;
        margin-bottom: 0.8rem;
    }
    
    .feature-icon {
        color: var(--secondary-color);
        margin-right: 10px;
        font-size: 1.2rem;
    }
    
    .feature-text {
        color: var(--text-color);
        font-size: 0.95rem;
    }
    
    .cta-button {
        display: inline-block;
        background: linear-gradient(90deg, var(--secondary-color), var(--accent-color));
        color: white;
        padding: 12px 24px;
        border-radius: 50px;
        font-weight: 600;
        text-align: center;
        text-decoration: none;
        margin-top: 1rem;
        transition: all 0.2s ease;
        border: none;
        cursor: pointer;
        width: 100%;
    }
    
    .cta-button:hover {
        background: linear-gradient(90deg, var(--accent-color), var(--secondary-color));
        box-shadow: 0 5px 15px rgba(46, 125, 230, 0.3);
        transform: translateY(-2px);
    }
    
    .premium-card {
        border-top-color: #FFD700;
        position: relative;
        overflow: hidden;
    }
    
    .premium-card .plan-price {
        color: #FFB100;
    }
    
    .premium-card .feature-icon {
        color: #FFB100;
    }
    
    .premium-card .cta-button {
        background: linear-gradient(90deg, #FFB100, #FFC93C);
    }
    
    .premium-card .cta-button:hover {
        background: linear-gradient(90deg, #FFC93C, #FFB100);
        box-shadow: 0 5px 15px rgba(255, 177, 0, 0.3);
    }
    
    .popular-tag {
        position: absolute;
        top: 20px;
        right: -35px;
        background: #FFD700;
        color: #333;
        padding: 5px 40px;
        font-size: 0.8rem;
        font-weight: 600;
        transform: rotate(45deg);
    }
    
    .enterprise-card {
        border-top-color: #6C63FF;
    }
    
    .enterprise-card .plan-price {
        color: #6C63FF;
    }
    
    .enterprise-card .feature-icon {
        color: #6C63FF;
    }
    
    .enterprise-card .cta-button {
        background: linear-gradient(90deg, #6C63FF, #8F85FF);
    }
    
    .enterprise-card .cta-button:hover {
        background: linear-gradient(90deg, #8F85FF, #6C63FF);
        box-shadow: 0 5px 15px rgba(108, 99, 255, 0.3);
    }
    
    .section-heading {
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem 0;
        font-size: 0.9rem;
        color: var(--light-text-color);
    }
    
    .faq-container {
        margin-top: 4rem;
    }
    
    .faq-item {
        margin-bottom: 1.5rem;
        background: white;
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    
    .faq-question {
        font-weight: 600;
        font-size: 1.1rem;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .faq-answer {
        font-size: 0.95rem;
        color: var(--text-color);
    }
    
    @media screen and (max-width: 768px) {
        .plans-container {
            flex-direction: column;
        }
        
        .plan-card {
            width: 100%;
            min-width: unset;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1>Planos e Preços</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Escolha o plano ideal para o seu negócio</p>", unsafe_allow_html=True)

# Planos
st.markdown("<div class='plans-container'>", unsafe_allow_html=True)

# Plano Básico
st.markdown("""
<div class='plan-card'>
    <div class='plan-title'>Básico</div>
    <div class='plan-price'>R$ 49,90</div>
    <div class='plan-period'>por mês, cobrança mensal</div>
    
    <div class='plan-features'>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Até 50 clientes</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Até 100 propostas por mês</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Módulo financeiro básico</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Controle de propostas</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Suporte por email</span>
        </div>
    </div>
    
    <button class='cta-button'>Começar Agora</button>
</div>
""", unsafe_allow_html=True)

# Plano Premium
st.markdown("""
<div class='plan-card premium-card'>
    <div class='popular-tag'>POPULAR</div>
    <div class='plan-title'>Premium</div>
    <div class='plan-price'>R$ 89,90</div>
    <div class='plan-period'>por mês, cobrança mensal</div>
    
    <div class='plan-features'>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Clientes ilimitados</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Propostas ilimitadas</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Módulo financeiro completo</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Relatórios avançados</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Integração com sistemas externos</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Suporte prioritário</span>
        </div>
    </div>
    
    <button class='cta-button'>Escolher Premium</button>
</div>
""", unsafe_allow_html=True)

# Plano Enterprise
st.markdown("""
<div class='plan-card enterprise-card'>
    <div class='plan-title'>Enterprise</div>
    <div class='plan-price'>R$ 199,90</div>
    <div class='plan-period'>por mês, cobrança mensal</div>
    
    <div class='plan-features'>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Tudo do plano Premium</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Múltiplos usuários</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Controle de permissões</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>API completa para integração</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Suporte 24/7 dedicado</span>
        </div>
        <div class='feature-item'>
            <span class='feature-icon'>✓</span>
            <span class='feature-text'>Personalização de marca</span>
        </div>
    </div>
    
    <button class='cta-button'>Falar com Consultor</button>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Seção de FAQ
st.markdown("<h2>Perguntas Frequentes</h2>", unsafe_allow_html=True)

st.markdown("<div class='faq-container'>", unsafe_allow_html=True)

# FAQ 1
st.markdown("""
<div class='faq-item'>
    <div class='faq-question'>Como funciona o período de teste?</div>
    <div class='faq-answer'>
        Oferecemos um período de teste gratuito de 14 dias para todos os planos. Durante este período, você terá acesso a todos os recursos do plano escolhido. Não é necessário cartão de crédito para começar o teste.
    </div>
</div>
""", unsafe_allow_html=True)

# FAQ 2
st.markdown("""
<div class='faq-item'>
    <div class='faq-question'>Posso mudar de plano depois?</div>
    <div class='faq-answer'>
        Sim, você pode fazer upgrade ou downgrade do seu plano a qualquer momento. As mudanças entram em vigor imediatamente, e o valor será ajustado proporcionalmente ao período restante da sua assinatura.
    </div>
</div>
""", unsafe_allow_html=True)

# FAQ 3
st.markdown("""
<div class='faq-item'>
    <div class='faq-question'>Como funciona o suporte técnico?</div>
    <div class='faq-answer'>
        Todos os planos incluem suporte técnico por email. Os planos Premium e Enterprise têm acesso a suporte prioritário com tempo de resposta garantido de até 6 horas em dias úteis. O plano Enterprise conta com suporte 24/7 por email, chat e telefone.
    </div>
</div>
""", unsafe_allow_html=True)

# FAQ 4
st.markdown("""
<div class='faq-item'>
    <div class='faq-question'>Existe alguma cobrança adicional?</div>
    <div class='faq-answer'>
        Não há cobranças ocultas. O valor mensal cobre todas as funcionalidades listadas para cada plano. Apenas serviços adicionais específicos, como personalização avançada ou integrações sob medida, podem ter custos extras, mas sempre com orçamento prévio.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div class='footer'>
    © 2025 Planner Organizer. Todos os direitos reservados.<br>
    Dúvidas? Entre em contato: contato@plannerorganiza.com.br
</div>
""", unsafe_allow_html=True)

def main():
    """Função principal - apenas para manter compatibilidade"""
    pass

if __name__ == "__main__":
    main()