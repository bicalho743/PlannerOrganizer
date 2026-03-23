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

# Importar gerador de PDF unificado v2
try:
    from utils.pdf_generator_v2 import gerar_pdf_cliente as gerar_pdf_fechamento
    print("DEBUG: Usando o gerador de PDF v2!")
except ImportError as e:
    # Log detalhado do erro para diagnóstico
    print(f"ERRO DETALHADO NA IMPORTAÇÃO: {str(e)}")
    traceback.print_exc()
    # Fallback seguro em caso de erro
    gerar_pdf_fechamento = None
    print("DEBUG: Gerador de PDF indisponível (fallback)!")

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
        try:
            # Preparar dados para gerar_pdf_cliente que espera (dados, output_path)
            itens_raw = proposta_dict.get('produtos', [])
            itens_tuples = []
            total_calculado = 0
            for it in itens_raw:
                nome_it = it.get('nome', it.get('produto_nome', it.get('descricao', ''))).title()
                qtd = float(it.get('quantidade', 1))
                val = float(it.get('valor_unit', it.get('valor', it.get('preco_unitario', 0))))
                subtotal = qtd * val
                total_calculado += subtotal
                itens_tuples.append((f"{nome_it} ({int(qtd)}x)", subtotal, False))
            valor_proposta = float(proposta_dict.get('valor', proposta_dict.get('valor_total', total_calculado)))
            dados_pdf = {
                'proposta_id': proposta_dict.get('id', ''),
                'cliente': cliente_dict.get('nome', ''),
                'telefone': cliente_dict.get('telefone', ''),
                'tipo': proposta_dict.get('tipo_proposta', ''),
                'status': proposta_dict.get('status', ''),
                'descricao': proposta_dict.get('descricao', ''),
                'itens': itens_tuples,
                'total': valor_proposta
            }
            pdf_path = gerar_pdf_fechamento(dados_pdf, filename)
            if not pdf_path or not os.path.exists(pdf_path):
                return False, "Não foi possível gerar o PDF.", None
                
            return True, "PDF gerado com sucesso com o novo layout profissional!", pdf_path
        except TypeError as te:
            # Se gerar_pdf_fechamento retorna um número diferente de valores
            print(f"DEBUG: TypeError ao gerar PDF fechamento: {str(te)}")
            return False, "Erro na geração do PDF de fechamento.", None
        
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
            # Mostrar mensagem de sucesso primeiro
            st.success("Proposta do cliente gerada com sucesso!")
            
            # Botão de download depois (igual ao de vendas)
            with open(filename, "rb") as file:
                pdf_bytes = file.read()
            
            st.download_button(
                label="📥 Baixar Proposta cliente",
                data=pdf_bytes,
                file_name=os.path.basename(filename),
                mime="application/pdf",
                key=f"download_pdf_proposta_{proposta_id}"
            )
            
            return True, filename
        else:
            st.error(mensagem)
            return False, None
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False, None
        
