import streamlit as st
import pandas as pd
import datetime
import logging
import io
import traceback
import unidecode
import sys
import os
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para poder importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import Database

st.set_page_config(page_title="Debug Importação de Propostas", page_icon="🔍", layout="wide")

st.title("🔍 Debug Importação de Propostas")
st.write("Ferramenta para debugar problemas de importação de propostas.")

# Inicializar estado da sessão para armazenar conexão ao banco de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Função para encontrar cliente pelo nome - com mais detalhes de debug
def encontrar_cliente_id(nome_cliente, debug=False):
    """
    Procura um cliente pelo nome no banco de dados com mais informações de debug
    
    Args:
        nome_cliente: Nome do cliente para buscar
        debug: Se True, exibe informações de debug
        
    Returns:
        tuple: (ID do cliente, informações de debug)
    """
    db = st.session_state.db
    clientes = db.get_clientes()
    info_debug = []
    
    if clientes.empty:
        return None, ["Não há clientes cadastrados no sistema"]
    
    # Exibir total de clientes para debug
    info_debug.append(f"Total de clientes no banco: {len(clientes)}")
    
    # 1. Busca direta exata
    info_debug.append(f"Tentando busca exata para '{nome_cliente}'")
    cliente = clientes[clientes['nome'] == nome_cliente]
    if not cliente.empty:
        cliente_id = int(cliente['id'].iloc[0])
        info_debug.append(f"Cliente encontrado por busca exata com ID: {cliente_id}")
        return cliente_id, info_debug
    
    # 2. Busca normalizada (sem acentos, minúsculas)
    nome_normalizado = unidecode.unidecode(nome_cliente.lower())
    info_debug.append(f"Tentando busca normalizada para '{nome_normalizado}'")
    
    for _, c in clientes.iterrows():
        nome_db = str(c['nome'])
        nome_db_norm = unidecode.unidecode(nome_db.lower())
        if nome_normalizado == nome_db_norm:
            cliente_id = int(c['id'])
            info_debug.append(f"Cliente encontrado por busca normalizada: '{nome_db}' (ID: {cliente_id})")
            return cliente_id, info_debug
    
    # 3. Busca por substrings
    info_debug.append("Tentando busca por substring")
    for _, c in clientes.iterrows():
        nome_db = str(c['nome'])
        nome_db_norm = unidecode.unidecode(nome_db.lower())
        if nome_normalizado in nome_db_norm or nome_db_norm in nome_normalizado:
            cliente_id = int(c['id'])
            info_debug.append(f"Cliente encontrado por substring: '{nome_db}' (ID: {cliente_id})")
            return cliente_id, info_debug
            
    # Se chegou aqui, não encontrou o cliente
    info_debug.append(f"Cliente '{nome_cliente}' não encontrado com nenhuma estratégia")
    
    # Mostrar os primeiros 5 clientes do banco para debug
    info_debug.append("Primeiros clientes no banco (para referência):")
    for i, (_, c) in enumerate(clientes.head(5).iterrows()):
        info_debug.append(f"  - {c['nome']} (ID: {c['id']})")
    
    return None, info_debug

