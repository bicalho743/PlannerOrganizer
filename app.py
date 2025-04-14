import os
import sys
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

from utils.database import Database

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do banco de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
        st.success("Conexão com o banco de dados estabelecida com sucesso!")
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. O endpoint pode estar desabilitado.")
        st.warning("Se você estiver usando Neon PostgreSQL ou outro banco de dados serverless, você precisa reativar o endpoint.")
        
        # Mostrar informação sobre o DATABASE_URL (sem mostrar credenciais)
        db_url = os.getenv('DATABASE_URL', 'Não definido')
        if db_url:
            # Esconder credenciais na mensagem
            safe_url = db_url.split('@')
            if len(safe_url) > 1:
                host_part = safe_url[1]
                st.info(f"Sua conexão de banco de dados aponta para: ...@{host_part}")
            else:
                st.info("DATABASE_URL está definido, mas não está no formato esperado.")
        else:
            st.info("A variável de ambiente DATABASE_URL não está definida.")
        
        st.error(f"Detalhes do erro: {str(e)}")
        st.stop()

# Estilo CSS customizado para garantir o menu no topo
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background-color: #262730;
    }

    div.block-container {
        padding-top: 0;
    }

    div.stButton > button {
        width: 100%;
        background-color: #F1A208 !important;
        color: #262730 !important;
        font-weight: 500;
        text-align: left;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }

    div.stButton > button:hover {
        background-color: #ffc107 !important;
    }

    /* Container escuro para os botões */
    div.nav-buttons {
        background-color: #262730;
        padding: 1rem;
        margin: 0 -1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Menu principal (deve aparecer no topo)
st.sidebar.title("Menu Principal")

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definição do menu principal
MENU_PRINCIPAL = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios"
}

