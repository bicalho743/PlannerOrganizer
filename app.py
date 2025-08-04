import os
import sys
import streamlit as st
import logging
import pandas as pd
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Execução do script render removida para evitar loops de inicialização

# Corrigir o problema de adaptação de tipos numpy.int64 para PostgreSQL
try:
    from utils.type_conversion_fix import fix_numpy_int64_bug
    success = fix_numpy_int64_bug()
    if success:
        logger.info("Adaptadores para numpy.int* registrados com sucesso")
    else:
        logger.warning("Não foi possível registrar adaptadores para numpy.int*")
except Exception as e:
    logger.error(f"Erro ao importar/executar fix_numpy_int64_bug: {str(e)}")

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
    logger.info(f"Adicionado {project_root} ao sys.path")

from utils.database import Database
from utils.planos import verificar_login  # Importando apenas a função de verificação de login
from utils.analytics_injector import inject_analytics_tags, track_page_view, inject_seo_meta_tags
from utils.ga4_injector import setup_google_analytics
from utils.html_head_injector import inject_head_content
from utils.simple_mobile_fix import apply_mobile_sidebar_fix

# Importar módulo de autenticação Firebase (pode ser comentado para desabilitar temporariamente)
try:
    from utils.firebase_auth import firebase_auth
except ImportError:
    # Fallback para sistemas sem autenticação Firebase
    firebase_auth = None
    st.warning("Módulo Firebase Auth não encontrado. Usando autenticação padrão.")

# Inicialização dos estados da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Estado para controlar a página de login
if 'login_page' not in st.session_state:
    st.session_state.login_page = "login"  # Valores possíveis: login, registrar, recuperar_senha

# Verificar estado para mostrar termos de uso
if "show_termos" not in st.session_state:
    st.session_state.show_termos = False

# Verificar estado para mostrar política de privacidade
if "show_politica" not in st.session_state:
    st.session_state.show_politica = False

# Verificar estado para mostrar página de planos
if "show_planos" not in st.session_state:
    st.session_state.show_planos = False

# Verificar estado para mostrar página de envio de manual
if "show_enviar_manual" not in st.session_state:
    st.session_state.show_enviar_manual = False

# Verificar estado para mostrar página de debug de propostas finalizadas
if "show_debug_propostas_finalizadas" not in st.session_state:
    st.session_state.show_debug_propostas_finalizadas = False

# Estados removidos para evitar complexidade desnecessária

