import streamlit as st
from utils.backup import BackupManager
import humanize
from datetime import datetime

def show():
    st.title("🔄 Backup do Sistema")

    # Inicializar gerenciador de backup
    if 'backup_manager' not in st.session_state:
        st.session_state.backup_manager = BackupManager()
        # Agendar backup diário
        st.session_state.backup_manager.schedule_backups(24)

    # Tabs para organizar as operações
    tab1, tab2 = st.tabs(["Backup Manual", "Backups Disponíveis"])

    with tab1:
        st.subheader("Realizar Backup Manual")

        if st.button("Iniciar Backup", key="start_backup"):
            with st.spinner("Realizando backup..."):
                try:
                    result = st.session_state.backup_manager.run_backup()
                    if "Erro" in result:
                        st.error(result)
                    else:
                        st.success("Backup realizado com sucesso!")
                        st.code(result)
                except Exception as e:
                    st.error(f"Erro ao realizar backup: {str(e)}")

    with tab2:
        st.subheader("Backups Disponíveis")

        try:
            backups = st.session_state.backup_manager.list_backups()
        except Exception as e:
            st.error(f"Erro ao listar backups: {str(e)}")
            backups = []

        if not backups:
            st.info("Nenhum backup encontrado.")
        else:
            for backup in backups:
                with st.expander(f"📦 {backup['name']}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"Data: {backup['date'].strftime('%d/%m/%Y %H:%M:%S')}")
                        st.write(f"Tamanho: {humanize.naturalsize(backup['size'])}")

                    with col2:
                        if backup['name'].startswith('db_backup_'):
                            if st.button("Restaurar", key=backup['name']):
                                with st.spinner("Restaurando backup..."):
                                    try:
                                        success, msg = st.session_state.backup_manager.restore_database(
                                            backup['path']
                                        )
                                        if success:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)
                                    except Exception as e:
                                        st.error(f"Erro ao restaurar backup: {str(e)}")

        # Configurações do backup automático
        st.subheader("Configurações")
        st.info(
            "O sistema realiza backups automáticos a cada 24 horas. "
            "Os backups são armazenados na pasta 'backups' do sistema."
        )