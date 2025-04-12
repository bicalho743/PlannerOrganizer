import streamlit as st
import pandas as pd
import io
import re
import logging
from datetime import datetime
import unidecode
import traceback

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Função super-robusta para normalizar valores monetários
def normalizar_valor_monetario(valor_str):
    try:
        # Converter para string se não for
        if not isinstance(valor_str, str):
            valor_str = str(valor_str)
            
        # Remover espaços e símbolos de moeda
        valor_str = valor_str.strip().replace('R$', '').replace(' ', '')
        
        # Caso seja um valor vazio, retornar 0
        if not valor_str:
            return 0
            
        # Remover todos os caracteres que não sejam dígitos, pontos ou vírgulas
        valor_str = ''.join(c for c in valor_str if c.isdigit() or c in '.,')
        
        # Casos especiais de tratamento
        if valor_str.count('.') > 1:
            # Caso de valor como "3.450.00" -> converter para "3450.00"
            # Remover todos os pontos exceto o último
            partes = valor_str.split('.')
            valor_str = ''.join(partes[:-1]).replace('.', '') + '.' + partes[-1]
        
        # Se tem vírgula, substituí-la por ponto (formato brasileiro -> americano)
        if ',' in valor_str:
            # Se tem ponto e vírgula, verificar qual é o separador decimal
            if '.' in valor_str:
                # Se o ponto vem antes da vírgula, é formato brasileiro (1.000,00)
                if valor_str.index('.') < valor_str.index(','):
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                else:
                    # É formato americano (1,000.00), remover as vírgulas
                    valor_str = valor_str.replace(',', '')
            else:
                # Só tem vírgula, substituir por ponto
                valor_str = valor_str.replace(',', '.')
        
        # Converter para float
        valor = float(valor_str)
        
        return valor
    except Exception as e:
        logger.error(f"Erro ao normalizar valor monetário '{valor_str}': {str(e)}")
        return None

# Função para mapear/normalizar nomes de clientes para busca flexível
def get_client_mappings(db):
    # Obter clientes do banco de dados
    clientes_df = db.get_clientes()
    
    if clientes_df.empty:
        st.error("Não há clientes cadastrados no sistema. Importe clientes primeiro.")
        return None
    
    # Criar mapa de nomes normalizados
    client_map = {}
    normalized_map = {}
    
    for _, row in clientes_df.iterrows():
        client_id = row['id']
        name = row['nome'].strip()
        
        # Armazenar o nome original e ID
        client_map[name] = client_id
        
        # Normalizar nome (remover acentos, minúsculas)
        normalized_name = unidecode.unidecode(name.lower())
        normalized_map[normalized_name] = client_id
        
        # Adicionar partes do nome para busca parcial
        parts = normalized_name.split()
        if len(parts) > 1:
            normalized_map[parts[0]] = client_id  # Primeiro nome
    
    return {
        'exact': client_map,
        'normalized': normalized_map,
        'all_clients': clientes_df
    }

# Função para encontrar cliente por diferentes estratégias
def find_client_id(client_name, mappings):
    if not client_name or not mappings:
        return None
    
    # 1. Busca exata
    if client_name in mappings['exact']:
        return mappings['exact'][client_name]
    
    # 2. Busca normalizada
    normalized_name = unidecode.unidecode(client_name.lower())
    if normalized_name in mappings['normalized']:
        return mappings['normalized'][normalized_name]
    
    # 3. Busca parcial
    for stored_name, client_id in mappings['normalized'].items():
        if normalized_name in stored_name or stored_name in normalized_name:
            return client_id
    
    # 4. Busca por conteúdo parcial (mais flexível)
    for original_name, client_id in mappings['exact'].items():
        # Se pelo menos metade do nome bate
        if len(original_name) > 3 and (
            original_name[:len(original_name)//2] in client_name or
            client_name[:len(client_name)//2] in original_name
        ):
            return client_id
    
    return None

# Função para importar diretamente as propostas
def importar_propostas_direto(db):
    # Planilha de propostas embutida no código
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
    
    # Buscar mapeamento de clientes
    client_mappings = get_client_mappings(db)
    if not client_mappings:
        return False, "Não há clientes cadastrados no sistema."
    
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
        
        # Dados da proposta
        proposta_data = {}
        
        # 1. Encontrar cliente
        try:
            cliente_nome = str(row['cliente_nome']).strip()
            cliente_id = find_client_id(cliente_nome, client_mappings)
            
            if not cliente_id:
                erros.append(f"Cliente '{cliente_nome}' não encontrado (linha {idx+2})")
                continue
            
            proposta_data['cliente_id'] = cliente_id
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
        
        # 7. Adicionar proposta ao banco de dados
        try:
            proposta_id = db.add_proposta(**proposta_data)
            sucessos += 1
        except Exception as e:
            erros.append(f"Erro ao salvar proposta na linha {idx+2}: {str(e)}")
            continue
    
    # Limpar a barra de progresso ao finalizar
    progress_bar.empty()
    status_text.empty()
    
    # Relatório final
    mensagem = f"Importação concluída. {sucessos} registros importados com sucesso. Erros: {len(erros)}"
    if erros:
        if len(erros) <= 10:
            erros_msg = "\n".join([f"- {erro}" for erro in erros])
        else:
            erros_msg = "\n".join([f"- {erro}" for erro in erros[:10]]) + f"\n... e mais {len(erros) - 10} erros."
        logger.error(f"Erros na importação:\n{erros_msg}")
    
    return sucessos > 0, mensagem, erros

# Função para exibir a interface do importador
def show():
    st.title("⚡ Importação Rápida de Propostas")
    st.write("Este utilitário importará automaticamente a planilha de propostas fornecida.")
    
    # Mostrar estatísticas de propostas existentes
    from utils.database import Database
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    db = st.session_state.db
    
    try:
        propostas_atuais = db.get_propostas()
        st.write(f"Total de propostas no sistema atualmente: {len(propostas_atuais)}")
    except:
        st.warning("Não foi possível obter o número atual de propostas.")
    
    # Botão para iniciar a importação direta
    if st.button("⚡ Iniciar Importação", type="primary"):
        with st.spinner("Importando propostas..."):
            sucesso, mensagem, erros = importar_propostas_direto(db)
            
            if sucesso:
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

if __name__ == "__main__":
    show()