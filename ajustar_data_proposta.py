import streamlit as st
import pandas as pd
import time
import sys
import datetime
import os
from utils.database import Database

def main():
    st.set_page_config(page_title="Ajustar Data de Proposta", layout="wide")
    st.title("Ajuste de Data de Proposta")
    
    # Inicializar o banco de dados
    if "db" not in st.session_state:
        st.session_state.db = Database()
    
    # Obter propostas
    propostas = st.session_state.db.get_propostas()
    
    if propostas.empty:
        st.warning("Nenhuma proposta encontrada.")
        return
    
    # Juntar com informações do cliente
    clientes = st.session_state.db.get_clientes()
    propostas = propostas.merge(
        clientes[['id', 'nome']], 
        left_on='cliente_id', 
        right_on='id', 
        suffixes=('', '_cliente')
    )
    
    # Seleção da proposta
    proposta_options = [
        f"Proposta #{p['numero']} - {p['nome']} - {p['descricao']}" 
        for _, p in propostas.iterrows()
    ]
    
    proposta_selecionada = st.selectbox(
        "Selecione a proposta para ajustar a data:",
        proposta_options,
        index=0
    )
    
    # Extrair o número da proposta selecionada
    proposta_num = int(proposta_selecionada.split('#')[1].split(' -')[0])
    proposta = propostas[propostas['numero'] == proposta_num].iloc[0]
    
    # Mostrar informações atuais
    st.write("### Dados Atuais da Proposta")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Número:** {proposta['numero']}")
        st.write(f"**Cliente:** {proposta['nome']}")
        
    with col2:
        data_proposta = pd.to_datetime(proposta['data_proposta'])
        st.write(f"**Data da Proposta:** {data_proposta.strftime('%d/%m/%Y')}")
        
        if pd.notna(proposta['data_inicio']):
            data_inicio = pd.to_datetime(proposta['data_inicio'])
            st.write(f"**Data de Início:** {data_inicio.strftime('%d/%m/%Y')}")
    
    with col3:
        if pd.notna(proposta['data_fim']):
            data_fim = pd.to_datetime(proposta['data_fim'])
            st.write(f"**Data de Fim:** {data_fim.strftime('%d/%m/%Y')}")
        
        dias = proposta.get('previsao_dias', 0)
        st.write(f"**Previsão de Dias:** {dias if dias else 'Não definido'}")
    
    # Ajustar a data
    st.write("### Nova Data da Proposta")
    with st.form("ajustar_data"):
        nova_data_str = st.text_input(
            "Nova data (DD/MM/YYYY):",
            value=data_proposta.strftime('%d/%m/%Y')
        )
        
        dias_previstos = st.number_input(
            "Previsão de dias:",
            min_value=0,
            value=int(proposta.get('previsao_dias', 0)) if proposta.get('previsao_dias') else 0,
            step=1
        )
        
        submetido = st.form_submit_button("Salvar Nova Data", use_container_width=True)
    
    if submetido:
        try:
            # Converter a data para o formato do banco
            try:
                # Tentar formato brasileiro primeiro (DD/MM/YYYY)
                nova_data = pd.to_datetime(nova_data_str, format="%d/%m/%Y").date()
            except:
                try:
                    # Tentar inferir o formato
                    nova_data = pd.to_datetime(nova_data_str).date()
                except Exception as e:
                    st.error(f"Formato de data inválido: {str(e)}. Use o formato DD/MM/YYYY.")
                    return
            
            # Atualizar data da proposta com chamadas sequenciais
            with st.spinner("Atualizando data da proposta..."):
                # 1. Atualizar data da proposta
                print(f"DEBUG: Atualizando data da proposta {proposta['id']} para {nova_data}")
                st.session_state.db.atualizar_proposta(
                    proposta_id=proposta['id'],
                    data_proposta=nova_data
                )
                time.sleep(0.5)  # Pequena pausa para garantir que a operação seja concluída
                
                # 2. Atualizar data de início
                print(f"DEBUG: Atualizando data de início para {nova_data}")
                st.session_state.db.atualizar_proposta(
                    proposta_id=proposta['id'],
                    data_inicio=nova_data
                )
                time.sleep(0.5)
                
                # 3. Atualizar previsão de dias
                print(f"DEBUG: Atualizando previsão para {dias_previstos} dias")
                st.session_state.db.atualizar_proposta(
                    proposta_id=proposta['id'],
                    previsao_dias=dias_previstos
                )
                time.sleep(0.5)
                
                # 4. Calcular e atualizar data de fim
                if dias_previstos > 0:
                    data_fim = nova_data + datetime.timedelta(days=dias_previstos)
                    print(f"DEBUG: Atualizando data de fim para {data_fim}")
                    st.session_state.db.atualizar_proposta(
                        proposta_id=proposta['id'],
                        data_fim=data_fim
                    )
            
            st.success("✅ Data da proposta atualizada com sucesso!")
            st.write(f"**Nova data da proposta:** {nova_data.strftime('%d/%m/%Y')}")
            
            if dias_previstos > 0:
                st.write(f"**Nova previsão:** {dias_previstos} dias")
                data_fim = nova_data + datetime.timedelta(days=dias_previstos)
                st.write(f"**Nova data de fim:** {data_fim.strftime('%d/%m/%Y')}")
            
            # Adicionar botão para gerar PDF
            if st.button("Gerar PDF da Proposta Atualizada"):
                try:
                    # Criar diretório para PDFs se não existir
                    os.makedirs("pdfs", exist_ok=True)

                    # Nome do arquivo
                    filename = f"pdfs/proposta_{proposta['numero']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    # Importar a função de geração de PDF
                    from pages.propostas import gerar_pdf_fechamento
                    
                    # Obter a proposta atualizada
                    propostas_atualizadas = st.session_state.db.get_propostas()
                    proposta_atualizada = propostas_atualizadas[propostas_atualizadas['id'] == proposta['id']].iloc[0]
                    
                    # Buscar acréscimos da proposta
                    acrescimos = st.session_state.db.get_acrescimos_proposta(proposta['id'])
                    
                    # Gerar PDF
                    with st.spinner("Gerando PDF..."):
                        pdf_path = gerar_pdf_fechamento(
                            proposta=proposta_atualizada,
                            cliente={'nome': proposta['nome']},
                            acrescimos=acrescimos,
                            filename=filename,
                            usar_template=False
                        )
                        
                        # Criar link para download
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                            st.download_button(
                                label="📥 Baixar PDF",
                                data=pdf_bytes,
                                file_name=os.path.basename(filename),
                                mime="application/pdf"
                            )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")
        
        except Exception as e:
            st.error(f"Erro ao atualizar data: {str(e)}")

if __name__ == "__main__":
    main()