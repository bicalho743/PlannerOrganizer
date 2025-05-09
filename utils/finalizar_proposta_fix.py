"""
Módulo para finalização segura de propostas
Este módulo implementa a função finalizar_proposta_sql que utiliza SQL direto
para garantir a finalização correta de propostas.
"""
import os
import logging
import psycopg2
from datetime import datetime, date
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.DEBUG, 
                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     handlers=[
                         logging.StreamHandler(),
                         logging.FileHandler('/tmp/finalizar_proposta_debug.log')
                     ])
logger = logging.getLogger(__name__)

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL não encontrada")
            return None
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}")
        return None

def verificar_funcao_sql_existe(conn=None):
    """Verifica se a função SQL finalizar_proposta existe no banco de dados"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'finalizar_proposta'
            );
        """)
        result = cursor.fetchone()
        
        exists = False
        if result and len(result) > 0:
            exists = result[0]
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return exists
    except Exception as e:
        logger.error(f"Erro ao verificar função SQL: {str(e)}")
        if close_conn and conn:
            conn.close()
        return False

def buscar_proposta(proposta_id: int, conn=None) -> Dict[str, Any]:
    """Busca informações de uma proposta no banco de dados"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return {}
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.id, p.cliente_id, p.usuario_id, p.data_inicio, p.data_proposta,
                p.data_fim, p.valor, p.status, p.status_execucao,
                c.nome as cliente_nome
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
        """, (proposta_id,))
        
        # Verificação de segurança para cursor.description
        columns = []
        if cursor.description is not None:
            columns = [desc[0] for desc in cursor.description]
        else:
            logger.warning(f"cursor.description é None ao buscar proposta #{proposta_id}")
            
        result = cursor.fetchone()
        
        proposta = {}
        if result:
            proposta = dict(zip(columns, result))
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return proposta
    except Exception as e:
        logger.error(f"Erro ao buscar proposta: {str(e)}")
        if close_conn and conn:
            conn.close()
        return {}

def verificar_lancamento_financeiro_existe(proposta_id: int, conn=None) -> bool:
    """Verifica se já existe um lançamento financeiro para a proposta"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        # Verifica qualquer lançamento associado à proposta, independente do tipo
        cursor.execute("""
            SELECT id, descricao, tipo FROM financeiro 
            WHERE proposta_id = %s
        """, (proposta_id,))
        
        lancamentos = cursor.fetchall()
        exists = False
        
        # Se encontrou qualquer lançamento associado à proposta, marcar como verdadeiro
        if lancamentos and len(lancamentos) > 0:
            exists = True
            for lanc in lancamentos:
                try:
                    lanc_id = lanc[0]
                    lanc_desc = lanc[1] if len(lanc) > 1 else "Descrição não disponível"
                    lanc_tipo = lanc[2] if len(lanc) > 2 else "Tipo não disponível"
                    logger.info(f"Lançamento existente: ID={lanc_id}, Descrição={lanc_desc}, Tipo={lanc_tipo}")
                except (IndexError, TypeError):
                    pass
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return exists
    except Exception as e:
        logger.error(f"Erro ao verificar lançamento financeiro: {str(e)}")
        if close_conn and conn:
            conn.close()
        return False

def criar_lancamento_financeiro(proposta_id: int, proposta: Dict[str, Any], conn=None) -> int:
    """Cria um lançamento financeiro para a proposta finalizada"""
    close_conn = False
    if not conn:
        conn = get_db_connection()
        close_conn = True
    
    if not conn:
        return 0
        
    try:
        cursor = conn.cursor()
        data_atual = date.today()
        
        cursor.execute("""
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, tipo, status, proposta_id, usuario_id)
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
        """, (
            f"Proposta #{proposta_id} - {proposta.get('cliente_nome', 'Cliente')}",
            proposta.get('valor', 0),
            data_atual,
            'Serviços de Organização',
            'receita_a_receber',
            'Pendente',
            proposta_id,
            proposta.get('usuario_id', '')
        ))
        
        result = cursor.fetchone()
        lancamento_id = 0
        if result and len(result) > 0:
            lancamento_id = result[0]
            
        cursor.close()
        if close_conn:
            conn.close()
            
        return lancamento_id
    except Exception as e:
        logger.error(f"Erro ao criar lançamento financeiro: {str(e)}")
        if close_conn and conn:
            conn.close()
        return 0

def finalizar_proposta_sql(proposta_id: int, usuario_id: Optional[str] = None) -> bool:
    """
    Finaliza uma proposta utilizando SQL direto para contornar problemas de tipo
    """
    logger.info(f"Iniciando finalização da proposta #{proposta_id} via SQL")
    
    # Verificar se a função SQL existe no banco
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return False
        
    try:
        # Se a função SQL finalizar_proposta existe, usá-la
        if verificar_funcao_sql_existe(conn):
            logger.info("Usando função SQL finalizar_proposta")
            cursor = conn.cursor()
            cursor.execute("SELECT finalizar_proposta(%s)", (proposta_id,))
            result = cursor.fetchone()
            success = False
            if result and len(result) > 0:
                success = result[0]
                
            cursor.close()
            conn.close()
            
            logger.info(f"Proposta #{proposta_id} finalizada com {'sucesso' if success else 'falha'}")
            return success
            
        # Caso contrário, implementar a finalização manualmente
        logger.info("Função SQL não encontrada, implementando finalização manualmente")
        
        # Buscar informações da proposta
        proposta = buscar_proposta(proposta_id, conn)
        if not proposta:
            logger.error(f"Proposta #{proposta_id} não encontrada")
            conn.close()
            return False
            
        # Se usuario_id foi fornecido, verificar se é o proprietário da proposta
        if usuario_id and proposta.get('usuario_id') != usuario_id:
            logger.error(f"Usuário {usuario_id} não é o proprietário da proposta #{proposta_id}")
            conn.close()
            return False
            
        # Atualizar o status da proposta para 'Finalizada'
        data_atual = date.today()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE propostas 
            SET 
                status = 'Finalizada',
                status_execucao = 'Finalizada',
                data_fim = %s,
                data_proposta = COALESCE(data_proposta, data_inicio, %s)
            WHERE id = %s
        """, (data_atual, data_atual, proposta_id))
        
        # Verificar se já existe um lançamento financeiro
        if not verificar_lancamento_financeiro_existe(proposta_id, conn):
            # Criar um lançamento financeiro
            lancamento_id = criar_lancamento_financeiro(proposta_id, proposta, conn)
            logger.info(f"Criado lançamento financeiro #{lancamento_id} para a proposta #{proposta_id}")
            
        cursor.close()
        conn.close()
        
        logger.info(f"Proposta #{proposta_id} finalizada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta #{proposta_id}: {str(e)}")
        if conn:
            conn.close()
        return False

