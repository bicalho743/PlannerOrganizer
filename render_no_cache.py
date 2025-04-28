"""
Script para inicialização do sistema no Render sem problemas de cache
Este script deve ser executado antes da aplicação principal no Render
para garantir que as tabelas e colunas estejam corretamente configuradas.
"""
import os
import sys
import time
import subprocess

print("=== RENDER NO CACHE STARTUP ===")
print(f"Iniciando em: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Execute fix_render_schema.py to correct database schema
try:
    print("\n>>> Executando correção de esquema...")
    result = subprocess.run(
        [sys.executable, "fix_render_schema.py"],
        capture_output=True,
        text=True,
        check=True
    )
    print(result.stdout)
    print(">>> Correção de esquema concluída!")
except subprocess.CalledProcessError as e:
    print(f"ERRO na correção de esquema: {e}")
    print(f"Output: {e.stdout}")
    print(f"Error: {e.stderr}")
    print("\nTentando continuar mesmo com erro...")

# Start the main application
try:
    print("\n>>> Iniciando aplicação principal...")
    
    # Get the command to run (usually streamlit run app.py)
    cmd = os.environ.get('RENDER_STARTUP_COMMAND', 'streamlit run app.py --server.port 10000 --server.address 0.0.0.0')
    
    print(f"Comando: {cmd}")
    os.system(cmd)
except Exception as e:
    print(f"ERRO ao iniciar aplicação: {e}")
    sys.exit(1)