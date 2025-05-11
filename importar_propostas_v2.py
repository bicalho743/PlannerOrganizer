import streamlit as st
import pandas as pd
import io
from datetime import datetime
import logging
import traceback
import unidecode  # Para normalizar strings na comparação
import re  # Para expressões regulares

# Importar função robusta para valores monetários
from utils.importador import normalizar_valor_monetario

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Título da página
st.title("📥 Importar Propostas (V2)")

# Inicializar banco de dados
from utils.database import Database
from utils.limpar_dados import limpar_clientes_form

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
Esta é uma versão atualizada do importador de propostas, com melhor tratamento de erros 
e capacidade de processar diversos formatos monetários.

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
        'cliente_nome': 'Maria da Silva',
        'descricao': 'Organização de armários',
        'valor': '1500,00',
        'status': 'Aberta',
        'tipo_proposta': 'Organização',
        'data_inicio': '01/06/2025',
        'data_fim': '10/06/2025',
        'prazo_entrega': '15/06/2025'
    },
    {
        'cliente_nome': 'João Santos',
        'descricao': 'Consultoria de decoração',
        'valor': '2000,00',
        'status': 'Aberta',
        'tipo_proposta': 'Consultoria',
        'data_inicio': '15/05/2025',
        'data_fim': '20/05/2025',
        'prazo_entrega': '30/05/2025'
    },
    {
        'cliente_nome': 'Ana Oliveira',
        'descricao': 'Reorganização de cozinha',
        'valor': '1800,00',
        'status': 'Aberta',
        'tipo_proposta': 'Reorganização',
        'data_inicio': '15/07/2025',
        'data_fim': '20/07/2025',
        'prazo_entrega': '25/07/2025'
    }
])

# Converter para CSV para download
template_csv = template_df.to_csv(index=False, sep=';').encode('utf-8')

