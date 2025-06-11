import streamlit as st
import os

# Configuração da página
try:
    st.set_page_config(
        page_title="Planos Planner Organizer",
        page_icon="💎",
        layout="wide"
    )
except:
    pass

# CSS customizado para a landing page
st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #1E366F;
    margin-bottom: 2rem;
}
.plan-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin: 1rem 0;
    border: 2px solid #f0f2f6;
}
.plan-price {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1E366F;
    text-align: center;
}
.plan-title {
    font-size: 1.5rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 1rem;
    color: #262730;
}
.feature-list {
    list-style: none;
    padding: 0;
}
.feature-list li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #f0f2f6;
}
.feature-list li:before {
    content: "✓ ";
    color: #28a745;
    font-weight: bold;
}
.cta-button {
    background: #1E366F;
    color: white;
    padding: 1rem 2rem;
    border: none;
    border-radius: 5px;
    font-size: 1.1rem;
    cursor: pointer;
    width: 100%;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<h1 class="main-header">💎 Planos Planner Organizer</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Escolha o plano ideal para o seu negócio de organização</p>', unsafe_allow_html=True)

# Layout dos planos
col1, col2, col3 = st.columns(3)

# Plano Básico
with col1:
    st.markdown("""
    <div class="plan-card">
        <div class="plan-title">Plano Básico</div>
        <div class="plan-price">R$ 49</div>
        <p style="text-align: center; color: #666;">por mês</p>
        <ul class="feature-list">
            <li>Até 50 clientes</li>
            <li>Até 100 propostas</li>
            <li>Relatórios básicos</li>
            <li>Suporte por email</li>
            <li>1 usuário</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Escolher Básico", key="basico", use_container_width=True):
        st.success("Plano Básico selecionado! Redirecionando para pagamento...")

# Plano Profissional
with col2:
    st.markdown("""
    <div class="plan-card" style="border-color: #1E366F; transform: scale(1.05);">
        <div class="plan-title" style="color: #1E366F;">Plano Profissional ⭐</div>
        <div class="plan-price">R$ 99</div>
        <p style="text-align: center; color: #666;">por mês</p>
        <ul class="feature-list">
            <li>Clientes ilimitados</li>
            <li>Propostas ilimitadas</li>
            <li>Relatórios avançados</li>
            <li>Suporte prioritário</li>
            <li>Até 3 usuários</li>
            <li>Backup automático</li>
            <li>Integração com WhatsApp</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Escolher Profissional", key="profissional", use_container_width=True):
        st.success("Plano Profissional selecionado! Redirecionando para pagamento...")

# Plano Enterprise
with col3:
    st.markdown("""
    <div class="plan-card">
        <div class="plan-title">Plano Enterprise</div>
        <div class="plan-price">R$ 199</div>
        <p style="text-align: center; color: #666;">por mês</p>
        <ul class="feature-list">
            <li>Recursos ilimitados</li>
            <li>Multi-empresa</li>
            <li>API personalizada</li>
            <li>Suporte 24/7</li>
            <li>Usuários ilimitados</li>
            <li>Treinamento incluído</li>
            <li>Customizações</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Escolher Enterprise", key="enterprise", use_container_width=True):
        st.success("Plano Enterprise selecionado! Entre em contato para configuração personalizada.")

# Seção de benefícios
st.markdown("---")
st.markdown("### 🎯 Por que escolher o Planner Organizer?")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **📊 Gestão Completa**
    
    Controle total sobre clientes, propostas e financeiro em uma única plataforma.
    """)

with col2:
    st.markdown("""
    **🔒 Segurança**
    
    Seus dados protegidos com criptografia e backup automático na nuvem.
    """)

with col3:
    st.markdown("""
    **📱 Acesso Mobile**
    
    Interface responsiva para gerenciar seu negócio de qualquer lugar.
    """)

with col4:
    st.markdown("""
    **🎓 Suporte**
    
    Equipe especializada pronta para ajudar no crescimento do seu negócio.
    """)

# Call to action final
st.markdown("---")
st.markdown("### 🚀 Comece hoje mesmo!")
st.markdown("Teste grátis por 14 dias, sem compromisso. Cancele quando quiser.")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🎯 Iniciar Teste Gratuito", use_container_width=True, type="primary"):
        st.balloons()
        st.success("Teste gratuito ativado! Bem-vindo ao Planner Organizer!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>💎 Planner Organizer - Transformando personal organizers em empresários de sucesso</p>
    <p>📧 contato@plannerorganizer.com.br | 📞 (11) 99999-9999</p>
</div>
""", unsafe_allow_html=True)