# Função para normalizar valor monetário
def normalizar_valor_monetario(valor_str, debug=False):
    """
    Normaliza um valor monetário no formato brasileiro para float
    
    Args:
        valor_str: String com o valor monetário
        debug: Se True, exibe informações de debug
    
    Returns:
        tuple: (valor como float, informações de debug)
    """
    info_debug = []
    info_debug.append(f"Valor original: '{valor_str}'")
    
    try:
        # Converter para string caso não seja
        valor_str = str(valor_str).strip()
        info_debug.append(f"Valor após strip: '{valor_str}'")
        
        # Remover símbolo de moeda
        valor_str = re.sub(r'R\$', '', valor_str)
        info_debug.append(f"Valor sem símbolo de moeda: '{valor_str}'")
        
        # Remover espaços
        valor_str = valor_str.replace(' ', '')
        info_debug.append(f"Valor sem espaços: '{valor_str}'")
        
        # Tratar diferentes formatos de números (1.234,56 ou 1,234.56)
        # Para valores acima de mil com separador de milhar
        if '.' in valor_str and ',' in valor_str:
            # Verificar qual vem primeiro
            ponto_pos = valor_str.find('.')
            virgula_pos = valor_str.find(',')
            
            if ponto_pos < virgula_pos:  # formato 1.234,56 (BR)
                valor_str = valor_str.replace('.', '')  # remove pontos (separadores de milhar)
                valor_str = valor_str.replace(',', '.')  # substitui vírgula por ponto
            else:  # formato 1,234.56 (US)
                valor_str = valor_str.replace(',', '')  # remove vírgulas (separadores de milhar)
        else:
            # Para valores abaixo de mil ou sem separador de milhar
            valor_str = valor_str.replace(',', '.')  # troca vírgula por ponto
            
        info_debug.append(f"Valor formatado para parsing: '{valor_str}'")
        
        # Extrair apenas dígitos e um único ponto decimal (se houver)
        # Isso lida com casos como "1.234" que pode ser interpretado como 1234.0 e não 1.234
        num_parts = valor_str.split('.')
        if len(num_parts) > 2:
            # Se tem mais de um ponto, reconstrói com apenas o último como decimal
            valor_int = ''.join(num_parts[:-1])
            valor_str = valor_int + '.' + num_parts[-1]
            info_debug.append(f"Reconstruído com só um ponto decimal: '{valor_str}'")
        
        # Converter para float
        valor = float(valor_str)
        
        info_debug.append(f"Valor convertido para float: {valor}")
        
        # Validar o resultado
        if valor <= 0:
            info_debug.append("Erro: Valor menor ou igual a zero")
            return None, info_debug
            
        return valor, info_debug
        
    except (ValueError, TypeError) as e:
        info_debug.append(f"Erro de conversão: {str(e)}")
        return None, info_debug

def analisar_arquivo_csv(arquivo, num_linhas=5):
    """
    Analisa um arquivo CSV e mostra informações detalhadas sobre ele
    
    Args:
        arquivo: Arquivo CSV para análise
        num_linhas: Número de linhas para analisar
    
    Returns:
        dict: Informações sobre o arquivo
    """
    resultados = {}
    
    # Identificar encoding e separador
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
    separadores = [';', ',', '\t']
    
    melhor_df = None
    melhor_encoding = None
    melhor_separador = None
    max_colunas = 0
    
    for encoding in encodings:
        for sep in separadores:
            try:
                arquivo.seek(0)
                df = pd.read_csv(arquivo, sep=sep, encoding=encoding, nrows=num_linhas)
                
                # Selecionar o DataFrame com mais colunas
                if df.shape[1] > max_colunas:
                    max_colunas = df.shape[1]
                    melhor_df = df
                    melhor_encoding = encoding
                    melhor_separador = sep
            except Exception as e:
                continue
    
    if melhor_df is None:
        return {"erro": "Não foi possível ler o arquivo com nenhuma combinação de encoding/separador"}
    
    # Analisar encoding e separador
    resultados["encoding"] = melhor_encoding
    resultados["separador"] = melhor_separador
    resultados["num_colunas"] = melhor_df.shape[1]
    resultados["num_linhas_total"] = None  # Vai ser preenchido depois
    
    # Analisar as colunas
    resultados["colunas"] = list(melhor_df.columns)
    
    # Analisar amostra do conteúdo
    amostra = []
    for idx, row in melhor_df.iterrows():
        linha = {}
        for col in melhor_df.columns:
            valor = row[col]
            linha[col] = str(valor)
        amostra.append(linha)
    
    resultados["amostra"] = amostra
    
    # Contar linhas totais do arquivo
    arquivo.seek(0)
    num_linhas_total = sum(1 for line in arquivo if line)
    resultados["num_linhas_total"] = num_linhas_total
    
    # Resetar para começar do início
    arquivo.seek(0)
    
    return resultados

