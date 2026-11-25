import streamlit as st
import os
from datetime import datetime
from utils.ui import botao_documento

# Links de checkout do Stripe (mesmos usados no app mobile)
# Preços desde 23/11/2026 (quem já assinava segue no preço antigo):
STRIPE_CHECKOUT_MENSAL = "https://buy.stripe.com/9B6cN53bYbE53mJeMK18c04"      # R$ 59,90/mês
STRIPE_CHECKOUT_TRIMESTRAL = "https://buy.stripe.com/14A5kD5k623vbTfawu18c05"  # R$ 149,90 a cada 3 meses
STRIPE_CHECKOUT_ANUAL = "https://buy.stripe.com/00w14n3bY8rT1eB8om18c06"       # R$ 479,90/ano
STRIPE_CHECKOUT_ANUAL_INDICADA = "https://buy.stripe.com/dRmdR9dQCfUl0axeMK18c08"  # R$ 429,90/ano (10% para indicadas)
STRIPE_PORTAL_RETURN_URL = "https://app.plannerorganiza.com.br"

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


# cores das propostas em bolinhas: as mesmas do onboarding (utils/onboarding_novo.CORES)
def _cores():
    try:
        from utils.onboarding_novo import CORES
        return dict(CORES)
    except Exception:
        return {"Verde": "#2F7D57", "Ameixa": "#5B4B8A", "Azul-marinho": "#0D1B2A", "Rosa": "#B5546A",
                "Dourado": "#B8943D", "Azul": "#3D6BB3"}


