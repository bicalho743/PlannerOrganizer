import streamlit as st
import os
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Planos - Planner Organizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado
st.markdown("""
<style>
    /* Estilo geral da página */
    .main {
        background-color: #f9f9f9;
    }
    
    /* Cabeçalho da página */
    .header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #1E366F, #2D8CFF);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    /* Container dos planos */
    .planos-container {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 2rem;
    }
    
    /* Card de plano */
    .plano-card {
        background: white;
        border-radius: 10px;
        padding: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        flex: 1;
        transition: transform 0.3s, box-shadow 0.3s;
        text-align: center;
    }
    
    .plano-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    /* Plano destacado */
    .plano-destaque {
        transform: scale(1.05);
        border: 2px solid #2D8CFF;
        position: relative;
    }
    
    .plano-destaque:hover {
        transform: translateY(-10px) scale(1.05);
    }
    
    /* Bandeira de destaque */
    .destaque-flag {
        position: absolute;
        top: -10px;
        right: -10px;
        background: #ff6b6b;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    
    /* Título do plano */
    .plano-titulo {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E366F;
        margin-bottom: 1rem;
    }
    
    /* Preço do plano */
    .plano-preco {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2D8CFF;
        margin-bottom: 0.5rem;
    }
    
    /* Período do plano */
    .plano-periodo {
        color: #666;
        margin-bottom: 1.5rem;
    }
    
    /* Trial gratuito */
    .free-trial {
        background-color: #e6fff0;
        color: #00a651;
        padding: 8px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    
    /* Lista de benefícios */
    .beneficios ul {
        list-style-type: none;
        padding: 0;
        text-align: left;
        margin-bottom: 2rem;
    }
    
    .beneficios li {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .beneficios li:before {
        content: "✓";
        color: #2D8CFF;
        margin-right: 10px;
        font-weight: bold;
    }
    
    /* Botão de ação */
    .btn-action {
        display: inline-block;
        background: #2D8CFF;
        color: white;
        padding: 12px 25px;
        border-radius: 30px;
        text-decoration: none;
        font-weight: bold;
        transition: all 0.3s;
        border: none;
        cursor: pointer;
        width: 100%;
    }
    
    .btn-action:hover {
        background: #1E366F;
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Seção de depoimentos */
    .depoimentos {
        margin-top: 3rem;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Rodapé */
    .footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid #e0e0e0;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho da página
st.markdown("""
<div class="header">
    <h1>Planner Organizer</h1>
    <p>O sistema ideal para Personal Organizers profissionalizarem seu negócio</p>
</div>
""", unsafe_allow_html=True)

# Breve descrição
st.markdown("""
<h2 style="text-align: center; color: #1E366F; margin-bottom: 2rem;">
    Escolha o plano ideal para o seu negócio
</h2>
<p style="text-align: center; color: #666; max-width: 800px; margin: 0 auto 3rem auto; font-size: 1.1rem;">
    Automatize suas propostas, gerencie clientes e transforme sua organização em resultados financeiros.
    Todos os planos incluem acesso completo a todos os recursos por tempo limitado.
</p>
""", unsafe_allow_html=True)

# Container dos planos
st.markdown('<div class="planos-container">', unsafe_allow_html=True)

# Plano Mensal
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="plano-card">
        <div class="plano-titulo">Plano Mensal</div>
        <div class="plano-preco">R$9,70</div>
        <div class="plano-periodo">por mês</div>
        <div class="free-trial">✨ 7 DIAS DE TESTE GRÁTIS</div>
        <div class="beneficios">
            <ul>
                <li>Acesso a todos os recursos</li>
                <li>Propostas ilimitadas</li>
                <li>Relatórios financeiros</li>
                <li>Suporte por e-mail</li>
                <li>Cancelamento a qualquer momento</li>
            </ul>
        </div>
        <a href="/cadastro?plano=mensal" class="btn-action">Começar Agora</a>
    </div>
    """, unsafe_allow_html=True)

# Plano Anual (destacado)
with col2:
    st.markdown("""
    <div class="plano-card plano-destaque">
        <div class="destaque-flag">RECOMENDADO</div>
        <div class="plano-titulo">Plano Anual</div>
        <div class="plano-preco">R$97,00</div>
        <div class="plano-periodo">por ano</div>
        <div class="free-trial">✨ 7 DIAS DE TESTE GRÁTIS</div>
        <div class="beneficios">
            <ul>
                <li>Todos os benefícios do Plano Mensal</li>
                <li>Economia de 17% em relação ao mensal</li>
                <li>Preços fixos por 12 meses</li>
                <li>Relatórios avançados</li>
                <li>Suporte prioritário</li>
            </ul>
        </div>
        <a href="/cadastro?plano=anual" class="btn-action">Começar Agora</a>
    </div>
    """, unsafe_allow_html=True)

