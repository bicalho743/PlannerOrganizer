"""
Página de Política de Privacidade para o sistema Planner Organizer
"""
import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

def show():
    """Exibe a página de política de privacidade"""
    # Ocultar completamente a barra lateral
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Política de Privacidade")
    
    st.markdown("""
    Agradecemos por utilizar o Sistema Planner Organizer. A sua privacidade é importante para nós. 
    Esta Política de Privacidade descreve como suas informações pessoais são coletadas, usadas e compartilhadas.
    """)
    
    st.subheader("1. Informações que Coletamos")
    st.write("""
    Coletamos informações que você nos fornece diretamente:
    - Informações de cadastro: nome, e-mail, telefone, credenciais de login
    - Informações de uso: dados sobre como você utiliza nosso sistema
    - Informações de pagamento: quando aplicável para transações financeiras
    """)
    
    st.subheader("2. Como Usamos Suas Informações")
    st.write("""
    Utilizamos suas informações para:
    - Fornecer, manter e melhorar nossos serviços
    - Processar transações e enviar notificações relacionadas
    - Enviar comunicações técnicas, atualizações e mensagens de suporte
    - Responder a seus comentários e perguntas
    - Personalizar sua experiência no sistema
    """)
    
    st.subheader("3. Compartilhamento de Informações")
    st.write("""
    Não vendemos suas informações pessoais a terceiros. Podemos compartilhar informações nas seguintes situações:
    - Com seu consentimento
    - Para cumprir obrigações legais
    - Para proteger direitos e segurança
    - Com provedores de serviços que nos ajudam a operar o sistema
    """)
    
    st.subheader("4. Segurança de Dados")
    st.write("""
    Implementamos medidas técnicas e organizacionais para proteger suas informações contra acesso 
    não autorizado, perda ou alteração. No entanto, nenhum sistema é completamente seguro, 
    e não podemos garantir a segurança absoluta de seus dados.
    """)
    
    st.subheader("5. Seus Direitos")
    st.write("""
    Você tem direito a:
    - Acessar seus dados pessoais
    - Corrigir informações imprecisas
    - Solicitar a exclusão de seus dados
    - Opor-se ao processamento de suas informações
    - Retirar seu consentimento a qualquer momento
    """)
    
    st.subheader("6. Alterações nesta Política")
    st.write("""
    Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos sobre mudanças 
    significativas e obteremos seu consentimento quando necessário.
    """)
    
    # Verificar se estamos no fluxo de criação de conta
    if st.session_state.get("creating_account", False):
        # Botões para aceitar/recusar termos
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Aceitar Política e Continuar", type="primary", use_container_width=True):
                # Marcar política como aceita e continuar
                st.session_state.politica_aceita = True
                st.session_state.show_politica = False
                st.rerun()
        
        with col2:
            if st.button("Recusar e Voltar", use_container_width=True):
                # Voltar ao login sem criar a conta
                st.session_state.show_politica = False
                st.rerun()
    else:
        # Botão simples para voltar
        if st.button("Voltar"):
            st.session_state.show_politica = False
            st.rerun()

if __name__ == "__main__":
    show()