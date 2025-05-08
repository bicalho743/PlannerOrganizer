import streamlit as st
import os
import sys
import json
import pandas as pd
from datetime import datetime

# Adicionar diretório raiz ao path para poder importar os módulos de utils
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.brevo_helper import obter_listas_brevo, exportar_contatos_para_brevo

# Configurações da página
st.set_page_config(
    page_title="Gerenciar Capturas de Email - Planner Organizer",
    page_icon="favicon.png",
    layout="wide"
)

# Verifica autenticação
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Você precisa estar autenticado para acessar esta página.")
    st.stop()

# Título da página
st.title("Gerenciamento de Capturas de Email")
st.subheader("Configuração e administração de e-mails capturados")

# Define o caminho para o arquivo de capturas
arquivo_capturas = os.path.join("data", "captured_emails.json")

# Função para carregar os e-mails capturados
def carregar_emails_capturados():
    """Carrega os e-mails capturados do arquivo local"""
    if not os.path.exists(arquivo_capturas):
        return []
    
    try:
        with open(arquivo_capturas, 'r') as f:
            dados = json.load(f)
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar e-mails capturados: {e}")
        return []

# Função para salvar chave API
def salvar_chave_api(chave):
    """Salva a chave API do Brevo nas variáveis de ambiente"""
    os.environ["BREVO_API_KEY"] = chave
    
    # Também salva em um arquivo para persistência entre sessões
    config_dir = os.path.join("data", "config")
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "brevo_config.json")
    with open(config_file, 'w') as f:
        json.dump({"api_key": chave}, f)
    
    return True

# Criando abas para organizar a interface
tab1, tab2, tab3 = st.tabs(["Configuração", "Visualizar Capturas", "Exportar para Brevo"])

# Aba 1: Configuração da API
with tab1:
    st.subheader("Configuração da API Brevo")
    
    # Verifica se já existe uma chave salva
    chave_atual = os.environ.get("BREVO_API_KEY", "")
    tem_chave = bool(chave_atual)
    
    # Exibe status atual
    if tem_chave:
        st.success("✅ API Brevo configurada")
        chave_mascarada = chave_atual[:4] + "*" * (len(chave_atual) - 8) + chave_atual[-4:] if len(chave_atual) > 8 else "****"
        st.info(f"Chave atual: {chave_mascarada}")
    else:
        st.warning("⚠️ API Brevo não configurada")
    
    # Campo para inserir nova chave
    nova_chave = st.text_input("Chave da API Brevo", 
                               value="", 
                               type="password",
                               help="Insira a chave da API do Brevo para integração direta")
    
    # Botão para salvar a chave
    if st.button("Salvar chave da API", use_container_width=True):
        if not nova_chave:
            st.error("Por favor, insira uma chave da API.")
        else:
            sucesso = salvar_chave_api(nova_chave)
            if sucesso:
                st.success("✅ Chave da API salva com sucesso!")
                st.rerun()  # Atualiza a página para refletir a nova configuração
    
    # Instruções para obter a chave
    with st.expander("Como obter sua chave de API Brevo"):
        st.markdown("""
        ### Passos para obter uma chave de API do Brevo:
        
        1. Acesse sua conta no [Brevo](https://app.brevo.com/)
        2. Vá para **Configurações** > **Integração**
        3. Clique em **API Keys**
        4. Gere uma nova chave de API ou use uma existente
        5. Copie a chave e cole no campo acima
        
        A chave de API permite que o sistema envie os e-mails capturados diretamente para sua lista de contatos no Brevo.
        """)

# Aba 2: Visualizar e-mails capturados
with tab2:
    st.subheader("E-mails Capturados Localmente")
    
    # Carregar os e-mails capturados
    emails_capturados = carregar_emails_capturados()
    
    # Exibir contagem
    st.info(f"Total de e-mails capturados: {len(emails_capturados)}")
    
    # Verificar se há e-mails para exibir
    if not emails_capturados:
        st.warning("Nenhum e-mail capturado encontrado.")
    else:
        # Criar DataFrame para exibição mais amigável
        df = pd.DataFrame(emails_capturados)
        
        # Formatar as datas para exibição
        if 'captured_at' in df.columns:
            df['data_captura'] = pd.to_datetime(df['captured_at']).dt.strftime('%d/%m/%Y %H:%M')
        
        # Ordenar por data de captura (mais recente primeiro)
        if 'captured_at' in df.columns:
            df = df.sort_values('captured_at', ascending=False)
        
        # Selecionar colunas relevantes para exibição
        colunas_exibir = ['email', 'first_name', 'last_name', 'data_captura', 'source']
        colunas_exibir = [col for col in colunas_exibir if col in df.columns]
        
        # Renomear colunas para português
        mapeamento_colunas = {
            'email': 'Email',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'data_captura': 'Data de Captura',
            'source': 'Origem'
        }
        
        # Aplicar renomeação nas colunas disponíveis
        rename_dict = {col: mapeamento_colunas.get(col, col) for col in colunas_exibir}
        df_exibir = df[colunas_exibir].rename(columns=rename_dict)
        
        # Exibir a tabela com possibilidade de filtro
        st.dataframe(df_exibir, use_container_width=True)
        
        # Opção para exportar como CSV
        csv = df_exibir.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar como CSV",
            data=csv,
            file_name=f"emails_capturados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

# Aba 3: Exportar para Brevo
with tab3:
    st.subheader("Exportar Contatos para Brevo")
    
    # Verificar se a API está configurada
    tem_api = bool(os.environ.get("BREVO_API_KEY", ""))
    
    if not tem_api:
        st.error("⚠️ Você precisa configurar a API do Brevo na aba Configuração antes de exportar contatos.")
    else:
        # Carregar os e-mails capturados
        emails_capturados = carregar_emails_capturados()
        
        if not emails_capturados:
            st.warning("Não há e-mails capturados para exportar.")
        else:
            st.info(f"Existem {len(emails_capturados)} e-mails capturados que podem ser exportados para o Brevo.")
            
            # Obter listas disponíveis no Brevo
            listas = obter_listas_brevo()
            
            if not listas:
                st.warning("Não foi possível obter as listas do Brevo. Verifique sua chave de API.")
            else:
                # Criar opções de seleção para as listas
                lista_opcoes = [{"label": f"{lista['name']} (ID: {lista['id']})", "value": lista['id']} for lista in listas]
                lista_opcoes.insert(0, {"label": "Nenhuma (apenas adicionar contatos)", "value": None})
                
                # Permitir seleção da lista
                lista_selecionada = st.selectbox(
                    "Selecione a lista para adicionar os contatos:",
                    options=[opcao["value"] for opcao in lista_opcoes],
                    format_func=lambda x: next((opcao["label"] for opcao in lista_opcoes if opcao["value"] == x), str(x))
                )
                
                # Botão para exportar
                if st.button("Exportar contatos para Brevo", use_container_width=True):
                    with st.spinner("Exportando contatos..."):
                        resultado = exportar_contatos_para_brevo()
                        
                        if resultado["success"]:
                            st.success(resultado["message"])
                            
                            # Se foi bem sucedido, oferecer recarregar a página
                            if st.button("Atualizar página", use_container_width=True):
                                st.rerun()
                        else:
                            st.error(resultado["message"])

# Rodapé informativo
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Esta ferramenta permite gerenciar os e-mails capturados a partir da página de planos.</p>
    <p>Os e-mails são armazenados localmente quando a API do Brevo não está configurada.</p>
</div>
""", unsafe_allow_html=True)

# Executar o script principal se chamado diretamente
if __name__ == "__main__":
    # O código já está sendo executado acima
    pass