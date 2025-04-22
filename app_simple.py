import streamlit as st

# Configuração inicial da página
st.set_page_config(
    page_title="Planner Organizer - Modo de Manutenção",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo para a página de manutenção
st.markdown("""
<style>
    .maintenance-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem auto;
        max-width: 800px;
    }
    
    .maintenance-icon {
        font-size: 4rem;
        color: #2d8cff;
        margin-bottom: 1.5rem;
    }
    
    .maintenance-title {
        font-size: 2.2rem;
        color: #1E366F;
        margin-bottom: 1.5rem;
        font-weight: 700;
    }
    
    .maintenance-message {
        font-size: 1.1rem;
        color: #495057;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    
    .progress-container {
        width: 100%;
        background-color: #e9ecef;
        border-radius: 8px;
        height: 25px;
        margin-bottom: 1rem;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #2d8cff, #1a56cc);
        border-radius: 8px;
        width: 75%;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
        color: white;
        font-weight: 600;
    }
    
    .estimated-time {
        color: #6c757d;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    
    .contact-info {
        font-size: 0.95rem;
        color: #495057;
        margin-top: 1.5rem;
        background-color: #f1f3f5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d8cff;
    }
</style>
""", unsafe_allow_html=True)

# Conteúdo da página de manutenção
st.markdown("""
<div class="maintenance-container">
    <div class="maintenance-icon">🛠️</div>
    <h1 class="maintenance-title">Sistema em Manutenção</h1>
    <p class="maintenance-message">
        Estamos realizando atualizações importantes para melhorar sua experiência. 
        O sistema estará de volta em breve com melhorias de desempenho e novas funcionalidades.
    </p>
    
    <div class="progress-container">
        <div class="progress-bar">75%</div>
    </div>
    
    <p class="estimated-time">Tempo estimado para conclusão: Em breve</p>
    
    <p>Agradecemos sua compreensão e paciência.</p>
    
    <div class="contact-info">
        <strong>Precisa de ajuda?</strong> Entre em contato através do e-mail 
        <a href="mailto:suporte@plannerorganiza.com.br">suporte@plannerorganiza.com.br</a>
    </div>
</div>
""", unsafe_allow_html=True)

# Informações adicionais
st.markdown("---")
st.markdown("### O que está sendo melhorado?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Performance**
    
    Otimizações que tornarão o sistema mais rápido e responsivo.
    """)
    
with col2:
    st.markdown("""
    **Novas funcionalidades**
    
    Adição de recursos solicitados pelos usuários.
    """)
    
with col3:
    st.markdown("""
    **Segurança**
    
    Atualizações para garantir a proteção dos seus dados.
    """)

# Formulário para notificação
st.markdown("---")
st.markdown("### Receba um aviso quando voltarmos")

with st.form("notification_form"):
    email = st.text_input("Seu e-mail")
    submit = st.form_submit_button("Notificar-me")
    
    if submit and email:
        st.success(f"Obrigado! Enviaremos uma notificação para {email} quando o sistema estiver disponível.")