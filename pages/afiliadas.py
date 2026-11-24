"""
Programa de afiliadas (utils/afiliados.py).

- Qualquer conta pode se inscrever (nome, CPF, Pix). Fica pendente até a dona aprovar.
- Aprovada: link e código para divulgar, indicações, comissões a liberar, liberadas e recebidas.
- Quem está em ADMIN_EMAILS (variável do servidor, e-mails separados por vírgula) vê a administração:
  aprovar ou recusar inscrições e o Pix do mês (quem tem R$ 50 ou mais liberados), com "marcar como pago".
"""
import os
from datetime import date

import streamlit as st

from utils import afiliados as af

LINK_BASE = "https://plannerorganiza.com.br/?ref="

TERMOS = f"""
**Como funciona**
- Você ganha **{int(af.PERCENTUAL * 100)}% de cada pagamento** de quem assinar pelo seu link ou código,
  **durante {af.MESES_COMISSAO} meses** a partir do primeiro pagamento, no site, no iPhone ou no Android.
- A comissão é calculada sobre o valor que de fato entra (sem a taxa do cartão ou da loja).
- Quem usa o seu link ou código testa o Planner grátis por {af.DIAS_TESTE_INDICADA} dias, como todo mundo.
- A comissão fica liberada **{af.DIAS_LIBERAR} dias depois** do pagamento da indicada (prazo de reembolso).
  Se houver reembolso, a comissão é cancelada.
- O pagamento é feito **todo mês por Pix**, quando o valor liberado chega a **R$ {af.MINIMO_PAGAMENTO:.0f}**.

**Regras**
- Não vale indicar a si mesma nem criar contas para ganhar comissão.
- Não é permitido anunciar no Google usando o nome "Planner Organiza" nem fingir ser o Planner Organiza.
- Comissões pagas a pessoa física podem ter retenção de impostos conforme a lei; se você for MEI, pode emitir nota.
- O programa pode mudar ou acabar com aviso de 30 dias; comissões já liberadas continuam garantidas.
"""


def _brl(v):
    return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _emails_da_sessao(uid):
    """E-mails da conta conectada, das mesmas fontes do topo do menu (perfil, login do Firebase, usuário)."""
    usuario = st.session_state.get("usuario") or {}
    user = st.session_state.get("user") or {}
    lista = [(user.get("email") if isinstance(user, dict) else ""),
             (usuario.get("email") if isinstance(usuario, dict) else getattr(usuario, "email", ""))]
    try:
        from pages.perfil import carregar_perfil
        lista.append((carregar_perfil(uid) or {}).get("email"))
    except Exception:
        pass
    return [e.strip() for e in lista if e and e.strip()]


def _admin(email):
    lista = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    return bool(email) and email.strip().lower() in lista


def show():
    from utils.auth_guard import require_auth
    require_auth()
    from utils.database import get_usuario_id_from_session, engine

    uid = get_usuario_id_from_session()
    emails = _emails_da_sessao(uid)
    email = emails[0] if emails else ""

    st.markdown('<h1 class="page-title">Indique e ganhe</h1>', unsafe_allow_html=True)
    eu = af.afiliada_da_conta(engine, uid)
    admin = any(_admin(e) for e in emails)

    if admin:  # administradora: a administração vem primeiro; a inscrição dela mesma fica recolhida
        _administracao(engine)
        st.divider()
        if not eu:
            with st.expander("Quero ser afiliada também (opcional)"):
                _inscricao(engine, uid, email)
        else:
            _minha_situacao(engine, eu)
        return

    if not eu:
        _codigo_de_indicacao(engine, uid, emails)
        _inscricao(engine, uid, email)
    else:
        _minha_situacao(engine, eu)


DIAS_PARA_INFORMAR_CODIGO = 7  # conta nova pode informar quem a indicou, como o "Tenho um convite" do app