# Plano Vitalício
with col3:
    st.markdown("""
    <div class="plano-card">
        <div class="plano-titulo">Acesso Vitalício</div>
        <div class="plano-preco">R$247,00</div>
        <div class="plano-periodo">pagamento único</div>
        <div style="height: 41px; margin-bottom: 1.5rem;"></div>
        <div class="beneficios">
            <ul>
                <li>Todos os recursos disponíveis</li>
                <li>Acesso vitalício</li>
                <li>Sem mensalidades ou anuidades</li>
                <li>Todas as atualizações futuras</li>
                <li>Suporte prioritário</li>
            </ul>
        </div>
        <a href="/cadastro?plano=vitalicio" class="btn-action">Garantir Acesso Vitalício</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Depoimentos
st.markdown("""
<div class="depoimentos">
    <h2 style="text-align: center; color: #1E366F; margin-bottom: 2rem;">O que nossas clientes dizem</h2>
    
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 20px;">
        <div style="flex: 1; min-width: 300px; background: #f9f9f9; padding: 1.5rem; border-radius: 8px;">
            <p style="font-style: italic; color: #555;">"O Planner Organizer transformou minha forma de trabalhar! Minhas propostas ficam muito mais profissionais e consigo ter controle total do meu negócio."</p>
            <p style="font-weight: bold; color: #1E366F; margin-bottom: 0;">Maria Silva</p>
            <p style="color: #666; margin-top: 5px;">Personal Organizer, São Paulo</p>
        </div>
        
        <div style="flex: 1; min-width: 300px; background: #f9f9f9; padding: 1.5rem; border-radius: 8px;">
            <p style="font-style: italic; color: #555;">"Antes eu perdia horas fazendo propostas e relatórios. Agora faço tudo em minutos e meus clientes adoram o resultado final!"</p>
            <p style="font-weight: bold; color: #1E366F; margin-bottom: 0;">Ana Oliveira</p>
            <p style="color: #666; margin-top: 5px;">Personal Organizer, Rio de Janeiro</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Perguntas frequentes
st.markdown("""
<div style="margin-top: 3rem;">
    <h2 style="text-align: center; color: #1E366F; margin-bottom: 2rem;">Perguntas Frequentes</h2>
    
    <div style="max-width: 800px; margin: 0 auto;">
        <details style="margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <summary style="font-weight: bold; color: #1E366F; cursor: pointer;">Como funciona o período de teste grátis?</summary>
            <p style="padding-top: 1rem; color: #555;">Os planos mensal e anual vêm com 7 dias de teste gratuito. Você só será cobrado após esse período, e pode cancelar a qualquer momento antes do final do teste.</p>
        </details>
        
        <details style="margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <summary style="font-weight: bold; color: #1E366F; cursor: pointer;">Posso mudar de plano depois?</summary>
            <p style="padding-top: 1rem; color: #555;">Sim! Você pode fazer upgrade ou downgrade do seu plano a qualquer momento. Os valores serão ajustados proporcionalmente.</p>
        </details>
        
        <details style="margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <summary style="font-weight: bold; color: #1E366F; cursor: pointer;">O acesso vitalício realmente é para sempre?</summary>
            <p style="padding-top: 1rem; color: #555;">Sim, o acesso vitalício garante que você possa usar o sistema indefinidamente com um único pagamento, sem mensalidades futuras.</p>
        </details>
    </div>
</div>
""", unsafe_allow_html=True)

# Call to action final
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 3rem; background: linear-gradient(135deg, #1E366F, #2D8CFF); border-radius: 10px; color: white;">
    <h2 style="margin-bottom: 1.5rem;">Transforme sua organização em negócio de sucesso</h2>
    <p style="font-size: 1.1rem; margin-bottom: 2rem;">Junte-se a centenas de Personal Organizers que estão profissionalizando seu trabalho</p>
    <a href="#top" style="display: inline-block; background: white; color: #1E366F; padding: 15px 30px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 1.1rem;">Ver Planos Novamente</a>
</div>
""", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div class="footer">
    <p>© 2025 Planner Organizer. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)

# Script para lidar com os botões
st.markdown("""
<script>
    // Implementar navegação entre seções
    document.querySelectorAll('.btn-action').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const plano = e.target.getAttribute('href').split('=')[1];
            window.location.href = `/cadastro?plano=${plano}`;
        });
    });
</script>
""", unsafe_allow_html=True)