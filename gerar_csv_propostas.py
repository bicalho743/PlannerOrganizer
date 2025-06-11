import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Exportar Propostas para CSV",
    page_icon="📊",
    layout="wide"
)

# Título e descrição
st.title("Exportar Todas as Propostas")
st.write("Esta ferramenta exporta todas as propostas do sistema para um arquivo CSV que você pode abrir no Excel.")

# Inicializar banco de dados
from utils.database import Database

if 'db' not in st.session_state:
    st.session_state.db = Database()

# Função para exportar propostas
def exportar_propostas():
    try:
        # Obter todas as propostas do banco
        propostas = st.session_state.db.get_propostas()
        
        if propostas.empty:
            st.warning("Não há propostas para exportar.")
            return (None, None)
        
        # Adicionar categoria para melhor visualização
        def categorizar_proposta(row):
            if row['status'] == 'Aberta' or row['status'] == 'Em análise':
                return 'Abertas'
            elif row['status'] == 'Aprovada' and row['status_execucao'] == 'Em execução':
                return 'Em execução'
            elif row['status'] == 'Aprovada' and row['status_execucao'] == 'Finalizada':
                return 'Finalizadas'
            elif row['status'] == 'Recusada' or row['status_execucao'] == 'Cancelada':
                return 'Recusadas'
            else:
                return 'Outras'
        
        # Aplicar categorização
        propostas['categoria'] = propostas.apply(categorizar_proposta, axis=1)
        
        # Formatar valor para exibição
        def formatar_valor_seguro(valor):
            try:
                if pd.notna(valor) and valor is not None:
                    # Converter para float se necessário
                    valor_float = float(valor)
                    return f"R$ {valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    return "R$ 0,00"
            except (ValueError, TypeError):
                return "R$ 0,00"
        
        propostas['valor_formatado'] = propostas['valor'].apply(formatar_valor_seguro)
        
        # Formatar datas
        propostas['data_inicio_formatada'] = propostas['data_inicio'].apply(
            lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
        )
        propostas['data_fim_formatada'] = propostas['data_fim'].apply(
            lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
        )
        
        # Criar um nome de arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"todas_propostas_{timestamp}.csv"
        
        # Salvar CSV na pasta 'uploaded_files' ou criar se não existir
        pasta_destino = "uploaded_files"
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
        
        caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
        propostas.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
        
        return (caminho_arquivo, propostas)
    
    except Exception as e:
        st.error(f"Erro ao exportar propostas: {str(e)}")
        return (None, None)

# Interface principal
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("O que esta ferramenta faz:")
    st.markdown("""
    - Exporta todas as propostas cadastradas no sistema
    - Permite visualizar todas as categorias de propostas (Abertas, Em execução, Finalizadas, Recusadas)
    - Gera um arquivo CSV que pode ser aberto no Excel
    - Adiciona uma categorização para facilitar a visualização
    """)

with col2:
    st.subheader("Ações:")
    if st.button("📊 Exportar Todas as Propostas", type="primary"):
        with st.spinner("Exportando propostas..."):
            resultado = exportar_propostas()
            
            if resultado and len(resultado) == 2:
                caminho_arquivo, propostas = resultado
            else:
                caminho_arquivo, propostas = None, None
            
            if caminho_arquivo and propostas is not None:
                st.success(f"✅ Exportação concluída! Total de propostas: {len(propostas)}")
                
                # Oferecer download do arquivo
                with open(caminho_arquivo, "rb") as file:
                    st.download_button(
                        label="⬇️ Baixar arquivo CSV",
                        data=file,
                        file_name=os.path.basename(caminho_arquivo),
                        mime="text/csv"
                    )
                
                # Mostrar prévia dos dados
                st.subheader("Prévia dos dados exportados:")
                
                # Definir colunas para exibição
                colunas_exibir = [
                    'numero', 'cliente_nome', 'descricao', 'valor_formatado', 
                    'categoria', 'data_inicio_formatada', 'data_fim_formatada'
                ]
                
                # Mapear nomes para exibição
                mapeamento_colunas = {
                    'numero': 'Número',
                    'cliente_nome': 'Cliente',
                    'descricao': 'Descrição',
                    'valor_formatado': 'Valor',
                    'categoria': 'Status',
                    'data_inicio_formatada': 'Data Início',
                    'data_fim_formatada': 'Data Fim'
                }
                
                # Exibir dataframe estilizado
                try:
                    if not propostas.empty and all(col in propostas.columns for col in colunas_exibir):
                        df_exibir = propostas[colunas_exibir].rename(columns=mapeamento_colunas)
                        st.dataframe(df_exibir, hide_index=True, use_container_width=True)
                        
                        # Mostrar contagem por categoria
                        st.subheader("Distribuição por status")
                        contagem = propostas['categoria'].value_counts().reset_index()
                        contagem.columns = ['Status', 'Quantidade']
                        st.bar_chart(contagem, x='Status', y='Quantidade')
                    else:
                        st.dataframe(propostas, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Erro ao exibir dados: {str(e)}")
                    if propostas is not None and not propostas.empty:
                        st.dataframe(propostas, use_container_width=True)
            else:
                st.error("Falha na exportação das propostas.")

# Botão para voltar ao dashboard
if st.button("Voltar ao Dashboard"):
    st.info("Redirecionando para o dashboard...")
    st.stop()

if __name__ == "__main__":
    pass  # Código principal já está na parte superior