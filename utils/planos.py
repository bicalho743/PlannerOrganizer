import streamlit as st

def verificar_login():
    """
    Verifica se o usuário está logado e retorna informações básicas
    
    Returns:
        tuple: (usuario_id, usuario_nome, usuario_email) ou (None, None, None) se não estiver logado
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return None, None, None
    
    # Informações básicas do usuário
    usuario = st.session_state.get('usuario', {})
    usuario_id = usuario.get('id', st.session_state.get('usuario_id'))
    usuario_nome = usuario.get('nome', 'Usuário')
    usuario_email = usuario.get('email', '')
    
    return usuario_id, usuario_nome, usuario_email


def mostrar_planos(com_titulo=True, com_prova_social=True, 
                  com_teste_gratis=True, com_destaque_plano_medio=True, 
                  stripe_ready=False, espacamento_reduzido=False):
    """
    Versão simplificada da função de exibição de planos sem assinaturas Stripe.
    Essa função exibe uma mensagem informativa sobre indisponibilidade temporária dos planos.
    
    Args:
        com_titulo (bool): Se deve mostrar o título principal
        com_prova_social (bool): Se deve mostrar seção de depoimentos
        com_teste_gratis (bool): Se deve mostrar a mensagem de teste gratuito
        com_destaque_plano_medio (bool): Se deve destacar o plano do meio
        stripe_ready (bool): Se os botões devem estar preparados para Stripe 
        espacamento_reduzido (bool): Se deve usar espaçamento reduzido
    """
    # Exibir mensagem informativa ao invés dos planos
    st.info("""
    ### Planos de Assinatura Temporariamente Indisponíveis
    
    Estamos atualizando nosso sistema de pagamentos e planos para oferecer uma experiência 
    ainda melhor. Durante este período, todos os usuários têm acesso completo ao sistema.
    
    Por favor, entre em contato pelo email suporte@plannerorganizer.com.br 
    para mais informações.
    """)
    
    # Se solicitado, exibir mensagem sobre período de teste
    if com_teste_gratis:
        st.success("""
        ### Você pode usar o sistema gratuitamente!
        
        Durante o período de atualização, você tem acesso a todas as funcionalidades
        sem nenhum custo.
        """)
    
    # Se solicitado, exibir seção de prova social
    if com_prova_social:
        st.markdown("---")
        st.markdown("### O que nossos clientes dizem")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            > "O Planner Organizer transformou meu negócio! Consigo gerenciar todas as minhas propostas, 
            > clientes e finanças em um só lugar com facilidade e profissionalismo."
            > 
            > — Ana Paula, Personal Organizer
            """)
        
        with col2:
            st.markdown("""
            > "Meu faturamento aumentou 45% depois que comecei a usar o sistema. A gestão de propostas 
            > e o controle financeiro me ajudaram a profissionalizar meu negócio."
            > 
            > — Carlos Eduardo, Organizador Profissional
            """)