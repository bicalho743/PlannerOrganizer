"""
Módulo de apoio para operações com propostas.
Este arquivo contém funções utilitárias para trabalhar com propostas
de forma isolada e robusta.
"""
import os
import traceback
from datetime import datetime
import pandas as pd
import streamlit as st
from utils.pdf_generator import gerar_pdf_fechamento

def adicionar_acrescimo(db, proposta_id, tipo, fornecedor, descricao, valor):
    """
    Adiciona um acréscimo a uma proposta de forma segura, com tratamento 
    de erros abrangente.
    
    Args:
        db: Conexão com o banco de dados
        proposta_id: ID da proposta
        tipo: Tipo de acréscimo
        fornecedor: Nome do fornecedor
        descricao: Descrição do acréscimo
        valor: Valor do acréscimo
        
    Returns:
        tuple: (sucesso, mensagem, acrescimo_id)
            - sucesso: True se operação foi bem-sucedida, False caso contrário
            - mensagem: Mensagem explicativa do resultado
            - acrescimo_id: ID do acréscimo adicionado (ou None em caso de falha)
    """
    print(f"DEBUG HELPER: Adicionando acréscimo à proposta ID={proposta_id}")
    
    try:
        # Validar valor
        if not valor or float(valor) <= 0:
            return False, "O valor do acréscimo deve ser maior que zero.", None
        
        # Validar proposta_id
        if not proposta_id or not str(proposta_id).isdigit():
            return False, "ID da proposta inválido.", None
        
        # Definições padrão para campos opcionais
        if not fornecedor:
            fornecedor = f"{tipo} Padrão"
        
        if not descricao:
            descricao = f"Acréscimo de {tipo}"
        
        # Tentar buscar a proposta (para garantir que existe)
        proposta = None
        try:
            propostas = db.get_propostas()
            if not propostas.empty:
                proposta_found = propostas[propostas['id'] == int(proposta_id)]
                if not proposta_found.empty:
                    proposta = proposta_found.iloc[0]
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar proposta: {str(e)}")
            
        # Verificar se proposta existe
        if proposta is None:
            return False, f"Proposta ID={proposta_id} não encontrada.", None
        
        # Tentar adicionar o acréscimo
        acrescimo_id = db.add_acrescimo_proposta(
            proposta_id=proposta_id,
            tipo=tipo,
            fornecedor=fornecedor,
            descricao=descricao,
            valor=float(valor),
            status_pagamento="Pendente"
        )
        
        if not acrescimo_id:
            return False, "Não foi possível adicionar o acréscimo ao banco de dados.", None
            
        return True, f"Acréscimo de {tipo} adicionado com sucesso!", acrescimo_id
        
    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao adicionar acréscimo: {str(e)}")
        traceback.print_exc()
        return False, f"Erro: {str(e)}", None

def fechar_proposta(db, proposta_id):
    """
    Fecha uma proposta, alterando seu status para "Fechada"
    
    Args:
        db: Conexão com o banco de dados
        proposta_id: ID da proposta
        
    Returns:
        tuple: (sucesso, mensagem)
            - sucesso: True se operação foi bem-sucedida
            - mensagem: Mensagem explicativa do resultado
    """
    print(f"DEBUG HELPER: Fechando proposta ID={proposta_id}")
    
    try:
        # Buscar a proposta atual
        proposta = None
        try:
            propostas = db.get_propostas()
            if not propostas.empty:
                proposta_found = propostas[propostas['id'] == int(proposta_id)]
                if not proposta_found.empty:
                    proposta = proposta_found.iloc[0]
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar proposta: {str(e)}")
            
        # Verificar se proposta existe
        if proposta is None:
            return False, f"Proposta ID={proposta_id} não encontrada."
            
        # Verificar status atual
        if proposta['status'] == 'Fechada':
            return True, "Proposta já está fechada."
            
        # Atualizar status
        resultado = db.update_proposta(
            proposta_id=proposta_id,
            status="Fechada",
            data_fim=datetime.now().date()
        )
        
        if not resultado:
            return False, "Não foi possível fechar a proposta. Tente novamente."
            
        return True, "Proposta fechada com sucesso!"
        
    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao fechar proposta: {str(e)}")
        traceback.print_exc()
        return False, f"Erro: {str(e)}"

