import os
import sys
import streamlit as st
import logging
from datetime import datetime
import pandas as pd

# Configurar logging primeiro para capturar todos os erros
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log de início da aplicação
logger.info("Iniciando aplicação Planner Organizer")

# Adicionar diretório raiz ao path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    import utils
    from utils.database import Database
    from utils.celebration import toggle_celebration, show_celebration
    import utils.importador
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {str(e)}")
    st.error("Erro ao carregar módulos necessários. Por favor, tente novamente.")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="Planner Organizer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização da base de dados
if 'db' not in st.session_state:
    try:
        st.session_state.db = Database()
    except Exception as e:
        st.error("Erro ao conectar com o banco de dados. Por favor, tente novamente mais tarde.")
        st.exception(e)
        st.stop()

# Estilo CSS customizado
st.markdown("""
    <style>
    /* Estilo para botões principais */
    div.stButton > button {
        width: 100%;
        text-align: left;
        padding: 0.75rem 1rem;
        background-color: #F1A208 !important;
        color: #262730 !important;
        font-weight: 600;
        margin-bottom: 0.4rem;
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #ffc107 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    /* Estilo para a barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        color: white;
    }
    
    /* Container para os botões do menu */
    div.nav-buttons {
        background-color: #1E293B;
        padding: 1.2rem;
        margin: 0 -1rem;
        border-radius: 0 0 10px 10px;
    }
    
    /* Estilo para os expanders de informações */
    div.streamlit-expanderHeader {
        background-color: #3B82F6 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.8rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    div.streamlit-expanderHeader:hover {
        background-color: #2563EB !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    div.streamlit-expanderContent {
        background-color: #2A3F5F !important;
        color: white !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
        margin-top: -0.5rem !important;
        border: 1px solid #3B82F6 !important;
    }
    
    /* Ajustes para texto dentro dos expanders */
    div.streamlit-expanderContent p, div.streamlit-expanderContent li {
        color: #E2E8F0 !important;
    }
    
    div.streamlit-expanderContent h3 {
        color: #F1A208 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    div.streamlit-expanderContent strong {
        color: #F8FAFC !important;
    }
    
    /* Customização do título do sidebar */
    section[data-testid="stSidebar"] .stMarkdown h1 {
        color: #F1A208 !important;
        margin-bottom: 1rem !important;
        font-size: 1.5rem !important;
        text-align: center !important;
        padding-top: 1rem !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Personalização para separadores */
    hr {
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Menu principal - com cabeçalho melhorado
st.sidebar.markdown("""
<div style='text-align: center; padding: 15px; background-color: #1E293B; border-bottom: 3px solid #F1A208; margin-bottom: 20px;'>
    <img src="https://cdn-icons-png.flaticon.com/512/3208/3208615.png" width="60" style='margin-bottom: 10px;'>
    <h1 style='color: #F1A208; font-size: 1.5rem; margin: 5px 0;'>PLANNER ORGANIZER</h1>
    <p style='color: #E2E8F0; font-size: 0.8rem; margin: 0;'>Sistema de Gestão Profissional</p>
</div>
""", unsafe_allow_html=True)

# Funções para importação integrada dentro da aplicação principal
# Função para normalizar valor monetário
def normalizar_valor_monetario(valor_str):
    import re
    import locale
    from decimal import Decimal, InvalidOperation
    
    # Se for None ou vazio, retorna None
    if not valor_str or valor_str == '' or valor_str == 'nan':
        return None
    
    try:
        # Converter para string se não for
        valor_str = str(valor_str).strip()
        
        # Remover símbolos de moeda e espaços
        valor_str = re.sub(r'[R$€$\s]', '', valor_str)
        
        # Caso brasileiro: vírgula como decimal e ponto como separador de milhar
        if ',' in valor_str and ('.' in valor_str and valor_str.rindex('.') < valor_str.rindex(',')):
            # Remover pontos e substituir vírgula por ponto
            valor_str = valor_str.replace('.', '').replace(',', '.')
        
        # Caso americano: ponto como decimal e vírgula como separador de milhar
        elif ',' in valor_str and ('.' in valor_str and valor_str.rindex('.') > valor_str.rindex(',')):
            # Remover vírgulas
            valor_str = valor_str.replace(',', '')
        
        # Caso só tem vírgula (assumindo formato brasileiro)
        elif ',' in valor_str and '.' not in valor_str:
            valor_str = valor_str.replace(',', '.')
        
        # Converter para float
        return float(valor_str)
    
    except Exception as e:
        st.error(f"Erro ao normalizar valor monetário '{valor_str}': {str(e)}")
        return None

# Função para importação direta de propostas integrada ao main.py
def importar_propostas_direto_integrado():
    import pandas as pd
    import io
    import unidecode
    from datetime import datetime, date
    
    st.title("⚡ Importação Rápida de Propostas")
    st.write("Este utilitário importará automaticamente as propostas fornecidas.")
    
    # Mostrar estatísticas de propostas existentes
    db = st.session_state.db
    
    try:
        propostas_atuais = db.get_propostas()
        st.write(f"Total de propostas no sistema atualmente: {len(propostas_atuais)}")
    except:
        st.warning("Não foi possível obter o número atual de propostas.")
    
    # Função para obter mapeamento de clientes
    def get_client_mappings():
        try:
            # Obter clientes do banco de dados
            clientes_df = db.get_clientes()
            
            # Verificar se há clientes
            if clientes_df.empty:
                st.error("Não há clientes cadastrados no sistema. Importe clientes primeiro.")
                return None
            
            # Mostrar alguns clientes para debug
            st.write(f"Obtidos {len(clientes_df)} clientes do banco de dados.")
            
            # Criar mapas para busca
            client_map = {}
            normalized_map = {}
            
            for _, row in clientes_df.iterrows():
                client_id = row['id']
                name = row['nome'].strip() if isinstance(row['nome'], str) else str(row['nome'])
                
                # Armazenar o nome original e ID
                client_map[name] = client_id
                
                # Normalizar nome (remover acentos, minúsculas)
                normalized_name = unidecode.unidecode(name.lower())
                normalized_map[normalized_name] = client_id
                
                # Adicionar partes do nome para busca parcial
                parts = normalized_name.split()
                if len(parts) > 1:
                    normalized_map[parts[0]] = client_id  # Primeiro nome
            
            st.success(f"Mapeamento de clientes criado com sucesso. {len(client_map)} clientes mapeados.")
            
            # Mostrar alguns clientes para confirmação
            with st.expander("Ver lista de clientes disponíveis (primeiros 10)"):
                st.dataframe(clientes_df[['id', 'nome']].head(10))
                
            return {
                'exact': client_map,
                'normalized': normalized_map,
                'all_clients': clientes_df
            }
        except Exception as e:
            st.error(f"Erro ao obter clientes: {str(e)}")
            return None
    
    # Função para encontrar cliente por ID
    def find_client_id(client_name, mappings):
        if not client_name or not mappings:
            return None
        
        # Verificar mappings
        if 'exact' not in mappings or 'normalized' not in mappings:
            st.error(f"Erro: Formato inválido de mappings: {mappings.keys()}")
            return None
        
        # 1. Busca exata
        if client_name in mappings['exact']:
            client_id = mappings['exact'][client_name]
            st.write(f"Encontrado cliente '{client_name}' por busca exata: ID={client_id}")
            return client_id
        
        # 2. Busca normalizada
        normalized_name = unidecode.unidecode(client_name.lower())
        if normalized_name in mappings['normalized']:
            client_id = mappings['normalized'][normalized_name]
            st.write(f"Encontrado cliente '{client_name}' por busca normalizada: ID={client_id}")
            return client_id
        
        # 3. Busca parcial
        for stored_name, client_id in mappings['normalized'].items():
            if normalized_name in stored_name or stored_name in normalized_name:
                st.write(f"Encontrado cliente '{client_name}' por busca parcial (match: '{stored_name}'): ID={client_id}")
                return client_id
        
        # 4. Busca por conteúdo parcial (mais flexível)
        for original_name, client_id in mappings['exact'].items():
            # Se pelo menos metade do nome bate
            if len(original_name) > 3 and (
                original_name[:len(original_name)//2] in client_name or
                client_name[:len(client_name)//2] in original_name
            ):
                st.write(f"Encontrado cliente '{client_name}' por busca flexível (match: '{original_name}'): ID={client_id}")
                return client_id
        
        st.warning(f"Cliente '{client_name}' não encontrado")
        return None
    
    # Botão para iniciar a importação direta
    if st.button("⚡ Iniciar Importação", type="primary"):
        with st.spinner("Importando propostas..."):
            
            # Buscar mapeamento de clientes
            client_mappings = get_client_mappings()
            if not client_mappings:
                st.error("Não há clientes cadastrados no sistema ou houve erro ao obter os clientes.")
                return
            
            # Planilha de propostas embutida no código - com dados reais
            propostas_csv = """cliente_nome;descricao;valor;status;tipo_proposta;data_inicio;data_fim;prazo_entrega
Alessandra Marquiori;Organização;R$ 1.400,00;fechada;Organização;04/11/2023;10/11/2023;
Daniela Cristina Gomes Paraguai;Organização;R$ 1.900,00;fechada;Organização;13/11/2023;14/11/2023;
Lilian Mara de Bernardi Costa;Organização;R$ 2.200,00;fechada;Organização;27/11/2023;29/11/2023;
Ana Lucia Pena Peixoto;Organização;R$ 900,00;fechada;Organização;30/11/2023;30/11/2023;
Mônica Moreira de Andrade;Mudança;R$ 8.273,00;fechada;Mudança;06/12/2023;11/12/2023;
Daniela Cristina Gomes Paraguai;Organização;R$ 450,00;fechada;Organização;13/12/2023;13/12/2023;
Naely;Organização;R$ 4.163,00;fechada;Organização;14/12/2023;15/12/2023;
keila;Organização;R$ 2.856,00;fechada;Organização;29/12/2023;29/12/2023;
Paola Fernandes;Organização;R$ 4.036,52;fechada;Organização;02/01/2024;05/01/2024;
Juliana Pretti Campos;Mudança;R$ 1.500,00;fechada;Mudança;09/01/2024;10/01/2024;
keila;Organização;R$ 731,19;fechada;Organização;12/01/2024;12/01/2024;
Sandra Carvalhais;Mudança;R$ 3.500,00;fechada;Mudança;16/01/2024;29/01/2024;
Thaís Coelho;Organização;R$ 5.700,00;fechada;Organização;20/03/2024;20/03/2024;
Jéssica Pereira da Silva;Mudança;R$ 8.120,00;fechada;Mudança;20/03/2024;20/03/2024;
Letícia;Organização;R$ 700,00;fechada;Organização;20/03/2024;20/03/2024;
Thais Carneiro;Marcenaria;R$ 700,00;fechada;Marcenaria;18/04/2024;18/04/2024;
Thais Carneiro;Organização;R$ 12.151,00;fechada;Organização;18/04/2024;19/04/2024;
Paula Vicintim;Organização;R$ 14.340,00;fechada;Organização;18/04/2024;18/04/2024;
Marial Stael Diniz;Mudança;R$ 6.000,00;fechada;Mudança;13/05/2024;17/05/2024;
Gabi Menotti;Organização;R$ 1.958,09;fechada;Organização;15/05/2024;18/05/2024;
Luiza Barreto;Organização;R$ 350,00;fechada;Organização;15/05/2024;18/05/2024;
Thaís Coelho;organização;R$ 2.100,00;fechada;organização;21/05/2024;21/05/2024;
Regiane Kerch;Pós Mudança;R$ 2.600,00;fechada;Pós Mudança;03/06/2024;08/06/2024;
Marina Diniz Macedo Moura;Organização;R$ 5.000,00;fechada;Organização;03/06/2024;06/06/2024;
Dayana Stefana;organização online;R$ 700,00;fechada;organização online;03/06/2024;03/06/2024;
Thais Carneiro;Organização;R$ 2.700,00;fechada;Organização;10/06/2024;11/06/2024;
Jessyka Sampaio;organização;R$ 2.800,00;fechada;organização;01/07/2024;02/07/2024;
Gabi Menotti;organização em parceria;R$ 6.609,80;fechada;organização em parceria;03/07/2024;12/07/2024;
Daniela Garcia;organização online;R$ 600,00;fechada;organização online;04/07/2024;04/07/2024;
Letícia Thaís Caputo;Organização rouparia;R$ 700,00;fechada;Organização rouparia;06/07/2024;06/07/2024;
Luciana Mary Simões Ribeiro;consultoria online;R$ 600,00;fechada;consultoria online;12/07/2024;12/07/2024;
Juliana Pretti Campos;organização;R$ 2.400,00;fechada;organização;05/08/2024;08/08/2024;
Luciana Mary Simões Ribeiro;organização;R$ 1.200,00;fechada;organização;08/08/2024;08/08/2024;
Juliana Pretti Campos;Treinamento Funcionária;R$ 300,00;fechada;Treinamento Funcionária;08/08/2024;08/08/2024;
Amanda Sampaio barreto;organização;R$ 6.700,00;fechada;organização;12/08/2024;19/08/2024;
Amanda Sampaio barreto;Organização Adicional;R$ 2.200,00;fechada;Organização Adicional;20/08/2024;20/08/2024;
Maria Thereza;organização;R$ 5.300,00;fechada;organização;21/08/2024;30/08/2024;
Alessandra Alves Franco;organização;R$ 6.100,00;fechada;organização;02/09/2024;06/09/2024;
Alessandra Marquiori;organização/parceria;R$ 850,00;fechada;organização/parceria;27/08/2024;29/08/2024;
Fernanda Machado;organização mudança;R$ 9.600,00;fechada;organização mudança;09/09/2024;18/09/2024;
Maíra Cavalcante;organização escritório;R$ 1.200,00;fechada;organização escritório;14/10/2024;17/10/2024;
Luciana R. Braga de Freitas;mudança ouro;R$ 7.200,00;fechada;mudança ouro;04/11/2024;08/11/2024;
Humberto;organização;R$ 950,00;fechada;organização;30/10/2024;30/10/2024;
Rafaela Nejm;organização/parceria;R$ 0,00;fechada;organização/parceria;31/10/2024;31/10/2024;
Ana Paula Santana Oliveira;organizaçao;R$ 8.900,00;fechada;organizaçao;18/11/2024;22/11/2024;
Natália Cristeli;organização;R$ 1.200,00;fechada;organização;25/11/2024;26/11/2024;
Ana Carolina Soeiro de Carvalho (Nina);organização/parceria;R$ 900,00;fechada;organização/parceria;25/11/2024;26/11/2024;
Alessandra Marquiori;organização/parceria;R$ 500,00;fechada;organização/parceria;21/11/2024;21/11/2024;
Rebeca Chaves;organização;R$ 4.800,00;fechada;organização;02/12/2024;04/12/2024;
Fernanda Hissa;organização;R$ 2.000,00;fechada;organização;29/11/2024;30/11/2024;
Marcia Machado;organização/parceria;R$ 900,00;fechada;organização/parceria;25/11/2024;27/11/2024;
Vanessa Santos Pereira;organização;R$ 9.600,00;fechada;organização;18/12/2024;24/12/2024;
Bernadeth Baier da Silva;organização;R$ 7.000,00;fechada;organização;03/02/2025;07/02/2025;
Naty Vasconcelos;parceria;R$ 2.500,00;fechada;parceria;03/12/2024;12/12/2024;
Sandra Carvalhais;organização;R$ 3.300,00;fechada;organização;08/01/2025;10/01/2025;
Ana Paula Santana Oliveira;organização ;R$ 2.000,00;fechada;organização ;16/01/2025;17/01/2025;
Maria Thereza;organização;R$ 2.100,00;fechada;organização;22/01/2025;28/01/2025;
Márcia Barreto;organização mudança;R$ 2.250,00;fechada;organização mudança;13/01/2025;15/01/2025;
Thaís Coelho;organização mudança;R$ 12.500,00;fechada;organização mudança;27/01/2025;03/02/2025;
Daniela Garcia;organização online;R$ 1.200,00;fechada;organização online;18/01/2025;18/01/2025;
Regina;organização;R$ 0,00;fechada;organização;24/02/2025;06/03/2025;
Ana Clara;organização;R$ 3450.00;fechada;organização;01/04/2025;05/04/2025;"""
            
            # Carregar propostas do CSV embutido
            df = pd.read_csv(io.StringIO(propostas_csv), sep=';')
            
            # Estatísticas
            sucessos = 0
            erros = []
            
            # Barra de progresso
            st.write("### Progresso da importação")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Processar cada proposta
            for idx, row in df.iterrows():
                # Atualizar progresso
                progress = (idx + 1) / len(df)
                progress_bar.progress(progress)
                status_text.text(f"Processando proposta {idx+1} de {len(df)}")
                
                # Dados da proposta - criar um novo dicionário para cada proposta
                proposta_data = {}
                
                # 1. Encontrar cliente
                try:
                    cliente_nome = str(row['cliente_nome']).strip()
                    proposta_data['cliente_id'] = find_client_id(cliente_nome, client_mappings)
                    
                    if not proposta_data['cliente_id']:
                        erros.append(f"Cliente '{cliente_nome}' não encontrado (linha {idx+2})")
                        continue
                    
                    # Debug info
                    st.text(f"Processando proposta {idx+1}: ID cliente definido como {proposta_data['cliente_id']}")
                    
                except Exception as e:
                    erros.append(f"Erro ao processar cliente na linha {idx+2}: {str(e)}")
                    continue
                
                # 2. Processar descrição
                try:
                    descricao = str(row['descricao']).strip()
                    if not descricao:
                        erros.append(f"Descrição vazia na linha {idx+2}")
                        continue
                    
                    proposta_data['descricao'] = descricao
                except Exception as e:
                    erros.append(f"Erro ao processar descrição na linha {idx+2}: {str(e)}")
                    continue
                
                # 3. Processar valor
                try:
                    valor_str = str(row['valor']).strip()
                    valor = normalizar_valor_monetario(valor_str)
                    
                    if valor is None:
                        erros.append(f"Valor inválido na linha {idx+2}: '{valor_str}'")
                        continue
                    
                    proposta_data['valor'] = valor
                except Exception as e:
                    erros.append(f"Erro ao processar valor na linha {idx+2}: {str(e)}")
                    continue
                
                # 4. Processar status
                proposta_data['status'] = 'Aberta'  # Valor padrão
                try:
                    if 'status' in row and row['status']:
                        status_valor = str(row['status']).strip().capitalize()
                        if status_valor in ['Aberta', 'Fechada', 'Recusada']:
                            proposta_data['status'] = status_valor
                except Exception as e:
                    # Usar o status padrão em caso de erro
                    pass
                
                # 5. Processar tipo_proposta
                try:
                    if 'tipo_proposta' in row and row['tipo_proposta']:
                        proposta_data['tipo_proposta'] = str(row['tipo_proposta']).strip()
                except Exception:
                    # Campo opcional, ignorar erro
                    pass
                
                # 6. Processar datas
                try:
                    # Data início
                    if 'data_inicio' in row and row['data_inicio']:
                        try:
                            proposta_data['data_inicio'] = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                        except:
                            # Ignorar erro de data
                            pass
                    
                    # Data fim
                    if 'data_fim' in row and row['data_fim']:
                        try:
                            proposta_data['data_fim'] = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                        except:
                            # Ignorar erro de data
                            pass
                    
                    # Prazo entrega
                    if 'prazo_entrega' in row and row['prazo_entrega']:
                        try:
                            proposta_data['prazo_entrega'] = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                        except:
                            # Ignorar erro de data
                            pass
                except Exception:
                    # Campo opcional, ignorar erro
                    pass
                
                # Verificação final dos dados
                st.text(f"Verificando proposta {idx+1} - Cliente ID: {proposta_data.get('cliente_id')} | Valor: {proposta_data.get('valor')}")
                
                # 7. Adicionar proposta ao banco de dados
                try:
                    # Salvar no banco de dados
                    proposta_id = db.add_proposta(**proposta_data)
                    sucessos += 1
                    st.success(f"✅ Proposta {idx+1} salva com sucesso. ID: {proposta_id}")
                except Exception as e:
                    erros.append(f"Erro ao salvar proposta na linha {idx+2}: {str(e)}")
                    st.error(f"❌ Erro ao salvar proposta {idx+1}: {str(e)}")
                    continue
            
            # Limpar a barra de progresso ao finalizar
            progress_bar.empty()
            status_text.empty()
            
            # Relatório final
            mensagem = f"Importação concluída. {sucessos} registros importados com sucesso. Erros: {len(erros)}"
            if sucessos > 0:
                st.success(mensagem)
            else:
                st.error(mensagem)
            
            # Mostrar erros de forma mais organizada
            if erros:
                st.error(f"{len(erros)} erros encontrados:")
                
                # Agrupar erros por tipo para melhor visualização
                erros_por_tipo = {}
                for erro in erros:
                    tipo_erro = "Outro"
                    if "não encontrado" in erro:
                        tipo_erro = "Cliente não encontrado"
                    elif "Valor inválido" in erro or "Valor não numérico" in erro:
                        tipo_erro = "Valor monetário inválido"
                    elif "Descrição vazia" in erro:
                        tipo_erro = "Descrição vazia"
                    elif "Erro ao salvar" in erro:
                        tipo_erro = "Erro ao salvar no banco"
                    
                    if tipo_erro not in erros_por_tipo:
                        erros_por_tipo[tipo_erro] = []
                    erros_por_tipo[tipo_erro].append(erro)
                
                # Mostrar erros agrupados
                for tipo, lista_erros in erros_por_tipo.items():
                    with st.expander(f"{tipo} ({len(lista_erros)})"):
                        for erro in lista_erros[:20]:  # Limitar a 20 erros por tipo
                            st.write(f"- {erro}")
                        if len(lista_erros) > 20:
                            st.write(f"... e mais {len(lista_erros) - 20} erros deste tipo.")
            
            # Verificar propostas importadas
            try:
                propostas_novas = db.get_propostas()
                st.write(f"Total de propostas no sistema após importação: {len(propostas_novas)}")
                st.write(f"Propostas adicionadas: {len(propostas_novas) - len(propostas_atuais)}")
            except:
                pass

# Ferramenta especial de importação direta
if st.sidebar.button("⚡ IMPORTAR PROPOSTAS DIRETO", type="primary"):
    # Executar diretamente a função integrada sem mudar de página
    importar_propostas_direto_integrado()

# Container dos botões com fundo escuro
st.sidebar.markdown('<div class="nav-buttons">', unsafe_allow_html=True)

# Botões de navegação
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Definindo as páginas visíveis principais
MENU_PRINCIPAL = {
    "📊 Dashboard": "Dashboard",
    "👥 Cadastros": "Cadastros",
    "📝 Propostas": "Propostas",
    "🛒 Vendas": "Vendas",
    "💰 Financeiro": "Financeiro",
    "📈 Relatórios": "Relatórios"
}

# Criar botões para cada página
for label, page_key in MENU_PRINCIPAL.items():
    if st.sidebar.button(label, key=f"menu_{page_key.lower()}", use_container_width=True):
        st.session_state.current_page = page_key
        st.rerun()

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Informações do sistema no final
st.sidebar.markdown("---")

# Cabeçalho personalizado para as seções do sistema
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #F1A208; margin-bottom: 10px; font-size: 1.3rem;'>INFORMAÇÕES DO SISTEMA</h2>
    <p style='color: #E2E8F0; font-size: 0.9rem;'>Confira recursos e funcionalidades abaixo</p>
    <div style='background-color: #F1A208; height: 3px; width: 50%; margin: 10px auto;'></div>
</div>
""", unsafe_allow_html=True)

