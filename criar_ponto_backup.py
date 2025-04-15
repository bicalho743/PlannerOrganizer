import streamlit as st
import pandas as pd
import os
import sys
import shutil
from datetime import datetime

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar o BackupManager da pasta utils
from utils.backup import BackupManager

st.set_page_config(
    page_title="Sistema de Backup - Planner Organiza",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("📊 Sistema de Backup - Planner Organiza")
    
    backup_manager = BackupManager()
    
    st.markdown("""
    ### Sistema de Gerenciamento de Backups
    
    Este sistema permite criar, visualizar e restaurar backups do banco de dados e arquivos do sistema.
    Você pode usar isto para:
    
    1. Criar um backup completo do estado atual do sistema
    2. Criar um ponto de restauração fixo que pode ser usado como referência
    3. Restaurar o sistema a um backup anterior
    """)
    
    # Aba para visualizar e criar backups
    tab1, tab2, tab3 = st.tabs(["Criar Backup", "Listar Backups", "Restaurar Backup"])
    
    with tab1:
        st.header("Criar Novo Backup")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Backup Padrão")
            st.write("Cria um backup normal com timestamp automático.")
            
            if st.button("Criar Backup Normal", key="create_normal_backup"):
                with st.spinner("Criando backup..."):
                    result = backup_manager.run_backup()
                    st.success(f"Backup criado com sucesso!\n\n{result}")
        
        with col2:
            st.subheader("Ponto de Backup Fixo")
            st.write("Cria um backup marcado como ponto fixo para restauração.")
            
            backup_name = st.text_input("Nome do ponto de backup (opcional)", 
                                       value=f"ponto_fixo_{datetime.now().strftime('%Y%m%d')}")
            
            if st.button("Criar Ponto Fixo", key="create_fixed_point"):
                with st.spinner("Criando ponto fixo de backup..."):
                    # Criar backup normal
                    backup_manager.run_backup()
                    
                    # Copiar arquivos mais recentes para arquivos com nomes fixos
                    backups = backup_manager.list_backups()
                    if backups:
                        db_backups = [b for b in backups if b['name'].startswith('db_backup_')]
                        file_backups = [b for b in backups if b['name'].startswith('files_backup_')]
                        
                        if db_backups and file_backups:
                            newest_db = db_backups[0]['path']
                            newest_files = file_backups[0]['path']
                            
                            # Criar cópias com o nome fixo
                            fixed_db = os.path.join(backup_manager.backup_dir, f"db_{backup_name}.sql")
                            fixed_files = os.path.join(backup_manager.backup_dir, f"files_{backup_name}.zip")
                            
                            shutil.copy2(newest_db, fixed_db)
                            shutil.copy2(newest_files, fixed_files)
                            
                            st.success(f"""
                            Ponto fixo '{backup_name}' criado com sucesso!
                            
                            - Banco de dados: {fixed_db}
                            - Arquivos: {fixed_files}
                            """)
                        else:
                            st.error("Não foi possível encontrar os backups mais recentes.")
                    else:
                        st.error("Não há backups disponíveis para criar um ponto fixo.")
    
    with tab2:
        st.header("Backups Disponíveis")
        
        # Recarregar botão
        if st.button("Atualizar Lista", key="refresh_backups"):
            st.rerun()
        
        # Listar backups
        backups = backup_manager.list_backups()
        
        if not backups:
            st.info("Não há backups disponíveis.")
        else:
            # Dividir entre backups normais e pontos fixos
            regular_backups = []
            fixed_points = []
            
            for backup in backups:
                if '_fixo_' in backup['name'] or (backup['name'].startswith('db_') and not backup['name'].startswith('db_backup_')):
                    fixed_points.append(backup)
                else:
                    regular_backups.append(backup)
            
            # Mostrar pontos fixos
            if fixed_points:
                st.subheader("Pontos Fixos de Backup")
                
                fixed_data = []
                for backup in fixed_points:
                    name = backup['name'].replace('db_', '').replace('files_', '').replace('.sql', '').replace('.zip', '')
                    if name not in [item[0] for item in fixed_data]:
                        size_mb = round(backup['size'] / (1024 * 1024), 2)
                        fixed_data.append([
                            name,
                            backup['date'].strftime('%d/%m/%Y %H:%M'),
                            f"{size_mb} MB",
                            backup['path']
                        ])
                
                st.table(pd.DataFrame(fixed_data, columns=['Nome', 'Data', 'Tamanho', 'Arquivo']))
            
            # Mostrar backups normais
            if regular_backups:
                st.subheader("Backups Regulares")
                
                regular_data = []
                for backup in regular_backups:
                    timestamp = backup['name'].split('_')[2].split('.')[0] if 'backup_' in backup['name'] else ''
                    if timestamp and timestamp not in [item[0] for item in regular_data]:
                        size_mb = round(backup['size'] / (1024 * 1024), 2)
                        date_str = backup['date'].strftime('%d/%m/%Y %H:%M')
                        regular_data.append([
                            timestamp,
                            date_str,
                            f"{size_mb} MB",
                            backup['path']
                        ])
                
                st.table(pd.DataFrame(regular_data, columns=['Timestamp', 'Data', 'Tamanho', 'Arquivo']))
    
    with tab3:
        st.header("Restaurar Backup")
        st.warning("""
        ⚠️ **ATENÇÃO**: Restaurar um backup substituirá TODOS os dados atuais pelos dados do backup.
        Esta ação não pode ser desfeita. Certifique-se de criar um backup do estado atual antes de prosseguir.
        """)
        
        backups = backup_manager.list_backups()
        
        if not backups:
            st.info("Não há backups disponíveis para restauração.")
        else:
            # Obter todos os backups de banco de dados (normais e pontos fixos)
            db_backups = []
            for backup in backups:
                if backup['name'].endswith('.sql'):
                    if 'backup_' in backup['name']:
                        # Backup normal
                        timestamp = backup['name'].split('_')[2].split('.')[0]
                        date_str = backup['date'].strftime('%d/%m/%Y %H:%M')
                        db_backups.append({
                            'name': f"Backup de {date_str} ({timestamp})",
                            'path': backup['path'],
                            'is_fixed': False
                        })
                    else:
                        # Ponto fixo
                        name = backup['name'].replace('db_', '').replace('.sql', '')
                        db_backups.append({
                            'name': f"PONTO FIXO: {name}",
                            'path': backup['path'],
                            'is_fixed': True
                        })
            
            # Ordenar: primeiro os pontos fixos, depois os backups normais por data
            db_backups = sorted(db_backups, key=lambda x: (not x['is_fixed'], x['path']), reverse=True)
            
            # Criar opções para o selectbox
            backup_options = [b['name'] for b in db_backups]
            selected_backup = st.selectbox("Selecione o backup para restaurar:", backup_options)
            
            # Encontrar o caminho do backup selecionado
            selected_path = next((b['path'] for b in db_backups if b['name'] == selected_backup), None)
            
            if selected_path:
                st.info(f"Você selecionou o backup: {selected_backup}")
                
                # Requerir confirmação
                confirm = st.text_input("Digite 'CONFIRMAR' para prosseguir com a restauração:")
                
                if confirm == "CONFIRMAR":
                    if st.button("RESTAURAR AGORA", key="restore_backup"):
                        with st.spinner("Restaurando backup..."):
                            success, message = backup_manager.restore_database(selected_path)
                            
                            if success:
                                st.success(f"""
                                ✅ Backup restaurado com sucesso!
                                
                                Por favor, reinicie o aplicativo para aplicar as alterações.
                                """)
                            else:
                                st.error(f"Erro ao restaurar backup: {message}")

if __name__ == "__main__":
    main()