def debugar_proposta(row, idx):
    """
    Analisa uma linha de proposta para encontrar problemas
    
    Args:
        row: Linha de dados da proposta
        idx: Índice da linha (para relatórios)
        
    Returns:
        dict: Resultados da análise
    """
    resultados = {
        "linha": idx + 2,  # +2 porque idx começa em 0 e pulamos o cabeçalho
        "dados_originais": row.to_dict(),
        "etapas": []
    }
    
    # 1. Validar nome do cliente
    try:
        cliente_nome = str(row['cliente_nome']).strip()
        resultados["etapas"].append({
            "etapa": "Validação do nome do cliente", 
            "valor": cliente_nome,
            "status": "OK" if cliente_nome else "ERRO",
            "mensagem": "Nome do cliente extraído com sucesso" if cliente_nome else "Nome do cliente vazio"
        })
        
        if not cliente_nome:
            resultados["erro_final"] = "Nome do cliente vazio"
            return resultados
            
        # Buscar cliente por nome
        cliente_id, info_debug = encontrar_cliente_id(cliente_nome, debug=True)
        
        resultados["etapas"].append({
            "etapa": "Busca do cliente no banco", 
            "valor": cliente_id,
            "info_debug": info_debug,
            "status": "OK" if cliente_id is not None else "ERRO",
            "mensagem": f"Cliente encontrado com ID: {cliente_id}" if cliente_id is not None else "Cliente não encontrado"
        })
        
        if cliente_id is None:
            resultados["erro_final"] = f"Cliente '{cliente_nome}' não encontrado"
            return resultados
    except Exception as e:
        resultados["etapas"].append({
            "etapa": "Processamento do cliente", 
            "status": "ERRO",
            "mensagem": f"Erro ao processar cliente: {str(e)}",
            "traceback": traceback.format_exc()
        })
        resultados["erro_final"] = f"Erro ao processar cliente: {str(e)}"
        return resultados
    
    # 2. Validar descrição
    try:
        descricao = str(row['descricao']).strip()
        resultados["etapas"].append({
            "etapa": "Validação da descrição", 
            "valor": descricao,
            "status": "OK" if descricao else "ERRO",
            "mensagem": "Descrição extraída com sucesso" if descricao else "Descrição vazia"
        })
        
        if not descricao:
            resultados["erro_final"] = "Descrição vazia"
            return resultados
    except Exception as e:
        resultados["etapas"].append({
            "etapa": "Processamento da descrição", 
            "status": "ERRO",
            "mensagem": f"Erro ao processar descrição: {str(e)}",
            "traceback": traceback.format_exc()
        })
        resultados["erro_final"] = f"Erro ao processar descrição: {str(e)}"
        return resultados
    
    # 3. Validar valor
    try:
        valor_str = str(row['valor']).strip()
        valor, info_debug = normalizar_valor_monetario(valor_str, debug=True)
        
        resultados["etapas"].append({
            "etapa": "Processamento do valor", 
            "valor_str": valor_str,
            "valor_convertido": valor,
            "info_debug": info_debug,
            "status": "OK" if valor is not None else "ERRO",
            "mensagem": f"Valor convertido com sucesso: {valor}" if valor is not None else "Valor não numérico"
        })
        
        if valor is None:
            resultados["erro_final"] = "Valor não numérico ou inválido"
            return resultados
    except Exception as e:
        resultados["etapas"].append({
            "etapa": "Processamento do valor", 
            "status": "ERRO",
            "mensagem": f"Erro ao processar valor: {str(e)}",
            "traceback": traceback.format_exc()
        })
        resultados["erro_final"] = f"Erro ao processar valor: {str(e)}"
        return resultados
    
    # 4. Processar campos opcionais
    try:
        # Status
        status = 'Aberta'  # padrão
        if 'status' in row and pd.notna(row['status']):
            status_valor = str(row['status']).strip()
            if status_valor.lower() in ['aberta', 'fechada', 'recusada']:
                status = status_valor.capitalize()
                
        resultados["etapas"].append({
            "etapa": "Processamento do status", 
            "valor": status,
            "status": "OK",
            "mensagem": f"Status processado: {status}"
        })
        
        # Tipo de proposta
        tipo_proposta = None
        if 'tipo_proposta' in row and pd.notna(row['tipo_proposta']):
            tipo_proposta = str(row['tipo_proposta']).strip()
            
        resultados["etapas"].append({
            "etapa": "Processamento do tipo de proposta", 
            "valor": tipo_proposta,
            "status": "OK",
            "mensagem": f"Tipo de proposta processado: {tipo_proposta}"
        })
        
        # Datas
        datas = {}
        for campo_data in ['data_inicio', 'data_fim', 'prazo_entrega']:
            data_valor = None
            if campo_data in row and pd.notna(row[campo_data]):
                try:
                    data_str = str(row[campo_data])
                    data_valor = pd.to_datetime(data_str, format='%d/%m/%Y').date()
                    datas[campo_data] = data_valor
                    status_data = "OK"
                    msg_data = f"Data processada: {data_valor}"
                except Exception as e:
                    status_data = "AVISO"
                    msg_data = f"Erro no formato da data ({str(e)}), será usado o valor padrão None"
            else:
                status_data = "AVISO"
                msg_data = "Campo não presente ou vazio, será usado o valor padrão None"
                
            resultados["etapas"].append({
                "etapa": f"Processamento de {campo_data}", 
                "valor": str(data_valor) if data_valor is not None else "None",
                "status": status_data,
                "mensagem": msg_data
            })
    except Exception as e:
        resultados["etapas"].append({
            "etapa": "Processamento de campos opcionais", 
            "status": "ERRO",
            "mensagem": f"Erro ao processar campos opcionais: {str(e)}",
            "traceback": traceback.format_exc()
        })
        resultados["erro_final"] = f"Erro ao processar campos opcionais: {str(e)}"
        return resultados
    
    # Se chegou até aqui, está tudo ok
    resultados["sucesso"] = True
    resultados["proposta"] = {
        "cliente_id": cliente_id,
        "cliente_nome": cliente_nome,
        "descricao": descricao,
        "valor": valor,
        "status": status,
        "tipo_proposta": tipo_proposta
    }
    
    # Adicionar datas se existirem
    for campo_data in ['data_inicio', 'data_fim', 'prazo_entrega']:
        if campo_data in datas:
            resultados["proposta"][campo_data] = datas[campo_data]
    
    return resultados

