"""
Script para criar um arquivo ZIP de deployment do projeto.
Este script exclui arquivos e diretórios desnecessários para reduzir o tamanho do pacote.
"""

import os
import shutil
import tempfile
import zipfile
import datetime
import streamlit as st
from pathlib import Path

def create_deployment_zip():
    """Cria um arquivo ZIP com todos os arquivos necessários para deployment"""
    
    # Configurações
    project_root = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"planner_organizer_deploy_{timestamp}.zip"
    
    # Arquivos e diretórios a serem excluídos do pacote
    excluded_items = [
        ".git", 
        ".gitignore", 
        "__pycache__", 
        "venv", 
        ".env", 
        ".venv", 
        "node_modules", 
        ".replit", 
        "replit.nix",
        "data",
        "temp_files",
        "uploaded_files",
        "backups",
        "backup_files",
        ".ipynb_checkpoints",
        "create_deployment_zip.py",
        "verificar_isolamento_dados.py",
        "verificar_autenticacao.py",
        "limpar_propostas.py",
        "limpar_clientes.py",
        "limpar_vendas.py",
        "excluir_venda_direto.py",
        "excluir_venda_simples.py",
        "excluir_vendas_standalone.py"
    ]
    
    # Arquivos que devem ser incluídos sempre
    required_files = [
        "app.py", 
        "render.yaml", 
        "render_startup.py", 
        "render_deploy_helper.py",
        "render_ready.txt",
        "requirements.txt",
        "Procfile",
        "README.md"
    ]
    
    # Diretórios que devem ser incluídos sempre
    required_dirs = [
        "utils",
        "pages",
        ".streamlit",
        "templates",
        "src",
        "api"
    ]
    
    # Criar diretório temporário
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copiar arquivos para o diretório temporário
        for item in os.listdir(project_root):
            src_path = os.path.join(project_root, item)
            dst_path = os.path.join(temp_dir, item)
            
            # Verificar se deve ser excluído
            if item in excluded_items:
                continue
                
            # Copiar
            if os.path.isdir(src_path):
                # Copiar diretório recursivamente, excluindo __pycache__
                shutil.copytree(
                    src_path, 
                    dst_path, 
                    ignore=shutil.ignore_patterns(*excluded_items)
                )
            else:
                # Copiar arquivo
                shutil.copy2(src_path, dst_path)
        
        # Verificar se os arquivos e diretórios requeridos estão presentes
        for file in required_files:
            src_file = os.path.join(project_root, file)
            dst_file = os.path.join(temp_dir, file)
            if os.path.exists(src_file) and not os.path.exists(dst_file):
                if os.path.isdir(src_file):
                    shutil.copytree(src_file, dst_file)
                else:
                    shutil.copy2(src_file, dst_file)
        
        for dir_name in required_dirs:
            src_dir = os.path.join(project_root, dir_name)
            dst_dir = os.path.join(temp_dir, dir_name)
            if os.path.exists(src_dir) and not os.path.exists(dst_dir):
                shutil.copytree(
                    src_dir, 
                    dst_dir, 
                    ignore=shutil.ignore_patterns(*excluded_items)
                )
        
        # Criar o arquivo ZIP
        zip_path = os.path.join(project_root, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
    
    return zip_path

def main():
    """Interface Streamlit para criar o ZIP de deployment"""
    st.set_page_config(
        page_title="Criar ZIP para Deploy",
        page_icon="📦",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    st.title("📦 Criar ZIP para Deploy")
    st.write("""
    Este utilitário cria um arquivo ZIP contendo todos os arquivos necessários 
    para fazer o deploy do Planner Organizer no Render ou em outro serviço.
    
    O arquivo ZIP exclui diretórios temporários e outros arquivos desnecessários
    para reduzir o tamanho do pacote e facilitar o upload.
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("""
        **Arquivos incluídos**: Código-fonte, templates, configurações
        
        **Arquivos excluídos**: Arquivos Git, caches, arquivos temporários,
        uploads de usuários, backups, ferramentas de debug
        """)
    
    with col2:
        if st.button("Criar ZIP de Deployment", type="primary"):
            with st.spinner("Criando arquivo ZIP..."):
                try:
                    zip_path = create_deployment_zip()
                    zip_size = Path(zip_path).stat().st_size / (1024 * 1024)  # Tamanho em MB
                    
                    st.success(f"ZIP criado com sucesso! ({zip_size:.1f} MB)")
                    
                    # Criar botão de download
                    with open(zip_path, "rb") as fp:
                        st.download_button(
                            label="Baixar ZIP",
                            data=fp,
                            file_name=os.path.basename(zip_path),
                            mime="application/zip"
                        )
                    
                    st.info("""
                    1. Faça o download do arquivo ZIP
                    2. No Render, escolha "Deploy from Upload" ao criar um novo Web Service
                    3. Faça upload deste arquivo ZIP
                    """)
                except Exception as e:
                    st.error(f"Erro ao criar ZIP: {str(e)}")
    
    st.divider()
    st.markdown("""
    ### Como usar no Render
    
    1. No dashboard do Render, clique em **New +** > **Web Service**
    2. Escolha **Deploy from Upload Files** (em vez de GitHub)
    3. Faça upload do arquivo ZIP baixado
    4. Configure:
       - **Name**: planner-organiza
       - **Runtime**: Python 3
       - **Build Command**: `pip install -r requirements.txt`
       - **Start Command**: `python render_deploy_helper.py && python render_startup.py && streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
    5. Adicione as variáveis de ambiente:
       - **DATABASE_URL**: URL do seu banco de dados PostgreSQL
       - **JWT_SECRET**: Uma string aleatória para segurança
       - **PYTHON_VERSION**: 3.11.0
    """)

if __name__ == "__main__":
    main()