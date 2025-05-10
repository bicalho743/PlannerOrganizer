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
        logger.error(f"Erro ao verificar existência da função: {str(e)}")
        if close_conn and conn:
            conn.close()
        return False

def finalizar_proposta_sql(proposta_id: int) -> Dict[str, Any]:
    """
    Finaliza uma proposta usando função SQL dedicada, se disponível
    
    Args:
        proposta_id: ID da proposta a ser finalizada
        
    Returns:
        dict: Resultado da operação
    """
    logger.info(f"Iniciando finalização da proposta #{proposta_id}")
    
    conn = get_db_connection()
    if not conn:
        return {"status": False, "mensagem": "Erro ao conectar ao banco de dados"}
    
    try:
        # Verificar se a função existe
        func_exists = verificar_funcao_sql_existe(conn)
        
        cursor = conn.cursor()
        if func_exists:
            # Usando a função SQL dedicada
            logger.info("Usando função SQL finalizar_proposta")
            cursor.execute("SELECT finalizar_proposta(%s)", (proposta_id,))
            result = cursor.fetchone()
            success = False
            message = "Erro ao finalizar proposta"
            
            if result and len(result) > 0:
                success = True
                message = "Proposta finalizada com sucesso"
            
            cursor.close()
            conn.commit()
            conn.close()
            
            return {"status": success, "mensagem": message}
        
        # Sem função SQL, usar alternativa Python
        logger.info("Função SQL não encontrada, usando implementação Python")
        resultado = finalizar_proposta_segura(proposta_id)
        conn.close()
        return resultado
    
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta via SQL: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return {"status": False, "mensagem": f"Erro ao finalizar proposta: {str(e)}"}

