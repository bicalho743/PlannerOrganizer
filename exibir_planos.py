"""
Módulo para exibição de planos sem dependências externas
Este arquivo existe para ser importado por outros módulos sem
causar problemas de set_page_config duplicado
"""
import streamlit as st
import random
import time
import json
import requests
from datetime import datetime

def criar_checkout_session(plan_id):
    """
    Cria uma sessão de checkout do Stripe para um plano específico
    
    Args:
        plan_id (str): ID do plano (monthly, yearly, lifetime)
        
    Returns:
        dict: Resposta da API com session_id e URL
    """
    # Gerando parâmetros aleatórios para evitar cache
    timestamp = int(time.time())
    random_param = random.randint(1000, 9999)
    
    try:
        # Tentar conectar à API Stripe
        response = requests.post(
            "http://0.0.0.0:8000/api/checkout-session",
            json={
                "price_id": f"price_{plan_id}_{timestamp}_{random_param}",  # Simular price_id
                "success_url": f"http://0.0.0.0:5000/success?t={timestamp}_{random_param}",
                "cancel_url": f"http://0.0.0.0:5000/cancel?t={timestamp}_{random_param}",
                "mode": "subscription" if plan_id in ["monthly", "yearly"] else "payment",
                "customer_email": f"test_{timestamp}_{random_param}@example.com",
                "metadata": {
                    "plan_id": plan_id,
                    "timestamp": str(timestamp),
                    "random": str(random_param)
                }
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback para modo de simulação
            st.warning(f"Não foi possível conectar ao Stripe (código {response.status_code}). Usando modo de simulação.")
            return {
                "id": f"cs_{timestamp}_{random_param}",
                "url": f"https://checkout.stripe.com/pay/cs_{timestamp}_{random_param}"
            }
            
    except Exception as e:
        # Fallback para modo de simulação em caso de erro
        st.warning(f"Erro ao conectar ao Stripe: {str(e)}. Usando modo de simulação.")
        return {
            "id": f"cs_{timestamp}_{random_param}",
            "url": f"https://checkout.stripe.com/pay/cs_{timestamp}_{random_param}"
        }

def exibir_planos_simples():
    """Função simplificada para exibir os planos na página de login"""
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
        margin-bottom: 20px;
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
    </style>
    """, unsafe_allow_html=True)
    
    # TABELA DE PLANOS
    col1, col2, col3 = st.columns([1, 1.2, 1])  # o do meio ganha mais espaço

    # Adicionando timestamp aleatório para evitar preenchimento automático
    timestamp = int(time.time())
    random_param = random.randint(1000, 9999)

    # URLs para redirecionamento
    base_url = "http://0.0.0.0:5000"
    success_url = f"{base_url}/success?session_id={{CHECKOUT_SESSION_ID}}&t={timestamp}_{random_param}"
    cancel_url = f"{base_url}/cancel?t={timestamp}_{random_param}"

    with col1:
        # Cartão para Plano Mensal
        st.markdown("""
        <div class="plano-card">
            <div class="plano-titulo">💳 Plano Mensal</div>
            <div class="plano-preco">R$9,70</div>
            <div class="plano-periodo">por mês</div>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 12px; font-weight: bold;">✨ 7 DIAS DE TESTE GRÁTIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte por e-mail</li>
                    <li>Cancelamento a qualquer momento</li>
                    <li>Ideal para testar o sistema</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão para checkout do plano mensal
        button_mensal = st.button("Assinar Plano Mensal", type="primary", use_container_width=True, key=f"mensal_{timestamp}_{random_param}")
        if button_mensal:
            with st.spinner("Conectando ao servidor de pagamentos..."):
                try:
                    # Criar a sessão de checkout
                    checkout_session = criar_checkout_session("monthly")
                    
                    # Se for bem sucedido, redireciona
                    if checkout_session and "url" in checkout_session:
                        st.success("Redirecionando para o checkout...")
                        # Link HTML para abrir em nova aba
                        st.markdown(f"""
                        <a href="{checkout_session['url']}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #2d8cff; color: white; border: none; padding: 10px 20px; 
                            border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">
                                Clique aqui para ir para o checkout
                            </button>
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Não foi possível criar a sessão de checkout. Tente novamente.")
                except Exception as e:
                    st.error(f"Erro ao processar pagamento: {str(e)}")

    with col2:
        # Cartão para Plano Anual (com destaque)
        st.markdown("""
        <div class="plano-card plano-destaque">
            <div class="plano-titulo">📆 Plano Anual</div>
            <div class="plano-preco">R$97,00</div>
            <div class="plano-periodo">por ano</div>
            <div class="plano-economia">ECONOMIZE 17%</div>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 12px; font-weight: bold;">✨ 7 DIAS DE TESTE GRÁTIS</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso a todos os recursos</li>
                    <li>Suporte prioritário</li>
                    <li>Atualizações gratuitas</li>
                    <li>Treinamento personalizado</li>
                    <li>Melhor custo-benefício</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão para checkout do plano anual
        button_anual = st.button("Assinar Plano Anual", type="primary", use_container_width=True, key=f"anual_{timestamp}_{random_param}")
        if button_anual:
            with st.spinner("Conectando ao servidor de pagamentos..."):
                try:
                    # Criar a sessão de checkout
                    checkout_session = criar_checkout_session("yearly")
                    
                    # Se for bem sucedido, redireciona
                    if checkout_session and "url" in checkout_session:
                        st.success("Redirecionando para o checkout...")
                        # Link HTML para abrir em nova aba
                        st.markdown(f"""
                        <a href="{checkout_session['url']}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #2d8cff; color: white; border: none; padding: 10px 20px; 
                            border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">
                                Clique aqui para ir para o checkout
                            </button>
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Não foi possível criar a sessão de checkout. Tente novamente.")
                except Exception as e:
                    st.error(f"Erro ao processar pagamento: {str(e)}")

    with col3:
        # Cartão para Plano Vitalício
        st.markdown("""
        <div class="plano-card">
            <div class="plano-titulo">💎 Acesso Vitalício</div>
            <div class="plano-preco">R$247,00</div>
            <div class="plano-periodo">pagamento único</div>
            <div class="plano-economia">MELHOR VALOR A LONGO PRAZO</div>
            <div class="plano-beneficios">
                <ul>
                    <li>Acesso permanente ao sistema</li>
                    <li>Suporte prioritário</li>
                    <li>Sem mensalidades futuras</li>
                    <li>Todas as atualizações inclusas</li>
                    <li>Melhor para longo prazo</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão para checkout do plano vitalício
        button_vitalicio = st.button("Adquirir Acesso Vitalício", type="primary", use_container_width=True, key=f"vitalicio_{timestamp}_{random_param}")
        if button_vitalicio:
            with st.spinner("Conectando ao servidor de pagamentos..."):
                try:
                    # Criar a sessão de checkout
                    checkout_session = criar_checkout_session("lifetime")
                    
                    # Se for bem sucedido, redireciona
                    if checkout_session and "url" in checkout_session:
                        st.success("Redirecionando para o checkout...")
                        # Link HTML para abrir em nova aba
                        st.markdown(f"""
                        <a href="{checkout_session['url']}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #2d8cff; color: white; border: none; padding: 10px 20px; 
                            border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">
                                Clique aqui para ir para o checkout
                            </button>
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Não foi possível criar a sessão de checkout. Tente novamente.")
                except Exception as e:
                    st.error(f"Erro ao processar pagamento: {str(e)}")