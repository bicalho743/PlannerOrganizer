import streamlit as st
from utils.analytics_injector import inject_seo_meta_tags, inject_seo_headings, inject_structured_data, inject_organization_schema

def main():
    """
    Página landing otimizada para SEO baseada no conteúdo HTML fornecido
    """
    
    # Configurar página
    st.set_page_config(
        page_title="Planner Organizer | Sistema de Gestão para Personal Organizer",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Implementar SEO completo
    inject_seo_meta_tags(
        page_title="Planner Organizer | Sistema de Gestão para Personal Organizer",
        description="Planner Organizer é o sistema ideal para personal organizers que desejam profissionalizar a gestão, criar propostas personalizadas e organizar seus atendimentos.",
        keywords="personal organizer, sistema organizador, gestão clientes, propostas, organização profissional, planner, organizador pessoal, gestão para personal organizer"
    )
    inject_seo_headings()
    inject_structured_data()
    inject_organization_schema()
    
    # CSS personalizado para melhorar apresentação
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .cta-button {
        background: #28a745;
        color: white;
        padding: 12px 30px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal com H1 otimizado para SEO
    st.markdown("""
    <div class="main-header">
        <h1>Planner Organizer: sistema de gestão para Personal Organizer</h1>
        <p style="font-size: 1.2rem; margin-top: 1rem;">
            Sistema completo para profissionalizar sua carreira como Personal Organizer
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Conteúdo principal otimizado para SEO
    st.markdown("""
    <p>Se você é uma <strong>personal organizer</strong> e busca mais eficiência, praticidade e organização no seu dia a dia, o <strong>Planner Organizer</strong> foi feito para você. Nosso sistema foi desenvolvido especialmente para atender às necessidades da <strong>organização profissional</strong>, centralizando informações, otimizando processos e facilitando o relacionamento com seus clientes.</p>
    """, unsafe_allow_html=True)
    
    # Seção 1: Organização profissional com tecnologia
    st.markdown("""
    <div class="feature-box">
        <h2>Organização profissional com tecnologia</h2>
        <p>A profissão de personal organizer exige controle, planejamento e visão estratégica. Pensando nisso, o Planner Organizer oferece uma plataforma completa e intuitiva, desenhada para que você possa focar no que realmente importa: transformar vidas por meio da <strong>organização profissional</strong>.</p>
        <p>Com o nosso sistema, você gerencia todas as etapas do seu trabalho — desde o primeiro contato com o cliente até o fechamento de propostas e acompanhamento financeiro — tudo em um único lugar, de forma segura e inteligente.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção 2: Sistema de propostas
    st.markdown("""
    <div class="feature-box">
        <h2>Um sistema de propostas feito para você</h2>
        <p>Chega de planilhas confusas ou anotações soltas. Com o <strong>sistema de propostas</strong> do Planner Organizer, você cria, envia e acompanha propostas com agilidade e profissionalismo.</p>
        <p>Nosso editor de propostas é personalizável e permite incluir seus serviços, pacotes, valores e condições com poucos cliques. Além disso, o cliente pode aprovar tudo online, trazendo mais praticidade e agilidade para o seu processo comercial.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção 3: Gestão completa
    st.markdown("""
    <div class="feature-box">
        <h2>Gestão completa para Personal Organizer</h2>
        <p>O <strong>Planner Organizer</strong> é mais do que um gerador de propostas. Ele é um sistema de <strong>gestão para personal organizer</strong>, permitindo acompanhar clientes ativos, organizar orçamentos, registrar visitas técnicas, controlar pagamentos e muito mais.</p>
        <p>Tenha uma visão clara do seu negócio com relatórios simples, gráficos intuitivos e uma experiência de uso pensada especialmente para quem trabalha com organização.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção 4: Por que escolher
    st.markdown("""
    <div class="feature-box">
        <h2>Por que escolher o Planner Organizer?</h2>
        <ul>
            <li>✅ 100% online, sem precisar instalar nada</li>
            <li>✅ Interface simples e elegante, fácil de usar mesmo para quem não tem experiência com tecnologia</li>
            <li>✅ Teste grátis por 7 dias</li>
            <li>✅ Suporte humanizado e feito por quem entende da profissão</li>
            <li>✅ Compatível com celular, tablet e computador</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção final
    st.markdown("""
    <div class="feature-box">
        <h2>Planner Organizer: tecnologia a favor da sua organização</h2>
        <p>Nós entendemos a importância do seu trabalho. E sabemos que cada detalhe da sua rotina pode ser mais leve com as ferramentas certas. Por isso, criamos o <strong>Planner Organizer</strong>, um sistema completo que une tecnologia, praticidade e inteligência para elevar sua carreira como <strong>personal organizer</strong>.</p>
        <p><strong>Experimente agora mesmo.</strong> Cadastre-se e ganhe 7 dias grátis para testar todas as funcionalidades do sistema. Mais organização, mais controle, mais tempo para você.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA principal
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <a href="#" class="cta-button">🚀 TESTE GRÁTIS POR 7 DIAS</a>
            <br><br>
            <p><em>Sem compromisso • Sem cartão de crédito • Acesso completo</em></p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()