CSS = """
<style>
.pf-eyebrow { font-size: .74rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #9C7A22; margin: 0 0 4px; }
h1.pf-titulo { margin: 0 !important; padding: 0 !important; font-family: 'Cormorant Garamond', Georgia, serif !important;
               font-size: 2.6rem !important; font-weight: 600 !important; color: var(--navy) !important; line-height: 1.15 !important; }
h1.pf-titulo::after { content: ""; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--gold); margin-top: 8px; }
.pf-sub { color: #5B6B80; font-size: .98rem; margin: 10px 0 4px; }
.st-key-pf_topo_salvar { padding-top: 44px; align-items: flex-end; }
.st-key-pf_corpo { margin-top: 14px; }
.st-key-pf_topo_salvar .stButton > button { min-width: 86px; min-height: 46px; border-radius: 10px; }
[class*="st-key-pfc_"] { background: #fff; border-radius: 16px !important; border-color: #E7E2D6 !important; padding: 18px !important; }
.pf-h4 { font-size: 1rem; font-weight: 700; color: var(--navy); margin: 0 0 2px; display: flex; align-items: center; gap: 8px; }
.pf-nota { font-size: .84rem; color: #5B6B80; line-height: 1.5; }
[class*="st-key-pfc_"] label[data-testid="stWidgetLabel"] p { font-size: .84rem !important; color: #5B6B80 !important; }
[class*="st-key-pfc_"] .stTextInput input, [class*="st-key-pfc_"] .stTextArea textarea { border-radius: 10px !important; }
.pm-logo { width: 84px; height: 84px; border: 1.5px dashed var(--gold); border-radius: 14px; display: flex;
           align-items: center; justify-content: center; background: #fff; overflow: hidden; }
.pm-logo.tem { border-style: solid; border-color: #E7E2D6; }
.pm-logo img { max-width: 86%; max-height: 86%; object-fit: contain; }
.pm-logo span { color: #9C7A22; font-size: .84rem; text-align: center; padding: 6px; }
.pf-rot { font-size: .84rem; color: #5B6B80; margin: 0 0 2px; }
.st-key-pf_marca_linha [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; align-items: center; }
.st-key-pf_marca_linha [data-testid="stColumn"]:first-child { flex: 0 0 96px !important; width: 96px !important; min-width: 96px !important; }
.st-key-pf_marca_linha [data-testid="stColumn"]:last-child { flex: 1 1 auto !important; min-width: 0 !important; }
.st-key-pf_logo_acoes [data-testid="stFileUploader"] section { padding: 10px 12px !important; }
.st-key-pf_cor2_box [data-testid="stColorPicker"] { margin-top: 2px; }
.pm-prev { border-radius: 12px; overflow: hidden; border: 1px solid #E7E2D6; margin-top: 8px; background: #fff; }
.pm-prev .topo { padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.pm-prev .tit { color: #fff; font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.2rem; font-weight: 600;
                overflow-wrap: anywhere; line-height: 1.2; }
.pm-prev .cartao { width: 48px; height: 48px; background: #fff; border-radius: 8px; flex: none;
                   display: flex; align-items: center; justify-content: center; overflow: hidden; }
.pm-prev .cartao img { max-width: 84%; max-height: 84%; object-fit: contain; }
.pm-prev .faixa { height: 4px; }
.pm-prev .corpo { padding: 14px 16px; font-size: .84rem; color: #5B6B80; }
.pm-prev .quem { display: flex; gap: 10px; align-items: center; border-radius: 10px; padding: 10px; margin-top: 10px; }
.pm-prev .quem .bola { width: 36px; height: 36px; border-radius: 50%; flex: none; display: flex; align-items: center;
                       justify-content: center; color: #fff; font-weight: 700; font-size: .9rem; }
.pm-prev .quem b { display: block; color: var(--navy); font-size: .86rem; overflow-wrap: anywhere; }
.pm-prev .quem span { overflow-wrap: anywhere; }
.pm-prev .tot { display: flex; flex-wrap: wrap; gap: 4px 10px; justify-content: space-between; border-radius: 8px; padding: 10px; margin-top: 10px; font-weight: 700; }
.pm-prev .rod { font-size: .76rem; margin-top: 10px; overflow-wrap: anywhere; }
.st-key-pf_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { align-items: flex-start; }
@media (min-width: 1001px) {
  .st-key-pf_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { flex: 0 0 340px !important; width: 340px !important; }
  .st-key-pf_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { flex: 1 1 0 !important; min-width: 0 !important; }
}
.st-key-pf_ir_plano .stButton > button, .st-key-pf_ir_plano .stButton > button p { color: #9C7A22 !important; font-weight: 700 !important; }
@media (max-width: 1000px) {
  .st-key-pf_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; }
  .st-key-pf_corpo > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
}
@media (max-width: 640px) {
  h1.pf-titulo { font-size: 2.1rem !important; }
  .st-key-pf_topo_salvar { padding-top: 0; align-items: stretch; }
  .st-key-pf_topo_salvar .stButton > button { width: 100%; }
}
</style>
"""


def _css_bolinhas(cores):
    """Rádio de cores desenhado como bolinhas (mesmo jeito do onboarding); o nome fica para leitor de tela."""
    bolas = "".join(
        f'.st-key-pf_cor [role="radiogroup"] > div:nth-child({i}) label > div > div:first-child {{ background:{c} !important; }}'
        for i, c in enumerate(cores, 1))
    return ('<style>.st-key-pf_cor [role="radiogroup"] { gap:10px !important; flex-wrap:wrap; margin:4px 0 2px; }'
            '.st-key-pf_cor [role="radiogroup"] label > div > div:first-child { width:30px !important; '
            'height:30px !important; border:none !important; border-radius:50% !important; margin:0 !important; '
            'cursor:pointer; box-shadow:0 0 0 1px rgba(13,27,42,.12); }'
            '.st-key-pf_cor [role="radiogroup"] label > div > div:first-child > div { display:none !important; }'
            '.st-key-pf_cor [role="radiogroup"] > div[data-selected="true"] label > div > div:first-child, '
            '.st-key-pf_cor [role="radiogroup"] label:has(input:checked) > div > div:first-child '
            '{ box-shadow:0 0 0 2px #FFFFFF, 0 0 0 4px #C9A84C !important; }'
            '.st-key-pf_cor [role="radiogroup"] [data-testid="stMarkdownContainer"] { position:absolute; width:1px; height:1px; '
            'overflow:hidden; clip:rect(0 0 0 0); }' + bolas + '</style>')


