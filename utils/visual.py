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


# ícones de traço (mesma família dos do menu lateral), no lugar de emoji e de símbolos de texto
_TRACOS = {
    "mensagem": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "retorno": '<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/>',
    "bolo": '<path d="M4 21h16"/><path d="M5 21v-7a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v7"/>'
            '<path d="M5 16c1.5 1 3 1 4.5 0s3-1 4.5 0 3 1 5 0"/><path d="M12 12V8"/><path d="M12 5.5a1 1 0 0 0 0-2"/>',
    "receber": '<path d="M12 4v13"/><path d="m6 11 6 6 6-6"/><path d="M5 21h14"/>',
    "pagar": '<path d="M12 20V7"/><path d="m6 13 6-6 6 6"/><path d="M5 3h14"/>',
    "visita": '<path d="M12 21s-7-6.1-7-11.5a7 7 0 0 1 14 0C19 14.9 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "servico": '<path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/><path d="M4 12h16"/>',
}


def icone(nome, tam=18):
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{_TRACOS.get(nome, "")}</svg>')
