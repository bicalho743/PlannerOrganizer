import pandas as pd
import streamlit as st
from datetime import datetime
import io
import logging
import traceback

logger = logging.getLogger(__name__)

# Mapeamento de meses em português para validação
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

def try_read_csv(arquivo, encodings=['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'cp850', 'cp437', 'cp860', 'cp863', 'cp865', 'windows-1252', 'utf-16', 'utf-16-le', 'utf-16-be']):
    """Try reading CSV with different encodings and handling binary streams"""
    for encoding in encodings:
        try:
            # Reset file pointer to beginning
            arquivo.seek(0)
            # Create a bytes buffer to store the content
            bytes_buffer = io.BytesIO(arquivo.read())
            
            try:
                # Try to read directly with pandas and specified encoding
                # This works better for some files than manually decoding first
                arquivo.seek(0)
                df = pd.read_csv(arquivo, sep=';', encoding=encoding, on_bad_lines='warn')
                logger.info(f"Successful read with direct pandas using {encoding}")
                return df
            except Exception as pe:
                logger.warning(f"Direct pandas read failed with {encoding}: {str(pe)}")
                
                try:
                    # Try to decode with current encoding
                    text_content = bytes_buffer.getvalue().decode(encoding, errors='replace')
                    # Create a string buffer and read as CSV
                    string_buffer = io.StringIO(text_content)
                    df = pd.read_csv(string_buffer, sep=';', on_bad_lines='warn')
                    logger.info(f"Successful read with manual decode using {encoding}")
                    return df
                except Exception as e:
                    logger.warning(f"Manual decode failed with {encoding}: {str(e)}")
                    continue
                
        except UnicodeDecodeError as e:
            logger.warning(f"Failed to decode with {encoding}: {str(e)}")
            continue
        except pd.errors.EmptyDataError:
            logger.warning(f"Empty data with encoding {encoding}")
            continue
        except Exception as e:
            logger.error(f"Error reading CSV with encoding {encoding}: {str(e)}\n{traceback.format_exc()}")
            continue

    # Try a last resort approach - read byte by byte and replace problematic characters
    try:
        arquivo.seek(0)
        content = arquivo.read()
        # Replace the problematic byte 0xed with a similar character
        content_fixed = content.replace(b'\xed', b'i')
        
        for encoding in ['utf-8', 'latin1', 'windows-1252']:
            try:
                text = content_fixed.decode(encoding, errors='replace')
                df = pd.read_csv(io.StringIO(text), sep=';', on_bad_lines='warn')
                logger.info(f"Successful read with byte replacement using {encoding}")
                return df
            except Exception as e:
                logger.warning(f"Byte replacement approach failed with {encoding}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Byte replacement approach failed: {str(e)}")
    
    # If we get here, none of the encodings worked
    error_msg = "Não foi possível ler o arquivo com nenhuma das codificações suportadas"
    logger.error(error_msg)
    raise ValueError(error_msg)

def importar_cadastros(arquivo, tipo_cadastro, db):
    """Importa cadastros de um arquivo CSV ou Excel"""
    try:
        st.write("### Log de Importação")
        st.info(f"Iniciando importação de {tipo_cadastro}")

        if not db:
            st.error("Erro: Conexão com banco de dados não inicializada")
            return False, "Erro: Conexão com banco de dados não inicializada"

        # Detecta o tipo de arquivo e lê
        st.info("Lendo arquivo...")
        try:
            arquivo_nome = getattr(arquivo, 'name', '')
            st.info(f"Tipo de arquivo: {arquivo_nome}")

            if arquivo_nome.endswith('.csv'):
                df = try_read_csv(arquivo)
            else:
                # For Excel files, use a different approach
                arquivo.seek(0)
                bytes_buffer = io.BytesIO(arquivo.read())
                df = pd.read_excel(bytes_buffer)

            if df is None or df.empty:
                return False, "Erro ao ler arquivo: arquivo vazio ou formato não suportado"

            # Debug info
            st.success(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
            st.info(f"Colunas encontradas: {', '.join(df.columns)}")
            st.info(f"Primeiras linhas:\n{df.head().to_string()}")

        except Exception as e:
            error_msg = f"Erro ao ler arquivo: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            st.error(error_msg)
            return False, f"Erro ao ler arquivo: {str(e)}"

        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})
        df = df.fillna('')  # Replace NaN with empty string to avoid encoding issues

        sucessos = 0
        erros = []

        total_rows = len(df)
        progress_bar = st.progress(0)

        for idx, row in df.iterrows():
            try:
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)

                if tipo_cadastro == "Cliente":
                    # Process client data with better error handling
                    try:
                        nome = str(row['nome']).strip() if row.get('nome') else None
                        if not nome:
                            erros.append(f"Nome vazio na linha {idx + 2}")
                            continue

                        cliente_data = {
                            'nome': nome,
                            'telefone': str(row.get('telefone', '')).strip(),
                            'cpf': str(row.get('cpf', '')).strip(),
                            'email': str(row.get('email', '')).strip(),
                            'estado': str(row.get('estado', '')).strip(),
                            'cidade': str(row.get('cidade', '')).strip(),
                            'bairro': str(row.get('bairro', '')).strip(),
                            'endereco': str(row.get('endereco', '')).strip(),
                            'data_aniversario': str(row.get('data_aniversario', '')).strip(),
                            'origem_cliente': str(row.get('origem_cliente', 'Importação')).strip(),
                            'observacoes': str(row.get('observacoes', '')).strip()
                        }

                        # Clean up empty strings
                        cliente_data = {k: v for k, v in cliente_data.items() if v}

                        db.add_cliente(**cliente_data)
                        sucessos += 1
                    except Exception as e:
                        erro_msg = f"Erro ao processar cliente na linha {idx + 2}: {str(e)}"
                        erros.append(erro_msg)
                        logger.error(erro_msg)
                        continue

                elif tipo_cadastro == "Fornecedor":
                    try:
                        # Verificar campo obrigatório
                        descricao = str(row['descricao']).strip() if pd.notna(row.get('descricao')) else None
                        if not descricao:
                            erros.append(f"Descrição (Razão Social) vazia na linha {idx + 2}")
                            continue
                        
                        # Garantir que tipo_conta tenha um valor padrão
                        tipo_conta = str(row.get('tipo_conta', 'PF')).strip() if pd.notna(row.get('tipo_conta')) else 'PF'
                        
                        # Preparar dados do fornecedor
                        fornecedor_data = {
                            'descricao': descricao,
                            'contato': str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                            'categoria': str(row.get('categoria', '')).strip() if pd.notna(row.get('categoria')) else None,
                            'estado': str(row.get('estado', '')).strip() if pd.notna(row.get('estado')) else None,
                            'cidade': str(row.get('cidade', '')).strip() if pd.notna(row.get('cidade')) else None,
                            'bairro': str(row.get('bairro', '')).strip() if pd.notna(row.get('bairro')) else None,
                            'endereco': str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                            'pix': str(row.get('pix', '')).strip() if pd.notna(row.get('pix')) else None,
                            'recorrente': bool(row.get('recorrente', False)) if pd.notna(row.get('recorrente')) else False,
                            'observacoes': str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao')) else None,
                            'tipo_conta': tipo_conta
                        }
                        
                        # Adicionar fornecedor
                        db.add_fornecedor(**fornecedor_data)
                        sucessos += 1
                        
                    except Exception as e:
                        erro_msg = f"Erro ao processar fornecedor na linha {idx + 2}: {str(e)}"
                        st.error(erro_msg)
                        erros.append(erro_msg)
                        logger.error(erro_msg)
                        continue

                elif tipo_cadastro == "Parceiro":
                    try:
                        # Verificar campo obrigatório
                        nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                        if not nome:
                            erros.append(f"Nome vazio na linha {idx + 2}")
                            continue
                        
                        # Preparar dados do parceiro
                        parceiro_data = {
                            'nome': nome,
                            'telefone': str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                            'area_atuacao': str(row.get('area_atuacao', '')).strip() if pd.notna(row.get('area_atuacao')) else None,
                            'tipo_parceria': str(row.get('tipo_parceria', '')).strip() if pd.notna(row.get('tipo_parceria')) else None,
                            'observacoes': str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao')) else None
                        }
                        
                        # Adicionar parceiro
                        db.add_parceiro(**parceiro_data)
                        sucessos += 1
                        
                    except Exception as e:
                        erro_msg = f"Erro ao processar parceiro na linha {idx + 2}: {str(e)}"
                        st.error(erro_msg)
                        erros.append(erro_msg)
                        logger.error(erro_msg)
                        continue

                elif tipo_cadastro == "Assistente":
                    try:
                        # Verificar campo obrigatório
                        nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                        if not nome:
                            erros.append(f"Nome vazio na linha {idx + 2}")
                            continue
                        
                        # Preparar dados do assistente
                        assistente_data = {
                            'nome': nome,
                            'telefone': str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                            'endereco': str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                            'pix': str(row.get('pix', '')).strip() if pd.notna(row.get('pix')) else None,
                            'observacoes': str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao')) else None
                        }
                        
                        # Adicionar assistente
                        db.add_assistente(**assistente_data)
                        sucessos += 1
                        
                    except Exception as e:
                        erro_msg = f"Erro ao processar assistente na linha {idx + 2}: {str(e)}"
                        st.error(erro_msg)
                        erros.append(erro_msg)
                        logger.error(erro_msg)
                        continue
                    
                elif tipo_cadastro == "Produto":
                    nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                    if not nome:
                        erros.append(f"Nome vazio na linha {idx + 2}")
                        continue
                    
                    try:
                        # Converter valores
                        preco_custo = float(row.get('preco_custo', 0)) if pd.notna(row.get('preco_custo')) else 0
                        preco_venda = float(row.get('preco_venda', 0)) if pd.notna(row.get('preco_venda')) else 0
                        estoque = int(row.get('estoque', 0)) if pd.notna(row.get('estoque')) else 0
                        
                        # Validar valores
                        if preco_venda <= 0:
                            erros.append(f"Preço de venda inválido na linha {idx + 2}")
                            continue
                            
                        # Adicionar produto
                        db.add_produto(
                            nome=nome,
                            descricao=str(row.get('descricao', '')).strip() if pd.notna(row.get('descricao')) else None,
                            preco_custo=preco_custo,
                            preco_venda=preco_venda,
                            categoria=str(row.get('categoria', '')).strip() if pd.notna(row.get('categoria')) else None,
                            estoque=estoque
                        )
                        sucessos += 1
                    except Exception as e:
                        erro_msg = f"Erro ao processar produto na linha {idx + 2}: {str(e)}"
                        erros.append(erro_msg)
                        logger.error(erro_msg)
                        continue
                        
                elif tipo_cadastro == "Proposta":
                    try:
                        # Verificar cliente_id ou cliente_nome
                        cliente_id = None
                        
                        # Se temos um cliente_id direto
                        if pd.notna(row.get('cliente_id')):
                            try:
                                cliente_id = int(row['cliente_id'])
                            except ValueError:
                                erros.append(f"ID de cliente inválido na linha {idx + 2}")
                                continue
                        # Se temos cliente_nome, precisamos buscar o ID
                        elif pd.notna(row.get('cliente_nome')):
                            # Carregar clientes para buscar o ID pelo nome
                            cliente_nome = str(row['cliente_nome']).strip()
                            clientes = db.get_clientes()
                            
                            if not clientes.empty:
                                # Exibe debug no console
                                logger.info(f"Buscando cliente pelo nome: '{cliente_nome}'")
                                logger.info(f"Clientes disponíveis: {clientes['nome'].tolist()}")
                                
                                # Busca com correspondência exata
                                cliente_encontrado = clientes[clientes['nome'] == cliente_nome]
                                
                                if not cliente_encontrado.empty:
                                    cliente_id = int(cliente_encontrado['id'].iloc[0])
                                    logger.info(f"Cliente encontrado com ID: {cliente_id}")
                                else:
                                    # Busca com correspondência parcial (case insensitive)
                                    cliente_nome_lower = cliente_nome.lower()
                                    for _, c in clientes.iterrows():
                                        if cliente_nome_lower in c['nome'].lower():
                                            cliente_id = int(c['id'])
                                            logger.info(f"Cliente encontrado com correspondência parcial: {c['nome']}, ID: {cliente_id}")
                                            break
                                    
                                    if cliente_id is None:
                                        erros.append(f"Cliente '{cliente_nome}' não encontrado, linha {idx + 2}")
                                        continue
                            else:
                                erros.append(f"Não há clientes cadastrados no sistema para associar à proposta na linha {idx + 2}")
                                continue
                        else:
                            erros.append(f"Cliente não especificado na linha {idx + 2}")
                            continue
                            
                        # Validar descrição
                        descricao = str(row.get('descricao', '')).strip() if pd.notna(row.get('descricao')) else None
                        if not descricao:
                            erros.append(f"Descrição vazia na linha {idx + 2}")
                            continue
                            
                        # Validar valor
                        valor = None
                        try:
                            valor = float(row.get('valor', 0)) if pd.notna(row.get('valor')) else 0
                            if valor <= 0:
                                erros.append(f"Valor inválido na linha {idx + 2}")
                                continue
                        except ValueError:
                            erros.append(f"Valor não numérico na linha {idx + 2}")
                            continue
                            
                        # Preparar status
                        status = str(row.get('status', 'Aberta')).strip() if pd.notna(row.get('status')) else 'Aberta'
                        if status not in ['Aberta', 'Recusada', 'Fechada']:
                            st.warning(f"Status inválido na linha {idx + 2}. Usando 'Aberta'.")
                            status = 'Aberta'
                            
                        # Preparar tipo_proposta
                        tipo_proposta = str(row.get('tipo_proposta', '')).strip() if pd.notna(row.get('tipo_proposta')) else None
                        
                        # Processar datas
                        data_inicio = None
                        data_fim = None
                        prazo_entrega = None
                        
                        if pd.notna(row.get('data_inicio')):
                            try:
                                if isinstance(row['data_inicio'], str):
                                    data_inicio = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                                else:
                                    data_inicio = pd.to_datetime(row['data_inicio']).date()
                            except Exception as e:
                                st.warning(f"Data de início inválida na linha {idx + 2}: {str(e)}")
                                
                        if pd.notna(row.get('data_fim')):
                            try:
                                if isinstance(row['data_fim'], str):
                                    data_fim = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                                else:
                                    data_fim = pd.to_datetime(row['data_fim']).date()
                            except Exception as e:
                                st.warning(f"Data de fim inválida na linha {idx + 2}: {str(e)}")
                                
                        if pd.notna(row.get('prazo_entrega')):
                            try:
                                if isinstance(row['prazo_entrega'], str):
                                    prazo_entrega = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                                else:
                                    prazo_entrega = pd.to_datetime(row['prazo_entrega']).date()
                            except Exception as e:
                                st.warning(f"Prazo de entrega inválido na linha {idx + 2}: {str(e)}")
                        
                        # Adicionar proposta
                        db.add_proposta(
                            cliente_id=cliente_id,
                            descricao=descricao,
                            valor=valor,
                            status=status,
                            tipo_proposta=tipo_proposta,
                            data_inicio=data_inicio,
                            data_fim=data_fim,
                            prazo_entrega=prazo_entrega
                        )
                        sucessos += 1
                    except Exception as e:
                        erro_msg = f"Erro ao processar proposta na linha {idx + 2}: {str(e)}"
                        erros.append(erro_msg)
                        logger.error(erro_msg)
                        continue

            except Exception as e:
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}"
                erros.append(erro_msg)
                logger.error(f"{erro_msg}\n{traceback.format_exc()}")
                continue

        progress_bar.empty()

        mensagem = f"Importação concluída. {sucessos} registros importados com sucesso."
        if erros:
            mensagem += f"\nErros encontrados: {len(erros)}"
            for erro in erros[:5]:  # Show only first 5 errors
                mensagem += f"\n- {erro}"
            logger.error(f"Erros na importação:\n{chr(10).join(erros)}")

        return sucessos > 0, mensagem

    except Exception as e:
        erro_msg = f"Erro ao processar arquivo: {str(e)}\n{traceback.format_exc()}"
        logger.error(erro_msg)
        return False, f"Erro ao processar arquivo: {str(e)}"

