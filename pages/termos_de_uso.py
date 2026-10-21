"""
Página de Termos de Uso para o sistema Planner Organizer
"""
import streamlit as st
import os
import sys

project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.texto_legal import CONTATO, para_html, mostrar_pagina

TITULO = "Termos e Condições de Uso"
INTRO = ("Estes termos regem o uso do Planner Organizer, sistema on-line de gestão para profissionais de "
         "organização (propostas, clientes, vendas, financeiro e relatórios). Ao criar uma conta você declara "
         "que leu e concorda com eles e com a nossa Política de Privacidade.")

SECOES = [
    ("1. Conta e acesso", [
        "A conta é pessoal. Você é responsável pelo sigilo do seu login e pelas ações feitas com ele. "
        "Avise-nos em " + CONTATO + " se suspeitar de uso indevido.",
    ], None),
    ("2. Teste grátis e assinatura", [
        "Toda conta nova tem 7 dias de teste grátis com todos os recursos. Depois disso o uso continua "
        "mediante assinatura, mensal ou anual, nos preços exibidos em Plano e cobrança no momento da contratação.",
        "O pagamento é processado pelo Stripe por cartão de crédito e renovado automaticamente ao fim de cada "
        "período até que você cancele. Se uma cobrança falhar, o acesso aos recursos pagos pode ser suspenso "
        "até a regularização.",
    ], None),
    ("3. Cancelamento e reembolso", [
        "Você pode cancelar a qualquer momento pelo portal de cobrança (Plano e cobrança). O cancelamento "
        "interrompe as próximas renovações; o acesso segue até o fim do período já pago.",
        "Na primeira contratação, você pode desistir em até 7 dias do pagamento e receber o valor de volta "
        "(art. 49 do Código de Defesa do Consumidor), escrevendo para " + CONTATO + ".",
    ], None),
    ("4. Seus dados e os dados dos seus clientes", [
        "Os dados que você cadastra (clientes, propostas, fornecedores, valores, logotipo) continuam sendo seus. "
        "Usamos esses dados só para prestar o serviço, como descrito na Política de Privacidade.",
        "Ao cadastrar dados de terceiros, como seus clientes, você é a controladora desses dados perante a LGPD "
        "e deve ter base legal para tratá-los (por exemplo, a execução do contrato com o cliente). "
        "O Planner Organizer atua como operador, tratando esses dados apenas sob suas instruções.",
        "Após o cancelamento seus dados ficam guardados para que você possa voltar. Você pode pedir a exclusão "
        "definitiva a qualquer momento.",
    ], None),
    ("5. Uso permitido", [
        "O sistema deve ser usado para fins lícitos e de acordo com sua finalidade. Não é permitido tentar acessar "
        "dados de outras contas, sobrecarregar ou burlar a plataforma, nem revender o acesso.",
    ], None),
    ("6. Propriedade intelectual", [
        "O software, o design e a marca Planner Organizer pertencem aos seus desenvolvedores. A assinatura dá "
        "direito de uso enquanto estiver ativa e não transfere nenhum desses direitos.",
    ], None),
    ("7. Disponibilidade e responsabilidade", [
        "Trabalhamos para manter o sistema disponível e os dados protegidos, mas podem ocorrer interrupções para "
        "manutenção ou por falhas de terceiros (hospedagem, pagamento, login). Os cálculos e relatórios são "
        "ferramentas de apoio: valores, impostos e documentos enviados aos seus clientes devem ser conferidos por você.",
    ], None),
    ("8. Suspensão", [
        "Podemos suspender contas que violem estes termos, avisando pelo e-mail cadastrado sempre que possível.",
    ], None),
    ("9. Alterações", [
        "Podemos atualizar estes termos. Mudanças relevantes serão avisadas por e-mail ou no próprio sistema "
        "com antecedência; continuar usando depois disso significa concordar com a nova versão.",
    ], None),
    ("10. Contato e foro", [
        "Dúvidas: " + CONTATO + ". Fica eleito o foro do domicílio do consumidor, conforme a legislação brasileira.",
    ], None),
]


def get_termos_conteudo():
    """HTML dos termos de uso (usado no modal do cadastro)."""
    return para_html(TITULO, INTRO, SECOES)

def show():
    """Exibe a página de termos de uso"""
    mostrar_pagina(TITULO, INTRO, SECOES)

    if st.session_state.get("creating_account", False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aceitar Termos e Criar Conta", type="primary", use_container_width=True):
                st.session_state.termos_aceitos = True
                st.session_state.show_termos = False
                st.success("Termos aceitos! Prosseguindo com o cadastro...")
                st.rerun()
        with col2:
            if st.button("Recusar e Voltar", use_container_width=True):
                st.session_state.creating_account = False
                st.session_state.show_termos = False
                st.rerun()
    else:
        if st.button("Voltar"):
            st.session_state.show_termos = False
            st.rerun()

if __name__ == "__main__":
    show()
