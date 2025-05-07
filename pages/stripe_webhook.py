"""
Endpoint para processar webhooks do Stripe
"""
import json
import streamlit as st
import time

# Importações para processamento de eventos do Stripe
from utils.import_assinaturas import (
    registrar_assinatura,
    atualizar_status_assinatura,
    cancelar_assinatura,
    processar_webhook_evento
)

def show():
    """Exibe o endpoint de webhooks do Stripe"""
    # Configuração da página
    st.set_page_config(
        page_title="Webhook Stripe",
        page_icon="🔄",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Ocultar elementos Streamlit
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Verificar se é realmente uma solicitação de webhook
    if st.experimental_get_query_params().get('stripe_webhook') == ['true']:
        # Exibir mensagem simples
        st.markdown("## Endpoint de Webhook do Stripe")
        st.info("Este endpoint processa eventos do Stripe automaticamente.")
        
        # Processar o webhook
        try:
            # Obter payload e cabeçalhos
            request_data = json.loads(st.get_raw_json())
            
            # Obter cabeçalho de assinatura
            signature = st.request_headers().get('Stripe-Signature')
            
            st.write("Processando evento...")
            
            # Processar o evento
            resultado_processamento = processar_webhook_evento(
                payload=request_data,
                sig_header=signature
            )
            
            # Atualizar banco de dados com base no evento
            _atualizar_banco_de_dados(request_data, resultado_processamento)
            
            if resultado_processamento.get('success'):
                st.success("Evento processado com sucesso!")
            else:
                st.error(f"Erro ao processar evento: {resultado_processamento.get('message')}")
                
            # Retornar status 200 para Stripe
            st.response.status_code = 200
            return
            
        except Exception as e:
            st.error(f"Erro ao processar webhook: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            
            # Ainda retornar 200 para evitar reenvios
            st.response.status_code = 200
            return
    
    # Página padrão (quando não for webhook)
    st.title("Endpoint de Webhook Stripe")
    st.write("""
    Este é o endpoint para processamento de webhooks do Stripe.
    
    Você não deveria estar acessando esta página diretamente.
    """)

def _atualizar_banco_de_dados(request_data, resultado_processamento):
    """
    Atualiza o banco de dados com base no tipo de evento recebido
    
    Args:
        request_data: Dados da requisição
        resultado_processamento: Resultado do processamento do evento
    """
    try:
        # Extrair tipo de evento
        tipo_evento = request_data.get('type')
        
        # Registrar o evento no log
        print(f"Evento Stripe recebido: {tipo_evento}")
        print(f"Resultado do processamento: {resultado_processamento}")
        
        # Dependendo do tipo de evento, realizar ações adicionais
        # Exemplo: Enviar e-mail de confirmação, atualizar UI, etc.
        
    except Exception as e:
        print(f"Erro ao atualizar banco de dados: {str(e)}")
        import traceback
        traceback.print_exc()

# Executar a função principal se for executado diretamente
if __name__ == "__main__":
    show()