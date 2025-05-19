import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import logging
import traceback
import unidecode  # Para normalizar strings na comparação
import re  # Para expressões regulares
import os
import sys

# Adicionar diretório raiz ao path
root_dir = os.path.abspath(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Importar função robusta para valores monetários
from utils.importador import normalizar_valor_monetario

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Título da página
st.title("📥 Importar Propostas Retroativas")

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
Esta ferramenta permite importar propostas com datas retroativas, mantendo intacta 
a cronologia de eventos e permitindo reconstruir o histórico de propostas.

Para uma importação bem-sucedida, seu arquivo deve:
1. Usar ponto e vírgula (;) como separador
2. Conter uma coluna 'cliente_nome' com o nome do cliente já cadastrado no sistema
3. Conter colunas 'descricao', 'valor', 'data_criacao' e 'status' obrigatoriamente
""")

# Exibir exemplo de arquivo
with st.expander("Ver exemplo de arquivo CSV"):
    exemplo = """cliente_nome;descricao;valor;status;tipo_proposta;data_criacao;data_inicio;data_fim;prazo_entrega
Fulano da Silva;Organização de armários;1500.00;Finalizada;Organização;01/01/2025;01/02/2025;10/02/2025;15/02/2025
Ciclano dos Santos;Consultoria de decoração;2000.00;Recusada;Consultoria;15/01/2025;15/02/2025;20/02/2025;25/02/2025"""

    st.code(exemplo)

# Download do template
template_file = io.BytesIO()
template_df = pd.DataFrame([
    {
        'cliente_nome': 'Maria da Silva',
        'descricao': 'Organização de armários',
        'valor': '1500,00',
        'status': 'Finalizada',
        'tipo_proposta': 'Organização',
        'data_criacao': '01/01/2025',
        'data_inicio': '01/02/2025',
        'data_fim': '10/02/2025',
        'prazo_entrega': '15/02/2025'
    },
    {
        'cliente_nome': 'João Santos',
        'descricao': 'Consultoria de decoração',
        'valor': '2000,00',
        'status': 'Recusada',
        'tipo_proposta': 'Consultoria',
        'data_criacao': '15/01/2025',
        'data_inicio': '15/02/2025',
        'data_fim': '20/02/2025',
        'prazo_entrega': '25/02/2025'
    },
    {
        'cliente_nome': 'Ana Oliveira',
        'descricao': 'Reorganização de cozinha',
        'valor': '1800,00',
        'status': 'Em execução',
        'tipo_proposta': 'Reorganização',
        'data_criacao': '10/03/2025',
        'data_inicio': '15/03/2025',
        'data_fim': '20/03/2025',
        'prazo_entrega': '25/03/2025'
    }
])

# Converter para CSV para download
template_csv = template_df.to_csv(index=False, sep=';').encode('utf-8')

# Botão para baixar o template
st.download_button(
    label="📝 Baixar template CSV",
    data=template_csv,
    file_name="template_proposta_retroativa.csv",
    mime="text/csv",
)

# Lista de clientes para seleção manual
def get_clients_mapping():
    """Recupera a lista de clientes do banco de dados e cria um mapeamento de nomes para IDs"""
    clientes = st.session_state.db.get_clientes()
    
    # Garantir que o DataFrame não está vazio
    if clientes.empty:
        return {}
        
    # Criar mapeamentos
    # Mapeamento principal: nome exato -> id
    nome_para_id = {row['nome']: row['id'] for _, row in clientes.iterrows() if pd.notna(row.get('nome'))}
    
    # Mapeamento normalizado: nome sem acentos, minúsculo, sem espaços extras -> (id, nome_original)
    norm_para_id_nome = {
        unidecode.unidecode(str(row['nome']).lower().strip()): (row['id'], row['nome'])
        for _, row in clientes.iterrows() if pd.notna(row.get('nome'))
    }
    
    return {'exato': nome_para_id, 'normalizado': norm_para_id_nome}

def find_client_id(cliente_nome, clientes_mapping):
    """
    Procura um cliente pelo nome usando diferentes estratégias de correspondência
    
    Args:
        cliente_nome: Nome do cliente para buscar
        clientes_mapping: Dicionário de mapeamento de nomes para IDs
        
    Returns:
        tuple: (id do cliente, nome exato encontrado) ou (None, None) se não encontrado
    """
    # Verificar se string cliente_nome é válida
    if not cliente_nome or not isinstance(cliente_nome, str):
        logger.warning(f"Nome de cliente inválido: {cliente_nome}")
        return None, None
        
    # Primeira tentativa: correspondência exata
    if cliente_nome in clientes_mapping['exato']:
        cliente_id = clientes_mapping['exato'][cliente_nome]
        return cliente_id, cliente_nome
        
    # Segunda tentativa: normalizar o nome (remover acentos, minúsculas, etc.)
    cliente_nome_norm = unidecode.unidecode(cliente_nome.lower().strip())
    if cliente_nome_norm in clientes_mapping['normalizado']:
        cliente_id, nome_original = clientes_mapping['normalizado'][cliente_nome_norm]
        return cliente_id, nome_original
        
    # Terceira tentativa: verificar se o nome fornecido contém ou está contido em algum cliente
    for nome_norm, (id_cliente, nome_orig) in clientes_mapping['normalizado'].items():
        if nome_norm in cliente_nome_norm or cliente_nome_norm in nome_norm:
            return id_cliente, nome_orig
            
    # Não encontrou correspondência
    return None, None

def try_read_csv_with_formats(arquivo):
    """Tenta ler um CSV com diferentes separadores e codificações"""
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
    separators = [';', ',', '\t']
    
    for encoding in encodings:
        for sep in separators:
            try:
                # Reset file pointer to beginning
                arquivo.seek(0)
                df = pd.read_csv(arquivo, sep=sep, encoding=encoding)
                
                # Verificar se o DataFrame tem pelo menos as colunas necessárias
                required_cols = ['cliente_nome', 'descricao', 'valor']
                if all(col in df.columns for col in required_cols):
                    logger.info(f"Arquivo lido com sucesso usando encoding={encoding}, sep={sep}")
                    return df
            except Exception as e:
                continue
    
    # Se chegou aqui, não conseguiu ler o arquivo com nenhuma combinação
    raise ValueError("Não foi possível ler o arquivo CSV. Verifique o formato e as colunas requeridas.")

def importar_propostas_retroativas(arquivo, debug_mode=False):
    """
    Importar propostas retroativas a partir de um arquivo CSV, mantendo as datas originais
    """
    if not arquivo:
        st.error("Por favor, selecione um arquivo para importar.")
        return
        
    st.info("Iniciando importação...")
    
    # Obter mapeamento de clientes
    clientes_mapping = get_clients_mapping()
    if not clientes_mapping.get('exato') and not clientes_mapping.get('normalizado'):
        st.error("Não há clientes cadastrados no sistema. Por favor, cadastre clientes primeiro.")
        return
        
    try:
        # Tentar ler o arquivo com diferentes formatos
        df = try_read_csv_with_formats(arquivo)
        
        # Exibir preview para debug
        if debug_mode:
            st.write("### Preview do arquivo")
            st.write(df.head())
            
        # Validar colunas obrigatórias
        required_cols = ['cliente_nome', 'descricao', 'valor']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Coluna obrigatória '{col}' não encontrada no arquivo.")
                return
        
        sucessos = 0
        erros = []
        
        # Criar barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Processar linha por linha
        for i, row in df.iterrows():
            try:
                # Atualizar progresso
                progress = (i + 1) / len(df)
                progress_bar.progress(progress)
                status_text.text(f"Processando linha {i+1} de {len(df)}...")
                
                # Verificar cliente
                cliente_nome = str(row['cliente_nome']).strip() if pd.notna(row.get('cliente_nome')) else None
                if not cliente_nome:
                    erros.append(f"Erro na linha {i+2}: Nome do cliente não fornecido.")
                    continue
                
                # Encontrar ID do cliente
                cliente_id, nome_encontrado = find_client_id(cliente_nome, clientes_mapping)
                if not cliente_id:
                    erros.append(f"Erro na linha {i+2}: Cliente '{cliente_nome}' não encontrado no sistema.")
                    continue
                
                # Processar valor
                valor_str = str(row.get('valor', '')) if pd.notna(row.get('valor')) else None
                valor = normalizar_valor_monetario(valor_str)
                if not valor:
                    erros.append(f"Erro na linha {i+2}: Valor inválido: '{valor_str}'.")
                    continue
                
                # Processar datas
                data_criacao = None
                if 'data_criacao' in row and pd.notna(row['data_criacao']):
                    try:
                        data_criacao = datetime.strptime(str(row['data_criacao']).strip(), '%d/%m/%Y')
                    except:
                        try:
                            # Tentar formato alternativo
                            data_criacao = pd.to_datetime(row['data_criacao']).to_pydatetime()
                        except:
                            erros.append(f"Erro na linha {i+2}: Formato de data_criacao inválido. Use DD/MM/AAAA.")
                            continue
                
                data_inicio = None
                if 'data_inicio' in row and pd.notna(row['data_inicio']):
                    try:
                        data_inicio = datetime.strptime(str(row['data_inicio']).strip(), '%d/%m/%Y')
                    except:
                        try:
                            # Tentar formato alternativo
                            data_inicio = pd.to_datetime(row['data_inicio']).to_pydatetime()
                        except:
                            erros.append(f"Erro na linha {i+2}: Formato de data_inicio inválido. Use DD/MM/AAAA.")
                            continue
                
                data_fim = None
                if 'data_fim' in row and pd.notna(row['data_fim']):
                    try:
                        data_fim = datetime.strptime(str(row['data_fim']).strip(), '%d/%m/%Y')
                    except:
                        try:
                            # Tentar formato alternativo
                            data_fim = pd.to_datetime(row['data_fim']).to_pydatetime()
                        except:
                            erros.append(f"Erro na linha {i+2}: Formato de data_fim inválido. Use DD/MM/AAAA.")
                            continue
                
                prazo_entrega = None
                if 'prazo_entrega' in row and pd.notna(row['prazo_entrega']):
                    prazo_entrega = str(row['prazo_entrega']).strip()
                
                # Processar campos opcionais
                descricao = str(row['descricao']).strip() if pd.notna(row.get('descricao')) else "Sem descrição"
                
                status = str(row.get('status', 'Em elaboração')).strip() if pd.notna(row.get('status')) else "Em elaboração"
                # Normalizar o status para os valores aceitos no sistema
                status_map = {
                    'em elaboracao': 'Em elaboração',
                    'em elaboração': 'Em elaboração',
                    'elaboracao': 'Em elaboração',
                    'elaboração': 'Em elaboração',
                    'em execucao': 'Em execução',
                    'em execução': 'Em execução',
                    'execucao': 'Em execução',
                    'execução': 'Em execução',
                    'finalizada': 'Finalizada',
                    'finalizado': 'Finalizada',
                    'recusada': 'Recusada',
                    'recusado': 'Recusada',
                    'cancelada': 'Recusada',
                    'cancelado': 'Recusada'
                }
                status_norm = status.lower().strip()
                if status_norm in status_map:
                    status = status_map[status_norm]
                
                tipo_proposta = str(row.get('tipo_proposta', '')).strip() if pd.notna(row.get('tipo_proposta')) else None
                
                # Preparar dados para adicionar proposta
                proposta_data = {
                    'cliente_id': cliente_id,
                    'descricao': descricao,
                    'valor': valor,
                    'status': status
                }
                
                # Adicionar campos opcionais se existirem
                if tipo_proposta:
                    proposta_data['tipo_proposta'] = tipo_proposta
                if data_inicio:
                    proposta_data['data_inicio'] = data_inicio
                if data_fim:
                    proposta_data['data_fim'] = data_fim
                if prazo_entrega:
                    proposta_data['prazo_entrega'] = prazo_entrega
                if data_criacao:
                    proposta_data['data_criacao'] = data_criacao
                
                # Adicionar proposta retroativa (usamos add_proposta_retroativa que respeita a data_criacao)
                if debug_mode:
                    st.write(f"Adicionando proposta: {proposta_data}")
                
                # Adicionar proposta com data retroativa
                proposta_id = st.session_state.db.add_proposta_retroativa(**proposta_data)
                
                if proposta_id:
                    # Se a proposta estiver finalizada, também finalizar no sistema
                    if status == 'Finalizada':
                        st.session_state.db.finalizar_proposta(proposta_id)
                        
                    sucessos += 1
                    if debug_mode:
                        st.success(f"Proposta {proposta_id} adicionada com sucesso para cliente {nome_encontrado}")
                else:
                    erros.append(f"Erro ao adicionar proposta na linha {i+2}: não foi possível criar o registro.")
                    
            except Exception as e:
                erros.append(f"Erro na linha {i+2}: {str(e)}")
                if debug_mode:
                    st.error(f"Erro na linha {i+2}: {str(e)}")
                    st.error(traceback.format_exc())
        
        # Exibir resultados
        if sucessos > 0:
            st.success(f"{sucessos} propostas importadas com sucesso!")
        
        if erros:
            st.error(f"Erros encontrados: {len(erros)}")
            for erro in erros:
                st.write(f"- {erro}")
        
        return sucessos, erros
        
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        st.error(traceback.format_exc())
        return 0, [str(e)]

# Interface principal
st.write("### Importar Propostas Retroativas")
arquivo = st.file_uploader("Selecione o arquivo CSV com as propostas", type=["csv"])

col1, col2 = st.columns(2)
with col1:
    debug_mode = st.checkbox("Modo debug (exibir detalhes)", value=False)

with col2:
    # Modo avançado permite importar propostas para clientes específicos por ID
    usar_cliente_id = st.checkbox("Usar ID do cliente em vez do nome", value=False, help="Para importação avançada")

if arquivo:
    if st.button("📥 Importar Propostas Retroativas"):
        with st.spinner("Importando..."):
            sucessos, erros = importar_propostas_retroativas(arquivo, debug_mode)

# Adicionar função ao banco de dados
# Função para adicionar proposta retroativa
def add_proposta_retroativa_to_db():
    """
    Adiciona o método add_proposta_retroativa ao objeto Database na session_state
    """
    if hasattr(st.session_state.db, 'add_proposta_retroativa'):
        return  # Função já existe
        
    # Método para adicionar ao objeto Database
    def add_proposta_retroativa(self, cliente_id, descricao, valor, status="Em elaboração", 
                            tipo_proposta=None, data_inicio=None, data_fim=None, 
                            prazo_entrega=None, data_criacao=None):
        """
        Adiciona uma proposta com uma data de criação específica (retroativa)
        """
        def query():
            from sqlalchemy import text
            from models.models import Proposta
            
            proposta = Proposta(
                cliente_id=cliente_id,
                descricao=descricao,
                valor=valor,
                status=status,
                tipo_proposta=tipo_proposta,
                data_inicio=data_inicio,
                data_fim=data_fim,
                prazo_entrega=prazo_entrega
            )
            
            # Adicionar o usuário atual como proprietário
            if hasattr(self, 'usuario_id') and self.usuario_id:
                proposta.usuario_id = self.usuario_id
            
            self.session.add(proposta)
            self.session.flush()  # Para obter o ID
            
            # Se uma data de criação foi especificada, atualizamos diretamente
            if data_criacao:
                # Usar SQL direto para atualizar o timestamp
                sql = text(f"""
                    UPDATE propostas
                    SET data_criacao = :data_criacao
                    WHERE id = :id
                """)
                
                self.session.execute(sql, {
                    "data_criacao": data_criacao,
                    "id": proposta.id
                })
            
            self.session.commit()
            return proposta.id
            
        return self._safe_query(query)
        
    # Adicionar o método à classe Database na session_state
    import types
    st.session_state.db.add_proposta_retroativa = types.MethodType(add_proposta_retroativa, st.session_state.db)

# Verificar se precisamos adicionar o método ao Database
add_proposta_retroativa_to_db()