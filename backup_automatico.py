"""
Sistema de Backup Automático para Produção
Cria backups regulares do banco de dados e arquivos importantes
"""

import os
import schedule
import time
import subprocess
from datetime import datetime
import logging
from pathlib import Path
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

class BackupAutomatico:
    def __init__(self):
        self.backup_dir = Path("backups_producao")
        self.backup_dir.mkdir(exist_ok=True)
        
    def criar_backup_banco(self):
        """Cria backup do banco de dados PostgreSQL"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_db_{timestamp}.sql"
            
            # Comando para backup do PostgreSQL
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logging.error("DATABASE_URL não encontrada")
                return False
                
            cmd = f"pg_dump {database_url} > {backup_file}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"✅ Backup do banco criado: {backup_file}")
                return True
            else:
                logging.error(f"❌ Erro no backup: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Erro ao criar backup: {e}")
            return False
    
    def backup_arquivos_importantes(self):
        """Backup de arquivos de configuração e uploads"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Pastas importantes para backup
            pastas_importantes = [
                "uploaded_files",
                "pdfs", 
                "utils",
                "pages"
            ]
            
            backup_arquivo = self.backup_dir / f"backup_arquivos_{timestamp}.zip"
            
            # Criar zip com arquivos importantes
            import zipfile
            with zipfile.ZipFile(backup_arquivo, 'w') as zipf:
                # Backup das pastas
                for pasta in pastas_importantes:
                    if os.path.exists(pasta):
                        for root, dirs, files in os.walk(pasta):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path)
                
                # Backup de arquivos importantes da raiz
                arquivos_raiz = ['app.py', 'requirements.txt', 'pyproject.toml']
                for arquivo in arquivos_raiz:
                    if os.path.exists(arquivo):
                        zipf.write(arquivo)
            
            logging.info(f"✅ Backup de arquivos criado: {backup_arquivo}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Erro no backup de arquivos: {e}")
            return False
    
    def limpar_backups_antigos(self, dias_manter=7):
        """Remove backups mais antigos que X dias"""
        try:
            import time
            agora = time.time()
            limite = agora - (dias_manter * 24 * 60 * 60)
            
            removidos = 0
            for arquivo in self.backup_dir.glob("backup_*"):
                if arquivo.stat().st_mtime < limite:
                    arquivo.unlink()
                    removidos += 1
            
            if removidos > 0:
                logging.info(f"🗑️ Removidos {removidos} backups antigos")
                
        except Exception as e:
            logging.error(f"❌ Erro ao limpar backups: {e}")
    
    def backup_completo(self):
        """Executa backup completo (banco + arquivos)"""
        logging.info("🚀 Iniciando backup completo...")
        
        sucesso_banco = self.criar_backup_banco()
        sucesso_arquivos = self.backup_arquivos_importantes()
        self.limpar_backups_antigos()
        
        if sucesso_banco and sucesso_arquivos:
            logging.info("✅ Backup completo realizado com sucesso!")
        else:
            logging.warning("⚠️ Backup parcialmente concluído")
    
    def iniciar_agendamento(self):
        """Configura os agendamentos automáticos"""
        # Backup completo diário às 2h da manhã
        schedule.every().day.at("02:00").do(self.backup_completo)
        
        # Backup rápido do banco a cada 6 horas
        schedule.every(6).hours.do(self.criar_backup_banco)
        
        logging.info("📅 Agendamentos de backup configurados:")
        logging.info("   - Backup completo: diário às 2h")
        logging.info("   - Backup do banco: a cada 6 horas")
        
        # Loop principal
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto

def main():
    """Função principal para executar o sistema de backup"""
    backup_system = BackupAutomatico()
    
    # Fazer um backup imediato
    backup_system.backup_completo()
    
    # Iniciar agendamentos (descomente para produção)
    # backup_system.iniciar_agendamento()

if __name__ == "__main__":
    main()