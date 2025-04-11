import streamlit as st
import pandas as pd
import io
from datetime import datetime
import logging
import traceback
import unidecode  # Para normalizar strings na comparação

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Título da página
st.title("📥 Importar Propostas")

# Inicializar banco de dados
from utils.database import Database

# Garantir que temos uma instância do banco de dados na session_state
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
        st.success("Banco de dados conectado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        st.stop()

# Mensagem explicativa
st.write("""
Esta página permite importar propostas a partir de um arquivo CSV.

Para uma importação bem-sucedida, seu arquivo deve:
1. Usar ponto e vírgula (;) como separador
2. Conter uma coluna 'cliente_nome' com o nome do cliente já cadastrado no sistema
3. Conter colunas 'descricao' e 'valor' obrigatoriamente
""")

# Exibir exemplo de arquivo
with st.expander("Ver exemplo de arquivo CSV"):
    exemplo = """cliente_nome;descricao;valor;status;tipo_proposta;data_inicio;data_fim
Fulano da Silva;Organização de armários;1500.00;Aberta;Organização;01/06/2025;10/06/2025
Ciclano dos Santos;Consultoria de decoração;2000.00;Aberta;Consultoria;15/05/2025;20/05/2025"""

    st.code(exemplo)

# Download do template
template_file = io.BytesIO()
template_df = pd.DataFrame([
    {
        'cliente_nome': 'Fulano da Silva',
        'descricao': 'Organização de armários',
        'valor': 1500.00,
        'status': 'Aberta',
        'tipo_proposta': 'Organização',
        'data_inicio': '01/06/2025',
        'data_fim': '10/06/2025',
        'prazo_entrega': '15/06/2025'
    }
])

# Converter para CSV
template_csv = template_df.to_csv(index=False, sep=';').encode('utf-8')

# Botão para baixar o template
st.download_button(
    label="📝 Baixar template CSV",
    data=template_csv,
    file_name="template_proposta.csv",
    mime="text/csv",
)

# Lista de clientes para seleção manual
def get_clients_mapping():
    """Recupera a lista de clientes do banco de dados e cria um mapeamento de nomes para IDs"""
    db = st.session_state.db
    clientes_df = db.get_clientes()
    
    # Se não há clientes cadastrados, retorna um dicionário vazio
    if clientes_df.empty:
        return {}
    
    # Cria um dicionário normal com nome -> id
    clientes_dict = dict(zip(clientes_df['nome'].str.strip(), clientes_df['id']))
    
    # Cria um dicionário normalizado para busca flexível
    clientes_norm = {}
    for nome, id_cliente in clientes_dict.items():
        # Normaliza removendo acentos, espaços extras e convertendo para minúsculas
        nome_norm = unidecode.unidecode(nome.lower().strip())
        clientes_norm[nome_norm] = id_cliente
        
        # Adiciona versões com nomes parciais (primeiro nome, etc.)
        partes = nome_norm.split()
        if len(partes) > 1:
            clientes_norm[partes[0]] = id_cliente  # Primeiro nome
            
    return {
        'exact': clientes_dict,      # Para correspondência exata
        'normalized': clientes_norm  # Para busca flexível
    }

# Função para encontrar cliente pelo nome com diferentes estratégias
def find_client_id(cliente_nome, clientes_mapping):
    """
    Procura um cliente pelo nome usando diferentes estratégias de correspondência
    
    Args:
        cliente_nome: Nome do cliente para buscar
        clientes_mapping: Dicionário de mapeamento de nomes para IDs
        
    Returns:
        tuple: (id do cliente, nome exato encontrado) ou (None, None) se não encontrado
    """
    if not cliente_nome or not clientes_mapping:
        return None, None
    
    # Limpar o nome do cliente
    nome = cliente_nome.strip()
    
    # 1. Tentar correspondência exata
    if nome in clientes_mapping['exact']:
        return clientes_mapping['exact'][nome], nome
    
    # 2. Tentar correspondência normalizada
    nome_norm = unidecode.unidecode(nome.lower().strip())
    if nome_norm in clientes_mapping['normalized']:
        client_id = clientes_mapping['normalized'][nome_norm]
        
        # Buscar o nome original para referência
        for original_nome, id_cliente in clientes_mapping['exact'].items():
            if id_cliente == client_id:
                return client_id, original_nome
                
        return client_id, None  # Caso não encontre o nome original
    
    # 3. Tentar correspondência parcial
    for nome_cliente, id_cliente in clientes_mapping['normalized'].items():
        if nome_norm in nome_cliente or nome_cliente in nome_norm:
            # Buscar o nome original para referência
            for original_nome, id in clientes_mapping['exact'].items():
                if id == id_cliente:
                    return id_cliente, original_nome
    
    # Nenhuma correspondência encontrada
    return None, None

# Função para importar propostas
def importar_propostas(arquivo, debug_mode=False):
    """Importar propostas a partir de um arquivo CSV"""
    try:
        # Carregar o arquivo
        try:
            df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            # Tentar codificações alternativas
            encodings = ['latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']
            for encoding in encodings:
                try:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=';', encoding=encoding)
                    st.info(f"Arquivo lido com sucesso usando codificação {encoding}")
                    break
                except:
                    continue
            else:
                # Se nenhuma codificação funcionou
                st.error("Não foi possível ler o arquivo. Tente salvar como UTF-8 ou CSV separado por ponto e vírgula.")
                return False, "Erro na leitura do arquivo"
        
        # Debug info
        if debug_mode:
            st.write(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
            st.write("Primeiras linhas:")
            st.dataframe(df.head())
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        if colunas_faltantes:
            st.error(f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}")
            return False, f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
        
        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})
        df = df.fillna('')  # Substituir NaN por string vazia para evitar problemas
        
        # Obter o banco de dados
        db = st.session_state.db
        
        # Carregar clientes para mapear nomes para IDs
        clientes_mapping = get_clients_mapping()
        if not clientes_mapping['exact']:
            st.error("Não há clientes cadastrados no sistema")
            return False, "Não há clientes cadastrados no sistema"
        
        # Em modo debug, mostrar clientes disponíveis
        if debug_mode:
            # Criar um DataFrame para exibir
            clientes_df = pd.DataFrame([(id, nome) for nome, id in clientes_mapping['exact'].items()], 
                                       columns=['id', 'nome'])
            st.write("### Clientes disponíveis no sistema")
            st.dataframe(clientes_df)
        
        # Resultados
        sucessos = 0
        erros = []
        
        # Barra de progresso
        progress_bar = st.progress(0)
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                progress = (idx + 1) / len(df)
                progress_bar.progress(progress)
                
                # Inicializar cliente_id como None no início de cada iteração
                cliente_id = None
                cliente_encontrado = None
                
                # Buscar cliente pelo nome
                cliente_nome = str(row['cliente_nome']).strip()
                if not cliente_nome:
                    erros.append(f"Nome do cliente vazio na linha {idx + 2}")
                    continue
                
                # Buscar cliente por diferentes estratégias
                cliente_id, cliente_encontrado = find_client_id(cliente_nome, clientes_mapping)
                
                # Se não encontrou cliente
                if cliente_id is None:
                    erros.append(f"Cliente '{cliente_nome}' não encontrado na linha {idx + 2}")
                    continue
                
                # Debug
                if debug_mode and cliente_encontrado:
                    st.info(f"Cliente '{cliente_nome}' corresponde a '{cliente_encontrado}' (ID: {cliente_id})")
                
                # Validar descrição
                descricao = str(row['descricao']).strip()
                if not descricao:
                    erros.append(f"Descrição vazia na linha {idx + 2}")
                    continue
                
                # Validar valor
                valor = None
                try:
                    valor_str = str(row['valor']).strip().replace(',', '.')
                    valor = float(valor_str)
                    if valor <= 0:
                        erros.append(f"Valor deve ser maior que zero na linha {idx + 2}")
                        continue
                except (ValueError, TypeError):
                    erros.append(f"Valor não numérico na linha {idx + 2}")
                    continue
                
                # Status padrão se não for fornecido
                status = 'Aberta'
                if 'status' in row and row['status']:
                    status_valor = str(row['status']).strip()
                    if status_valor in ['Aberta', 'Fechada', 'Recusada']:
                        status = status_valor
                
                # Tipo de proposta
                tipo_proposta = None
                if 'tipo_proposta' in row and row['tipo_proposta']:
                    tipo_proposta = str(row['tipo_proposta']).strip()
                
                # Processar datas
                data_inicio = None
                data_fim = None
                prazo_entrega = None
                
                # Data de início
                if 'data_inicio' in row and row['data_inicio']:
                    try:
                        data_inicio = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Data de início inválida na linha {idx + 2}: {str(e)}")
                
                # Data de fim
                if 'data_fim' in row and row['data_fim']:
                    try:
                        data_fim = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Data de fim inválida na linha {idx + 2}: {str(e)}")
                
                # Prazo de entrega
                if 'prazo_entrega' in row and row['prazo_entrega']:
                    try:
                        prazo_entrega = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Prazo de entrega inválido na linha {idx + 2}: {str(e)}")
                
                # Adicionar proposta - verificar se cliente_id é um inteiro válido
                if not isinstance(cliente_id, int):
                    erros.append(f"ID de cliente inválido na linha {idx + 2}")
                    continue
                    
                proposta_id = db.add_proposta(
                    cliente_id=cliente_id,
                    descricao=descricao,
                    valor=valor,
                    status=status,
                    tipo_proposta=tipo_proposta,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    prazo_entrega=prazo_entrega
                )
                
                if debug_mode:
                    st.success(f"Proposta {idx + 1} adicionada com sucesso. ID: {proposta_id}")
                sucessos += 1
                
            except Exception as e:
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}"
                if debug_mode:
                    st.error(erro_msg)
                erros.append(erro_msg)
                logger.error(f"{erro_msg}\n{traceback.format_exc()}")
                continue
        
        # Limpar barra de progresso
        progress_bar.empty()
        
        # Mensagem final
        if sucessos > 0:
            st.success(f"{sucessos} propostas importadas com sucesso!")
        
        if erros:
            st.error(f"{len(erros)} erros encontrados:")
            for erro in erros[:5]:  # Mostrar apenas os 5 primeiros erros
                st.error(f"- {erro}")
            
            if len(erros) > 5:
                st.warning(f"... e mais {len(erros) - 5} erros. Verifique o log para detalhes.")
        
        return sucessos > 0, f"Importação concluída. {sucessos} propostas importadas com sucesso. Erros: {len(erros)}"
    
    except Exception as e:
        erro_msg = f"Erro ao processar arquivo: {str(e)}"
        st.error(erro_msg)
        logger.error(f"{erro_msg}\n{traceback.format_exc()}")
        return False, erro_msg

