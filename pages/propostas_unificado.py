import streamlit as st
import streamlit.components.v1 as components
import base64
import logging
logging.basicConfig(level=logging.INFO)
from utils.finalizar_proposta_v2 import finalizar_proposta_v2
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import uuid
import plotly.graph_objects as go
import html as html_module
from utils.database import Fornecedor
from utils.propostas_helper import st_gerar_pdf_cliente, st_gerar_pdf_interno, st_gerar_pdf_fornecedores, gerar_pdf_proposta
from utils.design_tokens import (
    NAVY, NAVY_HOVER, GOLD,
)
from utils.status_execucao import EXEC_EM_EXECUCAO, EXEC_FINALIZADA, EXEC_CANCELADA
from utils.ui import botao_excluir, link_fechar, input_moeda, cartao_clicavel, baixar_pdf, botao_editar, botao_documento
from utils.visual import CSS_PILULA, esc, hoje, icone_whatsapp, pilula


def _safe_float(val, default=0.0):
    try:
        if pd.isna(val) or val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


from utils.currency_formatter import fmt_brl as _fmt_brl
from utils.formatadores import valor_ou_traco


def _proposal_meta_header(proposta, status_norm):
    """Pílula da situação (usada pela visão antiga de itens, _tab_itens)."""
    st.markdown(f'<div style="padding:4px 2px 12px">{pilula(status_norm)}</div>', unsafe_allow_html=True)


ABAS_DETALHE = ["Serviço", "Produtos", "Fornecedores", "Assistentes", "Outros custos", "Relatórios PDF"]


def _status_de(proposta):
    """Situação para a tela: em_aberto, aprovada, em_execucao, finalizada ou recusada (mesmas regras do quadro)."""
    from utils.proposta_status import normalize as _normalize_status
    s = _normalize_status(proposta.get('status', '')) or ''
    if s not in ('finalizada', 'recusada') and str(proposta.get('status_execucao') or '') == EXEC_EM_EXECUCAO:
        return 'em_execucao'
    return s


def _dm(d):
    return f"{d.day:02d}/{d.month:02d}" if d else ""


def _num_proposta(proposta, pid):
    n = proposta.get('numero', pid)
    try:
        return f"{int(float(n)):03d}"
    except (TypeError, ValueError):
        return str(n)


def _cliente_da_proposta(proposta):
    try:
        cid = int(float(proposta.get('cliente_id')))
        df = st.session_state.db.get_clientes()
        linha = df[df['id'] == cid]
        return linha.iloc[0].to_dict() if not linha.empty else {}
    except Exception:
        return {}


def _limpar_pdfs(pid):
    from utils.nova_proposta import limpar_pdfs
    limpar_pdfs(pid)


def _fechar_detalhe():
    st.session_state['kanban_selected_proposta'] = None


def _iniciar_execucao(proposta_id, proposta):
    """Aprovada → Em execução (o mesmo do botão "Iniciar execução" de antes)."""
    from utils.proposta_status import STATUS_EM_EXECUCAO
    try:
        res = st.session_state.db.update_proposta_status(
            proposta_id=proposta_id, novo_status=STATUS_EM_EXECUCAO,
            data_aprovacao=proposta.get('data_aprovacao') or hoje())
        if res.get('status', False):
            _limpar_pdfs(proposta_id)
            st.session_state['kanban_selected_proposta'] = None
            st.session_state.db.invalidar_cache()
            st.rerun()
        else:
            st.error(res.get('message', 'Erro ao iniciar.'))
    except Exception as e:
        st.error(str(e))


@st.dialog("Concluir o serviço?")
def _confirmar_finalizar(proposta_id):
    """Finalizar mexe no financeiro e abre a pós-organização: pede confirmação antes (um clique sem querer concluía)."""
    st.write("O serviço passa para **Concluída**. O saldo, os produtos, os fornecedores e a equipe entram no "
             "financeiro, e começam as mensagens da pós-organização.")
    c1, c2 = st.columns(2)
    if c1.button("Sim, concluir", key=f"fim_sim_{proposta_id}", type="primary", use_container_width=True):
        _finalizar(proposta_id)
    if c2.button("Cancelar", key=f"fim_nao_{proposta_id}", use_container_width=True):
        st.rerun()


def _finalizar(proposta_id):
    """Em execução → Concluída: finalizar_proposta_v2 grava o financeiro (produtos, extras, fornecedores,
    assistentes) e a pós-organização, como o antigo "FINALIZAR PROJETO"."""
    try:
        res = finalizar_proposta_v2(int(proposta_id))
    except Exception as e:
        st.error(str(e))
        return
    if res.get('status', False):
        _limpar_pdfs(proposta_id)
        st.session_state['kanban_selected_proposta'] = None
        st.session_state['proposta_finalizada_sucesso'] = True
        st.session_state.db.invalidar_cache()
        st.rerun()
    else:
        st.error(res.get('message', res.get('mensagem', 'Erro ao finalizar.')))


def _reabrir(proposta_id):
    try:
        from reabrir_proposta import reabrir_proposta_finalizada
        res = reabrir_proposta_finalizada(proposta_id)
    except Exception as e:
        st.error(str(e))
        return
    if res.get('status') in ['sucesso', 'sucesso_com_alerta']:
        _limpar_pdfs(proposta_id)
        st.session_state.db.invalidar_cache()
        st.session_state['kanban_selected_proposta'] = None
        if res.get('status') == 'sucesso_com_alerta' and res.get('alerta'):
            st.session_state['_prop_aviso'] = res.get('alerta')
        st.rerun()
    else:
        st.error(res.get('mensagem'))


def _marcar_cb(proposta_id, status, texto):
    from utils import propostas_dados
    propostas_dados.marcar(st.session_state.db, proposta_id, status, texto)
    st.session_state.db.invalidar_cache()


def _det_cabecalho(proposta_id, proposta, status, cliente):
    from utils.propostas_dados import servico_curto
    nome = proposta.get('nome') or proposta.get('cliente_nome') or 'Cliente'
    lugar = str(cliente.get('bairro') or cliente.get('cidade') or '').strip()
    partes = [str(proposta.get('tipo_proposta') or '').strip(), servico_curto(proposta, 44)]
    partes = [x for i, x in enumerate(partes) if x and x not in partes[:i]] + ([lugar] if lugar else [])
    st.markdown(
        f'<div class="pd-top"><div><div class="pd-ey">Proposta nº {esc(_num_proposta(proposta, proposta_id))}</div>'
        f'<h1 class="pd-tit">{esc(nome)}</h1><div class="pd-sub">{esc(" · ".join(partes))}</div></div>'
        f'<div>{pilula(status)}</div></div>', unsafe_allow_html=True)


def _det_proximo(proposta_id, proposta, status, marcas):
    """Painel azul-marinho com o próximo passo e o botão dele."""
    from utils import propostas_dados as dados
    from utils.propostas_dados import _data
    if status == 'em_aberto':
        sit, quando_ = dados.envio(proposta, marcas)
        tit = "Esperar a resposta da cliente" if sit == "enviada" else "Enviar a proposta para a cliente"
        sub = (f"Enviada {dados.quando(quando_)}" if sit == "enviada" and quando_ else
               "Ainda não enviada: use Enviar pelo WhatsApp")
        rot, icone_, tipo_b = "Aprovar proposta", ":material/check:", "gold"
    elif status == 'aprovada':
        ini = _data(proposta.get('data_inicio'))
        tit = "Agendar e iniciar o serviço"
        sub = f"Serviço marcado para {_dm(ini)}" if ini else "Ainda sem data: use Agendar na agenda"
        rot, icone_, tipo_b = "Iniciar execução", ":material/play_arrow:", "gold"
    elif status == 'em_execucao':
        dia = dados.dia_do_servico(proposta)
        tit = "Concluir o serviço"
        sub = (f"Dia {dia[0]} de {dia[1]}" if dia else "Em andamento") + " · ao finalizar, o financeiro e a pós-organização são lançados"
        rot, icone_, tipo_b = "Finalizar serviço", ":material/task_alt:", "gold"
    elif status == 'finalizada':
        fim = _data(proposta.get('data_fim'))
        tit = "Serviço concluído" + (f" em {_dm(fim)}" if fim else "")
        sub = "Ao reabrir, a proposta volta para Em execução"
        rot, icone_, tipo_b = "Reabrir", ":material/replay:", "lin"
    else:
        tit = "Proposta recusada"
        sub = "Ao reabrir, a proposta volta para Em aberto"
        rot, icone_, tipo_b = "Reabrir", ":material/replay:", "lin"
    with st.container(key="pd_prox"):
        c1, c2 = st.columns([1.5, 1], vertical_alignment="center")
        c1.markdown(f'<div class="pd-prox"><span class="l">Próximo passo</span><b>{esc(tit)}</b>'
                    f'<span class="l">{esc(sub)}</span></div>', unsafe_allow_html=True)
        with c2, st.container(key=f"{'cta' if tipo_b == 'gold' else 'pdlin'}_pd_acao"):
            clicou = st.button(rot, key=f"pd_acao_{proposta_id}", icon=icone_, use_container_width=True)
    # concluir pede confirmação aqui mesmo (o detalhe já é uma janela; não dá para abrir outra por cima)
    conf = f"_conf_fim_{proposta_id}"
    if clicou and status == 'em_execucao':
        st.session_state[conf] = True
    if st.session_state.get(conf) and status == 'em_execucao':
        st.warning("Concluir o serviço? O saldo, os produtos, os fornecedores e a equipe entram no financeiro, e "
                   "começam as mensagens da pós-organização.")
        s1, s2 = st.columns(2)
        if s1.button("Sim, concluir", key=f"pd_fim_sim_{proposta_id}", type="primary", use_container_width=True):
            st.session_state.pop(conf, None)
            _finalizar(proposta_id)
        if s2.button("Cancelar", key=f"pd_fim_nao_{proposta_id}", use_container_width=True):
            st.session_state.pop(conf, None)
            st.rerun(scope="fragment")
        return
    if not clicou:
        return
    if status == 'em_aberto':
        _aprovar(proposta_id, proposta)
    elif status == 'aprovada':
        _iniciar_execucao(proposta_id, proposta)
    else:
        _reabrir(proposta_id)


def _aprovar(proposta_id, proposta):
    """Aprovação (clique único, como antes): grava o sinal informado e lança o sinal como receita recebida."""
    from utils.proposta_status import STATUS_APROVADA
    valor = _safe_float(proposta.get('valor'))
    sinal = _safe_float(proposta.get('sinal'))
    chave = f"sinal_aprovar_{proposta_id}"
    if chave in st.session_state:   # campo na tela: vazio vale 0 (como no formulário antigo)
        sinal_atual = min(float(st.session_state.get(chave) or 0), valor)
    else:
        sinal_atual = sinal
    try:
        if abs(sinal_atual - sinal) > 0.004:
            st.session_state.db.update_proposta(proposta_id, sinal=sinal_atual)
        res = st.session_state.db.update_proposta_status(
            proposta_id=proposta_id, novo_status=STATUS_APROVADA, data_aprovacao=hoje())
        if res.get('status', False):
            _limpar_pdfs(proposta_id)
            st.session_state.db.sincronizar_sinal_proposta(proposta_id)
            st.session_state['kanban_selected_proposta'] = None
            st.session_state.db.invalidar_cache()
            st.rerun()
        else:
            st.error(res.get('message', 'Erro ao aprovar.'))
    except Exception as e:
        st.error(str(e))


def _det_aprovacao(proposta_id, proposta):
    """Em aberto: o sinal que a cliente paga ao aprovar e o atalho para recusar."""
    valor = _safe_float(proposta.get('valor'))
    sinal = _safe_float(proposta.get('sinal'))
    with st.container(border=True, key="pd_aprov"):
        c1, c2 = st.columns([1.3, 1], vertical_alignment="center")
        with c1:
            s = input_moeda("Sinal pago pela cliente ao aprovar (R$)", f"sinal_aprovar_{proposta_id}", value=sinal,
                            step=10.0, help="Entra no Financeiro como recebido e é descontado do total no relatório da cliente.")
        if s > valor:
            st.caption("O sinal não pode passar do valor da proposta.")
            s = valor
        c2.markdown(f'<div class="pd-saldo">Saldo no fim: <b>{_fmt_brl(max(valor - s, 0))}</b></div>',
                    unsafe_allow_html=True)
        with st.container(key="pd_links_rec"):
            if st.button("Recusar proposta", key=f"btn_recusar_{proposta_id}", type="tertiary", icon=":material/close:"):
                st.session_state[f"confirm_refuse_{proposta_id}"] = True
                st.rerun()


def _det_acoes(proposta_id, proposta, status, cliente, itens=None):
    """Enviar pelo WhatsApp · Baixar PDF · Agendar na agenda."""
    from utils.nova_proposta import link_whatsapp, mensagem_whatsapp
    from utils.propostas_dados import _data
    nome = proposta.get('nome') or proposta.get('cliente_nome') or ''
    valor = _safe_float(proposta.get('valor'))
    with st.container(key="pd_acoes"):
        c1, c2, c3 = st.columns(3)
        with c1, st.container(key=f"wa_pd_{proposta_id}"):
            if status == 'em_aberto':
                url = link_whatsapp(cliente.get('telefone'), mensagem_whatsapp(nome, proposta.get('tipo_proposta'), valor))
                st.link_button("Enviar pelo WhatsApp", url, use_container_width=True, key=f"pd_zap_{proposta_id}",
                               on_click=_marcar_cb, args=(proposta_id, "Enviada", "Enviada pelo WhatsApp"))
            else:
                primeiro = str(nome).split(' ')[0]
                url = link_whatsapp(cliente.get('telefone'), f"Oi, {primeiro}! Tudo bem?")
                st.link_button("Conversar no WhatsApp", url, use_container_width=True, key=f"pd_zap_{proposta_id}")
        with c2:
            def _gerar():
                from utils.propostas_helper import gerar_pdf_cliente_proposta
                try:
                    ok, msg, arq = gerar_pdf_cliente_proposta(st.session_state.db, proposta_id, tipo_documento="proposta")
                except Exception as e:
                    return None, None, str(e)
                return (arq, os.path.basename(arq), None) if ok and arq else (None, None, msg)
            # a chave muda com a situação, os valores e os itens: o PDF guardado nunca fica desatualizado
            import hashlib
            assin = repr((status, _safe_float(proposta.get('valor')), _safe_float(proposta.get('sinal')),
                          str(proposta.get('descricao') or ''), str(proposta.get('data_inicio') or ''),
                          [round(_total_itens(k, v), 2) for k, v in (itens or {}).items()]))
            versao = hashlib.md5(assin.encode()).hexdigest()[:8]
            baixar_pdf("Baixar PDF", f"proposta_det_{proposta_id}_{versao}", _gerar)
        with c3:
            ini = _data(proposta.get('data_inicio'))
            if status in ('finalizada', 'recusada'):
                # a data de fim de uma concluída é a data da conclusão: aqui só abre a Agenda
                if st.button(f"Ver na Agenda{': ' + _dm(ini) if ini else ''}", key=f"pd_ag_ir2_{proposta_id}",
                             use_container_width=True):
                    st.session_state['ag_dia'] = ini or hoje()
                    st.session_state['kanban_selected_proposta'] = None
                    st.session_state.current_page = "Agenda"
                    st.rerun()
                return
            with st.popover("Agendar na agenda" if not ini else f"Na agenda: {_dm(ini)}", use_container_width=True):
                st.caption("O serviço aparece na Agenda nos dias de trabalho depois que a cliente aprova.")
                d = st.date_input("Primeiro dia do serviço", value=ini or hoje(), format="DD/MM/YYYY",
                                  key=f"pd_ag_data_{proposta_id}")
                try:
                    dias = max(int(float(proposta.get('previsao_dias') or 1)), 1)
                except (TypeError, ValueError):
                    dias = 1
                dias = st.number_input("Dias de serviço", 1, 60, dias, 1, key=f"pd_ag_dias_{proposta_id}")
                if st.button("Salvar na agenda", key=f"pd_ag_ok_{proposta_id}", type="primary", use_container_width=True):
                    try:
                        st.session_state.db.update_proposta(proposta_id, data_inicio=d, previsao_dias=int(dias),
                                                            data_fim=d + timedelta(days=int(dias) - 1))
                        st.session_state.db.invalidar_cache()
                        _limpar_pdfs(proposta_id)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                if st.button("Abrir a Agenda", key=f"pd_ag_ir_{proposta_id}", type="tertiary"):
                    st.session_state['ag_dia'] = ini or hoje()
                    st.session_state['kanban_selected_proposta'] = None
                    st.session_state.current_page = "Agenda"
                    st.rerun()


