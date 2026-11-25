"""
Peças visuais do desenho novo (um só destaque dourado), usadas no Início e na Agenda do site.

- hoje() e agora(): horário de Brasília (o servidor do Render roda em UTC; sem isso, depois das 21h o "hoje"
  viraria o dia seguinte);
- pilula(status): a escala de situação das propostas
  ○ Em aberto (contorno dourado) · ● Aprovada (dourado) · ▶ Em execução (azul-marinho) · ✓ Concluída (verde).
"""
import html
from datetime import datetime, timedelta, timezone

BRASILIA = timezone(timedelta(hours=-3))

PILULAS = {
    # status normalizado: (símbolo, rótulo, classe)
    "em_aberto": ("○", "Em aberto", "ab"),
    "aprovada": ("●", "Aprovada", "ap"),
    "em_execucao": ("▶", "Em execução", "ex"),
    "finalizada": ("✓", "Concluída", "co"),
    "recusada": ("✕", "Recusada", "re"),
}

CSS_PILULA = """
.pv-pil { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px;
          font-size: .74rem; font-weight: 700; white-space: nowrap; line-height: 1.3; }
.pv-pil.ab { border: 1.5px solid #C9A84C; color: #7A5F0B; background: #fff; }
.pv-pil.ap { background: #F6EDD3; color: #7A5F0B; }
.pv-pil.ex { background: #E3E8F0; color: #0D1B2A; }
.pv-pil.co { background: #E3F1E8; color: #2F6B4F; }
.pv-pil.re { background: #F2F4F7; color: #667085; }
"""

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def agora():
    return datetime.now(BRASILIA)


def hoje():
    return agora().date()


def saudacao(hora=None):
    h = agora().hour if hora is None else hora
    return "Bom dia" if 5 <= h < 12 else ("Boa tarde" if 12 <= h < 18 else "Boa noite")


def esc(v):
    return html.escape(str(v if v is not None else ""))


def pilula(status):
    simbolo, rotulo, cls = PILULAS.get(status, ("", str(status or ""), "re"))
    return f'<span class="pv-pil {cls}">{simbolo} {rotulo}</span>'
