import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Função auxiliar para formatar datas com segurança
def format_date_safe(date_obj, format_str='%d/%m/%Y'):
    """Formata uma data com segurança, retornando string em caso de erro"""
    try:
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime(format_str)
        elif isinstance(date_obj, str):
            return date_obj
        else:
            return str(date_obj)
    except Exception as e:
        return str(date_obj)

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
    # Layout simplificado com 3 colunas
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
                            st.write(f"**Prazo:** {format_date_safe(proposta['prazo_entrega'])}")
            else:
                st.info("Nenhuma proposta em aberto.")
        else:
            st.info("Nenhuma proposta cadastrada.")

    with col3:
        st.subheader("🎂 Aniversariantes")
        hoje = datetime.now()
        
    with col4:
        st.subheader("📆 Clientes - 90 dias")
        
        # Verificar se há propostas disponíveis
        try:
            # Verificar propostas e clientes
            if 'propostas' not in locals() or propostas.empty:
                propostas = st.session_state.db.get_propostas()
                
            if propostas.empty:
                st.info("Nenhuma proposta encontrada.")
            else:
                # Obter data atual
                hoje_date = datetime.now().date()
                
                # Calcular data limite (90 dias atrás)
                data_limite_90_dias = hoje_date - timedelta(days=90)
                
                # Verificar se a coluna 'cliente_nome' existe
                # (Já deve existir pois foi adicionada na função get_propostas)
                if 'cliente_nome' not in propostas.columns:
                    st.warning("Coluna 'cliente_nome' não encontrada nas propostas, utilize uma versão atualizada.")
                    propostas['cliente_nome'] = "Cliente não identificado"
                
                # Filtrar propostas por tipo (apenas de organização e com data de início preenchida)
                propostas_organizacao = propostas[
                    (propostas['tipo_proposta'].isin(['Organização', 'Organização Mudança'])) &
                    (propostas['data_inicio'].notna())
                ]
                
                if propostas_organizacao.empty:
                    st.info("Nenhuma proposta de organização com data de início definida.")
                else:
                    # Converter data_inicio para datetime.date se ainda não for
                    try:
                        # Tentar converter todas as datas para datetime.date
                        propostas_organizacao['data_inicio'] = pd.to_datetime(propostas_organizacao['data_inicio']).dt.date
                    except Exception as e:
                        st.warning(f"Erro ao converter datas: {str(e)}. Usando formato original.")
                    
                    # Calcular dias passados desde o início para cada proposta
                    def calcular_dias(data_inicio):
                        try:
                            if isinstance(data_inicio, datetime) or hasattr(data_inicio, 'date'):
                                return (hoje_date - data_inicio).days
                            elif isinstance(data_inicio, str):
                                # Tentar converter para data se for string
                                converted = pd.to_datetime(data_inicio).date()
                                return (hoje_date - converted).days
                            else:
                                return 0
                        except Exception:
                            return 0
                        
                    propostas_organizacao['dias_passados'] = propostas_organizacao['data_inicio'].apply(calcular_dias)
                    
                    # Clientes que atingiram 90 dias
                    propostas_90_dias = propostas_organizacao[propostas_organizacao['dias_passados'] >= 90].sort_values('dias_passados')
                    
                    # Clientes que ainda não atingiram 90 dias mas estão próximos
                    propostas_proximas = propostas_organizacao[
                        (propostas_organizacao['dias_passados'] < 90) & 
                        (propostas_organizacao['dias_passados'] >= 60)
                    ].sort_values('dias_passados', ascending=False)
                    
                    # Exibir clientes que atingiram 90 dias
                    st.markdown("""
                    <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin-bottom: 15px;'>
                        <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>✅ Completaram 90 dias</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not propostas_90_dias.empty:
                        for _, proposta in propostas_90_dias.head(5).iterrows():
                            with st.container():
                                st.markdown(f"""
                                <div style='background-color: #304878; padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                                    <div style='font-weight: bold; color: white;'>📋 {proposta['cliente_nome']}</div>
                                    <div style='color: #E2E8F0; font-size: 0.9em;'>
                                        Organização concluída há {proposta['dias_passados']} dias
                                    </div>
                                    <div style='color: #F1A208; font-size: 0.8em;'>
                                        Início: {format_date_safe(proposta['data_inicio'])}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("Nenhum cliente completou 90 dias desde a organização.")
                    
                    # Exibir clientes próximos de completar 90 dias
                    st.markdown("""
                    <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin: 15px 0;'>
                        <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>🔜 Próximos a completar 90 dias</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not propostas_proximas.empty:
                        for _, proposta in propostas_proximas.head(5).iterrows():
                            dias_restantes = 90 - proposta['dias_passados']
                            with st.container():
                                st.markdown(f"""
                                <div style='background-color: #375170; padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                                    <div style='font-weight: bold; color: white;'>📋 {proposta['cliente_nome']}</div>
                                    <div style='color: #E2E8F0; font-size: 0.9em;'>
                                        Faltam {dias_restantes} dias para completar 90 dias
                                    </div>
                                    <div style='color: #F1A208; font-size: 0.8em;'>
                                        Início: {format_date_safe(proposta['data_inicio'])}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("Nenhum cliente próximo de completar 90 dias.")
        except Exception as e:
            st.error(f"Erro ao carregar dados de monitoramento: {str(e)}")
        
        # Dicionário de tradução de meses inglês -> português
        meses_traducao = {
            'jan': 'jan', 'feb': 'fev', 'mar': 'mar', 'apr': 'abr',
            'may': 'mai', 'jun': 'jun', 'jul': 'jul', 'aug': 'ago',
            'sep': 'set', 'oct': 'out', 'nov': 'nov', 'dec': 'dez'
        }
        
        # Nome do mês em português e inglês
        mes_atual_en = hoje.strftime('%b').lower()
        mes_atual = meses_traducao.get(mes_atual_en, mes_atual_en)  # Mês atual em formato abreviado em português
        
        # Nome completo do mês em português
        meses_completos = {
            'jan': 'Janeiro', 'fev': 'Fevereiro', 'mar': 'Março', 'abr': 'Abril',
            'mai': 'Maio', 'jun': 'Junho', 'jul': 'Julho', 'ago': 'Agosto',
            'set': 'Setembro', 'out': 'Outubro', 'nov': 'Novembro', 'dez': 'Dezembro'
        }
        nome_mes_completo = meses_completos.get(mes_atual, hoje.strftime('%B').capitalize())
        
        # Dia atual no formato do banco (DD/MMM em português)
        dia_atual = f"{hoje.day:02d}/{mes_atual}"

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
                    <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>🗓️ Mês de {nome_mes_completo}</h4>
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
                    st.info(f"Nenhum aniversariante em {nome_mes_completo}.")

            # Próximos aniversariantes (próximos dias)
            st.markdown("""
            <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin: 15px 0;'>
                <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>🔜 Próximos 7 dias</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Gerar as datas dos próximos 7 dias
            proximos_dias = pd.date_range(hoje, periods=7, freq='D')
            
            # Converter cada data para o formato em português
            datas_proximas = []
            for d in proximos_dias:
                mes_en = d.strftime('%b').lower()
                mes_pt = meses_traducao.get(mes_en, mes_en)
                datas_proximas.append(f"{d.day:02d}/{mes_pt}")
            
            # Buscar aniversariantes dos próximos dias
            proximos = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower().isin([d.lower() for d in datas_proximas]))
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