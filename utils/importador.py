import pandas as pd
import streamlit as st
from datetime import datetime
import io
import logging
import traceback

logger = logging.getLogger(__name__)

# Mapeamento de meses em português para validação
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

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

def gerar_template_csv(tipo):
    """Gera um arquivo CSV template baseado no tipo de importação"""
    if tipo == "Cliente":
        df = pd.DataFrame(columns=[
            'nome', 'telefone', 'email', 'data_aniversario', 
            'origem_cliente', 'cpf', 'estado', 'cidade',
            'bairro', 'endereco', 'observacoes'
        ])
    elif tipo == "Fornecedor":
        df = pd.DataFrame(columns=[
            'descricao',  # Razão Social
            'telefone',   
            'endereco',   
            'categoria',  
            'pix',       
            'observacao'  
        ])
    elif tipo == "Assistente":
        df = pd.DataFrame(columns=[
            'nome',      
            'telefone',  
            'endereco',  
            'pix',      
            'observacao' 
        ])
    elif tipo == "Parceiro":
        df = pd.DataFrame(columns=[
            'nome',          
            'telefone',      
            'area_atuacao',  
            'tipo_parceria', 
            'observacao'     
        ])
    else:
        return None

    return df.to_csv(index=False, sep=';').encode('utf-8')

def importar_cadastros(arquivo, tipo_cadastro, db):
    """Importa cadastros de um arquivo CSV"""
    try:
        st.write("### Log de Importação")
        st.info(f"Iniciando importação de {tipo_cadastro}")

        if not db:
            st.error("Erro: Conexão com banco de dados não inicializada")
            return False, "Erro: Conexão com banco de dados não inicializada"

        # Detecta o tipo de arquivo e lê
        st.info("Lendo arquivo...")
        try:
            df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
            st.success(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            return False, f"Erro ao ler arquivo: {str(e)}"

        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})

        sucessos = 0
        erros = []

        total_rows = len(df)
        progress_bar = st.progress(0)

        for idx, row in df.iterrows():
            try:
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)

                if tipo_cadastro == "Cliente":
                    # Processar dados do cliente
                    nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                    if not nome:
                        continue

                    telefone = str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None
                    if telefone:
                        telefone = ''.join(filter(str.isdigit, telefone))

                    # Processamento do CPF
                    cpf = str(row.get('cpf', '')).strip() if pd.notna(row.get('cpf')) else None
                    if cpf:
                        # Remove caracteres não numéricos do CPF
                        cpf = ''.join(filter(str.isdigit, cpf))
                        # Formata o CPF se tiver 11 dígitos
                        if len(cpf) == 11:
                            cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

                    data_aniv = validar_data(row.get('data_aniversario'))

                    db.add_cliente(
                        nome=nome,
                        telefone=telefone,
                        cpf=cpf,
                        email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                        estado=str(row.get('estado', '')).strip() if pd.notna(row.get('estado')) else None,
                        cidade=str(row.get('cidade', '')).strip() if pd.notna(row.get('cidade')) else None,
                        bairro=str(row.get('bairro', '')).strip() if pd.notna(row.get('bairro')) else None,
                        endereco=str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                        data_aniversario=data_aniv,
                        origem_cliente=str(row.get('origem_cliente', 'Importação')).strip() if pd.notna(row.get('origem_cliente')) else 'Importação',
                        observacoes=str(row.get('observacoes', '')).strip() if pd.notna(row.get('observacoes')) else None
                    )
                    sucessos += 1

                elif tipo_cadastro == "Fornecedor":
                    descricao = str(row['descricao']).strip() if pd.notna(row.get('descricao')) else None
                    if not descricao:
                        continue

                    db.add_fornecedor(
                        descricao=descricao,
                        contato=str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                        endereco=str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                        categoria=str(row.get('categoria', '')).strip() if pd.notna(row.get('categoria')) else None,
                        pix=str(row.get('pix', '')).strip() if pd.notna(row.get('pix')) else None,
                        observacoes=str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao')) else None
                    )
                    sucessos += 1

                elif tipo_cadastro == "Parceiro":
                    nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                    if not nome:
                        continue

                    db.add_parceiro(
                        nome=nome,
                        telefone=str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                        area_atuacao=str(row.get('area_atuacao', '')).strip() if pd.notna(row.get('area_atuacao')) else None,
                        tipo_parceria=str(row.get('tipo_parceria', '')).strip() if pd.notna(row.get('tipo_parceria')) else None,
                        observacoes=str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao')) else None
                    )
                    sucessos += 1

                elif tipo_cadastro == "Assistente":
                    nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                    if not nome:
                        continue

                    db.add_assistente(
                        nome=nome,
                        telefone=str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                        endereco=str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                        pix=str(row.get('pix', '')).strip() if pd.notna(row.get('pix')) else None,
                        observacoes=str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao')) else None
                    )
                    sucessos += 1

            except Exception as e:
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}"
                st.error(erro_msg)
                erros.append(erro_msg)
                continue

        progress_bar.empty()

        mensagem = f"Importação concluída. {sucessos} registros importados com sucesso."
        if erros:
            mensagem += f"\nErros encontrados: {len(erros)}"
            for erro in erros[:5]:  # Mostrar apenas os 5 primeiros erros
                mensagem += f"\n- {erro}"

        return sucessos > 0, mensagem

    except Exception as e:
        erro_msg = f"Erro ao processar arquivo: {str(e)}"
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