def _det_valores(proposta, status):
    valor = _safe_float(proposta.get('valor'))
    sinal = _safe_float(proposta.get('sinal'))
    recebido = status in ('aprovada', 'em_execucao', 'finalizada')
    if sinal > 0:
        rot_s = "sinal recebido" if recebido else "sinal na aprovação"
        cls = ' class="verde"' if recebido else ""
    else:
        rot_s, cls = "sem sinal", ""
    st.markdown(
        f'<div class="pd-res"><div><b>{_fmt_brl(valor).replace(",00", "")}</b><span>valor do serviço</span></div>'
        f'<div><b{cls}>{_fmt_brl(sinal).replace(",00", "")}</b><span>{rot_s}</span></div>'
        f'<div><b>{_fmt_brl(max(valor - sinal, 0)).replace(",00", "")}</b><span>a receber no fim</span></div></div>',
        unsafe_allow_html=True)


def _itens_da_proposta(proposta_id):
    db = st.session_state.db
    try:
        produtos = db.get_produtos_organizadores(proposta_id)
    except Exception:
        produtos = pd.DataFrame()
    saida = {"Produtos": produtos}
    for rot, tipo in (("Fornecedores", "FORNECEDOR"), ("Assistentes", "ASSISTENTE"), ("Outros custos", "OUTROS")):
        try:
            saida[rot] = db.get_acrescimos_proposta_por_tipo(proposta_id, tipo)
        except Exception:
            saida[rot] = pd.DataFrame()
    return saida


def _total_itens(rot, df):
    if df is None or df.empty:
        return 0.0
    if rot == "Produtos":
        return float((df['valor'].astype(float) * df['quantidade'].astype(float)).sum())
    return float(df['valor'].astype(float).sum())


def _aba_servico(proposta_id, proposta, status, marcas, itens):
    from utils.propostas_dados import observacoes_visita, servico_curto
    valor = _safe_float(proposta.get('valor'))
    tipo = str(proposta.get('tipo_proposta') or 'Serviço').strip()
    desc = str(proposta.get('descricao') or '').strip()
    curto = servico_curto(proposta, 60)
    titulo = tipo if curto == tipo else f"{tipo}: {curto}"
    try:
        prev = int(float(proposta.get('previsao_dias') or 0))
    except (TypeError, ValueError):
        prev = 0
    det = desc or "Sem descrição cadastrada."
    html = (f'<div class="pd-it"><div><b>{esc(titulo)}</b><span class="desc">{esc(det)}</span>'
            + (f'<span>{prev} dia{"s" if prev != 1 else ""} de serviço</span>' if prev else "")
            + f'</div><b>{_fmt_brl(valor).replace(",00", "")}</b></div>')
    total = valor
    for rot, df in itens.items():
        t = _total_itens(rot, df)
        if t > 0:
            total += t
            n = len(df)
            html += (f'<div class="pd-it"><div><b>{rot}</b><span>{n} {"item" if n == 1 else "itens"}</span></div>'
                     f'<b>{_fmt_brl(t).replace(",00", "")}</b></div>')
    if total > valor:
        html += f'<div class="pd-it tot"><div><b>Total geral</b></div><b>{_fmt_brl(total)}</b></div>'
    obs = observacoes_visita(marcas)
    if obs and obs not in desc:
        html += (f'<div class="pd-it"><div><b>Observações da visita</b><span class="desc">{esc(obs)}</span>'
                 f'<span>Só para você: não aparecem no PDF desta proposta.</span></div></div>')
    st.markdown(html, unsafe_allow_html=True)


def _aba_itens(proposta_id, rot, status, itens):
    """Produtos, fornecedores, assistentes e outros custos. Incluir e editar fica liberado durante a execução,
    como antes (é o que vai para o Financeiro ao finalizar); nas outras situações a lista é só para consulta."""
    if status == 'em_execucao':
        {"Produtos": _tab_produtos, "Fornecedores": _tab_fornecedores, "Assistentes": _tab_assistentes,
         "Outros custos": _tab_outros}[rot](proposta_id)
        return
    df = itens.get(rot)
    if df is None or df.empty:
        st.markdown(f'<div class="pd-vazio">Nenhum item em {rot.lower()}.</div>', unsafe_allow_html=True)
    elif rot == "Produtos":
        html = ""
        for _, p in df.iterrows():
            q = int(_safe_float(p.get('quantidade'), 1))
            v = _safe_float(p.get('valor'))
            html += (f'<div class="pd-it"><div><b>{esc(p.get("nome"))}</b><span>{q} × {_fmt_brl(v)} · '
                     f'{esc(p.get("comodo") or "Geral")}</span></div><b>{_fmt_brl(q * v)}</b></div>')
        st.markdown(html, unsafe_allow_html=True)
    else:
        html = ""
        for _, a in df.iterrows():
            nome = a.get('fornecedor') if rot != "Outros custos" else str(a.get('descricao') or '').split(' - ')[0]
            sub = a.get('descricao') if rot != "Outros custos" else (a.get('fornecedor') or '')
            html += (f'<div class="pd-it"><div><b>{esc(nome or "—")}</b><span>{esc(sub or "")}</span></div>'
                     f'<b>{_fmt_brl(_safe_float(a.get("valor")))}</b></div>')
        st.markdown(html, unsafe_allow_html=True)
    if status in ('em_aberto', 'aprovada'):
        st.caption("Para incluir itens, inicie a execução: eles vão para o Financeiro ao finalizar.")
    elif status in ('finalizada', 'recusada'):
        st.caption("Para mudar os itens, reabra a proposta.")


def _aba_relatorios(proposta_id, proposta, status):
    nome_cliente = proposta.get('nome', proposta.get('cliente_nome', 'Cliente'))
    numero = proposta.get('numero', proposta_id)
    rc1, rc2 = st.columns(2)
    with rc1:
        if status in ('em_aberto', 'aprovada'):
            def _prop():
                from utils.propostas_helper import gerar_pdf_cliente_proposta
                try:
                    ok, msg, arq = gerar_pdf_cliente_proposta(st.session_state.db, proposta_id, tipo_documento="proposta")
                except Exception as e:
                    return None, None, str(e)
                return (arq, os.path.basename(arq), None) if ok and arq else (None, None, msg)
            baixar_pdf("Baixar proposta da cliente", f"rel_prop_{proposta_id}", _prop,
                       legenda="Proposta de serviço para enviar")
        else:
            _report_card_download("", "relatório do cliente", "Fechamento do serviço para a cliente", proposta_id,
                                  "cliente", nome_cliente, numero)
    with rc2:
        _report_card_download("", "relatório interno", "Margens e custos, só para você", proposta_id, "interno",
                              nome_cliente, numero)
    rc3, rc4 = st.columns(2)
    with rc3:
        _report_card_download("", "relatório de fornecedores", "Lista de terceiros", proposta_id, "fornecedores",
                              nome_cliente, numero)
    with rc4:
        _report_card_download("", "relatório de produtos", "Produtos vendidos na organização", proposta_id, "vendas",
                              nome_cliente, numero)


def _det_historico(proposta, status, marcas):
    from utils.propostas_dados import _data
    eventos = []
    criada = _data(proposta.get('data_proposta'))
    rascunho = any(m['status'] == 'Rascunho' for m in marcas)
    if criada:
        eventos.append((criada, 0, "#C9A84C", "Proposta criada" + (" como rascunho" if rascunho else "")))
    for m in marcas:
        if m['status'] == 'Enviada':
            eventos.append((m['data'], 1, "#C9A84C", m['observacao'] or "Enviada"))
        elif m['status'] == 'Lembrete':
            eventos.append((m['data'], 1, "#C9A84C", "Lembrete pelo WhatsApp"))
        elif m['status'] not in ('Rascunho', 'Visita') and (m['observacao'] or m['status']):
            eventos.append((m['data'], 1, "#98A2B3", m['observacao'] or m['status']))
    aprov = _data(proposta.get('data_aprovacao'))
    sinal = _safe_float(proposta.get('sinal'))
    if aprov and status in ('aprovada', 'em_execucao', 'finalizada'):
        eventos.append((aprov, 2, "#2F6B4F", "Aprovada" + (f" · sinal de {_fmt_brl(sinal).replace(',00', '')} "
                                                           "lançado no financeiro" if sinal > 0 else "")))
    ini = _data(proposta.get('data_inicio_execucao'))
    if ini and status in ('em_execucao', 'finalizada'):
        eventos.append((ini, 3, "#0D1B2A", "Execução iniciada"))
    fim = _data(proposta.get('data_fim'))
    if status == 'finalizada' and fim:
        eventos.append((fim, 4, "#2F6B4F", "Concluída"))
    if status == 'recusada':
        eventos.append((fim or criada, 4, "#98A2B3", "Recusada"))
    eventos = [e for e in eventos if e[0]]
    if not eventos:
        return
    eventos.sort(key=lambda e: (e[0], e[1]))
    html = '<div class="pd-secao">Histórico</div>' + "".join(
        f'<div class="pd-tl"><i style="background:{cor}"></i><span>{esc(txt)} · {_dm(d)}</span></div>'
        for d, _, cor, txt in eventos)
    st.markdown(html, unsafe_allow_html=True)


def _det_mais_acoes(proposta_id, proposta, status):
    """Mais ações: editar, duplicar e excluir (reabrir fica no Próximo passo)."""
    with st.expander("Mais ações: editar, duplicar, excluir", icon=":material/more_vert:"):
        with st.form(key=f"form_editar_open_{proposta_id}"):
            st.markdown(f'<div style="font-weight:600;color:{NAVY};font-size:13px;margin-bottom:2px;">Editar proposta</div>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                ed_valor = input_moeda("Valor da proposta (R$):", f"ed_valor_{proposta_id}",
                                       value=_safe_float(proposta.get('valor')), step=10.0)
            ed_sinal = None
            if status != 'em_aberto':
                with c2:
                    ed_sinal = input_moeda("Sinal / entrada já pago (R$):", f"ed_sinal_{proposta_id}",
                                           value=_safe_float(proposta.get('sinal')), step=10.0,
                                           help="Valor que a cliente pagou ao confirmar. É descontado do total no relatório da cliente.")
            _tipos = ["Organização", "Pré-mudança", "Pós-mudança", "Consultoria", "Acompanhamento", "Projeto", "Outro"]
            _tipo_atual = str(proposta.get('tipo_proposta') or "").strip()
            if _tipo_atual and _tipo_atual not in _tipos:
                _tipos = [_tipo_atual] + _tipos
            c3, c4 = st.columns(2)
            ed_tipo = c3.selectbox("Categoria:", _tipos, index=_tipos.index(_tipo_atual) if _tipo_atual in _tipos else 0,
                                   key=f"ed_tipo_{proposta_id}")
            from utils.propostas_dados import _data
            ed_data = c4.date_input("Início previsto:", value=_data(proposta.get('data_inicio')), format="DD/MM/YYYY",
                                    key=f"ed_data_{proposta_id}")
            ed_desc = st.text_area("Descrição:", value=str(proposta.get('descricao') or ''), height=110,
                                   key=f"ed_desc_{proposta_id}")
            if st.form_submit_button("Salvar alterações", type="primary", use_container_width=True):
                try:
                    campos = dict(valor=ed_valor, tipo_proposta=ed_tipo, descricao=ed_desc, data_inicio=ed_data)
                    if ed_sinal is not None:
                        campos['sinal'] = ed_sinal
                    res = st.session_state.db.update_proposta(proposta_id, **campos)
                    ok = res.get('status', False) if isinstance(res, dict) else bool(res)
                    if ok and not (isinstance(res, dict) and res.get('status') == 'error'):
                        if status in ('aprovada', 'em_execucao'):
                            # valor/sinal mudaram: ajusta o sinal recebido e o saldo a receber no Financeiro
                            st.session_state.db.sincronizar_sinal_proposta(proposta_id)
                        st.session_state.db.invalidar_cache()
                        _limpar_pdfs(proposta_id)
                        st.rerun()
                    else:
                        st.error(res.get('message', 'Erro ao atualizar.') if isinstance(res, dict) else 'Erro ao atualizar.')
                except Exception as e:
                    st.error(str(e))

        c1, c2 = st.columns(2)
        with c1:
            if botao_editar("Duplicar proposta", key=f"btn_dup_{proposta_id}", icon=":material/content_copy:",
                            use_container_width=True):
                try:
                    from utils.proposta_status import STATUS_EM_ABERTO
                    novo = st.session_state.db.add_proposta(
                        cliente_id=proposta.get('cliente_id'), descricao=str(proposta.get('descricao') or ''),
                        valor=_safe_float(proposta.get('valor')), status=STATUS_EM_ABERTO,
                        tipo_proposta=str(proposta.get('tipo_proposta') or '') or None,
                        previsao_dias=proposta.get('previsao_dias') if pd.notna(proposta.get('previsao_dias')) else None,
                        gerar_transacoes_automaticas=False)
                    if novo:
                        st.session_state.db.update_proposta(novo, data_proposta=hoje())
                        # cópia nasce como rascunho (antes aparecia "enviada hoje" sem ter sido enviada)
                        from utils import propostas_dados as _pd
                        _pd.marcar(st.session_state.db, int(novo), "Rascunho", f"Cópia da proposta nº {_num_proposta(proposta, proposta_id)}")
                        st.session_state.db.invalidar_cache()
                        st.session_state['kanban_selected_proposta'] = int(novo)
                        st.rerun()
                    else:
                        st.error("Não foi possível duplicar a proposta.")
                except Exception as e:
                    st.error(str(e))
        with c2:
            if botao_excluir("Excluir proposta", f"btn_excluir_open_{proposta_id}"):
                st.session_state[f"confirm_delete_{proposta_id}"] = True
                st.rerun()


