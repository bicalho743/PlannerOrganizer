import streamlit as st
import pandas as pd
import datetime
import logging
import io
import traceback
import unidecode
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para poder importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import Database

st.set_page_config(page_title="Importação de Propostas Simplificada", page_icon="📋", layout="wide")

st.title("📊 Importação de Propostas Simplificada")
st.write("Ferramenta para importação de propostas a partir de arquivo CSV.")

# Inicializar estado da sessão para armazenar conexão ao banco de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Criar modelo para download
def criar_modelo_csv():
    """Cria um modelo CSV para download"""
    dados = [
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
    ]
    df = pd.DataFrame(dados)
    
    # Salvar no sistema de arquivos
    modelo_path = 'modelo_propostas_para_importacao.csv'
    df.to_csv(modelo_path, index=False, sep=';')
    st.success(f"Modelo atualizado em {modelo_path}")
    
    # Retornar para download
    csv_bytes = df.to_csv(index=False, sep=';').encode('utf-8')
    return csv_bytes

# Função para encontrar cliente pelo nome
def encontrar_cliente_id(nome_cliente):
    """
    Procura um cliente pelo nome no banco de dados
    
    Args:
        nome_cliente: Nome do cliente para buscar
        
    Returns:
        int: ID do cliente encontrado ou None se não encontrado
    """
    db = st.session_state.db
    clientes = db.get_clientes()
    
    if clientes.empty:
        return None
    
    # 1. Busca direta exata
    cliente = clientes[clientes['nome'] == nome_cliente]
    if not cliente.empty:
        return int(cliente['id'].iloc[0])
    
    # 2. Busca normalizada (sem acentos, minúsculas)
    nome_normalizado = unidecode.unidecode(nome_cliente.lower())
    for _, c in clientes.iterrows():
        nome_db = str(c['nome'])
        nome_db_norm = unidecode.unidecode(nome_db.lower())
        if nome_normalizado == nome_db_norm:
            return int(c['id'])
    
    # 3. Busca por substrings
    for _, c in clientes.iterrows():
        nome_db = str(c['nome'])
        nome_db_norm = unidecode.unidecode(nome_db.lower())
        if nome_normalizado in nome_db_norm or nome_db_norm in nome_normalizado:
            return int(c['id'])
            
    return None

