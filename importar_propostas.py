import streamlit as st
import pandas as pd
import io
from datetime import datetime
import logging
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Título da página
st.title("📥 Importar Propostas")

# Mensagem explicativa
st.write("""
Esta página permite importar propostas a partir de um arquivo CSV.

Para uma importação bem-sucedida, seu arquivo deve:
1. Usar ponto e vírgula (;) como separador
2. Conter uma coluna 'cliente_nome' com o nome exato do cliente já cadastrado no sistema
3. Conter colunas 'descricao' e 'valor' obrigatoriamente
""")

# Exibir exemplo de arquivo
st.subheader("Exemplo de arquivo CSV")
exemplo = """cliente_nome;descricao;valor;status;tipo_proposta;data_inicio;data_fim
Fulano da Silva;Organização de armários;1500.00;Aberta;Organização;01/06/2025;10/06/2025
Ciclano dos Santos;Consultoria de decoração;2000.00;Aberta;Consultoria;15/05/2025;20/05/2025"""

st.code(exemplo)

# Download do template
template_file = io.BytesIO()
template_df = pd.DataFrame([
    {
        'cliente_nome': 'Fulano da Silva',
        'descricao': 'Organização de armários',
        'valor': 1500.00,
        'status': 'Aberta',
        'tipo_proposta': 'Organização',
        'data_inicio': '01/06/2025',
        'data_fim': '10/06/2025',
        'prazo_entrega': '15/06/2025'
    }
])

# Converter para CSV
template_csv = template_df.to_csv(index=False, sep=';').encode('utf-8')

# Botão para baixar o template
st.download_button(
    label="📝 Baixar template CSV",
    data=template_csv,
    file_name="template_proposta.csv",
    mime="text/csv",
)