def _det_confirmacoes(proposta_id):
    # ── Confirmação: Recusar ─────────────────────────────────────────────
    if st.session_state.get(f"confirm_refuse_{proposta_id}", False):
        st.markdown(
            f'<div class="pd-conf"><b>Recusar proposta?</b><span>Ela vai para o histórico, em cinza. Dá para reabrir '
            f'depois.</span></div>', unsafe_allow_html=True)
        cr1, cr2 = st.columns([1, 1])
        with cr1:
            if st.button("Cancelar", key=f"btn_cancel_ref_{proposta_id}", use_container_width=True):
                st.session_state[f"confirm_refuse_{proposta_id}"] = False
                st.rerun()
        with cr2:
            if botao_excluir("Recusar proposta", f"btn_confirm_ref_{proposta_id}"):
                try:
                    from sqlalchemy import text as sa_text
                    from utils.database import engine
                    with engine.connect() as conn:
                        conn.execute(sa_text(
                            "UPDATE propostas SET status = 'recusada', status_execucao = 'Cancelada', "
                            "data_fim = COALESCE(data_fim, :hoje) WHERE id = :pid AND usuario_id = :uid"
                        ), {"pid": proposta_id, "hoje": hoje(), "uid": st.session_state.get('usuario_id')})
                        conn.commit()
                    st.session_state[f"confirm_refuse_{proposta_id}"] = False
                    _limpar_pdfs(proposta_id)
                    st.session_state['kanban_selected_proposta'] = None
                    st.session_state.db.invalidar_cache()
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # ── Confirmação: Excluir ─────────────────────────────────────────────
    if st.session_state.get(f"confirm_delete_{proposta_id}", False):
        st.markdown(
            '<div class="pd-conf del"><b>Excluir proposta?</b><span>Esta ação não poderá ser desfeita e removerá todos '
            'os dados relacionados.</span></div>', unsafe_allow_html=True)
        dc1, dc2 = st.columns([1, 1])
        with dc1:
            if st.button("Cancelar", key=f"btn_cancel_del_{proposta_id}", use_container_width=True):
                st.session_state[f"confirm_delete_{proposta_id}"] = False
                st.rerun()
        with dc2:
            if botao_excluir("Excluir proposta", f"btn_confirm_del_{proposta_id}"):
                try:
                    usuario_id = st.session_state.get('usuario_id')
                    sucesso, mensagem = st.session_state.db.excluir_proposta_segura(proposta_id, usuario_id)
                    if sucesso:
                        st.session_state.db.invalidar_cache()
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state[f"confirm_delete_{proposta_id}"] = False
                        st.rerun()
                    else:
                        st.error(mensagem)
                except Exception as e:
                    st.error(str(e))


def _render_detail_panel(proposta_id, proposta, propostas_com_clientes=None):
    """Detalhe completo de uma proposta (dentro da gaveta à direita)."""
    from utils import propostas_dados
    status = _status_de(proposta)
    marcas = propostas_dados.historicos(st.session_state.db, [proposta_id]).get(int(proposta_id), [])
    cliente = _cliente_da_proposta(proposta)
    st.markdown(CSS_DETALHE, unsafe_allow_html=True)
    _det_cabecalho(proposta_id, proposta, status, cliente)
    _det_proximo(proposta_id, proposta, status, marcas)
    if status == 'em_aberto':
        _det_aprovacao(proposta_id, proposta)
    _det_confirmacoes(proposta_id)
    itens = _itens_da_proposta(proposta_id)
    _det_acoes(proposta_id, proposta, status, cliente, itens)
    _det_valores(proposta, status)
    with st.container(key="pd_abas"):
        aba = st.pills("Seção", ABAS_DETALHE, default="Serviço", required=True, key=f"pd_aba_{proposta_id}",
                       label_visibility="collapsed") or "Serviço"
    if aba == "Serviço":
        _aba_servico(proposta_id, proposta, status, marcas, itens)
    elif aba == "Relatórios PDF":
        _aba_relatorios(proposta_id, proposta, status)
    else:
        _aba_itens(proposta_id, aba, status, itens)
    _det_historico(proposta, status, marcas)
    _det_mais_acoes(proposta_id, proposta, status)


CSS_DETALHE = """
<style>
[data-testid="stDialog"]:has(.pd-top) > div { width:min(760px, 100vw) !important; max-width:100vw !important;
   margin-left:auto !important; background:#F7F5F0 !important; }
[role="dialog"]:has(.pd-top) { background:#F7F5F0 !important; width:100% !important; max-width:100% !important; }
[role="dialog"]:has(.pd-top) h2 { font-size:.78rem !important; letter-spacing:.14em; text-transform:uppercase;
   color:#9C7A22 !important; font-weight:700 !important; }
[role="dialog"]:has(.pd-top) h2 * { font-size:.78rem !important; color:#9C7A22 !important; font-weight:700 !important; }
.pd-top { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.pd-ey { display:none; }
h1.pd-tit { margin:0 !important; padding:0 !important; font-family:'Cormorant Garamond',Georgia,serif !important;
            font-size:2.2rem !important; font-weight:600 !important; color:var(--navy) !important; line-height:1.15 !important;
            overflow-wrap:anywhere; }
h1.pd-tit::after { content:""; display:block; width:40px; height:3px; border-radius:2px; background:var(--gold); margin-top:6px; }
.pd-sub { color:#5B6B80; font-size:.95rem; margin-top:8px; }
.st-key-pd_prox { background:var(--navy); border-radius:16px; padding:18px 20px; margin-top:6px; }
.pd-prox { display:flex; flex-direction:column; gap:3px; color:#fff; padding-bottom:6px; }
.pd-prox .l { font-size:.8rem; color:rgba(255,255,255,.72); }
.pd-prox b { font-size:1.08rem; color:#fff; }
.st-key-pd_prox [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:wrap !important; row-gap:12px; }
.st-key-pd_prox [data-testid="stColumn"] { min-width:200px !important; flex:1 1 200px !important; }
.st-key-cta_pd_acao .stButton > button, .st-key-pdlin_pd_acao .stButton > button { min-height:46px; font-weight:700; }
.st-key-pdlin_pd_acao .stButton > button { background:transparent !important; border:1px solid rgba(255,255,255,.45) !important; }
.st-key-pdlin_pd_acao .stButton > button * { color:#fff !important; }
.st-key-pd_aprov { background:#fff; border-color:#E7E2D6 !important; border-radius:14px !important; }
.pd-saldo { font-size:.86rem; color:#5B6B80; padding-top:24px; }
.st-key-pd_aprov [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:wrap !important; row-gap:0 !important; }
.st-key-pd_aprov [data-testid="stColumn"] { min-width:200px !important; flex:1 1 200px !important; }
.pd-saldo b { color:var(--navy); }
.st-key-pd_links_rec button, .st-key-pd_links_rec button p { color:#9B2C2C !important; font-weight:600 !important; }
.st-key-pd_acoes [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:wrap !important; gap:10px !important; }
.st-key-pd_acoes [data-testid="stColumn"] { min-width:150px !important; flex:1 1 150px !important; }
.st-key-pd_acoes a, .st-key-pd_acoes button { min-height:44px; background:#fff !important; border:1px solid #E7E2D6 !important;
       border-radius:10px !important; }
.st-key-pd_acoes [class*="st-key-btndoc_"] .stButton > button, .st-key-pd_acoes [data-testid="stDownloadButton"] button { background:#fff !important; border:1px solid #E7E2D6 !important; }
.st-key-pd_acoes a p, .st-key-pd_acoes button p, .st-key-pd_acoes button span { color:var(--navy) !important; font-weight:600 !important; }
.pd-res { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:4px 0 6px; }
.pd-res div { background:#fff; border:1px solid #E7E2D6; border-radius:12px; padding:12px; min-width:0; }
.pd-res b { display:block; font-size:1.2rem; color:var(--navy); font-variant-numeric:tabular-nums; white-space:nowrap;
            overflow:hidden; text-overflow:ellipsis; }
.pd-res b.verde { color:#2F6B4F; }
.pd-res span { font-size:.75rem; color:#5B6B80; }
.st-key-pd_abas [data-testid="stButtonGroup"] { gap:6px; flex-wrap:wrap; }
.st-key-pd_abas button { border-radius:999px !important; background:#ECE7DC !important; border:0 !important; min-height:36px; }
.st-key-pd_abas button p { color:#5B6B80 !important; font-weight:600 !important; }
.st-key-pd_abas button[aria-checked="true"], .st-key-pd_abas button[kind*="Active"] { background:#fff !important;
       box-shadow:inset 0 -2px 0 #C9A84C, 0 1px 2px rgba(0,0,0,.06); }
.st-key-pd_abas button[aria-checked="true"] p, .st-key-pd_abas button[kind*="Active"] p { color:var(--navy) !important; }
.pd-it { background:#fff; border:1px solid #E7E2D6; border-radius:12px; padding:14px 16px; margin-top:10px; display:flex;
         justify-content:space-between; gap:12px; }
.pd-it > div { min-width:0; }
.pd-it b { color:var(--navy); }
.pd-it > b { white-space:nowrap; font-variant-numeric:tabular-nums; }
.pd-it span { display:block; font-size:.82rem; color:#5B6B80; margin-top:2px; }
.pd-it span.desc { white-space:pre-wrap; overflow-wrap:anywhere; }
.pd-it.tot { background:#F6EDD3; border-color:#E8D5A3; }
.pd-vazio { background:#fff; border:1px dashed #E7E2D6; border-radius:12px; padding:16px; color:#5B6B80; font-size:.88rem; margin-top:10px; }
.pd-secao { font-size:.74rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#5B6B80; margin:22px 0 6px; }
.pd-tl { display:flex; gap:12px; font-size:.9rem; padding:6px 0; color:#1A202C; }
.pd-tl i { flex:none; width:10px; height:10px; border-radius:50%; margin-top:6px; }
.pd-conf { background:#FAF9F7; border:1px solid #E7E2D6; border-radius:12px; padding:14px 16px; margin:10px 0 8px; }
.pd-conf b { display:block; color:var(--navy); }
.pd-conf span { font-size:.84rem; color:#5B6B80; }
.pd-conf.del { background:#FBE9E7; border-color:#9B2C2C33; }
.pd-conf.del b { color:#9B2C2C; }
.itens-empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:28px 20px;
    background:#faf9f7; border-radius:12px; border:1px dashed #ddd; margin:8px 0 16px 0; text-align:center; }
.itens-empty-title { font-size:15px; font-weight:600; color:#4a4a4a; margin-bottom:6px; }
.itens-empty-hint { font-size:12px; color:#9a9890; }
@media (max-width: 640px) {
  .pd-res { grid-template-columns:1fr 1fr; }
  h1.pd-tit { font-size:1.8rem !important; }
}
</style>
"""


def _pdf_inline_viewer(pdf_bytes, key, height=720):
    """Render a PDF privately, in-session, using pdf.js (canvas rendering).

    The bytes are embedded (base64) directly inside the component and rendered
    to <canvas> by pdf.js in the authenticated owner's own browser. Nothing is
    written to the public `static/` dir, so there is no guessable/public URL to
    the document — only the logged-in owner who triggered the view ever
    receives the bytes. pdf.js itself (a public, non-sensitive library) is
    served from our own static dir with a CDN fallback. "Abrir em nova aba"
    opens a new window that renders the same in-memory bytes with pdf.js.

    Canvas rendering is used (instead of the browser's native PDF plugin via
    data:/blob: URIs) because Chrome blocks those inside the sandboxed,
    null-origin component iframe."""
    b64 = base64.b64encode(pdf_bytes).decode()
    safe_key = str(key).replace("-", "_")
    template = r"""
<div style="font-family:sans-serif;">
  <div style="padding:6px 0;text-align:center;">
    <button id="newtab___KEY__" style="background:#0D1B2A;color:#C9A84C;border:none;border-radius:6px;padding:8px 14px;font-weight:700;cursor:pointer;">Abrir em nova aba</button>
  </div>
  <div id="status___KEY__" style="color:#888;font-size:12px;text-align:center;padding:4px;">Carregando visualização…</div>
  <div id="cont___KEY__" style="width:100%;height:__HEIGHT__px;overflow:auto;background:#525659;padding:8px;box-sizing:border-box;border-radius:8px;"></div>
</div>
<script>
(function(){
  var B64 = "__B64__";
  var CDN_LIB = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
  var CDN_WORKER = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

  function b64ToBytes(b){var s=atob(b),l=s.length,a=new Uint8Array(l);for(var i=0;i<l;i++)a[i]=s.charCodeAt(i);return a;}

  function loadScript(src, ok, fail){
    var s=document.createElement("script"); s.src=src; s.onload=ok; s.onerror=fail; document.head.appendChild(s);
  }

  function withLib(cb){
    if (window.pdfjsLib){ cb(window.pdfjsLib, CDN_WORKER); return; }
    loadScript(CDN_LIB, function(){ cb(window.pdfjsLib, CDN_WORKER); }, function(){ cb(null); });
  }

  withLib(function(lib, workerSrc){
    var status=document.getElementById("status___KEY__");
    var cont=document.getElementById("cont___KEY__");
    if(!lib){ status.textContent="Não foi possível carregar o visualizador. Use o botão de download."; return; }
    lib.GlobalWorkerOptions.workerSrc=workerSrc;
    lib.getDocument({data:b64ToBytes(B64)}).promise.then(function(pdf){
      status.style.display="none";
      var p=Promise.resolve();
      for(var n=1;n<=pdf.numPages;n++){(function(num){
        p=p.then(function(){return pdf.getPage(num).then(function(page){
          var v=page.getViewport({scale:1});
          var sc=(cont.clientWidth-24)/v.width; if(sc>2)sc=2; if(sc<=0)sc=1;
          var vp=page.getViewport({scale:sc});
          var cv=document.createElement("canvas"); cv.width=vp.width; cv.height=vp.height;
          cv.style.display="block"; cv.style.margin="0 auto 8px"; cv.style.boxShadow="0 1px 4px rgba(0,0,0,0.4)";
          cont.appendChild(cv);
          return page.render({canvasContext:cv.getContext("2d"),viewport:vp}).promise;
        });});
      })(n);}
      return p;
    }).catch(function(err){ status.style.display="block"; status.textContent="Erro ao renderizar PDF: "+err; });
  });

  document.getElementById("newtab___KEY__").addEventListener("click", function(){
    var w=window.open("","_blank");
    if(!w){ alert("Permita pop-ups para abrir em nova aba."); return; }
    var libUrl = CDN_LIB;
    var wkUrl = CDN_WORKER;
    var doc='<!DOCTYPE html><html><head><meta charset="utf-8"><title>PDF</title>'
      +'<style>body{margin:0;background:#525659;}canvas{display:block;margin:0 auto 8px;box-shadow:0 1px 4px rgba(0,0,0,0.4);}#c{padding:10px;}</style></head>'
      +'<body><div id="c"></div>'
      +'<div id="err" style="display:none;color:#fff;padding:16px;font-family:sans-serif;">Não foi possível carregar o visualizador. Volte e use o botão de download.</div>'
      +'<scr'+'ipt src="'+libUrl+'" onerror="document.getElementById(\'err\').style.display=\'block\';"></scr'+'ipt><scr'+'ipt>'
      +'var B="'+B64+'";function b2b(b){var s=atob(b),l=s.length,a=new Uint8Array(l);for(var i=0;i<l;i++)a[i]=s.charCodeAt(i);return a;}'
      +'if(typeof pdfjsLib==="undefined"){document.getElementById("err").style.display="block";}else{'
      +'pdfjsLib.GlobalWorkerOptions.workerSrc="'+wkUrl+'";'
      +'pdfjsLib.getDocument({data:b2b(B)}).promise.then(function(pdf){var c=document.getElementById("c");var p=Promise.resolve();for(var n=1;n<=pdf.numPages;n++){(function(num){p=p.then(function(){return pdf.getPage(num).then(function(pg){var v=pg.getViewport({scale:1});var sc=(c.clientWidth-20)/v.width;if(sc>2)sc=2;if(sc<=0)sc=1;var vp=pg.getViewport({scale:sc});var cv=document.createElement("canvas");cv.width=vp.width;cv.height=vp.height;c.appendChild(cv);return pg.render({canvasContext:cv.getContext("2d"),viewport:vp}).promise;});});})(n);}return p;}).catch(function(e){document.getElementById("err").style.display="block";});}'
      +'</scr'+'ipt></body></html>';
    w.document.open(); w.document.write(doc); w.document.close();
  });
})();
</script>
"""
    html = (template.replace("__KEY__", safe_key)
                    .replace("__HEIGHT__", str(height))
                    .replace("__B64__", b64))
    components.html(html, height=height + 80)


