import streamlit as st
from datetime import datetime
import pandas as pd

def show():
    st.title("📊 Dashboard")

    # Add test data button in sidebar if database is empty
    if 'db' not in st.session_state:
        st.error("Database connection not initialized")
        return

    clientes = st.session_state.db.get_clientes()
    if clientes.empty:
        st.sidebar.warning("Banco de dados vazio")
        if st.sidebar.button("Adicionar Dados de Teste", key="btn_add_test_data_dashboard"):
            if st.session_state.db.add_test_data():
                st.sidebar.success("Dados de teste adicionados com sucesso!")
                st.rerun()
            else:
                st.sidebar.error("Erro ao adicionar dados de teste")

    # Dashboard layout
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.subheader("📊 Resumo")

        # Estatísticas básicas
        total_clientes = len(clientes) if not clientes.empty else 0
        st.metric("Total de Clientes", total_clientes)

        # Propostas
        try:
            propostas = st.session_state.db.get_propostas()
            propostas_ativas = len(propostas[propostas['status'] == 'Aberta']) if not propostas.empty else 0
            st.metric("Propostas Ativas", propostas_ativas)
        except Exception as e:
            st.warning("Erro ao carregar propostas")
            propostas = pd.DataFrame()

        # Financeiro
        try:
            financeiro = st.session_state.db.get_financeiro()
            if not financeiro.empty:
                valores_receber = financeiro[
                    (financeiro['tipo'] == 'receita') & 
                    (financeiro['status'] == 'pendente')
                ]['valor'].sum()
            else:
                valores_receber = 0.0
            st.metric("Valores a Receber", f"R$ {valores_receber:,.2f}")
        except Exception as e:
            st.warning("Erro ao carregar dados financeiros")

    with col2:
        st.subheader("📋 Propostas em Aberto")
        if not propostas.empty:
            propostas_abertas = propostas[propostas['status'] == 'Aberta'].sort_values('data_inicio', ascending=False)
            if not propostas_abertas.empty:
                for _, proposta in propostas_abertas.head(5).iterrows():
                    with st.expander(f"Proposta #{proposta['id']} - {proposta['descricao'][:50]}..."):
                        st.write(f"**Cliente:** {proposta['cliente_nome']}")
                        st.write(f"**Valor:** R$ {proposta['valor']:,.2f}")
                        if proposta.get('prazo_entrega'):
                            st.write(f"**Prazo:** {proposta['prazo_entrega'].strftime('%d/%m/%Y')}")
            else:
                st.info("Nenhuma proposta em aberto.")
        else:
            st.info("Nenhuma proposta cadastrada.")

    with col3:
        st.subheader("🎂 Aniversariantes")
        hoje = datetime.now()
        mes_atual = hoje.strftime('%b').lower()  # Mês atual em formato abreviado
        dia_atual = hoje.strftime('%d/%b').lower()  # Dia/mês atual

        if not clientes.empty and 'data_aniversario' in clientes.columns:
            # Aniversariantes de hoje
            aniversariantes_hoje = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower() == dia_atual)
            ]

            with st.container():
                st.markdown("""
                <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin-bottom: 15px;'>
                    <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>✨ Hoje</h4>
                </div>
                """, unsafe_allow_html=True)
                
                if not aniversariantes_hoje.empty:
                    for _, aniversariante in aniversariantes_hoje.iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div style='background-color: #304878; padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                                <div style='font-weight: bold; color: white;'>🎈 {aniversariante['nome']}</div>
                                {"<div style='color: #E2E8F0; font-size: 0.9em;'>📱 " + aniversariante['telefone'] + "</div>" if aniversariante['telefone'] else ""}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Nenhum aniversariante hoje!")

            # Aniversariantes do mês atual
            aniversariantes_mes = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower().str.endswith(f"/{mes_atual}"))
            ]
            
            with st.container():
                st.markdown(f"""
                <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin: 15px 0;'>
                    <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>🗓️ Mês de {hoje.strftime('%B').capitalize()}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                if not aniversariantes_mes.empty:
                    aniversariantes_ordenados = aniversariantes_mes.copy()
                    # Extrair o dia do aniversário para ordenação
                    aniversariantes_ordenados['dia'] = aniversariantes_ordenados['data_aniversario'].str.split('/').str[0].astype(int)
                    aniversariantes_ordenados = aniversariantes_ordenados.sort_values('dia')
                    
                    for _, aniversariante in aniversariantes_ordenados.iterrows():
                        # Verificar se o aniversário já passou este mês
                        dia_aniv = int(aniversariante['data_aniversario'].split('/')[0])
                        passou = dia_aniv < hoje.day
                        
                        with st.container():
                            st.markdown(f"""
                            <div style='background-color: {'#375170' if not passou else '#415570'}; padding: 10px; 
                                  border-radius: 5px; margin-bottom: 8px; opacity: {'1' if not passou else '0.8'};'>
                                <div style='font-weight: bold; color: white;'>
                                    {'🎂' if not passou else '✓'} {aniversariante['nome']} 
                                    <span style='font-weight: normal; color: {"#F1A208" if not passou else "#B0B0B0"}; 
                                          font-size: 0.9em;'>({aniversariante['data_aniversario']})</span>
                                </div>
                                {"<div style='color: #E2E8F0; font-size: 0.9em;'>📱 " + aniversariante['telefone'] + "</div>" if aniversariante['telefone'] else ""}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info(f"Nenhum aniversariante em {hoje.strftime('%B').capitalize()}.")

            # Próximos aniversariantes (próximos dias)
            st.markdown("""
            <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin: 15px 0;'>
                <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>🔜 Próximos 7 dias</h4>
            </div>
            """, unsafe_allow_html=True)
            
            proximos_dias = pd.date_range(hoje, periods=7, freq='D')
            datas_proximas = [d.strftime('%d/%b').lower() for d in proximos_dias]

            proximos = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower().isin(datas_proximas))
            ]

            if not proximos.empty:
                for _, proximo in proximos.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style='background-color: #304878; padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                            <div style='font-weight: bold; color: white;'>🎂 {proximo['nome']} 
                                <span style='font-weight: normal; color: #F1A208; font-size: 0.9em;'>({proximo['data_aniversario']})</span>
                            </div>
                            {"<div style='color: #E2E8F0; font-size: 0.9em;'>📱 " + proximo['telefone'] + "</div>" if proximo['telefone'] else ""}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Nenhum aniversariante nos próximos dias.")
        else:
            st.info("Nenhum cliente cadastrado com data de aniversário.")