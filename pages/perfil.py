import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

from utils.page_config import apply_page_header, apply_page_footer

def salvar_perfil_usuario(dados_perfil):
    """
    Salva as informações do perfil do usuário na sessão e também
    em um arquivo JSON para persistência
    
    Args:
        dados_perfil: Dicionário com os dados do perfil
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Atualizar objeto na sessão
        if "usuario" not in st.session_state:
            st.session_state.usuario = {}
            
        # Atualizar campos do perfil
        st.session_state.usuario.update(dados_perfil)
        
        # Criar diretório para perfis de usuários se não existir
        os.makedirs("data/perfis", exist_ok=True)
        
        # Gerar ID único para o usuário se não existir
        if "user_id" not in st.session_state.usuario:
            st.session_state.usuario["user_id"] = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        # Salvar em arquivo JSON
        user_id = st.session_state.usuario["user_id"]
        arquivo_perfil = f"data/perfis/{user_id}.json"
        
        with open(arquivo_perfil, "w") as f:
            json.dump(st.session_state.usuario, f, indent=2)
            
        return True
    except Exception as e:
        st.error(f"Erro ao salvar perfil: {str(e)}")
        return False

def carregar_perfil_usuario():
    """
    Carrega as informações do perfil do usuário da sessão ou do arquivo
    
    Returns:
        dict: Dados do perfil ou dicionário vazio
    """
    # Se já existe na sessão, retornar
    if "usuario" in st.session_state and st.session_state.usuario:
        return st.session_state.usuario
    
    # Tentar carregar do arquivo se houver user_id
    try:
        if "user_id" in st.session_state:
            arquivo_perfil = f"data/perfis/{st.session_state.user_id}.json"
            if os.path.exists(arquivo_perfil):
                with open(arquivo_perfil, "r") as f:
                    return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar perfil: {str(e)}")
        
    # Se não encontrou, retornar vazio
    return {}

def show():
    """Exibe a página de perfil do usuário"""
    # Configuração da página
    apply_page_header()
    
    # Título da página
    st.title("🧑‍💼 Meu Perfil")
    
    # Carregar dados atuais do perfil
    perfil = carregar_perfil_usuario()
    
    # Formulário para edição do perfil
    with st.form("formulario_perfil"):
        st.subheader("Informações Pessoais")
        
        # Campos pessoais
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo", 
                                value=perfil.get("nome", ""))
        with col2:
            email = st.text_input("Email", 
                                 value=perfil.get("email", ""), 
                                 disabled="email" in perfil)
        
        st.subheader("Informações Profissionais")
        
        # Campos profissionais
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Empresa/Negócio", 
                                   value=perfil.get("empresa", ""))
        with col2:
            telefone = st.text_input("Telefone para contato", 
                                    value=perfil.get("telefone", ""), 
                                    help="Formato: (00) 00000-0000")
        
        # Redes sociais
        st.subheader("Redes Sociais")
        col1, col2 = st.columns(2)
        with col1:
            instagram = st.text_input("Instagram", 
                                     value=perfil.get("instagram", ""), 
                                     help="Sem o '@'. Ex: seu_perfil")
        with col2:
            site = st.text_input("Website", 
                                value=perfil.get("site", ""),
                                help="URL completa. Ex: https://seusite.com.br")
        
        # Sobre mim / Bio
        st.subheader("Sobre mim")
        bio = st.text_area("Descrição profissional", 
                          value=perfil.get("bio", ""),
                          help="Esta descrição aparecerá nos relatórios e propostas enviados aos clientes",
                          height=150)
        
        # Preferências de notificação
        st.subheader("Preferências")
        
        col1, col2 = st.columns(2)
        with col1:
            notificar_email = st.checkbox("Receber notificações por email", 
                                         value=perfil.get("notificar_email", True))
        with col2:
            mostrar_valores = st.checkbox("Mostrar valores na página inicial", 
                                         value=perfil.get("mostrar_valores", True))
        
        # Botão para salvar
        st.markdown("### ")  # Espaçador
        salvar = st.form_submit_button("Salvar Perfil", use_container_width=True)
        
        if salvar:
            # Criar dicionário com os dados do formulário
            dados_perfil = {
                "nome": nome,
                "email": email if not "email" in perfil else perfil["email"],
                "empresa": empresa,
                "telefone": telefone,
                "instagram": instagram,
                "site": site,
                "bio": bio,
                "notificar_email": notificar_email,
                "mostrar_valores": mostrar_valores,
                "ultima_atualizacao": datetime.now().isoformat()
            }
            
            # Manter campos que não são editáveis
            if "role" in perfil:
                dados_perfil["role"] = perfil["role"]
                
            # Salvar o perfil
            if salvar_perfil_usuario(dados_perfil):
                st.success("✅ Perfil salvo com sucesso!")
                
                # Forçar atualização da interface
                st.rerun()
            else:
                st.error("❌ Erro ao salvar perfil. Tente novamente.")
    
    # Informação adicional
    with st.expander("📋 Informações sobre o Perfil"):
        st.markdown("""
        **Seus dados são usados para:**
        
        - Personalizar relatórios e propostas para clientes
        - Identificá-lo no sistema
        - Fornecer experiência personalizada
        
        Mantenha seus dados atualizados para garantir que suas propostas e relatórios contenham 
        as informações de contato corretas.
        """)
        
        # Debug - mostrar dados atuais do perfil (remover em produção)
        if st.checkbox("Mostrar dados do perfil (DEBUG)", value=False):
            st.write(perfil)
            st.write("Session state:", st.session_state)
    
    # Rodapé
    apply_page_footer()

# Inicializar a interface se executado diretamente
if __name__ == "__main__":
    show()