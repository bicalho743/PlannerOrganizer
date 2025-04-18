import streamlit as st
import requests
import os
import json

# Configuração da API Stripe
# No ambiente Replit usamos a API funcionando na porta 8000, 8001 e 8002
STRIPE_API_URL = "http://0.0.0.0:8000"  # API principal do Stripe (/api/checkout/session)
# URLs de backup para tentar conexão alternativa
STRIPE_LOCAL_API_URL = "http://127.0.0.1:8000"
STRIPE_DIRECT_API_URL = "http://0.0.0.0:8002"  # API direta do Stripe (/checkout/mensal, /checkout/anual, etc)
STRIPE_DIRECT_LOCAL_API_URL = "http://127.0.0.1:8002"
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_live_51RFB2dLWUPER7pUXim2VuVkCESsrjNcHkDQuMJeDCvvW0ZsyFfqM2exfCTwSSe5O4R2TXBxHJtIpYSGBTAx2gBXT00gpAVYK1f")

def criar_checkout_session(plan_id):
    """
    Cria uma sessão de checkout do Stripe para um plano específico
    
    Args:
        plan_id (str): ID do plano (monthly, yearly, lifetime)
        
    Returns:
        dict: Resposta da API com session_id e URL
    """
    # Lista de possíveis endpoints para tentar
    endpoints = [
        f"{STRIPE_API_URL}/api/checkout/session",        # API principal endpoint (/api/checkout/session)
        f"{STRIPE_LOCAL_API_URL}/api/checkout/session",  # Backup via localhost
        f"{STRIPE_API_URL}:8000/api/checkout/session",   # Alternativa com porta explícita
        # Endpoints da API direct
        f"{STRIPE_DIRECT_API_URL}/checkout_{plan_id}",   # API direta endpoint (/checkout_monthly, /checkout_yearly, etc)
        f"{STRIPE_DIRECT_LOCAL_API_URL}/checkout_{plan_id}",  # Backup via localhost
    ]
    
    # IDs de preço do Stripe fornecidos pelo cliente
    price_mapping = {
        "monthly": "price_1RFE2ULWUPER7pUXw1i1X5oR",    # ID do preço Mensal (R$9,70) com trial de 7 dias e recorrência configurada
        "yearly": "price_1RFBTtLWUPER7pUXPt2Ajhgz",     # ID do preço Anual (R$97,00) com trial de 7 dias
        "lifetime": "price_1RFBULLWUPER7pUXCiGZn3Jn"    # ID do preço Vitalício (R$247,00) sem trial
    }
    
    # Preparar os dados para enviar ao Stripe usando IDs de preço
    session_data = {
        "price_id": price_mapping.get(plan_id, price_mapping["monthly"]),
        "success_url": "https://workspace.solanobicalho.repl.co/success",
        "cancel_url": "https://workspace.solanobicalho.repl.co/cancel",
        "metadata": {"plan": plan_id},
        "mode": "subscription" if plan_id in ["monthly", "yearly"] else "payment"
    }
    
    last_error = None
    for endpoint in endpoints:
        try:
            st.write(f"Tentando conectar com: {endpoint}")
            # Aqui enviamos os dados da sessão como JSON para a API
            response = requests.post(
                endpoint, 
                json=session_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            # Mostrar a resposta para debug
            st.write(f"Resposta: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            else:
                st.write(f"Conteúdo da resposta: {response.text[:200]}")
        except Exception as e:
            last_error = str(e)
            st.write(f"Erro ao conectar: {str(e)}")
            continue
    
    st.error(f"Erro ao criar sessão: {last_error}")
    return {"error": last_error}

def exibir_planos_integracao():
    """
    Versão melhorada da exibição de planos com melhor integração com Stripe
    e melhor experiência de redirecionamento
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
    
    .stripe-button {
        background: linear-gradient(135deg, #4CAF50, #2E7D32);
        color: white !important;
        padding: 10px 15px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        display: block;
        text-align: center;
        margin-top: 15px;
        transition: all 0.3s ease;
    }
    
    .stripe-button:hover {
        background: linear-gradient(135deg, #2E7D32, #1B5E20);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stripe-button.destaque {
        background: linear-gradient(135deg, #ff6b6b, #e83e3e);
    }
    
    .stripe-button.destaque:hover {
        background: linear-gradient(135deg, #e83e3e, #cf2b2b);
    }
    
    .stripe-info {
        margin-top: 10px;
        padding: 10px;
        background-color: #f0f0f0;
        border-radius: 5px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título da seção
    st.markdown("<h2 style='text-align: center; color: #1E366F; margin-top: 20px; margin-bottom: 10px;'>Escolha o Plano Ideal Para o Seu Negócio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 18px; margin-bottom: 30px;'>Invista no crescimento da sua organização com nossos planos acessíveis</p>", unsafe_allow_html=True)
    
    # TABELA DE PLANOS
    col1, col2, col3 = st.columns([1, 1.2, 1])  # o do meio ganha mais espaço

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
        if st.button("Assinar Plano Mensal", type="primary", use_container_width=True):
            checkout_data = criar_checkout_session("monthly")
            
            if "error" in checkout_data:
                st.error(f"Erro ao processar pagamento: {checkout_data['error']}")
            else:
                checkout_url = checkout_data.get("url")
                
                if checkout_url:
                    # Display the URL as a clickable link
                    st.markdown(f"""
                    <div class="stripe-info">
                        URL de checkout: <a href="{checkout_url}" target="_blank">{checkout_url}</a>
                    </div>
                    <a href="{checkout_url}" target="_blank" class="stripe-button">
                        Prosseguir para checkout do plano mensal
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Also try to open it automatically
                    st.markdown(f"""
                    <script>
                        window.open("{checkout_url}", "_blank");
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.success("Link de checkout gerado com sucesso!")
                else:
                    st.warning("Link de checkout não foi gerado corretamente.")

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
        if st.button("Assinar Plano Anual", type="primary", use_container_width=True):
            checkout_data = criar_checkout_session("yearly")
            
            if "error" in checkout_data:
                st.error(f"Erro ao processar pagamento: {checkout_data['error']}")
            else:
                checkout_url = checkout_data.get("url")
                
                if checkout_url:
                    # Display the URL as a clickable link
                    st.markdown(f"""
                    <div class="stripe-info">
                        URL de checkout: <a href="{checkout_url}" target="_blank">{checkout_url}</a>
                    </div>
                    <a href="{checkout_url}" target="_blank" class="stripe-button destaque">
                        Prosseguir para checkout do plano anual
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Also try to open it automatically
                    st.markdown(f"""
                    <script>
                        window.open("{checkout_url}", "_blank");
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.success("Link de checkout gerado com sucesso!")
                else:
                    st.warning("Link de checkout não foi gerado corretamente.")

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
        if st.button("Adquirir Acesso Vitalício", type="primary", use_container_width=True):
            checkout_data = criar_checkout_session("lifetime")
            
            if "error" in checkout_data:
                st.error(f"Erro ao processar pagamento: {checkout_data['error']}")
            else:
                checkout_url = checkout_data.get("url")
                
                if checkout_url:
                    # Display the URL as a clickable link
                    st.markdown(f"""
                    <div class="stripe-info">
                        URL de checkout: <a href="{checkout_url}" target="_blank">{checkout_url}</a>
                    </div>
                    <a href="{checkout_url}" target="_blank" class="stripe-button">
                        Prosseguir para checkout do acesso vitalício
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Also try to open it automatically
                    st.markdown(f"""
                    <script>
                        window.open("{checkout_url}", "_blank");
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.success("Link de checkout gerado com sucesso!")
                else:
                    st.warning("Link de checkout não foi gerado corretamente.")
    
    # Rodapé com informações sobre segurança
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; margin-bottom: 20px; font-size: 14px; color: #666;">
        <p>Pagamentos processados com segurança pelo <img src="https://cdn.freebiesupply.com/logos/large/2x/stripe-logo-png-transparent.png" height="20" style="vertical-align: middle; margin: 0 5px;"> Stripe</p>
        <p>Seus dados estão protegidos com criptografia de ponta a ponta.</p>
    </div>
    """, unsafe_allow_html=True)

# Para teste independente
if __name__ == "__main__":
    exibir_planos_integracao()