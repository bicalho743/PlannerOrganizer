"""
Sistema de Monitoramento para Produção
Monitora performance, erros e saúde geral da aplicação
"""

import streamlit as st
import psutil
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import Database
import logging
import os

class MonitorProducao:
    def __init__(self):
        self.db = Database()
        
    def verificar_saude_banco(self):
        """Verifica se o banco está respondendo"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            return f"Erro: {e}"
    
    def obter_metricas_sistema(self):
        """Coleta métricas do sistema"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memoria_percent': psutil.virtual_memory().percent,
            'disco_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now()
        }
    
    def contar_usuarios_ativos(self):
        """Conta usuários que fizeram login nas últimas 24h"""
        try:
            query = """
            SELECT COUNT(DISTINCT usuario_id) as usuarios_ativos
            FROM propostas 
            WHERE data_criacao >= NOW() - INTERVAL '24 hours'
            """
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
        except:
            return 0
    
    def contar_propostas_hoje(self):
        """Conta propostas criadas hoje"""
        try:
            query = """
            SELECT COUNT(*) as propostas_hoje
            FROM propostas 
            WHERE DATE(data_criacao) = CURRENT_DATE
            """
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
        except:
            return 0
    
    def verificar_logs_erro(self):
        """Verifica logs de erro recentes"""
        logs_erro = []
        try:
            if os.path.exists('app.log'):
                with open('app.log', 'r') as f:
                    linhas = f.readlines()
                    for linha in linhas[-50:]:  # Últimas 50 linhas
                        if 'ERROR' in linha or 'CRITICAL' in linha:
                            logs_erro.append(linha.strip())
        except:
            pass
        return logs_erro

def show():
    """Interface principal do monitor"""
    st.set_page_config(
        page_title="Monitor de Produção",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Monitor de Produção")
    st.markdown("**Monitoramento em tempo real da aplicação**")
    
    monitor = MonitorProducao()
    
    # Atualização automática a cada 30 segundos
    if st.button("🔄 Atualizar Dados"):
        st.rerun()
    
    # Layout em colunas
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas principais
    with col1:
        saude_banco = monitor.verificar_saude_banco()
        if saude_banco == True:
            st.metric("🗄️ Banco de Dados", "🟢 Online")
        else:
            st.metric("🗄️ Banco de Dados", "🔴 Problemas")
            st.error(f"Erro: {saude_banco}")
    
    with col2:
        usuarios_ativos = monitor.contar_usuarios_ativos()
        st.metric("👥 Usuários Ativos (24h)", usuarios_ativos)
    
    with col3:
        propostas_hoje = monitor.contar_propostas_hoje()
        st.metric("📄 Propostas Hoje", propostas_hoje)
    
    with col4:
        metricas = monitor.obter_metricas_sistema()
        st.metric("💻 CPU", f"{metricas['cpu_percent']:.1f}%")
    
    # Gráficos de sistema
    st.subheader("📈 Performance do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de CPU e Memória
        fig_sistema = go.Figure()
        fig_sistema.add_trace(go.Indicator(
            mode = "gauge+number",
            value = metricas['cpu_percent'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "CPU %"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_sistema.update_layout(height=300)
        st.plotly_chart(fig_sistema, use_container_width=True)
    
    with col2:
        # Gráfico de Memória
        fig_memoria = go.Figure()
        fig_memoria.add_trace(go.Indicator(
            mode = "gauge+number",
            value = metricas['memoria_percent'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Memória %"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_memoria.update_layout(height=300)
        st.plotly_chart(fig_memoria, use_container_width=True)
    
    # Logs de erro
    st.subheader("🚨 Logs de Erro Recentes")
    logs_erro = monitor.verificar_logs_erro()
    
    if logs_erro:
        st.error(f"⚠️ Encontrados {len(logs_erro)} erros recentes:")
        for log in logs_erro[-10:]:  # Mostrar apenas os 10 mais recentes
            st.code(log)
    else:
        st.success("✅ Nenhum erro encontrado nos logs recentes!")
    
    # Auto-refresh
    st.markdown("---")
    st.info("💡 **Dica:** Esta página atualiza automaticamente. Use o botão 'Atualizar Dados' para refresh manual.")

if __name__ == "__main__":
    show()