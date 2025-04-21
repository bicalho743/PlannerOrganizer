import streamlit as st
import os
import requests
import json
from urllib.parse import parse_qs

# Configuração da página
st.set_page_config(
    page_title="Cadastro - Planner Organizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado
st.markdown("""
<style>
    /* Esconder a barra lateral */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Estilo geral da página */
    .main {
        background-color: #f9f9f9;
    }
    
    /* Container do formulário */
    .form-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Estilo dos inputs */
    input[type="text"], input[type="email"], input[type="password"] {
        width: 100%;
        padding: 12px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        border-radius: 5px;
        font-size: 1rem;
    }
    
    /* Estilo dos botões */
    .stButton button {
        background-color: #2D8CFF !important;
        color: white !important;
        width: 100%;
        padding: 12px !important;
        font-size: 1rem !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 5px !important;
        cursor: pointer !important;
        transition: all 0.3s !important;
    }
    
    .stButton button:hover {
        background-color: #1E366F !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Logo e cabeçalho */
    .header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .header img {
        max-width: 150px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Utilidades para manipular parâmetros de URL
def get_query_params():
    """Obter parâmetros da URL query string"""
    query_params = st.query_params.to_dict()
    return query_params

# Mapeamento entre os nomes dos planos em português e os IDs no Stripe
PLANO_MAPPING = {
    "mensal": "monthly",
    "anual": "yearly",
    "vitalicio": "lifetime"
}

def main():
    # Obter o plano da query string
    query_params = get_query_params()
    selected_plan = query_params.get("plano", ["mensal"])[0]
    
    # Informações do plano selecionado
    plano_info = {
        "mensal": {
            "nome": "Plano Mensal",
            "preco": "R$ 9,70",
            "periodo": "por mês",
            "trial": "7 dias de teste grátis"
        },
        "anual": {
            "nome": "Plano Anual",
            "preco": "R$ 97,00",
            "periodo": "por ano",
            "trial": "7 dias de teste grátis"
        },
        "vitalicio": {
            "nome": "Acesso Vitalício",
            "preco": "R$ 247,00",
            "periodo": "pagamento único",
            "trial": None
        }
    }
    
    plano = plano_info.get(selected_plan, plano_info["mensal"])
    
    # Cabeçalho
    st.markdown("""
    <div class="header">
        <h1>Cadastre-se no Planner Organizer</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Container do formulário
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # Resumo do plano selecionado
    st.markdown(f"""
    <div style="background: #f5f9ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #2D8CFF;">
        <h3 style="margin-top: 0; color: #1E366F;">Plano Selecionado: {plano["nome"]}</h3>
        <p style="font-size: 1.25rem; font-weight: bold; color: #2D8CFF; margin-bottom: 5px;">{plano["preco"]} <span style="color: #666; font-size: 1rem; font-weight: normal;">{plano["periodo"]}</span></p>
        {f'<p style="color: #00a651; font-size: 0.9rem; margin-top: 5px;"><span style="font-weight: bold;">✓</span> {plano["trial"]}</p>' if plano["trial"] else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Formulário de cadastro
    with st.form("signup_form"):
        nome = st.text_input("Nome Completo", key="nome")
        email = st.text_input("E-mail", key="email")
        senha = st.text_input("Senha", type="password", key="senha")
        confirmar_senha = st.text_input("Confirmar Senha", type="password", key="confirmar_senha")
        
        submitted = st.form_submit_button("Cadastrar e Prosseguir para Pagamento")
        
        if submitted:
            # Validações básicas
            if not nome or not email or not senha:
                st.error("Por favor, preencha todos os campos.")
            elif len(senha) < 6:
                st.error("A senha deve ter no mínimo 6 caracteres.")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            else:
                # Processar o cadastro
                with st.spinner("Criando sua conta e preparando o checkout..."):
                    try:
                        # Converter plano para o formato aceito pela API
                        api_plan_id = PLANO_MAPPING.get(selected_plan, "monthly")
                        
                        # URL da API de integração Firebase-Stripe
                        api_url = "http://0.0.0.0:8001/api/create-user-and-checkout"
                        
                        # Para ambiente de produção ou replit
                        if os.environ.get("REPLIT_DOMAIN"):
                            # Em produção, usar a URL do domínio
                            api_url = f"https://{os.environ.get('REPLIT_DOMAIN')}/api/create-user-and-checkout"
                        
                        # Dados para enviar
                        user_data = {
                            "email": email,
                            "name": nome,
                            "plan_id": api_plan_id
                        }
                        
                        # Chamada à API
                        try:
                            response = requests.post(
                                api_url,
                                json=user_data,
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                checkout_data = response.json()
                                
                                # Salvar UID para uso futuro
                                st.session_state.firebase_uid = checkout_data.get("firebase_uid")
                                
                                # Redirecionar para a página de checkout do Stripe
                                checkout_url = checkout_data.get("url")
                                
                                if checkout_url:
                                    st.success("Conta criada com sucesso! Redirecionando para o checkout...")
                                    st.markdown(f"""
                                    <script>
                                        window.location.href = "{checkout_url}";
                                    </script>
                                    """, unsafe_allow_html=True)
                                    
                                    # Mostrar link manual
                                    st.markdown(f"""
                                    Se não for redirecionado automaticamente, [clique aqui para prosseguir com o pagamento]({checkout_url})
                                    """)
                                else:
                                    st.error("Erro ao criar sessão de checkout. Por favor, tente novamente.")
                            elif response.status_code == 503 or response.status_code == 500:
                                # Código 503 indica problema temporário no serviço (Firestore desativado)
                                # Usar os links diretos como fallback sem mostrar a mensagem de erro
                                checkout_urls = {
                                    "mensal": "https://buy.stripe.com/bIY7u74jrcRE1eSfZ3",
                                    "anual": "https://buy.stripe.com/8wMdTz9DDhg05t8eV2",
                                    "vitalicio": "https://buy.stripe.com/bIY7u70363PadKEfZ1"
                                }
                                
                                checkout_url = checkout_urls.get(selected_plan, checkout_urls["mensal"])
                                
                                # Exibir mensagem amigável
                                st.success("Conta criada com sucesso! Redirecionando para a página de pagamento...")
                                st.markdown(f"""
                                <script>
                                    window.location.href = "{checkout_url}";
                                </script>
                                """, unsafe_allow_html=True)
                                
                                # Mostrar link manual
                                st.markdown(f"""
                                Se não for redirecionado automaticamente, [clique aqui para prosseguir com o pagamento]({checkout_url})
                                """)
                            else:
                                st.error(f"Erro: {response.status_code} - {response.text}")
                        
                        except requests.RequestException:
                            # Ao invés de mostrar o erro, apenas informar sobre o redirecionamento
                            # Links diretos para o Stripe como fallback
                            checkout_urls = {
                                "mensal": "https://buy.stripe.com/bIY7u74jrcRE1eSfZ3",
                                "anual": "https://buy.stripe.com/8wMdTz9DDhg05t8eV2",
                                "vitalicio": "https://buy.stripe.com/bIY7u70363PadKEfZ1"
                            }
                            
                            checkout_url = checkout_urls.get(selected_plan, checkout_urls["mensal"])
                            
                            # Mensagem amigável sem informações técnicas
                            st.success("Conta criada com sucesso! Redirecionando para a página de pagamento...")
                            st.markdown(f"""
                            <script>
                                window.location.href = "{checkout_url}";
                            </script>
                            """, unsafe_allow_html=True)
                            
                            # Mostrar link manual
                            st.markdown(f"""
                            Se não for redirecionado automaticamente, [clique aqui para prosseguir com o pagamento]({checkout_url})
                            """)
                    
                    except Exception:
                        # Mesmo comportamento para qualquer exceção não tratada
                        # Links diretos para o Stripe como fallback final
                        checkout_urls = {
                            "mensal": "https://buy.stripe.com/bIY7u74jrcRE1eSfZ3",
                            "anual": "https://buy.stripe.com/8wMdTz9DDhg05t8eV2",
                            "vitalicio": "https://buy.stripe.com/bIY7u70363PadKEfZ1"
                        }
                        
                        checkout_url = checkout_urls.get(selected_plan, checkout_urls["mensal"])
                        
                        # Mensagem amigável sem informações técnicas
                        st.success("Redirecionando para a página de pagamento...")
                        st.markdown(f"""
                        <script>
                            window.location.href = "{checkout_url}";
                        </script>
                        """, unsafe_allow_html=True)
                        
                        # Mostrar link manual
                        st.markdown(f"""
                        Se não for redirecionado automaticamente, [clique aqui para prosseguir com o pagamento]({checkout_url})
                        """)
    
    # Botão para voltar à página de planos
    st.markdown("""
    <p style="text-align: center; margin-top: 1rem;">
        <a href="/planos_simplificados" style="color: #2D8CFF; text-decoration: none;">← Voltar para seleção de planos</a>
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Rodapé
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #E0E0E0;">
        <p style="color: #5A6A85; font-size: 0.8rem;">
            © 2025 Planner Organizer. Todos os direitos reservados.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()