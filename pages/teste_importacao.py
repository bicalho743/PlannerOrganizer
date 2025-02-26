import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

def show():
    # Log do estado da sessão
    logger.info("=== Estado da Sessão ===")
    for key, value in st.session_state.items():
        if key not in ['senha', 'token']:
            logger.info(f"{key}: {value}")

    st.title("🧪 Teste de Importação")

    # Verificar conexão com banco de dados
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        return
    else:
        st.success("Conexão com banco de dados presente na sessão")
        logger.info("Conexão com banco de dados encontrada")

    # Criar DataFrame de teste mínimo com dados formatados corretamente
    dados_teste = {
        'nome': ['Cliente Teste'],
        'telefone': ['11999999999'],  # Já formatado sem pontuação
        'email': ['teste@email.com'],
        'tipo_conta': ['PF'],
        'cpf': ['12345678900']  # Já formatado sem pontuação
    }

    df_teste = pd.DataFrame(dados_teste)
    st.write("Preview dos dados:")
    st.dataframe(df_teste)

    # Botão para testar importação
    if st.button("Testar Importação"):
        try:
            logger.info("Iniciando teste de importação")

            # Tentar adicionar cliente diretamente com dados já formatados
            st.session_state.db.add_cliente(
                nome=dados_teste['nome'][0],
                telefone=dados_teste['telefone'][0],  # Já formatado
                email=dados_teste['email'][0],
                tipo_conta=dados_teste['tipo_conta'][0],
                cpf=dados_teste['cpf'][0]  # Já formatado
            )

            st.success("Cliente teste adicionado com sucesso!")
            logger.info("Cliente teste adicionado com sucesso")

        except Exception as e:
            erro_msg = f"Erro durante o teste: {str(e)}"
            logger.error(erro_msg)
            logger.error(f"Stack trace: {traceback.format_exc()}")
            st.error(erro_msg)
            st.code(traceback.format_exc(), language="python")