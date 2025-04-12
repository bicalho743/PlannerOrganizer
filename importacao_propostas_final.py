import streamlit as st
import pandas as pd
import datetime
import logging
import io
import re
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

st.set_page_config(page_title="Importação de Propostas", page_icon="📋", layout="wide")

st.title("📊 Importação de Propostas")
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
    modelo_path = 'template_proposta.csv'
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

# Função para normalizar valor monetário de forma super robusta
def normalizar_valor_monetario(valor_str):
    """
    Normaliza um valor monetário brasileiro para float
    
    Args:
        valor_str: String com o valor monetário
    
    Returns:
        float: Valor convertido para float
    """
    if pd.isna(valor_str):
        return None
        
    # Converter para string
    valor_str = str(valor_str).strip()
    
    # Remover símbolos de moeda e caracteres não numéricos
    valor_str = re.sub(r'[R$\s]', '', valor_str)
    
    # Tratar separadores
    if ',' in valor_str and '.' in valor_str:
        # Verificar se é formato brasileiro (1.234,56) ou americano (1,234.56)
        if valor_str.find('.') < valor_str.find(','):
            # Formato BR: remover pontos e substituir vírgula por ponto
            valor_str = valor_str.replace('.', '').replace(',', '.')
        else:
            # Formato US: remover vírgulas
            valor_str = valor_str.replace(',', '')
    else:
        # Se tem só vírgula, assume que é decimal (BR)
        valor_str = valor_str.replace(',', '.')
    
    # Lidar com múltiplos pontos (caso exista)
    partes = valor_str.split('.')
    if len(partes) > 2:
        # Reconstituir com apenas um ponto decimal
        valor_str = ''.join(partes[:-1]) + '.' + partes[-1]
    
    # Verificar se há apenas caracteres válidos
    if not re.match(r'^[0-9.]+$', valor_str):
        # Filtrar apenas números e um ponto
        apenas_numeros = ''.join([c for c in valor_str if c.isdigit() or c == '.'])
        # Garantir apenas um ponto decimal
        partes = apenas_numeros.split('.')
        if len(partes) > 2:
            apenas_numeros = ''.join(partes[:-1]) + '.' + partes[-1]
        valor_str = apenas_numeros
    
    # Converter para float
    try:
        valor = float(valor_str)
        return valor
    except ValueError:
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
        
        # Informação detalhada sobre o arquivo
        st.info(f"Arquivo contém {len(df)} registros e {len(df.columns)} colunas.")
        
        # Processar cada linha
        sucessos = 0
        erros = []
        
        # Barra de progresso
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        total_rows = len(df)
        
        # Mostrar detalhes para debug
        with st.expander("Ver detalhes de processamento"):
            st.write("Processamento detalhado de cada linha:")
            
            debug_container = st.container()
            
            # Criar área para detalhes de processamento
            debug_text = st.empty()
            debug_info = []
        
        for idx, row in df.iterrows():
            try:
                # Atualizar progresso
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"Processando linha {idx+1} de {total_rows}...")
                
                linha_info = []
                linha_info.append(f"**Linha {idx+2}:** Processando...")
                
                # 1. Validar e obter cliente
                try:
                    cliente_nome = str(row['cliente_nome']).strip()
                    linha_info.append(f"- Nome do cliente: '{cliente_nome}'")
                    
                    if not cliente_nome:
                        msg_erro = f"Nome do cliente vazio na linha {idx+2}"
                        linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                        erros.append(msg_erro)
                        continue
                    
                    # Buscar cliente por nome
                    cliente_id = encontrar_cliente_id(cliente_nome)
                    if cliente_id is None:
                        msg_erro = f"Cliente '{cliente_nome}' não encontrado na linha {idx+2}"
                        linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                        erros.append(msg_erro)
                        continue
                        
                    linha_info.append(f"  - ✅ Cliente encontrado com ID: {cliente_id}")
                    
                except Exception as e:
                    msg_erro = f"Erro ao processar cliente na linha {idx+2}: {str(e)}"
                    linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                    erros.append(msg_erro)
                    continue
                
                # 2. Validar descrição
                try:
                    descricao = str(row['descricao']).strip()
                    linha_info.append(f"- Descrição: '{descricao}'")
                    
                    if not descricao:
                        msg_erro = f"Descrição vazia na linha {idx+2}"
                        linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                        erros.append(msg_erro)
                        continue
                        
                    linha_info.append(f"  - ✅ Descrição válida")
                    
                except Exception as e:
                    msg_erro = f"Erro ao processar descrição na linha {idx+2}: {str(e)}"
                    linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                    erros.append(msg_erro)
                    continue
                
                # 3. Processar valor (convertendo formato brasileiro)
                try:
                    valor_str = str(row['valor']).strip()
                    linha_info.append(f"- Valor original: '{valor_str}'")
                    
                    # Converter com a função robusta
                    valor = normalizar_valor_monetario(valor_str)
                    
                    if valor is None:
                        msg_erro = f"Valor não numérico na linha {idx+2}"
                        linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                        erros.append(msg_erro)
                        continue
                        
                    if valor <= 0:
                        msg_erro = f"Valor inválido (deve ser maior que zero) na linha {idx+2}"
                        linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                        erros.append(msg_erro)
                        continue
                        
                    linha_info.append(f"  - ✅ Valor convertido: {valor}")
                    
                except Exception as e:
                    msg_erro = f"Erro ao processar valor na linha {idx+2}: {str(e)}"
                    linha_info.append(f"  - ❌ ERRO: {msg_erro}")
                    erros.append(msg_erro)
                    continue
                
                # 4. Processar campos opcionais
                # Status
                status = 'Aberta'  # padrão
                if 'status' in row and pd.notna(row['status']):
                    status_valor = str(row['status']).strip()
                    if status_valor.lower() in ['aberta', 'fechada', 'recusada']:
                        status = status_valor.capitalize()
                
                linha_info.append(f"- Status: '{status}'")
                
                # Tipo de proposta
                tipo_proposta = None
                if 'tipo_proposta' in row and pd.notna(row['tipo_proposta']):
                    tipo_proposta = str(row['tipo_proposta']).strip()
                
                linha_info.append(f"- Tipo de proposta: '{tipo_proposta}'")
                
                # Datas
                data_inicio = None
                data_fim = None
                prazo_entrega = None
                
                # Processar data_inicio
                if 'data_inicio' in row and pd.notna(row['data_inicio']):
                    try:
                        data_inicio = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                        linha_info.append(f"- Data início: {data_inicio}")
                    except:
                        linha_info.append("- Data início: formato inválido, usando None")
                
                # Processar data_fim
                if 'data_fim' in row and pd.notna(row['data_fim']):
                    try:
                        data_fim = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                        linha_info.append(f"- Data fim: {data_fim}")
                    except:
                        linha_info.append("- Data fim: formato inválido, usando None")
                
                # Processar prazo_entrega
                if 'prazo_entrega' in row and pd.notna(row['prazo_entrega']):
                    try:
                        prazo_entrega = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                        linha_info.append(f"- Prazo entrega: {prazo_entrega}")
                    except:
                        linha_info.append("- Prazo entrega: formato inválido, usando None")
                
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
                    linha_info.append(f"- ✅ Proposta adicionada com sucesso!")
                except Exception as e:
                    msg_erro = f"Erro ao salvar proposta na linha {idx+2}: {str(e)}"
                    linha_info.append(f"- ❌ ERRO: {msg_erro}")
                    erros.append(msg_erro)
                    continue
                    
            except Exception as e:
                msg_erro = f"Erro ao processar linha {idx+2}: {str(e)}"
                linha_info.append(f"- ❌ ERRO: {msg_erro}")
                erros.append(msg_erro)
                continue
            finally:
                # Adicionar informações da linha ao log de debug
                debug_info.append("<br>".join(linha_info))
                
                # Atualizar área de debug
                debug_text.markdown("<br><br>".join(debug_info), unsafe_allow_html=True)
        
        # Limpar barra de progresso
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if sucessos > 0:
            st.success(f"{sucessos} propostas importadas com sucesso!")
        
        if erros:
            st.error(f"{len(erros)} erros encontrados:")
            for i, erro in enumerate(erros[:20]):  # Mostrar até 20 primeiros erros
                st.error(f"{i+1}. {erro}")
            
            if len(erros) > 20:
                st.warning(f"... e mais {len(erros) - 20} erros. Verifique o log para detalhes.")
        
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
    file_name="template_proposta.csv",
    mime="text/csv"
)

# Importar arquivo
st.subheader("2. Importar Propostas")

st.write("""
### ⚠️ Dicas para corrigir erros comuns:

1. **Valores monetários**: 
   - Use o formato brasileiro: 1.500,00 ou 1500,00 (vírgula como separador decimal)
   - Não use 1.500.00 (com dois pontos)
   - A ferramenta tentará corrigir automaticamente, mas o formato correto garante sucesso

2. **Nomes de clientes**:
   - Verifique se os clientes existem no sistema
   - A busca vai tentar encontrar o cliente mesmo com diferenças em acentos, mas o nome deve ser semelhante

3. **Separadores do CSV**:
   - O arquivo deve usar ponto-e-vírgula (;) como separador
   - Certifique-se de que não há colunas extras ou faltantes
""")

arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

if arquivo:
    st.write("---")
    if st.button("🔄 Importar Propostas", type="primary"):
        with st.spinner("Importando propostas..."):
            if importar_propostas(arquivo):
                st.balloons()
            else:
                st.error("A importação não foi concluída com sucesso.")