import streamlit as st
from utils.database import Database
from sqlalchemy import text

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
    .success {
        background-color: #d1fae5;
        border-left: 5px solid #10b981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .info {
        background-color: #e0f2fe;
        border-left: 5px solid #0ea5e9;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .card {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: white;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    /* Tabs customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f3f4f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0f2fe;
        border-bottom: 2px solid #0ea5e9;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🧹 Limpar Propostas e Gerenciar Numeração")
    st.markdown("---")
    
    # Criar abas para separar as funcionalidades
    tab1, tab2 = st.tabs(["🗑️ Limpar Todas as Propostas", "🔄 Resetar Numeração"])
    
    with tab1:
        st.header("Limpar Todas as Propostas")
        
        st.markdown("""
        <div class="warning">
            <h4>⚠️ ATENÇÃO: Esta ação irá remover todas as propostas do sistema!</h4>
            <p>Esta operação também removerá:</p>
            <ul>
                <li>Produtos associados às propostas</li>
                <li>Andamentos registrados</li>
                <li>Acréscimos vinculados</li>
                <li>Lançamentos financeiros gerados pelas propostas</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Confirmar Limpeza", type="primary", key="btn_limpar"):
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
                    
                    # Resetar a sequência
                    db.session.execute("ALTER SEQUENCE propostas_numero_seq RESTART WITH 1")
                    
                    db.session.commit()
                    
                st.success("✅ Todas as propostas foram removidas com sucesso e a numeração foi reiniciada!")
            except Exception as e:
                st.error(f"Erro ao limpar propostas: {str(e)}")
    
    with tab2:
        st.header("Resetar Numeração de Propostas")
        
        st.markdown("""
        <div class="info">
            <h4>ℹ️ Sobre esta ferramenta</h4>
            <p>Esta ferramenta permite reiniciar a numeração das propostas sem excluir os dados. 
            Novas propostas começarão do número que você definir.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Obter o valor atual da sequência
        try:
            db = Database()
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT last_value FROM propostas_numero_seq")).fetchone()
                valor_atual = result[0] if result else "Desconhecido"
                
                st.markdown(f"""
                <div class="card">
                    <h4>Valor atual da sequência: {valor_atual}</h4>
                    <p>O próximo número de proposta será: <b>{valor_atual + 1}</b></p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao obter informações da sequência: {str(e)}")
        
        # Opções de reset
        col1, col2 = st.columns(2)
        
        with col1:
            reset_option = st.radio(
                "Escolha uma opção:",
                ["Resetar para 1", "Definir valor personalizado"],
                index=0,
                key="reset_option"
            )
        
        with col2:
            if reset_option == "Definir valor personalizado":
                novo_valor = st.number_input("Novo valor inicial:", min_value=1, value=1, step=1, key="novo_valor")
            else:
                novo_valor = 1
                st.info("A sequência será resetada para 1")
        
        # Executar o reset
        if st.button("🔄 Resetar Numeração", use_container_width=True, key="btn_resetar"):
            confirmar = st.checkbox("Confirmo que quero resetar a sequência de propostas", key="confirmar")
            
            if confirmar:
                try:
                    with db.engine.begin() as conn:
                        # Executar o SQL para resetar a sequência
                        conn.execute(text(f"ALTER SEQUENCE propostas_numero_seq RESTART WITH {novo_valor}"))
                        
                        # Verificar se o reset foi bem-sucedido
                        result = conn.execute(text("SELECT last_value FROM propostas_numero_seq")).fetchone()
                        novo_valor_seq = result[0] if result else "Desconhecido"
                        
                        st.markdown(f"""
                        <div class="success">
                            <h4>✅ Sequência resetada com sucesso!</h4>
                            <p>O próximo número de proposta será: <b>{novo_valor_seq + 1}</b></p>
                            <p>Por favor, recarregue a aplicação para ver a mudança aplicada.</p>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erro ao resetar sequência: {str(e)}")
            else:
                st.warning("Por favor, confirme a ação marcando a caixa acima.")
    
    # Adicionar um botão para voltar para a aplicação principal
    st.markdown("---")
    if st.button("Voltar para o aplicativo principal", key="btn_voltar"):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'/\'">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