# Botão para baixar o template
st.download_button(
    label="📝 Baixar template CSV",
    data=template_csv,
    file_name="template_proposta_v2.csv",
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

def try_read_csv_with_formats(arquivo):
    """Tenta ler um CSV com diferentes separadores e codificações"""
    # Lista de possíveis separadores e encodings
    separadores = [';', ',', '\t']
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig', 'windows-1252']
    
    # Tenta cada combinação
    for encoding in encodings:
        for sep in separadores:
            try:
                arquivo.seek(0)
                df = pd.read_csv(arquivo, sep=sep, encoding=encoding)
                
                # Verificar se o DataFrame tem pelo menos 1 linha e 2 colunas
                if df.shape[0] > 0 and df.shape[1] > 1:
                    logger.info(f"Arquivo lido com sucesso usando separador '{sep}' e codificação '{encoding}'")
                    return df, True
            except Exception as e:
                continue
    
    # Se chegou aqui, não conseguiu ler o arquivo
    return None, False

# Função para importar propostas - VERSÃO ROBUSTA
def importar_propostas_v2(arquivo, debug_mode=False, usar_cliente_id=False):
    """
    Nova versão da função de importação de propostas com melhor tratamento 
    de erros e processamento de valores monetários
    """
    try:
        # Resultados
        sucessos = 0
        erros = []
        
        # 1. ETAPA: LEITURA DO ARQUIVO
        try:
            # Tentar ler o arquivo com formatos variados
            df, success = try_read_csv_with_formats(arquivo)
            
            if not success:
                mensagem = "Não foi possível ler o arquivo. Tente usar CSV com separador ponto-e-vírgula (;) e codificação UTF-8."
                logger.error(mensagem)
                return False, mensagem
                
        except Exception as e:
            mensagem = f"Erro ao ler arquivo: {str(e)}"
            logger.error(mensagem)
            return False, mensagem
        
        # Debug info
        if debug_mode:
            st.write(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
            st.write("Primeiras linhas:")
            st.dataframe(df.head())
        
        # 2. ETAPA: VERIFICAÇÃO DAS COLUNAS
        # Verificar colunas obrigatórias
        if usar_cliente_id:
            colunas_obrigatorias = ['cliente_id', 'descricao', 'valor']
        else:
            colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor']
            
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        if colunas_faltantes:
            mensagem = f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
            logger.error(mensagem)
            return False, mensagem
        
        # 3. ETAPA: LIMPEZA DOS DADOS
        # Substituir valores nulos por string vazia para evitar problemas
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})
        df = df.fillna('')  # Substituir NaN por string vazia
        
        # 4. ETAPA: VERIFICAÇÃO DE CLIENTES NO SISTEMA
        # Obter o banco de dados
        db = st.session_state.db
        
        # Verificar se já existem clientes no sistema
        clientes_df = db.get_clientes()
        if clientes_df.empty and not debug_mode:
            mensagem = "Não há clientes cadastrados no sistema. Importe clientes primeiro antes de importar propostas."
            logger.error(mensagem)
            return False, mensagem
        
        # Criar um conjunto com os IDs dos clientes disponíveis para verificação
        clientes_ids_disponiveis = set(clientes_df['id'].astype(int).tolist()) if not clientes_df.empty else set()
        
        # Carregar clientes para mapear nomes para IDs apenas se não estivermos usando cliente_id direto
        clientes_mapping = None
        if not usar_cliente_id:
            clientes_mapping = get_clients_mapping()
            if not clientes_mapping['exact'] and not debug_mode:
                mensagem = "Não há clientes cadastrados no sistema"
                logger.error(mensagem)
                return False, mensagem
            
            # Em modo debug, mostrar clientes disponíveis
            if debug_mode:
                clientes_disponiveis = list(clientes_mapping['exact'].keys())
                st.write("### Clientes disponíveis no sistema")
                st.write(f"Total: {len(clientes_disponiveis)}")
                if len(clientes_disponiveis) <= 30:  # Mostrar todos se forem poucos
                    st.write(clientes_disponiveis)
                else:
                    st.write(clientes_disponiveis[:30] + ["..."])  # Mostrar apenas os primeiros 30
        
        # 5. ETAPA: PROCESSAMENTO DAS PROPOSTAS
        # Barra de progresso
        progress_bar = st.progress(0)
        total_rows = len(df)
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                # Atualizar progresso
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                
                # Variáveis para processar proposta
                proposta_data = {}
                
                # Adicionar o ID do usuário atual se estiver disponível na sessão
                if 'usuario_id' in st.session_state and st.session_state.usuario_id:
                    proposta_data['usuario_id'] = st.session_state.usuario_id
                    if debug_mode:
                        st.info(f"Usando usuario_id={st.session_state.usuario_id} para a proposta na linha {idx + 2}")
                
                # 5.1 Processar cliente_id
                # Inicializar como None e atribuir mais tarde se tudo estiver correto
                proposta_data['cliente_id'] = None
                
                if usar_cliente_id:
                    # Estratégia 1: Usar cliente_id do arquivo
                    try:
                        id_temp = int(row['cliente_id'])
                        
                        # Verificar se o cliente existe
                        if id_temp not in clientes_ids_disponiveis and not debug_mode:
                            erros.append(f"Cliente ID {id_temp} não encontrado na linha {idx + 2}")
                            continue
                        
                        # Se tudo ok, atribuir ao dicionário de dados
                        proposta_data['cliente_id'] = id_temp
                        
                        if debug_mode:
                            st.info(f"ID do cliente na linha {idx + 2}: {id_temp}")
                    except (ValueError, TypeError) as e:
                        erros.append(f"ID de cliente inválido na linha {idx + 2}: {row['cliente_id']}")
                        continue
                else:
                    # Estratégia 2: Buscar cliente pelo nome
                    try:
                        cliente_nome = str(row['cliente_nome']).strip()
                        if not cliente_nome:
                            erros.append(f"Nome do cliente vazio na linha {idx + 2}")
                            continue
                        
                        # Buscar cliente por diferentes estratégias
                        id_temp, cliente_encontrado = find_client_id(cliente_nome, clientes_mapping)
                        
                        # Se não encontrou cliente
                        if id_temp is None:
                            erros.append(f"Cliente '{cliente_nome}' não encontrado na linha {idx + 2}")
                            continue
                        
                        # Se encontrou, atribuir ao dicionário de dados
                        proposta_data['cliente_id'] = int(id_temp)
                        
                        if debug_mode and cliente_encontrado:
                            st.info(f"Cliente '{cliente_nome}' corresponde a '{cliente_encontrado}' (ID: {id_temp})")
                    except Exception as e:
                        erros.append(f"Erro ao processar cliente na linha {idx + 2}: {str(e)}")
                        continue
                
                # 5.2 Processar descrição
                try:
                    descricao = str(row['descricao']).strip()
                    if not descricao:
                        erros.append(f"Descrição vazia na linha {idx + 2}")
                        continue
                    
                    proposta_data['descricao'] = descricao
                except Exception as e:
                    erros.append(f"Erro ao processar descrição na linha {idx + 2}: {str(e)}")
                    continue
                
                # 5.3 Processar valor
                try:
                    valor = normalizar_valor_monetario(str(row['valor']))
                    if valor is None or valor <= 0:
                        erros.append(f"Valor inválido na linha {idx + 2}")
                        continue
                    
                    proposta_data['valor'] = valor
                    
                    if debug_mode:
                        st.info(f"Valor original: '{row['valor']}', processado: '{valor}'")
                except Exception as e:
                    erros.append(f"Erro ao processar valor na linha {idx + 2}: {str(e)}")
                    continue
                
                # 5.4 Processar status
                proposta_data['status'] = 'Aberta'  # Valor padrão
                if 'status' in row and row['status']:
                    status_valor = str(row['status']).strip()
                    if status_valor in ['Aberta', 'Fechada', 'Recusada']:
                        proposta_data['status'] = status_valor
                
                # 5.5 Processar tipo_proposta
                if 'tipo_proposta' in row and row['tipo_proposta']:
                    proposta_data['tipo_proposta'] = str(row['tipo_proposta']).strip()
                
                # 5.6 Processar datas
                # Data de início
                if 'data_inicio' in row and row['data_inicio']:
                    try:
                        proposta_data['data_inicio'] = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Data de início inválida na linha {idx + 2}: {str(e)}")
                
                # Data de fim
                if 'data_fim' in row and row['data_fim']:
                    try:
                        proposta_data['data_fim'] = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Data de fim inválida na linha {idx + 2}: {str(e)}")
                
                # Prazo de entrega
                if 'prazo_entrega' in row and row['prazo_entrega']:
                    try:
                        proposta_data['prazo_entrega'] = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                    except Exception as e:
                        if debug_mode:
                            st.warning(f"Prazo de entrega inválido na linha {idx + 2}: {str(e)}")
                
                # 5.7 Verificar se cliente_id foi definido corretamente
                if proposta_data['cliente_id'] is None or not isinstance(proposta_data['cliente_id'], int):
                    erros.append(f"ID de cliente inválido na linha {idx + 2}")
                    continue
                
                # 5.8 Adicionar proposta ao banco de dados
                try:
                    proposta_id = db.add_proposta(**proposta_data)
                    
                    if debug_mode:
                        st.success(f"Proposta {idx + 1} adicionada com sucesso. ID: {proposta_id}")
                    
                    sucessos += 1
                except Exception as e:
                    erro_msg = f"Erro ao gravar proposta na linha {idx + 2}: {str(e)}"
                    logger.error(erro_msg)
                    erros.append(erro_msg)
                    continue
                
            except Exception as e:
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}"
                logger.error(f"{erro_msg}\n{traceback.format_exc()}")
                erros.append(erro_msg)
                continue
        
        # 6. ETAPA: FINALIZAÇÃO
        # Limpar barra de progresso
        progress_bar.empty()
        
        # Gerar relatório final
        if sucessos > 0:
            st.success(f"{sucessos} propostas importadas com sucesso!")
        
        if erros:
            st.error(f"{len(erros)} erros encontrados:")
            for erro in erros[:10]:  # Mostrar os primeiros 10 erros
                st.error(f"- {erro}")
            
            if len(erros) > 10:
                st.warning(f"... e mais {len(erros) - 10} erros. Verifique o log para detalhes.")
            
            # Logar todos os erros
            logger.error(f"Erros na importação:\n" + "\n".join(erros))
        
        return sucessos > 0, f"Importação concluída. {sucessos} registros importados com sucesso. Erros encontrados: {len(erros)}"
    
    except Exception as e:
        erro_msg = f"Erro ao processar arquivo: {str(e)}"
        logger.error(f"{erro_msg}\n{traceback.format_exc()}")
        return False, erro_msg

