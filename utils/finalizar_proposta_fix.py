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

logging.basicConfig(level=logging.INFO)
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
    """Função de compatibilidade para código existente"""
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
        
        # 1. Buscar acréscimos do tipo FORNECEDOR e gerar comissões
        cursor.execute("""
            SELECT id, fornecedor, valor, percentual_comissao 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'FORNECEDOR'
        """, (proposta_id,))
        
        fornecedores = cursor.fetchall()
        valor_total_fornecedores = 0
        
        for fornecedor in fornecedores:
            id_fornecedor, desc_fornecedor, valor_fornecedor, percentual_comissao = fornecedor
            if valor_fornecedor and float(valor_fornecedor) > 0:
                valor_total_fornecedores += float(valor_fornecedor)
                
                # Se tiver percentual de comissão, criar lançamento
                if percentual_comissao and float(percentual_comissao) > 0:
                    valor_comissao = float(valor_fornecedor) * (float(percentual_comissao) / 100)
                    
                    # Verificar se já existe transação para este fornecedor
                    cursor.execute("""
                        SELECT id FROM financeiro 
                        WHERE proposta_id = %s AND origem_tipo = 'comissao_fornecedor' AND origem_id = %s
                    """, (proposta_id, id_fornecedor))
                    
                    if cursor.fetchone() is None and valor_comissao > 0:
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
                
                if cursor.fetchone() is None:
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
                
                if cursor.fetchone() is None:
                    # Criar lançamento para o assistente
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, 
                         origem_id, origem_tipo, proposta_id, 
                         tipo_conta, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        f"Assistente: {desc_assistente} - Proposta #{numero}",
                        valor_assistente,
                        "Pagamento Equipe/Assistentes",
                        "Assistentes",
                        "despesa_a_pagar",
                        id_assistente,
                        "acrescimo_assistente",
                        proposta_id,
                        "PF",
                        "Pendente",
                        "contas_a_pagar",
                        usuario_id
                    ))
                    lancamentos_gerados += 1
        
        resultado["lancamentos"]["valores"]["assistentes"] = valor_total_assistentes
        
        # 4. Registrar produtos da proposta
        cursor.execute("""
            SELECT id, nome, valor, quantidade, produto_id
            FROM produtos_proposta 
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
                usuario_id
            ))
            
            venda_id = cursor.fetchone()[0]
            
            # Adicionar itens à venda
            for produto in produtos:
                id_prod, nome_prod, valor_prod, quantidade, produto_id = produto
                if valor_prod and quantidade:
                    subtotal = float(valor_prod) * float(quantidade)
                    cursor.execute("""
                        INSERT INTO itens_venda
                        (venda_id, produto_id, quantidade, preco_unitario, subtotal, descricao)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        venda_id,
                        produto_id,
                        quantidade,
                        valor_prod,
                        subtotal,
                        nome_prod
                    ))
            
            # Criar lançamento financeiro para a venda
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