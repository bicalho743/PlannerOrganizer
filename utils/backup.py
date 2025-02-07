import os
import shutil
import subprocess
import zipfile
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

            # Use environment variables for PostgreSQL connection
            pg_dump_cmd = [
                "pg_dump",
                f"--host={os.getenv('PGHOST', '')}",
                f"--port={os.getenv('PGPORT', '5432')}",
                f"--username={os.getenv('PGUSER', '')}",
                f"--dbname={os.getenv('PGDATABASE', '')}",
                "--format=plain",
                f"--file={backup_file}"
            ]

            # Set PGPASSWORD environment variable for the subprocess
            env = os.environ.copy()
            if os.getenv('PGPASSWORD'):
                env['PGPASSWORD'] = os.getenv('PGPASSWORD')

            result = subprocess.run(pg_dump_cmd, env=env, check=True, capture_output=True, text=True)
            if result.stderr:
                return False, f"Erro no pg_dump: {result.stderr}"
            return True, f"Backup do banco criado: {backup_file}"
        except subprocess.CalledProcessError as e:
            return False, f"Erro ao executar pg_dump: {e.stderr}"
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

            # Verificar quais arquivos existem antes de criar o ZIP
            existing_files = [f for f in files_to_backup if os.path.exists(f)]

            if not existing_files:
                return False, "Nenhum arquivo encontrado para backup"

            # Criar arquivo ZIP com os arquivos que existem
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in existing_files:
                    zipf.write(file)

            return True, f"Backup dos arquivos criado: {backup_file}"
        except Exception as e:
            return False, f"Erro ao criar backup dos arquivos: {str(e)}"

    def run_backup(self):
        """Executa backup completo"""
        results = []

        # Backup do banco
        success_db, msg_db = self.create_database_backup()
        results.append(msg_db)

        # Backup dos arquivos
        success_files, msg_files = self.create_files_backup()
        results.append(msg_files)

        # Se houver erro em algum dos backups, indicar no resultado
        if not success_db or not success_files:
            return "Erro: " + "\n".join(results)

        return "\n".join(results)

    def schedule_backups(self, interval_hours=24):
        """Agenda backups automáticos"""
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)

        schedule.every(interval_hours).hours.do(self.run_backup)
        scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        scheduler_thread.start()

    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = []
        if os.path.exists(self.backup_dir):
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
            if not os.path.exists(backup_file):
                return False, "Arquivo de backup não encontrado"

            psql_cmd = [
                "psql",
                f"--host={os.getenv('PGHOST', '')}",
                f"--port={os.getenv('PGPORT', '5432')}",
                f"--username={os.getenv('PGUSER', '')}",
                f"--dbname={os.getenv('PGDATABASE', '')}",
                f"--file={backup_file}"
            ]

            # Set PGPASSWORD environment variable for the subprocess
            env = os.environ.copy()
            if os.getenv('PGPASSWORD'):
                env['PGPASSWORD'] = os.getenv('PGPASSWORD')

            result = subprocess.run(psql_cmd, env=env, check=True, capture_output=True, text=True)
            if result.stderr and "ERROR" in result.stderr:
                return False, f"Erro ao restaurar: {result.stderr}"
            return True, "Backup restaurado com sucesso"
        except subprocess.CalledProcessError as e:
            return False, f"Erro ao executar psql: {e.stderr}"
        except Exception as e:
            return False, f"Erro ao restaurar backup: {str(e)}"