def validar_data(data_str):
    """Valida e mantém o formato DD/MMM para datas de aniversário"""
    if pd.isna(data_str):
        return None
    try:
        if isinstance(data_str, str):
            # Formato DD/MMM
            try:
                dia, mes = data_str.strip().lower().split('/')
                # Validar dia (1-31)
                dia_num = int(dia)
                if dia_num < 1 or dia_num > 31:
                    st.warning(f"Dia inválido em: {data_str}")
                    return None
                # Validar mês abreviado
                if mes not in MESES:
                    st.warning(f"Mês inválido em: {data_str}")
                    return None
                # Retornar a data original no formato DD/MMM
                return f"{dia.zfill(2)}/{mes}"
            except (ValueError, TypeError):
                # Se não conseguir separar em dia/mês, retorna None
                st.warning(f"Formato de data inválido: {data_str}")
                return None
        return None
    except Exception as e:
        st.warning(f"Erro ao processar data: {data_str}. Erro: {str(e)}")
        return None

def testar_conexao_db(db):
    """Testa a conexão com o banco de dados tentando inserir um cliente de teste"""
    try:
        st.info("Testando conexão com o banco de dados...")

        # Dados de teste
        cliente_teste = {
            'nome': 'Cliente Teste',
            'telefone': '(00) 00000-0000',
            'cpf': '000.000.000-00',
            'estado': 'Teste',
            'cidade': 'Teste',
            'bairro': 'Teste',
            'endereco': 'Rua de Teste',
            'data_aniversario': '01/jan',
            'origem_cliente': 'Teste',
            'observacoes': 'Cliente de teste - será removido'
        }

        # Tentar inserir
        db.add_cliente(**cliente_teste)
        st.success("Teste de conexão com o banco de dados bem sucedido!")
        return True
    except Exception as e:
        traceback_str = traceback.format_exc()
        erro = f"Erro ao testar conexão com o banco de dados:\n{str(e)}\nTraceback:\n{traceback_str}"
        st.error(erro)
        return False

