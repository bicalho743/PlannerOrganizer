import streamlit as st

def mostrar_planos():
    """
    Exibe a seção de planos e preços para o sistema
    """
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
        st.button("Assinar Mensal", key="btn_mensal", type="primary")  # aqui entraria o link do Stripe

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

    with col3:
        st.markdown("### 🏆 Acesso Vitalício")
        st.markdown("**R$ 247,00 uma única vez**")
        st.markdown("- Acesso permanente ao sistema")
        st.markdown("- Sem mensalidade nunca mais")
        st.markdown("- Ideal para quem já decidiu")
        st.button("Comprar Vitalício", key="btn_vitalicio", type="primary")

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