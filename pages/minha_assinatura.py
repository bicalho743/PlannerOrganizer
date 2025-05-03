"""
Página para exibir e gerenciar assinatura do usuário
"""
import streamlit as st
import os
from datetime import datetime, timedelta
from utils.database import Session, Perfil
from utils.auth import verificar_autenticacao, obter_usuario_atual
from utils.stripe_integration import inicializar_stripe, criar_sessao_checkout, gerar_portal_cliente, verificar_assinatura_ativa, obter_limites_plano

# Constantes
TITULO_PAGINA = "Minha Assinatura"
MENSAGEM_NAO_AUTENTICADO = "Você precisa estar logado para acessar esta página."
MENSAGEM_SEM_ASSINATURA = "Você está utilizando o plano gratuito."
MENSAGEM_CARREGANDO = "Carregando informações da sua assinatura..."

def exibir_informacoes_plano_gratuito():
    """Exibe informações do plano gratuito"""
    st.subheader("Plano Gratuito")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Recursos incluídos:")
        st.markdown("- Até 10 clientes")
        st.markdown("- Até 5 propostas")
        st.markdown("- Funcionalidades básicas")
    
    with col2:
        st.markdown("### Limitações:")
        st.markdown("- Sem acesso a relatórios avançados")
        st.markdown("- Sem dashboards detalhados")
        st.markdown("- Sem automações")
    
    st.markdown("---")
    
    st.info("Atualize para o plano profissional e desfrute de todos os recursos do sistema!")
    
    if st.button("Atualizar para o Plano Profissional", type="primary"):
        st.session_state.mostrar_opcoes_assinatura = True

def exibir_informacoes_plano_profissional(perfil):
    """Exibe informações do plano profissional"""
    st.subheader("Plano Profissional")
    
    # Verificar se temos as colunas de assinatura
    tem_data_expiracao = hasattr(perfil, 'assinatura_expiracao')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Recursos incluídos:")
        st.markdown("- Até 100 clientes")
        st.markdown("- Até 50 propostas")
        st.markdown("- Relatórios avançados")
        st.markdown("- Dashboards detalhados")
        st.markdown("- Todas as funcionalidades")
    
    with col2:
        st.markdown("### Informações da assinatura:")
        
        if tem_data_expiracao and perfil.assinatura_expiracao:
            data_expiracao = perfil.assinatura_expiracao
            dias_restantes = (data_expiracao - datetime.now()).days
            
            st.markdown(f"**Válido até:** {data_expiracao.strftime('%d/%m/%Y')}")
            st.markdown(f"**Dias restantes:** {dias_restantes}")
            
            if dias_restantes <= 7:
                st.warning(f"Sua assinatura expira em {dias_restantes} dias!")
        else:
            st.markdown("**Status:** Ativo")
    
    st.markdown("---")
    
    # Botão para acessar portal do cliente no Stripe
    if st.button("Gerenciar Assinatura", type="secondary"):
        try:
            with st.spinner("Carregando portal de gerenciamento..."):
                if hasattr(perfil, 'cliente_stripe_id') and perfil.cliente_stripe_id:
                    portal_url = gerar_portal_cliente(perfil)
                    # Redirecionar para o portal do cliente
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={portal_url}">', unsafe_allow_html=True)
                else:
                    st.error("Não foi possível gerar o link para o portal. Entre em contato com o suporte.")
        except Exception as e:
            st.error(f"Erro ao acessar o portal: {str(e)}")