# Opções de depuração
debug_mode = st.checkbox("Modo de depuração (exibe informações detalhadas)")

# Widget para upload de arquivo
arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

if arquivo:
    col1, col2 = st.columns([1,2])
    with col1:
        if st.button("Importar Propostas", type="primary"):
            with st.spinner("Importando propostas..."):
                sucesso, mensagem = importar_propostas(arquivo, debug_mode=debug_mode)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
                    
    with col2:
        if st.button("Verificar arquivo (sem importar)"):
            with st.spinner("Verificando arquivo..."):
                try:
                    # Tenta ler o arquivo com diferentes codificações
                    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']
                    for encoding in encodings:
                        try:
                            arquivo.seek(0)
                            df = pd.read_csv(arquivo, sep=';', encoding=encoding)
                            st.success(f"Arquivo lido com sucesso usando codificação {encoding}")
                            st.write(f"Dimensões: {df.shape}")
                            st.write("Primeiras linhas:")
                            st.dataframe(df.head())
                            
                            # Verificar correspondência de clientes
                            if 'cliente_nome' in df.columns:
                                st.write("### Verificando correspondência de clientes:")
                                clientes_mapping = get_clients_mapping()
                                
                                resultados = []
                                for idx, row in df.iterrows():
                                    cliente_nome = str(row['cliente_nome']).strip()
                                    cliente_id, cliente_encontrado = find_client_id(cliente_nome, clientes_mapping)
                                    
                                    status = "✅ Encontrado" if cliente_id else "❌ Não encontrado"
                                    resultados.append({
                                        'Linha': idx + 2,
                                        'Nome no CSV': cliente_nome,
                                        'Nome no Sistema': cliente_encontrado if cliente_encontrado else "-",
                                        'ID': cliente_id if cliente_id else "-",
                                        'Status': status
                                    })
                                
                                resultados_df = pd.DataFrame(resultados)
                                st.dataframe(resultados_df)
                                
                                # Estatísticas de correspondência
                                encontrados = sum(1 for r in resultados if r['Status'] == "✅ Encontrado")
                                total = len(resultados)
                                st.write(f"Correspondência: {encontrados}/{total} clientes encontrados ({encontrados/total:.0%})")
                                
                            break
                        except Exception as e:
                            continue
                    else:
                        st.error("Não foi possível ler o arquivo com nenhuma codificação.")
                except Exception as e:
                    st.error(f"Erro ao verificar arquivo: {str(e)}")
else:
    st.info("Por favor, faça upload de um arquivo CSV para começar a importação.")