import streamlit as st
from utils.database import Database

def limpar_propostas_form():
    """
    Cria um formulário para limpar todas as propostas do sistema e reiniciar a sequência.
    """
    st.warning("""
    ### ⚠️ Atenção: Operação Irreversível
    
    Você está prestes a remover **TODAS** as propostas cadastradas no sistema.
    
    Esta operação também removerá:
    - Todos os andamentos de propostas
    - Todos os acréscimos vinculados a propostas
    - Todos os produtos vinculados a propostas
    - Todas as transações financeiras vinculadas a propostas
    
    Os clientes serão mantidos no sistema.
    
    **Esta ação não pode ser desfeita.**
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        confirmar = st.text_input("Digite 'LIMPAR PROPOSTAS' para prosseguir com a limpeza", 
                              help="Esta verificação de segurança é necessária para evitar exclusões acidentais.",
                              key="confirmar_limpar_propostas")
    
    with col2:
        if confirmar == "LIMPAR PROPOSTAS":
            botao_cor = "primary"
            botao_desabilitado = False
        else:
            botao_cor = "secondary"
            botao_desabilitado = True
            
        if st.button("Limpar Todas as Propostas", 
                   type=botao_cor, 
                   disabled=botao_desabilitado,
                   key="btn_limpar_propostas",
                   help="Este botão só será habilitado quando você digitar 'LIMPAR PROPOSTAS' no campo ao lado."):
            with st.spinner("Limpando propostas..."):
                try:
                    db = Database()
                    resultado = db.limpar_propostas()
                    
                    if resultado:
                        st.success("✅ Todas as propostas e dados relacionados foram removidos com sucesso!")
                        
                        # Adicionar botão para recarregar a página após limpeza
                        st.button("Recarregar Página", type="primary", 
                               on_click=lambda: st.rerun(),
                               key="reload_after_propostas")
                    else:
                        st.error("❌ Ocorreu um erro durante a limpeza das propostas.")
                except Exception as e:
                    st.error(f"❌ Erro ao limpar propostas: {str(e)}")

def limpar_clientes_form():
    """
    Cria um formulário para limpar todos os dados de clientes do sistema.
    """
    st.warning("""
    ### ⚠️ Atenção: Operação Irreversível
    
    Você está prestes a remover **TODOS** os clientes cadastrados no sistema.
    
    Esta operação também removerá:
    - Todas as propostas vinculadas a clientes
    - Todos os andamentos de propostas
    - Todos os produtos vinculados a propostas
    - Todas as transações financeiras vinculadas a propostas
    - Todas as vendas vinculadas a clientes
    
    **Esta ação não pode ser desfeita.**
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        confirmar = st.text_input("Digite 'CONFIRMAR' para prosseguir com a limpeza", 
                                 help="Esta verificação de segurança é necessária para evitar exclusões acidentais.")
    
    with col2:
        if confirmar == "CONFIRMAR":
            botao_cor = "primary"
            botao_desabilitado = False
        else:
            botao_cor = "secondary"
            botao_desabilitado = True
            
        if st.button("Limpar Todos os Clientes", 
                     type=botao_cor, 
                     disabled=botao_desabilitado,
                     help="Este botão só será habilitado quando você digitar 'CONFIRMAR' no campo ao lado."):
            with st.spinner("Limpando dados de clientes..."):
                try:
                    db = Database()
                    resultado = db.limpar_clientes()
                    
                    if resultado:
                        st.success("✅ Todos os clientes e dados relacionados foram removidos com sucesso!")
                        
                        # Adicionar botão para recarregar a página após limpeza
                        st.button("Recarregar Página", type="primary", 
                                 on_click=lambda: st.rerun())
                    else:
                        st.error("❌ Ocorreu um erro durante a limpeza dos dados.")
                except Exception as e:
                    st.error(f"❌ Erro ao limpar dados: {str(e)}")