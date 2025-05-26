import streamlit as st
import pandas as pd
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import Database

def main():
    st.set_page_config(
        page_title="Teste - Todas as Propostas",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("🔍 Teste de Visualização Completa de Propostas")
    st.markdown("---")
    
    # Simular login (usando ID conhecido que funciona)
    if 'db' not in st.session_state:
        usuario_id = "37URJQFLe8M1QVbyFfvDhmbQ9aC2"
        st.session_state.db = Database(usuario_id=usuario_id)
        st.session_state.usuario_id = usuario_id
    
    st.success(f"✅ Conectado com usuário ID: {st.session_state.usuario_id}")
    
    try:
        # Buscar dados brutos
        propostas_raw = st.session_state.db.get_propostas()
        clientes_raw = st.session_state.db.get_clientes()
        
        st.write(f"**📊 Dados encontrados:**")
        st.write(f"- Propostas: {len(propostas_raw)}")
        st.write(f"- Clientes: {len(clientes_raw)}")
        
        if len(propostas_raw) == 0:
            st.error("❌ Nenhuma proposta encontrada!")
            return
            
        # Mostrar dados brutos primeiro
        with st.expander("🔍 Ver dados brutos das propostas"):
            st.dataframe(propostas_raw, use_container_width=True)
            
        with st.expander("🔍 Ver dados brutos dos clientes"):
            st.dataframe(clientes_raw, use_container_width=True)
        
        st.markdown("---")
        st.write("**📋 LISTAGEM FORMATADA - TODAS AS PROPOSTAS:**")
        
        # Processar dados para exibição limpa
        propostas_exibicao = []
        
        for idx, prop in propostas_raw.iterrows():
            # Buscar nome do cliente
            cliente_nome = "Cliente não encontrado"
            cliente_id = prop.get('cliente_id')
            
            if cliente_id and len(clientes_raw) > 0:
                cliente_encontrado = clientes_raw[clientes_raw['id'] == cliente_id]
                if len(cliente_encontrado) > 0:
                    cliente_nome = cliente_encontrado.iloc[0]['nome']
            
            # Montar dados da proposta
            propostas_exibicao.append({
                'ID': prop.get('id', 'N/A'),
                'Número': prop.get('numero', 'N/A'),
                'Cliente': cliente_nome,
                'Descrição': str(prop.get('descricao', 'N/A'))[:60] + "..." if len(str(prop.get('descricao', 'N/A'))) > 60 else str(prop.get('descricao', 'N/A')),
                'Status': prop.get('status', 'N/A'),
                'Valor': f"R$ {float(prop.get('valor', 0)):,.2f}" if prop.get('valor') else 'N/A',
                'Data Início': str(prop.get('data_inicio', 'N/A'))[:10],
                'Tipo': prop.get('tipo_proposta', 'N/A')
            })
        
        # Exibir tabela formatada
        df_propostas = pd.DataFrame(propostas_exibicao)
        
        st.dataframe(
            df_propostas,
            use_container_width=True,
            height=500,
            column_config={
                'ID': st.column_config.NumberColumn('ID', width='small'),
                'Número': st.column_config.NumberColumn('Número', width='small'),
                'Cliente': st.column_config.TextColumn('Cliente', width='medium'),
                'Descrição': st.column_config.TextColumn('Descrição', width='large'),
                'Status': st.column_config.TextColumn('Status', width='small'),
                'Valor': st.column_config.TextColumn('Valor', width='small'),
                'Data Início': st.column_config.TextColumn('Data', width='small'),
                'Tipo': st.column_config.TextColumn('Tipo', width='small')
            }
        )
        
        st.success(f"🎉 **SUCESSO!** Exibindo {len(df_propostas)} propostas encontradas!")
        
        # Estatísticas
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Propostas", len(df_propostas))
        
        with col2:
            finalizadas = len([p for p in propostas_exibicao if p['Status'] == 'Finalizada'])
            st.metric("Finalizadas", finalizadas)
        
        with col3:
            em_execucao = len([p for p in propostas_exibicao if p['Status'] == 'Em execução'])
            st.metric("Em Execução", em_execucao)
        
        with col4:
            valor_total = sum([float(p['Valor'].replace('R$ ', '').replace(',', '')) for p in propostas_exibicao if p['Valor'] != 'N/A'])
            st.metric("Valor Total", f"R$ {valor_total:,.2f}")
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()