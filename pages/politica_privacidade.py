"""
Página de Política de Privacidade para o sistema Planner Organizer
"""
import streamlit as st
import os
import sys

project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

def get_politica_conteudo():
    """Retorna o conteúdo HTML da política de privacidade"""
    return """
    <h1>Política de Privacidade</h1>
    
    <p>
    Esta Política de Privacidade descreve como tratamos os dados pessoais dos usuários da nossa plataforma, 
    em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD).
    </p>
    
    <h2>1. Coleta de Dados</h2>
    <p>
    Coletamos dados como nome, e-mail, telefone e IP no momento do cadastro ou uso da plataforma. 
    Também podem ser coletados dados de navegação, para fins analíticos.
    </p>
    
    <h2>2. Finalidade do Uso</h2>
    <p>
    Utilizamos os dados para:
    <ul>
    <li>Autenticação e acesso à conta</li>
    <li>Comunicação com o usuário (e-mails transacionais ou promocionais)</li>
    <li>Aprimoramento da experiência no sistema</li>
    <li>Fins estatísticos e de segurança</li>
    </ul>
    </p>
    
    <h2>3. Compartilhamento de Dados</h2>
    <p>
    Os dados poderão ser compartilhados com serviços terceiros (como Firebase ou ferramentas de e-mail) 
    apenas quando necessário para o funcionamento do sistema. Nenhum dado é vendido ou divulgado a terceiros 
    sem autorização.
    </p>
    
    <h2>4. Segurança da Informação</h2>
    <p>
    Utilizamos medidas técnicas e organizacionais para proteger seus dados contra acessos não autorizados, 
    perda ou alteração indevida.
    </p>
    
    <h2>5. Direitos do Titular</h2>
    <p>
    Você pode, a qualquer momento:
    <ul>
    <li>Solicitar acesso aos seus dados</li>
    <li>Corrigir dados incorretos</li>
    <li>Solicitar exclusão</li>
    <li>Revogar consentimentos</li>
    </ul>
    </p>
    
    <h2>6. Alterações na Política de Privacidade</h2>
    <p>
    Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos sobre mudanças 
    significativas e obteremos seu consentimento quando necessário.
    </p>
    
    <h2>7. Controlador dos Dados</h2>
    <p>
    O controlador dos seus dados pessoais é a empresa Planner Organizer, responsável pelas decisões 
    referentes ao tratamento dos seus dados pessoais.
    </p>
    
    <h2>8. Contato para Questões de Privacidade</h2>
    <p>
    Para exercer seus direitos ou esclarecer dúvidas sobre esta Política de Privacidade, 
    entre em contato pelo e-mail: privacidade@plannerorganizer.com.br
    </p>
    """

def show():
    """Exibe a página de política de privacidade"""
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .block-container {
        max-width: 900px !important;
        margin: 0 auto !important;
        padding: 2rem 3rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="color: #C9A84C; font-size: 1.8rem; margin-bottom: 0.5rem;">Política de Privacidade</h1>', unsafe_allow_html=True)

    st.markdown('<p style="color: rgba(245,240,232,0.6); margin-bottom: 2rem;">Esta Política de Privacidade descreve como tratamos os dados pessoais dos usuários da nossa plataforma, em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD).</p>', unsafe_allow_html=True)

    secoes = [
        ("1. Coleta de Dados",
         "Coletamos dados como nome, e-mail, telefone e IP no momento do cadastro ou uso da plataforma. Também podem ser coletados dados de navegação, para fins analíticos.",
         None),
        ("2. Finalidade do Uso",
         "Utilizamos os dados para:",
         ["Autenticação e acesso à conta",
          "Comunicação com o usuário (e-mails transacionais ou promocionais)",
          "Aprimoramento da experiência no sistema",
          "Fins estatísticos e de segurança"]),
        ("3. Compartilhamento de Dados",
         "Os dados poderão ser compartilhados com serviços terceiros (como Firebase ou ferramentas de e-mail) apenas quando necessário para o funcionamento do sistema. Nenhum dado é vendido ou divulgado a terceiros sem autorização.",
         None),
        ("4. Segurança da Informação",
         "Utilizamos medidas técnicas e organizacionais para proteger seus dados contra acessos não autorizados, perda ou alteração indevida.",
         None),
        ("5. Direitos do Titular",
         "Você pode, a qualquer momento:",
         ["Solicitar acesso aos seus dados",
          "Corrigir dados incorretos",
          "Solicitar exclusão",
          "Revogar consentimentos"]),
        ("6. Alterações na Política de Privacidade",
         "Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos sobre mudanças significativas e obteremos seu consentimento quando necessário.",
         None),
        ("7. Controlador dos Dados",
         "O controlador dos seus dados pessoais é a empresa Planner Organizer, responsável pelas decisões referentes ao tratamento dos seus dados pessoais.",
         None),
        ("8. Contato para Questões de Privacidade",
         'Para exercer seus direitos ou esclarecer dúvidas sobre esta Política de Privacidade, entre em contato pelo e-mail: <span style="color: #C9A84C;">privacidade@plannerorganizer.com.br</span>',
         None),
    ]

    for titulo, texto, lista in secoes:
        st.markdown(f'<h3 style="color: #C9A84C; font-size: 1.1rem; margin-top: 1.5rem;">{titulo}</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: rgba(245,240,232,0.85); line-height: 1.8; font-size: 0.95rem;">{texto}</p>', unsafe_allow_html=True)
        if lista:
            items_html = "".join(f"<li>{item}</li>" for item in lista)
            st.markdown(f'<ul style="color: rgba(245,240,232,0.85); line-height: 2; font-size: 0.95rem; margin-left: 1.5rem;">{items_html}</ul>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("creating_account", False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aceitar Política e Continuar", type="primary", use_container_width=True):
                st.session_state.politica_aceita = True
                st.session_state.show_politica = False
                st.rerun()
        with col2:
            if st.button("Recusar e Voltar", use_container_width=True):
                st.session_state.show_politica = False
                st.rerun()
    else:
        if st.button("← Voltar"):
            st.session_state.show_politica = False
            st.rerun()

if __name__ == "__main__":
    show()
