import streamlit as st
import os
import sys
import time

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.brevo_helper import adicionar_contato_brevo, obter_listas_brevo
from utils.render_fix import inject_render_compatibility_fix

# Configuração da página
st.set_page_config(
    page_title="Teste de Integração Brevo",
    page_icon="favicon.png",
    layout="wide"
)

# Injetar correção para Render
inject_render_compatibility_fix()

# Título da página
st.title("Teste de Integração com Brevo")

# Explicação sobre o teste
st.info("""
Este é um teste da integração com o Brevo para captura de e-mails na lista de ID #7.
Use o formulário abaixo para testar se o e-mail está sendo salvo corretamente.
""")

# Formulário para adicionar e-mail
st.subheader("Adicionar e-mail à lista")

with st.form("form_brevo_test"):
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome")
    
    with col2:
        email = st.text_input("E-mail")
    
    submit = st.form_submit_button("Adicionar à lista do Brevo")

if submit:
    if not email or '@' not in email:
        st.error("Por favor, insira um e-mail válido.")
    else:
        with st.spinner("Adicionando contato..."):
            # Tentar adicionar o contato
            resultado = adicionar_contato_brevo(email=email, nome_completo=nome)
            
            # Exibir resultado
            if resultado.get("success", False):
                if resultado.get("fallback", False):
                    st.warning(resultado.get("message", "E-mail salvo localmente (fallback)."))
                else:
                    st.success(resultado.get("message", "E-mail adicionado com sucesso!"))
            else:
                st.error(resultado.get("message", "Erro ao adicionar e-mail."))

# Seção para visualizar as listas disponíveis
st.subheader("Listas disponíveis no Brevo")

if st.button("Verificar listas disponíveis"):
    with st.spinner("Obtendo listas..."):
        listas = obter_listas_brevo()
        
        if listas:
            st.success(f"Foram encontradas {len(listas)} listas")
            for lista in listas:
                st.info(f"ID: {lista['id']} - Nome: {lista['name']}")
        else:
            st.error("Não foi possível obter as listas ou não há listas disponíveis.")

# Informações sobre configuração
st.subheader("Informações de configuração")

api_key = os.getenv("BREVO_API_KEY", "")
masked_key = api_key[:4] + "****" + api_key[-4:] if len(api_key) > 8 else "Não configurada"

st.code(f"""
Lista ID: 7 (fixo)
API Key: {masked_key}
""")

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888;">
Teste de integração com Brevo - Lista ID: 7<br>
Implementado a pedido do cliente
</div>
""", unsafe_allow_html=True)