def _codigo_de_indicacao(engine, uid, emails):
    """Conta nova, ainda sem afiliada: pode digitar o código de quem a indicou (se o link não ligou sozinho)."""
    try:
        if not uid or af.codigo_da_indicacao(engine, uid):
            return
        from pages.perfil import carregar_perfil
        from utils.trial import _data_cadastro_para_date
        cadastro = _data_cadastro_para_date((carregar_perfil(uid) or {}).get("data_cadastro"))
        if not cadastro or (date.today() - cadastro).days > DIAS_PARA_INFORMAR_CODIGO:
            return
    except Exception as e:
        print(f"[afiliados] código de indicação: {e}")
        return
    with st.expander("Foi indicada por alguém? Digite o código da indicação"):
        with st.form("form_codigo_indicacao"):
            cod = st.text_input("Código", placeholder="Ex.: TAMARA")
            if st.form_submit_button("Confirmar"):
                try:
                    from utils import convites
                    convites.resgatar(engine, uid, cod)
                    st.success("Pronto! Sua conta ficou ligada a quem indicou você.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


def _minha_situacao(engine, eu):
    if eu["status"] == "pendente":
        st.info(f"Sua inscrição está em análise. Código reservado: **{eu['codigo']}**. "
                "Assim que for aprovada, o seu link aparece aqui.")
    elif eu["status"] == "recusada":
        st.warning("Sua inscrição não foi aprovada desta vez. Fale com a gente em contato@candeiatec.com.br.")
    else:
        _painel_afiliada(engine, eu)


def _inscricao(engine, uid, email):
    st.markdown(f"Indique o Planner Organiza para outras organizers e ganhe **{int(af.PERCENTUAL * 100)}% "
                f"de cada pagamento por {af.MESES_COMISSAO} meses**, recebendo por Pix todo mês.")
    st.markdown(TERMOS)
    with st.form("form_afiliada"):
        nome = st.text_input("Nome completo")
        c1, c2 = st.columns(2)
        cpf = c1.text_input("CPF")
        pix = c2.text_input("Chave Pix")
        instagram = st.text_input("Instagram (opcional)", placeholder="@seuperfil")
        codigo = st.text_input("Código que você quer usar (opcional)", placeholder="Ex.: TAMARA",
                               help="Só letras e números. Se ficar em branco, usamos o seu primeiro nome.")
        aceite = st.checkbox("Li e aceito as regras do programa")
        if st.form_submit_button("Quero ser afiliada", type="primary"):
            if not aceite:
                st.error("Para continuar, marque que aceita as regras do programa.")
            else:
                try:
                    cod = af.inscrever(engine, uid, nome, email, cpf, pix, instagram, codigo)
                    st.success(f"Inscrição enviada! Seu código reservado é **{cod}**. "
                               "Assim que for aprovada, o seu link aparece nesta página.")
                    st.rerun()
                except af.AfiliadoInvalido as e:
                    st.error(str(e))


def _painel_afiliada(engine, eu):
    link = LINK_BASE + eu["codigo"]
    p = af.painel(engine, eu["codigo"])
    st.markdown("**Seu link para divulgar**")
    st.code(link, language=None)
    st.markdown(f"Ou peça para digitarem o código **{eu['codigo']}** em \"Tenho um convite\", ao criar a conta no app.")
    c = st.columns(4)
    c[0].metric("Indicadas", p["indicadas"])
    c[1].metric("Assinantes", p["assinantes"])
    c[2].metric("Liberado para receber", _brl(p["liberado"]),
                help=f"Pago por Pix no início do mês, a partir de R$ {af.MINIMO_PAGAMENTO:.0f}.")
    c[3].metric("A liberar", _brl(p["a_liberar"]), help=f"Fica liberado {af.DIAS_LIBERAR} dias após o pagamento.")
    st.caption(f"Já recebido: {_brl(p['recebido'])} · Pix cadastrado: {eu['pix']}")
    if p["comissoes"]:
        st.markdown("**Comissões**")
        st.dataframe([{
            "Data": str(x["pago_em"])[:10], "Canal": af.CANAIS.get(x["canal"], x["canal"]),
            "Pagamento": _brl(x["valor_pago"]), "Comissão": _brl(x["comissao"]),
            "Situação": {"pendente": "A liberar" if str(x["liberada_em"])[:10] > date.today().isoformat()
                         else "Liberada", "paga": "Paga", "cancelada": "Cancelada (reembolso)"}[x["status"]],
        } for x in p["comissoes"]], hide_index=True, use_container_width=True)
    with st.expander("Regras do programa"):
        st.markdown(TERMOS)


def _administracao(engine):
    st.markdown("### Administração do programa")
    st.caption("Só administradoras veem esta parte.")
    pend = af.listar_afiliadas(engine, "pendente")
    st.markdown(f"**Inscrições para aprovar ({len(pend)})**")
    for a in pend:
        with st.container(border=True):
            st.markdown(f"**{a['nome']}** · código {a['codigo']} · {a.get('email') or ''} · "
                        f"{a.get('instagram') or 'sem Instagram'} · CPF {a['cpf']} · Pix {a['pix']}")
            b1, b2, _ = st.columns([1, 1, 4])
            if b1.button("Aprovar", key=f"apr_{a['codigo']}", type="primary"):
                af.mudar_status(engine, a["codigo"], "aprovada"); st.rerun()
            if b2.button("Recusar", key=f"rec_{a['codigo']}"):
                af.mudar_status(engine, a["codigo"], "recusada"); st.rerun()

    st.markdown("**Pix do mês** (comissões liberadas a partir de R$ 50)")
    pagar = af.a_pagar(engine)
    if not pagar:
        st.caption("Ninguém para pagar agora.")
    for a in pagar:
        with st.container(border=True):
            st.markdown(f"**{a['nome']}** ({a['codigo']}) · **{_brl(a['valor'])}** · Pix: `{a['pix']}` · CPF {a['cpf']}")
            if st.button("Marquei como pago", key=f"pg_{a['codigo']}"):
                total = af.marcar_pago(engine, a["codigo"])
                st.success(f"{_brl(total)} marcados como pagos para {a['nome']}."); st.rerun()

    aprovadas = af.listar_afiliadas(engine, "aprovada")
    if aprovadas:
        st.markdown(f"**Afiliadas aprovadas ({len(aprovadas)})**")
        linhas = []
        for a in aprovadas:
            p = af.painel(engine, a["codigo"])
            linhas.append({"Nome": a["nome"], "Código": a["codigo"], "Indicadas": p["indicadas"],
                           "Assinantes": p["assinantes"], "A liberar": _brl(p["a_liberar"]),
                           "Liberado": _brl(p["liberado"]), "Recebido": _brl(p["recebido"])})
        st.dataframe(linhas, hide_index=True, use_container_width=True)
