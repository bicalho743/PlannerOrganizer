import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date

# Links de checkout do Stripe (mesmos usados no app mobile)
STRIPE_CHECKOUT_MENSAL = "https://buy.stripe.com/4gMcN5dQC9vX6yVfQO18c01"
STRIPE_CHECKOUT_ANUAL = "https://buy.stripe.com/8x26oHaEqbE5g9vbAy18c00"
STRIPE_PORTAL_RETURN_URL = "https://plannerorganiza.com.br"

# Link direto do Portal do Cliente (login por e-mail). Configurável por env
# para ajuste sem redeploy — o valor abaixo veio do painel do Stripe.
STRIPE_PORTAL_LINK = os.environ.get(
    "STRIPE_PORTAL_LINK",
    "https://billing.stripe.com/p/login/8x26oHaEqbE5g9vbAy18c00",
)


def _is_pro(perfil):
    """Mesma regra do app mobile: pro/ativo/admin contam como plano ativo."""
    plano = (perfil.get('plano') or 'gratuito').lower()
    role = (perfil.get('role') or '').lower()
    return plano in ('pro', 'ativo', 'admin') or role == 'admin'


def _dias_restantes_trial(perfil):
    """Dias restantes do trial de 7 dias, com base na data de cadastro."""
    dc = perfil.get('data_cadastro')
    if isinstance(dc, str):
        try:
            dc = datetime.fromisoformat(dc[:10]).date()
        except Exception:
            dc = date.today()
    elif isinstance(dc, datetime):
        dc = dc.date()
    elif not isinstance(dc, date):
        dc = date.today()
    dias_passados = (date.today() - dc).days
    return max(0, 7 - dias_passados)


def _render_plano_badge(perfil):
    """Exibe o selo do plano no topo do perfil (paridade visual com o app)."""
    if _is_pro(perfil):
        st.markdown(
            '<div style="display:inline-block;background:#C9A84C;color:#0D1B2A;'
            'padding:6px 18px;border-radius:20px;font-weight:700;font-size:0.95rem;'
            'margin-bottom:1rem;">⭐ Plano Pro</div>',
            unsafe_allow_html=True,
        )
    else:
        dias = _dias_restantes_trial(perfil)
        if dias > 0:
            plural = 's' if dias != 1 else ''
            st.markdown(
                f'<div style="display:inline-block;background:#1E3A5F;color:#C9A84C;'
                f'padding:6px 18px;border-radius:20px;font-weight:700;font-size:0.95rem;'
                f'margin-bottom:1rem;">🕐 Trial — {dias} dia{plural} restante{plural}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="display:inline-block;background:#C0392B;color:#fff;'
                'padding:6px 18px;border-radius:20px;font-weight:700;font-size:0.95rem;'
                'margin-bottom:1rem;">⚠️ Trial expirado</div>',
                unsafe_allow_html=True,
            )


def _criar_portal_session(email):
    """
    Cria uma sessão do Portal do Cliente Stripe para o e-mail informado.
    Retorna (url, erro). A URL abre a página onde o cliente gerencia a
    assinatura, cartão e faturas.
    """
    secret = os.environ.get("STRIPE_SECRET_KEY", "")
    if not secret:
        return None, "STRIPE_SECRET_KEY não configurada no servidor."
    if not email:
        return None, "E-mail do usuário não disponível."
    try:
        import stripe
        stripe.api_key = secret
        clientes = stripe.Customer.list(email=email, limit=1)
        if not clientes.data:
            return None, "sem_assinatura"
        session = stripe.billing_portal.Session.create(
            customer=clientes.data[0].id,
            return_url=STRIPE_PORTAL_RETURN_URL,
        )
        return session.url, None
    except Exception as e:
        return None, str(e)

