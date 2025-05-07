import streamlit as st
import requests
import os
import sys
from datetime import datetime

# Adicionar diretório raiz ao path para importar módulos personalizados
# Ajuste para obter o diretório pai pois estamos na pasta 'pages'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Agora podemos importar os módulos da raiz
from utils.planos import verificar_login
from utils.assinatura_db import iniciar_periodo_teste, verificar_assinatura_ativa

# Configuração da página
st.set_page_config(
    page_title="Iniciar Período de Teste - Planner Organizer",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remover o menu hamburguer e rodapé
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.css-1vq4p4l, .e1fqkh3o4 {margin-top: -75px;}
</style>
""", unsafe_allow_html=True)

# Função principal
def main():
    # Verificação de login
    usuario_id, usuario_nome, usuario_email = verificar_login()

    # Se não estiver logado, mostrar mensagem sem redirecionar
    if not usuario_id:
        st.warning("Você precisa estar logado para iniciar um período de teste gratuito.")
        
        # Formulário de login simplificado
        st.subheader("Faça login para continuar")
        
        with st.form("login_form_teste"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit_login:
                # Aqui realizaria o login mas como é apenas demonstrativo, 
                # vamos apenas mostrar que seria redirecionado
                st.success("Login realizado. Você será redirecionado para a página de teste.")
                st.rerun()
                
        # Link para voltar à página principal
        if st.button("Voltar à página principal"):
            st.markdown('<a href="/" target="_self">Voltar para página principal</a>', unsafe_allow_html=True)
            
        st.stop()
    
    # Cabeçalho
    st.title("Período de Teste Gratuito")
    
    # Verificar se já existe uma assinatura ativa
    resultado_verificacao = verificar_assinatura_ativa(usuario_id)
    
    if resultado_verificacao.get('sucesso') and resultado_verificacao.get('assinatura_ativa'):
        st.warning("Você já possui uma assinatura ativa e não precisa iniciar um período de teste.")
        
        # Mostrar detalhes da assinatura atual
        assinatura = resultado_verificacao.get('assinatura', {})
        plano = assinatura.get('plano', 'Não identificado')
        status = assinatura.get('status', 'Não identificado')
        
        st.markdown(f"""
        ## Sua assinatura atual:
        - **Plano:** {plano}
        - **Status:** {status}
        """)
        
        # Botão para voltar à página de assinatura
        if st.button("Ver detalhes da minha assinatura", type="primary"):
            st.markdown('<a href="/minha_assinatura" target="_self">Ver minha assinatura</a>', unsafe_allow_html=True)
        
        st.stop()
    
    # Interface principal para iniciar o período de teste
    st.markdown("""
    ## Experimente o Planner Organizer Gratuitamente
    
    Você está prestes a iniciar um período de teste gratuito de 7 dias, que lhe dará acesso a **todas as funcionalidades** do sistema.
    
    ### O que você receberá:
    - Acesso completo a todas as funcionalidades premium
    - 7 dias para explorar o sistema sem compromisso
    - Cancelamento simples a qualquer momento
    
    Nenhum cartão de crédito é necessário para iniciar seu período de teste gratuito.
    """)
    
    # Checkbox para termos
    termos_aceitos = st.checkbox("Eu concordo com os Termos de Serviço e entendo que posso cancelar meu período de teste a qualquer momento.")
    
    # Botão para iniciar
    if st.button("INICIAR MEU PERÍODO DE TESTE GRATUITO AGORA", type="primary", disabled=not termos_aceitos):
        with st.spinner("Iniciando seu período de teste..."):
            # Chamar a função para iniciar o período de teste
            resultado = iniciar_periodo_teste(usuario_id, dias=7)
            
            if resultado.get('sucesso'):
                # Mostrar mensagem de sucesso
                st.success("Período de teste iniciado com sucesso! Você agora tem acesso a todas as funcionalidades por 7 dias.")
                
                # Adicionar botão para ir para o dashboard
                st.balloons()
                st.markdown("### Seu período de teste foi ativado com sucesso!")
                
                # Link para a página de assinatura com parâmetro de sucesso
                st.markdown('<a href="/minha_assinatura?status=trial_success" target="_self">Ver minha assinatura</a>', unsafe_allow_html=True)
            else:
                # Mostrar mensagem de erro
                st.error(f"Não foi possível iniciar o período de teste: {resultado.get('mensagem', 'Erro desconhecido')}")
                
                # Verificar se o erro foi porque já existe uma assinatura
                if "já possui" in resultado.get('mensagem', '').lower():
                    st.warning("Parece que você já possui algum tipo de assinatura. Verifique sua página de assinatura para mais detalhes.")
                    
                    if st.button("Ver minha assinatura"):
                        st.markdown('<a href="/minha_assinatura" target="_self">Ver minha assinatura</a>', unsafe_allow_html=True)
    
    # Informações adicionais
    with st.expander("Perguntas Frequentes"):
        st.markdown("""
        ### O que acontece quando meu período de teste terminar?
        Ao final do período de teste, você será notificado e poderá escolher um plano para continuar utilizando o sistema. Se não escolher um plano, seu acesso será limitado.
        
        ### É necessário cartão de crédito para iniciar o teste?
        Não, você pode iniciar o período de teste sem fornecer informações de pagamento.
        
        ### Posso cancelar durante o período de teste?
        Sim, você pode cancelar a qualquer momento durante o período de teste, sem qualquer cobrança.
        """)

# Ponto de entrada
if __name__ == "__main__":
    main()
else:
    main()  # Isso garante que a função seja executada independente de como o módulo é importado