"""
Módulo aprimorado para finalização segura de propostas com verificação completa
de todos os tipos de lançamentos financeiros - Versão 2.

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

def finalizar_proposta_v2(proposta_id: int) -> Dict[str, Any]:
    """
    Nova versão da função para finalização de propostas com geração completa de lançamentos
    
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
    # Log extra para depuração
    print(f"===== FUNÇÃO FINALIZAR_PROPOSTA_V2 INICIADA PARA PROPOSTA #{proposta_id} =====")
    logger.info(f"[V2] Iniciando nova finalização da proposta #{proposta_id}")
    conn = get_db_connection()
    
    if not conn:
        logger.error("Erro de conexão com banco")
        return {"status": False, "mensagem": "Erro de conexão com banco"}
        
    cursor = None
    lancamentos_gerados = 0
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.numero, p.descricao, p.valor, p.status, p.status_execucao, 
                   p.cliente_id, p.usuario_id, c.nome as nome_cliente
            FROM propostas p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
            FOR UPDATE OF p
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
        
        if proposta_info['status_execucao'] == 'Finalizada':
            logger.info(f"Proposta #{proposta_id} já está finalizada, ignorando chamada duplicada")
            return {"status": True, "mensagem": f"Proposta #{proposta_info.get('numero', proposta_id)} já está finalizada"}

        cursor.execute("""
            UPDATE propostas 
            SET status = 'Finalizada', 
                status_execucao = 'Finalizada'
            WHERE id = %s AND status_execucao != 'Finalizada'
        """, (proposta_id,))

        if cursor.rowcount == 0:
            logger.info(f"Proposta #{proposta_id} já finalizada por outra execução concorrente")
            return {"status": True, "mensagem": f"Proposta #{proposta_info.get('numero', proposta_id)} já está finalizada"}

        logger.info(f"Proposta #{proposta_id} marcada como finalizada")

        cursor.execute("""
            SELECT COUNT(*) FROM financeiro 
            WHERE proposta_id = %s AND origem_tipo IN 
            ('comissao_fornecedor', 'venda_produtos', 'servicos_adicionais', 'pagamento_assistente')
        """, (proposta_id,))
        
        count = cursor.fetchone()[0]
        if count > 0:
            logger.warning(f"Proposta #{proposta_id} já possui {count} lançamentos financeiros")
            cursor.execute("""
                DELETE FROM financeiro 
                WHERE proposta_id = %s AND origem_tipo IN 
                ('comissao_fornecedor', 'venda_produtos', 'servicos_adicionais', 'pagamento_assistente')
            """, (proposta_id,))
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
        # Buscar produtos no módulo de produtos (primeira opção)
        # Primeiro, vamos verificar se há um problema de transação abortada e limpar
        try:
            # Tentar limpar transações abortadas
            conn.rollback()
            
            cursor.execute("""
                SELECT p.id, 'ESTOQUE' as fornecedor, 
                       COALESCE(p.nome, p.descricao) as descricao, 
                       COALESCE(p.preco_venda, p.preco_custo, 0) as valor 
                FROM produtos p
                JOIN itens_venda i ON p.id = i.produto_id
                JOIN vendas v ON i.venda_id = v.id
                WHERE v.proposta_id = %s
            """, (proposta_id,))
        except Exception as e:
            logger.warning(f"Erro ao buscar produtos do estoque: {str(e)}")
            # Se falhar, retornamos uma lista vazia
            logger.info("Continuando com lista vazia de produtos do estoque")
            # Garantir que a transação seja limpa
            try:
                conn.rollback()
            except Exception as e:
                print(f"Erro: {e}")
        
        try:
            produtos_estoque = cursor.fetchall()
        except:
            # Se houve erro na consulta, inicializar com lista vazia
            produtos_estoque = []
            
        # Buscar produtos da tabela produtos_organizadores (nova opção)
        try:
            cursor.execute("""
                SELECT id, 'ORGANIZACAO' as fornecedor, 
                      nome as descricao, 
                      valor * quantidade as valor 
                FROM produtos_organizadores
                WHERE proposta_id = %s
            """, (proposta_id,))
            
            produtos_organizadores = cursor.fetchall()
            logger.info(f"Encontrados {len(produtos_organizadores)} produtos em produtos_organizadores para proposta #{proposta_id}")
        except Exception as e:
            logger.warning(f"Erro ao buscar produtos de organização: {str(e)}")
            produtos_organizadores = []
        
        # Buscar produtos adicionados como acréscimos (segunda opção)
        cursor.execute("""
            SELECT id, fornecedor, descricao, valor
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'PRODUTO'
        """, (proposta_id,))
        
        try:
            produtos_acrescimos = cursor.fetchall()
        except:
            # Se houve erro na consulta, inicializar com lista vazia
            produtos_acrescimos = []
            
        valor_total_produtos = 0
        
        # Combinar produtos do estoque, produtos de organização e produtos de acréscimos
        # Garantir que todas as listas não sejam None
        if produtos_estoque is None:
            produtos_estoque = []
        if produtos_organizadores is None:
            produtos_organizadores = []
        if produtos_acrescimos is None:
            produtos_acrescimos = []
            
        produtos_combinados = produtos_estoque + produtos_organizadores + produtos_acrescimos
        logger.info(f"Produtos combinados: {len(produtos_combinados)} itens (estoque: {len(produtos_estoque)}, organização: {len(produtos_organizadores)}, acréscimos: {len(produtos_acrescimos)})")
        
        if produtos_combinados and len(produtos_combinados) > 0:
            print(f"Total de produtos encontrados: {len(produtos_combinados)}")
            # Calcular valor total de todos os produtos
            for produto in produtos_combinados:
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
                
                cursor.execute("SELECT COUNT(*) FROM vendas WHERE proposta_id = %s", (proposta_id,))
                vendas_existentes = cursor.fetchone()[0]
                if vendas_existentes == 0:
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
                else:
                    logger.info(f"Venda já existe para proposta #{proposta_id}, pulando criação")
        
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
        # Melhorada a consulta para pegar fornecedores com percentual
        cursor.execute("""
            SELECT a.id, a.fornecedor, a.descricao, a.valor, 
                   f.percentual_comissao, 
                   f.id as fornecedor_id
            FROM acrescimos_proposta a
            LEFT JOIN fornecedores f ON (
                LOWER(a.fornecedor) = LOWER(f.descricao)
            )
            WHERE a.proposta_id = %s AND a.tipo = 'FORNECEDOR'
        """, (proposta_id,))
        
        fornecedores = cursor.fetchall()
        valor_total_comissoes = 0
        
        if fornecedores and len(fornecedores) > 0:
            # Gerar um lançamento para cada fornecedor
            for fornecedor in fornecedores:
                forn_id, forn_nome, forn_descricao, forn_valor, percentual_db, fornecedor_cadastro_id = fornecedor
                
                # Usar percentual padrão de 5% se não estiver definido ou for zero
                percentual = 5.0  # Percentual padrão
                if percentual_db is not None and float(percentual_db) > 0:
                    percentual = float(percentual_db)
                
                # Verificar apenas se o valor do fornecedor é maior que zero
                if forn_valor and float(forn_valor) > 0:
                    forn_valor = float(forn_valor)
                    percentual = float(percentual)
                    valor_comissao = forn_valor * percentual / 100
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
                        forn_id,  # origem_id
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
                        "pagamento_assistente",  # origem_tipo
                        proposta_id,  # proposta_id
                        "Pendente",  # status
                        "contas_a_pagar",  # classificacao
                        proposta_info['usuario_id']  # usuario_id
                    ))
                    
                    lancamento_id = cursor.fetchone()[0]
                    logger.info(f"Lançamento financeiro de Pagamento de Assistente criado: #{lancamento_id}, Valor: R${valor_assistente:.2f}, Assistente: {assist_nome}")
                    lancamentos_gerados += 1
            
            resultado["lancamentos"]["valores"]["despesa_assistentes"] = valor_total_assistentes
        
        # ============================================
        # GATILHO: Criar pós-organização automaticamente
        # ============================================
        try:
            # IMPORTANTE: Usar a data ATUAL (hoje) como base para as ações,
            # não a data_fim da proposta, pois a proposta pode ser finalizada
            # dias/semanas após o término do projeto
            data_final = date.today()
            
            # Verificar se já existe pós-organização para esta proposta
            cursor.execute("""
                SELECT id FROM post_organizations WHERE proposta_id = %s AND usuario_id = %s
            """, (proposta_id, proposta_info['usuario_id']))
            
            existing_pos_org = cursor.fetchone()
            
            if not existing_pos_org:
                # Criar registro de pós-organização
                cursor.execute("""
                    INSERT INTO post_organizations (proposta_id, cliente_id, data_final_projeto, status, usuario_id)
                    VALUES (%s, %s, %s, 'ATIVO', %s)
                    RETURNING id
                """, (proposta_id, proposta_info['cliente_id'], data_final, proposta_info['usuario_id']))
                
                pos_org_id = cursor.fetchone()[0]
                
                # Criar ações automáticas padrão
                from datetime import timedelta
                acoes_padrao = [
                    ('AGRADECIMENTO', data_final + timedelta(days=1)),
                    ('MANUTENCAO', data_final + timedelta(days=2)),
                    ('FOLLOW_UP', data_final + timedelta(days=7)),
                    ('FEEDBACK', data_final + timedelta(days=7)),
                    ('OPORTUNIDADE', data_final + timedelta(days=10)),
                ]
                
                for action_type, due_date in acoes_padrao:
                    cursor.execute("""
                        INSERT INTO post_organization_actions 
                        (post_organization_id, action_type, due_date, status, usuario_id)
                        VALUES (%s, %s, %s, 'PENDENTE', %s)
                    """, (pos_org_id, action_type, due_date, proposta_info['usuario_id']))
                
                logger.info(f"Pós-organização criada automaticamente para proposta #{proposta_id}")
                resultado["pos_organizacao"] = {"status": "success", "id": pos_org_id}
            else:
                resultado["pos_organizacao"] = {"status": "exists", "id": existing_pos_org[0]}
                
        except Exception as pos_error:
            logger.warning(f"Erro ao criar pós-organização (não crítico): {str(pos_error)}")
            resultado["pos_organizacao"] = {"status": "error", "message": str(pos_error)}
        
        # Commit das alterações no banco
        conn.commit()
        
        # Atualizar resultados
        resultado["lancamentos"]["gerados"] = lancamentos_gerados
        resultado["proposta_numero"] = proposta_info['numero']
        
        # Contabilizar totais
        total_receitas = (resultado["lancamentos"]["valores"]["base"] +
                         resultado["lancamentos"]["valores"]["produtos"] +
                         resultado["lancamentos"]["valores"]["servicos_adicionais"] +
                         resultado["lancamentos"]["valores"]["comissoes"])
        
        total_despesas = resultado["lancamentos"]["valores"]["despesa_assistentes"]
        
        resultado["totais"] = {
            "receitas": total_receitas,
            "despesas": total_despesas,
            "lucro": total_receitas - total_despesas
        }
        
        logger.info(f"Finalização da proposta #{proposta_id} concluída com sucesso. Gerados {lancamentos_gerados} lançamentos financeiros.")
        
        return resultado
        
    except Exception as e:
        # Em caso de erro, fazer rollback e registrar
        if conn:
            conn.rollback()
        
        logger.error(f"Erro ao finalizar proposta: {str(e)}")
        return {
            "status": False,
            "mensagem": f"Erro ao finalizar proposta: {str(e)}"
        }
    
    finally:
        # Fechar conexão com o banco
        if cursor:
            cursor.close()
        if conn:
            conn.close()