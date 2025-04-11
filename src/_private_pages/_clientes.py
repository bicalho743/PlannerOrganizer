import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import traceback
import io
from utils.celebration import toggle_celebration, show_celebration

logger = logging.getLogger(__name__)

def normalizar_data(data_str):
    """Converte uma data no formato DD/MMM para DD/MM"""
    if not data_str or pd.isna(data_str):
        return None

    meses = {
        'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04',
        'mai': '05', 'jun': '06', 'jul': '07', 'ago': '08',
        'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
    }

    try:
        dia, mes = data_str.lower().strip().split('/')
        if mes in meses:
            mes = meses[mes]
        return f"{dia.zfill(2)}/{mes.zfill(2)}"
    except:
        return None

def show():
    st.title("👥 Gestão de Clientes")

    tab1, tab2, tab3 = st.tabs(["Cadastrar Cliente", "Lista de Clientes", "Importar Clientes"])

    with tab1:
        st.subheader("Novo Cliente")
        with st.form("cadastro_cliente", clear_on_submit=True):
            nome = st.text_input("Nome completo")

            telefone = st.text_input("Telefone")
            if telefone:
                telefone = ''.join(filter(str.isdigit, telefone))
                if len(telefone) != 11:
                    st.error("Telefone deve ter 11 dígitos")
                    return

            cpf = st.text_input("CPF")
            if cpf:
                cpf = ''.join(filter(str.isdigit, cpf))
                if len(cpf) != 11:
                    st.error("CPF deve ter 11 dígitos")
                    return

            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("E-mail")
            with col2:
                data_aniversario = st.date_input("Data de Aniversário", format="DD/MM/YYYY")
                origem_cliente = st.selectbox(
                    "Onde conheceu a Personal Organizer?",
                    ["Indicação", "Redes Sociais", "Site", "Evento", "Outro"]
                )

            # Seção de Endereço
            st.write("---")
            st.subheader("Endereço")
            col1, col2 = st.columns(2)
            with col1:
                estado = st.text_input("Estado (UF)")
                cidade = st.text_input("Cidade")
            with col2:
                bairro = st.text_input("Bairro")
                endereco = st.text_input("Endereço completo (Rua, número, complemento)")

            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if nome and telefone and cpf:
                    try:
                        st.session_state.db.add_cliente(
                            nome=nome,
                            email=email,
                            telefone=telefone,
                            estado=estado,
                            cidade=cidade,
                            bairro=bairro,
                            endereco=endereco,
                            cpf=cpf,
                            data_aniversario=data_aniversario,
                            origem_cliente=origem_cliente
                        )
                        # Activate celebration screen
                        toggle_celebration(
                            task_name="Novo Cliente Cadastrado",
                            custom_message=f"🌟 Cliente {nome} cadastrado com sucesso!"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {str(e)}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")

    with tab2:
        st.subheader("Clientes Cadastrados")

        try:
            clientes = st.session_state.db.get_clientes()

            if clientes.empty:
                st.info("Nenhum cliente cadastrado.")
                return

            # Adicionar botões de edição e exclusão para cada cliente
            for index, cliente in clientes.iterrows():
                with st.expander(f"{cliente['nome']} - CPF: {cliente['cpf']}"):
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**Email:** {cliente['email']}")
                        st.write(f"**Telefone:** {cliente['telefone']}")
                        if cliente['data_aniversario']:
                            st.write(f"**Aniversário:** {cliente['data_aniversario'].strftime('%d/%m')}")
                        st.write(f"**Endereço:** {cliente['endereco']}")

                    with col2:
                        if st.button("✏️ Editar", key=f"edit_{cliente['id']}"):
                            st.session_state.cliente_em_edicao = cliente
                            st.rerun()

                    with col3:
                        if st.button("🗑️ Excluir", key=f"del_{cliente['id']}"):
                            if st.session_state.db.delete_cliente(cliente['id']):
                                st.success("Cliente excluído com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir cliente.")

            # Modal de edição
            if 'cliente_em_edicao' in st.session_state:
                cliente = st.session_state.cliente_em_edicao
                st.write("---")
                st.subheader("Editar Cliente")

                with st.form("edicao_cliente"):
                    nome = st.text_input("Nome", value=cliente['nome'])
                    email = st.text_input("Email", value=cliente['email'] if cliente['email'] else "")
                    telefone = st.text_input("Telefone", value=cliente['telefone'] if cliente['telefone'] else "")
                    cpf = st.text_input("CPF", value=cliente['cpf'] if cliente['cpf'] else "")

                    col1, col2 = st.columns(2)
                    with col1:
                        data_aniversario = st.date_input(
                            "Data de Aniversário",
                            value=cliente['data_aniversario'] if cliente['data_aniversario'] else None,
                            format="DD/MM/YYYY"
                        )
                    with col2:
                        origem_cliente = st.selectbox(
                            "Origem do Cliente",
                            ["Indicação", "Redes Sociais", "Site", "Evento", "Outro"],
                            index=["Indicação", "Redes Sociais", "Site", "Evento", "Outro"].index(cliente['origem_cliente']) if cliente['origem_cliente'] else 0
                        )

                    estado = st.text_input("Estado", value=cliente['estado'] if cliente['estado'] else "")
                    cidade = st.text_input("Cidade", value=cliente['cidade'] if cliente['cidade'] else "")
                    bairro = st.text_input("Bairro", value=cliente['bairro'] if cliente['bairro'] else "")
                    endereco = st.text_input("Endereço", value=cliente['endereco'] if cliente['endereco'] else "")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Salvar"):
                            try:
                                st.session_state.db.update_cliente(
                                    cliente['id'],
                                    nome=nome,
                                    email=email,
                                    telefone=telefone,
                                    cpf=cpf,
                                    data_aniversario=data_aniversario,
                                    origem_cliente=origem_cliente,
                                    estado=estado,
                                    cidade=cidade,
                                    bairro=bairro,
                                    endereco=endereco
                                )
                                del st.session_state.cliente_em_edicao
                                st.success("Cliente atualizado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar cliente: {str(e)}")

                    with col2:
                        if st.form_submit_button("Cancelar"):
                            del st.session_state.cliente_em_edicao
                            st.rerun()

        except Exception as e:
            st.error(f"Erro ao carregar clientes: {str(e)}")

    with tab3:
        st.subheader("Importar Clientes")
        st.write("""
        Para importar clientes, seu arquivo deve ter o seguinte formato:
        - O arquivo pode usar vírgula (,) ou ponto e vírgula (;) como separador
        - Se houver separadores dentro de um campo, ele deve estar entre aspas duplas
        - Uma linha por cliente
        - As seguintes colunas são esperadas:
          - nome (obrigatório)
          - email
          - telefone
          - cpf
          - estado
          - cidade
          - bairro
          - endereco
          - data_aniversario (formato: DD/MM ou DD/MMM)
        """)

        uploaded_file = st.file_uploader("Escolha o arquivo", type=['csv'])

        if uploaded_file is not None:
            try:
                file_content = uploaded_file.getvalue()
                df = pd.read_csv(io.StringIO(file_content.decode('utf-8')), sep=';')

                if 'nome' not in df.columns:
                    st.error("O arquivo deve conter uma coluna 'nome'")
                else:
                    st.write("Preview dos dados:")
                    st.dataframe(df.head())

                    if st.button("Confirmar Importação"):
                        progress_bar = st.progress(0)
                        for index, row in df.iterrows():
                            try:
                                nome = str(row['nome']).strip() if pd.notna(row.get('nome')) else None
                                if not nome:
                                    continue

                                # Processar CPF
                                cpf = None
                                if pd.notna(row.get('cpf')):
                                    cpf = str(row['cpf']).strip()
                                    cpf = ''.join(filter(str.isdigit, cpf))

                                # Processar telefone
                                telefone = None
                                if pd.notna(row.get('telefone')):
                                    telefone = str(row['telefone']).strip()
                                    telefone = ''.join(filter(str.isdigit, telefone))

                                # Processar data de aniversário
                                data_aniv = None
                                if pd.notna(row.get('data_aniversario')):
                                    data_str = normalizar_data(str(row['data_aniversario']))
                                    if data_str:
                                        try:
                                            data = datetime.strptime(data_str, '%d/%m')
                                            data_aniv = datetime.now().replace(
                                                month=data.month,
                                                day=data.day
                                            ).date()
                                        except Exception as e:
                                            logger.warning(f"Erro ao processar data de aniversário na linha {index + 2}: {str(e)}")

                                st.session_state.db.add_cliente(
                                    nome=nome,
                                    email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                                    telefone=telefone,
                                    cpf=cpf,
                                    estado=str(row.get('estado', '')).strip() if pd.notna(row.get('estado')) else None,
                                    cidade=str(row.get('cidade', '')).strip() if pd.notna(row.get('cidade')) else None,
                                    bairro=str(row.get('bairro', '')).strip() if pd.notna(row.get('bairro')) else None,
                                    endereco=str(row.get('endereco', '')).strip() if pd.notna(row.get('endereco')) else None,
                                    data_aniversario=data_aniv,
                                    origem_cliente='Importação'
                                )

                            except Exception as e:
                                st.error(f"Erro ao importar linha {index + 2}: {str(e)}")
                                continue

                            progress = (index + 1) / len(df)
                            progress_bar.progress(progress)

                        st.success("Importação concluída!")

            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {str(e)}")