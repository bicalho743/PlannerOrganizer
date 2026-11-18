"""
Onboarding na web, igual ao do app (bicalho743/planner-app, docs/onboarding/):

- Perguntas: conta nova (sem empresa, clientes e propostas) que ainda não respondeu vê uma janela com
  nome, negócio, tempo de atuação, o que mais pesa e formalização. Tudo dá para pular.
  As respostas vão para perfis.onboarding (JSON); nome e empresa para o perfil; MEI/Simples para o regime.
- Primeiros passos (Início): os mesmos 5 do app, na ordem do que ela marcou, até fechar ou terminar.
"""
from datetime import date

import streamlit as st

TEMPOS = {"comecando": "Estou começando", "ate2": "Até 2 anos", "mais2": "Mais de 2 anos"}
DORES = {"cobrar": "Saber quanto cobrar", "propostas": "Propostas com cara profissional",
         "retornos": "Lembrar dos retornos às clientes", "dinheiro": "Controlar o dinheiro do mês",
         "mei": "MEI e impostos"}
FORMAIS = {"mei": "MEI", "simples": "Simples Nacional", "nao": "Ainda não sou formalizada"}

CSS = """
<style>
.onb-etapa { font-size: .74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--gold-dark); }
.onb-titulo { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.8rem; font-weight: 600; color: #0D1B2A;
              line-height: 1.15; margin: 2px 0 4px; }
.onb-titulo em { color: #8A6A1C; }
.onb-texto { color: #475467; font-size: .95rem; line-height: 1.5; margin-bottom: 6px; }
</style>
"""


def _db():
    return st.session_state.db


def onboarding():
    """Respostas guardadas (uma leitura por sessão)."""
    if "_onb" not in st.session_state:
        try:
            st.session_state["_onb"] = _db().get_onboarding() or {}
        except Exception as e:
            print(f"[onboarding] {e}")
            st.session_state["_onb"] = {"erro": True}  # na dúvida, não abre nada
    return st.session_state["_onb"]


def _salvar(dados):
    try:
        _db().salvar_onboarding(dados)
    except Exception as e:
        print(f"[onboarding] {e}")
    st.session_state["_onb"] = {**onboarding(), **dados}


def conta_nova():
    """Sem empresa, sem clientes e sem propostas (uma leitura por sessão)."""
    if "_onb_conta_nova" not in st.session_state:
        try:
            db = _db()
            perfil = db.get_perfil_usuario() or {}
            if hasattr(perfil, "to_dict"):
                perfil = perfil.to_dict()
            empresa = str((perfil or {}).get("empresa") or "").strip()
            st.session_state["_onb_conta_nova"] = (not empresa and db.get_clientes().empty and db.get_propostas().empty)
        except Exception as e:
            print(f"[onboarding] {e}")
            st.session_state["_onb_conta_nova"] = False
    return st.session_state["_onb_conta_nova"]


def precisa_perguntas():
    o = onboarding()
    return not o and conta_nova()


def mostrar_perguntas():
    """Janela das perguntas. Chamar no fim da execução do app (uma janela por vez). True se abriu."""
    if not precisa_perguntas():
        return False

    def _pular():
        _salvar({"pulou": date.today().isoformat(), "origem": "web", "passos": "ativo"})

    @st.dialog("Vamos montar o seu Planner", width="large", on_dismiss=lambda: _pular())
    def _janela():
        u = st.session_state.get("usuario") or {}
        st.markdown(CSS + '<div class="onb-etapa">Leva 1 minuto</div>'
                    '<div class="onb-titulo">Que bom ter você aqui! <em>Conte um pouco do seu negócio.</em></div>'
                    '<div class="onb-texto">Com isso eu deixo o Planner no seu jeito: o nome sai nas propostas e os '
                    'primeiros passos ficam na ordem do que mais pesa para você.</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        nome = c1.text_input("Como quer ser chamada?", value=(u.get("nome") or u.get("name") or "").split(" ")[0],
                             key="onb_nome")
        empresa = c2.text_input("Nome do seu negócio", placeholder="Ana Lima Organização", key="onb_empresa")
        tempo = st.radio("Há quanto tempo você atua como personal organizer?", list(TEMPOS), index=None,
                         format_func=TEMPOS.get, horizontal=True, key="onb_tempo")
        dores = st.pills("O que mais pesa hoje? (pode marcar mais de uma)", list(DORES), selection_mode="multi",
                         format_func=DORES.get, key="onb_dores")
        formal = st.radio("Como o seu negócio é formalizado?", list(FORMAIS), index=None, format_func=FORMAIS.get,
                          horizontal=True, key="onb_formal")
        st.caption("O app organiza, mas não substitui o seu contador.")
        b1, b2 = st.columns([1, 2], vertical_alignment="center")
        if b1.button("Pular", key="onb_pular", type="tertiary"):
            _pular(); st.rerun()
        if b2.button("Ver meu Planner", key="onb_salvar", type="primary", use_container_width=True):
            db = _db()
            dados = {}
            if (nome or "").strip():
                dados["nome"] = nome.strip()
            if (empresa or "").strip():
                dados["empresa"] = empresa.strip()
            try:
                if dados:
                    db.salvar_perfil_usuario(dados)
                if formal == "mei":
                    db.salvar_regime("MEI")
                elif formal == "simples":
                    db.salvar_regime("Simples Nacional")
            except Exception as e:
                print(f"[onboarding] {e}")
            _salvar({"tempo": tempo, "dores": list(dores or []), "formal": formal, "origem": "web",
                     "respondido": date.today().isoformat(), "passos": "ativo"})
            st.session_state.pop("_onb_conta_nova", None)
            st.rerun()

    _janela()
    return True


