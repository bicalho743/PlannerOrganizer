"""
Script para iniciar a aplicação no estado do MVP16042025
Este script configura a aplicação para iniciar no estado do MVP,
carregando todos os componentes necessários.
"""
import streamlit as st
import os
import sys
import subprocess
import json

# Configuração da página
st.set_page_config(
    page_title="Planner Organiza - MVP16042025",
    page_icon="📊",
    layout="wide"
)

# Título da aplicação
st.title("📊 Planner Organiza - Restauração do MVP16042025")

# Descrição do MVP
st.markdown("""
## Estado do MVP16042025

Este é o estado do MVP (Minimum Viable Product) do sistema Planner Organizer 
com as seguintes funcionalidades implementadas e funcionando:

### Principais recursos

1. **Cadastros completos:**
   - Clientes (com exclusão individual e múltipla)
   - Fornecedores
   - Parceiros
   - Assistentes

2. **Gerenciamento de propostas:**
   - Cadastro de propostas
   - Fluxo de status: Em elaboração → Aguardando aprovação → Aprovada → Em execução → Finalizada
   - Geração automática de registros financeiros

3. **Módulo financeiro:**
   - Registro de receitas e despesas
   - Vinculação com propostas
   - Relatórios financeiros
   
4. **Vendas:**
   - Registro de vendas
   - Vinculação com clientes e propostas

5. **Dashboard:**
   - Visão geral
   - Alertas de retorno cliente
   - Estatísticas de desempenho

6. **Funcionalidades adicionais:**
   - Sistema de importação de dados (clientes, propostas)
   - Sistema de backups
   - Melhorias de interface e experiência do usuário
""")

# Verificar os workflows em execução
st.header("Workflows em Execução")

def get_running_workflows():
    """Retorna uma lista dos workflows atualmente em execução"""
    try:
        # Comando que obtém os workflows em execução
        cmd = "ps -ef | grep streamlit | grep -v grep | awk '{print $8, $9, $10, $11, $12, $13, $14, $15}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        workflows = []
        
        for line in result.stdout.splitlines():
            if 'streamlit run' in line:
                # Extrair o nome do script e a porta
                parts = line.split()
                script_idx = parts.index('run') + 1 if 'run' in parts else -1
                
                if script_idx > 0 and script_idx < len(parts):
                    script = parts[script_idx]
                    port_idx = -1
                    
                    try:
                        port_idx = parts.index('--server.port') + 1
                    except ValueError:
                        port = "N/A"
                    
                    if port_idx > 0 and port_idx < len(parts):
                        port = parts[port_idx]
                    else:
                        port = "N/A"
                    
                    workflows.append({
                        'script': script,
                        'port': port,
                        'url': f"http://0.0.0.0:{port}" if port != "N/A" else "N/A"
                    })
        
        return workflows
    except Exception as e:
        st.error(f"Erro ao obter workflows: {e}")
        return []

# Exibir workflows
workflows = get_running_workflows()

if workflows:
    st.write(f"Encontrados {len(workflows)} workflows em execução:")
    
    # Criar uma tabela para exibir os workflows
    workflow_data = []
    for wf in workflows:
        workflow_data.append({
            "Script": wf['script'],
            "Porta": wf['port'],
            "URL": wf['url']
        })
    
    # Exibir como tabela
    st.table(workflow_data)
    
    # Adicionar links de acesso
    st.subheader("Acessar Aplicações Principais")
    
    col1, col2, col3 = st.columns(3)
    
    for wf in workflows:
        script_name = wf['script']
        url = wf['url']
        
        if 'login' in script_name.lower() and url != "N/A":
            with col1:
                st.markdown(f"[🔐 Login/Autenticação]({url})")
        
        if 'app.py' == script_name and url != "N/A":
            with col2:
                st.markdown(f"[📱 Aplicação Principal]({url})")
        
        if 'backup' in script_name.lower() and url != "N/A":
            with col3:
                st.markdown(f"[💾 Sistema de Backup]({url})")
else:
    st.warning("Nenhum workflow do Streamlit encontrado em execução.")

# Seção para iniciar aplicativos principais
st.header("Iniciar Aplicativos Principais")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Aplicação Principal")
    
    if st.button("Iniciar Aplicação Principal", key="start_main_app"):
        try:
            # Executar app.py em uma nova janela
            subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0"])
            st.success("Aplicação principal iniciada! Acesse em: http://0.0.0.0:5000")
        except Exception as e:
            st.error(f"Erro ao iniciar aplicação principal: {e}")

with col2:
    st.subheader("Sistema de Backup")
    
    if st.button("Iniciar Sistema de Backup", key="start_backup"):
        try:
            # Executar criar_ponto_backup.py em uma nova janela
            subprocess.Popen(["streamlit", "run", "criar_ponto_backup.py", "--server.port", "5001", "--server.address", "0.0.0.0"])
            st.success("Sistema de backup iniciado! Acesse em: http://0.0.0.0:5001")
        except Exception as e:
            st.error(f"Erro ao iniciar sistema de backup: {e}")

# Seção para módulos adicionais
st.header("Módulos Adicionais")

modules = [
    {"name": "Importar Clientes", "script": "importar_clientes.py", "port": "5002"},
    {"name": "Importar Propostas", "script": "importar_propostas.py", "port": "5003"},
    {"name": "Ajustar Data Proposta", "script": "ajustar_data_proposta.py", "port": "5004"},
    {"name": "Limpar Propostas", "script": "limpar_propostas.py", "port": "5005"},
    {"name": "Limpar Clientes", "script": "limpar_clientes.py", "port": "5006"},
    {"name": "Examinar Tabela Propostas", "script": "examinar_tabela_propostas.py", "port": "5007"}
]

# Criar botões para cada módulo
cols = st.columns(3)
for i, module in enumerate(modules):
    with cols[i % 3]:
        if st.button(f"Iniciar {module['name']}", key=f"start_{i}"):
            try:
                # Executar o script em uma nova janela
                subprocess.Popen([
                    "streamlit", "run", module["script"],
                    "--server.port", module["port"],
                    "--server.address", "0.0.0.0"
                ])
                st.success(f"{module['name']} iniciado! Acesse em: http://0.0.0.0:{module['port']}")
            except Exception as e:
                st.error(f"Erro ao iniciar {module['name']}: {e}")

# Mostrar links úteis
st.header("Links Úteis")

st.markdown("""
- [Documentação do MVP16042025](backups/MVP16042025.md)
- [Verificar Estado do Banco de Dados](http://0.0.0.0:8999) (Firebase-PostgreSQL)
""")

# Informações de ajuda
st.sidebar.header("Informações")
st.sidebar.info("""
**Planner Organiza - MVP16042025**

Este é o estado do MVP (Minimum Viable Product) do sistema Planner Organizer
concluído em 16/04/2025.

O MVP pode ser utilizado como está para:
- Cadastro e gerenciamento de clientes
- Criação e acompanhamento de propostas
- Rastreamento financeiro
- Gerenciamento de vendas

Para mais informações, consulte a documentação completa.
""")

# Exibir data e hora atual
import datetime
st.sidebar.write(f"Data atual: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")