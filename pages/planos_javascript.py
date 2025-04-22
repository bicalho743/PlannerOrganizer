import streamlit as st
import json
import requests
import os

def show():
    """
    Exibe a página de planos com integração com API de pagamento
    """
    st.title("Assine o Planner Organizer")
    
    st.markdown("""
    Escolha o plano que melhor se adequa às suas necessidades.
    
    ### Como funciona o processo de assinatura:
    1. Selecione o plano desejado
    2. Clique no botão de assinatura
    3. Complete o pagamento na página segura do Stripe
    4. Você será redirecionado de volta para o sistema após confirmação
    """)
    
    # Função para criar uma sessão de checkout
    def create_checkout_session(plan_id):
        try:
            # URL da API de pagamento (FastAPI)
            api_url = "http://localhost:8000/create-checkout-session"
            
            # Enviar a requisição para a API
            response = requests.post(
                api_url,
                json={"plan_id": plan_id}
            )
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                data = response.json()
                if "url" in data:
                    # Abrir a URL de checkout em uma nova aba
                    st.markdown(f"""
                    <script>
                        window.open("{data['url']}", "_blank");
                    </script>
                    """, unsafe_allow_html=True)
                    return True, data["url"]
                else:
                    return False, data.get("error", "Erro desconhecido ao criar sessão de checkout")
            else:
                return False, f"Erro no servidor: {response.status_code}"
            
        except Exception as e:
            return False, f"Erro ao conectar com o servidor de pagamentos: {str(e)}"
    
    # Criar layout com três colunas para os planos
    col1, col2, col3 = st.columns(3)
    
    # Plano Mensal
    with col1:
        st.markdown("""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; height: 100%;">
            <h3 style="color: #1E88E5; text-align: center;">Plano Mensal</h3>
            <h2 style="text-align: center;">R$ 9,70</h2>
            <p style="text-align: center; color: #666;">por mês</p>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin: 15px 0; font-size: 12px;">
                ✨ 7 DIAS DE TESTE GRÁTIS
            </div>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Acesso a todos os recursos
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Suporte por e-mail
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Cancelamento a qualquer momento
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Ideal para testar o sistema
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Assinar Plano Mensal", key="subscribe_monthly", use_container_width=True):
            with st.spinner("Preparando checkout..."):
                success, result = create_checkout_session("mensal")
                if success:
                    st.success("Redirecionando para a página de pagamento...")
                    # Criar um link manual caso o redirecionamento automático não funcione
                    st.markdown(f"[Clique aqui se a página não abrir automaticamente]({result})")
                else:
                    st.error(result)
    
    # Plano Anual
    with col2:
        st.markdown("""
        <div style="border: 2px solid #1E88E5; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); height: 100%;">
            <h3 style="color: #1E88E5; text-align: center;">Plano Anual</h3>
            <h2 style="text-align: center;">R$ 97,00</h2>
            <p style="text-align: center; color: #666;">por ano</p>
            <div style="background-color: #1E88E5; color: white; padding: 5px; border-radius: 20px; text-align: center; margin: 15px 0; font-size: 12px; font-weight: bold;">
                ECONOMIZE 17%
            </div>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin: 15px 0; font-size: 12px;">
                ✨ 7 DIAS DE TESTE GRÁTIS
            </div>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Acesso a todos os recursos
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Suporte prioritário
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Atualizações gratuitas
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Treinamento personalizado
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Melhor custo-benefício
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Assinar Plano Anual", key="subscribe_annual", use_container_width=True, type="primary"):
            with st.spinner("Preparando checkout..."):
                success, result = create_checkout_session("anual")
                if success:
                    st.success("Redirecionando para a página de pagamento...")
                    # Criar um link manual caso o redirecionamento automático não funcione
                    st.markdown(f"[Clique aqui se a página não abrir automaticamente]({result})")
                else:
                    st.error(result)
    
    # Plano Vitalício
    with col3:
        st.markdown("""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; height: 100%;">
            <h3 style="color: #1E88E5; text-align: center;">Acesso Vitalício</h3>
            <h2 style="text-align: center;">R$ 247,00</h2>
            <p style="text-align: center; color: #666;">pagamento único</p>
            <div style="background-color: #1E88E5; color: white; padding: 5px; border-radius: 20px; text-align: center; margin: 15px 0; font-size: 12px; font-weight: bold;">
                MELHOR VALOR A LONGO PRAZO
            </div>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Acesso permanente ao sistema
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Suporte prioritário
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Sem mensalidades futuras
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Todas as atualizações inclusas
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Melhor para longo prazo
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Adquirir Acesso Vitalício", key="subscribe_lifetime", use_container_width=True):
            with st.spinner("Preparando checkout..."):
                success, result = create_checkout_session("vitalicio")
                if success:
                    st.success("Redirecionando para a página de pagamento...")
                    # Criar um link manual caso o redirecionamento automático não funcione
                    st.markdown(f"[Clique aqui se a página não abrir automaticamente]({result})")
                else:
                    st.error(result)
    
    # Informações sobre o Stripe
    st.info("""
    💳 **Pagamento Seguro**: Todos os pagamentos são processados de forma segura pelo Stripe, líder mundial em pagamentos online.
    
    🔒 **Seus dados estão protegidos**: Não armazenamos suas informações de cartão de crédito.
    """)
    
    # Botão para retornar à página inicial
    if st.button("Voltar para a Página Inicial", use_container_width=True):
        st.session_state.current_page = "Dashboard"
        st.rerun()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Planos - Planner Organizer",
        page_icon="📊",
        layout="wide"
    )
    show()