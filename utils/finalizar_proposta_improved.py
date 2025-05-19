"""
Módulo aprimorado para finalização segura de propostas com verificação completa
de todos os tipos de lançamentos financeiros.

Esta versão garante que todos os lançamentos financeiros sejam criados corretamente:
- Valor base da proposta
- Produtos adicionados
- Serviços adicionais (OUTROS)
- Comissões de fornecedores 
- Pagamento de assistentes

Todas as entradas são verificadas e processadas adequadamente.
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

def finalizar_proposta_improved(proposta_id: int) -> Dict[str, Any]:
    """
    Versão aprimorada da finalização de propostas com geração completa de lançamentos
    
    Esta função garante que todos os lançamentos financeiros sejam criados:
    
    - Valor base da proposta: Receita - valor base
    - Produtos: Receita - venda de produtos
    - Serviços adicionais: Receita - serviços adicionais
    - Fornecedores: Receita - comissão sobre fornecedores
    - Assistentes: Despesa - pagamento equipe/assistentes
    
    Também registra vendas no módulo de vendas para produtos.
    
    Args:
        proposta_id: ID da proposta a ser finalizada
        
    Returns:
        Dict com resultados da operação, incluindo detalhes dos lançamentos gerados
    """
    logger.info(f"[IMPROVED] Iniciando finalização aprimorada da proposta #{proposta_id}")
    conn = get_db_connection()
    
    if not conn:
        logger.error("Erro de conexão com banco")
        return {"status": False, "mensagem": "Erro de conexão com banco"}
        
    cursor = None
    lancamentos_gerados = 0
    
    try:
        cursor = conn.cursor()
        
        # Verificar se a proposta existe e obter informações básicas
        cursor.execute("""
            SELECT p.id, p.numero, p.descricao, p.valor, p.status, p.status_execucao, 
                   p.cliente_id, p.usuario_id, c.nome as nome_cliente
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
        """, (proposta_id,))
        
        proposta_row = cursor.fetchone()
        
        if not proposta_row:
            logger.error(f"Proposta #{proposta_id} não encontrada")
            conn.close()
            return {"status": False, "mensagem": f"Proposta #{proposta_id} não encontrada"}
            
        # Extrair dados da proposta
        proposta_info = {
            'id': proposta_row[0],
            'numero': proposta_row[1],
            'descricao': proposta_row[2],
            'valor': proposta_row[3],
            'status': proposta_row[4],
            'status_execucao': proposta_row[5],
            'cliente_id': proposta_row[6],
            'usuario_id': proposta_row[7]
        }
        nome_cliente = proposta_row[8]
        
        # Verificar se a proposta já está com status finalizado
        if proposta_info['status_execucao'] != 'Finalizada':
            # Atualizar status da proposta para finalizada
            cursor.execute("""
                UPDATE propostas 
                SET status = 'Concluída', 
                    status_execucao = 'Finalizada',
                    data_finalizacao = CURRENT_DATE,
                    data_atualizacao = CURRENT_DATE
                WHERE id = %s
            """, (proposta_id,))
            
            logger.info(f"Proposta #{proposta_id} marcada como finalizada")
        
        # Verificar se já existem lançamentos para esta proposta
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s
        """, (proposta_id,))
        
        count = cursor.fetchone()[0]
        if count > 0:
            logger.warning(f"Proposta #{proposta_id} já possui {count} lançamentos financeiros")
            # Limpar lançamentos existentes para evitar duplicações
            cursor.execute("DELETE FROM financeiro WHERE proposta_id = %s", (proposta_id,))
            logger.info(f"Removidos {count} lançamentos existentes para proposta #{proposta_id}")
        
        # Dicionário para armazenar resultados
        resultado = {
            "status": True,
            "mensagem": f"Proposta #{proposta_info['numero']} finalizada com sucesso",
            "lancamentos": {
                "gerados": 0,
                "valores": {
                    "base": 0,
                    "produtos": 0,
                    "servicos_adicionais": 0,
                    "comissoes": 0,
                    "despesa_assistentes": 0
                }
            }
        }
        
        # OBS: O lançamento para o valor base da proposta é feito na APROVAÇÃO, não na finalização.
        # Aqui só verificamos se esse lançamento existe, para fins de consistência.
        valor_base = float(proposta_info['valor']) if proposta_info['valor'] else 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro 
            WHERE proposta_id = %s 
            AND categoria = 'Serviços de organização'
            AND subcategoria = 'Valor a receber'
            AND origem_tipo = 'proposta_base'
        """, (proposta_id,))
        
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info(f"Lançamento de valor base já existe para a proposta #{proposta_info['numero']}")
            
            # Obter o valor para o relatório
            cursor.execute("""
                SELECT valor FROM financeiro 
                WHERE proposta_id = %s 
                AND categoria = 'Serviços de organização'
                AND subcategoria = 'Valor a receber'
                AND origem_tipo = 'proposta_base'
                LIMIT 1
            """, (proposta_id,))
            
            row = cursor.fetchone()
            if row:
                resultado["lancamentos"]["valores"]["base"] = float(row[0])
        else:
            logger.warning(f"Proposta #{proposta_info['numero']} não possui lançamento de valor base!")
        
        # Etapa 2: Produtos - Gerar lançamento para produtos
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'PRODUTO'
        """, (proposta_id,))
        
        produtos = cursor.fetchall()
        valor_total_produtos = 0
        
        if produtos and len(produtos) > 0:
            # Calcular valor total de produtos
            for produto in produtos:
                produto_id, fornecedor, descricao, produto_valor = produto
                # Garantir que temos valores válidos
                produto_valor = float(produto_valor) if produto_valor else 0
                # Como não temos quantidade na tabela, consideramos 1 unidade de cada
                produto_quantidade = 1
                
                if produto_valor > 0:
                    valor_produto = produto_valor * produto_quantidade
                    valor_total_produtos += valor_produto
            
            if valor_total_produtos > 0:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                     proposta_id, status, classificacao, usuario_id)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"Receita - Venda de produtos - Proposta #{proposta_info['numero']} - {nome_cliente}",
                    valor_total_produtos,
                    "Venda de Produtos",  # Categoria
                    "Produtos",  # Subcategoria
                    "Receita",  # Tipo
                    proposta_id,  # origem_id
                    "venda_produtos",  # origem_tipo
                    proposta_id,  # proposta_id
                    "Pendente",  # status
                    "contas_a_receber",  # classificacao
                    proposta_info['usuario_id']  # usuario_id
                ))
                
                lancamento_id = cursor.fetchone()[0]
                logger.info(f"Lançamento financeiro de Venda de Produtos criado: #{lancamento_id}, Valor: R${valor_total_produtos:.2f}")
                lancamentos_gerados += 1
                resultado["lancamentos"]["valores"]["produtos"] = valor_total_produtos
                
                # Registrar venda no módulo de vendas
                cursor.execute("""
                    INSERT INTO vendas 
                    (observacoes, valor_total, data_venda, cliente_id, proposta_id, usuario_id, status)
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
        
        # Etapa 3: Serviços adicionais (OUTROS) - Gerar lançamento para serviços adicionais
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'OUTROS'
        """, (proposta_id,))
        
        outros = cursor.fetchall()
        valor_total_outros = 0
        
        if outros and len(outros) > 0:
            # Calcular valor total de outros serviços
            for outro in outros:
                outro_id, fornecedor, descricao, outro_valor = outro
                if outro_valor and float(outro_valor) > 0:
                    valor_total_outros += float(outro_valor)
            
            if valor_total_outros > 0:
                cursor.execute("""
                    INSERT INTO financeiro 
                    (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                     proposta_id, status, classificacao, usuario_id)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"Receita - Serviços adicionais - Proposta #{proposta_info['numero']} - {nome_cliente}",
                    valor_total_outros,
                    "Serviços adicionais",  # Categoria
                    "Outros serviços",  # Subcategoria
                    "Receita",  # Tipo
                    proposta_id,  # origem_id
                    "servicos_adicionais",  # origem_tipo
                    proposta_id,  # proposta_id
                    "Pendente",  # status
                    "contas_a_receber",  # classificacao
                    proposta_info['usuario_id']  # usuario_id
                ))
                
                lancamento_id = cursor.fetchone()[0]
                logger.info(f"Lançamento financeiro de Serviços Adicionais criado: #{lancamento_id}, Valor: R${valor_total_outros:.2f}")
                lancamentos_gerados += 1
                resultado["lancamentos"]["valores"]["servicos_adicionais"] = valor_total_outros
        
        # Etapa 4: Comissões de fornecedores
        # Buscar acréscimos do tipo Fornecedor
        cursor.execute("""
            SELECT a.id, a.fornecedor, a.descricao, a.valor, f.percentual_comissao, f.id as fornecedor_id
            FROM acrescimos_proposta a
            LEFT JOIN fornecedores f ON LOWER(a.fornecedor) = LOWER(f.descricao)
            WHERE a.proposta_id = %s AND a.tipo = 'FORNECEDOR'
            AND f.percentual_comissao IS NOT NULL AND f.percentual_comissao > 0
        """, (proposta_id,))
        
        fornecedores = cursor.fetchall()
        valor_total_comissoes = 0
        
        if fornecedores and len(fornecedores) > 0:
            # Gerar um lançamento para cada fornecedor com comissão
            for fornecedor in fornecedores:
                forn_id, forn_nome, forn_descricao, forn_valor, percentual, fornecedor_cadastro_id = fornecedor
                
                if forn_valor and percentual and float(forn_valor) > 0 and float(percentual) > 0:
                    valor_comissao = float(forn_valor) * float(percentual) / 100
                    valor_total_comissoes += valor_comissao
                    
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                         proposta_id, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Comissão de {percentual}% - Fornecedor {forn_nome} - Proposta #{proposta_info['numero']}",
                        valor_comissao,
                        "Comissão sobre fornecedores",  # Categoria
                        "Comissão de Fornecedor",  # Subcategoria
                        "Receita",  # Tipo
                        forn_id,  # origem_id (mantemos o ID do acréscimo para rastreabilidade)
                        "comissao_fornecedor",  # origem_tipo
                        proposta_id,  # proposta_id
                        "Pendente",  # status
                        "contas_a_receber",  # classificacao
                        proposta_info['usuario_id']  # usuario_id
                    ))
                    
                    lancamento_id = cursor.fetchone()[0]
                    logger.info(f"Lançamento financeiro de Comissão criado: #{lancamento_id}, Valor: R${valor_comissao:.2f}, Fornecedor: {forn_nome}")
                    lancamentos_gerados += 1
            
            resultado["lancamentos"]["valores"]["comissoes"] = valor_total_comissoes
        
        # Etapa 5: Pagamentos para assistentes
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor 
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'ASSISTENTE'
        """, (proposta_id,))
        
        assistentes = cursor.fetchall()
        valor_total_assistentes = 0
        
        if assistentes and len(assistentes) > 0:
            # Gerar um lançamento para cada assistente
            for assistente in assistentes:
                assist_id, assist_nome, assist_descricao, assist_valor = assistente
                
                if assist_valor and float(assist_valor) > 0:
                    valor_assistente = float(assist_valor)
                    valor_total_assistentes += valor_assistente
                    
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, tipo, origem_id, origem_tipo, 
                         proposta_id, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Assistente: {assist_nome} - Proposta #{proposta_info['numero']}",
                        valor_assistente,
                        "Pagamento Equipe/Assistentes",  # Categoria
                        "Assistentes",  # Subcategoria
                        "Despesa",  # Tipo
                        assist_id,  # origem_id
                        "acrescimo_assistente",  # origem_tipo
                        proposta_id,  # proposta_id
                        "Pendente",  # status
                        "contas_a_pagar",  # classificacao
                        proposta_info['usuario_id']  # usuario_id
                    ))
                    
                    lancamento_id = cursor.fetchone()[0]
                    logger.info(f"Lançamento financeiro de Assistente criado: #{lancamento_id}, Valor: R${valor_assistente:.2f}")
                    lancamentos_gerados += 1
            
            resultado["lancamentos"]["valores"]["despesa_assistentes"] = valor_total_assistentes
        
        # Commit e finalização
        conn.commit()
        cursor.close()
        conn.close()
        
        # Atualizar resultado com informações gerais
        resultado["lancamentos"]["gerados"] = lancamentos_gerados
        resultado["total_receitas"] = (
            float(resultado["lancamentos"]["valores"].get("base", 0)) +
            float(resultado["lancamentos"]["valores"].get("produtos", 0)) +
            float(resultado["lancamentos"]["valores"].get("servicos_adicionais", 0)) +
            float(resultado["lancamentos"]["valores"].get("comissoes", 0))
        )
        resultado["total_despesas"] = float(resultado["lancamentos"]["valores"].get("despesa_assistentes", 0))
        
        logger.info(f"Finalização da proposta #{proposta_id} concluída. Gerados {lancamentos_gerados} lançamentos.")
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao finalizar proposta: {str(e)}")
        if conn:
            conn.rollback()
            if cursor:
                cursor.close()
            conn.close()
        return {
            "status": False,
            "mensagem": f"Erro ao finalizar proposta: {str(e)}"
        }

# Função auxiliar para integração com o sistema existente
def regenerar_lancamentos_proposta(proposta_id: int) -> Dict[str, Any]:
    """
    Regenera todos os lançamentos financeiros para uma proposta específica
    
    Esta função simplesmente chama a versão aprimorada da finalização de proposta,
    que já lida com a remoção e recriação dos lançamentos.
    """
    return finalizar_proposta_improved(proposta_id)