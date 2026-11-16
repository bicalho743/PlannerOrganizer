"""
Plano e cobrança — situação da assinatura e o que fazer a seguir.

- Pro: portal do cliente Stripe (cartão, faturas, cancelamento).
- Teste grátis ou expirado/cancelado: planos mensal e anual (Payment Links do Stripe
  com o UID da conta em client_reference_id; o webhook da API ativa o plano).
"""
import streamlit as st

from pages.perfil import (STRIPE_CHECKOUT_MENSAL, STRIPE_CHECKOUT_ANUAL, STRIPE_PORTAL_LINK,
                          checkout_url, carregar_perfil, _criar_portal_session)
from utils.trial import is_pro, dias_restantes_trial, DIAS_TRIAL
from utils.rastreamento import onclick_checkout

CSS = """
<style>
.pl-status { border: 1px solid #E4E7EC; border-radius: 12px; padding: 18px 20px; background: #fff; margin-bottom: 18px; }
.pl-status .rot { font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #667085; }
.pl-status .val { font-size: 1.35rem; font-weight: 700; color: #101828; margin: 4px 0 2px; }
.pl-status .sub { font-size: .88rem; color: #475467; }
.pl-status.alerta { border-color: #FEC84B; background: #FFFAEB; }
.pl-status.pro { border-color: var(--navy); }
.pl-cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; max-width: 640px; }
.pl-card { border: 1px solid #E4E7EC; border-radius: 12px; padding: 18px 20px; background: #fff; position: relative; }
.pl-card.destaque { border: 2px solid var(--navy); }
.pl-card .selo { position: absolute; top: -10px; left: 18px; background: var(--gold); color: var(--navy);
                 font-size: .68rem; font-weight: 700; letter-spacing: .04em; padding: 2px 10px; border-radius: 999px; }
.pl-card .nome { font-size: .8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: #475467; }
.pl-card .preco { font-size: 1.6rem; font-weight: 700; color: #101828; margin: 4px 0; font-variant-numeric: tabular-nums; }
.pl-card .preco span { font-size: .85rem; font-weight: 500; color: #667085; }
.pl-card .obs { font-size: .82rem; color: #475467; min-height: 1.2em; }
.pl-card a.cta { display: block; text-align: center; margin-top: 14px; padding: 9px 0; border-radius: 8px; font-weight: 600;
                 text-decoration: none !important; font-size: .9rem; }
.pl-card a.cta.primario { background: var(--navy); color: #fff !important; }
.pl-card a.cta.secundario { border: 1px solid #D0D5DD; color: #344054 !important; }
.pl-lista { margin: 18px 0 0; padding: 0; list-style: none; color: #344054; font-size: .9rem; }
.pl-lista li { padding: 3px 0; }
.pl-lista li::before { content: "✓"; color: #067647; font-weight: 700; margin-right: 8px; }
@media (max-width: 600px) { .pl-cards { grid-template-columns: 1fr; } }
</style>
"""

# assinaturas feitas no celular: nome da loja, onde gerenciar e link
LOJAS_CELULAR = {
    "google": ("Google Play", "o app Google Play no celular (Perfil → Pagamentos e assinaturas → Assinaturas)",
               "https://play.google.com/store/account/subscriptions?package=com.plannerorganiza.app"),
    "apple": ("iPhone (App Store)", "os Ajustes do iPhone (seu nome → Assinaturas)",
              "https://apps.apple.com/account/subscriptions"),
}


# símbolo da loja no botão de gerenciar (Google Play: triângulo colorido; App Store: maçã)
ICONE_LOJA = {
    "google": ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">'
               '<path fill="#00D7FE" d="M3.6 1.8 13.4 12 3.6 22.2c-.4-.2-.6-.7-.6-1.2V3c0-.5.2-1 .6-1.2z"/>'
               '<path fill="#32BBFF" d="M3.6 1.8 13.4 12 3.6 22.2c-.4-.2-.6-.7-.6-1.2V3c0-.5.2-1 .6-1.2z" opacity=".35"/>'
               '<path fill="#00F076" d="M16.8 8.6 13.4 12 3.6 1.8c.3-.2.8-.2 1.2 0z"/>'
               '<path fill="#FF3A44" d="M16.8 15.4 4.8 22.2c-.4.2-.9.2-1.2 0L13.4 12z"/>'
               '<path fill="#FFD109" d="m20.6 10.7-3.8-2.1L13.4 12l3.4 3.4 3.8-2.1c.9-.5.9-2.1 0-2.6z"/></svg>'),
    "apple": ('<svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true"><path fill="#111" d="M16.4 12.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9s-2-.9-3.4-.9C5.8 6.8 4.2 7.9 3.3 9.5c-1.8 3.2-.5 7.8 1.3 10.4.9 1.3 1.9 2.7 3.3 2.6 1.3-.1 1.8-.9 3.4-.9s2 .9 3.4.8c1.4 0 2.3-1.3 3.2-2.6 1-1.5 1.4-2.9 1.4-3-.1 0-2.9-1.1-2.9-4.2zM13.8 4.9c.7-.9 1.2-2.1 1.1-3.3-1 0-2.3.7-3 1.6-.7.8-1.3 2-1.1 3.2 1.1.1 2.3-.6 3-1.5z"/></svg>'),
}
PL_LOJA_CSS = """<style>
.pl-loja { display:inline-flex; align-items:center; gap:10px; padding:9px 16px; border-radius:10px;
  border:1px solid #D0D5DD; background:#fff; color:#101828 !important; text-decoration:none !important;
  font-size:.92rem; font-weight:500; margin-top:4px; }
.pl-loja:hover { border-color:#C9A84C; background:#FFFDF7; }
</style>"""


