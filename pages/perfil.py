import streamlit as st
import os
from datetime import datetime
from utils.ui import botao_documento

# Links de checkout do Stripe (mesmos usados no app mobile)
STRIPE_CHECKOUT_MENSAL = "https://buy.stripe.com/aFa00j27UbE5cXjfQO18c02"  # R$ 39,90/mês (desde out/2026)
STRIPE_CHECKOUT_ANUAL = "https://buy.stripe.com/8x26oHaEqbE5g9vbAy18c00"
STRIPE_PORTAL_RETURN_URL = "https://plannerorganiza.com.br"

# Link direto do Portal do Cliente (login por e-mail). Configurável por env
# para ajuste sem redeploy — o valor abaixo veio do painel do Stripe.
STRIPE_PORTAL_LINK = os.environ.get(
    "STRIPE_PORTAL_LINK",
    "https://billing.stripe.com/p/login/8x26oHaEqbE5g9vbAy18c00",
)



def checkout_url(base, email, uid=None):
    """Payment Link com e-mail pré-preenchido (edite pelo pagador, é só
    conveniência) e client_reference_id = UID Firebase (oculto, não editável).
    O webhook ativa o plano priorizando o UID — assim, mesmo que a pessoa
    pague com um e-mail diferente do de login, a conta certa é liberada."""
    from urllib.parse import quote
    email = (email or '').strip()
    partes = []
    if email:
        partes.append(f"prefilled_email={quote(email)}")
    if uid:
        partes.append(f"client_reference_id={quote(str(uid))}")
    return f"{base}?{'&'.join(partes)}" if partes else base


def _criar_portal_session(email):
    """
    Cria uma sessão do Portal do Cliente Stripe para o e-mail informado.
    Retorna (url, erro). A URL abre a página onde o cliente gerencia a
    assinatura, cartão e faturas.
    """
    secret = os.environ.get("STRIPE_SECRET_KEY", "")
    if not secret:
        return None, "STRIPE_SECRET_KEY não configurada no servidor."
    if not secret.startswith("sk_"):
        return None, ("STRIPE_SECRET_KEY inválida no servidor: deve começar com 'sk_' "
                      "(chave secreta da API), não 'whsec_' (segredo de webhook). "
                      "Corrija a variável de ambiente.")
    if not email:
        return None, "E-mail do usuário não disponível."
    try:
        import stripe
        stripe.api_key = secret
        clientes = stripe.Customer.list(email=email, limit=1)
        if not clientes.data:
            return None, "sem_assinatura"
        session = stripe.billing_portal.Session.create(
            customer=clientes.data[0].id,
            return_url=STRIPE_PORTAL_RETURN_URL,
        )
        return session.url, None
    except Exception as e:
        return None, str(e)

CAMPOS_PERFIL = ("nome", "email", "telefone", "empresa", "instagram", "website", "cargo", "cnpj", "logo",
                 "cor_principal", "cor_secundaria", "mensagem_padrao", "observacoes_relatorio", "plano", "role",
                 "ativo", "data_cadastro")
COR_PRINCIPAL_PADRAO = "#0D1B2A"
COR_SECUNDARIA_PADRAO = "#C9A84C"
OBSERVACOES_PADRAO = """1. Pagamento sinal, na reserva da data, via PIX
2. Os valores apresentados incluem todos os custos.
3. Não está incluído a organização de documentos.
4. No caso da proposta incluir treinamento, é necessário a presença de funcionário no período da organização
5. Não incluido produtos e organizadores, caso o cliente opte por adquirí-los"""
LOGO_MAX_PX = 600
LOGO_MAX_MB = 5


def _db():
    from utils.database import Database
    return st.session_state.db if "db" in st.session_state else Database()


def carregar_perfil(user_id=None):
    """Perfil da conta logada (o argumento é mantido por compatibilidade). {} se não houver."""
    try:
        perfil = _db().get_perfil_usuario() or {}
    except Exception as e:
        print(f"Erro ao carregar perfil do banco: {e}")
        return {}
    dados = {k: perfil.get(k) for k in CAMPOS_PERFIL}
    if perfil.get("ultimo_login"):
        dados["ultima_atualizacao"] = perfil["ultimo_login"].strftime("%d/%m/%Y %H:%M")
    return dados


