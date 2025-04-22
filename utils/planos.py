import streamlit as st
import os
import json
import requests

def mostrar_planos():
    """
    Exibe a seção de planos completa com layout atrativo e botões de ação
    """
    # CSS personalizado para os planos
    st.markdown("""
    <style>
    .planos-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        margin-top: 2rem;
    }
    
    .plano-card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        padding: 25px;
        width: 300px;
        text-align: center;
        transition: transform 0.3s;
    }
    
    .plano-card:hover {
        transform: translateY(-5px);
    }
    
    .plano-destaque {
        border: 2px solid #4CAF50;
        position: relative;
    }
    
    .plano-titulo {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #1E366F;
    }
    
    .plano-preco {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 5px;
    }
    
    .plano-periodo {
        color: #757575;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }
    
    .plano-economia {
        background-color: #1E88E5;
        color: white;
        font-weight: 500;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        position: absolute;
        top: -10px;
        right: 10px;
    }
    
    .plano-badge {
        background-color: #e6fff0;
        color: #00a651;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .plano-botao {
        background: linear-gradient(135deg, #1E88E5, #1E366F);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        margin-top: 20px;
        transition: all 0.3s;
    }
    
    .plano-botao:hover {
        background: linear-gradient(135deg, #0D47A1, #1E366F);
        transform: translateY(-2px);
    }
    
    .plano-beneficios {
        text-align: left;
        margin-top: 20px;
    }
    
    .plano-beneficios ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    .plano-beneficios li {
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
    }
    
    .plano-beneficios li::before {
        content: "✓";
        color: #4CAF50;
        font-weight: bold;
        margin-right: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Seção de planos
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>Planos e Preços</h1>", unsafe_allow_html=True)
    
    # Layout de 3 colunas
    col1, col2, col3 = st.columns(3)
    
    # Checagem da integração com Stripe
    stripe_ready = False
    try:
        # Verificar se a API do Stripe está disponível tentando fazer uma requisição simples
        # para o endpoint de status da aplicação
        stripe_api_url = os.environ.get("STRIPE_API_URL", "http://localhost:8000/api/health")
        response = requests.get(stripe_api_url, timeout=2)
        stripe_ready = response.status_code == 200
    except:
        # Se não conseguir conectar, assumimos que não está pronto
        stripe_ready = False
    
    # Plano Mensal
    with col1:
        st.markdown("""
        <div class="plano-card">
            <div class="plano-titulo">📱 Plano Mensal</div>
            <div class="plano-preco">R$9,70</div>
            <div class="plano-periodo">por mês</div>
            <div class="plano-badge">✨ 7 DIAS DE TESTE GRÁTIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte por e-mail</li>
                    <li>Atualizações mensais</li>
                    <li>Acesso pelo celular e computador</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if stripe_ready:
            st.button("ASSINAR PLANO MENSAL", key="btn_mensal", type="primary", use_container_width=True)
    
    # Plano Anual
    with col2:
        st.markdown("""
        <div class="plano-card plano-destaque">
            <div class="plano-economia">ECONOMIZE 17%</div>
            <div class="plano-titulo">🔥 Plano Anual</div>
            <div class="plano-preco">R$97,00</div>
            <div class="plano-periodo">por ano (R$8,08/mês)</div>
            <div class="plano-badge">✨ 7 DIAS DE TESTE GRÁTIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário</li>
                    <li>Atualizações mensais</li>
                    <li>Acesso pelo celular e computador</li>
                    <li>Funcionalidades avançadas de relatórios</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if stripe_ready:
            st.button("ASSINAR PLANO ANUAL", key="btn_anual", type="primary", use_container_width=True)
    
    # Plano Vitalício
    with col3:
        st.markdown("""
        <div class="plano-card">
            <div class="plano-titulo">💎 Acesso Vitalício</div>
            <div class="plano-preco">R$247,00</div>
            <div class="plano-periodo">pagamento único</div>
            <div class="plano-badge">🏆 MELHOR PARA PROFISSIONAIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário vitalício</li>
                    <li>Atualizações futuras incluídas</li>
                    <li>Acesso pelo celular e computador</li>
                    <li>Funcionalidades avançadas de relatórios</li>
                    <li>Sem mensalidades ou cobranças recorrentes</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if stripe_ready:
            st.button("ADQUIRIR ACESSO VITALÍCIO", key="btn_vitalicio", type="primary", use_container_width=True)
    
    # Seção de perguntas frequentes
    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Perguntas Frequentes</h2>", unsafe_allow_html=True)
    
    # Perguntas e respostas usando expander
    with st.expander("💬 Como funciona o período de teste?"):
        st.write("""
        Você tem 7 dias para testar todas as funcionalidades do sistema sem nenhum compromisso. 
        Se não gostar, é só cancelar antes do final do período de teste e não será cobrado.
        """)
    
    with st.expander("💬 Posso mudar de plano depois?"):
        st.write("""
        Sim! Você pode fazer upgrade ou downgrade do seu plano a qualquer momento.
        Se fizer upgrade para o plano vitalício, suas mensalidades serão automaticamente canceladas.
        """)
    
    with st.expander("💬 Como funciona o pagamento?"):
        st.write("""
        Utilizamos o Stripe, uma das plataformas de pagamento mais seguras do mundo. 
        Aceitamos todos os cartões de crédito principais. Seus dados financeiros são criptografados
        e nunca temos acesso direto às informações do seu cartão.
        """)
    
    with st.expander("💬 O que acontece se eu cancelar a assinatura?"):
        st.write("""
        Você mantém acesso ao sistema até o final do período pago. Após isso, seu acesso será limitado
        até que renove sua assinatura. Seus dados permanecem seguros em nosso sistema por 30 dias
        após o término da assinatura.
        """)
    
    # Seção de garantias
    st.markdown("""
    <div style="background-color: #e6fff0; border-radius: 10px; padding: 20px; margin-top: 2rem; text-align: center;">
        <h3 style="color: #00a651; margin-bottom: 10px;">🔒 Garantia de satisfação</h3>
        <p>Se você não estiver satisfeito com o sistema nos primeiros 30 dias após a compra, devolvemos 100% do seu dinheiro.</p>
        <p style="margin-top: 10px; font-size: 0.9rem;">Seus dados estão seguros e protegidos com criptografia de ponta a ponta.</p>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown("### 💳 Plano Mensal")
        st.markdown("**R$ 9,70 / mês**")
        st.markdown("✨ *7 dias de teste grátis*")
        st.markdown("- Todos os recursos")
        st.markdown("- Suporte por e-mail")
        st.markdown("- Atualizações mensais")
        st.button("COMEÇAR AGORA", key="simples_mensal", use_container_width=True)

    with col2:
        st.markdown("### 🔥 Plano Anual")
        st.markdown("**R$ 97,00 / ano** (economize 17%)")
        st.markdown("✨ *7 dias de teste grátis*")
        st.markdown("- Todos os recursos")
        st.markdown("- Suporte prioritário")
        st.markdown("- Funcionalidades avançadas")
        st.button("MELHOR OPÇÃO", key="simples_anual", type="primary", use_container_width=True)

    with col3:
        st.markdown("### 💎 Vitalício")
        st.markdown("**R$ 247,00** (único)")
        st.markdown("🏆 *Sem mensalidades*")
        st.markdown("- Todos os recursos")
        st.markdown("- Suporte prioritário vitalício")
        st.markdown("- Atualizações futuras incluídas")
        st.button("COMPRAR", key="simples_vitalicio", use_container_width=True)