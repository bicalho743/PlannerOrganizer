"""
Módulo para regenerar lançamentos financeiros de propostas já finalizadas
"""
import os
import logging
import psycopg2
from datetime import datetime, date
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.DEBUG, 
                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     handlers=[
                         logging.StreamHandler()
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
                p.data_fim, p.valor, p.status, p.status_execucao, p.numero, p.descricao,
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

def regenerar_lancamentos(proposta_id: int) -> Dict[str, Any]:
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
        
        # Verificar se já existem lançamentos para a proposta
        cursor.execute("""
            SELECT COUNT(*) FROM financeiro WHERE proposta_id = %s
        """, (proposta_id,))
        
        count = cursor.fetchone()[0]
        
        # Apagar lançamentos existentes se houver
        if count > 0:
            logger.info(f"Removendo {count} lançamentos existentes para proposta #{proposta_id}")
            cursor.execute("DELETE FROM financeiro WHERE proposta_id = %s", (proposta_id,))
        
        # Buscar informações da proposta
        proposta = buscar_proposta(proposta_id, conn)
        if not proposta:
            logger.error(f"Erro ao buscar detalhes da proposta #{proposta_id}")
            conn.close()
            return {"status": False, "mensagem": f"Erro ao buscar detalhes da proposta #{proposta_id}"}
            
        cliente_id = proposta.get('cliente_id')
        usuario_id = proposta.get('usuario_id')
        valor = proposta.get('valor', 0)
        numero = proposta.get('numero', proposta_id)
        cliente_nome = proposta.get('cliente_nome', 'Cliente')
        
        lancamentos_gerados = 0
        
        # 1. Criar lançamento principal da proposta
        cursor.execute("""
            INSERT INTO financeiro 
            (descricao, valor, data, categoria, subcategoria, 
            tipo, proposta_id, status, classificacao, usuario_id)
            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            f"Valor a receber - Proposta #{numero} - {cliente_nome}",
            valor,
            "Serviços de organização",
            "Valor a receber",
            "Receita",
            proposta_id,
            "Pendente",
            "contas_a_receber",
            usuario_id
        ))
        
        lancamento_id = cursor.fetchone()[0]
        lancamentos_gerados += 1
        logger.info(f"Lançamento principal criado (ID: {lancamento_id})")
        
        # 2. Buscar acréscimos do tipo FORNECEDOR
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
                
                # Calcular o valor da comissão (5% para todos)
                valor_comissao = float(valor_fornecedor) * 0.05
                
                # Não criamos mais lançamentos automáticos de comissão para fornecedores
                # Apenas registramos o valor para fins informativos
                logger.info(f"Comissão calculada para fornecedor {nome_fornecedor}: R$ {valor_comissao:.2f} (lançamento não criado)")
                logger.info(f"Os lançamentos de comissão devem ser criados manualmente pelo usuário")
        
        # 3. Buscar acréscimos do tipo OUTRO
        cursor.execute("""
            SELECT id, descricao, valor
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'OUTRO'
        """, (proposta_id,))
        
        outros = cursor.fetchall()
        
        for outro in outros:
            id_outro, desc_outro, valor_outro = outro
            if valor_outro and float(valor_outro) > 0:
                try:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, 
                        tipo, proposta_id, status, classificacao, usuario_id)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Acréscimo de OUTRO - Proposta #{numero}",
                        valor_outro,
                        "Serviços Adicionais",
                        "Outros Acréscimos",
                        "Receita",
                        proposta_id,
                        "Pendente",
                        "contas_a_receber",
                        usuario_id
                    ))
                    
                    id_lancamento = cursor.fetchone()[0]
                    lancamentos_gerados += 1
                    logger.info(f"Lançamento de acréscimo OUTRO criado (ID: {id_lancamento})")
                except Exception as e:
                    logger.error(f"Erro ao criar lançamento de acréscimo OUTRO: {str(e)}")
        
        # 4. Buscar acréscimos do tipo ASSISTENTE
        cursor.execute("""
            SELECT id, descricao, valor
            FROM acrescimos_proposta 
            WHERE proposta_id = %s AND tipo = 'ASSISTENTE'
        """, (proposta_id,))
        
        assistentes = cursor.fetchall()
        
        for assistente in assistentes:
            id_assistente, desc_assistente, valor_assistente = assistente
            if valor_assistente and float(valor_assistente) > 0:
                # Não criamos mais lançamentos automáticos para assistentes
                # Apenas registramos o valor para fins informativos
                logger.info(f"Assistente {desc_assistente}: R$ {float(valor_assistente):.2f} (lançamento não criado)")
                logger.info(f"Os lançamentos para assistentes devem ser criados manualmente pelo usuário")
        
        # 5. Verificar se existe venda associada a esta proposta
        cursor.execute("""
            SELECT v.id, v.valor_total, v.status, v.data_venda 
            FROM vendas v
            WHERE v.proposta_id = %s
        """, (proposta_id,))
        
        vendas = cursor.fetchall()
        
        # Criar lançamentos para cada venda
        for venda in vendas:
            venda_id, venda_valor, venda_status, venda_data = venda
            
            # Verificar se já existe lançamento para esta venda
            cursor.execute("""
                SELECT id FROM financeiro 
                WHERE descricao LIKE %s
            """, (f"%Venda de Produtos #{venda_id}%",))
            
            if cursor.fetchone() is None:
                try:
                    cursor.execute("""
                        INSERT INTO financeiro 
                        (descricao, valor, data, categoria, subcategoria, 
                        tipo, proposta_id, status, classificacao, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        f"Receita - Venda de Produtos #{venda_id} - {cliente_nome}",
                        venda_valor,
                        venda_data,
                        "Venda de Produtos",
                        "Produtos",
                        "Receita",
                        proposta_id,
                        "Pendente",
                        "contas_a_receber",
                        usuario_id
                    ))
                    
                    id_lancamento = cursor.fetchone()[0]
                    lancamentos_gerados += 1
                    logger.info(f"Lançamento de venda criado (ID: {id_lancamento}) para venda #{venda_id}")
                except Exception as e:
                    logger.error(f"Erro ao criar lançamento para venda #{venda_id}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        resultado = {
            "status": True,
            "mensagem": f"Foram gerados {lancamentos_gerados} lançamentos para a proposta #{proposta_id}",
            "lancamentos_gerados": lancamentos_gerados,
            "proposta": {
                "id": proposta_id,
                "cliente": cliente_nome,
                "valor": valor
            }
        }
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao regenerar lançamentos para proposta #{proposta_id}: {str(e)}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
            conn.close()
        return {"status": False, "mensagem": f"Erro: {str(e)}"}