# Sobre o Sistema - com botão personalizado
st.sidebar.markdown("""
<div class='system-info-button' onclick="document.querySelector('#sobre-sistema-expander button').click();" 
     style='background-color: #3B82F6; padding: 12px; border-radius: 10px; margin-bottom: 15px; cursor: pointer; 
     box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;'>
    <div style='display: flex; align-items: center;'>
        <div style='font-size: 24px; margin-right: 10px;'>📌</div>
        <div>
            <div style='font-weight: bold; font-size: 1.1rem; color: white;'>Sobre o Sistema</div>
            <div style='color: rgba(255,255,255,0.8); font-size: 0.8rem;'>Funcionalidades e recursos</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# O expander real (que será controlado pelo botão acima)
with st.sidebar.expander("📌 Sobre o Sistema", expanded=False):
    st.markdown("""
    O **Sistema Planner Organizer** é uma ferramenta completa para o gerenciamento 
    eficiente do seu negócio de Personal Organizer. Com ele, você pode:

    ### 📊 Funcionalidades Principais

    **👥 Gestão de Clientes**
    - Cadastro completo de clientes
    - Controle de aniversários
    - Histórico de atendimentos
    - Importação de dados em massa

    **📝 Gestão de Propostas**
    - Criação e acompanhamento de propostas
    - Cálculo automático de valores
    - Geração de PDFs profissionais
    - Controle de status e prazos
    
    **🛒 Gestão de Vendas**
    - Cadastro de produtos
    - Controle de estoque
    - Registro de vendas
    - Histórico de transações

    **💰 Gestão Financeira**
    - Controle de receitas e despesas
    - Gestão de contas a receber
    - Relatórios financeiros detalhados
    - Dashboard com indicadores

    **📈 Relatórios e Análises**
    - Visão geral do negócio
    - Análise de desempenho
    - Gráficos e estatísticas
    - Exportação de dados
    """)

# Informações do Sistema - com botão personalizado
st.sidebar.markdown("""
<div class='system-info-button' onclick="document.querySelector('#info-sistema-expander button').click();" 
     style='background-color: #2563EB; padding: 12px; border-radius: 10px; margin-bottom: 15px; cursor: pointer; 
     box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;'>
    <div style='display: flex; align-items: center;'>
        <div style='font-size: 24px; margin-right: 10px;'>ℹ️</div>
        <div>
            <div style='font-weight: bold; font-size: 1.1rem; color: white;'>Informações do Sistema</div>
            <div style='color: rgba(255,255,255,0.8); font-size: 0.8rem;'>Versão e atualizações recentes</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# O expander real (que será controlado pelo botão acima)
with st.sidebar.expander("ℹ️ Informações do Sistema", expanded=False):
    st.markdown("""
    ### Sistema Personal Organizer
    **Versão:** 1.1.0

    **Recursos Disponíveis:**
    - ✅ Gestão de Clientes
    - ✅ Controle de Propostas
    - ✅ Gestão de Vendas e Produtos
    - ✅ Gestão Financeira
    - ✅ Relatórios e Análises
    - ✅ Importação de Dados

    **Novidades:**
    - 🛒 Sistema de vendas e controle de estoque
    - 🎉 Telas de celebração
    - 📊 Dashboard aprimorado
    - 📱 Interface responsiva

    <div style='text-align: center; margin-top: 20px; padding: 10px; background-color: #1E293B; border-radius: 5px;'>
    Desenvolvido com ❤️ usando Streamlit
    </div>
    """, unsafe_allow_html=True)

# Verificar se há uma celebração pendente
if st.session_state.get('show_celebration', False):
    show_celebration(
        task_name=st.session_state.get('celebration_task'),
        custom_message=st.session_state.get('celebration_message')
    )
else:
    # A navegação agora é controlada pelos botões do menu principal
    # Não é mais necessário verificar os botões aqui, pois eles já
    # atualizam st.session_state.current_page e fazem rerun()

    # Roteamento de páginas
    try:
        if st.session_state.current_page == "Dashboard":
            from pages.dashboard import show
            show()
        elif st.session_state.current_page == "Cadastros":
            from pages.cadastros import show
            show()
        elif st.session_state.current_page == "Propostas":
            from pages.propostas import show
            show()
        elif st.session_state.current_page == "Vendas":
            from pages.vendas import show
            show()
        elif st.session_state.current_page == "Financeiro":
            from pages.financeiro import show
            show()
        elif st.session_state.current_page == "Relatórios":
            from pages.relatorios import show
            show()
        elif st.session_state.current_page == "ImportacaoDireta":
            import importar_planilha_diretamente
            importar_planilha_diretamente.show()
        elif st.session_state.current_page == "Importar":
            st.title("📥 Importação de Dados")
            st.write("### Selecione o tipo de dados para importar:")

            import_type = st.selectbox(
                "Tipo de Importação",
                ["Clientes", "Propostas", "Fornecedores", "Assistentes", "Parceiros", "Produtos"]
            )

            st.info(f"A importação de {import_type} permite carregar dados em massa através de arquivos CSV ou Excel.")

            uploaded_file = st.file_uploader(
                "Escolha um arquivo para importar",
                type=["csv", "xlsx"]
            )

            # Download de template
            col1, col2 = st.columns(2)
            with col1:
                st.write("### Template para Importação")
                # Botão para baixar template CSV
                st.download_button(
                    label=f"Baixar Template CSV",
                    data=utils.importador.gerar_template_csv(import_type),
                    file_name=f"template_{import_type.lower()}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Botão para baixar template Excel
                st.write("&nbsp;")  # Para alinhar com o título da coluna 1
                st.download_button(
                    label=f"Baixar Template Excel",
                    data=utils.importador.gerar_template_excel(import_type),
                    file_name=f"template_{import_type.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            if uploaded_file:
                try:
                    # Importar dados baseado no tipo selecionado
                    if import_type == "Propostas":
                        success, message = utils.importador.importar_propostas(uploaded_file, st.session_state.db)
                    else:
                        # Usar a função genérica para outros tipos de cadastro
                        success, message = utils.importador.importar_cadastros(
                            arquivo=uploaded_file,
                            tipo_cadastro=import_type.rstrip('s'),  # Remover o 's' do plural
                            db=st.session_state.db
                        )
                    
                    if success:
                        st.success(message)
                        # Adicionar opção de celebração
                        if st.button("🎉 Celebrar Importação", key="celebrate_import"):
                            toggle_celebration(
                                task_name="Importação Concluída",
                                custom_message=f"Importação de {import_type} realizada com sucesso!"
                            )
                            st.rerun()
                    else:
                        st.error(message)
                
                except Exception as e:
                    st.error(f"Erro durante a importação: {str(e)}")

    except ImportError as e:
        logger.error(f"Erro ao importar módulo da página {st.session_state.current_page}: {str(e)}")
        st.error(f"Erro ao carregar página {st.session_state.current_page}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao exibir página {st.session_state.current_page}: {str(e)}")
        st.error(f"Erro ao exibir página {st.session_state.current_page}: {str(e)}")

# Rodapé melhorado
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 15px; margin-top: 10px;'>
    <div style='font-weight: bold; color: #F1A208; margin-bottom: 5px; font-size: 1rem;'>Sistema Planner Organizer</div>
    <div style='color: #E2E8F0; font-size: 0.7rem; margin-bottom: 10px;'>© 2025 - Todos os direitos reservados</div>
    <div style='display: flex; justify-content: center; margin-top: 5px;'>
        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: #F1A208; display: flex; 
                 justify-content: center; align-items: center; margin: 0 5px; font-size: 15px;'>📱</div>
        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: #F1A208; display: flex; 
                 justify-content: center; align-items: center; margin: 0 5px; font-size: 15px;'>💼</div>
        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: #F1A208; display: flex; 
                 justify-content: center; align-items: center; margin: 0 5px; font-size: 15px;'>📈</div>
    </div>
</div>
""", unsafe_allow_html=True)