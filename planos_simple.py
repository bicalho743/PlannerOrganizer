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
st.title("Planner Organizer")
st.subheader("Transforme sua organização em resultados")

# Seção de planos
st.markdown("## 💼 Comece agora e leve sua organização ao próximo nível!")
st.markdown("Escolha o plano ideal para o seu momento e comece com 7 dias grátis")

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
    
    # Usando técnica mais moderna de botão
    if st.button("Assinar Mensal", key="btn_mensal", type="primary", use_container_width=True):
        st.success("Você selecionou o plano mensal!")

with col2:
    st.info("### 🔥 Plano Anual")
    st.markdown("**R$ 97 / ano**")
    st.markdown("**Economize 17% comparado ao mensal!**")
    st.markdown("- Acesso total por 12 meses")
    st.markdown("- Atualizações incluídas")
    st.markdown("- Suporte prioritário")
    
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

# Botão Streamlit para funcionalidade real
if st.button("INICIAR TESTE GRÁTIS", key="btn_teste", type="primary", use_container_width=True):
    st.success("Seu período de teste gratuito de 7 dias foi iniciado!")
    st.markdown("Você já pode acessar o sistema completo. [Clique aqui para entrar](/).")