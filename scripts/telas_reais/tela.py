"""Abre uma tela do sistema já logada na conta de demonstração, sem menu nem cabeçalho do Streamlit
(para gravar as telas reais). Uso: streamlit run tela.py -- ; no navegador /?t=<tela>&modo=celular|computador"""
import importlib
import os
import sys

import streamlit as st

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, RAIZ)
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
st.markdown(f"<style>{open(os.path.join(RAIZ, '.streamlit/style.css')).read()}</style>", unsafe_allow_html=True)
st.markdown("""<style>:root { --modulo: #B8943D; }
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .viewerBadge_container__1QSob { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { margin-left: 0 !important; width: 100% !important; max-width: 100% !important;
  padding-top: 1.2rem !important; }
@media (min-width: 769px) { .block-container, [data-testid="stMainBlockContainer"] { padding: 2rem 3.5rem !important; } }
</style>""", unsafe_allow_html=True)

from utils.database import Database  # noqa: E402

st.session_state.authenticated = True
st.session_state.usuario_id = "demo_landing"
st.session_state.usuario = {"nome": "Ana Ribeiro", "email": "ana@exemplo.com.br"}
if "db" not in st.session_state:
    st.session_state.db = Database(usuario_id="demo_landing")
MAPA = {"inicio": ("pages.dashboard", "Dashboard"), "agenda": ("pages.agenda", "Agenda"),
        "propostas": ("pages.propostas_unificado", "Propostas"), "precificacao": ("pages.precificacao", "Precificacao"),
        "clientes": ("pages.cadastros", "Clientes"), "pos": ("pages.pos_organizacao", "PosOrganizacao"),
        "financeiro": ("pages.financeiro", "Financeiro"), "relatorios": ("pages.relatorios", "Relatórios"),
        "vendas": ("pages.vendas", "Vendas"), "perfil": ("pages.perfil", "Perfil")}
tela = st.query_params.get("t", "inicio")
mod, pagina = MAPA[tela]
st.session_state.setdefault("current_page", pagina)
m = importlib.import_module(mod)
_ = m.show(modo="clientes") if tela == "clientes" else m.show()
st.session_state["_last_page_rendered"] = pagina
