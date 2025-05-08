import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path para poder importar os módulos de utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.render_fix import inject_render_compatibility_fix

def show():
    # Injetar script de compatibilidade para o Render (se necessário)
    inject_render_compatibility_fix()
    
    # Configuração da página
    st.title("Planos de Assinatura")
    st.subheader("Escolha o plano ideal para o seu negócio")
    
    # CSS para os cartões de planos
    st.markdown("""
    <style>
    .pricing-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border-top: 4px solid #4F4F52;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }
    
    .pricing-card.featured {
        border-top: 4px solid #4CAF50;
    }
    
    .pricing-card.premium {
        border-top: 4px solid #FFC107;
    }
    
    .plan-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1C1C1E;
        margin-bottom: 0.5rem;
    }
    
    .plan-price {
        font-size: 2rem;
        font-weight: 700;
        color: #1C1C1E;
        margin: 1rem 0;
    }
    
    .plan-period {
        font-size: 0.9rem;
        color: #6C6C70;
        margin-bottom: 1.5rem;
    }
    
    .plan-features {
        list-style-type: none;
        padding: 0;
        margin: 0 0 1.5rem 0;
        flex-grow: 1;
    }
    
    .plan-features li {
        margin-bottom: 0.8rem;
        color: #4F4F52;
        display: flex;
        align-items: center;
    }
    
    .plan-features li::before {
        content: "✓";
        color: #4CAF50;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    .plan-button {
        text-align: center;
        background-color: #4F4F52;
        color: white;
        padding: 0.8rem;
        border-radius: 5px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: block;
        text-decoration: none;
    }
    
    .plan-button:hover {
        background-color: #3A3A3D;
        transform: translateY(-2px);
    }
    
    .plan-button.featured {
        background-color: #4CAF50;
    }
    
    .plan-button.featured:hover {
        background-color: #3d8b40;
    }
    
    .plan-button.premium {
        background-color: #FFC107;
        color: #333;
    }
    
    .plan-button.premium:hover {
        background-color: #e5ac06;
    }
    
    .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 2rem;
    }
    
    .comparison-table th,
    .comparison-table td {
        padding: 1rem;
        text-align: center;
        border-bottom: 1px solid #E0E0E0;
    }
    
    .comparison-table th {
        background-color: #F8F9FA;
        font-weight: 600;
        color: #4F4F52;
    }
    
    .comparison-table tr:hover {
        background-color: #F8F9FA;
    }
    
    .check-icon {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .minus-icon {
        color: #E0E0E0;
    }
    
    @media (max-width: 768px) {
        .pricing-card {
            margin-bottom: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Dividir em três colunas para os planos
    col1, col2, col3 = st.columns(3)
    
    # Plano Básico
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <div class="plan-name">Plano Básico</div>
            <div class="plan-price">R$ 49,90</div>
            <div class="plan-period">por mês</div>
            <ul class="plan-features">
                <li>Até 50 propostas</li>
                <li>Até 30 clientes</li>
                <li>Gestão de propostas</li>
                <li>Controle financeiro básico</li>
                <li>Relatórios mensais</li>
            </ul>
            <a href="#" class="plan-button">Assinar Agora</a>
        </div>
        """, unsafe_allow_html=True)
    
    # Plano Profissional (Destacado)
    with col2:
        st.markdown("""
        <div class="pricing-card featured">
            <div class="plan-name">Plano Profissional</div>
            <div class="plan-price">R$ 89,90</div>
            <div class="plan-period">por mês</div>
            <ul class="plan-features">
                <li>Propostas ilimitadas</li>
                <li>Clientes ilimitados</li>
                <li>Gestão de propostas avançada</li>
                <li>Controle financeiro completo</li>
                <li>Relatórios personalizados</li>
                <li>Suporte prioritário</li>
                <li>Importação/Exportação de dados</li>
            </ul>
            <a href="#" class="plan-button featured">Assinar Agora</a>
        </div>
        """, unsafe_allow_html=True)
    
    # Plano Premium
    with col3:
        st.markdown("""
        <div class="pricing-card premium">
            <div class="plan-name">Plano Premium</div>
            <div class="plan-price">R$ 129,90</div>
            <div class="plan-period">por mês</div>
            <ul class="plan-features">
                <li>Tudo do Plano Profissional</li>
                <li>Módulo de automação</li>
                <li>Integrações com outros sistemas</li>
                <li>API para desenvolvedor</li>
                <li>Painel de BI personalizado</li>
                <li>Consultoria mensal</li>
                <li>Acesso a novos recursos em beta</li>
            </ul>
            <a href="#" class="plan-button premium">Assinar Agora</a>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabela de comparação de recursos
    st.subheader("Comparação de recursos")
    
    st.markdown("""
    <table class="comparison-table">
        <tr>
            <th>Recurso</th>
            <th>Básico</th>
            <th>Profissional</th>
            <th>Premium</th>
        </tr>
        <tr>
            <td>Gestão de Propostas</td>
            <td><span class="check-icon">✓</span></td>
            <td><span class="check-icon">✓</span></td>
            <td><span class="check-icon">✓</span></td>
        </tr>
        <tr>
            <td>Gestão de Clientes</td>
            <td><span class="check-icon">✓</span></td>
            <td><span class="check-icon">✓</span></td>
            <td><span class="check-icon">✓</span></td>
        </tr>
        <tr>
            <td>Controle Financeiro</td>
            <td>Básico</td>
            <td>Completo</td>
            <td>Completo + Previsões</td>
        </tr>
        <tr>
            <td>Relatórios</td>
            <td>Limitados</td>
            <td>Personalizados</td>
            <td>Personalizados + BI</td>
        </tr>
        <tr>
            <td>Importação/Exportação</td>
            <td><span class="minus-icon">-</span></td>
            <td><span class="check-icon">✓</span></td>
            <td><span class="check-icon">✓</span></td>
        </tr>
        <tr>
            <td>Automações</td>
            <td><span class="minus-icon">-</span></td>
            <td><span class="minus-icon">-</span></td>
            <td><span class="check-icon">✓</span></td>
        </tr>
        <tr>
            <td>Integrações</td>
            <td><span class="minus-icon">-</span></td>
            <td>Limitadas</td>
            <td>Completas</td>
        </tr>
        <tr>
            <td>Suporte</td>
            <td>E-mail</td>
            <td>E-mail + Chat</td>
            <td>Prioritário + Telefone</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    # Perguntas frequentes
    st.subheader("Perguntas Frequentes")
    
    with st.expander("Posso mudar de plano a qualquer momento?"):
        st.write("Sim, você pode atualizar ou fazer downgrade do seu plano a qualquer momento. As alterações e cobranças serão proporcionais ao tempo restante da sua assinatura atual.")
    
    with st.expander("Como funciona o período de teste?"):
        st.write("Oferecemos 14 dias de teste gratuito para todos os planos. Você só será cobrado após o término desse período se decidir continuar usando o sistema.")
    
    with st.expander("Quais formas de pagamento são aceitas?"):
        st.write("Aceitamos cartões de crédito e débito das principais bandeiras, além de pagamento via PIX ou boleto bancário para assinaturas anuais.")
    
    with st.expander("Qual a política de reembolso?"):
        st.write("Se você não estiver satisfeito com o serviço, oferecemos reembolso total até 7 dias após a primeira cobrança. Basta entrar em contato com nosso suporte.")
    
    with st.expander("Preciso de cartão de crédito para o período de teste?"):
        st.write("Não é necessário informar dados de pagamento para iniciar o período de teste gratuito. Você só precisará fornecer esses dados se decidir continuar usando o sistema após o término do teste.")

# Permitir que este arquivo seja executado diretamente
if __name__ == "__main__":
    show()