def debugar_propostas(arquivo, num_linhas=5):
    """
    Analisa um arquivo de propostas para identificar problemas
    
    Args:
        arquivo: Arquivo CSV para análise
        num_linhas: Número de linhas para analisar
        
    Returns:
        dict: Resultados da análise
    """
    resultados = {}
    
    # Primeiro, analisar o arquivo CSV
    info_arquivo = analisar_arquivo_csv(arquivo)
    resultados["info_arquivo"] = info_arquivo
    
    if "erro" in info_arquivo:
        resultados["erro"] = info_arquivo["erro"]
        return resultados
    
    # Agora, ler o arquivo completo para análise
    arquivo.seek(0)
    try:
        df = pd.read_csv(
            arquivo, 
            sep=info_arquivo["separador"], 
            encoding=info_arquivo["encoding"]
        )
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            resultados["erro"] = f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
            resultados["colunas_presentes"] = list(df.columns)
            resultados["colunas_faltantes"] = colunas_faltantes
            return resultados
            
        # Pegar apenas as primeiras linhas para debug
        df_debug = df.head(num_linhas)
        
        # Processar cada linha
        analises = []
        
        for idx, row in df_debug.iterrows():
            analise = debugar_proposta(row, idx)
            analises.append(analise)
            
        resultados["analises"] = analises
        
        # Contagens
        sucessos = sum(1 for a in analises if "sucesso" in a and a["sucesso"])
        erros = sum(1 for a in analises if "erro_final" in a)
        
        resultados["estatisticas"] = {
            "total_analisado": len(analises),
            "sucessos": sucessos,
            "erros": erros
        }
        
        return resultados
        
    except Exception as e:
        resultados["erro"] = f"Erro ao processar arquivo: {str(e)}"
        resultados["traceback"] = traceback.format_exc()
        return resultados

# Interface principal
st.subheader("Ferramenta de Debug")

# Upload do arquivo
arquivo = st.file_uploader("Selecione o arquivo CSV para debug", type=['csv'])

