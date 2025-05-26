#!/usr/bin/env python3
"""
Script de inicialização otimizado para deploy no Replit Cloud Run
Configura automaticamente as variáveis de ambiente e parâmetros necessários
"""

import os
import sys
import subprocess

def setup_environment():
    """Configura o ambiente para produção"""
    
    # Definir porta dinâmica do Cloud Run
    port = os.environ.get('PORT', '5000')
    
    # Configurar variáveis específicas para produção
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
    
    print(f"🚀 Iniciando aplicação na porta {port}")
    print("🔧 Configurações de produção aplicadas")
    
    return port

def start_streamlit(port):
    """Inicia o Streamlit com configurações otimizadas"""
    
    cmd = [
        'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'true',
        '--server.enableXsrfProtection', 'false',
        '--server.fileWatcherType', 'none',
        '--server.runOnSave', 'false'
    ]
    
    print(f"📋 Comando: {' '.join(cmd)}")
    
    try:
        # Executar o comando
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Aplicação interrompida pelo usuário")
        sys.exit(0)

if __name__ == "__main__":
    print("🌟 Inicializando sistema em modo produção...")
    
    # Configurar ambiente
    port = setup_environment()
    
    # Iniciar aplicação
    start_streamlit(port)