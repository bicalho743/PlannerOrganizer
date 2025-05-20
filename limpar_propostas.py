import streamlit as st
from utils.limpar_dados import limpar_propostas_form

# Configuração da página
st.set_page_config(
    page_title="Limpar Propostas - Planner Organiza",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton button {
        background-color: #ffc107;
        color: #000;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton button:hover {
        background-color: #ffb300;
        color: #000;
    }
    h1, h2, h3 {
        color: #1e3a8a;
    }
    .warning {
        background-color: #feecdc;
        border-left: 5px solid #ff5722;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🗑️ Limpar Propostas")
    st.markdown("---")
    
    st.write("""
    ### Ferramenta para limpar todas as propostas
    
    Esta página permite remover todas as propostas cadastradas no sistema e reiniciar a numeração
    para que os testes possam começar do zero com a proposta número 1.
    """)
    
    # Chamar o formulário de limpeza de propostas
    limpar_propostas_form()
    
    # Adicionar um botão para voltar para a aplicação principal
    st.markdown("---")
    if st.button("Voltar para o aplicativo principal"):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'/\'">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
import streamlit as st
from utils.database import Database

st.title("🧹 Limpar Propostas")

st.warning("⚠️ ATENÇÃO: Esta ação irá remover todas as propostas do sistema!")
st.write("Esta operação também removerá:")
st.write("- Produtos associados às propostas")
st.write("- Andamentos registrados")
st.write("- Acréscimos vinculados")
st.write("- Lançamentos financeiros gerados pelas propostas")

if st.button("Confirmar Limpeza", type="primary"):
    try:
        db = Database()
        
        # Execute limpeza em ordem para respeitar foreign keys
        with st.spinner("Limpando dados..."):
            # Remover produtos e fornecedores associados
            db.session.execute("DELETE FROM produtos_fornecedores")
            db.session.execute("DELETE FROM produtos_organizadores WHERE proposta_id IN (SELECT id FROM propostas)")
            
            # Remover andamentos
            db.session.execute("DELETE FROM andamento_propostas")
            
            # Remover acréscimos
            db.session.execute("DELETE FROM acrescimos_proposta")
            
            # Remover lançamentos financeiros vinculados
            db.session.execute("DELETE FROM financeiro WHERE proposta_id IS NOT NULL")
            
            # Finalmente remover as propostas
            db.session.execute("DELETE FROM propostas")
            
            db.session.commit()
            
        st.success("✅ Todas as propostas foram removidas com sucesso!")
    except Exception as e:
        st.error(f"Erro ao limpar propostas: {str(e)}")