def _gerar_report_pdf(proposta_id, report_type, nome_cliente="Cliente", numero_proposta=None):
    """Gera um PDF de relatório e devolve (caminho, nome_arquivo, erro).

    Isolado para ser chamado SOB DEMANDA (no clique), nunca no render — assim
    abrir o detalhe de uma proposta finalizada não dispara 4 gerações de PDF."""
    try:
        if report_type == "cliente":
            from utils.propostas_helper import gerar_pdf_cliente_proposta
            sucesso, mensagem, filename = gerar_pdf_cliente_proposta(st.session_state.db, proposta_id)
            return (filename, os.path.basename(filename), None) if (sucesso and filename) else (None, None, mensagem)
        elif report_type == "interno":
            from utils.propostas_helper import gerar_pdf_interno_proposta
            sucesso, mensagem, filename = gerar_pdf_interno_proposta(st.session_state.db, proposta_id)
            return (filename, os.path.basename(filename), None) if (sucesso and filename) else (None, None, mensagem)
        elif report_type == "fornecedores":
            from utils.propostas_helper import gerar_pdf_fornecedores_proposta
            sucesso, mensagem, filename = gerar_pdf_fornecedores_proposta(st.session_state.db, proposta_id)
            return (filename, os.path.basename(filename), None) if (sucesso and filename) else (None, None, mensagem)
        elif report_type == "vendas":
            from utils.pdf_generator_v2 import gerar_pdf_venda_v2
            produtos = st.session_state.db.get_produtos_organizadores(proposta_id)
            if produtos is None or (hasattr(produtos, 'empty') and produtos.empty):
                return (None, None, "Nenhum produto cadastrado.")
            val_col = 'valor_unit' if 'valor_unit' in produtos.columns else 'valor'
            valor_total = float(produtos[val_col].astype(float).mul(produtos['quantidade'].astype(float)).sum())
            num_exibir = numero_proposta or proposta_id
            venda_dados = {'id': num_exibir, 'status': 'Proposta', 'forma_pagamento': 'N/A',
                           'valor_total': round(valor_total, 2),
                           'data_venda': datetime.now().strftime('%d/%m/%Y'),
                           'observacoes': f"Produtos Proposta #{num_exibir} - {nome_cliente}"}
            rename_map = {'nome': 'produto_nome', val_col: 'preco_unitario'}
            itens_pdf = produtos.rename(columns=rename_map)[['produto_nome', 'quantidade', 'preco_unitario']].copy()
            cliente_nome_arq = nome_cliente.replace(' ', '_').lower()
            fname = f"pdfs/Relatorio_Produtos_{cliente_nome_arq}_{num_exibir}.pdf"
            os.makedirs("pdfs", exist_ok=True)
            pdf_path = gerar_pdf_venda_v2(venda_dados, {'nome': nome_cliente}, itens_pdf, fname)
            if pdf_path and os.path.exists(pdf_path):
                return (pdf_path, f"Relatorio_Produtos_{cliente_nome_arq}_{num_exibir}.pdf", None)
            return (None, None, "Erro ao gerar PDF de vendas.")
    except Exception as e:
        return (None, None, str(e))
    return (None, None, "Tipo de relatório desconhecido.")


def _report_card_download(icon, title, subtitle, proposta_id, report_type, nome_cliente="Cliente", numero_proposta=None):
    """Botão "Baixar <relatório>" de um clique; o PDF só é gerado quando a pessoa pede
    (abrir a proposta não gera os quatro relatórios)."""
    baixar_pdf(f"Baixar {title}", f"rel_{report_type}_{proposta_id}",
               lambda: _gerar_report_pdf(proposta_id, report_type, nome_cliente, numero_proposta),
               legenda=subtitle)


