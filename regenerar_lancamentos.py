import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

# Adicionar diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

from utils.database import Database
from utils.regenerar_lancamentos import regenerar_lancamentos_proposta

st.set_page_config(
    page_title="Regenerar Lançamentos Financeiros",
    page_icon="🔄",
    layout="wide"
)

st.title("Regenerar Lançamentos Financeiros")

st.write("""
Esta ferramenta permite regenerar os lançamentos financeiros para uma proposta específica.
Use com cuidado, pois isso removerá os lançamentos existentes e criará novos.
""")

st.warning("⚠️ Esta é uma operação potencialmente perigosa. Use com cautela.")

with st.form("regenerar_form"):
    proposta_id = st.number_input("ID da Proposta", min_value=1, value=None, step=1)
    
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Regenerar Lançamentos")
    with col2:
        check_only = st.checkbox("Apenas verificar (não fazer alterações)", value=True)

if submit and proposta_id:
    with st.spinner("Processando..."):
        db = Database()
        
        # Buscar informações da proposta
        proposta = db.get_proposta_by_id(proposta_id)
        
        if proposta:
            st.info(f"Proposta #{proposta.numero} - {proposta.descricao}")
            
            if check_only:
                st.info("Modo Verificação: Nenhuma alteração será feita no banco de dados")
                
                # Buscar acréscimos da proposta
                acrescimos = db.get_acrescimos_proposta(proposta_id)
                
                # Exibir informações
                st.subheader("Acréscimos da Proposta")
                
                if acrescimos:
                    df_acrescimos = pd.DataFrame([
                        {
                            "Tipo": a.tipo,
                            "Fornecedor/Assistente": a.fornecedor,
                            "Descrição": a.descricao,
                            "Valor": float(a.valor)
                        }
                        for a in acrescimos
                    ])
                    
                    st.dataframe(df_acrescimos)
                else:
                    st.warning("Nenhum acréscimo encontrado para esta proposta")
                
                # Lançamentos financeiros existentes
                st.subheader("Lançamentos Financeiros Existentes")
                
                financeiro = db.get_lancamentos_by_proposta(proposta_id)
                
                if financeiro:
                    df_financeiro = pd.DataFrame([
                        {
                            "ID": f.id,
                            "Tipo": f.tipo,
                            "Descrição": f.descricao,
                            "Valor": float(f.valor),
                            "Categoria": f.categoria,
                            "Subcategoria": f.subcategoria,
                            "Status": f.status,
                            "Data": f.data
                        }
                        for f in financeiro
                    ])
                    
                    st.dataframe(df_financeiro)
                else:
                    st.warning("Nenhum lançamento financeiro encontrado para esta proposta")
                
            else:
                # Regenerar lançamentos
                resultado = regenerar_lancamentos_proposta(proposta_id)
                
                if resultado["sucesso"]:
                    st.success(f"Lançamentos regenerados com sucesso! {resultado['lancamentos_gerados']} lançamentos criados.")
                    
                    # Mostrar novos lançamentos
                    financeiro = db.get_lancamentos_by_proposta(proposta_id)
                    
                    if financeiro:
                        df_financeiro = pd.DataFrame([
                            {
                                "ID": f.id,
                                "Tipo": f.tipo,
                                "Descrição": f.descricao,
                                "Valor": float(f.valor),
                                "Categoria": f.categoria,
                                "Subcategoria": f.subcategoria,
                                "Status": f.status,
                                "Data": f.data
                            }
                            for f in financeiro
                        ])
                        
                        st.dataframe(df_financeiro)
                else:
                    st.error(f"Erro ao regenerar lançamentos: {resultado['mensagem']}")
        else:
            st.error(f"Proposta com ID {proposta_id} não encontrada!")