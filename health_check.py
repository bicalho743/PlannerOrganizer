#!/usr/bin/env python3
"""
Health Check para Deploy no Replit Cloud Run
Este arquivo verifica se a aplicação está funcionando corretamente
"""

import os
import sys
import requests
import time

def check_health():
    """Verifica se a aplicação está respondendo"""
    try:
        # Tentar conectar na porta padrão
        port = os.environ.get('PORT', '5000')
        url = f"http://0.0.0.0:{port}"
        
        # Fazer uma requisição simples
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Aplicação está funcionando corretamente!")
            return True
        else:
            print(f"❌ Aplicação retornou status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar saúde da aplicação: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Iniciando verificação de saúde da aplicação...")
    
    # Aguardar um pouco para a aplicação inicializar
    time.sleep(5)
    
    # Verificar saúde
    if check_health():
        sys.exit(0)  # Sucesso
    else:
        sys.exit(1)  # Falha