def _tab_detalhes(proposta_id, proposta):
    # ── Barra de progresso ────────────────────────────────────────────────
    hoje = datetime.now().date()
    data_inicio_exec = proposta.get('data_inicio_execucao') or proposta.get('data_inicio')
    if data_inicio_exec is None:
        data_inicio_exec = hoje - timedelta(days=1)
    data_fim_prevista = proposta.get('data_fim')
    if data_fim_prevista is None:
        data_fim_prevista = data_inicio_exec + timedelta(days=30)

    try:
        total_dias = max(1, (data_fim_prevista - data_inicio_exec).days)
        dias_decorridos = (hoje - data_inicio_exec).days
        progresso = min(100, max(0, int(dias_decorridos / total_dias * 100)))
        dias_restantes = max(0, (data_fim_prevista - hoje).days)
        atrasado = hoje > data_fim_prevista
        cor_prog = "#C0392B" if atrasado else "#1D6A4A"
        label_prog = (f"Atrasado em {(hoje - data_fim_prevista).days} dias"
                      if atrasado else f"{dias_restantes} dias restantes")
        st.markdown(f"""
        <div style="background:#f7f7f5;border-radius:10px;padding:14px 18px;margin-bottom:18px;border:1px solid #e8e6e0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-weight:600;color:{NAVY};font-size:13px;">Progresso do Prazo</span>
            <span style="font-size:13px;color:{cor_prog};font-weight:600;">{label_prog}</span>
          </div>
          <div style="background:#e8e6e0;border-radius:6px;height:10px;overflow:hidden;">
            <div style="background:{cor_prog};width:{progresso}%;height:100%;border-radius:6px;transition:width .3s;"></div>
          </div>
          <div style="margin-top:6px;font-size:12px;color:#9a9890;">{progresso}% — {dias_decorridos} de {total_dias} dias</div>
        </div>""", unsafe_allow_html=True)
    except (TypeError, AttributeError):
        pass

    # ── Formulário novo andamento ─────────────────────────────────────────
    st.markdown(f'<p style="font-weight:600;color:{NAVY};font-size:14px;margin-bottom:4px;">Novo Andamento</p>', unsafe_allow_html=True)
    with st.form(key=f"form_andamento_{proposta_id}"):
        descricao_andamento = st.text_area("Descrição:", height=90, placeholder="Descreva o que aconteceu nesta etapa…", label_visibility="collapsed")
        submitted = st.form_submit_button("Registrar Andamento", type="primary", use_container_width=True)
        if submitted:
            if descricao_andamento:
                try:
                    resultado = st.session_state.db.add_andamento_proposta(
                        proposta_id=proposta_id, status="Em andamento", observacao=descricao_andamento)
                    if resultado:
                        st.success("Andamento registrado!")
                        st.rerun()
                    else:
                        st.error("Erro ao registrar andamento.")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
            else:
                st.warning("Insira uma descrição.")

    # ── Histórico de andamentos ───────────────────────────────────────────
    try:
        andamentos = st.session_state.db.get_andamentos_proposta(proposta_id)
        if not andamentos.empty:
            st.markdown(f'<p style="font-weight:600;color:{NAVY};font-size:14px;margin:16px 0 8px;">Histórico</p>', unsafe_allow_html=True)
            cards = ""
            for _, a in andamentos.iterrows():
                texto = html_module.escape(str(a.get('observacao') or a.get('descricao') or 'Sem descrição'))
                data_and = a.get('data')
                data_str = data_and.strftime('%d/%m/%Y') if pd.notna(data_and) and data_and else '—'
                cards += (
                    f'<div style="border-left:3px solid {GOLD};background:#fff;border-radius:0 8px 8px 0;'
                    f'padding:10px 14px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.06);">'
                    f'<div style="font-size:13px;color:#1C1C1A;">{texto}</div>'
                    f'<div style="font-size:11px;color:#9a9890;margin-top:4px;"> {data_str}</div>'
                    f'</div>'
                )
            st.markdown(cards, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar andamentos: {str(e)}")


def _tab_produtos(proposta_id):
    # ── Lista atual de produtos ───────────────────────────────────────────
    try:
        produtos_proposta_raw = st.session_state.db.get_produtos_organizadores(proposta_id=proposta_id)
        if not produtos_proposta_raw.empty:
            produtos_proposta = produtos_proposta_raw.rename(columns={'valor': 'valor_unit'})
            produtos_proposta['valor_total'] = produtos_proposta['valor_unit'] * produtos_proposta['quantidade']
            valor_total_produtos = produtos_proposta['valor_total'].sum()

            # Métricas resumo
            c1, c2 = st.columns(2)
            c1.metric("Itens adicionados", len(produtos_proposta))
            c2.metric("Total produtos", _fmt_brl(valor_total_produtos))

            # Cards dos itens
            cards = ""
            for _, p in produtos_proposta.iterrows():
                nome = html_module.escape(str(p.get('nome', '')))
                comodo = html_module.escape(str(p.get('comodo') or 'Geral'))
                qty = int(p.get('quantidade', 1))
                vunit = float(p.get('valor_unit', 0))
                vtot = float(p.get('valor_total', 0))
                vunit_str = _fmt_brl(vunit)
                vtot_str  = _fmt_brl(vtot)
                cards += (
                    f'<div style="border-left:3px solid {GOLD};background:#fff;border-radius:0 8px 8px 0;'
                    f'padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);'
                    f'display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><span style="font-weight:600;color:{NAVY};font-size:13px;">{nome}</span>'
                    f'<span style="font-size:11px;color:#9a9890;margin-left:8px;"> {comodo}</span></div>'
                    f'<div style="text-align:right;white-space:nowrap;">'
                    f'<span style="font-size:11px;color:#9a9890;">{qty}× {vunit_str}</span><br>'
                    f'<span style="font-weight:700;color:#1D6A4A;font-size:13px;">{vtot_str}</span></div>'
                    f'</div>'
                )
            st.markdown(cards, unsafe_allow_html=True)

            # Editar produto (quantidade / valor unitário) — com opção de remover
            with st.expander("Editar produto"):
                produto_edit_id = st.selectbox(
                    "Selecione o produto:",
                    options=produtos_proposta['id'].tolist(),
                    format_func=lambda x: produtos_proposta.loc[produtos_proposta['id'] == x, 'nome'].iloc[0],
                    key=f"select_editar_produto_{proposta_id}"
                )
                _linha = produtos_proposta.loc[produtos_proposta['id'] == produto_edit_id].iloc[0]
                _qtd_atual = int(_linha.get('quantidade', 1))
                _valor_atual = float(_linha.get('valor_unit', 0))
                with st.form(key=f"form_editar_produto_{proposta_id}"):
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        nova_qtd = st.number_input("Quantidade:", min_value=1, value=_qtd_atual,
                                                   key=f"edit_qtd_produto_{proposta_id}")
                    with ce2:
                        novo_valor = input_moeda("Valor unitário (R$):",
                                                 f"edit_valor_produto_{proposta_id}",
                                                 value=_valor_atual, step=1.0)
                    st.caption(f"Novo total do item: {_fmt_brl(nova_qtd * novo_valor)}")
                    cbtn1, cbtn2 = st.columns([3, 1])
                    with cbtn1:
                        salvar = st.form_submit_button("Salvar alterações", type="primary", use_container_width=True)
                    with cbtn2:
                        remover = botao_excluir("Remover", f"rem_prod_{proposta_id}", is_form=True)
                    if salvar:
                        try:
                            if st.session_state.db.update_produto_organizador(produto_edit_id, valor=novo_valor, quantidade=nova_qtd):
                                st.session_state.db.invalidar_cache()
                                st.success("Produto atualizado!")
                            else:
                                st.error("Falha ao atualizar.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                    if remover:
                        try:
                            if st.session_state.db.remove_produto_organizador(produto_edit_id):
                                st.session_state.db.invalidar_cache()
                                st.success("Produto removido!")
                            else:
                                st.error("Falha ao remover.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

            # PDF dos produtos
            st.markdown("---")
            def _gerar_pdf_produtos(proposta_id=proposta_id, produtos_proposta=produtos_proposta,
                                    valor_total_produtos=valor_total_produtos):
                # baixar_pdf: o download não fecha a janela da proposta e o link não expira (antes não baixava nada)
                import tempfile
                from utils.pdf_generator_v2 import gerar_pdf_venda_v2
                from sqlalchemy import text as _text
                try:
                    _prop_row = st.session_state.db.session.execute(
                        _text("SELECT p.numero, c.nome FROM propostas p LEFT JOIN clientes c ON p.cliente_id = c.id WHERE p.id = :pid"),
                        {"pid": proposta_id}).fetchone()
                    _num_prop = _prop_row[0] if _prop_row else proposta_id
                    _nome_cl = _prop_row[1] if _prop_row and _prop_row[1] else "Cliente"
                    venda_dados = {'id': _num_prop, 'status': 'Proposta', 'forma_pagamento': 'N/A',
                                   'valor_total': round(float(valor_total_produtos), 2),
                                   'data_venda': datetime.now().strftime('%d/%m/%Y')}
                    itens_pdf = produtos_proposta.rename(columns={'nome': 'produto_nome', 'valor_unit': 'preco_unitario'})[
                        ['produto_nome', 'quantidade', 'preco_unitario']].copy()
                    caminho = os.path.join(tempfile.mkdtemp(), "produtos.pdf")
                    gerar_pdf_venda_v2(venda_dados, {'nome': _nome_cl}, itens_pdf, caminho)
                    return caminho, f"Produtos_{_nome_cl.replace(' ', '_')}_{_num_prop}.pdf", None
                except Exception as e:
                    return None, None, str(e)
            baixar_pdf("Baixar relatório dos produtos", f"pdf_produtos_proposta_{proposta_id}", _gerar_pdf_produtos)
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon"></div>
              <div class="itens-empty-title">Nenhum produto ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir produtos</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {str(e)}")

    st.markdown(f'<p style="font-weight:600;color:{NAVY};font-size:14px;margin-bottom:4px;"> Adicionar Produto</p>', unsafe_allow_html=True)
    with st.form(key=f"form_produto_{proposta_id}"):
        produtos_cadastrados = st.session_state.db.get_produtos()
        if not produtos_cadastrados.empty:
            opcoes_produtos = produtos_cadastrados['id'].tolist()
            def format_produto_option(pid):
                p = produtos_cadastrados.loc[produtos_cadastrados['id'] == pid]
                if not p.empty:
                    return f"{p['nome'].iloc[0]} — {_fmt_brl(float(p['preco_venda'].iloc[0]))}"
                return "?"
            produto_selecionado_id = st.selectbox("Produto:", options=opcoes_produtos,
                                                   format_func=format_produto_option,
                                                   key=f"select_produto_{proposta_id}")
            produto = produtos_cadastrados.loc[produtos_cadastrados['id'] == produto_selecionado_id].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                quantidade = st.number_input("Quantidade:", min_value=1, value=1)
                comodo = st.text_input("Cômodo/Área:")
            with col2:
                preco_padrao = float(produto['preco_venda'])
                usar_preco_padrao = st.checkbox("Usar preço padrão", value=True)
                if not usar_preco_padrao:
                    valor_unitario = input_moeda("Preço (R$):", f"preco_custom_{proposta_id}", value=preco_padrao, step=1.0)
                else:
                    valor_unitario = preco_padrao
                    st.write(f"Preço: {_fmt_brl(preco_padrao)}")
            if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
                try:
                    st.session_state.db.add_produto_organizador(proposta_id=proposta_id, nome=produto['nome'],
                        descricao=produto['descricao'], valor=valor_unitario, quantidade=quantidade,
                        comodo=comodo if comodo else "Geral")
                    st.success(f"'{produto['nome']}' adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.warning("Nenhum produto cadastrado. Adicione em Cadastros > Produtos.")
            st.form_submit_button("ADICIONAR", disabled=True)


def _tab_itens(proposta_id, show_finalizar=False, proposta=None):
    """Itens & Custos com navegação lateral por categoria."""

    if show_finalizar and proposta is not None:
        from utils.proposta_status import normalize as _norm_exec_status
        # Cabeçalho unificado (badge de status + categoria + início) para
        # manter consistência com as telas de aberta/aprovada e finalizada.
        _proposal_meta_header(proposta, _norm_exec_status(proposta.get('status', '')) or '')
        valor_base_atual = _safe_float(proposta.get('valor'))
        sinal_atual = _safe_float(proposta.get('sinal'))
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 14px;background:#faf9f7;border:1px solid #e8e5df;border-radius:10px;'
            f'margin-bottom:10px;">'
            f'<span style="font-size:13px;color:{NAVY};font-weight:600;">Valor do serviço (Personal Organizer)</span>'
            f'<span style="font-size:14px;color:#1D6A4A;font-weight:700;">{_fmt_brl(valor_base_atual)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if sinal_atual > 0:
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:8px 14px;background:#fff;border:1px solid #e8e5df;border-radius:10px;'
                f'margin:-4px 0 10px;">'
                f'<span style="font-size:12px;color:#8B8680;">Sinal / entrada já pago</span>'
                f'<span style="font-size:13px;color:#B7860D;font-weight:700;">– {_fmt_brl(sinal_atual)}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with st.container(key=f"btned_servico_{proposta_id}"), st.expander("Editar serviço", icon=":material/edit:"):
            with st.form(key=f"form_editar_valor_exec_{proposta_id}"):
                novo_valor = input_moeda(
                    "Valor do serviço (Personal Organizer) — R$:",
                    f"novo_valor_exec_{proposta_id}", value=valor_base_atual, step=10.0)
                novo_sinal = input_moeda(
                    "Sinal / entrada já pago pelo cliente — R$:",
                    f"novo_sinal_exec_{proposta_id}", value=sinal_atual, step=10.0,
                    help="Valor que o cliente pagou ao confirmar o serviço. Será descontado do total no relatório do cliente.")
                _tipos_opcoes = ["Organização", "Consultoria", "Acompanhamento", "Projeto", "Outro"]
                _tipo_atual = str(proposta.get('tipo_proposta') or "").strip()
                if _tipo_atual and _tipo_atual not in _tipos_opcoes:
                    _tipos_opcoes = [_tipo_atual] + _tipos_opcoes
                _idx_tipo = _tipos_opcoes.index(_tipo_atual) if _tipo_atual in _tipos_opcoes else 0
                novo_tipo = st.selectbox(
                    "Tipo de Proposta:",
                    _tipos_opcoes, index=_idx_tipo,
                    key=f"novo_tipo_exec_{proposta_id}")
                nova_descricao = st.text_area(
                    "Descrição do serviço (ambientes/itens):",
                    value=str(proposta.get('descricao') or ''),
                    height=120,
                    key=f"nova_descricao_exec_{proposta_id}")
                if st.form_submit_button("Salvar alterações", type="primary", use_container_width=True):
                    try:
                        res = st.session_state.db.update_proposta(
                            proposta_id, valor=novo_valor, tipo_proposta=novo_tipo,
                            descricao=nova_descricao, sinal=novo_sinal)
                        ok = res.get('status', False) if isinstance(res, dict) else bool(res)
                        if ok:
                            # valor/sinal mudaram: ajusta o sinal recebido e o saldo a receber no Financeiro
                            st.session_state.db.sincronizar_sinal_proposta(proposta_id)
                            st.session_state.db.invalidar_cache()
                            st.success("Serviço atualizado!")
                            st.rerun()
                        else:
                            msg = res.get('message', 'Erro ao atualizar serviço.') if isinstance(res, dict) else 'Erro ao atualizar serviço.'
                            st.error(msg)
                    except Exception as e:
                        st.error(str(e))

    try:
        produtos_df     = st.session_state.db.get_produtos_organizadores(proposta_id)
        fornecedores_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
        assistentes_df  = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
        outros_df       = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")
    except Exception as e:
        st.error(f"Erro ao carregar itens: {e}"); return

    t_prod  = (produtos_df['valor'] * produtos_df['quantidade']).sum() if not produtos_df.empty else 0
    t_forn  = fornecedores_df['valor'].sum() if not fornecedores_df.empty else 0
    t_asst  = assistentes_df['valor'].sum() if not assistentes_df.empty else 0
    t_outr  = outros_df['valor'].sum() if not outros_df.empty else 0
    t_total = t_prod + t_forn + t_asst + t_outr

    cats = [
        ("Produtos",     "", len(produtos_df),     t_prod,  GOLD),
        ("Fornecedores", "", len(fornecedores_df),  t_forn,  "#0F5E6E"),
        ("Assistentes",  "", len(assistentes_df),   t_asst,  "#6B4EAA"),
        ("Outros",       "", len(outros_df),        t_outr,  "#E07B39"),
    ]

    key_cat = f"itens_cat_{proposta_id}"
    if key_cat not in st.session_state:
        st.session_state[key_cat] = "Produtos"
    old_to_new = {"Produtos": "Produtos", "Fornecedores": "Fornecedores",
                  "Assistentes": "Assistentes", "Outros": "Outros"}
    if st.session_state[key_cat] in old_to_new:
        st.session_state[key_cat] = old_to_new[st.session_state[key_cat]]

    cat_ativa = st.session_state[key_cat]

    _itens_css = """
    <style>
    .itens-sidebar-title {
        font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: #8B8680; padding: 0 0 10px 2px;
        border-bottom: 1px solid #eee; margin-bottom: 6px;
    }
    .itens-total-box {
        background: #faf9f7; border: 1px solid #e8e5df; border-radius: 10px;
        padding: 14px 12px; margin-top: 12px;
    }
    .itens-total-label {
        font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; color: #8B8680; margin-bottom: 4px;
    }
    .itens-total-value {
        font-size: 18px; font-weight: 700; color: __NAVY__;
    }
    .itens-content-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 18px; background: #faf9f7; border-radius: 10px;
        margin-bottom: 16px; border: 1px solid #e8e5df;
    }
    .itens-content-title {
        font-size: 16px; font-weight: 700; color: __NAVY__;
        display: flex; align-items: center; gap: 8px;
    }
    .itens-content-subtitle {
        font-size: 12px; color: #8B8680; margin-top: 2px;
    }
    .itens-empty-state {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 48px 20px;
        background: #faf9f7; border-radius: 12px; border: 1px dashed #ddd;
        margin: 8px 0 16px 0; text-align: center;
    }
    .itens-empty-icon { font-size: 40px; margin-bottom: 12px; opacity: 0.6; }
    .itens-empty-title {
        font-size: 15px; font-weight: 600; color: #4a4a4a; margin-bottom: 6px;
    }
    .itens-empty-hint { font-size: 12px; color: #9a9890; }
    </style>
    """.replace("__NAVY__", NAVY)
    st.markdown(_itens_css, unsafe_allow_html=True)

    col_nav, col_main = st.columns([1, 2.8])

    with col_nav:
        st.markdown('<div class="itens-sidebar-title">ITENS & CUSTOS</div>', unsafe_allow_html=True)

        labels = []
        label_map = {}
        for cat_name, cat_icon, cat_qtd, cat_total, cat_cor in cats:
            sub = _fmt_brl(cat_total) if cat_total > 0 else ""
            display = f"{cat_icon} {cat_name}  {cat_qtd}" + (f" · {sub}" if sub else "")
            labels.append(display)
            label_map[display] = cat_name

        labels_base = [name for name, _, _, _, _ in cats]
        idx_atual = labels_base.index(cat_ativa) if cat_ativa in labels_base else 0

        escolha = st.radio(
            "Categoria",
            options=labels,
            index=idx_atual,
            key=f"radio_cat_{proposta_id}",
            label_visibility="collapsed"
        )

        cat_ativa = label_map.get(escolha, "Produtos")
        st.session_state[key_cat] = cat_ativa

        st.markdown(f"""
        <div class="itens-total-box">
          <div class="itens-total-label">Total geral</div>
          <div class="itens-total-value">{_fmt_brl(t_total)}</div>
        </div>""", unsafe_allow_html=True)

        if show_finalizar:
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            if st.button(" FINALIZAR PROJETO", key=f"btn_finalizar_exec_{proposta_id}", use_container_width=True, type="primary"):
                try:
                    res = finalizar_proposta_v2(int(proposta_id))
                    if res.get('status', False):
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state['proposta_finalizada_sucesso'] = True
                        st.session_state.db.invalidar_cache()
                        st.rerun()
                    else:
                        st.error(res.get('message', 'Erro ao finalizar.'))
                except Exception as e:
                    st.error(str(e))

    with col_main:
        for cat_name, cat_icon, cat_qtd, cat_total, cat_cor in cats:
            if cat_name == cat_ativa:
                sub_text = f"{cat_qtd} {'item' if cat_qtd == 1 else 'itens'} · {_fmt_brl(cat_total)}"
                st.markdown(f"""
                <div class="itens-content-header">
                  <div>
                    <div class="itens-content-title">{cat_icon} {cat_name}</div>
                    <div class="itens-content-subtitle">{sub_text}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                break

        if cat_ativa == "Produtos":
            _tab_produtos(proposta_id)
        elif cat_ativa == "Fornecedores":
            _tab_fornecedores(proposta_id)
        elif cat_ativa == "Assistentes":
            _tab_assistentes(proposta_id)
        elif cat_ativa == "Outros":
            _tab_outros(proposta_id)



def _acrescimos_cards(acrescimos, cor_borda=GOLD):
    """Renderiza acréscimos como cards com borda colorida e valor à direita."""
    cards = ""
    for _, a in acrescimos.iterrows():
        nome = html_module.escape(str(a.get('fornecedor') or a.get('descricao') or '—'))
        desc = html_module.escape(str(a.get('descricao') or ''))
        val  = float(a.get('valor', 0))
        val_str = _fmt_brl(val)
        desc_html = (f"<br><span style='font-size:11px;color:#9a9890;'>{desc}</span>" if desc and desc != nome else "")
        cards += (
            f'<div style="border-left:3px solid {cor_borda};background:#fff;border-radius:0 8px 8px 0;'
            f'padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);'
            f'display:flex;justify-content:space-between;align-items:center;">'
            f'<div><span style="font-weight:600;color:{NAVY};font-size:13px;">{nome}</span>{desc_html}</div>'
            f'<span style="font-weight:700;color:#1D6A4A;font-size:13px;white-space:nowrap;">{val_str}</span>'
            f'</div>'
        )
    return cards


def _tab_fornecedores(proposta_id):
    # ── Lista atual ───────────────────────────────────────────────────────
    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
        if not acrescimos.empty:
            total_forn = acrescimos['valor'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Fornecedores", len(acrescimos))
            c2.metric("Total", _fmt_brl(total_forn))
            st.markdown(_acrescimos_cards(acrescimos, "#0F5E6E"), unsafe_allow_html=True)

            with st.expander(" Editar /  Remover"):
                ids = acrescimos['id'].tolist()
                fmt_forn = lambda x: acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]
                col_e, col_r = st.columns(2)
                with col_e:
                    with st.form(key=f"form_editar_fornecedor_{proposta_id}"):
                        aid = st.selectbox("Editar:", options=ids, format_func=fmt_forn, key=f"sel_edit_forn_{proposta_id}")
                        atual = acrescimos.loc[acrescimos['id'] == aid].iloc[0]
                        nv = input_moeda("Novo valor (R$):", f"nv_forn_{proposta_id}", value=float(atual['valor']), step=10.0)
                        nd = st.text_area("Observações:", value=str(atual['descricao'] or ""), height=70, key=f"nd_forn_{proposta_id}")
                        if st.form_submit_button("Salvar", use_container_width=True):
                            try:
                                if st.session_state.db.update_acrescimo_proposta(aid, valor=nv, descricao=nd):
                                    st.success("Atualizado!"); st.rerun()
                                else:
                                    st.error("Falha ao atualizar.")
                            except Exception as e:
                                st.error(str(e))
                with col_r:
                    with st.form(key=f"form_remover_fornecedor_{proposta_id}"):
                        rid = st.selectbox("Remover:", options=ids, format_func=fmt_forn, key=f"sel_rem_forn_{proposta_id}")
                        if botao_excluir("Remover", f"rem_forn_{proposta_id}", is_form=True):
                            try:
                                if st.session_state.db.remove_acrescimo_proposta(rid):
                                    st.success("Removido!"); st.rerun()
                                else:
                                    st.error("Falha ao remover.")
                            except Exception as e:
                                st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon"></div>
              <div class="itens-empty-title">Nenhum fornecedor ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir fornecedores</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar fornecedores: {str(e)}")

    st.markdown(f'<p style="font-weight:600;color:{NAVY};font-size:14px;margin-bottom:4px;"> Adicionar Fornecedor</p>', unsafe_allow_html=True)
    try:
        fornecedores = st.session_state.db.get_fornecedores()
        if not fornecedores.empty:
            with st.form(key=f"form_fornecedor_{proposta_id}"):
                def fmt_forn_opt(fid):
                    r = fornecedores.loc[fornecedores['id'] == fid]
                    return r['descricao'].iloc[0] if not r.empty else "?"
                forn_sel = st.selectbox("Fornecedor:", options=fornecedores['id'].tolist(),
                                        format_func=fmt_forn_opt, key=f"select_fornecedor_{proposta_id}")
                col1, col2 = st.columns(2)
                with col1:
                    valor_servico = input_moeda("Valor (R$):", f"valor_forn_{proposta_id}", value=0.0, step=10.0)
                with col2:
                    observacoes = st.text_area("Observações:", height=70, key=f"obs_forn_{proposta_id}")
                if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
                    if valor_servico <= 0:
                        st.error("Valor deve ser maior que zero.")
                    else:
                        try:
                            res = st.session_state.db.add_fornecedor_proposta(proposta_id=proposta_id,
                                  fornecedor_id=forn_sel, valor=valor_servico, observacoes=observacoes)
                            if res and "acrescimo_id" in res:
                                st.success("Fornecedor adicionado!"); st.rerun()
                            else:
                                st.error("Erro ao adicionar.")
                        except Exception as e:
                            st.error(str(e))
        else:
            st.info("Nenhum fornecedor cadastrado. Adicione em Cadastros > Fornecedores.")
    except Exception as e:
        st.error(str(e))


def _tab_assistentes(proposta_id):
    # ── Lista atual ───────────────────────────────────────────────────────
    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
        if not acrescimos.empty:
            total_asst = acrescimos['valor'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Assistentes", len(acrescimos))
            c2.metric("Total", _fmt_brl(total_asst))
            st.markdown(_acrescimos_cards(acrescimos, "#6B4EAA"), unsafe_allow_html=True)

            with st.expander(" Editar /  Remover"):
                ids = acrescimos['id'].tolist()
                fmt_a = lambda x: acrescimos.loc[acrescimos['id'] == x, 'fornecedor'].iloc[0]
                col_e, col_r = st.columns(2)
                with col_e:
                    with st.form(key=f"form_editar_assistente_{proposta_id}"):
                        aid = st.selectbox("Editar:", options=ids, format_func=fmt_a, key=f"sel_edit_asst_{proposta_id}")
                        atual = acrescimos.loc[acrescimos['id'] == aid].iloc[0]
                        nv = input_moeda("Novo valor (R$):", f"nv_asst_{proposta_id}", value=float(atual['valor']), step=10.0)
                        nd = st.text_area("Descrição:", value=str(atual['descricao'] or ""), height=70, key=f"nd_asst_{proposta_id}")
                        if st.form_submit_button("Salvar", use_container_width=True):
                            try:
                                if st.session_state.db.update_acrescimo_proposta(aid, valor=nv, descricao=nd):
                                    st.success("Atualizado!"); st.rerun()
                                else:
                                    st.error("Falha ao atualizar.")
                            except Exception as e:
                                st.error(str(e))
                with col_r:
                    with st.form(key=f"form_remover_assistente_{proposta_id}"):
                        rid = st.selectbox("Remover:", options=ids, format_func=fmt_a, key=f"sel_rem_asst_{proposta_id}")
                        if botao_excluir("Remover", f"rem_asst_{proposta_id}", is_form=True):
                            try:
                                if st.session_state.db.remove_acrescimo_proposta(rid):
                                    st.success("Removido!"); st.rerun()
                                else:
                                    st.error("Falha ao remover.")
                            except Exception as e:
                                st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon"></div>
              <div class="itens-empty-title">Nenhum assistente ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir assistentes</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar assistentes: {str(e)}")

    st.markdown(f'<p style="font-weight:600;color:{NAVY};font-size:14px;margin-bottom:4px;"> Adicionar Assistente</p>', unsafe_allow_html=True)
    try:
        assistentes = st.session_state.db.get_assistentes()
        if not assistentes.empty:
            with st.form(key=f"form_assistente_{proposta_id}"):
                asst_sel = st.selectbox("Assistente:", options=assistentes['id'].tolist(),
                                        format_func=lambda x: assistentes.loc[assistentes['id'] == x, 'nome'].iloc[0])
                col1, col2 = st.columns(2)
                with col1:
                    valor_servico = input_moeda("Valor (R$):", f"valor_asst_add_{proposta_id}", value=0.0, step=10.0)
                with col2:
                    observacoes = st.text_area("Observações:", height=70)
                if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
                    if valor_servico <= 0:
                        st.error("Valor deve ser maior que zero.")
                    else:
                        try:
                            res = st.session_state.db.add_assistente_proposta(proposta_id=proposta_id,
                                  assistente_id=asst_sel, valor=valor_servico, observacoes=observacoes)
                            if res and "acrescimo_id" in res:
                                st.success("Assistente adicionado!"); st.rerun()
                            else:
                                st.error("Erro ao adicionar.")
                        except Exception as e:
                            st.error(str(e))
        else:
            st.info("Nenhum assistente cadastrado. Adicione em Cadastros > Assistentes.")
    except Exception as e:
        st.error(str(e))


def _tab_outros(proposta_id):
    # ── Lista atual ───────────────────────────────────────────────────────
    try:
        acrescimos = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")
        if not acrescimos.empty:
            total_outros = acrescimos['valor'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Itens extras", len(acrescimos))
            c2.metric("Total", _fmt_brl(total_outros))
            # Montar cards com nome extraído da descrição
            cards = ""
            for _, a in acrescimos.iterrows():
                desc_raw = str(a.get('descricao') or '—')
                nome = html_module.escape(desc_raw.split(' - ')[0] if ' - ' in desc_raw else desc_raw)
                sub  = html_module.escape(desc_raw.split(' - ')[1] if ' - ' in desc_raw else '')
                comodo = html_module.escape(str(a.get('fornecedor') or 'Geral'))
                val = float(a.get('valor', 0))
                val_str = _fmt_brl(val)
                sub_html = (f'<br><span style="font-size:11px;color:#9a9890;">{sub}</span>' if sub else '')
                cards += (
                    f'<div style="border-left:3px solid #E07B39;background:#fff;border-radius:0 8px 8px 0;'
                    f'padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);'
                    f'display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><span style="font-weight:600;color:{NAVY};font-size:13px;">{nome}</span>{sub_html}'
                    f'<span style="font-size:11px;color:#9a9890;margin-left:6px;">{comodo}</span></div>'
                    f'<span style="font-weight:700;color:#1D6A4A;font-size:13px;white-space:nowrap;">{val_str}</span>'
                    f'</div>'
                )
            st.markdown(cards, unsafe_allow_html=True)

            with st.expander(" Remover item"):
                with st.form(key=f"form_remover_outros_{proposta_id}"):
                    rid = st.selectbox("Selecione:", options=acrescimos['id'].tolist(),
                                       format_func=lambda x: acrescimos.loc[acrescimos['id'] == x, 'descricao'].iloc[0])
                    if botao_excluir("Remover", f"rem_outros_{proposta_id}", is_form=True):
                        try:
                            if st.session_state.db.remove_acrescimo_proposta(rid):
                                st.success("Item removido!"); st.rerun()
                            else:
                                st.error("Falha ao remover.")
                        except Exception as e:
                            st.error(str(e))
        else:
            st.markdown("""
            <div class="itens-empty-state">
              <div class="itens-empty-icon"></div>
              <div class="itens-empty-title">Nenhum item extra ainda</div>
              <div class="itens-empty-hint">Clique em "+ Adicionar" abaixo para incluir itens extras</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar itens: {str(e)}")

    st.markdown(f'<p style="font-weight:600;color:{NAVY};font-size:14px;margin-bottom:4px;"> Adicionar Item Extra</p>', unsafe_allow_html=True)
    with st.form(key=f"form_outros_{proposta_id}"):
        col1, col2 = st.columns(2)
        with col1:
            nome_item = st.text_input("Nome do Item:")
            descricao_item = st.text_input("Descrição:")
            comodo_area = st.text_input("Cômodo/Área:")
        with col2:
            valor_unitario = input_moeda("Valor unitário (R$):", f"vu_outros_{proposta_id}", value=0.0, step=10.0)
            quantidade = st.number_input("Quantidade:", min_value=1, value=1)
            valor_total_calc = valor_unitario * quantidade
            st.markdown(f'<p style="color:#1D6A4A;font-weight:600;margin-top:22px;">Total: {_fmt_brl(valor_total_calc)}</p>', unsafe_allow_html=True)
        if st.form_submit_button("ADICIONAR", type="primary", use_container_width=True):
            if not nome_item or valor_unitario <= 0:
                st.error("Preencha o nome e um valor válido.")
            else:
                try:
                    res = st.session_state.db.add_acrescimo_proposta(
                        proposta_id=proposta_id, tipo="OUTROS",
                        valor=valor_unitario * quantidade,
                        descricao=f"{nome_item} - {descricao_item}" if descricao_item else nome_item,
                        fornecedor=comodo_area if comodo_area else "Geral"
                    )
                    if res and "acrescimo_id" in res:
                        st.success(f"'{nome_item}' adicionado!"); st.rerun()
                    else:
                        st.error("Erro ao adicionar.")
                except Exception as e:
                    st.error(str(e))


def _status_badge(label, cor_fundo, cor_texto="#fff"):
    st.markdown(f"""
    <div style="display:inline-block;background:{cor_fundo};color:{cor_texto};
                border-radius:20px;padding:5px 16px;font-size:13px;font-weight:600;
                margin-bottom:16px;">{label}</div>""", unsafe_allow_html=True)


def _tab_acoes(proposta_id, proposta):
    from utils.proposta_status import (
        normalize as _normalize_status, label_for as _label_status,
        STATUS_EM_ABERTO, STATUS_APROVADA, STATUS_RECUSADA,
        STATUS_EM_EXECUCAO, STATUS_FINALIZADA,
    )
    status_atual   = _normalize_status(proposta.get('status', '')) or ''
    status_execucao = proposta.get('status_execucao', '')

    em_aberto    = status_atual == STATUS_EM_ABERTO
    esta_aprovada = status_atual == STATUS_APROVADA
    em_execucao  = status_execucao == 'Em execução'
    finalizada   = status_atual in [STATUS_FINALIZADA, STATUS_RECUSADA]

    # ── Badge de status ───────────────────────────────────────────────────
    if em_aberto:
        _status_badge(" Em Aberto", "#B7860D")
    elif esta_aprovada and not em_execucao and not finalizada:
        _status_badge(" Aprovada — aguardando início", "#1D6A4A")
    elif em_execucao and not finalizada:
        _status_badge("Em Execução", "#1565C0")
    elif finalizada:
        cor_fin = "#4A4A4A" if status_atual == STATUS_FINALIZADA else "#C0392B"
        _status_badge(f" {_label_status(status_atual)}", cor_fin)
    else:
        _status_badge(f"● {_label_status(status_atual)}", "#555")

    # ── EM ABERTO ─────────────────────────────────────────────────────────
    if em_aberto:
        st.markdown('<p style="color:#555;font-size:13px;margin-bottom:12px;">Escolha a próxima ação para esta proposta.</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(" Aprovar Proposta", type="primary", use_container_width=True, key=f"btn_aprovar_{proposta_id}"):
                try:
                    res = st.session_state.db.update_proposta_status(proposta_id=proposta_id,
                          novo_status=STATUS_APROVADA, data_aprovacao=datetime.now().date())
                    if res.get('status', False):
                        st.success("Proposta aprovada!")
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error(res.get('message', 'Erro ao aprovar.'))
                except Exception as e:
                    st.error(str(e))
        with col2:
            if st.button("Recusar Proposta", use_container_width=True, key=f"btn_recusar_{proposta_id}"):
                try:
                    res = st.session_state.db.update_proposta_status(proposta_id=proposta_id, novo_status=STATUS_RECUSADA)
                    if res.get('status', False):
                        st.session_state.db.update_proposta(proposta_id, status_execucao=EXEC_CANCELADA, data_fim=datetime.now().date())
                        st.success("Proposta recusada.")
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error("Erro ao recusar.")
                except Exception as e:
                    st.error(str(e))

    # ── APROVADA ──────────────────────────────────────────────────────────
    elif esta_aprovada and not em_execucao and not finalizada:
        st.markdown('<p style="color:#555;font-size:13px;margin-bottom:12px;">Inicie a execução quando o trabalho começar.</p>', unsafe_allow_html=True)
        if st.button("▶ Iniciar Execução", type="primary", use_container_width=True, key=f"btn_iniciar_exec_{proposta_id}"):
            try:
                res = st.session_state.db.update_proposta_status(proposta_id=proposta_id,
                      novo_status=STATUS_EM_EXECUCAO, data_aprovacao=proposta.get('data_aprovacao'))
                if res.get('status', False):
                    st.success("Execução iniciada!")
                    st.session_state['kanban_selected_proposta'] = None
                    st.session_state.db.invalidar_cache()
                    st.rerun()
                else:
                    st.error(res.get('message', 'Erro.'))
            except Exception as e:
                st.error(str(e))

    # ── EM EXECUÇÃO ───────────────────────────────────────────────────────
    elif em_execucao and not finalizada:
        try:
            valor_base      = _safe_float(proposta.get('valor'))
            produtos_df     = st.session_state.db.get_produtos_organizadores(proposta_id)
            fornecedores_df = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "FORNECEDOR")
            assistentes_df  = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "ASSISTENTE")
            outros_df       = st.session_state.db.get_acrescimos_proposta_por_tipo(proposta_id, "OUTROS")

            total_prod = (produtos_df['valor'] * produtos_df['quantidade']).sum() if not produtos_df.empty else 0
            total_forn = fornecedores_df['valor'].sum() if not fornecedores_df.empty else 0
            total_asst = assistentes_df['valor'].sum() if not assistentes_df.empty else 0
            total_outr = outros_df['valor'].sum() if not outros_df.empty else 0
            total_geral = valor_base + total_prod + total_forn + total_asst + total_outr

            # Métricas compactas
            c1, c2, c3 = st.columns(3)
            c1.metric("Serviço (PO)", _fmt_brl(valor_base))
            c2.metric("Custos totais", _fmt_brl(total_forn + total_asst + total_outr + total_prod))
            c3.metric("Total geral", _fmt_brl(total_geral))

            # Editar valor do serviço durante a execução
            with st.expander("Editar valor do serviço"):
                with st.form(key=f"form_editar_valor_exec_{proposta_id}"):
                    novo_valor = input_moeda(
                        "Valor do serviço (Personal Organizer) — R$:",
                        f"novo_valor_exec_{proposta_id}", value=float(valor_base), step=10.0)
                    if st.form_submit_button("Salvar valor", type="primary", use_container_width=True):
                        try:
                            res = st.session_state.db.update_proposta(proposta_id, valor=novo_valor)
                            ok = res.get('status', False) if isinstance(res, dict) else bool(res)
                            if ok:
                                st.session_state.db.invalidar_cache()
                                st.success("Valor atualizado!")
                                st.rerun()
                            else:
                                msg = res.get('message', 'Erro ao atualizar valor.') if isinstance(res, dict) else 'Erro ao atualizar valor.'
                                st.error(msg)
                        except Exception as e:
                            st.error(str(e))

            # Breakdown em cards
            breakdown = [
                ("Personal Organizer", valor_base, GOLD),
                (" Produtos",           total_prod, "#0F5E6E"),
                (" Fornecedores",       total_forn, "#0F5E6E"),
                (" Assistentes",        total_asst, "#6B4EAA"),
                (" Outros",             total_outr, "#E07B39"),
            ]
            rows_html = ""
            for label, val, cor in breakdown:
                if val > 0:
                    rows_html += f"""
                    <div style="display:flex;justify-content:space-between;padding:7px 12px;
                                border-left:3px solid {cor};background:#fff;border-radius:0 6px 6px 0;
                                margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.05);">
                      <span style="font-size:13px;color:#333;">{label}</span>
                      <span style="font-size:13px;font-weight:600;color:#1D6A4A;">{_fmt_brl(val)}</span>
                    </div>"""
            rows_html += f"""
                    <div style="display:flex;justify-content:space-between;padding:9px 12px;
                                background:{NAVY};border-radius:6px;margin-top:6px;">
                      <span style="font-size:13px;color:{GOLD};font-weight:700;">TOTAL GERAL</span>
                      <span style="font-size:14px;font-weight:700;color:#fff;">{_fmt_brl(total_geral)}</span>
                    </div>"""
            st.markdown(rows_html, unsafe_allow_html=True)

            # Gráfico de pizza
            if any(v > 0 for _, v, _ in breakdown):
                labels = [l for l, v, _ in breakdown if v > 0]
                values = [v for _, v, _ in breakdown if v > 0]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.35,
                                              textinfo='percent', hoverinfo='label+value')])
                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250,
                                  showlegend=True,
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.3))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar resumo: {str(e)}")

        st.markdown("---")
        with st.form(key=f"form_finalizar_concluida_{proposta_id}"):
            if st.form_submit_button("MARCAR COMO CONCLUÍDA", type="primary", use_container_width=True):
                try:
                    res = finalizar_proposta_v2(int(proposta_id))
                    if res.get('status', False):
                        st.success("Proposta finalizada com sucesso!")
                        st.session_state['kanban_selected_proposta'] = None
                        st.session_state.db.invalidar_cache()
                        st.rerun()
                    else:
                        st.error(f"Erro: {res.get('message', 'Desconhecido')}")
                except Exception as e:
                    st.error(str(e))

    # ── FINALIZADA ────────────────────────────────────────────────────────
    elif finalizada:
        st.markdown('<p style="color:#555;font-size:13px;margin-bottom:12px;">Gere os relatórios para esta proposta concluída.</p>', unsafe_allow_html=True)

        # Cards de relatório
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;">
          <div style="background:{NAVY};border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:22px;"></div>
            <div style="color:{GOLD};font-weight:700;font-size:12px;margin-top:4px;">RELATÓRIO CLIENTE</div>
            <div style="color:#aaa;font-size:10px;">Proposta de serviço</div>
          </div>
          <div style="background:{NAVY};border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:22px;"></div>
            <div style="color:{GOLD};font-weight:700;font-size:12px;margin-top:4px;">RELATÓRIO INTERNO</div>
            <div style="color:#aaa;font-size:10px;">Margens e custos</div>
          </div>
          <div style="background:{NAVY};border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:22px;"></div>
            <div style="color:{GOLD};font-weight:700;font-size:12px;margin-top:4px;">RELATÓRIO FORNECEDORES</div>
            <div style="color:#aaa;font-size:10px;">Lista de terceiros</div>
          </div>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            if botao_documento("Gerar para a cliente", use_container_width=True, key=f"btn_rel_cliente_{proposta_id}"):
                try:
                    st_gerar_pdf_cliente(proposta_id)
                except Exception as e:
                    st.error(str(e))
        with col2:
            if botao_documento("Gerar interno", use_container_width=True, key=f"btn_rel_interno_{proposta_id}"):
                try:
                    st_gerar_pdf_interno(proposta_id)
                except Exception as e:
                    st.error(str(e))
        with col3:
            if botao_documento("Gerar fornecedores", use_container_width=True, key=f"btn_rel_forn_{proposta_id}"):
                try:
                    st_gerar_pdf_fornecedores(proposta_id)
                except Exception as e:
                    st.error(str(e))

        with st.expander(" Reabrir Proposta Finalizada"):
            st.warning("Esta ação retornará a proposta para o status 'Em Execução'.")
            if botao_editar("Reabrir proposta", key=f"btn_reabrir_{proposta_id}", icon=":material/replay:", use_container_width=True):
                try:
                    from reabrir_proposta import reabrir_proposta_finalizada
                    res = reabrir_proposta_finalizada(proposta_id)
                    if res.get('status') in ['sucesso', 'sucesso_com_alerta']:
                        st.session_state.db.invalidar_cache()
                        st.success(res.get('mensagem'))
                        if res.get('status') == 'sucesso_com_alerta':
                            st.warning(res.get('alerta'))
                        st.session_state['kanban_selected_proposta'] = None
                        st.rerun()
                    else:
                        st.error(res.get('mensagem'))
                except Exception as e:
                    st.error(str(e))

    else:
        st.info(f"Status: {status_atual} / {status_execucao}")

    # ── Gerar PDF da proposta (sempre disponível) ─────────────────────────
    st.markdown("---")
    if botao_documento("Gerar PDF da proposta (cliente)", key=f"btn_pdf_proposta_{proposta_id}", use_container_width=True):
        try:
            sucesso, mensagem, arquivo = gerar_pdf_proposta(db=st.session_state.db, proposta_id=proposta_id)
            if sucesso and arquivo:
                with open(arquivo, "rb") as f:
                    st.success("PDF gerado!")
                    from utils.ui import baixar_pdf_pronto
                    baixar_pdf_pronto("Baixar Proposta", f.read(), os.path.basename(arquivo), f"proposta_{proposta_id}")
            else:
                st.error(f"Erro: {mensagem}")
        except Exception as e:
            st.error(str(e))

    # ── Excluir proposta ──────────────────────────────────────────────────
    with st.expander(" Excluir Proposta", expanded=False):
        st.warning("Esta ação é **permanente** e removerá todos os dados relacionados.")
        confirmar_exclusao = st.checkbox("Entendo que esta ação não pode ser desfeita", key=f"confirmar_exclusao_{proposta_id}")
        if confirmar_exclusao:
            col1, col2 = st.columns(2)
            with col1:
                if botao_excluir("EXCLUIR PROPOSTA", f"btn_excluir_kanban_{proposta_id}"):
                    try:
                        usuario_id = st.session_state.get('usuario_id')
                        sucesso, mensagem = st.session_state.db.excluir_proposta_segura(proposta_id, usuario_id)
                        if sucesso:
                            st.session_state.db.invalidar_cache()
                            st.success(mensagem)
                            st.session_state['kanban_selected_proposta'] = None
                            st.rerun()
                        else:
                            st.error(mensagem)
                    except Exception as e:
                        st.error(str(e))
            with col2:
                if st.button("Cancelar", key=f"btn_cancel_excl_{proposta_id}", type="primary", use_container_width=True):
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Lista (protótipo "propostasB"): cabeçalho, 4 cartões de resumo, quadro em 4 colunas e histórico
# ══════════════════════════════════════════════════════════════════════════════

