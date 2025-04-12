import streamlit as st
import pandas as pd
import io
import logging
import traceback
from utils.database import Database
from utils.celebration import toggle_celebration

# Configurar o logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Título da página
st.title("📥 Importação de Clientes com ID")

# Inicializar banco de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
        st.success("Banco de dados conectado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        st.stop()

# Função para importar clientes
def importar_clientes_com_id(arquivo, db):
    try:
        # Detectar codificação e formato
        try:
            # Tentar diferentes codificações
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
            separadores = [';', ',', '\t']
            
            df = None
            for encoding in encodings:
                if df is not None:
                    break
                    
                for sep in separadores:
                    try:
                        arquivo.seek(0)
                        df = pd.read_csv(arquivo, sep=sep, encoding=encoding)
                        
                        # Verificar se o DataFrame tem pelo menos 1 linha e 2 colunas
                        if df.shape[0] > 0 and df.shape[1] > 1:
                            st.success(f"Arquivo lido com sucesso usando separador '{sep}' e codificação '{encoding}'")
                            break
                    except Exception as e:
                        continue
            
            if df is None or df.empty:
                return False, "Erro ao ler arquivo: arquivo vazio ou formato não suportado"
                
        except Exception as e:
            error_msg = f"Erro ao ler arquivo: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg
        
        # Verificar coluna id
        if 'id' not in df.columns:
            return False, "Erro: O arquivo deve conter uma coluna 'id'"
        
        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})
        
        # Estatísticas
        total_rows = len(df)
        sucessos = 0
        erros = []
        
        # Barra de progresso
        progress_bar = st.progress(0)
        st.write("### Log de Importação")
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                # Atualizar progresso
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                
                # Verificar ID
                cliente_id = None
                try:
                    if pd.notna(row['id']):
                        cliente_id = int(row['id'])
                    else:
                        erros.append(f"ID vazio na linha {idx + 2}")
                        continue
                except (ValueError, TypeError):
                    erros.append(f"ID inválido na linha {idx + 2}: {row['id']}")
                    continue
                
                # Verificar nome (obrigatório)
                nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                if not nome:
                    erros.append(f"Nome vazio na linha {idx + 2}")
                    continue
                
                # Preparar dados do cliente
                cliente_data = {
                    'id': cliente_id,
                    'nome': nome,
                    'telefone': str(row.get('telefone', '')).strip() if pd.notna(row.get('telefone')) else None,
                    'cpf': str(row.get('cpf', '')).strip() if pd.notna(row.get('cpf')) else None,
                    'email': str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                    'estado': str(row.get('estado', '')).strip() if pd.notna(row.get('estado')) else None,
                    'cidade': str(row.get('cidade', '')).strip() if pd.notna(row.get('cidade')) else None,
                    'bairro': str(row.get('bairro', '')).strip() if pd.notna(row.get('bairro')) else None,
                    'endereco': str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                    'data_aniversario': str(row.get('data_aniversario', '')).strip() if pd.notna(row.get('data_aniversario')) else None,
                    'origem_cliente': str(row.get('origem_cliente', 'Importação')).strip() if pd.notna(row.get('origem_cliente')) else 'Importação',
                    'observacoes': str(row.get('observacoes', '')).strip() if pd.notna(row.get('observacoes')) else None
                }
                
                # Remover valores None
                cliente_data = {k: v for k, v in cliente_data.items() if v is not None}
                
                # Adicionar cliente com ID específico
                db.add_cliente_with_id(**cliente_data)
                sucessos += 1
                st.write(f"✅ Cliente '{nome}' (ID: {cliente_id}) importado com sucesso")
                
            except Exception as e:
                erro_msg = f"Erro ao processar cliente na linha {idx + 2}: {str(e)}"
                erros.append(erro_msg)
                st.error(erro_msg)
                logger.error(f"{erro_msg}\n{traceback.format_exc()}")
                continue
        
        # Relatório final
        if sucessos > 0:
            mensagem = f"Importação concluída: {sucessos} clientes importados com sucesso!"
            if erros:
                mensagem += f" Erros encontrados: {len(erros)}"
                for erro in erros:
                    st.error(erro)
            return True, mensagem
        else:
            mensagem = "Nenhum cliente foi importado. Verifique os erros."
            if erros:
                for erro in erros:
                    st.error(erro)
            return False, mensagem
            
    except Exception as e:
        erro_msg = f"Erro durante a importação: {str(e)}"
        logger.error(f"{erro_msg}\n{traceback.format_exc()}")
        return False, erro_msg

# Instruções
st.write("""
## Instruções para Importação

1. Prepare um arquivo CSV com os seguintes campos:
   - `id` (obrigatório) - Número de identificação do cliente
   - `nome` (obrigatório) - Nome completo do cliente
   - `email` - E-mail do cliente
   - `telefone` - Número de telefone
   - `endereco` - Endereço completo
   - `cpf` - CPF do cliente
   - `data_aniversario` - Data de aniversário (formato: DD/MM ou DD/MMM)
   - `origem_cliente` - Como o cliente chegou até você
   - `estado` - Estado (UF)
   - `cidade` - Cidade
   - `bairro` - Bairro
   - `observacoes` - Observações gerais

2. Certifique-se de que cada cliente tenha um ID único

3. O separador pode ser vírgula (,) ou ponto-e-vírgula (;)
""")

# Download do template
st.download_button(
    label="📄 Baixar Template CSV",
    data=open("clientes_template.csv", "rb").read(),
    file_name="clientes_template.csv",
    mime="text/csv"
)

# Widget para upload de arquivo
st.write("## Carregar Arquivo")
arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

if arquivo:
    # Exibir prévia
    st.write("## Prévia do Arquivo")
    try:
        # Tentar ler com diferentes separadores
        try:
            df = pd.read_csv(arquivo, sep=';')
        except:
            try:
                arquivo.seek(0)
                df = pd.read_csv(arquivo, sep=',')
            except:
                arquivo.seek(0)
                df = pd.read_csv(arquivo)
        
        st.dataframe(df.head())
        
        # Processar importação
        if st.button("Iniciar Importação", type="primary"):
            with st.spinner("Importando clientes..."):
                sucesso, mensagem = importar_clientes_com_id(arquivo, st.session_state.db)
                if sucesso:
                    st.success(mensagem)
                    # Mostrar opção de celebração
                    if st.button("🎉 Celebrar", key="btn_celebrar"):
                        toggle_celebration(
                            task_name="Importação de Clientes",
                            custom_message="Clientes importados com sucesso!"
                        )
                else:
                    st.error(mensagem)
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {str(e)}")
else:
    st.info("Carregue um arquivo CSV para começar a importação.")