import streamlit as st
import os
import sys

# Adicionar o diretório raiz ao path para importar módulos personalizados
sys.path.append('.')

from utils.regenerar_lancamentos import regenerar_lancamentos
import logging

# Configuração de logging
logging.basicConfig(level=logging.DEBUG, 
                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Regenerar Lançamentos de Proposta Finalizada",
    page_icon=":money_with_wings:",
    layout="wide"
)

st.title("Regenerar Lançamentos de Proposta Finalizada")

st.markdown("""
Esta ferramenta permite regenerar os lançamentos financeiros de uma proposta que já foi finalizada.
Útil em casos onde a finalização foi feita diretamente no banco de dados ou quando os lançamentos não foram criados corretamente.
""")

proposta_id = st.number_input("ID da Proposta", min_value=1, value=94, step=1)

if st.button("Regenerar Lançamentos"):
    with st.spinner("Regenerando lançamentos..."):
        try:
            resultado = regenerar_lancamentos(int(proposta_id))
            
            if resultado["status"]:
                st.success(f"Lançamentos regenerados com sucesso para a proposta #{proposta_id}")
                
                # Mostrar detalhes dos lançamentos gerados
                st.subheader("Detalhes:")
                st.json(resultado)
            else:
                st.error(f"Erro ao regenerar lançamentos: {resultado['mensagem']}")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
            logger.exception("Erro ao regenerar lançamentos")

st.divider()

st.markdown("""
### Como usar:
1. Informe o ID da proposta que deseja regenerar os lançamentos
2. Clique no botão "Regenerar Lançamentos"
3. Verifique na página de Financeiro se os lançamentos foram criados corretamente

**Atenção:** Esta ferramenta irá remover todos os lançamentos existentes para a proposta informada e criar novos.
""")