# Função principal de importação
def importar_propostas(arquivo):
    try:
        # Tentar diferentes formatações de CSV
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
        separadores = [';', ',', '\t']
        
        df = None
        for encoding in encodings:
            for sep in separadores:
                try:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=sep, encoding=encoding)
                    if df.shape[0] > 0 and df.shape[1] > 1:
                        st.success(f"Arquivo lido com sucesso usando separador '{sep}' e codificação '{encoding}'")
                        break
                except Exception as e:
                    continue
            if df is not None:
                break
        
        if df is None:
            st.error("Não foi possível ler o arquivo. Tente usar CSV com separador ponto-e-vírgula (;) e codificação UTF-8.")
            return False
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}")
            return False
        
        # Verificar se existem clientes no sistema
        db = st.session_state.db
        clientes = db.get_clientes()
        if clientes.empty:
            st.error("Não há clientes cadastrados no sistema. Importe clientes primeiro.")
            return False
        
        # Mostrar os primeiros registros
        st.write("Primeiras linhas do arquivo:")
        st.dataframe(df.head())
        
        # Processar cada linha
        sucessos = 0
        erros = []
        
        # Barra de progresso
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        total_rows = len(df)
        for idx, row in df.iterrows():
            try:
                # Atualizar progresso
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"Processando linha {idx+1} de {total_rows}...")
                
                # 1. Validar e obter cliente
                cliente_nome = str(row['cliente_nome']).strip()
                if not cliente_nome:
                    erros.append(f"Nome do cliente vazio na linha {idx+2}")
                    continue
                
                # Buscar cliente por nome
                cliente_id = encontrar_cliente_id(cliente_nome)
                if cliente_id is None:
                    erros.append(f"Cliente '{cliente_nome}' não encontrado na linha {idx+2}")
                    continue
                
                # 2. Validar descrição
                descricao = str(row['descricao']).strip()
                if not descricao:
                    erros.append(f"Descrição vazia na linha {idx+2}")
                    continue
                
                # 3. Processar valor (convertendo formato brasileiro)
                try:
                    valor_str = str(row['valor']).strip()
                    # Limpar formatação
                    valor_str = valor_str.replace('R$', '').replace(' ', '')
                    # Manter apenas dígitos, pontos e vírgulas
                    valor_str = ''.join(c for c in valor_str if c.isdigit() or c in '.,')
                    # Converter vírgula para ponto
                    valor_str = valor_str.replace(',', '.')
                    
                    # Converter para float
                    valor = float(valor_str)
                    if valor <= 0:
                        erros.append(f"Valor inválido (deve ser maior que zero) na linha {idx+2}")
                        continue
                except (ValueError, TypeError) as e:
                    erros.append(f"Valor não numérico na linha {idx+2}")
                    continue
                
                # 4. Processar campos opcionais
                # Status
                status = 'Aberta'  # padrão
                if 'status' in row and pd.notna(row['status']):
                    status_valor = str(row['status']).strip()
                    if status_valor.lower() in ['aberta', 'fechada', 'recusada']:
                        status = status_valor.capitalize()
                
                # Tipo de proposta
                tipo_proposta = None
                if 'tipo_proposta' in row and pd.notna(row['tipo_proposta']):
                    tipo_proposta = str(row['tipo_proposta']).strip()
                
                # Datas
                data_inicio = None
                data_fim = None
                prazo_entrega = None
                
                # Processar data_inicio
                if 'data_inicio' in row and pd.notna(row['data_inicio']):
                    try:
                        data_inicio = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                    except:
                        pass
                
                # Processar data_fim
                if 'data_fim' in row and pd.notna(row['data_fim']):
                    try:
                        data_fim = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                    except:
                        pass
                
                # Processar prazo_entrega
                if 'prazo_entrega' in row and pd.notna(row['prazo_entrega']):
                    try:
                        prazo_entrega = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                    except:
                        pass
                
                # 5. Adicionar a proposta ao banco de dados
                try:
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
                    erro_msg = f"Erro ao salvar proposta na linha {idx+2}: {str(e)}"
                    erros.append(erro_msg)
                    continue
                    
            except Exception as e:
                erro_msg = f"Erro ao processar linha {idx+2}: {str(e)}"
                erros.append(erro_msg)
                continue
        
        # Limpar barra de progresso
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if sucessos > 0:
            st.success(f"{sucessos} propostas importadas com sucesso!")
        
        if erros:
            st.error(f"{len(erros)} erros encontrados:")
            for erro in erros[:10]:  # Mostrar apenas os 10 primeiros erros
                st.error(f"- {erro}")
            
            if len(erros) > 10:
                st.warning(f"... e mais {len(erros) - 10} erros. Verifique o log para detalhes.")
        
        return sucessos > 0
        
    except Exception as e:
        traceback_str = traceback.format_exc()
        st.error(f"Erro na importação: {str(e)}")
        st.code(traceback_str)
        return False

# Criar e baixar modelo
st.subheader("1. Modelo para Importação")
st.info("""
O arquivo deve ter as seguintes colunas obrigatórias:
- **cliente_nome**: Nome do cliente (deve existir no sistema)
- **descricao**: Descrição da proposta 
- **valor**: Valor da proposta (formato brasileiro, ex: 1.500,00)

Colunas opcionais:
- **status**: Aberta, Fechada ou Recusada (padrão: Aberta)
- **tipo_proposta**: Tipo de proposta
- **data_inicio**: Data de início no formato DD/MM/AAAA
- **data_fim**: Data de fim no formato DD/MM/AAAA
- **prazo_entrega**: Prazo de entrega no formato DD/MM/AAAA
""")

modelo_csv = criar_modelo_csv()
st.download_button(
    label="📥 Baixar modelo CSV",
    data=modelo_csv,
    file_name="modelo_propostas_para_importacao.csv",
    mime="text/csv"
)

# Importar arquivo
st.subheader("2. Importar Propostas")
arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

if arquivo:
    st.write("---")
    if st.button("🔄 Importar Propostas", type="primary"):
        with st.spinner("Importando propostas..."):
            if importar_propostas(arquivo):
                st.balloons()
            else:
                st.error("A importação não foi concluída com sucesso.")