def gerar_pdf_cliente_proposta(db, proposta_id, custom_filename=None):
    """
    Gera um PDF de relatório para cliente de uma proposta finalizada
    
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
    print(f"DEBUG HELPER: Gerando PDF Cliente para proposta ID={proposta_id}")
    
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
                    proposta = proposta_found.iloc[0].to_dict()
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
                    cliente = cliente_found.iloc[0].to_dict()
            
            if cliente is None:
                return False, f"Cliente ID={cliente_id} não encontrado.", None
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar cliente: {str(e)}")
            return False, f"Erro ao buscar cliente: {str(e)}", None
            
        # Obter acréscimos
        acrescimos = db.get_acrescimos_proposta(proposta_id)
        if acrescimos is None:
            acrescimos = pd.DataFrame()  # DataFrame vazio se não houver acréscimos
            
        # Nome do arquivo
        if custom_filename:
            filename = custom_filename
        else:
            # Garantir que temos ID da proposta e nome do cliente
            cliente_nome = cliente.get('nome', 'sem_nome').replace(' ', '_').lower()
            
            # Adicionar data atual para evitar sobrescrever arquivos
            data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Criando nome de arquivo com o formato: Cliente_Proposta_#ID_NomeCliente_DATA.pdf
            filename = f"pdfs/Cliente_Proposta_{proposta_id}_{cliente_nome}_{data_atual}.pdf"
            
        tipo_proposta = proposta.get('tipo_proposta', 'Organização')
        valor_base = float(proposta.get('valor', 0))

        itens_tuples = []
        itens_tuples.append((f"Personal Organizer - {tipo_proposta}", valor_base, False))

        total_adicionais = 0

        produtos = []
        try:
            produtos_df = db.get_produtos_organizadores(proposta_id)
            if produtos_df is not None and not produtos_df.empty:
                produtos = produtos_df.to_dict('records')
        except Exception:
            pass

        for it in produtos:
            nome_it = it.get('nome', it.get('produto_nome', '')).title()
            qtd = float(it.get('quantidade', 1))
            val = float(it.get('valor_unit', it.get('valor', it.get('preco_unitario', 0))))
            subtotal = qtd * val
            total_adicionais += subtotal
            itens_tuples.append((f"{nome_it} ({int(qtd)}x)", subtotal, False))

        if not acrescimos.empty:
            for _, ac in acrescimos.iterrows():
                tipo_ac = str(ac.get('tipo', '')).lower()
                if tipo_ac in ('fornecedor', 'assistente'):
                    continue
                desc = ac.get('descricao', ac.get('fornecedor', 'Acréscimo')).title()
                val_ac = float(ac.get('valor', 0))
                total_adicionais += val_ac
                itens_tuples.append((desc, val_ac, False))

        total_geral = valor_base + total_adicionais

        from utils.pdf_generator_v2 import gerar_pdf_cliente
        dados_pdf = {
            'proposta_id': proposta.get('id', ''),
            'cliente': cliente.get('nome', ''),
            'telefone': cliente.get('telefone', ''),
            'tipo': tipo_proposta,
            'status': proposta.get('status', ''),
            'descricao': proposta.get('descricao', ''),
            'itens': itens_tuples,
            'total': total_geral,
            'valor_base': valor_base,
            'valor_adicionais': total_adicionais,
        }
        gerar_pdf_cliente(dados_pdf, filename)
        return True, "Relatório do cliente gerado com sucesso", filename

    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao gerar PDF cliente: {str(e)}")
        traceback.print_exc()
        return False, f"Erro ao gerar PDF cliente: {str(e)}", None

def gerar_pdf_interno_proposta(db, proposta_id, custom_filename=None):
    """
    Gera um PDF de relatório interno para uma proposta finalizada
    
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
    print(f"DEBUG HELPER: Gerando PDF Interno para proposta ID={proposta_id}")
    
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
                    proposta = proposta_found.iloc[0].to_dict()
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
                    cliente = cliente_found.iloc[0].to_dict()
            
            if cliente is None:
                return False, f"Cliente ID={cliente_id} não encontrado.", None
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar cliente: {str(e)}")
            return False, f"Erro ao buscar cliente: {str(e)}", None
            
        # Obter acréscimos
        acrescimos = db.get_acrescimos_proposta(proposta_id)
        if acrescimos is None:
            acrescimos = pd.DataFrame()  # DataFrame vazio se não houver acréscimos
            
        # Nome do arquivo
        if custom_filename:
            filename = custom_filename
        else:
            # Garantir que temos ID da proposta e nome do cliente
            cliente_nome = cliente.get('nome', 'sem_nome').replace(' ', '_').lower()
            
            # Adicionar data atual para evitar sobrescrever arquivos
            data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Criando nome de arquivo com o formato: Interno_Proposta_#ID_NomeCliente_DATA.pdf
            filename = f"pdfs/Interno_Proposta_{proposta_id}_{cliente_nome}_{data_atual}.pdf"
            
        valor_base = float(proposta.get('valor', 0))

        produtos_org = []
        try:
            produtos_df = db.get_produtos_organizadores(proposta_id)
            if produtos_df is not None and not produtos_df.empty:
                produtos_org = produtos_df.to_dict('records')
        except Exception:
            pass

        catalogo = {}
        try:
            catalogo_df = db.get_produtos()
            if catalogo_df is not None and not catalogo_df.empty:
                for _, p in catalogo_df.iterrows():
                    nome_norm = str(p.get('nome', '')).strip().upper()
                    catalogo[nome_norm] = {
                        'preco_custo': float(p.get('preco_custo', 0) or 0),
                        'preco_venda': float(p.get('preco_venda', 0) or 0),
                    }
        except Exception:
            pass

        total_produtos_venda = 0
        lucro_produtos = 0
        for it in produtos_org:
            nome_prod = str(it.get('nome', it.get('produto_nome', ''))).strip()
            qtd = float(it.get('quantidade', 1))
            val_venda = float(it.get('valor_unit', it.get('valor', it.get('preco_unitario', 0))))
            total_produtos_venda += qtd * val_venda
            cat = catalogo.get(nome_prod.upper())
            if cat:
                lucro_produtos += (cat['preco_venda'] - cat['preco_custo']) * qtd
            else:
                lucro_produtos += 0

        fornecedores_cadastro = {}
        try:
            forn_df = db.get_fornecedores()
            if forn_df is not None and not forn_df.empty:
                for _, f in forn_df.iterrows():
                    nome_f = str(f.get('descricao', f.get('nome', ''))).strip().upper()
                    pct = float(f.get('percentual_comissao', 0) or 0)
                    fornecedores_cadastro[nome_f] = pct
        except Exception:
            pass

        total_fornecedores = 0
        total_assistentes = 0
        total_comissoes = 0
        total_outros = 0
        if not acrescimos.empty:
            for _, ac in acrescimos.iterrows():
                tipo_ac = str(ac.get('tipo', '')).upper()
                val_ac = float(ac.get('valor', 0))
                if tipo_ac == 'FORNECEDOR':
                    total_fornecedores += val_ac
                    nome_forn = str(ac.get('fornecedor', '')).strip().upper()
                    pct_com = fornecedores_cadastro.get(nome_forn, 0)
                    if pct_com > 0:
                        total_comissoes += val_ac * pct_com / 100
                elif tipo_ac == 'ASSISTENTE':
                    total_assistentes += val_ac
                else:
                    total_outros += val_ac

        total_custo_cliente = valor_base + total_produtos_venda + total_fornecedores + total_outros

        itens_custo = [
            ("Personal Organizer", valor_base, False),
            ("Produtos", total_produtos_venda, False),
            ("Fornecedores", total_fornecedores, False),
            ("Outros", total_outros, False),
        ]

        receita = valor_base + total_comissoes + lucro_produtos + total_outros - total_assistentes

        itens_receita = [
            ("Personal Organizer", valor_base, False),
            ("Comissões", total_comissoes, False),
            ("Lucro em Produtos", lucro_produtos, False),
            ("Outros", total_outros, False),
            ("Pagamento Assistentes", total_assistentes, True),
        ]

        periodo_str = ''
        data_inicio = proposta.get('data_inicio', '')
        data_fim = proposta.get('data_fim', proposta.get('data_conclusao', ''))
        if data_inicio and data_fim:
            try:
                if hasattr(data_inicio, 'strftime'):
                    di = data_inicio.strftime('%d/%m/%Y')
                else:
                    di = str(data_inicio)
                if hasattr(data_fim, 'strftime'):
                    df = data_fim.strftime('%d/%m/%Y')
                else:
                    df = str(data_fim)
                periodo_str = f"{di} – {df}"
            except Exception:
                periodo_str = str(data_inicio)
        elif data_inicio:
            periodo_str = str(data_inicio)

        from utils.pdf_generator_v2 import gerar_pdf_interno
        dados_pdf = {
            'proposta_id': proposta.get('id', ''),
            'cliente': cliente.get('nome', ''),
            'tipo': proposta.get('tipo_proposta', ''),
            'status': proposta.get('status', ''),
            'periodo': periodo_str,
            'itens_custo': itens_custo,
            'total_custo': total_custo_cliente,
            'itens_receita': itens_receita,
            'total_receita': receita
        }
        gerar_pdf_interno(dados_pdf, filename)
        return True, "Relatório interno gerado com sucesso", filename

    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao gerar PDF interno: {str(e)}")
        traceback.print_exc()
        return False, f"Erro ao gerar PDF interno: {str(e)}", None