def show():
    from utils.auth_guard import require_auth
    require_auth()
    from utils.database import get_usuario_id_from_session

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(PL_LOJA_CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Plano e cobrança</h1>', unsafe_allow_html=True)

    usuario = st.session_state.get("usuario") or {}
    email = (usuario.get("email") if isinstance(usuario, dict) else getattr(usuario, "email", "")) or ""
    uid = get_usuario_id_from_session()
    perfil = carregar_perfil(email or uid or "") or {}
    plano = (perfil.get("plano") or "gratuito").lower()

    # ---------- situação ----------
    if is_pro(perfil):
        # cada assinatura é gerenciada onde foi feita: site (Stripe), Google Play ou App Store
        from utils.assinatura import dados_assinatura
        origem = dados_assinatura(uid).get("origem") if uid else None
        if origem in LOJAS_CELULAR:
            nome, onde, link = LOJAS_CELULAR[origem]
            st.markdown('<div class="pl-status pro"><span class="rot">Situação</span>'
                        f'<div class="val">Plano Pro ativo · assinado pelo {nome}</div>'
                        f'<span class="sub">Para trocar o cartão ou cancelar, use {onde}.</span></div>',
                        unsafe_allow_html=True)
            st.markdown(f'<a class="pl-loja" href="{link}" target="_blank" rel="noopener">'
                        f'{ICONE_LOJA.get(origem, "")}<span>Gerenciar no {nome}</span></a>',
                        unsafe_allow_html=True)
            return
        st.markdown('<div class="pl-status pro"><span class="rot">Situação</span>'
                    '<div class="val">Plano Pro ativo</div>'
                    '<span class="sub">Todos os recursos liberados. Cartão, faturas e cancelamento ficam no portal do Stripe.</span></div>',
                    unsafe_allow_html=True)
        if st.button("Abrir portal de cobrança", type="primary", icon=":material/credit_card:", key="pl_portal"):
            with st.spinner("Abrindo o portal…"):
                url, erro = _criar_portal_session(perfil.get("email") or email)
            if url:
                st.link_button("Ir para o portal do Stripe", url, icon=":material/open_in_new:")
            elif erro == "sem_assinatura":
                st.info("Não encontramos assinatura no Stripe com o seu e-mail. Se acabou de assinar, aguarde alguns minutos.")
            else:
                st.markdown(f'Não foi possível abrir pelo app. <a href="{STRIPE_PORTAL_LINK}" target="_blank">'
                            'Entre no portal pelo seu e-mail</a>.', unsafe_allow_html=True)
        return

    from utils.convites import dias_trial_da_conta
    from utils.database import engine as _engine_plano
    dias_teste = dias_trial_da_conta(_engine_plano, uid)   # 30 para quem entrou com convite, senão 7
    dias = dias_restantes_trial(perfil, dias_teste)
    if plano == "cancelado":
        st.markdown('<div class="pl-status alerta"><span class="rot">Situação</span>'
                    '<div class="val">Assinatura cancelada</div>'
                    '<span class="sub">Seus dados continuam guardados. Assine de novo para voltar a usar todos os recursos.</span></div>',
                    unsafe_allow_html=True)
    elif dias > 0:
        st.markdown(f'<div class="pl-status"><span class="rot">Situação</span>'
                    f'<div class="val">Teste grátis: {dias} dia{"s" if dias != 1 else ""} restante{"s" if dias != 1 else ""}</div>'
                    f'<span class="sub">O teste dura {dias_teste} dias com tudo liberado. Assine antes do fim para não interromper o acesso.</span></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="pl-status alerta"><span class="rot">Situação</span>'
                    '<div class="val">Teste grátis encerrado</div>'
                    '<span class="sub">Seus dados continuam guardados. Escolha um plano para continuar.</span></div>',
                    unsafe_allow_html=True)

    # ---------- planos ----------
    url_mensal = checkout_url(STRIPE_CHECKOUT_MENSAL, email, uid)
    url_anual = checkout_url(STRIPE_CHECKOUT_ANUAL, email, uid)
    st.markdown(f"""
    <div class="pl-cards">
      <div class="pl-card">
        <div class="nome">Mensal</div>
        <div class="preco">R$ 39,90 <span>/mês</span></div>
        <div class="obs">Cancele quando quiser.</div>
        <a class="cta secundario" href="{url_mensal}" target="_blank" rel="noopener" {onclick_checkout('mensal', 39.9)}>Assinar mensal</a>
      </div>
      <div class="pl-card destaque">
        <span class="selo">38% MAIS BARATO</span>
        <div class="nome">Anual</div>
        <div class="preco">R$ 297 <span>/ano</span></div>
        <div class="obs">Equivale a R$ 24,75 por mês.</div>
        <a class="cta primario" href="{url_anual}" target="_blank" rel="noopener" {onclick_checkout('anual', 297)}>Assinar anual</a>
      </div>
    </div>
    <ul class="pl-lista">
      <li>Propostas e relatórios em PDF com a sua marca</li>
      <li>Clientes, vendas, financeiro e pós-organização</li>
      <li>Pagamento seguro pelo Stripe (cartão de crédito)</li>
    </ul>
    <p style="font-size:.85rem;color:#667085;margin-top:14px">
      Depois de pagar, o plano é liberado em alguns instantes; atualize a página.
      Já assinou e continua em modo consulta? <a href="{STRIPE_PORTAL_LINK}" target="_blank">Confira sua assinatura no portal</a>
      ou escreva para contato@plannerorganiza.com.br.
    </p>
    """, unsafe_allow_html=True)
