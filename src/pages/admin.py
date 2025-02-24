import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    if not st.session_state.autenticado or st.session_state.usuario.tipo != 'admin':
        st.error("Acesso negado. Esta página é restrita para administradores.")
        return

    st.title("👤 Administração de Usuários")
    
    # Carregar lista de usuários
    usuarios = st.session_state.db.get_usuarios()
    
    if not usuarios.empty:
        # Converter tipos de dados
        usuarios['data_cadastro'] = pd.to_datetime(usuarios['data_cadastro'])
        
        # Exibir estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Usuários", len(usuarios))
        with col2:
            usuarios_ativos = len(usuarios[usuarios['ativo']])
            st.metric("Usuários Ativos", usuarios_ativos)
        with col3:
            usuarios_inativos = len(usuarios[~usuarios['ativo']])
            st.metric("Usuários Inativos", usuarios_inativos)
        
        # Tabela de usuários com ações
        st.subheader("Gerenciar Usuários")
        
        for idx, usuario in usuarios.iterrows():
            with st.expander(f"📧 {usuario['email']} - {usuario['nome']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Nome:** {usuario['nome']}")
                    st.write(f"**Email:** {usuario['email']}")
                    st.write(f"**Empresa:** {usuario['empresa'] or 'Não informada'}")
                    st.write(f"**Data de Cadastro:** {usuario['data_cadastro'].strftime('%d/%m/%Y')}")
                
                with col2:
                    # Alterar status (ativo/inativo)
                    novo_status = st.toggle(
                        "Usuário Ativo",
                        value=usuario['ativo'],
                        key=f"status_{usuario['id']}"
                    )
                    
                    if novo_status != usuario['ativo']:
                        sucesso = st.session_state.db.atualizar_status_usuario(
                            usuario['id'],
                            novo_status
                        )
                        if sucesso:
                            st.success(f"Status atualizado para {'ativo' if novo_status else 'inativo'}")
                            st.rerun()
                    
                    # Alterar tipo de usuário
                    novo_tipo = st.selectbox(
                        "Tipo de Usuário",
                        options=['usuario', 'admin'],
                        index=0 if usuario['tipo'] == 'usuario' else 1,
                        key=f"tipo_{usuario['id']}"
                    )
                    
                    if novo_tipo != usuario['tipo']:
                        sucesso = st.session_state.db.atualizar_tipo_usuario(
                            usuario['id'],
                            novo_tipo
                        )
                        if sucesso:
                            st.success(f"Tipo de usuário atualizado para {novo_tipo}")
                            st.rerun()
    else:
        st.info("Nenhum usuário cadastrado ainda.")