COLUNAS = [("em_aberto", "Em aberto"), ("aprovada", "Aprovada"), ("em_execucao", "Em execução"),
           ("finalizada", "Concluída")]
COR_COLUNA = {"em_aberto": "#E5D08F", "aprovada": "#C9A84C", "em_execucao": "#0D1B2A", "finalizada": "#2F6B4F"}
BARRA_RESUMO = {"em_aberto": "#EFE3BE", "aprovada": "#C9A84C", "em_execucao": "#0D1B2A", "finalizada": "#2F6B4F"}
MAX_CONCLUIDAS = 3
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]
MSG_LEMBRETE = ("Oi, {nome}! Tudo bem? Passando para saber se ficou alguma dúvida sobre a proposta de organização "
                "que te enviei. Fico à disposição!")


def _css_wa():
    """Símbolo do WhatsApp nos botões que abrem a conversa (containers com chave "wa_...")."""
    import urllib.parse as _up
    svg = icone_whatsapp(16).replace('style="flex:none"', '').replace(' aria-hidden="true"', '')
    if 'xmlns' not in svg:
        svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    uri = "data:image/svg+xml;utf8," + _up.quote(svg)
    return ('[class*="st-key-wa_"] a::before { content:""; flex:none; width:16px; height:16px; margin-right:7px; '
            f'background:url("{uri}") center/16px 16px no-repeat; }}'
            '[class*="st-key-wa_"] a { display:inline-flex !important; align-items:center; justify-content:center; }'
            '[class*="st-key-wa_"] a > div { flex:0 0 auto !important; width:auto !important; }')