def validar_dataframe(df, tipo_cadastro):
    """Valida o DataFrame antes da importação"""
    st.info("Validando estrutura dos dados...")

    # Definir colunas obrigatórias baseadas no tipo de cadastro
    if tipo_cadastro == "Produto":
        colunas_base = ['nome', 'preco_venda']
    elif tipo_cadastro == "Proposta":
        # Para propostas, precisamos cliente (id ou nome) e valor
        if 'cliente_id' in df.columns or 'cliente_nome' in df.columns:
            colunas_base = ['descricao', 'valor']
        else:
            colunas_base = ['cliente_id', 'descricao', 'valor']
    else:
        colunas_base = ['nome', 'telefone', 'email']
    
    colunas_faltantes = [col for col in colunas_base if col not in df.columns]

    if colunas_faltantes:
        erro = f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
        st.error(erro)
        return False, erro

    # Validar se há pelo menos uma linha de dados
    if len(df) == 0:
        erro = "O arquivo não contém dados para importação"
        st.error(erro)
        return False, erro

    # Validações específicas por tipo de cadastro
    if tipo_cadastro == "Produto":
        # Verificar se os preços são válidos (quando presentes)
        for idx, row in df.iterrows():
            if 'preco_venda' in row and pd.notna(row['preco_venda']):
                try:
                    preco_venda = float(row['preco_venda'])
                    if preco_venda <= 0:
                        erro = f"Preço de venda deve ser maior que zero na linha {idx+2}"
                        st.error(erro)
                        return False, erro
                except ValueError:
                    erro = f"Preço de venda inválido na linha {idx+2}: {row['preco_venda']}"
                    st.error(erro)
                    return False, erro
    
    elif tipo_cadastro == "Proposta":
        # Verificar se os valores de proposta são válidos
        for idx, row in df.iterrows():
            if 'valor' in row and pd.notna(row['valor']):
                try:
                    valor = float(row['valor'])
                    if valor <= 0:
                        erro = f"Valor da proposta deve ser maior que zero na linha {idx+2}"
                        st.error(erro)
                        return False, erro
                except ValueError:
                    erro = f"Valor da proposta inválido na linha {idx+2}: {row['valor']}"
                    st.error(erro)
                    return False, erro
                    
            # Verificar se temos ou cliente_id ou cliente_nome
            if not ('cliente_id' in row and pd.notna(row['cliente_id'])) and not ('cliente_nome' in row and pd.notna(row['cliente_nome'])):
                erro = f"Cliente não especificado na linha {idx+2}. Forneça cliente_id ou cliente_nome."
                st.error(erro)
                return False, erro

    return True, "Validação OK"

