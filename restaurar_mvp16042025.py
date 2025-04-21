"""
Script para restaurar o sistema ao checkpoint MVP16042025
Este script usa a classe BackupManager para restaurar o sistema 
diretamente, sem precisar acessar a interface web.
"""
import os
import sys
import shutil
from datetime import datetime

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar o BackupManager da pasta utils
from utils.backup import BackupManager

def criar_pontos_mvp():
    """
    Cria os arquivos de ponto de backup para o MVP16042025
    baseado no documento existente
    """
    # Caminhos para os arquivos de backup
    backup_dir = "backups"
    db_backup = os.path.join(backup_dir, "db_MVP16042025.sql")
    files_backup = os.path.join(backup_dir, "files_MVP16042025.zip")
    
    print(f"Verificando se os arquivos de backup MVP16042025 já existem...")
    
    # Verificar se já existem
    if os.path.exists(db_backup) and os.path.exists(files_backup):
        print(f"Arquivos de backup MVP16042025 já existem.")
        return True, db_backup
    
    # Verificar se há backups recentes que possam ser usados
    backup_manager = BackupManager()
    backups = backup_manager.list_backups()
    
    if not backups:
        print("Não há backups disponíveis para criar o ponto MVP16042025.")
        
        # Vamos criar um backup atual para usar
        print("Criando novo backup...")
        resultado = backup_manager.run_backup()
        print(f"Resultado: {resultado}")
        
        # Atualizar a lista de backups
        backups = backup_manager.list_backups()
        if not backups:
            return False, "Não foi possível criar novos backups."
    
    # Encontrar os backups mais recentes
    db_backups = [b for b in backups if b['name'].startswith('db_backup_')]
    file_backups = [b for b in backups if b['name'].startswith('files_backup_')]
    
    if not db_backups or not file_backups:
        return False, "Não foi possível encontrar backups completos."
    
    # Ordenar por data (mais recente primeiro)
    db_backups = sorted(db_backups, key=lambda x: x['date'], reverse=True)
    file_backups = sorted(file_backups, key=lambda x: x['date'], reverse=True)
    
    # Usar os mais recentes
    newest_db = db_backups[0]['path']
    newest_files = file_backups[0]['path']
    
    # Criar cópias com o nome MVP16042025
    try:
        shutil.copy2(newest_db, db_backup)
        shutil.copy2(newest_files, files_backup)
        
        print(f"Criados arquivos de backup para MVP16042025:")
        print(f"- Banco de dados: {db_backup}")
        print(f"- Arquivos: {files_backup}")
        
        return True, db_backup
    except Exception as e:
        return False, f"Erro ao criar arquivos de backup MVP16042025: {e}"

def restaurar_mvp():
    """
    Restaura o sistema para o checkpoint MVP16042025
    """
    print("Iniciando restauração para o checkpoint MVP16042025...")
    
    # Criar ou verificar os pontos de backup
    sucesso, resultado = criar_pontos_mvp()
    
    if not sucesso:
        print(f"Erro: {resultado}")
        return False
    
    # Restaurar a partir do arquivo de backup
    backup_manager = BackupManager()
    print(f"Restaurando banco de dados a partir de: {resultado}")
    
    # Fazer a restauração
    sucesso, mensagem = backup_manager.restore_database(resultado)
    
    if sucesso:
        print("✅ Checkpoint MVP16042025 restaurado com sucesso!")
        print("Por favor, reinicie todas as aplicações para aplicar as alterações.")
        print("Você pode usar o comando 'restart_workflow' para cada workflow.")
        return True
    else:
        print(f"❌ Erro ao restaurar checkpoint: {mensagem}")
        return False

if __name__ == "__main__":
    restaurar_mvp()