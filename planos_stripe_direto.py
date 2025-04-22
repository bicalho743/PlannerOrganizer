import streamlit as st
import os

def main():
    st.set_page_config(
        page_title="Planos - Planner Organizer",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Planos do Planner Organizer")
    st.markdown("### Escolha o melhor plano para o seu negócio")
    
    # Links diretos do Stripe (estes são links de exemplo, substitua pelos seus links do Stripe)
    link_mensal = "https://buy.stripe.com/test_14k3dG3pL3rI6KQ000"
    link_anual = "https://buy.stripe.com/test_5kA9F26BP1jA4CI004"
    link_vitalicio = "https://buy.stripe.com/test_aEU9F26BPeSEbZ6005"
    
    # Mostrar os planos em colunas
    col1, col2, col3 = st.columns(3)
    
    # Plano Mensal
    with col1:
        st.subheader("Plano Mensal")
        st.markdown("""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; height: 100%;">
            <h4 style="color: #1E88E5; text-align: center;">Mensal</h4>
            <h2 style="text-align: center;">R$ 9,70</h2>
            <p style="text-align: center; color: #666;">por mês</p>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin: 15px 0; font-size: 12px;">
                ✨ 7 DIAS DE TESTE GRÁTIS
            </div>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Acesso a todos os recursos
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Suporte por e-mail
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Cancelamento a qualquer momento
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Ideal para testar o sistema
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <a href="{link_mensal}" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; margin-top: 10px;">
                Assinar Plano Mensal
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    # Plano Anual
    with col2:
        st.subheader("Plano Anual")
        st.markdown("""
        <div style="border: 2px solid #1E88E5; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); height: 100%;">
            <h4 style="color: #1E88E5; text-align: center;">Anual</h4>
            <h2 style="text-align: center;">R$ 97,00</h2>
            <p style="text-align: center; color: #666;">por ano</p>
            <div style="background-color: #1E88E5; color: white; padding: 5px; border-radius: 20px; text-align: center; margin: 15px 0; font-size: 12px; font-weight: bold;">
                ECONOMIZE 17%
            </div>
            <div style="background-color: #e6fff0; color: #00a651; padding: 5px; border-radius: 5px; text-align: center; margin: 15px 0; font-size: 12px;">
                ✨ 7 DIAS DE TESTE GRÁTIS
            </div>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Acesso a todos os recursos
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Suporte prioritário
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Atualizações gratuitas
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Treinamento personalizado
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Melhor custo-benefício
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <a href="{link_anual}" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; margin-top: 10px;">
                Assinar Plano Anual
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    # Plano Vitalício
    with col3:
        st.subheader("Acesso Vitalício")
        st.markdown("""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; height: 100%;">
            <h4 style="color: #1E88E5; text-align: center;">Vitalício</h4>
            <h2 style="text-align: center;">R$ 247,00</h2>
            <p style="text-align: center; color: #666;">pagamento único</p>
            <div style="background-color: #1E88E5; color: white; padding: 5px; border-radius: 20px; text-align: center; margin: 15px 0; font-size: 12px; font-weight: bold;">
                MELHOR VALOR A LONGO PRAZO
            </div>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Acesso permanente ao sistema
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Suporte prioritário
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Sem mensalidades futuras
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Todas as atualizações inclusas
                </li>
                <li style="margin-bottom: 8px; position: relative; padding-left: 25px;">
                    <span style="color: #4CAF50; position: absolute; left: 0;">✓</span> Melhor para longo prazo
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <a href="{link_vitalicio}" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; margin-top: 10px;">
                Adquirir Acesso Vitalício
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    # Informações adicionais
    st.markdown("""
    ### Perguntas Frequentes
    
    **Como funciona o período de teste de 7 dias?**  
    Você terá acesso completo a todas as funcionalidades do sistema durante 7 dias. Só será cobrado após esse período, caso decida continuar.
    
    **Posso cancelar a assinatura quando quiser?**  
    Sim, você pode cancelar sua assinatura a qualquer momento diretamente em sua conta.
    
    **O que está incluído na assinatura?**  
    Todas as funcionalidades do sistema estão incluídas em todos os planos: gerenciamento de clientes, propostas, financeiro, relatórios e muito mais.
    
    **Preciso de cartão de crédito para o período de teste?**  
    Sim, é necessário informar um cartão para criar sua conta, mas você não será cobrado durante o período de teste.
    """)
    
    # Texto sobre segurança
    st.info("""
    💳 **Pagamento Seguro pelo Stripe**: Todos os pagamentos são processados de forma segura.  
    🔒 **Seus dados estão protegidos**: Não armazenamos suas informações de cartão de crédito.
    """)

if __name__ == "__main__":
    main()