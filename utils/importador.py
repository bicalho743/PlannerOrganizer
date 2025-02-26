import pandas as pd
import streamlit as st
from datetime import datetime
import io
import traceback

def validar_data(data_str):
    """Converte string de data para objeto datetime"""
    if pd.isna(data_str):
        return None
    try:
        if isinstance(data_str, str):
            try:
                return datetime.strptime(data_str, '%d/%m/%Y').date()
            except ValueError:
                try:
                    return datetime.strptime(data_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        # Tenta converter apenas mês e dia
                        data = datetime.strptime(data_str, '%d/%m')
                        return datetime.now().replace(month=data.month, day=data.day).date()
                    except ValueError:
                        st.warning(f"Data inválida: {data_str}")
                        return None
        elif isinstance(data_str, datetime):
            return data_str.date()
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
            'email': 'teste@teste.com',
            'tipo_conta': 'PF',
            'data_aniversario': datetime.now().date(),
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

    # Validar colunas obrigatórias
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

    return True, "Validação OK"

def importar_cadastros(arquivo, tipo_cadastro, db):
    """Importa cadastros de um arquivo Excel ou CSV"""
    try:
        st.write("### Log de Importação")
        st.info(f"Iniciando importação de {tipo_cadastro}")

        # Verificar se o db está inicializado
        if not db:
            st.error("Erro: Conexão com banco de dados não inicializada")
            return False, "Erro: Conexão com banco de dados não inicializada"

        # Verificar se os métodos necessários existem
        metodos_necessarios = {
            'Cliente': 'add_cliente',
            'Fornecedor': 'add_fornecedor',
            'Assistente': 'add_assistente',
            'Parceiro': 'add_parceiro'
        }

        metodo = metodos_necessarios.get(tipo_cadastro)
        if not metodo or not hasattr(db, metodo):
            erro = f"Erro: Método {metodo} não encontrado no banco de dados"
            st.error(erro)
            return False, erro

        # Testar conexão com o banco de dados
        st.info("Verificando conexão com o banco de dados...")
        if not testar_conexao_db(db):
            return False, "Erro ao testar conexão com o banco de dados"

        # Detecta o tipo de arquivo pela extensão
        nome_arquivo = arquivo.name.lower()
        st.info(f"Processando arquivo: {nome_arquivo}")

        try:
            st.info("Lendo arquivo...")
            if nome_arquivo.endswith(('.xlsx', '.xls')):
                st.info("Detectado arquivo Excel")
                df = pd.read_excel(arquivo)
            else:
                st.info("Detectado arquivo CSV")
                df = pd.read_csv(arquivo)

            st.success(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
            st.info(f"Colunas encontradas: {', '.join(df.columns.tolist())}")

        except Exception as e:
            erro = f"Erro ao ler arquivo: {str(e)}\n{traceback.format_exc()}"
            st.error(erro)
            return False, erro

        # Limpar dados
        st.info("Limpando e validando dados...")
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})

        # Validar colunas obrigatórias
        colunas_base = ['nome', 'telefone', 'email']
        colunas_faltantes = [col for col in colunas_base if col not in df.columns]
        if colunas_faltantes:
            erro = f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
            st.error(erro)
            return False, erro

        sucessos = 0
        erros = []

        total_rows = len(df)
        st.info(f"Iniciando importação de {total_rows} registros...")

        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, row in df.iterrows():
            try:
                # Atualizar progresso
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"Processando registro {idx + 1} de {total_rows}")

                # Dados base para todos os tipos
                dados = {
                    'nome': str(row['nome']).strip(),
                    'telefone': str(row['telefone']).strip() if not pd.isna(row['telefone']) else None,
                    'email': str(row['email']).strip() if not pd.isna(row['email']) else None,
                    'observacoes': str(row.get('observacoes', '')).strip() if not pd.isna(row.get('observacoes')) else None
                }

                st.info(f"Processando registro: {dados['nome']}")

                try:
                    if tipo_cadastro == "Cliente":
                        tipo_conta = str(row.get('tipo_conta', 'PF')).strip().upper()
                        dados.update({
                            'tipo_conta': tipo_conta,
                            'cpf': str(row.get('cpf', '')).strip() if tipo_conta == 'PF' and not pd.isna(row.get('cpf')) else None,
                            'cnpj': str(row.get('cnpj', '')).strip() if tipo_conta == 'PJ' and not pd.isna(row.get('cnpj')) else None,
                            'razao_social': str(row.get('razao_social', '')).strip() if tipo_conta == 'PJ' and not pd.isna(row.get('razao_social')) else None,
                            'data_aniversario': pd.to_datetime(row.get('data_aniversario')).date() if not pd.isna(row.get('data_aniversario')) else None,
                            'origem_cliente': str(row.get('origem_cliente', '')).strip() if not pd.isna(row.get('origem_cliente')) else None,
                        })
                        st.info(f"Tentando adicionar cliente: {dados['nome']}")
                        getattr(db, metodo)(**dados)
                        st.success(f"Cliente {dados['nome']} adicionado com sucesso!")
                        sucessos += 1

                    elif tipo_cadastro == "Fornecedor":
                        dados.update({
                            'categoria': str(row.get('categoria', '')).strip() if not pd.isna(row.get('categoria')) else None,
                            'tipo_conta': str(row.get('tipo_conta', 'PF')).strip().upper(),
                            'recorrente': bool(row.get('recorrente', False))
                        })
                        getattr(db, metodo)(**dados)
                        sucessos += 1

                    elif tipo_cadastro == "Assistente":
                        dados.update({
                            'disponibilidade': str(row.get('disponibilidade', '')).strip() if not pd.isna(row.get('disponibilidade')) else None,
                        })
                        getattr(db, metodo)(**dados)
                        sucessos += 1

                    elif tipo_cadastro == "Parceiro":
                        dados.update({
                            'area_atuacao': str(row.get('area_atuacao', '')).strip() if not pd.isna(row.get('area_atuacao')) else None,
                            'tipo_parceria': str(row.get('tipo_parceria', '')).strip() if not pd.isna(row.get('tipo_parceria')) else None,
                        })
                        getattr(db, metodo)(**dados)
                        sucessos += 1

                except Exception as e:
                    erro_msg = f"Erro ao adicionar {tipo_cadastro} {dados['nome']}: {str(e)}\n{traceback.format_exc()}"
                    st.error(erro_msg)
                    erros.append(erro_msg)
                    continue

            except Exception as e:
                traceback_str = traceback.format_exc()
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}\nTraceback:\n{traceback_str}"
                st.error(erro_msg)
                erros.append(erro_msg)

        # Remover barra de progresso e status
        progress_bar.empty()
        status_text.empty()

        # Preparar mensagem de retorno
        st.info(f"Importação finalizada. Sucessos: {sucessos}, Erros: {len(erros)}")
        mensagem = f"Importação concluída:\n- Registros importados com sucesso: {sucessos}"
        if erros:
            mensagem += f"\n- Erros encontrados: {len(erros)}\n"
            for erro in erros:
                mensagem += f"\n  • {erro}"

        return sucessos > 0, mensagem

    except Exception as e:
        traceback_str = traceback.format_exc()
        erro_msg = f"Erro ao processar arquivo: {str(e)}\nTraceback:\n{traceback_str}"
        st.error(erro_msg)
        return False, erro_msg