CSS_QUADRO = """
<style>
.pq-ey { font-size:.74rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#9C7A22; margin:0 0 4px; }
h1.pq-tit { margin:0 !important; padding:0 !important; font-family:'Cormorant Garamond',Georgia,serif !important;
            font-size:2.6rem !important; font-weight:600 !important; color:var(--navy) !important; line-height:1.15 !important; }
h1.pq-tit::after { content:""; display:block; width:40px; height:3px; border-radius:2px; background:var(--gold); margin-top:8px; }
.pq-sub { color:#5B6B80; font-size:.98rem; margin:10px 0 4px; }
.st-key-cta_pq_nova { padding-top:62px; }
.st-key-cta_pq_nova .stButton > button { min-height:46px; }
.pq-kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:18px 0 22px; }
.pq-kpi { min-width:0; }
.pq-kpi i { display:block; height:6px; border-radius:3px; margin-bottom:10px; }
.pq-kpi div { background:#fff; border:1px solid #E7E2D6; border-radius:16px; padding:16px 18px; }
.pq-kpi b { display:block; font-size:1.55rem; font-weight:700; color:var(--navy); margin:8px 0 2px; font-variant-numeric:tabular-nums;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.pq-kpi span.q { font-size:.82rem; color:#5B6B80; }
[class*="st-key-pqcol_"] { background:#EFEBE2; border-radius:16px; padding:12px 12px 6px; min-height:420px; gap:10px !important; }
.pq-colh { display:flex; justify-content:space-between; align-items:center; font-size:.9rem; font-weight:700; color:var(--navy);
           padding:2px 4px 2px; }
.pq-colh .pv-pil { min-width:24px; justify-content:center; }
[class*="st-key-pqc_"] { background:#fff; border:1px solid #E7E2D6; border-left:4px solid var(--c, #E7E2D6);
           border-radius:12px; padding:12px 14px 10px; gap:4px !important; }
[class*="st-key-pqr_"] { min-height:30px; }
[class*="st-key-pqc_"]:hover { box-shadow:0 2px 8px rgba(16,24,40,.08); }
.pq-card { cursor:pointer; padding-bottom:12px; }
.pq-card b { display:block; color:var(--navy); margin-top:8px; font-size:.98rem; overflow-wrap:anywhere; }
.pq-card .s { display:block; font-size:.8rem; color:#5B6B80; overflow-wrap:anywhere; margin-top:1px; }
[class*="st-key-pqr_"] [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:nowrap !important;
       align-items:center; gap:6px !important; }
[class*="st-key-pqr_"] [data-testid="stColumn"] { min-width:0 !important; width:auto !important; }
.pq-val { line-height:30px; font-weight:700; color:var(--navy); font-size:.9rem; white-space:nowrap; font-variant-numeric:tabular-nums; }
.pq-pago { line-height:30px; text-align:right; font-size:.8rem; color:#5B6B80; }
[class*="pqa_"] .stButton, [class*="pqa_"] .stLinkButton { display:flex; justify-content:flex-end; }
[class*="pqa_"] button, [class*="pqa_"] a { background:transparent !important; border:0 !important; width:auto !important;
       padding:0 !important; min-height:28px !important; box-shadow:none !important; white-space:nowrap; }
[class*="pqa_"] button p, [class*="pqa_"] a p, [class*="pqa_"] [data-testid="stIconMaterial"] {
       color:#9C7A22 !important; font-weight:700 !important; font-size:.82rem !important; white-space:nowrap; }
[class*="pqa_"] button:hover p, [class*="pqa_"] a:hover p { color:var(--navy) !important; }
[class*="st-key-wa_pqa_"] a::before { width:14px !important; height:14px !important; background-size:14px 14px !important; margin-right:5px !important; }
.pq-vazio { font-size:.84rem; color:#5B6B80; padding:6px 4px; }
.pq-mais a, .pq-mais { font-size:.82rem; color:#9C7A22 !important; font-weight:600; text-decoration:none !important; padding:2px 4px; }
.pq-mais a:hover { color:var(--navy) !important; }
.pq-nota { font-size:.84rem; color:#5B6B80; margin-top:12px; }
.pq-secao { font-size:.74rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#4A5B73; margin:28px 0 10px; }
.pq-h { display:grid; grid-template-columns:52px minmax(0,1.6fr) minmax(0,1.2fr) 110px 120px 112px 64px; gap:10px;
        align-items:center; font-size:.88rem; color:#1A202C; background:#fff; border:1px solid #E7E2D6; border-radius:12px;
        padding:10px 14px; }
.pq-h .n { color:#5B6B80; font-variant-numeric:tabular-nums; }
.pq-h b { color:var(--navy); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pq-h .t { color:#5B6B80; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pq-h .v { text-align:right; font-weight:700; color:var(--navy); font-variant-numeric:tabular-nums; white-space:nowrap; }
.pq-h .rl { text-align:right; color:#2F6B4F; font-variant-numeric:tabular-nums; white-space:nowrap; font-size:.82rem; }
.pq-h .d { text-align:right; color:#5B6B80; font-variant-numeric:tabular-nums; }
.pq-h.re { background:#F7F7F5; color:#98A2B3; }
.pq-h.re b, .pq-h.re .v { color:#98A2B3; }
.pq-h.cab { background:transparent; border:0; padding:2px 14px; font-size:.72rem; font-weight:700; letter-spacing:.08em;
            text-transform:uppercase; color:#5B6B80; }
[class*="st-key-kcard_pqh_"] { margin-bottom:-6px; }
[class*="st-key-kcard_pqh_"]:hover .pq-h { border-color:#C9A84C; }
@media (max-width: 1280px) {
  .st-key-pq_cols > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] { flex-direction:row !important; flex-wrap:wrap !important; row-gap:14px !important; }
  .st-key-pq_cols > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:1 1 calc(50% - 8px) !important; width:calc(50% - 8px) !important; min-width:0 !important; }
  [class*="st-key-pqcol_"] { min-height:0; }
  .pq-kpis { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
@media (max-width: 900px) {
  .pq-h { grid-template-columns:44px minmax(0,1fr) 96px 64px; }
  .pq-h .t, .pq-h .rl, .pq-h .s { display:none; }
}
@media (max-width: 640px) {
  .st-key-pq_cols > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:1 1 100% !important; width:100% !important; }
  .st-key-pq_cab [data-testid="stHorizontalBlock"] { flex-direction:column !important; }
  .st-key-cta_pq_nova { padding-top:0; }
  h1.pq-tit { font-size:2.1rem !important; }
  .pq-kpi b { font-size:1.25rem; }
  .pq-kpi div { padding:12px 14px; }
  .pq-h { grid-template-columns:minmax(0,1fr) 90px 56px; }
  .pq-h .n { display:none; }
}
</style>
"""


def _situacoes(df):
    """Coluna de cada proposta (mesmas regras de antes: em execução pelo status ou pelo status_execucao)."""
    from utils.proposta_status import normalize as _normalize_status
    if df.empty:
        return pd.Series(dtype=str)
    st_ = df['status'].apply(lambda s: _normalize_status(str(s or '')) or '')
    if 'status_execucao' in df.columns:
        exec_ = (df['status_execucao'] == EXEC_EM_EXECUCAO) & ~st_.isin(['finalizada', 'recusada'])
        st_ = st_.where(~exec_, 'em_execucao')
    return st_


def _data_fim_ou(p):
    from utils.propostas_dados import _data
    return _data(p.get('data_fim')) or _data(p.get('data_inicio')) or _data(p.get('data_proposta'))


def _contexto(p, situacao, marcas):
    """'Closet e Quarto · enviada há 4 dias', '· sinal recebido', '· dia 1 de 2', '· 20/11'."""
    from utils import propostas_dados as dados
    serv = dados.servico_curto(p)
    if situacao == 'em_aberto':
        sit, d = dados.envio(p, marcas)
        extra = "rascunho" if sit == "rascunho" else (f"enviada {dados.quando(d)}" if d else "enviada")
    elif situacao == 'aprovada':
        ini = dados._data(p.get('data_inicio'))
        if _safe_float(p.get('sinal')) > 0:
            extra = "sinal recebido"
        elif ini:
            extra = f"marcada para {_dm(ini)}"
        else:
            extra = "aguardando data"
    elif situacao == 'em_execucao':
        dia = dados.dia_do_servico(p)
        extra = f"dia {dia[0]} de {dia[1]}" if dia else "em andamento"
    else:
        extra = _dm(_data_fim_ou(p))
    return f"{serv} · {extra}" if extra else serv


def _abrir(pid):
    atual = st.session_state.get('kanban_selected_proposta')
    st.session_state['kanban_selected_proposta'] = None if atual == pid else pid