def cancelar_proposta(proposta_id: int) -> Dict[str, Any]:
    """
    Cancela uma proposta, alterando seu status
    
    Args:
        proposta_id: ID da proposta a ser cancelada
        
    Returns:
        dict: Resultado da operação
    """
    logger.info(f"Cancelando proposta #{proposta_id}")
    
    conn = get_db_connection()
    if not conn:
        return {"status": False, "mensagem": "Erro ao conectar ao banco de dados"}
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE propostas 
            SET status = 'Cancelada', 
                status_execucao = 'Cancelada',
                data_cancelamento = CURRENT_DATE
            WHERE id = %s
            RETURNING id;
        """, (proposta_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.rollback()
            conn.close()
            return {"status": False, "mensagem": f"Proposta #{proposta_id} não encontrada"}
        
        conn.commit()
        conn.close()
        
        return {"status": True, "mensagem": f"Proposta #{proposta_id} cancelada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao cancelar proposta: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return {"status": False, "mensagem": f"Erro ao cancelar proposta: {str(e)}"}

def desassociar_propostas_cliente(cliente_id: int) -> int:
    """
    Desassocia todas as propostas de um cliente, tornando-as canceladas
    
    Args:
        cliente_id: ID do cliente
        
    Returns:
        int: Número de propostas desassociadas
    """
    logger.info(f"Desassociando propostas do cliente #{cliente_id}")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Erro ao conectar com o banco de dados")
        return 0
    
    try:
        cursor = conn.cursor()
        
        # Verificar se existe função SQL para desassociar
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

        # Atualizar status da proposta para garantir que apareça na aba Finalizadas
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
        nome_cliente = "Cliente não identificado"
        if proposta_info['cliente_id']:
            cursor.execute("SELECT nome FROM clientes WHERE id = %s", (proposta_info['cliente_id'],))
            cliente_result = cursor.fetchone()
            if cliente_result and cliente_result[0]:
                nome_cliente = cliente_result[0]
        
        # Padrão para valores
        resultado["lancamentos"]["valores"] = {
            "produtos": 0,
            "fornecedores": 0,
            "assistentes": 0,
            "outros": 0,
            "base": 0
        }
        
        # 0. VERIFICAR E CRIAR LANÇAMENTO BASE (se não existir)
        # Verificar se já existe um lançamento base para esta proposta
        cursor.execute("""
            SELECT id FROM financeiro 
            WHERE proposta_id = %s AND origem_tipo = 'proposta_base'
        """, (proposta_id,))
        
        lancamento_base_existente = cursor.fetchone()
        
        if not lancamento_base_existente:
            # Criar lançamento base da proposta
            logger.info(f"Criando lançamento base para proposta #{proposta_info['numero']} - R$ {proposta_info['valor']}")
            
            cursor.execute("""
                INSERT INTO financeiro 
                (descricao, valor, data, categoria, subcategoria, 
                tipo, proposta_id, status, classificacao, usuario_id, origem_tipo, origem_id)
                VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"Proposta base #{proposta_info['numero']} - {nome_cliente}",
                proposta_info['valor'],
                "Serviços de organização",
                "Valor a receber",
                "Receita",
                proposta_id,
                "Pendente",
                "contas_a_receber",
                proposta_info['usuario_id'],
                "proposta_base",
                proposta_id
            ))
            
            lancamento_id = cursor.fetchone()[0]
            lancamentos_gerados += 1
            logger.info(f"Lançamento principal criado (ID: {lancamento_id})")
        else:
            logger.info(f"Lançamento base da proposta já existe (ID: {lancamento_base_existente[0]})")
            
        # Registrar valor base no resultado para controle
        resultado["lancamentos"]["valores"]["base"] = proposta_info['valor']
        
        # 1. TRATAMENTO DOS PRODUTOS - Receita (venda de produtos) e registro no módulo de vendas
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'PRODUTO'
        """, (proposta_id,))
        
        produtos = cursor.fetchall()
        valor_total_produtos = 0
        
        if produtos and len(produtos) > 0:
            # 1.1. Gerar lançamento financeiro para vendas de produtos
            for produto in produtos:
                produto_id, produto_nome, descricao_produto, produto_valor = produto
                if produto_valor and float(produto_valor) > 0:
                    # Como não temos quantidade na tabela, consideramos 1 unidade
                    produto_quantidade = 1
                    valor_produto_total = float(produto_valor)
                    valor_total_produtos += valor_produto_total
            
            if valor_total_produtos > 0:
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
                    "Produtos",  # Subcategoria
                    "Receita",  # Tipo
                    proposta_id,  # origem_id
                    "venda_produtos",  # origem_tipo
                    proposta_id,  # proposta_id
                    "PF",  # tipo_conta
                    "Pendente",  # status
                    "contas_a_receber",  # classificacao
                    proposta_info['usuario_id']  # usuario_id
                ))
                
                lancamento_id = cursor.fetchone()[0]
                logger.info(f"Lançamento financeiro de Venda de Produtos criado: #{lancamento_id}, Valor: R${valor_total_produtos:.2f}")
                lancamentos_gerados += 1
                
                # 1.2. Registrar venda no módulo de vendas
                cursor.execute("""
                    INSERT INTO vendas 
                    (descricao, valor_total, data_venda, cliente_id, proposta_id, usuario_id, status)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"Venda da proposta #{proposta_info['numero']} - {nome_cliente}",
                    valor_total_produtos,
                    proposta_info['cliente_id'],
                    proposta_id,
                    proposta_info['usuario_id'],
                    "Confirmada"
                ))
                
                venda_id = cursor.fetchone()[0]
                logger.info(f"Registro de venda criado: #{venda_id}, Valor: R${valor_total_produtos:.2f}")
                
                # 1.3. Registrar itens da venda (tabela itens_venda)
                for produto in produtos:
                    produto_id, produto_nome, descricao_produto, produto_valor = produto
                    if produto_valor and float(produto_valor) > 0:
                        # Como não temos quantidade na tabela, consideramos 1 unidade
                        produto_quantidade = 1
                        valor_produto_total = float(produto_valor)
                        
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
                    # Calcular o valor da comissão aplicando o percentual
                    valor_comissao = float(valor_fornecedor)
                    if percentual_comissao and float(percentual_comissao) > 0:
                        # Se tiver percentual de comissão, aplicar ao valor do fornecedor
                        valor_comissao = float(valor_fornecedor) * (float(percentual_comissao) / 100)
                        logger.info(f"Comissão calculada: {valor_comissao:.2f} ({percentual_comissao}% de {valor_fornecedor})")
                    
                    valor_total_fornecedores += valor_comissao
                    
                    # 2.1. Criar lançamento financeiro para comissão sobre fornecedor
                    logger.info(f"Criando lançamento para comissão sobre fornecedor {nome_fornecedor}: R${valor_comissao:.2f}")
                    
                    # Verificar se já existe uma transação de comissão para este fornecedor
                    cursor.execute("""
                        SELECT id FROM financeiro 
                        WHERE proposta_id = %s 
                        AND origem_tipo = 'comissao_fornecedor' 
                        AND descricao LIKE %s
                    """, (proposta_id, f"%{nome_fornecedor}%"))
                    
                    transacao_comissao_existente = cursor.fetchone()
                    
                    if not transacao_comissao_existente:
                        # Criar o lançamento de comissão
                        cursor.execute("""
                            INSERT INTO financeiro 
                            (descricao, valor, data, categoria, subcategoria, 
                            tipo, proposta_id, status, classificacao, usuario_id, origem_tipo, origem_id)
                            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            f"Comissão de {percentual_comissao or 5}% - Fornecedor {nome_fornecedor} - Proposta #{proposta_info['numero']}",
                            valor_comissao,
                            "Comissão sobre fornecedores",
                            "Comissão de Fornecedor",
                            "Receita",
                            proposta_id,
                            "Pendente",
                            "contas_a_receber",
                            proposta_info['usuario_id'],
                            "comissao_fornecedor",
                            id_fornecedor
                        ))
                        
                        lancamento_id = cursor.fetchone()[0]
                        lancamentos_gerados += 1
                        logger.info(f"Lançamento de comissão criado (ID: {lancamento_id}) para fornecedor {nome_fornecedor}")
                    else:
                        logger.info(f"Lançamento de comissão para fornecedor {nome_fornecedor} já existe (ID: {transacao_comissao_existente[0]})")
            
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
                    
                    # 3.1. Criar lançamento financeiro para pagamento de assistente
                    logger.info(f"Criando lançamento para assistente {nome_assistente}: R${valor_assistente:.2f}")
                    
                    # Verificar se já existe uma transação para este assistente
                    cursor.execute("""
                        SELECT id FROM financeiro 
                        WHERE proposta_id = %s 
                        AND origem_tipo = 'acrescimo_assistente' 
                        AND origem_id = %s
                    """, (proposta_id, id_assistente))
                    
                    transacao_assistente_existente = cursor.fetchone()
                    
                    if not transacao_assistente_existente:
                        # Criar o lançamento para o assistente
                        cursor.execute("""
                            INSERT INTO financeiro 
                            (descricao, valor, data, categoria, subcategoria, 
                            tipo, proposta_id, status, classificacao, usuario_id, origem_tipo, origem_id)
                            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            f"Assistente: {nome_assistente or desc_assistente} - Proposta #{proposta_info['numero']}",
                            valor_assistente,
                            "Pagamento Equipe/Assistentes",
                            "Assistentes", 
                            "Despesa",
                            proposta_id,
                            "Pendente",
                            "contas_a_pagar",
                            proposta_info['usuario_id'],
                            "acrescimo_assistente",
                            id_assistente
                        ))
                        
                        lancamento_id = cursor.fetchone()[0]
                        lancamentos_gerados += 1
                        logger.info(f"Lançamento para assistente criado (ID: {lancamento_id}) para {nome_assistente or desc_assistente}")
                    else:
                        logger.info(f"Lançamento para assistente {nome_assistente or desc_assistente} já existe (ID: {transacao_assistente_existente[0]})")
            
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
                    
                    # 4.1. Verificar se já existe lançamento para este serviço adicional
                    cursor.execute("""
                        SELECT id FROM financeiro 
                        WHERE proposta_id = %s 
                        AND origem_tipo = 'servico_adicional' 
                        AND origem_id = %s
                    """, (proposta_id, id_outro))
                    
                    transacao_servico_existente = cursor.fetchone()
                    
                    if not transacao_servico_existente:
                        # Gerar lançamento financeiro para outros itens (serviços adicionais)
                        cursor.execute("""
                            INSERT INTO financeiro 
                            (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                             proposta_id, status, classificacao, usuario_id)
                            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                            "Pendente",  # status
                            "contas_a_receber",  # classificacao
                            proposta_info['usuario_id']  # usuario_id
                        ))
                        
                        lancamento_id = cursor.fetchone()[0]
                        lancamentos_gerados += 1
                        logger.info(f"Lançamento para serviço adicional criado (ID: {lancamento_id}) para {desc_outro}")
                    else:
                        logger.info(f"Lançamento para serviço adicional {desc_outro} já existe (ID: {transacao_servico_existente[0]})")
            
            # Adicionar o valor de outros itens ao resultado
            resultado["lancamentos"]["valores"]["outros"] = valor_total_outros
        
        # 5. TRATAMENTO DO VALOR BASE DA PROPOSTA - Já foi verificado e criado no início da função
        # O valor da proposta base já está no resultado para controle
        # resultado["lancamentos"]["valores"]["base"] = proposta_info['valor']
        
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
        if count > 0:
            logger.warning(f"Proposta #{proposta_id} já possui {count} lançamentos financeiros")
            conn.close()
            return {"status": False, "mensagem": f"Proposta #{proposta_id} já possui {count} lançamentos financeiros"}
        
        # Proposta já está finalizada mas não tem lançamentos, gerar os lançamentos
        resultado = finalizar_proposta_segura(proposta_id)
        
        conn.commit()
        conn.close()
        return resultado
    except Exception as e:
        logger.error(f"Erro ao gerar lançamentos para proposta já finalizada: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return {"status": False, "mensagem": f"Erro ao gerar lançamentos: {str(e)}"}