if arquivo:
    st.write("---")
    
    # Selecionar número de linhas para analisar
    num_linhas = st.slider("Número de linhas para analisar", min_value=1, max_value=10, value=5)
    
    if st.button("🔍 Analisar Arquivo", type="primary"):
        with st.spinner("Analisando arquivo..."):
            resultados = debugar_propostas(arquivo, num_linhas=num_linhas)
            
            # Exibir resultados da análise
            st.write("## Resultados da Análise")
            
            # Informações gerais do arquivo
            st.subheader("Informações do Arquivo")
            if "erro" in resultados:
                st.error(resultados["erro"])
            else:
                info_arquivo = resultados["info_arquivo"]
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Encoding detectado", info_arquivo["encoding"])
                col2.metric("Separador detectado", repr(info_arquivo["separador"]))
                col3.metric("Número de colunas", info_arquivo["num_colunas"])
                
                st.write(f"**Colunas encontradas:** {', '.join(info_arquivo['colunas'])}")
                st.write(f"**Total de linhas no arquivo:** {info_arquivo['num_linhas_total']}")
                
                # Mostrar amostra do conteúdo
                st.subheader("Amostra do Conteúdo")
                st.dataframe(pd.DataFrame(info_arquivo["amostra"]))
                
                # Estatísticas da análise
                if "estatisticas" in resultados:
                    stats = resultados["estatisticas"]
                    st.subheader("Estatísticas da Análise")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total analisado", stats["total_analisado"])
                    col2.metric("Registros válidos", stats["sucessos"])
                    col3.metric("Registros com erros", stats["erros"])
                
                # Análise por linha
                st.subheader("Análise Detalhada por Linha")
                
                for i, analise in enumerate(resultados["analises"]):
                    with st.expander(f"Linha {analise['linha']} - " + 
                                    ("✅ OK" if "sucesso" in analise and analise["sucesso"] else 
                                    f"❌ ERRO: {analise.get('erro_final', 'Desconhecido')}")):
                        
                        # Dados originais
                        st.write("**Dados originais:**")
                        st.json(analise["dados_originais"])
                        
                        # Etapas de processamento
                        st.write("**Etapas de processamento:**")
                        for etapa in analise["etapas"]:
                            if etapa["status"] == "OK":
                                st.success(f"**{etapa['etapa']}**: {etapa['mensagem']}")
                            elif etapa["status"] == "AVISO":
                                st.warning(f"**{etapa['etapa']}**: {etapa['mensagem']}")
                            else:
                                st.error(f"**{etapa['etapa']}**: {etapa['mensagem']}")
                            
                            # Informações de debug
                            if "info_debug" in etapa:
                                st.write("**Informações de debug:**")
                                for info in etapa["info_debug"]:
                                    st.write(f"- {info}")
                            
                            # Traceback para erros
                            if "traceback" in etapa:
                                st.write("**Traceback do erro:**")
                                st.code(etapa["traceback"])
                        
                        # Resultado final
                        if "sucesso" in analise and analise["sucesso"]:
                            st.write("**Resultado final (proposta válida):**")
                            st.json(analise["proposta"])
                        else:
                            st.error(f"**Resultado final: Proposta inválida** - {analise.get('erro_final', 'Erro desconhecido')}")
                
                # Recomendações
                st.subheader("Recomendações")
                
                # Verificar os erros mais comuns
                erros = [a.get("erro_final") for a in resultados["analises"] if "erro_final" in a]
                if erros:
                    erros_unicos = {}
                    for erro in erros:
                        if erro in erros_unicos:
                            erros_unicos[erro] += 1
                        else:
                            erros_unicos[erro] = 1
                    
                    st.write("**Erros encontrados:**")
                    for erro, count in erros_unicos.items():
                        st.write(f"- {erro} ({count} ocorrências)")
                    
                    # Sugestões baseadas nos erros
                    st.write("**Sugestões para correção:**")
                    
                    if any("não numérico" in e for e in erros_unicos.keys()):
                        st.write("""
                        **Problema com valores monetários:**
                        - Verifique se todos os valores estão no formato brasileiro (ex: 1.500,00)
                        - Remova símbolos como R$ ou caracteres não numéricos
                        - Certifique-se de que não há espaços no campo de valor
                        """)
                    
                    if any("não encontrado" in e for e in erros_unicos.keys()):
                        st.write("""
                        **Problema com nomes de clientes:**
                        - Verifique se os clientes realmente existem no banco de dados
                        - Confira a grafia exata dos nomes (incluindo acentos e maiúsculas/minúsculas)
                        - Certifique-se de que não há espaços extras no início ou fim do nome
                        """)
                    
                    if any("vazi" in e.lower() for e in erros_unicos.keys()):
                        st.write("""
                        **Problema com campos vazios:**
                        - Preencha todos os campos obrigatórios: cliente_nome, descricao, valor
                        - Verifique se há células vazias no arquivo
                        """)
                else:
                    st.success("Não foram encontrados erros nas linhas analisadas!")
                    
                # Sugestões gerais
                st.write("""
                **Recomendações gerais:**
                1. Use o modelo de importação fornecido como base
                2. Certifique-se de que o arquivo esteja no formato CSV com separador ';'
                3. Use codificação UTF-8 para evitar problemas com caracteres especiais
                4. Valores monetários devem usar o formato brasileiro (ex: 1.500,00)
                5. Datas devem estar no formato DD/MM/AAAA
                6. Certifique-se de que todos os clientes existem no sistema antes de importar
                """)