# Seção para limpar dados de clientes
with st.expander("🧹 Limpar Cadastro de Clientes"):
    st.write("Use esta opção para remover todos os clientes do sistema antes da importação.")
    limpar_clientes_form()

# Opções de importação
col1, col2 = st.columns(2)
with col1:
    debug_mode = st.checkbox("Modo de depuração", help="Exibe informações detalhadas durante a importação")
with col2:
    usar_cliente_id = st.checkbox("Usar ID do cliente", help="Use esta opção se seu arquivo CSV contém o ID do cliente em vez do nome")

# Exemplo para modo cliente_id
if usar_cliente_id:
    st.info("""
    Seu arquivo CSV deve conter a coluna 'cliente_id' com o ID numérico do cliente.
    Exemplo: cliente_id;descricao;valor;status
             42;Organização de armários;1500,00;Aberta
    """)

# Widget para upload de arquivo
arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

if arquivo:
    col1, col2 = st.columns([1,2])
    with col1:
        if st.button("Importar Propostas", type="primary"):
            with st.spinner("Importando propostas..."):
                sucesso, mensagem = importar_propostas_v2(arquivo, debug_mode=debug_mode, usar_cliente_id=usar_cliente_id)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
                    
    with col2:
        if st.button("Verificar arquivo (sem importar)"):
            with st.spinner("Verificando arquivo..."):
                try:
                    # Tentar ler o arquivo com formatos variados
                    df, success = try_read_csv_with_formats(arquivo)
                    
                    if not success:
                        st.error("Não foi possível ler o arquivo. Tente outro formato ou codificação.")
                    else:
                        st.write(f"Dimensões: {df.shape}")
                        st.write("Primeiras linhas:")
                        st.dataframe(df.head())
                        
                        # Verificar colunas presentes
                        st.write("### Colunas encontradas no arquivo:")
                        st.write(", ".join(df.columns.tolist()))
                        
                        # Testar processamento de valores
                        if 'valor' in df.columns:
                            st.write("### Teste de processamento de valores monetários:")
                            for idx, row in df.head(5).iterrows():
                                valor_original = row.get('valor', '')
                                valor_processado = normalizar_valor_monetario(str(valor_original))
                                status = "✅ Válido" if valor_processado is not None else "❌ Inválido"
                                st.write(f"Linha {idx+2}: '{valor_original}' → {valor_processado} ({status})")
                        
                        # Verificar correspondência de clientes
                        if not usar_cliente_id and 'cliente_nome' in df.columns:
                            st.write("### Teste de correspondência de clientes:")
                            clientes_mapping = get_clients_mapping()
                            
                            for idx, row in df.head(5).iterrows():
                                cliente_nome = str(row.get('cliente_nome', '')).strip()
                                id_cliente, nome_encontrado = find_client_id(cliente_nome, clientes_mapping)
                                status = "✅ Encontrado" if id_cliente is not None else "❌ Não encontrado"
                                st.write(f"Linha {idx+2}: '{cliente_nome}' → ID: {id_cliente} ({status})")
                except Exception as e:
                    st.error(f"Erro ao verificar arquivo: {str(e)}")
else:
    st.info("Por favor, faça upload de um arquivo CSV para começar a importação.")