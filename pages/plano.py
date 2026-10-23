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
.pl-fundadora { background: #FBF5E6; border: 1px solid #E3CF97; color: #5C4712; border-radius: 10px; padding: 10px 14px; font-size: .9rem; margin-bottom: 12px; }
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


def show():
    from utils.auth_guard import require_auth
    require_auth()
    from utils.database import get_usuario_id_from_session

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Plano e cobrança</h1>', unsafe_allow_html=True)

    usuario = st.session_state.get("usuario") or {}
    email = (usuario.get("email") if isinstance(usuario, dict) else getattr(usuario, "email", "")) or ""
    uid = get_usuario_id_from_session()
    perfil = carregar_perfil(email or uid or "") or {}
    plano = (perfil.get("plano") or "gratuito").lower()

    # ---------- situação ----------
    if is_pro(perfil):
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

    dias = dias_restantes_trial(perfil)
    if plano == "cancelado":
        st.markdown('<div class="pl-status alerta"><span class="rot">Situação</span>'
                    '<div class="val">Assinatura cancelada</div>'
                    '<span class="sub">Seus dados continuam guardados. Assine de novo para voltar a usar todos os recursos.</span></div>',
                    unsafe_allow_html=True)
    elif dias > 0:
        st.markdown(f'<div class="pl-status"><span class="rot">Situação</span>'
                    f'<div class="val">Teste grátis: {dias} dia{"s" if dias != 1 else ""} restante{"s" if dias != 1 else ""}</div>'
                    f'<span class="sub">O teste dura {DIAS_TRIAL} dias com tudo liberado. Assine antes do fim para não interromper o acesso.</span></div>',
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
    <div class="pl-fundadora"><b>Cupom de lançamento ORGANIZA:</b> 25% de desconto por 6 meses para as 50 primeiras assinantes. No mensal, cerca de R$ 29,90 por mês nos 6 primeiros meses; no anual, R$ 222,75 no primeiro ano. Digite o cupom na tela de pagamento.</div>
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
