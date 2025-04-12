"""
Módulo específico para importação direta de propostas
Este módulo é projetado para evitar problemas de escopo com as variáveis cliente_id
"""
import streamlit as st
import pandas as pd
import unidecode
from datetime import datetime

def salvar_proposta(db, cliente_id_arg, descricao_arg, 
                   valor_arg, status_arg, tipo_proposta_arg=None,
                   data_inicio_arg=None, data_fim_arg=None, 
                   prazo_entrega_arg=None):
    """Função isolada para salvar proposta no banco de dados"""
    try:
        # Validar cliente_id_arg - verificando se não é None antes
        if cliente_id_arg is None:
            return False, None, "ID do cliente não pode ser nulo"
            
        # Validar valor_arg - verificando se não é None antes
        if valor_arg is None:
            return False, None, "Valor da proposta não pode ser nulo"
            
        # Garantir que os tipos estejam corretos - com validações adicionais
        # para evitar erros de conversão 'NoneType'
        try:
            cliente_id_int = int(cliente_id_arg)
        except (TypeError, ValueError):
            return False, None, f"Erro ao converter ID do cliente para número: {cliente_id_arg}"
            
        try:
            valor_float = float(valor_arg)
        except (TypeError, ValueError):
            return False, None, f"Erro ao converter valor para número: {valor_arg}"
        
        # Debug para verificar os valores
        print(f"Debug - Salvando proposta: cliente_id={cliente_id_int}, valor={valor_float}")
        
        # Chamar a função do banco de dados
        proposta_id = db.add_proposta(
            cliente_id=cliente_id_int,
            descricao=descricao_arg,
            valor=valor_float,
            status=status_arg,
            tipo_proposta=tipo_proposta_arg,
            data_inicio=data_inicio_arg,
            data_fim=data_fim_arg,
            prazo_entrega=prazo_entrega_arg
        )
        return True, proposta_id, None
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return False, None, f"{str(e)}\n{traceback_str}"

def normalizar_valor_monetario(valor_str):
    """Normaliza um valor monetário no formato brasileiro para float"""
    if not valor_str or pd.isna(valor_str):
        return None
        
    # Se já for um número, retornar como float
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    
    # Converter string para formato numérico
    try:
        # Substituir vírgula por ponto e remover símbolos
        valor_limpo = valor_str.replace('R$', '').replace('r$', '').strip()
        valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
        return float(valor_limpo)
    except (ValueError, AttributeError):
        return None

def get_client_mappings(clientes_df):
    """Cria mapeamentos para busca eficiente de clientes"""
    if clientes_df.empty:
        return {"exact": {}, "normalized": {}, "all_clients": []}
    
    # Mapeamentos
    exact_mapping = {cliente['nome']: cliente['id'] for _, cliente in clientes_df.iterrows()}
    normalized_mapping = {unidecode.unidecode(cliente['nome'].lower()): cliente['id'] for _, cliente in clientes_df.iterrows()}
    return {
        "exact": exact_mapping,
        "normalized": normalized_mapping,
        "all_clients": clientes_df.to_dict('records')
    }

def find_client_id(client_name, mappings):
    """Encontra o ID do cliente usando diferentes estratégias de busca"""
    if not client_name or not mappings:
        return None, "Nome do cliente não especificado"
    
    # Busca direta (case sensitive)
    if client_name in mappings["exact"]:
        st.write(f"Encontrado cliente '{client_name}' por busca exata: ID={mappings['exact'][client_name]}")
        return mappings["exact"][client_name], None
    
    # Busca normalizada (sem acentos e lowercase)
    normalized_name = unidecode.unidecode(client_name.lower())
    if normalized_name in mappings["normalized"]:
        st.write(f"Encontrado cliente '{client_name}' por nome normalizado")
        return mappings["normalized"][normalized_name], None
    
    # Busca por similaridade
    best_match = None
    best_ratio = 0
    from difflib import SequenceMatcher
    
    for client in mappings["all_clients"]:
        ratio = SequenceMatcher(None, normalized_name, unidecode.unidecode(client['nome'].lower())).ratio()
        if ratio > 0.8 and ratio > best_ratio:  # Pelo menos 80% de similaridade
            best_match = client
            best_ratio = ratio
    
    if best_match:
        st.write(f"Encontrado cliente '{best_match['nome']}' por similaridade ({best_ratio:.0%})")
        return best_match['id'], None
    
    return None, f"Cliente '{client_name}' não encontrado"