def desassociar_propostas_cliente_sql(cliente_id: int) -> int:
    """
    Desassocia propostas de um cliente utilizando SQL direto
    Retorna o número de propostas atualizadas
    """
    logger.info(f"Desassociando propostas do cliente #{cliente_id}")
    
    # Verificar se a função SQL existe no banco
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return 0
        
    try:
        # Se a função SQL desassociar_propostas_cliente existe, usá-la
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'desassociar_propostas_cliente'
            );
        """)
        result = cursor.fetchone()
        func_exists = False
        if result and len(result) > 0:
            func_exists = result[0]
            
        if func_exists:
            logger.info("Usando função SQL desassociar_propostas_cliente")
            cursor.execute("SELECT desassociar_propostas_cliente(%s)", (cliente_id,))
            result = cursor.fetchone()
            count = 0
            if result and len(result) > 0:
                count = result[0]
                
            cursor.close()
            conn.close()
            
            logger.info(f"{count} propostas desassociadas do cliente #{cliente_id}")
            return count
            
        # Caso contrário, implementar a desassociação manualmente
        logger.info("Função SQL não encontrada, implementando desassociação manualmente")
        
        cursor.execute("""
            UPDATE propostas
            SET status = 'Cancelada', 
                status_execucao = 'Cancelada'
            WHERE cliente_id = %s
            AND status NOT IN ('Finalizada', 'Cancelada')
        """, (cliente_id,))
        
        count = cursor.rowcount
        cursor.close()
        conn.close()
        
        logger.info(f"{count} propostas desassociadas do cliente #{cliente_id}")
        return count
    except Exception as e:
        logger.error(f"Erro ao desassociar propostas do cliente #{cliente_id}: {str(e)}")
        if conn:
            conn.close()
        return 0

# Function replacement
def finalizar_proposta_segura(proposta_id: int) -> Dict[str, Any]:
    """
    Função de compatibilidade para código existente
    
    Implementa a finalização de propostas com geração de lançamentos financeiros:
    
    - Produtos: Receita - categoria venda de produtos
    - Fornecedores: Receita - comissão sobre fornecedores
    - Assistentes: Despesa - pagamento equipe/assistentes
    - Outros: Receita - serviços adicionais
    
    Também registra vendas no módulo de vendas para produtos.
    """
    logger.info(f"Iniciando finalização segura da proposta #{proposta_id}")
    conn = get_db_connection()
    if not conn:
        logger.error("Erro de conexão com banco")
        return {"status": False, "mensagem": "Erro de conexão com banco"}
    
    try:
        cursor = conn.cursor()
        lancamentos_gerados = 0
        resultado = {
            "status": True,
            "mensagem": "Proposta finalizada com sucesso",
            "lancamentos": {
                "gerados": 0,
                "valores": {}
            }
        }

        # Atualizar status da proposta (usando data_fim em vez de data_finalizacao)
        cursor.execute("""
            UPDATE propostas 
            SET status = 'Finalizada',
                status_execucao = 'Finalizada',
                data_fim = CURRENT_DATE
            WHERE id = %s
            RETURNING id, valor, usuario_id, numero, descricao, cliente_id;
        """, (proposta_id,))

        result = cursor.fetchone()
        if not result:
            logger.error(f"Proposta {proposta_id} não encontrada!")
            raise Exception(f"Proposta {proposta_id} não encontrada!")
            
        proposta_info = {
            'id': result[0],
            'valor': result[1],
            'usuario_id': result[2],
            'numero': result[3],
            'descricao': result[4],
            'cliente_id': result[5]
        }
        
        # Buscar nome do cliente para adicionar à descrição dos lançamentos
        cursor.execute("SELECT nome FROM clientes WHERE id = %s", (proposta_info['cliente_id'],))
        cliente_result = cursor.fetchone()
        nome_cliente = cliente_result[0] if cliente_result else "Cliente"
        
        # 1. TRATAMENTO DOS PRODUTOS - Receita (venda de produtos) + Registro no módulo de vendas
        cursor.execute("""
            SELECT id, nome, valor, quantidade, id as produto_id
            FROM produtos_organizadores 
            WHERE proposta_id = %s
        """, (proposta_id,))
        
        produtos = cursor.fetchall()
        valor_total_produtos = 0
        venda_id = None
        
        if produtos and len(produtos) > 0:
            # Calcular valor total
            for produto in produtos:
                produto_id, produto_nome, produto_valor, produto_quantidade, _ = produto
                if produto_valor and produto_quantidade:
                    valor_produto_total = float(produto_valor) * float(produto_quantidade)
                    valor_total_produtos += valor_produto_total
            
            if valor_total_produtos > 0:
                # 1.1. Gerar lançamento financeiro para a venda de produtos
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                     proposta_id, tipo_conta, status, classificacao, usuario_id)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"Venda de produtos - Proposta #{proposta_info['numero']} - {nome_cliente}",
                    valor_total_produtos,
                    "Venda de Produtos",  # Categoria
                    "Produtos da Proposta",  # Subcategoria
                    "Receita",  # Tipo
                    proposta_id,  # origem_id
                    "proposta_produtos",  # origem_tipo
                    proposta_id,  # proposta_id
                    "PF",  # tipo_conta
                    "Pendente",  # status
                    "contas_a_receber",  # classificacao
                    proposta_info['usuario_id']  # usuario_id
                ))
                
                lancamento_id = cursor.fetchone()[0]
                logger.info(f"Lançamento financeiro de Venda de Produtos criado: #{lancamento_id}, Valor: R${valor_total_produtos:.2f}")
                lancamentos_gerados += 1
                
                # 1.2. Criar entrada no módulo de vendas (tabela vendas)
                cursor.execute("""
                    INSERT INTO vendas 
                    (proposta_id, cliente_id, data_venda, valor_total, status, usuario_id)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)
                    RETURNING id
                """, (
                    proposta_id,
                    proposta_info['cliente_id'],
                    valor_total_produtos,
                    "Concluída",
                    proposta_info['usuario_id']
                ))
                
                venda_id = cursor.fetchone()[0]
                logger.info(f"Registro de venda criado: #{venda_id}, Valor: R${valor_total_produtos:.2f}")
                
                # 1.3. Registrar itens da venda (tabela itens_venda)
                for produto in produtos:
                    produto_id, produto_nome, produto_valor, produto_quantidade, _ = produto
                    if produto_valor and produto_quantidade:
                        valor_produto_total = float(produto_valor) * float(produto_quantidade)
                        
                        # Verificar se o produto existe na tabela produtos
                        cursor.execute("""
                            SELECT id FROM produtos WHERE id = %s
                        """, (produto_id,))
                        
                        produto_existe = cursor.fetchone()
                        
                        if produto_existe:
                            # Se o produto existe, adicionar normalmente
                            cursor.execute("""
                                INSERT INTO itens_venda 
                                (venda_id, produto_id, descricao, quantidade, preco_unitario, subtotal, usuario_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                venda_id,
                                produto_id,
                                produto_nome,  # Como descricao
                                produto_quantidade,
                                produto_valor,  # Como preco_unitario
                                valor_produto_total,  # Como subtotal
                                proposta_info['usuario_id']  # usuario_id
                            ))
                            logger.info(f"Item de venda adicionado: Produto #{produto_id} - {produto_nome}")
                        else:
                            # Se o produto não existe, adicionar sem o produto_id (colocar como NULL)
                            logger.warning(f"Produto ID #{produto_id} não encontrado na tabela produtos, adicionando somente a descrição")
                            cursor.execute("""
                                INSERT INTO itens_venda 
                                (venda_id, descricao, quantidade, preco_unitario, subtotal, usuario_id)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                venda_id,
                                produto_nome,  # Como descricao
                                produto_quantidade,
                                produto_valor,  # Como preco_unitario
                                valor_produto_total,  # Como subtotal
                                proposta_info['usuario_id']  # usuario_id
                            ))
                        
                logger.info(f"Todos os itens da venda foram registrados.")
                
                # Adicionar o valor dos produtos ao resultado
                resultado["lancamentos"]["valores"]["produtos"] = valor_total_produtos
        
        # 2. TRATAMENTO DOS FORNECEDORES - Receita (comissão sobre fornecedores)
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor, percentual_comissao 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'FORNECEDOR'
        """, (proposta_id,))
        
        fornecedores = cursor.fetchall()
        valor_total_fornecedores = 0
        
        if fornecedores and len(fornecedores) > 0:
            for fornecedor in fornecedores:
                id_fornecedor, nome_fornecedor, desc_fornecedor, valor_fornecedor, percentual_comissao = fornecedor
                if valor_fornecedor and float(valor_fornecedor) > 0:
                    valor_total_fornecedores += float(valor_fornecedor)
                    
                    # 2.1. Gerar lançamento financeiro para comissão sobre fornecedor
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                         proposta_id, tipo_conta, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Comissão fornecedor {nome_fornecedor} - Proposta #{proposta_info['numero']} - {nome_cliente}",
                        valor_fornecedor,  # Valor total do fornecedor como comissão
                        "Comissão sobre fornecedores",  # Categoria
                        "Comissão de Fornecedor",  # Subcategoria
                        "Receita",  # Tipo
                        id_fornecedor,  # origem_id
                        "comissao_fornecedor",  # origem_tipo
                        proposta_id,  # proposta_id
                        "PF",  # tipo_conta
                        "Pendente",  # status
                        "contas_a_receber",  # classificacao
                        proposta_info['usuario_id']  # usuario_id
                    ))
                    
                    lancamento_id = cursor.fetchone()[0]
                    logger.info(f"Lançamento financeiro de Comissão de Fornecedor criado: #{lancamento_id}, Valor: R${valor_fornecedor:.2f}")
                    lancamentos_gerados += 1
            
            # Adicionar o valor dos fornecedores ao resultado
            resultado["lancamentos"]["valores"]["fornecedores"] = valor_total_fornecedores
        
        # 3. TRATAMENTO DOS ASSISTENTES - Despesa (pagamento equipe/assistentes)
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'ASSISTENTE'
        """, (proposta_id,))
        
        assistentes = cursor.fetchall()
        valor_total_assistentes = 0
        
        if assistentes and len(assistentes) > 0:
            for assistente in assistentes:
                id_assistente, nome_assistente, desc_assistente, valor_assistente = assistente
                if valor_assistente and float(valor_assistente) > 0:
                    valor_total_assistentes += float(valor_assistente)
                    
                    # 3.1. Gerar lançamento financeiro para pagamento de assistente
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                         proposta_id, tipo_conta, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Pagamento assistente {nome_assistente} - Proposta #{proposta_info['numero']} - {nome_cliente}",
                        valor_assistente,
                        "Pagamento Equipe/Assistentes",  # Categoria
                        "Assistentes",  # Subcategoria
                        "Despesa",  # Tipo
                        id_assistente,  # origem_id
                        "pagamento_assistente",  # origem_tipo
                        proposta_id,  # proposta_id
                        "PF",  # tipo_conta
                        "Pendente",  # status
                        "contas_a_pagar",  # classificacao
                        proposta_info['usuario_id']  # usuario_id
                    ))
                    
                    lancamento_id = cursor.fetchone()[0]
                    logger.info(f"Lançamento financeiro de Pagamento de Assistente criado: #{lancamento_id}, Valor: R${valor_assistente:.2f}")
                    lancamentos_gerados += 1
            
            # Adicionar o valor dos assistentes ao resultado
            resultado["lancamentos"]["valores"]["assistentes"] = valor_total_assistentes
        
        # 4. TRATAMENTO DE OUTROS ITENS - Receita (serviços adicionais)
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'OUTRO'
        """, (proposta_id,))
        
        outros_itens = cursor.fetchall()
        valor_total_outros = 0
        
        if outros_itens and len(outros_itens) > 0:
            for outro in outros_itens:
                id_outro, nome_outro, desc_outro, valor_outro = outro
                if valor_outro and float(valor_outro) > 0:
                    valor_total_outros += float(valor_outro)
                    
                    # 4.1. Gerar lançamento financeiro para outros itens (serviços adicionais)
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                         proposta_id, tipo_conta, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Serviço adicional: {desc_outro} - Proposta #{proposta_info['numero']} - {nome_cliente}",
                        valor_outro,
                        "Serviços Adicionais",  # Categoria
                        "Outros Serviços",  # Subcategoria
                        "Receita",  # Tipo
                        id_outro,  # origem_id
                        "servico_adicional",  # origem_tipo
                        proposta_id,  # proposta_id
                        "PF",  # tipo_conta
                        "Pendente",  # status
                        "contas_a_receber",  # classificacao
                        proposta_info['usuario_id']  # usuario_id
                    ))
                    
                    lancamento_id = cursor.fetchone()[0]
                    logger.info(f"Lançamento financeiro de Serviço Adicional criado: #{lancamento_id}, Valor: R${valor_outro:.2f}")
                    lancamentos_gerados += 1
            
            # Adicionar o valor de outros itens ao resultado
            resultado["lancamentos"]["valores"]["outros"] = valor_total_outros
        
        # 5. TRATAMENTO DO VALOR BASE DA PROPOSTA - Receita (serviço principal)
        if proposta_info['valor'] and float(proposta_info['valor']) > 0:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                 proposta_id, tipo_conta, status, classificacao, usuario_id)
                VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"Serviço organização - Proposta #{proposta_info['numero']} - {nome_cliente}",
                proposta_info['valor'],
                "Serviços de Organização",  # Categoria
                "Serviço Principal",  # Subcategoria
                "Receita",  # Tipo
                proposta_id,  # origem_id
                "proposta_base",  # origem_tipo
                proposta_id,  # proposta_id
                "PF",  # tipo_conta
                "Pendente",  # status
                "contas_a_receber",  # classificacao
                proposta_info['usuario_id']  # usuario_id
            ))
            
            lancamento_id = cursor.fetchone()[0]
            logger.info(f"Lançamento financeiro de Serviço Principal criado: #{lancamento_id}, Valor: R${float(proposta_info['valor']):.2f}")
            lancamentos_gerados += 1
            
            # Adicionar o valor base ao resultado
            resultado["lancamentos"]["valores"]["base"] = float(proposta_info['valor'])
        
        # Finalização
        logger.info(f"Proposta #{proposta_id} finalizada. {lancamentos_gerados} lançamentos financeiros gerados.")
        conn.commit()
        
        # Atualizar os resultados
        resultado["lancamentos"]["gerados"] = lancamentos_gerados
        resultado["total_geral"] = (
            float(resultado["lancamentos"]["valores"].get("base", 0)) +
            float(resultado["lancamentos"]["valores"].get("produtos", 0)) +
            float(resultado["lancamentos"]["valores"].get("fornecedores", 0)) +
            float(resultado["lancamentos"]["valores"].get("outros", 0))
        )
        
        return resultado
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro ao finalizar proposta: {str(e)}")
        return {
            "status": False,
            "mensagem": f"Erro ao finalizar proposta: {str(e)}",
            "lancamentos": {
                "gerados": 0,
                "valores": {}
            }
        }

