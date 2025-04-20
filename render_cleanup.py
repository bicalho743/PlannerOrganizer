#!/usr/bin/env python3
"""
Script para remover todas as versões do Stripe e instalar apenas a versão 11.6.0
Este script é executado como parte do processo de build no Render
"""

import os
import sys
import subprocess
import pkg_resources

def run_command(command):
    """Executa um comando shell e retorna a saída"""
    print(f"Executando: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro ao executar o comando: {result.stderr}")
    else:
        print(f"Saída: {result.stdout}")
    return result

def main():
    """Função principal para limpar e reinstalar o Stripe"""
    print("Iniciando limpeza de versões do Stripe...")
    
    # Verificar se o Stripe está instalado
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    if 'stripe' in installed_packages:
        print(f"Stripe versão {installed_packages['stripe']} encontrado. Removendo...")
        run_command("pip uninstall -y stripe")
    else:
        print("Stripe não está instalado.")
    
    # Instalar a versão correta do Stripe
    print("Instalando Stripe versão 11.6.0...")
    result = run_command("pip install --no-cache-dir stripe==11.6.0")
    
    if result.returncode == 0:
        print("Stripe 11.6.0 instalado com sucesso!")
    else:
        print("FALHA ao instalar Stripe 11.6.0. Verificando possíveis conflitos...")
        run_command("pip check")
    
    # Verificar a versão instalada
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    if 'stripe' in installed_packages:
        print(f"Versão final do Stripe instalada: {installed_packages['stripe']}")
    else:
        print("ERRO: Stripe não está instalado após tentativa de instalação.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())