# ---------- Primeiros passos (Início) ----------

def _precificacao_feita(db):
    try:
        from utils import precificacao as pr
        salvos = db.get_precificacao() or {}
        return any(k in pr.PADROES and float(v or 0) != float(pr.PADROES[k]) for k, v in salvos.items())
    except Exception:
        return False


def _tem_compromisso(db):
    try:
        return bool(db.get_compromissos())
    except Exception:
        return False


def _tem_celular(db):
    """Algum celular da conta recebe os avisos (o app registrou o aviso da manhã)."""
    try:
        from sqlalchemy import text
        from utils.database import engine
        with engine.connect() as conn:
            return conn.execute(text("SELECT 1 FROM push_tokens WHERE usuario_id = :u LIMIT 1"),
                                {"u": db.usuario_id}).first() is not None
    except Exception:
        return False


def passos(perfil, clientes, propostas):
    """Lista (id, título, detalhe, página, rótulo do botão, feito, marcou) na ordem: proposta + o que ela marcou."""
    db = _db()
    dores = onboarding().get("dores") or []
    lista = [
        ("proposta", "Crie a primeira proposta", "Monte o orçamento e gere o PDF com a sua marca.", "Propostas",
         "Criar proposta", not propostas.empty, "propostas"),
        ("cobrar", "Descubra quanto cobrar", "Hora, diária e preço de projeto a partir dos seus custos.", "Precificacao",
         "Calcular", _precificacao_feita(db), "cobrar"),
        ("app", "Receba os avisos no celular", "Instale o app e entre com esta conta: ele avisa retornos e cobranças "
         "de manhã.", None, None, _tem_celular(db), "retornos"),
        ("logo", "Coloque sua marca", "Logotipo, cores e contatos saem em todas as propostas em PDF.", "Perfil",
         "Abrir Perfil e marca", bool((perfil or {}).get("logo")), None),
        ("compromisso", "Marque um compromisso", "Visita, diária ou orçamento na Agenda.", "Agenda", "Abrir Agenda",
         _tem_compromisso(db), None),
    ]
    resto = sorted(lista[1:], key=lambda p: 0 if p[6] in dores else 1)
    return [lista[0]] + resto, dores


def mostrar_passos(perfil, clientes, propostas):
    """True se mostrou o cartão. Aparece para conta sem dados ou que respondeu o onboarding (até fechar ou terminar)."""
    o = onboarding()
    sem_dados = clientes.empty and propostas.empty
    if o.get("passos") == "fechado" or (not sem_dados and o.get("passos") != "ativo"):
        return False
    itens, dores = passos(perfil, clientes, propostas)
    feitos = sum(1 for p in itens if p[5])
    if feitos == len(itens):
        _salvar({"passos": "fechado"})
        return False
    c_tit, c_fechar = st.columns([6, 1], vertical_alignment="center")
    c_tit.markdown(f'<div class="ini-secao">Primeiros passos · {feitos} de {len(itens)}</div>', unsafe_allow_html=True)
    if not sem_dados and c_fechar.button("Fechar", key="ini_passos_fechar", type="tertiary"):
        _salvar({"passos": "fechado"}); st.rerun()
    proximo = next((i for i, p in enumerate(itens, 1) if not p[5]), None)
    for i, (pid, t, d, pagina, rotulo, feito, dor) in enumerate(itens, 1):
        with st.container(border=True):
            c1, c2 = st.columns([5, 2], vertical_alignment="center")
            marca = ('<span class="n ok">✓</span>' if feito
                     else f'<span class="n{" prox" if i == proximo else ""}">{i}</span>')
            extra = (' <span style="font-size:.7rem;font-weight:700;color:#8A6A1C;background:#F6F0DF;'
                     'border-radius:20px;padding:2px 8px;margin-left:6px">Você marcou</span>'
                     if (dor and dor in dores and not feito) else "")
            c1.markdown(f'<div class="ini-passo">{marca}<div class="ini-txt"><b>{t}</b>{extra}'
                        f'<span class="det">{d}</span></div></div>', unsafe_allow_html=True)
            if feito:
                continue
            with c2.container(key=f"cta_passo_{i}" if i == proximo else f"passo_{i}"):
                if pid == "app":
                    st.link_button("Baixar o app", "https://plannerorganiza.com.br/#baixar", use_container_width=True)
                elif st.button(rotulo, key=f"ini_passo_{pid}", use_container_width=True):
                    st.session_state.current_page = pagina
                    st.rerun()
    return True