def gerar_template_csv(tipo):
    """Gera um arquivo CSV template baseado no tipo de importação"""
    if tipo == "Cliente" or tipo == "Clientes":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'data_aniversario', 
            'origem_cliente', 'cpf', 'estado', 'cidade',
            'bairro', 'endereco', 'observacoes'
        ])
    elif tipo == "Fornecedor" or tipo == "Fornecedores":
        df = pd.DataFrame(columns=[
            'descricao',  # Razão Social
            'telefone',   
            'endereco',   
            'categoria',  
            'pix',       
            'observacao'  
        ])
    elif tipo == "Assistente" or tipo == "Assistentes":
        df = pd.DataFrame(columns=[
            'nome',      
            'telefone',  
            'endereco',  
            'pix',      
            'observacao' 
        ])
    elif tipo == "Parceiro" or tipo == "Parceiros":
        df = pd.DataFrame(columns=[
            'nome',          
            'telefone',      
            'area_atuacao',  
            'tipo_parceria', 
            'observacao'     
        ])
    elif tipo == "Produto" or tipo == "Produtos":
        df = pd.DataFrame(columns=[
            'nome',          # Nome do produto
            'descricao',     # Descrição
            'preco_custo',   # Preço de custo
            'preco_venda',   # Preço de venda
            'categoria',     # Categoria
            'estoque'        # Quantidade em estoque
        ])
    elif tipo == "Proposta" or tipo == "Propostas":
        df = pd.DataFrame(columns=[
            'cliente_nome',     # Nome do cliente (obrigatório)
            'descricao',       # Descrição da proposta (obrigatório)
            'valor',           # Valor da proposta (obrigatório)
            'status',          # Status: Aberta, Fechada, Recusada
            'tipo_proposta',   # Tipo de proposta
            'data_inicio',     # Data de início (DD/MM/AAAA)
            'data_fim',        # Data de fim (DD/MM/AAAA)
            'prazo_entrega'    # Prazo de entrega (DD/MM/AAAA)
        ])
    else:
        # Retornar um template genérico em vez de None para evitar erros
        df = pd.DataFrame(columns=['nome', 'descricao'])

    return df.to_csv(index=False, sep=';').encode('utf-8')

