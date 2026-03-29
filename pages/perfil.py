import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

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
    
    # Link para o portal do cliente Stripe
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #026937;">
        <h4 style="margin-top: 0; color: #026937;">Portal do Cliente Stripe</h4>
        <p>Gerencie sua assinatura, atualize seus dados de pagamento e visualize suas faturas.</p>
        <a href="https://dashboard.stripe.com/billing/portal" target="_blank">
            <button style="background-color: #026937; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Acessar Portal do Cliente
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
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