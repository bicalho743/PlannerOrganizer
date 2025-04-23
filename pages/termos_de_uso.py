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

def show():
    """Exibe a página de termos de uso"""
    st.title("Termos e Condições de Uso")
    
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
    
    # Botão para voltar
    if st.button("Voltar"):
        st.session_state.show_termos = False
        st.rerun()

if __name__ == "__main__":
    show()