def _previa_html(p):
    """Prévia do topo da proposta com a marca (valores de exemplo; nada vem de proposta real)."""
    from utils.visual import esc
    principal = p.get("cor_principal") or COR_PRINCIPAL_PADRAO
    destaque = p.get("cor_secundaria") or COR_SECUNDARIA_PADRAO
    empresa = esc(p.get("empresa") or p.get("nome") or "Seu negócio")
    nome = (p.get("nome") or "").strip()
    cargo = esc(p.get("cargo") or "Personal Organizer")
    inicial = esc((nome or p.get("empresa") or "P")[:1].upper())
    insta = ("@" + p["instagram"].lstrip("@")) if p.get("instagram") else ""
    contatos = " · ".join(esc(x) for x in (p.get("telefone"), insta, p.get("website")) if x)
    logo = f'<div class="cartao"><img src="{p["logo"]}" alt=""></div>' if p.get("logo") else ""
    fundo = principal + "14" if len(principal) == 7 else "#F6F3FB"
    return (f'<div class="pm-prev"><div class="topo" style="background:{principal}">'
            f'<div class="tit">{empresa}</div>{logo}</div>'
            f'<div class="faixa" style="background:{destaque}"></div>'
            f'<div class="corpo">Proposta de Serviço nº 001'
            f'<div class="quem" style="background:{fundo}"><span class="bola" style="background:{principal}">{inicial}</span>'
            f'<div><b>{esc(nome) or "Seu nome"}</b><span>{cargo}</span></div></div>'
            f'<div class="tot" style="background:{fundo};color:{principal}"><span>Investimento</span><span>R$ 2.070,00</span></div>'
            + (f'<div class="rod">{contatos}</div>' if contatos else "") + '</div></div>')


CHAVES = {"pf_empresa": "empresa", "pf_tel": "telefone", "pf_insta": "instagram", "pf_site": "website",
          "pf_nome": "nome", "pf_cargo": "cargo", "pf_cnpj": "cnpj", "pf_msg": "mensagem_padrao",
          "pf_obs": "observacoes_relatorio", "pf_cor": "cor_principal", "pf_cor2": "cor_secundaria"}


def _preencher(perfil, usuario):
    """Põe nos campos o que está salvo (ao entrar na tela). Sem st.form: a prévia acompanha o que se digita."""
    padrao = {"nome": usuario.get("nome", ""), "telefone": usuario.get("telefone", ""),
              "empresa": usuario.get("empresa", ""), "cargo": "Personal Organizer",
              "mensagem_padrao": "Agradecemos a confiança em nossos serviços.",
              "observacoes_relatorio": OBSERVACOES_PADRAO, "cor_principal": COR_PRINCIPAL_PADRAO,
              "cor_secundaria": COR_SECUNDARIA_PADRAO}
    for chave, campo in CHAVES.items():
        st.session_state[chave] = perfil.get(campo) or padrao.get(campo) or ""
    st.session_state["pf_cor"] = st.session_state["pf_cor"].upper()
    st.session_state["pf_cor2"] = st.session_state["pf_cor2"].upper()
    st.session_state.pop("pf_logo_rm", None)


