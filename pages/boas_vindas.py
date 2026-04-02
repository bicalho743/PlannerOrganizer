import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from utils.database import Database
from sqlalchemy import text

from utils.currency_formatter import fmt_brl as format_currency

def get_random_color():
    """Retorna uma cor aleatória entre um conjunto de cores pré-definidas do tema"""
    colors = ["#C9A84C", "#4CAF50", "#ff6b6b", "#ffbb33", "#9C27B0", "#FF9800"]
    return random.choice(colors)

def show():
    """Exibe a página de boas-vindas após o login"""
    from utils.auth_guard import require_auth
    require_auth()
    
    
    # Configurações básicas
    st.markdown("""
    <style>
    .welcome-header {
        color: #0D1B2A;
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
        border-left: 4px solid #C9A84C;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #C9A84C;
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
        border-left: 3px solid #C9A84C;
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
        background: linear-gradient(135deg, #f5f0e0, #E8D5A3);
        padding: 1.8rem;
        border-radius: 12px;
        position: relative;
        margin-top: 1rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }
    
    .quote-text {
        font-style: italic;
        color: #0D1B2A;
        margin-bottom: 1rem;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    .quote-author {
        font-weight: 600;
        color: #B8943D;
        font-size: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #C9A84C, #B8943D) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(201,168,76,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #B8943D, #A07C30) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(201,168,76,0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Adicionar data fixa com design melhorado
    st.markdown("""
    <div style="text-align: center; background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <span style="font-size: 1.2rem; color: #0D1B2A; font-weight: 500;">📅 25 de abril de 2025</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout principal - Colunas para métricas e atividades
    col_metricas, col_direita = st.columns([2, 1])
    
    # Seção de métricas principais
    with col_metricas:
        
        # Métricas em 3 colunas
        m1, m2, m3 = st.columns(3)
        
        with m1:
            # Obter dados reais do banco de dados
            db = Database()
            propostas_em_andamento = db.session.execute(
                text("SELECT COUNT(*) FROM propostas WHERE status = 'Em execução'")
            ).scalar() or 0
                
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #faf9f7, #f5f0e0); border-radius: 12px; padding: 1.5rem; box-shadow: 0 8px 16px rgba(0,0,0,0.08); text-align: center; transition: all 0.3s ease; height: 100%;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #0D1B2A; margin-bottom: 0.5rem;">{propostas_em_andamento}</div>
                <div style="color: #5A6A85; font-size: 0.9rem; font-weight: 500;">Propostas em Execução</div>
                <div style="margin-top: 0.7rem; font-size: 1.8rem; color: #C9A84C;">📝</div>
            </div>
            """, unsafe_allow_html=True)
        
        with m2:
            # Obter dados reais do banco de dados
            db = Database()
            receitas = db.session.execute(
                text("SELECT COALESCE(SUM(valor), 0) FROM financeiro WHERE tipo = 'receita' AND EXTRACT(MONTH FROM data) = EXTRACT(MONTH FROM CURRENT_DATE)")
            ).scalar() or 0
                
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f7fff7, #e6ffe6); border-radius: 12px; padding: 1.5rem; box-shadow: 0 8px 16px rgba(0,0,0,0.08); text-align: center; transition: all 0.3s ease; height: 100%;">
                <div style="font-size: 2.2rem; font-weight: 700; color: #2E7D32; margin-bottom: 0.5rem;">{format_currency(receitas)}</div>
                <div style="color: #5A6A85; font-size: 0.9rem; font-weight: 500;">Receitas do Mês</div>
                <div style="margin-top: 0.7rem; font-size: 1.8rem; color: #4CAF50;">💰</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m3:
            # Obter dados reais do banco de dados
            db = Database()
            clientes = db.session.execute(
                text("SELECT COUNT(*) FROM clientes")
            ).scalar() or 0
                
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff8f2, #ffeadb); border-radius: 12px; padding: 1.5rem; box-shadow: 0 8px 16px rgba(0,0,0,0.08); text-align: center; transition: all 0.3s ease; height: 100%;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #E65100; margin-bottom: 0.5rem;">{clientes}</div>
                <div style="color: #5A6A85; font-size: 0.9rem; font-weight: 500;">Clientes Cadastrados</div>
                <div style="margin-top: 0.7rem; font-size: 1.8rem; color: #FF9800;">👥</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráfico de propostas por status
        st.subheader("📈 Status das Propostas")
        
        # Obter dados reais do banco de dados
        db = Database()
        # Utilizando SQLAlchemy para obter dados de status de proposta
        result = db.session.execute(
            text("SELECT status, COUNT(*) FROM propostas GROUP BY status ORDER BY COUNT(*) DESC")
        )
        dados_propostas = [(row[0], row[1]) for row in result]
        
        if dados_propostas:
            status_propostas = [status for status, _ in dados_propostas]
            contagem_propostas = [contagem for _, contagem in dados_propostas]
        else:
            status_propostas = []
            contagem_propostas = []
        
        # Gráfico de barras para status das propostas
        st.bar_chart(
            pd.DataFrame(
                {"Quantidade": contagem_propostas},
                index=status_propostas
            )
        )
        
        # Projetos recentes
        st.subheader("🔍 Projetos Recentes")
        
        # Obter projetos recentes do banco de dados
        db = Database()
        # Utilizando SQLAlchemy para obter projetos recentes
        result = db.session.execute(
            text("""
            SELECT p.id, p.descricao, p.status, p.data_inicio, c.nome 
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.data_inicio DESC LIMIT 4
            """)
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
                
            # Define colors based on status
            status_colors = {
                "Finalizada": ["#e8f5e9", "#2E7D32", "#4CAF50"],  # Background, Text, Border
                "Em execução": ["#fff8e1", "#F57C00", "#FFC107"], 
                "Aguardando aprovação": ["#f5f0e0", "#0D1B2A", "#C9A84C"],
                "Cancelada": ["#ffebee", "#C62828", "#EF5350"]
            }
            
            # Use default colors if status doesn't match any known status
            bg_color, text_color, border_color = status_colors.get(
                projeto["status"], 
                ["#f5f5f5", "#757575", "#bdbdbd"]
            )
            
            st.markdown(f"""
            <div style="background-color: white; border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem; border-left: 4px solid {border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center;">
                <div style="flex-grow: 1;">
                    <div style="font-size: 0.8rem; color: #78909C; margin-bottom: 0.5rem;">{data_formatada}</div>
                    <div style="font-weight: 500; color: #263238; font-size: 1rem;">{projeto["descricao"]}</div>
                    <div style="font-size: 0.9rem; color: #546E7A; margin-top: 0.3rem;">{projeto["cliente"]}</div>
                </div>
                <div style="background-color: {bg_color}; padding: 0.4rem 0.8rem; border-radius: 20px; color: {text_color}; font-size: 0.75rem; font-weight: 500;">
                    {projeto["status"]}
                </div>
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
        
        # Obter lembretes do banco de dados
        db = Database()
        # Utilizando SQLAlchemy para obter propostas com prazos avançados
        result = db.session.execute(
            text("""
            SELECT p.descricao, c.nome, p.data_inicio, 
                   CURRENT_DATE - p.data_inicio AS dias_corridos
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.status = 'Em execução'
            ORDER BY dias_corridos DESC
            LIMIT 3
            """)
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
            elif dias > 30:
                lembretes.append({
                    "texto": f"Proposta de {p[1]} está há {dias} dias em execução",
                    "prioridade": "média"
                })
            else:
                lembretes.append({
                    "texto": f"Proposta de {p[1]} iniciada há {dias} dias",
                    "prioridade": "baixa"
                })
        
        # Não usar lembretes fictícios, apenas mostrar os reais
        # Se não houver lembretes, apenas deixar a seção vazia
        
        # Exibir lembretes
        for lembrete in lembretes:
            cor = "#ff6b6b" if lembrete["prioridade"] == "alta" else ("#ffbb33" if lembrete["prioridade"] == "média" else "#4CAF50")
            # Define icons and colors based on priority
            priority_info = {
                "alta": ["🔴", "#FFEBEE", "#C62828", "#EF5350"],  # icon, bg, text, border
                "média": ["🟠", "#FFF3E0", "#E65100", "#FF9800"],
                "baixa": ["🟢", "#E8F5E9", "#2E7D32", "#4CAF50"]
            }
            
            icon, bg_color, text_color, border_color = priority_info.get(
                lembrete["prioridade"], 
                ["⚪", "#F5F5F5", "#757575", "#BDBDBD"]
            )
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; border-radius: 10px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 2px 6px rgba(0,0,0,0.04); border: 1px solid {border_color};">
                <div style="display: flex; align-items: center;">
                    <div style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</div>
                    <div style="color: {text_color}; font-weight: 500; flex-grow: 1;">{lembrete["texto"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Seção de navegação rápida
        st.subheader("🔍 Navegação")
        
        st.markdown("""
        <div style="padding: 1rem; background-color: #f5f0e0; border-radius: 8px; margin-bottom: 1.5rem;">
            Acesse as principais funções através do menu lateral esquerdo.
        </div>
        """, unsafe_allow_html=True)
        
        # Exibir apenas informações dinâmicas do sistema
        st.markdown("""
        <div class="quote-card">
            <div class="quote-text">Planner Organizer - Sistema de Gerenciamento</div>
            <div class="quote-author">— Versão 1.0</div>
        </div>
        """, unsafe_allow_html=True)