"""
Implementação da página de planos otimizada para integração direta no fluxo do aplicativo.
Esta abordagem evita problemas de navegação e redirecionamento, oferecendo uma experiência mais fluida.
"""
import streamlit as st
from datetime import datetime, timedelta
from utils.assinatura_db import iniciar_periodo_teste, verificar_assinatura_ativa

def show():
    """Exibe a página de planos integrada com o fluxo de teste gratuito"""
    st.title("Planos e Preços")
    
    # Verificação de login
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        usuario_id = None
        usuario_nome = None
        usuario_email = None
        tem_assinatura = False
    else:
        # Informações do usuário logado
        usuario = st.session_state.get('usuario', {})
        usuario_id = usuario.get('id', usuario.get('uid'))
        usuario_nome = usuario.get('nome', 'Usuário')
        usuario_email = usuario.get('email', '')
        
        # Verificar se já existe uma assinatura ativa
        if usuario_id:
            resultado_verificacao = verificar_assinatura_ativa(usuario_id)
            tem_assinatura = resultado_verificacao.get('sucesso') and resultado_verificacao.get('assinatura_ativa')
        else:
            tem_assinatura = False
    
    # CSS personalizado para os cartões de plano
    st.markdown("""
    <style>
    .pricing-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 30px 0;
        flex-wrap: wrap;
    }
    .pricing-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 25px;
        width: 250px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .pricing-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    .pricing-card.highlight {
        border: 2px solid #2d8cff;
    }
    .pricing-card.highlight::before {
        content: 'MAIS POPULAR';
        position: absolute;
        top: 10px;
        right: -30px;
        background-color: #2d8cff;
        color: white;
        font-size: 12px;
        font-weight: bold;
        padding: 5px 30px;
        transform: rotate(45deg);
    }
    .pricing-name {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 5px;
    }
    .pricing-price {
        font-size: 2rem;
        font-weight: 700;
        color: #2d8cff;
        margin: 10px 0;
    }
    .pricing-period {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 15px;
    }
    .pricing-feature {
        display: flex;
        align-items: center;
        margin: 8px 0;
        font-size: 0.95rem;
        color: #333;
    }
    .pricing-feature svg {
        margin-right: 8px;
        color: #2d8cff;
    }
    .pricing-button {
        display: block;
        background-color: #2d8cff;
        color: white;
        text-align: center;
        padding: 12px;
        border-radius: 4px;
        font-weight: 600;
        margin-top: 20px;
        transition: background-color 0.3s ease;
        text-decoration: none;
        cursor: pointer;
    }
    .pricing-button:hover {
        background-color: #0062cc;
    }
    .pricing-button.outline {
        background-color: transparent;
        border: 2px solid #2d8cff;
        color: #2d8cff;
    }
    .pricing-button.outline:hover {
        background-color: #f0f7ff;
    }
    .pricing-button.highlight {
        background-color: #2d8cff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Conteúdo principal
    st.markdown("""
    <div style="text-align: center; max-width: 800px; margin: 0 auto;">
        <h1 style="margin-bottom: 1rem;">Escolha o Plano Ideal para o Seu Negócio</h1>
        <p style="font-size: 1.1rem; margin-bottom: 2rem; color: #666;">
            Gerencie suas propostas, clientes e finanças com a plataforma mais completa do mercado.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cartões de preços
    st.markdown("""
    <div class="pricing-container">
        <div class="pricing-card">
            <div class="pricing-name">Mensal</div>
            <div class="pricing-price">R$ 49,90</div>
            <div class="pricing-period">por mês</div>
            
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Propostas ilimitadas
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Controle financeiro
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Relatórios personalizados
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Suporte por e-mail
            </div>
            
            <a href="/api/checkout/mensal" class="pricing-button">ASSINAR AGORA</a>
        </div>
        
        <div class="pricing-card highlight">
            <div class="pricing-name">Anual</div>
            <div class="pricing-price">R$ 399,90</div>
            <div class="pricing-period">por ano (2 meses grátis)</div>
            
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Propostas ilimitadas
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Controle financeiro avançado
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Relatórios avançados
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Suporte prioritário
            </div>
            
            <a href="/api/checkout/anual" class="pricing-button highlight">ASSINAR AGORA</a>
        </div>
        
        <div class="pricing-card">
            <div class="pricing-name">Vitalício</div>
            <div class="pricing-price">R$ 1499,90</div>
            <div class="pricing-period">pagamento único</div>
            
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Propostas ilimitadas
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Todos os recursos disponíveis
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Atualizações para sempre
            </div>
            <div class="pricing-feature">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
                Suporte VIP
            </div>
            
            <a href="/api/checkout/vitalicio" class="pricing-button">ASSINAR AGORA</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de Teste Gratuito
    if usuario_id and not tem_assinatura:
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h2>Experimente Grátis por 7 Dias</h2>
            <p>Acesse todas as funcionalidades sem compromisso.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Container para o formulário de teste gratuito
        with st.container():
            st.markdown("### Iniciar Período de Teste Gratuito")
            st.markdown("Você terá acesso a todas as funcionalidades por 7 dias, sem necessidade de cartão de crédito.")
            
            aceito_termos = st.checkbox("Li e concordo com os Termos de Serviço")
            
            if st.button("INICIAR PERÍODO GRATUITO", disabled=not aceito_termos, type="primary"):
                with st.spinner("Processando..."):
                    # Iniciar período de teste
                    resultado = iniciar_periodo_teste(usuario_id, dias=7)
                    
                    if resultado.get('sucesso'):
                        st.success("Período de teste iniciado com sucesso!")
                        st.balloons()
                        
                        # Enviar e-mail de confirmação
                        try:
                            from utils.email_sender import enviar_confirmacao_teste
                            data_fim = (datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')
                            enviar_confirmacao_teste(
                                destinatario=usuario_email,
                                nome=usuario_nome,
                                data_fim=data_fim
                            )
                        except Exception as e:
                            print(f"Erro ao enviar e-mail: {str(e)}")
                        
                        st.markdown("""
                        <script>
                            setTimeout(function() {
                                window.location.href = "/minha_assinatura?status=trial_success";
                            }, 2000);
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Erro ao iniciar período de teste: {resultado.get('mensagem', 'Erro desconhecido')}")
    elif not usuario_id:
        st.warning("Para iniciar o período de teste gratuito, você precisa estar logado. Faça login para continuar.")
        
        # Adicionar botão para login
        if st.button("Fazer Login"):
            st.markdown("""
            <script>
                window.location.href = "/?redirect=/planos_integrado";
            </script>
            """, unsafe_allow_html=True)
    elif tem_assinatura:
        st.info("Você já possui um plano ativo. Confira mais detalhes na seção Minha Assinatura.")
    
    # Seção final com chamada para ação
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2>Pronto para começar?</h2>
        <p style="margin-bottom: 2rem;">Escolha o plano que melhor se adapta às suas necessidades e leve seu negócio de organização para o próximo nível.</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    show()

if __name__ == "__main__":
    main()