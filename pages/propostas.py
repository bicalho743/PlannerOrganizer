import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timedelta
import time

def show():
    st.title("PROPOSTAS")
    
    # Verificar se temos uma conexão com o banco de dados
    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return
    
    # Criar um formulário para nova proposta
    st.subheader("Nova Proposta")
    
    # Obter a lista de clientes do banco de dados
    try:
        clientes = st.session_state.db.get_clientes()
        if clientes.empty:
            st.warning("Nenhum cliente cadastrado. Por favor, cadastre clientes primeiro.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {str(e)}")
        return
    
    # Formulário para cadastro de nova proposta
    with st.form(key="nova_proposta_form"):
        # Cliente (seleção a partir do módulo de cadastro)
        clientes_lista = clientes['nome'].tolist()
        cliente = st.selectbox("Cliente:", clientes_lista)
        
        # Descrição do serviço
        descricao = st.text_area("Descrição do serviço:", height=100)
        
        # Valor do serviço
        valor = st.number_input("Valor do serviço (R$):", min_value=0.0, format="%.2f")
        
        # Prazo estimado (em dias)
        prazo = st.number_input("Prazo estimado (dias):", min_value=1, value=15)
        
        # Data de início prevista
        data_inicio = st.date_input("Data de início prevista:", datetime.now().date())
        
        # Calcular data de término com base no prazo
        data_fim = data_inicio + timedelta(days=prazo)
        st.info(f"Data de término prevista: {data_fim.strftime('%d/%m/%Y')}")
        
        # Gerar ID único para a proposta (não visível para o usuário)
        # Este será substituído pelo ID gerado pelo banco de dados
        proposta_id = str(uuid.uuid4())
        
        # Botão para salvar
        submitted = st.form_submit_button("Salvar Proposta")
        
        if submitted:
            try:
                # Obter o ID do cliente selecionado
                cliente_id = clientes[clientes['nome'] == cliente]['id'].iloc[0]
                
                # Criar nova proposta
                novo_numero = st.session_state.db.add_proposta(
                    cliente_id=cliente_id,
                    descricao=descricao,
                    valor=valor,
                    status="Em elaboração",  # Status inicial
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    previsao_dias=prazo
                )
                
                if novo_numero:
                    st.success(f"Proposta #{novo_numero} criada com sucesso!")
                    
                    # Aguardar um momento para a mensagem ser exibida
                    time.sleep(1)
                    st.rerun()  # Recarregar a página para limpar o formulário
                else:
                    st.error("Erro ao salvar proposta.")
            except Exception as e:
                st.error(f"Erro ao salvar proposta: {str(e)}")
    
    # Mostrar propostas existentes em uma tabela
    st.subheader("Propostas Existentes")
    try:
        propostas = st.session_state.db.get_propostas()
        
        if not propostas.empty:
            # Mesclar com informações do cliente para exibir o nome
            propostas_com_clientes = propostas.merge(
                clientes[['id', 'nome']],
                left_on='cliente_id',
                right_on='id',
                suffixes=('', '_cliente')
            )
            
            # Preparar DataFrame para exibição
            df_exibicao = pd.DataFrame()
            df_exibicao['Número'] = propostas_com_clientes['numero']
            df_exibicao['Cliente'] = propostas_com_clientes['nome']
            df_exibicao['Descrição'] = propostas_com_clientes['descricao']
            df_exibicao['Valor (R$)'] = propostas_com_clientes['valor'].apply(lambda x: f"R$ {float(x):.2f}")
            df_exibicao['Status'] = propostas_com_clientes['status']
            
            # Formatar datas para exibição
            df_exibicao['Início'] = propostas_com_clientes['data_inicio'].apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
            )
            df_exibicao['Prazo (dias)'] = propostas_com_clientes['previsao_dias']
            
            # Exibir tabela
            st.dataframe(df_exibicao)
        else:
            st.info("Nenhuma proposta cadastrada.")
    except Exception as e:
        st.error(f"Erro ao carregar propostas: {str(e)}")