# Criação dos botões do menu principal
for label, page in MENU_PRINCIPAL.items():
    if st.sidebar.button(label, key=f"main_menu_{page.lower()}", use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Roteamento de páginas
try:
    if st.session_state.current_page == "Dashboard":
        from pages.dashboard import show
        show()
    elif st.session_state.current_page == "Cadastros":
        from pages.cadastros import show
        show()
    elif st.session_state.current_page == "Propostas":
        # Mostrar página de propostas inline para evitar erros de importação
        st.title("PROPOSTAS")
        
        # Verificar se temos uma conexão com o banco de dados
        if not hasattr(st.session_state, 'db'):
            st.error("Erro: Conexão com banco de dados não disponível")
        else:
            # Criar um formulário para nova proposta
            st.subheader("Nova Proposta")
            
            # Obter a lista de clientes do banco de dados
            try:
                clientes = st.session_state.db.get_clientes()
                if clientes.empty:
                    st.warning("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
                else:
                    import pandas as pd
                    import uuid
                    from datetime import datetime, timedelta
                    import time
                    
                    # Formulário para cadastro de nova proposta
                    with st.form(key="nova_proposta_form"):
                        # Cliente (seleção a partir do módulo de cadastro)
                        clientes_lista = clientes['nome'].tolist()
                        cliente = st.selectbox("Cliente:", clientes_lista)
                        
                        # Descrição do serviço
                        descricao = st.text_area("Descrição do serviço:", height=100)
                        
                        # Valor do serviço
                        valor = st.number_input("Valor do serviço (R$):", min_value=0.0, format="%.2f")
                        
                        # Prazo estimado (em dias)
                        prazo = st.number_input("Prazo estimado (dias):", min_value=1, value=15)
                        
                        # Data de início prevista
                        data_inicio = st.date_input("Data de início prevista:", datetime.now().date())
                        
                        # Calcular data de término com base no prazo
                        data_fim = data_inicio + timedelta(days=prazo)
                        st.info(f"Data de término prevista: {data_fim.strftime('%d/%m/%Y')}")
                        
                        # Gerar ID único para a proposta (não visível para o usuário)
                        # Este será substituído pelo ID gerado pelo banco de dados
                        proposta_id = str(uuid.uuid4())
                        
                        # Botão para salvar
                        submitted = st.form_submit_button("Salvar Proposta")
                        
                        if submitted:
                            try:
                                # Obter o ID do cliente selecionado
                                cliente_id = clientes[clientes['nome'] == cliente]['id'].iloc[0]
                                
                                # Criar nova proposta
                                novo_numero = st.session_state.db.add_proposta(
                                    cliente_id=cliente_id,
                                    descricao=descricao,
                                    valor=valor,
                                    status="Em elaboração",  # Status inicial
                                    data_inicio=data_inicio,
                                    data_fim=data_fim,
                                    previsao_dias=prazo,  # Prazo em dias (número)
                                    # O prazo_entrega deve ser do tipo date
                                    prazo_entrega=data_inicio  # Usamos data_inicio como base
                                )
                                
                                if novo_numero:
                                    st.success(f"Proposta #{novo_numero} criada com sucesso!")
                                    
                                    # Aguardar um momento para a mensagem ser exibida
                                    time.sleep(1)
                                    st.rerun()  # Recarregar a página para limpar o formulário
                                else:
                                    st.error("Erro ao salvar proposta.")
                            except Exception as e:
                                st.error(f"Erro ao salvar proposta: {str(e)}")
                    
                    # Mostrar propostas existentes em uma tabela
                    st.subheader("Propostas Existentes")
                    try:
                        propostas = st.session_state.db.get_propostas()
                        
                        if not propostas.empty:
                            # Mesclar com informações do cliente para exibir o nome
                            propostas_com_clientes = propostas.merge(
                                clientes[['id', 'nome']],
                                left_on='cliente_id',
                                right_on='id',
                                suffixes=('', '_cliente')
                            )
                            
                            # Preparar DataFrame para exibição
                            df_exibicao = pd.DataFrame()
                            df_exibicao['Número'] = propostas_com_clientes['numero']
                            df_exibicao['Cliente'] = propostas_com_clientes['nome']
                            df_exibicao['Descrição'] = propostas_com_clientes['descricao']
                            df_exibicao['Valor (R$)'] = propostas_com_clientes['valor'].apply(lambda x: f"R$ {float(x):.2f}")
                            df_exibicao['Status'] = propostas_com_clientes['status']
                            
                            # Formatar datas para exibição
                            df_exibicao['Início'] = propostas_com_clientes['data_inicio'].apply(
                                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                            )
                            df_exibicao['Prazo (dias)'] = propostas_com_clientes['previsao_dias']
                            
                            # Exibir tabela
                            st.dataframe(df_exibicao)
                        else:
                            st.info("Nenhuma proposta cadastrada.")
                    except Exception as e:
                        st.error(f"Erro ao carregar propostas: {str(e)}")
            except Exception as e:
                st.error(f"Erro ao carregar clientes: {str(e)}")
    elif st.session_state.current_page == "Financeiro":
        from pages.financeiro import show
        show()
    elif st.session_state.current_page == "Relatórios":
        from pages.relatorios import show
        show()
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Informações do sistema no final
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.markdown("""
    ### Sistema Personal Organizer
    **Versão:** 1.0.2

    **Recursos Disponíveis:**
    - ✅ Gestão de Clientes
    - ✅ Controle de Propostas
    - ✅ Gestão Financeira
    - ✅ Relatórios e Análises

    **Novidades:**
    - 🎉 Telas de celebração
    - 📊 Dashboard aprimorado
    - 📱 Interface responsiva

    Desenvolvido com ❤️ usando Streamlit
    """)

    # Sem botão de importação conforme solicitado

# A navegação é controlada pelos botões do menu principal
# Os botões já atualizam st.session_state.current_page

# O conteúdo principal já é exibido acima, sem duplicação
# Se a página for Propostas, já temos o código inserido diretamente no app.py
# Não precisamos chamar o módulo externo pages.propostas
if st.session_state.current_page in ["Dashboard", "Cadastros", "Financeiro", "Relatórios"]:
    module_name = st.session_state.current_page.lower()
    try:
        module = __import__(f"pages.{module_name}", fromlist=["show"])
        module.show()
    except ImportError as e:
        st.error(f"Erro ao carregar módulo {module_name}: {str(e)}")
# Não temos mais a opção de importação no menu