def carregar_perfil(user_id):
    """
    Carrega os dados do perfil do usuário do banco de dados (com fallback para arquivo JSON)
    
    Args:
        user_id: ID ou email do usuário
        
    Returns:
        dict: Dados do perfil ou dicionário vazio se não existir
    """
    try:
        from utils.database import Database
        
        # Tentar carregar do banco de dados primeiro
        if 'db' in st.session_state:
            db = st.session_state.db
        else:
            db = Database()
        
        perfil_bd = db.get_perfil_usuario()
        
        if perfil_bd:
            # Converter dados do banco para o formato esperado
            return {
                'nome': perfil_bd.get('nome', ''),
                'email': perfil_bd.get('email', ''),
                'telefone': perfil_bd.get('telefone', ''),
                'empresa': perfil_bd.get('empresa', ''),
                'instagram': perfil_bd.get('instagram', ''),
                'website': perfil_bd.get('website', ''),
                'cargo': perfil_bd.get('cargo', ''),
                'cor_principal': perfil_bd.get('cor_principal', ''),
                'cor_secundaria': perfil_bd.get('cor_secundaria', ''),
                'observacoes_relatorio': perfil_bd.get('observacoes_relatorio', ''),
                'plano': perfil_bd.get('plano', ''),
                'role': perfil_bd.get('role', ''),
                'ativo': perfil_bd.get('ativo'),
                'data_cadastro': perfil_bd.get('data_cadastro'),
                'ultima_atualizacao': perfil_bd.get('ultimo_login', '').strftime("%d/%m/%Y %H:%M:%S") if perfil_bd.get('ultimo_login') else ''
            }
    except Exception as e:
        print(f"Erro ao carregar perfil do banco: {str(e)}")
    
    # Fallback para arquivo JSON se banco falhar
    user_id_normalizado = user_id.replace('@', '_at_').replace('.', '_dot_')
    perfil_path = f"data/perfis/{user_id_normalizado}.json"
    
    if os.path.exists(perfil_path):
        try:
            with open(perfil_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar perfil: {str(e)}")
            return {}
    else:
        return {}

def salvar_perfil(user_id, dados_perfil):
    """
    Salva os dados do perfil do usuário no banco de dados
    
    Args:
        user_id: ID ou email do usuário
        dados_perfil: Dicionário com os dados do perfil
        
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    try:
        from utils.database import Database
        
        # Usar o sistema de banco de dados
        if 'db' in st.session_state:
            db = st.session_state.db
        else:
            db = Database()
        
        # Tentar salvar no banco de dados primeiro
        success = db.salvar_perfil_usuario(dados_perfil)
        
        if success:
            # Manter backup em arquivo JSON como fallback
            user_id_normalizado = user_id.replace('@', '_at_').replace('.', '_dot_')
            os.makedirs("data/perfis", exist_ok=True)
            perfil_path = f"data/perfis/{user_id_normalizado}.json"
            dados_perfil['ultima_atualizacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with open(perfil_path, 'w', encoding='utf-8') as f:
                json.dump(dados_perfil, f, ensure_ascii=False, indent=4)
        
        return success
        
    except Exception as e:
        # Fallback para arquivo JSON se banco falhar
        try:
            user_id_normalizado = user_id.replace('@', '_at_').replace('.', '_dot_')
            os.makedirs("data/perfis", exist_ok=True)
            perfil_path = f"data/perfis/{user_id_normalizado}.json"
            dados_perfil['ultima_atualizacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with open(perfil_path, 'w', encoding='utf-8') as f:
                json.dump(dados_perfil, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e2:
            st.error(f"Erro ao salvar perfil: {str(e)} | Fallback: {str(e2)}")
            return False

def show():
    """
    Exibe a página de perfil do usuário
    """
    from utils.auth_guard import require_auth
    require_auth()
    st.markdown('<h1 style="font-size: 2rem; font-weight: 600; margin-top: 0; padding-top: 0; margin-bottom: 1rem;">Perfil do Usuário</h1>', unsafe_allow_html=True)
    
    # Verificar se o usuário está logado
    print(f"Verificando estado da autenticação no perfil: {st.session_state.keys()}")
    if "authenticated" in st.session_state:
        print(f"Estado de autenticação: {st.session_state.authenticated}")
    
    if "usuario" in st.session_state:
        print(f"Dados do usuário na sessão: {st.session_state.usuario}")
    else:
        print("Dados do usuário na sessão: Não encontrado")
        
    if "user" in st.session_state:
        print(f"Objeto 'user' na sessão: {type(st.session_state.user)}")
    
    # Verificar se o usuário está autenticado
    if "authenticated" in st.session_state and st.session_state.authenticated:
        # Se apenas o objeto 'user' existe mas não 'usuario'
        if "user" in st.session_state and "usuario" not in st.session_state:
            # Criar objeto 'usuario' com dados mínimos
            if isinstance(st.session_state.user, dict) and 'email' in st.session_state.user:
                email = st.session_state.user.get('email')
                st.session_state.usuario = {
                    'email': email,
                    'nome': email.split('@')[0].title(),
                    'role': 'user'
                }
                print(f"Criado objeto 'usuario' a partir de 'user': {st.session_state.usuario}")
    
    # Verificação principal
    if "usuario" not in st.session_state or not st.session_state.usuario:
        st.warning("Você precisa estar logado para acessar seu perfil.")
        # Verificar login admin como fallback
        if "authenticated" in st.session_state and st.session_state.authenticated:
            st.info("Você está autenticado, mas seus dados de usuário não estão disponíveis. Tente fazer login novamente.")
        return
    
    # Obter dados do usuário atual
    usuario = st.session_state.usuario
    user_id = usuario.get('email', 'usuario_desconhecido')
    
    # Carregar perfil existente
    perfil = carregar_perfil(user_id)

    # Selo do plano (paridade visual com o app mobile)
    _render_plano_badge(perfil)

    # Exibir formulário de perfil
    with st.form("form_perfil", clear_on_submit=False):
        st.subheader("Dados Pessoais")
        
        # Seção de dados pessoais
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo", 
                                value=perfil.get('nome', usuario.get('nome', '')))
            
            telefone = st.text_input("Telefone", 
                                    value=perfil.get('telefone', usuario.get('telefone', '')),
                                    help="Formato: (XX) XXXXX-XXXX")
        
        with col2:
            email = st.text_input("Email", 
                                value=perfil.get('email', usuario.get('email', '')), 
                                disabled=True,
                                help="O email não pode ser alterado pois é usado para autenticação")
            
            instagram = st.text_input("Instagram", 
                                    value=perfil.get('instagram', ''),
                                    help="Seu perfil do Instagram (sem @)")
        
        st.subheader("Dados Profissionais")
        
        # Seção de dados da empresa
        col1, col2 = st.columns(2)
        
        with col1:
            empresa = st.text_input("Nome da Empresa/Negócio", 
                                   value=perfil.get('empresa', usuario.get('empresa', '')))
            
            website = st.text_input("Website", 
                                   value=perfil.get('website', 'www.plannerorganizer.com.br'),
                                   help="Seu site ou landing page")
        
        with col2:
            cargo = st.text_input("Cargo/Função", 
                                 value=perfil.get('cargo', 'Personal Organizer'))
            
            cnpj = st.text_input("CNPJ (se houver)", 
                                value=perfil.get('cnpj', ''),
                                help="Formato: XX.XXX.XXX/XXXX-XX")
        
        # Endereço
        st.subheader("Endereço Profissional")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            endereco = st.text_input("Endereço", 
                                    value=perfil.get('endereco', ''))
        
        with col2:
            numero = st.text_input("Número", 
                                 value=perfil.get('numero', ''))
        
        with col3:
            complemento = st.text_input("Complemento", 
                                      value=perfil.get('complemento', ''))
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            bairro = st.text_input("Bairro", 
                                  value=perfil.get('bairro', ''))
        
        with col2:
            cidade = st.text_input("Cidade", 
                                  value=perfil.get('cidade', ''))
        
        with col3:
            estado = st.text_input("Estado", 
                                  value=perfil.get('estado', ''),
                                  max_chars=2)
            
        cep = st.text_input("CEP", 
                          value=perfil.get('cep', ''),
                          help="Formato: XXXXX-XXX")
        
        # Informações adicionais para relatórios
        st.subheader("Personalização de Relatórios")
        
        mensagem_padrao = st.text_area(
            "Mensagem de Agradecimento (para incluir nos relatórios)", 
            value=perfil.get('mensagem_padrao', 'Agradecemos a confiança em nossos serviços.'),
            help="Esta mensagem aparecerá nos relatórios enviados para clientes"
        )
        
        # Campo para observações personalizadas nos relatórios
        observacoes_default = """1. Pagamento sinal, na reserva da data, via PIX
2. Os valores apresentados incluem todos os custos.
3. Não está incluído a organização de documentos.
4. No caso da proposta incluir treinamento, é necessário a presença de funcionário no período da organização
5. Não incluido produtos e organizadores, caso o cliente opte por adquirí-los"""
        
        observacoes_relatorio = st.text_area(
            "Observações para Relatórios de Propostas",
            value=perfil.get('observacoes_relatorio', observacoes_default),
            height=150,
            help="Estas observações aparecerão em todos os PDFs de propostas gerados. Uma observação por linha, numeradas automaticamente."
        )
        
        # Seção de personalização de cores para PDFs
        st.subheader("🎨 Cores Personalizadas para PDFs")
        st.info("💡 Personalize as cores dos seus relatórios PDF para combinar com sua identidade visual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cor_principal = st.color_picker(
                "Cor Principal", 
                value=perfil.get('cor_principal', '#0D1B2A'),
                help="Cor principal para títulos, cabeçalhos e destaque nos PDFs"
            )
        
        with col2:
            cor_secundaria = st.color_picker(
                "Cor Secundária", 
                value=perfil.get('cor_secundaria', '#E8D5A3'),
                help="Cor secundária para fundos, bordas e elementos complementares nos PDFs"
            )
        
        # Preview das cores
        st.markdown("**Preview das cores:**")
        col_preview1, col_preview2 = st.columns(2)
        
        with col_preview1:
            st.markdown(f"""
            <div style="background-color: {cor_principal}; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold;">
                Cor Principal<br>
                <small style="opacity: 0.8;">{cor_principal}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_preview2:
            st.markdown(f"""
            <div style="background-color: {cor_secundaria}; color: {cor_principal}; padding: 15px; border-radius: 8px; text-align: center; border: 2px solid {cor_principal};">
                Cor Secundária<br>
                <small style="opacity: 0.8;">{cor_secundaria}</small>
            </div>
            """, unsafe_allow_html=True)
        
        botao_salvar = st.form_submit_button("💾 Salvar Perfil")
        
        if botao_salvar:
            # Preparar dados para salvar
            dados_perfil = {
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'instagram': instagram,
                'empresa': empresa,
                'website': website,
                'cargo': cargo,
                'cnpj': cnpj,
                'endereco': endereco,
                'numero': numero,
                'complemento': complemento,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'cep': cep,
                'mensagem_padrao': mensagem_padrao,
                'observacoes_relatorio': observacoes_relatorio,
                'cor_principal': cor_principal,
                'cor_secundaria': cor_secundaria
            }
            
            # Salvar perfil no banco de dados
            try:
                from utils.database import Database
                
                # Usar a instância do banco de dados da sessão
                if 'db' in st.session_state:
                    db = st.session_state.db
                    sucesso = db.salvar_perfil_usuario(dados_perfil)
                else:
                    # Fallback para arquivo JSON
                    sucesso = salvar_perfil(user_id, dados_perfil)
                
                if sucesso:
                    st.success("✅ Perfil salvo com sucesso!")
                    
                    # CORREÇÃO: Atualizar dados do usuário na sessão SEM sobrescrever outros campos
                    if 'usuario' in st.session_state and isinstance(st.session_state.usuario, dict):
                        # Manter todos os dados existentes e apenas adicionar/atualizar os novos
                        st.session_state.usuario.update({
                            'nome': nome,
                            'telefone': telefone,
                            'empresa': empresa,
                            'cargo': cargo,
                            'mensagem_padrao': mensagem_padrao,
                            'observacoes_relatorio': observacoes_relatorio
                        })
                    
                    # Atualizar também o objeto 'user' se existir
                    if 'user' in st.session_state and isinstance(st.session_state.user, dict):
                        st.session_state.user.update({
                            'nome': nome,
                            'telefone': telefone,
                            'empresa': empresa,
                            'cargo': cargo
                        })
                else:
                    st.error("❌ Erro ao salvar perfil. Tente novamente.")
            except Exception as e:
                st.error(f"❌ Erro ao salvar perfil: {str(e)}")
    
    # Exibir informações de última atualização
    if 'ultima_atualizacao' in perfil:
        st.info(f"📅 Última atualização: {perfil['ultima_atualizacao']}")
    
    # Seção de faturamento e assinatura
    st.subheader("💳 Faturamento e Assinatura")

    if _is_pro(perfil):
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #026937;">
            <h4 style="margin-top: 0; color: #026937;">Portal do Cliente Stripe</h4>
            <p>Gerencie sua assinatura, atualize seus dados de pagamento e visualize suas faturas.</p>
        </div>
        """, unsafe_allow_html=True)

        col_portal, _ = st.columns([1, 2])
        with col_portal:
            if st.button("💳 Acessar Portal do Cliente", key="btn_stripe_portal", use_container_width=True):
                with st.spinner("Abrindo portal..."):
                    url, erro = _criar_portal_session(perfil.get('email') or user_id)
                if url:
                    st.session_state["stripe_portal_url"] = url
                elif erro == "sem_assinatura":
                    st.info("Nenhuma assinatura encontrada no Stripe para o seu e-mail. Se você acabou de assinar, aguarde alguns minutos.")
                elif erro and "configuration" in erro.lower():
                    st.warning("O Portal do Cliente ainda não foi ativado na conta Stripe. Ative em Settings → Billing → Customer portal no painel do Stripe.")
                else:
                    st.error(f"Não foi possível abrir o portal: {erro}")

        if st.session_state.get("stripe_portal_url"):
            url = st.session_state["stripe_portal_url"]
            st.link_button("🔗 Abrir Portal do Cliente", url, use_container_width=False)
            st.caption("Se o botão não abrir automaticamente, clique no link acima.")
    else:
        st.markdown("""
        <div style="background-color: #fff8e6; padding: 15px; border-radius: 5px; border-left: 4px solid #C9A84C;">
            <h4 style="margin-top: 0; color: #8a6d1a;">Assine o Plano Pro</h4>
            <p>Desbloqueie todos os recursos do Planner Organizer sem limites.</p>
        </div>
        """, unsafe_allow_html=True)
        col_m, col_a = st.columns(2)
        with col_m:
            st.link_button("🚀 Mensal — R$ 29,90/mês", STRIPE_CHECKOUT_MENSAL, use_container_width=True)
        with col_a:
            st.link_button("📅 Anual — R$ 297,00 (economia de 2 meses)", STRIPE_CHECKOUT_ANUAL, use_container_width=True)

    # Link direto do portal — acesso garantido por e-mail, independente do
    # que o banco registra como plano ou da configuração da API.
    st.markdown(
        f'<p style="font-size:0.85rem;color:#64748b;margin-top:12px;">'
        f'Já é assinante? <a href="{STRIPE_PORTAL_LINK}" target="_blank">'
        f'Gerencie sua assinatura pelo portal do cliente</a> (acesso por e-mail).</p>',
        unsafe_allow_html=True,
    )

    # Exibir dicas de uso
    with st.expander("📘 Sobre o Perfil", expanded=False):
        st.markdown("""
        ### Por que preencher seu perfil?
        
        As informações do seu perfil serão utilizadas nos relatórios e documentos gerados pelo sistema, como:
        
        - **Propostas para clientes**: Seu nome e contatos aparecerão como dados do profissional
        - **Relatórios financeiros**: O nome da empresa será utilizado nos cabeçalhos
        - **Documentos PDF**: Todas as informações de contato aparecerão no rodapé dos documentos
        
        Mantenha seus dados sempre atualizados para uma experiência profissional completa!
        """)

if __name__ == "__main__":
    show()