# Função para importar propostas
def importar_propostas(arquivo, db):
    """Importar propostas a partir de um arquivo CSV"""
    try:
        # Carregar o arquivo
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
        st.write(f"Arquivo lido com sucesso. Dimensões: {df.shape}")
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = ['cliente_nome', 'descricao', 'valor']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        if colunas_faltantes:
            st.error(f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}")
            return False, f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltantes)}"
        
        # Limpar dados
        df = df.replace({pd.NA: None, 'nan': None, 'NaN': None, '': None})
        df = df.fillna('')  # Substituir NaN por string vazia para evitar problemas
        
        # Carregar clientes para mapear nomes para IDs
        clientes = db.get_clientes()
        if clientes.empty:
            st.error("Não há clientes cadastrados no sistema")
            return False, "Não há clientes cadastrados no sistema"
        
        # Exibir dados dos clientes para debug
        st.write("### Clientes disponíveis no sistema")
        st.dataframe(clientes[['id', 'nome']])
        
        # Criar dicionário de nomes para IDs
        clientes_dict = dict(zip(clientes['nome'].str.strip(), clientes['id']))
        
        # Resultados
        sucessos = 0
        erros = []
        
        # Barra de progresso
        progress_bar = st.progress(0)
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                progress = (idx + 1) / len(df)
                progress_bar.progress(progress)
                
                # Buscar cliente pelo nome
                cliente_nome = str(row['cliente_nome']).strip()
                if not cliente_nome:
                    erros.append(f"Nome do cliente vazio na linha {idx + 2}")
                    continue
                
                # Verificar se o cliente existe
                if cliente_nome not in clientes_dict:
                    # Tentar correspondência aproximada
                    encontrado = False
                    for nome_cliente, id_cliente in clientes_dict.items():
                        if cliente_nome.lower() in nome_cliente.lower() or nome_cliente.lower() in cliente_nome.lower():
                            st.info(f"Cliente '{cliente_nome}' corresponde a '{nome_cliente}' na base de dados")
                            cliente_id = id_cliente
                            encontrado = True
                            break
                    
                    if not encontrado:
                        erros.append(f"Cliente '{cliente_nome}' não encontrado na linha {idx + 2}")
                        continue
                else:
                    cliente_id = clientes_dict[cliente_nome]
                
                # Validar descrição
                descricao = str(row['descricao']).strip()
                if not descricao:
                    erros.append(f"Descrição vazia na linha {idx + 2}")
                    continue
                
                # Validar valor
                valor = None
                try:
                    valor = float(row['valor'])
                    if valor <= 0:
                        erros.append(f"Valor deve ser maior que zero na linha {idx + 2}")
                        continue
                except (ValueError, TypeError):
                    erros.append(f"Valor não numérico na linha {idx + 2}")
                    continue
                
                # Status padrão se não for fornecido
                status = 'Aberta'
                if 'status' in row and row['status']:
                    status_valor = str(row['status']).strip()
                    if status_valor in ['Aberta', 'Fechada', 'Recusada']:
                        status = status_valor
                
                # Tipo de proposta
                tipo_proposta = None
                if 'tipo_proposta' in row and row['tipo_proposta']:
                    tipo_proposta = str(row['tipo_proposta']).strip()
                
                # Processar datas
                data_inicio = None
                data_fim = None
                prazo_entrega = None
                
                # Data de início
                if 'data_inicio' in row and row['data_inicio']:
                    try:
                        data_inicio = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                    except Exception as e:
                        st.warning(f"Data de início inválida na linha {idx + 2}: {str(e)}")
                
                # Data de fim
                if 'data_fim' in row and row['data_fim']:
                    try:
                        data_fim = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                    except Exception as e:
                        st.warning(f"Data de fim inválida na linha {idx + 2}: {str(e)}")
                
                # Prazo de entrega
                if 'prazo_entrega' in row and row['prazo_entrega']:
                    try:
                        prazo_entrega = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                    except Exception as e:
                        st.warning(f"Prazo de entrega inválido na linha {idx + 2}: {str(e)}")
                
                # Adicionar proposta
                proposta_id = db.add_proposta(
                    cliente_id=cliente_id,
                    descricao=descricao,
                    valor=valor,
                    status=status,
                    tipo_proposta=tipo_proposta,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    prazo_entrega=prazo_entrega
                )
                
                st.success(f"Proposta {idx + 1} adicionada com sucesso. ID: {proposta_id}")
                sucessos += 1
                
            except Exception as e:
                erro_msg = f"Erro na linha {idx + 2}: {str(e)}"
                st.error(erro_msg)
                erros.append(erro_msg)
                logger.error(f"{erro_msg}\n{traceback.format_exc()}")
                continue
        
        # Limpar barra de progresso
        progress_bar.empty()
        
        # Mensagem final
        if sucessos > 0:
            st.success(f"{sucessos} propostas importadas com sucesso!")
        
        if erros:
            st.error(f"{len(erros)} erros encontrados:")
            for erro in erros[:5]:  # Mostrar apenas os 5 primeiros erros
                st.error(f"- {erro}")
            
            if len(erros) > 5:
                st.warning(f"... e mais {len(erros) - 5} erros. Verifique o log para detalhes.")
        
        return sucessos > 0, f"Importação concluída. {sucessos} propostas importadas com sucesso. Erros: {len(erros)}"
    
    except Exception as e:
        erro_msg = f"Erro ao processar arquivo: {str(e)}"
        st.error(erro_msg)
        logger.error(f"{erro_msg}\n{traceback.format_exc()}")
        return False, erro_msg

# Widget para upload de arquivo
arquivo = st.file_uploader("Selecione o arquivo CSV", type=['csv'])

if arquivo:
    if st.button("Importar Propostas", type="primary"):
        if 'db' in st.session_state:
            with st.spinner("Importando propostas..."):
                sucesso, mensagem = importar_propostas(arquivo, st.session_state.db)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
        else:
            st.error("Conexão com banco de dados não inicializada")