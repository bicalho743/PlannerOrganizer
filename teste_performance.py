"""
Teste de Performance e Capacidade para Produção
Simula múltiplos usuários e mede tempos de resposta
"""

import streamlit as st
import time
import threading
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils.database import Database

class TestePerformance:
    def __init__(self):
        self.resultados = []
        self.db = Database()
        
    def teste_conexao_banco(self):
        """Testa velocidade de conexão com banco"""
        tempos = []
        for i in range(10):
            inicio = time.time()
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM propostas")
                    resultado = cursor.fetchone()
                fim = time.time()
                tempos.append(fim - inicio)
            except Exception as e:
                tempos.append(None)
        return tempos
    
    def teste_carregamento_propostas(self):
        """Testa velocidade de carregamento de propostas"""
        inicio = time.time()
        try:
            propostas = self.db.get_propostas()
            fim = time.time()
            return {
                'tempo': fim - inicio,
                'qtd_propostas': len(propostas),
                'sucesso': True
            }
        except Exception as e:
            fim = time.time()
            return {
                'tempo': fim - inicio,
                'erro': str(e),
                'sucesso': False
            }
    
    def teste_api_endpoint(self, endpoint='http://localhost:8000/'):
        """Testa resposta da API"""
        try:
            inicio = time.time()
            response = requests.get(endpoint, timeout=10)
            fim = time.time()
            return {
                'tempo': fim - inicio,
                'status_code': response.status_code,
                'sucesso': response.status_code == 200
            }
        except Exception as e:
            return {
                'tempo': None,
                'erro': str(e),
                'sucesso': False
            }

def show():
    """Interface principal do teste de performance"""
    st.set_page_config(
        page_title="Teste de Performance",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Teste de Performance")
    st.markdown("**Verificação de capacidade e velocidade do sistema**")
    
    teste = TestePerformance()
    
    # Botões de teste
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗄️ Testar Banco", use_container_width=True):
            with st.spinner("Testando conexões com banco..."):
                tempos_banco = teste.teste_conexao_banco()
                
                if any(t is not None for t in tempos_banco):
                    tempo_medio = sum(t for t in tempos_banco if t is not None) / len([t for t in tempos_banco if t is not None])
                    st.success(f"✅ Banco OK - Tempo médio: {tempo_medio:.3f}s")
                    
                    # Gráfico dos tempos
                    fig = px.line(
                        x=range(len(tempos_banco)), 
                        y=tempos_banco,
                        title="Tempos de Resposta do Banco",
                        labels={'x': 'Teste', 'y': 'Tempo (s)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ Problemas na conexão com banco")
    
    with col2:
        if st.button("📄 Testar Propostas", use_container_width=True):
            with st.spinner("Testando carregamento de propostas..."):
                resultado = teste.teste_carregamento_propostas()
                
                if resultado['sucesso']:
                    st.success(f"✅ Propostas OK")
                    st.info(f"📊 {resultado['qtd_propostas']} propostas carregadas em {resultado['tempo']:.3f}s")
                else:
                    st.error(f"❌ Erro: {resultado.get('erro', 'Desconhecido')}")
    
    with col3:
        if st.button("🌐 Testar API", use_container_width=True):
            with st.spinner("Testando API FastAPI..."):
                resultado = teste.teste_api_endpoint()
                
                if resultado['sucesso']:
                    st.success(f"✅ API OK - {resultado['tempo']:.3f}s")
                else:
                    st.error(f"❌ API com problemas: {resultado.get('erro', 'Timeout')}")
    
    # Teste completo
    st.markdown("---")
    if st.button("🚀 Teste Completo de Performance", use_container_width=True):
        with st.spinner("Executando teste completo..."):
            resultados = {
                'Banco de Dados': [],
                'Carregamento de Propostas': [],
                'API FastAPI': []
            }
            
            # Múltiplos testes
            for i in range(5):
                st.write(f"Executando rodada {i+1}/5...")
                
                # Teste banco
                tempos_banco = teste.teste_conexao_banco()
                tempo_medio_banco = sum(t for t in tempos_banco if t is not None) / len([t for t in tempos_banco if t is not None]) if any(t is not None for t in tempos_banco) else None
                resultados['Banco de Dados'].append(tempo_medio_banco)
                
                # Teste propostas
                resultado_propostas = teste.teste_carregamento_propostas()
                resultados['Carregamento de Propostas'].append(resultado_propostas['tempo'] if resultado_propostas['sucesso'] else None)
                
                # Teste API
                resultado_api = teste.teste_api_endpoint()
                resultados['API FastAPI'].append(resultado_api['tempo'] if resultado_api['sucesso'] else None)
                
                time.sleep(1)  # Pausa entre testes
            
            # Mostrar resultados
            st.success("✅ Teste completo finalizado!")
            
            # Criar DataFrame para exibição
            df_resultados = pd.DataFrame(resultados)
            st.subheader("📊 Resultados dos Testes")
            st.dataframe(df_resultados)
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            
            for col, (nome, valores) in zip([col1, col2, col3], resultados.items()):
                with col:
                    valores_validos = [v for v in valores if v is not None]
                    if valores_validos:
                        media = sum(valores_validos) / len(valores_validos)
                        minimo = min(valores_validos)
                        maximo = max(valores_validos)
                        
                        st.metric(
                            f"{nome}",
                            f"{media:.3f}s",
                            f"Min: {minimo:.3f}s | Max: {maximo:.3f}s"
                        )
                        
                        # Indicador de performance
                        if media < 0.5:
                            st.success("🟢 Excelente")
                        elif media < 1.0:
                            st.info("🟡 Bom")
                        else:
                            st.warning("🟠 Melhorar")
                    else:
                        st.error("❌ Falhou")
    
    # Recomendações
    st.markdown("---")
    st.subheader("💡 Recomendações de Performance")
    
    st.info("""
    **Para melhor performance em produção:**
    
    🎯 **Tempos ideais:**
    - Banco de dados: < 0.3s
    - Carregamento de propostas: < 1s
    - API: < 0.5s
    
    ⚡ **Otimizações possíveis:**
    - Cache de consultas frequentes
    - Índices no banco de dados
    - Compressão de imagens
    - CDN para arquivos estáticos
    """)

if __name__ == "__main__":
    show()