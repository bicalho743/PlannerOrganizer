import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from utils.database import Database

def format_currency(value):
    """Formata um valor como moeda brasileira"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_random_color():
    """Retorna uma cor aleatória entre um conjunto de cores pré-definidas do tema"""
    colors = ["#2d8cff", "#4CAF50", "#ff6b6b", "#ffbb33", "#9C27B0", "#FF9800"]
    return random.choice(colors)

def show():
    """Exibe a página de boas-vindas após o login"""
    
    # Configurações básicas
    st.markdown("""
    <style>
    .welcome-header {
        color: #2d8cff;
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        line-height: 1.2;
        text-shadow: 0px 2px 3px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, white, #f5f9ff);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border-left: 4px solid #2d8cff;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d8cff;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #5A6A85;
        font-size: 0.9rem;
    }
    
    .task-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        margin-bottom: 0.7rem;
        border-left: 3px solid #2d8cff;
        transition: all 0.3s ease;
    }
    
    .task-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }
    
    .task-date {
        font-size: 0.8rem;
        color: #9E9E9E;
        font-weight: 400;
    }
    
    .task-title {
        font-size: 1rem;
        font-weight: 600;
        color: #37474F;
        margin: 0.5rem 0;
    }
    
    .task-status {
        display: inline-block;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .status-urgente {
        background-color: #ffebee;
        color: #f44336;
    }
    
    .status-pendente {
        background-color: #fff8e1;
        color: #ffa000;
    }
    
    .status-concluido {
        background-color: #e8f5e9;
        color: #4caf50;
    }
    
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }
    
    .quote-card {
        background: linear-gradient(135deg, #E3F2FD, #bbdefb);
        padding: 1.8rem;
        border-radius: 12px;
        position: relative;
        margin-top: 1rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }
    
    .quote-text {
        font-style: italic;
        color: #1E366F;
        margin-bottom: 1rem;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    .quote-author {
        font-weight: 600;
        color: #1976D2;
        font-size: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2d8cff, #0063cc) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(45,140,255,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0063cc, #004a99) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(45,140,255,0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho de boas-vindas
    st.markdown(f'<h1 class="welcome-header">👋 Olá! Bem-vindo(a) de volta</h1>', unsafe_allow_html=True)
    st.markdown("**Planner Organizer** - Sistema Profissional para Personal Organizers", unsafe_allow_html=True)
    
    # Data atual em formato brasileiro
    hoje = datetime.now()
    data_formatada = hoje.strftime("%d de %B de %Y")
    # Tradução do mês para português
    meses_pt = {
        "January": "janeiro", "February": "fevereiro", "March": "março",
        "April": "abril", "May": "maio", "June": "junho",
        "July": "julho", "August": "agosto", "September": "setembro",
        "October": "outubro", "November": "novembro", "December": "dezembro"
    }
    for mes_en, mes_pt in meses_pt.items():
        data_formatada = data_formatada.replace(mes_en, mes_pt)
    
    st.markdown(f"📅 **{data_formatada}**")
    st.markdown("---")
    
    # Layout principal - Colunas para métricas e atividades
    col_metricas, col_direita = st.columns([2, 1])
    
    # Seção de métricas principais
    with col_metricas:
        st.subheader("📊 Resumo do Seu Negócio")
        
        # Métricas em 3 colunas
        m1, m2, m3 = st.columns(3)
        
        with m1:
            # Tenta obter dados reais, caso contrário usa mock
            try:
                db = Database()
                propostas_em_andamento = db.session.execute(
                    "SELECT COUNT(*) FROM propostas WHERE status = 'Em execução'"
                ).scalar() or 5
            except:
                propostas_em_andamento = 5
                
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{propostas_em_andamento}</div>
                <div class="metric-label">Propostas em Execução</div>
            </div>
            """, unsafe_allow_html=True)
        
        with m2:
            # Tenta obter dados reais, caso contrário usa mock
            try:
                db = Database()
                receitas = db.session.execute(
                    "SELECT SUM(valor) FROM financeiro WHERE tipo = 'receita' AND EXTRACT(MONTH FROM data) = EXTRACT(MONTH FROM CURRENT_DATE)"
                ).scalar() or 0
            except:
                receitas = 8750.50
                
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{format_currency(receitas)}</div>
                <div class="metric-label">Receitas do Mês</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m3:
            # Tenta obter dados reais, caso contrário usa mock
            try:
                db = Database()
                clientes = db.session.execute(
                    "SELECT COUNT(*) FROM clientes"
                ).scalar() or 15
            except:
                clientes = 15
                
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{clientes}</div>
                <div class="metric-label">Clientes Cadastrados</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráfico de propostas por status
        st.subheader("📈 Status das Propostas")
        
        # Tenta obter dados reais, caso contrário usa mock
        try:
            db = Database()
            # Utilizando SQLAlchemy para obter dados de status de proposta
            result = db.session.execute(
                "SELECT status, COUNT(*) FROM propostas GROUP BY status ORDER BY COUNT(*) DESC"
            )
            dados_propostas = [(row[0], row[1]) for row in result]
            
            status_propostas = [status for status, _ in dados_propostas]
            contagem_propostas = [contagem for _, contagem in dados_propostas]
        except:
            status_propostas = ["Em execução", "Finalizada", "Em elaboração", "Aprovada", "Aguardando aprovação"]
            contagem_propostas = [5, 12, 3, 2, 1]
        
        # Gráfico de barras para status das propostas
        st.bar_chart(
            pd.DataFrame(
                {"Quantidade": contagem_propostas},
                index=status_propostas
            )
        )
        
        # Projetos recentes
        st.subheader("🔍 Projetos Recentes")
        
        # Tenta obter dados reais, caso contrário usa mock
        try:
            db = Database()
            # Utilizando SQLAlchemy para obter projetos recentes
            result = db.session.execute(
                """
                SELECT p.id, p.descricao, p.status, p.data_inicio, c.nome 
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                ORDER BY p.data_inicio DESC LIMIT 4
                """
            )
            projetos_recentes = [(row[0], row[1], row[2], row[3], row[4]) for row in result]
            
            projetos = [
                {
                    "id": p[0], 
                    "descricao": p[1], 
                    "status": p[2], 
                    "data": p[3], 
                    "cliente": p[4]
                } 
                for p in projetos_recentes
            ]
        except:
            hoje = datetime.now()
            projetos = [
                {
                    "id": 45, 
                    "descricao": "Organização Cozinha e Despensa", 
                    "status": "Em execução", 
                    "data": hoje - timedelta(days=2), 
                    "cliente": "Maria Silva"
                },
                {
                    "id": 44, 
                    "descricao": "Organização Closet Master", 
                    "status": "Finalizada", 
                    "data": hoje - timedelta(days=5), 
                    "cliente": "João Santos"
                },
                {
                    "id": 43, 
                    "descricao": "Consultoria de Organização", 
                    "status": "Aguardando aprovação", 
                    "data": hoje - timedelta(days=7), 
                    "cliente": "Lucas Mendes"
                },
                {
                    "id": 42, 
                    "descricao": "Organização Home Office", 
                    "status": "Em elaboração", 
                    "data": hoje - timedelta(days=8), 
                    "cliente": "Ana Oliveira"
                },
            ]
        
        # Exibir projetos recentes
        for projeto in projetos:
            status_class = "status-pendente"
            if projeto["status"] == "Finalizada":
                status_class = "status-concluido"
            elif projeto["status"] == "Em execução":
                status_class = "status-urgente"
            
            if isinstance(projeto["data"], datetime):
                data_formatada = projeto["data"].strftime("%d/%m/%Y")
            else:
                data_formatada = "Data não disponível"
                
            st.markdown(f"""
            <div class="task-card">
                <div class="task-date">{data_formatada}</div>
                <div class="task-title">{projeto["descricao"]} - {projeto["cliente"]}</div>
                <span class="task-status {status_class}">{projeto["status"]}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Acesso rápido
        st.subheader("⚡ Acesso Rápido")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Nova Proposta", key="nova_proposta"):
                st.session_state.current_page = "Propostas"
                st.rerun()
        
        with col2:
            if st.button("👥 Novo Cliente", key="novo_cliente"):
                st.session_state.current_page = "Cadastros"
                st.rerun()
                
        with col3:
            if st.button("💰 Financeiro", key="financeiro"):
                st.session_state.current_page = "Financeiro"
                st.rerun()
    
    # Coluna da direita - Informações complementares
    with col_direita:
        # Lembretes e atividades
        st.subheader("📌 Seus Lembretes")
        
        # Tenta obter dados reais, caso contrário usa mock
        try:
            db = Database()
            # Utilizando SQLAlchemy para obter propostas com prazos avançados
            result = db.session.execute(
                """
                SELECT p.descricao, c.nome, p.data_inicio, 
                       CURRENT_DATE - p.data_inicio AS dias_corridos
                FROM propostas p
                JOIN clientes c ON p.cliente_id = c.id
                WHERE p.status = 'Em execução'
                ORDER BY dias_corridos DESC
                LIMIT 3
                """
            )
            propostas_proximas = [(row[0], row[1], row[2], row[3]) for row in result]
            
            lembretes = []
            for p in propostas_proximas:
                dias = p[3]
                if dias > 55:
                    lembretes.append({
                        "texto": f"Proposta de {p[1]} está há {dias} dias em execução",
                        "prioridade": "alta"
                    })
        except:
            lembretes = [
                {
                    "texto": "Proposta de Maria Silva está há 58 dias em execução",
                    "prioridade": "alta"
                },
                {
                    "texto": "Ligar para fornecedor de produtos",
                    "prioridade": "média"
                },
                {
                    "texto": "Enviar proposta para cliente José",
                    "prioridade": "baixa"
                }
            ]
        
        # Adiciona lembretes gerais caso tenha poucos lembretes
        if len(lembretes) < 3:
            lembretes_gerais = [
                {"texto": "Ligar para fornecedor de produtos", "prioridade": "média"},
                {"texto": "Enviar proposta para cliente José", "prioridade": "baixa"},
                {"texto": "Verificar estoque de materiais", "prioridade": "média"},
                {"texto": "Agendar reunião com assistente", "prioridade": "baixa"}
            ]
            
            while len(lembretes) < 3:
                lembretes.append(lembretes_gerais.pop(0))
        
        # Exibir lembretes
        for lembrete in lembretes:
            cor = "#ff6b6b" if lembrete["prioridade"] == "alta" else ("#ffbb33" if lembrete["prioridade"] == "média" else "#4CAF50")
            st.markdown(f"""
            <div style="padding: 1rem; background-color: white; border-radius: 8px; margin-bottom: 0.8rem; border-left: 3px solid {cor};">
                {lembrete["texto"]}
            </div>
            """, unsafe_allow_html=True)
            
        # Dica do dia
        st.subheader("💡 Dica do Dia")
        
        dicas = [
            "Divida projetos grandes em tarefas menores para aumentar a produtividade.",
            "Mantenha uma agenda de follow-up com seus clientes.",
            "Use etiquetas coloridas para facilitar a identificação de itens.",
            "Invista em fotografias profissionais do antes/depois de seus trabalhos.",
            "Estabeleça metas claras para cada mês do ano.",
            "Solicite depoimentos de clientes satisfeitos para seu marketing.",
            "Acompanhe as tendências de organização em feiras e eventos do setor.",
            "Crie pacotes de serviços com diferentes níveis de preço."
        ]
        
        dica = random.choice(dicas)
        
        st.markdown(f"""
        <div style="padding: 1rem; background-color: #E3F2FD; border-radius: 8px; margin-bottom: 1.5rem;">
            {dica}
        </div>
        """, unsafe_allow_html=True)
        
        # Frase motivacional
        frases = [
            {"texto": "A organização é o primeiro passo para transformar sonhos em realidade.", "autor": "Personal Organizer"},
            {"texto": "Espaços organizados criam mentes tranquilas e vidas produtivas.", "autor": "Marie Kondo"},
            {"texto": "A simplicidade é a sofisticação final.", "autor": "Leonardo da Vinci"},
            {"texto": "Organizar é dar às pessoas a sensação de segurança e controle em suas vidas.", "autor": "Personal Organizer"},
            {"texto": "Para cada minuto gasto organizando, uma hora é ganha.", "autor": "Benjamin Franklin"}
        ]
        
        frase = random.choice(frases)
        
        st.markdown(f"""
        <div class="quote-card">
            <div class="quote-text">"{frase["texto"]}"</div>
            <div class="quote-author">— {frase["autor"]}</div>
        </div>
        """, unsafe_allow_html=True)