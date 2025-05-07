import streamlit as st
import os
import requests
import sys
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("Iniciando módulo planos_simple.py")

# URL base da API
API_URL = "https://plannerorganiza-dev.replit.app"
logger.info(f"API_URL definida como: {API_URL}")

# Configurações de preços do Stripe
STRIPE_PRICE_ID_MENSAL = os.environ.get('STRIPE_PRICE_ID_MENSAL')
STRIPE_PRICE_ID_ANUAL = os.environ.get('STRIPE_PRICE_ID_ANUAL')
STRIPE_PRICE_ID_VITALICIO = os.environ.get('STRIPE_PRICE_ID_VITALICIO')

# Importações para autenticação
# Importamos o objeto firebase_auth e definimos as funções necessárias
from utils.firebase_auth import firebase_auth

# Função auxiliar para verificar login
def check_login():
    """Verifica se o usuário está logado e retorna suas informações"""
    if firebase_auth.is_authenticated():
        return firebase_auth.get_current_user()
    return None

# Função auxiliar para realizar logout
def logout():
    """Realiza logout do usuário"""
    return firebase_auth.logout()

# Importações para processamento de pagamentos
from utils.import_assinaturas import (
    criar_sessao_checkout,
    obter_assinatura_usuario
)

# Função auxiliar para obter o token do Firebase
def get_firebase_token():
    """Recupera o token do Firebase da sessão"""
    return st.session_state.get("firebase_token")

