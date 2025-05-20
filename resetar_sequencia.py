import streamlit as st
import os
import sys
from sqlalchemy import text

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

from utils.database import Database
from utils.auth import verificar_autenticacao
from utils.tenant import configurar_tenant, registrar_tenant_middleware

st.set_page_config(
    page_title="Resetar Sequência de Propostas",
    page_icon="🔄",
    layout="centered"
)

st.title("🔄 Resetar Sequência de Propostas")

# Verificar autenticação
verificar_autenticacao()

# Inicializar o banco de dados
if 'db' not in st.session_state:
    # Configurar o tenant com base no usuário atual
    usuario_atual = st.session_state.get('usuario_autenticado')
    if usuario_atual and 'uid' in usuario_atual:
        configurar_tenant(usuario_atual['uid'])
        st.session_state.db = Database()
        registrar_tenant_middleware(st.session_state.db)
    else:
        st.error("Não foi possível identificar o usuário logado.")
        st.stop()

st.write("""
Esta ferramenta permite resetar a sequência de numeração das propostas, 
para que novas propostas comecem do número 1.

**Atenção:** Esta ação é irreversível e afeta todas as propostas criadas após o reset.
""")

# Informações sobre o estado atual da sequência
with st.expander("Informações sobre a sequência atual"):
    try:
        # Obter o valor atual da sequência
        with st.session_state.db.engine.connect() as conn:
            result = conn.execute(text("SELECT last_value FROM propostas_numero_seq")).fetchone()
            valor_atual = result[0] if result else "Desconhecido"
            
            st.write(f"**Valor atual da sequência:** {valor_atual}")
            st.write("O próximo número de proposta será:", valor_atual + 1)
    except Exception as e:
        st.error(f"Erro ao obter informações da sequência: {str(e)}")

# Opções de reset
st.subheader("Opções de Reset")

col1, col2 = st.columns(2)

with col1:
    reset_to_one = st.radio(
        "Escolha uma opção:",
        ["Resetar para 1", "Definir valor personalizado"],
        index=0
    )

with col2:
    if reset_to_one == "Definir valor personalizado":
        novo_valor = st.number_input("Novo valor inicial:", min_value=1, value=1, step=1)
    else:
        novo_valor = 1
        st.info("A sequência será resetada para 1")

# Executar o reset
if st.button("🔄 Resetar Sequência", use_container_width=True):
    # Confirmar a ação
    confirmar = st.checkbox("Confirmo que quero resetar a sequência de propostas")
    
    if confirmar:
        try:
            with st.session_state.db.engine.begin() as conn:
                # Executar o SQL para resetar a sequência
                conn.execute(text(f"ALTER SEQUENCE propostas_numero_seq RESTART WITH {novo_valor}"))
                
                # Verificar se o reset foi bem-sucedido
                result = conn.execute(text("SELECT last_value FROM propostas_numero_seq")).fetchone()
                novo_valor_seq = result[0] if result else "Desconhecido"
                
                st.success(f"Sequência resetada com sucesso! O próximo número de proposta será: {novo_valor_seq + 1}")
        except Exception as e:
            st.error(f"Erro ao resetar sequência: {str(e)}")
    else:
        st.warning("Por favor, confirme a ação marcando a caixa acima.")

# Mensagem informativa
st.info("""
**Dica:** Ao criar novas propostas, o sistema usará o próximo número da sequência atual.
Para melhores resultados, recomendamos limpar propostas duplicadas antes de resetar a sequência.
""")