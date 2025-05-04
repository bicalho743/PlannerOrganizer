"""
Página para gerenciar assinatura do Stripe
Esta página permite ao usuário visualizar e gerenciar sua assinatura.
"""
import streamlit as st
from datetime import datetime, timedelta
import os

from utils.auth import verificar_autenticacao
from utils.stripe_integration import (
    criar_checkout_session,
    criar_portal_cliente,
    obter_status_assinatura,
    verificar_limite_atingido
)

# Configuração da página
st.set_page_config(
    page_title="Minha Assinatura",
    page_icon="💳",
    layout="wide"
)

# Verificar autenticação
usuario = verificar_autenticacao()
if not usuario:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Título da página
st.title("Minha Assinatura")
st.markdown("Gerencie sua assinatura e veja detalhes do seu plano atual.")

# Função para formatar data
def formatar_data(data):
    if not data:
        return "Não disponível"
    return data.strftime("%d/%m/%Y")

# Função para mostrar detalhes da assinatura
def exibir_detalhes_assinatura(assinatura):
    """Exibe os detalhes da assinatura do usuário"""
    st.subheader("Detalhes da Assinatura")
    
    status_map = {
        "active": "Ativa",
        "trialing": "Em período de teste",
        "past_due": "Pagamento pendente",
        "canceled": "Cancelada",
        "unpaid": "Não paga",
        "incomplete": "Incompleta",
        "incomplete_expired": "Expirada",
        "sem_assinatura": "Sem assinatura"
    }
    
    status_texto = status_map.get(assinatura.get("status_assinatura"), "Desconhecido")
    tipo_plano = assinatura.get("tipo_plano", "gratuito").capitalize()
    
    # Criar colunas para mostrar detalhes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Status:** {status_texto}")
        st.markdown(f"**Tipo de Plano:** {tipo_plano}")
        
        if assinatura.get("plano_nome"):
            st.markdown(f"**Plano:** {assinatura.get('plano_nome')}")
            
            # Formatação do valor com R$
            valor = assinatura.get("plano_valor", 0)
            intervalo = "mensal" if assinatura.get("plano_intervalo") == "month" else "anual"
            st.markdown(f"**Valor:** R$ {valor:.2f} ({intervalo})")
        
    with col2:
        if assinatura.get("data_inicio"):
            st.markdown(f"**Data de Início:** {formatar_data(assinatura.get('data_inicio'))}")
            st.markdown(f"**Próxima Cobrança:** {formatar_data(assinatura.get('data_fim'))}")
        
        # Botão para gerenciar no portal do Stripe (somente se tiver assinatura ativa)
        if assinatura.get("possui_assinatura") and assinatura.get("status_assinatura") not in ["canceled", "sem_assinatura"]:
            st.markdown("---")
            st.markdown("**Gerenciar sua assinatura** (alterar método de pagamento, cancelar, etc)")
            
            if st.button("Acessar Portal de Gerenciamento", type="primary"):
                with st.spinner("Redirecionando para o portal..."):
                    # Criar sessão do portal do cliente
                    resultado = criar_portal_cliente(usuario["uid"])
                    
                    if "error" in resultado:
                        st.error(f"Erro ao acessar portal: {resultado['error']}")
                    else:
                        # Redirecionar para o portal
                        portal_url = resultado["url"]
                        js = f"""
                        <script>
                        window.open("{portal_url}", "_blank");
                        </script>
                        """
                        st.markdown(js, unsafe_allow_html=True)
                        st.success("Portal aberto em uma nova janela!")

