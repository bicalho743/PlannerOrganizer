import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from utils.force_spacing_fix import apply_spacing_fix
from utils.currency_formatter import format_currency_br, fmt_brl
from utils.simple_mobile_fix import apply_mobile_sidebar_fix

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
    # Aplicar correção de espaçamento PRIMEIRO
    apply_spacing_fix()
    # Aplicar correção mobile para sidebar
    apply_mobile_sidebar_fix()
    
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
                pass  # Removido st.rerun() para evitar loops
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
        # CSS removido para evitar tags malformadas
        
        st.markdown(f"""
        <div style="text-align: center; margin: -10px 0 25px 0; padding-top: 0; position: relative; top: 0px;">
            <p style="font-style: italic; color: #0D1B2A; margin: 0; font-size: 1.1rem; font-weight: 500;">
                "{frase['texto']}"
            </p>
            <p style="color: #C9A84C; margin: 8px 0 0 0; font-size: 0.85rem; text-align: right; font-weight: 500;">
                — {frase['autor']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mostrar uma dica profissional
        dica = random.choice(dicas_profissionais)
        # CSS para forçar redução do espaçamento
        st.markdown("""
        <style>
        .main .block-container {
            padding-top: 0px !important;
        }
        .stApp > div:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <style>
        /* Força o conteúdo a ficar colado no cabeçalho */
        [data-testid="stAppViewContainer"] > .main > .block-container {{
            padding-top: 5px !important;
            margin-top: 75px !important;
        }}
        </style>
        <div style="text-align: center; margin: -20px 0 25px 0; padding-top: 0; position: relative; top: 0px;">
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
        
        # Limpar dados de propostas para evitar erro Arrow
        if not propostas.empty:
            # Debug: verificar dados problemáticos na coluna valor
            problematic_values = propostas[propostas['valor'].astype(str).str.contains(r'[a-zA-Z]', na=False)]
            if not problematic_values.empty:
                print(f"DEBUG DASHBOARD: Valores problemáticos encontrados na coluna 'valor': {problematic_values[['id', 'valor']].to_dict('records')}")
                
            # Limpar coluna valor - converter nomes para 0
            def clean_valor_dashboard(x):
                if pd.isna(x):
                    return 0.0
                val_str = str(x).strip().lower()
                # Se contém letras (nomes), retorna 0
                if any(char.isalpha() for char in val_str):
                    return 0.0
                try:
                    return float(str(x).replace(',', '.'))
                except:
                    return 0.0
                    
            propostas['valor'] = propostas['valor'].apply(clean_valor_dashboard)
            
            # Contar propostas em elaboração ou aguardando aprovação como "em aberto"
            propostas_em_aberto = len(propostas[
                (propostas['status'] == 'Em elaboração') | 
                (propostas['status'] == 'Aguardando aprovação')
            ])
            
            print(f"DEBUG DASHBOARD: {propostas_em_aberto} propostas em aberto encontradas")
        else:
            propostas_em_aberto = 0
            print("DEBUG DASHBOARD: Nenhuma proposta encontrada")
    except Exception as e:
        print(f"DEBUG DASHBOARD: Erro ao carregar propostas: {str(e)}")
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
                (((financeiro['tipo'] == 'Receita') | (financeiro['tipo'] == 'receita_a_receber') | 
                  (financeiro['tipo'] == 'receita')) | 
                 (financeiro['classificacao'] == 'contas_a_receber')) & 
                (financeiro['status'] == 'Pendente')
            ]['valor'].sum()
            
            # Valores a Pagar (despesas pendentes)
            valores_pagar = financeiro[
                (((financeiro['tipo'] == 'Despesa') | (financeiro['tipo'] == 'despesa_a_pagar') |
                  (financeiro['tipo'] == 'despesa')) |
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
        <div style="background: linear-gradient(135deg, #0D1B2A, #162840); 
             color: white; padding: 20px; border-radius: 10px; 
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center; color: white;">
                <span style="background-color: rgba(255,255,255,0.2); 
                       border-radius: 50%; width: 32px; height: 32px; 
                       display: flex; align-items: center; justify-content: center;
                       margin-right: 10px; color: white;">👥</span>
                <span style="color: white !important;"><strong>Clientes</strong></span>
            </div>
            <div style="font-size: 2rem; font-weight: bold; margin: 5px 0; color: #C9A84C !important;">{}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; color: white !important;">Total de clientes cadastrados</div>
        </div>
        """.format(total_clientes), unsafe_allow_html=True)

    # Cartão 2: Propostas em Aberto
    with col_metricas2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0D1B2A, #162840); 
             color: white; padding: 20px; border-radius: 10px; 
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center; color: white;">
                <span style="background-color: rgba(255,255,255,0.2); 
                       border-radius: 50%; width: 32px; height: 32px; 
                       display: flex; align-items: center; justify-content: center;
                       margin-right: 10px; color: white;">📝</span>
                <span style="color: white !important;"><strong>Propostas</strong></span>
            </div>
            <div style="font-size: 2rem; font-weight: bold; margin: 5px 0; color: #C9A84C !important;">{}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; color: white !important;">Propostas em aberto</div>
        </div>
        """.format(propostas_em_aberto), unsafe_allow_html=True)

    # Cartão 3: Saldo Financeiro
    with col_metricas3:
        cor_fundo = "#0D1B2A"
        cor_secundaria = "#162840"
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, {0}, {1}); 
             color: white; padding: 20px; border-radius: 10px; 
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center; color: white;">
                <span style="background-color: rgba(255,255,255,0.2); 
                       border-radius: 50%; width: 32px; height: 32px; 
                       display: flex; align-items: center; justify-content: center;
                       margin-right: 10px; color: white;">💰</span>
                <span style="color: white !important;"><strong>Saldo</strong></span>
            </div>
            <div style="font-size: 2rem; font-weight: bold; margin: 5px 0; color: #C9A84C !important;">{2}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; color: white !important;">
                <span style="margin-right: 10px; color: white !important;">📥 {3}</span>
                <span style="color: white !important;">📤 {4}</span>
            </div>
        </div>
        """.format(cor_fundo, cor_secundaria, format_currency_br(saldo_liquido), format_currency_br(valores_receber), format_currency_br(valores_pagar)), unsafe_allow_html=True)

    # Segunda linha - Propostas em aberto e aniversariantes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Título com ícone igual à versão de produção
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <span style="font-size: 20px; margin-right: 8px;">📋</span>
            <h3 style="margin: 0; color: #333; font-size: 20px;">Propostas em Aberto</h3>
        </div>
        """, unsafe_allow_html=True)
        if not propostas.empty:
            # Filtrar propostas em aberto (Em elaboração e Aguardando aprovação)
            propostas_abertas = propostas[
                (propostas['status'] == 'Em elaboração') | 
                (propostas['status'] == 'Aguardando aprovação')
            ].sort_values('data_inicio', ascending=False)
            
            if not propostas_abertas.empty:
                print(f"DEBUG DASHBOARD: Exibindo {len(propostas_abertas)} propostas abertas")
                for idx, proposta in propostas_abertas.head(5).iterrows():
                    print(f"DEBUG DASHBOARD: Proposta {idx}: {proposta.to_dict()}")
                    
                    status_emoji = "🔄" if proposta['status'] == 'Em elaboração' else "⏳"
                    numero = proposta.get('numero', 'N/A')
                    descricao = proposta.get('descricao', 'Sem descrição')
                    
                    # Cliente nome para o título
                    cliente_nome = proposta.get('cliente_nome', 'N/A')
                    if pd.isna(cliente_nome) or str(cliente_nome).strip() == '':
                        cliente_nome = 'Cliente não informado'
                    
                    # Criar título do expander com dados seguros
                    titulo_descricao = descricao[:40] + "..." if len(str(descricao)) > 40 else str(descricao)
                    titulo_expander = f"{status_emoji} #{numero} - {cliente_nome} - {titulo_descricao}"
                    
                    with st.expander(titulo_expander):
                        # Cliente
                        cliente_nome = proposta.get('cliente_nome', 'N/A')
                        if pd.isna(cliente_nome) or str(cliente_nome).strip() == '':
                            cliente_nome = 'Cliente não informado'
                        
                        # Valor
                        try:
                            valor = float(proposta['valor']) if not pd.isna(proposta['valor']) else 0.0
                            valor_formatado = fmt_brl(valor)
                        except (ValueError, TypeError):
                            valor_formatado = "R$ 0,00"
                        
                        # Data início
                        data_inicio = proposta.get('data_inicio')
                        if pd.notna(data_inicio) and str(data_inicio).strip() != '':
                            data_inicio_str = format_date_safe(data_inicio)
                        else:
                            data_inicio_str = "Não informada"
                            
                        # Prazo
                        prazo_str = ""
                        previsao_dias = proposta.get('previsao_dias')
                        if pd.notna(previsao_dias) and str(previsao_dias).strip() != '':
                            try:
                                dias = int(float(previsao_dias))
                                if dias > 0:
                                    prazo_str = f"{dias} dias"
                            except (ValueError, TypeError):
                                pass
                        
                        # Status de execução
                        status_execucao = proposta.get('status_execucao', 'N/A')
                        if pd.isna(status_execucao) or str(status_execucao).strip() == '':
                            status_execucao = 'N/A'
                            
                        # Observações
                        observacoes = proposta.get('observacoes', '')
                        if pd.isna(observacoes) or str(observacoes).strip() == '':
                            observacoes = 'Nenhuma observação'
                        else:
                            observacoes = str(observacoes)[:100] + "..." if len(str(observacoes)) > 100 else str(observacoes)
                        
                        # Mostrar informações usando st.write com formatação simples
                        st.write(f"**Cliente:** {cliente_nome}")
                        st.write(f"**Valor:** {valor_formatado}")
                        st.write(f"**Status:** {proposta.get('status', 'N/A')}")
                        st.write(f"**Data Início:** {data_inicio_str}")
                        if prazo_str:
                            st.write(f"**Prazo:** {prazo_str}")
                        st.write(f"**Status Execução:** {status_execucao}")
                        st.write(f"**Observações:** {observacoes}")
                            
                print(f"DEBUG DASHBOARD: Finalizada exibição das propostas abertas")
            else:
                st.info("Nenhuma proposta em elaboração ou aguardando aprovação.")
        else:
            st.info("Nenhuma proposta cadastrada.")

    with col2:
        # Título com ícone igual à versão de produção
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <span style="font-size: 20px; margin-right: 8px;">🎂</span>
            <h3 style="margin: 0; color: #333; font-size: 20px;">Aniversariantes</h3>
        </div>
        """, unsafe_allow_html=True)
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
                <div style='background: linear-gradient(135deg, #0D1B2A, #162840); 
                            padding: 12px 15px; border-radius: 8px; margin-bottom: 15px;'>
                    <div style='color: #C9A84C; margin: 0; font-size: 1rem; font-weight: bold;'>
                        ✨ Hoje
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if not aniversariantes_hoje.empty:
                    for _, aniversariante in aniversariantes_hoje.iterrows():
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #0D1B2A 0%, #162840 100%); 
                                    padding: 12px 15px; border-radius: 6px; margin-bottom: 8px;'>
                            <div style='color: white; font-weight: 600; margin-bottom: 4px;'>
                                ✓ {aniversariante['nome']}
                            </div>
                            <div style='color: #E8F4FD; font-size: 0.85rem;'>
                                📱 {aniversariante.get('telefone', 'Não informado')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='background: #f8f9fa; border: 1px solid #e9ecef; 
                                padding: 12px 15px; border-radius: 6px; margin-bottom: 15px;'>
                        <p style='margin: 0; color: #6c757d; text-align: center;'>
                            Nenhum aniversariante hoje!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            # Aniversariantes do mês atual
            aniversariantes_mes = clientes[
                (clientes['data_aniversario'].notna()) &
                (clientes['data_aniversario'].str.lower().str.endswith(f"/{mes_atual}"))
            ]
            
            with st.container():
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #0D1B2A, #162840); 
                            padding: 12px 15px; border-radius: 8px; margin: 15px 0;'>
                    <div style='color: #C9A84C; margin: 0; font-size: 1rem; font-weight: bold;'>
                        📅 Mês de {nome_mes_completo}
                    </div>
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
                        
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #0D1B2A 0%, #162840 100%); 
                                    padding: 12px 15px; border-radius: 6px; margin-bottom: 8px;'>
                            <div style='color: white; font-weight: 600; margin-bottom: 4px;'>
                                {'✓' if passou else '✓'} {aniversariante['nome']} 
                                <span style='font-weight: normal; color: #E8F4FD; font-size: 0.85rem;'>
                                    ({aniversariante['data_aniversario']})
                                </span>
                            </div>
                            <div style='color: #E8F4FD; font-size: 0.85rem;'>
                                📱 {aniversariante.get('telefone', 'Não informado')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #f8f9fa; border: 1px solid #e9ecef; 
                                padding: 12px 15px; border-radius: 6px; margin-bottom: 15px;'>
                        <p style='margin: 0; color: #6c757d; text-align: center;'>
                            Nenhum aniversariante em {nome_mes_completo}.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            # Próximos aniversariantes (próximos dias)
            st.markdown("""
            <div style='background: linear-gradient(135deg, #0D1B2A, #162840); 
                        padding: 12px 15px; border-radius: 8px; margin: 15px 0;'>
                <div style='color: #C9A84C; margin: 0; font-size: 1rem; font-weight: bold;'>
                    🔜 Próximos 7 dias
                </div>
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
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #0D1B2A 0%, #162840 100%); 
                                padding: 12px 15px; border-radius: 6px; margin-bottom: 8px;'>
                        <div style='color: white; font-weight: 600; margin-bottom: 4px;'>
                            ✓ {proximo['nome']} 
                            <span style='font-weight: normal; color: #E8F4FD; font-size: 0.85rem;'>
                                ({proximo['data_aniversario']})
                            </span>
                        </div>
                        <div style='color: #E8F4FD; font-size: 0.85rem;'>
                            📱 {proximo.get('telefone', 'Não informado')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background: #f8f9fa; border: 1px solid #e9ecef; 
                            padding: 12px 15px; border-radius: 6px; margin-bottom: 15px;'>
                    <p style='margin: 0; color: #6c757d; text-align: center;'>
                        Nenhum aniversariante nos próximos 7 dias.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum cliente cadastrado com data de aniversário.")
            
    # Seção unificada de alertas de Pós-Organização
    st.subheader("📋 Alertas Pós-Organização")
    
    with st.container():
        st.markdown("""
        <div style='background-color: #0D1B2A; padding: 10px; border-radius: 7px; margin-bottom: 15px;'>
            <h4 style='color: #C9A84C; margin: 0; font-size: 1rem;'>📞 Ações Pendentes de Acompanhamento</h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            if 'db' in st.session_state and st.session_state.db:
                df_alertas = st.session_state.db.get_pending_post_actions_for_dashboard()
                
                if not df_alertas.empty:
                    for _, alerta in df_alertas.iterrows():
                        tipo_config = {
                            'agradecimento':   {'icone': '🙏', 'texto': 'Agradecimento',  'cor': '#27ae60', 'dias': 'D+1',  'objetivo': 'Mensagem elegante de encerramento'},
                            'acompanhamento':  {'icone': '📞', 'texto': 'Acompanhamento', 'cor': '#C9A84C', 'dias': 'D+7',  'objetivo': 'Saber como a cliente está se sentindo'},
                            'ajuste_fino':     {'icone': '🔧', 'texto': 'Ajuste fino',    'cor': '#e67e22', 'dias': 'D+30', 'objetivo': 'Propor pequenos ajustes após uso real'},
                            'feedback':        {'icone': '💬', 'texto': 'Feedback',        'cor': '#f39c12', 'dias': 'D+45', 'objetivo': 'Colher opinião genuína da experiência'},
                            'continuidade':    {'icone': '🤝', 'texto': 'Continuidade',    'cor': '#B8943D', 'dias': 'D+60', 'objetivo': 'Oferta elegante de serviço contínuo'},
                            'retorno_tecnico': {'icone': '🔄', 'texto': 'Retorno Técnico', 'cor': '#e74c3c', 'dias': '',     'objetivo': 'Visita técnica agendada'},
                        }
                        
                        at = alerta['action_type'].lower() if isinstance(alerta['action_type'], str) else str(alerta['action_type']).lower()
                        config = tipo_config.get(at, {'icone': '📋', 'texto': at.replace('_', ' ').title(), 'cor': '#0D1B2A', 'dias': '', 'objetivo': ''})
                        
                        try:
                            data_fmt = pd.to_datetime(alerta['due_date']).strftime('%d/%m/%Y')
                        except:
                            data_fmt = str(alerta['due_date'])
                        
                        dias_badge = f"<span style='background:rgba(255,255,255,0.25);padding:2px 8px;border-radius:10px;font-size:0.75em;margin-left:8px;font-weight:600;'>{config['dias']}</span>" if config['dias'] else ""
                        objetivo_txt = f"<div style='color:rgba(255,255,255,0.85);font-size:0.8em;font-style:italic;margin-top:2px;'>{config['objetivo']}</div>" if config['objetivo'] else ""
                        
                        st.markdown(f"""
                        <div style='background-color: {config['cor']}; 
                              padding: 10px 14px; border-radius: 7px; margin-bottom: 8px;'>
                            <div style='font-weight: bold; color: white; display:flex; align-items:center; flex-wrap:wrap;'>
                                {config['icone']} {config['texto']}{dias_badge}
                                <span style='font-weight: normal; color: rgba(255,255,255,0.9); font-size: 0.85em; margin-left:auto;'>
                                    Proposta #{alerta['proposta_numero']} · {data_fmt}
                                </span>
                            </div>
                            <div style='color: white; font-size: 0.9em; margin-top:3px;'>
                                Cliente: <b>{alerta['cliente_nome']}</b>
                            </div>
                            {objetivo_txt}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='background: #f8f9fa; border: 1px solid #e9ecef; 
                                padding: 12px 15px; border-radius: 6px; margin-bottom: 15px;'>
                        <p style='margin: 0; color: #6c757d; text-align: center;'>
                            Nenhuma ação pendente de pós-organização.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Conexão com banco de dados não disponível.")
        except Exception as e:
            st.warning("Erro ao processar alertas de pós-organização.")