def gerar_template_excel(tipo):
    """Gera um arquivo Excel template baseado no tipo de importação"""
    if tipo == "Cliente" or tipo == "Clientes":
        df = pd.DataFrame(columns=[
            'nome',  # Obrigatório
            'telefone',
            'cpf',
            'estado',
            'cidade',
            'bairro',
            'endereco',
            'data_aniversario',  # Formato: DD/MMM (ex: 25/Jan)
            'origem_cliente',
            'observacoes'
        ])
        # Adicionar uma linha de exemplo
        df.loc[0] = [
            'Nome do Cliente',  # nome
            '(11) 99999-9999',  # telefone
            '123.456.789-00',   # cpf
            'SP',               # estado
            'São Paulo',        # cidade
            'Centro',           # bairro
            'Rua Principal, 123', # endereco
            '25/Jan',           # data_aniversario
            'Site',             # origem_cliente
            'Observações aqui'  # observacoes
        ]
    elif tipo == "Fornecedor" or tipo == "Fornecedores":
        df = pd.DataFrame(columns=[
            'descricao',  # Razão Social
            'telefone',   
            'endereco',   
            'categoria',  
            'pix',       
            'observacao'  
        ])
    elif tipo == "Assistente" or tipo == "Assistentes":
        df = pd.DataFrame(columns=[
            'nome',      
            'telefone',  
            'endereco',  
            'pix',      
            'observacao' 
        ])
    elif tipo == "Parceiro" or tipo == "Parceiros":
        df = pd.DataFrame(columns=[
            'nome',          
            'telefone',      
            'area_atuacao',  
            'tipo_parceria', 
            'observacao'     
        ])
    elif tipo == "Proposta" or tipo == "Propostas":
        df = pd.DataFrame(columns=[
            'cliente_nome',  # Nome do cliente para buscar o ID
            'descricao',    # Descrição do serviço
            'valor',        # Valor da proposta
            'tipo_proposta',# Tipo (Organização, Consultoria, etc)
            'status',       # Status (Aberta, Fechada, Recusada)
            'data_inicio',  # Data de início (DD/MM/YYYY)
            'data_fim',     # Data de fim (DD/MM/YYYY)
            'prazo_entrega' # Prazo de entrega (DD/MM/YYYY)
        ])
    elif tipo == "Produto" or tipo == "Produtos":
        df = pd.DataFrame(columns=[
            'nome',          # Nome do produto
            'descricao',     # Descrição
            'preco_custo',   # Preço de custo
            'preco_venda',   # Preço de venda
            'categoria',     # Categoria
            'estoque'        # Quantidade em estoque
        ])
        # Adicionar linha de exemplo
        df.loc[0] = [
            'Produto de Exemplo',     # nome
            'Descrição detalhada',    # descricao
            25.50,                    # preco_custo
            45.99,                    # preco_venda
            'Organização',            # categoria
            10                        # estoque
        ]
    elif tipo == "Proposta" or tipo == "Propostas":
        df = pd.DataFrame(columns=[
            'cliente_nome',     # Nome do cliente (obrigatório)
            'descricao',        # Descrição da proposta (obrigatório)
            'valor',            # Valor da proposta (obrigatório)
            'status',           # Status: Aberta, Fechada, Recusada
            'tipo_proposta',    # Tipo de proposta
            'data_inicio',      # Data de início (DD/MM/AAAA)
            'data_fim',         # Data de fim (DD/MM/AAAA)
            'prazo_entrega'     # Prazo de entrega (DD/MM/AAAA)
        ])
        # Adicionar uma linha de exemplo
        df.loc[0] = [
            'Nome do Cliente',     # cliente_nome
            'Proposta de Organização Residencial', # descricao
            1500.00,               # valor
            'Aberta',              # status
            'Organização',         # tipo_proposta
            '01/05/2025',          # data_inicio
            '15/05/2025',          # data_fim
            '20/05/2025'           # prazo_entrega
        ]
    else:
        # Retornar um template genérico em vez de None para evitar erros
        df = pd.DataFrame(columns=['nome', 'descricao'])
        df.loc[0] = ['Nome', 'Descrição']

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()