def preparar_logo(arquivo):
    """Reduz o logotipo enviado para no máximo LOGO_MAX_PX e devolve um data URL PNG (ou levanta ValueError)."""
    import base64
    import io
    from PIL import Image, UnidentifiedImageError
    bruto = arquivo.getvalue()
    if len(bruto) > LOGO_MAX_MB * 1024 * 1024:
        raise ValueError(f"A imagem passa de {LOGO_MAX_MB} MB. Envie uma versão menor.")
    try:
        img = Image.open(io.BytesIO(bruto))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise ValueError("Não consegui abrir essa imagem. Envie um PNG ou JPG.")
    img = img.convert("RGBA")
    img.thumbnail((LOGO_MAX_PX, LOGO_MAX_PX))
    saida = io.BytesIO()
    img.save(saida, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(saida.getvalue()).decode()


def _pdf_exemplo(perfil):
    """PDF de proposta fictícia com a marca atual, para conferir antes de mandar para clientes."""
    import tempfile
    from utils.pdf_generator_v2 import gerar_pdf_cliente
    dados = {
        "proposta_id": 1, "cliente": "Cliente exemplo", "tipo": "Organização residencial", "status": "Em Aberto",
        "periodo": datetime.now().strftime("%d/%m/%Y"), "descricao": "Organização de closet e cozinha",
        "itens": [{"nome": "Organização de closet", "quantidade": 1, "valor_unit": 1800.0, "valor": 1800.0},
                  {"nome": "Caixas organizadoras", "quantidade": 6, "valor_unit": 45.0, "valor": 270.0}],
        "total": 2070.0, "observacoes": perfil.get("observacoes_relatorio") or OBSERVACOES_PADRAO,
    }
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        gerar_pdf_cliente(dados, tmp.name, perfil=perfil, titulo="Proposta Comercial")
        return open(tmp.name, "rb").read()


CSS = """
<style>
.pm-logo { width: 100%; aspect-ratio: 1 / 1; max-width: 200px; border: 1px dashed #D0D5DD; border-radius: 12px;
           display: flex; align-items: center; justify-content: center; background: #fff; overflow: hidden; }
.pm-logo img { max-width: 86%; max-height: 86%; object-fit: contain; }
.pm-logo span { color: #98A2B3; font-size: .85rem; text-align: center; padding: 12px; }
.pm-prev { border-radius: 12px; overflow: hidden; border: 1px solid #E4E7EC; margin-top: 4px; }
.pm-prev .topo { padding: 18px 20px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.pm-prev .tit { color: #fff; font-weight: 700; font-size: 1.1rem; }
.pm-prev .lin { font-size: .82rem; margin-top: 4px; }
.pm-prev .cartao { width: 64px; height: 64px; background: #fff; border-radius: 8px; flex: none;
                   display: flex; align-items: center; justify-content: center; overflow: hidden; }
.pm-prev .cartao img { max-width: 84%; max-height: 84%; object-fit: contain; }
.pm-prev .faixa { height: 4px; }
.pm-prev .rod { background: #F2F4F7; color: #667085; font-size: .75rem; padding: 8px 20px; display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
</style>
"""


def _previa_html(p):
    import html
    principal = p.get("cor_principal") or COR_PRINCIPAL_PADRAO
    destaque = p.get("cor_secundaria") or COR_SECUNDARIA_PADRAO
    nome = html.escape(p.get("nome") or "Seu nome")
    cargo = html.escape(p.get("cargo") or "Personal Organizer")
    insta = html.escape(("@" + p["instagram"].lstrip("@")) if p.get("instagram") else "")
    empresa = html.escape(p.get("empresa") or p.get("nome") or "Sua empresa")
    contatos = " · ".join(html.escape(x) for x in (p.get("telefone"), insta, p.get("website")) if x)
    logo = f'<div class="cartao"><img src="{p["logo"]}"></div>' if p.get("logo") else ""
    return (f'<div class="pm-prev"><div class="topo" style="background:{principal}"><div>'
            f'<div class="tit">Proposta Comercial</div>'
            f'<div class="lin" style="color:{destaque}">{" · ".join(x for x in (nome, cargo, insta) if x)}</div></div>{logo}</div>'
            f'<div class="faixa" style="background:{destaque}"></div>'
            f'<div class="rod"><span>{empresa}</span><span>{contatos}</span></div></div>')


def show():
    """Perfil e marca: dados que aparecem nos PDFs enviados às clientes."""
    from utils.auth_guard import require_auth
    require_auth()
    usuario = st.session_state.get("usuario") or {}
    if not isinstance(usuario, dict):
        usuario = {"email": getattr(usuario, "email", ""), "nome": getattr(usuario, "nome", "")}

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Perfil e marca</h1>', unsafe_allow_html=True)
    st.caption("Seu logotipo, cores e contatos saem em todas as propostas e relatórios em PDF que você envia às clientes.")

    perfil = carregar_perfil()
    email_conta = perfil.get("email") or usuario.get("email", "")

    if st.session_state.pop("pm_salvo", False):
        st.success("Perfil salvo. Os próximos PDFs já saem com a sua marca.")

    with st.form("form_perfil", clear_on_submit=False, border=False):
        col_logo, col_marca = st.columns([1, 2], gap="large")
        with col_logo:
            st.markdown("**Logotipo**")
            if perfil.get("logo"):
                st.markdown(f'<div class="pm-logo"><img src="{perfil["logo"]}" alt="Logotipo"></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="pm-logo"><span>Sem logotipo ainda</span></div>', unsafe_allow_html=True)
            arquivo = st.file_uploader("Enviar logotipo (PNG ou JPG)", type=["png", "jpg", "jpeg"], key="pm_logo_up",
                                       max_upload_size=LOGO_MAX_MB)
            remover = st.checkbox("Remover logotipo", key="pm_logo_rm") if perfil.get("logo") else False
        with col_marca:
            empresa = st.text_input("Nome da empresa", value=perfil.get("empresa") or usuario.get("empresa", ""),
                                    placeholder="Ex.: Organiza Tâmara")
            cnpj = st.text_input("CNPJ (opcional)", value=perfil.get("cnpj") or "", placeholder="00.000.000/0001-00")
            c1, c2 = st.columns(2)
            cor_principal = c1.color_picker("Cor principal", value=perfil.get("cor_principal") or COR_PRINCIPAL_PADRAO,
                                            help="Fundo do cabeçalho e títulos dos PDFs")
            cor_secundaria = c2.color_picker("Cor de destaque", value=perfil.get("cor_secundaria") or COR_SECUNDARIA_PADRAO,
                                             help="Faixas, linhas e destaques dos PDFs")

        st.markdown("**Seus contatos**")
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome", value=perfil.get("nome") or usuario.get("nome", ""))
        cargo = c2.text_input("Cargo", value=perfil.get("cargo") or "Personal Organizer")
        telefone = c1.text_input("Telefone / WhatsApp", value=perfil.get("telefone") or usuario.get("telefone", ""),
                                 placeholder="(31) 99999-0000")
        instagram = c2.text_input("Instagram", value=perfil.get("instagram") or "", placeholder="seuperfil")
        website = c1.text_input("Site", value=perfil.get("website") or "", placeholder="www.seusite.com.br")
        c2.text_input("E-mail da conta", value=email_conta, disabled=True,
                      help="É o e-mail de login; não pode ser alterado aqui.")

        st.markdown("**Textos dos documentos**")
        mensagem_padrao = st.text_area("Mensagem de agradecimento", value=perfil.get("mensagem_padrao") or
                                       "Agradecemos a confiança em nossos serviços.", height=80)
        observacoes_relatorio = st.text_area("Observações das propostas (uma por linha)",
                                             value=perfil.get("observacoes_relatorio") or OBSERVACOES_PADRAO, height=150)

        salvar = st.form_submit_button("Salvar perfil e marca", type="primary", icon=":material/save:")

    if salvar:
        dados = {
            "email": email_conta, "nome": nome.strip(), "cargo": cargo.strip(), "telefone": telefone.strip(),
            "instagram": instagram.strip().lstrip("@").replace("https://www.instagram.com/", "").strip("/"),
            "website": website.strip(), "empresa": empresa.strip(), "cnpj": cnpj.strip(),
            "cor_principal": cor_principal, "cor_secundaria": cor_secundaria,
            "mensagem_padrao": mensagem_padrao, "observacoes_relatorio": observacoes_relatorio,
        }
        try:
            if arquivo is not None:
                dados["logo"] = preparar_logo(arquivo)
            elif remover:
                dados["logo"] = None
        except ValueError as e:
            st.error(str(e))
            return
        if not dados["nome"]:
            st.error("Informe seu nome.")
            return
        if _db().salvar_perfil_usuario(dados):
            if isinstance(st.session_state.get("usuario"), dict):
                st.session_state.usuario.update({k: dados[k] for k in ("nome", "telefone", "empresa", "cargo")})
            st.session_state.pop("pm_logo_up", None)
            st.session_state["pm_salvo"] = True
            st.rerun()
        else:
            st.error("Não foi possível salvar agora. Tente de novo em instantes.")

    st.markdown("**Como fica no PDF**")
    st.markdown(_previa_html(perfil), unsafe_allow_html=True)
    st.caption("A prévia mostra o que está salvo. Depois de alterar, clique em Salvar para atualizar.")
    if botao_documento("Gerar PDF de exemplo", icon=":material/picture_as_pdf:", key="pm_pdf_exemplo"):
        try:
            st.session_state["pm_pdf_bytes"] = _pdf_exemplo(perfil)
        except Exception as e:
            st.error(f"Não foi possível gerar o exemplo: {e}")
    if st.session_state.get("pm_pdf_bytes"):
        st.download_button("Baixar PDF de exemplo", st.session_state["pm_pdf_bytes"], file_name="proposta-exemplo.pdf",
                           mime="application/pdf", icon=":material/download:", key="pm_pdf_baixar")

    st.divider()
    if st.button("Ver plano e cobrança", icon=":material/credit_card:", key="pf_ir_plano"):
        st.session_state.current_page = "Plano"
        st.rerun()
