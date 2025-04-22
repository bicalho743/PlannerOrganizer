import streamlit as st
import requests
import os

def main():
    st.set_page_config(
        page_title="Checkout - Planner Organizer",
        page_icon="💳",
        layout="wide"
    )
    
    st.title("Checkout Simplificado")
    
    # Obter o plano da URL (se disponível)
    query_params = st.experimental_get_query_params()
    plano = query_params.get("plano", [""])[0]
    
    if not plano:
        # Se não houver plano na URL, mostrar todos os planos
        st.info("Selecione um plano abaixo para prosseguir com o checkout")
        
        # Botões para cada plano
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.header("Plano Mensal")
            st.write("R$ 9,70 / mês")
            if st.button("Selecionar Plano Mensal", key="btn_mensal", use_container_width=True):
                plano = "mensal"
        
        with col2:
            st.header("Plano Anual")
            st.write("R$ 97,00 / ano")
            if st.button("Selecionar Plano Anual", key="btn_anual", use_container_width=True):
                plano = "anual"
        
        with col3:
            st.header("Acesso Vitalício")
            st.write("R$ 247,00 (único)")
            if st.button("Selecionar Acesso Vitalício", key="btn_vitalicio", use_container_width=True):
                plano = "vitalicio"
    
    # Processamento do plano selecionado
    if plano in ["mensal", "anual", "vitalicio"]:
        st.success(f"Plano selecionado: {plano.title()}")
        
        # Configurar informações do plano para exibição
        plano_info = {
            "mensal": {
                "nome": "Plano Mensal",
                "preco": "R$ 9,70",
                "periodo": "por mês",
                "teste_gratis": True,
                "texto_botao": "Ir para Checkout do Plano Mensal",
            },
            "anual": {
                "nome": "Plano Anual",
                "preco": "R$ 97,00",
                "periodo": "por ano",
                "teste_gratis": True,
                "economia": "17%",
                "texto_botao": "Ir para Checkout do Plano Anual",
            },
            "vitalicio": {
                "nome": "Acesso Vitalício",
                "preco": "R$ 247,00",
                "periodo": "pagamento único",
                "teste_gratis": False,
                "texto_botao": "Ir para Checkout do Acesso Vitalício",
            }
        }
        
        info = plano_info[plano]
        
        # Exibir o card do plano
        st.markdown(f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; background-color: #f9f9f9;">
            <h2 style="color: #1E88E5; margin-bottom: 10px;">{info['nome']}</h2>
            <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">{info['preco']}</div>
            <div style="color: #666; margin-bottom: 15px;">{info['periodo']}</div>
            
            {f'<div style="background-color: #e6fff0; color: #00a651; padding: 8px; border-radius: 5px; margin-bottom: 15px; text-align: center;">✨ 7 DIAS DE TESTE GRÁTIS</div>' if info.get('teste_gratis') else ''}
            
            {f'<div style="background-color: #1E88E5; color: white; padding: 8px; border-radius: 5px; margin-bottom: 15px; text-align: center;">ECONOMIZE {info["economia"]}</div>' if info.get('economia') else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Botão para iniciar checkout
        if st.button(info['texto_botao'], key="checkout_button", use_container_width=True, type="primary"):
            try:
                with st.spinner("Preparando checkout..."):
                    # URL da API de pagamento
                    api_url = "http://localhost:8000/create-checkout-session"
                    
                    # Enviar a requisição para a API
                    response = requests.post(
                        api_url,
                        json={"plan_id": plano}
                    )
                    
                    # Verificar se a requisição foi bem-sucedida
                    if response.status_code == 200:
                        data = response.json()
                        if "url" in data:
                            st.success("Checkout criado com sucesso!")
                            st.markdown(f"""
                            <a href="{data['url']}" target="_blank" style="text-decoration: none;">
                                <button style="width: 100%; padding: 15px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold;">
                                    Prosseguir para Pagamento Seguro
                                </button>
                            </a>
                            """, unsafe_allow_html=True)
                            
                            # Script para redirecionamento automático (mas mantém a opção de clique manual)
                            st.markdown(f"""
                            <script>
                                window.open("{data['url']}", "_blank");
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Erro ao criar checkout: {data.get('error', 'Erro desconhecido')}")
                    else:
                        st.error(f"Erro na API de pagamento: Código {response.status_code}")
            except Exception as e:
                st.error(f"Erro ao se conectar com o servidor de pagamento: {str(e)}")
    
    # Botão para voltar para a página inicial
    if st.button("Voltar para a Página Inicial", use_container_width=True):
        st.switch_page("app.py")

# Função para chamar o checkout direto para cada plano (para uso em links externos)
def checkout_mensal():
    """
    Redireciona o usuário para a página de checkout do plano mensal no Stripe.
    """
    try:
        # URL da API de pagamento
        api_url = "http://localhost:8000/create-checkout-session"
        
        # Enviar a requisição para a API
        response = requests.post(
            api_url,
            json={"plan_id": "mensal"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "url" in data:
                # Redirecionar para a URL de checkout
                import webbrowser
                webbrowser.open(data["url"])
                st.success("Redirecionando para o checkout...")
            else:
                st.error(f"Erro ao criar checkout: {data.get('error', 'Erro desconhecido')}")
        else:
            st.error(f"Erro na API de pagamento: Código {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao se conectar com o servidor de pagamento: {str(e)}")

def checkout_anual():
    """
    Redireciona o usuário para a página de checkout do plano anual no Stripe.
    """
    try:
        # URL da API de pagamento
        api_url = "http://localhost:8000/create-checkout-session"
        
        # Enviar a requisição para a API
        response = requests.post(
            api_url,
            json={"plan_id": "anual"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "url" in data:
                # Redirecionar para a URL de checkout
                import webbrowser
                webbrowser.open(data["url"])
                st.success("Redirecionando para o checkout...")
            else:
                st.error(f"Erro ao criar checkout: {data.get('error', 'Erro desconhecido')}")
        else:
            st.error(f"Erro na API de pagamento: Código {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao se conectar com o servidor de pagamento: {str(e)}")

def checkout_vitalicio():
    """
    Redireciona o usuário para a página de checkout do plano vitalício no Stripe.
    """
    try:
        # URL da API de pagamento
        api_url = "http://localhost:8000/create-checkout-session"
        
        # Enviar a requisição para a API
        response = requests.post(
            api_url,
            json={"plan_id": "vitalicio"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "url" in data:
                # Redirecionar para a URL de checkout
                import webbrowser
                webbrowser.open(data["url"])
                st.success("Redirecionando para o checkout...")
            else:
                st.error(f"Erro ao criar checkout: {data.get('error', 'Erro desconhecido')}")
        else:
            st.error(f"Erro na API de pagamento: Código {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao se conectar com o servidor de pagamento: {str(e)}")

def checkout_direto_api():
    """
    Cria uma sessão de checkout usando a API do Stripe e redireciona o usuário.
    """
    # Obter o plano da URL
    query_params = st.experimental_get_query_params()
    plano = query_params.get("plano", [""])[0]
    
    if plano in ["mensal", "anual", "vitalicio"]:
        try:
            # URL da API de pagamento
            api_url = "http://localhost:8000/create-checkout-session"
            
            # Enviar a requisição para a API
            response = requests.post(
                api_url,
                json={"plan_id": plano}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "url" in data:
                    # Redirecionar para a URL de checkout
                    st.markdown(f'''
                    <meta http-equiv="refresh" content="0;URL='{data["url"]}'" />
                    <p>Redirecionando para o checkout...</p>
                    ''', unsafe_allow_html=True)
                else:
                    st.error(f"Erro ao criar checkout: {data.get('error', 'Erro desconhecido')}")
            else:
                st.error(f"Erro na API de pagamento: Código {response.status_code}")
        except Exception as e:
            st.error(f"Erro ao se conectar com o servidor de pagamento: {str(e)}")
    else:
        st.error("Plano inválido. Escolha entre: mensal, anual, vitalicio")

if __name__ == "__main__":
    main()