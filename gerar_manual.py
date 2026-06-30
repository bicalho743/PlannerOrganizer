"""
Ferramenta interna (workflow "Gerar Manual") para gerar o PDF do manual do
sistema Planner Organizer. Reutiliza a lógica de geração de
`pages/manual_sistema.py`, sem exigir sessão autenticada.
"""
import os
import streamlit as st

from pages.manual_sistema import gerar_manual_sistema

st.set_page_config(page_title="Gerar Manual", page_icon="📘")

st.title("📘 Gerar Manual do Sistema")
st.write(
    "Ferramenta interna para gerar o PDF do manual do Planner Organizer. "
    "Clique no botão abaixo para gerar a versão mais recente."
)

if st.button("Gerar Manual PDF", type="primary", use_container_width=True):
    with st.spinner("Gerando manual..."):
        try:
            caminho = gerar_manual_sistema(verificar_auth=False)
        except Exception as e:
            caminho = None
            st.error(f"Erro ao gerar o manual: {e}")

    if caminho and os.path.exists(caminho):
        st.success("Manual gerado com sucesso!")
        with open(caminho, "rb") as f:
            st.download_button(
                label="Baixar Manual (PDF)",
                data=f.read(),
                file_name="Manual_Planner_Organizer.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    elif caminho is not None:
        st.error("Falha ao gerar o manual: arquivo não encontrado.")
