"""
Página de Política de Privacidade para o sistema Planner Organizer
"""
import streamlit as st
import os
import sys

project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.texto_legal import CONTATO, para_html, mostrar_pagina

TITULO = "Política de Privacidade"
INTRO = ("Esta política explica quais dados pessoais o Planner Organizer trata, para quê, com quem são "
         "compartilhados e como você exerce seus direitos, conforme a Lei Geral de Proteção de Dados "
         "(Lei nº 13.709/2018, LGPD).")

SECOES = [
    ("1. Dados da sua conta", [
        "Tratamos estes dados como controladores:",
    ], [
        "Cadastro e perfil: nome, e-mail, telefone, empresa, cargo, Instagram, site, logotipo e cores da sua marca.",
        "Login: e-mail e senha (ou conta Google), gerenciados pelo Google Firebase Authentication. Não guardamos sua senha.",
        "Assinatura: plano, situação e histórico de cobrança. Os dados do cartão são digitados e guardados pelo Stripe; nós não os recebemos.",
        "Uso: datas de cadastro e último acesso, páginas visitadas e dados técnicos do navegador, por meio do Google Analytics.",
    ]),
    ("2. Dados que você cadastra sobre terceiros", [
        "Clientes, fornecedores, assistentes e parceiros que você cadastra podem incluir nome, telefone, e-mail, "
        "CPF, endereço, data de aniversário, chave PIX e observações. Para esses dados você é a controladora e o "
        "Planner Organizer é operador: tratamos apenas para guardar, exibir e gerar os documentos que você pede, "
        "e nunca os usamos para outros fins nem entramos em contato com essas pessoas.",
    ], None),
    ("3. Para que usamos e com qual base legal", None, [
        "Prestar o serviço (login, cadastros, propostas, relatórios em PDF): execução de contrato.",
        "Cobrança da assinatura e emissão de comprovantes: execução de contrato e obrigação legal.",
        "E-mails sobre a conta, o teste grátis e a cobrança: execução de contrato.",
        "E-mails com novidades e materiais: consentimento, que você pode retirar pelo link de descadastro.",
        "Estatísticas de uso para melhorar o sistema e segurança contra abuso: legítimo interesse.",
    ]),
    ("4. Com quem compartilhamos", [
        "Não vendemos dados. Compartilhamos apenas com fornecedores necessários para o serviço funcionar:",
    ], [
        "Render (hospedagem do sistema e do banco de dados).",
        "Google Firebase (login) e Google Analytics (estatísticas de uso).",
        "Stripe (pagamentos).",
        "Brevo (envio de e-mails).",
        "Autoridades, quando houver obrigação legal ou ordem judicial.",
    ]),
    ("5. Transferência internacional", [
        "Esses fornecedores podem guardar dados fora do Brasil, principalmente nos Estados Unidos. A transferência "
        "é feita para executar o contrato com você e com fornecedores que adotam cláusulas contratuais de proteção "
        "de dados, como prevê o art. 33 da LGPD.",
    ], None),
    ("6. Por quanto tempo guardamos", [
        "Enquanto a conta existir. Após o cancelamento da assinatura, os dados ficam guardados para que você possa "
        "voltar, até que você peça a exclusão. Ao excluir a conta, apagamos os dados em até 30 dias, exceto o que "
        "a lei obriga a manter (por exemplo, registros de cobrança e de acesso pelo prazo legal).",
    ], None),
    ("7. Segurança", [
        "Conexão criptografada (HTTPS), senhas sob responsabilidade do Firebase, separação dos dados de cada conta "
        "e acesso restrito ao banco de dados. Se ocorrer um incidente que possa causar risco relevante, avisaremos "
        "você e a ANPD.",
    ], None),
    ("8. Seus direitos", [
        "Você pode pedir a qualquer momento, pelo e-mail " + CONTATO + ":",
    ], [
        "confirmação e acesso aos seus dados, inclusive cópia em formato aberto (portabilidade);",
        "correção de dados incompletos ou errados (a maior parte pode ser feita em Perfil e marca);",
        "exclusão da conta e dos dados, ou anonimização do que não for necessário;",
        "informação sobre com quem compartilhamos;",
        "retirada do consentimento para e-mails de novidades.",
    ]),
    ("", [
        "Respondemos em até 15 dias. Os clientes cadastrados por você devem pedir os direitos deles diretamente "
        "a você; ajudamos no que for preciso. Você também pode reclamar à Autoridade Nacional de Proteção de Dados (ANPD).",
    ], None),
    ("9. Cookies", [
        "Usamos cookies essenciais para manter você conectada e cookies do Google Analytics para estatísticas. "
        "Você pode bloqueá-los no navegador; o login pode deixar de funcionar sem os essenciais.",
    ], None),
    ("10. Menores de idade", [
        "O Planner Organizer é destinado a profissionais maiores de 18 anos.",
    ], None),
    ("11. Encarregado e contato", [
        "Para assuntos de privacidade, fale com o encarregado pelo tratamento de dados em " + CONTATO + ".",
    ], None),
    ("12. Alterações", [
        "Mudanças relevantes nesta política serão avisadas por e-mail ou no sistema antes de valerem.",
    ], None),
]


def get_politica_conteudo():
    """HTML da política de privacidade (usado no modal do cadastro)."""
    return para_html(TITULO, INTRO, SECOES)

def show():
    """Exibe a página de política de privacidade"""
    mostrar_pagina(TITULO, INTRO, SECOES)

    if st.session_state.get("creating_account", False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aceitar Política e Continuar", type="primary", use_container_width=True):
                st.session_state.politica_aceita = True
                st.session_state.show_politica = False
                st.rerun()
        with col2:
            if st.button("Recusar e Voltar", use_container_width=True):
                st.session_state.show_politica = False
                st.rerun()
    else:
        if st.button("Voltar"):
            st.session_state.show_politica = False
            st.rerun()

if __name__ == "__main__":
    show()
