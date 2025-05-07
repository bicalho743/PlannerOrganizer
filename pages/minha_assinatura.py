"""
Página para gerenciamento de assinatura do usuário
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Importações para autenticação
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

# Importações para stripe e assinaturas
from utils.import_assinaturas import (
    obter_assinatura_usuario,
    cancelar_assinatura_stripe,
    cancelar_assinatura,
    mudar_plano_assinatura,
    criar_sessao_checkout
)

def show():
    """Exibe a página de gerenciamento de assinatura"""
    # Configuração da página
    st.set_page_config(
        page_title="Minha Assinatura - Planner Organiza",
        page_icon="💳",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Verificar login
    user = check_login()
    
    if not user:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.info("Redirecionando para a página de login...")
        st.session_state['redirect'] = "/minha_assinatura"
        st.button("Ir para Login", on_click=lambda: st._rerun())
        return
    
    # Extrair dados do usuário
    usuario_id = user.get('localId')
    usuario_nome = user.get('displayName', 'Usuário')
    usuario_email = user.get('email', 'email@exemplo.com')
    
    # Cabeçalho
    st.title("Minha Assinatura")
    
    # Verificar status da URL
    status = st.experimental_get_query_params().get('status', [None])[0]
    if status == 'success':
        st.success("Pagamento processado com sucesso! Sua assinatura foi ativada.")
        # Limpar o parâmetro da URL para evitar mensagens repetidas
        st.experimental_set_query_params()
    elif status == 'cancel':
        st.warning("Pagamento cancelado. Sua assinatura não foi alterada.")
        # Limpar o parâmetro da URL para evitar mensagens repetidas
        st.experimental_set_query_params()
    elif status == 'trial_success':
        st.success("Período de teste gratuito iniciado com sucesso! Você agora tem acesso a todas as funcionalidades do sistema por 7 dias.")
        # Limpar o parâmetro da URL para evitar mensagens repetidas
        st.experimental_set_query_params()
    
    # Obter informações da assinatura atual
    resultado_assinatura = obter_assinatura_usuario(usuario_id)
    
    # Se não tem assinatura, mostrar opções de inscrição
    if not resultado_assinatura.get('sucesso'):
        st.info("Você ainda não possui uma assinatura.")
        
        st.markdown("""
        ## Escolha um plano para começar
        
        Assine o Planner Organiza e tenha acesso a todas as funcionalidades.
        """)
        
        # Botão para ir para a página de planos
        if st.button("Ver Planos Disponíveis", type="primary"):
            st.session_state['redirect'] = "/planos"
            st._rerun()
            
        return
    
    # Extrair informações da assinatura
    assinatura = resultado_assinatura.get('assinatura', {})
    
    # Informações da assinatura
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("## Detalhes da Assinatura")
            
            # Extração de dados do dicionário assinatura com valores padrão
            plano_atual = assinatura.get('plano', 'Não definido')
            status_assinatura = assinatura.get('status', 'Indefinido')
            data_inicio = assinatura.get('data_inicio')
            data_fim = assinatura.get('data_fim')
            customer_id = assinatura.get('customer_id')
            
            # Calcular dias restantes
            dias_restantes = float('inf')
            if data_fim and isinstance(data_fim, datetime):
                dias_restantes = (data_fim - datetime.now()).days
                if dias_restantes < 0:
                    dias_restantes = 0
            
            st.markdown(f"**Plano atual:** {plano_atual}")
            
            # Datas formatadas
            if data_inicio:
                data_inicio_formatada = data_inicio.strftime("%d/%m/%Y") if isinstance(data_inicio, datetime) else data_inicio
                st.markdown(f"**Data de início:** {data_inicio_formatada}")
            
            st.markdown(f"**Status:** {status_assinatura}")
            
            if data_fim and status_assinatura == 'ativo':
                data_fim_formatada = data_fim.strftime("%d/%m/%Y") if isinstance(data_fim, datetime) else data_fim
                st.markdown(f"**Válido até:** {data_fim_formatada}")
                
                if plano_atual.lower() != 'vitalicio' and dias_restantes < float('inf'):
                    # Mostrar contagem regressiva se estiver perto do vencimento
                    if dias_restantes <= 7:
                        st.warning(f"Sua assinatura expira em {dias_restantes} dias.")
                    else:
                        st.info(f"Tempo restante: {dias_restantes} dias")
        
        with col2:
            # Se tiver customer_id, mostrar opção para gerenciar pagamentos no Stripe
            if customer_id:
                st.markdown("## Gerenciar Pagamentos")
                
                # URL para portal de clientes do Stripe
                portal_url = criar_sessao_portal_cliente(customer_id)
                
                if portal_url:
                    st.markdown(f"""
                    <a href="{portal_url}" target="_blank" style="
                        display: inline-block;
                        background-color: #1E88E5;
                        color: white;
                        padding: 0.5rem 1rem;
                        text-decoration: none;
                        border-radius: 4px;
                        text-align: center;
                        margin-top: 1rem;
                    ">Gerenciar Método de Pagamento</a>
                    """, unsafe_allow_html=True)
    
    # Separador
    st.markdown("---")
    
    # Opções da assinatura
    st.markdown("## Opções da Assinatura")
    
    # Mostrar opções diferentes dependendo do status e plano
    if status_assinatura == 'ativo':
        # Opções diferentes para cada plano
        if plano_atual.lower() == 'mensal':
            with st.expander("Mudar para plano Anual (economia de 17%)"):
                st.markdown("""
                Ao mudar para o plano anual, você economiza aproximadamente 17% em comparação ao pagamento mensal.
                
                **Plano Anual:** R$ 97,00 por ano (equivalente a R$ 8,08 por mês)
                """)
                
                if st.button("Mudar para Plano Anual"):
                    # Criar checkout para upgrade
                    price_id = os.environ.get('STRIPE_PRICE_ID_ANUAL')
                    if price_id:
                        success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
                        cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=cancel"
                        
                        resultado = criar_sessao_checkout(
                            price_id=price_id,
                            usuario_id=usuario_id,
                            usuario_email=usuario_email,
                            usuario_nome=usuario_nome,
                            success_url=success_url,
                            cancel_url=cancel_url
                        )
                        
                        if resultado.get('success'):
                            st.markdown(f"""
                            <script>
                                window.location.href = "{resultado.get('checkout_url')}";
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Erro ao criar sessão de checkout: {resultado.get('message')}")
            
            with st.expander("Mudar para plano Vitalício (pague uma vez, use para sempre)"):
                st.markdown("""
                Com o plano vitalício, você faz um único pagamento e tem acesso permanente a todas as funcionalidades do sistema, incluindo atualizações futuras.
                
                **Plano Vitalício:** R$ 247,00 (pagamento único)
                """)
                
                if st.button("Mudar para Plano Vitalício"):
                    # Criar checkout para upgrade
                    price_id = os.environ.get('STRIPE_PRICE_ID_VITALICIO')
                    if price_id:
                        success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
                        cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=cancel"
                        
                        resultado = criar_sessao_checkout(
                            price_id=price_id,
                            usuario_id=usuario_id,
                            usuario_email=usuario_email,
                            usuario_nome=usuario_nome,
                            success_url=success_url,
                            cancel_url=cancel_url
                        )
                        
                        if resultado.get('success'):
                            st.markdown(f"""
                            <script>
                                window.location.href = "{resultado.get('checkout_url')}";
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Erro ao criar sessão de checkout: {resultado.get('message')}")
        
        elif plano_atual.lower() == 'anual':
            with st.expander("Mudar para plano Vitalício (pague uma vez, use para sempre)"):
                st.markdown("""
                Com o plano vitalício, você faz um único pagamento e tem acesso permanente a todas as funcionalidades do sistema, incluindo atualizações futuras.
                
                **Plano Vitalício:** R$ 247,00 (pagamento único)
                """)
                
                if st.button("Mudar para Plano Vitalício"):
                    # Criar checkout para upgrade
                    price_id = os.environ.get('STRIPE_PRICE_ID_VITALICIO')
                    if price_id:
                        success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
                        cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=cancel"
                        
                        resultado = criar_sessao_checkout(
                            price_id=price_id,
                            usuario_id=usuario_id,
                            usuario_email=usuario_email,
                            usuario_nome=usuario_nome,
                            success_url=success_url,
                            cancel_url=cancel_url
                        )
                        
                        if resultado.get('success'):
                            st.markdown(f"""
                            <script>
                                window.location.href = "{resultado.get('checkout_url')}";
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Erro ao criar sessão de checkout: {resultado.get('message')}")
        
        elif plano_atual.lower() == 'vitalicio':
            st.success("Você já possui o melhor plano disponível! Aproveite todas as funcionalidades vitalícias do Planner Organiza.")
        
        # Opção de cancelamento para planos não-vitalícios
        if plano_atual.lower() != 'vitalicio':
            with st.expander("Cancelar assinatura"):
                st.markdown("""
                ⚠️ **Atenção:** Ao cancelar sua assinatura, você perderá acesso às funcionalidades premium após o período atual pago.
                """)
                
                motivo = st.selectbox(
                    "Motivo do cancelamento",
                    [
                        "Selecione um motivo...",
                        "Estou insatisfeito com o serviço",
                        "Encontrei uma alternativa melhor",
                        "É muito caro",
                        "Não estou usando o suficiente",
                        "Problemas técnicos",
                        "Outro motivo"
                    ]
                )
                
                outro_motivo = ""
                if motivo == "Outro motivo":
                    outro_motivo = st.text_area("Por favor, descreva o motivo do cancelamento")
                
                cancelar = st.button("Confirmar Cancelamento", type="primary")
                
                if cancelar:
                    if motivo == "Selecione um motivo...":
                        st.error("Por favor, selecione um motivo para o cancelamento.")
                    elif motivo == "Outro motivo" and not outro_motivo:
                        st.error("Por favor, descreva o motivo do cancelamento.")
                    else:
                        motivo_final = outro_motivo if motivo == "Outro motivo" else motivo
                        
                        # Cancelar no Stripe primeiro
                        subscription_id = assinatura.get('subscription_id')
                        if subscription_id:
                            resultado_stripe = cancelar_assinatura_stripe(subscription_id)
                            
                            if not resultado_stripe.get('success'):
                                st.error(f"Erro ao cancelar assinatura no Stripe: {resultado_stripe.get('message')}")
                                return
                        
                        # Cancelar no banco de dados
                        resultado = cancelar_assinatura(usuario_id, motivo_final)
                        
                        if resultado.get('sucesso'):
                            st.success("Assinatura cancelada com sucesso.")
                            st.info("Você continuará tendo acesso até o final do período pago.")
                            st.button("Atualizar página", on_click=lambda: st._rerun())
                        else:
                            st.error(f"Erro ao cancelar assinatura: {resultado.get('mensagem')}")
    
    elif status_assinatura == 'cancelado':
        st.warning("Sua assinatura está cancelada.")
        
        # Botão para reativar
        if st.button("Assinar Novamente", type="primary"):
            st.session_state['redirect'] = "/planos"
            st._rerun()
    
    elif status_assinatura == 'expirado':
        st.warning("Sua assinatura expirou.")
        
        # Botão para renovar
        if st.button("Renovar Assinatura", type="primary"):
            st.session_state['redirect'] = "/planos"
            st._rerun()
            
    elif status_assinatura == 'trial':
        # Calcular dias restantes do período de teste
        dias_restantes_trial = float('inf')
        if data_fim and isinstance(data_fim, datetime):
            dias_restantes_trial = (data_fim - datetime.now()).days
            if dias_restantes_trial < 0:
                dias_restantes_trial = 0
                
        data_fim_formatada = data_fim.strftime("%d/%m/%Y") if isinstance(data_fim, datetime) else data_fim
                
        # Exibir informações do período de teste
        st.info(f"Você está em um período de teste gratuito que termina em {data_fim_formatada}.")
        
        if dias_restantes_trial <= 2:
            st.warning(f"Seu período de teste termina em {dias_restantes_trial} dias! Assine um plano para continuar tendo acesso.")
        else:
            st.success(f"Restam {dias_restantes_trial} dias de teste. Aproveite todas as funcionalidades!")
        
        # Adicionar container para botões de assinatura
        st.markdown("### Escolha um plano para continuar após o período de teste")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Mensal")
            st.markdown("R$ 9,90/mês")
            
            # Botão para plano mensal
            if st.button("Assinar Plano Mensal", key="trial_mensal"):
                # Criar checkout para plano mensal
                price_id = os.environ.get('STRIPE_PRICE_ID_MENSAL')
                if price_id:
                    success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
                    cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=cancel"
                    
                    resultado = criar_sessao_checkout(
                        price_id=price_id,
                        usuario_id=usuario_id,
                        usuario_email=usuario_email,
                        usuario_nome=usuario_nome,
                        success_url=success_url,
                        cancel_url=cancel_url
                    )
                    
                    if resultado.get('success'):
                        st.markdown(f"""
                        <script>
                            window.location.href = "{resultado.get('checkout_url')}";
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Erro ao criar sessão de checkout: {resultado.get('message')}")
                        
        with col2:
            st.markdown("#### Anual")
            st.markdown("R$ 97,00/ano")
            st.markdown("*Economia de 17%*")
            
            # Botão para plano anual
            if st.button("Assinar Plano Anual", key="trial_anual"):
                # Criar checkout para plano anual
                price_id = os.environ.get('STRIPE_PRICE_ID_ANUAL')
                if price_id:
                    success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
                    cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=cancel"
                    
                    resultado = criar_sessao_checkout(
                        price_id=price_id,
                        usuario_id=usuario_id,
                        usuario_email=usuario_email,
                        usuario_nome=usuario_nome,
                        success_url=success_url,
                        cancel_url=cancel_url
                    )
                    
                    if resultado.get('success'):
                        st.markdown(f"""
                        <script>
                            window.location.href = "{resultado.get('checkout_url')}";
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Erro ao criar sessão de checkout: {resultado.get('message')}")
                        
        with col3:
            st.markdown("#### Vitalício")
            st.markdown("R$ 247,00")
            st.markdown("*Pague uma vez, use para sempre*")
            
            # Botão para plano vitalício
            if st.button("Assinar Plano Vitalício", key="trial_vitalicio"):
                # Criar checkout para plano vitalício
                price_id = os.environ.get('STRIPE_PRICE_ID_VITALICIO')
                if price_id:
                    success_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=success"
                    cancel_url = os.environ.get('APP_URL', 'http://localhost:5000') + "/minha_assinatura?status=cancel"
                    
                    resultado = criar_sessao_checkout(
                        price_id=price_id,
                        usuario_id=usuario_id,
                        usuario_email=usuario_email,
                        usuario_nome=usuario_nome,
                        success_url=success_url,
                        cancel_url=cancel_url
                    )
                    
                    if resultado.get('success'):
                        st.markdown(f"""
                        <script>
                            window.location.href = "{resultado.get('checkout_url')}";
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Erro ao criar sessão de checkout: {resultado.get('message')}")
    
    # Histórico de pagamentos
    st.markdown("## Histórico de Transações")
    
    # Aqui iria o código para recuperar o histórico de pagamentos do Stripe
    # Como isso exige comunicação com a API do Stripe, estamos simplificando
    
    if 'customer_id' in assinatura and customer_id:
        st.info("Para visualizar seu histórico completo de transações, acesse o portal de gerenciamento de pagamentos.")
    else:
        st.info("Histórico de transações não disponível.")

    # Verificar se existe redirecionamento e executar
    if st.session_state.get('redirect'):
        redirect_url = st.session_state.pop('redirect')
        st.markdown(f"""
        <script>
            window.location.href = "{redirect_url}";
        </script>
        """, unsafe_allow_html=True)

# Função auxiliar para criar sessão do portal de clientes do Stripe
def criar_sessao_portal_cliente(customer_id):
    """
    Cria uma sessão do portal de clientes do Stripe
    
    Args:
        customer_id: ID do cliente no Stripe
        
    Returns:
        str: URL da sessão ou None em caso de erro
    """
    try:
        from utils.import_assinaturas import criar_sessao_portal_cliente
        resultado = criar_sessao_portal_cliente(customer_id)
        
        if resultado.get('success'):
            return resultado.get('url')
        
        return None
    except Exception as e:
        print(f"Erro ao criar sessão do portal: {str(e)}")
        return None

if __name__ == "__main__":
    show()