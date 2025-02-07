import os
import shutil
import subprocess
from datetime import datetime
import schedule
import time
import threading
import streamlit as st

class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """Garante que o diretório de backup existe"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
    def create_database_backup(self):
        """Cria backup do banco de dados PostgreSQL"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{self.backup_dir}/db_backup_{timestamp}.sql"
            
            # Usando variáveis de ambiente do PostgreSQL
            pg_dump_cmd = [
                "pg_dump",
                f"--dbname={os.getenv('DATABASE_URL')}",
                "--format=plain",
                f"--file={backup_file}"
            ]
            
            subprocess.run(pg_dump_cmd, check=True)
            return True, f"Backup do banco criado: {backup_file}"
        except Exception as e:
            return False, f"Erro ao criar backup do banco: {str(e)}"
            
    def create_files_backup(self):
        """Cria backup dos arquivos de dados"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{self.backup_dir}/files_backup_{timestamp}.zip"
            
            # Lista de arquivos para backup
            files_to_backup = [
                "clientes.csv",
                "propostas.csv",
                "financeiro.csv",
                "produtos.csv"
            ]
            
            # Criar arquivo ZIP com os arquivos
            with zipfile.ZipFile(backup_file, 'w') as zipf:
                for file in files_to_backup:
                    if os.path.exists(file):
                        zipf.write(file)
                        
            return True, f"Backup dos arquivos criado: {backup_file}"
        except Exception as e:
            return False, f"Erro ao criar backup dos arquivos: {str(e)}"
            
    def run_backup(self):
        """Executa backup completo"""
        results = []
        
        # Backup do banco
        success, msg = self.create_database_backup()
        results.append(msg)
        
        # Backup dos arquivos
        success, msg = self.create_files_backup()
        results.append(msg)
        
        return "\n".join(results)
        
    def schedule_backups(self, interval_hours=24):
        """Agenda backups automáticos"""
        schedule.every(interval_hours).hours.do(self.run_backup)
        
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        # Iniciar agendador em uma thread separada
        scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        scheduler_thread.start()
        
    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith(('db_backup_', 'files_backup_')):
                path = os.path.join(self.backup_dir, file)
                size = os.path.getsize(path)
                date = datetime.fromtimestamp(os.path.getctime(path))
                backups.append({
                    'name': file,
                    'size': size,
                    'date': date,
                    'path': path
                })
        return sorted(backups, key=lambda x: x['date'], reverse=True)
        
    def restore_database(self, backup_file):
        """Restaura backup do banco de dados"""
        try:
            psql_cmd = [
                "psql",
                f"--dbname={os.getenv('DATABASE_URL')}",
                f"--file={backup_file}"
            ]
            
            subprocess.run(psql_cmd, check=True)
            return True, "Backup restaurado com sucesso"
        except Exception as e:
            return False, f"Erro ao restaurar backup: {str(e)}"