def importar_propostas(arquivo, db):
    """Importa propostas de um arquivo Excel"""
    try:
        st.write("### Log de Importação de Propostas")
        st.info("Iniciando importação de propostas...")

        if not db:
            st.error("Erro: Conexão com banco de dados não inicializada")
            return False, "Erro: Conexão com banco de dados não inicializada"

        # Ler arquivo Excel
        try:
            arquivo.seek(0) # Reset file pointer
            bytes_buffer = io.BytesIO(arquivo.read())
            df = pd.read_excel(bytes_buffer)
            st.success(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            return False, f"Erro ao ler arquivo: {str(e)}"

        # Validar colunas obrigatórias
        colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor', 'tipo_proposta', 'status']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        if colunas_faltantes:
            erro = f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
            st.error(erro)
            return False, erro

        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})

        # Carregar clientes para mapear nomes para IDs
        clientes = db.get_clientes()
        if clientes.empty:
            return False, "Não há clientes cadastrados no sistema"

        # Criar dicionário de nome para ID
        clientes_dict = dict(zip(clientes['nome'].str.strip().str.lower(), clientes['id']))

        sucessos = 0
        erros = []
        total_rows = len(df)
        progress_bar = st.progress(0)

        for idx, row in df.iterrows():
            try:
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)

                # Processar dados da linha
                cliente_nome = str(row['cliente_nome']).strip().lower()
                if not cliente_nome:
                    erro_msg = f"Nome do cliente vazio na linha {idx + 2}"
                    erros.append(erro_msg)
                    continue

                # Buscar ID do cliente
                if cliente_nome not in clientes_dict:
                    erro_msg = f"Cliente não encontrado: {row['cliente_nome']}"
                    erros.append(erro_msg)
                    continue

                cliente_id = clientes_dict[cliente_nome]

                # Processar valor
                try:
                    valor = float(row['valor'])
                except (ValueError, TypeError):
                    erro_msg = f"Valor inválido na linha {idx + 2}"
                    erros.append(erro_msg)
                    continue

                # Processar datas
                data_inicio = None
                data_fim = None
                prazo_entrega = None

                if pd.notna(row.get('data_inicio')):
                    try:
                        data_inicio = pd.to_datetime(row['data_inicio']).date()
                    except:
                        st.warning(f"Data de início inválida na linha {idx + 2}")

                if pd.notna(row.get('data_fim')):
                    try:
                        data_fim = pd.to_datetime(row['data_fim']).date()
                    except:
                        st.warning(f"Data de fim inválida na linha {idx + 2}")

                if pd.notna(row.get('prazo_entrega')):
                    try:
                        prazo_entrega = pd.to_datetime(row['prazo_entrega']).date()
                    except:
                        st.warning(f"Prazo de entrega inválido na linha {idx + 2}")

                # Adicionar proposta
                try:
                    db.add_proposta(
                        cliente_id=cliente_id,
                        descricao=str(row['descricao']).strip(),
                        valor=valor,
                        status=str(row['status']).strip(),
                        tipo_proposta=str(row['tipo_proposta']).strip() if pd.notna(row.get('tipo_proposta')) else None,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        prazo_entrega=prazo_entrega
                    )
                    sucessos += 1
                except Exception as e:
                    erro_msg = f"Erro ao adicionar proposta na linha {idx + 2}: {str(e)}"
                    erros.append(erro_msg)
                    st.error(erro_msg)
                    continue

            except Exception as e:
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}"
                st.error(erro_msg)
                erros.append(erro_msg)
                continue

        progress_bar.empty()

        mensagem = f"Importação concluída. {sucessos} propostas importadas com sucesso."
        if erros:
            mensagem += f"\nErros encontrados: {len(erros)}"
            for erro in erros[:5]:  # Mostrar apenas os 5 primeiros erros
                mensagem += f"\n- {erro}"

        return sucessos > 0, mensagem

    except Exception as e:
        erro_msg = f"Erro ao processar arquivo: {str(e)}"
        st.error(erro_msg)
        return False, erro_msg