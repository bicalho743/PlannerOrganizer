import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

def show():
    # Forçar autenticação temporariamente para teste
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = True
        logger.info("Forçando autenticação para teste")

    # Debug do estado da sessão logo no início
    logger.info("=== Estado da Sessão (Início) ===")
    st.write("### Estado da Sessão (Debug)")
    for key, value in st.session_state.items():
        logger.info(f"{key}: {value}")
        # Não mostrar dados sensíveis na interface
        if key not in ['senha', 'token']:
            st.write(f"- {key}: {value}")

    st.title("🧪 Teste de Importação")

    # Verificar estado da sessão
    if 'db' not in st.session_state:
        st.error("Erro: Conexão com banco de dados não inicializada")
        logger.error("Banco de dados não encontrado na sessão")
        return
    else:
        st.success("Conexão com banco de dados presente na sessão")
        logger.info("Conexão com banco de dados encontrada")

    # Criar DataFrame de teste mínimo
    dados_teste = {
        'nome': ['Cliente Teste'],
        'telefone': ['(11) 99999-9999'],
        'email': ['teste@email.com'],
        'tipo_conta': ['PF'],
        'cpf': ['123.456.789-00']
    }

    df_teste = pd.DataFrame(dados_teste)
    st.write("Preview dos dados:")
    st.dataframe(df_teste)

    # Botão de teste com key única
    key_teste = "teste_importacao_debug_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    if st.button("Testar Importação", key=key_teste):
        try:
            logger.info("Iniciando teste de importação")
            logger.info(f"Estado da sessão antes da importação: {st.session_state}")

            # Tentar adicionar cliente diretamente
            st.session_state.db.add_cliente(
                nome=dados_teste['nome'][0],
                telefone=dados_teste['telefone'][0],
                email=dados_teste['email'][0],
                tipo_conta=dados_teste['tipo_conta'][0],
                cpf=dados_teste['cpf'][0]
            )

            st.success("Cliente teste adicionado com sucesso!")
            logger.info("Cliente teste adicionado com sucesso")
            logger.info(f"Estado da sessão após importação: {st.session_state}")

        except Exception as e:
            erro_msg = f"Erro durante o teste: {str(e)}"
            logger.error(erro_msg)
            logger.error(f"Stack trace: {traceback.format_exc()}")
            st.error(erro_msg)
            st.code(traceback.format_exc(), language="python")

    # Log final do estado da sessão
    logger.info("=== Estado da Sessão (Final) ===")
    logger.info(f"Estado final: {st.session_state}")