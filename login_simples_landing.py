import streamlit as st

# Configuração básica da página
st.set_page_config(
    page_title="Planner Organizer", 
    page_icon="📊",
    layout="centered"
)

# Inicializar estado da sessão se necessário
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Título e subtítulo
st.title("Planner Organizer")
st.subheader("Sistema de Gestão Profissional para o seu Negócio")

# Área de login
st.write("### Acesso ao Sistema")
st.write("Experimente o sistema completo de gestão de propostas comerciais")

# Botão de login direto
if st.button("Acessar o Sistema", type="primary", use_container_width=True):
    # Simular autenticação
    st.session_state.authenticated = True
    st.session_state.user = {
        "uid": "admin-demo",
        "email": "admin@example.com",
        "name": "Administrador",
        "role": "admin",
        "demo_mode": True
    }
    
    # Mostrar mensagem de sucesso
    st.success("Login realizado com sucesso!")
    st.info("Redirecionando para o sistema...")
    
    # Redirecionar para o app principal
    st.switch_page("app.py")

# Seção de planos
st.write("## Planos Disponíveis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Mensal**
    
    R$ 9,70 /mês
    
    - Acesso a todas as funcionalidades
    - Suporte via email
    - 7 dias de teste grátis
    - Cancele quando quiser
    """)
    st.button("Assinar Plano Mensal", key="btn_mensal", use_container_width=True)
    
with col2:
    st.markdown("""
    **Anual** (Mais Popular)
    
    R$ 97,00 /ano
    
    - Acesso a todas as funcionalidades
    - Suporte prioritário
    - 7 dias de teste grátis
    - Cancele quando quiser
    - Economia de 2 meses no ano
    """)
    st.button("Assinar Plano Anual", key="btn_anual", use_container_width=True)
    
with col3:
    st.markdown("""
    **Vitalício**
    
    R$ 247,00 pagamento único
    
    - Acesso a todas as funcionalidades
    - Suporte premium
    - Acesso vitalício
    - Acesso a novas funcionalidades
    - Prioridade nas atualizações
    """)
    st.button("Comprar Acesso Vitalício", key="btn_vitalicio", use_container_width=True)

# Rodapé
st.divider()
st.caption("© 2025 Planner Organizer. Todos os direitos reservados.")
st.caption("Dúvidas? Entre em contato: contato@plannerorganizer.com.br")