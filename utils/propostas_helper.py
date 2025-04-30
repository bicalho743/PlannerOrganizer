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

# Importar a versão melhorada do gerador de PDF
try:
    # Forçar a importação do módulo melhorado
    import utils.pdf_generator_melhorado
    # Agora importar a função específica
    from utils.pdf_generator_melhorado import gerar_pdf_fechamento
    print("DEBUG: Usando o gerador de PDF melhorado!")
except ImportError as e:
    # Log detalhado do erro para diagnóstico
    print(f"ERRO DETALHADO NA IMPORTAÇÃO: {str(e)}")
    traceback.print_exc()
    # Fallback para o gerador original em caso de erro
    from utils.pdf_generator import gerar_pdf_fechamento
    print("DEBUG: Usando o gerador de PDF original (fallback)!")

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
    print(f"DEBUG HELPER: Gerando PDF melhorado para proposta ID={proposta_id}")
    
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
            # Garantir que temos ID da proposta e nome do cliente
            proposta_id = proposta.get('id', 'sem_id')
            cliente_nome = cliente_dict.get('nome', 'sem_nome').replace(' ', '_').lower()
            
            # Adicionar data atual para evitar sobrescrever arquivos
            data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Criando nome de arquivo com o formato: Proposta_#ID_NomeCliente_DATA.pdf
            filename = f"pdfs/Proposta_{proposta_id}_{cliente_nome}_{data_atual}.pdf"
            
        # Buscar informações adicionais para o PDF melhorado
        # Buscar produtos da proposta se estiverem disponíveis
        produtos = []
        try:
            # Usar o método get_produtos_organizadores que já existe para buscar os produtos
            produtos_df = db.get_produtos_organizadores(proposta_id)
            if produtos_df is not None and not produtos_df.empty:
                produtos = produtos_df.to_dict('records')
                print(f"DEBUG PDF: Encontrados {len(produtos)} produtos para a proposta")
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao buscar produtos: {str(e)}")
            produtos = []
            
        # Obter dados do perfil do usuário para o PDF
        try:
            # Tentar importar o carregador de perfil
            from utils.perfil_loader import carregar_perfil_usuario
            perfil = carregar_perfil_usuario()
            print(f"DEBUG PDF: Perfil do usuário carregado: {perfil.get('nome', 'N/A')}")
        except Exception as e:
            print(f"DEBUG PDF ERROR: Erro ao carregar perfil do usuário: {str(e)}")
            perfil = {}
            
        # Adicionar dados do perfil à proposta para uso no PDF
        proposta_dict = proposta
        if hasattr(proposta, 'to_dict'):
            proposta_dict = proposta.to_dict()
        elif isinstance(proposta, pd.Series):
            proposta_dict = proposta.to_dict()
            # Garantir que campos críticos estejam presentes
            print(f"DEBUG PDF: Convertendo Series para dict com campos: {list(proposta_dict.keys())}")
        else:
            # Se não for possível converter, garantir que seja um dicionário
            proposta_dict = dict(proposta)
            print(f"DEBUG PDF: Usando proposta como dict diretamente: {list(proposta_dict.keys())}")
            
        # Garantir que todos os campos importantes estejam presentes
        campos_esperados = ['id', 'tipo_proposta', 'status', 'data_inicio', 'data_fim', 'prazo_entrega']
        for campo in campos_esperados:
            if campo not in proposta_dict:
                print(f"DEBUG PDF: ALERTA - Campo '{campo}' não encontrado no dicionário da proposta!")
            else:
                print(f"DEBUG PDF: Campo '{campo}' encontrado com valor: {proposta_dict[campo]}")
                
        # Adicionar valores adicionais
        proposta_dict['perfil'] = perfil
        proposta_dict['produtos'] = produtos
            
        # Gerar PDF com novo layout
        pdf_path = gerar_pdf_fechamento(proposta_dict, cliente_dict, acrescimos, filename)
        if not pdf_path or not os.path.exists(pdf_path):
            return False, "Não foi possível gerar o PDF.", None
            
        return True, "PDF gerado com sucesso com o novo layout profissional!", pdf_path
        
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
                # Usar o nome do arquivo original, garantindo que o nome fica correto no download
                nome_arquivo = os.path.basename(filename)
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf.read(),
                    file_name=nome_arquivo,
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