def importar_proposta_formulario():
    """Interface de formulário para importação de propostas"""
    st.title("⚡ Importação Direta de Propostas")
    st.markdown("""
    ### Importação de Propostas Simplificada
    Esta ferramenta permite importar propostas diretamente, sem precisar enviar arquivos.
    Basta preencher os dados abaixo e clicar em importar.
    """)
    
    with st.form("propostas_form"):
        # Campos do formulário
        nome_cliente = st.text_input("Nome do Cliente")
        descricao = st.text_input("Descrição da Proposta")
        valor = st.text_input("Valor (R$)")
        status = st.selectbox("Status", ["Em andamento", "Concluída", "Cancelada", "Aguardando aprovação"])
        tipo_proposta = st.selectbox("Tipo de Proposta", ["Organização", "Projeto", "Consultoria", "Outro"])
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data de Início", value=None)
        with col2:
            data_fim = st.date_input("Data de Fim", value=None)
        
        prazo_entrega = st.date_input("Prazo de Entrega", value=None)
        
        # Botão de envio
        submitted = st.form_submit_button("Importar Proposta")
    
    if submitted:
        # Verificar se cliente foi informado
        if not nome_cliente:
            st.error("Nome do cliente é obrigatório!")
            return
        
        # Verificar se descrição foi informada
        if not descricao:
            st.error("Descrição da proposta é obrigatória!")
            return
        
        # Normalizar valor
        valor_normalizado = normalizar_valor_monetario(valor)
        if not valor_normalizado:
            st.error("Valor inválido! Por favor, informe um valor numérico.")
            return
        
        # Iniciar processo de importação
        with st.spinner("Importando proposta..."):
            # Obter referência ao banco de dados
            db = st.session_state.db
            
            # 1. Verificar clientes atuais
            try:
                propostas_atuais = db.get_propostas()
                st.write(f"Total de propostas no sistema antes da importação: {len(propostas_atuais)}")
            except Exception as e:
                st.error(f"Erro ao carregar propostas existentes: {str(e)}")
                return
            
            # 2. Buscar cliente pelo nome
            clientes = db.get_clientes()
            
            # 3. Criar mapeamentos para busca de clientes
            mappings = get_client_mappings(clientes)
            
            # 4. Obter ID do cliente
            cliente_id, erro_cliente = find_client_id(nome_cliente, mappings)
            
            if erro_cliente:
                st.error(erro_cliente)
                return
            
            st.write(f"Processando proposta: ID cliente definido como {cliente_id}")
            
            # 5. Verificação final dos dados
            st.text(f"Verificando proposta - Cliente ID: {cliente_id} | Valor: {valor_normalizado}")
            
            # 6. Adicionar proposta ao banco de dados usando a função auxiliar
            sucesso, proposta_id, erro = salvar_proposta(
                db=db,
                cliente_id_arg=cliente_id,
                descricao_arg=descricao,
                valor_arg=valor_normalizado,
                status_arg=status,
                tipo_proposta_arg=tipo_proposta,
                data_inicio_arg=data_inicio,
                data_fim_arg=data_fim,
                prazo_entrega_arg=prazo_entrega
            )
            
            if sucesso:
                sucessos = 1
                st.success(f"✅ Proposta salva com sucesso. ID: {proposta_id}")
            else:
                st.error(f"❌ Erro ao salvar proposta: {erro}")
                return
            
            # 7. Verificar propostas importadas
            try:
                propostas_novas = db.get_propostas()
                st.write(f"Total de propostas no sistema após importação: {len(propostas_novas)}")
                st.write(f"Propostas adicionadas: {len(propostas_novas) - len(propostas_atuais)}")
            except:
                pass

