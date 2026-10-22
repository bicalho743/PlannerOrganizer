"""
Tutorial rápido: janela passo a passo com uma tela de cada módulo.

Abre sozinho na primeira entrada da conta (perfis.tutorial_visto vazio) e pode ser revisto pelo
botão "Tutorial rápido" do menu. As imagens ficam em static/tour (telas reais com dados fictícios,
as mesmas do vídeo de divulgação).
"""
import os

import streamlit as st

PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "tour")

# (imagem, título, texto, página do menu)
PASSOS = [
    ("01_inicio", "Seu dia numa tela só",
     "O Início mostra o lucro do mês, o que há para receber e pagar e a lista Para fazer: retornos, cobranças, "
     "propostas paradas e aniversários, cada um com o botão certo.", "Dashboard"),
    ("02_agenda", "Agenda que junta tudo",
     "Marque diárias, visitas e orçamentos. Com valor, o compromisso entra sozinho em A receber. A agenda também "
     "mostra serviços, aniversários, retornos e vencimentos.", "Agenda"),
    ("02b_aniversario", "Lembrete de aniversário",
     "No dia do aniversário da cliente, o Início e a Agenda avisam, com o botão Dar parabéns: a mensagem já vai "
     "pronta no WhatsApp.", "Dashboard"),
    ("03_clientes", "Clientes organizadas",
     "Nome e telefone já bastam. Origem e aniversário ajudam nos relatórios e nas mensagens. Dá para importar de planilha.",
     "Clientes"),
    ("04_propostas", "Do orçamento ao serviço",
     "Crie a proposta, baixe o PDF com a sua marca e aprove quando a cliente aceitar: sinal e saldo entram no "
     "Financeiro. Ao finalizar, os retornos são agendados.", "Propostas"),
    ("05_precificacao", "Saiba quanto cobrar",
     "Informe quanto quer ganhar, seus custos e suas horas: o app mostra a hora mínima, a sugerida e o preço de "
     "cada projeto.", "Precificacao"),
    ("06_vendas", "Venda de produtos",
     "Caixas, cabides e organizadores: a venda baixa o estoque, aceita parcelas e mostra o lucro.", "Vendas"),
    ("07_pos", "Nunca mais esqueça de retornar uma cliente",
     "Ao finalizar o serviço, o app agenda cinco retornos e lembra cada um no dia certo, com a mensagem pronta "
     "para mandar pelo WhatsApp.",
     "PosOrganizacao"),
    ("08_financeiro", "Financeiro sem planilha",
     "Quanto entrou, quanto gastou e quanto sobrou, com as contas a receber e a pagar. Clique num cartão para "
     "marcar como recebido ou pago.", "Financeiro"),
    ("09_mei", "MEI e Simples Nacional",
     "Na aba MEI, escolha o tipo da sua empresa: MEI, Simples Nacional ou outro. Você acompanha o DAS de cada mês, o "
     "limite do ano e o prazo da declaração. O app não é contador: em caso de dúvida, procure um.", "Financeiro"),
    ("10_relatorios", "Relatórios prontos",
     "Resultado do período, clientes, propostas e trabalhos, comparados com o período anterior, e o Excel "
     "formatado para o contador.", "Relatórios"),
    ("11_marca", "Com a sua marca",
     "Em Perfil e marca, envie o logotipo e escolha as cores: elas saem em todas as propostas e relatórios.",
     "Perfil"),
]

CSS = """
<style>
.tour-passo { font-size: .74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--gold-dark); }
.tour-titulo { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.7rem; font-weight: 600; color: #0D1B2A;
               margin: 2px 0 4px; line-height: 1.2; }
.tour-texto { color: #475467; font-size: .95rem; line-height: 1.55; margin-bottom: 10px; }
.tour-barra { display: flex; gap: 5px; margin: 6px 0 12px; }
.tour-barra i { flex: 1; height: 4px; border-radius: 99px; background: #E4E7EC; }
.tour-barra i.on { background: var(--gold); }
[class*="st-key-tour_img"] img { border: 1px solid #E4E7EC; border-radius: 10px; max-height: 46vh;
                                 object-fit: cover; object-position: top; }
</style>
"""


def precisa_mostrar():
    """True na primeira entrada da conta (uma consulta por sessão)."""
    if "_tour_visto" not in st.session_state:
        try:
            st.session_state["_tour_visto"] = bool(st.session_state.db.get_tutorial_visto())
        except Exception as e:
            print(f"[tour] {e}")
            st.session_state["_tour_visto"] = True  # na dúvida, não atrapalha
    return not st.session_state["_tour_visto"]


def abrir():
    st.session_state["tour_aberto"] = True
    st.session_state["tour_passo"] = 0


def _fechar(ir_para=None):
    st.session_state["tour_aberto"] = False
    st.session_state["_tour_visto"] = True
    try:
        st.session_state.db.marcar_tutorial_visto()
    except Exception as e:
        print(f"[tour] {e}")
    if ir_para:
        st.session_state.current_page = ir_para


def mostrar():
    """Chamar no fim da execução do app (uma janela por vez)."""
    if not st.session_state.get("tour_aberto") and precisa_mostrar():
        abrir()
    if not st.session_state.get("tour_aberto"):
        return

    @st.dialog("Tutorial rápido", width="large", on_dismiss=lambda: _fechar())
    def _janela():
        i = min(st.session_state.get("tour_passo", 0), len(PASSOS) - 1)
        img, titulo, texto, pagina = PASSOS[i]
        st.markdown(CSS + '<div class="tour-barra">' +
                    "".join(f'<i class="{"on" if k <= i else ""}"></i>' for k in range(len(PASSOS))) + "</div>"
                    f'<div class="tour-passo">Passo {i + 1} de {len(PASSOS)}</div>'
                    f'<div class="tour-titulo">{titulo}</div><div class="tour-texto">{texto}</div>',
                    unsafe_allow_html=True)
        caminho = os.path.join(PASTA, f"{img}.jpg")
        if os.path.exists(caminho):
            with st.container(key="tour_img"):
                st.image(caminho, use_container_width=True)
        c_pular, c_abrir, c_volta, c_vai = st.columns([1.1, 1.4, 1, 1.3], vertical_alignment="center")
        if c_pular.button("Pular tutorial", key="tour_pular", type="tertiary"):
            _fechar(); st.rerun()
        if c_abrir.button("Abrir esta tela", key="tour_abrir", icon=":material/open_in_new:", use_container_width=True):
            _fechar(pagina); st.rerun()
        if i > 0 and c_volta.button("Voltar", key="tour_voltar", use_container_width=True):
            st.session_state["tour_passo"] = i - 1; st.rerun()
        ultimo = i == len(PASSOS) - 1
        if c_vai.button("Começar a usar" if ultimo else "Próximo", key="tour_proximo", type="primary",
                        icon=None if ultimo else ":material/arrow_forward:", use_container_width=True):
            if ultimo:
                _fechar()
            else:
                st.session_state["tour_passo"] = i + 1
            st.rerun()

    _janela()
