"""
Helpers para links e botões de WhatsApp (logo oficial em SVG).
Usado no Dashboard e no módulo de Pós-Organização.
"""
import re
import urllib.parse

# Glifo oficial do WhatsApp (Font Awesome brands, licença CC BY 4.0)
WHATSAPP_SVG = (
    '<svg viewBox="0 0 448 512" width="15" height="15" fill="currentColor" '
    'style="flex-shrink:0;" aria-hidden="true">'
    '<path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 '
    '0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 '
    '0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 '
    '18.3L72 359.2l-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 '
    '0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 '
    '2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-32.6-16.3-54-29.1-75.5-66-5.7-9.8 '
    '5.7-9.1 16.3-30.3 1.8-3.7.9-6.9-.5-9.7-1.4-2.8-12.5-30.1-17.1-41.2-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 '
    '0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 '
    '59.7 94.8 83.8 35.2 15.2 49 16.5 66.6 13.9 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 '
    '3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>'
)

_BTN_BASE = (
    "display:flex;align-items:center;justify-content:center;gap:7px;"
    "border-radius:8px;padding:8px 12px;min-height:38px;box-sizing:border-box;"
    "font-size:0.85rem;font-weight:600;font-family:inherit;"
)


def format_telefone_whatsapp(telefone):
    """Normaliza o telefone para o formato internacional (DDI 55) usado no wa.me."""
    if telefone is None:
        return ""
    digits = re.sub(r"\D", "", str(telefone))
    if digits and not digits.startswith("55") and len(digits) in (10, 11):
        digits = "55" + digits
    return digits


def whatsapp_link(telefone, mensagem=""):
    """Retorna o link wa.me com a mensagem pré-preenchida, ou '' se não houver telefone."""
    digits = format_telefone_whatsapp(telefone)
    if not digits:
        return ""
    if mensagem:
        return f"https://wa.me/{digits}?text={urllib.parse.quote(str(mensagem))}"
    return f"https://wa.me/{digits}"


def whatsapp_button_html(url, label="WhatsApp"):
    """
    Botão de WhatsApp com o logo oficial. Se url for vazio, renderiza
    desabilitado (cliente sem telefone cadastrado).
    """
    if not url:
        return (
            f'<span style="{_BTN_BASE}background:#e2e8f0;color:#94a3b8;cursor:not-allowed;" '
            f'title="Cliente sem telefone cadastrado">{WHATSAPP_SVG} {label}</span>'
        )
    return (
        f'<a href="{url}" target="_blank" rel="noopener" '
        f'style="{_BTN_BASE}background:#25D366;color:#ffffff;text-decoration:none;">'
        f"{WHATSAPP_SVG} {label}</a>"
    )
