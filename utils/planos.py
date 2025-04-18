import streamlit as st

def mostrar_planos(com_titulo=True, com_prova_social=True, com_teste_gratis=True, com_destaque_plano_medio=True, stripe_ready=True):
    """
    Exibe a seção de planos e preços completa para o sistema.
    
    Args:
        com_titulo (bool): Se True, mostra o título e subtítulo da seção
        com_prova_social (bool): Se True, mostra os depoimentos dos clientes
        com_teste_gratis (bool): Se True, mostra a seção de teste grátis
        com_destaque_plano_medio (bool): Se True, destaca visualmente o plano do meio (Anual)
        stripe_ready (bool): Se True, adiciona funcionalidade dos botões para integração com Stripe
    """
    # CSS adicional para os cartões de planos
    st.markdown("""
    <style>
    .plano-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .plano-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.15);
    }
    
    .plano-destaque {
        background: linear-gradient(to bottom, #f9fdff, #eaf7ff);
        border: 2px solid #2d8cff !important;
        position: relative;
        overflow: hidden;
    }
    
    .plano-destaque:before {
        content: "RECOMENDADO";
        position: absolute;
        top: 10px;
        right: -30px;
        background: #ff6b6b;
        color: white;
        padding: 5px 40px;
        font-size: 10px;
        font-weight: bold;
        transform: rotate(45deg);
    }
    
    .plano-titulo {
        font-size: 24px;
        font-weight: 700;
        color: #1E366F;
        margin-bottom: 10px;
        text-align: center;
    }
    
    .plano-preco {
        font-size: 36px;
        font-weight: 800;
        color: #2d8cff;
        text-align: center;
        margin-bottom: 5px;
    }
    
    .plano-periodo {
        color: #666;
        text-align: center;
        margin-bottom: 20px;
        font-size: 14px;
    }
    
    .plano-destaque .plano-preco {
        color: #1E366F;
    }
    
    .plano-economia {
        background-color: #e6fff0;
        color: #00a651;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-align: center;
        margin: 0 auto 20px auto;
        max-width: 80%;
    }
    
    .plano-beneficios {
        margin-bottom: 20px;
        flex-grow: 1;
    }
    
    .plano-beneficios ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    .plano-beneficios li {
        margin-bottom: 12px;
        position: relative;
        padding-left: 28px;
    }
    
    .plano-beneficios li:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #2d8cff;
        font-weight: bold;
    }
    
    .plano-destaque .plano-beneficios li:before {
        color: #00a651;
    }
    
    .plano-button {
        background: linear-gradient(135deg, #2d8cff, #1e66b5);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        width: 100%;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(45,140,255,0.2);
    }
    
    .plano-button:hover {
        background: linear-gradient(135deg, #1e66b5, #154c8c);
        box-shadow: 0 6px 10px rgba(45,140,255,0.3);
    }
    
    .plano-destaque .plano-button {
        background: linear-gradient(135deg, #ff6b6b, #e83e3e);
        box-shadow: 0 4px 6px rgba(255,107,107,0.2);
    }
    
    .plano-destaque .plano-button:hover {
        background: linear-gradient(135deg, #e83e3e, #cf2b2b);
        box-shadow: 0 6px 10px rgba(255,107,107,0.3);
    }
    
    .beneficios-titulo {
        text-align: center;
        font-weight: 700;
        margin-bottom: 30px;
        color: #1E366F;
    }
    
    .beneficios-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .beneficio-item {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .beneficio-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    .beneficio-icone {
        font-size: 32px;
        margin-bottom: 10px;
        color: #2d8cff;
    }
    
    .beneficio-titulo {
        font-weight: 600;
        color: #1E366F;
        margin-bottom: 5px;
    }
    
    .beneficio-descricao {
        color: #666;
        font-size: 14px;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .plano-card {
            margin-bottom: 30px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Seção de planos - Título
    if com_titulo:
        st.markdown("<h2 style='text-align: center; color: #1E366F; margin-top: 50px; margin-bottom: 10px;'>Escolha o Plano Ideal Para o Seu Negócio</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666; font-size: 18px; margin-bottom: 40px;'>Invista no crescimento da sua organização com nossos planos acessíveis</p>", unsafe_allow_html=True)
    
    # Benefícios gerais antes da tabela de planos
    st.markdown("<div class='beneficios-titulo'>Todos os planos incluem:</div>", unsafe_allow_html=True)
    
    # Grid de benefícios visuais
    st.markdown("""
    <div class='beneficios-grid'>
        <div class='beneficio-item'>
            <div class='beneficio-icone'>📊</div>
            <div class='beneficio-titulo'>Painel Financeiro</div>
            <div class='beneficio-descricao'>Controle completo das suas finanças</div>
        </div>
        <div class='beneficio-item'>
            <div class='beneficio-icone'>🧾</div>
            <div class='beneficio-titulo'>Propostas Profissionais</div>
            <div class='beneficio-descricao'>Modelo personalizado com sua marca</div>
        </div>
        <div class='beneficio-item'>
            <div class='beneficio-icone'>💰</div>
            <div class='beneficio-titulo'>Precificação Inteligente</div>
            <div class='beneficio-descricao'>Calcule valores com precisão</div>
        </div>
        <div class='beneficio-item'>
            <div class='beneficio-icone'>📈</div>
            <div class='beneficio-titulo'>Relatórios Avançados</div>
            <div class='beneficio-descricao'>Dados para decisões estratégicas</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # TABELA DE PLANOS
    col1, col2, col3 = st.columns([1, 1.2, 1])  # o do meio ganha mais espaço

    with col1:
        plano_mensal = f"""
        <div class="plano-card">
            <div class="plano-titulo">💡 Plano Mensal</div>
            <div class="plano-preco">R$9,70</div>
            <div class="plano-periodo">por mês</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte por e-mail</li>
                    <li>Cancelamento a qualquer momento</li>
                    <li>Ideal para testar o sistema</li>
                </ul>
            </div>
            <button class="plano-button">ASSINAR MENSAL</button>
        </div>
        """
        st.markdown(plano_mensal, unsafe_allow_html=True)
        
        # Botão funcional para Stripe (opcional)
        if stripe_ready:
            btn_mensal = st.button("Assinar Mensal", key="btn_mensal", type="primary", use_container_width=True)
            if btn_mensal:
                st.success("Redirecionando para pagamento do plano mensal...")

    with col2:
        plano_class = "plano-card plano-destaque" if com_destaque_plano_medio else "plano-card"
        plano_anual = f"""
        <div class="{plano_class}">
            <div class="plano-titulo">🔥 Plano Anual</div>
            <div class="plano-preco">R$97,00</div>
            <div class="plano-periodo">por ano</div>
            <div class="plano-economia">ECONOMIZE 17%</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário</li>
                    <li>Atualizações gratuitas</li>
                    <li>Treinamento personalizado</li>
                    <li>Melhor custo-benefício</li>
                </ul>
            </div>
            <button class="plano-button">ASSINAR ANUAL</button>
        </div>
        """
        st.markdown(plano_anual, unsafe_allow_html=True)
        
        # Botão funcional para Stripe (opcional)
        if stripe_ready:
            btn_anual = st.button("Assinar Anual", key="btn_anual", type="primary", use_container_width=True)
            if btn_anual:
                st.success("Redirecionando para pagamento do plano anual...")

    with col3:
        plano_vitalicio = f"""
        <div class="plano-card">
            <div class="plano-titulo">🏆 Acesso Vitalício</div>
            <div class="plano-preco">R$247,00</div>
            <div class="plano-periodo">pagamento único</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso permanente ao sistema</li>
                    <li>Suporte prioritário</li>
                    <li>Sem mensalidades futuras</li>
                    <li>Todas as atualizações inclusas</li>
                    <li>Melhor para longo prazo</li>
                </ul>
            </div>
            <button class="plano-button">COMPRAR VITALÍCIO</button>
        </div>
        """
        st.markdown(plano_vitalicio, unsafe_allow_html=True)
        
        # Botão funcional para Stripe (opcional)
        if stripe_ready:
            btn_vitalicio = st.button("Comprar Vitalício", key="btn_vitalicio", type="primary", use_container_width=True)
            if btn_vitalicio:
                st.success("Redirecionando para pagamento do plano vitalício...")
    
    # Prova social
    if com_prova_social:
        st.markdown("<h3 style='text-align: center; margin-top: 50px; color: #1E366F;'>O que nossos clientes dizem</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f0f8ff, #e1efff); padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                <p style="font-style: italic; color: #1E366F; font-size: 16px;">
                    "Com o PlannerOrganizer fechei 3 contratos em uma semana! A interface é intuitiva e os relatórios impressionam meus clientes."
                </p>
                <p style="text-align: right; font-weight: 600; color: #2d8cff;">— Ana L., Personal Organizer</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #e1efff, #d8eaff); padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                <p style="font-style: italic; color: #1E366F; font-size: 16px;">
                    "Valeu cada centavo, nunca mais voltei pro Excel! Meu negócio cresceu 35% desde que comecei a usar o sistema."
                </p>
                <p style="text-align: right; font-weight: 600; color: #2d8cff;">— Juliana R., Home Organizer</p>
            </div>
            """, unsafe_allow_html=True)

    # Teste grátis
    if com_teste_gratis:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1E366F, #2d8cff); padding: 30px; border-radius: 15px; text-align: center; margin-top: 50px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin-bottom: 15px;">Não precisa decidir agora</h2>
            <p style="color: white; font-size: 18px; margin-bottom: 25px;">
                Experimente o Planner Organizer gratuitamente por 7 dias.<br>
                Sem compromisso. Cancele quando quiser.
            </p>
            <button style="background-color: white; color: #1E366F; border: none; padding: 15px 40px; border-radius: 30px; font-weight: bold; font-size: 18px; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                INICIAR PERÍODO GRATUITO
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão funcional para Stripe (opcional)
        if stripe_ready:
            st.button("INICIAR PERÍODO GRATUITO", key="btn_teste", type="primary", use_container_width=True)

def mostrar_planos_simples():
    """
    Versão simplificada da seção de planos, para usar em páginas com espaço limitado
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
        st.button("Assinar Mensal", key="btn_mensal_simples", type="primary")  # aqui entraria o link do Stripe

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
        
        st.button("Assinar Anual", key="btn_anual_simples", type="primary")

    with col3:
        st.markdown("### 🏆 Acesso Vitalício")
        st.markdown("**R$ 247,00 uma única vez**")
        st.markdown("- Acesso permanente ao sistema")
        st.markdown("- Sem mensalidade nunca mais")
        st.markdown("- Ideal para quem já decidiu")
        st.button("Comprar Vitalício", key="btn_vitalicio_simples", type="primary")

    # Prova social
    st.markdown("---")
    st.markdown("### 💬 Quem já usa, recomenda:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("\"Com o PlannerOrganizer fechei 3 contratos em uma semana!\" – Ana L.")
    
    with col2:
        st.info("\"Valeu cada centavo, nunca mais voltei pro Excel!\" – Juliana R.")