
#!/usr/bin/env python3
"""
Script para limpeza de arquivos duplicados e desnecessários
"""
import os
import shutil

def cleanup_project():
    """Remove arquivos duplicados e desnecessários"""
    
    # Arquivos para remover
    files_to_remove = [
        'app_simple.py',
        'app_stable.py', 
        'login_simples.py',
        'planos_standalone.py',
        'todas_propostas_simples.py',
        'enviar_manual_simples.py',
        'gerar_csv_propostas.py',
        'health_check.py',
        'importar_clientes.py',
        'reabrir_proposta.py',
        'lista_arquivos.txt',
        'profile_auth_fixes.diff',
        'financeiro_filtro.patch',
        'render_ready.txt',
        'professional_woman.png',  # Manter apenas professional_business_woman.png
        'generated-icon.png',
        'DEPLOY.md'
    ]
    
    # Remover arquivos desnecessários
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ Removido: {file}")
    
    # Limpar pasta attached_assets de arquivos temporários
    if os.path.exists('attached_assets'):
        for file in os.listdir('attached_assets'):
            if file.startswith('Pasted-') or file.endswith('.txt'):
                file_path = os.path.join('attached_assets', file)
                os.remove(file_path)
                print(f"✅ Removido asset temporário: {file}")
    
    print("🎉 Limpeza concluída!")

if __name__ == "__main__":
    cleanup_project()
