import streamlit as st
import pandas as pd
import sys
import os
import logging
import io
from utils.database import Database
from utils.importador import importar_cadastros, try_read_csv

# Configurar logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger('teste_importacao')

st.title("Teste de Importação de Fornecedores")

# Inicializar banco de dados
db = Database()
st.session_state['db'] = db

# Criar um exemplo de CSV na memória
fornecedor_data = """descricao;telefone;categoria;endereco;pix;observacao
Fornecedor Teste 1;(11) 99999-9999;Produtos;Rua Teste, 123;pix@teste.com;Observação teste
Fornecedor Teste 2;(21) 88888-8888;Serviços;Av. Exemplo, 456;chave2@teste.com;Outra observação
"""

# Carregando o CSV para o buffer de memória
fornecedor_file = io.StringIO(fornecedor_data)
st.write("### Dados para importação:")
df = pd.read_csv(fornecedor_file, sep=';')
st.dataframe(df)

# Resetar o buffer
fornecedor_file.seek(0)

st.write("### Log de importação detalhado:")

if st.button("Testar Importação"):
    try:
        buffer = io.BytesIO(fornecedor_file.read().encode('utf-8'))
        
        st.info("1. Tentando ler o arquivo")
        try:
            df = try_read_csv(buffer)
            st.success(f"Leitura bem sucedida. Dimensões: {df.shape}")
            st.write(df.head())
        except Exception as e:
            st.error(f"Erro na leitura: {str(e)}")
            
        buffer.seek(0)
        
        st.info("2. Executando importação")
        try:
            sucesso, mensagem = importar_cadastros(buffer, "Fornecedor", db)
            if sucesso:
                st.success(f"Importação bem sucedida: {mensagem}")
            else:
                st.error(f"Falha na importação: {mensagem}")
        except Exception as e:
            st.error(f"Exceção durante importação: {str(e)}")
            
        st.info("3. Verificando fornecedores no banco")
        try:
            fornecedores = db.get_fornecedores()
            st.write(fornecedores)
        except Exception as e:
            st.error(f"Erro ao consultar fornecedores: {str(e)}")
            
    except Exception as e:
        st.error(f"Erro geral: {str(e)}")
        
st.write("---")
st.subheader("Verificação do Modelo de Fornecedor")

try:
    # Verificar a definição da classe Fornecedor
    from utils.database import Fornecedor
    
    st.write(f"Campos da classe Fornecedor:")
    fields = [c.name for c in Fornecedor.__table__.columns]
    st.write(fields)
    
    # Verificar a assinatura da função add_fornecedor
    import inspect
    from utils.database import Database
    
    sig = inspect.signature(Database.add_fornecedor)
    st.write("Parâmetros de add_fornecedor:")
    st.write(list(sig.parameters.keys()))
    
except Exception as e:
    st.error(f"Erro ao analisar modelo: {str(e)}")