def gerar_pdf_fornecedores_proposta(db, proposta_id, custom_filename=None):
    """
    Gera um PDF de relatório de fornecedores de uma proposta
    
    Args:
        db: Conexão com o banco de dados
        proposta_id: ID da proposta
        custom_filename: Nome de arquivo personalizado (opcional)
        
    Returns:
        tuple: (sucesso, mensagem, filename)
    """
    print(f"DEBUG HELPER: Gerando PDF Fornecedores para proposta ID={proposta_id}")
    
    try:
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
            
        proposta = None
        try:
            propostas = db.get_propostas()
            if not propostas.empty:
                proposta_found = propostas[propostas['id'] == int(proposta_id)]
                if not proposta_found.empty:
                    proposta = proposta_found.iloc[0].to_dict()
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar proposta: {str(e)}")
            
        if proposta is None:
            return False, f"Proposta ID={proposta_id} não encontrada.", None
            
        try:
            clientes = db.get_clientes()
            cliente = None
            cliente_id = int(proposta['cliente_id'])
            
            if not clientes.empty:
                cliente_found = clientes[clientes['id'] == cliente_id]
                if not cliente_found.empty:
                    cliente = cliente_found.iloc[0].to_dict()
            
            if cliente is None:
                return False, f"Cliente ID={cliente_id} não encontrado.", None
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar cliente: {str(e)}")
            return False, f"Erro ao buscar cliente: {str(e)}", None
            
        acrescimos = db.get_acrescimos_proposta(proposta_id)
        
        itens_fornecedores = []
        if acrescimos is not None and not acrescimos.empty:
            for _, acrescimo in acrescimos.iterrows():
                tipo = acrescimo.get('tipo', '').lower()
                if tipo == 'fornecedor':
                    fornecedor_nome = acrescimo.get('fornecedor', '')
                    descricao = acrescimo.get('descricao', '')
                    valor = acrescimo.get('valor', 0)
                    
                    if descricao:
                        desc_final = descricao
                    elif fornecedor_nome:
                        desc_final = f"Fornecimento de {fornecedor_nome}"
                    else:
                        desc_final = "Fornecedor"
                    
                    itens_fornecedores.append({
                        "descricao": desc_final,
                        "valor": valor
                    })
        
        if not itens_fornecedores:
            return False, "Nenhum fornecedor encontrado para esta proposta.", None
            
        if custom_filename:
            filename = custom_filename
        else:
            cliente_nome = cliente.get('nome', 'sem_nome').replace(' ', '_').lower()
            data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pdfs/Fornecedores_Proposta_{proposta_id}_{cliente_nome}_{data_atual}.pdf"
            
        itens_tuples = []
        total_forn = 0
        for it in itens_fornecedores:
            desc = it.get('descricao', 'Fornecedor').title()
            val = float(it.get('valor', 0))
            total_forn += val
            itens_tuples.append((desc, val, False))

        from utils.pdf_generator_v2 import gerar_pdf_fornecedores
        dados_pdf = {
            'proposta_id': proposta.get('id', ''),
            'cliente': cliente.get('nome', ''),
            'telefone': cliente.get('telefone', ''),
            'tipo': proposta.get('tipo_proposta', ''),
            'status': proposta.get('status', ''),
            'itens': itens_tuples,
            'total': total_forn
        }
        gerar_pdf_fornecedores(dados_pdf, filename)
        return True, "Relatório de fornecedores gerado com sucesso", filename

    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao gerar PDF fornecedores: {str(e)}")
        traceback.print_exc()
        return False, f"Erro ao gerar PDF fornecedores: {str(e)}", None

