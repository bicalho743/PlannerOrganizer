"""
Funil de vendas (só para administradoras, ADMIN_EMAILS): do cadastro à assinatura, por período, canal e origem.
Os números vêm de utils/funil.py.
"""
import streamlit as st

from utils import funil


def e_admin() -> bool:
    try:
        from pages.afiliadas import _admin, _emails_da_sessao
        from utils.database import get_usuario_id_from_session
        return any(_admin(e) for e in _emails_da_sessao(get_usuario_id_from_session()))
    except Exception:
        return False


def _barra(rotulo, n, pct_total, pct_ant, primeira):
    largura = max(2, min(100, pct_total))
    queda = "" if primeira else f" · {pct_ant:.0f}% da etapa anterior"
    st.markdown(
        f"""<div style="margin:.35rem 0 .7rem">
  <div style="display:flex;justify-content:space-between;font-size:.92rem;color:#16283E">
    <span><b>{rotulo}</b></span><span><b>{n}</b> <span style="color:#6B7C94">({pct_total:.0f}%{queda})</span></span></div>
  <div style="background:#EEE7D6;border-radius:6px;height:12px;margin-top:4px">
    <div style="width:{largura}%;background:#C9A84C;height:12px;border-radius:6px"></div></div>
</div>""", unsafe_allow_html=True)


def _funil(lista, titulo=None):
    if titulo:
        st.markdown(f"**{titulo}** · {len(lista)} conta(s)")
    if not lista:
        st.caption("Nenhuma conta neste recorte.")
        return
    for i, (_, rotulo, n, pt, pa) in enumerate(funil.resumo(lista)):
        _barra(rotulo, n, pt, pa, i == 0)


def show():
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown('<h1 class="page-title">Funil de vendas</h1>', unsafe_allow_html=True)
    if not e_admin():
        st.info("Esta página é só para a administração.")
        return
    from utils.database import engine

    dias = st.radio("Contas criadas nos últimos", [7, 14, 30, 60], index=2, horizontal=True,
                    format_func=lambda d: f"{d} dias", key="funil_dias")
    desde, ate = funil.periodo(dias)
    lista = funil.contas(engine, desde, ate)
    st.caption(f"De {desde:%d/%m} a {ate:%d/%m}. Cada barra mostra quantas contas chegaram à etapa e a porcentagem "
               "sobre o total de cadastros e sobre a etapa anterior.")

    _funil(lista)

    st.divider()
    st.markdown("### Por canal")
    st.caption("Canal em que a conta apareceu primeiro. \"?\" são contas de antes desta medição (24/11/2026).")
    grupos = funil.por_grupo(lista, "canal")
    cols = st.columns(max(1, min(3, len(grupos))))
    for i, (canal, itens) in enumerate(sorted(grupos.items(), key=lambda kv: -len(kv[1]))):
        with cols[i % len(cols)]:
            _funil(itens, {"app": "App (celular)", "site": "Site"}.get(canal, "Sem canal registrado"))

    st.markdown("### Por origem")
    for origem, itens in sorted(funil.por_grupo(lista, "origem").items(), key=lambda kv: -len(kv[1])):
        with st.expander(f"{origem} · {len(itens)} conta(s)"):
            _funil(itens)

    st.markdown("### Contas do período")
    marca = lambda b: "✓" if b else ""
    st.dataframe([{
        "Cadastro": str(x["data_cadastro"])[:10], "E-mail": x["email"], "Canal": x["canal"], "Origem": x["origem"],
        "Questionário": marca(x["onboarding"]), "Cliente": marca(x["cliente"]), "Proposta": marca(x["proposta"]),
        "PDF": marca(x["pdf"]), "Viu planos": marca(x["planos"]), "Assinou": marca(x["assinou"]),
    } for x in lista], hide_index=True, use_container_width=True)
    st.caption("PDF e \"Viu planos\" começaram a ser medidos em 24/11/2026; antes disso aparecem vazios.")

    st.divider()
    with st.expander("Ferramenta: renumerar as propostas de uma conta (1, 2, 3...)"):
        st.caption("Para contas antigas, cujos números seguiam a contagem do banco todo. A ordem nova segue a data "
                   "da proposta. Os lançamentos e PDFs continuam ligados; só o número mostrado muda. "
                   "Lançamentos antigos do Financeiro guardam o número antigo no texto da descrição.")
        from sqlalchemy import text as _t
        from utils import renumerar as rn
        email = st.text_input("E-mail da conta", key="renum_email").strip().lower()
        if email:
            with engine.connect() as c:
                u = c.execute(_t("SELECT usuario_id FROM perfis WHERE lower(email) = :e"), {"e": email}).first()
            if not u:
                st.warning("Nenhuma conta com esse e-mail.")
            else:
                prev = rn.previa(engine, u[0])
                if not prev:
                    st.info("Essa conta não tem propostas.")
                else:
                    st.dataframe([{"Data": str(d or "")[:10], "Número atual": a, "Número novo": n}
                                  for _, a, n, d in prev], hide_index=True, use_container_width=True)
                    if st.button(f"Renumerar as {len(prev)} propostas", key="renum_ok", type="primary"):
                        try:
                            m = rn.renumerar(engine, u[0])
                            st.success(f"Pronto: {m} proposta(s) mudaram de número.")
                        except Exception as e:
                            st.error(str(e))