def gerar_template_excel(tipo):
    """Gera um arquivo Excel template baseado no tipo de importação"""
    if tipo == "Cliente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'data_aniversario', 
            'origem_cliente', 'tipo_conta', 'cpf', 'cnpj', 
            'razao_social', 'observacoes'
        ])
    elif tipo == "Fornecedor":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'categoria',
            'tipo_conta', 'recorrente', 'observacoes'
        ])
    elif tipo == "Assistente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email',
            'disponibilidade', 'observacoes'
        ])
    elif tipo == "Parceiro":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'area_atuacao',
            'tipo_parceria', 'observacoes'
        ])
    else:
        return None

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

def gerar_template_csv(tipo):
    """Gera um arquivo CSV template baseado no tipo de importação"""
    if tipo == "Cliente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'data_aniversario', 
            'origem_cliente', 'tipo_conta', 'cpf', 'cnpj', 
            'razao_social', 'observacoes'
        ])
    elif tipo == "Fornecedor":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'categoria',
            'tipo_conta', 'recorrente', 'observacoes'
        ])
    elif tipo == "Assistente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'endereco',
            'disponibilidade', 'observacoes'
        ])
    elif tipo == "Parceiro":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'area_atuacao',
            'tipo_parceria', 'observacoes'
        ])
    else:
        return None

    return df.to_csv(index=False).encode('utf-8')

def importar_propostas(arquivo, db):
    """Importa propostas de um arquivo CSV"""
    try:
        df = pd.read_csv(arquivo, encoding='utf-8')

        # Validar colunas obrigatórias
        colunas_obrigatorias = ['cliente_id', 'descricao', 'valor', 'status']
        for col in colunas_obrigatorias:
            if col not in df.columns:
                return False, f"Coluna obrigatória '{col}' não encontrada no arquivo"

        sucessos = 0
        erros = []

        for _, row in df.iterrows():
            try:
                # Validar e converter tipos numéricos
                try:
                    cliente_id = int(row['cliente_id'])
                    valor = float(row['valor'])
                except (ValueError, TypeError) as e:
                    erros.append(f"Erro na linha {_ + 2}: Valor inválido para cliente_id ou valor - {str(e)}")
                    continue

                # Validar e converter datas
                data_inicio = validar_data(row.get('data_inicio'))
                data_fim = validar_data(row.get('data_fim'))
                prazo_entrega = validar_data(row.get('prazo_entrega'))

                db.add_proposta(
                    cliente_id=cliente_id,
                    descricao=row['descricao'],
                    valor=valor,
                    status=row['status'],
                    tipo_proposta=row.get('tipo_proposta'),
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    prazo_entrega=prazo_entrega
                )
                sucessos += 1

            except Exception as e:
                erros.append(f"Erro na linha {_ + 2}: {str(e)}")

        return True, f"Importação concluída: {sucessos} propostas importadas com sucesso. {len(erros)} erros." + (f"\nErros:\n" + "\n".join(erros) if erros else "")

    except Exception as e:
        return False, f"Erro ao processar arquivo: {str(e)}"