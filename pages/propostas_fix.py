"""
Adaptação da página de propostas para corrigir o problema de finalização no Render
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from utils.database import Database
from utils.finalizar_proposta_fix import finalizar_proposta_seguro

# Configuração da página
st.set_page_config(
    page_title="Planner Organiza - Propostas",
    page_icon="📝",
    layout="wide"
)

# Verificar login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Função para carregar propostas
def load_propostas(db, status=None):
    return db.get_propostas(status=status)

# Função para carregar detalhes da proposta
def load_proposta_details(db, proposta_id):
    proposta = db.get_proposta(proposta_id)
    proposta_produtos = db.get_proposta_produtos(proposta_id)
    proposta_fornecedores = db.get_proposta_fornecedores(proposta_id)
    proposta_acrescimos = db.get_proposta_acrescimos(proposta_id)
    proposta_assistentes = db.get_proposta_assistentes(proposta_id)
    return proposta, proposta_produtos, proposta_fornecedores, proposta_acrescimos, proposta_assistentes

# Criar tabs para as diferentes seções
def main():
    st.title("📝 Propostas")
    
    # Inicializar database
    usuario_id = st.session_state.user_info.get('localId') if st.session_state.user_info else None
    db = Database(usuario_id)
    
    # Criar tabs para diferentes funcionalidades
    tabs = ["Nova Proposta", "Em Análise", "Em Execução", "Finalizadas", "Todas as Propostas"]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs)
    
    # Tab 1: Nova Proposta
    with tab1:
        if 'edit_proposta_id' in st.session_state and st.session_state.edit_proposta_id:
            st.warning(f"Você está editando a proposta #{st.session_state.edit_proposta_id}")
        
        # Formulário para nova proposta
        form_container = st.container()
        
        with form_container:
            with st.form("proposta_form"):
                # Cliente
                clientes = db.get_clientes()
                if 'edit_proposta_id' in st.session_state and st.session_state.edit_proposta_id:
                    proposta = db.get_proposta(st.session_state.edit_proposta_id)
                    cliente_atual = proposta.cliente_id if proposta else None
                else:
                    proposta = None
                    cliente_atual = None
                
                cliente_options = [c.nome for c in clientes]
                cliente_selected = st.selectbox(
                    "Cliente *", 
                    options=cliente_options,
                    index=next((i for i, c in enumerate(clientes) if c.id == cliente_atual), 0) if cliente_atual and clientes else 0
                )
                cliente_id = next((c.id for c in clientes if c.nome == cliente_selected), None)
                
                # Adicionar novo cliente
                with st.expander("Cliente não encontrado? Adicione um novo"):
                    nome_cliente = st.text_input("Nome do Cliente")
                    telefone_cliente = st.text_input("Telefone do Cliente")
                    email_cliente = st.text_input("Email do Cliente")
                    
                    if st.button("Adicionar Cliente"):
                        if nome_cliente and telefone_cliente:
                            result = db.add_cliente(nome_cliente, telefone_cliente, email_cliente)
                            if result['status'] == 'success':
                                st.success(f"Cliente {nome_cliente} adicionado com sucesso!")
                                st.rerun()
                            else:
                                st.error(result['message'])
                        else:
                            st.error("Nome e telefone são obrigatórios")
                
                # Dados básicos da proposta
                col1, col2 = st.columns(2)
                with col1:
                    descricao = st.text_input(
                        "Descrição da Proposta *", 
                        value=proposta.descricao if proposta else ""
                    )
                with col2:
                    valor = st.number_input(
                        "Valor (R$) *", 
                        value=float(proposta.valor) if proposta else 0.0,
                        step=100.0
                    )
                
                # Datas
                col1, col2, col3 = st.columns(3)
                with col1:
                    data_inicio = st.date_input(
                        "Data de Início", 
                        value=proposta.data_inicio if proposta and proposta.data_inicio else date.today(),
                        format="DD/MM/YYYY"
                    )
                with col2:
                    data_fim = st.date_input(
                        "Data de Conclusão Prevista",
                        value=proposta.data_fim if proposta and proposta.data_fim else date.today() + timedelta(days=30),
                        format="DD/MM/YYYY"
                    )
                with col3:
                    prazo_entrega = st.number_input(
                        "Prazo de Entrega (dias)",
                        value=proposta.prazo_entrega if proposta else 30,
                        min_value=1
                    )
                
                # Tipo de proposta e status
                col1, col2 = st.columns(2)
                with col1:
                    tipos_proposta = ["Organização Residencial", "Organização Empresarial", "Consultoria", "Palestra", "Curso", "Outro"]
                    tipo_proposta = st.selectbox(
                        "Tipo de Proposta", 
                        options=tipos_proposta,
                        index=tipos_proposta.index(proposta.tipo_proposta) if proposta and proposta.tipo_proposta in tipos_proposta else 0
                    )
                with col2:
                    status_options = ["Em análise", "Em execução", "Finalizada", "Cancelada"]
                    status = st.selectbox(
                        "Status", 
                        options=status_options,
                        index=status_options.index(proposta.status) if proposta and proposta.status in status_options else 0
                    )
                
                # Observações
                observacoes = st.text_area(
                    "Observações", 
                    value=proposta.observacoes if proposta and proposta.observacoes else ""
                )
                
                # Botões de submissão
                if proposta:
                    submit_text = "Atualizar Proposta"
                else:
                    submit_text = "Salvar Proposta"
                    
                submit_button = st.form_submit_button(submit_text)
                
                if submit_button:
                    if not cliente_id or not descricao or valor <= 0:
                        st.error("Cliente, descrição e valor são campos obrigatórios")
                    else:
                        # Adicionar ou atualizar proposta
                        if proposta:
                            # Atualizar proposta existente
                            result = db.update_proposta(
                                st.session_state.edit_proposta_id,
                                cliente_id,
                                descricao,
                                valor,
                                status,
                                tipo_proposta,
                                data_inicio,
                                data_fim,
                                prazo_entrega,
                                observacoes
                            )
                            if result['status'] == 'success':
                                st.success(f"Proposta #{st.session_state.edit_proposta_id} atualizada com sucesso!")
                                st.session_state.edit_proposta_id = None
                                st.rerun()
                            else:
                                st.error(result['message'])
                        else:
                            # Adicionar nova proposta
                            result = db.add_proposta(
                                cliente_id,
                                descricao,
                                valor,
                                status,
                                tipo_proposta,
                                data_inicio,
                                data_fim,
                                prazo_entrega,
                                observacoes
                            )
                            if result['status'] == 'success':
                                st.success(f"Proposta adicionada com sucesso!")
                                proposta_id = result['id']
                                
                                # Redirecionar para edição de produtos e fornecedores
                                st.session_state.edit_proposta_id = proposta_id
                                st.rerun()
                            else:
                                st.error(result['message'])
            
            # Se estiver editando, mostrar informações adicionais
            if 'edit_proposta_id' in st.session_state and st.session_state.edit_proposta_id:
                proposta_id = st.session_state.edit_proposta_id
                
                # Obter dados da proposta
                proposta, proposta_produtos, proposta_fornecedores, proposta_acrescimos, proposta_assistentes = load_proposta_details(db, proposta_id)
                
                # Mostrar tabs para produtos, fornecedores, etc.
                st.subheader(f"Detalhes da Proposta #{proposta_id}")
                
                detail_tabs = st.tabs(["Produtos", "Fornecedores", "Outros Custos", "Assistentes", "Finalizar"])
                
                # Tab Produtos
                with detail_tabs[0]:
                    # Listar produtos existentes
                    st.subheader("Produtos da Proposta")
                    
                    if proposta_produtos:
                        df_produtos = pd.DataFrame([{
                            'ID': p.id,
                            'Descrição': p.descricao,
                            'Quantidade': p.quantidade,
                            'Valor Unitário': p.valor_unitario,
                            'Total': p.quantidade * p.valor_unitario
                        } for p in proposta_produtos])
                        
                        st.dataframe(df_produtos)
                        
                        # Valor total dos produtos
                        total_produtos = sum(p.quantidade * p.valor_unitario for p in proposta_produtos)
                        st.info(f"Total de produtos: R$ {total_produtos:.2f}")
                    else:
                        st.info("Nenhum produto adicionado")
                    
                    # Adicionar novo produto
                    with st.form("add_produto_form"):
                        st.subheader("Adicionar Produto")
                        
                        # Campos do formulário
                        descricao_produto = st.text_input("Descrição do Produto *")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            quantidade = st.number_input("Quantidade *", min_value=1, value=1)
                        with col2:
                            valor_unitario = st.number_input("Valor Unitário (R$) *", min_value=0.0, value=0.0, step=10.0)
                        
                        submit_produto = st.form_submit_button("Adicionar Produto")
                        
                        if submit_produto:
                            if not descricao_produto or quantidade <= 0:
                                st.error("Descrição e quantidade são obrigatórios")
                            else:
                                # Adicionar produto
                                result = db.add_proposta_produto(
                                    proposta_id,
                                    descricao_produto,
                                    quantidade,
                                    valor_unitario
                                )
                                
                                if result['status'] == 'success':
                                    st.success("Produto adicionado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                
                # Tab Fornecedores
                with detail_tabs[1]:
                    # Listar fornecedores existentes
                    st.subheader("Fornecedores da Proposta")
                    
                    if proposta_fornecedores:
                        df_fornecedores = pd.DataFrame([{
                            'ID': f.id,
                            'Nome': f.nome,
                            'Percentual (%)': f.percentual,
                            'Valor Estimado': (f.percentual / 100) * proposta.valor if proposta else 0
                        } for f in proposta_fornecedores])
                        
                        st.dataframe(df_fornecedores)
                        
                        # Valor total das comissões
                        total_comissoes = sum((f.percentual / 100) * proposta.valor for f in proposta_fornecedores)
                        st.info(f"Total de comissões: R$ {total_comissoes:.2f}")
                    else:
                        st.info("Nenhum fornecedor adicionado")
                    
                    # Adicionar novo fornecedor
                    with st.form("add_fornecedor_form"):
                        st.subheader("Adicionar Fornecedor/Parceiro")
                        
                        # Campos do formulário
                        nome_fornecedor = st.text_input("Nome do Fornecedor/Parceiro *")
                        percentual = st.number_input("Percentual de Comissão (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
                        
                        if percentual > 0 and proposta:
                            st.info(f"Valor estimado da comissão: R$ {(percentual / 100) * proposta.valor:.2f}")
                        
                        submit_fornecedor = st.form_submit_button("Adicionar Fornecedor")
                        
                        if submit_fornecedor:
                            if not nome_fornecedor:
                                st.error("Nome do fornecedor é obrigatório")
                            else:
                                # Adicionar fornecedor
                                result = db.add_proposta_fornecedor(
                                    proposta_id,
                                    nome_fornecedor,
                                    percentual
                                )
                                
                                if result['status'] == 'success':
                                    st.success("Fornecedor adicionado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                
                # Tab Outros Custos
                with detail_tabs[2]:
                    # Listar acréscimos existentes
                    st.subheader("Outros Custos da Proposta")
                    
                    outros_acrescimos = [a for a in proposta_acrescimos if a.tipo == 'OUTRO']
                    
                    if outros_acrescimos:
                        df_acrescimos = pd.DataFrame([{
                            'ID': a.id,
                            'Descrição': a.descricao,
                            'Valor (R$)': a.valor,
                        } for a in outros_acrescimos])
                        
                        st.dataframe(df_acrescimos)
                        
                        # Valor total dos acréscimos
                        total_acrescimos = sum(a.valor for a in outros_acrescimos)
                        st.info(f"Total de outros custos: R$ {total_acrescimos:.2f}")
                    else:
                        st.info("Nenhum custo adicional registrado")
                    
                    # Adicionar novo acréscimo
                    with st.form("add_acrescimo_form"):
                        st.subheader("Adicionar Custo")
                        
                        # Campos do formulário
                        descricao_acrescimo = st.text_input("Descrição do Custo *")
                        valor_acrescimo = st.number_input("Valor (R$) *", min_value=0.0, value=0.0, step=10.0)
                        
                        submit_acrescimo = st.form_submit_button("Adicionar Custo")
                        
                        if submit_acrescimo:
                            if not descricao_acrescimo or valor_acrescimo <= 0:
                                st.error("Descrição e valor são obrigatórios")
                            else:
                                # Adicionar acréscimo
                                result = db.add_proposta_acrescimo(
                                    proposta_id,
                                    'OUTRO',
                                    descricao_acrescimo,
                                    valor_acrescimo
                                )
                                
                                if result['status'] == 'success':
                                    st.success("Custo adicionado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                
                # Tab Assistentes
                with detail_tabs[3]:
                    # Listar assistentes existentes
                    st.subheader("Assistentes da Proposta")
                    
                    if proposta_assistentes:
                        df_assistentes = pd.DataFrame([{
                            'ID': a.id,
                            'Nome': a.descricao,
                            'Valor (R$)': a.valor,
                        } for a in proposta_assistentes])
                        
                        st.dataframe(df_assistentes)
                        
                        # Valor total dos assistentes
                        total_assistentes = sum(a.valor for a in proposta_assistentes)
                        st.info(f"Total de assistentes: R$ {total_assistentes:.2f}")
                    else:
                        st.info("Nenhum assistente registrado")
                    
                    # Adicionar novo assistente
                    with st.form("add_assistente_form"):
                        st.subheader("Adicionar Assistente")
                        
                        # Campos do formulário
                        nome_assistente = st.text_input("Nome do Assistente *")
                        valor_assistente = st.number_input("Valor para o Assistente (R$) *", min_value=0.0, value=0.0, step=50.0)
                        
                        submit_assistente = st.form_submit_button("Adicionar Assistente")
                        
                        if submit_assistente:
                            if not nome_assistente or valor_assistente <= 0:
                                st.error("Nome e valor são obrigatórios")
                            else:
                                # Adicionar assistente
                                result = db.add_proposta_assistente(
                                    proposta_id,
                                    nome_assistente,
                                    valor_assistente
                                )
                                
                                if result['status'] == 'success':
                                    st.success("Assistente adicionado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                
                # Tab Finalizar
                with detail_tabs[4]:
                    st.subheader("Resumo da Proposta")
                    
                    # Detalhes da proposta
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Cliente:** {proposta.cliente_nome}")
                        st.write(f"**Descrição:** {proposta.descricao}")
                        st.write(f"**Status:** {proposta.status}")
                        st.write(f"**Tipo:** {proposta.tipo_proposta}")
                    with col2:
                        st.write(f"**Valor Base:** R$ {proposta.valor:.2f}")
                        st.write(f"**Data Início:** {proposta.data_inicio.strftime('%d/%m/%Y') if proposta.data_inicio else 'N/D'}")
                        st.write(f"**Data Fim:** {proposta.data_fim.strftime('%d/%m/%Y') if proposta.data_fim else 'N/D'}")
                        st.write(f"**Prazo Entrega:** {proposta.prazo_entrega} dias")
                    
                    st.markdown("---")
                    
                    # Resumo financeiro
                    st.subheader("Resumo Financeiro")
                    
                    valor_base = float(proposta.valor)
                    
                    # Calcular totais
                    total_produtos = sum(p.quantidade * p.valor_unitario for p in proposta_produtos)
                    total_fornecedores = sum((f.percentual / 100) * valor_base for f in proposta_fornecedores)
                    total_assistentes = sum(a.valor for a in proposta_assistentes)
                    total_outros = sum(a.valor for a in proposta_acrescimos if a.tipo == 'OUTRO')
                    
                    total_custos = total_produtos + total_fornecedores + total_outros + total_assistentes
                    
                    # Debugging info
                    st.write(f"DEBUG FINANCEIRO: base={valor_base}, produtos={total_produtos}, fornecedores={total_fornecedores}, assistentes={total_assistentes} (subtraído), outros={total_outros}, total={valor_base + total_produtos + total_fornecedores - total_assistentes + total_outros}")
                    
                    # Dados para tabela
                    financeiro = [
                        {"Item": "Valor Base", "Valor": f"R$ {valor_base:.2f}"},
                        {"Item": "Produtos", "Valor": f"R$ {total_produtos:.2f}"},
                        {"Item": "Comissões", "Valor": f"R$ {total_fornecedores:.2f}"},
                        {"Item": "Assistentes", "Valor": f"R$ {total_assistentes:.2f}"},
                        {"Item": "Outros Custos", "Valor": f"R$ {total_outros:.2f}"},
                        {"Item": "Total de Custos", "Valor": f"R$ {total_custos:.2f}"},
                        {"Item": "Lucro Estimado", "Valor": f"R$ {valor_base - total_custos:.2f}"}
                    ]
                    
                    df_financeiro = pd.DataFrame(financeiro)
                    st.table(df_financeiro)
                    
                    # Botão para finalizar proposta
                    if proposta.status == 'Finalizada':
                        st.success("Esta proposta já está finalizada!")
                    else:
                        if st.button("Finalizar Proposta"):
                            confirm = st.checkbox("Confirmar finalização? Esta ação não pode ser desfeita. Todos os lançamentos financeiros serão gerados automaticamente.")
                            
                            if confirm:
                                # Chamada à versão segura de finalização que utiliza validação extra
                                result = finalizar_proposta_seguro(proposta_id, usuario_id)
                                
                                if result['status'] == 'success':
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                
                # Botão para sair da edição
                if st.button("Sair da Edição"):
                    st.session_state.edit_proposta_id = None
                    st.rerun()
    
    # Tabs para listar propostas por status
    
    # Tab 2: Em Análise
    with tab2:
        propostas = load_propostas(db, status="Em análise")
        
        st.header("Propostas em Análise")
        
        if propostas:
            for proposta in propostas:
                with st.expander(f"{proposta.cliente_nome} - {proposta.descricao} (R$ {proposta.valor:.2f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {proposta.id}")
                        st.write(f"**Cliente:** {proposta.cliente_nome}")
                        st.write(f"**Descrição:** {proposta.descricao}")
                        st.write(f"**Valor:** R$ {proposta.valor:.2f}")
                    
                    with col2:
                        st.write(f"**Tipo:** {proposta.tipo_proposta}")
                        st.write(f"**Status:** {proposta.status}")
                        st.write(f"**Data Início:** {proposta.data_inicio.strftime('%d/%m/%Y') if proposta.data_inicio else 'N/D'}")
                        st.write(f"**Data Fim:** {proposta.data_fim.strftime('%d/%m/%Y') if proposta.data_fim else 'N/D'}")
                    
                    if st.button(f"Editar Proposta #{proposta.id}", key=f"edit_{proposta.id}"):
                        st.session_state.edit_proposta_id = proposta.id
                        st.rerun()
        else:
            st.info("Nenhuma proposta em análise encontrada.")
    
    # Tab 3: Em Execução
    with tab3:
        propostas = load_propostas(db, status="Em execução")
        
        st.header("Propostas em Execução")
        
        if propostas:
            for proposta in propostas:
                with st.expander(f"{proposta.cliente_nome} - {proposta.descricao} (R$ {proposta.valor:.2f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {proposta.id}")
                        st.write(f"**Cliente:** {proposta.cliente_nome}")
                        st.write(f"**Descrição:** {proposta.descricao}")
                        st.write(f"**Valor:** R$ {proposta.valor:.2f}")
                    
                    with col2:
                        st.write(f"**Tipo:** {proposta.tipo_proposta}")
                        st.write(f"**Status:** {proposta.status}")
                        st.write(f"**Data Início:** {proposta.data_inicio.strftime('%d/%m/%Y') if proposta.data_inicio else 'N/D'}")
                        st.write(f"**Data Fim:** {proposta.data_fim.strftime('%d/%m/%Y') if proposta.data_fim else 'N/D'}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(f"Editar Proposta #{proposta.id}", key=f"edit_{proposta.id}"):
                            st.session_state.edit_proposta_id = proposta.id
                            st.rerun()
                    
                    with col2:
                        if st.button(f"Finalizar Proposta #{proposta.id}", key=f"finish_{proposta.id}"):
                            # Usar a versão segura de finalização
                            result = finalizar_proposta_seguro(proposta.id, usuario_id)
                            
                            if result['status'] == 'success':
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['message'])
        else:
            st.info("Nenhuma proposta em execução encontrada.")
    
    # Tab 4: Finalizadas
    with tab4:
        propostas = load_propostas(db, status="Finalizada")
        
        st.header("Propostas Finalizadas")
        
        if propostas:
            for proposta in propostas:
                with st.expander(f"{proposta.cliente_nome} - {proposta.descricao} (R$ {proposta.valor:.2f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {proposta.id}")
                        st.write(f"**Cliente:** {proposta.cliente_nome}")
                        st.write(f"**Descrição:** {proposta.descricao}")
                        st.write(f"**Valor:** R$ {proposta.valor:.2f}")
                    
                    with col2:
                        st.write(f"**Tipo:** {proposta.tipo_proposta}")
                        st.write(f"**Status:** {proposta.status}")
                        st.write(f"**Data Início:** {proposta.data_inicio.strftime('%d/%m/%Y') if proposta.data_inicio else 'N/D'}")
                        st.write(f"**Data Fim:** {proposta.data_fim.strftime('%d/%m/%Y') if proposta.data_fim else 'N/D'}")
                    
                    # Botão para gerar relatórios
                    if st.button(f"Ver Detalhes #{proposta.id}", key=f"view_{proposta.id}"):
                        st.session_state.edit_proposta_id = proposta.id
                        st.rerun()
        else:
            st.info("Nenhuma proposta finalizada encontrada.")
    
    # Tab 5: Todas as Propostas
    with tab5:
        propostas = load_propostas(db)
        
        st.header("Todas as Propostas")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por cliente
            clientes = [c.nome for c in db.get_clientes()]
            cliente_filtro = st.selectbox("Filtrar por Cliente", ["Todos"] + clientes)
        
        with col2:
            # Filtro por status
            status_options = ["Todos", "Em análise", "Em execução", "Finalizada", "Cancelada"]
            status_filtro = st.selectbox("Filtrar por Status", status_options)
        
        with col3:
            # Filtro por tipo
            tipos_proposta = ["Todos", "Organização Residencial", "Organização Empresarial", "Consultoria", "Palestra", "Curso", "Outro"]
            tipo_filtro = st.selectbox("Filtrar por Tipo", tipos_proposta)
        
        # Aplicar filtros
        propostas_filtradas = propostas
        
        if cliente_filtro != "Todos":
            propostas_filtradas = [p for p in propostas_filtradas if p.cliente_nome == cliente_filtro]
        
        if status_filtro != "Todos":
            propostas_filtradas = [p for p in propostas_filtradas if p.status == status_filtro]
        
        if tipo_filtro != "Todos":
            propostas_filtradas = [p for p in propostas_filtradas if p.tipo_proposta == tipo_filtro]
        
        # Exibir propostas filtradas
        if propostas_filtradas:
            for proposta in propostas_filtradas:
                with st.expander(f"{proposta.cliente_nome} - {proposta.descricao} (R$ {proposta.valor:.2f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {proposta.id}")
                        st.write(f"**Cliente:** {proposta.cliente_nome}")
                        st.write(f"**Descrição:** {proposta.descricao}")
                        st.write(f"**Valor:** R$ {proposta.valor:.2f}")
                    
                    with col2:
                        st.write(f"**Tipo:** {proposta.tipo_proposta}")
                        st.write(f"**Status:** {proposta.status}")
                        st.write(f"**Data Início:** {proposta.data_inicio.strftime('%d/%m/%Y') if proposta.data_inicio else 'N/D'}")
                        st.write(f"**Data Fim:** {proposta.data_fim.strftime('%d/%m/%Y') if proposta.data_fim else 'N/D'}")
                    
                    if st.button(f"Editar Proposta #{proposta.id}", key=f"edit_all_{proposta.id}"):
                        st.session_state.edit_proposta_id = proposta.id
                        st.rerun()
        else:
            st.info("Nenhuma proposta encontrada com os filtros selecionados.")

# Executar função principal
if __name__ == "__main__":
    main()