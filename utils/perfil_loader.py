import os
import json
import streamlit as st

def carregar_perfil_para_relatorios():
    """
    Carrega os dados do perfil do usuário para usar em relatórios
    
    Returns:
        dict: Dicionário com as informações de contato do usuário
    """
    # Valores padrão
    dados = {
        'nome_empresa': "Planner Organizer",
        'email_contato': "contato@plannerorganizer.com.br",
        'telefone_contato': "(11) 98765-4321",
        'website': "www.plannerorganizer.com.br",
        'instagram': "",
        'mensagem_personalizada': "Agradecemos a confiança em nossos serviços."
    }
    
    # Tentar obter dados da sessão
    if "usuario" not in st.session_state or not st.session_state.usuario:
        return dados
    
    usuario = st.session_state.usuario
    
    # Verificar se existe perfil salvo
    if not isinstance(usuario, dict) or not usuario.get("email"):
        return dados
    
    # Normalizar o ID do usuário para uso em nome de arquivo
    user_id = usuario.get("email")
    user_id_normalizado = user_id.replace('@', '_at_').replace('.', '_dot_')
    
    # Tentar carregar perfil para dados mais completos
    perfil_path = f"data/perfis/{user_id_normalizado}.json"
    
    try:
        if os.path.exists(perfil_path):
            with open(perfil_path, 'r', encoding='utf-8') as f:
                perfil = json.load(f)
                
                # Usar informações do perfil salvo
                if perfil.get("empresa"):
                    dados['nome_empresa'] = perfil.get("empresa")
                elif perfil.get("nome"):
                    dados['nome_empresa'] = perfil.get("nome")
                    
                if perfil.get("email"):
                    dados['email_contato'] = perfil.get("email")
                    
                if perfil.get("telefone"):
                    dados['telefone_contato'] = perfil.get("telefone")
                    
                if perfil.get("website"):
                    dados['website'] = perfil.get("website")
                    
                if perfil.get("instagram"):
                    dados['instagram'] = perfil.get("instagram")
                    
                if perfil.get("mensagem_padrao"):
                    dados['mensagem_personalizada'] = perfil.get("mensagem_padrao")
        else:
            # Caso não exista perfil, usar dados básicos da sessão
            if usuario.get("empresa"):
                dados['nome_empresa'] = usuario.get("empresa")
            elif usuario.get("nome"):
                dados['nome_empresa'] = usuario.get("nome")
            
            if usuario.get("email"):
                dados['email_contato'] = usuario.get("email")
                
            if usuario.get("telefone"):
                dados['telefone_contato'] = usuario.get("telefone")
    except Exception as e:
        print(f"Erro ao carregar perfil para PDF: {str(e)}")
    
    return dados