def importar_propostas_csv_direto():
    """Interface para importar propostas a partir de CSV embutido"""
    st.title("⚡ Importação Rápida de Propostas")
    st.write("Este utilitário importará automaticamente as propostas fornecidas.")
    
    # Mostrar estatísticas de propostas existentes
    db = st.session_state.db
    
    try:
        propostas_atuais = db.get_propostas()
        st.write(f"Total de propostas no sistema atualmente: {len(propostas_atuais)}")
    except:
        st.warning("Não foi possível obter o número atual de propostas.")
    
    # Buscar mapeamento de clientes
    try:
        # Obter clientes do banco de dados
        clientes_df = db.get_clientes()
        
        # Verificar se há clientes
        if clientes_df.empty:
            st.error("Não há clientes cadastrados no sistema. Importe clientes primeiro.")
            return
        
        # Mostrar alguns clientes para debug
        st.write(f"Obtidos {len(clientes_df)} clientes do banco de dados.")
        
        # Mostrar alguns clientes para confirmação
        with st.expander("Ver lista de clientes disponíveis (primeiros 10)"):
            st.dataframe(clientes_df[['id', 'nome']].head(10))
            
        mappings = get_client_mappings(clientes_df)
        st.success(f"Mapeamento de clientes criado com sucesso. {len(mappings['exact'])} clientes mapeados.")
    except Exception as e:
        st.error(f"Erro ao obter clientes: {str(e)}")
        return
    
    # Botão para iniciar a importação direta
    if st.button("⚡ Iniciar Importação", type="primary"):
        with st.spinner("Importando propostas..."):
            # Planilha de propostas embutida no código - com dados reais
            propostas_csv = """cliente_nome;descricao;valor;status;tipo_proposta;data_inicio;data_fim;prazo_entrega
Alessandra Marquiori;Organização;R$ 1.400,00;fechada;Organização;04/11/2023;10/11/2023;
Daniela Cristina Gomes Paraguai;Organização;R$ 1.900,00;fechada;Organização;13/11/2023;14/11/2023;
Lilian Mara de Bernardi Costa;Organização;R$ 2.200,00;fechada;Organização;27/11/2023;29/11/2023;
Ana Lucia Pena Peixoto;Organização;R$ 900,00;fechada;Organização;30/11/2023;30/11/2023;"""
            
            # Converter o CSV para DataFrame
            import io
            df = pd.read_csv(io.StringIO(propostas_csv), sep=';')
            
            st.write(f"CSV carregado com {len(df)} propostas:")
            st.dataframe(df.head())
            
            # Preparar barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Contadores
            sucessos = 0
            erros = []
            
            # Processar cada linha
            for idx, row in df.iterrows():
                status_text.text(f"Processando proposta {idx+1} de {len(df)}...")
                progress_bar.progress((idx + 1) / len(df))
                
                # 1. Buscar cliente
                client_name = row['cliente_nome']
                cliente_id, erro = find_client_id(client_name, mappings)
                
                if erro:
                    erros.append(erro)
                    st.error(erro)
                    continue
                
                # 2. Preparar dados da proposta
                try:
                    # Converter valor
                    valor = normalizar_valor_monetario(row['valor'])
                    if not valor:
                        erro_msg = f"Valor não numérico na linha {idx+2}: {row['valor']}"
                        erros.append(erro_msg)
                        st.error(erro_msg)
                        continue
                    
                    # Converter datas
                    data_inicio = None
                    data_fim = None
                    prazo_entrega = None
                    
                    try:
                        if pd.notna(row['data_inicio']):
                            data_inicio = pd.to_datetime(row['data_inicio'], format='%d/%m/%Y').date()
                    except:
                        pass
                        
                    try:
                        if pd.notna(row['data_fim']):
                            data_fim = pd.to_datetime(row['data_fim'], format='%d/%m/%Y').date()
                    except:
                        pass
                    
                    try:
                        if pd.notna(row['prazo_entrega']):
                            prazo_entrega = pd.to_datetime(row['prazo_entrega'], format='%d/%m/%Y').date()
                    except:
                        pass
                    
                    # Verificar status
                    status = row['status'].lower()
                    if status == 'fechada':
                        status = 'Concluída'
                    elif status == 'aberta':
                        status = 'Em andamento'
                    elif status == 'recusada':
                        status = 'Cancelada'
                    
                    # Extrair tipo de proposta
                    tipo_proposta = row['tipo_proposta'] if pd.notna(row['tipo_proposta']) else None
                    
                    # Extrair descrição
                    descricao = row['descricao'] if pd.notna(row['descricao']) else None
                    if not descricao:
                        erro_msg = f"Descrição vazia na linha {idx+2}"
                        erros.append(erro_msg)
                        st.error(erro_msg)
                        continue
                        
                    # Verificação final dos dados
                    st.text(f"Verificando proposta {idx+1} - Cliente ID: {cliente_id} | Valor: {valor}")
                    
                    # Salvar proposta
                    sucesso, proposta_id, erro = salvar_proposta(
                        db=db,
                        cliente_id_arg=cliente_id,
                        descricao_arg=descricao,
                        valor_arg=valor,
                        status_arg=status,
                        tipo_proposta_arg=tipo_proposta,
                        data_inicio_arg=data_inicio,
                        data_fim_arg=data_fim,
                        prazo_entrega_arg=prazo_entrega
                    )
                    
                    if sucesso:
                        sucessos += 1
                        st.success(f"✅ Proposta {idx+1} salva com sucesso. ID: {proposta_id}")
                    else:
                        erros.append(f"Erro ao salvar proposta na linha {idx+2}: {erro}")
                        st.error(f"❌ Erro ao salvar proposta {idx+1}: {erro}")
                
                except Exception as e:
                    erros.append(f"Erro ao processar linha {idx+2}: {str(e)}")
                    st.error(f"Erro ao processar linha {idx+2}: {str(e)}")
            
            # Limpar progresso
            progress_bar.empty()
            status_text.empty()
            
            # Relatório final
            mensagem = f"Importação concluída. {sucessos} registros importados com sucesso. Erros: {len(erros)}"
            if sucessos > 0:
                st.success(mensagem)
            else:
                st.error(mensagem)
            
            # Verificar propostas importadas
            try:
                propostas_novas = db.get_propostas()
                st.write(f"Total de propostas no sistema após importação: {len(propostas_novas)}")
                st.write(f"Propostas adicionadas: {len(propostas_novas) - len(propostas_atuais)}")
            except:
                pass

def show():
    """Função principal para exibir a página de importação direta"""
    st.title("⚡ Importar Propostas Direto")
    
    # Tabs para diferentes métodos de importação
    tab1, tab2 = st.tabs(["Formulário Individual", "CSV Direto"])
    
    with tab1:
        importar_proposta_formulario()
        
    with tab2:
        importar_propostas_csv_direto()
    
    # Botão para voltar
    if st.button("← Voltar ao Menu Principal", key="btn_voltar"):
        # Limpar estado de importação direta
        if 'show_import_direto' in st.session_state:
            st.session_state['show_import_direto'] = False
        
        # Retornar à página anterior ou dashboard
        if 'previous_page' in st.session_state:
            st.session_state['current_page'] = st.session_state['previous_page']
        else:
            st.session_state['current_page'] = "Dashboard"
            
        st.rerun()