# Configuração inicial da página
st.set_page_config(
    page_title="Planner Organizer | Sistema para Personal Organizers",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Scripts de inicialização removidos para evitar loops

# JavaScript removido para evitar loops infinitos

# Diagnóstico de componentes do sistema
logger.info("🔍 Verificando status dos componentes do sistema...")

# Verificar Firebase Auth
try:
    if firebase_auth is not None:
        logger.info("✅ Firebase Auth: ATIVO")
    else:
        logger.warning("⚠️ Firebase Auth: INATIVO - Usando autenticação padrão")
except Exception as e:
    logger.error(f"❌ Firebase Auth: ERRO - {e}")

# Verificar Database
try:
    if 'db' in st.session_state:
        logger.info("✅ Database: ATIVO")
    else:
        logger.warning("⚠️ Database: NÃO INICIALIZADO")
except Exception as e:
    logger.error(f"❌ Database: ERRO - {e}")

# Verificar variáveis de ambiente críticas
env_vars = ['DATABASE_URL', 'FIREBASE_API_KEY', 'BREVO_API_KEY']
for var in env_vars:
    if os.getenv(var):
        logger.info(f"✅ {var}: CONFIGURADO")
    else:
        logger.warning(f"⚠️ {var}: NÃO CONFIGURADO")

# Função para mostrar termos de uso
def show_termos():
    """Mostra a página de termos de uso"""
    st.session_state.show_termos = True

# Função para mostrar política de privacidade
def show_politica():
    """Mostra a página de política de privacidade"""
    st.session_state.show_politica = True

# Função para mostrar página de planos
def show_planos():
    """Mostra a página de planos"""
    st.session_state.show_planos = True

# Função para mostrar página de envio de manual
def show_enviar_manual():
    """Mostra a página de envio de manual"""
    st.session_state.show_enviar_manual = True

def debug_propostas_finalizadas():
    """Página de debug para filtro de propostas finalizadas"""
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    import os
    from utils.database import Database

    # Configuração da página
    st.set_page_config(
        page_title="Propostas Finalizadas",
        page_icon="🔍",
        layout="wide"
    )

    # TÍTULO DA PÁGINA
    st.title("🔍 DIAGNÓSTICO DE PROPOSTAS FINALIZADAS")
    st.warning("Esta é uma ferramenta de diagnóstico para resolver o problema de filtragem de propostas finalizadas.")

    # Inicializar banco de dados diretamente (sem usar session_state)
    db = Database()

    # Bloco 1: Exibir todas as propostas para diagnóstico
    st.header("📋 Todas as Propostas no Banco")
    todas_propostas = db.get_propostas()

    # Mostrar total de propostas
    st.info(f"Total de propostas no banco de dados: {len(todas_propostas) if not todas_propostas.empty else 0}")

    # Selecionar apenas colunas relevantes para a análise
    colunas_display = ['id', 'numero', 'cliente_nome', 'status', 'status_execucao', 'valor']

    # Criar tabela com todas as propostas para diagnóstico
    if not todas_propostas.empty:
        st.dataframe(todas_propostas[colunas_display])

        # Detalhamento de cada proposta com seu status
        st.subheader("Detalhamento de Status por Proposta:")
        for idx, p in todas_propostas.iterrows():
            # Verificar se atende aos critérios de filtragem
            status_match = p['status'] == 'Finalizada'
            exec_match = p['status_execucao'] == 'Finalizada'
            recusada_match = p['status'] == 'Recusada'

            if (status_match and exec_match) or recusada_match:
                st.success(f"✅ PROPOSTA #{p['numero']} - {p['cliente_nome']} ATENDE AOS CRITÉRIOS")
                st.write(f"- Status: {p['status']}")
                st.write(f"- Status Execução: {p['status_execucao']}")
            else:
                st.error(f"❌ PROPOSTA #{p['numero']} - {p['cliente_nome']} NÃO ATENDE AOS CRITÉRIOS")
                st.write(f"- Status: {p['status']}")
                st.write(f"- Status Execução: {p['status_execucao']}")
            st.write("---")
    else:
        st.error("Não foram encontradas propostas no banco de dados.")

    # Bloco 2: Testar filtragem diretamente
    st.header("🔎 Teste de Filtragem")

    if not todas_propostas.empty:
        # Aplicar o filtro direto
        propostas_finalizadas = todas_propostas[
            ((todas_propostas['status'] == 'Finalizada') & (todas_propostas['status_execucao'] == 'Finalizada')) |
            (todas_propostas['status'] == 'Recusada')
        ]

        # Mostrar resultado da filtragem
        st.write(f"Total de propostas após filtragem: {len(propostas_finalizadas)}")

        if not propostas_finalizadas.empty:
            st.success("Propostas que atendem aos critérios:")
            # Converter dados para tipos compatíveis com Arrow antes de exibir
            try:
                # Verificar se as colunas existem no dataframe
                available_cols = [col for col in colunas_display if col in propostas_finalizadas.columns]
                if available_cols:
                    df_display = propostas_finalizadas[available_cols].copy()

                    # Garantir que valores monetários sejam convertidos corretamente
                    if 'valor' in df_display.columns:
                        df_display['valor'] = pd.to_numeric(df_display['valor'], errors='coerce')
                        df_display['valor'] = df_display['valor'].fillna(0.0)

                    # Converter todas as colunas object para string para evitar problemas de tipo misto
                    for col in df_display.columns:
                        if df_display[col].dtype == 'object':
                            df_display[col] = df_display[col].astype(str)

                    st.dataframe(df_display)
                else:
                    st.warning("Colunas para exibição não encontradas no dataframe")
            except Exception as e:
                st.error(f"Erro ao exibir tabela: {e}")
                st.write("Dados das propostas:")
                for idx, row in propostas_finalizadas.iterrows():
                    st.write(f"• {row.get('numero', 'N/A')} - {row.get('cliente_nome', 'N/A')} - R$ {row.get('valor', 0):.2f}")

            # Mostrar as propostas que DEVERIAM aparecer na aba
            st.subheader("Propostas Finalizadas (Formato Final):")
            for idx, proposta in propostas_finalizadas.iterrows():
                with st.expander(f"{proposta['numero']} - {proposta['cliente_nome']} - {proposta['descricao']} (R$ {proposta['valor']:.2f})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**ID:** {proposta['id']}")
                        st.write(f"**Cliente:** {proposta['cliente_nome']}")
                        st.write(f"**Descrição:** {proposta['descricao']}")
                        st.write(f"**Valor:** R$ {proposta['valor']:.2f}")

                    with col2:
                        st.write(f"**Tipo:** {proposta['tipo_proposta']}")
                        st.write(f"**Status:** {proposta['status']}")
                        st.write(f"**Status Execução:** {proposta['status_execucao']}")
                        data_inicio_str = proposta['data_inicio'].strftime('%d/%m/%Y') if pd.notna(proposta['data_inicio']) else 'N/D'
                        st.write(f"**Data Início:** {data_inicio_str}")
                        data_fim_str = proposta['data_fim'].strftime('%d/%m/%Y') if pd.notna(proposta['data_fim']) else 'N/D'
                        st.write(f"**Data Fim:** {data_fim_str}")
        else:
            st.warning("Nenhuma proposta atende aos critérios de filtragem!")

    st.divider()

    # Adicionar botão para atualizar a página
    if st.button("🔄 Atualizar Dados"):
        pass  # Removido st.rerun() para evitar loops

    # Adicionar informação sobre a consulta SQL
    st.divider()
    st.subheader("Detalhes da Implementação")
    st.code("""
    # Código de filtro que estamos usando:
    propostas_finalizadas = todas_propostas[
        ((todas_propostas['status'] == 'Finalizada') & (todas_propostas['status_execucao'] == 'Finalizada')) |
        (todas_propostas['status'] == 'Recusada')
    ]
    """, language="python")

    # Adicionar detalhes sobre o banco de dados
    st.write("**Informações de conexão com o banco:**")
    st.code(f"- Database URL: {'Usando variável de ambiente' if 'DATABASE_URL' in os.environ else 'Não configurada'}")
    st.code(f"- Hora da consulta: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Verificações de páginas especiais removidas para evitar loops infinitos com st.stop()

# Verificações de URL removidas para evitar loops com st.stop()

# Inicialização da autenticação in-app
if not st.session_state.authenticated:
    # Ocultar completamente a barra lateral na página de login
    st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Verificar se estamos mostrando termos de uso ou política de privacidade
    query_params = st.query_params

    # Verificar os parâmetros de consulta para os documentos legais
    if "show_termos" in query_params and query_params["show_termos"] == "true":
        try:
            from pages.termos_de_uso import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar os termos de uso: {e}")

    elif "show_politica" in query_params and query_params["show_politica"] == "true":
        try:
            from pages.politica_privacidade import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar a política de privacidade: {e}")

    # Verificar se o usuário está tentando registrar ou recuperar senha
    if st.session_state.login_page == "registrar":
        try:
            # Tentar importar e mostrar a página de registro
            from pages.registrar import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar o módulo de registro: {e}")
            # Resetar para página de login
            st.session_state.login_page = "login"

    elif st.session_state.login_page == "recuperar_senha":
        try:
            # Tentar importar e mostrar a página de recuperação de senha
            from pages.recuperar_senha import show
            show()
            st.stop()  # Parar o fluxo após mostrar a página
        except ImportError as e:
            st.error(f"Não foi possível carregar o módulo de recuperação de senha: {e}")
            # Resetar para página de login
            st.session_state.login_page = "login"

    # Aplicar estilos centralizados
    from utils.styles_manager import StylesManager
    StylesManager.apply_all_fixes()

    # CSS customizado para a página de login
    st.markdown("""
    <style>
    /* BOTÕES DE LOGIN - CORREÇÃO ESPECÍFICA */
    .stButton > button, .stFormSubmitButton > button {
        color: white !important;
        font-weight: 600 !important;
        background-color: #1f4e79 !important;
        border: none !important;
        text-shadow: none !important;
    }
    
    /* Remover TODO espaçamento do HTML e body */
    html, body {
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Ocultar cabeçalho do Streamlit completamente */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ocultar toolbar */
    .stApp > header {
        display: none !important;
    }
    
    /* Remover TODO espaçamento superior da página */
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .main {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding: 0 !important;
    }
    
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
        min-height: auto !important;
    }
    
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding: 1rem !important;
    }
    
    /* Remover espaçamento de containers principais */
    .main-container, .wrapper, .page {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Zerar possível espaçamento do Firebase UI */
    #firebaseui-auth-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Ajustar primeiro elemento visível */
    .element-container:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Forçar botões mais visíveis */
    .stButton > button {
        background-color: #6c757d !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #5a6268 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    
    .login-header {
        font-size: 3rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        margin-top: 0 !important;
        text-align: left;
    }
    
    .login-subtitle {
        font-size: 1.2rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
        text-align: left;
    }
    
    .stats-container {
        display: flex;
        gap: 2rem;
        margin: 2rem 0;
        justify-content: flex-start;
    }
    
    .stat-box {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 20px;
        padding: 2rem 1.5rem;
        text-align: center;
        min-width: 200px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        border-left: 4px solid #e0e0e0;
    }
    
    .stat-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        border-color: #3a75c4;
        border-left-color: #3a75c4;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        font-weight: 500;
    }
    
    .section-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 3rem 0 2rem 0;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin-bottom: 2rem;
    }
    
    .feature-box {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        border-left: 4px solid #e0e0e0;
    }
    
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        border-color: #3a75c4;
        border-left-color: #3a75c4;
    }
    
    .feature-icon {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .feature-desc {
        color: #7f8c8d;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    .testimonial-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin: 3rem 0;
    }
    
    .testimonial-box {
        background: #f8f9fa;
        border: 2px solid #e0e0e0;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        position: relative;
        border-left: 4px solid #e0e0e0;
    }
    
    .testimonial-text {
        color: #555;
        font-style: italic;
        line-height: 1.6;
        margin-bottom: 1rem;
        font-size: 0.95rem;
    }
    
    .testimonial-author {
        color: #3a75c4;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .testimonial-quote {
        position: absolute;
        top: -10px;
        left: 20px;
        background: white;
        color: #3a75c4;
        font-size: 2rem;
        padding: 0 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout principal com duas colunas
    left_col, right_col = st.columns([3, 2])

    with left_col:
        # Cabeçalho principal
        st.markdown('<h1 class="login-header">Planner Organizer</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Sistema Profissional para Personal Organizers</p>', unsafe_allow_html=True)

        # Banner com estatísticas
        st.markdown('''
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-number">+300%</div>
                <div class="stat-label">Aumento na produtividade</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">-25%</div>
                <div class="stat-label">Redução de retrabalho</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">+45%</div>
                <div class="stat-label">Aumento no faturamento</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Seção "Por que escolher o Planner Organizer?"
        st.markdown('<h3 class="section-title">Por que escolher o Planner Organizer?</h3>', unsafe_allow_html=True)

        st.markdown('''
        <div class="feature-grid">
            <div class="feature-box">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Gestão Completa de Propostas</div>
                <div class="feature-desc">
                    Controle todo o ciclo de vida das suas propostas em um único local, 
                    desde a elaboração até a finalização.
                </div>
            </div>
            <div class="feature-box">
                <div class="feature-icon">💰</div>
                <div class="feature-title">Controle Financeiro</div>
                <div class="feature-desc">
                    Gerencie receitas, despesas e comissões de forma automatizada e 
                    integrada com suas propostas.
                </div>
            </div>
            <div class="feature-box">
                <div class="feature-icon">📱</div>
                <div class="feature-title">Acesso de Qualquer Lugar</div>
                <div class="feature-desc">
                    Sistema web responsivo que pode ser acessado de qualquer dispositivo, 
                    a qualquer momento.
                </div>
            </div>
            <div class="feature-box">
                <div class="feature-icon">📄</div>
                <div class="feature-title">Relatórios Profissionais</div>
                <div class="feature-desc">
                    Gere relatórios personalizados para clientes e para controle interno 
                    da sua operação.
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Depoimentos de clientes
        st.markdown('<h3 class="section-title">O que nossos clientes dizem</h3>', unsafe_allow_html=True)

        st.markdown('''
        <div class="testimonial-container">
            <div class="testimonial-box">
                <div class="testimonial-quote">"</div>
                <div class="testimonial-text">
                    "O Planner Organizer transformou meu negócio! Consigo gerenciar todas as minhas propostas, 
                    clientes e finanças em um só lugar com facilidade e profissionalismo."
                </div>
                <div class="testimonial-author">
                    — Ana Paula, Personal Organizer
                </div>
            </div>
            <div class="testimonial-box">
                <div class="testimonial-quote">"</div>
                <div class="testimonial-text">
                    "Meu faturamento aumentou 45% depois que comecei a usar o sistema. A gestão de propostas 
                    e o controle financeiro me ajudaram a profissionalizar meu negócio."
                </div>
                <div class="testimonial-author">
                    — Fernanda Silva, Organizadora Profissional
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Imagem promocional
        st.markdown("<h2>Transforme Seu Negócio com o Planner Organizer</h2>", unsafe_allow_html=True)

        # Imagem da profissional frustrada com papéis/planilhas
        st.image("professional_woman.png", caption="", width=250)
        st.markdown('''
        <div style="background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 8px; margin-top: -20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-weight: 600; color: #4F4F52; font-size: 16px; margin-bottom: 8px;">Chega de dores de cabeça!</div>
            <div style="color: #6C6C70; font-size: 14px; line-height: 1.4;">Abandone as planilhas desorganizadas e os papéis espalhados. Gerencie seu negócio de forma profissional e sem estresse.</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: #4F4F52; margin-top: 0;">Por que escolher o Planner Organizer?</h3>
            <ul style="margin-bottom: 0; padding-left: 25px; color: #1C1C1E;">
                <li style="margin-bottom: 10px;">Interface intuitiva desenvolvida especificamente para personal organizers</li>
                <li style="margin-bottom: 10px;">Acesso de qualquer dispositivo, a qualquer momento</li>
                <li style="margin-bottom: 10px;">Suporte técnico brasileiro especializado</li>
                <li style="margin-bottom: 10px;">Documentação completa e tutoriais em vídeo</li>
                <li>Atualizações constantes com novas funcionalidades</li>
            </ul>
        </div>
        '''
        , unsafe_allow_html=True)

        # CTA (Call to Action) com uma solução para abrir em nova aba usando javascript
        # Isso garante que abrirá em nova aba de forma confiável

        # Usar uma abordagem com JavaScript puro para abrir em nova aba é mais confiável
        current_url = st.query_params
        base_url = f"https://{os.environ.get('REPLIT_SLUG', '')}--{os.environ.get('REPL_OWNER', '')}.repl.co"

        # CTA para download do manual
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0; padding: 2rem; background: linear-gradient(135deg, #f8f9fa, #e9f2ff); border-radius: 16px; box-shadow: 0 8px 16px rgba(0,0,0,0.05);">
            <h3 style="color: #1E366F; margin-bottom: 1rem; font-size: 1.8rem;">📘 Manual Completo do Sistema</h3>
            <p style="color: #5A6A85; font-size: 1.1rem; margin-bottom: 1.5rem;">
                Receba gratuitamente o guia completo com todas as funcionalidades do Planner Organizer
            </p>
            <a href="https://e793124a-608d-4baa-9b36-f1c10d18b5f4-00-er4f29bufe88.worf.replit.dev/enviar_manual" 
               target="_blank" 
               style="display: inline-block; background: linear-gradient(135deg, #026937, #02844a); 
                      color: white; text-align: center; padding: 1rem 2.5rem; text-decoration: none; 
                      border-radius: 12px; font-size: 1.2rem; font-weight: 600;
                      box-shadow: 0 6px 20px rgba(2, 105, 55, 0.3); 
                      transition: all 0.3s ease; border: none;">
                📥 Baixe o Manual Gratuitamente
            </a>
        </div>
        """, unsafe_allow_html=True)

        # Seção de FAQ usando o componente nativo do Streamlit
        st.markdown("## Perguntas Frequentes")

        # Container para o FAQ com borda
        faq_container = st.container(border=True)

        with faq_container:
            # Pergunta 1
            with st.expander("Como o sistema ajuda a manter contato com as clientes?"):
                st.markdown("""
                O sistema possui lembretes automáticos para datas importantes, como aniversários das clientes e datas de follow-up. 
                Você receberá notificações quando uma cliente não contratar seus serviços por mais de 3 meses, permitindo que 
                faça contato no momento certo.
                """)

            # Pergunta 2
            with st.expander("Preciso instalar algum software no meu computador?"):
                st.markdown("""
                Não! O sistema é totalmente baseado na web. Você pode acessá-lo de qualquer dispositivo 
                (computador, tablet ou celular) com acesso à internet, sem necessidade de instalação.
                """)

            # Pergunta 3
            with st.expander("Como funciona o período de teste gratuito?"):
                st.markdown("""
                Você terá acesso completo a todas as funcionalidades do sistema por 7 dias, sem compromisso. 
                Se decidir não continuar, basta cancelar antes do fim do período de teste e não será cobrado(a). 
                Não solicitamos dados de cartão de crédito para o período de teste.
                """)

            # Pergunta 4
            with st.expander("O sistema guarda histórico de atendimentos às clientes?"):
                st.markdown("""
                Sim! Você pode registrar cada atendimento realizado, com data, valores, tipo de serviço e observações. 
                Isso cria um histórico completo que permite analisar quais clientes estão inativas e precisam ser 
                contatadas novamente.
                """)

            # Pergunta 5
            with st.expander("Como organizar propostas no sistema?"):
                st.markdown("""
                Você pode cadastrar todas as suas propostas com detalhes completos, acompanhar o status de cada uma 
                (em elaboração, em execução, finalizada ou recusada), gerar relatórios e ter uma visão clara de sua 
                taxa de conversão e rendimentos. O sistema facilita a organização de todo o fluxo de trabalho.
                """)

        # Adicionando seção de depoimentos/confiança
        st.markdown("""
        ## CONFIADO POR PERSONAL ORGANIZERS DE TODO O BRASIL
        """)

        # Container para mostrar os nomes com styling
        testimonial_cols = st.columns(5)
        with testimonial_cols[0]:
            st.markdown("**Mônica Alves**<br>*Personal Organizer*", unsafe_allow_html=True)
        with testimonial_cols[1]:
            st.markdown("**Ana Prata**<br>*Personal Organizer*", unsafe_allow_html=True)
        with testimonial_cols[2]:
            st.markdown("**Lívia Martins**<br>*Personal Organizer*", unsafe_allow_html=True)
        with testimonial_cols[3]:
            st.markdown("**Isabela Silva**<br>*Personal Organizer*", unsafe_allow_html=True)
        with testimonial_cols[4]:
            st.markdown("**Mariana Costa**<br>*Personal Organizer*", unsafe_allow_html=True)

        # Botão "Ver Planos e Preços" em verde
        st.markdown("""
        <a href="https://promo.plannerorganiza.com.br/planos" 
           target="_blank" 
           id="planos-link" 
           style="display: inline-block; background-color: #026937; color: white; 
                  text-align: center; padding: 1rem 2rem; text-decoration: none; 
                  border-radius: 10px; width: 100%; font-size: 1.2rem; 
                  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); font-weight: 600;
                  transition: all 0.3s ease;">
            Ver Planos e Preços
        </a>
        <script>
            // JavaScript para adicionar efeito hover ao link
            document.getElementById('planos-link').addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.02)';
                this.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.2)';
            });

            document.getElementById('planos-link').addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            });
        </script>
        """, unsafe_allow_html=True)

    with right_col:
        # Título da seção de login, mais próximo das caixas de preenchimento
        st.markdown('''
        <h2 style="text-align: center; color: #4F4F52; margin-top: 0; margin-bottom: 0;">Acesse sua conta</h2>
        ''', unsafe_allow_html=True)

        # JavaScript para interceptar cliques no link de planos
        planos_js = """
        <script>
            document.addEventListener('show_planos', function() {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: true,
                    dataType: 'bool',
                    componentId: 'planos_link'
                }, '*');
            });
        </script>
        """
        # components.html(planos_js, height=0)  # Temporariamente comentado para resolver erro de carregamento

        # Login apenas com e-mail (botões sociais removidos conforme solicitado)

        # Formulário simples - aproximando a mensagem do título
        st.markdown('''
        <div style="text-align: center; margin-top: 5px; margin-bottom: 10px; color: #5A6A85;">
            Entre com seu e-mail e senha para acessar o sistema
        </div>
        ''', unsafe_allow_html=True)

        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
            submit = st.form_submit_button("Entrar na minha conta", use_container_width=True)

            if submit:
                # Tentar login pelo Firebase se disponível
                if firebase_auth is not None:
                    with st.spinner("Autenticando..."):
                        result = firebase_auth.login(email, password)
                        if result['success']:
                            # Configurar tudo ANTES de marcar como autenticado
                            if 'user' in result and 'localId' in result['user']:
                                st.session_state.usuario_id = result['user']['localId']
                                from utils.database import Database
                                st.session_state.db = Database(usuario_id=result['user']['localId'])
                            
                            # Marcar como autenticado
                            st.session_state.authenticated = True
                            st.session_state.current_page = "Dashboard"
                            
                            # Mostrar mensagem de sucesso e atualizar interface
                            st.success("✅ Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro de autenticação: {result['error']}")
                else:
                    st.error("Credenciais inválidas. Verifique seu email e senha.")



        # Botões para navegação - estilo conforme imagem
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Esqueceu sua senha?", key="btn_recuperar_senha", use_container_width=True):
                st.session_state.login_page = "recuperar_senha"
        with col2:
            if st.button("Criar uma conta", key="btn_criar_conta", use_container_width=True):
                st.session_state.login_page = "registrar"

        # A div do container de login foi removida, então não precisamos mais fechar



    # Seção de marcas/clientes
    st.markdown('''
    <div class="brands-section" style="background-color: #f7f7f8; border-radius: 10px; padding: 1.5rem;">
        <p style="color: #4F4F52; font-size: 0.9rem; margin-bottom: 1rem; text-align: center; font-weight: 500;">CONFIADO POR PERSONAL ORGANIZERS DE TODO O BRASIL</p>
        <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;">
            <span style="color: #4F4F52; font-weight: 600; margin: 0 1rem;">Organizze Bem</span>
            <span style="color: #4F4F52; font-weight: 600; margin: 0 1rem;">Armários Perfeitos</span>
            <span style="color: #4F4F52; font-weight: 600; margin: 0 1rem;">Solução Organizada</span>
            <span style="color: #4F4F52; font-weight: 600; margin: 0 1rem;">Limpeza & Ordem</span>
            <span style="color: #4F4F52; font-weight: 600; margin: 0 1rem;">PlanejaSmart</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Rodapé
    st.markdown('''
    <div style="text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #E0E0E0;">
        <p style="color: #5A6A85; font-size: 0.8rem;">
            © 2025 Planner Organizer. Todos os direitos reservados.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # Impede a renderização do resto da aplicação
    st.stop()

# A configuração da página já foi definida no início do arquivo
# Não é permitido chamar st.set_page_config() mais de uma vez por app

# Inicialização do banco de dados
if 'db' not in st.session_state:
    try:
        # Verificar se há um ID de usuário na sessão
        usuario_id = None

        # Verificar st.session_state.usuario_id (mais direto)
        if 'usuario_id' in st.session_state:
            usuario_id = st.session_state.usuario_id


        # Verificar st.session_state.user (Firebase Auth)
        elif 'user' in st.session_state and st.session_state.user and 'localId' in st.session_state.user:
            usuario_id = st.session_state.user['localId']


        # Verificar st.session_state.usuario (alternativa)
        elif 'usuario' in st.session_state and st.session_state.usuario:
            if isinstance(st.session_state.usuario, dict) and 'id' in st.session_state.usuario:
                usuario_id = st.session_state.usuario['id']
                print(f"DEBUG MULTI-TENANT: Encontrado usuario_id={usuario_id} no objeto usuario")

        # Inicializar o Database com o ID do usuário quando disponível
        if usuario_id:
            print(f"DEBUG MULTI-TENANT: Inicializando Database com usuario_id={usuario_id}")
            st.session_state.db = Database(usuario_id=usuario_id)
        else:
            print("DEBUG MULTI-TENANT: AVISO - Inicializando Database sem ID de usuário!")
            # Quando não temos um ID de usuário, inicializamos sem filtro
            st.session_state.db = Database()

        # Removemos a mensagem de sucesso para manter o visual limpo
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        st.warning("Se você estiver usando Neon PostgreSQL ou outro banco de dados serverless, você precisa reativar o endpoint.")

        # Mostrar informação sobre o DATABASE_URL (sem mostrar credenciais)
        db_url = os.getenv('DATABASE_URL', 'Não definido')
        if db_url:
            # Esconder credenciais na mensagem
            safe_url = db_url.split('@')
            if len(safe_url) > 1:
                host_part = safe_url[1]
                st.info(f"Sua conexão de banco de dados aponta para: ...@{host_part}")
            else:
                st.info("DATABASE_URL está definido, mas não está no formato esperado.")
        else:
            st.info("A variável de ambiente DATABASE_URL não está definida.")

        st.error(f"Detalhes do erro: {str(e)}")
        st.stop()

# Carregar CSS customizado centralizado
try:
    with open('.streamlit/style.css', 'r') as f:
        custom_css = f.read()
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    logger.warning("Arquivo style.css não encontrado")
except Exception as e:
    logger.error(f"Erro ao carregar CSS: {e}")

# Sem título na barra lateral - removido conforme solicitação

# CSS para ocultar navegação automática e ajustar a barra lateral
st.markdown("""
<style>
/* === OCULTAR NAVEGAÇÃO AUTOMÁTICA DO STREAMLIT === */

/* Ocultar navegação automática de páginas */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"],
div[data-testid="stSidebar"] nav,
div[data-testid="stSidebar"] ul,
div[data-testid="stSidebar"] li {
    display: none !important;
    visibility: hidden !important;
}

/* Ocultar header/toolbar do desenvolvimento */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
.css-1d391kg, 
.css-1kyxreq, 
.css-1l02zno,
header[data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
}

/* Ocultar menu hambúrguer e settings */
[data-testid="stDeployButton"],
[data-testid="stHeaderToolbar"],
[data-testid="stMainMenuButton"],
button[title="Settings"] {
    display: none !important;
    visibility: hidden !important;
}

/* Ajustar barra lateral */
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Força brutal - ocultar qualquer elemento nav na sidebar */
.css-17eq0hr, .css-1d391kg, .css-1kyxreq, .css-17lntkn {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# JavaScript para criar seta customizada de colapso
st.markdown("""
<script>
let customArrowButton = null;

function createCustomSidebarArrow() {
    // Remover seta existente se houver
    if (customArrowButton) {
        customArrowButton.remove();
    }
    
    // Criar nova seta customizada
    customArrowButton = document.createElement('button');
    customArrowButton.className = 'custom-sidebar-arrow';
    customArrowButton.title = 'Recolher/Expandir Barra Lateral';
    
    // Verificar se a sidebar está visível para definir a direção da seta
    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
        const isCollapsed = sidebar.style.transform === 'translateX(-100%)' || 
                           sidebar.offsetWidth < 50 ||
                           getComputedStyle(sidebar).display === 'none';
        
        if (isCollapsed) {
            customArrowButton.classList.add('sidebar-collapsed');
        }
    }
    
    // Adicionar funcionalidade de clique
    customArrowButton.addEventListener('click', function() {
        // Tentar encontrar o botão original do Streamlit
        const originalButton = document.querySelector('button[data-testid="collapsedControl"]') ||
                              document.querySelector('button[data-testid="baseButton-minimal"]') ||
                              document.querySelector('section[data-testid="stSidebar"] button[kind="secondary"]');
        
        if (originalButton) {
            originalButton.click();
        } else {
            // Fallback: tentar disparar evento customizado
            const sidebarToggleEvent = new CustomEvent('sidebarToggle');
            document.dispatchEvent(sidebarToggleEvent);
        }
        
        // Alternar classe da seta
        setTimeout(() => {
            this.classList.toggle('sidebar-collapsed');
        }, 100);
    });
    
    // Adicionar ao DOM
    document.body.appendChild(customArrowButton);
}

function ensureCustomArrowVisible() {
    // Verificar se a seta customizada existe e está visível
    if (!customArrowButton || !document.body.contains(customArrowButton)) {
        createCustomSidebarArrow();
    }
    
    // Tentar modificar setas originais para serem invisíveis
    const originalButtons = document.querySelectorAll([
        'button[data-testid="collapsedControl"]',
        'button[data-testid="baseButton-minimal"]',
        'section[data-testid="stSidebar"] button[kind="secondary"]'
    ].join(','));
    
    originalButtons.forEach(btn => {
        if (btn && btn !== customArrowButton) {
            btn.style.opacity = '0';
            btn.style.visibility = 'hidden';
            btn.style.pointerEvents = 'none';
        }
    });
}

// Executar quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(createCustomSidebarArrow, 500);
});

// Executar periodicamente para garantir que a seta esteja sempre visível
setInterval(ensureCustomArrowVisible, 1000);

// Observar mudanças no DOM
const observer = new MutationObserver(ensureCustomArrowVisible);
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definição do menu principal
MENU_PRINCIPAL = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "🛒 Vendas": "Vendas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios",
    "🧑‍💼 Meu Perfil": "Perfil"
}

