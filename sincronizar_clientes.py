"""
Ferramenta administrativa para sincronizar dados de clientes com o Firebase
Este aplicativo permite sincronizar clientes entre o PostgreSQL e o Firebase.
"""
import os
import json
import streamlit as st
import pandas as pd

# Garantir que o arquivo de credenciais existe
if not os.path.exists("api/firebase_credentials.json"):
    st.error("Arquivo de credenciais do Firebase não encontrado.")
    st.stop()

# Importar módulos
from utils.firebase_client_sync import (
    get_all_clients_from_postgres,
    get_all_clients_from_firebase,
    sync_client_to_firebase,
    sync_all_clients_to_firebase,
    link_client_to_firebase_user
)
from utils.firebase_config import initialize_firebase

# Inicializar Firebase antes de tudo
_ = initialize_firebase()

# Configuração da página
st.set_page_config(
    page_title="Sincronização de Clientes - Firebase",
    page_icon="🔄",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .status-box {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .title-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .sidebar-content {
        padding: 10px;
        background-color: #f1f3f5;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def success_box(message):
    st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)

def warning_box(message):
    st.markdown(f'<div class="warning-box">{message}</div>', unsafe_allow_html=True)

def error_box(message):
    st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)


def main():
    # Título
    st.markdown('<div class="title-container"><h1>Sincronização de Clientes com Firebase</h1></div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.sidebar.header("Opções")
    
    # Funções disponíveis
    option = st.sidebar.radio(
        "Escolha uma função:",
        [
            "Visualizar Clientes - PostgreSQL",
            "Visualizar Clientes - Firebase",
            "Sincronizar Cliente Específico",
            "Sincronizar Todos os Clientes",
            "Vincular Cliente a Usuário"
        ]
    )
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar função selecionada
    if option == "Visualizar Clientes - PostgreSQL":
        show_postgres_clients()
    elif option == "Visualizar Clientes - Firebase":
        show_firebase_clients()
    elif option == "Sincronizar Cliente Específico":
        sync_specific_client()
    elif option == "Sincronizar Todos os Clientes":
        sync_all_clients()
    elif option == "Vincular Cliente a Usuário":
        link_client_user()


def show_postgres_clients():
    st.header("Clientes no PostgreSQL")
    
    with st.spinner("Carregando clientes..."):
        clients_df = get_all_clients_from_postgres()
    
    if clients_df.empty:
        warning_box("Nenhum cliente encontrado no banco de dados PostgreSQL.")
        return
    
    # Exibir estatísticas
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Total de Clientes", len(clients_df))
    
    # Detectar campos nulos em emails (para estatísticas)
    email_count = clients_df['email'].notnull().sum()
    col2.metric("Clientes com Email", f"{email_count} ({email_count/len(clients_df):.1%})")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar tabela de clientes
    st.dataframe(clients_df)
    
    # Opção para baixar como CSV
    csv = clients_df.to_csv(index=False)
    st.download_button(
        label="Baixar dados como CSV",
        data=csv,
        file_name="clientes_postgres.csv",
        mime="text/csv"
    )


def show_firebase_clients():
    st.header("Clientes no Firebase")
    
    with st.spinner("Carregando clientes do Firebase..."):
        clients_list = get_all_clients_from_firebase()
    
    if not clients_list:
        warning_box("Nenhum cliente encontrado no Firebase.")
        return
    
    # Converter para DataFrame para melhor visualização
    clients_df = pd.DataFrame(clients_list)
    
    # Exibir estatísticas
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Total de Clientes no Firebase", len(clients_df))
    
    # Verificar quantos estão vinculados a usuários
    if 'firebase_user_id' in clients_df.columns:
        users_linked = clients_df['firebase_user_id'].notnull().sum()
        col2.metric("Clientes Vinculados a Usuários", f"{users_linked} ({users_linked/len(clients_df):.1%})")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar tabela de clientes
    st.dataframe(clients_df)
    
    # Opção para baixar como CSV
    csv = clients_df.to_csv(index=False)
    st.download_button(
        label="Baixar dados como CSV",
        data=csv,
        file_name="clientes_firebase.csv",
        mime="text/csv"
    )


def sync_specific_client():
    st.header("Sincronizar Cliente Específico")
    
    # Obter lista de clientes do PostgreSQL para selecionar
    with st.spinner("Carregando clientes..."):
        clients_df = get_all_clients_from_postgres()
    
    if clients_df.empty:
        error_box("Nenhum cliente encontrado no banco de dados PostgreSQL.")
        return
    
    # Criar opções de seleção com ID e nome
    client_options = [f"{row['id']} - {row['nome']}" for _, row in clients_df.iterrows()]
    
    selected_client = st.selectbox(
        "Selecione o cliente para sincronizar:",
        options=client_options
    )
    
    # Extrair ID do cliente da opção selecionada
    if selected_client:
        client_id = int(selected_client.split(' - ')[0])
        
        # Mostrar dados do cliente selecionado
        client_row = clients_df[clients_df['id'] == client_id].iloc[0]
        
        st.subheader("Dados do Cliente")
        col1, col2 = st.columns(2)
        col1.text(f"ID: {client_id}")
        col1.text(f"Nome: {client_row['nome']}")
        col1.text(f"Email: {client_row['email']}")
        col2.text(f"Telefone: {client_row['telefone']}")
        col2.text(f"CPF: {client_row['cpf']}")
        col2.text(f"Data Cadastro: {client_row['data_cadastro']}")
        
        # Botão para sincronizar
        if st.button("Sincronizar com Firebase", type="primary"):
            with st.spinner("Sincronizando cliente..."):
                result = sync_client_to_firebase(client_id)
            
            if result['success']:
                success_box(result['message'])
                st.json(result)
            else:
                error_box(result['message'])
                st.json(result)


def sync_all_clients():
    st.header("Sincronizar Todos os Clientes")
    
    # Mostrar aviso
    st.warning("""
    Esta operação irá sincronizar todos os clientes do PostgreSQL para o Firebase.
    Dependendo do número de clientes, esta operação pode levar algum tempo.
    """)
    
    # Obter contagem de clientes
    with st.spinner("Contando clientes..."):
        clients_df = get_all_clients_from_postgres()
    
    if clients_df.empty:
        error_box("Nenhum cliente encontrado no banco de dados PostgreSQL.")
        return
    
    st.info(f"Total de clientes para sincronizar: {len(clients_df)}")
    
    # Botão para iniciar sincronização
    if st.button("Iniciar Sincronização", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Iniciando sincronização...")
        
        with st.spinner("Sincronizando todos os clientes..."):
            result = sync_all_clients_to_firebase()
            
        progress_bar.progress(100)
        
        if result['success']:
            stats = result['stats']
            success_box(result['message'])
            
            # Mostrar estatísticas detalhadas
            st.subheader("Resultado da Sincronização")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", stats['total'])
            col1.metric("Criados", stats['created'])
            col2.metric("Atualizados", stats['updated'])
            col2.metric("Erros", stats['errors'])
            col3.metric("Taxa de Sucesso", f"{(stats['created'] + stats['updated'])/stats['total']:.1%}")
            
            # Opção para ver detalhes
            if st.checkbox("Ver detalhes completos"):
                st.json(stats)
        else:
            error_box(result['message'])


def link_client_user():
    st.header("Vincular Cliente a Usuário do Firebase")
    
    # Obter lista de clientes do PostgreSQL
    with st.spinner("Carregando clientes..."):
        clients_df = get_all_clients_from_postgres()
    
    if clients_df.empty:
        error_box("Nenhum cliente encontrado no banco de dados PostgreSQL.")
        return
    
    # Criar opções de seleção com ID e nome
    client_options = [f"{row['id']} - {row['nome']}" for _, row in clients_df.iterrows()]
    
    selected_client = st.selectbox(
        "Selecione o cliente:",
        options=client_options
    )
    
    # Campo para informar ID do usuário no Firebase
    firebase_user_id = st.text_input(
        "ID do Usuário no Firebase:",
        help="Informe o ID do usuário no Firebase Authentication (UID)."
    )
    
    # Extrair ID do cliente da opção selecionada
    if selected_client and firebase_user_id and st.button("Vincular", type="primary"):
        client_id = int(selected_client.split(' - ')[0])
        
        with st.spinner("Vinculando cliente ao usuário..."):
            result = link_client_to_firebase_user(client_id, firebase_user_id)
        
        if result['success']:
            success_box(result['message'])
            st.json(result)
        else:
            error_box(result['message'])
            st.json(result)


if __name__ == "__main__":
    main()