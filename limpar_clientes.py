import streamlit as st
from utils.database import Database

# Título da página
st.title("🧹 Limpeza de Clientes")

# Inicializar banco de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
        st.success("Banco de dados conectado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        st.stop()

# Mensagem explicativa
st.write("""
Esta página permite limpar todos os dados de clientes do sistema para preparar para importação com IDs específicos.

⚠️ **ATENÇÃO**: Esta operação excluirá:
- Todos os clientes
- Todas as propostas
- Todos os produtos associados a propostas
- Todos os registros financeiros associados a propostas
- Todas as vendas
""")

# Botão para confirmar
if st.button("Limpar TODOS os Dados de Clientes", type="primary"):
    with st.spinner("Limpando dados de clientes..."):
        try:
            db = st.session_state.db
            resultado = db.limpar_clientes()
            
            if resultado:
                st.success("✅ Todos os clientes e dados relacionados foram removidos com sucesso!")
                st.info("""
                Agora você pode importar seus clientes com IDs específicos.
                
                Certifique-se de que seu arquivo CSV tenha uma coluna 'cliente_id' e 
                marque a opção "Usar ID do cliente direto do arquivo" na página de importação.
                """)
            else:
                st.error("❌ Ocorreu um erro durante a limpeza dos dados.")
        except Exception as e:
            st.error(f"❌ Erro ao limpar dados: {str(e)}")
else:
    st.warning("Clique no botão acima para limpar os dados de clientes.")