def exibir_opcoes_assinatura(perfil):
    """Exibe opções de planos para assinatura"""
    st.subheader("Escolha seu plano")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Plano Mensal")
        st.markdown("**R$ 49,90 / mês**")
        st.markdown("- Acesso a todos os recursos")
        st.markdown("- Cancele a qualquer momento")
        st.markdown("- Suporte prioritário")
        
        if st.button("Escolher Plano Mensal", key="mensal"):
            try:
                with st.spinner("Criando sua assinatura..."):
                    inicializar_stripe()
                    session = Session()
                    checkout_url = criar_sessao_checkout(perfil, 'profissional', 'mensal', session)
                    session.close()
                    
                    # Redirecionar para o checkout
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro ao criar assinatura: {str(e)}")
    
    with col2:
        st.markdown("### Plano Anual")
        st.markdown("**R$ 499,00 / ano**")
        st.markdown("- Economize 2 meses grátis")
        st.markdown("- Acesso a todos os recursos")
        st.markdown("- Suporte prioritário")
        
        if st.button("Escolher Plano Anual", key="anual"):
            try:
                with st.spinner("Criando sua assinatura..."):
                    inicializar_stripe()
                    session = Session()
                    checkout_url = criar_sessao_checkout(perfil, 'profissional', 'anual', session)
                    session.close()
                    
                    # Redirecionar para o checkout
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro ao criar assinatura: {str(e)}")
    
    st.markdown("---")
    st.caption("Clique em um dos botões acima para ser redirecionado para o checkout seguro do Stripe.")
    st.caption("A cobrança será realizada pela Planner Organizer através do Stripe.")

def exibir_status_uso(perfil):
    """Exibe o status de uso do plano atual"""
    st.subheader("Status de Uso")
    
    try:
        session = Session()
        
        # Importações aqui para evitar referência circular
        from utils.database import Cliente, Proposta
        
        # Contar itens do usuário
        num_clientes = session.query(Cliente).filter_by(usuario_id=perfil.usuario_id).count()
        num_propostas = session.query(Proposta).filter_by(usuario_id=perfil.usuario_id).count()
        
        # Obter limites do plano
        limites = obter_limites_plano(perfil)
        limite_clientes = limites.get('limite_clientes', 10)
        limite_propostas = limites.get('limite_propostas', 5)
        
        # Calcular percentuais
        pct_clientes = min(100, int((num_clientes / limite_clientes) * 100))
        pct_propostas = min(100, int((num_propostas / limite_propostas) * 100))
        
        # Exibir barras de progresso
        st.markdown("### Clientes")
        st.progress(pct_clientes / 100)
        st.caption(f"{num_clientes} de {limite_clientes} clientes ({pct_clientes}%)")
        
        st.markdown("### Propostas")
        st.progress(pct_propostas / 100)
        st.caption(f"{num_propostas} de {limite_propostas} propostas ({pct_propostas}%)")
        
        # Alertas
        if pct_clientes >= 90:
            st.warning(f"Você está próximo do limite de clientes! Considere atualizar seu plano.")
        
        if pct_propostas >= 90:
            st.warning(f"Você está próximo do limite de propostas! Considere atualizar seu plano.")
            
        session.close()
    except Exception as e:
        st.error(f"Erro ao carregar status de uso: {str(e)}")

def main():
    st.set_page_config(
        page_title=TITULO_PAGINA,
        page_icon="💳",
        layout="wide"
    )
    
    st.title(TITULO_PAGINA)
    
    # Verificar se o usuário está autenticado
    if not verificar_autenticacao():
        st.warning(MENSAGEM_NAO_AUTENTICADO)
        st.stop()
    
    # Obter informações do usuário atual
    usuario_id = obter_usuario_atual()
    
    # Iniciar sessão do banco
    session = Session()
    
    try:
        # Buscar perfil do usuário
        perfil = session.query(Perfil).filter_by(usuario_id=usuario_id).first()
        
        if not perfil:
            st.error("Perfil não encontrado. Entre em contato com o suporte.")
            st.stop()
        
        # Mostrar informações da assinatura
        if "mostrar_opcoes_assinatura" in st.session_state and st.session_state.mostrar_opcoes_assinatura:
            exibir_opcoes_assinatura(perfil)
            
            if st.button("Voltar"):
                st.session_state.mostrar_opcoes_assinatura = False
                st.rerun()
        else:
            # Verificar tipo de plano
            if perfil.plano == 'gratuito':
                exibir_informacoes_plano_gratuito()
            else:
                exibir_informacoes_plano_profissional(perfil)
            
            # Exibir status de uso
            st.markdown("---")
            exibir_status_uso(perfil)
    
    except Exception as e:
        st.error(f"Erro ao carregar informações da assinatura: {str(e)}")
    
    finally:
        session.close()

if __name__ == "__main__":
    main()