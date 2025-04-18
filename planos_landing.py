import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer - Planos",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remover o menu hamburguer e rodapé
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Cabeçalho principal com logo e slogan
st.markdown("""
<div style="text-align: center; background: linear-gradient(135deg, #1E366F, #2D8CFF); padding: 2rem 1rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
    <h1 style="font-size: 3rem; margin-bottom: 1rem;">Planner Organizer</h1>
    <p style="font-size: 1.5rem; font-weight: 300;">Transforme sua organização em resultados</p>
</div>
""", unsafe_allow_html=True)

# Seção de planos
st.markdown("## 💼 Comece agora e leve sua organização ao próximo nível!")
st.markdown("<h4 style='color: #666;'>Escolha o plano ideal para o seu momento e comece com 7 dias grátis</h4>", unsafe_allow_html=True)

# Benefícios gerais antes da tabela de planos
st.markdown("### ✅ Benefícios para todos os planos:")
st.markdown("- 📊 Painel financeiro para saber quanto está lucrando")
st.markdown("- 🧾 Propostas automáticas com identidade visual")
st.markdown("- 💰 Precificação profissional para valorizar seu serviço")
st.markdown("- 📈 Relatórios por cliente, projeto e período")
st.markdown("---")

# TABELA DE PLANOS
col1, col2, col3 = st.columns([1, 1.2, 1])  # o do meio ganha mais espaço

with col1:
    st.markdown("### 💡 Plano Mensal")
    st.markdown("**R$ 9,70 / mês**")
    st.markdown("- Todos os recursos")
    st.markdown("- Cancelamento fácil")
    st.markdown("- Ideal para começar")
    
    # Usando tecnica mais moderna de botão
    if st.button("Assinar Mensal", key="btn_mensal", type="primary", use_container_width=True):
        st.success("Você selecionou o plano mensal!")

with col2:
    st.markdown("""
        <div style='border: 2px solid #2d8cff; border-radius: 12px; padding: 10px; background-color: #e6f0ff;'>
        <h3 style='text-align:center;'>🔥 Plano Anual</h3>
        <p style='text-align:center; font-size: 20px;'><strong>R$ 97 / ano</strong></p>
        <p style='text-align:center; color:green;'>💸 Economize 17% comparado ao mensal!</p>
        <ul>
            <li>Acesso total por 12 meses</li>
            <li>Atualizações incluídas</li>
            <li>Suporte prioritário</li>
        </ul>
        <div style='text-align:center; margin-top:10px;'>
            <button style='background-color: #2d8cff; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor:pointer;'>Assinar Anual</button>
        </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Botão nativo para funcionalidade real
    if st.button("Assinar Anual", key="btn_anual", type="primary", use_container_width=True):
        st.success("Você selecionou o plano anual com 17% de desconto!")

with col3:
    st.markdown("### 🏆 Acesso Vitalício")
    st.markdown("**R$ 247,00 uma única vez**")
    st.markdown("- Acesso permanente ao sistema")
    st.markdown("- Sem mensalidade nunca mais")
    st.markdown("- Ideal para quem já decidiu")
    
    if st.button("Comprar Vitalício", key="btn_vitalicio", type="primary", use_container_width=True):
        st.success("Você selecionou o acesso vitalício!")

# Prova social
st.markdown("---")
st.markdown("### 💬 Quem já usa, recomenda:")
col1, col2 = st.columns(2)

with col1:
    st.success("\"Com o PlannerOrganizer fechei 3 contratos em uma semana!\" – Ana L.")

with col2:
    st.info("\"Valeu cada centavo, nunca mais voltei pro Excel!\" – Juliana R.")

# Teste grátis
st.markdown("---")
st.markdown("### 🎁 Comece agora com 7 dias grátis")
st.markdown("Você pode testar todos os recursos antes de decidir. Sem compromisso.")

# Botão grande de teste grátis
st.markdown("""
    <div style='text-align:center; margin:20px 0;'>
        <button style='background-color: #28a745; color: white; border: none; padding: 15px 30px; border-radius: 8px; font-weight: bold; font-size:18px; cursor:pointer;'>
            INICIAR TESTE GRÁTIS
        </button>
    </div>
""", unsafe_allow_html=True)

# Botão Streamlit para funcionalidade real
if st.button("INICIAR TESTE GRÁTIS", key="btn_teste", type="primary", use_container_width=True):
    st.success("Seu período de teste gratuito de 7 dias foi iniciado!")
    st.markdown("Você já pode acessar o sistema completo. [Clique aqui para entrar](/).")

# Informações de contato
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; background-color: #f5f5f5; border-radius: 8px;">
    <h3 style="color: #1E366F;">Ainda tem dúvidas?</h3>
    <p>Entre em contato com nosso suporte:</p>
    <a href="mailto:contato@plannerorganiza.com.br" style="color: #1976D2; text-decoration: none;">contato@plannerorganiza.com.br</a>
    <p style="margin-top: 1rem; font-size: 0.8rem; color: #777;">
        © 2025 Planner Organizer. Todos os direitos reservados.
    </p>
</div>
""", unsafe_allow_html=True)

# Botão para voltar ao Login
st.markdown("---")
if st.button("Voltar ao login", key="btn_voltar"):
    # Aqui redirecionaria para o login
    st.info("Redirecionando para a página de login...")