# Função para mostrar uso atual
def exibir_uso_atual(assinatura):
    """Exibe o uso atual do plano em relação aos limites"""
    st.subheader("Uso Atual")
    
    # Verificar se possui limites
    if not assinatura.get("limite_clientes"):
        st.info("Informações de uso disponíveis apenas para assinantes.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    # Clientes
    with col1:
        limite_clientes = assinatura.get("limite_clientes", 0)
        contagem_clientes = assinatura.get("contagem_clientes", 0)
        percentual_clientes = (contagem_clientes / limite_clientes * 100) if limite_clientes > 0 else 0
        
        st.markdown(f"### Clientes")
        st.progress(min(percentual_clientes / 100, 1.0))
        st.markdown(f"{contagem_clientes} de {limite_clientes} clientes utilizados ({percentual_clientes:.1f}%)")
        
        if verificar_limite_atingido(usuario["uid"], "clientes"):
            st.warning("⚠️ Limite atingido")
    
    # Propostas
    with col2:
        limite_propostas = assinatura.get("limite_propostas", 0)
        contagem_propostas = assinatura.get("contagem_propostas", 0)
        percentual_propostas = (contagem_propostas / limite_propostas * 100) if limite_propostas > 0 else 0
        
        st.markdown(f"### Propostas")
        st.progress(min(percentual_propostas / 100, 1.0))
        st.markdown(f"{contagem_propostas} de {limite_propostas} propostas utilizadas ({percentual_propostas:.1f}%)")
        
        if verificar_limite_atingido(usuario["uid"], "propostas"):
            st.warning("⚠️ Limite atingido")
    
    # Produtos
    with col3:
        limite_produtos = assinatura.get("limite_produtos", 0)
        contagem_produtos = assinatura.get("contagem_produtos", 0)
        percentual_produtos = (contagem_produtos / limite_produtos * 100) if limite_produtos > 0 else 0
        
        st.markdown(f"### Produtos")
        st.progress(min(percentual_produtos / 100, 1.0))
        st.markdown(f"{contagem_produtos} de {limite_produtos} produtos utilizados ({percentual_produtos:.1f}%)")
        
        if verificar_limite_atingido(usuario["uid"], "produtos"):
            st.warning("⚠️ Limite atingido")

# Função para mostrar planos disponíveis
def exibir_planos_disponiveis(tipo_plano_atual):
    """Exibe os planos disponíveis para assinatura"""
    st.subheader("Planos Disponíveis")
    
    # Escolher plano
    plano_tab1, plano_tab2 = st.tabs(["Plano Mensal", "Plano Anual"])
    
    with plano_tab1:
        st.markdown("### Plano Inicial")
        st.markdown("**R$ 29,90/mês**")
        st.markdown("- Até 50 clientes")
        st.markdown("- Até 100 propostas")
        st.markdown("- Até 50 produtos")
        st.markdown("- Todas as funcionalidades")
        st.markdown("- Suporte por email")
        
        if tipo_plano_atual == "gratuito":
            if st.button("Assinar Plano Mensal", key="assinar_mensal"):
                with st.spinner("Preparando checkout..."):
                    # Criar sessão de checkout
                    resultado = criar_checkout_session(
                        usuario_id=usuario["uid"],
                        email=usuario["email"],
                        nome=usuario["nome"],
                        plano="mensal"
                    )
                    
                    if "error" in resultado:
                        st.error(f"Erro ao criar checkout: {resultado['error']}")
                    else:
                        # Redirecionar para o checkout
                        checkout_url = resultado["url"]
                        js = f"""
                        <script>
                        window.open("{checkout_url}", "_blank");
                        </script>
                        """
                        st.markdown(js, unsafe_allow_html=True)
                        st.success("Checkout aberto em uma nova janela!")
    
    with plano_tab2:
        st.markdown("### Plano Inicial (Anual)")
        st.markdown("**R$ 299,00/ano** (economia de 17%)")
        st.markdown("- Até 50 clientes")
        st.markdown("- Até 100 propostas")
        st.markdown("- Até 50 produtos")
        st.markdown("- Todas as funcionalidades")
        st.markdown("- Suporte por email")
        
        if tipo_plano_atual == "gratuito":
            if st.button("Assinar Plano Anual", key="assinar_anual"):
                with st.spinner("Preparando checkout..."):
                    # Criar sessão de checkout
                    resultado = criar_checkout_session(
                        usuario_id=usuario["uid"],
                        email=usuario["email"],
                        nome=usuario["nome"],
                        plano="anual"
                    )
                    
                    if "error" in resultado:
                        st.error(f"Erro ao criar checkout: {resultado['error']}")
                    else:
                        # Redirecionar para o checkout
                        checkout_url = resultado["url"]
                        js = f"""
                        <script>
                        window.open("{checkout_url}", "_blank");
                        </script>
                        """
                        st.markdown(js, unsafe_allow_html=True)
                        st.success("Checkout aberto em uma nova janela!")

def main():
    # Verificar se existe uma sessão de checkout
    query_params = st.experimental_get_query_params()
    if "session_id" in query_params:
        session_id = query_params["session_id"][0]
        st.success("Assinatura realizada com sucesso! Obrigado por assinar nosso sistema.")
        # Limpar parâmetros da URL
        st.experimental_set_query_params()
    
    # Obter status da assinatura
    assinatura = obter_status_assinatura(usuario["uid"])
    tipo_plano_atual = assinatura.get("tipo_plano", "gratuito")
    
    # Exibir detalhes
    exibir_detalhes_assinatura(assinatura)
    
    st.markdown("---")
    
    # Exibir uso atual
    exibir_uso_atual(assinatura)
    
    st.markdown("---")
    
    # Exibir planos disponíveis (somente para plano gratuito ou cancelado)
    if tipo_plano_atual == "gratuito" or assinatura.get("status_assinatura") in ["canceled", "sem_assinatura"]:
        exibir_planos_disponiveis(tipo_plano_atual)
    
    # Rodapé
    st.markdown("---")
    st.info("Os pagamentos são processados de forma segura pelo Stripe. Seus dados de cartão de crédito não são armazenados em nossos servidores.")

if __name__ == "__main__":
    main()