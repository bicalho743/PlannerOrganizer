import streamlit as st
import pandas as pd
import time
import sys
import datetime
import os
from utils.database import Database

def corrigir_todas_propostas():
    """Atualiza a data_proposta de todas as propostas para usar a data_inicio quando disponível"""
    db = Database()
    
    try:
        # Executar SQL diretamente
        from sqlalchemy.sql import text
        
        # Atualizar todas as propostas que têm data_inicio mas não têm data_proposta igual
        sql = """
        UPDATE propostas
        SET data_proposta = data_inicio
        WHERE data_inicio IS NOT NULL 
        AND (data_proposta IS NULL OR data_proposta != data_inicio)
        """
        
        result = db.session.execute(text(sql))
        db.session.commit()
        
        # Retornar número de linhas afetadas
        return result.rowcount
    except Exception as e:
        print(f"Erro ao atualizar propostas: {str(e)}")
        db.session.rollback()
        return 0

def main():
    st.set_page_config(page_title="Ajustar Data de Proposta", layout="wide")
    st.title("Ajuste de Data de Proposta")
    
    # Inicializar o banco de dados
    if "db" not in st.session_state:
        st.session_state.db = Database()
    
    # Botão para corrigir datas de todas as propostas
    if st.button("⚠️ Corrigir Datas de Todas as Propostas"):
        atualizadas = corrigir_todas_propostas()
        st.success(f"✅ {atualizadas} propostas atualizadas com sucesso! As datas de proposta agora correspondem às datas de início.")
        
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
                # Calcular a data de fim
                data_fim = nova_data + datetime.timedelta(days=dias_previstos) if dias_previstos > 0 else None
                
                # Atualizar todos os campos de uma só vez para garantir consistência
                print(f"DEBUG: Atualizando TODAS as datas da proposta {proposta['id']} para:")
                print(f"DEBUG: - Data da proposta: {nova_data}")
                print(f"DEBUG: - Data de início: {nova_data}")
                print(f"DEBUG: - Previsão de dias: {dias_previstos}")
                print(f"DEBUG: - Data de fim: {data_fim}")
                
                try:
                    # Primeiro, faça um update direto no banco para garantir consistência
                    sql_query = """
                    UPDATE propostas 
                    SET data_proposta = %s, 
                        data_inicio = %s, 
                        data_fim = %s, 
                        previsao_dias = %s 
                    WHERE id = %s
                    """
                    
                    # Usar Session para executar comando SQL direto
                    from sqlalchemy.sql import text
                    from utils.database import Session
                    
                    session = Session()
                    try:
                        # Executar SQL diretamente para evitar problemas de sincronização
                        session.execute(
                            text(sql_query), 
                            {
                                "param_1": nova_data, 
                                "param_2": nova_data, 
                                "param_3": data_fim,
                                "param_4": dias_previstos,
                                "param_5": proposta['id']
                            }
                        )
                        session.commit()
                        print(f"DEBUG: SQL direto executado com sucesso para proposta {proposta['id']}")
                    except Exception as e:
                        session.rollback()
                        print(f"DEBUG: Erro ao executar SQL direto: {str(e)}")
                        raise
                    finally:
                        session.close()
                    
                    # Usar também o método padrão como backup
                    st.session_state.db.atualizar_proposta(
                        proposta_id=proposta['id'],
                        data_proposta=nova_data,
                        data_inicio=nova_data,
                        previsao_dias=dias_previstos,
                        data_fim=data_fim
                    )
                    
                    # Verificar se os dados foram atualizados
                    time.sleep(1)  # Dar tempo para o banco processar
                    
                    # Buscar a proposta atualizada diretamente
                    propostas_atualizadas = st.session_state.db.get_propostas()
                    proposta_verificacao = propostas_atualizadas[propostas_atualizadas['id'] == proposta['id']].iloc[0]
                    
                    # Validar os dados
                    print(f"DEBUG: Verificação após atualização - proposta {proposta['id']}:")
                    print(f"DEBUG: - Data proposta: {proposta_verificacao['data_proposta']}")
                    print(f"DEBUG: - Data início: {proposta_verificacao['data_inicio']}")
                    print(f"DEBUG: - Data fim: {proposta_verificacao['data_fim']}")
                    print(f"DEBUG: - Previsão dias: {proposta_verificacao['previsao_dias']}")
                    
                except Exception as e:
                    print(f"DEBUG: ERRO NA ATUALIZAÇÃO: {str(e)}")
                    st.error(f"Erro ao atualizar dados: {str(e)}")
                    raise
            
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
                        print("DEBUG PDF: Recarregando dados atualizados da proposta #" + str(proposta['numero']))
                        # Pegar dados recentes do banco
                        try:
                            # Garantir que temos a versão mais atualizada da proposta
                            from sqlalchemy.sql import text
                            from utils.database import Session
                            
                            session = Session()
                            try:
                                result = session.execute(
                                    text("SELECT id, numero, data_proposta, data_inicio, data_fim, previsao_dias FROM propostas WHERE id = :id"),
                                    {"id": proposta['id']}
                                ).fetchone()
                                
                                if result:
                                    print(f"DEBUG PDF: Proposta recarregada com sucesso! ID={result[0]}")
                                    print(f"DEBUG PDF: Data da proposta: {result[2]}")
                                    print(f"DEBUG PDF: Data início: {result[3]}")
                                    print(f"DEBUG PDF: Data fim: {result[4]}")
                                
                            except Exception as e:
                                print(f"DEBUG PDF: Erro ao consultar proposta: {str(e)}")
                            finally:
                                session.close()
                        except Exception as debug_e:
                            print(f"DEBUG PDF: Erro no debug: {str(debug_e)}")
                        
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