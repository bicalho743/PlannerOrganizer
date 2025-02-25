import streamlit as st
import pandas as pd
from utils.importador import importar_cadastros, testar_conexao_db
from datetime import datetime

def show():
    st.title("🧪 Teste de Importação")
    
    # Verificar estado da sessão
    st.write("### Estado da Sessão")
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return
    else:
        st.success("Conexão com banco de dados presente na sessão")
    
    # Testar conexão com o banco
    st.write("### Teste de Conexão")
    if not testar_conexao_db(st.session_state.db):
        st.error("Erro de conexão com o banco de dados")
        return
    else:
        st.success("Conexão com banco de dados OK")

    # Criar DataFrame de teste
    st.write("### Dados de Teste")
    dados_teste = {
        'nome': ['Cliente Teste 1', 'Cliente Teste 2'],
        'telefone': ['(11) 99999-9999', '(11) 88888-8888'],
        'email': ['teste1@email.com', 'teste2@email.com'],
        'tipo_conta': ['PF', 'PJ'],
        'data_aniversario': [datetime.now().date(), datetime.now().date()],
        'origem_cliente': ['Teste', 'Teste'],
        'cpf': ['123.456.789-00', None],
        'cnpj': [None, '12.345.678/0001-90'],
        'razao_social': [None, 'Empresa Teste LTDA']
    }
    
    df_teste = pd.DataFrame(dados_teste)
    st.write("Preview dos dados de teste:")
    st.dataframe(df_teste)

    # Botão para testar importação
    if st.button("Testar Importação", key="teste_importacao"):
        with st.spinner("Importando dados de teste..."):
            try:
                # Converter DataFrame para arquivo em memória
                import io
                buffer = io.StringIO()
                df_teste.to_csv(buffer, index=False)
                buffer.seek(0)
                
                # Criar arquivo fake para teste
                class FakeFile:
                    def __init__(self, buffer):
                        self.buffer = buffer
                        self.name = "teste.csv"
                    
                    def read(self):
                        return self.buffer.read()
                
                arquivo_teste = FakeFile(buffer)
                
                # Tentar importar
                sucesso, mensagem = importar_cadastros(arquivo_teste, "Cliente", st.session_state.db)
                
                if sucesso:
                    st.success(f"Teste realizado com sucesso!\n{mensagem}")
                    st.session_state['update_clientes'] = True
                else:
                    st.error(f"Erro no teste:\n{mensagem}")
            
            except Exception as e:
                st.error(f"Erro durante o teste: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python")
