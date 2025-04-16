import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Função auxiliar para formatar datas com segurança
def format_date_safe(date_obj, format_str='%d/%m/%Y'):
    """Formata uma data com segurança, retornando string em caso de erro"""
    try:
        # Verificar se o objeto tem método strftime (datetime, date, etc)
        if hasattr(date_obj, 'strftime') and callable(date_obj.strftime):
            return date_obj.strftime(format_str)
        # Verificar se é uma string
        elif hasattr(date_obj, 'strip') and callable(date_obj.strip):
            return date_obj
        # Caso contrário, converter para string
        else:
            return str(date_obj)
    except Exception:
        # Em caso de erro, retornar como string
        try:
            return str(date_obj)
        except:
            return "Data indisponível"

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
    # Layout com 3 colunas para a primeira linha
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.subheader("📊 Resumo")

        # Estatísticas básicas
        total_clientes = len(clientes) if not clientes.empty else 0
        st.metric("Total de Clientes", total_clientes)

        # Propostas
        try:
            propostas = st.session_state.db.get_propostas()
            
            # Contar propostas em elaboração ou aguardando aprovação como "em aberto"
            if not propostas.empty:
                propostas_em_aberto = len(propostas[
                    (propostas['status'] == 'Em elaboração') | 
                    (propostas['status'] == 'Aguardando aprovação')
                ])
            else:
                propostas_em_aberto = 0
                
            st.metric("Propostas em Aberto", propostas_em_aberto)
        except Exception as e:
            st.warning("Erro ao carregar propostas")
            propostas = pd.DataFrame()

        # Financeiro
        try:
            financeiro = st.session_state.db.get_financeiro()
            
            # Valores a Receber
            if not financeiro.empty:
                # Considerar receitas e receitas a receber pendentes
                valores_receber = financeiro[
                    ((financeiro['tipo'] == 'receita') | (financeiro['tipo'] == 'receita_a_receber')) & 
                    (financeiro['status'] == 'Pendente')
                ]['valor'].sum()
                
                # Valores a Pagar (despesas pendentes)
                valores_pagar = financeiro[
                    (financeiro['tipo'] == 'despesa') & 
                    (financeiro['status'] == 'Pendente')
                ]['valor'].sum()
            else:
                valores_receber = 0.0
                valores_pagar = 0.0
                
            # Exibir métricas
            st.metric("Valores a Receber", f"R$ {valores_receber:,.2f}", 
                     delta=f"Total: R$ {valores_receber:,.2f}", delta_color="normal")
            
            st.metric("Valores a Pagar", f"R$ {valores_pagar:,.2f}", 
                     delta=f"-R$ {valores_pagar:,.2f}", delta_color="inverse")
            
            # Calcular saldo líquido
            saldo_liquido = valores_receber - valores_pagar
            delta_saldo = f"+R$ {saldo_liquido:,.2f}" if saldo_liquido >= 0 else f"-R$ {abs(saldo_liquido):,.2f}"
            delta_color = "normal" if saldo_liquido >= 0 else "inverse"
            
            st.metric("Saldo Líquido", f"R$ {saldo_liquido:,.2f}", 
                     delta=delta_saldo, delta_color=delta_color)
            
        except Exception as e:
            st.warning(f"Erro ao carregar dados financeiros: {str(e)}")

    with col2:
        st.subheader("📋 Propostas em Aberto")
        if not propostas.empty:
            # Filtrar propostas em aberto (Em elaboração e Aguardando aprovação)
            propostas_abertas = propostas[
                (propostas['status'] == 'Em elaboração') | 
                (propostas['status'] == 'Aguardando aprovação')
            ].sort_values('data_inicio', ascending=False)
            
            if not propostas_abertas.empty:
                for _, proposta in propostas_abertas.head(5).iterrows():
                    status_emoji = "🔄" if proposta['status'] == 'Em elaboração' else "⏳"
                    
                    with st.expander(f"{status_emoji} #{proposta['numero']} - {proposta['descricao'][:40]}..."):
                        st.write(f"**Cliente:** {proposta.get('cliente_nome', 'N/A')}")
                        st.write(f"**Valor:** R$ {float(proposta['valor']):,.2f}")
                        st.write(f"**Status:** {proposta['status']}")
                        
                        if pd.notna(proposta.get('data_inicio')):
                            st.write(f"**Data Início:** {format_date_safe(proposta['data_inicio'])}")
                            
                        if pd.notna(proposta.get('previsao_dias')) and proposta.get('previsao_dias') > 0:
                            st.write(f"**Prazo:** {proposta['previsao_dias']} dias")
            else:
                st.info("Nenhuma proposta em elaboração ou aguardando aprovação.")
        else:
            st.info("Nenhuma proposta cadastrada.")

    with col3:
        st.subheader("🎂 Aniversariantes")
        hoje = datetime.now()
        
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
            
    # Nova seção para alertas de retorno ao cliente se aproximando dos 60 dias após execução
    st.subheader("📢 Alertas Retorno Cliente")
    
    # Container para mostrar propostas se aproximando de 60 dias após execução
    with st.container():
        st.markdown("""
        <div style='background-color: #2A3F5F; padding: 10px; border-radius: 7px; margin-bottom: 15px;'>
            <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>⏱️ Clientes aguardando retorno (próximo aos 60 dias)</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Verificar se propostas está vazio ou se tem a coluna status
        if not isinstance(propostas, pd.DataFrame) or propostas.empty or 'status' not in propostas.columns:
            propostas_executadas = pd.DataFrame()
        else:
            # Buscar todas as propostas executadas
            propostas_executadas = propostas[propostas['status'].isin(['Executada', 'Em execução', 'Finalizada'])]
            
        try:
            # Verificar propostas executadas
            
            if isinstance(propostas_executadas, pd.DataFrame) and not propostas_executadas.empty:
                # Data atual
                hoje = datetime.now().date()
                
                # Lista para armazenar propostas próximas de 60 dias
                propostas_alerta = []
                
                # Verificar se a coluna data_inicio existe
                if 'data_inicio' not in propostas_executadas.columns:
                    st.info("Campo 'data_inicio' não encontrado nas propostas.")
                    # Não usamos return aqui para evitar sair da função antes de completar
                    
                for idx, proposta in propostas_executadas.iterrows():
                    # Verificar se proposta tem todos os campos necessários
                    campos_obrigatorios = ['id', 'numero', 'descricao', 'data_inicio']
                    if not all(campo in proposta for campo in campos_obrigatorios):
                        continue  # Pula se faltar algum campo obrigatório
                    
                    # Verificar se tem data de início
                    if pd.notna(proposta.get('data_inicio')):
                        # Converter para datetime se for string
                        if isinstance(proposta['data_inicio'], str):
                            try:
                                data_inicio = datetime.strptime(proposta['data_inicio'], '%Y-%m-%d').date()
                            except ValueError:
                                try:
                                    data_inicio = datetime.strptime(proposta['data_inicio'], '%d/%m/%Y').date()
                                except ValueError:
                                    continue  # Se não conseguir converter, pula
                        else:
                            data_inicio = proposta['data_inicio'].date() if hasattr(proposta['data_inicio'], 'date') else proposta['data_inicio']
                            
                        # Calcular a data que será 60 dias após o início
                        data_60_dias = data_inicio + timedelta(days=60)
                        
                        # Calcular quantos dias faltam para atingir 60 dias
                        dias_restantes = (data_60_dias - hoje).days
                        
                        # Se faltar 10 dias ou menos (e ainda não tiver passado), mostrar alerta
                        if 0 <= dias_restantes <= 10:
                            propostas_alerta.append({
                                'id': proposta['id'],
                                'numero': proposta['numero'],
                                'cliente_nome': proposta.get('cliente_nome', 'Cliente não informado'),
                                'descricao': proposta['descricao'],
                                'data_inicio': data_inicio,
                                'dias_restantes': dias_restantes,
                                'data_60_dias': data_60_dias
                            })
                
                # Ordenar por dias restantes (mais urgentes primeiro)
                propostas_alerta.sort(key=lambda x: x['dias_restantes'])
                
                # Mostrar alertas
                if propostas_alerta:
                    for p in propostas_alerta:
                        with st.container():
                            st.markdown(f"""
                            <div style='background-color: {'#FF5722' if p['dias_restantes'] <= 3 else '#FF9800'}; 
                                  padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                                <div style='font-weight: bold; color: white;'>
                                    {'⚠️' if p['dias_restantes'] <= 3 else '⚠️'} Proposta #{p['numero']} 
                                    <span style='font-weight: normal; color: white; font-size: 0.9em;'>
                                        (Faltam {p['dias_restantes']} dias para contatar o cliente)
                                    </span>
                                </div>
                                <div style='color: white; font-size: 0.9em;'>
                                    Cliente: <b>{p['cliente_nome']}</b>
                                </div>
                                <div style='color: white; font-size: 0.9em;'>
                                    Data da organização: {format_date_safe(p['data_inicio'])} | Completará 60 dias em: {format_date_safe(p['data_60_dias'])}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Não há clientes aguardando retorno no momento.")
            else:
                st.info("Não há propostas em execução no sistema.")
        except Exception as e:
            st.warning("Erro ao processar alertas de retorno ao cliente.")