def show():
    """Perfil e marca: dados que aparecem nos PDFs enviados às clientes."""
    from utils.auth_guard import require_auth
    from utils.visual import esc
    require_auth()
    usuario = st.session_state.get("usuario") or {}
    if not isinstance(usuario, dict):
        usuario = {"email": getattr(usuario, "email", ""), "nome": getattr(usuario, "nome", "")}

    perfil = carregar_perfil()
    email_conta = perfil.get("email") or usuario.get("email", "")
    if st.session_state.get("_last_page_rendered") != "Perfil" or "pf_empresa" not in st.session_state:
        _preencher(perfil, usuario)

    st.markdown(CSS, unsafe_allow_html=True)
    c_tit, c_btn = st.columns([4, 1], vertical_alignment="top")
    c_tit.markdown('<div class="pf-eyebrow">Como as clientes veem você</div><h1 class="pf-titulo">Perfil e marca</h1>'
                   '<div class="pf-sub">Tudo o que sai nas suas propostas, recibos e mensagens.</div>',
                   unsafe_allow_html=True)
    with c_btn, st.container(key="pf_topo_salvar"):
        salvar = st.button("Salvar", type="primary", key="pf_salvar_topo")

    if st.session_state.pop("pm_salvo", False):
        st.success("Perfil salvo. Os próximos PDFs já saem com a sua marca.")

    cores = _cores()
    cor_salva = (perfil.get("cor_principal") or COR_PRINCIPAL_PADRAO).upper()
    opcoes = [c.upper() for c in cores.values()]
    nomes = {c.upper(): n for n, c in cores.items()}
    if cor_salva not in opcoes:   # cor escolhida antes, fora da paleta: continua valendo até ela trocar
        opcoes = [cor_salva] + opcoes
        nomes[cor_salva] = "Sua cor atual"
    if st.session_state.get("pf_cor") not in opcoes:
        st.session_state["pf_cor"] = cor_salva
    up_key = f"pf_logo_up_{st.session_state.get('pf_logo_n', 0)}"

    corpo = st.container(key="pf_corpo")
    esq, dir_ = corpo.columns([1.9, 1], gap="medium")
    with esq:
        with st.container(border=True, key="pfc_negocio"):
            st.markdown('<div class="pf-h4">Seu negócio</div>', unsafe_allow_html=True)
            # uma linha de colunas por par: no celular a ordem dos campos continua a mesma
            c1, c2 = st.columns(2)
            c1.text_input("Nome do negócio", key="pf_empresa", placeholder="Ex.: Organiza Tâmara")
            c2.text_input("WhatsApp", key="pf_tel", placeholder="(31) 99999-0000")
            c1, c2 = st.columns(2)
            c1.text_input("Instagram", key="pf_insta", placeholder="seuperfil")
            c2.text_input("Site", key="pf_site", placeholder="www.seusite.com.br")
            c1, c2 = st.columns(2)
            c1.text_input("Seu nome", key="pf_nome")
            c2.text_input("Cargo", key="pf_cargo")
            c1, c2 = st.columns(2)
            c1.text_input("CNPJ (opcional)", key="pf_cnpj", placeholder="00.000.000/0001-00")
            c2.text_input("E-mail da conta", value=email_conta, disabled=True, key="pf_email",
                          help="É o e-mail de login; não pode ser alterado aqui.")

        with st.container(border=True, key="pfc_marca"):
            st.markdown('<div class="pf-h4">Sua marca</div>', unsafe_allow_html=True)
            arquivo = st.session_state.get(up_key)
            logo_mostrar, erro_logo = perfil.get("logo"), None
            if arquivo is not None:
                try:
                    logo_mostrar = preparar_logo(arquivo)
                except ValueError as e:
                    erro_logo = str(e)
            if st.session_state.get("pf_logo_rm"):
                logo_mostrar = None
            with st.container(key="pf_marca_linha"):
                cl, cc = st.columns([1, 5], vertical_alignment="center")
                cl.markdown(f'<div class="pm-logo tem"><img src="{logo_mostrar}" alt="Logotipo"></div>' if logo_mostrar
                            else '<div class="pm-logo"><span>+ Logo</span></div>', unsafe_allow_html=True)
                with cc:
                    st.markdown('<div class="pf-rot">Cor das propostas</div>', unsafe_allow_html=True)
                    st.markdown(_css_bolinhas(opcoes), unsafe_allow_html=True)
                    st.radio("Cor das propostas", opcoes, key="pf_cor", horizontal=True,
                             format_func=lambda c: nomes.get(c, c), label_visibility="collapsed")
            with st.container(key="pf_logo_acoes"):
                st.file_uploader("Enviar ou trocar o logotipo (PNG ou JPG)", type=["png", "jpg", "jpeg"], key=up_key,
                                 max_upload_size=LOGO_MAX_MB)
                if erro_logo:
                    st.error(erro_logo)
                if perfil.get("logo"):
                    st.checkbox("Remover logotipo", key="pf_logo_rm")
            with st.container(key="pf_cor2_box"):
                st.color_picker("Cor de destaque (faixas e linhas do PDF)", key="pf_cor2")

        with st.container(border=True, key="pfc_textos"):
            st.markdown('<div class="pf-h4">Textos das propostas</div>', unsafe_allow_html=True)
            st.text_area("Mensagem de agradecimento", key="pf_msg", height=80)
            st.text_area("Condições e observações das propostas (uma por linha)", key="pf_obs", height=150)

        salvar_baixo = st.button("Salvar perfil e marca", type="primary", icon=":material/save:", key="pf_salvar_baixo")
        with st.container(key="pf_ir_plano"):
            if st.button("Ver plano e cobrança", type="tertiary", icon=":material/credit_card:", key="pf_ir_plano_btn"):
                st.session_state.current_page = "Plano"
                st.rerun()

    atual = {campo: st.session_state.get(chave) for chave, campo in CHAVES.items()}
    atual["logo"] = logo_mostrar
    with dir_:
        with st.container(border=True, key="pfc_previa"):
            st.markdown('<div class="pf-h4">Prévia da proposta</div>', unsafe_allow_html=True)
            st.markdown(_previa_html(atual), unsafe_allow_html=True)
            if botao_documento("Gerar PDF de exemplo", icon=":material/picture_as_pdf:", key="pm_pdf_exemplo",
                               use_container_width=True):
                try:
                    st.session_state["pm_pdf_bytes"] = _pdf_exemplo(perfil)
                except Exception as e:
                    st.error(f"Não foi possível gerar o exemplo: {e}")
            if st.session_state.get("pm_pdf_bytes"):
                st.download_button("Baixar PDF de exemplo", st.session_state["pm_pdf_bytes"],
                                   file_name="proposta-exemplo.pdf", mime="application/pdf", icon=":material/download:",
                                   key="pm_pdf_baixar", use_container_width=True)
            st.caption("O PDF de exemplo usa o que está salvo. Depois de mudar, clique em Salvar.")
        with st.container(border=True, key="pfc_info"):
            st.markdown('<div class="pf-nota">A marca vale para propostas, recibos de venda e relatórios em PDF. '
                        'Você também pode trocar a cor na hora de enviar cada proposta.</div>', unsafe_allow_html=True)

    if not (salvar or salvar_baixo):
        return
    ss = st.session_state
    dados = {
        "email": email_conta, "nome": ss.pf_nome.strip(), "cargo": ss.pf_cargo.strip(), "telefone": ss.pf_tel.strip(),
        "instagram": ss.pf_insta.strip().lstrip("@").replace("https://www.instagram.com/", "").strip("/"),
        "website": ss.pf_site.strip(), "empresa": ss.pf_empresa.strip(), "cnpj": ss.pf_cnpj.strip(),
        "cor_principal": ss.pf_cor, "cor_secundaria": ss.pf_cor2,
        "mensagem_padrao": ss.pf_msg, "observacoes_relatorio": ss.pf_obs,
    }
    if erro_logo:
        st.error(erro_logo)
        return
    if arquivo is not None:
        dados["logo"] = logo_mostrar
    elif ss.get("pf_logo_rm"):
        dados["logo"] = None
    if not dados["nome"]:
        st.error("Informe seu nome.")
        return
    if _db().salvar_perfil_usuario(dados):
        if isinstance(ss.get("usuario"), dict):
            ss.usuario.update({k: dados[k] for k in ("nome", "telefone", "empresa", "cargo")})
        ss["pf_logo_n"] = ss.get("pf_logo_n", 0) + 1   # esvazia o campo de envio do logotipo
        ss.pop("pf_logo_rm", None)
        ss.pop("pm_pdf_bytes", None)
        ss["pm_salvo"] = True
        st.rerun()
    else:
        st.error("Não foi possível salvar agora. Tente de novo em instantes.")