def st_gerar_pdf_fornecedores(proposta_id, custom_filename=None):
    """Versão para Streamlit da função gerar_pdf_fornecedores_proposta"""
    try:
        sucesso, mensagem, filename = gerar_pdf_fornecedores_proposta(
            st.session_state.db, 
            proposta_id, 
            custom_filename
        )
        
        if sucesso:
            st.success(mensagem)
            
            with open(filename, "rb") as file:
                pdf_bytes = file.read()
            
            st.download_button(
                label="📥 Baixar Relatório de Fornecedores",
                data=pdf_bytes,
                file_name=os.path.basename(filename),
                mime="application/pdf",
                key=f"download_pdf_fornecedores_{proposta_id}"
            )
            
            return True, filename
        else:
            st.error(mensagem)
            return False, None
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False, None

def st_gerar_pdf_cliente(proposta_id, custom_filename=None):
    """Versão para Streamlit da função gerar_pdf_cliente_proposta"""
    try:
        sucesso, mensagem, filename = gerar_pdf_cliente_proposta(
            st.session_state.db, 
            proposta_id, 
            custom_filename
        )
        
        if sucesso:
            # Mostrar mensagem de sucesso primeiro
            st.success(mensagem)
            
            # Botão de download depois (igual ao de vendas)
            with open(filename, "rb") as file:
                pdf_bytes = file.read()
            
            st.download_button(
                label="📥 Baixar Relatório do Cliente",
                data=pdf_bytes,
                file_name=os.path.basename(filename),
                mime="application/pdf",
                key=f"download_pdf_cliente_{proposta_id}"
            )
            
            return True, filename
        else:
            st.error(mensagem)
            return False, None
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False, None

