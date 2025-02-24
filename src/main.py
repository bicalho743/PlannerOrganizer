import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Adicionar diretórios ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(Path(__file__).parent))

from utils.database import Database
import pages.login as login

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização da base de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Verificar autenticação
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    login.show()
else:
    # Menu lateral personalizado
    st.sidebar.title("Menu Principal")

    # Mostrar informações do usuário
    with st.sidebar:
        st.write(f"👤 Olá, {st.session_state.usuario['nome']}")

        # Mostrar mais detalhes do usuário
        with st.expander("Ver meus dados"):
            st.write("**Seus dados:**")
            st.write(f"ID: {st.session_state.usuario['id']}")
            st.write(f"Nome: {st.session_state.usuario['nome']}")
            st.write(f"Email: {st.session_state.usuario['email']}")
            st.write(f"Tipo de usuário: {st.session_state.usuario['tipo']}")
        if st.button("📤 Sair"):
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.experimental_rerun()

        st.markdown("---")

    pagina = st.sidebar.radio(
        "",  # Label vazio para não mostrar título do radio
        ["Dashboard", "Cadastros", "Propostas", "Financeiro", "Relatórios", "Importação"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard"
                        else f"👥 {x}" if x == "Cadastros"
                        else f"📝 {x}" if x == "Propostas"
                        else f"💰 {x}" if x == "Financeiro"
                        else f"📈 {x}" if x == "Relatórios"
                        else f"📥 {x}"  # Importação
    )

    # Lógica de navegação
    if pagina == "Dashboard":
        st.title("📋 Planner Organizer")

        # Add test data button in sidebar if database is empty
        clientes = st.session_state.db.get_clientes()
        if clientes.empty:
            st.sidebar.warning("Banco de dados vazio")
            if st.sidebar.button("Adicionar Dados de Teste"):
                if st.session_state.db.add_test_data():
                    st.sidebar.success("Dados de teste adicionados com sucesso!")
                    st.rerun()
                else:
                    st.sidebar.error("Erro ao adicionar dados de teste")

        # Dashboard content
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.subheader("📊 Resumo")

            # Estatísticas básicas
            clientes = st.session_state.db.get_clientes()
            propostas = st.session_state.db.get_propostas()
            financeiro = st.session_state.db.get_financeiro()

            st.metric("Total de Clientes", len(clientes) if not clientes.empty else 0)
            propostas_ativas = len(propostas[propostas['status'] == 'Aberta']) if not propostas.empty else 0
            st.metric("Propostas Ativas", propostas_ativas)

            # Resumo financeiro
            if not financeiro.empty:
                valores_receber = financeiro[
                    (financeiro['tipo'] == 'receita') & 
                    (financeiro['tipo_receita'].isin(['organização', 'venda']))
                ]['valor'].sum()
            else:
                valores_receber = 0.0

            st.metric("Valores a Receber", f"R$ {valores_receber:.2f}")

        with col2:
            st.subheader("📋 Propostas em Aberto")
            if not propostas.empty:
                propostas_abertas = propostas[propostas['status'] == 'Aberta']
                if not propostas_abertas.empty:
                    for _, p in propostas_abertas.iterrows():
                        with st.expander(f"Proposta #{p['numero']} - {p['descricao']}"):
                            st.write(f"**Valor:** R$ {p['valor']:.2f}")
                            if 'prazo_entrega' in p and p['prazo_entrega']:
                                st.write(f"**Prazo de Entrega:** {p['prazo_entrega']}")
                else:
                    st.info("Nenhuma proposta em aberto.")
            else:
                st.info("Nenhuma proposta cadastrada.")

        with col3:
            st.subheader("🎂 Aniversariantes")
            hoje = datetime.now().date()

            if not clientes.empty and 'data_aniversario' in clientes.columns:
                try:
                    # Converter data_aniversario para datetime explicitamente
                    clientes['data_aniversario'] = pd.to_datetime(clientes['data_aniversario'], errors='coerce')

                    # Filtrar aniversariantes do dia
                    aniversariantes_hoje = clientes[
                        (clientes['data_aniversario'].notna()) & 
                        (clientes['data_aniversario'].dt.month == hoje.month) & 
                        (clientes['data_aniversario'].dt.day == hoje.day)
                    ]

                    # Mostrar aniversariantes de hoje
                    st.write("**Hoje:**")
                    if not aniversariantes_hoje.empty:
                        for _, aniversariante in aniversariantes_hoje.iterrows():
                            with st.container():
                                st.write(f"🎈 **{aniversariante['nome']}**")
                                if aniversariante['telefone']:
                                    st.write(f"📱 {aniversariante['telefone']}")
                    else:
                        st.info("Nenhum aniversariante hoje!")

                    # Mostrar próximos aniversariantes (próximos 7 dias)
                    st.write("\n**Próximos 7 dias:**")
                    proximos_aniversariantes = clientes[
                        (clientes['data_aniversario'].notna()) &
                        (((clientes['data_aniversario'].dt.month == hoje.month) & 
                          (clientes['data_aniversario'].dt.day > hoje.day) & 
                          (clientes['data_aniversario'].dt.day <= hoje.day + 7)) |
                         ((clientes['data_aniversario'].dt.month == (hoje.month % 12 + 1)) & 
                          (clientes['data_aniversario'].dt.day <= (hoje.day + 7) % 31)))
                    ]

                    if not proximos_aniversariantes.empty:
                        for _, aniversariante in proximos_aniversariantes.iterrows():
                            with st.container():
                                data_aniv = aniversariante['data_aniversario'].strftime('%d/%m')
                                st.write(f"🎂 **{aniversariante['nome']}** ({data_aniv})")
                                if aniversariante['telefone']:
                                    st.write(f"📱 {aniversariante['telefone']}")
                    else:
                        st.info("Nenhum aniversariante nos próximos dias.")
                except Exception as e:
                    st.error(f"Erro ao processar datas de aniversário: {str(e)}")
            else:
                st.info("Nenhum cliente cadastrado com data de aniversário.")

    elif pagina == "Cadastros":
        import pages.cadastros as cadastros
        cadastros.show()

    elif pagina == "Propostas":
        import pages.propostas as propostas
        propostas.show()

    elif pagina == "Financeiro":
        import pages.financeiro as financeiro
        financeiro.show()

    elif pagina == "Relatórios":
        import pages.relatorios as relatorios
        relatorios.show()

    elif pagina == "Importação":
        import pages.importacao as importacao
        importacao.show()

    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Desenvolvido com ❤️ usando Streamlit")