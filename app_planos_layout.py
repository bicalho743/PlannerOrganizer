"""
Arquivo de exemplo para incorporar a seção de planos diretamente na aplicação principal.
Copie e cole este código diretamente no app.py no local onde deseja exibir os planos.
"""

# Importação do módulo de planos
from utils.planos import mostrar_planos

# Exemplo de como incorporar a seção de planos no app.py
def exemplo_integracao_app():
    """
    Exemplo de como integrar a seção de planos com o app principal.
    Copie o código relevante para seu app.py
    """
    import streamlit as st
    
    # Se o usuário não estiver autenticado, mostre a landing page com os planos
    if not st.session_state.get('authenticated', False):
        # Remover a barra lateral
        st.markdown("""
        <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
        </style>
        """, unsafe_allow_html=True)
        
        # Layout principal com duas colunas: lado esquerdo para marketing, lado direito para planos
        left_col, right_col = st.columns([3, 2])
        
        with left_col:
            # Cabeçalho principal
            st.markdown('<h1 class="main-header">Planner Organizer</h1>', unsafe_allow_html=True)
            st.markdown('<p class="subheader">Sistema Profissional para Personal Organizers</p>', unsafe_allow_html=True)
            
            # Benefícios principais, estatísticas e outros elementos de marketing...
            # ... (Manter seu código atual do app.py para esta seção) ...
            
            # Adicione aqui o caso de uso específico de negócio para organizers
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f0f8ff, #e1efff); padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h3>Gerenciamento profissional para cada projeto</h3>
                <p>O Planner Organizer foi criado exclusivamente para atender às necessidades específicas de Personal Organizers:</p>
                <ul>
                    <li><strong>Propostas detalhadas</strong> com valores justos que valorizam seu trabalho</li>
                    <li><strong>Gerenciamento financeiro completo</strong> para controlar receitas e despesas</li>
                    <li><strong>Controle de projetos</strong> do início ao fim com avisos automáticos</li>
                    <li><strong>Relatórios profissionais</strong> para impressionar seus clientes</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with right_col:
            # Aqui você pode mostrar o formulário de login
            # ... (Manter seu código atual do app.py para esta seção) ...
            
            # Depois do formulário de login, mostre a seção de planos
            st.markdown("---")
            
            # Chame a função de mostrar_planos com opções simplificadas
            # (isso pode ficar em outra aba ou abaixo do login, dependendo do layout desejado)
            mostrar_planos(
                com_titulo=True,       # True para mostrar o título principal "Escolha o Plano Ideal..."
                com_prova_social=True, # True para mostrar os depoimentos de clientes
                com_teste_gratis=True, # True para mostrar a seção de "Comece com 7 dias grátis"
                com_destaque_plano_medio=True, # True para destacar visualmente o plano anual (do meio)
                stripe_ready=True      # True para adicionar botões funcionais para integração com Stripe
            )
    else:
        # Aqui continua seu código normal da aplicação principal
        # para usuários já logados...
        pass

# Não execute nada diretamente neste arquivo de exemplo
if __name__ == "__main__":
    print("Este é um módulo de exemplo para integração com o app.py principal.")
    print("Copie apenas as partes relevantes para o seu projeto.")