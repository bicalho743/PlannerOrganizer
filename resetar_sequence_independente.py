import streamlit as st
from sqlalchemy import text
import logging
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar banco de dados
from utils.database import Database
from utils.auth import verificar_autenticacao

# Configuração da página
st.set_page_config(
    page_title="Resetar Sequência",
    page_icon="🔄",
    layout="centered"
)

# Título
st.title("🔄 Reiniciar Numeração de Propostas")

# Verificar autenticação
verificar_autenticacao()

# Inicializar o banco de dados
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Mensagem explicativa
st.write("""
Esta ferramenta permite reiniciar a numeração das propostas, permitindo
que novas propostas comecem do número 1 (em vez de continuar do número atual).

Isso não afeta as propostas existentes, apenas a numeração das novas propostas criadas.
""")

st.markdown("---")

# Bloco principal
try:
    # Obter o valor atual da sequência
    with st.session_state.db.engine.begin() as conn:
        result = conn.execute(text("SELECT last_value FROM propostas_numero_seq")).fetchone()
        valor_atual = result[0] if result else "Desconhecido"
        
        # Exibir o valor atual
        st.info(f"**Valor atual da sequência:** {valor_atual}")
        st.write(f"Se você criar uma nova proposta agora, ela terá o número: **{valor_atual + 1}**")
    
    st.markdown("---")
    
    # Opção de valor para resetar
    st.subheader("Reiniciar Numeração")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        valor_escolhido = st.number_input("Reiniciar a partir do número:", 
                                       min_value=1, 
                                       value=1,
                                       step=1,
                                       help="Novas propostas começarão a partir deste número")
    
    with col2:
        st.write("")
        st.write("")
        confirmar = st.checkbox("Confirmo que desejo reiniciar a sequência de numeração de propostas")
    
    # Botão para executar o reset
    if st.button("🔄 Reiniciar Numeração", use_container_width=True, type="primary", disabled=not confirmar):
        with st.spinner("Reiniciando sequência..."):
            try:
                # Executar o comando SQL para resetar a sequência
                with st.session_state.db.engine.begin() as conn:
                    conn.execute(text(f"ALTER SEQUENCE propostas_numero_seq RESTART WITH {valor_escolhido}"))
                    
                    # Verificar o novo valor
                    result = conn.execute(text("SELECT last_value FROM propostas_numero_seq")).fetchone()
                    novo_valor = result[0] if result else "Desconhecido"
                    
                    # Exibir sucesso
                    st.success(f"✅ Sequência reiniciada com sucesso!")
                    st.balloons()
                    
                    st.write(f"O próximo número de proposta será: **{novo_valor + 1}**")
                    st.write("Você pode criar uma nova proposta agora para verificar.")
                
            except Exception as e:
                st.error(f"Erro ao reiniciar sequência: {str(e)}")
                logger.error(f"Erro ao reiniciar sequência: {str(e)}")
                logger.error(traceback.format_exc())
    
    if not confirmar and st.button("Cancelar", use_container_width=True):
        st.warning("Operação cancelada. Nenhuma alteração foi feita.")
    
    # Botão para voltar
    st.markdown("---")
    if st.button("Voltar para o aplicativo principal", use_container_width=True):
        st.markdown('<meta http-equiv="refresh" content="0;URL=\'/\'">', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao acessar o banco de dados: {str(e)}")
    logger.error(f"Erro ao acessar o banco de dados: {str(e)}")
    logger.error(traceback.format_exc())