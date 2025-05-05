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
    # Removido o título de Dashboard conforme solicitado

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

    # A data já foi adicionada no cabeçalho, então não precisamos mais desta seção
    
    # Simples exibição de uma frase aleatória (motivacional ou dica)
    import random
    import time
    
    # Lista de frases motivacionais com autores
    frases_motivacionais = [
        {"texto": "O sucesso é ir de fracasso em fracasso sem perder o entusiasmo.", "autor": "Winston Churchill"},
        {"texto": "Acredite que você pode, assim você já está no meio do caminho.", "autor": "Theodore Roosevelt"},
        {"texto": "Tudo parece impossível até que seja feito.", "autor": "Nelson Mandela"},
        {"texto": "A persistência é o caminho do êxito.", "autor": "Charles Chaplin"},
        {"texto": "Se você quer algo que nunca teve, precisa fazer algo que nunca fez.", "autor": "Thomas Jefferson"},
        {"texto": "O único lugar onde o sucesso vem antes do trabalho é no dicionário.", "autor": "Albert Einstein"},
        {"texto": "Coragem é a resistência ao medo, domínio do medo – não ausência do medo.", "autor": "Mark Twain"},
        {"texto": "Não encontre falhas, encontre soluções.", "autor": "Henry Ford"},
        {"texto": "O futuro pertence àqueles que acreditam na beleza dos seus sonhos.", "autor": "Eleanor Roosevelt"},
        {"texto": "Grandes mentes discutem ideias; mentes medianas discutem eventos; mentes pequenas discutem pessoas.", "autor": "Eleanor Roosevelt"},
        {"texto": "Você perde 100% dos tiros que não dá.", "autor": "Wayne Gretzky"},
        {"texto": "Transforme suas feridas em sabedoria.", "autor": "Oprah Winfrey"},
        {"texto": "A única limitação para o nosso sucesso de amanhã são as nossas dúvidas de hoje.", "autor": "Franklin D. Roosevelt"},
        {"texto": "O maior erro que você pode cometer é o de ficar o tempo todo com medo de cometer algum.", "autor": "Elbert Hubbard"},
        {"texto": "Faça da sua vida um sonho, e de um sonho, uma realidade.", "autor": "Antoine de Saint-Exupéry"},
        {"texto": "Não espere por oportunidades extraordinárias. Agarre ocasiões comuns e torne-as grandes.", "autor": "Orison Swett Marden"},
        {"texto": "Sorte é o que acontece quando a preparação encontra a oportunidade.", "autor": "Sêneca"},
        {"texto": "Não sonhe pequeno, pois não há magia na pequenez dos sonhos.", "autor": "Donald Trump"},
        {"texto": "A melhor maneira de prever o futuro é criá-lo.", "autor": "Peter Drucker"},
        {"texto": "Quem quer vencer um obstáculo deve armar-se da força do leão e da prudência da serpente.", "autor": "Píndaro"}
    ]
    
    # Lista de dicas profissionais
    dicas_profissionais = [
        "Organizar é mais do que arrumar: é criar soluções práticas e duradouras.",
        "Conheça as necessidades do cliente antes de iniciar qualquer organização.",
        "Cada espaço tem um potencial único — descubra-o e valorize-o.",
        "Setorizar é o segredo para uma organização funcional.",
        "Antes de organizar, ajude o cliente a desapegar do que não faz mais sentido.",
        "Produtos organizadores são aliados, mas não substituem um bom projeto de organização.",
        "Priorize a funcionalidade, depois pense na estética.",
        "A organização deve ser fácil de manter, não só bonita de ver.",
        "Ouça atentamente o que o cliente quer — a organização deve refletir o estilo de vida dele.",
        "Etiquetas são pequenas, mas fazem uma diferença enorme na manutenção da organização.",
        "Todo item precisa ter seu lugar definido para evitar a bagunça no dia a dia.",
        "Menos é mais: simplificar é um dos maiores luxos na organização.",
        "Crie sistemas de organização que economizem tempo para quem usa o espaço.",
        "Trabalhe com planejamento: cada espaço organizado deve ter começo, meio e fim claros.",
        "O sucesso do seu trabalho é medido pela praticidade que o cliente sente depois.",
        "Use materiais de qualidade — eles elevam o resultado e a satisfação do cliente.",
        "Mantenha-se atualizada: técnicas e tendências de organização evoluem constantemente.",
        "Seja discreta e respeitosa: cada cliente confia a você sua intimidade.",
        "Organização não é impor regras, é criar soluções sob medida para cada realidade.",
        "Um bom Personal Organizer transforma espaços e também transforma vidas."
    ]
    
    # Escolher aleatoriamente entre mostrar uma frase motivacional ou uma dica
    random.seed(int(time.time()) % 100000)
    
    if random.choice([True, False]):
        # Mostrar uma frase motivacional
        frase = random.choice(frases_motivacionais)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <p style="font-style: italic; color: #1E366F; margin: 0; font-size: 1.1rem; font-weight: 500;">
                "{frase['texto']}"
            </p>
            <p style="color: #4A6FA5; margin: 8px 0 0 0; font-size: 0.85rem; text-align: right; font-weight: 500;">
                — {frase['autor']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mostrar uma dica profissional
        dica = random.choice(dicas_profissionais)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <p style="color: #FF9800; font-weight: bold; font-size: 0.9rem; margin-bottom: 5px;">
                💡 DICA PROFISSIONAL
            </p>
            <p style="color: #333; margin: 0; font-size: 1.05rem;">
                {dica}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Dashboard layout com cards modernos
    # Primeira linha - 3 cartões de métricas principais
    col_metricas1, col_metricas2, col_metricas3 = st.columns(3)

    # Obter dados
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
    except Exception as e:
        st.warning("Erro ao carregar propostas")
        propostas = pd.DataFrame()
        propostas_em_aberto = 0

    # Financeiro
    try:
        financeiro = st.session_state.db.get_financeiro()
        
        # Valores a Receber
        if not financeiro.empty:
            # Considerar receitas, receitas a receber e lançamentos na classificação contas_a_receber pendentes
            valores_receber = financeiro[
                (((financeiro['tipo'] == 'receita') | (financeiro['tipo'] == 'receita_a_receber') | 
                  (financeiro['tipo'] == 'Receita')) | 
                 (financeiro['classificacao'] == 'contas_a_receber')) & 
                (financeiro['status'] == 'Pendente')
            ]['valor'].sum()
            
            # Valores a Pagar (despesas pendentes)
            valores_pagar = financeiro[
                ((financeiro['tipo'] == 'despesa') | 
                 (financeiro['tipo'] == 'despesa_a_pagar') |
                 (financeiro['classificacao'] == 'contas_a_pagar')) & 
                (financeiro['status'] == 'Pendente')
            ]['valor'].sum()
        else:
            valores_receber = 0.0
            valores_pagar = 0.0
            
        # Calcular saldo líquido
        saldo_liquido = valores_receber - valores_pagar
        
    except Exception as e:
        st.warning(f"Erro ao carregar dados financeiros: {str(e)}")
        valores_receber = 0.0
        valores_pagar = 0.0
        saldo_liquido = 0.0

    # Cartão 1: Total de Clientes
    with col_metricas1:
        # Estatísticas básicas
        total_clientes = len(clientes) if not clientes.empty else 0
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1E366F, #2A4D8F); 
             color: white; padding: 20px; border-radius: 10px; 
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center;">
                <span style="background-color: rgba(255,255,255,0.2); 
                       border-radius: 50%; width: 32px; height: 32px; 
                       display: flex; align-items: center; justify-content: center;
                       margin-right: 10px;">👥</span>
                <span><strong>Clientes</strong></span>
            </div>
            <div style="font-size: 2rem; font-weight: bold; margin: 5px 0;">{}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Total de clientes cadastrados</div>
        </div>
        """.format(total_clientes), unsafe_allow_html=True)

    # Cartão 2: Propostas em Aberto
    with col_metricas2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FF9800, #FF5722); 
             color: white; padding: 20px; border-radius: 10px; 
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center;">
                <span style="background-color: rgba(255,255,255,0.2); 
                       border-radius: 50%; width: 32px; height: 32px; 
                       display: flex; align-items: center; justify-content: center;
                       margin-right: 10px;">📝</span>
                <span><strong>Propostas</strong></span>
            </div>
            <div style="font-size: 2rem; font-weight: bold; margin: 5px 0;">{}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Propostas em aberto</div>
        </div>
        """.format(propostas_em_aberto), unsafe_allow_html=True)

    # Cartão 3: Saldo Financeiro
    with col_metricas3:
        cor_fundo = "#4CAF50" if saldo_liquido >= 0 else "#F44336"
        cor_secundaria = "#388E3C" if saldo_liquido >= 0 else "#D32F2F"
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, {0}, {1}); 
             color: white; padding: 20px; border-radius: 10px; 
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center;">
                <span style="background-color: rgba(255,255,255,0.2); 
                       border-radius: 50%; width: 32px; height: 32px; 
                       display: flex; align-items: center; justify-content: center;
                       margin-right: 10px;">💰</span>
                <span><strong>Saldo</strong></span>
            </div>
            <div style="font-size: 2rem; font-weight: bold; margin: 5px 0;">R$ {2:,.2f}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                <span style="margin-right: 10px;">📥 R$ {3:,.2f}</span>
                <span>📤 R$ {4:,.2f}</span>
            </div>
        </div>
        """.format(cor_fundo, cor_secundaria, saldo_liquido, valores_receber, valores_pagar), unsafe_allow_html=True)

    # Segunda linha - Propostas em aberto e aniversariantes
    col1, col2 = st.columns([2, 1])
    
    with col1:
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

    with col2:
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
            <h4 style='color: #F1A208; margin: 0; font-size: 1rem;'>⏱️ Clientes aguardando retorno (faltam até 15 dias para completar 60 dias)</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Verificar se propostas está vazio ou se tem a coluna status
        if not isinstance(propostas, pd.DataFrame) or propostas.empty or 'status' not in propostas.columns:
            propostas_executadas = pd.DataFrame()
        else:
            # Buscar todas as propostas executadas
            propostas_executadas = propostas[propostas['status'].isin(['Executada', 'Em execução', 'Finalizada', 'Concluída'])]
            
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
                    campos_obrigatorios = ['id', 'numero', 'descricao']
                    if not all(campo in proposta for campo in campos_obrigatorios):
                        continue  # Pula se faltar algum campo obrigatório
                    
                    # Decidir qual data usar para cálculo:
                    # Para propostas finalizadas, usar data_fim (data de conclusão)
                    # Para outras propostas, usar data_inicio
                    data_referencia = None
                    
                    # Para propostas finalizadas ou concluídas, preferir a data_fim
                    if (proposta['status'] == 'Finalizada' or proposta['status'] == 'Concluída') and pd.notna(proposta.get('data_fim')):
                        data_campo = proposta['data_fim']
                        campo_nome = "data_fim"
                    # Para outras propostas ou se não tiver data_fim, usar data_inicio
                    elif pd.notna(proposta.get('data_inicio')):
                        data_campo = proposta['data_inicio']
                        campo_nome = "data_inicio"
                    else:
                        continue  # Se não tem nenhuma data válida, pular esta proposta
                    
                    # Converter para datetime se for string
                    if isinstance(data_campo, str):
                        try:
                            data_referencia = datetime.strptime(data_campo, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                data_referencia = datetime.strptime(data_campo, '%d/%m/%Y').date()
                            except ValueError:
                                continue  # Se não conseguir converter, pula
                    else:
                        data_referencia = data_campo.date() if hasattr(data_campo, 'date') else data_campo
                        
                    # Calcular a data que será 60 dias após a data de referência
                    data_60_dias = data_referencia + timedelta(days=60)
                    
                    # Calcular quantos dias faltam para atingir 60 dias
                    try:
                        dias_restantes = (data_60_dias - hoje).days
                        
                        # Se faltar 15 dias ou menos (e ainda não tiver passado), mostrar alerta
                        if 0 <= dias_restantes <= 15:
                            # Garantir que todos os valores sejam do tipo correto para evitar comparações incompatíveis
                            prop_id = int(proposta['id']) if not pd.isna(proposta['id']) else 0
                            prop_numero = int(proposta['numero']) if not pd.isna(proposta['numero']) else 0
                            
                            propostas_alerta.append({
                                'id': prop_id,
                                'numero': prop_numero,
                                'cliente_nome': str(proposta.get('cliente_nome', 'Cliente não informado')),
                                'descricao': str(proposta['descricao']) if not pd.isna(proposta['descricao']) else "",
                                'data_referencia': data_referencia,
                                'campo_nome': campo_nome,
                                'dias_restantes': dias_restantes,
                                'data_60_dias': data_60_dias
                            })
                    except Exception as e:
                        # Ignorar essa proposta caso ocorra algum erro de tipo
                        continue
                
                # Ordenar por dias restantes (mais urgentes primeiro)
                propostas_alerta.sort(key=lambda x: x['dias_restantes'])
                
                # Mostrar alertas
                if propostas_alerta:
                    for p in propostas_alerta:
                        with st.container():
                            st.markdown(f"""
                            <div style='background-color: #2A3F5F; 
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
                                    {('Data de conclusão' if p['campo_nome'] == 'data_fim' else 'Data da organização')}: {format_date_safe(p['data_referencia'])} | Completará 60 dias em: {format_date_safe(p['data_60_dias'])}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Não há clientes aguardando retorno no momento.")
            else:
                st.info("Não há propostas em execução no sistema.")
        except Exception as e:
            st.warning("Erro ao processar alertas de retorno ao cliente.")