"""
Módulo para carregar e manipular dados do perfil do usuário.
Este módulo fornece funções para carregar, salvar e acessar os dados do perfil
do usuário logado, facilitando a centralização dessas informações.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def carregar_perfil_usuario():
    """
    Carrega os dados do perfil do usuário atual.
    
    Returns:
        dict: Dicionário com os dados do perfil do usuário
    """
    # Verificar se o usuário está logado
    if "usuario" not in st.session_state or not st.session_state.usuario:
        print("DEBUG PERFIL: Usuário não logado, retornando perfil padrão.")
        return get_perfil_padrao()
    
    usuario = st.session_state.usuario
    
    # Verificar se é um dicionário
    if not isinstance(usuario, dict):
        print("DEBUG PERFIL: Usuário não é um dicionário, tentando converter.")
        # Tentar converter para dicionário
        try:
            if hasattr(usuario, 'to_dict'):
                usuario = usuario.to_dict()
            else:
                # Extrair atributos conhecidos
                usuario = {
                    'nome': getattr(usuario, 'nome', None),
                    'email': getattr(usuario, 'email', None),
                    'empresa': getattr(usuario, 'empresa', None),
                    'telefone': getattr(usuario, 'telefone', None),
                    'instagram': getattr(usuario, 'instagram', None),
                }
        except Exception as e:
            print(f"DEBUG PERFIL ERROR: Não foi possível converter usuário: {str(e)}")
            return get_perfil_padrao()
    
    # Limpar URLs de Instagram (remover @ e https)
    if 'instagram' in usuario and usuario['instagram']:
        instagram = usuario['instagram']
        if instagram.startswith('@'):
            instagram = instagram.replace('@', '', 1)
        if instagram.startswith('https://www.instagram.com/'):
            instagram = instagram.replace('https://www.instagram.com/', '', 1)
        if instagram.endswith('/'):
            instagram = instagram[:-1]
        usuario['instagram'] = instagram
    
    # Verificar e complementar dados ausentes
    perfil = get_perfil_padrao()
    
    # Atualizar com dados do usuário atual
    for chave in perfil.keys():
        if chave in usuario and usuario[chave]:
            perfil[chave] = usuario[chave]
    
    return perfil

def salvar_perfil_usuario(dados_perfil):
    """
    Salva os dados do perfil do usuário na sessão.
    
    Args:
        dados_perfil: Dicionário com os dados do perfil
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Verificar se o usuário está logado
        if "usuario" not in st.session_state or not st.session_state.usuario:
            print("DEBUG PERFIL ERROR: Usuário não logado, não é possível salvar perfil.")
            return False
        
        # Atualizar dados do usuário
        usuario = st.session_state.usuario
        
        # Se for um dicionário, atualizamos diretamente
        if isinstance(usuario, dict):
            for chave, valor in dados_perfil.items():
                usuario[chave] = valor
        else:
            # Tentar atualizar atributos
            for chave, valor in dados_perfil.items():
                if hasattr(usuario, chave):
                    setattr(usuario, chave, valor)
        
        # Atualizar na sessão
        st.session_state.usuario = usuario
        
        print("DEBUG PERFIL: Perfil do usuário atualizado com sucesso.")
        return True
    
    except Exception as e:
        print(f"DEBUG PERFIL ERROR: Erro ao salvar perfil: {str(e)}")
        return False

def get_perfil_padrao():
    """
    Retorna um perfil com valores padrão.
    
    Returns:
        dict: Dicionário com valores padrão para o perfil
    """
    return {
        'nome': 'Planner Organizer',
        'email': 'contato@plannerorganizer.com.br',
        'telefone': '(11) 98765-4321',
        'empresa': 'Planner Organizer', 
        'instagram': 'plannerorganizer',
        'website': 'www.plannerorganizer.com.br',
        'cor_principal': '#1E366F',  # Azul escuro
        'cor_secundaria': '#e9f2ff',  # Azul claro
    }

def formatar_instagram(usuario):
    """
    Formata o nome de usuário do Instagram para exibição.
    
    Args:
        usuario: Nome de usuário do Instagram
        
    Returns:
        str: Nome de usuário formatado
    """
    if not usuario:
        return None
    
    # Remover @ se existir
    if usuario.startswith('@'):
        usuario = usuario[1:]
    
    # Remover URL se for uma URL
    if usuario.startswith('http'):
        usuario = usuario.split('/')[-1]
    
    # Adicionar @ de volta
    return f"@{usuario}"

def formatar_telefone(telefone):
    """
    Formata um número de telefone para exibição.
    
    Args:
        telefone: Número de telefone
        
    Returns:
        str: Número de telefone formatado
    """
    if not telefone:
        return None
    
    # Remover caracteres não numéricos
    numeros = ''.join(filter(str.isdigit, telefone))
    
    if len(numeros) == 11:  # Celular
        return f"({numeros[0:2]}) {numeros[2:7]}-{numeros[7:11]}"
    elif len(numeros) == 10:  # Telefone fixo
        return f"({numeros[0:2]}) {numeros[2:6]}-{numeros[6:10]}"
    else:
        return telefone  # Retorna original se não reconhecer o formato