def _cartao(p, situacao, marcas, telefones):
    from utils import propostas_dados as dados
    from utils.nova_proposta import link_whatsapp, mensagem_whatsapp
    pid = int(p['id'])
    nome = str(p.get('nome') or p.get('cliente_nome') or 'Cliente')
    valor = _safe_float(p.get('valor'))
    with st.container(key=f"pqc_{situacao}_{pid}"):
        html = (f'<div class="pq-card">{pilula(situacao)}<b>{esc(nome)}</b>'
                f'<span class="s">{esc(_contexto(p, situacao, marcas))}</span></div>')
        if cartao_clicavel(html, key=f"pq_{pid}", rotulo=f"Abrir proposta de {nome}"):
            _abrir(pid)
            st.rerun(scope="fragment")
        with st.container(key=f"pqr_{pid}"):
            c1, c2 = st.columns([1, 1], vertical_alignment="center")
            c1.markdown(f'<div class="pq-val">{_fmt_brl(valor).replace(",00", "")}</div>', unsafe_allow_html=True)
            with c2:
                tel = telefones.get(int(_safe_float(p.get('cliente_id'), -1)))
                if situacao == 'em_aberto':
                    sit, _ = dados.envio(p, marcas)
                    primeiro = nome.split(' ')[0]
                    if sit == "rascunho":
                        url = link_whatsapp(tel, mensagem_whatsapp(nome, p.get('tipo_proposta'), valor))
                        rot, marca, texto = "Enviar", "Enviada", "Enviada pelo WhatsApp"
                    else:
                        url = link_whatsapp(tel, MSG_LEMBRETE.format(nome=primeiro))
                        rot, marca, texto = "Lembrar", "Lembrete", "Lembrete pelo WhatsApp"
                    with st.container(key=f"wa_pqa_{pid}"):
                        st.link_button(rot, url, key=f"pq_wa_{pid}", icon=":material/arrow_forward:",
                                       icon_position="right", on_click=_marcar_cb, args=(pid, marca, texto),
                                       help="Abre o WhatsApp com a mensagem pronta")
                elif situacao == 'aprovada':
                    with st.container(key=f"pqa_i_{pid}"):
                        if st.button("Iniciar", key=f"pq_ini_{pid}", icon=":material/arrow_forward:",
                                     icon_position="right", help="Passa para Em execução"):
                            _iniciar_execucao(pid, p)
                elif situacao == 'em_execucao':
                    with st.container(key=f"pqa_f_{pid}"):
                        if st.button("Finalizar", key=f"pq_fim_{pid}", icon=":material/arrow_forward:",
                                     icon_position="right", help="Conclui o serviço e lança o financeiro e a pós-organização"):
                            _confirmar_finalizar(pid)
                elif str(p.get('status_pagamento_base') or '') == 'Pago':
                    st.markdown('<div class="pq-pago">pago</div>', unsafe_allow_html=True)


@st.fragment
def _kanban_board_fragment(grupos, total_concluidas, telefones, propostas_com_clientes):
    """Quadro (4 colunas) + gaveta de detalhe, num fragmento: abrir e fechar o detalhe não redesenha os
    resumos nem o histórico. Mudanças de situação (aprovar, iniciar, finalizar...) fazem o rerun completo.
    As marcas de envio são lidas aqui dentro: o "Enviar" do cartão roda só o fragmento."""
    from utils import propostas_dados
    marcas = propostas_dados.historicos(st.session_state.db)
    st.markdown(f"<style>[class*='st-key-pqc_'] {{}}"
                + "".join(f"[class*='st-key-pqc_{k}_'] {{ --c:{c}; }}" for k, c in COR_COLUNA.items())
                + "</style>", unsafe_allow_html=True)
    with st.container(key="pq_cols"):
        cols = st.columns(4, gap="small")
    for col, (sit, rotulo) in zip(cols, COLUNAS):
        df = grupos.get(sit, pd.DataFrame())
        n = total_concluidas if sit == 'finalizada' else len(df)
        with col, st.container(key=f"pqcol_{sit}"):
            cls = {"em_aberto": "ab", "aprovada": "ap", "em_execucao": "ex", "finalizada": "co"}[sit]
            st.markdown(f'<div class="pq-colh"><span>{rotulo}</span><span class="pv-pil {cls}">{n}</span></div>',
                        unsafe_allow_html=True)
            if df.empty:
                st.markdown('<div class="pq-vazio">Nenhuma proposta aqui.</div>', unsafe_allow_html=True)
            for _, p in df.iterrows():
                _cartao(p, sit, marcas.get(int(p['id']), []), telefones)
            if sit == 'finalizada' and total_concluidas > len(df):
                st.markdown(f'<div class="pq-mais"><a href="#historico-propostas">Ver todas as {total_concluidas} no '
                            f'histórico →</a></div>', unsafe_allow_html=True)

    selected_id = st.session_state.get('kanban_selected_proposta')
    if selected_id is None:
        return
    linhas = propostas_com_clientes[propostas_com_clientes['id'] == selected_id] if not propostas_com_clientes.empty else []
    if len(linhas) == 0:
        st.session_state['kanban_selected_proposta'] = None
        return
    proposta_row = linhas.iloc[0]

    @st.dialog(f"Proposta nº {_num_proposta(proposta_row, selected_id)}", width="large", position="right",
               on_dismiss=_fechar_detalhe)
    def _modal_detalhes():
        _render_detail_panel(selected_id, proposta_row, propostas_com_clientes)

    _modal_detalhes()


def _resumos_html(grupos, concl_mes, hoje_):
    def soma(df):
        return float(df['valor'].apply(_safe_float).sum()) if not df.empty else 0.0

    def qtd(n):
        return f"{n} proposta{'s' if n != 1 else ''}"
    itens = []
    for sit, _ in COLUNAS:
        if sit == 'finalizada':
            v, q = soma(concl_mes), f"{len(concl_mes)} em {MESES[hoje_.month - 1]}"
        else:
            df = grupos.get(sit, pd.DataFrame())
            v, q = soma(df), qtd(len(df))
        itens.append(f'<div class="pq-kpi"><i style="background:{BARRA_RESUMO[sit]}"></i><div>{pilula(sit)}'
                     f'<b>{_fmt_brl(v).replace(",00", "")}</b><span class="q">{q}</span></div></div>')
    return '<div class="pq-kpis">' + "".join(itens) + '</div>'


def _historico(hist):
    """Concluídas e recusadas (recusadas em cinza), com busca e período; clicar abre o detalhe."""
    st.markdown('<div id="historico-propostas"></div><div class="pq-secao">Histórico</div>', unsafe_allow_html=True)
    if hist.empty:
        st.markdown('<div class="pq-vazio">As propostas concluídas e recusadas aparecem aqui.</div>',
                    unsafe_allow_html=True)
        return
    with st.expander(f"{len(hist)} proposta{'s' if len(hist) != 1 else ''} concluídas e recusadas",
                     expanded=bool(st.session_state.get('pq_hist_aberto', True))):
        hist_c1, hist_c2 = st.columns([2, 1])
        with hist_c1:
            busca_cliente = st.text_input("Buscar por cliente", key="hist_busca_cliente", placeholder="Nome da cliente...")
        with hist_c2:
            meses_opcoes = ["Todos"]
            datas_validas = pd.to_datetime(hist['_fim'], errors='coerce').dropna()
            for m in sorted(datas_validas.dt.to_period('M').unique(), reverse=True):
                if m.strftime('%m/%Y') not in meses_opcoes:
                    meses_opcoes.append(m.strftime('%m/%Y'))
            filtro_mes = st.selectbox("Período", meses_opcoes, key="hist_filtro_mes")
        hist_df = hist
        if busca_cliente:
            hist_df = hist_df[hist_df['nome'].astype(str).str.lower().str.contains(busca_cliente.lower(), regex=False)]
        if filtro_mes != "Todos":
            mes_num, ano_num = filtro_mes.split('/')
            d = pd.to_datetime(hist_df['_fim'], errors='coerce')
            hist_df = hist_df[(d.dt.month == int(mes_num)) & (d.dt.year == int(ano_num))]
        if hist_df.empty:
            st.info("Nenhuma proposta encontrada com os filtros selecionados.")
            return
        from utils.propostas_helper import (calcular_receita_liquida, _construir_catalogo_produtos,
                                            _construir_fornecedores_comissao)
        _catalogo_hist = _construir_catalogo_produtos(st.session_state.db)
        _fornecedores_hist = _construir_fornecedores_comissao(st.session_state.db)
        st.markdown('<div class="pq-h cab"><span class="n">Nº</span><span>Cliente</span><span class="t">Serviço</span>'
                    '<span class="v">Valor</span><span class="rl">Receita líquida</span><span class="s">Situação</span>'
                    '<span class="d">Data</span></div>', unsafe_allow_html=True)
        for _, prop in hist_df.iterrows():
            h_pid = int(prop['id'])
            sit = prop['_sit']
            try:
                h_receita = float(calcular_receita_liquida(
                    st.session_state.db, h_pid, proposta=prop.to_dict(), catalogo=_catalogo_hist,
                    fornecedores_cadastro=_fornecedores_hist).get('receita_liquida', 0.0)) if sit == 'finalizada' else 0.0
            except Exception:
                h_receita = 0.0
            from utils.propostas_dados import servico_curto
            html = (f'<div class="pq-h{" re" if sit == "recusada" else ""}"><span class="n">{esc(_num_proposta(prop, h_pid))}</span>'
                    f'<b>{esc(prop.get("nome") or prop.get("cliente_nome") or "Cliente")}</b>'
                    f'<span class="t">{esc(servico_curto(prop))}</span>'
                    f'<span class="v">{_fmt_brl(_safe_float(prop.get("valor")))}</span>'
                    f'<span class="rl">{_fmt_brl(h_receita) if sit == "finalizada" else "–"}</span>'
                    f'<span class="s">{pilula(sit)}</span><span class="d">{_dm(prop["_fim"]) if prop["_fim"] else "–"}</span></div>')
            if cartao_clicavel(html, key=f"pqh_{h_pid}", rotulo=f"Abrir proposta {h_pid}"):
                st.session_state['kanban_selected_proposta'] = h_pid
                st.rerun()


def _decidir_entrada():
    """Outras telas abrem a Nova proposta (kanban_nova_proposta_open) ou uma proposta (kanban_selected_proposta).
    Ao chegar de outra tela, vale o pedido mais novo: uma Nova proposta largada no meio não esconde a proposta
    que a Agenda mandou abrir, e um detalhe que ficou aberto não esconde a Nova proposta."""
    ss = st.session_state
    visto = ss.get('_pq_visto') or {}
    entrou = ss.get('_last_page_rendered') != "Propostas"
    sel, aberta = ss.get('kanban_selected_proposta'), bool(ss.get('kanban_nova_proposta_open'))
    if entrou and not ss.get('nova_proposta_prefill') and not ss.get('nova_proposta_cliente_id'):
        novo_sel = sel is not None and sel != visto.get('sel')
        nova_ab = aberta and not visto.get('aberta')
        if novo_sel:
            ss['kanban_nova_proposta_open'] = False
        elif nova_ab:
            ss['kanban_selected_proposta'] = None
    elif ss.get('nova_proposta_prefill') or ss.get('nova_proposta_cliente_id'):
        ss['kanban_selected_proposta'] = None


def _lembrar_entrada():
    st.session_state['_pq_visto'] = {'sel': st.session_state.get('kanban_selected_proposta'),
                                     'aberta': bool(st.session_state.get('kanban_nova_proposta_open'))}


def show():
    from utils.auth_guard import require_auth
    require_auth()

    if not hasattr(st.session_state, 'db'):
        st.error("Erro: Conexão com banco de dados não disponível")
        return

    if 'kanban_selected_proposta' not in st.session_state:
        st.session_state['kanban_selected_proposta'] = None
    if 'kanban_nova_proposta_open' not in st.session_state:
        st.session_state['kanban_nova_proposta_open'] = False

    st.markdown("<style>" + CSS_PILULA + _css_wa() + "</style>", unsafe_allow_html=True)

    from utils import nova_proposta
    _decidir_entrada()
    if nova_proposta.preparar():
        _lembrar_entrada()
        nova_proposta.mostrar()
        return
    _lembrar_entrada()

    st.markdown(CSS_QUADRO, unsafe_allow_html=True)
    if st.session_state.pop('proposta_finalizada_sucesso', False):
        st.success("Proposta finalizada! O financeiro e a pós-organização já foram lançados.")
    aviso = st.session_state.pop('_prop_aviso', None)
    if aviso:
        st.warning(aviso)

    # ── cabeçalho ────────────────────────────────────────────────────────
    with st.container(key="pq_cab"):
        c_tit, c_btn = st.columns([4, 1.3], vertical_alignment="top")
        c_tit.markdown('<div class="pq-ey">Do primeiro contato ao serviço feito</div><h1 class="pq-tit">Propostas</h1>'
                       '<div class="pq-sub">Monte, envie e acompanhe cada proposta até virar serviço.</div>',
                       unsafe_allow_html=True)
        with c_btn, st.container(key="cta_pq_nova"):
            if st.button("Nova proposta", icon=":material/add:", key="btn_nova_proposta_top", use_container_width=True):
                st.session_state['kanban_selected_proposta'] = None
                nova_proposta.iniciar()
                st.rerun()

    # ── dados ────────────────────────────────────────────────────────────
    try:
        propostas = st.session_state.db.get_propostas()
        clientes = st.session_state.db.get_clientes()
        for col in ['valor', 'previsao_dias', 'id', 'numero', 'cliente_id']:
            if col in propostas.columns:
                propostas[col] = pd.to_numeric(propostas[col], errors='coerce')
        if not propostas.empty and not clientes.empty:
            propostas_com_clientes = propostas.merge(clientes[['id', 'nome']], left_on='cliente_id', right_on='id',
                                                     suffixes=('', '_cliente'), how='left')
        else:
            propostas_com_clientes = propostas.copy() if not propostas.empty else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados iniciais: {str(e)}")
        return

    if not propostas_com_clientes.empty and 'nome' not in propostas_com_clientes.columns:
        propostas_com_clientes['nome'] = propostas_com_clientes.get('cliente_nome', 'Cliente')
    telefones = {}
    if not clientes.empty and 'telefone' in clientes.columns:
        telefones = {int(r['id']): r.get('telefone') for _, r in clientes.iterrows()}

    hoje_ = hoje()
    grupos, hist, concl_mes, total_concl = {}, pd.DataFrame(), pd.DataFrame(), 0
    if not propostas_com_clientes.empty:
        df = propostas_com_clientes.copy()
        df['_sit'] = _situacoes(df)
        df['_fim'] = df.apply(_data_fim_ou, axis=1)
        for sit in ('em_aberto', 'aprovada', 'em_execucao'):
            g = df[df['_sit'] == sit]
            ordem = 'data_proposta' if sit == 'em_aberto' else 'data_inicio'
            if ordem in g.columns:
                g = g.sort_values(ordem, ascending=sit != 'em_aberto', na_position='last')
            grupos[sit] = g
        concl = df[df['_sit'] == 'finalizada'].sort_values('_fim', ascending=False, na_position='last')
        total_concl = len(concl)
        grupos['finalizada'] = concl.head(MAX_CONCLUIDAS)
        concl_mes = concl[concl['_fim'].apply(lambda d: bool(d) and d.year == hoje_.year and d.month == hoje_.month)]
        hist = df[df['_sit'].isin(['finalizada', 'recusada'])].sort_values('_fim', ascending=False, na_position='last')

    st.markdown(_resumos_html(grupos, concl_mes, hoje_), unsafe_allow_html=True)

    _kanban_board_fragment(grupos, total_concl, telefones, propostas_com_clientes)
    st.markdown('<div class="pq-nota">Recusadas ficam no histórico, em cinza.</div>', unsafe_allow_html=True)
    _historico(hist)


if __name__ == "__main__":
    show()