# Função para iniciar período de teste
def iniciar_periodo_teste(usuario_id, dias=7):
    """
    Inicia um período de teste para o usuário
    
    Args:
        usuario_id: ID do usuário
        dias: Número de dias do período de teste
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Primeiro, tenta iniciar o período de teste via API
        headers = {"Authorization": f"Bearer {get_firebase_token()}"}
        try:
            # Tentar fazer a requisição para a API
            response = requests.post(
                f"{API_URL}/api/iniciar_teste", 
                json={"usuario_id": usuario_id, "dias": dias},
                headers=headers
            )
            
            if response.status_code == 200:
                resultado = response.json()
                return resultado
            else:
                print(f"Erro na API: {response.status_code} - {response.text}")
                # Se falhar, continuar com o método direto
        except Exception as api_e:
            print(f"Erro ao chamar API: {str(api_e)}")
            # Se falhar, continuar com o método direto
        
        # Método alternativo direto (fallback)
        from utils.assinatura_db import registrar_assinatura
        from datetime import datetime, timedelta
        
        # Calcular datas
        data_inicio = datetime.now()
        data_fim = data_inicio + timedelta(days=dias)
        
        # Registrar como assinatura de teste
        resultado = registrar_assinatura(
            usuario_id=usuario_id,
            plano='Teste',
            status='trial',
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        return resultado
    except Exception as e:
        print(f"Erro ao iniciar período de teste: {str(e)}")
        return {'sucesso': False, 'mensagem': f'Erro ao iniciar período de teste: {str(e)}'}

def mostrar_pagina_planos():
    # Configuração da página
    st.set_page_config(
        page_title="Planos - Planner Organiza",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Verificar login
    user = check_login()
    
    # Cabeçalho
    st.title("Escolha seu plano")
    st.markdown("### Comece agora e leve sua organização ao próximo nível")
    
    # CSS para estilizar a página
    st.markdown("""
    <style>
    .pricing-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 2rem 0;
    }
    .pricing-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        width: 100%;
        max-width: 300px;
        text-align: center;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    .pricing-card.highlight {
        border-color: #4CAF50;
        position: relative;
    }
    .highlight-badge {
        position: absolute;
        top: -10px;
        right: -10px;
        background-color: #4CAF50;
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.8rem;
        transform: rotate(15deg);
    }
    .pricing-card h3 {
        color: #333;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .price {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .price-period {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .feature-list {
        list-style-type: none;
        padding: 0;
        margin: 0 0 1.5rem 0;
        text-align: left;
    }
    .feature-list li {
        padding: 0.5rem 0;
        position: relative;
        padding-left: 1.5rem;
    }
    .feature-list li:before {
        content: "✓";
        color: #4CAF50;
        position: absolute;
        left: 0;
    }
    .pricing-button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.3s ease;
        width: 100%;
        margin-top: 1rem;
        text-decoration: none;
        display: inline-block;
    }
    .pricing-button:hover {
        background-color: #1565C0;
    }
    .pricing-button.highlight {
        background-color: #4CAF50;
    }
    .pricing-button.highlight:hover {
        background-color: #388E3C;
    }
    .value-prop {
        text-align: center;
        margin: 3rem 0;
    }
    .value-prop h2 {
        color: #333;
        margin-bottom: 1rem;
    }
    .value-prop p {
        color: #666;
        max-width: 800px;
        margin: 0 auto;
    }
    .testimonial {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 2rem;
        margin: 3rem 0;
        text-align: center;
    }
    .testimonial blockquote {
        font-style: italic;
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .testimonial-author {
        font-weight: bold;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Se o usuário estiver logado, verificar sua assinatura
    usuario_id = None
    usuario_nome = "Usuário"
    usuario_email = "email@exemplo.com"
    tem_assinatura = False
    
    if user:
        usuario_id = user.get('localId')
        usuario_nome = user.get('displayName', 'Usuário')
        usuario_email = user.get('email', 'email@exemplo.com')
        
        # Verificar se já tem assinatura
        resultado_assinatura = obter_assinatura_usuario(usuario_id)
        tem_assinatura = resultado_assinatura.get('sucesso', False)
        
        if tem_assinatura:
            assinatura = resultado_assinatura.get('assinatura', {})
            plano_atual = assinatura.get('plano')
            
            st.success(f"Você já possui o plano {plano_atual}! Aproveite todos os recursos.")
            
            # Mostrar link para gerenciar assinatura
            st.markdown("""
            <div style="text-align: center; margin: 2rem 0;">
                <a href="/minha_assinatura" class="pricing-button">Gerenciar minha assinatura</a>
            </div>
            """, unsafe_allow_html=True)
            
            # Adicionar explicação sobre recursos disponíveis
            st.markdown("### Recursos disponíveis no seu plano:")
            
            recursos = [
                "✓ Gerenciamento ilimitado de propostas",
                "✓ Gerenciamento ilimitado de clientes",
                "✓ Relatórios personalizados",
                "✓ Exportação de dados",
                "✓ Suporte prioritário"
            ]
            
            for recurso in recursos:
                st.markdown(f"<p style='margin: 0.5rem 0;'>{recurso}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### Precisa de ajuda?")
            st.markdown("Entre em contato com nosso suporte: contato@plannerorganiza.com.br")
            
            # Parar a execução aqui, pois não precisamos mostrar os planos
            return
    
    # Funcionalidade de assinatura (botões)
    def criar_botao_assinar(plano, price_id, highlight=False):
        if not user:
            return f"""
            <a href="/login?redirect=/planos" class="pricing-button{'highlight' if highlight else ''}">
                Faça login para assinar
            </a>
            """
        else:
            # Definir ID do botão
            button_id = f"btn_{plano.lower().replace(' ', '_')}"
            
            # Definir URL da API com base no plano
            endpoint = ""
            if plano == "Mensal":
                endpoint = "/api/checkout/mensal"
            elif plano == "Anual":
                endpoint = "/api/checkout/anual"
            elif plano == "Vitalício":
                endpoint = "/api/checkout/vitalicio"
                
            # Função JavaScript para fazer a requisição com autenticação
            js_code = f"""
            function redirecionar_{plano.lower().replace(' ', '_')}() {{
                const token = localStorage.getItem('firebase_token');
                const apiUrl = window.location.origin;
                
                if (token) {{
                    // Enviar com autenticação
                    fetch(apiUrl + "{endpoint}", {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + token
                        }}
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.url) {{
                            window.location.href = data.url;
                        }} else {{
                            alert('Erro ao criar sessão de checkout: ' + (data.message || 'Erro desconhecido'));
                        }}
                    }})
                    .catch(error => {{
                        console.error('Erro:', error);
                        alert('Erro ao processar pagamento. Por favor, tente novamente.');
                    }});
                }} else {{
                    // Redirecionamento direto para URL da API (fallback sem token)
                    window.location.href = apiUrl + "{endpoint}";
                }}
            }}
            """
            
            # Para planos anuais e vitalícios, adicionar informação sobre o teste gratuito
            trial_info = ""
            if plano in ["Anual", "Vitalício"]:
                trial_info = """
                <div style="margin-top: 10px; font-size: 0.9rem; color: #4CAF50;">
                    Inclui 7 dias de teste grátis!
                </div>
                """
            
            return f"""
            <a href="#" id="{button_id}" class="pricing-button{'highlight' if highlight else ''}">
                {f'Começar teste grátis' if plano in ['Anual', 'Vitalício'] else 'Assinar agora'}
            </a>
            {trial_info}
            <script>
            {js_code}
            document.getElementById("{button_id}").addEventListener("click", function() {{
                redirecionar_{plano.lower().replace(' ', '_')}();
            }});
            </script>
            """
    
    # Cards de preços
    st.markdown("""
    <div class="pricing-container">
        <!-- Plano Mensal -->
        <div class="pricing-card">
            <h3>Plano Mensal</h3>
            <div class="price">R$ 9,70</div>
            <div class="price-period">por mês</div>
            <ul class="feature-list">
                <li>Gerenciamento de propostas</li>
                <li>Gerenciamento de clientes</li>
                <li>Relatórios personalizados</li>
                <li>Exportação de dados</li>
                <li>Suporte por e-mail</li>
            </ul>
            """ + criar_botao_assinar("Mensal", STRIPE_PRICE_ID_MENSAL) + """
        </div>
        
        <!-- Plano Anual -->
        <div class="pricing-card highlight">
            <div class="highlight-badge">Melhor valor</div>
            <h3>Plano Anual</h3>
            <div class="price">R$ 97,00</div>
            <div class="price-period">por ano (2 meses grátis)</div>
            <ul class="feature-list">
                <li>Tudo do plano mensal</li>
                <li>Suporte prioritário</li>
                <li>Acesso a novas funcionalidades</li>
                <li>Sem preocupação mensal</li>
                <li>Economia de 17%</li>
            </ul>
            """ + criar_botao_assinar("Anual", STRIPE_PRICE_ID_ANUAL, True) + """
        </div>
        
        <!-- Plano Vitalício -->
        <div class="pricing-card">
            <h3>Plano Vitalício</h3>
            <div class="price">R$ 247,00</div>
            <div class="price-period">pagamento único</div>
            <ul class="feature-list">
                <li>Tudo do plano anual</li>
                <li>Acesso vitalício</li>
                <li>Sem mensalidades futuras</li>
                <li>Suporte VIP</li>
                <li>Acesso a todas as atualizações</li>
            </ul>
            """ + criar_botao_assinar("Vitalício", STRIPE_PRICE_ID_VITALICIO) + """
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Proposta de valor
    st.markdown("""
    <div class="value-prop">
        <h2>Por que escolher o Planner Organiza?</h2>
        <p>Nosso sistema foi desenvolvido especificamente para profissionais de organização, facilitando o gerenciamento de propostas, clientes e serviços em um único lugar. Com o Planner Organiza, você economiza tempo, reduz a burocracia e aumenta sua produtividade.</p>
    </div>
    
    <div class="testimonial">
        <blockquote>
            "O Planner Organiza transformou meu negócio completamente. Consigo gerenciar todos os meus projetos de organização de forma eficiente e profissional. Meus clientes ficam impressionados com os relatórios detalhados!"
        </blockquote>
        <div class="testimonial-author">Maria Silva, Organizadora Profissional</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Perguntas frequentes
    st.markdown("## Perguntas Frequentes")
    
    with st.expander("Como funciona o período de teste?"):
        st.write("""
        Após criar sua conta, você tem acesso a um período de teste de 7 dias com todas as funcionalidades do sistema. 
        Depois desse período, você precisará escolher um dos planos para continuar utilizando o sistema.
        """)
    
    with st.expander("Posso cancelar minha assinatura a qualquer momento?"):
        st.write("""
        Sim! Você pode cancelar sua assinatura a qualquer momento através da página "Minha Assinatura". 
        Após o cancelamento, você continuará tendo acesso ao sistema até o final do período pago.
        """)
    
    with st.expander("Existe alguma taxa de configuração?"):
        st.write("""
        Não, não há taxas adicionais. O valor anunciado é o único que você pagará.
        """)
    
    with st.expander("Como funciona o plano vitalício?"):
        st.write("""
        O plano vitalício é um pagamento único que garante acesso permanente ao sistema. 
        Você não precisará pagar mensalidades ou anuidades futuras e terá acesso a todas as atualizações do sistema.
        """)
    
    # Botão para iniciar período de teste gratuito
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0; padding: 2rem; background-color: #f9f9f9; border-radius: 10px;">
        <h2>Quer experimentar antes de decidir?</h2>
        <p style="margin-bottom: 1.5rem;">Inicie um período de teste gratuito de 7 dias e explore todas as funcionalidades.</p>
    """, unsafe_allow_html=True)
    
    # Adicionando o botão de teste gratuito
    if not user:
        st.markdown("""
        <a href="/login?redirect=/planos" class="pricing-button highlight" style="max-width: 300px; margin: 0 auto; display: block;">
            Faça login para iniciar o teste gratuito
        </a>
        """, unsafe_allow_html=True)
    else:
        # Verificar se o usuário já tem uma assinatura ou teste ativo
        if not tem_assinatura:
            st.markdown("""
            <div class="pricing-button highlight" style="max-width: 300px; margin: 0 auto; display: block; cursor: pointer;" onclick="document.getElementById('iniciar_teste_container').style.display='block';">
                INICIAR PERÍODO GRATUITO
            </div>
            
            <div id="iniciar_teste_container" style="display: none; margin-top: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9;">
                <h3 style="margin-top: 0; color: #2d8cff;">Iniciar Período de Teste Gratuito</h3>
                <p>Você está prestes a iniciar um período de teste gratuito de 7 dias com acesso a todas as funcionalidades.</p>
                <p><strong>Nenhum cartão de crédito é necessário.</strong></p>
                <label style="display: block; margin: 15px 0;">
                    <input type="checkbox" id="termos_teste" style="margin-right: 10px;">
                    Eu concordo com os Termos de Serviço
                </label>
                <button onclick="iniciarTeste()" style="background-color: #2d8cff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">CONFIRMAR</button>
                <button onclick="document.getElementById('iniciar_teste_container').style.display='none';" style="background-color: #f5f5f5; color: #666; border: 1px solid #ddd; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-left: 10px;">CANCELAR</button>
            </div>
            
            <script>
            function iniciarTeste() {
                if (!document.getElementById('termos_teste').checked) {
                    alert('Você precisa concordar com os Termos de Serviço para continuar.');
                    return;
                }
                
                const token = localStorage.getItem('firebase_token');
                const headers = {
                    'Content-Type': 'application/json'
                };
                
                if (token) {
                    headers['Authorization'] = 'Bearer ' + token;
                }
                
                // Use o endpoint completo com o host atual para iniciar o teste
                const apiUrl = window.location.origin;
                fetch(apiUrl + "/api/iniciar_teste", {
                    method: 'POST',
                    headers: headers,
                    credentials: 'include'
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.sucesso) {
                        alert('Período de teste iniciado com sucesso!');
                        window.location.href = '/minha_assinatura?status=trial_success';
                    } else if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        alert('Erro: ' + (data.mensagem || data.error || 'Erro desconhecido'));
                    }
                })
                .catch(function(error) {
                    console.error('Erro:', error);
                    alert('Ocorreu um erro ao iniciar o período de teste. Por favor, tente novamente.');
                });
            }
            </script>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color: #666; text-align: center;">Você já possui um plano ativo.</p>
            """, unsafe_allow_html=True)
    
    st.markdown("""
    </div>
    """, unsafe_allow_html=True)
    
    # Seção final com chamada para ação
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2>Pronto para começar?</h2>
        <p style="margin-bottom: 2rem;">Escolha o plano que melhor se adapta às suas necessidades e leve seu negócio de organização para o próximo nível.</p>
    </div>
    """, unsafe_allow_html=True)

# Executar a função principal
def main():
    mostrar_pagina_planos()

def show():
    main()

if __name__ == "__main__":
    main()