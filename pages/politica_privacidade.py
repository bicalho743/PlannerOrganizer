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
    Esta Política de Privacidade descreve como tratamos os dados pessoais dos usuários da nossa plataforma, 
    em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD).
    """)
    
    st.header("1. Coleta de Dados")
    st.write("""
    Coletamos dados como nome, e-mail, telefone e IP no momento do cadastro ou uso da plataforma. 
    Também podem ser coletados dados de navegação, para fins analíticos.
    """)
    
    st.header("2. Finalidade do Uso")
    st.write("""
    Utilizamos os dados para:
    - Autenticação e acesso à conta
    - Comunicação com o usuário (e-mails transacionais ou promocionais)
    - Aprimoramento da experiência no sistema
    - Fins estatísticos e de segurança
    """)
    
    st.header("3. Compartilhamento de Dados")
    st.write("""
    Os dados poderão ser compartilhados com serviços terceiros (como Firebase, Stripe ou ferramentas de e-mail) 
    apenas quando necessário para o funcionamento do sistema. Nenhum dado é vendido ou divulgado a terceiros 
    sem autorização.
    """)
    
    st.header("4. Segurança da Informação")
    st.write("""
    Utilizamos medidas técnicas e organizacionais para proteger seus dados contra acessos não autorizados, 
    perda ou alteração indevida.
    """)
    
    st.header("5. Direitos do Titular")
    st.write("""
    Você pode, a qualquer momento:
    - Solicitar acesso aos seus dados
    - Corrigir dados incorretos
    - Solicitar exclusão
    - Revogar consentimentos
    """)
    
    st.header("6. Alterações na Política de Privacidade")
    st.write("""
    Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos sobre mudanças 
    significativas e obteremos seu consentimento quando necessário.
    """)
    
    st.header("7. Controlador dos Dados")
    st.write("""
    O controlador dos seus dados pessoais é a empresa Planner Organizer, responsável pelas decisões 
    referentes ao tratamento dos seus dados pessoais.
    """)
    
    st.header("8. Contato para Questões de Privacidade")
    st.write("""
    Para exercer seus direitos ou esclarecer dúvidas sobre esta Política de Privacidade, 
    entre em contato pelo e-mail: privacidade@plannerorganizer.com.br
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