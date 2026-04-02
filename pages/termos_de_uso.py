"""
Página de Termos de Uso para o sistema Planner Organizer
"""
import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

def get_termos_conteudo():
    """Retorna o conteúdo HTML dos termos de uso"""
    return """
    <h1>Termos e Condições de Uso</h1>
    
    <p>
    Bem-vindo ao nosso sistema. Ao utilizar esta plataforma, você concorda com os presentes Termos e Condições de Uso. 
    Leia com atenção antes de prosseguir.
    </p>
    
    <h3>1.1 Aceitação dos Termos</h3>
    <p>
    Ao acessar e utilizar este sistema, o usuário declara que leu, entendeu e concorda com os termos aqui descritos. 
    Caso não concorde, deve se abster de utilizar os serviços.
    </p>
    
    <h3>1.2 Uso da Plataforma</h3>
    <p>
    O sistema deve ser utilizado exclusivamente para fins legais e de acordo com sua finalidade. 
    É proibido o uso indevido, cópia não autorizada, engenharia reversa, ou qualquer ação que 
    comprometa a integridade da plataforma.
    </p>
    
    <h3>1.3 Propriedade Intelectual</h3>
    <p>
    Todos os direitos sobre o sistema, seus códigos, design, funcionalidades e marcas são de 
    propriedade exclusiva da empresa desenvolvedora. O uso não confere qualquer direito sobre esses ativos.
    </p>
    
    <h3>1.4 Responsabilidades do Usuário</h3>
    <p>
    O usuário é responsável por manter seus dados de acesso em sigilo, e por toda atividade realizada com seu login. 
    A empresa não se responsabiliza por acessos indevidos decorrentes de negligência.
    </p>
    
    <h3>1.5 Suspensão e Cancelamento</h3>
    <p>
    Reservamo-nos o direito de suspender ou cancelar o acesso de qualquer usuário que descumpra estes termos, 
    sem necessidade de aviso prévio.
    </p>
    
    <h3>1.6 Alterações nos Termos</h3>
    <p>
    Estes termos poderão ser atualizados periodicamente. O uso contínuo do sistema após alterações 
    será considerado como aceitação das novas condições.
    </p>
    """

def show():
    """Exibe a página de termos de uso"""
    # Ocultar completamente a barra lateral
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    .stSubheader, h2, h3 {
        color: rgba(245,240,232,0.85) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem; color: #C9A84C;">Termos e Condições de Uso</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Bem-vindo ao nosso sistema. Ao utilizar esta plataforma, você concorda com os presentes Termos e Condições de Uso. 
    Leia com atenção antes de prosseguir.
    """)
    
    st.subheader("1.1 Aceitação dos Termos")
    st.write("""
    Ao acessar e utilizar este sistema, o usuário declara que leu, entendeu e concorda com os termos aqui descritos. 
    Caso não concorde, deve se abster de utilizar os serviços.
    """)
    
    st.subheader("1.2 Uso da Plataforma")
    st.write("""
    O sistema deve ser utilizado exclusivamente para fins legais e de acordo com sua finalidade. 
    É proibido o uso indevido, cópia não autorizada, engenharia reversa, ou qualquer ação que 
    comprometa a integridade da plataforma.
    """)
    
    st.subheader("1.3 Propriedade Intelectual")
    st.write("""
    Todos os direitos sobre o sistema, seus códigos, design, funcionalidades e marcas são de 
    propriedade exclusiva da empresa desenvolvedora. O uso não confere qualquer direito sobre esses ativos.
    """)
    
    st.subheader("1.4 Responsabilidades do Usuário")
    st.write("""
    O usuário é responsável por manter seus dados de acesso em sigilo, e por toda atividade realizada com seu login. 
    A empresa não se responsabiliza por acessos indevidos decorrentes de negligência.
    """)
    
    st.subheader("1.5 Suspensão e Cancelamento")
    st.write("""
    Reservamo-nos o direito de suspender ou cancelar o acesso de qualquer usuário que descumpra estes termos, 
    sem necessidade de aviso prévio.
    """)
    
    st.subheader("1.6 Alterações nos Termos")
    st.write("""
    Estes termos poderão ser atualizados periodicamente. O uso contínuo do sistema após alterações 
    será considerado como aceitação das novas condições.
    """)
    
    # Verificar se estamos no fluxo de criação de conta
    if st.session_state.get("creating_account", False):
        # Botões para aceitar/recusar termos
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Aceitar Termos e Criar Conta", type="primary", use_container_width=True):
                # Marcar termos como aceitos e continuar
                st.session_state.termos_aceitos = True
                st.session_state.show_termos = False
                # Redirecionar para o formulário de cadastro
                st.success("Termos aceitos! Prosseguindo com o cadastro...")
                st.rerun()
        
        with col2:
            if st.button("Recusar e Voltar", use_container_width=True):
                # Voltar ao login sem criar a conta
                st.session_state.creating_account = False
                st.session_state.show_termos = False
                st.rerun()
    else:
        # Botão simples para voltar
        if st.button("Voltar"):
            st.session_state.show_termos = False
            st.rerun()

if __name__ == "__main__":
    show()