def gerar_pdf_proposta(db, proposta_id, custom_filename=None):
    """
    Gera um PDF de fechamento para uma proposta
    
    Args:
        db: Conexão com o banco de dados
        proposta_id: ID da proposta
        custom_filename: Nome de arquivo personalizado (opcional)
        
    Returns:
        tuple: (sucesso, mensagem, filename)
            - sucesso: True se operação foi bem-sucedida
            - mensagem: Mensagem explicativa do resultado
            - filename: Caminho do arquivo gerado (ou None em caso de falha)
    """
    print(f"DEBUG HELPER: Gerando PDF para proposta ID={proposta_id}")
    
    try:
        # Garantir que o diretório existe
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
            
        # Buscar a proposta
        proposta = None
        try:
            propostas = db.get_propostas()
            if not propostas.empty:
                proposta_found = propostas[propostas['id'] == int(proposta_id)]
                if not proposta_found.empty:
                    proposta = proposta_found.iloc[0]
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar proposta: {str(e)}")
            
        # Verificar se proposta existe
        if proposta is None:
            return False, f"Proposta ID={proposta_id} não encontrada.", None
            
        # Buscar cliente
        try:
            # Obter clientes e procurar o cliente específico
            clientes = db.get_clientes()
            cliente = None
            cliente_id = int(proposta['cliente_id'])
            
            if not clientes.empty:
                cliente_found = clientes[clientes['id'] == cliente_id]
                if not cliente_found.empty:
                    cliente = cliente_found.iloc[0]
            
            if cliente is None:
                return False, f"Cliente ID={cliente_id} não encontrado.", None
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar cliente: {str(e)}")
            return False, f"Erro ao buscar cliente: {str(e)}", None
            
        # Converter cliente para dicionário se necessário
        cliente_dict = cliente
        if hasattr(cliente, 'to_dict'):
            cliente_dict = cliente.to_dict()
        elif not isinstance(cliente, dict):
            # Caso seja um objeto SQLAlchemy, extrair atributos
            cliente_dict = {'nome': cliente.nome if hasattr(cliente, 'nome') else "Cliente"}
            
        # Obter acréscimos
        acrescimos = db.get_acrescimos_proposta(proposta_id)
        if acrescimos is None:
            acrescimos = pd.DataFrame()  # DataFrame vazio se não houver acréscimos
            
        # Nome do arquivo
        if custom_filename:
            filename = custom_filename
        else:
            # Garantir que temos número da proposta e ID do cliente
            numero = proposta.get('numero', 'sem_numero')
            cliente_id = proposta.get('cliente_id', 'sem_cliente')
            filename = f"pdfs/proposta_{numero}_{cliente_id}_fechamento.pdf"
            
        # Gerar PDF
        pdf_path = gerar_pdf_fechamento(proposta, cliente_dict, acrescimos, filename)
        if not pdf_path or not os.path.exists(pdf_path):
            return False, "Não foi possível gerar o PDF.", None
            
        return True, "PDF gerado com sucesso!", pdf_path
        
    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        return False, f"Erro ao gerar PDF: {str(e)}", None
        
def marcar_proposta_como_paga(db, proposta_id):
    """
    Marca uma proposta como paga, atualizando seu status de pagamento
    
    Args:
        db: Conexão com o banco de dados
        proposta_id: ID da proposta
        
    Returns:
        tuple: (sucesso, mensagem)
            - sucesso: True se operação foi bem-sucedida
            - mensagem: Mensagem explicativa do resultado
    """
    print(f"DEBUG HELPER: Marcando proposta ID={proposta_id} como paga")
    
    try:
        # Implementar lógica para marcar proposta como paga
        resultado = db.atualizar_pagamento_base_proposta(
            proposta_id=proposta_id,
            status_pagamento_base="Recebido"
        )
        
        if not resultado:
            return False, "Não foi possível marcar a proposta como paga."
            
        return True, "Proposta marcada como paga com sucesso!"
        
    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao marcar proposta como paga: {str(e)}")
        traceback.print_exc()
        return False, f"Erro: {str(e)}"

# Versões amigáveis para uso em Streamlit

def st_adicionar_acrescimo(proposta_id, tipo, fornecedor, descricao, valor):
    """Versão para Streamlit da função adicionar_acrescimo"""
    try:
        sucesso, mensagem, acrescimo_id = adicionar_acrescimo(
            st.session_state.db, 
            proposta_id, 
            tipo, 
            fornecedor, 
            descricao, 
            valor
        )
        
        if sucesso:
            st.success(mensagem)
            # Rerun para atualizar a interface
            st.rerun()
        else:
            st.error(mensagem)
            
        return sucesso, acrescimo_id
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False, None

def st_fechar_proposta(proposta_id):
    """Versão para Streamlit da função fechar_proposta"""
    try:
        sucesso, mensagem = fechar_proposta(st.session_state.db, proposta_id)
        
        if sucesso:
            st.success(mensagem)
            # Rerun para atualizar a interface
            st.rerun()
        else:
            st.error(mensagem)
            
        return sucesso
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False

def st_gerar_pdf_proposta(proposta_id, custom_filename=None):
    """Versão para Streamlit da função gerar_pdf_proposta"""
    try:
        sucesso, mensagem, filename = gerar_pdf_proposta(
            st.session_state.db, 
            proposta_id, 
            custom_filename
        )
        
        if sucesso:
            st.success(mensagem)
            
            # Botão para download do arquivo
            with open(filename, "rb") as pdf:
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf.read(),
                    file_name=os.path.basename(filename),
                    mime="application/pdf"
                )
            
            return True, filename
        else:
            st.error(mensagem)
            return False, None
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False, None

def st_marcar_proposta_como_paga(proposta_id):
    """Versão para Streamlit da função marcar_proposta_como_paga"""
    try:
        sucesso, mensagem = marcar_proposta_como_paga(st.session_state.db, proposta_id)
        
        if sucesso:
            st.success(mensagem)
            # Rerun para atualizar a interface
            st.rerun()
        else:
            st.error(mensagem)
            
        return sucesso
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False