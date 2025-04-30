"""
Versão da página de clientes com acesso direto ao banco para contornar problemas do SQLAlchemy no Render
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.direct_db import DirectDB

# Configuração da página
st.set_page_config(
    page_title="Planner Organiza - Clientes",
    page_icon="👥",
    layout="wide"
)

# Verificar login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Função para carregar clientes via acesso direto ao banco
def load_clientes():
    """Carrega os clientes do banco de dados usando acesso direto"""
    try:
        user_id = st.session_state.user_info.get('localId')
        direct_db = DirectDB(usuario_id=user_id)
        clientes = direct_db.get_clientes()
        direct_db.close()
        return clientes
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {str(e)}")
        return []

# Função para obter cliente específico via acesso direto ao banco
def get_cliente(cliente_id):
    """Obtém um cliente específico do banco de dados usando acesso direto"""
    try:
        user_id = st.session_state.user_info.get('localId')
        direct_db = DirectDB(usuario_id=user_id)
        cliente = direct_db.get_cliente(cliente_id)
        direct_db.close()
        return cliente
    except Exception as e:
        st.error(f"Erro ao buscar cliente: {str(e)}")
        return None

# Função para adicionar cliente via acesso direto ao banco
def add_cliente_direct(nome, telefone, email, cpf=None, endereco=None, 
                      cidade=None, estado=None, bairro=None, 
                      data_aniversario=None, origem_cliente=None, observacoes=None):
    """Adiciona um cliente no banco de dados usando acesso direto"""
    try:
        user_id = st.session_state.user_info.get('localId')
        direct_db = DirectDB(usuario_id=user_id)
        
        # Verificar se email já existe
        if email:
            query = """
                SELECT COUNT(*) as count FROM clientes 
                WHERE email = %(email)s AND usuario_id = %(usuario_id)s
            """
            result = direct_db.execute_query(query, {'email': email, 'usuario_id': user_id})
            if result and result[0]['count'] > 0:
                direct_db.close()
                return {'status': 'error', 'message': 'Já existe um cliente com este email.'}
        
        # Inserir cliente
        query = """
            INSERT INTO clientes 
            (nome, telefone, email, cpf, endereco, cidade, estado, bairro, 
             data_aniversario, origem_cliente, observacoes, data_cadastro, usuario_id) 
            VALUES 
            (%(nome)s, %(telefone)s, %(email)s, %(cpf)s, %(endereco)s, 
             %(cidade)s, %(estado)s, %(bairro)s, %(data_aniversario)s, 
             %(origem_cliente)s, %(observacoes)s, %(data_cadastro)s, %(usuario_id)s)
            RETURNING id
        """
        
        params = {
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'cpf': cpf,
            'endereco': endereco,
            'cidade': cidade,
            'estado': estado,
            'bairro': bairro,
            'data_aniversario': data_aniversario,
            'origem_cliente': origem_cliente,
            'observacoes': observacoes,
            'data_cadastro': datetime.now().date(),
            'usuario_id': user_id
        }
        
        result = direct_db.execute_query(query, params)
        direct_db.close()
        
        if result and 'id' in result[0]:
            return {'status': 'success', 'message': f'Cliente {nome} adicionado com sucesso!', 'id': result[0]['id']}
        else:
            return {'status': 'error', 'message': 'Não foi possível adicionar o cliente.'}
    
    except Exception as e:
        return {'status': 'error', 'message': f'Erro ao adicionar cliente: {str(e)}'}

# Função para atualizar cliente via acesso direto ao banco
def update_cliente_direct(cliente_id, nome, telefone, email, cpf=None, endereco=None, 
                         cidade=None, estado=None, bairro=None, 
                         data_aniversario=None, origem_cliente=None, observacoes=None):
    """Atualiza um cliente no banco de dados usando acesso direto"""
    try:
        user_id = st.session_state.user_info.get('localId')
        direct_db = DirectDB(usuario_id=user_id)
        
        # Verificar se email já existe em outro cliente
        if email:
            query = """
                SELECT COUNT(*) as count FROM clientes 
                WHERE email = %(email)s AND id != %(cliente_id)s AND usuario_id = %(usuario_id)s
            """
            result = direct_db.execute_query(query, {
                'email': email, 
                'cliente_id': cliente_id, 
                'usuario_id': user_id
            })
            
            if result and result[0]['count'] > 0:
                direct_db.close()
                return {'status': 'error', 'message': 'Já existe outro cliente com este email.'}
        
        # Atualizar cliente
        query = """
            UPDATE clientes SET 
                nome = %(nome)s,
                telefone = %(telefone)s,
                email = %(email)s,
                cpf = %(cpf)s,
                endereco = %(endereco)s,
                cidade = %(cidade)s,
                estado = %(estado)s,
                bairro = %(bairro)s,
                data_aniversario = %(data_aniversario)s,
                origem_cliente = %(origem_cliente)s,
                observacoes = %(observacoes)s
            WHERE id = %(cliente_id)s AND usuario_id = %(usuario_id)s
        """
        
        params = {
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'cpf': cpf,
            'endereco': endereco,
            'cidade': cidade,
            'estado': estado,
            'bairro': bairro,
            'data_aniversario': data_aniversario,
            'origem_cliente': origem_cliente,
            'observacoes': observacoes,
            'cliente_id': cliente_id,
            'usuario_id': user_id
        }
        
        direct_db.execute_action(query, params)
        direct_db.close()
        
        return {'status': 'success', 'message': f'Cliente {nome} atualizado com sucesso!'}
    
    except Exception as e:
        return {'status': 'error', 'message': f'Erro ao atualizar cliente: {str(e)}'}

# Função para excluir cliente via acesso direto ao banco
def delete_cliente_direct(cliente_id):
    """Exclui um cliente do banco de dados usando acesso direto"""
    try:
        user_id = st.session_state.user_info.get('localId')
        direct_db = DirectDB(usuario_id=user_id)
        
        # Verificar se cliente tem propostas
        query = """
            SELECT COUNT(*) as count FROM propostas 
            WHERE cliente_id = %(cliente_id)s AND usuario_id = %(usuario_id)s
        """
        result = direct_db.execute_query(query, {'cliente_id': cliente_id, 'usuario_id': user_id})
        
        if result and result[0]['count'] > 0:
            direct_db.close()
            return {'status': 'error', 'message': 'Este cliente possui propostas vinculadas e não pode ser excluído.'}
        
        # Excluir cliente
        query = """
            DELETE FROM clientes 
            WHERE id = %(cliente_id)s AND usuario_id = %(usuario_id)s
        """
        
        direct_db.execute_action(query, {'cliente_id': cliente_id, 'usuario_id': user_id})
        direct_db.close()
        
        return {'status': 'success', 'message': 'Cliente excluído com sucesso!'}
    
    except Exception as e:
        return {'status': 'error', 'message': f'Erro ao excluir cliente: {str(e)}'}

# Função para mostrar formulário de cliente
def show_cliente_form(cliente=None):
    """Mostra formulário para adicionar ou editar cliente"""
    with st.form("cliente_form"):
        st.subheader("Dados Básicos")
        
        nome = st.text_input("Nome *", value=cliente.get('nome', '') if cliente else '')
        
        col1, col2 = st.columns(2)
        with col1:
            telefone = st.text_input("Telefone *", value=cliente.get('telefone', '') if cliente else '')
        with col2:
            email = st.text_input("Email", value=cliente.get('email', '') if cliente else '')
        
        st.subheader("Dados Complementares")
        
        col1, col2 = st.columns(2)
        with col1:
            cpf = st.text_input("CPF/CNPJ", value=cliente.get('cpf', '') if cliente else '')
        with col2:
            data_aniversario = st.date_input(
                "Data de Aniversário", 
                value=cliente.get('data_aniversario') if cliente and cliente.get('data_aniversario') else None,
                format="DD/MM/YYYY"
            )
            if data_aniversario and data_aniversario.year == datetime.now().year:
                data_aniversario = None
        
        st.subheader("Endereço")
        
        endereco = st.text_input("Logradouro", value=cliente.get('endereco', '') if cliente else '')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            bairro = st.text_input("Bairro", value=cliente.get('bairro', '') if cliente else '')
        with col2:
            cidade = st.text_input("Cidade", value=cliente.get('cidade', '') if cliente else '')
        with col3:
            estados = [
                "", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", 
                "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
            ]
            estado = st.selectbox("Estado", options=estados, index=estados.index(cliente.get('estado', '')) if cliente and cliente.get('estado') in estados else 0)
        
        st.subheader("Informações Adicionais")
        
        origens = ["", "Site", "Redes Sociais", "Indicação", "Google", "Outros"]
        origem_cliente = st.selectbox(
            "Origem do Cliente", 
            options=origens,
            index=origens.index(cliente.get('origem_cliente', '')) if cliente and cliente.get('origem_cliente') in origens else 0
        )
        
        observacoes = st.text_area("Observações", value=cliente.get('observacoes', '') if cliente else '')
        
        if cliente:
            submit_button = st.form_submit_button("Atualizar Cliente")
        else:
            submit_button = st.form_submit_button("Adicionar Cliente")
        
        if submit_button:
            if not nome or not telefone:
                st.error("Nome e telefone são campos obrigatórios.")
            else:
                if cliente:
                    result = update_cliente_direct(
                        cliente['id'], nome, telefone, email, cpf, endereco, 
                        cidade, estado, bairro, data_aniversario, 
                        origem_cliente if origem_cliente != "" else None, 
                        observacoes
                    )
                else:
                    result = add_cliente_direct(
                        nome, telefone, email, cpf, endereco, 
                        cidade, estado, bairro, data_aniversario, 
                        origem_cliente if origem_cliente != "" else None, 
                        observacoes
                    )
                
                if result['status'] == 'success':
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])

# Função principal
def main():
    """Função principal da página de clientes"""
    st.title("👥 Clientes")
    
    # Carregar clientes
    clientes = load_clientes()
    
    # Tabs para organizar a interface
    tab1, tab2 = st.tabs(["Lista de Clientes", "Adicionar Cliente"])
    
    # Tab 1: Lista de Clientes
    with tab1:
        if clientes:
            # Converter para DataFrame para melhor visualização
            df = pd.DataFrame(clientes)
            
            # Selecionar e renomear colunas para exibição
            if 'nome' in df.columns and 'telefone' in df.columns:
                display_df = df[['nome', 'telefone', 'email']].copy()
                display_df.columns = ['Nome', 'Telefone', 'Email']
                
                # Adicionar coluna de ações
                for idx, row in display_df.iterrows():
                    cliente_id = df.iloc[idx]['id']
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{row['Nome']}**")
                        st.write(f"📞 {row['Telefone']} | ✉️ {row['Email'] if pd.notna(row['Email']) else 'N/A'}")
                    
                    with col2:
                        if st.button(f"Editar", key=f"edit_{cliente_id}"):
                            st.session_state.selected_cliente = cliente_id
                            st.rerun()
                        
                        if st.button(f"Excluir", key=f"delete_{cliente_id}"):
                            confirm = st.checkbox(f"Confirmar exclusão de {row['Nome']}?", key=f"confirm_{cliente_id}")
                            if confirm:
                                result = delete_cliente_direct(cliente_id)
                                if result['status'] == 'success':
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                    
                    st.markdown("---")
            else:
                st.warning("Formato de dados de clientes inválido.")
        else:
            st.info("Nenhum cliente cadastrado. Adicione seu primeiro cliente na aba 'Adicionar Cliente'.")
    
    # Tab 2: Adicionar Cliente ou Editar Cliente
    with tab2:
        # Verificar se um cliente está selecionado para edição
        if 'selected_cliente' in st.session_state and st.session_state.selected_cliente:
            cliente = get_cliente(st.session_state.selected_cliente)
            if cliente:
                st.subheader(f"Editar Cliente: {cliente.get('nome', '')}")
                show_cliente_form(cliente)
                
                if st.button("Cancelar Edição"):
                    st.session_state.selected_cliente = None
                    st.rerun()
            else:
                st.error("Cliente não encontrado.")
                if st.button("Voltar"):
                    st.session_state.selected_cliente = None
                    st.rerun()
        else:
            st.subheader("Adicionar Novo Cliente")
            show_cliente_form()

# Executar função principal
if __name__ == "__main__":
    main()