# Adicionar opção de administração se o usuário for admin
if st.session_state.get('autenticado', False) and getattr(st.session_state.get('usuario', None), 'tipo', '') == 'admin':
    MENU_PRINCIPAL["⚙️ Administração"] = "Admin"

# Criação dos botões do menu principal com estilização personalizada
for label, page in MENU_PRINCIPAL.items():
    # Verificar se este é o botão da página atual para destacá-lo
    is_active = st.session_state.current_page == page

    # Aplicar classe personalizada para o botão ativo usando JavaScript
    if is_active:
        # Adicionar código JavaScript para adicionar classe ao botão após ele ser renderizado
        button_id = f"main_menu_{page.lower()}"
        st.sidebar.markdown(f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Aguardar até que o elemento seja renderizado
                setTimeout(function() {{
                    const button = document.querySelector('[data-testid="stButton"] button[kind="secondary"][data-baseweb="button"][aria-keyshortcuts="{button_id}"]');
                    if (button) {{
                        button.classList.add('menu-active');
                    }}
                }}, 100);
            }});
        </script>
        """, unsafe_allow_html=True)

    # Renderizar o botão normalmente
    if st.sidebar.button(label, key=f"main_menu_{page.lower()}", use_container_width=True):
        st.session_state.current_page = page
        # Removido st.rerun() - navegação funciona sem ele

# Adicionar botão de logout
if st.sidebar.button("🚪 Sair do Sistema", 
                     key="btn_logout", 
                     type="secondary", 
                     use_container_width=True,
                     help="Clique para sair do sistema e retornar à tela de login"):
    # Limpar o estado de autenticação
    st.session_state.authenticated = False
    # Exibir mensagem
    st.sidebar.success("Logout realizado com sucesso!")
    # Removido st.rerun() - logout funciona sem reload

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Garantir que usuário autenticado sempre tenha uma página definida
if st.session_state.authenticated:
    # Verificar se não há página definida ou se é primeira vez
    if 'current_page' not in st.session_state or st.session_state.get('show_welcome', True):
        # Definir Dashboard como página inicial
        st.session_state.current_page = "Dashboard"
        st.session_state.show_welcome = False

# Importar o cabeçalho e rodapé padrão
from utils.page_config import apply_page_header, apply_page_footer

# Aplicar o cabeçalho e rodapé em todas as páginas 
apply_page_header()
apply_page_footer()

# Aplicar correção mobile para sidebar
from utils.simple_mobile_fix import apply_mobile_sidebar_fix
apply_mobile_sidebar_fix()

# Roteamento de páginas
try:
    if st.session_state.current_page == "Dashboard":
        from pages.dashboard import show
        show()
    elif st.session_state.current_page == "Cadastros":
        from pages.cadastros import show
        show()
    elif st.session_state.current_page == "Propostas":
        from pages.propostas_unificado import show
        show()
    elif st.session_state.current_page == "Vendas":
        from pages.vendas import show
        show()
    elif st.session_state.current_page == "Financeiro":
        from pages.financeiro import show
        show()
    elif st.session_state.current_page == "Relatórios":
        from pages.relatorios import show
        show()
    elif st.session_state.current_page == "Perfil":
        from pages.perfil import show
        show()
    elif st.session_state.current_page == "Admin":
        # Admin page placeholder - module not yet implemented
        st.title("⚙️ Administração")
        st.info("Módulo de administração em desenvolvimento.")
        st.write("Esta seção estará disponível em breve com funcionalidades administrativas.")
except Exception as e:
    st.error(f"Erro ao carregar página: {str(e)}")

# Divisor antes das informações do sistema
st.sidebar.markdown('<div style="margin: 1.5rem 0;"><hr style="border: none; height: 1px; background-color: #E0E0E0;"></div>', unsafe_allow_html=True)

# CSS para melhorar a visibilidade do texto no expander do sistema
st.sidebar.markdown("""
<style>
/* Estilo específico para o expander de informações do sistema na sidebar */
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent {
    background-color: rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 16px !important;
    margin: 8px 0 !important;
}



