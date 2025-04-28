"""
Versão alternativa do app para contornar problemas de SQLAlchemy no Render
Esta versão usa a classe DirectDB para acessar o banco de dados diretamente via psycopg2
Copie este arquivo para app.py no Render se estiver tendo problemas com o SQLAlchemy
"""
import os
import json
import streamlit as st
from datetime import datetime
from utils.direct_db import DirectDB
from utils.firebase_auth import FirebaseAuth

# Configuração da página
st.set_page_config(
    page_title="Planner Organiza - Sistema Profissional",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Inicializar variáveis de sessão"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'show_termos' not in st.session_state:
        st.session_state.show_termos = False
    if 'show_politica' not in st.session_state:
        st.session_state.show_politica = False

def verify_database():
    """Verifica e corrige estrutura do banco para o ambiente Render"""
    try:
        direct_db = DirectDB()
        result = direct_db.update_database_schema()
        if result['status'] == 'success':
            print(f"Verificação do banco de dados concluída: {result['message']}")
        else:
            print(f"ERRO na verificação do banco: {result['message']}")
        direct_db.close()
        return result
    except Exception as e:
        print(f"Exceção durante verificação do banco: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def login_page():
    """Mostra página de login"""
    # Cabeçalho
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("app-icon.svg", width=150)
        st.title("Planner Organiza")
        st.subheader("Sistema de Gerenciamento Profissional")
    
    # Formulário de login
    with st.form("login_form"):
        email = st.text_input("Email", key="email")
        password = st.text_input("Senha", type="password", key="password")
        submit_button = st.form_submit_button("Entrar")
        
        if submit_button:
            auth = FirebaseAuth()
            result = auth.login_user(email, password)
            
            if result["status"] == "success":
                st.session_state.logged_in = True
                st.session_state.user_info = result["user"]
                st.rerun()
            else:
                st.error(result["message"])
    
    # Links para registro/recuperação
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Registrar nova conta"):
            st.switch_page("pages/registrar.py")
    with c2:
        if st.button("Esqueci minha senha"):
            st.switch_page("pages/recuperar_senha.py")
    
    # Links para termos e política
    st.markdown("---")
    t1, t2, t3 = st.columns([2, 2, 3])
    with t1:
        if st.button("Termos de Uso"):
            st.session_state.show_termos = True
    with t2:
        if st.button("Política de Privacidade"):
            st.session_state.show_politica = True

def show_termos():
    """Mostra a página de termos de uso"""
    st.title("Termos de Uso")
    
    st.markdown("""
    ## Termos de Uso do Sistema Planner Organiza

    ### 1. ACEITAÇÃO DOS TERMOS
    Ao acessar e utilizar o Sistema Planner Organiza, você concorda com estes Termos de Uso. Se você não concordar com qualquer parte destes termos, não utilize o sistema.

    ### 2. DESCRIÇÃO DO SERVIÇO
    O Sistema Planner Organiza é uma plataforma de gestão empresarial que permite o gerenciamento de clientes, propostas, projetos e finanças para profissionais de organização.

    ### 3. LICENÇA DE USO
    Concedemos a você uma licença limitada, não exclusiva e não transferível para utilizar o sistema conforme o plano contratado.

    ### 4. PRIVACIDADE E DADOS
    Respeitamos sua privacidade e protegemos seus dados conforme descrito em nossa Política de Privacidade.

    ### 5. RESPONSABILIDADES DO USUÁRIO
    - Fornecer informações precisas
    - Manter suas credenciais de acesso seguras
    - Utilizar o sistema de acordo com a legislação aplicável
    - Responsabilizar-se pelos dados inseridos

    ### 6. LIMITAÇÃO DE RESPONSABILIDADE
    Não nos responsabilizamos por:
    - Perda de dados devido a falhas do usuário
    - Interrupções temporárias do serviço
    - Uso inadequado do sistema

    ### 7. ALTERAÇÕES NOS TERMOS
    Podemos alterar estes termos a qualquer momento. Alterações significativas serão notificadas aos usuários.

    ### 8. ENCERRAMENTO
    Podemos encerrar sua conta por violação destes termos ou por inatividade prolongada.

    ### 9. LEI APLICÁVEL
    Estes termos são regidos pelas leis do Brasil.
    """)
    
    if st.button("Fechar Termos"):
        st.session_state.show_termos = False
        st.rerun()

def show_politica():
    """Mostra a página de política de privacidade"""
    st.title("Política de Privacidade")
    
    st.markdown("""
    ## Política de Privacidade do Sistema Planner Organiza

    ### 1. INFORMAÇÕES QUE COLETAMOS
    Coletamos informações fornecidas por você como:
    - Dados de cadastro (nome, email, telefone)
    - Dados de clientes e propostas cadastrados
    - Dados financeiros inseridos no sistema
    - Informações de uso do sistema

    ### 2. COMO UTILIZAMOS SUAS INFORMAÇÕES
    - Para fornecer e manter o serviço
    - Para notificá-lo sobre mudanças em nosso serviço
    - Para fornecer suporte ao cliente
    - Para melhorar nosso serviço

    ### 3. ARMAZENAMENTO DE DADOS
    Seus dados são armazenados em servidores seguros com acesso restrito.

    ### 4. COMPARTILHAMENTO DE DADOS
    Não compartilhamos suas informações pessoais com terceiros, exceto:
    - Com seu consentimento explícito
    - Para cumprir obrigações legais
    - Para proteger nossos direitos

    ### 5. SEGURANÇA
    Implementamos medidas técnicas e organizacionais para proteger seus dados.

    ### 6. SEUS DIREITOS
    Você tem direito a:
    - Acessar seus dados
    - Corrigir dados imprecisos
    - Solicitar a exclusão de seus dados

    ### 7. ALTERAÇÕES NESTA POLÍTICA
    Podemos atualizar nossa Política de Privacidade periodicamente.

    ### 8. CONTATO
    Para questões sobre esta política, entre em contato conosco.
    """)
    
    if st.button("Fechar Política"):
        st.session_state.show_politica = False
        st.rerun()

def main():
    """Função principal"""
    init_session_state()
    
    # Exibir Termos ou Política se solicitado
    if st.session_state.show_termos:
        show_termos()
        return
    
    if st.session_state.show_politica:
        show_politica()
        return
    
    # Verificar estrutura do banco para corrigir problemas no Render
    verify_database()
    
    # Verificar login
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Se estiver logado, mostrar menu lateral
    with st.sidebar:
        st.image("app-icon.svg", width=100)
        st.title("Planner Organiza")
        
        st.markdown("---")
        st.subheader("Menu Principal")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard.py")
        
        if st.button("👥 Clientes", use_container_width=True):
            st.switch_page("pages/clientes.py")
        
        if st.button("📝 Propostas", use_container_width=True):
            st.switch_page("pages/propostas.py")
        
        if st.button("📦 Produtos", use_container_width=True):
            st.switch_page("pages/produtos.py")
        
        if st.button("💲 Financeiro", use_container_width=True):
            st.switch_page("pages/financeiro.py")
        
        if st.button("📋 Relatórios", use_container_width=True):
            st.switch_page("pages/relatorios.py")
        
        st.markdown("---")
        st.subheader("Configurações")
        
        if st.button("⚙️ Configurações", use_container_width=True):
            st.switch_page("pages/configuracoes.py")
        
        if st.button("👤 Meu Perfil", use_container_width=True):
            st.switch_page("pages/perfil.py")
        
        if st.button("📱 Meus Contatos", use_container_width=True):
            st.switch_page("pages/contatos.py")
        
        st.markdown("---")
        
        user_info = st.session_state.user_info
        if user_info:
            st.info(f"Logado como: {user_info.get('email', 'Usuário')}")
        
        if st.button("Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()
    
    # Conteúdo principal - Dashboard simplificado
    st.title("Dashboard")
    
    # Usar DirectDB para evitar problemas com SQLAlchemy
    try:
        user_id = st.session_state.user_info.get('localId')
        direct_db = DirectDB(usuario_id=user_id)
        
        # Obter dados via acesso direto ao banco
        clientes = direct_db.get_clientes()
        propostas = direct_db.get_propostas()
        propostas_abertas = [p for p in propostas if p['status'] in ['Em análise', 'Em execução']]
        propostas_finalizadas = [p for p in propostas if p['status'] == 'Finalizada']
        
        # Fechar conexão
        direct_db.close()
        
        # Exibir estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Clientes", len(clientes))
        
        with col2:
            st.metric("Total de Propostas", len(propostas))
        
        with col3:
            st.metric("Propostas Abertas", len(propostas_abertas))
        
        with col4:
            st.metric("Propostas Finalizadas", len(propostas_finalizadas))
        
        # Exibir propostas recentes
        st.subheader("Propostas Recentes")
        
        if propostas:
            # Ordenar propostas por data (mais recentes primeiro)
            propostas_ordenadas = sorted(
                propostas, 
                key=lambda x: x.get('data_proposta', datetime.now().strftime('%Y-%m-%d')),
                reverse=True
            )
            
            # Limitar a 5 propostas recentes
            for proposta in propostas_ordenadas[:5]:
                with st.expander(f"{proposta.get('cliente_nome')} - {proposta.get('descricao', 'Sem descrição')}"):
                    st.write(f"**Status:** {proposta.get('status', 'N/A')}")
                    st.write(f"**Valor:** R$ {proposta.get('valor', 0):,.2f}")
                    st.write(f"**Data:** {proposta.get('data_proposta', 'N/A')}")
        else:
            st.info("Nenhuma proposta encontrada. Comece adicionando uma nova proposta.")
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.info("Tente navegar para outra página e voltar para atualizar os dados.")

# Executar aplicação
if __name__ == "__main__":
    main()