def st_gerar_pdf_interno(proposta_id, custom_filename=None):
    """Versão para Streamlit da função gerar_pdf_interno_proposta"""
    try:
        sucesso, mensagem, filename = gerar_pdf_interno_proposta(
            st.session_state.db, 
            proposta_id, 
            custom_filename
        )
        
        if sucesso:
            # Mostrar mensagem de sucesso primeiro
            st.success(mensagem)
            
            # Botão de download depois (igual ao de vendas)
            with open(filename, "rb") as file:
                pdf_bytes = file.read()
            
            st.download_button(
                label="📥 Baixar Relatório interno",
                data=pdf_bytes,
                file_name=os.path.basename(filename),
                mime="application/pdf",
                key=f"download_pdf_interno_{proposta_id}"
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
def gerar_pdf_venda_proposta(db, proposta_id, custom_filename=None):
    """
    Gera um PDF de relatório de produtos/vendas de uma proposta
    Usa o mesmo layout do relatório de serviço
    
    Args:
        db: Conexão com o banco de dados
        proposta_id: ID da proposta
        custom_filename: Nome de arquivo personalizado (opcional)
        
    Returns:
        tuple: (sucesso, mensagem, filename)
    """
    print(f"DEBUG HELPER: Gerando PDF Vendas para proposta ID={proposta_id}")
    
    try:
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
            
        # Buscar a proposta
        proposta = None
        try:
            propostas = db.get_propostas()
            if not propostas.empty:
                proposta_found = propostas[propostas['id'] == int(proposta_id)]
                if not proposta_found.empty:
                    proposta = proposta_found.iloc[0].to_dict()
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar proposta: {str(e)}")
            
        if proposta is None:
            return False, f"Proposta ID={proposta_id} não encontrada.", None
            
        # Buscar cliente
        try:
            clientes = db.get_clientes()
            cliente = None
            cliente_id = int(proposta['cliente_id'])
            
            if not clientes.empty:
                cliente_found = clientes[clientes['id'] == cliente_id]
                if not cliente_found.empty:
                    cliente = cliente_found.iloc[0].to_dict()
            
            if cliente is None:
                return False, f"Cliente ID={cliente_id} não encontrado.", None
        except Exception as e:
            print(f"DEBUG HELPER ERROR: Erro ao buscar cliente: {str(e)}")
            return False, f"Erro ao buscar cliente: {str(e)}", None
            
        # Obter acréscimos (que incluem produtos e fornecedores)
        acrescimos = db.get_acrescimos_proposta(proposta_id)
        if acrescimos is None:
            acrescimos = pd.DataFrame()
            
        # Nome do arquivo
        if custom_filename:
            filename = custom_filename
        else:
            cliente_nome = cliente.get('nome', 'sem_nome').replace(' ', '_').lower()
            data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pdfs/Venda_Proposta_{proposta_id}_{cliente_nome}_{data_atual}.pdf"
            
        # Usar pdf_generator_v2 que tem layout Navy/Gold
        from utils.pdf_generator_v2 import gerar_pdf_venda
        
        # Preparar itens para a tabela
        itens_tabela = acrescimos if not acrescimos.empty else pd.DataFrame()
        
        venda_dados = {
            "id": proposta.get('numero', proposta_id),
            "status": proposta.get('status', 'Concluída'),
            "forma_pagamento": "N/A",
            "valor_total": proposta.get('valor', 0),
            "data_venda": datetime.now().strftime('%d/%m/%Y'),
            "observacoes": proposta.get('descricao', '')
        }
        try:
            pdf_path = gerar_pdf_venda(venda_dados, cliente, itens_tabela, filename)
            if not pdf_path or not os.path.exists(pdf_path):
                return False, "Não foi possível gerar o PDF de vendas.", None
        except Exception as e:
            return False, f"Erro ao gerar PDF de vendas: {str(e)}", None
        
        return True, "Relatório de vendas/produtos gerado com sucesso", filename
        
    except Exception as e:
        print(f"DEBUG HELPER CRITICAL: Erro ao gerar PDF vendas: {str(e)}")
        traceback.print_exc()
        return False, f"Erro ao gerar PDF vendas: {str(e)}", None
