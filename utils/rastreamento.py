"""
Google Analytics (G-E9KP3F40VT) e Pixel da Meta (654529850558184) na página do app.

O Streamlit não executa <script> vindo de st.markdown, e um components.html roda num iframe:
por isso o script abaixo, dentro do iframe, escreve as tags no documento principal
(window.parent), uma vez só. Os eventos ficam numa fila da sessão (evento) e saem no fim de
cada execução (disparar), também pela página principal. Eventos de "uma vez por pessoa"
(cadastro, compra) levam uma chave guardada no localStorage para não repetir.

Funis que importam para anúncio no Instagram:
  CompleteRegistration / sign_up      conta criada
  PrimeiraProposta / primeira_proposta ativação
  InitiateCheckout / begin_checkout   clicou em assinar (onclick nos links de pagamento)
  Purchase / purchase                 plano ativo pela primeira vez
"""
import json

import streamlit as st
import streamlit.components.v1 as components

GA_ID = "G-E9KP3F40VT"
PIXEL_ID = "654529850558184"

_INSTALAR = """
<script>
(function(){
  var w = window.parent, d = w.document;
  if (d.getElementById('po-rastreamento')) return;
  var m = d.createElement('meta'); m.id = 'po-rastreamento'; d.head.appendChild(m);
  var g = d.createElement('script'); g.async = true; g.src = 'https://www.googletagmanager.com/gtag/js?id=%(ga)s';
  d.head.appendChild(g);
  w.dataLayer = w.dataLayer || [];
  w.gtag = w.gtag || function(){ w.dataLayer.push(arguments); };
  w.gtag('js', new Date()); w.gtag('config', '%(ga)s');
  if (!w.fbq) {
    var n = w.fbq = function(){ n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
    if (!w._fbq) w._fbq = n; n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
    var f = d.createElement('script'); f.async = true; f.src = 'https://connect.facebook.net/en_US/fbevents.js';
    d.head.appendChild(f);
  }
  w.fbq('init', '%(px)s'); w.fbq('track', 'PageView');
})();
</script>
""" % {"ga": GA_ID, "px": PIXEL_ID}


def instalar():
    """Coloca GA e Pixel na página principal (uma vez por carregamento do navegador)."""
    components.html(_INSTALAR, height=0)


def evento(ga, meta, params=None, meta_custom=False, uma_vez=None):
    """Põe um evento na fila. uma_vez: chave do localStorage que impede repetir no mesmo navegador."""
    st.session_state.setdefault("_po_eventos", []).append(
        {"ga": ga, "meta": meta, "params": params or {}, "custom": meta_custom, "chave": uma_vez})


def disparar():
    """Envia os eventos da fila pela página principal. Chamar no fim da execução do app."""
    fila = st.session_state.pop("_po_eventos", [])
    if not fila:
        return
    components.html(f"""
<script>
(function(){{
  var w = window.parent, fila = {json.dumps(fila)}, n = 0;
  var t = setInterval(function(){{
    if (!(w.gtag && w.fbq) && ++n < 50) return;
    clearInterval(t);
    fila.forEach(function(e){{
      try {{
        if (e.chave) {{ if (w.localStorage.getItem(e.chave)) return; w.localStorage.setItem(e.chave, '1'); }}
      }} catch (x) {{}}
      if (w.gtag) w.gtag('event', e.ga, e.params);
      if (w.fbq) w.fbq(e.custom ? 'trackCustom' : 'track', e.meta, e.params);
    }});
  }}, 100);
}})();
</script>""", height=0)


CAMPOS_ORIGEM = ("tema", "utm_source", "utm_medium", "utm_campaign", "utm_content")


def guardar_origem(query_params):
    """Guarda na sessão de onde a pessoa veio (tema do anúncio e UTMs que a landing repassa)."""
    origem = {k: str(query_params.get(k))[:60] for k in CAMPOS_ORIGEM if query_params.get(k)}
    if origem:
        st.session_state["_origem_visita"] = origem


def origem_da_visita():
    return dict(st.session_state.get("_origem_visita") or {})


def onclick_checkout(plano, valor):
    """Atributo onclick para os links de pagamento (rodam na página principal, onde gtag/fbq estão)."""
    p = f"{{value:{valor},currency:'BRL'}}"
    return (f"onclick=\"try{{localStorage.setItem('po_plano','{plano}')}}catch(e){{}};"
            f"window.gtag&&gtag('event','begin_checkout',{p});"
            f"window.fbq&&fbq('track','InitiateCheckout',{p})\"")


def compra_se_assinante(perfil, uid):
    """Purchase uma vez por pessoa, na primeira vez que o app a vê com plano ativo."""
    from utils.trial import is_pro
    if not uid or not is_pro(perfil):
        return
    components.html(f"""
<script>
(function(){{
  var w = window.parent, chave = 'po_compra_{uid}', n = 0;
  try {{ if (w.localStorage.getItem(chave)) return; }} catch (x) {{ return; }}
  var t = setInterval(function(){{
    if (!(w.gtag && w.fbq) && ++n < 50) return;
    clearInterval(t);
    var anual = (w.localStorage.getItem('po_plano') === 'anual');
    var p = {{value: anual ? 297 : 29.9, currency: 'BRL'}};
    w.localStorage.setItem(chave, '1');
    if (w.gtag) w.gtag('event', 'purchase', p);
    if (w.fbq) w.fbq('track', 'Purchase', p);
  }}, 100);
}})();
</script>""", height=0)