/* Melhorar contraste do texto no expander - FORÇAR cor escura para visibilidade */
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent * {
    color: #2c3e50 !important;
    background-color: transparent !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent h1,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent h2,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent h3,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent h4,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent h5,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent h6 {
    color: #1a252f !important;
    font-weight: 700 !important;
    margin-bottom: 12px !important;
    margin-top: 16px !important;
    background-color: transparent !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent p,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent li,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent span,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent div {
    color: #34495e !important;
    line-height: 1.6 !important;
    background-color: transparent !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent strong,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent b {
    color: #1a252f !important;
    font-weight: 700 !important;
    background-color: transparent !important;
}

/* Estilo para o cabeçalho do expander */
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderHeader {
    color: #ffffff !important;
    font-weight: 600 !important;
    background-color: rgba(255, 255, 255, 0.05) !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
}

/* Garantir que listas tenham boa visibilidade */
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent ul,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent ol {
    margin: 8px 0 !important;
    padding-left: 20px !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent ul li,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent ol li {
    color: #34495e !important;
    margin-bottom: 4px !important;
    background-color: transparent !important;
}

/* Forçar cor escura em todos os elementos markdown dentro da sidebar */
section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    color: #2c3e50 !important;
    background-color: transparent !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
    color: #2c3e50 !important;
    background-color: transparent !important;
}

/* Fundo branco para melhor contraste */
section[data-testid="stSidebar"] div[data-testid="stExpander"] .streamlit-expanderContent {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

/* Corrigir botões dentro do expander para ter texto branco */
section[data-testid="stSidebar"] div[data-testid="stExpander"] button[data-testid="baseButton-primary"],
section[data-testid="stSidebar"] div[data-testid="stExpander"] button[data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] div[data-testid="stExpander"] .stDownloadButton button {
    color: #ffffff !important;background-color: #3a75c4 !important;
    border: 1px solid #3a75c4 !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] button[data-testid="baseButton-primary"]:hover,
section[data-testid="stSidebar"] div[data-testid="stExpander"] button[data-testid="baseButton-secondary"]:hover,
section[data-testid="stSidebar"] div[data-testid="stExpander"] .stDownloadButton button:hover {
    color: #ffffff !important;
    background-color: #2B547E !important;
    border: 1px solid #2B547E !important;
}
</style>
""", unsafe_allow_html=True)

# Usando um expander para as informações do sistema
with st.sidebar.expander("ℹ️ Informações do Sistema"):
    st.markdown("### Planner Organizer")
    st.markdown("**Versão:** 1.0.4")

    st.markdown("### Módulos do Sistema:")
    st.markdown("""
    - **Dashboard** - Métricas e alertas
    - **Cadastros** - Clientes, parceiros e fornecedores
    - **Propostas** - Gestão completa de propostas
    - **Vendas** - Controle de produtos vendidos
    - **Financeiro** - Receitas e despesas
    - **Relatórios** - Análises e visualizações
    """)

    st.markdown("### Funcionalidades Principais:")
    st.markdown("""
    - ✅ Fluxo completo de propostas
    - ✅ Integração entre módulos
    - ✅ Sistema de alertas de prazos
    - ✅ Geração de lançamentos financeiros
    - ✅ Cálculo de comissões
    - ✅ Importação em lote
    - ✅ Backup e restauração
    """)

    # Botão para gerar o manual do sistema
    if st.button("📘 Gerar Manual do Sistema", use_container_width=True):
        with st.spinner("Gerando manual em PDF..."):
            try:
                from pages.manual_sistema import gerar_manual_sistema
                pdf_path = gerar_manual_sistema()

                # Ler o arquivo PDF para download
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()

                st.success("Manual gerado com sucesso!")
                st.download_button(
                    label="📥 Baixar Manual do Sistema",
                    data=pdf_bytes,
                    file_name="Manual_Planner_Organizer.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao gerar o manual: {str(e)}")

    # Gerenciar o estado para os modais de termos e política
    if "mostrar_termos" not in st.session_state:
        st.session_state.mostrar_termos = False

    if "mostrar_politica" not in st.session_state:
        st.session_state.mostrar_politica = False

    # Funções para gerenciar os estados dos modais
    def exibir_termos():
        st.session_state.mostrar_termos = True

    def ocultar_termos():
        st.session_state.mostrar_termos = False

    def exibir_politica():
        st.session_state.mostrar_politica = True

    def ocultar_politica():
        st.session_state.mostrar_politica = False

    # Sem rodapé aqui - movido para o footer global

    # Exibir modais conforme o estado
    if st.session_state.mostrar_termos:
        # Criar um modal/dialog para os termos de uso
        with st.container():
            st.markdown("#### Termos de Uso")
            st.markdown("---")

            # Importamos a função do módulo
            from pages.termos_de_uso import get_termos_conteudo

            # Exibimos o conteúdo
            st.markdown(get_termos_conteudo(), unsafe_allow_html=True)

            # Botão para fechar
            if st.button("Fechar", key="fechar_termos", use_container_width=True):
                st.session_state.mostrar_termos = False
                # Removido st.rerun() - modal fecha sem reload

    if st.session_state.mostrar_politica:
        # Criar um modal/dialog para a política de privacidade
        with st.container():
            st.markdown("#### Política de Privacidade")
            st.markdown("---")

            # Importamos a função do módulo
            from pages.politica_privacidade import get_politica_conteudo

            # Exibimos o conteúdo
            st.markdown(get_politica_conteudo(), unsafe_allow_html=True)

            # Botão para fechar
            if st.button("Fechar", key="fechar_politica", use_container_width=True):
                st.session_state.mostrar_politica = False
                # Removido st.rerun() - modal fecha sem reload

    # Botão para download dos ícones do sistema
    try:
        with open("downloads/planner-icons.zip", "rb") as f:
            icones_bytes = f.read()

        st.download_button(
            label="🎨 Baixar Ícones do Sistema",
            data=icones_bytes,
            file_name="planner-icons.zip",
            mime="application/zip",
            use_container_width=True,
            help="Baixe todos os ícones do sistema em diferentes formatos (SVG, PNG, Favicon)"
        )
    except Exception as e:
        st.warning(f"Pacote de ícones não disponível")

# Menu de desenvolvedor removido - acesso direto aos módulos através do menu principal

# A navegação é controlada pelos botões do menu principal
# Os botões já atualizam st.session_state.current_page

# O conteúdo principal já é exibido acima através da importação dos módulos
# Não precisamos processar novamente os módulos
if False:
    module_name = st.session_state.current_page.lower()
    try:
        module = __import__(f"pages.{module_name}", fromlist=["show"])
        module.show()
    except ImportError as e:
        st.error(f"Erro ao carregar módulo {module_name}: {str(e)}")
# Não temos mais a opção de importação no menu
# Rodapé removido - apenas o do page_config.py será usado