def gerar_lancamentos_proposta_ja_finalizada(proposta_id: int) -> Dict[str, Any]:
    """
    Função para gerar os lançamentos financeiros de uma proposta que já foi finalizada anteriormente.
    Útil quando a proposta foi finalizada diretamente via SQL, sem passar pela lógica de negócios.
    """
    logger.info(f"Gerando lançamentos para proposta já finalizada #{proposta_id}")
    conn = get_db_connection()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return {"status": False, "mensagem": "Não foi possível conectar ao banco de dados"}
    
    try:
        # Verificar se a proposta já está finalizada
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, status_execucao FROM propostas WHERE id = %s
        """, (proposta_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"Proposta #{proposta_id} não encontrada")
            conn.close()
            return {"status": False, "mensagem": f"Proposta #{proposta_id} não encontrada"}
        
        status, status_execucao = result
        
        # Se a proposta não estiver finalizada, retornar erro
        if status != 'Finalizada' or status_execucao != 'Finalizada':
            logger.warning(f"Proposta #{proposta_id} não está finalizada. Status atual: {status}/{status_execucao}")
            conn.close()
            return {"status": False, "mensagem": f"Proposta #{proposta_id} não está finalizada. Status atual: {status}/{status_execucao}"}
        
        # Verificar se já existem lançamentos para a proposta
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s
        """, (proposta_id,))
        
        count = cursor.fetchone()[0]
        
        # Apagar lançamentos existentes se houver
        if count > 0:
            logger.info(f"Removendo {count} lançamentos existentes para proposta #{proposta_id}")
            cursor.execute("DELETE FROM financeiro WHERE proposta_id = %s", (proposta_id,))
        
        # Agora vamos criar novos lançamentos
        resultado = finalizar_proposta_segura(proposta_id)
        
        conn.commit()
        conn.close()
        return resultado
    except Exception as e:
        logger.error(f"Erro ao gerar lançamentos para proposta finalizada #{proposta_id}: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return {"status": False, "mensagem": f"Erro: {str(e)}"}
        
# Original function continues here

    try:
        cursor = conn.cursor()
        lancamentos_gerados = 0
        resultado = {
            "status": True,
            "mensagem": "Proposta finalizada com sucesso",
            "lancamentos": {
                "gerados": 0,
                "valores": {}
            }
        }

        # Atualizar status da proposta (usando data_fim em vez de data_finalizacao)
        cursor.execute("""
            UPDATE propostas 
            SET status = 'Finalizada',
                status_execucao = 'Finalizada',
                data_fim = CURRENT_DATE
            WHERE id = %s
            RETURNING id, valor, usuario_id, numero, descricao, cliente_id;
        """, (proposta_id,))

        result = cursor.fetchone()
        if not result:
            logger.error(f"Proposta #{proposta_id} não encontrada")
            return {"status": False, "mensagem": "Proposta não encontrada"}

        proposta_id, valor, usuario_id, numero, descricao_proposta, cliente_id = result
        logger.info(f"Proposta #{proposta_id} encontrada. Valor: {valor}, Usuario: {usuario_id}")

        # Obter nome do cliente para descrição do lançamento
        cursor.execute("""
            SELECT c.nome FROM clientes c
            JOIN propostas p ON p.cliente_id = c.id
            WHERE p.id = %s
        """, (proposta_id,))
        
        cliente_nome = "Cliente não encontrado"
        result = cursor.fetchone()
        if result is not None:
            try:
                cliente_nome = result[0]
            except (IndexError, TypeError):
                logger.warning(f"Erro ao obter nome do cliente para proposta #{proposta_id}")
        
        # Aqui apenas registramos o valor, não criamos mais o lançamento base automático
        resultado["lancamentos"]["valores"]["base"] = valor
        
        # Calcular valor total da comissão sobre fornecedores (5% para todos os fornecedores)
        cursor.execute("""
            SELECT SUM(valor) FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'FORNECEDOR'
        """, (proposta_id,))
        
        resultado_fornecedores = cursor.fetchone()
        valor_total_fornecedores_raw = resultado_fornecedores[0] if resultado_fornecedores and resultado_fornecedores[0] else 0
        
        # Calcular 5% de comissão sobre o valor total dos fornecedores
        valor_comissao_total = float(valor_total_fornecedores_raw) * 0.05  # 5% como padrão
        
        logger.info(f"Calculando comissão sobre fornecedores: 5% de R${valor_total_fornecedores_raw:.2f} = R${valor_comissao_total:.2f}")
        
        # Criar lançamento de comissão sobre fornecedores com o valor calculado
        cursor.execute("""
            SELECT id FROM financeiro 
            WHERE proposta_id = %s 
            AND categoria = 'Comissão sobre fornecedores'
            AND descricao LIKE %s
        """, (proposta_id, f"%Proposta #{numero}%"))
        
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, subcategoria, 
                tipo, tipo_receita, origem_id, origem_tipo, proposta_id, 
                tipo_conta, status, classificacao, usuario_id)
                VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"Comissão de fornecedores - Proposta #{numero} - {cliente_nome}",
                valor_comissao_total,  # Valor calculado ou específico
                "Comissão sobre fornecedores",
                "Fornecedores",
                "Receita",
                "comissao",
                cliente_id,
                "cliente",
                proposta_id,
                "PF",
                "Pendente", 
                "receita",
                usuario_id
            ))
            lancamentos_gerados += 1
            logger.info(f"Lançamento de comissão sobre fornecedores criado para proposta #{numero} no valor de R${valor_comissao_total:.2f}")
        
        # Calcular valor total dos assistentes
        cursor.execute("""
            SELECT SUM(valor) FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'ASSISTENTE'
        """, (proposta_id,))
        
        resultado_assistentes = cursor.fetchone()
        valor_total_assistentes_raw = resultado_assistentes[0] if resultado_assistentes and resultado_assistentes[0] else 0
        
        # Registrar o valor total dos assistentes no log
        logger.info(f"Valor total calculado para assistentes na proposta #{proposta_id}: R${valor_total_assistentes_raw:.2f}")
        
        # Criar lançamento de pagamento equipe/assistentes com o valor calculado
        cursor.execute("""
            SELECT id FROM financeiro 
            WHERE proposta_id = %s 
            AND categoria = 'Pagamento Equipe/Assistentes'
            AND subcategoria = 'Assistentes'
            AND descricao LIKE %s
        """, (proposta_id, f"%Proposta #{numero}%"))
        
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, subcategoria, 
                tipo, origem_id, origem_tipo, proposta_id, 
                tipo_conta, status, classificacao, usuario_id)
                VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"Pagamento Equipe/Assistentes - Proposta #{numero} - {cliente_nome}",
                valor_total_assistentes_raw,  # Valor calculado ou específico
                "Pagamento Equipe/Assistentes",
                "Assistentes",
                "Despesa",
                cliente_id,
                "cliente",
                proposta_id,
                "PF",
                "Pendente", 
                "despesa_a_pagar",
                usuario_id
            ))
            lancamentos_gerados += 1
            logger.info(f"Lançamento de pagamento equipe/assistentes criado para proposta #{numero} no valor de R${valor_total_assistentes_raw:.2f}")
        
        # 1. Buscar acréscimos do tipo FORNECEDOR e gerar comissões
        cursor.execute("""
            SELECT id, fornecedor, valor, percentual_comissao, fornecedor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'FORNECEDOR'
        """, (proposta_id,))
        
        fornecedores = cursor.fetchall()
        valor_total_fornecedores = 0
        
        for fornecedor in fornecedores:
            id_fornecedor, desc_fornecedor, valor_fornecedor, percentual_comissao, nome_fornecedor = fornecedor
            if valor_fornecedor and float(valor_fornecedor) > 0:
                valor_total_fornecedores += float(valor_fornecedor)
                
                # Se não há percentual definido mas existe um fornecedor específico, definir um valor padrão
                if (not percentual_comissao or percentual_comissao == '') and nome_fornecedor:
                    nome_fornecedor_lower = nome_fornecedor.lower() if nome_fornecedor else ''
                    if 'multi' in nome_fornecedor_lower:
                        percentual_comissao = 5.0  # 5% para Multicoisas
                
                # Usar comissão padrão de 5% caso não esteja definido
                if not percentual_comissao or not str(percentual_comissao).strip():
                    percentual_comissao = 5.0
                    logger.info(f"Usando taxa de comissão padrão de 5% para o fornecedor {nome_fornecedor}")
                
                # Calcular o valor da comissão
                if float(percentual_comissao) > 0:
                    valor_comissao = float(valor_fornecedor) * (float(percentual_comissao) / 100)
                    logger.info(f"Calculado valor de comissão: {valor_comissao} ({percentual_comissao}% de {valor_fornecedor})")
                    
                    # Verificar se já existe transação para este fornecedor
                    logger.debug(f"Verificando transação existente para fornecedor {nome_fornecedor} (ID={id_fornecedor})")
                    cursor.execute("""
                        SELECT id FROM financeiro 
                        WHERE proposta_id = %s AND origem_tipo = 'comissao_fornecedor' AND origem_id = %s
                    """, (proposta_id, id_fornecedor))
                    fornecedor_existente = cursor.fetchone()
                    logger.debug(f"Transação para fornecedor {nome_fornecedor}: {'já existe' if fornecedor_existente else 'não existe'}")
                    
                    if fornecedor_existente is None and valor_comissao > 0:
                        # Criar lançamento de comissão
                        cursor.execute("""
                            INSERT INTO financeiro 
                            (descricao, valor, data, categoria, subcategoria, tipo, 
                             tipo_receita, origem_id, origem_tipo, proposta_id, 
                             tipo_conta, status, classificacao, usuario_id)
                            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            f"Comissão de {percentual_comissao}% - {desc_fornecedor} - Proposta #{numero}",
                            valor_comissao,
                            "Comissão sobre fornecedores",
                            "Comissão de Fornecedor",
                            "Receita",
                            "comissao",
                            id_fornecedor,
                            "comissao_fornecedor",
                            proposta_id,
                            "PF",
                            "Pendente",
                            "contas_a_receber",
                            usuario_id
                        ))
                        lancamentos_gerados += 1
        
        resultado["lancamentos"]["valores"]["fornecedores"] = valor_total_fornecedores
        
        # 2. Buscar acréscimos do tipo OUTRO e gerar lançamentos
        cursor.execute("""
            SELECT id, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'OUTRO'
        """, (proposta_id,))
        
        outros = cursor.fetchall()
        valor_total_outros = 0
        
        for outro in outros:
            id_outro, desc_outro, valor_outro = outro
            if valor_outro and float(valor_outro) > 0:
                valor_total_outros += float(valor_outro)
                
                # Verificar se já existe uma transação para este acréscimo
                cursor.execute("""
                    SELECT id FROM financeiro 
                    WHERE proposta_id = %s AND origem_tipo = 'acrescimo_outro' AND origem_id = %s
                """, (proposta_id, id_outro))
                
                outro_existente = cursor.fetchone()
                logger.debug(f"Transação para outro '{desc_outro}' (ID={id_outro}): {'já existe' if outro_existente else 'não existe'}")
                
                if outro_existente is None:
                    # Criar lançamento para o acréscimo
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, 
                         tipo_receita, origem_id, origem_tipo, proposta_id, 
                         tipo_conta, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        f"{desc_outro} - Proposta #{numero}",
                        valor_outro,
                        "Serviços Adicionais",
                        "Outros Acréscimos",
                        "Receita",
                        "Serviço",
                        id_outro,
                        "acrescimo_outro",
                        proposta_id,
                        "PF",
                        "Pendente",
                        "contas_a_receber",
                        usuario_id
                    ))
                    lancamentos_gerados += 1
        
        resultado["lancamentos"]["valores"]["outros"] = valor_total_outros
        
        # 3. Buscar acréscimos do tipo ASSISTENTE e gerar lançamentos
        cursor.execute("""
            SELECT id, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'ASSISTENTE'
        """, (proposta_id,))
        
        assistentes = cursor.fetchall()
        valor_total_assistentes = 0
        
        for assistente in assistentes:
            id_assistente, desc_assistente, valor_assistente = assistente
            if valor_assistente and float(valor_assistente) > 0:
                valor_total_assistentes += float(valor_assistente)
                
                # Verificar se já existe transação para este assistente
                cursor.execute("""
                    SELECT id FROM financeiro 
                    WHERE proposta_id = %s AND origem_tipo = 'acrescimo_assistente' AND origem_id = %s
                """, (proposta_id, id_assistente))
                
                assistente_existente = cursor.fetchone()
                logger.info(f"Verificando assistente {desc_assistente} (ID={id_assistente}): {'já existe' if assistente_existente else 'não existe'}")
                
                if assistente_existente is None:
                    # Criar lançamento para o assistente
                    try:
                        logger.info(f"Tentando criar lançamento para assistente com SQL: INSERT INTO financeiro (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, proposta_id, tipo_conta, status, classificacao, usuario_id)")
                        
                        # Lista de parâmetros para debug
                        params = [
                            f"Assistente: {desc_assistente} - Proposta #{numero}",
                            valor_assistente,
                            "Pagamento Equipe/Assistentes",
                            "Assistentes",
                            "Despesa",  # Alterado de "despesa_a_pagar" para "Despesa"
                            id_assistente,
                            "acrescimo_assistente",
                            proposta_id,
                            "PF",
                            "Pendente",
                            "contas_a_pagar",
                            usuario_id
                        ]
                        # Logar cada parâmetro individualmente para melhor legibilidade
                        for i, param in enumerate(params):
                            logger.info(f"Parâmetro {i+1}: {param}")
                        
                        # Executar a query
                        cursor.execute("""
                            INSERT INTO financeiro 
                            (descricao, valor, data, categoria, subcategoria, tipo, 
                             origem_id, origem_tipo, proposta_id, 
                             tipo_conta, status, classificacao, usuario_id)
                            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, params)
                        
                        result = cursor.fetchone()
                        if result:
                            lancamento_id = result[0]
                            logger.info(f"Lançamento de despesa criado para assistente {desc_assistente} no valor de {valor_assistente} com ID {lancamento_id}")
                        else:
                            logger.error(f"Nenhum ID retornado após inserção do lançamento para assistente {desc_assistente}")
                        
                    except Exception as e:
                        logger.error(f"Erro ao criar lançamento para assistente {desc_assistente}: {str(e)}")
                        # Imprimir o rastreamento completo da exceção
                        import traceback
                        logger.error(f"Traceback completo: {traceback.format_exc()}")
                    lancamentos_gerados += 1
        
        resultado["lancamentos"]["valores"]["assistentes"] = valor_total_assistentes
        
        # 4. Registrar produtos da proposta
        cursor.execute("""
            SELECT id, nome, valor, quantidade, id as produto_id
            FROM produtos_organizadores 
            WHERE proposta_id = %s
        """, (proposta_id,))
        
        produtos = cursor.fetchall()
        valor_total_produtos = 0
        venda_id = None
        
        if produtos and len(produtos) > 0:
            # Calcular valor total
            for produto in produtos:
                id_prod, nome_prod, valor_prod, quantidade, produto_id = produto
                if valor_prod and quantidade:
                    valor_total_produtos += float(valor_prod) * float(quantidade)
            
            # Verificar se já existe uma venda
            cursor.execute("""
                SELECT id FROM vendas WHERE proposta_id = %s
            """, (proposta_id,))
            
            venda_existente = cursor.fetchone()
            
            if venda_existente:
                # Remover venda existente
                venda_id = venda_existente[0]
                cursor.execute("DELETE FROM itens_venda WHERE venda_id = %s", (venda_id,))
                cursor.execute("DELETE FROM financeiro WHERE origem_id = %s AND origem_tipo = 'venda'", (venda_id,))
                cursor.execute("DELETE FROM vendas WHERE id = %s", (venda_id,))
            
            # Criar nova venda
            cursor.execute("""
                INSERT INTO vendas
                (cliente_id, proposta_id, data_venda, valor_total, status, forma_pagamento, observacoes, usuario_id)
                VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                cliente_id,
                proposta_id,
                valor_total_produtos,
                "Concluída",
                "Proposta",
                f"Venda gerada automaticamente da proposta #{numero}",
                usuario_id or None
            ))
            
            resultado_venda = cursor.fetchone()
            if resultado_venda is not None:
                venda_id = resultado_venda[0]
            else:
                logger.error("Erro: nenhum ID de venda retornado após inserção")
                venda_id = None
            
            # Adicionar itens à venda apenas se tiver um venda_id válido
            if venda_id is not None:
                for produto in produtos:
                    id_prod, nome_prod, valor_prod, quantidade, produto_id = produto
                    if valor_prod and quantidade:
                        subtotal = float(valor_prod) * float(quantidade)
                        cursor.execute("""
                            INSERT INTO itens_venda
                            (venda_id, produto_id, quantidade, preco_unitario, subtotal, descricao)
                            VALUES (%s, NULL, %s, %s, %s, %s)
                        """, (
                            venda_id,
                            quantidade,
                            valor_prod,
                            subtotal,
                            nome_prod
                        ))
            
            # Criar lançamento financeiro para a venda apenas se tiver um venda_id válido
            if venda_id is not None:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, subcategoria, tipo, 
                     tipo_receita, origem_id, origem_tipo, proposta_id, 
                     tipo_conta, status, classificacao, usuario_id)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"Produtos da proposta #{numero}",
                    valor_total_produtos,
                    "Venda Produtos",
                    "Produtos",
                    "Receita",
                    "Venda",
                    venda_id,
                    "venda",
                    proposta_id,
                    "PF",
                    "Pendente",
                    "contas_a_receber",
                    usuario_id
                ))
                lancamentos_gerados += 1
                logger.info(f"Lançamento financeiro para produtos criado no valor de {valor_total_produtos}")
        
        resultado["lancamentos"]["valores"]["produtos"] = valor_total_produtos
        resultado["lancamentos"]["gerados"] = lancamentos_gerados
        
        conn.commit()
        return resultado
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta: {str(e)}")
        conn.rollback()
        return {"status": False, "mensagem": f"Erro: {str(e)}"}
    finally:
        if conn:
            conn.close()